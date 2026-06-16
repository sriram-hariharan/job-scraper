import inspect
from hashlib import sha256
from pathlib import Path

from src.app import api
from src.storage.agent_state import store


EXPECTED_PROTECTED_HASHES = {
    "src/app/static/agentic_review.js": "e397571900ea459096fae33f4c40ebe12cdf2f79233ce6ee3ee17340427abb5d",
    "src/storage/agent_state/schema.sql": "d7e91c2b7e6e7720a8aeb64b7292d9ce28d6008b14c1d149f56a6c1fa39b3526",
    "src/storage/agent_state/migration_runner.py": "488e25670d7043c6a5b938441e13d7c066bbcf5fccda1a41401723650e61969e",
}

SAFETY_METADATA = {
    "read_only": True,
    "did_create_agent_run": False,
    "did_create_agent_step": False,
    "did_mutate_approval": False,
    "did_execute_pipeline": False,
    "did_schedule_background_work": False,
    "did_execute_scheduler": False,
    "did_export_files": False,
    "did_execute_application": False,
    "did_submit_application": False,
    "did_call_llm_provider": False,
    "did_create_connection": False,
    "did_commit_transaction": False,
    "did_run_migration": False,
    "ui_action_added": False,
    "pipeline_wiring_added": False,
}


def _hash(path: str) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def test_agent_trace_readonly_endpoint_is_registered_get_only():
    route = next(
        route
        for route in api.app.routes
        if getattr(route, "path", "")
        == "/api/agentic-approvals/{approval_request_id}/agent-trace"
    )

    assert route.methods == {"GET"}


def test_not_found_trace_response_is_stable_and_safe(monkeypatch):
    monkeypatch.setattr(api, "_agent_trace_readonly_storage_connection", lambda: None)

    first = api.get_agentic_approval_agent_trace("approval_missing")
    second = api.get_agentic_approval_agent_trace("approval_missing")

    assert first == second
    assert first == {
        "approval_request_id": "approval_missing",
        "agent_run_id": "",
        "found": False,
        "agent_run": {},
        "agent_steps": [],
        "step_count": 0,
        "empty_trace": True,
        "safety_metadata": SAFETY_METADATA,
    }


def test_run_with_zero_steps_is_empty_trace_but_found(monkeypatch):
    monkeypatch.setattr(api, "_agent_trace_readonly_storage_connection", lambda: object())
    monkeypatch.setattr(
        api,
        "_read_agent_trace_for_approval",
        lambda **kwargs: {
            "agent_run": {
                "agent_run_id": "agent_run_1",
                "approval_request_id": "approval_1",
                "agent_name": "final_application_scoring_agent",
                "run_status": "completed",
            },
            "agent_steps": [],
        },
    )

    payload = api.get_agentic_approval_agent_trace(
        "approval_1",
        agent_run_id="agent_run_1",
    )

    assert payload["found"] is True
    assert payload["agent_run"]["agent_run_id"] == "agent_run_1"
    assert payload["agent_steps"] == []
    assert payload["step_count"] == 0
    assert payload["empty_trace"] is True
    assert payload["safety_metadata"] == SAFETY_METADATA


def test_trace_steps_are_ordered_deterministically(monkeypatch):
    monkeypatch.setattr(api, "_agent_trace_readonly_storage_connection", lambda: object())
    monkeypatch.setattr(
        api,
        "_read_agent_trace_for_approval",
        lambda **kwargs: {
            "agent_run": {"agent_run_id": "agent_run_1"},
            "agent_steps": [
                {
                    "agent_step_id": "step_c",
                    "step_index": 2,
                    "observed_at_utc": "2026-06-12T10:02:00Z",
                },
                {
                    "agent_step_id": "step_b",
                    "step_index": 1,
                    "observed_at_utc": "2026-06-12T10:02:00Z",
                },
                {
                    "agent_step_id": "step_a",
                    "step_index": 1,
                    "observed_at_utc": "2026-06-12T10:01:00Z",
                },
            ],
        },
    )

    payload = api.get_agentic_approval_agent_trace("approval_1")

    assert [step["agent_step_id"] for step in payload["agent_steps"]] == [
        "step_a",
        "step_b",
        "step_c",
    ]
    assert payload["step_count"] == 3
    assert payload["empty_trace"] is False


def test_storage_read_helpers_prepare_select_only_queries():
    run_query = store.prepare_agent_run_select(
        approval_request_id="approval_1",
        agent_run_id="agent_run_1",
    )
    steps_query = store.prepare_agent_steps_select_for_run(
        agent_run_id="agent_run_1",
    )

    assert run_query["read_only"] is True
    assert steps_query["read_only"] is True
    assert run_query["params"] == ("approval_1", "agent_run_1")
    assert steps_query["params"] == ("agent_run_1",)
    for query in (run_query, steps_query):
        sql_upper = query["sql"].upper()
        assert "SELECT " in sql_upper
        for forbidden in ("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"):
            assert forbidden not in sql_upper
        assert query["did_create_connection"] is False
        assert query["did_commit_transaction"] is False
        assert query["did_run_migration"] is False


def test_readonly_endpoint_source_has_no_runtime_side_effect_markers():
    runtime_source = "\n".join(
        inspect.getsource(value)
        for value in (
            api._agent_trace_readonly_payload,
            api._read_agent_trace_for_approval,
            api.get_agentic_approval_agent_trace,
            api._agent_trace_readonly_storage_connection,
        )
    )

    forbidden_tokens = [
        "FileResponse",
        "StreamingResponse",
        "open(",
        "write(",
        "write_text",
        "write_bytes",
        "send_file",
        "subprocess",
        "background_tasks.add_task",
        "Thread",
        "Process",
        ".commit(",
        "connect(",
        "run_migration(",
        "INSERT INTO",
        "UPDATE ",
        "DELETE ",
        "CREATE TABLE",
        "DROP ",
        "ALTER ",
        "scheduler_execution(",
        "reporting_job_execution(",
        "application_execution(",
        "application_submission(",
        "export_writer",
        "run_llm",
        "model_client",
        "workflow_runner",
        "application_execution_queue",
    ]
    for token in forbidden_tokens:
        assert token not in runtime_source


def test_no_frontend_schema_or_migration_file_changed():
    later_readonly_ui_step_exists = Path("docs/agent_trace_readonly_ui_panel_no_api_no_writes.md").exists()
    later_readonly_ui_paths = {
        "src/app/static/agentic_review.js",
    }

    for path, expected_hash in EXPECTED_PROTECTED_HASHES.items():
        assert Path(path).exists()
        if later_readonly_ui_step_exists and path in later_readonly_ui_paths:
            continue
        assert _hash(path) == expected_hash
