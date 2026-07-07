# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path
import subprocess

from src.agents import (
    jd_evidence_score_impact_planning_artifact_annotator_default_off as annotator,
)
from src.agents.jd_evidence_score_impact_planning_artifact_annotator_default_off import (
    build_jd_evidence_score_impact_planning_artifact_annotator_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/jd_evidence_score_impact_planning_artifact_annotator_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase39_jd_evidence_score_impact_planning_artifact_annotator_default_off.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_evidence_score_impact_planning_artifact_annotator",
    "read_only",
    "advisory_only",
    "preview_only",
    "deterministic_score_impact_annotation",
    "requires_manual_user_control",
    "planning_row_count",
    "valid_planning_row_count",
    "invalid_planning_row_count",
    "impact_rows_present",
    "impact_row_count",
    "annotation_policy",
    "annotated_rows",
    "unannotated_rows",
    "unmapped_rows",
    "impact_rows_by_key",
    "annotation_summary",
    "score_preview_available_count",
    "score_preview_blocked_count",
    "positive_impact_count",
    "negative_impact_count",
    "neutral_impact_count",
    "red_flag_review_count",
    "existing_score_fields_detected",
    "existing_scores_preserved",
    "annotation_findings",
    "missing_inputs",
    "annotator_key",
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
    "phase 39a jd evidence score impact planning artifact annotator default-off",
    "jd evidence score impact planning artifact annotator",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic score impact annotation",
    "annotates copied planning-like rows with score impact preview metadata",
    "matches planning rows to score impact rows by item_id, job_id, id, or row index",
    "produces score impact review recommendations",
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
    "final scoring remains deterministic and controlled by scoring logic",
    "phase38-jd-evidence-score-impact-preview-release-v1",
    "phase38b-jd-evidence-score-impact-preview-dry-run-command-default-off-v1",
    "phase38a-jd-evidence-score-impact-preview-default-off-v1",
    "phase37-jd-evidence-scoring-contribution-preview-release-v1",
    "phase37b-jd-evidence-scoring-contribution-preview-dry-run-command-default-off-v1",
    "phase37a-jd-evidence-scoring-contribution-preview-default-off-v1",
    "phase36-jd-evidence-final-scoring-feature-adapter-release-v1",
    "phase35c-jd-signal-planning-artifact-evidence-enrichment-dry-run-command-default-off-v1",
    "phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
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
    "src/app/api.py": "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96",
    "src/app/services.py": "e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c",
    "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
    "src/app/static/app_redesign.css": "81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_suggestions.py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _planning_row(**extra) -> dict:
    row = {
        "item_id": "item-1",
        "job_id": "job-1",
        "id": "id-1",
        "title": "Data Engineer",
        "company": "Acme",
        "existing_score_present": True,
        "existing_score_field": "final_score",
        "existing_score_value": 80,
        "final_score": 80,
    }
    for key, value in extra.items():
        row[key] = value
    return row


def _impact_row(**extra) -> dict:
    row = {
        "item_id": "item-1",
        "job_id": "job-1",
        "title": "Data Engineer",
        "company": "Acme",
        "existing_score_present": True,
        "existing_score_field": "final_score",
        "existing_score_value": 80,
        "base_score_for_preview": 80,
        "bounded_advisory_contribution_points": 7,
        "hypothetical_score_preview": 87,
        "score_preview_delta": 7,
        "score_preview_available": True,
        "score_preview_blocked_reason": "",
        "impact_band": "positive",
        "requires_red_flag_review": False,
        "hypothetical_score_preview_produced": True,
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    for key, value in extra.items():
        row[key] = value
    return row


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "39A"
    assert payload["default_off"] is True
    assert payload["jd_evidence_score_impact_planning_artifact_annotator"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["preview_only"] is True
    assert payload["deterministic_score_impact_annotation"] is True
    assert payload["requires_manual_user_control"] is True
    assert payload["hypothetical_score_preview_produced"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_helper_exists_and_is_import_safe(capsys):
    importlib.reload(annotator)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(build_jd_evidence_score_impact_planning_artifact_annotator_default_off)


def test_missing_and_non_list_planning_rows_block_with_missing_reason():
    for value in (None, {"item_id": "bad"}):
        payload = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
            planning_rows=value,
            impact_rows=[_impact_row()],
        )
        _assert_safe(payload)
        assert payload["missing_inputs"] == ["planning_rows"]
        assert payload["annotated_rows"] == []
        assert payload["unmapped_rows"][0]["reason"] == "planning_rows must be supplied as a list"


def test_missing_impact_rows_returns_copied_unannotated_planning_rows():
    row = _planning_row()
    original = deepcopy(row)
    payload = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=[row]
    )
    _assert_safe(payload)
    assert row == original
    assert payload["missing_inputs"] == ["impact_rows"]
    assert payload["annotated_rows"] == []
    assert payload["unannotated_rows"][0]["item_id"] == "item-1"
    assert payload["unannotated_rows"][0]["score_impact_annotation_source"] == "missing_impact_rows"


def test_impact_result_shapes_are_accepted_and_explicit_rows_take_precedence():
    row = _planning_row(item_id="explicit")
    direct = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=[_planning_row()],
        impact_result={"impact_rows": [_impact_row()]},
    )
    nested = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=[_planning_row(item_id="nested")],
        impact_result={
            "impact_result": {
                "impact_packet": {
                    "impact_rows": [_impact_row(item_id="nested", job_id="nested")]
                }
            }
        },
    )
    explicit = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=[row],
        impact_result={"impact_rows": [_impact_row(item_id="wrong", job_id="wrong")]},
        impact_rows=[_impact_row(item_id="explicit", job_id="explicit")],
    )
    assert direct["annotated_rows"][0]["score_impact_annotation_source"] == "impact_result"
    assert nested["annotated_rows"][0]["score_impact_review_recommendation"] == "positive_review"
    assert explicit["annotated_rows"][0]["score_impact_annotation_source"] == "impact_rows"


