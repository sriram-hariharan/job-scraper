from __future__ import annotations

import base64
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.storage.admin_tools import production_schema_upgrade as upgrade

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.prod.yml"
SYSTEMD = ROOT / "deploy" / "systemd"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_compose_preserves_images_and_adds_only_current_web_runtime_mounts_and_liveness():
    source = _read(COMPOSE)
    assert "image: postgres:18" in source
    assert "image: redis:7-alpine" in source
    assert "postgres_data:/var/lib/postgresql" in source
    assert "web_pipeline_runs:/app/tmp/pipeline_runs" in source
    assert "web_data:/app/data" in source
    assert "web_outputs:/app/outputs" in source
    assert "http://127.0.0.1:8000/health" in source
    assert "curl" in _read(ROOT / "Dockerfile")


@pytest.mark.parametrize(
    ("service_name", "job", "interval"),
    [
        ("applylens-live-pipeline", "live_pipeline", "6h"),
        ("applylens-agent-discovery", "agent_discovery", "1d"),
    ],
)
def test_systemd_scheduler_units_use_canonical_compose_wrapper(service_name, job, interval):
    service = _read(SYSTEMD / f"{service_name}.service")
    timer = _read(SYSTEMD / f"{service_name}.timer")
    assert "Type=oneshot" in service
    assert "User=deploy" in service
    assert "WorkingDirectory=/home/deploy/apps/job-scraper" in service
    assert "/usr/bin/docker compose --env-file .env.production -f docker-compose.prod.yml" in service
    assert f"-m src.pipeline.scheduler --job {job}" in service
    assert "--sync-postgres-run-history" in service
    assert "--require-postgres-run-history-sync" in service
    assert f"OnUnitActiveSec={interval}" in timer
    assert "Persistent=true" in timer


def test_live_scheduler_unit_is_global_acquisition_only_and_has_no_unsafe_flags():
    service = _read(SYSTEMD / "applylens-live-pipeline.service")
    assert "--global-acquisition-only" in service
    assert "--skip-application-planning" in service
    assert "--delete-seen-data no" in service
    for forbidden in (
        "--planning-only",
        "--generate-tailoring",
        "--generate-llm-tailoring",
        "--refresh-llm-tailoring",
        "--generate-llm-fallback",
        "--allow-contract-drift",
        "--trigger-source",
    ):
        assert forbidden not in service


def test_backup_is_fixed_scope_atomic_compressed_and_bounded():
    source = _read(ROOT / "deploy" / "backup_postgres.sh")
    assert 'BACKUP_DIR="/home/deploy/backups/job-scraper/postgres"' in source
    assert 'RETENTION_DAYS="14"' in source
    assert "docker compose --env-file .env.production -f" in source
    assert "exec -T db" in source
    assert "pg_dump" in source
    assert "gzip -9" in source
    assert "mktemp" in source
    assert '[[ ! -s "${temporary_path}" ]]' in source
    assert "uncompressed_bytes=" in source
    assert "Backup contains no SQL payload" in source
    assert "refusing to overwrite" in source
    assert "chmod 600" in source
    assert "-name 'job_scraper_ops_*.sql.gz'" in source
    assert "restore" not in source.lower()


def test_schema_upgrade_allowlist_and_exclusions_are_exact():
    assert [item.name for item in upgrade.PRODUCTION_SCHEMA_ALLOWLIST] == [
        "user_pipeline",
        "profile_resumes",
        "onboarding_preferences",
        "user_ai_settings",
        "notification_state",
        "bulk_generation",
        "agent_feedback",
    ]
    assert set(upgrade.INTENTIONALLY_EXCLUDED_SCHEMAS) == {
        "agent_state",
        "agent_trace",
        "agentic_approvals",
        "durable_orchestration",
        "vector_evidence",
    }


def test_schema_plan_is_read_only_and_contract_checked():
    plan = upgrade.build_production_schema_plan()
    assert plan["mode"] == "plan"
    assert plan["read_only"] is True
    assert plan["transactional"] is True
    assert plan["on_error_stop"] is True
    assert all(len(item["sha256"]) == 64 for item in plan["included"])
    checked = {item["name"] for item in plan["included"] if item["contract_health_checked"]}
    assert checked == {"user_pipeline", "notification_state", "agent_feedback"}


def test_schema_apply_uses_env_connection_and_one_transaction(monkeypatch):
    observed = {}

    def fake_runner(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(upgrade.shutil, "which", lambda value: "/usr/bin/psql")
    payload = upgrade.apply_production_schema_upgrade(
        database_url="postgresql://app:super-secret@db:5432/job_scraper_ops",
        runner=fake_runner,
    )
    assert payload["mode"] == "apply"
    assert "--set=ON_ERROR_STOP=1" in observed["command"]
    assert "--single-transaction" in observed["command"]
    assert all("super-secret" not in part for part in observed["command"])
    assert observed["kwargs"]["env"]["PGPASSWORD"] == "super-secret"
    assert observed["kwargs"]["env"]["PGDATABASE"] == "job_scraper_ops"


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE users;",
        "TRUNCATE users;",
        "DELETE FROM users;",
        "CREATE EXTENSION vector;",
        "ALTER TABLE users DROP COLUMN email;",
    ],
)
def test_schema_upgrade_rejects_destructive_or_unapproved_sql(sql):
    schema = upgrade.ProductionSchema("synthetic", "synthetic.sql", "test")
    with pytest.raises(SystemExit):
        upgrade._validate_additive_sql(schema, sql)


def test_fernet_installer_requires_apply_does_not_print_secret_and_refuses_replacement(
    tmp_path, capsys
):
    spec = importlib.util.spec_from_file_location(
        "install_fernet_key", ROOT / "deploy" / "install_fernet_key.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    env_path = tmp_path / ".env.production"
    env_path.write_text("POSTGRES_DB=job_scraper_ops\n", encoding="utf-8")
    module._install_key(env_path)
    output = capsys.readouterr().out
    assert output == ""
    installed = env_path.read_text(encoding="utf-8")
    value = installed.split(f"{module.KEY_NAME}=", 1)[1].strip()
    assert len(base64.urlsafe_b64decode(value)) == 32
    assert value not in output
    assert os.stat(env_path).st_mode & 0o777 == 0o600
    with pytest.raises(SystemExit):
        module._install_key(env_path)


def test_backup_systemd_and_runbook_preserve_explicit_compose_contract():
    backup_service = _read(SYSTEMD / "applylens-postgres-backup.service")
    backup_timer = _read(SYSTEMD / "applylens-postgres-backup.timer")
    runbook = _read(ROOT / "deploy" / "PRODUCTION_DEPLOYMENT.md")
    assert "User=deploy" in backup_service
    assert "deploy/backup_postgres.sh" in backup_service
    assert "OnUnitActiveSec=1d" in backup_timer
    assert "applylensjobs.com" in runbook
    assert "job-scraper-prod-1" in runbook
    assert "Never invoke Compose with `down -v`" in runbook
    for line in runbook.splitlines():
        stripped = line.strip()
        if stripped.startswith("docker compose "):
            assert "--env-file .env.production -f docker-compose.prod.yml" in stripped


def test_example_documents_placeholder_only():
    source = _read(ROOT / "deploy" / "env.production.example")
    assert "APPLYLENS_AI_CREDENTIAL_FERNET_KEYS=replace_with_generated_fernet_key" in source
    assert "python3 deploy/install_fernet_key.py" in source
    assert "gAAAA" not in source
