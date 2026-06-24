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
    "src/app/static/agentic_review.js": "b3f311bc5390eacc4d698d71141ebd3a960a491765c074ebd37c33718f887a03",
    "src/app/static/app_redesign.css": "cbf6e94095f4ffcd932d31f163adde1c27f115dcbaa5ae4d0939398348f1e014",
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
    changed = set(tracked + untracked)
    allowed = {
        "src/app/api.py",
        "docs/phase19_operator_decision_capture_api_readback.md",
        "tests/test_phase19h_operator_decision_capture_api_readback_default_off.py",
        "docs/phase19_operator_decision_capture_ui_readback.md",
        "tests/test_phase19i_operator_decision_capture_ui_readback_default_off.py",
        "docs/phase19_readonly_approval_workflow_release_checkpoint.md",
        "tests/test_phase19j_readonly_approval_workflow_release_checkpoint_default_off.py",
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
                "b3f311bc5390eacc4d698d71141ebd3a960a491765c074ebd37c33718f887a03",
            )
        )
    }

    assert changed <= allowed | legacy_guards
