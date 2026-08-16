from __future__ import annotations

import importlib
import plistlib
import re
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import pytest

from src.pipeline import post_run_summary, scheduler
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


def test_global_acquisition_command_rejects_owner_downstream_options():
    with pytest.raises(ValueError, match="cannot be combined"):
        scheduler.build_live_pipeline_command(
            global_acquisition_only=True,
            run_application_planning=True,
        )

    command = scheduler.build_live_pipeline_command(
        global_acquisition_only=True,
        run_application_planning=False,
    )
    assert "--global-acquisition-only" in command
    assert "--skip-application-planning" in command
    assert "--run-application-planning" not in command


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
