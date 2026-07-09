from copy import deepcopy
from pathlib import Path
import ast

import pytest

from src.pipeline import collector
from src.storage.agent_trace.store import build_agent_trace_summary_payload


ROOT = Path(__file__).resolve().parents[1]
EXECUTION_GATE = "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_EXECUTION_ENABLED"
PERSISTENCE_GATE = (
    "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_TRACE_PERSISTENCE_ENABLED"
)
TRACE_GATE = "APPLYLENS_AGENT_TRACE_ENABLED"


FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "collector_output_changed",
    "production_output_changed",
    "evaluable_jobs_changed",
    "scored_jobs_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "cache_behavior_changed",
    "retry_behavior_changed",
    "dedupe_behavior_changed",
    "source_health_behavior_changed",
    "ats_health_behavior_changed",
    "review_queue_mutation_performed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "workflow_runner_executed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
    "external_action_automation_performed",
]


def _env(**overrides):
    base = {
        EXECUTION_GATE: "",
        PERSISTENCE_GATE: "",
        TRACE_GATE: "",
        "APPLYLENS_AGENT_TRACE_STRICT": "",
        "JOB_APP_PIPELINE_RUN_ID": "phase100b_pipeline",
        "JOB_STACK_OWNER_USER_ID": "phase100b_owner",
        "APPLYLENS_AGENT_CONTEXT_ID": "phase100b_context",
    }
    base.update(overrides)
    return base


def _trace_payload(chain_id="chain-phase100b"):
    return {
        "artifact_type": "agent_evidence_chain_trace_payload",
        "payload_version": "agent-evidence-chain-trace-payload-v1",
        "source_artifact_type": "agent_evidence_chain_bundle",
        "source_agent": "evidence_chain_composition",
        "chain_id": chain_id,
        "chain_status": "complete",
        "chain_readiness": "ready_for_human_review",
        "chain_reason_codes": [],
        "sampling_summary": {"included_agent_count": 1},
        "redaction_policy": "compact",
        "safety_metadata": {"provider_call_performed": False},
        "agent_run_compatible_summary": {
            "ordered_agent_count": 6,
            "included_agent_count": 1,
        },
        "agent_step_compatible_summaries": [
            {
                "agent_key": "operator_review",
                "artifact_present": True,
                "artifact_valid": True,
                "validation_summary": {"validation_status": "passed"},
            }
        ],
    }


def _execution_result(*payloads):
    per_job_results = []
    for index, payload in enumerate(payloads):
        artifacts = {}
        if payload is not None:
            artifacts["agent_evidence_chain_trace_payload"] = payload
        per_job_results.append(
            {
                "job_id": f"job-phase100b-{index}",
                "artifacts": artifacts,
            }
        )
    return {
        "artifact_type": "collector_controlled_evidence_chain_execution_result",
        "execution_result": {
            "artifact_type": "controlled_evidence_chain_execution_result",
            "executed": True,
            "per_job_results": per_job_results,
        },
    }


def _assert_no_production_mutations(result):
    for flag in FALSE_SAFETY_FLAGS:
        assert result[flag] is False
        assert result["safety_metadata"][flag] is False


def test_persistence_gate_off_skips_without_calling_helper_or_mutating_input():
    execution = _execution_result(_trace_payload())
    before = deepcopy(execution)
    calls = []

    def fail_helper(**kwargs):
        calls.append(kwargs)
        raise AssertionError("persistence gate off must not call helper")

    result = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        execution,
        env=_env(**{EXECUTION_GATE: "1", PERSISTENCE_GATE: ""}),
        execute_callback=lambda operation: operation,
        persistence_helper=fail_helper,
    )

    assert result["attempted"] is False
    assert result["persisted"] is False
    assert result["reason"] == "trace_persistence_disabled"
    assert result["trace_persistence_requested"] is False
    assert result["trace_persistence_performed"] is False
    assert calls == []
    assert execution == before
    _assert_no_production_mutations(result)


def test_global_trace_gate_off_skips_without_calling_helper():
    calls = []

    def fail_helper(**kwargs):
        calls.append(kwargs)
        raise AssertionError("trace gate off must not call helper")

    result = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        _execution_result(_trace_payload()),
        env=_env(**{EXECUTION_GATE: "1", PERSISTENCE_GATE: "1", TRACE_GATE: ""}),
        execute_callback=lambda operation: operation,
        persistence_helper=fail_helper,
    )

    assert result["reason"] == "trace_disabled"
    assert result["trace_persistence_requested"] is True
    assert result["trace_persistence_performed"] is False
    assert calls == []


def test_execution_result_missing_is_non_blocking_and_does_not_write():
    calls = []
    result = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        None,
        env=_env(**{EXECUTION_GATE: "1", PERSISTENCE_GATE: "1", TRACE_GATE: "1"}),
        execute_callback=lambda operation: calls.append(operation),
    )

    assert result["reason"] == "execution_result_missing"
    assert result["attempted"] is False
    assert result["persisted"] is False
    assert calls == []


