from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"
CSS_PATH = ROOT / "src/app/static/app_redesign.css"
DOC_PATH = (
    ROOT
    / "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback.md"
)
ENDPOINT = (
    "/api/manual-generate-ai-tailoring-preview-provider-response-normalization-contract"
)

PROTECTED_HASHES = {
    "src/app/api.py": "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/agents/manual_generate_ai_tailoring_preview_provider_response_normalization_contract.py": "2b31a53bd2cb8f8c4aa8359d5fcbcd246cd9618e65228b38675d7bd2af9470a4",
    "src/agents/manual_generate_ai_tailoring_preview_provider_response_validation_contract.py": "993952603b37420a40f9db750feb4ebbfa44fab4dbffe5751975aa1ee0f657d7",
    "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py": "26340a75114c6e1d3d909be3dfb6ddde1997578268ce966fda634c645c630fa6",
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
    "phase 31c manual generate ai tailoring preview provider response normalization ui readback",
    "ui readback only",
    "provider response normalization contract only",
    "response normalization only",
    "default-off",
    "read-only",
    "advisory-only",
    "manual-review only",
    "user trigger required",
    "operator confirmation required",
    "manual acceptance required",
    "provider response validation required",
    "provider response candidate required",
    "response normalization policy required",
    "provider configuration required",
    "response normalization ready",
    "normalized provider response accepted for future manual preview",
    "blocked reasons",
    "missing inputs",
    "normalization findings",
    "normalized provider response contract",
    "deterministic response normalization key",
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
    "rendermanualgenerateaitailoringpreviewproviderresponsenormalizationreadbacksection",
    "build_manual_generate_ai_tailoring_preview_provider_response_normalization_contract",
    "phase31b-manual-generate-ai-tailoring-preview-provider-response-normalization-api-readback-v1",
    "phase31a-manual-generate-ai-tailoring-preview-provider-response-normalization-contract-v1",
    "phase30-manual-generate-ai-tailoring-preview-provider-response-validation-release-v1",
    "phase29-manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-release-v1",
    "phase28-manual-generate-ai-tailoring-preview-provider-call-boundary-release-v1",
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
        "function renderManualGenerateAiTailoringPreviewProviderResponseNormalizationReadbackSection"
    )
    end = source.index("\nfunction renderHumanReviewedInfluencePreviewSection", start)
    return source[start:end]


def _fetch_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldFetchManualGenerateAiTailoringPreviewProviderResponseNormalizationReadback"
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
        "renderManualGenerateAiTailoringPreviewProviderResponseNormalizationReadbackSection"
        in source
    )
    assert (
        "renderManualGenerateAiTailoringPreviewProviderResponseNormalizationReadbackSection("
        "manualGenerateAiTailoringPreviewProviderResponseNormalizationVisibleTracePayload)"
    ) in source
    assert (
        "withManualGenerateAiTailoringPreviewProviderResponseNormalizationReadbackApiFetch("
        in source
    )


def test_default_off_requires_supplied_payload_or_fetch_gate():
    renderer = _renderer()
    fetch = _fetch_helpers()

    assert (
        "manual_generate_ai_tailoring_preview_provider_response_normalization_result"
        in renderer
    )
    assert 'if (!Object.keys(result).length) return "";' in renderer
    assert (
        "|| !shouldFetchManualGenerateAiTailoringPreviewProviderResponseNormalizationReadback("
        in fetch
    )


def test_fetch_readback_uses_get_endpoint_and_fail_closed_payload():
    fetch = _fetch_helpers()

    assert (
        "manual_generate_ai_tailoring_preview_provider_response_normalization_api_fetch"
        in fetch
    )
    assert ENDPOINT in fetch
    assert 'method: "GET"' in fetch
    assert (
        "manual_generate_ai_tailoring_preview_provider_response_normalization_result: result"
        in fetch
    )
    assert (
        "buildManualGenerateAiTailoringPreviewProviderResponseNormalizationReadbackFetchFailure"
        in fetch
    )
    assert "read_only: true" in fetch
    assert "response_normalization_only: true" in fetch
    assert "provider_response_normalization_contract_only: true" in fetch
    assert "provider_call_performed: false" in fetch
    assert "network_call_performed: false" in fetch
    assert "dispatch_performed: false" in fetch


