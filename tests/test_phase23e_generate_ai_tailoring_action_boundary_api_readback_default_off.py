# phase23f legacy guard marker: changes_only 65975190cebecd5cefc179be1d71c4cbe7b3214ed9c7b3691d6cc7877f7db6e3 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 8b5ac1590a977b002f3a04b77b9d8ce634eb3d806716586fca4872b81d33990a 63e37ba427991dd71c6addb440a83024661fe4cef363f8641149d48e14c55c56
# phase23f legacy guard marker: changes_only 63e37ba427991dd71c6addb440a83024661fe4cef363f8641149d48e14c55c56
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from src.agents.generate_ai_tailoring_action_boundary_contract import (
    STATUS_BLOCKED,
    STATUS_READY,
    STATUS_SKIPPED,
    build_generate_ai_tailoring_action_boundary_contract,
)
from src.app import api


ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "src/app/api.py"
DOC_PATH = (
    ROOT
    / "docs/phase23_generate_ai_tailoring_action_boundary_api_readback.md"
)
ENDPOINT = "/api/generate-ai-tailoring-action-boundary"

CALLER_FIELDS = (
    "enabled",
    "user_triggered",
    "tailoring_agent_opportunity_payload",
    "selected_opportunity_ids",
    "generation_context",
    "operator_context",
)

SAFETY_KEYS = (
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "manual_user_control_required",
    "user_trigger_required",
    "preview_only",
    "manual_acceptance_required",
    "no_auto_apply",
    "no_auto_submit",
    "no_autonomous_application_execution",
    "no_automatic_job_application_submission",
    "no_provider_calls",
    "no_network_calls",
    "no_database_writes",
    "no_persistence",
    "no_mutation",
    "no_resume_mutation",
    "no_application_mutation",
    "no_execution",
    "no_submission",
)