def test_trace_payload_extraction_ignores_missing_and_malformed_payloads():
    calls = []

    def persistence(**kwargs):
        calls.append(kwargs)
        return {
            "attempted": True,
            "recorded": True,
            "reason": "",
            "record_count": 2,
            "run_count": 1,
            "step_count": 1,
            "agent_run_id": "run-phase100b",
        }

    result = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        _execution_result(
            _trace_payload("valid-a"),
            None,
            {"artifact_type": "wrong"},
            _trace_payload("valid-b"),
        ),
        env=_env(**{EXECUTION_GATE: "1", PERSISTENCE_GATE: "1", TRACE_GATE: "1"}),
        execute_callback=lambda operation: operation,
        persistence_helper=persistence,
    )

    assert result["payloads_found_count"] == 2
    assert result["payloads_attempted_count"] == 2
    assert result["payloads_persisted_count"] == 2
    assert len(calls) == 2
    assert [call["trace_payload"]["chain_id"] for call in calls] == [
        "valid-a",
        "valid-b",
    ]


def test_successful_execute_callback_path_persists_each_payload_and_sets_write_flags():
    calls = []

    def persistence(**kwargs):
        calls.append(kwargs)
        return {
            "attempted": True,
            "recorded": True,
            "reason": "",
            "record_count": 2,
            "run_count": 1,
            "step_count": 1,
            "agent_run_id": f"agent-run-{len(calls)}",
        }

    execution = _execution_result(_trace_payload("one"), _trace_payload("two"))
    before = deepcopy(execution)
    result = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        execution,
        env=_env(**{EXECUTION_GATE: "1", PERSISTENCE_GATE: "1", TRACE_GATE: "1"}),
        execute_callback=lambda operation: operation,
        persistence_helper=persistence,
    )

    assert result["attempted"] is True
    assert result["persisted"] is True
    assert result["payloads_persisted_count"] == 2
    assert result["record_count"] == 4
    assert result["run_count"] == 2
    assert result["step_count"] == 2
    assert result["database_write_performed"] is True
    assert result["trace_persistence_performed"] is True
    assert result["trace_store_write_performed"] is True
    assert result["observability_mutation_performed"] is True
    assert result["safety_metadata"]["database_write_performed"] is True
    assert calls[0]["owner_user_id"] == "phase100b_owner"
    assert calls[0]["pipeline_run_id"] == "phase100b_pipeline"
    assert calls[0]["context_id"] == "phase100b_context"
    assert callable(calls[0]["execute_callback"])
    assert calls[0]["cursor"] is None
    assert execution == before
    _assert_no_production_mutations(result)


def test_successful_cursor_path_uses_phase96_helper_without_raw_collector_sql():
    class FakeCursor:
        def __init__(self):
            self.operations = []

        def execute(self, sql, params):
            self.operations.append((sql, params))

    cursor = FakeCursor()
    result = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        _execution_result(_trace_payload()),
        env=_env(**{EXECUTION_GATE: "1", PERSISTENCE_GATE: "1", TRACE_GATE: "1"}),
        cursor=cursor,
    )

    assert result["persisted"] is True
    assert result["record_count"] == 2
    assert result["run_count"] == 1
    assert result["step_count"] == 1
    assert len(cursor.operations) == 2


def test_missing_context_and_missing_executor_are_non_blocking_when_strict():
    missing_context = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        _execution_result(_trace_payload()),
        env={
            EXECUTION_GATE: "1",
            PERSISTENCE_GATE: "1",
            TRACE_GATE: "1",
            "APPLYLENS_AGENT_TRACE_STRICT": "1",
        },
        execute_callback=lambda operation: operation,
        strict=True,
    )
    missing_executor = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        _execution_result(_trace_payload()),
        env=_env(
            **{
                EXECUTION_GATE: "1",
                PERSISTENCE_GATE: "1",
                TRACE_GATE: "1",
                "APPLYLENS_AGENT_TRACE_STRICT": "1",
            }
        ),
        strict=True,
    )

    assert missing_context["reason"] == "missing_trace_context"
    assert missing_context["attempted"] is False
    assert missing_executor["reason"] == "write_executor_missing"
    assert missing_executor["attempted"] is False


def test_multiple_executors_returns_validation_failure_without_silent_choice():
    class FakeCursor:
        def execute(self, sql, params):
            raise AssertionError("must not execute when two executors are supplied")

    result = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        _execution_result(_trace_payload()),
        env=_env(**{EXECUTION_GATE: "1", PERSISTENCE_GATE: "1", TRACE_GATE: "1"}),
        cursor=FakeCursor(),
        execute_callback=lambda operation: operation,
    )

    assert result["reason"] == "multiple_write_executors"
    assert result["attempted"] is False
    assert result["persisted"] is False


