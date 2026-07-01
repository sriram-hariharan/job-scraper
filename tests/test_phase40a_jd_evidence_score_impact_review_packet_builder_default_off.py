# phase56b legacy guard marker: changes_only b78c29d523f5d21b26128a5ec6dd47e6820b10f9b226dfbcb96ba7353e1a98cd 16b2769b2a0713614f5c1293a7ca511f1032c0aa539ae4676d817d73d4184429
# phase56a legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f b78c29d523f5d21b26128a5ec6dd47e6820b10f9b226dfbcb96ba7353e1a98cd
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path
import subprocess

from src.agents import (
    jd_evidence_score_impact_review_packet_builder_default_off as builder,
)
from src.agents.jd_evidence_score_impact_review_packet_builder_default_off import (
    build_jd_evidence_score_impact_review_packet_builder_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/jd_evidence_score_impact_review_packet_builder_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase40_jd_evidence_score_impact_review_packet_builder_default_off.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_evidence_score_impact_review_packet_builder",
    "read_only",
    "advisory_only",
    "preview_only",
    "deterministic_review_packet_building",
    "manual_review_packet_only",
    "requires_manual_user_control",
    "annotated_rows_present",
    "annotated_row_count",
    "valid_annotated_row_count",
    "invalid_annotated_row_count",
    "review_policy",
    "review_packets",
    "review_packets_by_recommendation",
    "review_packet_summary",
    "manual_review_count",
    "positive_review_count",
    "negative_review_count",
    "neutral_review_count",
    "unmatched_count",
    "unknown_review_count",
    "score_preview_available_count",
    "score_preview_blocked_count",
    "red_flag_review_count",
    "existing_score_fields_detected",
    "existing_scores_preserved",
    "packet_findings",
    "missing_inputs",
    "packet_key",
    "hypothetical_score_preview_produced",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "scoring_feature_preparation_performed",
    "contribution_preview_performed",
    "score_impact_preview_performed",
    "planning_annotation_performed",
    "final_scoring_performed",
    "tailoring_opportunity_check_performed",
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
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

FALSE_ACTION_KEYS = {
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "scoring_feature_preparation_performed",
    "contribution_preview_performed",
    "score_impact_preview_performed",
    "planning_annotation_performed",
    "final_scoring_performed",
    "tailoring_opportunity_check_performed",
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
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

FORBIDDEN_SOURCE_MARKERS = (
    "from src.pipeline",
    "import src.pipeline",
    "from src.matching",
    "import src.matching",
    "from src.tailoring",
    "import src.tailoring",
    "generate_tailoring_suggestions",
    "application_execution_queue",
    "from src.app",
    "import src.app",
    "from src.storage",
    "import src.storage",
    "requests",
    "httpx",
    "urllib",
    "openai",
    "anthropic",
    "psycopg",
    "sqlite",
    "subprocess",
    "run_prefilter(",
    "score_resume_job_match(",
    "build_jd_evidence_score_impact_preview_default_off(",
    "build_jd_evidence_scoring_contribution_preview_default_off(",
    "build_jd_evidence_score_impact_planning_artifact_annotator_default_off(",
    "execute_application(",
    "submit_application(",
    "provider_call(",
    "network_call(",
)

FORBIDDEN_WRITE_MARKERS = (
    ".update(",
    "update(",
    ".write_text(",
    ".write_bytes(",
    ".mkdir(",
    ".save(",
    ".insert(",
)

DOC_MARKERS = (
    "phase 40a jd evidence score impact review packet builder default-off",
    "jd evidence score impact review packet builder",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic review packet building",
    "builds operator review packets from score impact annotated planning rows",
    "groups review packets by score impact review recommendation",
    "produces manual-review packet only output",
    "preserves existing score fields",
    "does not produce final application score",
    "does not change existing scoring logic",
    "does not call matching/scoring modules",
    "does not run relevance prefilter",
    "does not run jd intelligence extraction",
    "does not run evidence matching",
    "does not run scoring feature preparation",
    "does not run contribution preview",
    "does not run score impact preview",
    "does not run planning annotation",
    "does not run tailoring opportunity check",
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
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "manual user control remains required",
    "jd intelligence remains separate from final scoring",
    "evidence matching remains separate from final scoring",
    "scoring feature preparation remains separate from final scoring",
    "contribution preview remains separate from final scoring",
    "score impact preview remains separate from final scoring",
    "planning annotation remains separate from final scoring",
    "review packet building remains separate from final scoring",
    "final scoring remains deterministic and controlled by scoring logic",
    "phase39-jd-evidence-score-impact-planning-artifact-annotator-release-v1",
    "phase39b-jd-evidence-score-impact-planning-artifact-annotator-dry-run-command-default-off-v1",
    "phase39a-jd-evidence-score-impact-planning-artifact-annotator-default-off-v1",
    "phase38-jd-evidence-score-impact-preview-release-v1",
    "phase38b-jd-evidence-score-impact-preview-dry-run-command-default-off-v1",
    "phase38a-jd-evidence-score-impact-preview-default-off-v1",
    "phase37-jd-evidence-scoring-contribution-preview-release-v1",
    "phase36-jd-evidence-final-scoring-feature-adapter-release-v1",
    "phase35c-jd-signal-planning-artifact-evidence-enrichment-dry-run-command-default-off-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/jd_evidence_score_impact_planning_artifact_annotator_default_off.py": "fd0903a249d46f609f2fd790ac5100b2ef7554132749de349b33162c22b4ed6f",
    "run_jd_evidence_score_impact_planning_artifact_annotator_dry_run.py": "61401301966d5e7957e9aabacd485d42b663e3ca8f2f1bc3d774ee407aeaabce",
    "src/agents/jd_evidence_score_impact_preview_default_off.py": "94799582377fabd147fb134746d5b17a88b500589a6241e91a263356f1678ef1",
    "run_jd_evidence_score_impact_preview_dry_run.py": "73c27a8c1e86a880a02766e9a64917b5c699ebacac5e127c6330c51b3c1a6bbb",
    "src/agents/jd_evidence_scoring_contribution_preview_default_off.py": "6bfd39eb1bc51e01b990ca0a44e13645187eb0a07cb6ac1e91f6c9456cd41fd8",
    "run_jd_evidence_scoring_contribution_preview_dry_run.py": "3890723174effc02370619c563ca33f41101f55318bd4c54796a9a03408aeae5",
    "src/agents/jd_evidence_final_scoring_feature_adapter_default_off.py": "f7ec839c8810439f9ceb2fccd9938d34cbb2f623590f0c2c2bf80afeba6cc105",
    "run_jd_evidence_final_scoring_feature_adapter_dry_run.py": "1cae3e0cbefef29dcb176ce16df85d241d247411ab781eb5d838a21f9c425fad",
    "src/agents/jd_signal_planning_artifact_evidence_enricher_default_off.py": "0404ff9c89895b13cf5ccc55029820d2ff5b82fb2dbd3c0c1e426bd0e83335c8",
    "src/agents/jd_signal_resume_evidence_matrix_default_off.py": "1d0275337f4785730b27515f0e9830601fd9e3cc941fe21d2f7bb8257d64e9be",
    "run_jd_signal_planning_artifact_evidence_enrichment_dry_run.py": "9db84fca7407329f0b0f84f46fb030f4c975fef9db0197188f0429b435f3c7c3",
    "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py": "f8e365ab51de647dc6b45ff0c99cce075273eec61e12fc96c744118e1ca68c53",
    "src/agents/jd_intelligence_llm_signal_extractor_default_off.py": "a73124801ce6768aebb934e1c6a7e76d4f9888bbb7b0ca28eb93e882e06f4f6c",
    "run_jd_intelligence_planning_artifact_enrichment_dry_run.py": "d3e45057168f4daabba13077f0d27b6eb89be4d2f443c4a43a42274557ef26bb",
    "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py": "1966a4d95eaf57b735545efd00e28803bba077192c81668165e9b3f491491fe8",
    "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py": "7824233cbb4c6efd75481a8097a041488adfbd53f7c97e4832c02b8822741834",
    "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py": "4f01b4e58c8e517ec633331da44341ee5596d486ae7d40d38fdca4666d6fa47e",
    "src/agents/controlled_agent_router_readonly.py": "c1cac3d8d1858b5143d0c3ca0082f3b908410020a0e4220c1dea9531cbf3655d",
    "run_controlled_agent_router_planning_artifact_dry_run.py": "1e49a69da5b306272319f2bef5e7162467f294aff4cbe37e8167125a56777dc4",
    "src/app/api.py": "f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f",
    "src/app/services.py": "b78c29d523f5d21b26128a5ec6dd47e6820b10f9b226dfbcb96ba7353e1a98cd",
    "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
    "src/app/static/app_redesign.css": "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _annotated_row(**extra) -> dict:
    row = {
        "item_id": "item-1",
        "job_id": "job-1",
        "id": "row-1",
        "title": "Data Engineer",
        "company": "Acme",
        "location": "Remote",
        "source_url": "https://example.test/job",
        "existing_score_present": True,
        "existing_score_field": "final_score",
        "existing_score_value": 80,
        "final_score": 80,
        "score_impact_preview_result": {"matched": True},
        "score_impact_preview": {
            "matched": True,
            "hypothetical_score_preview": 87,
            "score_preview_delta": 7,
            "score_preview_available": True,
            "score_preview_blocked_reason": "",
            "impact_band": "positive",
            "requires_red_flag_review": False,
        },
        "score_impact_review_summary": {"recommendation": "positive_review"},
        "score_impact_review_recommendation": "positive_review",
        "score_impact_annotation_ready": True,
        "score_impact_annotation_source": "impact_rows",
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    for key, value in extra.items():
        row[key] = value
    return row


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "40A"
    assert payload["default_off"] is True
    assert payload["jd_evidence_score_impact_review_packet_builder"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["preview_only"] is True
    assert payload["deterministic_review_packet_building"] is True
    assert payload["manual_review_packet_only"] is True
    assert payload["requires_manual_user_control"] is True
    assert payload["hypothetical_score_preview_produced"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_helper_exists_and_is_import_safe(capsys):
    importlib.reload(builder)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(build_jd_evidence_score_impact_review_packet_builder_default_off)


def test_missing_annotated_rows_blocks_with_missing_input_reason():
    payload = build_jd_evidence_score_impact_review_packet_builder_default_off()
    _assert_safe(payload)
    assert payload["annotated_rows_present"] is False
    assert payload["missing_inputs"] == ["annotated_rows"]
    assert payload["review_packets"] == []
    assert payload["review_packet_summary"]["review_packet_count"] == 0


def test_annotator_result_shapes_are_accepted_and_explicit_rows_take_precedence():
    direct = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotator_result={"annotated_rows": [_annotated_row(item_id="direct")]}
    )
    nested = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotator_result={
            "annotator_result": {"annotated_rows": [_annotated_row(item_id="nested")]}
        }
    )
    summary_nested = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotator_result={
            "annotator_result": {
                "annotation_summary": {
                    "annotated_rows": [_annotated_row(item_id="summary")]
                }
            }
        }
    )
    explicit = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotated_rows=[_annotated_row(item_id="explicit")],
        annotator_result={"annotated_rows": [_annotated_row(item_id="ignored")]},
    )
    assert direct["review_packets"][0]["item_id"] == "direct"
    assert nested["review_packets"][0]["item_id"] == "nested"
    assert summary_nested["review_packets"][0]["item_id"] == "summary"
    assert explicit["review_packets"][0]["item_id"] == "explicit"
    assert explicit["packet_findings"]["annotated_rows_source"] == "annotated_rows"


def test_invalid_non_dict_rows_are_counted_and_reported_without_crashing():
    payload = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotated_rows=[_annotated_row(), "bad-row"],
    )
    _assert_safe(payload)
    assert payload["annotated_row_count"] == 2
    assert payload["valid_annotated_row_count"] == 1
    assert payload["invalid_annotated_row_count"] == 1
    assert payload["packet_findings"]["invalid_annotated_rows"] == [
        {"input_index": 1, "reason": "annotated row must be a dictionary"}
    ]


def test_input_rows_are_not_mutated_and_packets_are_deterministic():
    rows = [_annotated_row(item_id="a"), _annotated_row(item_id="b")]
    original = deepcopy(rows)
    first = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotated_rows=rows
    )
    second = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotated_rows=rows
    )
    assert rows == original
    assert first["review_packets"] == second["review_packets"]
    assert first["review_packet_summary"] == second["review_packet_summary"]
    assert first["packet_key"] == second["packet_key"]


