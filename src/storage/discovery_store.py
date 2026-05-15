from __future__ import annotations

import json
import os
import subprocess
from threading import Lock
from typing import Any, Dict, Iterable, List, Set

from src.storage.redis_cache import cache_delete, cache_get_json, cache_set_json


_init_lock = Lock()
_db_initialized = False
_db_write_lock = Lock()

_DISCOVERY_COMPANY_DOMAINS_CACHE_KEY = "discovery:company_domains:v1"
_DISCOVERY_ATS_COMPANIES_CACHE_PREFIX = "discovery:ats_companies:v1"


def _discovery_cache_ttl_seconds() -> int:
    raw = _clean_text(os.environ.get("JOB_STACK_DISCOVERY_REDIS_TTL_SECONDS"))
    try:
        ttl = int(raw)
    except Exception:
        ttl = 300

    return max(1, min(ttl, 3600))


def _cache_get_list_safe(key: str):
    try:
        cached = cache_get_json(key)
    except Exception:
        return None

    if isinstance(cached, list):
        return cached

    return None


def _cache_set_list_safe(key: str, values: Iterable[str]) -> None:
    try:
        cache_set_json(
            key,
            sorted({_clean_text(value) for value in values if _clean_text(value)}),
            ttl_seconds=_discovery_cache_ttl_seconds(),
        )
    except Exception:
        return


def _cache_delete_safe(*keys: str) -> None:
    for key in keys:
        try:
            cache_delete(key)
        except Exception:
            continue


def _ats_companies_cache_key(ats: str = "") -> str:
    safe_ats = _clean_text(ats).lower() or "all"
    return f"{_DISCOVERY_ATS_COMPANIES_CACHE_PREFIX}:{safe_ats}"


