from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit, urlunsplit

from src.config.role_taxonomy import ROLE_TAXONOMY


DEFAULT_ONBOARDING_PREFERENCES_SCHEMA_SQL_PATH = Path(
    "src/storage/onboarding_preferences/schema.sql"
)

PREFERENCE_LIST_FIELDS = (
    "selected_role_families",
    "target_seniority",
    "preferred_locations",
    "preferred_skills",
    "excluded_keywords",
)


def _load_local_dotenv_if_present(dotenv_path: Path = Path(".env")) -> None:
    path = dotenv_path.expanduser()
    if not path.exists() or not path.is_file():
        return

    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue

            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]

            os.environ[key] = value
    except Exception:
        return


_load_local_dotenv_if_present()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _json_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


def _sql_quote_jsonb(value: Any) -> str:
    return f"{_sql_quote_text(_json_compact(value))}::jsonb"


def _sql_bool_literal(value: Any) -> str:
    return "TRUE" if bool(value) else "FALSE"


def _read_sql_artifact(path: Path, label: str) -> str:
    resolved = Path(path)
    if not resolved.exists():
        raise ValueError(f"Missing {label} SQL file: {resolved}")

    sql = resolved.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{label.capitalize()} SQL file is empty: {resolved}")
    return sql


def onboarding_preferences_schema_sql_text(
    schema_path: Path = DEFAULT_ONBOARDING_PREFERENCES_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "onboarding preferences schema")


def _resolve_database_url(
    explicit_value: str,
    env_var_name: str,
    *,
    allow_placeholder: bool,
) -> str:
    explicit = str(explicit_value or "").strip()
    if explicit:
        return explicit

    env_name = str(env_var_name or "").strip() or "DATABASE_URL"
    env_value = str(os.environ.get(env_name, "") or "").strip()
    if env_value:
        return env_value

    if allow_placeholder:
        return f"${env_name}"

    raise SystemExit(
        f"Database URL is required. Pass --database-url or set {env_name} in the environment."
    )


def _redact_database_url(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return raw

    parts = urlsplit(raw)
    if "@" not in parts.netloc:
        return raw

    userinfo, hostinfo = parts.netloc.rsplit("@", 1)
    redacted_userinfo = f"{userinfo.split(':', 1)[0]}:***" if ":" in userinfo else "***"
    return urlunsplit((parts.scheme, f"{redacted_userinfo}@{hostinfo}", parts.path, parts.query, parts.fragment))


def _run_psql_stdin_command(
    *,
    sql: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    database_url_value = _resolve_database_url(
        database_url,
        database_url_env,
        allow_placeholder=bool(print_only),
    )
    cmd: List[str] = [str(psql_bin), database_url_value, "-X", "-q", "-v", "ON_ERROR_STOP=1"]
    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])
    payload: Dict[str, Any] = {"command": redacted_cmd, "command_text": shlex.join(redacted_cmd)}
    if print_only:
        payload["sql"] = sql
        return payload
    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(f"psql executable not found on PATH: {psql_bin!r}.")
    subprocess.run(cmd, check=True, input=sql, capture_output=True, text=True)
    return payload


def _run_psql_json_stdin_query(
    *,
    sql: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    database_url_value = _resolve_database_url(
        database_url,
        database_url_env,
        allow_placeholder=bool(print_only),
    )
    cmd: List[str] = [str(psql_bin), database_url_value, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-t", "-A"]
    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])
    payload: Dict[str, Any] = {"command": redacted_cmd, "command_text": shlex.join(redacted_cmd), "data": {}}
    if print_only:
        payload["sql"] = sql
        return payload
    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(f"psql executable not found on PATH: {psql_bin!r}.")
    completed = subprocess.run(cmd, check=True, input=sql, capture_output=True, text=True)
    stdout = (completed.stdout or "").strip()
    if not stdout:
        raise SystemExit("psql returned empty output for onboarding-preferences query.")
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse onboarding-preferences query JSON from psql output: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Onboarding-preferences query did not return a JSON object.")
    payload["data"] = data
    return payload


def _normalize_string_list(value: Any) -> List[str]:
    if value is None:
        raw_values: List[Any] = []
    elif isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = [value]

    normalized: List[str] = []
    for item in raw_values:
        text = _clean_text(item)
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _normalize_role_family_ids(value: Any) -> List[str]:
    normalized = _normalize_string_list(value)
    unknown = [role_family_id for role_family_id in normalized if role_family_id not in ROLE_TAXONOMY]
    if unknown:
        allowed = ", ".join(sorted(ROLE_TAXONOMY))
        raise ValueError(
            f"Unknown role family id(s): {', '.join(unknown)}. Allowed: {allowed}"
        )
    return normalized


def validate_onboarding_preferences_payload(preferences: Any) -> Dict[str, Any]:
    if preferences is None:
        preferences = {}
    if not isinstance(preferences, dict):
        raise ValueError("Onboarding preferences must be a dictionary.")

    selected_role_families = _normalize_role_family_ids(
        preferences.get("selected_role_families")
    )
    onboarding_completed = bool(preferences.get("onboarding_completed", False))
    if onboarding_completed and not selected_role_families:
        raise ValueError(
            "onboarding_completed cannot be true without at least one selected role family."
        )

    normalized: Dict[str, Any] = {
        "onboarding_completed": onboarding_completed,
        "selected_role_families": selected_role_families,
    }

    for field_name in PREFERENCE_LIST_FIELDS:
        if field_name == "selected_role_families":
            continue
        normalized[field_name] = _normalize_string_list(preferences.get(field_name))

    return normalized


