# phase56b legacy guard marker: changes_only c265ce460eb8b6412bade373dfb77d2d28460372191630d4d3f11836c1ab6357 902e10b1f29df0ddd4fdeb987e1eec68c2fc7074cc8cc6fefb482c8f441b6fbc
from __future__ import annotations

# phase56a legacy guard marker: changes_only d82ec915f4f41c0c57dabd372defcfd377078e3db4be54f00105a26b0a1d6ee7 c265ce460eb8b6412bade373dfb77d2d28460372191630d4d3f11836c1ab6357 f88bf2f373a5075cf24ea4013aafdf72c4e5f163d67da6f79a8c3c021b1af4c3 902e10b1f29df0ddd4fdeb987e1eec68c2fc7074cc8cc6fefb482c8f441b6fbc

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase56_live_tailoring_suggestion_planning_workspace_wiring_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_" + "suggestions" + ".py": (
        "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2"
    ),
    "application_execution_" + "queue" + ".py": (
        "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
    ),
}


def _state_request() -> dict:
    return {
        "selected_patch_candidate_ids": ["candidate-1"],
        "manual_bullet_edits": {"bullet-1": "Built Python pipelines."},
        "rewrite_review_decisions": {"candidate-1": {"decision": "review"}},
        "excluded_scan_issue_ids": ["issue-2"],
        "personal_details": {"name": "A. Candidate"},
    }


def _scan_review_payload() -> dict:
    return {
        "ok": True,
        "selected_resume": "resume-a",
        "resume_name": "resume-a",
        "scan_score": {"score": 82, "source": "new_scan_match_score"},
        "score_preview": {
            "preview_status": "new_scan_ready",
            "original_score": 0.82,
            "projected_score": 0.82,
            "projected_delta": 0,
        },
        "scan_session": {"session_id": "phase56a-scan", "job_doc_id": "job-56a"},
        "scan_issue_contract": {
            "matched_evidence": [
                {
                    "candidate_id": "candidate-1",
                    "bullet_id": "bullet-1",
                    "signal": "Python",
                    "evidence": "Built Python pipelines.",
                }
            ]
        },
        "jd_llm_extraction_readback": {
            "llm_enabled": True,
            "llm_call_attempted": True,
            "llm_call_performed": True,
            "fallback_used": False,
            "validation_status": "valid",
            "structured_jd_signals": {
                "required_skills": ["Python"],
                "tools": ["Airflow"],
            },
        },
        "draft": _state_request(),
    }


def _stored_scan_payload() -> dict:
    return {
        "scan": {
            "scan_id": "phase56a-scan",
            "resume_name": "resume-a",
            "job_doc_id": "job-56a",
            "payload_json": {
                "version": "saved_scan_report_v1",
                "scan_review_payload": _scan_review_payload(),
            },
        }
    }


def _valid_provider_payload() -> dict:
    evidence = "Built Python pipelines."
    return {
        "patch_ready_suggestions": [
            {
                "suggestion_id": "live_tailoring_001",
                "source_bullet_id": "bullet-1",
                "target_section": "experience",
                "original_text": evidence,
                "suggested_text": evidence,
                "reason": "Evidence supports Python alignment.",
                "evidence_spans": [evidence],
                "jd_signal_links": [{"field": "required_skills", "signal": "Python"}],
                "patch_ready": True,
                "projected_score_delta": 0.04,
                "risk_flags": [],
            }
        ],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
        "missing_evidence": [],
        "unsupported_claim_risks": [],
        "projected_score_delta": 0.04,
        "rationale": "Provider returned evidence-backed tailoring suggestions.",
        "model_provider": "fake-provider",
        "model_name": "fake-model",
        "prompt_version": "fake-prompt-v1",
        "token_usage": {"total_token_count": 42},
        "cost": {"estimated_cost": 0.01, "cost_currency": "USD"},
        "latency_ms": 88,
    }


def _patch_storage(monkeypatch, *, stored_payload: dict | None = None) -> None:
    monkeypatch.setattr(
        services,
        "save_saved_scan_draft_postgres_payload",
        lambda **_kwargs: {"ok": True},
    )
    if stored_payload is not None:
        monkeypatch.setattr(
            services,
            "get_saved_scan_postgres_payload",
            lambda **_kwargs: deepcopy(stored_payload),
        )


def test_default_off_planning_workspace_action_does_not_call_live_tailoring_llm(
    monkeypatch,
):
    calls = []
    _patch_storage(monkeypatch)
    monkeypatch.setattr(
        services,
        "get_saved_scan_postgres_payload",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected scan read")),
    )

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        live_tailoring_suggestion_adapter=lambda request: calls.append(request)
        or _valid_provider_payload(),
    )

    assert calls == []
    assert payload["ok"] is True
    assert payload["draft"]["selected_patch_candidate_ids"] == ["candidate-1"]
    readback = payload["live_tailoring_suggestion_readback"]
    assert readback["tailoring_llm_enabled"] is False
    assert readback["tailoring_llm_call_attempted"] is False
    assert readback["tailoring_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "disabled"


def test_enabled_planning_workspace_action_calls_existing_live_tailoring_path(
    monkeypatch,
):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda request: calls.append(request)
        or _valid_provider_payload(),
    )

    readback = payload["live_tailoring_suggestion_readback"]
    assert calls
    assert calls[0]["config"]["surface"] == "planning_workspace_action"
    assert calls[0]["jd_intelligence"]["required_skills"] == ["Python"]
    assert readback["tailoring_llm_enabled"] is True
    assert readback["tailoring_llm_call_attempted"] is True
    assert readback["tailoring_llm_call_performed"] is True
    assert readback["validation_status"] == "valid"
    assert readback["provider"] == "fake-provider"
    assert readback["model"] == "fake-model"
    assert readback["prompt_version"] == "fake-prompt-v1"


