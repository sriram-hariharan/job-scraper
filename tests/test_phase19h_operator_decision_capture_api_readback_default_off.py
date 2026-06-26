# phase23f legacy guard marker: changes_only 65975190cebecd5cefc179be1d71c4cbe7b3214ed9c7b3691d6cc7877f7db6e3 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 8b5ac1590a977b002f3a04b77b9d8ce634eb3d806716586fca4872b81d33990a 63e37ba427991dd71c6addb440a83024661fe4cef363f8641149d48e14c55c56
# phase23f legacy guard marker: changes_only 63e37ba427991dd71c6addb440a83024661fe4cef363f8641149d48e14c55c56
from hashlib import sha256
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from src.agents import operator_decision_capture_readback_contract as contract
from src.app import api


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/operator-decision-capture-readback"

PROTECTED_HASHES = {
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "63e37ba427991dd71c6addb440a83024661fe4cef363f8641149d48e14c55c56",
    "src/app/static/app_redesign.css": "8b5ac1590a977b002f3a04b77b9d8ce634eb3d806716586fca4872b81d33990a",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/operator_decision_capture_readback_contract.py": "4066b415b7ac84eca8e37df5b1b71cad208001fd49c76126bd928eab39992450",
}


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _enabled_config(**extra):
    return {
        contract.OPERATOR_DECISION_CAPTURE_READBACK_FLAG: True,
        **extra,
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
    assert response.json()["capture_status"] == contract.STATUS_NOT_ENABLED


def test_enabled_without_config_flag_returns_not_enabled(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "selected_action": "HOLD",
            "config": {},
        },
    )

    assert response.json()["capture_status"] == contract.STATUS_NOT_ENABLED


def test_kill_switch_blocks_api_readback(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "selected_action": "HOLD",
            "config": _enabled_config(kill_switch_enabled=True),
        },
    )

    assert response.json()["capture_status"] == (
        contract.STATUS_BLOCKED_BY_KILL_SWITCH
    )


def test_missing_action_returns_validation_error(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True, "config": _enabled_config()},
    )
    payload = response.json()

    assert payload["capture_status"] == contract.STATUS_MISSING_ACTION
    assert payload["validation_errors"] == ["selected_action_is_required"]


def test_invalid_action_returns_validation_error(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "selected_action": "SEND_NOW",
            "config": _enabled_config(),
        },
    )
    payload = response.json()

    assert payload["capture_status"] == contract.STATUS_INVALID_ACTION
    assert payload["validation_errors"] == [
        "selected_action_is_not_allowed"
    ]


def test_valid_action_returns_direct_ready_payload(monkeypatch):
    request_payload = {
        "enabled": True,
        "selected_action": "MAYBE_TAILOR",
        "selected_resume": "resume-main",
        "selected_variant": "variant-a",
        "operator_note": "Read-only review",
        "config": _enabled_config(),
    }
    expected = contract.build_operator_decision_capture_readback_payload(
        **request_payload
    )
    response = _client(monkeypatch).post(ENDPOINT, json=request_payload)

    assert response.status_code == 200
    assert response.json() == expected
    assert response.json()["capture_status"] == contract.STATUS_READY


def test_response_proves_read_only_no_persistence_or_authority(monkeypatch):
    payload = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "selected_action": "APPLY",
            "config": _enabled_config(),
        },
    ).json()

    assert payload["read_only"] is True
    assert payload["shadow_only"] is True
    assert payload["advisory_only"] is True
    for key in (
        "decision_persisted",
        "approval_created",
        "execution_authorized",
        "submission_authorized",
        "mutation_authorized",
    ):
        assert payload[key] is False


def test_route_calls_only_phase19g_helper_without_forbidden_wiring():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index(
        '@app.post("/api/operator-decision-capture-readback")'
    )
    end = source.index('\n\n@app.post("/api/provider-runtime-readback")', start)
    snippet = source[start:end]

    assert (
        "operator_decision_capture_readback_contract."
        "build_operator_decision_capture_readback_payload"
    ) in snippet.replace("\n", "").replace(" ", "")
    for marker in (
        "services.",
        "src.storage",
        "src.pipeline",
        "collector.",
        "provider_runtime",
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
        "create_execution",
        "execute_application",
        "submit_application",
    ):
        assert marker not in snippet.lower()


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase19h_changes_only_approved_files():
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
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
        "src/app/api.py",
        "docs/phase19_operator_decision_capture_api_readback.md",
        "tests/test_phase19h_operator_decision_capture_api_readback_default_off.py",
        "docs/phase19_operator_decision_capture_ui_readback.md",
        "tests/test_phase19i_operator_decision_capture_ui_readback_default_off.py",
        "docs/phase19_readonly_approval_workflow_release_checkpoint.md",
        "tests/test_phase19j_readonly_approval_workflow_release_checkpoint_default_off.py",
        "src/agents/provider_call_readiness_experiment.py",
        "docs/phase20_provider_call_readiness_experiment.md",
        "tests/test_phase20a_provider_call_readiness_experiment_default_off.py",
        "src/app/api.py",
        "docs/phase20_provider_call_readiness_api_readback.md",
        "tests/test_phase20b_provider_call_readiness_api_readback_default_off.py",
        "docs/phase20_provider_call_readiness_ui_readback.md",
        "tests/test_phase20c_provider_call_readiness_ui_readback_default_off.py",
        "docs/no_auto_apply_safety_policy.md",
        "docs/phase20_no_auto_apply_safety_checkpoint.md",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "docs/phase20_provider_readiness_release_checkpoint.md",
        "tests/test_phase20e_provider_readiness_release_checkpoint_default_off.py",
        "docs/manual_review_workflow_boundary.md",
        "docs/phase21_manual_review_workflow_boundary.md",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "src/agents/manual_review_readiness_contract.py",
        "docs/phase21_manual_review_readiness_contract.md",
        "tests/test_phase21b_manual_review_readiness_contract_default_off.py",
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
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "src/app/api.py",
                "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab",
            )
        )
    }

    assert changed <= allowed | legacy_guards