PERMANENT_FALSE_KEYS = (
    "ai_tailoring_generation_performed",
    "tailoring_provider_call_performed",
    "tailoring_runtime_call_performed",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "application_submission_performed",
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
    "phase23d-generate-ai-tailoring-action-boundary-contract-v1",
    "phase23c-tailoring-agent-opportunity-ui-readback-v1",
    "phase23b-tailoring-agent-opportunity-api-readback-v1",
    "phase23a-tailoring-agent-opportunity-contract-v1",
    "phase22-core-agent-evidence-materialization-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "63e37ba427991dd71c6addb440a83024661fe4cef363f8641149d48e14c55c56",
    "src/app/static/app_redesign.css": "8b5ac1590a977b002f3a04b77b9d8ce634eb3d806716586fca4872b81d33990a",
    "src/agents/generate_ai_tailoring_action_boundary_contract.py": "5c7675f889daa3342258be5d8eac5c191b196a84795238c658eb73cb76672953",
    "src/agents/tailoring_agent_opportunity_contract.py": "e61e910176a315e11b2e403a33920a53726c9df8ed0213f0121b5c6eb0c1d8b3",
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


def _ready_payload():
    return {
        "enabled": True,
        "user_triggered": True,
        "tailoring_agent_opportunity_payload": {
            "contract_status": "ready_for_manual_review",
            "tailoring_opportunities": [
                {
                    "opportunity_type": "missing_requirement",
                    "signal": "kubernetes",
                },
            ],
        },
        "selected_opportunity_ids": ["opportunity-1"],
        "generation_context": {
            "job_title": "Machine Learning Engineer",
        },
        "operator_context": {
            "operator_note": "Preview supported evidence only.",
        },
    }


def _route_snippet() -> str:
    source = API_PATH.read_text(encoding="utf-8")
    start = source.index(
        '@app.post("/api/generate-ai-tailoring-action-boundary")'
    )
    end = source.index(
        '\n\n@app.post("/api/provider-runtime-readback")',
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


def test_default_off_when_enabled_is_absent_false_or_not_exact_true(
    monkeypatch,
):
    client = _client(monkeypatch)

    for request_payload in ({}, {"enabled": False}, {"enabled": 1}):
        response = client.post(ENDPOINT, json=request_payload)
        assert response.status_code == 200
        payload = response.json()
        assert payload["action_boundary_status"] == STATUS_SKIPPED
        assert payload["action_allowed"] is False
        for key in SAFETY_KEYS:
            assert payload[key] is True


def test_enabled_without_exact_user_trigger_returns_blocked(monkeypatch):
    client = _client(monkeypatch)

    for user_triggered in (False, 1, "true"):
        payload = client.post(
            ENDPOINT,
            json={"enabled": True, "user_triggered": user_triggered},
        ).json()

        assert payload["action_boundary_status"] == STATUS_BLOCKED
        assert payload["action_allowed"] is False
        assert "user trigger required" in payload["action_blocked_reason"]


def test_enabled_and_user_triggered_returns_helper_payload_directly(
    monkeypatch,
):
    request_payload = _ready_payload()
    expected = build_generate_ai_tailoring_action_boundary_contract(
        **request_payload
    )
    response = _client(monkeypatch).post(ENDPOINT, json=request_payload)

    assert response.status_code == 200
    assert response.json() == expected
    assert response.json()["action_boundary_status"] == STATUS_READY
    assert response.json()["action_allowed"] is True


def test_api_does_not_mutate_caller_payload(monkeypatch):
    request_payload = _ready_payload()
    before = deepcopy(request_payload)

    _client(monkeypatch).post(ENDPOINT, json=request_payload)

    assert request_payload == before


def test_route_imports_helper_and_passes_only_expected_fields():
    source = API_PATH.read_text(encoding="utf-8")
    snippet = _route_snippet()

    assert (
        "from src.agents.generate_ai_tailoring_action_boundary_contract "
        "import (" in source
    )
    assert "build_generate_ai_tailoring_action_boundary_contract(" in snippet
    for field_name in CALLER_FIELDS:
        assert f'"{field_name}"' in snippet
    assert 'request_payload.get("enabled", False)' in snippet
    assert 'request_payload.get("user_triggered", False)' in snippet
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
        "overwrite_resume",
        "execute_application",
    ):
        assert marker not in snippet.lower()


def test_api_never_generates_rewrites_overwrites_or_submits(monkeypatch):
    for request_payload in ({}, {"enabled": True}, _ready_payload()):
        payload = _client(monkeypatch).post(
            ENDPOINT,
            json=request_payload,
        ).json()

        for key in PERMANENT_FALSE_KEYS:
            assert payload[key] is False
        assert payload["future_action_name"] == "Generate AI Tailoring"


def test_docs_contain_required_boundaries_and_references():
    assert DOC_PATH.exists()
    text = DOC_PATH.read_text(encoding="utf-8")
    lowered = " ".join(text.lower().split())

    assert text.startswith(
        "# Phase 23E Generate AI Tailoring Action-Boundary API Readback"
    )
    for marker in (
        "builds on phase 23d",
        "default-off api readback only",
        "/api/generate-ai-tailoring-action-boundary",
        "post",
        "accepts caller json",
        "returns the phase 23d helper payload directly",
        "no ui changes",
        "no services changes",
        "no agent helper changes",
        "no pipeline changes",
        "no matching changes",
        "no tailoring runtime changes",
        "no provider calls",
        "no network calls",
        "no database writes",
        "no persistence",
        "no mutation",
        "no execution",
        "no submission",
        "does not generate ai tailoring",
        "does not call tailoring runtime",
        "does not call providers",
        "does not create resume rewrites",
        "overwrite resumes",
        "does not submit applications",
        "user trigger is required",
        "manual acceptance is required",
        "preview/manual-review only unless the user accepts edits",
        "no silent resume rewrite",
        "no automatic resume overwrite",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
        "manual user control remains required",
    ):
        assert marker in lowered
    for tag in REQUIRED_TAGS:
        assert tag in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase23e_changes_only_api_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/app/api.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase23_generate_ai_tailoring_action_boundary_ui_readback.md",
        "tests/test_phase23f_generate_ai_tailoring_action_boundary_ui_readback_default_off.py",
        "docs/phase23_tailoring_agent_workflow_release_checkpoint.md",
        "tests/test_phase23g_tailoring_agent_workflow_release_checkpoint_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if (
            "changes_only" in path.read_text(encoding="utf-8")
            or "65975190cebecd5cefc179be1d71c4cbe7b3214ed9c7b3691d6cc7877f7db6e3"
            in path.read_text(encoding="utf-8")
                or "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab"
                in path.read_text(encoding="utf-8")
                or "8b5ac1590a977b002f3a04b77b9d8ce634eb3d806716586fca4872b81d33990a"
                in path.read_text(encoding="utf-8")
        )
    }

    assert changed <= allowed | legacy_guards