def test_packets_group_by_recommendation_and_operator_actions_are_deterministic():
    rows = [
        _annotated_row(item_id="manual", score_impact_review_recommendation="manual_review"),
        _annotated_row(item_id="positive", score_impact_review_recommendation="positive_review"),
        _annotated_row(item_id="negative", score_impact_review_recommendation="negative_review"),
        _annotated_row(item_id="neutral", score_impact_review_recommendation="neutral_review"),
        _annotated_row(item_id="unmatched", score_impact_review_recommendation="unmatched"),
        _annotated_row(item_id="unknown", score_impact_review_recommendation=""),
    ]
    payload = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotated_rows=rows
    )
    grouped = payload["review_packets_by_recommendation"]
    assert [packet["item_id"] for packet in grouped["manual_review"]] == ["manual"]
    assert grouped["manual_review"][0]["operator_next_action"] == "review_before_scoring"
    assert grouped["positive_review"][0]["operator_next_action"] == "review_positive_impact"
    assert grouped["negative_review"][0]["operator_next_action"] == "review_negative_impact"
    assert grouped["neutral_review"][0]["operator_next_action"] == "review_neutral_impact"
    assert grouped["unmatched"][0]["operator_next_action"] == "match_or_ignore_unmatched"
    assert grouped["unknown"][0]["operator_next_action"] == "inspect_unknown_recommendation"
    assert payload["manual_review_count"] == 1
    assert payload["positive_review_count"] == 1
    assert payload["negative_review_count"] == 1
    assert payload["neutral_review_count"] == 1
    assert payload["unmatched_count"] == 1
    assert payload["unknown_review_count"] == 1


