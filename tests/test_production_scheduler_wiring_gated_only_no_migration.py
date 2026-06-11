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


def _approved_execution_gate():
    return queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=_healthy_queue_gate(),
        approval_record_provider=_provider("approved"),
    )


def _approved_submission_gate():
    return queue.application_submission_decision_payload(
        approval_request_id="approval_1",
        approval_gated_execution_output=_approved_execution_gate(),
        approval_record_provider=_provider("approved"),
    )


def _approved_scheduler_gate():
    return queue.scheduler_background_execution_decision_payload(
        approval_request_id="approval_1",
        application_submission_output=_approved_submission_gate(),
        approval_record_provider=_provider("approved"),
    )


def _approved_live_scheduler_gate():
    return queue.live_scheduler_execution_decision_payload(
        approval_request_id="approval_1",
        scheduler_background_execution_output=_approved_scheduler_gate(),
        approval_record_provider=_provider("approved"),
    )


def _assert_no_uncontrolled_wiring_or_side_effects(result):
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


def test_production_scheduler_wiring_blocks_without_recorded_approval():
    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=_approved_live_scheduler_gate(),
    )

    assert result["production_scheduler_wiring_gate_enabled"] is True
    assert result["production_scheduler_wiring_decision_enabled"] is True
    assert result["production_scheduler_wiring_allowed"] is False
    assert result["production_scheduler_wiring_status"] == "blocked"
    assert "approval_record_provider_unavailable" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_blocks_missing_record_from_fake_provider():
    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=_approved_live_scheduler_gate(),
        approval_record_provider=lambda approval_request_id: None,
    )

    assert result["production_scheduler_wiring_allowed"] is False
    assert "missing_recorded_approval" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_blocks_non_approved_supported_status():
    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=_approved_live_scheduler_gate(),
        approval_record_provider=_provider("denied"),
    )

    assert result["approval_status"] == "denied"
    assert result["production_scheduler_wiring_allowed"] is False
    assert "approval_status_not_approved" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_blocks_unsupported_approval_status():
    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=_approved_live_scheduler_gate(),
        approval_record_provider=_provider("waiting"),
    )

    assert result["approval_status"] == "waiting"
    assert result["production_scheduler_wiring_allowed"] is False
    assert "unsupported_approval_status" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_blocks_without_approval_gated_execution():
    live_gate = deepcopy(_approved_live_scheduler_gate())
    live_gate["approval_gated_execution_allowed"] = False
    live_gate["approval_gated_execution_status"] = "blocked"

    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=live_gate,
        approval_record_provider=_provider("approved"),
    )

    assert result["production_scheduler_wiring_allowed"] is False
    assert "approval_gated_execution_not_allowed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    assert "approval_gated_execution_status_not_passed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_blocks_without_gated_application_submission():
    live_gate = deepcopy(_approved_live_scheduler_gate())
    live_gate["application_submission_allowed"] = False
    live_gate["application_submission_status"] = "blocked"

    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=live_gate,
        approval_record_provider=_provider("approved"),
    )

    assert result["production_scheduler_wiring_allowed"] is False
    assert "application_submission_not_allowed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    assert "application_submission_status_not_passed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_blocks_without_scheduler_background_decision():
    live_gate = deepcopy(_approved_live_scheduler_gate())
    live_gate["scheduler_background_execution_allowed"] = False
    live_gate["scheduler_background_execution_status"] = "blocked"

    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=live_gate,
        approval_record_provider=_provider("approved"),
    )

    assert result["production_scheduler_wiring_allowed"] is False
    assert "scheduler_background_execution_not_allowed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    assert "scheduler_background_execution_status_not_passed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_blocks_without_live_scheduler_decision():
    live_gate = deepcopy(_approved_live_scheduler_gate())
    live_gate["live_scheduler_execution_allowed"] = False
    live_gate["live_scheduler_execution_status"] = "blocked"

    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=live_gate,
        approval_record_provider=_provider("approved"),
    )

    assert result["production_scheduler_wiring_allowed"] is False
    assert "live_scheduler_execution_not_allowed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    assert "live_scheduler_execution_status_not_passed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_allowed_only_after_all_gates_pass():
    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=_approved_live_scheduler_gate(),
        approval_record_provider=_provider("approved"),
    )

    assert result["approval_status"] == "approved"
    assert result["queue_safety_gate_passed"] is True
    assert result["approval_gated_execution_allowed"] is True
    assert result["application_submission_allowed"] is True
    assert result["scheduler_background_execution_allowed"] is True
    assert result["live_scheduler_execution_allowed"] is True
    assert result["production_scheduler_wiring_allowed"] is True
    assert result["production_scheduler_wiring_status"] == "passed"
    assert result["production_scheduler_wiring_reason_codes"] == []
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_preserves_all_gate_blocks():
    live_gate = deepcopy(_approved_live_scheduler_gate())
    live_gate["blocked_by_queue_safety_gate"] = True
    live_gate["queue_safety_gate_passed"] = False
    live_gate["queue_safety_gate_status"] = "failed"
    live_gate["approval_gated_execution_allowed"] = False
    live_gate["approval_gated_execution_status"] = "blocked"
    live_gate["application_submission_allowed"] = False
    live_gate["application_submission_status"] = "blocked"
    live_gate["scheduler_background_execution_allowed"] = False
    live_gate["scheduler_background_execution_status"] = "blocked"
    live_gate["live_scheduler_execution_allowed"] = False
    live_gate["live_scheduler_execution_status"] = "blocked"

    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=live_gate,
        approval_record_provider=_provider("approved"),
    )

    assert result["production_scheduler_wiring_allowed"] is False
    assert "queue_safety_gate_blocked" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    assert "approval_gated_execution_not_allowed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    assert "application_submission_not_allowed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    assert "scheduler_background_execution_not_allowed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    assert "live_scheduler_execution_not_allowed" in result[
        "production_scheduler_wiring_reason_codes"
    ]
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_uses_fakeable_storage_boundary():
    calls = []

    def fake_provider(approval_request_id):
        calls.append(approval_request_id)
        return {"approval_request_id": approval_request_id, "approval_status": "approved"}

    result = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=_approved_live_scheduler_gate(),
        approval_record_provider=fake_provider,
    )

    assert calls == ["approval_1"]
    assert result["production_scheduler_wiring_allowed"] is True
    _assert_no_uncontrolled_wiring_or_side_effects(result)


def test_production_scheduler_wiring_queue_boundary_has_no_worker_or_migration_constructs():
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
    ]
    for token in forbidden_tokens:
        assert token not in source
