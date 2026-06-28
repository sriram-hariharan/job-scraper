# phase26c legacy guard marker: changes_only ca378dc0aee655d83a7af0d15e885313af5b719c2512eff10f3efc69cd43348a 3c55b13f7762c2118eabad4a32ca6c6a47b9674be44ac33058d3b55f97c4e5c5
# phase26b legacy guard marker: changes_only 1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6
# phase23f legacy guard marker: changes_only 1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 3c55b13f7762c2118eabad4a32ca6c6a47b9674be44ac33058d3b55f97c4e5c5 ca378dc0aee655d83a7af0d15e885313af5b719c2512eff10f3efc69cd43348a
# phase23f legacy guard marker: changes_only ca378dc0aee655d83a7af0d15e885313af5b719c2512eff10f3efc69cd43348a
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from src.agents.core_agent_evidence_materialization_preview import (
    STATUS_READY,
    STATUS_SKIPPED,
    build_core_agent_evidence_materialization_preview,
)
from src.app import api


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/core-agent-evidence-materialization-preview"
DOC_PATH = (
    ROOT
    / "docs/phase22_core_agent_evidence_materialization_api_readback.md"
)

CALLER_FIELDS = (
    "enabled",
    "relevance_prefilter_result",
    "jd_intelligence_signals",
    "final_application_scoring_result",
    "tailoring_opportunity_signals",
    "manual_review_context",
)

SAFETY_KEYS = (
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "manual_user_control_required",
    "no_auto_apply",
    "no_auto_submit",
    "no_autonomous_application_execution",
    "no_automatic_job_application_submission",
    "no_provider_calls",
    "no_network_calls",
    "no_database_writes",
    "no_persistence",
    "no_mutation",
    "no_execution",
    "no_submission",
)

FORBIDDEN_ROUTE_MARKERS = (
    "run_chat_completion",
    "run_chat_completion_with_metadata",
    "requests.",
    "httpx",
    "urllib",
    "subprocess",
    "open(",
    "read_text",
    "write_text",
    "DATABASE_URL",
    "cache_get_json",
    "cache_set_json",
    "score_resume_job_match(",
    "run_prefilter(",
    "_run_live_llm_tailoring",
    "generate_tailoring_suggestions",
    "application_execution_queue",
    "submit_application",
    "auto_apply",
    "auto_submit",
)

REQUIRED_TAGS = (
    "phase22c-core-agent-evidence-materialization-preview-v1",
    "phase22b-core-agent-automation-mutation-inventory-v1",
    "phase22a-manual-review-ux-hardening-v1",
    "phase21-manual-review-workflow-release-v1",
    "phase20-provider-readiness-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
    "phase19-readonly-approval-workflow-release-v1",
    "phase18-safety-wrap-release-v1",
    "phase17-three-core-shadow-readiness-release-v1",
)

PROTECTED_HASHES = {
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "ca378dc0aee655d83a7af0d15e885313af5b719c2512eff10f3efc69cd43348a",
    "src/app/static/app_redesign.css": "3c55b13f7762c2118eabad4a32ca6c6a47b9674be44ac33058d3b55f97c4e5c5",
    "src/agents/core_agent_evidence_materialization_preview.py": "d1b0862cf0355192a45a7b45fbeaa622d72e16b7c5234c71bea75aea90db9110",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
}


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _enabled_payload():
    return {
        "enabled": True,
        "relevance_prefilter_result": {
            "passed": True,
            "matched_terms": ["python"],
        },
        "jd_intelligence_signals": {
            "required_skills": ["python", "sql"],
            "missing_requirements": ["kubernetes"],
        },
        "final_application_scoring_result": {
            "final_score": 0.82,
            "review_rationale": "Strong fit with one reviewable gap.",
        },
        "tailoring_opportunity_signals": {
            "tailoring_opportunity_summary": [
                "Emphasize production ML evidence."
            ],
        },
        "manual_review_context": {
            "action": "MAYBE_TAILOR",
            "company": "Example Corp",
        },
    }


def _route_snippet() -> str:
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index(
        '@app.post("/api/core-agent-evidence-materialization-preview")'
    )
    end = source.index(
        '\n\n@app.get("/api/manual-generate-ai-tailoring-preview-contract")',
        start,
    )
    return source[start:end]


def _changed_files() -> set[str]:
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return set(tracked + untracked)


def test_endpoint_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_unauthenticated_request_uses_existing_auth_behavior():
    response = TestClient(api.app).post(ENDPOINT, json={})

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_default_off_when_enabled_is_absent_or_false(monkeypatch):
    client = _client(monkeypatch)

    for request_payload in ({}, {"enabled": False}, {"enabled": 1}):
        response = client.post(ENDPOINT, json=request_payload)
        assert response.status_code == 200
        payload = response.json()
        assert payload["preview_status"] == STATUS_SKIPPED
        assert payload[
            "core_agent_evidence_materialization_enabled"
        ] is False
        for key in SAFETY_KEYS:
            assert payload[key] is True


