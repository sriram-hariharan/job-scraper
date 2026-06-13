from copy import deepcopy

import pytest

from src.storage.agent_trace.store import build_agent_trace_summary_payload


def _run(**overrides):
    row = {
        "agent_run_id": "agent_run_1",
        "owner_user_id": "user_1",
        "pipeline_run_id": "pipeline_1",
        "context_id": "context_1",
        "status": "succeeded",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:02Z",
        "summary_json": {},
        "error": "",
    }
    row.update(overrides)
    return row


def _step(**overrides):
    row = {
        "agent_step_id": "agent_step_1",
        "agent_run_id": "agent_run_1",
        "owner_user_id": "user_1",
        "pipeline_run_id": "pipeline_1",
        "context_id": "context_1",
        "agent_name": "resume_match",
        "agent_version": "v1",
        "input_json": {},
        "output_json": {},
        "validation_json": {},
        "status": "succeeded",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:01Z",
        "latency_ms": 100,
        "model_provider": "openai",
        "model_name": "test-model",
        "token_usage_json": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        "cost_json": {"estimated_cost_usd": 0.001},
        "error": "",
    }
    row.update(overrides)
    return row


def test_trace_summary_helper_is_deterministic_and_does_not_mutate_inputs():
    runs = [_run()]
    steps = [
        _step(),
        _step(
            agent_step_id="agent_step_2",
            agent_name="critic",
            status="failed",
            error="schema validation failed",
            latency_ms=300,
            token_usage_json={"input_tokens": 4, "output_tokens": 1, "total_tokens": 5},
            cost_json={"estimated_cost_usd": 0.002},
        ),
    ]
    original_runs = deepcopy(runs)
    original_steps = deepcopy(steps)

    first = build_agent_trace_summary_payload(agent_runs=runs, agent_steps=steps)
    second = build_agent_trace_summary_payload(agent_runs=runs, agent_steps=steps)

    assert first == second
    assert runs == original_runs
    assert steps == original_steps


def test_trace_summary_helper_counts_status_agents_latency_tokens_and_costs():
    payload = build_agent_trace_summary_payload(
        agent_runs=[_run(), _run(agent_run_id="agent_run_2", status="failed")],
        agent_steps=[
            _step(),
            _step(
                agent_step_id="agent_step_2",
                agent_name="critic",
                status="failed",
                error="invalid output",
                latency_ms=250,
                token_usage_json={"input_tokens": 2, "output_tokens": 3, "total_tokens": 5},
                cost_json={"estimated_cost_usd": 0.004},
            ),
            _step(
                agent_step_id="agent_step_3",
                agent_name="critic",
                status="warning",
                latency_ms=None,
                model_provider="",
                model_name="",
                token_usage_json={},
                cost_json={},
            ),
        ],
    )

    assert payload["run_count"] == 2
    assert payload["step_count"] == 3
    assert payload["completed_step_count"] == 3
    assert payload["error_step_count"] == 1
    assert payload["warning_step_count"] == 1
    assert payload["run_status_counts"] == {"failed": 1, "succeeded": 1}
    assert payload["step_status_counts"] == {
        "failed": 1,
        "succeeded": 1,
        "warning": 1,
    }
    assert payload["agent_counts"] == {"critic": 2, "resume_match": 1}
    assert payload["latency_summary"] == {
        "count": 2,
        "total_ms": 350,
        "min_ms": 100,
        "max_ms": 250,
        "average_ms": 175.0,
    }
    assert payload["token_usage_summary"] == {
        "input_tokens": 12,
        "output_tokens": 8,
        "total_tokens": 20,
    }
    assert payload["cost_summary"] == {"estimated_cost_usd": 0.005}
    assert payload["model_usage_summary"] == {
        "provider_counts": {"openai": 2},
        "model_counts": {"openai/test-model": 2},
    }


def test_trace_summary_helper_reports_missing_required_fields():
    payload = build_agent_trace_summary_payload(
        agent_runs=[_run(agent_run_id="")],
        agent_steps=[_step(agent_step_id="", agent_name="")],
    )

    assert payload["all_required_fields_present"] is False
    assert payload["missing_required_fields"]["agent_runs"] == [
        {
            "index": 0,
            "agent_run_id": "",
            "missing_fields": ["agent_run_id"],
        }
    ]
    assert payload["missing_required_fields"]["agent_steps"] == [
        {
            "index": 0,
            "agent_step_id": "",
            "missing_fields": ["agent_step_id", "agent_name"],
        }
    ]


def test_trace_summary_helper_has_read_only_safety_metadata():
    payload = build_agent_trace_summary_payload(agent_runs=[], agent_steps=[])

    assert payload["ok"] is True
    assert payload["summary_type"] == "agent_trace"
    assert payload["safety_metadata"] == {
        "did_read_database": False,
        "did_write_database": False,
        "did_create_agent_run": False,
        "did_create_agent_step": False,
        "did_update_agent_run": False,
        "did_update_agent_step": False,
        "did_call_llm": False,
        "did_change_pipeline": False,
        "did_change_scoring": False,
        "did_change_approval": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }


def test_trace_summary_helper_rejects_non_list_rows():
    with pytest.raises(ValueError):
        build_agent_trace_summary_payload(agent_runs={"bad": "row"}, agent_steps=[])

    with pytest.raises(ValueError):
        build_agent_trace_summary_payload(agent_runs=[], agent_steps={"bad": "row"})
