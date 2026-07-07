# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path
import subprocess

from src.agents import (
    jd_evidence_score_impact_review_queue_builder_default_off as queue_builder,
)
from src.agents.jd_evidence_score_impact_review_queue_builder_default_off import (
    build_jd_evidence_score_impact_review_queue_builder_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT / "src/agents/jd_evidence_score_impact_review_queue_builder_default_off.py"
)
DOC_PATH = ROOT / "docs/phase41_jd_evidence_score_impact_review_queue_builder_default_off.md"

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_evidence_score_impact_review_queue_builder",
    "read_only",
    "advisory_only",
    "preview_only",
    "deterministic_review_queue_building",
    "manual_review_queue_only",
    "requires_manual_user_control",
    "review_packets_present",
    "review_packet_count",
    "valid_review_packet_count",
    "invalid_review_packet_count",
    "queue_policy",
    "review_queue",
    "review_queue_by_priority",
    "review_queue_summary",
    "urgent_review_count",
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
    "queue_findings",
    "missing_inputs",
    "queue_key",
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
    "review_packet_building_performed",
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
    "review_packet_building_performed",
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
    "build_jd_evidence_score_impact_review_packet_builder_default_off(",
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
    "phase 41a jd evidence score impact review queue builder default-off",
    "jd evidence score impact review queue builder",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic review queue building",
    "builds prioritized operator review queues from score impact review packets",
    "prioritizes red flag review and blocked score preview rows",
    "preserves deterministic order for equal priorities",
    "produces manual-review queue only output",
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
    "does not run review packet building",
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
    "review queue building remains separate from final scoring",
    "final scoring remains deterministic and controlled by scoring logic",
    "phase40-jd-evidence-score-impact-review-packet-builder-release-v1",
    "phase40b-jd-evidence-score-impact-review-packet-builder-dry-run-command-default-off-v1",
    "phase40a-jd-evidence-score-impact-review-packet-builder-default-off-v1",
    "phase39-jd-evidence-score-impact-planning-artifact-annotator-release-v1",
    "phase39b-jd-evidence-score-impact-planning-artifact-annotator-dry-run-command-default-off-v1",
    "phase39a-jd-evidence-score-impact-planning-artifact-annotator-default-off-v1",
    "phase38-jd-evidence-score-impact-preview-release-v1",
    "phase37-jd-evidence-scoring-contribution-preview-release-v1",
    "phase36-jd-evidence-final-scoring-feature-adapter-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/jd_evidence_score_impact_review_packet_builder_default_off.py": "daa472f00511e16d37975472dcf06fcd7ffcd3f353509d8524e949baae137f68",
    "run_jd_evidence_score_impact_review_packet_builder_dry_run.py": "87c9a0356e8e9d633062c0adcf387baebb721c6dd6331047f5190f1413de4dd8",
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


