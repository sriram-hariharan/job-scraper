from copy import deepcopy

import application_execution_queue as queue
from src.app import services


def _healthy_app_service_payload():
    return services.app_service_agentic_workflow_safety_gate_payload()


def _assert_queue_blocked(result, expected_reason_code):
    assert result["blocked_by_queue_safety_gate"] is True
    assert result["queue_safety_gate_enabled"] is True
    assert result["queue_safety_gate_passed"] is False
    assert result["queue_safety_gate_status"] == "failed"
    assert expected_reason_code in result["queue_safety_gate_reason_codes"]
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_queue_safety_gate_allows_healthy_app_service_gated_payload():
    result = queue.queue_safety_gate_payload(_healthy_app_service_payload())

    assert result["queue_safety_gate_enabled"] is True
    assert result["queue_safety_gate_passed"] is True
    assert result["queue_safety_gate_status"] == "passed"
    assert result["queue_safety_gate_reason_codes"] == []
    assert result["blocked_by_queue_safety_gate"] is False
    assert result["blocked_by_app_service_safety_gate"] is False
    assert result["blocked_by_fixture_validation_gate"] is False
    assert result["fixture_validation"]["fixture_validation_passed"] is True
    assert result["executable_adapter_count"] == 0
    assert result["allow_agent_execution"] is False
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_queue_safety_gate_runs_app_service_gate_when_no_payload_given():
    result = queue.queue_safety_gate_payload()

    assert result["app_service_safety_gate_passed"] is True
    assert result["queue_safety_gate_passed"] is True
    assert result["blocked_by_queue_safety_gate"] is False


def test_queue_safety_gate_blocks_missing_app_service_output():
    result = queue.queue_safety_gate_payload(None)

    _assert_queue_blocked(result, "missing_app_service_safety_gate_output")


def test_queue_safety_gate_blocks_app_service_gate_block():
    payload = _healthy_app_service_payload()
    payload["blocked_by_app_service_safety_gate"] = True
    payload["app_service_safety_gate_passed"] = False
    payload["app_service_safety_gate_status"] = "failed"

    result = queue.queue_safety_gate_payload(payload)

    _assert_queue_blocked(result, "app_service_safety_gate_blocked")
    assert result["blocked_by_app_service_safety_gate"] is True


def test_queue_safety_gate_blocks_workflow_runner_fixture_gate_block():
    payload = _healthy_app_service_payload()
    payload["blocked_by_fixture_validation_gate"] = True
    payload["fixture_validation_gate_passed"] = False
    payload["fixture_validation_gate_status"] = "failed"

    result = queue.queue_safety_gate_payload(payload)

    _assert_queue_blocked(result, "workflow_runner_fixture_validation_gate_blocked")
    assert result["blocked_by_fixture_validation_gate"] is True


def test_queue_safety_gate_blocks_missing_fixture_validation():
    payload = _healthy_app_service_payload()
    payload.pop("fixture_validation")

    result = queue.queue_safety_gate_payload(payload)

    _assert_queue_blocked(result, "missing_fixture_validation")


def test_queue_safety_gate_blocks_failed_fixture_validation():
    payload = _healthy_app_service_payload()
    payload["fixture_validation"] = deepcopy(payload["fixture_validation"])
    payload["fixture_validation"]["fixture_validation_passed"] = False
    payload["fixture_validation"]["fixture_validation_status"] = "failed"

    result = queue.queue_safety_gate_payload(payload)

    _assert_queue_blocked(result, "fixture_validation_failed")
    assert "fixture_validation_status_not_passed" in result[
        "queue_safety_gate_reason_codes"
    ]


def test_queue_safety_gate_blocks_executable_adapter_count():
    payload = _healthy_app_service_payload()
    payload["executable_adapter_count"] = 1

    result = queue.queue_safety_gate_payload(payload)

    _assert_queue_blocked(result, "executable_adapter_count_nonzero")


def test_queue_safety_gate_blocks_allow_agent_execution_true():
    payload = _healthy_app_service_payload()
    payload["allow_agent_execution"] = True

    result = queue.queue_safety_gate_payload(payload)

    _assert_queue_blocked(result, "allow_agent_execution_true")


def test_queue_safety_gate_blocks_did_execute_count_nonzero():
    payload = _healthy_app_service_payload()
    payload["did_execute_count"] = 1

    result = queue.queue_safety_gate_payload(payload)

    _assert_queue_blocked(result, "did_execute_count_nonzero")


def test_queue_safety_gate_blocks_did_execute_live_true():
    payload = _healthy_app_service_payload()
    payload["did_execute_live"] = True

    result = queue.queue_safety_gate_payload(payload)

    _assert_queue_blocked(result, "did_execute_live_true")


def test_queue_safety_gate_blocks_did_mutate_production_true():
    payload = _healthy_app_service_payload()
    payload["did_mutate_production"] = True

    result = queue.queue_safety_gate_payload(payload)

    _assert_queue_blocked(result, "did_mutate_production_true")


def test_queue_safety_gate_blocks_did_write_db_true():
    payload = _healthy_app_service_payload()
    payload["did_write_db"] = True

    result = queue.queue_safety_gate_payload(payload)

    _assert_queue_blocked(result, "did_write_db_true")