def _row_to_preferences_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    preferences = {
        "onboarding_completed": bool(row.get("onboarding_completed", False)),
        "selected_role_families": row.get("selected_role_families") or [],
        "target_seniority": row.get("target_seniority") or [],
        "preferred_locations": row.get("preferred_locations") or [],
        "preferred_skills": row.get("preferred_skills") or [],
        "excluded_keywords": row.get("excluded_keywords") or [],
    }
    return {
        "owner_user_id": _clean_text(row.get("owner_user_id")),
        "preferences": validate_onboarding_preferences_payload(preferences),
        "created_at": _clean_text(row.get("created_at")),
        "updated_at": _clean_text(row.get("updated_at")),
    }


def ensure_onboarding_preferences_schema(
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    return _run_psql_stdin_command(
        sql=onboarding_preferences_schema_sql_text(),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )


def get_onboarding_preferences_payload(
    owner_user_id: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_owner = _clean_text(owner_user_id)
    if not safe_owner:
        raise ValueError("owner_user_id is required.")

    schema_sql = onboarding_preferences_schema_sql_text() + "\n\n" if ensure_schema else ""
    sql = schema_sql + f"""
SELECT COALESCE(
    (
        SELECT json_build_object(
            'found', TRUE,
            'owner_user_id', owner_user_id,
            'onboarding_completed', onboarding_completed,
            'selected_role_families', selected_role_families,
            'target_seniority', target_seniority,
            'preferred_locations', preferred_locations,
            'preferred_skills', preferred_skills,
            'excluded_keywords', excluded_keywords,
            'created_at', created_at,
            'updated_at', updated_at
        )
        FROM user_onboarding_preferences
        WHERE owner_user_id = {_sql_quote_text(safe_owner)}
    ),
    json_build_object('found', FALSE, 'owner_user_id', {_sql_quote_text(safe_owner)})
)::text;
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    if print_only:
        return payload

    data = payload.get("data") or {}
    if not data.get("found"):
        payload["data"] = {
            "found": False,
            "owner_user_id": safe_owner,
            "preferences": validate_onboarding_preferences_payload({}),
        }
        return payload

    payload["data"] = {
        "found": True,
        **_row_to_preferences_payload(data),
    }
    return payload


def upsert_onboarding_preferences_payload(
    owner_user_id: str,
    preferences: Dict[str, Any],
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_owner = _clean_text(owner_user_id)
    if not safe_owner:
        raise ValueError("owner_user_id is required.")

    normalized = validate_onboarding_preferences_payload(preferences)
    schema_sql = onboarding_preferences_schema_sql_text() + "\n\n" if ensure_schema else ""
    sql = schema_sql + f"""
WITH upserted AS (
    INSERT INTO user_onboarding_preferences (
        owner_user_id,
        onboarding_completed,
        selected_role_families,
        target_seniority,
        preferred_locations,
        preferred_skills,
        excluded_keywords
    )
    VALUES (
        {_sql_quote_text(safe_owner)},
        {_sql_bool_literal(normalized["onboarding_completed"])},
        {_sql_quote_jsonb(normalized["selected_role_families"])},
        {_sql_quote_jsonb(normalized["target_seniority"])},
        {_sql_quote_jsonb(normalized["preferred_locations"])},
        {_sql_quote_jsonb(normalized["preferred_skills"])},
        {_sql_quote_jsonb(normalized["excluded_keywords"])}
    )
    ON CONFLICT (owner_user_id) DO UPDATE SET
        onboarding_completed = EXCLUDED.onboarding_completed,
        selected_role_families = EXCLUDED.selected_role_families,
        target_seniority = EXCLUDED.target_seniority,
        preferred_locations = EXCLUDED.preferred_locations,
        preferred_skills = EXCLUDED.preferred_skills,
        excluded_keywords = EXCLUDED.excluded_keywords,
        updated_at = NOW()
    RETURNING
        owner_user_id,
        onboarding_completed,
        selected_role_families,
        target_seniority,
        preferred_locations,
        preferred_skills,
        excluded_keywords,
        created_at,
        updated_at
)
SELECT json_build_object(
    'found', TRUE,
    'owner_user_id', owner_user_id,
    'onboarding_completed', onboarding_completed,
    'selected_role_families', selected_role_families,
    'target_seniority', target_seniority,
    'preferred_locations', preferred_locations,
    'preferred_skills', preferred_skills,
    'excluded_keywords', excluded_keywords,
    'created_at', created_at,
    'updated_at', updated_at
)::text
FROM upserted;
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    if print_only:
        payload["data"] = {
            "found": True,
            "owner_user_id": safe_owner,
            "preferences": normalized,
        }
        return payload

    payload["data"] = {
        "found": True,
        **_row_to_preferences_payload(payload.get("data") or {}),
    }
    return payload
