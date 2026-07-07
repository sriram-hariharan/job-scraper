from copy import deepcopy
from pathlib import Path

import pytest

from src.pipeline import collector


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS_FLAG = "APPLYLENS_AGENTIC_PIPELINE_ADVISORY_CHAIN_DIAGNOSTICS_ENABLED"
PERSISTENCE_FLAG = "APPLYLENS_AGENTIC_PIPELINE_ADVISORY_CHAIN_TRACE_PERSISTENCE_ENABLED"


def _env(**overrides):
    base = {
        DIAGNOSTICS_FLAG: "",
        PERSISTENCE_FLAG: "",
        "APPLYLENS_AGENT_TRACE_ENABLED": "",
        "APPLYLENS_AGENT_TRACE_STRICT": "",
        "JOB_APP_PIPELINE_RUN_ID": "phase82b_pipeline",
        "JOB_STACK_OWNER_USER_ID": "phase82b_owner",
        "APPLYLENS_AGENT_CONTEXT_ID": "phase82b_context",
    }
    base.update(overrides)
    return base


def _jobs():
    return [
        {
            "id": "job-phase82b",
            "title": "Machine Learning Engineer",
            "company": "Example AI",
            "application_priority_score": 0.93,
        },
        {
            "job_id": "job-phase82b-2",
            "title": "Backend Engineer",
            "company": "Example Cloud",
            "application_priority_score": 0.82,
        },
    ]


def _advisory_payload(**overrides):
    payload = {
        "validation": {"validation_status": "passed"},
        "trace_ready_advisory_result": {"trace_ready": True},
        "trace_persisted": False,
        "would_persist_trace": False,
        "did_call_trace_execution_helper": False,
        "did_call_llm": False,
        "did_call_live_provider": False,
        "did_call_workflow_runner": False,
        "did_submit_application": False,
        "did_click_apply": False,
        "did_mark_applied": False,
    }
    payload.update(overrides)
    return payload


def test_diagnostics_gate_off_skips_advisory_and_persistence_without_mutating_jobs():
    jobs = _jobs()
    before = deepcopy(jobs)
    calls = []

    def fail_if_called(**_kwargs):
        calls.append("called")
        raise AssertionError("disabled diagnostics must not call helpers")

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env=_env(
            **{
                DIAGNOSTICS_FLAG: "",
                PERSISTENCE_FLAG: "1",
                "APPLYLENS_AGENT_TRACE_ENABLED": "1",
            }
        ),
        advisory_chain_helper=fail_if_called,
        persistence_helper=fail_if_called,
        persistence_execute_callback=lambda operation: operation,
    )

    assert result is None
    assert calls == []
    assert jobs == before


def test_diagnostics_on_persistence_gate_off_runs_advisory_only():
    jobs = _jobs()
    before = deepcopy(jobs)
    persistence_calls = []

    def advisory(**_kwargs):
        return _advisory_payload()

    def fail_persistence(**kwargs):
        persistence_calls.append(kwargs)
        raise AssertionError("persistence gate off must not call persistence helper")

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env=_env(**{DIAGNOSTICS_FLAG: "1", PERSISTENCE_FLAG: ""}),
        advisory_chain_helper=advisory,
        persistence_helper=fail_persistence,
        persistence_execute_callback=lambda operation: operation,
    )

    assert result["validation"]["validation_status"] == "passed"
    assert result["advisory_chain_trace_persistence"]["reason"] == "trace_persistence_disabled"
    assert result["advisory_chain_trace_persistence"]["recorded"] is False
    assert persistence_calls == []
    assert jobs == before


def test_persistence_gate_on_trace_gate_off_does_not_call_persistence():
    jobs = _jobs()
    before = deepcopy(jobs)
    persistence_calls = []

    def advisory(**_kwargs):
        return _advisory_payload()

    def fail_persistence(**kwargs):
        persistence_calls.append(kwargs)
        raise AssertionError("trace gate off must not call persistence helper")

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env=_env(**{DIAGNOSTICS_FLAG: "1", PERSISTENCE_FLAG: "1", "APPLYLENS_AGENT_TRACE_ENABLED": ""}),
        advisory_chain_helper=advisory,
        persistence_helper=fail_persistence,
        persistence_execute_callback=lambda operation: operation,
    )

    assert result["advisory_chain_trace_persistence"]["reason"] == "trace_disabled"
    assert result["advisory_chain_trace_persistence"]["recorded"] is False
    assert persistence_calls == []
    assert jobs == before


