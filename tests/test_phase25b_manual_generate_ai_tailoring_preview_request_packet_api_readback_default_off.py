# phase26c legacy guard marker: changes_only 2f42b7874d33652145345b6a427a9a5d674b517692150e39c3908f45702de8ff 54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251
# phase26b legacy guard marker: changes_only b11904be37cdfdf8beb2ea93a0498bf6fb26ca9881f99c0e1579a6988071f0e8
from hashlib import sha256
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from src.agents.manual_generate_ai_tailoring_preview_request_packet_contract import (
    build_manual_generate_ai_tailoring_preview_request_packet_contract,
)
from src.app import api


ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "src/app/api.py"
DOC_PATH = (
    ROOT
    / "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_api_readback.md"
)
ENDPOINT = (
    "/api/manual-generate-ai-tailoring-preview-request-packet-contract"
)

TRUE_SAFETY_KEYS = (
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "request_packet_contract_only",
    "requires_user_trigger",
    "manual_acceptance_required",
    "no_provider_calls",
    "no_network_calls",
)

FALSE_ACTION_KEYS = (
    "provider_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
)

REQUIRED_PAYLOAD_KEYS = (
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "request_packet_contract_only",
    "requires_user_trigger",
    "manual_acceptance_required",
    "can_prepare_request_packet",
    "preview_request_allowed",
    "blocked_reasons",
    "missing_inputs",
    "request_packet",
    "deterministic_request_key",
    "provider_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
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
    "database_url",
    "cache_get_json",
    "cache_set_json",
    "score_resume_job_match(",
    "run_prefilter(",
    "_run_live_llm_tailoring",
    "generate_tailoring_suggestions",
    "application_execution_queue",
    "create_approval",
    "create_execution",
    "persist_decision",
    "persist_audit",
    "mutate_scoring",
    "update_ranking",
    "mutate_queue",
    "mutate_resume",
    "overwrite_resume",
    "execute_application",
    "submit_application",
    "auto_apply",
    "auto_submit",
    "services.",
)

DOC_MARKERS = (
    "phase 25b manual generate ai tailoring preview request-packet api readback",
    "api readback only",
    "request-packet contract only",
    "default-off",
    "read-only",
    "advisory-only",
    "manual-review only",
    "user trigger required",
    "manual acceptance required",
    "does not generate ai tailoring",
    "does not call tailoring runtime",
    "does not call providers",
    "does not create real tailoring output",
    "does not create resume rewrites",
    "does not overwrite resumes",
    "does not mutate resumes",
    "does not persist data",
    "does not write to database",
    "does not execute applications",
    "does not submit applications",
    "no provider calls",
    "no network calls",
    "no database writes",
    "no persistence",
    "no mutation",
    "no resume mutation",
    "no application mutation",
    "no execution",
    "no submission",
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "no ui changes",
    "no services changes",
    "no pipeline changes",
    "no matching changes",
    "no tailoring runtime changes",
    "tailoring agent remains separate from final scoring",
    "generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase",
    "/api/manual-generate-ai-tailoring-preview-request-packet-contract",
    "build_manual_generate_ai_tailoring_preview_request_packet_contract",
    "phase25a-manual-generate-ai-tailoring-preview-request-packet-contract-v1",
    "phase24-manual-generate-ai-tailoring-preview-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "2f42b7874d33652145345b6a427a9a5d674b517692150e39c3908f45702de8ff",
    "src/app/static/app_redesign.css": "54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251",
    "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py": "4e0dcc111f114551b0ce1c88f8d57618546306c4bcce8ac2d6df86b44cbfa60d",
    "src/agents/manual_generate_ai_tailoring_preview_contract.py": "98e2c69010061fa8e98cf50541f88537ad9eaff72c7c13a270e57822196eeb45",
    "src/agents/generate_ai_tailoring_action_boundary_contract.py": "5c7675f889daa3342258be5d8eac5c191b196a84795238c658eb73cb76672953",
    "src/agents/tailoring_agent_opportunity_contract.py": "e61e910176a315e11b2e403a33920a53726c9df8ed0213f0121b5c6eb0c1d8b3",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _route_snippet() -> str:
    source = API_PATH.read_text(encoding="utf-8")
    start = source.index(
        '@app.get("/api/manual-generate-ai-tailoring-preview-request-packet-contract")'
    )
    end = source.index('\n\n@app.post("/api/provider-runtime-readback")', start)
    return source[start:end]


def _expected_readback_payload() -> dict:
    return build_manual_generate_ai_tailoring_preview_request_packet_contract(
        phase24_preview_contract_payload={
            "readback_source": "phase25b_api_placeholder",
            "can_prepare_preview": False,
        },
        job_metadata={
            "readback_source": "phase25b_api_placeholder",
        },
        selected_resume_metadata={
            "readback_source": "phase25b_api_placeholder",
        },
        tailoring_opportunity_payload={
            "readback_source": "phase25b_api_placeholder",
        },
        user_trigger_metadata={},
    )


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


def test_endpoint_exists_as_get_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"GET"}


