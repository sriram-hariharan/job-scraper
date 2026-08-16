from __future__ import annotations

import importlib
import plistlib
import re
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import pytest

from src.pipeline import post_run_summary, scheduler
from src.storage import scheduler_artifacts_store
from src.storage.admin_tools.scheduler import sync_run_history


def _install_psql(monkeypatch, path="/opt/postgres/bin/psql"):
    monkeypatch.setattr(
        scheduler.shutil,
        "which",
        lambda name: path if name in {"psql", path} else None,
    )


def _plist(payload):
    return plistlib.loads(payload["plist_xml"].encode("utf-8"))


def test_supported_jobs_have_explicit_defaults_and_override_wins(monkeypatch):
    _install_psql(monkeypatch)
    definitions = {
        item["name"]: item for item in scheduler.get_scheduled_job_definitions()
    }

    assert set(definitions) == {"live_pipeline", "agent_discovery"}
    assert definitions["live_pipeline"]["launchd_interval_seconds"] == 21600
    assert definitions["agent_discovery"]["launchd_interval_seconds"] == 86400
    assert scheduler.build_scheduler_launchd_plist_payload(
        "agent_discovery",
        launchd_interval_seconds=12345,
    )["launchd_interval_seconds"] == 12345


@pytest.mark.parametrize(
    ("job_name", "expected_interval"),
    [("live_pipeline", 21600), ("agent_discovery", 86400)],
)
def test_launchd_plist_has_postgres_runtime_and_required_history_sync(
    monkeypatch,
    job_name,
    expected_interval,
):
    _install_psql(monkeypatch)
    payload = scheduler.build_scheduler_launchd_plist_payload(job_name)
    plist = _plist(payload)
    command = plist["ProgramArguments"]
    environment = plist["EnvironmentVariables"]

    assert plist["StartInterval"] == expected_interval
    assert "--sync-postgres-run-history" in command
    assert "--require-postgres-run-history-sync" in command
    assert command[command.index("--psql-bin") + 1] == "/opt/postgres/bin/psql"
    assert environment["PATH"].split(":")[0] == "/opt/postgres/bin"
    assert "DATABASE_URL" not in environment
    assert not any("password" in str(value).lower() for value in environment.values())
    if job_name == "live_pipeline":
        assert "--global-acquisition-only" in command
        assert "--skip-application-planning" in command
        assert "JOB_STACK_OWNER_USER_ID" not in environment
        assert "JOB_STACK_USER_PIPELINE_MODE" not in environment
    else:
        assert "--global-acquisition-only" not in command


def test_global_acquisition_command_rejects_owner_downstream_options(monkeypatch):
    with pytest.raises(ValueError, match="cannot be combined"):
        scheduler.build_live_pipeline_command(
            global_acquisition_only=True,
            run_application_planning=True,
        )
    with pytest.raises(ValueError, match="requires delete_seen_data='no'"):
        scheduler.build_live_pipeline_command(
            global_acquisition_only=True,
            delete_seen_data="yes",
        )

    command = scheduler.build_live_pipeline_command(
        global_acquisition_only=True,
        run_application_planning=False,
    )
    assert command.count("--delete-seen-data") == 1
    assert command[command.index("--delete-seen-data") + 1] == "no"
    assert "--global-acquisition-only" in command
    assert "--skip-application-planning" in command
    for forbidden_flag in (
        "--run-application-planning",
        "--application-planning-only",
        "--application-planning-generate-tailoring",
        "--application-planning-generate-llm-tailoring",
        "--application-planning-refresh-llm-tailoring",
        "--application-planning-generate-llm-fallback",
        "--application-planning-generate-llm-adjudication",
    ):
        assert forbidden_flag not in command

    import main as pipeline_main

    monkeypatch.setattr(sys, "argv", command[2:])
    parsed_args = pipeline_main._parse_args()
    pipeline_main._validate_application_planning_only_args(parsed_args)
    assert parsed_args.global_acquisition_only is True
    assert parsed_args.skip_application_planning is True
    assert parsed_args.delete_seen_data == "no"

    assert scheduler.build_scheduled_job_command("agent_discovery") == [
        sys.executable,
        "-u",
        "run_agent_discovery.py",
    ]