def test_review_reasons_cover_blocked_red_flag_positive_negative_and_neutral():
    def with_preview(**preview_extra) -> dict:
        row = _annotated_row()
        preview = deepcopy(row["score_impact_preview"])
        for key, value in preview_extra.items():
            preview[key] = value
        row["score_impact_preview"] = preview
        return row

    rows = [
        with_preview(
            item_id="blocked",
            score_preview_available=False,
            score_preview_blocked_reason="missing base score",
        ),
        with_preview(item_id="red", requires_red_flag_review=True),
        with_preview(item_id="positive", score_preview_delta=3, impact_band="positive"),
        with_preview(item_id="negative", score_preview_delta=-3, impact_band="negative"),
        with_preview(item_id="neutral", score_preview_delta=0, impact_band="neutral"),
    ]
    rows[0]["score_impact_review_recommendation"] = "manual_review"
    rows[1]["score_impact_review_recommendation"] = "manual_review"
    rows[2]["score_impact_review_recommendation"] = "positive_review"
    rows[3]["score_impact_review_recommendation"] = "negative_review"
    rows[4]["score_impact_review_recommendation"] = "neutral_review"
    payload = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotated_rows=rows
    )
    reasons = [packet["review_reason"] for packet in payload["review_packets"]]
    assert "score_preview_blocked:missing base score" in reasons
    assert "red_flag_review_required" in reasons
    assert "positive_impact:positive:delta=3" in reasons
    assert "negative_impact:negative:delta=-3" in reasons
    assert "neutral_impact:neutral:delta=0" in reasons
    assert payload["score_preview_available_count"] == 4
    assert payload["score_preview_blocked_count"] == 1
    assert payload["red_flag_review_count"] == 1


