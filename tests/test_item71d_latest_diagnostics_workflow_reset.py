from __future__ import annotations

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import api, services
from tests.test_item71b_safe_diagnostics_runtime_foundation import (
    ALL_CHAIN_STAGES,
    _stateful_storage,
)
from tests.test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off import (
    _stored_scan_payload,
)
from tests.test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off import (
    _valid_exact_provider_payload,
)


def _completed_saved_scan_payload() -> dict:
    stored = _stored_scan_payload()
    review = stored["scan"]["payload_json"]["scan_review_payload"]
    review.update(
        {
            "company": "Acme Corp",
            "role": "Staff Engineer",
            "job_description_text": "Persisted job description",
            "source_resume_text": "Persisted source resume",
            "structured_resume_targets": {
                "bullets": [{"target_identifier": "bullet-1"}],
                "skills": [{"target_identifier": "skills"}],
            },
            "personal_details": {"name": "A. Candidate"},
            "unrelated_scan_review_key": {"preserve": True},
            "diagnostic_state": {
                "version": 1,
                "scan_id": "phase56a-scan",
                "updated_at": "2026-08-24T08:05:15+00:00",
                "readbacks": {
                    "live_tailoring_suggestion_readback": {"validation_status": "valid"},
                    "live_exact_resume_change_proposal_readback": {
                        "validation_status": "valid",
                        "proposed_changes_preview": [{"proposal_id": "old-proposal"}],
                    },
                    "manual_exact_change_acceptance_readback": {"approved_change_plan_id": "old-plan"},
                    "guarded_resume_copy_artifact_readback": {"artifact_id": "old-artifact"},
                    "guarded_resume_copy_artifact_verification_readback": {"artifact_id": "old-artifact"},
                    "verified_artifact_operator_review_packet_readback": {"operator_review_packet_id": "old-review"},
                    "verified_artifact_operator_decision_readback": {"operator_decision_id": "old-decision"},
                    "operator_approved_artifact_application_readiness_packet_readback": {"application_readiness_packet_id": "old-ready"},
                    "human_only_manual_application_handoff_packet_readback": {"manual_handoff_packet_id": "old-handoff"},
                    "human_only_handoff_audit_trail_readback": {"handoff_audit_trail_id": "old-audit"},
                    "human_only_safety_boundary_summary_readback": {"safety_boundary_summary_id": "old-safety"},
                    "human_only_workflow_readiness_checkpoint_readback": {"workflow_readiness_checkpoint_id": "old-workflow"},
                },
                "validated_readbacks": {"old_validated": {"validation_status": "valid"}},
                "ambient_readbacks": {"old_ambient": {"validation_status": "valid"}},
                "human_inputs": {
                    "accepted_exact_change_proposal_ids": ["old-proposal"],
                    "verified_artifact_operator_decision_value": "accepted",
                },
                "last_execution": {
                    "requested_stages": list(ALL_CHAIN_STAGES),
                    "stage_results": [{"stage": "workflow_readiness_checkpoint", "valid": True}],
                },
            },
        }
    )
    return stored


def test_reset_replaces_only_diagnostic_state_and_survives_reload(monkeypatch):
    stored, original, calls = _stateful_storage(
        monkeypatch,
        stored_payload=_completed_saved_scan_payload(),
    )
    provider_calls = []
    monkeypatch.setattr(
        services,
        "_live_tailoring_suggestion_provider_adapter",
        lambda request: provider_calls.append(request),
    )
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request),
    )

    payload = services.reset_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
    )

    assert provider_calls == []
    assert len(calls["diagnostic_save"]) == 1
    assert calls["draft_save"] == []
    assert payload["diagnostics_reset"] is True
    assert payload["diagnostics_execution"] is False
    assert payload["requested_stages"] == []
    assert payload["stage_results"] == []

    fresh = payload["diagnostic_state"]
    assert set(fresh) == {
        "version",
        "scan_id",
        "updated_at",
        "readbacks",
        "validated_readbacks",
        "ambient_readbacks",
        "human_inputs",
        "last_execution",
    }
    assert fresh["readbacks"] == {}
    assert fresh["validated_readbacks"] == {}
    assert fresh["human_inputs"] == {}
    assert fresh["last_execution"]["requested_stages"] == []
    assert fresh["last_execution"]["stage_results"] == []
    assert fresh["last_execution"]["diagnostics_reset_performed"] is True
    assert fresh["last_execution"]["provider_retry_performed"] is False
    assert fresh["last_execution"]["background_execution_performed"] is False
    assert not any(
        key in fresh
        for key in ("previous_runs", "run_history", "diagnostic_runs", "run_number", "archived_state", "previous_workflow")
    )
    assert "old-" not in str(fresh)

    before_review = deepcopy(original["scan"]["payload_json"]["scan_review_payload"])
    after_review = deepcopy(stored["scan"]["payload_json"]["scan_review_payload"])
    before_review.pop("diagnostic_state")
    after_review.pop("diagnostic_state")
    assert after_review == before_review
    assert stored["scan"]["resume_name"] == original["scan"]["resume_name"]
    assert stored["scan"]["job_doc_id"] == original["scan"]["job_doc_id"]
    assert after_review["draft"] == before_review["draft"]
    assert after_review["personal_details"] == before_review["personal_details"]
    assert after_review["structured_resume_targets"] == before_review["structured_resume_targets"]
    assert after_review["source_resume_text"] == before_review["source_resume_text"]
    assert after_review["job_description_text"] == before_review["job_description_text"]

    reloaded = services.saved_scan_report_payload(
        "phase56a-scan",
        owner_user_id="owner-71b",
    )
    assert reloaded["diagnostic_state"] == fresh
    assert reloaded["diagnostic_state"]["validated_readbacks"] == {}


