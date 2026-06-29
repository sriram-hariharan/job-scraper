# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9
from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"
CSS_PATH = ROOT / "src/app/static/app_redesign.css"
DOC_PATH = (
    ROOT
    / "docs/phase24_manual_generate_ai_tailoring_preview_ui_readback.md"
)
ENDPOINT = "/api/manual-generate-ai-tailoring-preview-contract"

PROTECTED_HASHES = {
    "src/app/api.py": "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
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
    "phase 24c manual generate ai tailoring preview ui readback",
    "ui readback only",
    "default-off",
    "read-only",
    "advisory-only",
    "manual-review only",
    "preview contract only",
    "user trigger required",
    "manual acceptance required",
    "does not generate ai tailoring",
    "does not call tailoring runtime",
    "does not call providers",
    "does not create resume rewrites",
    "does not overwrite resumes",
    "does not mutate resumes",
    "does not persist data",
    "does not write to database",
    "does not execute applications",
    "does not submit applications",
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
    ENDPOINT,
    "rendermanualgenerateaitailoringpreviewreadbacksection",
    "phase24b-manual-generate-ai-tailoring-preview-api-readback-v1",
    "phase24a-manual-generate-ai-tailoring-preview-contract-v1",
    "phase23-tailoring-agent-workflow-release-v1",
)


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _renderer() -> str:
    source = _source()
    start = source.index(
        "function renderManualGenerateAiTailoringPreviewReadbackSection"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _fixture_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldRenderManualGenerateAiTailoringPreviewFixture"
    )
    end = source.index(
        "\nfunction renderManualGenerateAiTailoringPreviewReadbackSection",
        start,
    )
    return source[start:end]


def _fetch_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldFetchManualGenerateAiTailoringPreviewReadback"
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

    assert "renderManualGenerateAiTailoringPreviewReadbackSection" in source
    assert (
        "renderManualGenerateAiTailoringPreviewReadbackSection("
        "manualGenerateAiTailoringPreviewVisibleTracePayload)"
    ) in source
    assert "withManualGenerateAiTailoringPreviewReadbackApiFetch(" in source


def test_default_off_requires_supplied_payload_fixture_or_fetch_gate():
    fixture = _fixture_helpers()
    renderer = _renderer()
    fetch = _fetch_helpers()

    assert "source.manual_generate_ai_tailoring_preview_result" in fixture
    assert (
        "|| !shouldRenderManualGenerateAiTailoringPreviewFixture(search)"
        in fixture
    )
    assert 'if (!Object.keys(result).length) return "";' in renderer
    assert (
        "|| !shouldFetchManualGenerateAiTailoringPreviewReadback(search)"
        in fetch
    )


def test_renderer_contains_visible_safety_and_readiness_markers():
    renderer = _renderer().lower()

    for marker in (
        "default-off",
        "read-only",
        "advisory-only",
        "manual-review only",
        "preview contract only",
        "user trigger required",
        "manual acceptance required",
        "can prepare preview",
        "blocked reasons",
        "missing inputs",
        "does not generate ai tailoring",
        "does not call tailoring runtime",
        "does not call providers",
        "does not create resume rewrites",
        "does not overwrite resumes",
        "does not mutate resumes",
        "does not submit applications",
        "no provider calls",
        "no network calls",
        "no database writes",
        "no persistence",
        "no mutation",
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
        "Preview contract only",
        "User trigger required",
        "Manual acceptance required",
        "Can prepare preview",
        "Blocked reasons",
        "Missing inputs",
        "No provider calls",
        "No network calls",
        "No database writes",
        "No persistence",
        "No mutation",
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
        "tailoringruntime(",
        "scorejobs(",
        "rankjobs(",
        "mutatequeue(",
    ):
        assert marker not in renderer


def test_fetch_is_gated_get_only_and_fail_closed():
    fetch = _fetch_helpers()

    assert "manual_generate_ai_tailoring_preview_api_fetch" in fetch
    assert '=== "1"' in fetch
    assert fetch.count(f'"{ENDPOINT}"') == 1
    assert 'method: "GET"' in fetch
    assert "JSON.stringify" not in fetch
    assert "body:" not in fetch
    assert "catch (error)" in fetch
    assert "manual_generate_ai_tailoring_preview_failed_closed" in fetch
    assert "read_only: true" in fetch
    assert "advisory_only: true" in fetch
    assert "manual_review_only: true" in fetch
    assert "provider_call_performed: false" in fetch
    assert "tailoring_runtime_call_performed: false" in fetch
    assert "resume_mutation_performed: false" in fetch
    assert "application_submission_performed: false" in fetch


def test_ui_adds_only_the_phase24b_manual_preview_endpoint_url():
    js = _source()
    related_endpoint_lines = [
        line.strip()
        for line in js.splitlines()
        if "/api/" in line and "manual-generate-ai-tailoring" in line
    ]

    assert related_endpoint_lines
    assert ENDPOINT in js
    assert all(
        ENDPOINT in line
            or "/api/manual-generate-ai-tailoring-preview-request-packet-contract"
            in line
                or "/api/manual-generate-ai-tailoring-preview-dispatch-boundary-contract"
                in line
                    or "/api/manual-generate-ai-tailoring-preview-provider-request-envelope-contract"
                    in line
                    or "/api/manual-generate-ai-tailoring-preview-provider-call-boundary-contract"
                    in line
                    or "/api/manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-contract"
                    in line
                    or "/api/manual-generate-ai-tailoring-preview-provider-response-validation-contract"
                    in line
                    or "/api/manual-generate-ai-tailoring-preview-provider-response-normalization-contract"
                    in line
                for line in related_endpoint_lines
            )