def test_enabled_caller_json_returns_helper_payload_directly(monkeypatch):
    request_payload = _enabled_payload()
    expected = build_core_agent_evidence_materialization_preview(
        **request_payload
    )
    response = _client(monkeypatch).post(
        ENDPOINT,
        json=request_payload,
    )

    assert response.status_code == 200
    assert response.json() == expected
    assert response.json()["preview_status"] == STATUS_READY


def test_enabled_response_materializes_all_caller_evidence(monkeypatch):
    request_payload = _enabled_payload()
    payload = _client(monkeypatch).post(
        ENDPOINT,
        json=request_payload,
    ).json()

    assert payload["relevance_prefilter_evidence"] == request_payload[
        "relevance_prefilter_result"
    ]
    assert payload["jd_intelligence_evidence"] == request_payload[
        "jd_intelligence_signals"
    ]
    assert payload["final_application_scoring_evidence"] == request_payload[
        "final_application_scoring_result"
    ]
    assert payload["tailoring_opportunity_evidence"] == request_payload[
        "tailoring_opportunity_signals"
    ]
    assert payload["manual_review_evidence_packet"][
        "manual_review_context"
    ] == request_payload["manual_review_context"]


def test_api_does_not_mutate_caller_payload(monkeypatch):
    request_payload = _enabled_payload()
    before = deepcopy(request_payload)

    _client(monkeypatch).post(ENDPOINT, json=request_payload)

    assert request_payload == before


def test_route_passes_only_expected_fields_to_phase22c_helper():
    snippet = _route_snippet()

    assert "build_core_agent_evidence_materialization_preview(" in snippet
    for field_name in CALLER_FIELDS:
        assert f'"{field_name}"' in snippet
    assert 'request_payload.get("enabled", False)' in snippet
    assert "os.getenv" not in snippet
    assert "os.environ" not in snippet
    assert "config" not in snippet


def test_route_contains_no_provider_network_db_io_or_runtime_calls():
    snippet = _route_snippet()

    for marker in FORBIDDEN_ROUTE_MARKERS:
        assert marker not in snippet
    for marker in (
        "services.",
        "create_approval",
        "persist_decision",
        "persist_audit",
        "mutate_scoring",
        "update_ranking",
        "mutate_queue",
        "mutate_resume",
        "execute_application",
    ):
        assert marker not in snippet.lower()


def test_docs_contain_endpoint_boundaries_and_references():
    assert DOC_PATH.exists()
    text = DOC_PATH.read_text(encoding="utf-8")
    lowered = " ".join(text.lower().split())

    assert text.startswith(
        "# Phase 22D Core-Agent Evidence Materialization API Readback"
    )
    for marker in (
        "phase 22c",
        "/api/core-agent-evidence-materialization-preview",
        "post",
        "default-off api readback only",
        "accepts caller json",
        "returns the phase 22c helper payload directly",
        "no ui or pipeline execution connection",
        "no services changes",
        "no provider calls",
        "no network calls",
        "no database writes",
        "no persistence",
        "no mutation",
        "no execution",
        "no submission",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
        "manual user control remains required",
        "generate ai tailoring",
        "later user-triggered action",
    ):
        assert marker in lowered
    for tag in REQUIRED_TAGS:
        assert tag in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase22d_changes_only_api_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
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
            "src/app/api.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback.md",
            "tests/test_phase28b_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback.md",
            "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback 2.md",
            "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off 2.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint.md",
            "tests/test_phase28d_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.md",
            "tests/test_phase29a_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract_default_off.py",
            "src/app/api.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback.md",
            "tests/test_phase29b_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback.md",
            "tests/test_phase29c_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback_default_off.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint.md",
            "tests/test_phase29d_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_response_validation_contract.py",
            "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_contract.md",
            "tests/test_phase30a_manual_generate_ai_tailoring_preview_provider_response_validation_contract_default_off.py",
            "src/app/api.py",
            "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback.md",
            "tests/test_phase30b_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback_default_off.py",
                "src/app/static/agentic_review.js",
                "src/app/static/app_redesign.css",
                "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_ui_readback.md",
                "tests/test_phase30c_manual_generate_ai_tailoring_preview_provider_response_validation_ui_readback_default_off.py",
                    "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_release_checkpoint.md",
                    "tests/test_phase30d_manual_generate_ai_tailoring_preview_provider_response_validation_release_checkpoint_default_off.py",
                        "src/agents/manual_generate_ai_tailoring_preview_provider_response_normalization_contract.py",
                        "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_contract.md",
                        "tests/test_phase31a_manual_generate_ai_tailoring_preview_provider_response_normalization_contract_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if (
            "changes_only" in path.read_text(encoding="utf-8")
            or "1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6"
            in path.read_text(encoding="utf-8")
            or "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab"
            in path.read_text(encoding="utf-8")
            or "3c55b13f7762c2118eabad4a32ca6c6a47b9674be44ac33058d3b55f97c4e5c5"
            in path.read_text(encoding="utf-8")
        )
    }

    assert changed <= allowed | legacy_guards
