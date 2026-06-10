from copy import deepcopy

import application_execution_queue as queue
from src.app import services


def _healthy_queue_gate():
    return queue.queue_safety_gate_payload(
        services.app_service_agentic_workflow_safety_gate_payload()
    )


def _provider(status):
    def load_approval_record(approval_request_id):
        return {
            "approval_request_id": approval_request_id,
            "approval_status": status,
            "idempotency_key": "idem_1",
        }

    return load_approval_record


def _assert_non_submission(result):
    assert result["application_submission_enabled"] is False
    assert result["scheduler_background_execution_enabled"] is False
    assert result["live_execution_enabled"] is False
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False
    assert result["did_submit_application"] is False


def test_approval_gated_execution_blocks_without_recorded_approval():
    result = queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=_healthy_queue_gate(),
    )

    assert result["approval_gated_execution_enabled"] is True
    assert result["approval_gated_execution_allowed"] is False
    assert result["approval_gated_execution_status"] == "blocked"
    assert "approval_record_provider_unavailable" in result[
        "approval_gated_execution_reason_codes"
    ]
    assert result["queue_safety_gate_passed"] is True
    _assert_non_submission(result)


def test_approval_gated_execution_blocks_missing_record_from_fake_provider():
    result = queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=_healthy_queue_gate(),
        approval_record_provider=lambda approval_request_id: None,
    )

    assert result["approval_gated_execution_allowed"] is False
    assert result["approval_gated_execution_status"] == "blocked"
    assert "missing_recorded_approval" in result[
        "approval_gated_execution_reason_codes"
    ]
    _assert_non_submission(result)


def test_approval_gated_execution_blocks_non_approved_supported_status():
    result = queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=_healthy_queue_gate(),
        approval_record_provider=_provider("denied"),
    )

    assert result["approval_status"] == "denied"
    assert result["approval_gated_execution_allowed"] is False
    assert "approval_status_not_approved" in result[
        "approval_gated_execution_reason_codes"
    ]
    _assert_non_submission(result)


def test_approval_gated_execution_blocks_unsupported_approval_status():
    result = queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=_healthy_queue_gate(),
        approval_record_provider=_provider("waiting"),
    )

    assert result["approval_status"] == "waiting"
    assert result["approval_gated_execution_allowed"] is False
    assert "unsupported_approval_status" in result[
        "approval_gated_execution_reason_codes"
    ]
    _assert_non_submission(result)


def test_approval_gated_execution_allows_only_gate_flag_for_approved_status():
    result = queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=_healthy_queue_gate(),
        approval_record_provider=_provider("approved"),
    )

    assert result["approval_status"] == "approved"
    assert result["approval_gated_execution_allowed"] is True
    assert result["approval_gated_execution_status"] == "passed"
    assert result["approval_gated_execution_reason_codes"] == []
    assert result["queue_safety_gate_passed"] is True
    assert result["blocked_by_queue_safety_gate"] is False
    _assert_non_submission(result)


def test_approval_gated_execution_preserves_queue_safety_gate_block():
    queue_gate = deepcopy(_healthy_queue_gate())
    queue_gate["queue_safety_gate_passed"] = False
    queue_gate["queue_safety_gate_status"] = "failed"
    queue_gate["blocked_by_queue_safety_gate"] = True
    queue_gate["queue_safety_gate_reason_codes"] = ["fixture_validation_failed"]

    result = queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=queue_gate,
        approval_record_provider=_provider("approved"),
    )

    assert result["approval_gated_execution_allowed"] is False
    assert "queue_safety_gate_blocked" in result[
        "approval_gated_execution_reason_codes"
    ]
    assert result["blocked_by_queue_safety_gate"] is True
    _assert_non_submission(result)


def test_approval_gated_execution_uses_fakeable_storage_boundary():
    calls = []

    def fake_provider(approval_request_id):
        calls.append(approval_request_id)
        return {"approval_request_id": approval_request_id, "approval_status": "approved"}

    result = queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=_healthy_queue_gate(),
        approval_record_provider=fake_provider,
    )

    assert calls == ["approval_1"]
    assert result["approval_gated_execution_allowed"] is True
    _assert_non_submission(result)