def test_direct_live_scheduler_default_is_always_global_acquisition_only(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["scheduler", "--job", "live_pipeline", "--print-only"],
    )

    assert scheduler.main() == 0
    command = capsys.readouterr().out.strip()

    assert command.count("--delete-seen-data") == 1
    assert "--delete-seen-data no" in command
    assert "--global-acquisition-only" in command
    assert "--run-application-planning" not in command
    assert "JOB_STACK_OWNER_USER_ID" not in command
    assert "JOB_STACK_USER_PIPELINE_MODE" not in command


def test_direct_live_scheduler_rejects_explicit_owner_downstream_flags(
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scheduler",
            "--job",
            "live_pipeline",
            "--planning-only",
            "--print-only",
        ],
    )

    with pytest.raises(SystemExit, match="global acquisition only"):
        scheduler.main()


def test_launchd_generation_fails_clearly_without_psql(monkeypatch):
    monkeypatch.setattr(scheduler.shutil, "which", lambda _name: None)

    with pytest.raises(ValueError, match="psql executable not found"):
        scheduler.build_scheduler_launchd_plist_payload("live_pipeline")


def test_launchd_generation_rejects_database_credentials(monkeypatch):
    _install_psql(monkeypatch)

    with pytest.raises(ValueError, match="Do not embed database_url"):
        scheduler.build_scheduler_launchd_plist_payload(
            "live_pipeline",
            database_url="postgresql://user:secret@example.invalid/database",
        )


def test_required_postgres_sync_cannot_exist_without_sync_enabled():
    with pytest.raises(ValueError, match="requires sync_postgres_run_history"):
        scheduler.build_scheduler_wrapper_command(
            "agent_discovery",
            sync_postgres_run_history=False,
            require_postgres_run_history_sync=True,
        )


def test_run_ids_include_normalized_job_and_microsecond_precision():
    first = scheduler._new_scheduler_run_id("agent-discovery")
    second = scheduler._new_scheduler_run_id("agent_discovery")

    assert re.fullmatch(r"sched_agent_discovery_\d{8}T\d{12}Z", first)
    assert first != second


def test_common_child_context_and_live_status_context_are_preserved(monkeypatch):
    monkeypatch.setenv("EXISTING_ENV", "preserved")
    discovery = scheduler._build_scheduled_child_env(
        "agent_discovery",
        run_id="sched_agent_discovery_exact",
        options={},
    )
    live = scheduler._build_scheduled_child_env(
        "live_pipeline",
        run_id="sched_live_pipeline_exact",
        options={"output_dir": "outputs/example"},
    )

    assert discovery["JOB_STACK_SCHEDULER_RUN_ID"] == "sched_agent_discovery_exact"
    assert discovery["JOB_STACK_SCHEDULER_JOB_NAME"] == "agent_discovery"
    assert "JOB_APP_PIPELINE_RUN_ID" not in discovery
    assert live["JOB_STACK_SCHEDULER_RUN_ID"] == "sched_live_pipeline_exact"
    assert live["JOB_STACK_SCHEDULER_JOB_NAME"] == "live_pipeline"
    assert live["JOB_APP_PIPELINE_RUN_ID"] == "sched_live_pipeline_exact"
    assert live["JOB_APP_PIPELINE_STATUS_PATH"].endswith(
        "outputs/example/live_pipeline_status.json"
    )
    assert live["EXISTING_ENV"] == "preserved"