_DISCOVERY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS company_domains (
    domain TEXT PRIMARY KEY,
    source TEXT NOT NULL DEFAULT '',
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_company_domains_last_seen
ON company_domains (last_seen_at DESC);

CREATE TABLE IF NOT EXISTS discovered_ats_companies (
    ats TEXT NOT NULL,
    company TEXT NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (ats, company)
);

CREATE INDEX IF NOT EXISTS idx_discovered_ats_companies_ats_seen
ON discovered_ats_companies (ats, last_seen_at DESC);

CREATE TABLE IF NOT EXISTS discovery_crawl_state (
    company TEXT PRIMARY KEY,
    last_scraped DOUBLE PRECISION NOT NULL DEFAULT 0,
    state_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS discovery_offsets (
    source_name TEXT PRIMARY KEY,
    offset_value INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ats_detection_cache (
    domain TEXT PRIMARY KEY,
    cache_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
""".strip()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _database_url() -> str:
    database_url = _clean_text(os.environ.get("DATABASE_URL"))
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required for Postgres-backed discovery store."
        )
    return database_url


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


def _sql_jsonb(value: Any) -> str:
    return (
        _sql_quote_text(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        + "::jsonb"
    )


def _run_psql_statement(sql: str) -> None:
    subprocess.run(
        [
            "psql",
            _database_url(),
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _run_psql_json_query(sql: str) -> Dict[str, Any]:
    completed = subprocess.run(
        [
            "psql",
            _database_url(),
            "-X",
            "-t",
            "-A",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        return {}

    return dict(json.loads(lines[-1]) or {})


def init_discovery_store() -> None:
    global _db_initialized

    with _init_lock:
        if _db_initialized:
            return

        _run_psql_statement(_DISCOVERY_SCHEMA_SQL)
        _db_initialized = True


def get_company_domains() -> Set[str]:
    cached = _cache_get_list_safe(_DISCOVERY_COMPANY_DOMAINS_CACHE_KEY)
    if cached is not None:
        return {
            _clean_text(domain)
            for domain in cached
            if _clean_text(domain)
        }

    init_discovery_store()

    sql = """
WITH domain_rows AS (
    SELECT domain
    FROM company_domains
    ORDER BY domain ASC
)
SELECT json_build_object(
    'domains', COALESCE((SELECT json_agg(domain) FROM domain_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)
    domains = {
        _clean_text(domain)
        for domain in list(payload.get("domains", []) or [])
        if _clean_text(domain)
    }
    _cache_set_list_safe(_DISCOVERY_COMPANY_DOMAINS_CACHE_KEY, domains)
    return domains


def upsert_company_domains(domains: Iterable[str], *, source: str = "") -> int:
    init_discovery_store()

    cleaned = sorted({_clean_text(domain).lower() for domain in domains if _clean_text(domain)})
    if not cleaned:
        return 0

    values = []
    for domain in cleaned:
        values.append(
            "("
            + ", ".join(
                [
                    _sql_quote_text(domain),
                    _sql_quote_text(source),
                    "now()",
                    "now()",
                    _sql_jsonb({"source": source}),
                ]
            )
            + ")"
        )

    sql = f"""
WITH incoming(domain, source, first_seen_at, last_seen_at, metadata_json) AS (
    VALUES
{",\n".join(values)}
),
new_rows AS (
    SELECT incoming.*
    FROM incoming
    LEFT JOIN company_domains existing
      ON existing.domain = incoming.domain
    WHERE existing.domain IS NULL
),
upserted AS (
    INSERT INTO company_domains (
        domain,
        source,
        first_seen_at,
        last_seen_at,
        metadata_json
    )
    SELECT
        domain,
        source,
        first_seen_at,
        last_seen_at,
        metadata_json
    FROM incoming
    ON CONFLICT (domain) DO UPDATE SET
        last_seen_at = now(),
        metadata_json = company_domains.metadata_json || EXCLUDED.metadata_json
    RETURNING domain
)
SELECT json_build_object(
    'new_count', (SELECT COUNT(*) FROM new_rows),
    'upserted_count', (SELECT COUNT(*) FROM upserted)
);
""".strip()

    with _db_write_lock:
        payload = _run_psql_json_query(sql)

    _cache_delete_safe(_DISCOVERY_COMPANY_DOMAINS_CACHE_KEY)

    return int(payload.get("new_count", 0) or 0)


def get_discovered_ats_companies(ats: str = "") -> Set[str]:
    safe_ats = _clean_text(ats).lower()
    cache_key = _ats_companies_cache_key(safe_ats)

    cached = _cache_get_list_safe(cache_key)
    if cached is not None:
        return {
            _clean_text(company)
            for company in cached
            if _clean_text(company)
        }

    init_discovery_store()

    ats_filter = f"WHERE ats = {_sql_quote_text(safe_ats)}" if safe_ats else ""

    sql = f"""
WITH company_rows AS (
    SELECT company
    FROM discovered_ats_companies
    {ats_filter}
    ORDER BY company ASC
)
SELECT json_build_object(
    'companies', COALESCE((SELECT json_agg(company) FROM company_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)
    companies = {
        _clean_text(company)
        for company in list(payload.get("companies", []) or [])
        if _clean_text(company)
    }
    _cache_set_list_safe(cache_key, companies)
    return companies


def upsert_discovered_ats_companies(
    ats: str,
    companies: Iterable[str],
    *,
    source: str = "",
) -> int:
    init_discovery_store()

    safe_ats = _clean_text(ats).lower()
    cleaned = sorted({_clean_text(company).lower() for company in companies if _clean_text(company)})

    if not safe_ats or not cleaned:
        return 0

    values = []
    for company in cleaned:
        values.append(
            "("
            + ", ".join(
                [
                    _sql_quote_text(safe_ats),
                    _sql_quote_text(company),
                    "now()",
                    "now()",
                    _sql_jsonb({"source": source or "discovery"}),
                ]
            )
            + ")"
        )

    sql = f"""
WITH incoming(ats, company, first_seen_at, last_seen_at, metadata_json) AS (
    VALUES
{",\n".join(values)}
),
new_rows AS (
    SELECT incoming.*
    FROM incoming
    LEFT JOIN discovered_ats_companies existing
      ON existing.ats = incoming.ats
     AND existing.company = incoming.company
    WHERE existing.company IS NULL
),
upserted AS (
    INSERT INTO discovered_ats_companies (
        ats,
        company,
        first_seen_at,
        last_seen_at,
        metadata_json
    )
    SELECT
        ats,
        company,
        first_seen_at,
        last_seen_at,
        metadata_json
    FROM incoming
    ON CONFLICT (ats, company) DO UPDATE SET
        last_seen_at = now(),
        metadata_json = discovered_ats_companies.metadata_json || EXCLUDED.metadata_json
    RETURNING ats, company
)
SELECT json_build_object(
    'new_count', (SELECT COUNT(*) FROM new_rows),
    'upserted_count', (SELECT COUNT(*) FROM upserted)
);
""".strip()

    with _db_write_lock:
        payload = _run_psql_json_query(sql)

    _cache_delete_safe(
        _ats_companies_cache_key(safe_ats),
        _ats_companies_cache_key(""),
    )

    return int(payload.get("new_count", 0) or 0)


def load_discovery_crawl_schedule() -> Dict[str, Dict[str, Any]]:
    init_discovery_store()

    sql = """
WITH state_rows AS (
    SELECT
        company,
        last_scraped,
        state_json
    FROM discovery_crawl_state
    ORDER BY company ASC
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(row_to_json(state_rows)) FROM state_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)

    schedule: Dict[str, Dict[str, Any]] = {}
    for row in list(payload.get("rows", []) or []):
        company = _clean_text(row.get("company"))
        if not company:
            continue

        state = dict(row.get("state_json", {}) or {})
        state["last_scraped"] = float(row.get("last_scraped", 0) or 0)
        schedule[company] = state

    return schedule


def save_discovery_crawl_schedule(schedule: Dict[str, Any]) -> None:
    init_discovery_store()

    if not isinstance(schedule, dict):
        schedule = {}

    values = []
    for company, raw_state in schedule.items():
        safe_company = _clean_text(company)
        if not safe_company:
            continue

        state = dict(raw_state or {}) if isinstance(raw_state, dict) else {}
        try:
            last_scraped = float(state.get("last_scraped", 0) or 0)
        except Exception:
            last_scraped = 0

        values.append(
            "("
            + ", ".join(
                [
                    _sql_quote_text(safe_company),
                    str(last_scraped),
                    _sql_jsonb(state),
                    "now()",
                ]
            )
            + ")"
        )

    if not values:
        sql = "DELETE FROM discovery_crawl_state;"
    else:
        sql = f"""
WITH incoming(company, last_scraped, state_json, updated_at) AS (
    VALUES
{",\n".join(values)}
),
deleted AS (
    DELETE FROM discovery_crawl_state
    WHERE company NOT IN (SELECT company FROM incoming)
)
INSERT INTO discovery_crawl_state (
    company,
    last_scraped,
    state_json,
    updated_at
)
SELECT
    company,
    last_scraped,
    state_json,
    updated_at
FROM incoming
ON CONFLICT (company) DO UPDATE SET
    last_scraped = EXCLUDED.last_scraped,
    state_json = EXCLUDED.state_json,
    updated_at = now();
""".strip()

    with _db_write_lock:
        _run_psql_statement(sql)


def load_discovery_offsets() -> Dict[str, int]:
    init_discovery_store()

    sql = """
WITH offset_rows AS (
    SELECT source_name, offset_value
    FROM discovery_offsets
    ORDER BY source_name ASC
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(row_to_json(offset_rows)) FROM offset_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)

    return {
        _clean_text(row.get("source_name")): int(row.get("offset_value", 0) or 0)
        for row in list(payload.get("rows", []) or [])
        if _clean_text(row.get("source_name"))
    }


def save_discovery_offsets(offsets: Dict[str, Any]) -> None:
    init_discovery_store()

    if not isinstance(offsets, dict):
        offsets = {}

    values = []
    for source_name, offset_value in offsets.items():
        safe_source = _clean_text(source_name)
        if not safe_source:
            continue

        try:
            safe_offset = int(offset_value or 0)
        except Exception:
            safe_offset = 0

        values.append(
            "("
            + ", ".join(
                [
                    _sql_quote_text(safe_source),
                    str(max(0, safe_offset)),
                    "now()",
                ]
            )
            + ")"
        )

    if not values:
        sql = "DELETE FROM discovery_offsets;"
    else:
        sql = f"""
WITH incoming(source_name, offset_value, updated_at) AS (
    VALUES
{",\n".join(values)}
),
deleted AS (
    DELETE FROM discovery_offsets
    WHERE source_name NOT IN (SELECT source_name FROM incoming)
)
INSERT INTO discovery_offsets (
    source_name,
    offset_value,
    updated_at
)
SELECT
    source_name,
    offset_value,
    updated_at
FROM incoming
ON CONFLICT (source_name) DO UPDATE SET
    offset_value = EXCLUDED.offset_value,
    updated_at = now();
""".strip()

    with _db_write_lock:
        _run_psql_statement(sql)


def load_ats_detection_cache() -> Dict[str, Any]:
    init_discovery_store()

    sql = """
WITH cache_rows AS (
    SELECT domain, cache_json
    FROM ats_detection_cache
    ORDER BY domain ASC
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(row_to_json(cache_rows)) FROM cache_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)

    return {
        _clean_text(row.get("domain")): row.get("cache_json")
        for row in list(payload.get("rows", []) or [])
        if _clean_text(row.get("domain"))
    }


def save_ats_detection_cache(cache: Dict[str, Any]) -> None:
    init_discovery_store()

    if not isinstance(cache, dict):
        cache = {}

    values = []
    for domain, payload in cache.items():
        safe_domain = _clean_text(domain).lower()
        if not safe_domain:
            continue

        values.append(
            "("
            + ", ".join(
                [
                    _sql_quote_text(safe_domain),
                    _sql_jsonb(payload or {}),
                    "now()",
                ]
            )
            + ")"
        )

    if not values:
        sql = "DELETE FROM ats_detection_cache;"
    else:
        sql = f"""
WITH incoming(domain, cache_json, updated_at) AS (
    VALUES
{",\n".join(values)}
),
deleted AS (
    DELETE FROM ats_detection_cache
    WHERE domain NOT IN (SELECT domain FROM incoming)
)
INSERT INTO ats_detection_cache (
    domain,
    cache_json,
    updated_at
)
SELECT
    domain,
    cache_json,
    updated_at
FROM incoming
ON CONFLICT (domain) DO UPDATE SET
    cache_json = EXCLUDED.cache_json,
    updated_at = now();
""".strip()

    with _db_write_lock:
        _run_psql_statement(sql)
