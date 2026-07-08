from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from src.agents import jd_intelligence
from src.pipeline import collector
from tests.support.phase_guard_registry import assert_no_forbidden_runtime_calls_ast


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_ENABLED"
)
PERSISTENCE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_EXISTING_OUTPUT_TRACE_PERSISTENCE_ENABLED"
)


def _env(**overrides):
    base = {
        DIAGNOSTICS_FLAG: "",
        PERSISTENCE_FLAG: "",
        "APPLYLENS_AGENT_TRACE_ENABLED": "",
        "APPLYLENS_AGENT_TRACE_STRICT": "",
        "JOB_APP_PIPELINE_RUN_ID": "phase88b_pipeline",
        "JOB_STACK_OWNER_USER_ID": "phase88b_owner",
        "APPLYLENS_AGENT_CONTEXT_ID": "phase88b_context",
    }
    base.update(overrides)
    return base


def _already_intelligent_job(index: int = 1) -> dict:
    return {
        "job_id": f"job-88b-{index}",
        "title": f"Analytics Engineer {index}",
        "company": "Example Data",
        "intelligence": {
            "skills": {
                "required": ["python", "sql"],
                "preferred": ["airflow"],
                "all": ["python", "sql", "airflow"],
            },
            "visa_sponsorship": "unknown",
        },
    }


def _diagnostics_payload() -> dict:
    return jd_intelligence.build_existing_job_intelligence_trace_payload(
        [_already_intelligent_job(1), _already_intelligent_job(2)],
        sample_limit=1,
    )


def _collector_helper_source() -> str:
    source = (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name
            == "_maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence"
        ):
            return ast.get_source_segment(source, node) or ""
    raise AssertionError("collector JD diagnostics helper not found")


def test_all_gates_off_skips_diagnostics_and_persistence_without_mutation():
    jobs = [_already_intelligent_job()]
    before = deepcopy(jobs)

    def fail_builder(*_args, **_kwargs):
        raise AssertionError("diagnostics builder must not be called")

    result = collector._maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        jobs,
        env=_env(),
        payload_builder=fail_builder,
        persistence_helper=fail_builder,
        persistence_execute_callback=lambda operation: operation,
    )

    assert result is None
    assert jobs == before


def test_diagnostics_on_persistence_off_builds_payload_only():
    jobs = [_already_intelligent_job(1), _already_intelligent_job(2)]
    before = deepcopy(jobs)

    def fail_persistence(**_kwargs):
        raise AssertionError("persistence helper must not be called")

    payload = collector._maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        jobs,
        env=_env(**{DIAGNOSTICS_FLAG: "1", PERSISTENCE_FLAG: ""}),
        persistence_helper=fail_persistence,
        persistence_execute_callback=lambda operation: operation,
    )

    assert payload["stage_name"] == "jd_intelligence_existing_output"
    assert payload["trace_persistence_requested"] is False
    assert payload["trace_persistence_performed"] is False
    assert payload["jd_intelligence_existing_output_trace_persistence"]["reason"] == (
        "trace_persistence_disabled"
    )
    assert jobs == before


def test_persistence_gate_on_trace_gate_off_does_not_call_write_helper():
    calls = []

    def fail_persistence(**kwargs):
        calls.append(kwargs)
        raise AssertionError("trace-disabled path must not call persistence helper")

    payload = collector._maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        [_already_intelligent_job()],
        env=_env(**{DIAGNOSTICS_FLAG: "1", PERSISTENCE_FLAG: "1"}),
        persistence_helper=fail_persistence,
        persistence_execute_callback=lambda operation: operation,
    )

    persistence = payload["jd_intelligence_existing_output_trace_persistence"]
    assert persistence["reason"] == "trace_disabled"
    assert persistence["trace_persistence_requested"] is True
    assert persistence["trace_persistence_performed"] is False
    assert calls == []


