from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from src.app import api, services
from src.pipeline import scheduler
from src.storage.scheduler import read_postgres


ADMIN_USER = {"user_id": "admin-1", "is_admin": True}
NON_ADMIN_USER = {"user_id": "user-1", "is_admin": False}


def _record_kwargs():
    return {
        "run_id": "sched_agent_discovery_test",
        "job_name": "agent_discovery",
        "job_description": "Discovery",
        "command": ["python", "run_agent_discovery.py"],
        "status": "succeeded",
        "started_at": "2026-08-16T01:00:00Z",
        "finished_at": "2026-08-16T01:05:00Z",
        "return_code": 0,
        "options": {},
    }


def _eligible_runtime(**overrides):
    return {
        "job_name": "agent_discovery",
        "installed": True,
        "loaded": True,
        "enabled": True,
        "armed": True,
        "running": False,
        "runtime_state": "idle",
        **overrides,
    }


class FakeProcess:
    def __init__(self, return_code=None):
        self.return_code = return_code
        self.pid = 43210
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.return_code

    def wait(self, timeout=None):
        return self.return_code

    def terminate(self):
        self.terminated = True
        self.return_code = -15

    def kill(self):
        self.killed = True
        self.return_code = -9


@pytest.fixture(autouse=True)
def reset_manual_process_state(monkeypatch, tmp_path):
    services._MANUAL_AGENT_DISCOVERY_STATE.update(
        {"process": None, "log_handle": None, "started_at": None}
    )
    monkeypatch.setattr(
        services,
        "_MANUAL_AGENT_DISCOVERY_LOG_PATH",
        tmp_path / "agent_discovery_manual.out.log",
    )
    yield
    state = services._MANUAL_AGENT_DISCOVERY_STATE
    handle = state.get("log_handle")
    if handle is not None:
        handle.close()
    state.update({"process": None, "log_handle": None, "started_at": None})


def _client_as(monkeypatch, user):
    def guard(request):
        if user is not None:
            request.state.auth_user = dict(user)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


def test_scheduler_trigger_source_is_bounded_and_default_is_historical():
    assert scheduler.build_scheduler_run_record(
        **_record_kwargs()
    )["trigger_source"] == "external_scheduler_wrapper"
    assert scheduler.build_scheduler_run_record(
        **_record_kwargs(),
        trigger_source="manual_admin",
    )["trigger_source"] == "manual_admin"
    with pytest.raises(ValueError, match="Unsupported scheduler trigger_source"):
        scheduler.build_scheduler_run_record(
            **_record_kwargs(),
            trigger_source="arbitrary",
        )


def test_manual_wrapper_reuses_canonical_scheduler_and_required_postgres_sync(
    monkeypatch,
):
    monkeypatch.setattr(
        services,
        "resolve_scheduler_psql_executable",
        lambda _value: "/opt/postgres/bin/psql",
    )
    scheduled = scheduler.build_scheduler_wrapper_command("agent_discovery")
    explicit_default = scheduler.build_scheduler_wrapper_command(
        "agent_discovery",
        trigger_source="external_scheduler_wrapper",
    )
    manual = services.build_manual_agent_discovery_wrapper_command()

    assert explicit_default == scheduled
    assert manual[:4] == [
        scheduler.sys.executable,
        "-u",
        "-m",
        "src.pipeline.scheduler",
    ]
    assert manual[manual.index("--job") + 1] == "agent_discovery"
    assert manual[manual.index("--trigger-source") + 1] == "manual_admin"
    assert "--sync-postgres-run-history" in manual
    assert "--require-postgres-run-history-sync" in manual
    assert manual[manual.index("--psql-bin") + 1] == "/opt/postgres/bin/psql"
    assert "--database-url" not in manual
    assert "DATABASE_URL" not in " ".join(manual)