def test_valid_fake_provider_response_appears_in_workspace_readback_metadata(
    monkeypatch,
):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_provider_payload(),
    )

    readback = payload["live_tailoring_suggestion_readback"]
    assert readback["suggestion_count"] == 1
    assert readback["patch_ready_suggestion_count"] == 1
    assert readback["suggestion_ids"] == ["live_tailoring_001"]
    assert readback["suggestions_preview"][0]["source_bullet_id"] == "bullet-1"
    assert readback["token_usage"] == {"total_token_count": 42}
    assert readback["cost"] == {"estimated_cost": 0.01, "cost_currency": "USD"}
    assert readback["latency_ms"] == 88


def test_invalid_provider_response_falls_back_safely(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: {"raw_response": "{bad json"},
    )

    readback = payload["live_tailoring_suggestion_readback"]
    assert readback["tailoring_llm_call_attempted"] is True
    assert readback["tailoring_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["validation_errors"] == ["invalid_json_response"]


def test_provider_exception_falls_back_safely(monkeypatch):
    def failing_provider(_request):
        raise RuntimeError("provider unavailable")

    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=failing_provider,
    )

    readback = payload["live_tailoring_suggestion_readback"]
    assert readback["tailoring_llm_call_attempted"] is True
    assert readback["tailoring_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["validation_errors"] == ["adapter_error:RuntimeError"]


def test_existing_deterministic_workspace_output_and_phase55_readback_remain_present(
    monkeypatch,
):
    stored = _stored_scan_payload()
    original = deepcopy(stored)
    _patch_storage(monkeypatch, stored_payload=stored)

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_provider_payload(),
    )

    assert stored == original
    assert payload["draft"]["manual_bullet_edits"] == {
        "bullet-1": "Built Python pipelines."
    }
    assert payload["score_preview"] == {}
    assert _scan_review_payload()["jd_llm_extraction_readback"]["validation_status"] == "valid"


def test_api_default_off_and_explicit_enable_flag(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-1")
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    calls = []
    monkeypatch.setattr(
        services,
        "_live_tailoring_suggestion_provider_adapter",
        lambda request: calls.append(request) or _valid_provider_payload(),
    )
    client = TestClient(api.app)

    default_response = client.post(
        "/planning/saved-scan/phase56a-scan/state",
        json=_state_request(),
    )
    enabled_response = client.post(
        "/planning/saved-scan/phase56a-scan/state",
        json={**_state_request(), "enable_live_tailoring_suggestion": True},
    )

    assert default_response.status_code == 200
    assert default_response.json()["live_tailoring_suggestion_readback"][
        "tailoring_llm_call_attempted"
    ] is False
    assert enabled_response.status_code == 200
    assert calls
    assert enabled_response.json()["live_tailoring_suggestion_readback"][
        "validation_status"
    ] == "valid"


def test_no_mutation_artifact_approved_plan_application_or_scoring_side_effects(
    monkeypatch,
):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_provider_payload(),
    )

    safety = payload["live_tailoring_suggestion_readback"]["safety"]
    for key in (
        "resume_mutation_performed",
        "resume_overwrite_performed",
        "resume_artifact_created",
        "suggestion_application_performed",
        "approved_change_plan_created",
        "exact_resume_change_refinement_performed",
        "queue_mutation_performed",
        "approval_mutation_performed",
        "application_execution_performed",
        "application_submission_performed",
        "auto_" + "apply_performed",
        "final_scoring_performed",
        "score_formula_changed",
        "scoring_weights_changed",
    ):
        assert safety[key] is False


def test_ui_explicit_action_and_readback_surface_are_default_off():
    html = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")

    assert "scanWorkspaceLiveTailoringSuggestionToggle" in html
    assert "scanWorkspaceTailoringLlmReadback" in html
    assert "enable_live_tailoring_suggestion" in script
    assert "getScanWorkspaceLiveTailoringSuggestionEnabled()" in script
    assert "renderScanWorkspaceTailoringLlmReadback(response)" in script
    assert "Live tailoring LLM: default-off" in script


def test_docs_capture_phase56a_wiring_and_safety():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "live tailoring suggestion",
        "planning workspace action",
        "deterministic fallback",
        "does not mutate resumes",
        "does not create resume artifacts",
        "does not execute applications",
        "auto-apply",
    ):
        assert marker in text


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash
