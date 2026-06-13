from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api


ENDPOINT = "/api/agentic-approvals/{approval_request_id}/critic-evaluator-readonly"
ALLOWED_FILES = [
    "src/app/api.py",
    "tests/test_critic_evaluator_readonly_api_action_no_storage_no_llm.py",
    "docs/critic_evaluator_readonly_api_action_no_storage_no_llm.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_agentic_docs.py",
]


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _valid_trace() -> dict:
    return {
        "agent_steps": [
            {
                "agent_step_id": "step-1",
                "step_index": 1,
                "safety_metadata": {"read_only": True},
                "output_summary": {
                    "validation_json": {"is_valid": True, "errors": []},
                    "separation": {
                        "prefilter_relevance": "separate",
                        "llm_evaluation": "not_called",
                        "final_application_scoring": "separate",
                    },
                },
            }
        ]
    }


def _assert_disabled_safety_flags(payload: dict) -> None:
    assert payload["did_write_storage"] is False
    assert payload["did_call_llm"] is False
    assert payload["did_mutate_approval"] is False
    assert payload["did_change_score"] is False
    assert payload["did_execute_application"] is False
    assert payload["did_submit_application"] is False


def test_critic_evaluator_readonly_route_exists_and_is_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_critic_evaluator_readonly_route_returns_evaluator_contract(monkeypatch):
    client = _client(monkeypatch)

    response = client.post(
        "/api/agentic-approvals/approval_1/critic-evaluator-readonly",
        json={"trace_payload": _valid_trace(), "trace_payload_source": "inline"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval_request_id"] == "approval_1"
    assert payload["trace_payload_source"] == "inline"
    assert payload["explicit_user_action"] is True
    assert payload["read_only"] is True
    assert payload["evaluator_status"] == "passed"
    assert payload["evaluator_findings"] == []
    assert payload["evaluator_warnings"] == []
    assert payload["evaluator_recommendations"] == ["no_follow_up_required"]
    assert payload["requires_human_review"] is False
    assert payload["deterministic_rubric_version"] == "critic-evaluator-rubric-v1"
    _assert_disabled_safety_flags(payload)


def test_critic_evaluator_readonly_route_is_deterministic(monkeypatch):
    client = _client(monkeypatch)
    request_body = {"trace_payload": _valid_trace(), "trace_payload_source": "inline"}

    first = client.post(
        "/api/agentic-approvals/approval_1/critic-evaluator-readonly",
        json=request_body,
    ).json()
    second = client.post(
        "/api/agentic-approvals/approval_1/critic-evaluator-readonly",
        json=request_body,
    ).json()

    assert first == second


def test_critic_evaluator_readonly_route_empty_trace_requires_human_review(monkeypatch):
    response = _client(monkeypatch).post(
        "/api/agentic-approvals/approval_1/critic-evaluator-readonly",
        json={"trace_payload": {"agent_steps": []}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluator_status"] == "needs_human_review"
    assert payload["requires_human_review"] is True
    assert "trace_completeness_empty_trace" in payload["evaluator_findings"]
    _assert_disabled_safety_flags(payload)


def test_critic_evaluator_readonly_route_slice_has_no_side_effect_markers():
    source = Path("src/app/api.py").read_text()
    helper_start = source.index("def _critic_evaluator_readonly_safety_flags")
    route_start = source.index(
        '@app.post("/api/agentic-approvals/{approval_request_id}/critic-evaluator-readonly")'
    )
    route_end = source.index(
        '@app.post(\n    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-reporting-job"'
    )
    snippet = source[helper_start:route_end] + source[route_start:route_end]

    forbidden_markers = [
        "FileResponse(",
        "StreamingResponse(",
        "open(",
        ".write(",
        "write_text",
        "write_bytes",
        "send_file",
        "subprocess",
        "background_tasks.add_task",
        "Thread(",
        "Process(",
        "get_agentic_approval_store",
        "_agentic_approval_storage_connection",
        "cursor.execute",
        ".commit(",
        "src.storage",
        "schema.sql",
        "migration_runner",
        "run_application_planning",
        "application_execution_queue",
        "submit_application(",
        "execute_application(",
        "score_applications",
        "ranking",
        "openai",
        "anthropic",
        "langchain",
        "langgraph",
        "model_provider",
        "llm_client",
    ]

    for marker in forbidden_markers:
        assert marker not in snippet


def test_critic_evaluator_readonly_action_does_not_touch_frontend_or_protected_files():
    for path in ALLOWED_FILES:
        assert Path(path).exists(), path

    forbidden_prefixes = (
        "src/app/static/",
        "src/storage/",
        "src/pipeline/",
        "src/agents/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes), path

    assert "critic-evaluator-readonly" not in Path(
        "src/app/static/agentic_review.js"
    ).read_text()