def test_invalid_planning_and_impact_rows_do_not_crash_and_are_reported():
    payload = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=[_planning_row(), "bad-planning"],
        impact_rows=[_impact_row(), "bad-impact"],
    )
    _assert_safe(payload)
    assert payload["valid_planning_row_count"] == 1
    assert payload["invalid_planning_row_count"] == 1
    assert payload["unmapped_rows"][0]["reason"] == "planning row must be a dictionary"
    assert payload["annotation_findings"]["invalid_impact_rows"] == [
        {"input_index": 1, "reason": "impact row must be a dictionary"}
    ]


def test_matching_by_item_id_job_id_id_and_row_index_is_deterministic():
    rows = [
        _planning_row(item_id="item-match", job_id="other", id="other"),
        _planning_row(item_id="", job_id="job-match", id="other"),
        _planning_row(item_id="", job_id="", id="id-match"),
        _planning_row(item_id="", job_id="", id=""),
    ]
    impacts = [
        _impact_row(item_id="item-match", job_id="x", score_preview_delta=2),
        _impact_row(item_id="", job_id="job-match", score_preview_delta=3),
        _impact_row(item_id="", job_id="", id="id-match", score_preview_delta=4),
        _impact_row(item_id="", job_id="", id="", score_preview_delta=5),
    ]
    payload = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=rows,
        impact_rows=impacts,
    )
    _assert_safe(payload)
    assert [
        row["score_impact_preview"]["score_preview_delta"]
        for row in payload["annotated_rows"]
    ] == [2, 3, 4, 5]


def test_matched_rows_include_required_annotation_fields_and_preserve_order():
    payload = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=[_planning_row(item_id="a"), _planning_row(item_id="b")],
        impact_rows=[_impact_row(item_id="a"), _impact_row(item_id="b", score_preview_delta=0)],
    )
    _assert_safe(payload)
    assert [row["item_id"] for row in payload["annotated_rows"]] == ["a", "b"]
    row = payload["annotated_rows"][0]
    assert "score_impact_preview_result" in row
    assert "score_impact_preview" in row
    assert "score_impact_review_summary" in row
    assert row["score_impact_review_recommendation"] == "positive_review"
    assert row["score_impact_annotation_ready"] is True
    assert row["final_score_produced"] is False
    assert row["existing_score_changed"] is False