def test_postgres_status_query_exposes_provenance_and_dedicated_scheduled_anchor():
    sql = read_postgres._build_scheduler_status_sql(25)
    assert sql.count("trigger_source") >= 4
    assert "latest_scheduled_runs_by_job" in sql
    assert "WHERE trigger_source = 'external_scheduler_wrapper'" in sql
    assert "LIMIT 25" in sql


def test_eligible_manual_start_spawns_one_safe_bounded_wrapper(monkeypatch):
    captured = {}
    process = FakeProcess()
    monkeypatch.setattr(
        services,
        "get_scheduler_runtime_job_status",
        lambda _job: _eligible_runtime(),
    )
    monkeypatch.setattr(
        services,
        "build_manual_agent_discovery_wrapper_command",
        lambda **_kwargs: [
            scheduler.sys.executable,
            "-m",
            "src.pipeline.scheduler",
            "--job",
            "agent_discovery",
            "--trigger-source",
            "manual_admin",
            "--sync-postgres-run-history",
            "--require-postgres-run-history-sync",
        ],
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://synthetic:secret@example/db")

    def fake_popen(command, **kwargs):
        captured["command"] = list(command)
        captured["kwargs"] = dict(kwargs)
        return process

    monkeypatch.setattr(services.subprocess, "Popen", fake_popen)

    payload = services.start_manual_agent_discovery_payload()

    assert payload == {
        "ok": True,
        "accepted": True,
        "job_name": "agent_discovery",
        "trigger_source": "manual_admin",
    }
    assert captured["kwargs"]["shell"] is False
    assert captured["kwargs"]["cwd"] == str(scheduler.REPO_ROOT)
    assert captured["kwargs"]["env"]["DATABASE_URL"].endswith("example/db")
    assert not any("synthetic" in part or "secret" in part for part in captured["command"])
    assert "process" not in payload and "pid" not in json.dumps(payload).lower()


@pytest.mark.parametrize(
    "runtime,category",
    [
        (_eligible_runtime(running=True, runtime_state="running"), "agent_discovery_already_running"),
        (_eligible_runtime(loaded=False, armed=False, runtime_state="unloaded"), "agent_discovery_runtime_unavailable"),
        (_eligible_runtime(enabled=None, armed=None, running=None, runtime_state="unavailable"), "agent_discovery_runtime_unavailable"),
    ],
)
def test_manual_start_fails_closed_for_active_or_unhealthy_launchd(
    monkeypatch,
    runtime,
    category,
):
    monkeypatch.setattr(
        services,
        "get_scheduler_runtime_job_status",
        lambda _job: runtime,
    )
    monkeypatch.setattr(
        services.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("ineligible request must not spawn"),
    )
    with pytest.raises(services.ManualAgentDiscoveryStartError) as exc_info:
        services.start_manual_agent_discovery_payload()
    assert exc_info.value.category == category


def test_active_app_owned_manual_process_returns_conflict_without_spawn(monkeypatch):
    services._MANUAL_AGENT_DISCOVERY_STATE["process"] = FakeProcess()
    monkeypatch.setattr(
        services.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("active request must not spawn"),
    )
    with pytest.raises(services.ManualAgentDiscoveryStartError) as exc_info:
        services.start_manual_agent_discovery_payload()
    assert exc_info.value.category == "agent_discovery_already_running"


def test_concurrent_manual_starts_serialize_to_one_popen(monkeypatch):
    process = FakeProcess()
    calls = []
    monkeypatch.setattr(
        services,
        "get_scheduler_runtime_job_status",
        lambda _job: _eligible_runtime(),
    )
    monkeypatch.setattr(
        services,
        "build_manual_agent_discovery_wrapper_command",
        lambda **_kwargs: [scheduler.sys.executable, "-m", "src.pipeline.scheduler"],
    )

    def fake_popen(*_args, **_kwargs):
        calls.append(True)
        return process

    monkeypatch.setattr(services.subprocess, "Popen", fake_popen)

    def attempt():
        try:
            return services.start_manual_agent_discovery_payload()["accepted"]
        except services.ManualAgentDiscoveryStartError as exc:
            return exc.category

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: attempt(), range(2)))

    assert calls == [True]
    assert sorted(str(result) for result in results) == [
        "True",
        "agent_discovery_already_running",
    ]


