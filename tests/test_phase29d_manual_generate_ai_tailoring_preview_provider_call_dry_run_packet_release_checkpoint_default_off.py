from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint.md"
)
HELPER_PATH = (
    ROOT
    / "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py"
)
API_PATH = ROOT / "src/app/api.py"
JS_PATH = ROOT / "src/app/static/agentic_review.js"

REQUIRED_TAGS = (
    "phase29c-manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-ui-readback-v1",
    "phase29b-manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-api-readback-v1",
    "phase29a-manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-contract-v1",
    "phase28-manual-generate-ai-tailoring-preview-provider-call-boundary-release-v1",
    "phase27-manual-generate-ai-tailoring-preview-provider-request-envelope-release-v1",
    "phase26-manual-generate-ai-tailoring-preview-dispatch-boundary-release-v1",
    "phase25-manual-generate-ai-tailoring-preview-request-packet-release-v1",
    "phase24-manual-generate-ai-tailoring-preview-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

SAFETY_MARKERS = (
    "release checkpoint",
    "docs/tests only",
    "no runtime behavior changes",
    "no backend behavior changes",
    "no api changes",
    "no ui changes",
    "no services changes",
    "no agent helper changes",
    "no pipeline changes",
    "no matching changes",
    "no tailoring runtime changes",
    "default-off",
    "read-only",
    "advisory-only",
    "manual-review only",
    "dry-run only",
    "provider-call dry-run packet contract only",
    "user trigger required",
    "operator confirmation required",
    "manual acceptance required",
    "provider-call boundary required",
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
    "manual user control remains required",
    "final application submission remains manually controlled by the user",
    "tailoring agent remains separate from final scoring",
    "generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase",
    "no real generate ai tailoring execution control was added",
    "no provider-call control was added",
    "no network-call control was added",
    "no dispatch control was added",
    "phase 29a provided a deterministic provider-call dry-run packet contract helper only",
    "phase 29b provided a read-only provider-call dry-run packet api readback only",
    "phase 29c provided a passive provider-call dry-run packet ui readback only",
)

PROTECTED_HASHES = {
    "src/app/api.py": "c783bf766e09f43b3650ddcc79bc7043aaa5bcaaf37ed4deb365a894c951a9d6",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "ca378dc0aee655d83a7af0d15e885313af5b719c2512eff10f3efc69cd43348a",
    "src/app/static/app_redesign.css": "3c55b13f7762c2118eabad4a32ca6c6a47b9674be44ac33058d3b55f97c4e5c5",
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


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


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


def test_release_checkpoint_doc_exists_with_exact_title():
    assert DOC_PATH.exists()
    assert _doc_text().startswith(
        "# Phase 29D Manual Generate AI Tailoring Preview Provider-Call Dry-Run Packet Release Checkpoint"
    )


def test_checkpoint_references_phase29a_through_phase29c():
    text = _doc_text()

    for phase in ("Phase 29A", "Phase 29B", "Phase 29C"):
        assert phase in text
    for tag in REQUIRED_TAGS:
        assert tag in text
    for marker in (
        "/api/manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-contract",
        "renderManualGenerateAiTailoringPreviewProviderCallDryRunPacketReadbackSection",
        "build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract",
    ):
        assert marker in text


def test_checkpoint_contains_required_safety_markers():
    text = " ".join(_doc_text().lower().split())

    for marker in SAFETY_MARKERS:
        assert marker in text


def test_phase29_surfaces_still_exist_in_source_code():
    helper_source = HELPER_PATH.read_text(encoding="utf-8")
    api_source = API_PATH.read_text(encoding="utf-8")
    js_source = JS_PATH.read_text(encoding="utf-8")

    assert (
        "build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract"
        in helper_source
    )
    assert (
        "/api/manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-contract"
        in api_source
    )
    assert (
        "renderManualGenerateAiTailoringPreviewProviderCallDryRunPacketReadbackSection"
        in js_source
    )


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase29d_changes_only_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
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
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if path != Path(__file__).resolve()
        and any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "phase29d_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint",
                "phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint",
                "changes_only",
            )
        )
    }

    assert changed <= allowed | legacy_guards