@pytest.mark.parametrize(
    ("label", "output", "expected"),
    [
        (
            "com.jobstack.scheduler.agent.discovery",
            'disabled services = {\n\t"com.jobstack.scheduler.agent.discovery" => enabled\n}',
            True,
        ),
        (
            "com.jobstack.scheduler.live.pipeline",
            'disabled services = {\n\t"com.jobstack.scheduler.live.pipeline" => enabled\n}',
            True,
        ),
        (
            "com.jobstack.scheduler.live.pipeline",
            'disabled services = {\n\t"com.jobstack.scheduler.live.pipeline" => disabled\n}',
            False,
        ),
        (
            "com.jobstack.scheduler.live.pipeline",
            'disabled services = {\n\t"com.jobstack.scheduler.live.pipeline.planning.only" => disabled\n}',
            None,
        ),
    ],
)
def test_launchd_enabled_status_requires_exact_label(label, output, expected):
    assert scheduler._parse_launchctl_enabled_status(output, label) is expected


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        (
            "gui/501/example = {\n\tstate = not running\n\tservice = {\n\t\tstate = active\n\t}\n}",
            False,
        ),
        ("gui/501/example = {\n\tstate = running\n}", True),
        ("gui/501/example = {\n\tstate = waiting\n\tservice = {\n\t\tstate = running\n\t}\n}", None),
    ],
)
def test_launchd_running_status_uses_only_root_service_state(output, expected):
    assert scheduler._parse_launchctl_root_running_status(output) is expected


def test_launchd_runtime_status_is_read_only_and_deterministic(monkeypatch, tmp_path):
    plist_path = tmp_path / "com.jobstack.scheduler.live.pipeline.plist"
    plist_path.write_text("<plist/>", encoding="utf-8")
    commands = []
    monkeypatch.setattr(
        scheduler,
        "build_scheduler_launchd_agent_payload",
        lambda *_args, **_kwargs: {
            "label": "com.jobstack.scheduler.live.pipeline",
            "launchd_target": "gui/501",
            "installed_plist_path": str(plist_path),
            "print_command": [
                "launchctl",
                "print",
                "gui/501/com.jobstack.scheduler.live.pipeline",
            ],
        },
    )
    monkeypatch.setattr(scheduler.shutil, "which", lambda name: f"/bin/{name}")

    def fake_launchctl(cmd, *, check):
        commands.append(list(cmd))
        assert check is False
        if cmd[1] == "print":
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "gui/501/com.jobstack.scheduler.live.pipeline = {\n"
                    "\tstate = not running\n"
                    "\tservice = {\n"
                    "\t\tstate = active\n"
                    "\t}\n"
                    "}"
                ),
                stderr="",
            )
        return SimpleNamespace(
            returncode=0,
            stdout=(
                'disabled services = {\n'
                '\t"com.jobstack.scheduler.live.pipeline.planning.only" => disabled\n'
                '\t"com.jobstack.scheduler.live.pipeline" => enabled\n'
                '}'
            ),
            stderr="",
        )

    monkeypatch.setattr(scheduler, "_run_launchctl", fake_launchctl)

    status = scheduler.get_scheduler_launchd_agent_status("live_pipeline")

    assert commands == [
        ["launchctl", "print", "gui/501/com.jobstack.scheduler.live.pipeline"],
        ["launchctl", "print-disabled", "gui/501"],
    ]
    assert {command[1] for command in commands} == {"print", "print-disabled"}
    assert status["installed_plist_exists"] is True
    assert status["loaded"] is True
    assert status["enabled"] is True
    assert status["running"] is False
    assert status["runtime_state"] == "idle"


def test_launchd_runtime_status_keeps_failed_checks_unknown(monkeypatch, tmp_path):
    plist_path = tmp_path / "com.jobstack.scheduler.agent.discovery.plist"
    plist_path.write_text("<plist/>", encoding="utf-8")
    monkeypatch.setattr(
        scheduler,
        "build_scheduler_launchd_agent_payload",
        lambda *_args, **_kwargs: {
            "label": "com.jobstack.scheduler.agent.discovery",
            "launchd_target": "gui/501",
            "installed_plist_path": str(plist_path),
            "print_command": [
                "launchctl",
                "print",
                "gui/501/com.jobstack.scheduler.agent.discovery",
            ],
        },
    )
    monkeypatch.setattr(scheduler.shutil, "which", lambda name: f"/bin/{name}")

    def fake_launchctl(cmd, *, check):
        assert check is False
        return SimpleNamespace(returncode=1, stdout="", stderr="synthetic failure")

    monkeypatch.setattr(scheduler, "_run_launchctl", fake_launchctl)

    status = scheduler.get_scheduler_launchd_agent_status("agent_discovery")

    assert status["installed_plist_exists"] is True
    assert status["loaded"] is False
    assert status["enabled"] is None
    assert status["running"] is None
    assert status["runtime_state"] == "unloaded"


