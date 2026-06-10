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


def _assert_no_scheduler_or_live_submission(result):
    assert result["scheduler_background_execution_enabled"] is False
    assert result["live_scheduler_enabled"] is False
    assert result["automatic_submission_loop_enabled"] is False
    assert result["live_execution_enabled"] is False
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False
    assert result["did_submit_application"] is False


def test_application_submission_blocks_without_recorded_approval():
    result = queue.application_submission_decision_payload(
        approval_request_id="approval_1",
        approval_gated_execution_output=_approved_execution_gate(),
    )

    assert result["application_submission_gate_enabled"] is True
    assert result["application_submission_allowed"] is False
    assert result["application_submission_status"] == "blocked"
    assert "approval_record_provider_unavailable" in result[
        "application_submission_reason_codes"
    ]
    _assert_no_scheduler_or_live_submission(result)


def test_application_submission_blocks_non_approved_supported_status():
    result = queue.application_submission_decision_payload(
        approval_request_id="approval_1",
        approval_gated_execution_output=_approved_execution_gate(),
        approval_record_provider=_provider("denied"),
    )

    assert result["approval_status"] == "denied"
    assert result["application_submission_allowed"] is False
    assert "approval_status_not_approved" in result[
        "application_submission_reason_codes"
    ]
    _assert_no_scheduler_or_live_submission(result)


def test_application_submission_blocks_unsupported_approval_status():
    result = queue.application_submission_decision_payload(
        approval_request_id="approval_1",
        approval_gated_execution_output=_approved_execution_gate(),
        approval_record_provider=_provider("waiting"),
    )

    assert result["approval_status"] == "waiting"
    assert result["application_submission_allowed"] is False
    assert "unsupported_approval_status" in result[
        "application_submission_reason_codes"
    ]
    _assert_no_scheduler_or_live_submission(result)


def test_application_submission_blocks_missing_approval_gated_execution():
    execution_gate = deepcopy(_approved_execution_gate())
    execution_gate["approval_gated_execution_allowed"] = False
    execution_gate["approval_gated_execution_status"] = "blocked"
    execution_gate["approval_gated_execution_reason_codes"] = [
        "approval_record_provider_unavailable"
    ]

    result = queue.application_submission_decision_payload(
        approval_request_id="approval_1",
        approval_gated_execution_output=execution_gate,
        approval_record_provider=_provider("approved"),
    )

    assert result["application_submission_allowed"] is False
    assert "approval_gated_execution_not_allowed" in result[
        "application_submission_reason_codes"
    ]
    assert "approval_gated_execution_status_not_passed" in result[
        "application_submission_reason_codes"
    ]
    _assert_no_scheduler_or_live_submission(result)


def test_application_submission_can_be_marked_allowed_only_after_approval_and_execution_gate():
    result = queue.application_submission_decision_payload(
        approval_request_id="approval_1",
        approval_gated_execution_output=_approved_execution_gate(),
        approval_record_provider=_provider("approved"),
    )

    assert result["approval_status"] == "approved"
    assert result["approval_gated_execution_allowed"] is True
    assert result["approval_gated_execution_status"] == "passed"
    assert result["application_submission_allowed"] is True
    assert result["application_submission_status"] == "passed"
    assert result["application_submission_reason_codes"] == []
    _assert_no_scheduler_or_live_submission(result)


def test_application_submission_preserves_queue_safety_gate_block():
    execution_gate = deepcopy(_approved_execution_gate())
    execution_gate["blocked_by_queue_safety_gate"] = True
    execution_gate["queue_safety_gate_passed"] = False
    execution_gate["queue_safety_gate_status"] = "failed"

    result = queue.application_submission_decision_payload(
        approval_request_id="approval_1",
        approval_gated_execution_output=execution_gate,
        approval_record_provider=_provider("approved"),
    )

    assert result["application_submission_allowed"] is False
    assert "queue_safety_gate_blocked" in result["application_submission_reason_codes"]
    assert "queue_safety_gate_not_passed" in result[
        "application_submission_reason_codes"
    ]
    _assert_no_scheduler_or_live_submission(result)


def test_application_submission_uses_fakeable_storage_boundary():
    calls = []

    def fake_provider(approval_request_id):
        calls.append(approval_request_id)
        return {"approval_request_id": approval_request_id, "approval_status": "approved"}

    result = queue.application_submission_decision_payload(
        approval_request_id="approval_1",
        approval_gated_execution_output=_approved_execution_gate(),
        approval_record_provider=fake_provider,
    )

    assert calls == ["approval_1"]
    assert result["application_submission_allowed"] is True
    _assert_no_scheduler_or_live_submission(result)