def test_recommendations_cover_blocked_red_flag_positive_negative_neutral_and_unmatched():
    rows = [
        _planning_row(item_id="blocked", job_id="blocked-job"),
        _planning_row(item_id="red", job_id="red-job"),
        _planning_row(item_id="positive", job_id="positive-job"),
        _planning_row(item_id="negative", job_id="negative-job"),
        _planning_row(item_id="neutral", job_id="neutral-job"),
        _planning_row(item_id="missing", job_id="missing-job"),
    ]
    impacts = [
        _impact_row(item_id="blocked", job_id="blocked-impact", score_preview_available=False, score_preview_blocked_reason="blocked"),
        _impact_row(item_id="red", job_id="red-impact", requires_red_flag_review=True),
        _impact_row(item_id="positive", job_id="positive-impact", score_preview_delta=1),
        _impact_row(item_id="negative", job_id="negative-impact", score_preview_delta=-1),
        _impact_row(item_id="neutral", job_id="neutral-impact", score_preview_delta=0),
    ]
    payload = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=rows,
        impact_rows=impacts,
    )
    assert [
        row["score_impact_review_recommendation"]
        for row in payload["annotated_rows"]
    ] == [
        "manual_review",
        "manual_review",
        "positive_review",
        "negative_review",
        "neutral_review",
        "unmatched",
    ]
    assert payload["positive_impact_count"] == 1
    assert payload["negative_impact_count"] == 1
    assert payload["neutral_impact_count"] == 1
    assert payload["red_flag_review_count"] == 1


def test_unmatched_rows_can_be_left_unannotated_by_policy():
    payload = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=[_planning_row(item_id="missing", job_id="missing-job", id="missing-id")],
        impact_rows=["invalid", _impact_row(item_id="other", job_id="other-job", id="other-id")],
        annotation_policy={"annotate_unmatched_rows": False},
    )
    _assert_safe(payload)
    assert payload["annotated_rows"] == []
    assert payload["unannotated_rows"][0]["score_impact_review_recommendation"] == "unmatched"


def test_existing_score_fields_are_detected_preserved_and_not_changed():
    row = _planning_row(existing_score_value=91, final_score=91)
    original = deepcopy(row)
    payload = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=[row],
        impact_rows=[_impact_row(existing_score_value=91)],
    )
    _assert_safe(payload)
    assert row == original
    annotated = payload["annotated_rows"][0]
    assert annotated["final_score"] == 91
    assert annotated["existing_score_value"] == 91
    assert annotated["existing_score_changed"] is False
    assert payload["existing_score_fields_detected"] == [
        {"row_key": "item-1", "field": "final_score", "value": 91}
    ]
    assert payload["existing_scores_preserved"] is True


def test_no_final_score_is_produced_and_summary_is_deterministic():
    first = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=[_planning_row()],
        impact_rows=[_impact_row()],
    )
    second = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=[_planning_row()],
        impact_rows=[_impact_row()],
    )
    assert first["annotation_summary"] == second["annotation_summary"]
    assert first["annotator_key"] == second["annotator_key"]
    assert first["final_score_produced"] is False
    assert "final_application_score" not in str(first).lower()


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


def test_changed_files_are_limited_to_phase39a_and_legacy_guard_tests():
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
            "src/app/auth_ui.py",
            "src/app/static/shell.js",
            "src/app/ui_shell.py",
            "src/app/static/media/adv_diagnostics_img.svg",
        "src/app/ui.py",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.css",
            "src/app/static/scan_workspace_review.css",
            "src/app/static/styles.css",
        "src/app/static/app_redesign.css",
        "tests/test_queue_ui_metadata_contract.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "src/tailoring/llm.py",
        "generate_tailoring_suggestions.py",
        "src/tailoring/rendering.py",
        "tests/test_score_first_scan.py",
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
            "docs/phase71_tailoring_workspace_artifact_path_preload_repair_default_off.md",
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
    allowed |= {
        "src/agents/orchestrator_adapter_harness.py",
        "tests/test_phase80b_controlled_advisory_chain_trace_persistence.py",
    }
    unexpected = {
        path
        for path in changed
        if path not in allowed
        and not (path.startswith("tests/test_") and path.endswith(".py"))
    }
    assert unexpected == set()
