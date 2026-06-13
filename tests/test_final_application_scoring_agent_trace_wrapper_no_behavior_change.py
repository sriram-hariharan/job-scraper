from copy import deepcopy
import importlib
from pathlib import Path

from src.agents.agent_state import JobApplicationContext
from src.agents import final_application_scoring


def _summary():
    return {
        "input_count": 6,
        "scored_count": 5,
        "qualified_count": 3,
        "disqualified_count": 2,
        "score_summary": {
            "score_band_high": 2,
            "score_band_medium": 1,
            "score_band_low": 2,
        },
        "threshold_summary": {
            "qualification_threshold": 0.72,
            "disqualification_threshold": 0.45,
        },
        "decision_counts": {
            "qualified": 3,
            "disqualified": 2,
        },
        "top_score": 0.94,
        "bottom_score": 0.31,
        "average_score": 0.68,
    }


def _context():
    return JobApplicationContext(
        approval_request_id="approval_final_scoring",
        job_id="job_final_scoring",
        candidate_key="candidate_final_scoring",
        role_family="product_analytics",
        run_mode="dry_run",
        observed_at_utc="2026-06-12T16:00:00Z",
        metadata={"source": "unit_test"},
    )


def _assert_safety_flags_false(payload):
    assert payload["did_call_live_final_application_scoring"] is False
    assert payload["did_call_prefilter_relevance"] is False
    assert payload["did_call_deduplication"] is False
    assert payload["did_call_jd_intelligence"] is False
    assert payload["did_call_llm_provider"] is False
    assert payload["did_execute_application"] is False
    assert payload["did_submit_application"] is False
    assert payload["did_create_connection"] is False
    assert payload["did_commit_transaction"] is False
    assert payload["did_run_migration"] is False
    assert payload["did_schedule_background_work"] is False
    assert payload["did_execute_scheduler"] is False
    assert payload["did_execute_reporting_job"] is False
    assert payload["did_export_files"] is False
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert payload["pipeline_wiring_added"] is False


def test_import_has_no_side_effects():
    module = importlib.reload(final_application_scoring)

    _assert_safety_flags_false(module.safety_flags())


def test_final_application_scoring_wrapper_output_is_deterministic_and_preserves_input():
    summary = _summary()
    original = deepcopy(summary)

    first = final_application_scoring.describe_final_application_scoring_result(summary)
    second = final_application_scoring.describe_final_application_scoring_result(summary)

    assert summary == original
    assert first == second
    assert first["agent_name"] == "final_application_scoring_agent"
    assert first["agent_version"] == "final-application-scoring-wrapper-v1"
    assert first["status"] == "completed"
    assert first["input_count"] == 6
    assert first["scored_count"] == 5
    assert first["qualified_count"] == 3
    assert first["disqualified_count"] == 2
    assert "trace_summary" not in first
    assert "trace_summary" not in first["output_json"]
    _assert_safety_flags_false(first)


