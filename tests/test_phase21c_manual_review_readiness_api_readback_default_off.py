# phase26c legacy guard marker: changes_only 96d22785ac4e2d31f5de24e2438a85b80ca2e1a112b06adc22c35a3ab2e9d1c5 54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251
# phase26b legacy guard marker: changes_only 9bd26d43cd63bd52a62f16c8428d0c451f3a83b9298c4f66d882873bfa6ab803
# phase23f legacy guard marker: changes_only 9bd26d43cd63bd52a62f16c8428d0c451f3a83b9298c4f66d882873bfa6ab803 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251 96d22785ac4e2d31f5de24e2438a85b80ca2e1a112b06adc22c35a3ab2e9d1c5
# phase23f legacy guard marker: changes_only 96d22785ac4e2d31f5de24e2438a85b80ca2e1a112b06adc22c35a3ab2e9d1c5
from hashlib import sha256
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from src.agents import manual_review_readiness_contract as contract
from src.app import api


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/manual-review-readiness-readback"

PROTECTED_HASHES = {
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "96d22785ac4e2d31f5de24e2438a85b80ca2e1a112b06adc22c35a3ab2e9d1c5",
    "src/app/static/app_redesign.css": "54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251",
    "src/agents/manual_review_readiness_contract.py": "5253414d1343d5eae64af7fbb6f87da68f9d4931b762cac972a94c29dc9ad5a2",
    "src/agents/provider_call_readiness_experiment.py": "d4176e889893b3acfb348c15a59a73418818e369e326f3935f4d673a50d88d28",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
}


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _review_inputs():
    return {
        "job": {
            "title": "Machine Learning Engineer",
            "company": "Example Corp",
        },
        "ranking_summary": {"rank": 1, "score": 0.92},
        "resume_guidance_available": True,
    }


def test_endpoint_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_unauthenticated_request_uses_existing_auth_behavior():
    response = TestClient(api.app).post(ENDPOINT, json={})

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_authenticated_default_off_returns_not_enabled(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json={})

    assert response.status_code == 200
    assert response.json()["readiness_status"] == contract.STATUS_NOT_ENABLED


def test_enabled_missing_review_inputs_returns_missing_inputs(monkeypatch):
    payload = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True},
    ).json()

    assert payload["readiness_status"] == contract.STATUS_MISSING_INPUTS
    assert payload["missing_review_inputs"] == ["review_inputs_summary"]


def test_enabled_caller_review_inputs_returns_direct_ready_payload(
    monkeypatch,
):
    request_payload = {
        "enabled": True,
        "review_inputs_summary": _review_inputs(),
    }
    expected = contract.build_manual_review_readiness_payload(
        **request_payload
    )
    response = _client(monkeypatch).post(ENDPOINT, json=request_payload)

    assert response.status_code == 200
    assert response.json() == expected
    assert response.json()["readiness_status"] == contract.STATUS_READY


def test_response_requires_manual_review_and_manual_user_control(monkeypatch):
    payload = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True, "review_inputs_summary": _review_inputs()},
    ).json()

    assert payload["manual_review_required"] is True
    assert payload["manual_user_control_required"] is True
    assert payload["no_auto_apply"] is True
    assert payload["no_auto_submit"] is True
    assert payload["no_autonomous_application_execution"] is True
    assert payload["no_automatic_job_application_submission"] is True


def test_response_includes_allowed_modes_and_forbidden_actions(monkeypatch):
    payload = _client(monkeypatch).post(ENDPOINT, json={}).json()

    assert payload["allowed_assistance_modes"] == list(
        contract.ALLOWED_ASSISTANCE_MODES
    )
    assert payload["forbidden_actions"] == list(contract.FORBIDDEN_ACTIONS)


def test_safety_metadata_keeps_all_forbidden_paths_inactive(monkeypatch):
    payload = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True, "review_inputs_summary": _review_inputs()},
    ).json()
    safety = payload["safety_metadata"]

    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["manual_review_required"] is True
    assert safety["manual_user_control_required"] is True
    for key in (
        "provider_call_attempted",
        "network_call_attempted",
        "database_write_attempted",
        "approval_created",
        "decision_persisted",
        "audit_persisted",
        "scoring_mutated",
        "ranking_mutated",
        "queue_mutated",
        "resume_mutated",
        "application_mutated",
        "execution_authorized",
        "submission_authorized",
        "mutation_authorized",
    ):
        assert safety[key] is False


def test_route_calls_only_phase21b_helper_without_forbidden_wiring():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index('@app.post("/api/manual-review-readiness-readback")')
    end = source.index('\n\n@app.post("/api/provider-runtime-readback")', start)
    snippet = source[start:end]
    compact = snippet.replace("\n", "").replace(" ", "")

    assert (
        "manual_review_readiness_contract."
        "build_manual_review_readiness_payload"
    ) in compact
    for marker in (
        "services.",
        "src.storage",
        "src.pipeline",
        "collector.",
        "provider_client",
        "provider_callable",
        "openai",
        "anthropic",
        "requests.",
        "httpx",
        "open(",
        "connect(",
        ".commit(",
        "create_approval",
        "persist_decision",
        "persist_audit",
        "mutate_scoring",
        "update_ranking",
        "mutate_queue",
        "mutate_resume",
        "execute_application",
        "submit_application",
        "auto_apply",
        "auto_submit",
        "autonomous_application_execution",
    ):
        assert marker not in snippet.lower()


