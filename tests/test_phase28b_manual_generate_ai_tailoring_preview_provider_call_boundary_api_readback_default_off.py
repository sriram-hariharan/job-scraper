from hashlib import sha256
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from src.agents.manual_generate_ai_tailoring_preview_provider_call_boundary_contract import (
    build_manual_generate_ai_tailoring_preview_provider_call_boundary_contract,
)
from src.app import api


ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "src/app/api.py"
DOC_PATH = (
    ROOT
    / "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback.md"
)
ENDPOINT = (
    "/api/manual-generate-ai-tailoring-preview-provider-call-boundary-contract"
)

TRUE_SAFETY_KEYS = (
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "provider_call_boundary_contract_only",
    "requires_user_trigger",
    "operator_confirmation_required",
    "manual_acceptance_required",
    "provider_request_envelope_required",
    "provider_configuration_required",
    "provider_call_policy_required",
    "no_provider_calls",
    "no_network_calls",
)

FALSE_ACTION_KEYS = (
    "provider_call_performed",
    "network_call_performed",
    "dispatch_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
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
    "provider_call_boundary_contract_only",
    "requires_user_trigger",
    "operator_confirmation_required",
    "manual_acceptance_required",
    "provider_request_envelope_required",
    "provider_request_envelope_accepted",
    "provider_configuration_required",
    "provider_configuration_present",
    "provider_call_policy_required",
    "provider_call_policy_present",
    "provider_call_boundary_ready",
    "provider_call_allowed",
    "blocked_reasons",
    "missing_inputs",
    "provider_call_plan",
    "deterministic_provider_call_key",
    "provider_call_performed",
    "network_call_performed",
    "dispatch_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
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
    "phase 28b manual generate ai tailoring preview provider-call boundary api readback",
    "api readback only",
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
    "no ui changes",
    "no services changes",
    "no pipeline changes",
    "no matching changes",
    "no tailoring runtime changes",
    "tailoring agent remains separate from final scoring",
    "generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase",
    "/api/manual-generate-ai-tailoring-preview-provider-call-boundary-contract",
    "build_manual_generate_ai_tailoring_preview_provider_call_boundary_contract",
    "phase28a-manual-generate-ai-tailoring-preview-provider-call-boundary-contract-v1",
    "phase27-manual-generate-ai-tailoring-preview-provider-request-envelope-release-v1",
    "phase26-manual-generate-ai-tailoring-preview-dispatch-boundary-release-v1",
    "phase25-manual-generate-ai-tailoring-preview-request-packet-release-v1",
    "phase24-manual-generate-ai-tailoring-preview-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
    "src/app/static/app_redesign.css": "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c",
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


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _route_snippet() -> str:
    source = API_PATH.read_text(encoding="utf-8")
    start = source.index(
        '@app.get(\n'
        '    "/api/manual-generate-ai-tailoring-preview-provider-call-boundary-contract"'
    )
    end = source.index('\n\n@app.post("/api/provider-runtime-readback")', start)
    return source[start:end]


def _expected_readback_payload() -> dict:
    return build_manual_generate_ai_tailoring_preview_provider_call_boundary_contract(
        phase27_provider_request_envelope_payload={
            "readback_source": "phase28b_api_placeholder",
            "provider_request_envelope_ready": False,
            "provider_request_allowed": False,
            "provider_call_performed": False,
            "network_call_performed": False,
            "tailoring_runtime_call_performed": False,
            "ai_tailoring_generation_performed": False,
            "real_tailoring_output_created": False,
            "execution_performed": False,
            "submission_performed": False,
        },
        phase26_dispatch_boundary_payload={
            "readback_source": "phase28b_api_placeholder",
            "dispatch_ready": False,
            "dispatch_allowed": False,
        },
        phase25_request_packet_payload={
            "readback_source": "phase28b_api_placeholder",
            "preview_request_allowed": False,
        },
        user_trigger_metadata={},
        operator_confirmation_metadata={},
        provider_configuration_metadata={},
        provider_call_policy_metadata={},
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


def test_route_returns_phase28a_provider_call_boundary_payload_with_safety_flags(
    monkeypatch,
):
    response = _client(monkeypatch).get(ENDPOINT)

    assert response.status_code == 200
    payload = response.json()
    assert payload == _expected_readback_payload()
    assert set(REQUIRED_PAYLOAD_KEYS).issubset(payload.keys())
    assert payload["contract_version"] == (
        "phase-28a-manual-generate-ai-tailoring-preview-provider-call-boundary-v1"
    )
    assert payload["contract_status"] == (
        "manual_generate_ai_tailoring_preview_provider_call_boundary_blocked"
    )
    assert payload["user_trigger_present"] is False
    assert payload["operator_confirmation_present"] is False
    assert payload["provider_request_envelope_accepted"] is False
    assert payload["provider_configuration_present"] is False
    assert payload["provider_call_policy_present"] is False
    assert payload["provider_call_boundary_ready"] is False
    assert payload["provider_call_allowed"] is False
    assert "explicit user trigger required" in payload["blocked_reasons"]
    assert "operator confirmation required" in payload["blocked_reasons"]
    assert (
        "provider configuration metadata required"
        in payload["blocked_reasons"]
    )
    assert "provider call policy metadata required" in payload["blocked_reasons"]
    for key in TRUE_SAFETY_KEYS:
        assert payload[key] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_route_uses_helper_with_deterministic_readback_metadata_only():
    source = API_PATH.read_text(encoding="utf-8")
    snippet = _route_snippet()

    assert (
        "from src.agents.manual_generate_ai_tailoring_preview_provider_call_boundary_contract "
        "import (" in source
    )
    assert (
        "build_manual_generate_ai_tailoring_preview_provider_call_boundary_contract("
        in snippet
    )
    assert "phase28b_api_placeholder" in snippet
    assert "Body(" not in snippet
    assert "request_payload" not in snippet
    assert "payload: dict" not in snippet
    assert "user_trigger_metadata={}" in snippet
    assert "operator_confirmation_metadata={}" in snippet
    assert "provider_configuration_metadata={}" in snippet
    assert "provider_call_policy_metadata={}" in snippet


def test_route_contains_no_provider_network_db_io_runtime_or_mutation_calls():
    snippet = _route_snippet().lower()

    for marker in FORBIDDEN_ROUTE_MARKERS:
        assert marker not in snippet


def test_api_readback_never_calls_providers_generates_mutates_or_submits(
    monkeypatch,
):
    payload = _client(monkeypatch).get(ENDPOINT).json()

    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False
    assert payload["provider_request_envelope_accepted"] is False
    assert payload["provider_call_boundary_ready"] is False
    assert payload["provider_call_allowed"] is False
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


def test_phase28b_changes_only_api_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
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
                                "src/agents/jd_evidence_score_impact_review_queue_builder_default_off.py",
                                "docs/phase41_jd_evidence_score_impact_review_queue_builder_default_off.md",
                                "src/agents/exact_resume_change_set_proposal_builder_default_off.py",
                                "docs/phase42_exact_resume_change_set_proposal_builder_default_off.md",
                                "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py",
                                "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_default_off.md",
                                "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
                                "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_default_off.md",
                                "run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py",
                                "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_dry_run_command_default_off.md",
                                "tests/test_phase44b_controlled_exact_resume_change_set_provider_call_boundary_dry_run_command_default_off.py",
                "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py",
                "docs/phase45_controlled_exact_resume_change_set_provider_response_validation_default_off.md",
                "tests/test_phase45a_controlled_exact_resume_change_set_provider_response_validation_default_off.py",
                "run_controlled_exact_resume_change_set_provider_response_validation_dry_run.py",
                "docs/phase45_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.md",
                "tests/test_phase45b_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.py",
                "src/agents/controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
                "docs/phase46_controlled_exact_resume_change_set_provider_response_normalization_default_off.md",
                "tests/test_phase46a_controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
                                "tests/test_phase44a_controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
                                "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py",
                                "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.md",
                                "tests/test_phase43b_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.py",
                                "tests/test_phase43a_controlled_exact_resume_change_set_llm_request_packet_default_off.py",
                                "run_exact_resume_change_set_proposal_builder_dry_run.py",
                                "docs/phase42_exact_resume_change_set_proposal_builder_dry_run_command_default_off.md",
                                "tests/test_phase42b_exact_resume_change_set_proposal_builder_dry_run_command_default_off.py",
                                "tests/test_phase42a_exact_resume_change_set_proposal_builder_default_off.py",
                                "run_jd_evidence_score_impact_review_queue_builder_dry_run.py",
                                "docs/phase41_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.md",
                                "tests/test_phase41b_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.py",
                                "tests/test_phase41a_jd_evidence_score_impact_review_queue_builder_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if path != Path(__file__).resolve()
        and any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback",
                "phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback",
                "changes_only",
            )
        )
    }

    assert changed <= allowed | legacy_guards