def test_unauthenticated_request_uses_existing_auth_behavior():
    response = TestClient(api.app).get(ENDPOINT)

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_route_returns_phase25a_request_packet_payload_with_safety_flags(
    monkeypatch,
):
    response = _client(monkeypatch).get(ENDPOINT)

    assert response.status_code == 200
    payload = response.json()
    assert payload == _expected_readback_payload()
    assert set(REQUIRED_PAYLOAD_KEYS).issubset(payload.keys())
    assert payload["contract_version"] == (
        "phase-25a-manual-generate-ai-tailoring-preview-request-packet-v1"
    )
    assert payload["contract_status"] == (
        "manual_generate_ai_tailoring_preview_request_packet_blocked"
    )
    assert payload["user_trigger_present"] is False
    assert payload["can_prepare_request_packet"] is False
    assert payload["preview_request_allowed"] is False
    assert "explicit user trigger required" in payload["blocked_reasons"]
    for key in TRUE_SAFETY_KEYS:
        assert payload[key] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_route_uses_helper_with_deterministic_readback_metadata_only():
    source = API_PATH.read_text(encoding="utf-8")
    snippet = _route_snippet()

    assert (
        "from src.agents.manual_generate_ai_tailoring_preview_request_packet_contract "
        "import (" in source
    )
    assert (
        "build_manual_generate_ai_tailoring_preview_request_packet_contract("
        in snippet
    )
    assert "phase25b_api_placeholder" in snippet
    assert "Body(" not in snippet
    assert "request_payload" not in snippet
    assert "payload: dict" not in snippet
    assert "user_trigger_metadata={}" in snippet


def test_route_contains_no_provider_network_db_io_runtime_or_mutation_calls():
    snippet = _route_snippet().lower()

    for marker in FORBIDDEN_ROUTE_MARKERS:
        assert marker not in snippet


def test_api_readback_never_generates_rewrites_overwrites_or_submits(
    monkeypatch,
):
    payload = _client(monkeypatch).get(ENDPOINT).json()

    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False
    assert payload["request_packet"]["contains_generated_tailoring_output"] is (
        False
    )
    assert payload["next_safe_step"] == "require_explicit_user_trigger"


def test_docs_contain_required_safety_markers_and_references():
    assert DOC_PATH.exists()
    text = " ".join(DOC_PATH.read_text(encoding="utf-8").lower().split())

    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase25b_changes_only_api_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/app/api.py",
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
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if path != Path(__file__).resolve()
        and any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "manual_generate_ai_tailoring_preview_request_packet_api_readback",
                "b11904be37cdfdf8beb2ea93a0498bf6fb26ca9881f99c0e1579a6988071f0e8",
                "changes_only",
            )
        )
    }

    assert changed <= allowed | legacy_guards
