from __future__ import annotations

import ast
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from cryptography.fernet import Fernet, InvalidToken

from src.ai.provider_model_catalog import list_configurable_providers
from src.storage.user_ai_settings import credential_crypto, store


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "src/storage/user_ai_settings/schema.sql"
STORE_PATH = ROOT / "src/storage/user_ai_settings/store.py"
CRYPTO_PATH = ROOT / "src/storage/user_ai_settings/credential_crypto.py"
REQUIREMENTS_PATH = ROOT / "requirements.txt"
SYNTHETIC_SECRET = "synthetic-provider-secret-4F2A"


@pytest.fixture
def fernet_key(monkeypatch):
    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv(credential_crypto.AI_CREDENTIAL_FERNET_KEYS_ENV, key)
    return key


def _print_kwargs():
    return {"print_only": True, "ensure_schema": False}


def test_schema_defines_exact_owner_scoped_settings_and_credential_tables():
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    assert sql.count("CREATE TABLE IF NOT EXISTS user_ai_settings") == 1
    assert sql.count("CREATE TABLE IF NOT EXISTS user_ai_provider_credentials") == 1
    assert sql.count("CREATE TABLE IF NOT EXISTS user_ai_task_model_selections") == 1
    assert "owner_user_id TEXT PRIMARY KEY REFERENCES auth_users(user_id) ON DELETE CASCADE" in sql
    assert "owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE" in sql
    assert "PRIMARY KEY (owner_user_id, provider)" in sql
    assert "PRIMARY KEY (owner_user_id, workload_id)" in sql
    assert "CHECK (preferred_provider IS NULL OR preferred_provider IN ('groq', 'openai'))" in sql
    assert "CHECK (provider IN ('groq', 'openai'))" in sql
    assert "CHECK (encryption_scheme = 'fernet-v1')" in sql
    assert "api_key" not in sql


def test_task_selection_schema_has_owner_cascade_and_derived_state_is_not_stored():
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    task_table = sql.split(
        "CREATE TABLE IF NOT EXISTS user_ai_task_model_selections",
        1,
    )[1]
    assert (
        "owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) "
        "ON DELETE CASCADE"
    ) in task_table
    assert "workload_id TEXT NOT NULL" in task_table
    assert "provider TEXT NOT NULL" in task_table
    assert "model TEXT NOT NULL" in task_table
    assert "PRIMARY KEY (owner_user_id, workload_id)" in task_table
    for prohibited in (
        "qualification_status",
        "recommendation_status",
        "execution_mode",
        "effective_selection",
        "evidence_sha256",
        "registry_sha",
        "credential_ciphertext",
        "preferred_provider",
    ):
        assert prohibited not in task_table


@pytest.mark.parametrize("provider", ("groq", "openai", " GROQ ", "OpenAI"))
def test_valid_preferred_provider_is_normalized_and_accepted(provider):
    payload = store.set_user_ai_preferred_provider_payload(
        "synthetic-user-a",
        provider,
        **_print_kwargs(),
    )
    expected = provider.strip().lower()
    assert payload["data"]["preferred_provider"] == expected
    assert f"'{expected}'" in payload["sql"]


def test_unknown_preferred_provider_is_rejected_without_database_activity(monkeypatch):
    monkeypatch.setattr(
        store,
        "_run_psql_json_stdin_query",
        lambda **_kwargs: pytest.fail("database helper must not run"),
    )
    with pytest.raises(ValueError, match="Provider is not configurable"):
        store.set_user_ai_preferred_provider_payload(
            "synthetic-user-a",
            "unknown-provider",
            **_print_kwargs(),
        )


@pytest.mark.parametrize("provider", ("groq", "openai"))
def test_valid_credential_providers_are_accepted(provider, fernet_key):
    payload = store.upsert_user_ai_provider_credential_payload(
        "synthetic-user-a",
        provider,
        SYNTHETIC_SECRET,
        **_print_kwargs(),
    )
    assert payload["data"]["provider"] == provider
    assert payload["data"]["configured"] is True


