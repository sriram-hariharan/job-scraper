from copy import deepcopy

from src.agents import workflow_runner
from src.app import services


def _healthy_workflow_runner_result():
    return workflow_runner.run_agentic_workflow_dry_run()


def _assert_app_service_blocked(result, expected_reason_code):
    assert result["blocked_by_app_service_safety_gate"] is True
    assert result["app_service_safety_gate_enabled"] is True
    assert result["app_service_safety_gate_passed"] is False
    assert result["app_service_safety_gate_status"] == "failed"
    assert expected_reason_code in result["app_service_safety_gate_reason_codes"]
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_app_service_safety_gate_allows_healthy_workflow_runner_dry_run():
    result = services.app_service_agentic_workflow_safety_gate_payload(
        _healthy_workflow_runner_result()
    )

    assert result["app_service_safety_gate_enabled"] is True
    assert result["app_service_safety_gate_passed"] is True
    assert result["app_service_safety_gate_status"] == "passed"
    assert result["app_service_safety_gate_reason_codes"] == []
    assert result["blocked_by_app_service_safety_gate"] is False
    assert result["blocked_by_fixture_validation_gate"] is False
    assert result["fixture_validation_gate_passed"] is True
    assert result["fixture_validation_gate_status"] == "passed"
    assert result["fixture_validation"]["fixture_validation_passed"] is True
    assert result["executable_adapter_count"] == 0
    assert result["allow_agent_execution"] is False
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_app_service_safety_gate_runs_workflow_runner_dry_run_when_no_payload_given():
    result = services.app_service_agentic_workflow_safety_gate_payload()

    assert result["runner_version"] == "agentic_workflow_runner_v1"
    assert result["execution_mode"] == "dry_run"
    assert result["app_service_safety_gate_passed"] is True
    assert result["blocked_by_app_service_safety_gate"] is False


def test_app_service_safety_gate_blocks_workflow_runner_fixture_gate_block():
    payload = _healthy_workflow_runner_result()
    payload["blocked_by_fixture_validation_gate"] = True
    payload["fixture_validation_gate_passed"] = False
    payload["fixture_validation_gate_status"] = "failed"
    payload["fixture_validation_gate_reason_codes"] = ["fixture_validation_not_passed"]

    result = services.app_service_agentic_workflow_safety_gate_payload(payload)

    _assert_app_service_blocked(
        result,
        "workflow_runner_fixture_validation_gate_blocked",
    )
    assert result["blocked_by_fixture_validation_gate"] is True


def test_app_service_safety_gate_blocks_missing_fixture_validation():
    payload = _healthy_workflow_runner_result()
    payload.pop("fixture_validation")

    result = services.app_service_agentic_workflow_safety_gate_payload(payload)

    _assert_app_service_blocked(result, "missing_fixture_validation")
    assert "missing_workflow_runner_gate_field:fixture_validation" in result[
        "app_service_safety_gate_reason_codes"
    ]


def test_app_service_safety_gate_blocks_failed_fixture_validation():
    payload = _healthy_workflow_runner_result()
    payload["fixture_validation"] = deepcopy(payload["fixture_validation"])
    payload["fixture_validation"]["fixture_validation_passed"] = False
    payload["fixture_validation"]["fixture_validation_status"] = "failed"

    result = services.app_service_agentic_workflow_safety_gate_payload(payload)

    _assert_app_service_blocked(result, "fixture_validation_failed")
    assert "fixture_validation_status_not_passed" in result[
        "app_service_safety_gate_reason_codes"
    ]


def test_app_service_safety_gate_blocks_executable_adapter_count():
    payload = _healthy_workflow_runner_result()
    payload["executable_adapter_count"] = 1

    result = services.app_service_agentic_workflow_safety_gate_payload(payload)

    _assert_app_service_blocked(result, "executable_adapter_count_nonzero")


def test_app_service_safety_gate_blocks_allow_agent_execution_true():
    payload = _healthy_workflow_runner_result()
    payload["allow_agent_execution"] = True

    result = services.app_service_agentic_workflow_safety_gate_payload(payload)

    _assert_app_service_blocked(result, "allow_agent_execution_true")


def test_app_service_safety_gate_blocks_did_execute_count_nonzero():
    payload = _healthy_workflow_runner_result()
    payload["did_execute_count"] = 1

    result = services.app_service_agentic_workflow_safety_gate_payload(payload)

    _assert_app_service_blocked(result, "did_execute_count_nonzero")


def test_app_service_safety_gate_blocks_did_execute_live_true():
    payload = _healthy_workflow_runner_result()
    payload["did_execute_live"] = True

    result = services.app_service_agentic_workflow_safety_gate_payload(payload)

    _assert_app_service_blocked(result, "did_execute_live_true")


def test_app_service_safety_gate_blocks_did_mutate_production_true():
    payload = _healthy_workflow_runner_result()
    payload["did_mutate_production"] = True

    result = services.app_service_agentic_workflow_safety_gate_payload(payload)

    _assert_app_service_blocked(result, "did_mutate_production_true")


def test_app_service_safety_gate_blocks_did_write_db_true():
    payload = _healthy_workflow_runner_result()
    payload["did_write_db"] = True

    result = services.app_service_agentic_workflow_safety_gate_payload(payload)

    _assert_app_service_blocked(result, "did_write_db_true")
