import inspect

from src.storage.agent_trace import store
from src.storage.agent_trace.store import (
    agent_trace_contract_health_payload,
    agent_trace_schema_sql_text,
    complete_agent_run_postgres_payload,
    complete_agent_step_postgres_payload,
    create_agent_run_postgres_payload,
    fail_agent_run_postgres_payload,
    fail_agent_step_postgres_payload,
    record_agent_step_postgres_payload,
)


def test_agent_trace_schema_contains_required_tables_and_columns():
    sql = agent_trace_schema_sql_text()

    assert "CREATE TABLE IF NOT EXISTS agent_runs" in sql
    assert "CREATE TABLE IF NOT EXISTS agent_steps" in sql
    for column in [
        "agent_run_id",
        "owner_user_id",
        "pipeline_run_id",
        "context_id",
        "summary_json",
        "agent_step_id",
        "agent_name",
        "input_json",
        "output_json",
        "validation_json",
        "latency_ms",
        "token_usage_json",
        "cost_json",
    ]:
        assert column in sql

    health = agent_trace_contract_health_payload()
    assert health["all_checks_pass"] is True


def test_create_agent_run_payload_preserves_json_summary_print_only():
    payload = create_agent_run_postgres_payload(
        record={
            "agent_run_id": "agent_run_1",
            "owner_user_id": "user_1",
            "pipeline_run_id": "pipeline_1",
            "context_id": "ctx_1",
            "started_at": "2026-05-29T12:00:00+00:00",
            "summary_json": {"jobs": 3, "stage": "prefilter"},
        },
        print_only=True,
        ensure_schema=False,
    )

    assert payload["ok"] is True
    assert payload["run"]["agent_run_id"] == "agent_run_1"
    assert payload["run"]["summary_json"] == {"jobs": 3, "stage": "prefilter"}
    assert "INSERT INTO agent_runs" in payload["sql"]
    assert "'{\"jobs\":3,\"stage\":\"prefilter\"}'::jsonb" in payload["sql"]


def test_runtime_query_runner_supports_dbapi_and_psql_fallback():
    source = inspect.getsource(store._run_postgres_json_query)

    assert "cursor.execute(sql)" in source
    assert "subprocess.run" in source
    assert "driver_name = \"psycopg\"" in source