def test_manual_process_reconciles_and_shutdown_uses_tracked_process(monkeypatch):
    completed = FakeProcess(return_code=0)
    handle = (services._MANUAL_AGENT_DISCOVERY_LOG_PATH).open("a", encoding="utf-8")
    services._MANUAL_AGENT_DISCOVERY_STATE.update(
        {"process": completed, "log_handle": handle, "started_at": "2026-08-16T01:00:00Z"}
    )
    assert services.manual_agent_discovery_status_payload() == {
        "manual_run_active": False,
        "manual_run_started_at": None,
    }
    assert handle.closed is True

    running = FakeProcess()
    handle = (services._MANUAL_AGENT_DISCOVERY_LOG_PATH).open("a", encoding="utf-8")
    services._MANUAL_AGENT_DISCOVERY_STATE.update(
        {"process": running, "log_handle": handle, "started_at": "2026-08-16T02:00:00Z"}
    )
    monkeypatch.setattr(services.os, "killpg", lambda _pid, _signal: running.terminate())
    assert services.stop_manual_agent_discovery_for_server_shutdown() == {
        "ok": True,
        "stopped": True,
    }
    assert running.terminated is True
    assert handle.closed is True


def test_manual_discovery_endpoint_is_admin_only_and_agent_specific(monkeypatch):
    non_admin = _client_as(monkeypatch, NON_ADMIN_USER).post(
        "/scheduler/jobs/agent_discovery/run-now"
    )
    assert non_admin.status_code == 403
    assert non_admin.json() == {"detail": "Admin access required."}

    unauthenticated = _client_as(monkeypatch, None).post(
        "/scheduler/jobs/agent_discovery/run-now"
    )
    assert unauthenticated.status_code == 401
    assert unauthenticated.json() == {"detail": "Authentication required."}

    monkeypatch.setattr(
        services,
        "start_manual_agent_discovery_payload",
        lambda: {
            "ok": True,
            "accepted": True,
            "job_name": "agent_discovery",
            "trigger_source": "manual_admin",
        },
    )
    accepted = _client_as(monkeypatch, ADMIN_USER).post(
        "/scheduler/jobs/agent_discovery/run-now"
    )
    assert accepted.status_code == 202
    assert accepted.json() == {
        "ok": True,
        "accepted": True,
        "job_name": "agent_discovery",
        "trigger_source": "manual_admin",
    }
    assert _client_as(monkeypatch, ADMIN_USER).post(
        "/scheduler/jobs/live_pipeline/run-now"
    ).status_code == 404


def test_manual_discovery_endpoint_returns_bounded_conflict(monkeypatch):
    def conflict():
        raise services.ManualAgentDiscoveryStartError(
            "agent_discovery_already_running"
        )

    monkeypatch.setattr(services, "start_manual_agent_discovery_payload", conflict)
    response = _client_as(monkeypatch, ADMIN_USER).post(
        "/scheduler/jobs/agent_discovery/run-now"
    )
    assert response.status_code == 409
    assert response.json() == {
        "detail": {
            "ok": False,
            "error_category": "agent_discovery_already_running",
            "job_name": "agent_discovery",
        }
    }
    serialized = json.dumps(response.json()).lower()
    for forbidden in ("database_url", "password", "command", "environment", "pid"):
        assert forbidden not in serialized


def test_scheduler_schema_contract_remains_two_jobs_and_already_has_trigger_source():
    assert [row["name"] for row in scheduler.get_scheduled_job_definitions()] == [
        "agent_discovery",
        "live_pipeline",
    ]
    specs = services.scheduler_postgres_table_specs()
    run_columns = {
        column["name"] for column in specs["scheduler_run_history"]["columns"]
    }
    assert "trigger_source" in run_columns
