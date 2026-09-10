from __future__ import annotations

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import api, services
from src.storage.saved_scans import read_postgres
from tests.test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off import (
    _state_request,
    _stored_scan_payload,
    _valid_provider_payload as _valid_tailoring_provider_payload,
)
from tests.test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off import (
    _aws_scaffold_stored_scan_payload,
    _refined_aws_provider_payload,
    _valid_exact_provider_payload,
)


ALL_CHAIN_STAGES = [
    "live_exact_resume_change_proposal",
    "manual_exact_change_acceptance",
    "guarded_resume_copy_artifact",
    "guarded_resume_copy_artifact_verification",
    "verified_artifact_operator_review_packet",
    "verified_artifact_operator_decision",
    "application_readiness_packet",
    "manual_application_handoff_packet",
    "handoff_audit_trail",
    "safety_boundary_summary",
    "workflow_readiness_checkpoint",
]


def _stateful_storage(
    monkeypatch,
    *,
    owner: str = "owner-71b",
    stored_payload: dict | None = None,
):
    stored = deepcopy(stored_payload or _stored_scan_payload())
    original = deepcopy(stored)
    calls = {"get": [], "diagnostic_save": [], "draft_save": []}

    def get_saved_scan(**kwargs):
        calls["get"].append(deepcopy(kwargs))
        if kwargs.get("owner_user_id") != owner:
            return {"scan": {}}
        return deepcopy(stored)

    def save_diagnostic(**kwargs):
        calls["diagnostic_save"].append(deepcopy(kwargs))
        if kwargs.get("owner_user_id") != owner:
            return {"ok": False, "updated": False}
        stored["scan"]["payload_json"]["scan_review_payload"]["diagnostic_state"] = deepcopy(
            kwargs["diagnostic_state"]
        )
        return {"ok": True, "updated": True}

    def save_draft(**kwargs):
        calls["draft_save"].append(deepcopy(kwargs))
        return {"ok": True}

    monkeypatch.setattr(services, "get_saved_scan_postgres_payload", get_saved_scan)
    monkeypatch.setattr(
        services,
        "save_saved_scan_diagnostic_state_postgres_payload",
        save_diagnostic,
    )
    monkeypatch.setattr(services, "save_saved_scan_draft_postgres_payload", save_draft)
    return stored, original, calls


def test_diagnostics_only_execution_preserves_workspace_draft_and_reloads(monkeypatch):
    stored, original, calls = _stateful_storage(monkeypatch)

    payload = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=["live_exact_resume_change_proposal"],
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
    )

    assert calls["draft_save"] == []
    assert payload["ordinary_draft_updated"] is False
    review = stored["scan"]["payload_json"]["scan_review_payload"]
    assert review["draft"] == original["scan"]["payload_json"]["scan_review_payload"]["draft"]
    assert review["draft"] == _state_request()
    assert review["diagnostic_state"]["validated_readbacks"]
    assert "stage_results" not in review["diagnostic_state"]["readbacks"][
        "live_exact_resume_change_proposal_readback"
    ]

    reloaded = services.saved_scan_report_payload(
        "phase56a-scan", owner_user_id="owner-71b"
    )
    assert reloaded["diagnostic_state"] == review["diagnostic_state"]
    assert reloaded["scan_review_payload"]["draft"] == _state_request()


def test_persisted_diagnostic_readback_uses_provider_refined_text(monkeypatch):
    stored, _original, calls = _stateful_storage(
        monkeypatch,
        stored_payload=_aws_scaffold_stored_scan_payload(),
    )
    provider_requests = []

    payload = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=["live_exact_resume_change_proposal"],
        live_exact_resume_change_proposal_adapter=lambda request: (
            provider_requests.append(deepcopy(request))
            or _refined_aws_provider_payload(request)
        ),
    )

    scaffold = provider_requests[0]["included_change_proposals"][0]
    assert scaffold["proposed_text"].endswith("[Emphasize: AWS]")
    persisted = stored["scan"]["payload_json"]["scan_review_payload"][
        "diagnostic_state"
    ]
    preview = persisted["readbacks"][
        "live_exact_resume_change_proposal_readback"
    ]["proposed_changes_preview"][0]
    assert preview["proposed_text"] == "Built AWS S3 data pipelines with Databricks."
    assert preview["proposal_id"] == scaffold["proposal_id"]
    assert preview["target_identifier"] == scaffold["target_identifier"]
    assert payload["stage_results"][0]["valid"] is True
    assert calls["diagnostic_save"]