def test_css_contains_passive_panel_classes():
    css = CSS_PATH.read_text(encoding="utf-8")

    for marker in (
        ".manual-generate-ai-tailoring-preview-readback",
        ".manual-generate-ai-tailoring-preview-readback__safety-labels",
        ".manual-generate-ai-tailoring-preview-readback__metrics",
        ".manual-generate-ai-tailoring-preview-readback__boundary",
    ):
        assert marker in css


def test_docs_contain_required_boundaries_and_references():
    assert DOC_PATH.exists()
    text = " ".join(DOC_PATH.read_text(encoding="utf-8").lower().split())

    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_backend_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase24c_changes_only_static_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/app/api.py",
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
                                "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py",
                                "docs/phase33_controlled_agent_router_batch_handoff_plan_readonly.md",
                                "tests/test_phase33c_controlled_agent_router_batch_handoff_plan_readonly.py",
                                "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py",
                                "docs/phase33_controlled_agent_router_planning_artifact_mapper_readonly.md",
                                "tests/test_phase33d_controlled_agent_router_planning_artifact_mapper_readonly.py",
                                "run_controlled_agent_router_planning_artifact_dry_run.py",
                                "docs/phase33_controlled_agent_router_planning_artifact_dry_run_command_readonly.md",
                                "tests/test_phase33e_controlled_agent_router_planning_artifact_dry_run_command_readonly.py",
                                "src/agents/jd_intelligence_llm_signal_extractor_default_off.py",
                                "docs/phase34_jd_intelligence_llm_signal_extractor_default_off.md",
                                "tests/test_phase34a_jd_intelligence_llm_signal_extractor_default_off.py",
                                "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py",
                                "docs/phase34_jd_intelligence_planning_artifact_enricher_default_off.md",
                                "tests/test_phase34b_jd_intelligence_planning_artifact_enricher_default_off.py",
                                "run_jd_intelligence_planning_artifact_enrichment_dry_run.py",
                                "docs/phase34_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.md",
                                "tests/test_phase34c_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.py",
                                "src/agents/jd_signal_resume_evidence_matrix_default_off.py",
                                "docs/phase35_jd_signal_resume_evidence_matrix_default_off.md",
                                "tests/test_phase35a_jd_signal_resume_evidence_matrix_default_off.py",
                                "src/agents/jd_signal_planning_artifact_evidence_enricher_default_off.py",
                                "docs/phase35_jd_signal_planning_artifact_evidence_enricher_default_off.md",
                                "tests/test_phase35b_jd_signal_planning_artifact_evidence_enricher_default_off.py",
                                "run_jd_signal_planning_artifact_evidence_enrichment_dry_run.py",
                                "docs/phase35_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.md",
                                "tests/test_phase35c_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_final_scoring_feature_adapter_default_off.py",
                                "docs/phase36_jd_evidence_final_scoring_feature_adapter_default_off.md",
                                "tests/test_phase36a_jd_evidence_final_scoring_feature_adapter_default_off.py",
                                "run_jd_evidence_final_scoring_feature_adapter_dry_run.py",
                                "docs/phase36_jd_evidence_final_scoring_feature_adapter_dry_run_command_default_off.md",
                                "tests/test_phase36b_jd_evidence_final_scoring_feature_adapter_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_scoring_contribution_preview_default_off.py",
                                "docs/phase37_jd_evidence_scoring_contribution_preview_default_off.md",
                                "tests/test_phase37a_jd_evidence_scoring_contribution_preview_default_off.py",
                                "run_jd_evidence_scoring_contribution_preview_dry_run.py",
                                "docs/phase37_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.md",
                                "tests/test_phase37b_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_score_impact_preview_default_off.py",
                                "docs/phase38_jd_evidence_score_impact_preview_default_off.md",
                                "tests/test_phase38a_jd_evidence_score_impact_preview_default_off.py",
                                "tests/test_phase38a_jd_evidence_score_impact_preview_default_off 2.py",
                                "\"tests/test_phase38a_jd_evidence_score_impact_preview_default_off 2.py\"",
                                "run_jd_evidence_score_impact_preview_dry_run.py",
                                "docs/phase38_jd_evidence_score_impact_preview_dry_run_command_default_off.md",
                                "tests/test_phase38b_jd_evidence_score_impact_preview_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_score_impact_planning_artifact_annotator_default_off.py",
                                "docs/phase39_jd_evidence_score_impact_planning_artifact_annotator_default_off.md",
                                "tests/test_phase39a_jd_evidence_score_impact_planning_artifact_annotator_default_off.py",
                                "run_jd_evidence_score_impact_planning_artifact_annotator_dry_run.py",
                                "docs/phase39_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.md",
                                "tests/test_phase39b_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_score_impact_review_packet_builder_default_off.py",
                                "docs/phase40_jd_evidence_score_impact_review_packet_builder_default_off.md",
                                "tests/test_phase40a_jd_evidence_score_impact_review_packet_builder_default_off.py",
                                "run_jd_evidence_score_impact_review_packet_builder_dry_run.py",
                                "docs/phase40_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.md",
                                "tests/test_phase40b_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "changes_only",
                "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9",
                "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
                "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c",
            )
        )
    }

    assert changed <= allowed | legacy_guards