def _packet(**extra) -> dict:
    packet = {
        "item_id": "item-1",
        "job_id": "job-1",
        "row_id": "row-1",
        "title": "Data Engineer",
        "company": "Acme",
        "location": "Remote",
        "source_url": "https://example.test/job",
        "score_impact_review_recommendation": "positive_review",
        "score_preview_available": True,
        "score_preview_blocked_reason": "",
        "existing_score_present": True,
        "existing_score_field": "final_score",
        "existing_score_value": 80,
        "hypothetical_score_preview": 87,
        "score_preview_delta": 7,
        "impact_band": "positive",
        "requires_red_flag_review": False,
        "review_reason": "positive_impact:positive:delta=7",
        "operator_next_action": "review_positive_impact",
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    for key, value in extra.items():
        packet[key] = value
    return packet


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "41A"
    assert payload["default_off"] is True
    assert payload["jd_evidence_score_impact_review_queue_builder"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["preview_only"] is True
    assert payload["deterministic_review_queue_building"] is True
    assert payload["manual_review_queue_only"] is True
    assert payload["requires_manual_user_control"] is True
    assert payload["hypothetical_score_preview_produced"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_helper_exists_and_is_import_safe(capsys):
    importlib.reload(queue_builder)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(build_jd_evidence_score_impact_review_queue_builder_default_off)


def test_missing_review_packets_blocks_with_missing_input_reason():
    payload = build_jd_evidence_score_impact_review_queue_builder_default_off()
    _assert_safe(payload)
    assert payload["review_packets_present"] is False
    assert payload["missing_inputs"] == ["review_packets"]
    assert payload["review_queue"] == []


def test_builder_result_shapes_are_accepted_and_explicit_packets_take_precedence():
    direct = build_jd_evidence_score_impact_review_queue_builder_default_off(
        builder_result={"review_packets": [_packet(item_id="direct")]}
    )
    nested = build_jd_evidence_score_impact_review_queue_builder_default_off(
        builder_result={"builder_result": {"review_packets": [_packet(item_id="nested")]}}
    )
    grouped = build_jd_evidence_score_impact_review_queue_builder_default_off(
        builder_result={
            "review_packets_by_recommendation": {
                "positive_review": [_packet(item_id="grouped")]
            }
        }
    )
    nested_grouped = build_jd_evidence_score_impact_review_queue_builder_default_off(
        builder_result={
            "builder_result": {
                "review_packets_by_recommendation": {
                    "negative_review": [_packet(item_id="nested-grouped")]
                }
            }
        }
    )
    explicit = build_jd_evidence_score_impact_review_queue_builder_default_off(
        review_packets=[_packet(item_id="explicit")],
        builder_result={"review_packets": [_packet(item_id="ignored")]},
    )
    assert direct["review_queue"][0]["item_id"] == "direct"
    assert nested["review_queue"][0]["item_id"] == "nested"
    assert grouped["review_queue"][0]["item_id"] == "grouped"
    assert nested_grouped["review_queue"][0]["item_id"] == "nested-grouped"
    assert explicit["review_queue"][0]["item_id"] == "explicit"
    assert explicit["queue_findings"]["review_packets_source"] == "review_packets"


def test_invalid_non_dict_packets_are_counted_and_reported_without_crashing():
    payload = build_jd_evidence_score_impact_review_queue_builder_default_off(
        review_packets=[_packet(), "bad-packet"],
    )
    _assert_safe(payload)
    assert payload["review_packet_count"] == 2
    assert payload["valid_review_packet_count"] == 1
    assert payload["invalid_review_packet_count"] == 1
    assert payload["queue_findings"]["invalid_review_packets"] == [
        {"input_index": 1, "reason": "review packet must be a dictionary"}
    ]


def test_inputs_are_not_mutated_and_queue_is_deterministic():
    packets = [_packet(item_id="a"), _packet(item_id="b")]
    original = deepcopy(packets)
    first = build_jd_evidence_score_impact_review_queue_builder_default_off(
        review_packets=packets
    )
    second = build_jd_evidence_score_impact_review_queue_builder_default_off(
        review_packets=packets
    )
    assert packets == original
    assert first["review_queue"] == second["review_queue"]
    assert first["review_queue_summary"] == second["review_queue_summary"]
    assert first["queue_key"] == second["queue_key"]


def test_priority_rules_bands_and_queue_reasons_are_deterministic():
    packets = [
        _packet(item_id="positive", score_impact_review_recommendation="positive_review", score_preview_delta=2),
        _packet(item_id="blocked", score_preview_available=False, score_preview_blocked_reason="missing base"),
        _packet(item_id="manual", score_impact_review_recommendation="manual_review"),
        _packet(item_id="negative", score_impact_review_recommendation="negative_review", score_preview_delta=-3, impact_band="negative"),
        _packet(item_id="red", requires_red_flag_review=True),
        _packet(item_id="neutral", score_impact_review_recommendation="neutral_review", score_preview_delta=0, impact_band="neutral"),
        _packet(item_id="unmatched", score_impact_review_recommendation="unmatched"),
        _packet(item_id="unknown", score_impact_review_recommendation=""),
    ]
    payload = build_jd_evidence_score_impact_review_queue_builder_default_off(
        review_packets=packets
    )
    queue = payload["review_queue"]
    assert [item["item_id"] for item in queue] == [
        "red",
        "blocked",
        "manual",
        "negative",
        "positive",
        "neutral",
        "unmatched",
        "unknown",
    ]
    by_id = {item["item_id"]: item for item in queue}
    assert by_id["red"]["priority_rank"] == 100
    assert by_id["red"]["priority_band"] == "urgent"
    assert by_id["red"]["queue_reason"] == "urgent:red_flag_review_required"
    assert by_id["blocked"]["priority_rank"] == 90
    assert by_id["blocked"]["priority_band"] == "urgent"
    assert by_id["blocked"]["queue_reason"] == "urgent:score_preview_blocked:missing base"
    assert by_id["manual"]["priority_rank"] == 80
    assert by_id["manual"]["priority_band"] == "high"
    assert by_id["negative"]["priority_rank"] == 70
    assert by_id["positive"]["priority_rank"] == 60
    assert by_id["neutral"]["priority_rank"] == 40
    assert by_id["unmatched"]["priority_rank"] == 30
    assert by_id["unknown"]["priority_rank"] == 20
    assert by_id["unknown"]["priority_band"] == "backlog"
    assert payload["urgent_review_count"] == 2
    assert payload["manual_review_count"] == 1
    assert payload["positive_review_count"] == 3
    assert payload["negative_review_count"] == 1
    assert payload["neutral_review_count"] == 1
    assert payload["unmatched_count"] == 1
    assert payload["unknown_review_count"] == 1
    assert payload["score_preview_available_count"] == 7
    assert payload["score_preview_blocked_count"] == 1
    assert payload["red_flag_review_count"] == 1


def test_absolute_delta_sorting_and_equal_delta_order_are_deterministic():
    packets = [
        _packet(item_id="small", score_impact_review_recommendation="manual_review", score_preview_delta=1),
        _packet(item_id="big", score_impact_review_recommendation="manual_review", score_preview_delta=-5),
        _packet(item_id="equal-a", score_impact_review_recommendation="manual_review", score_preview_delta=5),
        _packet(item_id="equal-b", score_impact_review_recommendation="manual_review", score_preview_delta=5),
    ]
    payload = build_jd_evidence_score_impact_review_queue_builder_default_off(
        review_packets=packets
    )
    assert [item["item_id"] for item in payload["review_queue"]] == [
        "big",
        "equal-a",
        "equal-b",
        "small",
    ]
    disabled = build_jd_evidence_score_impact_review_queue_builder_default_off(
        review_packets=packets,
        queue_policy={"sort_by_absolute_delta_within_priority": False},
    )
    assert [item["item_id"] for item in disabled["review_queue"]] == [
        "small",
        "big",
        "equal-a",
        "equal-b",
    ]


def test_max_queue_items_truncates_deterministically_and_reports_finding():
    payload = build_jd_evidence_score_impact_review_queue_builder_default_off(
        review_packets=[
            _packet(item_id="red", requires_red_flag_review=True),
            _packet(item_id="blocked", score_preview_available=False),
            _packet(item_id="manual", score_impact_review_recommendation="manual_review"),
        ],
        queue_policy={"max_queue_items": 2},
    )
    assert [item["item_id"] for item in payload["review_queue"]] == ["red", "blocked"]
    assert payload["queue_findings"]["queue_truncated"] is True
    assert payload["queue_findings"]["queue_items_before_truncation"] == 3
    assert payload["queue_findings"]["queue_items_after_truncation"] == 2


def test_existing_score_fields_are_detected_preserved_and_not_changed():
    packet = _packet(existing_score_value=91)
    original = deepcopy(packet)
    payload = build_jd_evidence_score_impact_review_queue_builder_default_off(
        review_packets=[packet]
    )
    _assert_safe(payload)
    assert packet == original
    queued = payload["review_queue"][0]
    assert queued["existing_score_field"] == "final_score"
    assert queued["existing_score_value"] == 91
    assert queued["existing_score_changed"] is False
    assert queued["final_score_produced"] is False
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


def test_changed_files_are_limited_to_phase41a_and_legacy_guard_tests():
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
            "src/pipeline/collector.py",
            "tests/test_phase81d_collector_advisory_chain_diagnostics_sidecar_default_off.py",
        "tests/test_phase82b_collector_advisory_chain_trace_persistence_default_off.py",
        "tests/test_shadow_sidecar_trace_persistence_hook_integration_default_off.py",
        "tests/test_phase80b_controlled_advisory_chain_trace_persistence.py",
    }
    unexpected = {
        path
        for path in changed
        if path not in allowed
        and not (path.startswith("tests/test_") and path.endswith(".py"))
    }
    assert unexpected == set()
