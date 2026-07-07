from copy import deepcopy
from pathlib import Path

from src.pipeline import collector


ROOT = Path(__file__).resolve().parents[1]
FLAG = "APPLYLENS_AGENTIC_PIPELINE_ADVISORY_CHAIN_DIAGNOSTICS_ENABLED"


def _env(**overrides):
    base = {
        FLAG: "",
        "JOB_APP_PIPELINE_RUN_ID": "phase81d_pipeline",
        "JOB_STACK_OWNER_USER_ID": "phase81d_owner",
        "APPLYLENS_AGENT_CONTEXT_ID": "",
        "APPLYLENS_AGENT_TRACE_ENABLED": "1",
    }
    base.update(overrides)
    return base


def _jobs():
    return [
        {
            "id": "job-phase81d",
            "title": "Machine Learning Engineer",
            "company": "Example AI",
            "application_priority_score": 0.93,
        },
        {
            "job_id": "job-phase81d-2",
            "title": "Backend Engineer",
            "company": "Example Cloud",
            "application_priority_score": 0.82,
        },
    ]


def test_gate_off_does_not_call_advisory_helper_or_mutate_jobs():
    jobs = _jobs()
    before = deepcopy(jobs)
    calls = []

    def fail_if_called(**_kwargs):
        calls.append("called")
        raise AssertionError("default-off diagnostics must not call helper")

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env=_env(**{FLAG: ""}),
        advisory_chain_helper=fail_if_called,
    )

    assert result is None
    assert calls == []
    assert jobs == before


def test_gate_on_calls_advisory_helper_with_copied_summary_only():
    jobs = _jobs()
    before = deepcopy(jobs)
    captured = {}

    def fake_helper(**kwargs):
        captured.update(kwargs)
        kwargs["input_summary"]["first_job"]["title"] = "mutated in fake helper"
        return {
            "validation": {"validation_status": "passed"},
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

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env=_env(**{FLAG: "1"}),
        advisory_chain_helper=fake_helper,
    )

    assert result["validation"]["validation_status"] == "passed"
    assert captured["pipeline_run_id"] == "phase81d_pipeline"
    assert captured["owner_user_id"] == "phase81d_owner"
    assert captured["context_id"] == "advisory_chain:phase81d_pipeline"
    assert captured["input_summary"] == {
        "stage_name": "post_application_priority",
        "source_stage": "application_priority",
        "scored_job_count": 2,
        "first_job": {
            "id": "job-phase81d",
            "title": "mutated in fake helper",
            "company": "Example AI",
        },
    }
    assert captured["env"][FLAG] == "1"
    assert jobs == before


def test_gate_on_with_missing_ids_skips_non_blocking_without_calling_helper():
    jobs = _jobs()
    before = deepcopy(jobs)
    calls = []

    def fail_if_called(**_kwargs):
        calls.append("called")
        raise AssertionError("missing context must skip before helper call")

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env={
            FLAG: "1",
            "APPLYLENS_AGENT_TRACE_ENABLED": "1",
        },
        advisory_chain_helper=fail_if_called,
    )

    assert result["attempted"] is False
    assert result["reason"] == "missing_trace_context"
    assert result["owner_user_id"] == ""
    assert result["pipeline_run_id"] == ""
    assert calls == []
    assert jobs == before


def test_advisory_helper_failure_is_non_blocking_and_preserves_jobs():
    jobs = _jobs()
    before = deepcopy(jobs)

    def fail_helper(**_kwargs):
        raise RuntimeError("diagnostics helper unavailable")

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        env=_env(**{FLAG: "1"}),
        advisory_chain_helper=fail_helper,
    )

    assert result["attempted"] is True
    assert result["recorded"] is False
    assert result["reason"] == "advisory_chain_diagnostics_failed"
    assert "diagnostics helper unavailable" in result["warning"]
    assert jobs == before


def test_explicit_disabled_override_does_not_call_helper_even_when_env_enabled():
    jobs = _jobs()
    before = deepcopy(jobs)
    calls = []

    def fail_if_called(**_kwargs):
        calls.append("called")
        raise AssertionError("explicit disabled override must not call helper")

    result = collector._maybe_invoke_advisory_chain_diagnostics_after_application_priority(
        jobs,
        enabled=False,
        env=_env(**{FLAG: "1"}),
        advisory_chain_helper=fail_if_called,
    )

    assert result is None
    assert calls == []
    assert jobs == before


def test_call_site_is_after_vector_and_shadow_sidecars_before_source_health():
    source = (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")
    complete_marker = (
        'complete_stage("application_priority", counts={"scored_jobs": len(scored_jobs)})'
    )
    vector_marker = "_maybe_collect_vector_evidence_after_application_priority(scored_jobs)"
    shadow_marker = "_maybe_run_shadow_sidecar_after_application_priority("
    advisory_marker = (
        "_maybe_invoke_advisory_chain_diagnostics_after_application_priority(scored_jobs)"
    )
    source_health_marker = "if role_title_audit_rows is not None:"

    assert source.count(advisory_marker) == 1
    assert (
        source.index(complete_marker)
        < source.index(vector_marker)
        < source.index(shadow_marker, source.index(vector_marker))
        < source.index(advisory_marker, source.index(shadow_marker))
        < source.index(source_health_marker, source.index(advisory_marker))
    )
    assert f"= {advisory_marker}" not in source
    assert f"{advisory_marker}." not in source


def test_collector_diagnostics_source_has_no_raw_trace_provider_api_or_apply_calls():
    source = (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")
    helper_start = source.index(
        "def _maybe_invoke_advisory_chain_diagnostics_after_application_priority"
    )
    helper_end = source.index("def log_market_insights", helper_start)
    helper_source = source[helper_start:helper_end]

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