def test_all_gates_on_with_executor_calls_persistence_once():
    jobs = _jobs()
    before = deepcopy(jobs)
    persistence_calls = []

    def advisory(**kwargs):
        assert kwargs["pipeline_run_id"] == "phase82b_pipeline"
        assert kwargs["owner_user_id"] == "phase82b_owner"
        assert kwargs["context_id"] == "phase82b_context"
        return _advisory_payload()

    def persistence(**kwargs):
        persistence_calls.append(kwargs)
        return {
            "attempted": True,
            "recorded": True,
            "reason": "",
            "trace_persistence_enabled": True,
            "trace_store_write_enabled": True,
            "did_call_trace_execution_helper": True,
            "did_write_database": True,
        }

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env=_env(
            **{
                DIAGNOSTICS_FLAG: "1",
                PERSISTENCE_FLAG: "1",
                "APPLYLENS_AGENT_TRACE_ENABLED": "1",
            }
        ),
        advisory_chain_helper=advisory,
        persistence_helper=persistence,
        persistence_execute_callback=lambda operation: operation,
    )

    assert result["advisory_chain_trace_persistence"]["recorded"] is True
    assert len(persistence_calls) == 1
    assert persistence_calls[0]["advisory_result"]["validation"]["validation_status"] == "passed"
    assert persistence_calls[0]["owner_user_id"] == "phase82b_owner"
    assert persistence_calls[0]["pipeline_run_id"] == "phase82b_pipeline"
    assert persistence_calls[0]["context_id"] == "phase82b_context"
    assert callable(persistence_calls[0]["execute_callback"])
    assert persistence_calls[0]["cursor"] is None
    assert jobs == before


def test_missing_context_skips_before_advisory_or_persistence():
    jobs = _jobs()
    before = deepcopy(jobs)
    calls = []

    def fail_if_called(**_kwargs):
        calls.append("called")
        raise AssertionError("missing context must skip helper calls")

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env={
            DIAGNOSTICS_FLAG: "1",
            PERSISTENCE_FLAG: "1",
            "APPLYLENS_AGENT_TRACE_ENABLED": "1",
        },
        advisory_chain_helper=fail_if_called,
        persistence_helper=fail_if_called,
        persistence_execute_callback=lambda operation: operation,
    )

    assert result["attempted"] is False
    assert result["reason"] == "missing_trace_context"
    assert calls == []
    assert jobs == before


def test_missing_executor_skips_persistence_with_write_executor_missing():
    jobs = _jobs()
    before = deepcopy(jobs)
    persistence_calls = []

    def advisory(**_kwargs):
        return _advisory_payload()

    def fail_persistence(**kwargs):
        persistence_calls.append(kwargs)
        raise AssertionError("missing executor must skip persistence helper")

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env=_env(
            **{
                DIAGNOSTICS_FLAG: "1",
                PERSISTENCE_FLAG: "1",
                "APPLYLENS_AGENT_TRACE_ENABLED": "1",
            }
        ),
        advisory_chain_helper=advisory,
        persistence_helper=fail_persistence,
    )

    assert result["advisory_chain_trace_persistence"]["reason"] == "write_executor_missing"
    assert result["advisory_chain_trace_persistence"]["recorded"] is False
    assert persistence_calls == []
    assert jobs == before


def test_persistence_failure_non_strict_is_warning_and_preserves_jobs():
    jobs = _jobs()
    before = deepcopy(jobs)

    def advisory(**_kwargs):
        return _advisory_payload()

    def fail_persistence(**_kwargs):
        raise RuntimeError("phase82b persistence unavailable")

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env=_env(
            **{
                DIAGNOSTICS_FLAG: "1",
                PERSISTENCE_FLAG: "1",
                "APPLYLENS_AGENT_TRACE_ENABLED": "1",
                "APPLYLENS_AGENT_TRACE_STRICT": "",
            }
        ),
        advisory_chain_helper=advisory,
        persistence_helper=fail_persistence,
        persistence_execute_callback=lambda operation: operation,
    )

    persistence = result["advisory_chain_trace_persistence"]
    assert persistence["attempted"] is True
    assert persistence["recorded"] is False
    assert persistence["reason"] == "trace_persistence_failed"
    assert "phase82b persistence unavailable" in persistence["warning"]
    assert jobs == before


def test_persistence_failure_strict_raises_after_preserving_jobs():
    jobs = _jobs()
    before = deepcopy(jobs)

    def advisory(**_kwargs):
        return _advisory_payload()

    def fail_persistence(**_kwargs):
        raise RuntimeError("phase82b strict persistence unavailable")

    with pytest.raises(RuntimeError, match="phase82b strict persistence unavailable"):
        collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
            jobs,
            env=_env(
                **{
                    DIAGNOSTICS_FLAG: "1",
                    PERSISTENCE_FLAG: "1",
                    "APPLYLENS_AGENT_TRACE_ENABLED": "1",
                    "APPLYLENS_AGENT_TRACE_STRICT": "1",
                }
            ),
            advisory_chain_helper=advisory,
            persistence_helper=fail_persistence,
            persistence_execute_callback=lambda operation: operation,
        )

    assert jobs == before


def test_collector_persistence_source_uses_helper_without_provider_api_or_apply_calls():
    source = (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")
    helper_start = source.index(
        "def _maybe_invoke_advisory_chain_diagnostics_after_application_priority"
    )
    helper_end = source.index("def log_market_insights", helper_start)
    helper_source = source[helper_start:helper_end]

    assert "persist_read_only_advisory_chain_trace" in helper_source
    assert "APPLYLENS_AGENTIC_PIPELINE_ADVISORY_CHAIN_TRACE_PERSISTENCE_ENABLED" in source
    for forbidden in [
        "execute_agent_trace_recording(",
        "agent_trace_payload(",
        "workflow_runner",
        "run_chat_completion",
        "submit_application(",
        "click_apply(",
        "mark_applied(",
        "src.app.api",
        "src.app.services",
        "LangGraph",
    ]:
        assert forbidden not in helper_source
