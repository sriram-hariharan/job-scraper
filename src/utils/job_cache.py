from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

CACHE_FILE = Path("data/seen_job_ids.txt")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _postgres_seen_jobs_enabled() -> bool:
    return _clean_text(os.environ.get("JOB_STACK_SEEN_JOBS_BACKEND")).lower() == "postgres"


def _owner_user_id_from_env() -> str:
    return _clean_text(os.environ.get("JOB_STACK_OWNER_USER_ID"))


def _run_id_from_env() -> str:
    return _clean_text(
        os.environ.get("JOB_STACK_USER_PIPELINE_RUN_ID")
        or os.environ.get("JOB_APP_PIPELINE_RUN_ID")
    )


def _legacy_load_seen_job_ids() -> Set[str]:
    if not CACHE_FILE.exists():
        return set()

    with open(CACHE_FILE, encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def _legacy_save_new_job_ids(job_ids: Iterable[str]) -> None:
    values = [_clean_text(item) for item in job_ids if _clean_text(item)]
    if not values:
        return

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CACHE_FILE, "a", encoding="utf-8") as f:
        for job_id in values:
            f.write(job_id + "\n")


def _parse_seen_key(seen_key: str) -> Dict[str, str]:
    safe_key = _clean_text(seen_key)
    source = ""
    job_url = ""

    if ":" in safe_key:
        source, job_url = safe_key.split(":", 1)

    return {
        "seen_key": safe_key,
        "source": _clean_text(source),
        "job_url": _clean_text(job_url),
        "job_doc_id": _clean_text(job_url),
    }


def _postgres_load_seen_job_ids(owner_user_id: str) -> Set[str]:
    from src.storage.user_pipeline.store import get_user_seen_jobs_postgres_payload

    payload = get_user_seen_jobs_postgres_payload(
        owner_user_id=owner_user_id,
        limit=250000,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
        ensure_schema=True,
    )

    return {
        _clean_text(row.get("seen_key"))
        for row in list(payload.get("rows", []) or [])
        if _clean_text(row.get("seen_key"))
    }


def _postgres_save_new_job_ids(owner_user_id: str, job_ids: Iterable[str]) -> None:
    from src.storage.user_pipeline.store import (
        upsert_user_seen_job_postgres_payload,
        upsert_user_seen_job_staging_postgres_payload,
    )

    run_id = _run_id_from_env()
    values = [_clean_text(item) for item in job_ids if _clean_text(item)]
    if not values:
        return

    use_staging = bool(run_id)

    for seen_key in values:
        parsed = _parse_seen_key(seen_key)
        record = {
            "owner_user_id": owner_user_id,
            "seen_key": parsed["seen_key"],
            "source": parsed["source"],
            "job_url": parsed["job_url"],
            "job_doc_id": parsed["job_doc_id"],
            "metadata_json": {
                "storage_backend": "postgres",
                "seen_key_source": "collector_cache_filter",
                "staged_seen_job": use_staging,
            },
        }

        if use_staging:
            upsert_user_seen_job_staging_postgres_payload(
                record={
                    **record,
                    "run_id": run_id,
                },
                database_url="",
                database_url_env="DATABASE_URL",
                psql_bin="psql",
                print_only=False,
                ensure_schema=True,
            )
            continue

        upsert_user_seen_job_postgres_payload(
            record={
                **record,
                "first_run_id": run_id,
                "last_run_id": run_id,
            },
            database_url="",
            database_url_env="DATABASE_URL",
            psql_bin="psql",
            print_only=False,
            ensure_schema=True,
        )


def load_seen_job_ids():
    owner_user_id = _owner_user_id_from_env()

    if _postgres_seen_jobs_enabled() and owner_user_id:
        return _postgres_load_seen_job_ids(owner_user_id)

    return _legacy_load_seen_job_ids()


def _job_cache_key(job):
    job_id = job.get("job_id") or job.get("url")
    source = job.get("source")

    if not job_id:
        return ""

    return f"{source}:{job_id}"


def cache_keys_for_jobs(jobs):
    keys = []
    for job in jobs:
        cache_key = _job_cache_key(job)
        if cache_key:
            keys.append(cache_key)
    return keys


def save_new_job_ids(job_ids):
    values = [_clean_text(item) for item in job_ids if _clean_text(item)]
    if not values:
        return

    owner_user_id = _owner_user_id_from_env()

    if _postgres_seen_jobs_enabled() and owner_user_id:
        _postgres_save_new_job_ids(owner_user_id, values)
        return

    _legacy_save_new_job_ids(values)


def filter_new_jobs(jobs, seen_ids):
    new_jobs = []
    new_job_ids = []

    for job in jobs:
        cache_key = _job_cache_key(job)

        if not cache_key:
            new_jobs.append(job)
            continue

        if cache_key in seen_ids:
            continue

        new_jobs.append(job)
        new_job_ids.append(cache_key)

    return new_jobs, new_job_ids