def test_renderer_contains_visible_safety_and_readiness_markers():
    renderer = _renderer().lower()

    for marker in (
        "default-off",
        "read-only",
        "advisory-only",
        "manual-review only",
        "provider response normalization contract only",
        "response normalization only",
        "user trigger required",
        "operator confirmation required",
        "manual acceptance required",
        "provider response validation required",
        "provider response candidate required",
        "response normalization policy required",
        "provider configuration required",
        "response normalization ready",
        "normalized provider response accepted for future manual preview",
        "blocked reasons",
        "missing inputs",
        "normalization findings",
        "normalized provider response contract",
        "deterministic response normalization key",
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
        "Provider response normalization contract only",
        "Response normalization only",
        "User trigger required",
        "Operator confirmation required",
        "Manual acceptance required",
        "Provider response validation required",
        "Provider response candidate required",
        "Response normalization policy required",
        "Provider configuration required",
        "Response normalization ready",
        "Normalized provider response accepted for future manual preview",
        "Blocked reasons",
        "Missing inputs",
        "Normalization findings",
        "Normalized provider response contract",
        "Deterministic response normalization key",
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


def test_renderer_and_fetch_contain_no_controls_or_mutating_calls():
    renderer = _renderer().lower()
    fetch = _fetch_helpers().lower()

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
        "data-dispatch",
        "data-autonomous",
        "localstorage.setitem",
        "sessionstorage.setitem",
        "createapproval(",
        "create_approval",
        "createexecution(",
        "create_execution",
        "providercall(",
        "networkcall(",
        "callprovider(",
        "callnetwork(",
        "dispatchtailoring(",
        "dispatchpreview(",
        "tailoringruntime(",
        "generatetailoring(",
        "generate_tailoring_suggestions",
        "mutateresume(",
        "overwriteresume(",
        "executeapplication(",
        "submitapplication(",
        "mutatepipeline(",
        "mutatescoring(",
        "mutateranking(",
        "mutatematching(",
    ):
        assert marker not in renderer
        assert marker not in fetch


def test_renderer_contains_no_forbidden_action_style_camel_case_markers():
    renderer = _renderer()

    for marker in (
        "providerCall",
        "networkCall",
        "callProvider",
        "callNetwork",
        "dispatchTailoring",
        "dispatchPreview",
        "generateAiTailoring",
        "executeApplication",
        "submitApplication",
        "mutateResume",
        "updateRanking",
        "mutateScoring",
        "mutateMatching",
    ):
        assert marker not in renderer


def test_renderer_does_not_display_generated_tailoring_payload_fields():
    renderer = _renderer()

    for marker in (
        "generated_tailoring_text",
        "generated_tailoring_suggestions",
        "real_tailoring_output:",
        "resume_rewrite:",
        "rewritten_resume",
        "tailored_resume",
    ):
        assert marker not in renderer


def test_css_contains_scoped_readback_selectors():
    css = CSS_PATH.read_text(encoding="utf-8")

    for marker in (
        ".manual-generate-ai-tailoring-preview-provider-response-normalization-readback",
        ".manual-generate-ai-tailoring-preview-provider-response-normalization-readback__safety-labels",
        ".manual-generate-ai-tailoring-preview-provider-response-normalization-readback__metrics",
        ".manual-generate-ai-tailoring-preview-provider-response-normalization-readback__boundary",
    ):
        assert marker in css


def test_doc_contains_required_safety_markers_and_references():
    assert DOC_PATH.exists()
    text = " ".join(DOC_PATH.read_text(encoding="utf-8").lower().split())

    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_backend_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase31c_changes_only_static_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
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
                                "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py",
                                "docs/phase33_controlled_agent_router_batch_handoff_plan_readonly.md",
                                "tests/test_phase33c_controlled_agent_router_batch_handoff_plan_readonly.py",
                                "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py",
                                "docs/phase33_controlled_agent_router_planning_artifact_mapper_readonly.md",
                                "tests/test_phase33d_controlled_agent_router_planning_artifact_mapper_readonly.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if path != Path(__file__).resolve()
        and any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback",
                "phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback",
                "changes_only",
            )
        )
    }

    assert changed <= allowed | legacy_guards
