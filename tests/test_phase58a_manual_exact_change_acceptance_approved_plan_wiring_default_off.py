from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from tests.support.phase_guard_registry import assert_protected_hashes

from fastapi.testclient import TestClient

from src.app import api, services
from tests.test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off import (
    _patch_storage,
    _state_request,
    _stored_scan_payload,
    _valid_provider_payload as _valid_tailoring_provider_payload,
)
from tests.test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off import (
    _valid_exact_provider_payload,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase58_manual_exact_change_acceptance_approved_plan_wiring_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "f56624b5b3c7e2bb01a824386b86fbc2a194e727f0437ca0773764eae64ec941",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_" + "suggestions" + ".py": (
        "570d47a62385b736eadbf107e8f28a35aa3818e864f4d950fcb7a6c54e326a3d"
    ),
    "application_execution_" + "queue" + ".py": (
        "9bb4530b5a308356b908a958456ff18415c19e264b5e1c030fe8828d6caa481f"
    ),
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-58a")
    return TestClient(api.app)


# The shared _stored_scan_payload() fixture yields exactly one upstream
# candidate, so production (correctly) knows only "phase42a-001". Tests that
# genuinely need a second VALID-but-unaccepted proposal build a test-local
# two-candidate upstream payload here instead of mutating the shared fixture
# or inventing a provider-side proposal id, which require_known_proposal_ids
# rightly rejects.
KNOWN_PROPOSAL_ID = "phase42a-001"
SECOND_KNOWN_PROPOSAL_ID = "phase42a-002"


def _two_candidate_stored_payload() -> dict:
    stored = deepcopy(_stored_scan_payload())
    matched_evidence = (
        stored["scan"]["payload_json"]["scan_review_payload"]
        ["scan_issue_contract"]["matched_evidence"]
    )
    matched_evidence.append(
        {
            **deepcopy(matched_evidence[0]),
            "candidate_id": "candidate-2",
            "bullet_id": "bullet-2",
            "signal": "Airflow",
            "evidence": "Automated Airflow DAGs.",
        }
    )
    return stored


def _two_proposal_provider_payload() -> dict:
    """Refine BOTH known upstream candidates, inventing no proposal id."""

    payload = _valid_exact_provider_payload()
    first = payload["refined_change_proposals"][0]
    # Identity fields must match the upstream candidate exactly; the second
    # candidate targets the same "skills" section with the Airflow signal.
    payload["refined_change_proposals"].append(
        {
            **deepcopy(first),
            "proposal_id": SECOND_KNOWN_PROPOSAL_ID,
            "change_type": "skill",
            "target_section": "skills",
            "target_identifier": "skills",
            "current_text": "",
            "proposed_text": "Airflow",
            "change_reason": (
                "Surface supplied Airflow evidence in the skills target."
            ),
            "jd_terms_supported": ["Airflow"],
            "resume_evidence_used": ["Automated Airflow DAGs."],
        }
    )
    return payload


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def test_default_off_planning_workspace_action_does_not_create_approved_plan(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _valid_exact_provider_payload(),
    )

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        accepted_exact_change_proposal_ids=["phase42a-001"],
    )

    readback = payload["manual_exact_change_acceptance_readback"]
    assert calls == []
    assert readback["manual_acceptance_enabled"] is False
    assert readback["manual_acceptance_performed"] is False
    assert readback["approved_change_plan_created"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "disabled"
    assert readback["accepted_proposal_count"] == 0


def test_enabled_action_creates_plan_only_from_explicitly_accepted_ids(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase42a-001"],
    )

    readback = payload["manual_exact_change_acceptance_readback"]
    assert readback["manual_acceptance_enabled"] is True
    assert readback["manual_acceptance_performed"] is True
    assert readback["approved_change_plan_created"] is True
    assert readback["accepted_proposal_count"] == 1
    assert readback["accepted_proposal_ids"] == ["phase42a-001"]
    assert readback["stable_accepted_proposal_keys"] == ["phase42a-001"]
    packet = readback["approved_change_plan_packet"]
    assert packet["payload_type"] == "exact_resume_change_set_approved_change_plan_packet"
    assert [row["proposal_id"] for row in packet["approved_changes"]] == [
        "phase42a-001"
    ]
    assert packet["artifact_created"] is False
    assert packet["resume_change_applied"] is False


def test_unaccepted_proposal_ids_are_not_included(monkeypatch):
    # Two genuinely KNOWN upstream candidates: one accepted, one deliberately
    # left unaccepted. No provider-invented proposal id is used, so
    # require_known_proposal_ids=True stays fully in force.
    provider_payload = _two_proposal_provider_payload()
    _patch_storage(monkeypatch, stored_payload=_two_candidate_stored_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: provider_payload,
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=[KNOWN_PROPOSAL_ID],
    )

    readback = payload["manual_exact_change_acceptance_readback"]
    assert readback["validation_status"] != "fallback"
    approved = readback["approved_change_plan_packet"]["approved_changes"]
    assert [row["proposal_id"] for row in approved] == [KNOWN_PROPOSAL_ID]
    # The second proposal is valid and known, but was not accepted.
    assert readback["skipped_proposal_ids"] == [SECOND_KNOWN_PROPOSAL_ID]
    assert readback["rejected_proposal_count"] == 1


def test_missing_or_invalid_proposal_ids_fallback_safely(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    missing = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=[],
    )["manual_exact_change_acceptance_readback"]
    invalid = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["unknown-proposal"],
    )["manual_exact_change_acceptance_readback"]

    assert missing["approved_change_plan_created"] is False
    assert missing["validation_status"] == "fallback"
    assert missing["fallback_reason"] == "accepted_proposal_ids_required"
    assert invalid["approved_change_plan_created"] is False
    assert invalid["validation_status"] == "fallback"
    assert invalid["fallback_reason"] == "unknown_accepted_proposal_ids"
    assert invalid["invalid_proposal_ids"] == ["unknown-proposal"]


