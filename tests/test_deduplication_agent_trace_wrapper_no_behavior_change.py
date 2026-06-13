from copy import deepcopy
import importlib
from pathlib import Path

from src.agents.agent_state import JobApplicationContext
from src.agents import deduplication


def _summary():
    return {
        "input_count": 8,
        "filtered_count": 8,
        "unique_count": 5,
        "seen_count": 2,
        "new_count": 3,
        "same_run_duplicate_count": 3,
        "cross_run_duplicate_count": 2,
        "reason_counts": {
            "new_job": 3,
            "seen_job": 2,
            "same_run_duplicate": 3,
        },
    }


def _context():
    return JobApplicationContext(
        approval_request_id="approval_dedup",
        job_id="job_dedup",
        candidate_key="candidate_dedup",
        role_family="software_engineering",
        run_mode="dry_run",
        observed_at_utc="2026-06-12T14:00:00Z",
        metadata={"source": "unit_test"},
    )


def _assert_safety_flags_false(payload):
    assert payload["did_call_live_deduplication"] is False
    assert payload["did_call_prefilter_relevance"] is False
    assert payload["did_call_llm_evaluation"] is False
    assert payload["did_call_final_application_scoring"] is False
    assert payload["did_create_connection"] is False
    assert payload["did_commit_transaction"] is False
    assert payload["did_run_migration"] is False
    assert payload["did_schedule_background_work"] is False
    assert payload["did_execute_scheduler"] is False
    assert payload["did_execute_reporting_job"] is False
    assert payload["did_export_files"] is False
    assert payload["did_execute_application"] is False
    assert payload["did_submit_application"] is False
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert payload["pipeline_wiring_added"] is False


def test_import_has_no_side_effects():
    module = importlib.reload(deduplication)

    _assert_safety_flags_false(module.safety_flags())


def test_deduplication_wrapper_output_is_deterministic_and_preserves_input():
    summary = _summary()
    original = deepcopy(summary)

    first = deduplication.describe_deduplication_result(summary)
    second = deduplication.describe_deduplication_result(summary)

    assert summary == original
    assert first == second
    assert first["agent_name"] == "deduplication_agent"
    assert first["agent_version"] == "deduplication-wrapper-v1"
    assert first["status"] == "completed"
    assert first["input_count"] == 8
    assert first["filtered_count"] == 8
    assert first["unique_count"] == 5
    assert first["seen_count"] == 2
    assert first["new_count"] == 3
    assert first["same_run_duplicate_count"] == 3
    assert first["cross_run_duplicate_count"] == 2
    assert "trace_summary" not in first
    assert "trace_summary" not in first["output_json"]
    _assert_safety_flags_false(first)


def test_deduplication_wrapper_trace_summary_is_opt_in_deterministic_and_read_only():
    summary = _summary()
    original = deepcopy(summary)

    default_payload = deduplication.describe_deduplication_result(summary)
    first = deduplication.describe_deduplication_result(
        summary,
        include_trace_summary=True,
    )
    second = deduplication.describe_deduplication_result(
        summary,
        include_trace_summary=True,
    )

    assert "trace_summary" not in default_payload
    assert summary == original
    assert first == second
    assert first["trace_summary"]["summary_type"] == "agent_trace"
    assert first["trace_summary"]["run_count"] == 0
    assert first["trace_summary"]["step_count"] == 1
    assert first["trace_summary"]["agent_counts"] == {"deduplication_agent": 1}
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


def test_reason_counts_are_preserved_and_sorted():
    payload = deduplication.describe_deduplication_result(_summary())

    assert payload["reason_counts"] == {
        "new_job": 3,
        "same_run_duplicate": 3,
        "seen_job": 2,
    }
    assert payload["output_json"]["reason_counts"] == payload["reason_counts"]


def test_input_unique_seen_new_and_duplicate_counts_are_validated():
    payload = deduplication.describe_deduplication_result(_summary())

    assert payload["validation_json"] == {
        "is_valid": True,
        "errors": [],
        "preserves_deduplication": True,
        "did_call_live_deduplication": False,
        "did_call_prefilter_relevance": False,
        "did_call_llm_evaluation": False,
        "did_call_final_application_scoring": False,
    }