def test_unknown_credential_provider_and_empty_credential_fail_closed(fernet_key):
    with pytest.raises(ValueError, match="Provider is not configurable"):
        store.upsert_user_ai_provider_credential_payload(
            "synthetic-user-a",
            "unknown-provider",
            SYNTHETIC_SECRET,
            **_print_kwargs(),
        )
    with pytest.raises(
        credential_crypto.ProviderCredentialCryptoError,
        match="Provider credential is required",
    ):
        store.upsert_user_ai_provider_credential_payload(
            "synthetic-user-a",
            "groq",
            "   ",
            **_print_kwargs(),
        )


def test_fernet_round_trip_ciphertext_and_rotation_keyring(monkeypatch):
    old_key = Fernet.generate_key().decode("ascii")
    new_key = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv(credential_crypto.AI_CREDENTIAL_FERNET_KEYS_ENV, old_key)
    old_ciphertext = credential_crypto.encrypt_provider_credential(SYNTHETIC_SECRET)
    assert old_ciphertext != SYNTHETIC_SECRET

    monkeypatch.setenv(
        credential_crypto.AI_CREDENTIAL_FERNET_KEYS_ENV,
        f" {new_key}, ,{old_key} ",
    )
    assert credential_crypto.decrypt_provider_credential(old_ciphertext) == (
        SYNTHETIC_SECRET
    )
    new_ciphertext = credential_crypto.encrypt_provider_credential(SYNTHETIC_SECRET)
    assert Fernet(new_key.encode("ascii")).decrypt(
        new_ciphertext.encode("ascii")
    ).decode("utf-8") == SYNTHETIC_SECRET
    with pytest.raises(InvalidToken):
        Fernet(old_key.encode("ascii")).decrypt(new_ciphertext.encode("ascii"))


def test_missing_and_malformed_master_key_fail_closed(monkeypatch):
    monkeypatch.delenv(credential_crypto.AI_CREDENTIAL_FERNET_KEYS_ENV, raising=False)
    with pytest.raises(
        credential_crypto.ProviderCredentialCryptoError,
        match="keyring is not configured",
    ):
        credential_crypto.encrypt_provider_credential(SYNTHETIC_SECRET)

    monkeypatch.setenv(
        credential_crypto.AI_CREDENTIAL_FERNET_KEYS_ENV,
        "malformed-key,\N{SNOWMAN}",
    )
    with pytest.raises(
        credential_crypto.ProviderCredentialCryptoError,
        match="keyring is invalid",
    ):
        credential_crypto.encrypt_provider_credential(SYNTHETIC_SECRET)


def test_wrong_key_invalid_token_and_errors_never_expose_secret(monkeypatch):
    first_key = Fernet.generate_key().decode("ascii")
    second_key = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv(credential_crypto.AI_CREDENTIAL_FERNET_KEYS_ENV, first_key)
    ciphertext = credential_crypto.encrypt_provider_credential(SYNTHETIC_SECRET)
    monkeypatch.setenv(credential_crypto.AI_CREDENTIAL_FERNET_KEYS_ENV, second_key)

    for invalid_ciphertext in (ciphertext, "invalid-token", SYNTHETIC_SECRET):
        with pytest.raises(credential_crypto.ProviderCredentialCryptoError) as exc_info:
            credential_crypto.decrypt_provider_credential(invalid_ciphertext)
        assert SYNTHETIC_SECRET not in str(exc_info.value)
        assert invalid_ciphertext not in str(exc_info.value)


def test_mask_hint_reveals_at_most_four_suffix_characters():
    hint = credential_crypto.mask_provider_credential(SYNTHETIC_SECRET)
    assert hint == "••••••••4F2A"
    assert SYNTHETIC_SECRET not in hint
    assert credential_crypto.mask_provider_credential("abc") == "••••••••"
    assert credential_crypto.mask_provider_credential("abcd") == "••••••••"


def test_plaintext_never_enters_print_only_sql_or_safe_metadata(fernet_key):
    payload = store.upsert_user_ai_provider_credential_payload(
        "synthetic-user-a",
        "groq",
        SYNTHETIC_SECRET,
        **_print_kwargs(),
    )
    assert SYNTHETIC_SECRET not in payload["sql"]
    assert SYNTHETIC_SECRET not in json.dumps(payload["data"], ensure_ascii=False)
    assert "credential_ciphertext" not in payload["data"]
    assert "credential" not in payload["data"]
    assert payload["data"]["credential_hint"] == "••••••••4F2A"