def test_runtime_query_runner_falls_back_to_psql_when_dbapi_missing(monkeypatch):
    captured = {}

    class Completed:
        stdout = '{"ok":true,"rows":[]}\n'

    def fake_run(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["kwargs"] = dict(kwargs)
        return Completed()

    monkeypatch.setattr(store.shutil, "which", lambda value: f"/usr/bin/{value}")
    monkeypatch.setattr(store.subprocess, "run", fake_run)

    payload = store._run_postgres_json_query(
        sql="SELECT json_build_object('ok', true, 'rows', '[]'::json);",
        database_url="postgres://user:pass@example/db",
        print_only=False,
    )

    assert payload["driver"] == "psql"
    assert payload["data"] == {"ok": True, "rows": []}
    assert captured["cmd"][0] == "psql"
    assert captured["kwargs"]["input"].startswith("SELECT json_build_object")


def test_record_and_complete_agent_step_payloads_preserve_json_print_only():
    recorded = record_agent_step_postgres_payload(
        record={
            "agent_step_id": "agent_step_1",
            "agent_run_id": "agent_run_1",
            "owner_user_id": "user_1",
            "pipeline_run_id": "pipeline_1",
            "context_id": "ctx_1",
            "agent_name": "prefilter_agent",
            "agent_version": "v1",
            "input_json": {"job_id": "job_1"},
            "started_at": "2026-05-29T12:00:01+00:00",
        },
        print_only=True,
        ensure_schema=False,
    )
    completed = complete_agent_step_postgres_payload(
        agent_step_id="agent_step_1",
        owner_user_id="user_1",
        output_json={"decision": "pass"},
        validation_json={"valid": True},
        latency_ms=42,
        token_usage_json={"prompt_tokens": 0},
        cost_json={"usd": 0},
        completed_at="2026-05-29T12:00:02+00:00",
        print_only=True,
        ensure_schema=False,
    )

    assert recorded["ok"] is True
    assert recorded["step"]["input_json"] == {"job_id": "job_1"}
    assert "INSERT INTO agent_steps" in recorded["sql"]
    assert completed["ok"] is True
    assert completed["step"]["output_json"] == {"decision": "pass"}
    assert completed["step"]["validation_json"] == {"valid": True}
    assert "UPDATE agent_steps" in completed["sql"]
    assert "latency_ms = 42" in completed["sql"]


def test_failed_step_and_run_store_error_print_only():
    failed_step = fail_agent_step_postgres_payload(
        agent_step_id="agent_step_fail",
        owner_user_id="user_1",
        error="validation failed",
        validation_json={"valid": False},
        print_only=True,
        ensure_schema=False,
    )
    failed_run = fail_agent_run_postgres_payload(
        agent_run_id="agent_run_fail",
        owner_user_id="user_1",
        error="agent run failed",
        summary_json={"failed_step": "agent_step_fail"},
        print_only=True,
        ensure_schema=False,
    )

    assert failed_step["step"]["status"] == "failed"
    assert failed_step["step"]["error"] == "validation failed"
    assert "'validation failed'" in failed_step["sql"]
    assert failed_run["run"]["status"] == "failed"
    assert failed_run["run"]["error"] == "agent run failed"
    assert "'agent run failed'" in failed_run["sql"]


def test_complete_agent_run_payload_sets_succeeded_print_only():
    payload = complete_agent_run_postgres_payload(
        agent_run_id="agent_run_done",
        owner_user_id="user_1",
        summary_json={"steps": 2},
        completed_at="2026-05-29T12:00:03+00:00",
        print_only=True,
        ensure_schema=False,
    )

    assert payload["updated"] is True
    assert payload["run"]["status"] == "succeeded"
    assert payload["run"]["summary_json"] == {"steps": 2}
    assert "UPDATE agent_runs" in payload["sql"]


def test_create_agent_run_uses_runtime_query_runner_when_not_print_only(monkeypatch):
    captured = {}

    def fake_run_postgres_json_query(**kwargs):
        captured.update(kwargs)
        return {
            "data": {
                "created": True,
                "run": {
                    "agent_run_id": "agent_run_runtime",
                    "owner_user_id": "user_1",
                    "summary_json": {"runtime": True},
                },
            },
            "driver": "fake",
        }

    monkeypatch.setattr(store, "_run_postgres_json_query", fake_run_postgres_json_query)

    payload = store.create_agent_run_postgres_payload(
        record={
            "agent_run_id": "agent_run_runtime",
            "owner_user_id": "user_1",
            "summary_json": {"runtime": True},
        },
        print_only=False,
        ensure_schema=False,
    )

    assert payload["ok"] is True
    assert payload["run"]["agent_run_id"] == "agent_run_runtime"
    assert captured["print_only"] is False
    assert "INSERT INTO agent_runs" in captured["sql"]


def test_list_agent_steps_uses_runtime_query_runner_when_not_print_only(monkeypatch):
    captured = {}

    def fake_run_postgres_json_query(**kwargs):
        captured.update(kwargs)
        return {
            "data": {
                "rows": [
                    {
                        "agent_step_id": "agent_step_runtime",
                        "agent_run_id": "agent_run_runtime",
                    }
                ]
            }
        }

    monkeypatch.setattr(store, "_run_postgres_json_query", fake_run_postgres_json_query)

    payload = store.list_agent_steps_postgres_payload(
        owner_user_id="user_1",
        agent_run_id="agent_run_runtime",
        print_only=False,
        ensure_schema=False,
    )

    assert payload["ok"] is True
    assert payload["count"] == 1
    assert payload["steps"][0]["agent_step_id"] == "agent_step_runtime"
    assert captured["print_only"] is False
    assert "FROM agent_steps" in captured["sql"]


def test_agent_trace_list_helpers_support_context_filter_print_only():
    runs_payload = store.list_agent_runs_postgres_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        context_id="ctx_1",
        print_only=True,
        ensure_schema=False,
    )
    steps_payload = store.list_agent_steps_postgres_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        context_id="ctx_1",
        print_only=True,
        ensure_schema=False,
    )

    assert "AND context_id = 'ctx_1'" in runs_payload["sql"]
    assert "AND context_id = 'ctx_1'" in steps_payload["sql"]
