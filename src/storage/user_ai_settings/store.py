"""Owner-scoped Postgres persistence for dormant user AI provider settings."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit

from src.ai.provider_model_catalog import list_configurable_providers
from src.storage.user_ai_settings.credential_crypto import (
    AI_CREDENTIAL_ENCRYPTION_SCHEME,
    decrypt_provider_credential,
    encrypt_provider_credential,
    mask_provider_credential,
)


DEFAULT_USER_AI_SETTINGS_SCHEMA_SQL_PATH = Path(
    "src/storage/user_ai_settings/schema.sql"
)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _require_owner_user_id(owner_user_id: Any) -> str:
    owner = _clean_text(owner_user_id)
    if not owner:
        raise ValueError("owner_user_id is required.")
    return owner


def _normalize_configurable_provider(provider: Any) -> str:
    provider_name = _clean_text(provider).lower()
    if provider_name not in list_configurable_providers():
        raise ValueError("Provider is not configurable.")
    return provider_name


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


def _read_sql_artifact(path: Path, label: str) -> str:
    resolved = Path(path)
    if not resolved.exists():
        raise ValueError(f"Missing {label} SQL file: {resolved}")
    sql = resolved.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{label.capitalize()} SQL file is empty: {resolved}")
    return sql


def user_ai_settings_schema_sql_text(
    schema_path: Path = DEFAULT_USER_AI_SETTINGS_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "user AI settings schema")


def _resolve_database_url(
    explicit_value: str,
    env_var_name: str,
    *,
    allow_placeholder: bool,
) -> str:
    explicit = _clean_text(explicit_value)
    if explicit:
        return explicit
    env_name = _clean_text(env_var_name) or "DATABASE_URL"
    env_value = _clean_text(os.environ.get(env_name, ""))
    if env_value:
        return env_value
    if allow_placeholder:
        return f"${env_name}"
    raise SystemExit("Database URL is required for user AI settings storage.")


def _redact_database_url(value: str) -> str:
    raw = _clean_text(value)
    if not raw:
        return raw
    try:
        parts = urlsplit(raw)
    except Exception:
        return "***"
    if "@" not in parts.netloc:
        return raw
    userinfo, hostinfo = parts.netloc.rsplit("@", 1)
    username = userinfo.split(":", 1)[0]
    safe_userinfo = f"{username}:***" if username else "***"
    return urlunsplit(
        (
            parts.scheme,
            f"{safe_userinfo}@{hostinfo}",
            parts.path,
            parts.query,
            parts.fragment,
        )
    )


def _psql_command_payload(
    *,
    database_url: str,
    psql_bin: str,
    json_output: bool,
) -> Dict[str, Any]:
    command: List[str] = [
        str(psql_bin),
        database_url,
        "-X",
        "-q",
        "-v",
        "ON_ERROR_STOP=1",
    ]
    if json_output:
        command.extend(["-t", "-A"])
    redacted_command = list(command)
    redacted_command[1] = _redact_database_url(redacted_command[1])
    return {
        "raw_command": command,
        "command": redacted_command,
        "command_text": shlex.join(redacted_command),
    }


def _run_psql_stdin_command(
    *,
    sql: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    resolved_url = _resolve_database_url(
        database_url,
        database_url_env,
        allow_placeholder=print_only,
    )
    command_payload = _psql_command_payload(
        database_url=resolved_url,
        psql_bin=psql_bin,
        json_output=False,
    )
    payload = {
        "command": command_payload["command"],
        "command_text": command_payload["command_text"],
    }
    if print_only:
        payload["sql"] = sql
        return payload
    if shutil.which(str(psql_bin)) is None:
        raise SystemExit("psql executable is unavailable for user AI settings storage.")
    try:
        subprocess.run(
            command_payload["raw_command"],
            check=True,
            input=sql,
            capture_output=True,
            text=True,
        )
    except Exception:
        raise SystemExit("User AI settings database operation failed.") from None
    return payload


def _run_psql_json_stdin_query(
    *,
    sql: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    resolved_url = _resolve_database_url(
        database_url,
        database_url_env,
        allow_placeholder=print_only,
    )
    command_payload = _psql_command_payload(
        database_url=resolved_url,
        psql_bin=psql_bin,
        json_output=True,
    )
    payload: Dict[str, Any] = {
        "command": command_payload["command"],
        "command_text": command_payload["command_text"],
        "data": {},
    }
    if print_only:
        payload["sql"] = sql
        return payload
    if shutil.which(str(psql_bin)) is None:
        raise SystemExit("psql executable is unavailable for user AI settings storage.")
    try:
        completed = subprocess.run(
            command_payload["raw_command"],
            check=True,
            input=sql,
            capture_output=True,
            text=True,
        )
    except Exception:
        raise SystemExit("User AI settings database operation failed.") from None
    stdout = _clean_text(completed.stdout)
    if not stdout:
        raise SystemExit("User AI settings database query returned no result.")
    try:
        data = json.loads(stdout)
    except Exception:
        raise SystemExit("User AI settings database query returned invalid data.") from None
    if not isinstance(data, dict):
        raise SystemExit("User AI settings database query returned invalid data.")
    payload["data"] = data
    return payload


def _schema_prefix(ensure_schema: bool) -> str:
    return user_ai_settings_schema_sql_text() + "\n\n" if ensure_schema else ""


def _empty_provider_metadata() -> Dict[str, Dict[str, Any]]:
    return {
        provider: {"configured": False, "credential_hint": ""}
        for provider in list_configurable_providers()
    }


def _safe_settings_metadata(
    owner_user_id: str,
    row: Dict[str, Any],
) -> Dict[str, Any]:
    provider_rows = row.get("providers")
    if not isinstance(provider_rows, dict):
        provider_rows = {}
    providers = _empty_provider_metadata()
    for provider in list_configurable_providers():
        candidate = provider_rows.get(provider)
        if not isinstance(candidate, dict):
            continue
        configured = bool(candidate.get("configured", False))
        providers[provider] = {
            "configured": configured,
            "credential_hint": (
                _clean_text(candidate.get("credential_hint"))
                if configured
                else ""
            ),
        }
    preferred_provider = row.get("preferred_provider")
    if preferred_provider is not None:
        preferred_provider = _normalize_configurable_provider(preferred_provider)
    return {
        "owner_user_id": owner_user_id,
        "preferred_provider": preferred_provider,
        "providers": providers,
        "created_at": _clean_text(row.get("created_at")),
        "updated_at": _clean_text(row.get("updated_at")),
    }


def _safe_credential_metadata(
    owner_user_id: str,
    provider: str,
    row: Dict[str, Any],
) -> Dict[str, Any]:
    configured = bool(row.get("configured", row.get("found", False)))
    return {
        "owner_user_id": owner_user_id,
        "provider": provider,
        "configured": configured,
        "credential_hint": _clean_text(row.get("credential_hint")) if configured else "",
        "encryption_scheme": (
            _clean_text(row.get("encryption_scheme")) if configured else ""
        ),
        "created_at": _clean_text(row.get("created_at")),
        "updated_at": _clean_text(row.get("updated_at")),
    }


def _require_task_selection_text(value: Any, label: str) -> str:
    normalized = _clean_text(value)
    if not normalized:
        raise ValueError(f"{label} is required.")
    return normalized


def _safe_task_model_selection_metadata(
    owner_user_id: str,
    row: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "owner_user_id": owner_user_id,
        "workload_id": _clean_text(row.get("workload_id")),
        "provider": _clean_text(row.get("provider")).lower(),
        "model": _clean_text(row.get("model")),
        "created_at": _clean_text(row.get("created_at")),
        "updated_at": _clean_text(row.get("updated_at")),
    }


def ensure_user_ai_settings_schema(
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    return _run_psql_stdin_command(
        sql=user_ai_settings_schema_sql_text(),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )


def get_user_ai_settings_payload(
    owner_user_id: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    provider_pairs = []
    for provider in list_configurable_providers():
        provider_literal = _sql_quote_text(provider)
        provider_pairs.append(
            f"{provider_literal}, COALESCE((SELECT json_build_object("
            f"'configured', TRUE, 'credential_hint', credential_hint) "
            f"FROM user_ai_provider_credentials WHERE owner_user_id = "
            f"{_sql_quote_text(owner)} AND provider = {provider_literal}), "
            "json_build_object('configured', FALSE, 'credential_hint', ''))"
        )
    providers_sql = ",\n                ".join(provider_pairs)
    sql = _schema_prefix(ensure_schema) + f"""