def test_ciphertext_is_used_only_in_sql_and_excluded_from_metadata(monkeypatch):
    marker = "synthetic-ciphertext-marker"
    monkeypatch.setattr(store, "encrypt_provider_credential", lambda _value: marker)
    payload = store.upsert_user_ai_provider_credential_payload(
        "synthetic-user-a",
        "openai",
        SYNTHETIC_SECRET,
        **_print_kwargs(),
    )
    assert marker in payload["sql"]
    assert marker not in json.dumps(payload["data"], ensure_ascii=False)
    assert "credential_ciphertext" not in payload["data"]


def test_replacing_credential_uses_owner_provider_upsert(fernet_key):
    sql = store.upsert_user_ai_provider_credential_payload(
        "synthetic-user-a",
        "groq",
        SYNTHETIC_SECRET,
        **_print_kwargs(),
    )["sql"]
    assert "ON CONFLICT (owner_user_id, provider) DO UPDATE SET" in sql
    assert "credential_ciphertext = EXCLUDED.credential_ciphertext" in sql
    assert "updated_at = NOW()" in sql


def test_owner_scoped_metadata_decryption_and_delete_sql_paths():
    metadata_a = store.get_user_ai_settings_payload(
        "synthetic-user-a", **_print_kwargs()
    )["sql"]
    metadata_b = store.get_user_ai_settings_payload(
        "synthetic-user-b", **_print_kwargs()
    )["sql"]
    decrypt_a = store._get_user_ai_provider_credential_for_server(
        "synthetic-user-a", "groq", **_print_kwargs()
    )["sql"]
    delete_a = store.delete_user_ai_provider_credential_payload(
        "synthetic-user-a", "groq", **_print_kwargs()
    )["sql"]

    assert "'synthetic-user-a'" in metadata_a
    assert "'synthetic-user-b'" not in metadata_a
    assert "'synthetic-user-b'" in metadata_b
    assert "'synthetic-user-a'" not in metadata_b
    for sql in (decrypt_a, delete_a):
        assert "owner_user_id = 'synthetic-user-a'" in sql
        assert "provider = 'groq'" in sql
        assert "synthetic-user-b" not in sql


def test_task_selection_list_is_owner_scoped_safe_and_deterministic():
    first = store.list_user_ai_task_model_selections_payload(
        "synthetic-user-a",
        **_print_kwargs(),
    )
    second = store.list_user_ai_task_model_selections_payload(
        "synthetic-user-b",
        **_print_kwargs(),
    )

    assert "owner_user_id = 'synthetic-user-a'" in first["sql"]
    assert "synthetic-user-b" not in first["sql"]
    assert "owner_user_id = 'synthetic-user-b'" in second["sql"]
    assert "synthetic-user-a" not in second["sql"]
    assert "ORDER BY workload_id" in first["sql"]
    assert first["data"] == {
        "owner_user_id": "synthetic-user-a",
        "selections": [],
    }
    assert "credential_ciphertext" not in first["sql"]


def test_task_selection_upsert_is_exact_owner_workload_pair_and_updates_route():
    payload = store.upsert_user_ai_task_model_selection_payload(
        "synthetic-user-a",
        "skill_extraction",
        " OpenAI ",
        "gpt-5-mini",
        **_print_kwargs(),
    )
    sql = payload["sql"]

    assert "'synthetic-user-a'" in sql
    assert "'skill_extraction'" in sql
    assert "'openai'" in sql
    assert "'gpt-5-mini'" in sql
    assert "ON CONFLICT (owner_user_id, workload_id) DO UPDATE SET" in sql
    assert "provider = EXCLUDED.provider" in sql
    assert "model = EXCLUDED.model" in sql
    assert "updated_at = NOW()" in sql
    assert "synthetic-user-b" not in sql
    assert "credential_ciphertext" not in sql
    assert payload["data"] == {
        "owner_user_id": "synthetic-user-a",
        "workload_id": "skill_extraction",
        "provider": "openai",
        "model": "gpt-5-mini",
        "created_at": "",
        "updated_at": "",
    }


def test_task_selection_delete_targets_only_exact_owner_and_workload():
    payload = store.delete_user_ai_task_model_selection_payload(
        "synthetic-user-a",
        "skill_extraction",
        **_print_kwargs(),
    )
    sql = payload["sql"]

    assert "DELETE FROM user_ai_task_model_selections" in sql
    assert "owner_user_id = 'synthetic-user-a'" in sql
    assert "workload_id = 'skill_extraction'" in sql
    assert "synthetic-user-b" not in sql
    assert "credential_ciphertext" not in sql
    assert payload["data"] == {
        "owner_user_id": "synthetic-user-a",
        "workload_id": "skill_extraction",
        "deleted": False,
    }


def test_task_selection_list_rejects_cross_owner_database_row(monkeypatch):
    monkeypatch.setattr(
        store,
        "_run_psql_json_stdin_query",
        lambda **_kwargs: {
            "command": [],
            "command_text": "",
            "data": {
                "owner_user_id": "synthetic-user-a",
                "selections": [
                    {
                        "owner_user_id": "synthetic-user-b",
                        "workload_id": "skill_extraction",
                        "provider": "openai",
                        "model": "gpt-5-mini",
                    }
                ],
            },
        },
    )

    with pytest.raises(ValueError, match="ownership is invalid"):
        store.list_user_ai_task_model_selections_payload(
            "synthetic-user-a",
            ensure_schema=False,
        )


def test_server_decryption_lookup_rejects_cross_owner_result(monkeypatch, fernet_key):
    ciphertext = credential_crypto.encrypt_provider_credential(SYNTHETIC_SECRET)
    monkeypatch.setattr(
        store,
        "_run_psql_json_stdin_query",
        lambda **_kwargs: {
            "command": [],
            "command_text": "",
            "data": {
                "found": True,
                "owner_user_id": "synthetic-user-b",
                "provider": "groq",
                "credential_ciphertext": ciphertext,
                "encryption_scheme": "fernet-v1",
            },
        },
    )
    with pytest.raises(ValueError, match="ownership is invalid"):
        store._get_user_ai_provider_credential_for_server(
            "synthetic-user-a",
            "groq",
            ensure_schema=False,
        )


def test_server_decryption_lookup_returns_only_requested_credential(monkeypatch, fernet_key):
    ciphertext = credential_crypto.encrypt_provider_credential(SYNTHETIC_SECRET)
    monkeypatch.setattr(
        store,
        "_run_psql_json_stdin_query",
        lambda **_kwargs: {
            "command": [],
            "command_text": "",
            "data": {
                "found": True,
                "owner_user_id": "synthetic-user-a",
                "provider": "openai",
                "credential_ciphertext": ciphertext,
                "encryption_scheme": "fernet-v1",
            },
        },
    )
    result = store._get_user_ai_provider_credential_for_server(
        "synthetic-user-a",
        "openai",
        ensure_schema=False,
    )
    assert result == SYNTHETIC_SECRET


def test_preferred_provider_can_be_cleared_without_a_credential():
    payload = store.clear_user_ai_preferred_provider_payload(
        "synthetic-user-a", **_print_kwargs()
    )
    assert payload["data"]["preferred_provider"] is None
    assert "preferred_provider = NULL" in payload["sql"]
    assert "INSERT INTO user_ai_settings" in payload["sql"]


def test_safe_settings_metadata_reports_each_provider_independently(monkeypatch):
    database_row = {
        "found": True,
        "owner_user_id": "synthetic-user-a",
        "preferred_provider": "groq",
        "providers": {
            "groq": {"configured": True, "credential_hint": "••••••••4F2A"},
            "openai": {"configured": False, "credential_hint": ""},
        },
        "created_at": "2026-08-09T00:00:00Z",
        "updated_at": "2026-08-09T00:00:01Z",
    }
    monkeypatch.setattr(
        store,
        "_run_psql_json_stdin_query",
        lambda **_kwargs: {
            "command": [],
            "command_text": "",
            "data": database_row,
        },
    )
    payload = store.get_user_ai_settings_payload(
        "synthetic-user-a", ensure_schema=False
    )["data"]
    assert payload["providers"] == {
        "groq": {"configured": True, "credential_hint": "••••••••4F2A"},
        "openai": {"configured": False, "credential_hint": ""},
    }
    rendered = json.dumps(payload, ensure_ascii=False)
    assert "credential_ciphertext" not in rendered
    assert SYNTHETIC_SECRET not in rendered


