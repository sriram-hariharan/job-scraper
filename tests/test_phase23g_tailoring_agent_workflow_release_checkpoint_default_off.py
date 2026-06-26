from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT / "docs/phase23_tailoring_agent_workflow_release_checkpoint.md"
)
API_PATH = ROOT / "src/app/api.py"
JS_PATH = ROOT / "src/app/static/agentic_review.js"
HELPER_PATH = (
    ROOT / "src/agents/generate_ai_tailoring_action_boundary_contract.py"
)

REQUIRED_TAGS = (
    "phase23f-generate-ai-tailoring-action-boundary-ui-readback-v1",
    "phase23e-generate-ai-tailoring-action-boundary-api-readback-v1",
    "phase23d-generate-ai-tailoring-action-boundary-contract-v1",
    "phase23c-tailoring-agent-opportunity-ui-readback-v1",
    "phase23b-tailoring-agent-opportunity-api-readback-v1",
    "phase23a-tailoring-agent-opportunity-contract-v1",
    "phase22-core-agent-evidence-materialization-release-v1",
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
    "tailoring agent remains separate from final scoring",
    "opportunity detection only identifies tailoring opportunities",
    "opportunity readback does not generate ai tailoring",
    "generate ai tailoring remains user-triggered only",
    "action-boundary readback does not generate ai tailoring",
    "action-boundary readback does not call tailoring runtime",
    "action-boundary readback does not call providers",
    "action-boundary readback does not create resume rewrites",
    "action-boundary readback does not overwrite resumes",
    "action-boundary readback does not submit applications",
    "user trigger is required",
    "manual acceptance is required before any future resume edit",
    "generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase",
    "no silent resume rewrite",
    "no automatic resume overwrite",
    "no real generate ai tailoring button or control was added in phase 23f",
)

PROTECTED_HASHES = {
    "src/app/api.py": "c9e50dddb147be99f42ca3fee4d0589711cf3a38e67bb9f7abb32ff85e45579d",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "898a88b49c765d59c099132a049aad79ea3c42774ad58912c0aac9b0d859d9a2",
    "src/app/static/app_redesign.css": "83bcc1e4f1c276e42e7306e30a2beb2a60a4f92bc0efe41f2525d4540d866167",
    "src/agents/generate_ai_tailoring_action_boundary_contract.py": "5c7675f889daa3342258be5d8eac5c191b196a84795238c658eb73cb76672953",
    "src/agents/tailoring_agent_opportunity_contract.py": "e61e910176a315e11b2e403a33920a53726c9df8ed0213f0121b5c6eb0c1d8b3",
    "src/agents/core_agent_evidence_materialization_preview.py": "d1b0862cf0355192a45a7b45fbeaa622d72e16b7c5234c71bea75aea90db9110",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
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
        "# Phase 23G Tailoring-Agent Workflow Release Checkpoint"
    )


def test_checkpoint_references_phase23a_through_phase23f():
    text = _doc_text()

    for phase in (
        "Phase 23A",
        "Phase 23B",
        "Phase 23C",
        "Phase 23D",
        "Phase 23E",
        "Phase 23F",
    ):
        assert phase in text
    for tag in REQUIRED_TAGS:
        assert tag in text


def test_checkpoint_contains_required_safety_markers():
    text = " ".join(_doc_text().lower().split())

    for marker in SAFETY_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase23_surfaces_still_exist_in_source_code():
    api_source = API_PATH.read_text(encoding="utf-8")
    js_source = JS_PATH.read_text(encoding="utf-8")
    helper_source = HELPER_PATH.read_text(encoding="utf-8")

    assert "/api/tailoring-agent-opportunity-contract" in api_source
    assert "renderTailoringAgentOpportunityReadbackSection" in js_source
    assert (
        "build_generate_ai_tailoring_action_boundary_contract"
        in helper_source
    )
    assert "/api/generate-ai-tailoring-action-boundary" in api_source
    assert (
        "renderGenerateAiTailoringActionBoundaryReadbackSection"
        in js_source
    )


def test_no_runtime_source_files_are_changed_by_this_checkpoint():
    changed_runtime = {
        path
        for path in _changed_files()
        if path.startswith(
            (
                "src/",
                "application_execution_queue.py",
                "pipeline_runner.py",
                "run_pipeline.py",
            )
        )
    } - {
        "src/app/api.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "src/agents/manual_generate_ai_tailoring_preview_contract.py",
        "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py",
    }

    assert changed_runtime == set()


def test_no_new_runtime_provider_execution_or_submission_markers():
    changed = _changed_files()
    runtime_changes = [
        path
        for path in changed
        if path.startswith("src/")
        and path != "src/app/api.py"
        and path != "src/app/static/agentic_review.js"
        and path != "src/app/static/app_redesign.css"
        and path != "src/agents/manual_generate_ai_tailoring_preview_contract.py"
        and path != "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py"
    ]
    forbidden = (
        "provider_call(",
        "database_write",
        "persist_decision",
        "persist_audit",
        "mutate_resume",
        "mutate_application",
        "execute_application",
        "submit_application",
        "auto_apply",
        "auto_submit",
    )

    for relative_path in runtime_changes:
        source = (ROOT / relative_path).read_text(encoding="utf-8").lower()
        for marker in forbidden:
            assert marker not in source


def test_phase23g_changes_only_docs_tests_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/app/api.py",
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
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "changes_only",
                "c9e50dddb147be99f42ca3fee4d0589711cf3a38e67bb9f7abb32ff85e45579d",
                "898a88b49c765d59c099132a049aad79ea3c42774ad58912c0aac9b0d859d9a2",
                "83bcc1e4f1c276e42e7306e30a2beb2a60a4f92bc0efe41f2525d4540d866167",
            )
        )
    }

    assert changed <= allowed | legacy_guards
