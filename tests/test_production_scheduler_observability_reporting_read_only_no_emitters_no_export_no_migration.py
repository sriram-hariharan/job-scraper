from copy import deepcopy

import application_execution_queue as queue
from src.app import services


def _provider(status):
    def load_approval_record(approval_request_id):
        return {
            "approval_request_id": approval_request_id,
            "approval_status": status,
            "idempotency_key": "idem_1",
        }

    return load_approval_record


def _healthy_queue_gate():
    return queue.queue_safety_gate_payload(
        services.app_service_agentic_workflow_safety_gate_payload()
    )


def _approved_observability_gate():
    execution_gate = queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=_healthy_queue_gate(),
        approval_record_provider=_provider("approved"),
    )
    submission_gate = queue.application_submission_decision_payload(
        approval_request_id="approval_1",
        approval_gated_execution_output=execution_gate,
        approval_record_provider=_provider("approved"),
    )
    scheduler_gate = queue.scheduler_background_execution_decision_payload(
        approval_request_id="approval_1",
        application_submission_output=submission_gate,
        approval_record_provider=_provider("approved"),
    )
    live_scheduler_gate = queue.live_scheduler_execution_decision_payload(
        approval_request_id="approval_1",
        scheduler_background_execution_output=scheduler_gate,
        approval_record_provider=_provider("approved"),
    )
    wiring_gate = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=live_scheduler_gate,
        approval_record_provider=_provider("approved"),
    )
    return queue.production_scheduler_observability_decision_payload(
        approval_request_id="approval_1",
        production_scheduler_wiring_output=wiring_gate,
        approval_record_provider=_provider("approved"),
    )


def _assert_reporting_no_side_effects(result):
    assert result["production_scheduler_observability_reporting_read_only"] is True
    assert result["metrics_emitter_enabled"] is False
    assert result["logging_emitter_enabled"] is False
    assert result["audit_writer_enabled"] is False
    assert result["dashboard_code_enabled"] is False
    assert result["export_code_enabled"] is False
    assert result["reporting_job_enabled"] is False
    assert result["production_scheduler_wiring_enabled"] is False
    assert result["uncontrolled_scheduler_loop_enabled"] is False
    assert result["live_scheduler_loop_enabled"] is False
    assert result["background_worker_enabled"] is False
    assert result["automatic_submission_loop_enabled"] is False
    assert result["migration_execution_enabled"] is False
    assert result["live_execution_enabled"] is False
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False
    assert result["did_submit_application"] is False
    assert result["did_emit_metrics"] is False
    assert result["did_emit_logs"] is False
    assert result["did_write_audit_events"] is False
    assert result["did_start_background_work"] is False
    assert result["did_export_files"] is False
    assert result["did_create_dashboard_jobs"] is False
    assert result["did_create_reporting_jobs"] is False


def test_reporting_blocks_without_production_scheduler_observability_decision():
    result = queue.production_scheduler_observability_reporting_payload()

    assert result["production_scheduler_observability_reporting_gate_enabled"] is True
    assert result["production_scheduler_observability_reporting_allowed"] is False
    assert result["production_scheduler_observability_reporting_status"] == "blocked"
    assert result["production_scheduler_observability_reporting_reason_codes"] == [
        "missing_production_scheduler_observability_decision"
    ]
    assert result["production_scheduler_observability_reporting_summary"] == {
        "allowed": False,
        "status": "blocked",
        "reason_codes": ["missing_production_scheduler_observability_decision"],
        "read_only": True,
    }
    _assert_reporting_no_side_effects(result)


def test_reporting_blocks_unsupported_or_non_allowed_observability_decision():
    observability_gate = deepcopy(_approved_observability_gate())
    observability_gate["production_scheduler_observability_allowed"] = False
    observability_gate["production_scheduler_observability_status"] = "blocked"
    observability_gate["production_scheduler_observability_read_only"] = False

    result = queue.production_scheduler_observability_reporting_payload(
        observability_gate
    )

    assert result["production_scheduler_observability_reporting_allowed"] is False
    assert result["production_scheduler_observability_reporting_status"] == "blocked"
    assert result["production_scheduler_observability_reporting_reason_codes"] == [
        "production_scheduler_observability_not_allowed",
        "production_scheduler_observability_not_read_only",
        "production_scheduler_observability_status_not_passed",
    ]
    _assert_reporting_no_side_effects(result)


def test_reporting_returns_read_only_summary_for_allowed_observability_decision():
    observability_gate = _approved_observability_gate()

    result = queue.production_scheduler_observability_reporting_payload(
        observability_gate
    )

    assert result["production_scheduler_observability_allowed"] is True
    assert result["production_scheduler_observability_reporting_allowed"] is True
    assert result["production_scheduler_observability_reporting_status"] == "passed"
    assert result["production_scheduler_observability_reporting_reason_codes"] == []
    assert result["production_scheduler_observability_reporting_summary"] == {
        "allowed": True,
        "status": "passed",
        "reason_codes": [],
        "read_only": True,
        "approval_request_id": "approval_1",
        "approval_status": "approved",
        "production_scheduler_observability_status": "passed",
    }
    _assert_reporting_no_side_effects(result)


def test_reporting_summary_is_deterministic():
    observability_gate = _approved_observability_gate()

    first = queue.production_scheduler_observability_reporting_payload(
        observability_gate
    )
    second = queue.production_scheduler_observability_reporting_payload(
        deepcopy(observability_gate)
    )

    assert first == second


def test_reporting_preserves_existing_gate_outputs():
    observability_gate = _approved_observability_gate()

    result = queue.production_scheduler_observability_reporting_payload(
        observability_gate
    )

    assert result["queue_safety_gate_passed"] is True
    assert result["approval_gated_execution_allowed"] is True
    assert result["application_submission_allowed"] is True
    assert result["scheduler_background_execution_allowed"] is True
    assert result["live_scheduler_execution_allowed"] is True
    assert result["production_scheduler_wiring_allowed"] is True
    assert result["production_scheduler_observability_allowed"] is True
    _assert_reporting_no_side_effects(result)


def test_reporting_queue_boundary_has_no_emitters_exports_jobs_or_migration_constructs():
    source = open("application_execution_queue.py", encoding="utf-8").read()

    forbidden_tokens = [
        "asyncio.create_task",
        "threading.Thread",
        "BackgroundTasks",
        "subprocess.run",
        "subprocess.Popen",
        "subprocess.",
        "Popen(",
        "os.system",
        "migration_runner",
        "run_migration",
        "metrics_emitter(",
        "logging_emitter(",
        "audit_writer(",
        "dashboard_export",
        "reporting_job(",
        "export_writer(",
    ]
    for token in forbidden_tokens:
        assert token not in source