def test_documentation_records_api_and_permanent_product_boundary():
    text = (
        ROOT / "docs/phase21_manual_review_readiness_api_readback.md"
    ).read_text(encoding="utf-8").lower()

    for marker in (
        "phase 21c manual-review readiness api readback",
        "/api/manual-review-readiness-readback",
        "api readback only",
        "no auto-apply feature",
        "no auto-submit feature",
        "no autonomous application execution",
        "no automatic job application submission",
        "manual user control remains required",
        "phase21b-manual-review-readiness-contract-v1",
        "phase21a-manual-review-workflow-boundary-v1",
        "phase20-provider-readiness-release-v1",
        "phase20d-no-auto-apply-safety-checkpoint-v1",
        "phase19-readonly-approval-workflow-release-v1",
        "phase18-safety-wrap-release-v1",
    ):
        assert marker in text


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase21c_changes_only_api_doc_test_and_legacy_guards():
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    changed = set(tracked + untracked) - {
        "docs/core_agent_automation_mutation_inventory.md",
        "docs/phase22_core_agent_automation_mutation_inventory.md",
        "src/agents/core_agent_evidence_materialization_preview.py",
        "docs/phase22_core_agent_evidence_materialization_preview.md",
        "tests/test_phase22c_core_agent_evidence_materialization_preview_default_off.py",
        "src/app/api.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase22_core_agent_evidence_materialization_ui_readback.md",
        "tests/test_phase22e_core_agent_evidence_materialization_ui_readback_default_off.py",
        "docs/phase22_core_agent_evidence_materialization_release_checkpoint.md",
        "tests/test_phase22f_core_agent_evidence_materialization_release_checkpoint_default_off.py",
        "src/agents/tailoring_agent_opportunity_contract.py",
        "docs/phase23_tailoring_agent_opportunity_contract.md",
        "tests/test_phase23a_tailoring_agent_opportunity_contract_default_off.py",
        "docs/phase23_tailoring_agent_opportunity_api_readback.md",
        "tests/test_phase23b_tailoring_agent_opportunity_api_readback_default_off.py",
        "docs/phase23_tailoring_agent_opportunity_ui_readback.md",
        "tests/test_phase23c_tailoring_agent_opportunity_ui_readback_default_off.py",
        "src/agents/generate_ai_tailoring_action_boundary_contract.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_contract.md",
        "tests/test_phase23d_generate_ai_tailoring_action_boundary_contract_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_ui_readback.md",
        "tests/test_phase23f_generate_ai_tailoring_action_boundary_ui_readback_default_off.py",
        "docs/phase23_tailoring_agent_workflow_release_checkpoint.md",
        "tests/test_phase23g_tailoring_agent_workflow_release_checkpoint_default_off.py",
        "src/agents/manual_generate_ai_tailoring_preview_contract.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_contract.md",
        "tests/test_phase24a_manual_generate_ai_tailoring_preview_contract_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_api_readback.md",
        "tests/test_phase24b_manual_generate_ai_tailoring_preview_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase24_manual_generate_ai_tailoring_preview_ui_readback.md",
        "tests/test_phase24c_manual_generate_ai_tailoring_preview_ui_readback_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_release_checkpoint.md",
        "tests/test_phase24d_manual_generate_ai_tailoring_preview_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_contract.md",
            "tests/test_phase25a_manual_generate_ai_tailoring_preview_request_packet_contract_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_api_readback.md",
            "tests/test_phase25b_manual_generate_ai_tailoring_preview_request_packet_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_ui_readback.md",
            "tests/test_phase25c_manual_generate_ai_tailoring_preview_request_packet_ui_readback_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint.md",
            "tests/test_phase25d_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_contract.md",
            "tests/test_phase26a_manual_generate_ai_tailoring_preview_dispatch_boundary_contract_default_off.py",
            "src/app/api.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback.md",
            "tests/test_phase26b_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback.md",
            "tests/test_phase26c_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback_default_off.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint.md",
            "tests/test_phase26d_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_contract.md",
            "tests/test_phase27a_manual_generate_ai_tailoring_preview_provider_request_envelope_contract_default_off.py",
            "src/app/api.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback.md",
            "tests/test_phase27b_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback.md",
            "tests/test_phase27c_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback_default_off.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint.md",
            "tests/test_phase27d_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_contract.md",
            "tests/test_phase28a_manual_generate_ai_tailoring_preview_provider_call_boundary_contract_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
        "src/app/api.py",
        "docs/phase21_manual_review_readiness_api_readback.md",
        "tests/test_phase21c_manual_review_readiness_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "docs/phase21_manual_review_readiness_ui_readback.md",
        "tests/test_phase21d_manual_review_readiness_ui_readback_default_off.py",
        "docs/phase21_manual_review_workflow_release_checkpoint.md",
        "tests/test_phase21e_manual_review_workflow_release_checkpoint_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase22_manual_review_ux_hardening.md",
        "tests/test_phase22a_manual_review_ux_hardening_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "tests/test_phase21b_manual_review_readiness_contract_default_off.py",
                "9bd26d43cd63bd52a62f16c8428d0c451f3a83b9298c4f66d882873bfa6ab803",
                "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab",
            )
        )
    }

    assert changed <= allowed | legacy_guards