def test_final_scoring_wrapper_trace_summary_is_opt_in_deterministic_and_read_only():
    summary = _summary()
    original = deepcopy(summary)

    default_payload = final_application_scoring.describe_final_application_scoring_result(
        summary
    )
    first = final_application_scoring.describe_final_application_scoring_result(
        summary,
        include_trace_summary=True,
    )
    second = final_application_scoring.describe_final_application_scoring_result(
        summary,
        include_trace_summary=True,
    )

    assert "trace_summary" not in default_payload
    assert summary == original
    assert first == second
    assert first["trace_summary"]["summary_type"] == "agent_trace"
    assert first["trace_summary"]["run_count"] == 0
    assert first["trace_summary"]["step_count"] == 1
    assert first["trace_summary"]["agent_counts"] == {
        "final_application_scoring_agent": 1,
    }
    assert first["trace_summary"]["step_status_counts"] == {"completed": 1}
    assert first["trace_summary"]["all_required_fields_present"] is True
    assert first["trace_summary"]["safety_metadata"] == {
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
    assert "trace_summary" not in first["output_json"]
    _assert_safety_flags_false(first)


def test_supplied_score_threshold_decision_and_score_fields_are_preserved():
    payload = final_application_scoring.describe_final_application_scoring_result(
        _summary()
    )

    assert payload["score_summary"] == {
        "score_band_high": 2,
        "score_band_medium": 1,
        "score_band_low": 2,
    }
    assert payload["threshold_summary"] == {
        "qualification_threshold": 0.72,
        "disqualification_threshold": 0.45,
    }
    assert payload["decision_counts"] == {
        "disqualified": 2,
        "qualified": 3,
    }
    assert payload["top_score"] == 0.94
    assert payload["bottom_score"] == 0.31
    assert payload["average_score"] == 0.68
    assert payload["output_json"]["score_summary"] == payload["score_summary"]


def test_counts_are_validated_without_calling_live_scoring():
    payload = final_application_scoring.describe_final_application_scoring_result(
        _summary()
    )

    assert payload["validation_json"] == {
        "is_valid": True,
        "errors": [],
        "preserves_final_application_scoring": True,
        "did_call_live_final_application_scoring": False,
        "did_call_prefilter_relevance": False,
        "did_call_deduplication": False,
        "did_call_jd_intelligence": False,
        "did_call_llm_provider": False,
    }


def test_invalid_counts_fail_validation_safely():
    summary = _summary()
    summary["qualified_count"] = 4
    payload = final_application_scoring.describe_final_application_scoring_result(
        summary
    )

    assert payload["status"] == "invalid"
    assert payload["validation_json"]["is_valid"] is False
    assert payload["validation_json"]["errors"] == [
        "qualified_disqualified_scored_count_mismatch"
    ]
    assert payload["did_call_live_final_application_scoring"] is False
    assert payload["did_call_prefilter_relevance"] is False
    assert payload["did_call_deduplication"] is False
    assert payload["did_call_jd_intelligence"] is False
    assert payload["did_call_llm_provider"] is False
    assert payload["did_execute_application"] is False
    assert payload["did_submit_application"] is False


def test_invalid_counts_preserve_validation_errors_with_opt_in_trace_summary():
    summary = _summary()
    summary["qualified_count"] = 4
    original = deepcopy(summary)

    payload = final_application_scoring.describe_final_application_scoring_result(
        summary,
        include_trace_summary=True,
    )

    assert summary == original
    assert payload["status"] == "invalid"
    assert payload["validation_json"]["errors"] == [
        "qualified_disqualified_scored_count_mismatch"
    ]
    assert payload["trace_summary"]["step_status_counts"] == {"invalid": 1}
    assert payload["trace_summary"]["safety_metadata"]["did_write_database"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_call_llm"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_change_pipeline"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_change_scoring"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_change_approval"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_execute_application"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_submit_application"] is False
    _assert_safety_flags_false(payload)


def test_missing_score_fields_are_not_inferred_from_score_summary():
    summary = _summary()
    summary.pop("top_score")
    summary.pop("bottom_score")
    summary.pop("average_score")
    summary["score_summary"] = {"max_score": 0.99, "min_score": 0.11}

    payload = final_application_scoring.describe_final_application_scoring_result(
        summary
    )

    assert payload["top_score"] is None
    assert payload["bottom_score"] is None
    assert payload["average_score"] is None


def test_step_snapshot_uses_caller_supplied_context_ids_and_timestamp():
    summary = _summary()
    original = deepcopy(summary)

    step = final_application_scoring.build_final_application_scoring_step_snapshot(
        context=_context(),
        scoring_summary=summary,
        observed_at_utc="2026-06-12T16:01:00Z",
        agent_run_id="agent_run_final_scoring",
        step_index=5,
        agent_version="final-application-scoring-wrapper-test",
    )

    assert summary == original
    assert step["agent_name"] == "final_application_scoring_agent"
    assert step["step_name"] == "final_application_scoring_trace_wrapper"
    assert step["step_status"] == "completed"
    assert step["agent_run_id"] == "agent_run_final_scoring"
    assert step["observed_at_utc"] == "2026-06-12T16:01:00Z"
    assert step["output_summary"]["agent_version"] == (
        "final-application-scoring-wrapper-test"
    )
    assert step["output_summary"]["separation"] == {
        "final_application_scoring": "described_only",
        "prefilter_relevance": "not_called",
        "deduplication": "not_called",
        "jd_intelligence": "not_called",
        "llm_evaluation_live_extraction": "not_called",
        "application_execution": "not_called",
        "application_submission": "not_called",
    }
    assert "trace_summary" not in step["metadata"]


def test_step_snapshot_can_attach_opt_in_trace_summary_in_metadata():
    summary = _summary()
    original = deepcopy(summary)

    step = final_application_scoring.build_final_application_scoring_step_snapshot(
        context=_context(),
        scoring_summary=summary,
        observed_at_utc="2026-06-12T16:01:00Z",
        agent_run_id="agent_run_final_scoring",
        include_trace_summary=True,
    )

    assert summary == original
    assert step["metadata"]["trace_summary"]["summary_type"] == "agent_trace"
    assert step["metadata"]["trace_summary"]["step_count"] == 1
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_write_database"] is False
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_call_llm"] is False
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_change_pipeline"] is False
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_change_scoring"] is False
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_change_approval"] is False
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_execute_application"] is False
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_submit_application"] is False
    assert "trace_summary" not in step["output_summary"]


def test_final_scoring_wrapper_source_does_not_call_trace_storage_execution_helpers():
    source = Path("src/agents/final_application_scoring.py").read_text()

    forbidden_tokens = [
        "create_agent_run(",
        "record_agent_step(",
        "complete_agent_run(",
        "execute_agent_trace_recording(",
        "build_agent_trace_recording_payload(",
    ]
    for token in forbidden_tokens:
        assert token not in source


def test_wrapper_source_does_not_call_live_scoring_prefilter_dedup_jd_llm_or_runtime_paths():
    source = Path("src/agents/final_application_scoring.py").read_text()

    forbidden_tokens = [
        "src.pipeline.application_scorer",
        "score_jobs",
        "score_job(",
        "src.pipeline.job_ranker",
        "rank_jobs",
        "title_score",
        "recency_score",
        "momentum_score",
        "src.matching",
        "run_prefilter",
        "ResumeJobMatchResult",
        "job_fit_evaluator",
        "score_first_scan",
        "src.pipeline.job_filter",
        "filter_jobs",
        "src.pipeline.dedupe",
        "dedupe_jobs",
        "src.agents.relevance_prefilter",
        "src.agents.deduplication",
        "src.agents.jd_intelligence",
        "build_job_intelligence",
        "run_llm",
        "model_client",
        "open(",
        "connect(",
        ".commit(",
        "run_migration(",
        "FileResponse",
        "StreamingResponse",
        "write_text",
        "write_bytes",
        "send_file",
        "subprocess",
        "background_tasks.add_task",
        "Thread",
        "Process",
        "scheduler_execution(",
        "reporting_job_execution(",
        "application_execution(",
        "application_submission(",
        "export_writer",
        "metrics_emitter",
        "logging_emitter",
        "audit_writer",
        "datetime.",
        "utcnow",
        "now(",
        "uuid",
        "random",
        "src.app.api",
        "agentic_review.js",
        "workflow_runner",
        "application_execution_queue",
    ]
    for token in forbidden_tokens:
        assert token not in source