SELECT COALESCE(
    (
        SELECT json_build_object(
            'found', TRUE,
            'owner_user_id', settings.owner_user_id,
            'preferred_provider', settings.preferred_provider,
            'providers', json_build_object(
                {providers_sql}
            ),
            'created_at', settings.created_at,
            'updated_at', settings.updated_at
        )
        FROM user_ai_settings AS settings
        WHERE settings.owner_user_id = {_sql_quote_text(owner)}
    ),
    json_build_object('found', FALSE, 'owner_user_id', {_sql_quote_text(owner)})
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
        payload["data"] = {
            "found": False,
            **_safe_settings_metadata(owner, {}),
        }
        return payload
    row = dict(payload.get("data", {}) or {})
    payload["data"] = {
        "found": bool(row.get("found", False)),
        **_safe_settings_metadata(owner, row),
    }
    return payload


def set_user_ai_preferred_provider_payload(
    owner_user_id: str,
    provider: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    sql = _schema_prefix(ensure_schema) + f"""
WITH changed AS (
    INSERT INTO user_ai_settings (owner_user_id, preferred_provider)
    VALUES ({_sql_quote_text(owner)}, {_sql_quote_text(provider_name)})
    ON CONFLICT (owner_user_id) DO UPDATE SET
        preferred_provider = EXCLUDED.preferred_provider,
        updated_at = NOW()
    RETURNING owner_user_id, preferred_provider, created_at, updated_at
)
SELECT json_build_object(
    'found', TRUE,
    'owner_user_id', owner_user_id,
    'preferred_provider', preferred_provider,
    'created_at', created_at,
    'updated_at', updated_at
)::text FROM changed;
""".strip()
    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    row = dict(payload.get("data", {}) or {})
    row["preferred_provider"] = provider_name
    payload["data"] = {
        "found": True,
        **_safe_settings_metadata(owner, row),
    }
    return payload


def clear_user_ai_preferred_provider_payload(
    owner_user_id: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    sql = _schema_prefix(ensure_schema) + f"""
WITH changed AS (
    INSERT INTO user_ai_settings (owner_user_id, preferred_provider)
    VALUES ({_sql_quote_text(owner)}, NULL)
    ON CONFLICT (owner_user_id) DO UPDATE SET
        preferred_provider = NULL,
        updated_at = NOW()
    RETURNING owner_user_id, preferred_provider, created_at, updated_at
)
SELECT json_build_object(
    'found', TRUE,
    'owner_user_id', owner_user_id,
    'preferred_provider', preferred_provider,
    'created_at', created_at,
    'updated_at', updated_at
)::text FROM changed;
""".strip()
    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    row = dict(payload.get("data", {}) or {})
    row["preferred_provider"] = None
    payload["data"] = {
        "found": True,
        **_safe_settings_metadata(owner, row),
    }
    return payload


def upsert_user_ai_provider_credential_payload(
    owner_user_id: str,
    provider: str,
    credential: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    ciphertext = encrypt_provider_credential(credential)
    credential_hint = mask_provider_credential(credential)
    sql = _schema_prefix(ensure_schema) + f"""
WITH settings_row AS (
    INSERT INTO user_ai_settings (owner_user_id)
    VALUES ({_sql_quote_text(owner)})
    ON CONFLICT (owner_user_id) DO NOTHING
),
upserted AS (
    INSERT INTO user_ai_provider_credentials (
        owner_user_id,
        provider,
        credential_ciphertext,
        credential_hint,
        encryption_scheme
    )
    VALUES (
        {_sql_quote_text(owner)},
        {_sql_quote_text(provider_name)},
        {_sql_quote_text(ciphertext)},
        {_sql_quote_text(credential_hint)},
        {_sql_quote_text(AI_CREDENTIAL_ENCRYPTION_SCHEME)}
    )
    ON CONFLICT (owner_user_id, provider) DO UPDATE SET
        credential_ciphertext = EXCLUDED.credential_ciphertext,
        credential_hint = EXCLUDED.credential_hint,
        encryption_scheme = EXCLUDED.encryption_scheme,
        updated_at = NOW()
    RETURNING owner_user_id, provider, credential_hint, encryption_scheme,
              created_at, updated_at
)
SELECT json_build_object(
    'found', TRUE,
    'configured', TRUE,
    'owner_user_id', owner_user_id,
    'provider', provider,
    'credential_hint', credential_hint,
    'encryption_scheme', encryption_scheme,
    'created_at', created_at,
    'updated_at', updated_at
)::text FROM upserted;
""".strip()
    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    row = dict(payload.get("data", {}) or {})
    row.update(
        {
            "found": True,
            "configured": True,
            "credential_hint": credential_hint,
            "encryption_scheme": AI_CREDENTIAL_ENCRYPTION_SCHEME,
        }
    )
    payload["data"] = _safe_credential_metadata(owner, provider_name, row)
    return payload


def get_user_ai_provider_credential_metadata_payload(
    owner_user_id: str,
    provider: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    sql = _schema_prefix(ensure_schema) + f"""
SELECT COALESCE(
    (
        SELECT json_build_object(
            'found', TRUE,
            'configured', TRUE,
            'owner_user_id', owner_user_id,
            'provider', provider,
            'credential_hint', credential_hint,
            'encryption_scheme', encryption_scheme,
            'created_at', created_at,
            'updated_at', updated_at
        )
        FROM user_ai_provider_credentials
        WHERE owner_user_id = {_sql_quote_text(owner)}
          AND provider = {_sql_quote_text(provider_name)}
    ),
    json_build_object('found', FALSE, 'configured', FALSE)
)::text;
""".strip()
    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    payload["data"] = _safe_credential_metadata(
        owner,
        provider_name,
        dict(payload.get("data", {}) or {}),
    )
    return payload


def delete_user_ai_provider_credential_payload(
    owner_user_id: str,
    provider: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    sql = _schema_prefix(ensure_schema) + f"""
WITH deleted AS (
    DELETE FROM user_ai_provider_credentials
    WHERE owner_user_id = {_sql_quote_text(owner)}
      AND provider = {_sql_quote_text(provider_name)}
    RETURNING owner_user_id
)
SELECT json_build_object(
    'deleted', EXISTS(SELECT 1 FROM deleted),
    'owner_user_id', {_sql_quote_text(owner)},
    'provider', {_sql_quote_text(provider_name)}
)::text;
""".strip()
    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    deleted = bool((payload.get("data") or {}).get("deleted", False))
    payload["data"] = {
        "owner_user_id": owner,
        "provider": provider_name,
        "deleted": deleted,
        "configured": False,
        "credential_hint": "",
    }
    return payload


def list_user_ai_task_model_selections_payload(
    owner_user_id: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    sql = _schema_prefix(ensure_schema) + f"""
SELECT json_build_object(
    'owner_user_id', {_sql_quote_text(owner)},
    'selections', COALESCE(
        (
            SELECT json_agg(
                json_build_object(
                    'owner_user_id', owner_user_id,
                    'workload_id', workload_id,
                    'provider', provider,
                    'model', model,
                    'created_at', created_at,
                    'updated_at', updated_at
                ) ORDER BY workload_id
            )
            FROM user_ai_task_model_selections
            WHERE owner_user_id = {_sql_quote_text(owner)}
        ),
        '[]'::json
    )
)::text;
""".strip()
    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    row = dict(payload.get("data", {}) or {})
    rows = row.get("selections")
    if not isinstance(rows, list):
        rows = []
    selections = []
    for candidate in rows:
        if not isinstance(candidate, dict):
            continue
        if _clean_text(candidate.get("owner_user_id")) != owner:
            raise ValueError("Stored AI task selection ownership is invalid.")
        selections.append(
            _safe_task_model_selection_metadata(owner, candidate)
        )
    payload["data"] = {
        "owner_user_id": owner,
        "selections": selections,
    }
    return payload


def upsert_user_ai_task_model_selection_payload(
    owner_user_id: str,
    workload_id: str,
    provider: str,
    model: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    workload = _require_task_selection_text(workload_id, "workload_id")
    provider_name = _normalize_configurable_provider(provider)
    model_name = _require_task_selection_text(model, "model")
    sql = _schema_prefix(ensure_schema) + f"""
WITH upserted AS (
    INSERT INTO user_ai_task_model_selections (
        owner_user_id,
        workload_id,
        provider,
        model
    )
    VALUES (
        {_sql_quote_text(owner)},
        {_sql_quote_text(workload)},
        {_sql_quote_text(provider_name)},
        {_sql_quote_text(model_name)}
    )
    ON CONFLICT (owner_user_id, workload_id) DO UPDATE SET
        provider = EXCLUDED.provider,
        model = EXCLUDED.model,
        updated_at = NOW()
    RETURNING owner_user_id, workload_id, provider, model,
              created_at, updated_at
)
SELECT json_build_object(
    'owner_user_id', owner_user_id,
    'workload_id', workload_id,
    'provider', provider,
    'model', model,
    'created_at', created_at,
    'updated_at', updated_at
)::text FROM upserted;
""".strip()
    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    row = dict(payload.get("data", {}) or {})
    returned_owner = _clean_text(row.get("owner_user_id"))
    if returned_owner and returned_owner != owner:
        raise ValueError("Stored AI task selection ownership is invalid.")
    row.update(
        {
            "workload_id": workload,
            "provider": provider_name,
            "model": model_name,
        }
    )
    payload["data"] = _safe_task_model_selection_metadata(owner, row)
    return payload


def delete_user_ai_task_model_selection_payload(
    owner_user_id: str,
    workload_id: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    workload = _require_task_selection_text(workload_id, "workload_id")
    sql = _schema_prefix(ensure_schema) + f"""
WITH deleted AS (
    DELETE FROM user_ai_task_model_selections
    WHERE owner_user_id = {_sql_quote_text(owner)}
      AND workload_id = {_sql_quote_text(workload)}
    RETURNING owner_user_id
)
SELECT json_build_object(
    'deleted', EXISTS(SELECT 1 FROM deleted),
    'owner_user_id', {_sql_quote_text(owner)},
    'workload_id', {_sql_quote_text(workload)}
)::text;
""".strip()
    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    payload["data"] = {
        "owner_user_id": owner,
        "workload_id": workload,
        "deleted": bool((payload.get("data") or {}).get("deleted", False)),
    }
    return payload


def _get_user_ai_provider_credential_for_server(
    owner_user_id: str,
    provider: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Optional[str] | Dict[str, Any]:
    """Return one decrypted credential for an exact server-side owner lookup."""

    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    sql = _schema_prefix(ensure_schema) + f"""
SELECT COALESCE(
    (
        SELECT json_build_object(
            'found', TRUE,
            'owner_user_id', owner_user_id,
            'provider', provider,
            'credential_ciphertext', credential_ciphertext,
            'encryption_scheme', encryption_scheme
        )
        FROM user_ai_provider_credentials
        WHERE owner_user_id = {_sql_quote_text(owner)}
          AND provider = {_sql_quote_text(provider_name)}
    ),
    json_build_object('found', FALSE)
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
    row = dict(payload.get("data", {}) or {})
    if not row.get("found"):
        return None
    if (
        _clean_text(row.get("owner_user_id")) != owner
        or _clean_text(row.get("provider")).lower() != provider_name
    ):
        raise ValueError("Stored AI provider credential ownership is invalid.")
    if _clean_text(row.get("encryption_scheme")) != AI_CREDENTIAL_ENCRYPTION_SCHEME:
        raise ValueError("Stored AI provider credential scheme is unsupported.")
    return decrypt_provider_credential(row.get("credential_ciphertext"))


def clone_safe_user_ai_settings_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Return a defensive copy for future safe API/UI readback boundaries."""

    return deepcopy(metadata)