def test_reset_is_owner_scoped_and_zero_row_safe(monkeypatch):
    _stateful_storage(
        monkeypatch,
        owner="owner-71b",
        stored_payload=_completed_saved_scan_payload(),
    )
    with pytest.raises(services.SavedScanDiagnosticsNotFoundError, match="Saved scan was not found"):
        services.reset_saved_scan_diagnostics_payload(
            scan_id="phase56a-scan",
            owner_user_id="foreign-owner",
        )

    _stateful_storage(monkeypatch, stored_payload=_completed_saved_scan_payload())
    monkeypatch.setattr(
        services,
        "save_saved_scan_diagnostic_state_postgres_payload",
        lambda **_kwargs: {"ok": False, "updated": False},
    )
    with pytest.raises(services.SavedScanDiagnosticsNotFoundError, match="Saved scan was not found"):
        services.reset_saved_scan_diagnostics_payload(
            scan_id="phase56a-scan",
            owner_user_id="owner-71b",
        )


def test_api_accepts_reset_only_and_rejects_ambiguous_combinations(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda _request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda _request: "owner-71b")
    reset_calls = []
    execution_calls = []
    ordinary_calls = []
    monkeypatch.setattr(
        services,
        "reset_saved_scan_diagnostics_payload",
        lambda **kwargs: reset_calls.append(deepcopy(kwargs)) or {
            "ok": True,
            "diagnostics_reset": True,
            "diagnostic_state": {"readbacks": {}, "validated_readbacks": {}},
        },
    )
    monkeypatch.setattr(
        services,
        "execute_saved_scan_diagnostics_payload",
        lambda **kwargs: execution_calls.append(deepcopy(kwargs)) or {"ok": True},
    )
    monkeypatch.setattr(
        services,
        "save_saved_scan_state_payload",
        lambda **kwargs: ordinary_calls.append(deepcopy(kwargs)) or {"ok": True},
    )
    client = TestClient(api.app)

    response = client.post(
        "/planning/saved-scan/phase56a-scan/state",
        json={"diagnostics_reset": True},
    )
    assert response.status_code == 200
    assert response.json()["diagnostics_reset"] is True
    assert reset_calls == [{"scan_id": "phase56a-scan", "owner_user_id": "owner-71b"}]
    assert execution_calls == []
    assert ordinary_calls == []

    for conflicting in (
        {"diagnostics_execution": True, "diagnostic_stages": ["live_tailoring_suggestion"]},
        {"accepted_exact_change_proposal_ids": ["proposal-1"]},
        {"personal_details": {"name": "Changed"}},
    ):
        rejected = client.post(
            "/planning/saved-scan/phase56a-scan/state",
            json={"diagnostics_reset": True, **conflicting},
        )
        assert rejected.status_code == 400
        assert "diagnostics_reset cannot be combined" in rejected.json()["detail"]

    assert len(reset_calls) == 1
    assert execution_calls == []
    assert ordinary_calls == []


def test_full_deterministic_workflow_can_run_again_after_reset(monkeypatch):
    _stored, _original, calls = _stateful_storage(monkeypatch)
    provider_calls = []

    def exact_adapter(request):
        provider_calls.append(deepcopy(request))
        return _valid_exact_provider_payload()

    first = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=ALL_CHAIN_STAGES,
        accepted_exact_change_proposal_ids=["phase42a-001"],
        verified_artifact_operator_decision_value="accepted",
        live_exact_resume_change_proposal_adapter=exact_adapter,
    )
    first_artifact_id = first["guarded_resume_copy_artifact_readback"]["artifact_id"]
    assert all(result["valid"] for result in first["stage_results"])
    assert len(provider_calls) == 1

    reset = services.reset_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
    )
    assert reset["diagnostic_state"]["readbacks"] == {}
    assert len(provider_calls) == 1

    second = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=ALL_CHAIN_STAGES,
        accepted_exact_change_proposal_ids=["phase42a-001"],
        verified_artifact_operator_decision_value="accepted",
        live_exact_resume_change_proposal_adapter=exact_adapter,
    )
    assert all(result["valid"] for result in second["stage_results"])
    assert second["guarded_resume_copy_artifact_readback"]["artifact_created"] is True
    assert second["guarded_resume_copy_artifact_readback"]["artifact_id"] == first_artifact_id
    assert second["human_only_workflow_readiness_checkpoint_readback"]["workflow_readiness_checkpoint_created"] is True
    assert len(provider_calls) == 2
    assert calls["draft_save"] == []


def test_reset_service_has_no_application_or_provider_authority():
    names = set(services.reset_saved_scan_diagnostics_payload.__code__.co_names)
    for forbidden in (
        "execute_saved_scan_diagnostics_payload",
        "insert_application_action",
        "enqueue",
        "scheduler",
        "save_saved_scan_draft_postgres_payload",
        "delete_saved_scan_payload",
        "unlink",
    ):
        assert forbidden not in names