def test_missing_context_is_non_blocking_even_when_strict_enabled():
    calls = []

    def fail_persistence(**kwargs):
        calls.append(kwargs)
        raise AssertionError("missing context must not call persistence helper")

    payload = collector._maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        [_already_intelligent_job()],
        env={
            DIAGNOSTICS_FLAG: "1",
            PERSISTENCE_FLAG: "1",
            "APPLYLENS_AGENT_TRACE_ENABLED": "1",
            "APPLYLENS_AGENT_TRACE_STRICT": "1",
        },
        persistence_helper=fail_persistence,
        persistence_execute_callback=lambda operation: operation,
    )

    persistence = payload["jd_intelligence_existing_output_trace_persistence"]
    assert persistence["reason"] == "missing_trace_context"
    assert persistence["trace_persistence_performed"] is False
    assert calls == []


def test_missing_executor_is_non_blocking_even_when_strict_enabled():
    calls = []

    def fail_persistence(**kwargs):
        calls.append(kwargs)
        raise AssertionError("missing executor must not call persistence helper")

    payload = collector._maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        [_already_intelligent_job()],
        env=_env(
            **{
                DIAGNOSTICS_FLAG: "1",
                PERSISTENCE_FLAG: "1",
                "APPLYLENS_AGENT_TRACE_ENABLED": "1",
                "APPLYLENS_AGENT_TRACE_STRICT": "1",
            }
        ),
        persistence_helper=fail_persistence,
    )

    persistence = payload["jd_intelligence_existing_output_trace_persistence"]
    assert persistence["reason"] == "write_executor_missing"
    assert persistence["trace_persistence_performed"] is False
    assert calls == []


def test_direct_helper_happy_path_records_one_run_and_one_aggregate_step():
    operations = []
    payload = _diagnostics_payload()

    result = jd_intelligence.persist_existing_job_intelligence_trace_payload(
        diagnostics_payload=payload,
        owner_user_id="phase88b_owner",
        pipeline_run_id="phase88b_pipeline",
        context_id="phase88b_context",
        execute_callback=lambda operation: operations.append(operation),
    )

    assert result["attempted"] is True
    assert result["recorded"] is True
    assert result["trace_persistence_requested"] is True
    assert result["trace_persistence_performed"] is True
    assert result["record_count"] == 2
    assert result["agent_run_count"] == 1
    assert result["persisted_step_count"] == 1
    assert [operation["table"] for operation in operations] == [
        "agent_runs",
        "agent_steps",
    ]

    run_snapshot = result["recording_payload"]["records"][0]["snapshot"]
    step_snapshot = result["recording_payload"]["records"][1]["snapshot"]
    assert step_snapshot["agent_name"] == "jd_intelligence_existing_output"
    assert step_snapshot["agent_run_id"] == run_snapshot["agent_run_id"]
    assert run_snapshot["summary_json"]["job_count_seen"] == 2
    assert run_snapshot["summary_json"]["job_count_sampled"] == 1
    assert run_snapshot["summary_json"]["trace_persistence_performed"] is True
    assert step_snapshot["input_json"] == {
        "source_stage": "intelligence",
        "sample_limit": 1,
        "diagnostics_gate_enabled": True,
        "persistence_gate_enabled": True,
        "owner_user_id": "phase88b_owner",
        "pipeline_run_id": "phase88b_pipeline",
        "context_id": "phase88b_context",
    }
    assert step_snapshot["output_json"]["jobs"] == payload["jobs"]
    assert step_snapshot["validation_json"] == payload["validation_summary"]


def test_collector_happy_path_delegates_to_persistence_helper_once():
    calls = []

    def persistence(**kwargs):
        calls.append(kwargs)
        return {
            "attempted": True,
            "recorded": True,
            "reason": "",
            "trace_persistence_requested": True,
            "trace_persistence_performed": True,
            "agent_run_id": "agent_run_phase88b",
            "persisted_step_count": 1,
        }

    payload = collector._maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        [_already_intelligent_job()],
        env=_env(
            **{
                DIAGNOSTICS_FLAG: "1",
                PERSISTENCE_FLAG: "1",
                "APPLYLENS_AGENT_TRACE_ENABLED": "1",
            }
        ),
        persistence_helper=persistence,
        persistence_execute_callback=lambda operation: operation,
    )

    assert payload["trace_persistence_requested"] is True
    assert payload["trace_persistence_performed"] is True
    assert len(calls) == 1
    assert calls[0]["diagnostics_payload"]["stage_name"] == "jd_intelligence_existing_output"
    assert calls[0]["owner_user_id"] == "phase88b_owner"
    assert calls[0]["pipeline_run_id"] == "phase88b_pipeline"
    assert calls[0]["context_id"] == "phase88b_context"
    assert callable(calls[0]["execute_callback"])