def test_scheduler_runtime_jobs_are_exact_bounded_and_truthful(monkeypatch):
    def fake_status(job_name, **_kwargs):
        if job_name == "agent_discovery":
            return {
                "launchctl_available": True,
                "installed_plist_exists": True,
                "loaded": True,
                "enabled": True,
                "running": False,
                "runtime_state": "idle",
                "print_stdout": "synthetic-secret-output",
                "print_stderr": "synthetic-password",
            }
        return {
            "launchctl_available": True,
            "installed_plist_exists": True,
            "loaded": False,
            "enabled": None,
            "running": False,
            "runtime_state": "unloaded",
            "print_stdout": "synthetic-secret-output",
            "print_stderr": "synthetic-password",
        }

    monkeypatch.setattr(scheduler, "get_scheduler_launchd_agent_status", fake_status)

    runtime_jobs = scheduler.get_scheduler_runtime_jobs_status()

    assert [job["job_name"] for job in runtime_jobs] == [
        "agent_discovery",
        "live_pipeline",
    ]
    assert [job["cadence_seconds"] for job in runtime_jobs] == [86400, 21600]
    assert runtime_jobs[0]["armed"] is True
    assert runtime_jobs[0]["runtime_state"] == "idle"
    assert runtime_jobs[1]["armed"] is False
    assert runtime_jobs[1]["runtime_state"] == "unloaded"
    assert set(runtime_jobs[0]) == {
        "job_name",
        "description",
        "cadence_seconds",
        "installed",
        "loaded",
        "enabled",
        "armed",
        "running",
        "runtime_state",
    }
    assert "synthetic-secret-output" not in repr(runtime_jobs)
    assert "synthetic-password" not in repr(runtime_jobs)


def test_scheduler_runtime_enabled_state_is_unknown_when_inspection_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(
        scheduler,
        "get_scheduler_launchd_agent_status",
        lambda *_args, **_kwargs: {
            "launchctl_available": False,
            "installed_plist_exists": True,
            "loaded": False,
            "enabled": None,
            "running": None,
            "runtime_state": "unavailable",
        },
    )

    runtime = scheduler.get_scheduler_runtime_job_status("live_pipeline")

    assert runtime["installed"] is True
    assert runtime["loaded"] is None
    assert runtime["enabled"] is None
    assert runtime["armed"] is None
    assert runtime["running"] is None
    assert runtime["runtime_state"] == "unavailable"


def test_required_postgres_history_failure_is_visible(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scheduler",
            "--job",
            "agent_discovery",
            "--history-path",
            str(tmp_path / "history.jsonl"),
            "--sync-postgres-run-history",
            "--require-postgres-run-history-sync",
        ],
    )
    monkeypatch.setattr(
        scheduler.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(
        scheduler,
        "write_post_run_summary_artifact",
        lambda _record: {},
    )
    monkeypatch.setattr(
        scheduler,
        "append_scheduler_run_record",
        lambda *_args, **_kwargs: tmp_path / "history.jsonl",
    )
    sync_module = ModuleType(
        "src.storage.admin_tools.scheduler.sync_run_history"
    )
    sync_module.insert_scheduler_run_history_row_to_postgres = (
        lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("postgres unavailable")
        )
    )
    monkeypatch.setitem(
        sys.modules,
        "src.storage.admin_tools.scheduler.sync_run_history",
        sync_module,
    )

    with pytest.raises(RuntimeError, match="postgres unavailable"):
        scheduler.main()


