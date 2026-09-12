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


# --- CPU-only production PyTorch packaging contract -------------------------
#
# The production build resolved the default PyPI torch wheel, which declares
# nvidia-cudnn-cu13, nvidia-cusparselt-cu13, nvidia-nccl-cu13,
# nvidia-nvshmem-cu13 and triton under `platform_system == "Linux"`. The image
# exhausted the CPU-only host's disk while unpacking libcusparseLt.so.0.

DOCKERFILE = ROOT / "Dockerfile"
CPU_WHEEL_INDEX = "https://download.pytorch.org/whl/cpu"


def _dockerfile_run_steps() -> list[str]:
    """Return each Dockerfile instruction with line continuations joined."""
    joined = _read(DOCKERFILE).replace("\\\n", " ")
    return [
        " ".join(line.split())
        for line in joined.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _pip_install_step() -> str:
    steps = [step for step in _dockerfile_run_steps() if "pip install" in step]
    assert len(steps) == 1, f"expected one pip install step, found {len(steps)}"
    return steps[0]


def _load_cpu_torch_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_cpu_only_torch", ROOT / "deploy" / "verify_cpu_only_torch.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_production_image_installs_an_exact_cpu_torch_from_the_official_index():
    step = _pip_install_step()
    assert f"--index-url {CPU_WHEEL_INDEX}" in step
    pins = [token for token in step.split() if token.startswith("torch==")]
    assert len(pins) == 1, f"torch must be pinned exactly once, found {pins}"
    version = pins[0].split("==", 1)[1]
    # Deterministic: an exact version carrying the CPU local-version segment,
    # never a floating or bare specifier that could resolve to a CUDA build.
    assert version.endswith("+cpu"), version
    assert all(part.isdigit() for part in version[: -len("+cpu")].split("."))


def test_cpu_torch_is_installed_before_unrestricted_requirements_resolution():
    step = _pip_install_step()
    torch_at = step.index("torch==")
    requirements_at = step.index("-r requirements.txt")
    # Ordering is load-bearing: torch must already satisfy sentence-transformers'
    # `torch>=2.2` by the time the general resolution runs, so pip leaves it be.
    assert torch_at < requirements_at


def test_production_image_never_selects_a_cuda_or_gpu_wheel_source():
    # Executable instructions only: the explanatory comment above the install
    # step names the CUDA packages it exists to keep out.
    instructions = " ".join(_dockerfile_run_steps())
    for forbidden in ("/whl/cu", "nvidia-", "nvidia_", "cudnn", "triton", "+cu1"):
        assert forbidden not in instructions, forbidden
    assert CPU_WHEEL_INDEX in instructions
    # A CUDA index must not be reachable as a fallback resolution source.
    assert "--extra-index-url" not in instructions


def test_production_build_verifies_the_cpu_only_result():
    step = _pip_install_step()
    assert "python deploy/verify_cpu_only_torch.py" in step
    # The check must run in the same step, after the requirements resolution.
    assert step.index("-r requirements.txt") < step.index("verify_cpu_only_torch.py")


def test_cpu_torch_verifier_accepts_a_clean_cpu_environment():
    module = _load_cpu_torch_verifier()
    module.verify_cpu_only_torch("2.14.0+cpu", [])


@pytest.mark.parametrize(
    ("version", "gpu"),
    [
        ("2.14.0", []),                                  # default PyPI CUDA build
        ("2.14.0+cu130", []),                            # explicit CUDA build
        ("2.14.0+cpu", ["nvidia-cusparselt-cu13"]),      # CUDA leaked in anyway
        ("2.14.0+cpu", ["triton"]),
    ],
)
def test_cpu_torch_verifier_fails_closed_on_any_gpu_result(version, gpu):
    module = _load_cpu_torch_verifier()
    with pytest.raises(SystemExit):
        module.verify_cpu_only_torch(version, gpu)


def test_cpu_torch_verifier_detects_the_whole_gpu_distribution_family():
    module = _load_cpu_torch_verifier()

    class _Distribution:
        def __init__(self, name):
            self.metadata = {"Name": name}

    names = [
        "nvidia-cudnn-cu13",
        "nvidia_cusparselt_cu13",
        "triton",
        "pytorch-triton",
        "sentence-transformers",
        "llama-index",
        "numpy",
    ]
    found = module.installed_gpu_distributions([_Distribution(n) for n in names])
    assert found == [
        "nvidia-cudnn-cu13",
        "nvidia_cusparselt_cu13",
        "pytorch-triton",
        "triton",
    ]


def test_embedding_and_rag_dependencies_remain_declared():
    requirements = _read(ROOT / "requirements.txt")
    for dependency in (
        "sentence-transformers",
        "llama-index",
        "llama-index-embeddings-huggingface",
    ):
        assert any(
            line.strip() == dependency for line in requirements.splitlines()
        ), dependency
    # torch stays transitive in requirements.txt: a `+cpu` pin there would break
    # non-Linux development installs, so the pin is production-image scoped.
    assert "torch" not in requirements


def test_existing_postgres_build_and_runtime_setup_is_preserved():
    source = _read(DOCKERFILE)
    for expected in (
        "FROM node:22-alpine AS executive-kpi-builder",
        "FROM python:3.12-slim",
        "postgresql-client",
        "build-essential",
        "curl",
        "rm -rf /var/lib/apt/lists/*",
        "EXPOSE 8000",
        'CMD ["python", "run_api.py", "--host", "0.0.0.0", "--port", "8000"]',
        "COPY --from=executive-kpi-builder",
    ):
        assert expected in source, expected
    assert "psycopg[binary]==3.3.4" in _read(ROOT / "requirements.txt")