def test_invalid_counts_fail_validation_safely():
    summary = _summary()
    summary["new_count"] = 4
    payload = deduplication.describe_deduplication_result(summary)

    assert payload["status"] == "invalid"
    assert payload["validation_json"]["is_valid"] is False
    assert payload["validation_json"]["errors"] == ["seen_new_unique_count_mismatch"]
    assert payload["did_call_live_deduplication"] is False
    assert payload["did_call_prefilter_relevance"] is False
    assert payload["did_call_llm_evaluation"] is False
    assert payload["did_call_final_application_scoring"] is False
    assert payload["did_execute_application"] is False
    assert payload["did_submit_application"] is False


def test_invalid_counts_preserve_validation_errors_with_opt_in_trace_summary():
    summary = _summary()
    summary["new_count"] = 4
    original = deepcopy(summary)

    payload = deduplication.describe_deduplication_result(
        summary,
        include_trace_summary=True,
    )

    assert summary == original
    assert payload["status"] == "invalid"
    assert payload["validation_json"]["errors"] == ["seen_new_unique_count_mismatch"]
    assert payload["trace_summary"]["step_status_counts"] == {"invalid": 1}
    assert payload["trace_summary"]["safety_metadata"]["did_write_database"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_call_llm"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_change_pipeline"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_change_scoring"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_execute_application"] is False
    assert payload["trace_summary"]["safety_metadata"]["did_submit_application"] is False
    _assert_safety_flags_false(payload)


def test_step_snapshot_uses_caller_supplied_context_ids_and_timestamp():
    summary = _summary()
    original = deepcopy(summary)

    step = deduplication.build_deduplication_step_snapshot(
        context=_context(),
        deduplication_summary=summary,
        observed_at_utc="2026-06-12T14:01:00Z",
        agent_run_id="agent_run_dedup",
        step_index=3,
        agent_version="deduplication-wrapper-test",
    )

    assert summary == original
    assert step["agent_name"] == "deduplication_agent"
    assert step["step_name"] == "deduplication_trace_wrapper"
    assert step["step_status"] == "completed"
    assert step["agent_run_id"] == "agent_run_dedup"
    assert step["observed_at_utc"] == "2026-06-12T14:01:00Z"
    assert step["output_summary"]["agent_version"] == "deduplication-wrapper-test"
    assert step["output_summary"]["separation"] == {
        "deduplication": "described_only",
        "prefilter_relevance": "not_called",
        "llm_evaluation": "not_called",
        "final_application_scoring": "not_called",
    }
    assert "trace_summary" not in step["metadata"]


def test_step_snapshot_can_attach_opt_in_trace_summary_in_metadata():
    summary = _summary()
    original = deepcopy(summary)

    step = deduplication.build_deduplication_step_snapshot(
        context=_context(),
        deduplication_summary=summary,
        observed_at_utc="2026-06-12T14:01:00Z",
        agent_run_id="agent_run_dedup",
        include_trace_summary=True,
    )

    assert summary == original
    assert step["metadata"]["trace_summary"]["summary_type"] == "agent_trace"
    assert step["metadata"]["trace_summary"]["step_count"] == 1
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_write_database"] is False
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_call_llm"] is False
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_change_pipeline"] is False
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_execute_application"] is False
    assert step["metadata"]["trace_summary"]["safety_metadata"]["did_submit_application"] is False
    assert "trace_summary" not in step["output_summary"]


def test_deduplication_wrapper_source_does_not_call_trace_storage_execution_helpers():
    source = Path("src/agents/deduplication.py").read_text()

    forbidden_tokens = [
        "create_agent_run(",
        "record_agent_step(",
        "complete_agent_run(",
        "execute_agent_trace_recording(",
        "build_agent_trace_recording_payload(",
    ]
    for token in forbidden_tokens:
        assert token not in source


def test_wrapper_source_does_not_call_live_dedup_prefilter_llm_or_scoring_paths():
    source = Path("src/agents/deduplication.py").read_text()

    forbidden_tokens = [
        "src.pipeline.dedupe",
        "dedupe_jobs",
        "job_identity",
        "title_key",
        "user_seen_jobs",
        "seen_jobs_staging",
        "src.pipeline.job_filter",
        "filter_jobs",
        "relevance_prefilter",
        "job_fit_evaluator",
        "score_first_scan",
        "llm_evaluator",
        "run_llm",
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