def test_postgres_sync_executes_raw_url_but_returns_redacted_command(
    monkeypatch,
    tmp_path,
):
    database_url = (
        "postgresql://scheduler-user:p%40ssword@example.invalid/scheduler"
    )
    captured = {}

    monkeypatch.setattr(
        sync_run_history.shutil,
        "which",
        lambda _name: "/opt/postgres/bin/psql",
    )

    def fake_run(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["kwargs"] = dict(kwargs)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(sync_run_history.subprocess, "run", fake_run)

    payload = sync_run_history._sync_normalized_rows_to_postgres(
        rows=[{"run_id": "synthetic-scheduler-run"}],
        history_path=tmp_path / "history.jsonl",
        database_url=database_url,
        psql_bin="/opt/postgres/bin/psql",
    )

    assert captured["cmd"][1] == database_url
    assert captured["cmd"][2:] == [
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-1",
        "-f",
        payload["sql_path"],
    ]
    assert captured["kwargs"] == {"check": True}
    assert payload["command"][1] == "[DATABASE_URL_REDACTED]"
    assert "[DATABASE_URL_REDACTED]" in payload["command_text"]
    for secret in (database_url, "scheduler-user", "p@ssword", "p%40ssword"):
        assert secret not in payload["command_text"]
        assert all(secret not in part for part in payload["command"])


def test_postgres_sync_failure_preserves_exception_with_redacted_command(
    monkeypatch,
    tmp_path,
):
    database_url = (
        "postgresql://scheduler-user:p%40ssword@example.invalid/scheduler"
    )

    monkeypatch.setattr(
        sync_run_history.shutil,
        "which",
        lambda _name: "/opt/postgres/bin/psql",
    )

    def fail_run(cmd, **_kwargs):
        raise subprocess.CalledProcessError(returncode=7, cmd=cmd)

    monkeypatch.setattr(sync_run_history.subprocess, "run", fail_run)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        sync_run_history._sync_normalized_rows_to_postgres(
            rows=[{"run_id": "synthetic-scheduler-run"}],
            history_path=tmp_path / "history.jsonl",
            database_url=database_url,
            psql_bin="/opt/postgres/bin/psql",
        )

    assert exc_info.value.returncode == 7
    assert exc_info.value.cmd[1] == "[DATABASE_URL_REDACTED]"
    rendered_error = repr(exc_info.value)
    for secret in (database_url, "scheduler-user", "p@ssword", "p%40ssword"):
        assert secret not in rendered_error


@pytest.mark.parametrize("operation", ["statement", "query"])
def test_scheduler_artifact_psql_executes_exact_database_url(
    monkeypatch,
    operation,
):
    database_url = (
        "postgresql://scheduler-user:p%40ssword@example.invalid/scheduler"
    )
    captured = {}
    monkeypatch.setenv("DATABASE_URL", database_url)

    def fake_run(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["kwargs"] = dict(kwargs)
        return SimpleNamespace(stdout='{"ok":true}\n', returncode=0)

    monkeypatch.setattr(scheduler_artifacts_store.subprocess, "run", fake_run)

    if operation == "statement":
        scheduler_artifacts_store._run_psql_statement("SELECT 1")
    else:
        assert scheduler_artifacts_store._run_psql_json_query("SELECT 1") == {
            "ok": True
        }

    assert captured["cmd"][1] == database_url
    assert "[DATABASE_URL_REDACTED]" not in captured["cmd"]
    assert captured["kwargs"] == {
        "check": True,
        "capture_output": True,
        "text": True,
    }


@pytest.mark.parametrize("operation", ["statement", "query"])
def test_scheduler_artifact_psql_failure_redacts_database_url(
    monkeypatch,
    operation,
):
    database_url = (
        "postgresql://scheduler-user:p%40ssword@example.invalid/scheduler"
    )
    captured = {}
    monkeypatch.setenv("DATABASE_URL", database_url)

    def fail_run(cmd, **_kwargs):
        captured["cmd"] = list(cmd)
        raise subprocess.CalledProcessError(returncode=9, cmd=cmd)

    monkeypatch.setattr(scheduler_artifacts_store.subprocess, "run", fail_run)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        if operation == "statement":
            scheduler_artifacts_store._run_psql_statement("SELECT 1")
        else:
            scheduler_artifacts_store._run_psql_json_query("SELECT 1")

    assert captured["cmd"][1] == database_url
    assert exc_info.value.returncode == 9
    assert exc_info.value.cmd[1] == "[DATABASE_URL_REDACTED]"
    rendered_failure = repr(exc_info.value)
    for secret in (database_url, "scheduler-user", "p@ssword", "p%40ssword"):
        assert all(secret not in part for part in exc_info.value.cmd)
        assert secret not in rendered_failure


def test_scheduler_stdout_redacts_postgres_sync_database_url(
    monkeypatch,
    tmp_path,
    capsys,
):
    database_url = (
        "postgresql://scheduler-user:p%40ssword@example.invalid/scheduler"
    )
    executed_commands = []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scheduler",
            "--job",
            "agent_discovery",
            "--history-path",
            str(tmp_path / "history.jsonl"),
            "--sync-postgres-run-history",
            "--require-postgres-run-history-sync",
            "--database-url",
            database_url,
            "--psql-bin",
            "/opt/postgres/bin/psql",
        ],
    )
    monkeypatch.setattr(
        sync_run_history.shutil,
        "which",
        lambda _name: "/opt/postgres/bin/psql",
    )
    monkeypatch.setattr(
        scheduler,
        "write_post_run_summary_artifact",
        lambda _record: {},
    )
    monkeypatch.setattr(
        scheduler,
        "append_scheduler_run_record",
        lambda *_args, **_kwargs: tmp_path / "history.jsonl",
    )

    def fake_run(cmd, **_kwargs):
        executed_commands.append(list(cmd))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(sync_run_history.subprocess, "run", fake_run)

    assert scheduler.main() == 0
    output = capsys.readouterr().out

    assert any(cmd[1] == database_url for cmd in executed_commands)
    assert "postgres_sync_command=" in output
    assert "[DATABASE_URL_REDACTED]" in output
    for secret in (database_url, "scheduler-user", "p@ssword", "p%40ssword"):
        assert secret not in output


