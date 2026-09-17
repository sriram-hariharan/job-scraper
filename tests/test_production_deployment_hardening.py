from __future__ import annotations

import base64
import configparser
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.storage.admin_tools import production_schema_upgrade as upgrade

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.prod.yml"
SYSTEMD = ROOT / "deploy" / "systemd"


def _load_systemd_observer_module():
    spec = importlib.util.spec_from_file_location(
        "write_systemd_scheduler_runtime_snapshot",
        ROOT / "deploy" / "write_systemd_scheduler_runtime_snapshot.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    assert "JOB_STACK_SCHEDULER_RUNTIME_PROVIDER: systemd_snapshot" in source
    assert "JOB_STACK_SCHEDULER_RUNTIME_SNAPSHOT_PATH: /app/runtime/scheduler/status.json" in source
    assert 'JOB_STACK_SCHEDULER_RUNTIME_MAX_AGE_SECONDS: "180"' in source
    assert "source: /var/lib/applylens-scheduler-runtime" in source
    assert "target: /app/runtime/scheduler" in source
    assert "read_only: true" in source
    assert "create_host_path: false" in source
    for forbidden in (
        "/var/run/docker.sock",
        "/run/systemd/private",
        "/run/dbus/system_bus_socket",
        "privileged: true",
    ):
        assert forbidden not in source
    assert "http://127.0.0.1:8000/health" in source
    assert "curl" in _read(ROOT / "Dockerfile")


@pytest.mark.parametrize(
    ("service_name", "job", "calendar"),
    [
        (
            "applylens-live-pipeline",
            "live_pipeline",
            "*-*-* 04,10,16,22:42:00 UTC",
        ),
        (
            "applylens-agent-discovery",
            "agent_discovery",
            "*-*-* 04:57:00 UTC",
        ),
    ],
)
def test_systemd_scheduler_units_use_canonical_compose_wrapper(service_name, job, calendar):
    service = _read(SYSTEMD / f"{service_name}.service")
    timer = _read(SYSTEMD / f"{service_name}.timer")
    assert "Type=oneshot" in service
    assert "User=deploy" in service
    assert "WorkingDirectory=/home/deploy/apps/job-scraper" in service
    assert "/usr/bin/docker compose --env-file .env.production -f docker-compose.prod.yml" in service
    assert f"-m src.pipeline.scheduler --job {job}" in service
    assert "--sync-postgres-run-history" in service
    assert "--require-postgres-run-history-sync" in service
    assert f"OnCalendar={calendar}" in timer
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
        "scheduler",
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
    assert checked == {
        "user_pipeline",
        "notification_state",
        "agent_feedback",
        "scheduler",
    }


def test_scheduler_pause_schema_is_additive_and_backup_is_outside_its_surface():
    scheduler_schema = _read(ROOT / "src/storage/scheduler/schema.sql")
    assert "CREATE TABLE IF NOT EXISTS scheduler_automation_control_events" in scheduler_schema
    assert "GENERATED ALWAYS AS IDENTITY" in scheduler_schema
    assert "ALTER TABLE scheduler_automation_control_events" in scheduler_schema
    assert "ADD COLUMN IF NOT EXISTS job_name TEXT" in scheduler_schema
    assert "job_name IS NULL" in scheduler_schema
    assert "job_name IN ('agent_discovery', 'live_pipeline')" in scheduler_schema
    upgrade._validate_additive_sql(
        next(schema for schema in upgrade.PRODUCTION_SCHEMA_ALLOWLIST if schema.name == "scheduler"),
        scheduler_schema,
    )
    assert "DROP " not in scheduler_schema.upper()
    assert "TRUNCATE " not in scheduler_schema.upper()
    assert _read(SYSTEMD / "applylens-postgres-backup.service").count(
        "/home/deploy/apps/job-scraper/deploy/backup_postgres.sh"
    ) == 1
    assert "src.pipeline.scheduler" not in _read(
        SYSTEMD / "applylens-postgres-backup.service"
    )


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
    assert "OnCalendar=*-*-* 04:47:00 UTC" in backup_timer
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
    assert "JOB_STACK_AUTH_REGISTRATION_ENABLED=true" in source
    assert "JOB_STACK_AUTH_REGISTRATION_APPROVAL_REQUIRED=false" in source
    assert "JOB_STACK_AUTH_REGISTRATION_ENABLED=false" not in source
    assert "JOB_STACK_AUTH_REGISTRATION_APPROVAL_REQUIRED=true" not in source


# --- CPU-only production PyTorch packaging contract -------------------------
#
# The production build resolved the default PyPI torch wheel, which declares
# nvidia-cudnn-cu13, nvidia-cusparselt-cu13, nvidia-nccl-cu13,
# nvidia-nvshmem-cu13 and triton under `platform_system == "Linux"`. The image
# exhausted the CPU-only host's disk while unpacking libcusparseLt.so.0.

DOCKERFILE = ROOT / "Dockerfile"
CPU_WHEEL_INDEX = "https://download.pytorch.org/whl/cpu"
PACKAGED_V1_REGISTRY = (
    ROOT / "src/evaluation/production_provider_qualification_registry_v1.json"
)
PACKAGED_V1_SHA256 = (
    "6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f"
)


def test_packaged_provider_registry_is_tracked_image_content_not_volume_state():
    from hashlib import sha256

    dockerfile = _read(ROOT / "Dockerfile")
    dockerignore = _read(ROOT / ".dockerignore")
    compose = _read(COMPOSE)
    routing = _read(ROOT / "src/app/provider_model_routing_service.py")
    runbook = _read(ROOT / "deploy/PRODUCTION_DEPLOYMENT.md")

    assert PACKAGED_V1_REGISTRY.is_file()
    assert sha256(PACKAGED_V1_REGISTRY.read_bytes()).hexdigest() == (
        PACKAGED_V1_SHA256
    )
    assert "COPY . ." in dockerfile
    assert "src/" not in dockerignore
    assert "outputs/" in dockerignore
    assert "web_outputs:/app/outputs" in compose
    assert "load_production_provider_qualification_registry" in routing
    assert "load_provider_qualification_registry(" not in routing
    assert "PRODUCTION_PROVIDER_QUALIFICATION_REGISTRY_ARTIFACT_PATH" in routing
    assert "qualification_registry.REGISTRY_ARTIFACT_PATH" not in routing
    assert "/app/src/evaluation/production_provider_qualification_registry_v1.json" in runbook
    assert PACKAGED_V1_SHA256 in runbook
    assert "/app/outputs" in runbook


def _dockerfile_run_steps() -> list[str]:
    """Return each Dockerfile instruction with line continuations joined."""
    joined = _read(DOCKERFILE).replace("\\\n", " ")
    return [
        " ".join(line.split())
        for line in joined.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def test_routing_authority_permissions_are_normalized_after_every_copy():
    steps = _dockerfile_run_steps()
    permission_step = (
        "RUN chmod 0755 /app/src /app/src/evaluation "
        "&& chmod 0644 "
        "/app/src/evaluation/production_provider_qualification_registry_v1.json "
        "/app/src/evaluation/renderer_bound_v2_skill_qualification_registry.json "
        "/app/src/evaluation/renderer_bound_v2_job_fit_qualification_registry.json"
    )

    assert steps.count(permission_step) == 1
    assert steps.index(permission_step) > max(
        index for index, step in enumerate(steps) if step.startswith("COPY ")
    )
    assert "chmod -R" not in permission_step


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


# --- Production calendar timer contract ------------------------------------
#
# Activation-relative first-run legs are re-armed when systemd re-executes,
# which caused duplicate production runs without a reboot. Calendar-only UTC
# schedules retain the legitimate anchors without tying them to manager or
# machine lifetime.

TIMER_CALENDAR_CONTRACT = {
    "applylens-live-pipeline": "*-*-* 04,10,16,22:42:00 UTC",
    "applylens-postgres-backup": "*-*-* 04:47:00 UTC",
    "applylens-agent-discovery": "*-*-* 04:57:00 UTC",
}

MONOTONIC_TIMER_DIRECTIVES = {
    "OnActiveSec",
    "OnBootSec",
    "OnStartupSec",
    "OnUnitActiveSec",
    "OnUnitInactiveSec",
}

EXPECTED_SYSTEMD_INVENTORY = {
    "applylens-live-pipeline.service",
    "applylens-live-pipeline.timer",
    "applylens-postgres-backup.service",
    "applylens-postgres-backup.timer",
    "applylens-agent-discovery.service",
    "applylens-agent-discovery.timer",
    "applylens-scheduler-runtime-observation.service",
    "applylens-scheduler-runtime-observation.timer",
}

# Byte-exact ExecStart lines. The timer repair must not alter any service
# command, so these pin the scheduler safety flags and the backup scope.
EXPECTED_EXEC_START = {
    "applylens-live-pipeline": (
        "/usr/bin/docker compose --env-file .env.production -f docker-compose.prod.yml"
        " exec -T web python -u -m src.pipeline.scheduler --job live_pipeline"
        " --global-acquisition-only --skip-application-planning --delete-seen-data no"
        " --history-path data/scheduler_run_history.jsonl --sync-postgres-run-history"
        " --require-postgres-run-history-sync"
    ),
    "applylens-agent-discovery": (
        "/usr/bin/docker compose --env-file .env.production -f docker-compose.prod.yml"
        " exec -T web python -u -m src.pipeline.scheduler --job agent_discovery"
        " --history-path data/scheduler_run_history.jsonl --sync-postgres-run-history"
        " --require-postgres-run-history-sync"
    ),
    "applylens-postgres-backup": (
        "/home/deploy/apps/job-scraper/deploy/backup_postgres.sh"
    ),
}


def _unit_section(path: Path, section: str) -> dict[str, str]:
    """Parse one section of a systemd unit into exact key/value pairs."""
    parser = configparser.ConfigParser(strict=False, interpolation=None)
    parser.optionxform = str  # systemd directive names are case-sensitive
    parser.read_string(_read(path))
    return dict(parser[section])


@pytest.mark.parametrize(
    ("unit", "calendar"), sorted(TIMER_CALENDAR_CONTRACT.items())
)
def test_production_timers_use_only_the_exact_calendar_contract(unit, calendar):
    timer = SYSTEMD / f"{unit}.timer"
    section = _unit_section(timer, "Timer")

    assert section["OnCalendar"] == calendar
    assert section["Persistent"] == "true"
    assert section["Unit"] == f"{unit}.service"
    assert set(section) == {"OnCalendar", "Persistent", "Unit"}
    assert MONOTONIC_TIMER_DIRECTIVES.isdisjoint(section)


def test_no_production_timer_combines_activation_and_monotonic_recurrence():
    for unit in TIMER_CALENDAR_CONTRACT:
        section = _unit_section(SYSTEMD / f"{unit}.timer", "Timer")
        has_activation_leg = "OnActiveSec" in section
        has_monotonic_recurrence = bool(
            {"OnUnitActiveSec", "OnUnitInactiveSec"} & set(section)
        )
        assert not (has_activation_leg and has_monotonic_recurrence)
        assert MONOTONIC_TIMER_DIRECTIVES.isdisjoint(section)


def test_production_systemd_inventory_is_exact():
    assert {path.name for path in SYSTEMD.iterdir() if path.is_file()} == (
        EXPECTED_SYSTEMD_INVENTORY
    )


@pytest.mark.parametrize(("unit", "command"), sorted(EXPECTED_EXEC_START.items()))
def test_timer_repair_left_every_service_command_byte_exact(unit, command):
    section = _unit_section(SYSTEMD / f"{unit}.service", "Service")
    assert section["ExecStart"] == command
    assert section["Type"] == "oneshot"
    assert section["User"] == "deploy"
    assert section["WorkingDirectory"] == "/home/deploy/apps/job-scraper"


def test_runbook_documents_calendar_timer_transition_and_validation():
    runbook = _read(ROOT / "deploy" / "PRODUCTION_DEPLOYMENT.md")
    for calendar in TIMER_CALENDAR_CONTRACT.values():
        assert calendar in runbook
    for forbidden_directive in MONOTONIC_TIMER_DIRECTIVES:
        assert forbidden_directive in runbook
    for required_step in (
        "systemctl clean --what=state",
        "systemd-analyze verify",
        "systemd-analyze calendar",
        "systemctl daemon-reload",
        "TimersCalendar",
        "TimersMonotonic",
        "NextElapseUSecRealtime",
        "systemctl list-timers",
    ):
        assert required_step in runbook
    assert "Persistent=true" in runbook
    assert "maintenance window" in runbook
    assert "separately authorized" in runbook


def test_systemd_runtime_observer_units_are_bounded_and_do_not_start_workloads():
    service = _read(SYSTEMD / "applylens-scheduler-runtime-observation.service")
    timer = _read(SYSTEMD / "applylens-scheduler-runtime-observation.timer")
    assert "Type=oneshot" in service
    assert "User=deploy" in service
    assert "StateDirectory=applylens-scheduler-runtime" in service
    assert "NoNewPrivileges=true" in service
    assert "ProtectSystem=strict" in service
    assert (
        "ExecStart=/usr/bin/python3 /home/deploy/apps/job-scraper/"
        "deploy/write_systemd_scheduler_runtime_snapshot.py"
    ) in service
    assert "docker" not in service.lower()
    assert "network-online" not in service
    assert "OnUnitActiveSec=1min" in timer
    assert "Unit=applylens-scheduler-runtime-observation.service" in timer
    for workload in (
        "applylens-live-pipeline.service",
        "applylens-agent-discovery.service",
    ):
        assert workload not in timer


def test_systemd_runtime_observer_uses_exact_read_only_calls_and_contract(monkeypatch):
    module = _load_systemd_observer_module()
    calls = []
    real_popen = subprocess.Popen

    def fake_popen(command, **kwargs):
        calls.append((list(command), kwargs))
        unit = command[2]
        if unit.endswith(".timer"):
            output = (
                "LoadState=loaded\nActiveState=active\nSubState=waiting\n"
                "UnitFileState=enabled\n"
                "NextElapseUSecRealtime=Thu 2026-09-17 04:57:00 UTC\n"
            )
        elif "agent-discovery" in unit:
            output = (
                "ActiveState=failed\nSubState=failed\nResult=exit-code\n"
                "ExecMainStatus=1\n"
            )
        else:
            output = (
                "ActiveState=inactive\nSubState=dead\nResult=success\n"
                "ExecMainStatus=0\n"
            )
        return real_popen(
            [sys.executable, "-c", f"import os; os.write(1, {output.encode()!r})"],
            **kwargs,
        )

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    payload = module.collect_snapshot()

    assert payload["schema_version"] == module.SCHEMA_VERSION
    assert payload["runtime_provider"] == "systemd"
    assert payload["collection_ok"] is True
    assert [job["job_name"] for job in payload["jobs"]] == [
        "agent_discovery",
        "live_pipeline",
    ]
    assert len(calls) == 4
    assert [call[0][2] for call in calls] == [
        "applylens-agent-discovery.timer",
        "applylens-agent-discovery.service",
        "applylens-live-pipeline.timer",
        "applylens-live-pipeline.service",
    ]
    for command, kwargs in calls:
        assert command[:2] == ["/usr/bin/systemctl", "show"]
        assert command[3] == "--no-pager"
        assert command[4].startswith("--property=")
        assert kwargs["shell"] is False
        assert kwargs["stdout"] == subprocess.PIPE
        assert kwargs["stderr"] == subprocess.PIPE
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert module.COMMAND_TIMEOUT_SECONDS == 5
        assert kwargs["env"] == {
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
            "SYSTEMD_COLORS": "0",
            "SYSTEMD_PAGER": "cat",
            "TZ": "UTC",
        }
    serialized = json.dumps(payload)
    for forbidden in ("journal", "password", "credential", "DATABASE_URL"):
        assert forbidden not in serialized


def test_systemd_runtime_observer_rejects_unsupported_units_and_bad_output(monkeypatch):
    module = _load_systemd_observer_module()
    with pytest.raises(ValueError, match="unsupported systemd unit"):
        module._systemctl_show("synthetic.service", module.SERVICE_PROPERTIES)

    real_popen = subprocess.Popen

    def oversized_popen(command, **kwargs):
        return real_popen(
            [sys.executable, "-c", "import os; os.write(1, b'x' * 1048576)"],
            **kwargs,
        )

    monkeypatch.setattr(module.subprocess, "Popen", oversized_popen)
    with pytest.raises(RuntimeError, match="bounded limit"):
        module._systemctl_show(
            "applylens-live-pipeline.service",
            module.SERVICE_PROPERTIES,
        )


@pytest.mark.parametrize("stdout_size,stderr_size", [(0, 0), (16383, 0), (16384, 0), (8192, 8192), (0, 16384)])
def test_observer_capture_accepts_combined_byte_limit(monkeypatch, stdout_size, stderr_size):
    module = _load_systemd_observer_module()
    real_popen = subprocess.Popen
    children = []

    def fake_popen(command, **kwargs):
        child = real_popen(
            [sys.executable, "-c", f"import os; os.write(1, b'x'*{stdout_size}); os.write(2, b'y'*{stderr_size})"],
            **kwargs,
        )
        children.append(child)
        return child

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    code, stdout = module._run_bounded_systemctl([module.SYSTEMCTL, "show"])
    assert code == 0
    assert stdout == "x" * stdout_size
    assert children[0].stdout.closed and children[0].stderr.closed
    assert children[0].poll() == 0


@pytest.mark.parametrize("stdout_size,stderr_size", [(16385, 0), (0, 16385), (8192, 8193), (1048576, 0), (0, 1048576)])
def test_observer_capture_rejects_while_writer_is_live(monkeypatch, stdout_size, stderr_size):
    module = _load_systemd_observer_module()
    real_popen, real_read = subprocess.Popen, os.read
    children, read_sizes, requested_sizes, live_at_overflow = [], [], [], []

    def fake_popen(command, **kwargs):
        child = real_popen(
            [sys.executable, "-c", f"import os,time; os.write(1,b'x'*{stdout_size}); os.write(2,b'y'*{stderr_size}); time.sleep(30)"],
            **kwargs,
        )
        children.append(child)
        return child

    def tracked_read(fd, size):
        chunk = real_read(fd, size)
        # Popen also reads its private startup-error pipe; count only capture.
        if children and fd in {children[0].stdout.fileno(), children[0].stderr.fileno()}:
            requested_sizes.append(size)
            read_sizes.append(len(chunk))
            if sum(read_sizes) > module.MAX_COMMAND_OUTPUT_BYTES:
                live_at_overflow.append(children[0].poll() is None)
        return chunk

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(module.os, "read", tracked_read)
    with pytest.raises(RuntimeError, match="bounded limit"):
        module._run_bounded_systemctl([module.SYSTEMCTL, "show"])
    # Only the cap plus one sentinel byte ever reaches the collector, even
    # when the child attempts a MiB. Overflow is detected before child exit.
    assert sum(read_sizes) == module.MAX_COMMAND_OUTPUT_BYTES + 1
    assert max(requested_sizes) <= 4096
    assert live_at_overflow == [True]
    assert children[0].poll() is not None
    assert children[0].stdout.closed and children[0].stderr.closed


@pytest.mark.parametrize("ignore_terminate", [False, True])
def test_observer_timeout_reaps_child_with_bounded_kill_fallback(monkeypatch, ignore_terminate):
    module = _load_systemd_observer_module()
    real_popen = subprocess.Popen
    children, cleanup = [], []

    def fake_popen(command, **kwargs):
        child = real_popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
        terminate, kill, wait = child.terminate, child.kill, child.wait

        def tracked_terminate():
            cleanup.append("terminate")
            if not ignore_terminate:
                terminate()

        def tracked_kill():
            cleanup.append("kill")
            kill()

        def tracked_wait(*, timeout):
            assert timeout <= module.PROCESS_CLEANUP_TIMEOUT_SECONDS
            return wait(timeout=timeout)

        child.terminate, child.kill, child.wait = tracked_terminate, tracked_kill, tracked_wait
        children.append(child)
        return child

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(module, "COMMAND_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr(module, "PROCESS_CLEANUP_TIMEOUT_SECONDS", 0.1)
    with pytest.raises(subprocess.TimeoutExpired):
        module._run_bounded_systemctl([module.SYSTEMCTL, "show"])
    assert cleanup == (["terminate", "kill"] if ignore_terminate else ["terminate"])
    assert children[0].poll() is not None
    assert children[0].stdout.closed and children[0].stderr.closed


def test_systemd_runtime_observer_atomic_write_fsyncs_and_cleans_up(
    monkeypatch,
    tmp_path,
):
    module = _load_systemd_observer_module()
    output = tmp_path / "status.json"
    fsync_calls = []
    real_fsync = module.os.fsync

    def tracked_fsync(descriptor):
        fsync_calls.append(descriptor)
        return real_fsync(descriptor)

    monkeypatch.setattr(module.os, "fsync", tracked_fsync)
    payload = module.failed_snapshot()
    module.write_snapshot_atomic(payload, output)
    assert json.loads(output.read_text(encoding="utf-8")) == payload
    assert os.stat(output).st_mode & 0o777 == 0o644
    assert len(fsync_calls) == 2
    assert not list(tmp_path.glob(".status.json.*.tmp"))

    monkeypatch.setattr(
        module.os,
        "replace",
        lambda *_args: (_ for _ in ()).throw(OSError("replace failed")),
    )
    with pytest.raises(OSError, match="replace failed"):
        module.write_snapshot_atomic(payload, output)
    assert not list(tmp_path.glob(".status.json.*.tmp"))