def test_full_chain_propagates_validated_ids_and_preserves_human_gates(monkeypatch):
    _stored, _original, calls = _stateful_storage(monkeypatch)
    provider_calls = []

    payload = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=list(reversed(ALL_CHAIN_STAGES)) + ALL_CHAIN_STAGES,
        accepted_exact_change_proposal_ids=["phase42a-001"],
        verified_artifact_operator_decision_value="accepted",
        live_exact_resume_change_proposal_adapter=lambda request: provider_calls.append(request)
        or _valid_exact_provider_payload(),
    )

    assert payload["requested_stages"] == ALL_CHAIN_STAGES
    assert len(provider_calls) == 1
    assert len(payload["stage_results"]) == len(ALL_CHAIN_STAGES)
    assert all(result["valid"] for result in payload["stage_results"])
    assert payload["manual_exact_change_acceptance_readback"][
        "accepted_proposal_ids"
    ] == ["phase42a-001"]
    assert payload["guarded_resume_copy_artifact_readback"]["artifact_created"] is True
    assert payload["guarded_resume_copy_artifact_verification_readback"][
        "artifact_verification_passed"
    ] is True
    assert payload["verified_artifact_operator_review_packet_readback"][
        "operator_review_packet_created"
    ] is True
    assert payload["verified_artifact_operator_decision_readback"][
        "operator_decision_value"
    ] == "accepted"
    assert payload["operator_approved_artifact_application_readiness_packet_readback"][
        "application_readiness_packet_created"
    ] is True
    assert payload["human_only_manual_application_handoff_packet_readback"][
        "manual_handoff_packet_created"
    ] is True
    assert payload["human_only_handoff_audit_trail_readback"][
        "handoff_audit_trail_created"
    ] is True
    assert payload["human_only_safety_boundary_summary_readback"][
        "safety_boundary_summary_created"
    ] is True
    assert payload["human_only_workflow_readiness_checkpoint_readback"][
        "workflow_readiness_checkpoint_created"
    ] is True
    assert calls["draft_save"] == []


@pytest.mark.parametrize(
    ("stages", "kwargs", "readback_key", "error"),
    [
        (
            ["manual_exact_change_acceptance"],
            {},
            "manual_exact_change_acceptance_readback",
            "accepted_proposal_ids_required",
        ),
        (
            ["verified_artifact_operator_decision"],
            {},
            "verified_artifact_operator_decision_readback",
            "operator_review_packet_id_required",
        ),
    ],
)
def test_human_gates_fail_bounded_without_provider_rerun(
    monkeypatch, stages, kwargs, readback_key, error
):
    _stateful_storage(monkeypatch)
    provider_calls = []
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request),
    )

    payload = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=stages,
        **kwargs,
    )

    assert payload[readback_key]["validation_status"] == "fallback"
    assert error in payload[readback_key]["validation_errors"]
    assert provider_calls == []
    assert payload["diagnostic_state"]["last_execution"]["provider_retry_performed"] is False


def test_owner_scope_and_zero_row_update_fail_with_same_neutral_error(monkeypatch):
    _stateful_storage(monkeypatch)
    with pytest.raises(services.SavedScanDiagnosticsNotFoundError, match="Saved scan was not found"):
        services.execute_saved_scan_diagnostics_payload(
            scan_id="phase56a-scan",
            owner_user_id="foreign-owner",
            diagnostic_stages=["manual_exact_change_acceptance"],
        )

    _stateful_storage(monkeypatch)
    monkeypatch.setattr(
        services,
        "save_saved_scan_diagnostic_state_postgres_payload",
        lambda **_kwargs: {"ok": False, "updated": False},
    )
    with pytest.raises(services.SavedScanDiagnosticsNotFoundError, match="Saved scan was not found"):
        services.execute_saved_scan_diagnostics_payload(
            scan_id="phase56a-scan",
            owner_user_id="owner-71b",
            diagnostic_stages=["manual_exact_change_acceptance"],
        )


def test_invalid_manual_override_is_not_persisted(monkeypatch):
    stored, _original, _calls = _stateful_storage(monkeypatch)
    services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=[
            "live_exact_resume_change_proposal",
            "manual_exact_change_acceptance",
            "guarded_resume_copy_artifact",
        ],
        accepted_exact_change_proposal_ids=["phase42a-001"],
        approved_change_plan_id="foreign-looking-plan-id",
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
    )

    persisted = stored["scan"]["payload_json"]["scan_review_payload"]["diagnostic_state"]
    failed = persisted["readbacks"]["guarded_resume_copy_artifact_readback"]
    assert failed["validation_status"] == "fallback"
    assert "approved_change_plan_id" not in failed
    assert "foreign-looking-plan-id" not in str(persisted)
    assert "guarded_resume_copy_artifact_readback" not in persisted["validated_readbacks"]