def test_missing_trace_payload_is_non_blocking():
    result = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        _execution_result(None, {"artifact_type": "not-the-right-payload"}),
        env=_env(**{EXECUTION_GATE: "1", PERSISTENCE_GATE: "1", TRACE_GATE: "1"}),
        execute_callback=lambda operation: operation,
    )

    assert result["reason"] == "trace_payload_missing"
    assert result["payloads_found_count"] == 0
    assert result["record_count"] == 0
    assert result["persisted"] is False


def test_write_failure_non_strict_is_non_blocking_but_strict_reraises_after_attempt():
    def fail(**_kwargs):
        raise RuntimeError("phase100b persistence executor unavailable")

    non_strict = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        _execution_result(_trace_payload()),
        env=_env(**{EXECUTION_GATE: "1", PERSISTENCE_GATE: "1", TRACE_GATE: "1"}),
        execute_callback=lambda operation: operation,
        persistence_helper=fail,
        strict=False,
    )

    assert non_strict["attempted"] is True
    assert non_strict["persisted"] is False
    assert non_strict["reason"] == "evidence_chain_trace_persistence_failed"
    assert non_strict["payloads_failed_count"] == 1

    with pytest.raises(RuntimeError, match="phase100b persistence executor unavailable"):
        collector._maybe_persist_controlled_evidence_chain_execution_trace(
            _execution_result(_trace_payload()),
            env=_env(
                **{EXECUTION_GATE: "1", PERSISTENCE_GATE: "1", TRACE_GATE: "1"}
            ),
            execute_callback=lambda operation: operation,
            persistence_helper=fail,
            strict=True,
        )


def test_collector_integration_order_keeps_diagnostics_execution_then_persistence():
    source = (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")
    diagnostics_marker = "_maybe_build_evidence_chain_collector_diagnostics(scored_jobs)"
    execution_marker = (
        "_maybe_run_controlled_evidence_chain_execution_after_application_priority(scored_jobs)"
    )
    persistence_marker = (
        "_maybe_persist_controlled_evidence_chain_execution_trace("
        "\n        evidence_chain_execution_result"
    )
    source_health_marker = "if role_title_audit_rows is not None:"

    assert source.index(diagnostics_marker) < source.index(execution_marker)
    assert source.index(execution_marker) < source.index(persistence_marker)
    assert source.index(persistence_marker) < source.index(
        source_health_marker,
        source.index(persistence_marker),
    )


def test_readback_compatibility_uses_existing_generic_trace_summary_without_api_ui():
    run = {
        "agent_run_id": "agent_evidence_chain_trace:chain-phase100b:ctx",
        "owner_user_id": "phase100b_owner",
        "pipeline_run_id": "phase100b_pipeline",
        "context_id": "phase100b_context",
        "status": "succeeded",
        "started_at": "1970-01-01T00:00:00+00:00",
        "completed_at": "1970-01-01T00:00:00+00:00",
        "summary_json": {"source_agent": "evidence_chain_composition"},
    }
    step = {
        "agent_step_id": "step-phase100b",
        "agent_run_id": run["agent_run_id"],
        "owner_user_id": "phase100b_owner",
        "pipeline_run_id": "phase100b_pipeline",
        "context_id": "phase100b_context",
        "agent_name": "operator_review",
        "status": "succeeded",
        "started_at": "1970-01-01T00:00:00+00:00",
        "completed_at": "1970-01-01T00:00:00+00:00",
        "input_json": {},
        "output_json": {"agent_key": "operator_review"},
        "validation_json": {"validation_status": "passed"},
    }

    summary = build_agent_trace_summary_payload(agent_runs=[run], agent_steps=[step])

    assert summary["summary_type"] == "agent_trace"
    assert summary["run_count"] == 1
    assert summary["step_count"] == 1
    assert summary["agent_counts"] == {"operator_review": 1}
    assert summary["safety_metadata"]["did_write_database"] is False
    assert summary["safety_metadata"]["did_call_llm"] is False


def test_source_safety_no_raw_sql_provider_api_workflow_or_apply_paths():
    source = (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper_source = ""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "_maybe_persist_controlled_evidence_chain_execution_trace"
        ):
            helper_source = ast.get_source_segment(source, node) or ""
            break
    assert helper_source
    assert "persist_agent_evidence_chain_trace_payload" in helper_source
    for forbidden in [
        "cursor.execute(",
        "record_agent_step_postgres_payload",
        "create_agent_run_postgres_payload",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "workflow_runner",
        "submit_application",
        "click_apply",
        "mark_applied",
        "send_recruiter",
        "src.app.api",
        "src.app.services",
        "LangGraph",
    ]:
        assert forbidden not in helper_source
