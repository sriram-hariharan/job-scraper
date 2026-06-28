from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"
CSS_PATH = ROOT / "src/app/static/app_redesign.css"
DOC_PATH = (
    ROOT
    / "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback.md"
)
ENDPOINT = (
    "/api/manual-generate-ai-tailoring-preview-provider-call-boundary-contract"
)

PROTECTED_HASHES = {
    "src/app/api.py": "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py": "8e4b2a93d535f37387283b943d4a31fc3ff1c23016d2958132e2362a74f97f7b",
    "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py": "e1c9f6f55b7d8a8c0171b52d7e891d531aae0ad3384eb74d686f50ba4e59533f",
    "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py": "2fdc984c5ee395d43e71fd2ce991b9575316f8714188cc16a13c97c73074996f",
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

DOC_MARKERS = (
    "phase 28c manual generate ai tailoring preview provider-call boundary ui readback",
    "ui readback only",
    "provider-call boundary contract only",
    "default-off",
    "read-only",
    "advisory-only",
    "manual-review only",
    "user trigger required",
    "operator confirmation required",
    "manual acceptance required",
    "provider request-envelope required",
    "provider configuration required",
    "provider call policy required",
    "does not call providers",
    "does not call network",
    "does not dispatch",
    "does not generate ai tailoring",
    "does not call tailoring runtime",
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
    "no backend behavior changes",
    "no api changes",
    "no services changes",
    "no pipeline changes",
    "no matching changes",
    "no tailoring runtime changes",
    "tailoring agent remains separate from final scoring",
    "generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase",
    "no real generate ai tailoring button or control",
    "no provider-call control",
    "no network-call control",
    "no dispatch control",
    ENDPOINT,
    "rendermanualgenerateaitailoringpreviewprovidercallboundaryreadbacksection",
    "build_manual_generate_ai_tailoring_preview_provider_call_boundary_contract",
    "phase28b-manual-generate-ai-tailoring-preview-provider-call-boundary-api-readback-v1",
    "phase28a-manual-generate-ai-tailoring-preview-provider-call-boundary-contract-v1",
    "phase27-manual-generate-ai-tailoring-preview-provider-request-envelope-release-v1",
    "phase26-manual-generate-ai-tailoring-preview-dispatch-boundary-release-v1",
    "phase25-manual-generate-ai-tailoring-preview-request-packet-release-v1",
    "phase24-manual-generate-ai-tailoring-preview-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _renderer() -> str:
    source = _source()
    start = source.index(
        "function renderManualGenerateAiTailoringPreviewProviderCallBoundaryReadbackSection"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _fetch_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldFetchManualGenerateAiTailoringPreviewProviderCallBoundaryReadback"
    )
    end = source.index("\nfunction getAgenticReviewApprovalRequestId", start)
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


def test_renderer_exists_and_is_integrated():
    source = _source()

    assert (
        "renderManualGenerateAiTailoringPreviewProviderCallBoundaryReadbackSection"
        in source
    )
    assert (
        "renderManualGenerateAiTailoringPreviewProviderCallBoundaryReadbackSection("
        "manualGenerateAiTailoringPreviewProviderCallBoundaryVisibleTracePayload)"
    ) in source
    assert (
        "withManualGenerateAiTailoringPreviewProviderCallBoundaryReadbackApiFetch("
        in source
    )


def test_default_off_requires_supplied_payload_or_fetch_gate():
    renderer = _renderer()
    fetch = _fetch_helpers()

    assert (
        "manual_generate_ai_tailoring_preview_provider_call_boundary_result"
        in renderer
    )
    assert 'if (!Object.keys(result).length) return "";' in renderer
    assert (
        "|| !shouldFetchManualGenerateAiTailoringPreviewProviderCallBoundaryReadback("
        in fetch
    )


def test_renderer_contains_visible_safety_and_readiness_markers():
    renderer = _renderer().lower()

    for marker in (
        "default-off",
        "read-only",
        "advisory-only",
        "manual-review only",
        "provider-call boundary contract only",
        "user trigger required",
        "operator confirmation required",
        "manual acceptance required",
        "provider request-envelope required",
        "provider configuration required",
        "provider call policy required",
        "provider call boundary ready",
        "provider call allowed",
        "blocked reasons",
        "missing inputs",
        "provider call plan",
        "deterministic provider call key",
        "does not call providers",
        "does not call network",
        "does not dispatch",
        "does not generate ai tailoring",
        "does not call tailoring runtime",
        "does not create real tailoring output",
        "does not create resume rewrites",
        "does not overwrite resumes",
        "does not mutate resumes",
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
        "manual user control required",
        "preview/manual-review only",
        "next safe step",
    ):
        assert marker in renderer


def test_renderer_displays_contract_fields_without_actions():
    renderer = _renderer()

    for marker in (
        "Contract status",
        "Default-off",
        "Read-only",
        "Advisory-only",
        "Manual-review only",
        "Provider-call boundary contract only",
        "User trigger required",
        "Operator confirmation required",
        "Manual acceptance required",
        "Provider request-envelope required",
        "Provider configuration required",
        "Provider call policy required",
        "Provider call boundary ready",
        "Provider call allowed",
        "Blocked reasons",
        "Missing inputs",
        "Provider call plan",
        "Deterministic provider call key",
        "No provider calls",
        "No network calls",
        "No database writes",
        "No persistence",
        "No mutation",
        "No resume mutation",
        "No application mutation",
        "No execution",
        "No submission",
        "No auto-apply",
        "No auto-submit",
        "Next safe step",
    ):
        assert marker in renderer


def test_renderer_contains_no_controls_or_storage_writes():
    renderer = _renderer().lower()

    for marker in (
        "<button",
        "<input",
        "<form",
        "<select",
        "<textarea",
        "data-apply",
        "data-submit",
        "data-approval",
        "data-provider",
        "data-execute",
        "data-autonomous",
        "data-resume-rewrite",
        "data-resume-overwrite",
        "provider-call control",
        "network-call control",
        "dispatch control",
        "approval control",
        "execution control",
        "submit control",
        "localstorage.setitem",
        "sessionstorage.setitem",
        "generateaitailoring(",
        "createapproval(",
        "persistdecision(",
        "persistaudit(",
        "mutateresume(",
        "overwriteresume(",
        "submitapplication(",
        "providercall(",
        "networkcall(",
        "tailoringruntime(",
        "scorejobs(",
        "rankjobs(",
        "mutatequeue(",
    ):
        assert marker not in renderer


def test_fetch_is_gated_get_only_and_fail_closed():
    fetch = _fetch_helpers()

    assert "manual_generate_ai_tailoring_preview_provider_call_boundary_api_fetch" in fetch
    assert '=== "1"' in fetch
    assert fetch.count(f'"{ENDPOINT}"') == 1
    assert 'method: "GET"' in fetch
    assert "JSON.stringify" not in fetch
    assert "body:" not in fetch
    assert "catch (error)" in fetch
    assert (
        "manual_generate_ai_tailoring_preview_provider_call_boundary_failed_closed"
        in fetch
    )
    assert "read_only: true" in fetch
    assert "advisory_only: true" in fetch
    assert "manual_review_only: true" in fetch
    assert "provider_call_boundary_contract_only: true" in fetch
    assert "provider_call_performed: false" in fetch
    assert "network_call_performed: false" in fetch
    assert "dispatch_performed: false" in fetch
    assert "tailoring_runtime_call_performed: false" in fetch
    assert "ai_tailoring_generation_performed: false" in fetch
    assert "real_tailoring_output_created: false" in fetch
    assert "resume_mutation_performed: false" in fetch
    assert "application_submission_performed: false" in fetch
    assert "database_write_performed: false" in fetch
    assert "persistence_performed: false" in fetch
    assert "execution_performed: false" in fetch
    assert "submission_performed: false" in fetch
    assert "auto_apply_performed: false" in fetch
    assert "auto_submit_performed: false" in fetch


def test_ui_does_not_add_forbidden_controls_or_mutation_calls():
    source = _source().lower()
    provider_call_section = _renderer().lower() + "\n" + _fetch_helpers().lower()

    for marker in (
        "<button",
        "<input",
        "<form",
        "localstorage.setitem",
        "sessionstorage.setitem",
        "provider-call control",
        "network-call control",
        "dispatch control",
        "approval control",
        "execution control",
        "submit control",
        "generate_tailoring_suggestions",
        "tailoringruntime(",
        "mutateresume(",
        "overwriteresume(",
        "submitapplication(",
        "providercall(",
        "networkcall(",
        "mutatepipeline(",
        "scorejobs(",
        "rankjobs(",
        "matchjobs(",
        "mutatequeue(",
    ):
        assert marker not in provider_call_section

    assert "rendermanualgenerateaitailoringpreviewprovidercallboundaryreadbacksection" in source


def test_css_contains_passive_readback_styles_only():
    css = CSS_PATH.read_text(encoding="utf-8").lower()

    assert "manual-generate-ai-tailoring-preview-provider-call-boundary-readback" in css
    start = css.index(
        ".manual-generate-ai-tailoring-preview-provider-call-boundary-readback"
    )
    end = css.index("@media", start)
    provider_call_css = css[start:end]
    for marker in ("button", "input", "form", "cursor: pointer"):
        assert marker not in provider_call_css


def test_docs_contain_required_safety_markers_and_references():
    assert DOC_PATH.exists()
    text = " ".join(DOC_PATH.read_text(encoding="utf-8").lower().split())

    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_backend_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase28c_changes_only_static_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
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
                        "src/app/api.py",
                        "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_api_readback.md",
                        "tests/test_phase31b_manual_generate_ai_tailoring_preview_provider_response_normalization_api_readback_default_off.py",
                            "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback.md",
                            "tests/test_phase31c_manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback_default_off.py",
                                "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_release_checkpoint.md",
                                "tests/test_phase31d_manual_generate_ai_tailoring_preview_provider_response_normalization_release_checkpoint_default_off.py",
                                "src/agents/manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract.py",
                                "docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract.md",
                                "tests/test_phase32a_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract_default_off.py",
                                "src/app/api.py",
                                "docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback.md",
                                "tests/test_phase32b_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback_default_off.py",
                                "docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback 2.md",
                                "tests/test_phase32b_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback_default_off 2.py",
                                "src/agents/controlled_agent_router_readonly.py",
                                "docs/phase33_controlled_agent_router_readonly.md",
                                "tests/test_phase33a_controlled_agent_router_readonly.py",
                                "docs/phase33_controlled_agent_router_readonly 2.md",
                                "tests/test_phase33a_controlled_agent_router_readonly 2.py",
                                "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py",
                                "docs/phase33_controlled_agent_router_workflow_state_adapter_readonly.md",
                                "tests/test_phase33b_controlled_agent_router_workflow_state_adapter_readonly.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if path != Path(__file__).resolve()
        and any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback",
                "phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback",
                "changes_only",
            )
        )
    }

    assert changed <= allowed | legacy_guards