def test_emit_and_write_paths_strip_agent_only_kwargs(monkeypatch, tmp_path, capsys):
    _install_psql(monkeypatch)
    captured = {}

    def fake_write(job_name, **kwargs):
        captured.update(kwargs)
        return {
            "label": f"test.{job_name}",
            "launchd_interval_seconds": 86400,
            "working_directory": str(tmp_path),
            "plist_path": str(tmp_path / "test.plist"),
            "stdout_log_path": str(tmp_path / "out.log"),
            "stderr_log_path": str(tmp_path / "err.log"),
            "command_text": "preview",
            "plist_xml": "<plist/>",
        }

    monkeypatch.setattr(scheduler, "write_scheduler_launchd_plist", fake_write)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scheduler",
            "--job",
            "agent_discovery",
            "--write-launchd-plist",
            "--launchd-agent-dir",
            str(tmp_path / "agents"),
            "--launchd-target",
            "gui/999",
        ],
    )

    assert scheduler.main() == 0
    assert "launchd_agent_dir" not in captured
    assert "launchd_target" not in captured
    assert "launchd_plist_written=true" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("job_name", "expected_interval"),
    [("live_pipeline", 21600), ("agent_discovery", 86400)],
)
def test_emit_plist_cli_is_preview_only_for_both_jobs(
    monkeypatch,
    capsys,
    job_name,
    expected_interval,
):
    _install_psql(monkeypatch)
    monkeypatch.setattr(
        scheduler,
        "_run_launchctl",
        lambda *_args, **_kwargs: pytest.fail("preview must not call launchctl"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["scheduler", "--job", job_name, "--emit-launchd-plist"],
    )

    assert scheduler.main() == 0
    output = capsys.readouterr().out
    assert f"launchd_interval_seconds={expected_interval}" in output
    assert "--sync-postgres-run-history" in output
    assert "--require-postgres-run-history-sync" in output


def _load_discovery_runner():
    return importlib.import_module("run_agent_discovery")


def test_scheduled_discovery_persists_exact_run_summary_and_skipped_is_success(
    monkeypatch,
):
    runner = _load_discovery_runner()
    captured = {}
    monkeypatch.setenv("JOB_STACK_SCHEDULER_RUN_ID", "sched_agent_discovery_exact")
    monkeypatch.setattr(
        runner,
        "run_company_discovery_agent",
        lambda: {
            "status": "skipped",
            "skip_reason": "tavily_api_key_not_configured",
            "queries_attempted": 0,
            "queries_failed": 0,
            "candidate_counts_by_ats": {},
            "total_candidate_count": 0,
        },
    )
    monkeypatch.setattr(
        runner,
        "run_discovery",
        lambda: {"run_unique_discovered_by_ats": {"greenhouse": 2}},
    )
    monkeypatch.setattr(
        runner,
        "_write_summary",
        lambda _payload: pytest.fail("scheduled discovery must not write local JSON"),
    )

    def fake_upsert(**kwargs):
        captured.update(kwargs)
        return {"artifact_ref": "postgres://scheduler_artifacts/exact/summary"}

    monkeypatch.setattr(runner, "upsert_scheduler_artifact", fake_upsert)

    assert runner.main() == 0
    assert captured["run_id"] == "sched_agent_discovery_exact"
    assert captured["job_name"] == "agent_discovery"
    assert captured["artifact_kind"] == "agent_discovery_summary"
    assert captured["payload_json"]["component_statuses"] == {
        "company_discovery_agent": "skipped",
        "discovery_stage": "succeeded",
    }
    assert captured["payload_json"]["status"] == "succeeded"


@pytest.mark.parametrize("failed_component", ["company", "stage"])
def test_scheduled_discovery_isolates_and_represents_component_exceptions(
    monkeypatch,
    failed_component,
):
    runner = _load_discovery_runner()
    captured = {}
    monkeypatch.setenv("JOB_STACK_SCHEDULER_RUN_ID", "sched_agent_discovery_failure")

    if failed_component == "company":
        monkeypatch.setattr(
            runner,
            "run_company_discovery_agent",
            lambda: (_ for _ in ()).throw(RuntimeError("company failure")),
        )
        monkeypatch.setattr(runner, "run_discovery", lambda: {"sources": {}})
        expected_component = "company_discovery_agent"
    else:
        monkeypatch.setattr(
            runner,
            "run_company_discovery_agent",
            lambda: {"status": "succeeded"},
        )
        monkeypatch.setattr(
            runner,
            "run_discovery",
            lambda: (_ for _ in ()).throw(RuntimeError("stage failure")),
        )
        expected_component = "discovery_stage"

    monkeypatch.setattr(
        runner,
        "upsert_scheduler_artifact",
        lambda **kwargs: captured.update(kwargs) or {"artifact_ref": "postgres://summary"},
    )

    with pytest.raises(RuntimeError, match="completed with failures"):
        runner.main()

    assert captured["payload_json"]["component_statuses"][expected_component] == "failed"
    assert expected_component in captured["payload_json"]["failure_components"]


def test_post_run_summary_reads_exact_postgres_discovery_artifact(monkeypatch):
    canonical = {
        "status": "succeeded",
        "return_code": 0,
        "summary_message": "canonical",
        "component_statuses": {
            "company_discovery_agent": "skipped",
            "discovery_stage": "succeeded",
        },
        "discovery_summary": {
            "sources": {"domain": {"greenhouse": 1}},
            "run_unique_discovered_by_ats": {"greenhouse": 1},
        },
    }
    calls = []
    monkeypatch.setattr(
        post_run_summary,
        "get_scheduler_artifact_payload",
        lambda **kwargs: calls.append(kwargs) or canonical,
    )
    monkeypatch.setattr(
        post_run_summary,
        "_read_json_artifact",
        lambda _path: pytest.fail("canonical Postgres artifact must win"),
    )

    payload = post_run_summary.build_post_run_summary_payload(
        {
            "job_name": "agent_discovery",
            "run_id": "sched_agent_discovery_exact",
            "status": "succeeded",
            "return_code": 0,
        }
    )

    assert calls == [{
        "run_id": "sched_agent_discovery_exact",
        "artifact_kind": "agent_discovery_summary",
    }]
    assert payload["artifact_path"] == (
        "postgres://scheduler_artifacts/sched_agent_discovery_exact/"
        "agent_discovery_summary"
    )
    assert payload["rollup_counts"] == {"greenhouse": 1}