def test_manual_acceptance_does_not_call_live_llm_or_provider(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase42a-001"],
    )
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _valid_exact_provider_payload(),
    )
    readback = services._planning_workspace_manual_exact_change_acceptance_payload(
        live_exact_change_readback=payload["live_exact_resume_change_proposal_readback"],
        enabled=True,
        accepted_proposal_ids=["phase42a-001"],
    )

    assert calls == []
    assert readback["approved_change_plan_created"] is True
    assert readback["safety"]["provider_call_performed"] is False
    assert readback["safety"]["llm_call_performed"] is False


def test_phase55_phase56_and_phase57_readbacks_remain_intact(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_tailoring_provider_payload(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase42a-001"],
    )

    stored_review = _stored_scan_payload()["scan"]["payload_json"]["scan_review_payload"]
    assert stored_review["jd_llm_extraction_readback"]["validation_status"] == "valid"
    assert payload["live_tailoring_suggestion_readback"]["tailoring_llm_call_performed"] is True
    assert payload["live_exact_resume_change_proposal_readback"]["exact_change_llm_call_performed"] is True
    assert payload["manual_exact_change_acceptance_readback"]["approved_change_plan_created"] is True


def test_api_acceptance_readback_and_request_fields(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda _request: _valid_exact_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {
            **_state_request(),
            "enable_live_exact_resume_change_proposal": True,
            "enable_manual_exact_change_acceptance": True,
            "accepted_exact_change_proposal_ids": ["phase42a-001"],
        },
    )

    readback = payload["manual_exact_change_acceptance_readback"]
    assert readback["api_readback"] is True
    assert readback["ui_readback"] is True
    assert readback["accepted_proposal_ids"] == ["phase42a-001"]
    assert payload["draft"]["accepted_exact_change_proposal_ids"] == [
        "phase42a-001"
    ]


def test_ui_readback_display_is_passive_and_posts_explicit_acceptance_fields():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split("function getScanWorkspaceManualExactChangeAcceptancePayload", 1)[1].split(
        "function renderScanWorkspaceManualExactChangeAcceptanceReadback",
        1,
    )[0]
    renderer = script.split("function renderScanWorkspaceManualExactChangeAcceptanceReadback", 1)[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "manual_exact_change_acceptance_readback" in getter
    assert "accepted_exact_change_proposal_ids" in script
    assert "enable_manual_exact_change_acceptance" in script
    assert "approved_change_plan_created" in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_mutation_artifact_application_or_scoring_side_effects(monkeypatch):
    request = _state_request()
    original = deepcopy(request)
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **request,
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase42a-001"],
    )

    assert request == original
    safety = payload["manual_exact_change_acceptance_readback"]["safety"]
    assert safety["resume_mutation_performed"] is False
    assert safety["resume_artifact_created"] is False
    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["auto_apply_performed"] is False
    assert safety["scoring_formula_changed"] is False
    assert safety["scoring_weights_changed"] is False


def test_protected_files_are_unchanged():
    assert_protected_hashes(
        ROOT,
        PROTECTED_HASHES,
        compatibility_profiles=(
            "phase1_ai_provider_model_routing_hash_maintenance",
        ),
    )


def test_docs_include_phase58_safety_and_wiring_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "manual exact change acceptance",
        "approved-change plan wiring",
        "planning workspace action",
        "deterministic fallback",
        "no live llm call",
        "no resume mutation",
        "no resume artifact creation",
        "no application execution",
        "no auto-apply",
    ):
        assert marker in text