def test_existing_score_fields_are_detected_preserved_and_not_changed():
    row = _annotated_row(existing_score_value=91, final_score=91)
    original = deepcopy(row)
    payload = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotated_rows=[row]
    )
    _assert_safe(payload)
    assert row == original
    packet = payload["review_packets"][0]
    assert packet["existing_score_field"] == "final_score"
    assert packet["existing_score_value"] == 91
    assert packet["existing_score_changed"] is False
    assert packet["final_score_produced"] is False
    assert payload["existing_score_fields_detected"] == [
        {"row_key": "item-1", "field": "final_score", "value": 91}
    ]
    assert payload["existing_scores_preserved"] is True
    assert "final_application_score" not in str(payload).lower()


def test_source_has_no_forbidden_imports_calls_or_writes():
    source = HELPER_PATH.read_text(encoding="utf-8")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source
    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source


def test_docs_contain_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_changed_files_are_limited_to_phase40a_and_legacy_guard_tests():
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
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
        "run_controlled_exact_resume_change_set_provider_response_normalization_dry_run.py",
        "docs/phase46_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off.md",
        "tests/test_phase46b_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py",
        "docs/phase47_controlled_exact_resume_change_set_manual_review_packet_builder_default_off.md",
        "tests/test_phase47a_controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py",
        "run_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run.py",
        "docs/phase47_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run_command_default_off.md",
        "tests/test_phase47b_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
        "docs/phase48_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.md",
        "tests/test_phase48a_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run.py",
        "docs/phase48_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run_command_default_off.md",
        "tests/test_phase48b_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
        "docs/phase49_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.md",
        "tests/test_phase49a_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run.py",
        "docs/phase49_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.md",
        "tests/test_phase49b_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.py",
            "src/agents/controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py",
            "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.md",
            "tests/test_phase50a_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py",
        "run_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run.py",
        "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.md",
        "tests/test_phase50b_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_default_off.md",
        "tests/test_phase51a_controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "run_controlled_exact_resume_change_set_manual_decision_packet_dry_run.py",
        "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.md",
        "tests/test_phase51b_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "docs/phase52_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.md",
        "tests/test_phase52a_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run.py",
        "docs/phase52_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run_command_default_off.md",
        "tests/test_phase52b_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
        "docs/phase53_controlled_exact_resume_change_set_approved_change_plan_packet_default_off.md",
        "tests/test_phase53a_controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
        "run_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run.py",
        "docs/phase53_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run_command_default_off.md",
        "tests/test_phase53b_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py",
        "docs/phase54_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.md",
        "tests/test_phase54a_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py",
        "src/app/services.py",
        "src/app/api.py",
        "docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off.md",
        "tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off.py",
        "src/app/planning_ui.py",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.js",
        "docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.md",
        "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.py",
        "tests/test_three_core_agent_shadow_sidecar_bridge_default_off.py",

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
    unexpected = {
        path
        for path in changed
        if path not in allowed
        and not (path.startswith("tests/test_") and path.endswith(".py"))
    }
    assert unexpected == set()