def test_non_strict_persistence_execution_failure_returns_warning():
    def fail(_operation):
        raise RuntimeError("phase88b executor unavailable")

    result = jd_intelligence.persist_existing_job_intelligence_trace_payload(
        diagnostics_payload=_diagnostics_payload(),
        owner_user_id="phase88b_owner",
        pipeline_run_id="phase88b_pipeline",
        context_id="phase88b_context",
        execute_callback=fail,
        strict=False,
    )

    assert result["attempted"] is True
    assert result["recorded"] is False
    assert result["reason"] == "trace_persistence_failed"
    assert "phase88b executor unavailable" in result["warning"]
    assert result["trace_persistence_performed"] is False
    assert result["production_output_changed"] is False


def test_strict_persistence_execution_failure_reraises_after_attempt():
    def fail(_operation):
        raise RuntimeError("phase88b strict executor unavailable")

    with pytest.raises(RuntimeError, match="phase88b strict executor unavailable"):
        jd_intelligence.persist_existing_job_intelligence_trace_payload(
            diagnostics_payload=_diagnostics_payload(),
            owner_user_id="phase88b_owner",
            pipeline_run_id="phase88b_pipeline",
            context_id="phase88b_context",
            execute_callback=fail,
            strict=True,
        )


def test_readback_shape_is_generic_agent_trace_compatible_without_api_contract_change():
    result = jd_intelligence.persist_existing_job_intelligence_trace_payload(
        diagnostics_payload=_diagnostics_payload(),
        owner_user_id="phase88b_owner",
        pipeline_run_id="phase88b_pipeline",
        context_id="phase88b_context",
        execute_callback=lambda operation: operation,
    )
    run = result["recording_payload"]["records"][0]["snapshot"]
    step = result["recording_payload"]["records"][1]["snapshot"]
    readback_like_payload = {
        "pipeline_run_id": run["pipeline_run_id"],
        "owner_user_id": run["owner_user_id"],
        "agent_runs": [{**run, "steps": [step]}],
        "counts": {"agent_runs": 1, "agent_steps": 1},
    }

    assert readback_like_payload["agent_runs"][0]["steps"][0]["agent_name"] == (
        "jd_intelligence_existing_output"
    )
    assert readback_like_payload["agent_runs"][0]["steps"][0]["output_json"][
        "stage_name"
    ] == "jd_intelligence_existing_output"


def test_source_safety_no_duplicate_provider_scoring_api_or_raw_sql_in_collector():
    collector_helper_source = _collector_helper_source()
    for forbidden in [
        "build_job_intelligence(",
        "enrich_skills_with_llm(",
        "run_chat_completion(",
        "run_chat_completion_with_metadata(",
        "evaluate_jobs(",
        "score_jobs(",
        "cursor.execute(",
        "commit(",
        "src.app.services",
        "src.app.api",
        "workflow_runner",
    ]:
        assert forbidden not in collector_helper_source

    jd_path = ROOT / "src/agents/jd_intelligence.py"
    assert_no_forbidden_runtime_calls_ast(
        [jd_path],
        forbidden_calls=(
            "run_chat_completion",
            "run_chat_completion_with_metadata",
            "enrich_skills_with_llm",
            "build_job_intelligence",
            "evaluate_jobs",
            "score_jobs",
            "submit_application",
            "execute_application",
            "click_apply",
            "mark_as_applied",
            "send_recruiter_message",
        ),
        forbidden_imports=(
            "src.ai.llm_client",
            "src.intelligence.job_intelligence",
            "src.pipeline.collector",
            "src.app.services",
            "src.app.api",
            "src.agents.workflow_runner",
        ),
    )