def test_failed_new_human_input_cannot_advance_an_older_validated_chain(monkeypatch):
    stored, _original, _calls = _stateful_storage(monkeypatch)
    services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=[
            "live_exact_resume_change_proposal",
            "manual_exact_change_acceptance",
        ],
        accepted_exact_change_proposal_ids=["phase42a-001"],
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
    )

    payload = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=[
            "manual_exact_change_acceptance",
            "guarded_resume_copy_artifact",
        ],
        accepted_exact_change_proposal_ids=["foreign-proposal-id"],
    )

    assert payload["stage_results"][0]["valid"] is False
    assert payload["stage_results"][1]["valid"] is False
    persisted = stored["scan"]["payload_json"]["scan_review_payload"]["diagnostic_state"]
    assert persisted["human_inputs"]["accepted_exact_change_proposal_ids"] == [
        "phase42a-001"
    ]
    assert "foreign-proposal-id" not in str(persisted)


def test_independent_tailoring_stage_does_not_invalidate_exact_change_chain(monkeypatch):
    stored, _original, _calls = _stateful_storage(monkeypatch)
    services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=ALL_CHAIN_STAGES,
        accepted_exact_change_proposal_ids=["phase42a-001"],
        verified_artifact_operator_decision_value="accepted",
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
    )
    services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=["live_tailoring_suggestion"],
        live_tailoring_suggestion_adapter=lambda _request: _valid_tailoring_provider_payload(),
    )

    validated = stored["scan"]["payload_json"]["scan_review_payload"][
        "diagnostic_state"
    ]["validated_readbacks"]
    assert "live_tailoring_suggestion_readback" in validated
    assert "human_only_workflow_readiness_checkpoint_readback" in validated


def test_api_discriminator_preserves_ordinary_contract(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda _request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda _request: "owner-71b")
    ordinary_calls = []
    diagnostic_calls = []
    monkeypatch.setattr(
        services,
        "save_saved_scan_state_payload",
        lambda **kwargs: ordinary_calls.append(kwargs) or {"ok": True, "mode": "ordinary"},
    )
    monkeypatch.setattr(
        services,
        "execute_saved_scan_diagnostics_payload",
        lambda **kwargs: diagnostic_calls.append(kwargs) or {"ok": True, "mode": "diagnostic"},
    )
    client = TestClient(api.app)

    ordinary = client.post("/planning/saved-scan/scan-a/state", json=_state_request())
    diagnostic = client.post(
        "/planning/saved-scan/scan-a/state",
        json={
            "diagnostics_execution": True,
            "diagnostic_stages": ["manual_exact_change_acceptance"],
        },
    )

    assert ordinary.status_code == 200
    assert ordinary.json()["mode"] == "ordinary"
    assert diagnostic.status_code == 200
    assert diagnostic.json()["mode"] == "diagnostic"
    assert len(ordinary_calls) == 1
    assert len(diagnostic_calls) == 1
    assert diagnostic_calls[0]["diagnostic_stages"] == ["manual_exact_change_acceptance"]


def test_api_foreign_scan_failure_is_neutral_not_found(monkeypatch):
    _stateful_storage(monkeypatch, owner="owner-71b")
    monkeypatch.setattr(api, "auth_guard_response", lambda _request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda _request: "foreign-owner")

    response = TestClient(api.app).post(
        "/planning/saved-scan/phase56a-scan/state",
        json={
            "diagnostics_execution": True,
            "diagnostic_stages": ["manual_exact_change_acceptance"],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved scan was not found."


def test_storage_merge_is_owner_scoped_and_detects_zero_rows(monkeypatch):
    captured = []
    monkeypatch.setattr(
        read_postgres,
        "_run_psql_command",
        lambda **kwargs: {"command": [], "command_text": kwargs["sql"]},
    )

    def query(**kwargs):
        captured.append(kwargs["sql"])
        return {"data": {"updated": False, "scan_id": ""}, "command": [], "command_text": ""}

    monkeypatch.setattr(read_postgres, "_run_psql_json_query", query)
    result = read_postgres.save_saved_scan_diagnostic_state_postgres_payload(
        scan_id="scan-a",
        owner_user_id="owner-a",
        diagnostic_state={"version": 1},
    )

    assert result["ok"] is False
    assert result["updated"] is False
    sql = captured[0]
    assert "'{scan_review_payload,diagnostic_state}'" in sql
    assert "owner_user_id = 'owner-a'" in sql
    assert "RETURNING scan_id" in sql
    assert "{scan_review_payload,draft}" not in sql


def test_runtime_boundary_has_no_application_queue_or_resume_mutation_calls():
    source = services.execute_saved_scan_diagnostics_payload.__code__.co_names
    assert "save_saved_scan_draft_postgres_payload" not in source
    assert "insert_application_action" not in source
    assert "enqueue" not in source
    assert "scheduler" not in source
    assert "pipeline" not in source
