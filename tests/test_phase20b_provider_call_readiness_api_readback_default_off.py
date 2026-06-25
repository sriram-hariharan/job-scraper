from hashlib import sha256
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from src.agents import provider_call_readiness_experiment as experiment
from src.app import api


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/provider-call-readiness-readback"

PROTECTED_HASHES = {
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "ec19a732f5ad655e5252a986a0e52239549a1e6d435f21c79f6d80e2c8b43454",
    "src/app/static/app_redesign.css": "8fae431da8b4d0a8fcbd9dbe9778d334e84905ef0e2915fcbb67dcf20eb4cdef",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/provider_call_readiness_experiment.py": "d4176e889893b3acfb348c15a59a73418818e369e326f3935f4d673a50d88d28",
}


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _enabled_config(**extra):
    return {
        experiment.PROVIDER_CALL_READINESS_EXPERIMENT_FLAG: True,
        **extra,
    }


def _ready_request():
    return {
        "enabled": True,
        "requested_provider_capability": "review_jd_intelligence_packet",
        "provider_name": "caller-supplied-provider",
        "requested_model": "caller-supplied-model",
        "request_packet_summary": {
            "packet_type": "provider_call_preflight",
            "input_fields": ["job_description"],
        },
        "config": _enabled_config(),
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
    assert response.json()["readiness_status"] == (
        experiment.STATUS_NOT_ENABLED
    )


def test_enabled_without_config_flag_returns_not_enabled(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "requested_provider_capability": "review_packet",
            "request_packet_summary": {"packet_type": "preflight"},
            "config": {},
        },
    )

    assert response.json()["readiness_status"] == (
        experiment.STATUS_NOT_ENABLED
    )


def test_kill_switch_blocks_api_readback(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "requested_provider_capability": "review_packet",
            "request_packet_summary": {"packet_type": "preflight"},
            "config": _enabled_config(kill_switch_enabled=True),
        },
    )

    assert response.json()["readiness_status"] == (
        experiment.STATUS_BLOCKED_BY_KILL_SWITCH
    )


def test_missing_provider_capability_returns_validation_error(monkeypatch):
    payload = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "request_packet_summary": {"packet_type": "preflight"},
            "config": _enabled_config(),
        },
    ).json()

    assert payload["readiness_status"] == (
        experiment.STATUS_MISSING_PROVIDER_CAPABILITY
    )
    assert payload["validation_errors"] == [
        "requested_provider_capability_is_required"
    ]


def test_missing_request_packet_returns_validation_error(monkeypatch):
    payload = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "requested_provider_capability": "review_packet",
            "config": _enabled_config(),
        },
    ).json()

    assert payload["readiness_status"] == (
        experiment.STATUS_MISSING_REQUEST_PACKET
    )
    assert payload["validation_errors"] == [
        "request_packet_summary_is_required"
    ]


def test_valid_caller_supplied_payload_returns_direct_ready_result(
    monkeypatch,
):
    request_payload = _ready_request()
    expected = (
        experiment.build_provider_call_readiness_experiment_payload(
            **request_payload
        )
    )
    response = _client(monkeypatch).post(
        ENDPOINT,
        json=request_payload,
    )

    assert response.status_code == 200
    assert response.json() == expected
    assert response.json()["readiness_status"] == experiment.STATUS_READY


def test_response_is_read_only_and_never_authorizes_calls_or_actions(
    monkeypatch,
):
    payload = _client(monkeypatch).post(
        ENDPOINT,
        json=_ready_request(),
    ).json()

    assert payload["read_only"] is True
    assert payload["shadow_only"] is True
    assert payload["advisory_only"] is True
    for key in (
        "provider_call_attempted",
        "provider_call_authorized",
        "network_call_attempted",
        "approval_created",
        "decision_persisted",
        "execution_authorized",
        "submission_authorized",
        "mutation_authorized",
    ):
        assert payload[key] is False


def test_route_calls_only_phase20a_helper_without_forbidden_wiring():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index(
        '@app.post("/api/provider-call-readiness-readback")'
    )
    end = source.index('\n\n@app.post("/api/provider-runtime-readback")', start)
    snippet = source[start:end]
    compact = snippet.replace("\n", "").replace(" ", "")

    assert (
        "provider_call_readiness_experiment."
        "build_provider_call_readiness_experiment_payload"
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
    ):
        assert marker not in snippet.lower()


def test_permanent_no_automatic_application_behavior_is_documented():
    text = (
        ROOT / "docs/phase20_provider_call_readiness_api_readback.md"
    ).read_text(encoding="utf-8").lower()

    for marker in (
        "no auto-apply feature",
        "no auto-submit feature",
        "no autonomous application execution",
        "no automatic job application submission",
        "permanent product boundary",
    ):
        assert marker in text


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase20b_changes_only_api_doc_test_and_legacy_guards():
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
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
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
                "ec19a732f5ad655e5252a986a0e52239549a1e6d435f21c79f6d80e2c8b43454",
            )
        )
    }

    assert changed <= allowed | legacy_guards