def test_returned_metadata_cannot_mutate_catalog_or_fresh_metadata(monkeypatch):
    source_row = {
        "found": True,
        "preferred_provider": "openai",
        "providers": {
            "groq": {"configured": False, "credential_hint": ""},
            "openai": {"configured": True, "credential_hint": "••••••••4F2A"},
        },
    }
    monkeypatch.setattr(
        store,
        "_run_psql_json_stdin_query",
        lambda **_kwargs: {"command": [], "command_text": "", "data": source_row},
    )
    first = store.get_user_ai_settings_payload(
        "synthetic-user-a", ensure_schema=False
    )["data"]
    first["providers"]["groq"]["configured"] = True
    first["providers"]["openai"]["credential_hint"] = "mutated"
    second = store.get_user_ai_settings_payload(
        "synthetic-user-a", ensure_schema=False
    )["data"]
    assert second["providers"]["groq"]["configured"] is False
    assert second["providers"]["openai"]["credential_hint"] == "••••••••4F2A"
    assert list_configurable_providers() == ["groq", "openai"]


def test_catalog_is_authoritative_for_store_provider_validation(monkeypatch):
    monkeypatch.setattr(store, "list_configurable_providers", lambda: ["openai"])
    assert store._normalize_configurable_provider("OPENAI") == "openai"
    with pytest.raises(ValueError, match="Provider is not configurable"):
        store._normalize_configurable_provider("groq")


def test_import_is_lazy_and_has_no_database_provider_or_decryption_side_effects(
    monkeypatch,
):
    store_source = STORE_PATH.read_text(encoding="utf-8")
    crypto_source = CRYPTO_PATH.read_text(encoding="utf-8")
    tree = ast.parse(store_source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not imported_roots.intersection(
        {"groq", "openai", "requests", "httpx", "socket"}
    )
    assert "GROQ_API_KEY" not in store_source + crypto_source
    assert "OPENAI_API_KEY" not in store_source + crypto_source

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("import must not run psql"),
    )
    monkeypatch.setattr(
        credential_crypto,
        "decrypt_provider_credential",
        lambda *_args, **_kwargs: pytest.fail("import must not decrypt"),
    )
    module_name = "src.storage.user_ai_settings.store"
    original = sys.modules.pop(module_name, None)
    try:
        imported = importlib.import_module(module_name)
        assert imported.list_configurable_providers() == ["groq", "openai"]
    finally:
        sys.modules.pop(module_name, None)
        if original is not None:
            sys.modules[module_name] = original


def test_crypto_reads_only_application_keyring_not_provider_api_keys(
    monkeypatch,
    fernet_key,
):
    reads = []
    original_get = os.environ.get

    def recording_get(name, default=None):
        reads.append(name)
        return original_get(name, default)

    monkeypatch.setattr(os.environ, "get", recording_get)
    credential_crypto.encrypt_provider_credential(SYNTHETIC_SECRET)
    assert reads == [credential_crypto.AI_CREDENTIAL_FERNET_KEYS_ENV]
    assert "GROQ_API_KEY" not in reads
    assert "OPENAI_API_KEY" not in reads


def test_database_command_and_failures_redact_database_credentials(monkeypatch):
    database_url = "postgresql://synthetic_user:database-secret@localhost/example"
    print_payload = store.ensure_user_ai_settings_schema(
        database_url=database_url,
        print_only=True,
    )
    assert "database-secret" not in print_payload["command_text"]
    assert "synthetic_user:***" in print_payload["command_text"]

    monkeypatch.setattr(store.shutil, "which", lambda _value: "/synthetic/psql")
    monkeypatch.setattr(
        store.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError(f"failure {database_url} {SYNTHETIC_SECRET}")
        ),
    )
    with pytest.raises(SystemExit) as exc_info:
        store.ensure_user_ai_settings_schema(database_url=database_url)
    rendered = str(exc_info.value)
    assert "database-secret" not in rendered
    assert SYNTHETIC_SECRET not in rendered
    assert rendered == "User AI settings database operation failed."


def test_requirements_adds_exactly_one_cryptography_dependency():
    dependencies = [
        line.strip()
        for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert dependencies.count("cryptography") == 1
    assert not any(
        line.startswith(("pycryptodome", "fernet", "cryptography=="))
        for line in dependencies
    )
