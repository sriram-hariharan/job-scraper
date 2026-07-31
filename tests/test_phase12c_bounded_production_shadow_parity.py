from __future__ import annotations

from copy import deepcopy
import csv
import json

import pytest

from src.agents.production_shadow_graph import (
    PRODUCTION_SHADOW_EXECUTION_VERSION,
    PRODUCTION_SHADOW_NODE_ORDER,
    execute_production_shadow_graph,
)
from src.agents.production_shadow_parity import (
    PARITY_CLASSIFICATIONS,
    PARITY_STATUSES,
    PRODUCTION_SHADOW_PARITY_VERSION,
    ProductionShadowParityError,
    compare_production_shadow_parity,
)
from src.pipeline import post_planning_shadow as lifecycle_owner
from src.pipeline.shadow_observation_contract import parse_observation_json
from tests.test_phase12b_artifact_only_production_shadow_foundation import (
    _artifacts,
    _digests,
    _write_csv,
)


def _facts() -> dict[str, object]:
    return {
        "job_id": "job-0",
        "selected_resume_id": "resume-0",
        "queue_rank": 1,
        "action": "REVIEW",
        "advisory_priority": "manual_review",
        "advisory_reason_codes": ["review_requested", "operator_required"],
        "tailoring_decision": "manual_review_before_tailoring",
        "tailoring_reason_codes": ["review_requested"],
        "operator_review_lane": "review_before_action",
        "packet_generation_allowed": True,
        "requires_manual_review": True,
        "packet_resume": "resume-0",
    }


def _compare(
    *,
    authoritative: dict[str, object] | None = None,
    shadow: dict[str, object] | None = None,
    incomparable: dict[str, str] | None = None,
):
    return compare_production_shadow_parity(
        authoritative_facts=authoritative or _facts(),
        shadow_facts=shadow or _facts(),
        incomparable_fields=incomparable,
    )


def _classification(result, field):
    return next(
        row["classification"]
        for row in result["comparison_records"]
        if row["field"] == field
    )


def test_exact_parity_version_contract_and_deterministic_canonical_comparison():
    left = _facts()
    right = _facts()
    right["advisory_reason_codes"] = [
        "operator_required",
        "review_requested",
    ]
    first = _compare(authoritative=left, shadow=right)
    second = _compare(authoritative=deepcopy(left), shadow=deepcopy(right))
    assert first == second
    assert first["parity_version"] == PRODUCTION_SHADOW_PARITY_VERSION
    assert first["parity_status"] == "passed"
    assert first["substantive_mismatch_count"] == 0
    assert first["substantive_exact_match_count"] == 12
    assert set(PARITY_CLASSIFICATIONS) == {
        "exact_match",
        "mismatch",
        "authoritative_missing",
        "shadow_missing",
        "both_missing",
        "incomparable",
    }
    assert set(PARITY_STATUSES) == {
        "passed",
        "mismatch",
        "incomplete",
        "incomparable",
        "failed",
    }


def test_parity_is_deep_copy_contained_and_retains_no_raw_values():
    authoritative = _facts()
    shadow = _facts()
    before_left, before_right = deepcopy(authoritative), deepcopy(shadow)
    result = _compare(authoritative=authoritative, shadow=shadow)
    result["comparison_records"][0]["classification"] = "mismatch"
    assert authoritative == before_left
    assert shadow == before_right
    rendered = json.dumps(_compare(), sort_keys=True)
    assert "resume-0" not in rendered
    assert "job-0" not in rendered
    for row in _compare()["comparison_records"]:
        assert set(row) == {
            "field",
            "classification",
            "reason_code",
            "authoritative_present",
            "shadow_present",
            "authoritative_digest",
            "shadow_digest",
        }
    unsafe = _facts()
    unsafe["raw_provider_output"] = "SENSITIVE"
    with pytest.raises(ProductionShadowParityError, match="contract_invalid"):
        _compare(authoritative=unsafe)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("selected_resume_id", "resume-other"),
        ("queue_rank", 2),
        ("action", "APPLY"),
        ("advisory_priority", "apply_now"),
        ("advisory_reason_codes", ["different_reason"]),
        ("tailoring_decision", "tailor_before_apply"),
        ("tailoring_reason_codes", ["different_reason"]),
        ("operator_review_lane", "ready_to_apply"),
        ("packet_generation_allowed", False),
        ("requires_manual_review", False),
        ("packet_resume", "resume-other"),
    ],
)
def test_each_substantive_decision_mismatch_is_classified(field, replacement):
    shadow = _facts()
    shadow[field] = replacement
    result = _compare(shadow=shadow)
    assert _classification(result, field) == "mismatch"
    assert result["parity_status"] == "mismatch"
    assert result["substantive_mismatch_count"] == 1


@pytest.mark.parametrize(
    ("side", "classification"),
    [
        ("authoritative", "authoritative_missing"),
        ("shadow", "shadow_missing"),
    ],
)
def test_required_missing_fact_is_incomplete(side, classification):
    authoritative, shadow = _facts(), _facts()
    target = authoritative if side == "authoritative" else shadow
    target.pop("action")
    result = _compare(authoritative=authoritative, shadow=shadow)
    assert _classification(result, "action") == classification
    assert result["parity_status"] == "incomplete"


def test_optional_both_missing_and_explicit_incomparable_behavior():
    authoritative, shadow = _facts(), _facts()
    authoritative.pop("advisory_reason_codes")
    shadow.pop("advisory_reason_codes")
    result = _compare(authoritative=authoritative, shadow=shadow)
    assert _classification(result, "advisory_reason_codes") == "both_missing"
    assert result["parity_status"] == "passed"

    all_fields = {field: "schema_declared_incomparable" for field in _facts()}
    incomparable = _compare(incomparable=all_fields)
    assert incomparable["parity_status"] == "incomparable"
    assert incomparable["incomparable_count"] == 12


def test_malformed_allowlisted_value_fails_closed():
    authoritative = _facts()
    authoritative["queue_rank"] = True
    result = _compare(authoritative=authoritative)
    assert result["parity_status"] == "failed"
    assert _classification(result, "queue_rank") == "incomparable"


def test_graph_v2_runs_parity_before_finalization_and_preserves_artifacts(
    tmp_path,
):
    paths = _artifacts(tmp_path)
    before = _digests(paths)
    job_ids = ["job-0"]
    arguments = dict(paths)
    result = execute_production_shadow_graph(
        job_ids=job_ids,
        owner_user_id="owner-12c",
        pipeline_run_id="run-12c",
        context_id="context-12c",
        artifact_paths=arguments,
    )
    row = result["results"][0]
    assert result["execution_version"] == PRODUCTION_SHADOW_EXECUTION_VERSION
    assert row["status"] == "parity_completed"
    assert row["parity"]["parity_status"] == "passed"
    assert row["completed_node_order"] == list(PRODUCTION_SHADOW_NODE_ORDER)
    assert row["completed_node_order"][-2:] == [
        "compare_authoritative_parity",
        "finalize_shadow_observation",
    ]
    assert row["pending_node"] == "operator_review"
    assert result["artifact_digests_before"] == result[
        "artifact_digests_after"
    ]
    assert _digests(paths) == before
    assert job_ids == ["job-0"]
    assert arguments == paths
    for scope in (
        "provider_call",
        "production_write",
        "mutation",
        "application",
        "ats",
    ):
        assert result[f"{scope}_count"] == 0
        assert row[f"{scope}_count"] == 0


def test_one_incomplete_job_does_not_block_another(tmp_path):
    paths = _artifacts(tmp_path, jobs=2)
    priority = paths["advisory_priority"]
    rows = list(csv.DictReader(priority.open(encoding="utf-8")))
    _write_csv(priority, rows[:1])
    before = _digests(paths)
    result = execute_production_shadow_graph(
        job_ids=["job-0", "job-1"],
        owner_user_id="owner-12c",
        pipeline_run_id="run-12c",
        context_id="context-12c",
        artifact_paths=paths,
    )
    assert [row["status"] for row in result["results"]] == [
        "parity_completed",
        "input_rejected",
    ]
    assert _digests(paths) == before


def test_observation_persists_only_bounded_parity_and_disabled_writes_nothing(
    tmp_path, monkeypatch
):
    paths = _artifacts(tmp_path)
    execution = execute_production_shadow_graph(
        job_ids=["job-0"],
        owner_user_id="owner-12c",
        pipeline_run_id="run-12c",
        context_id="context-12c",
        artifact_paths=paths,
    )
    aggregate = lifecycle_owner._classify_command_payload(execution)
    aggregate.update(
        {
            "cleanup_categories": {},
            "process_liveness_confirmed": True,
        }
    )
    lifecycle = lifecycle_owner.prepare_post_planning_shadow(
        {
            lifecycle_owner.SHADOW_FLAG: "true",
            lifecycle_owner.PRODUCTION_SHADOW_FLAG: "true",
            "JOB_STACK_OWNER_USER_ID": "owner-12c",
            "JOB_APP_PIPELINE_RUN_ID": "run-12c",
        }
    )
    lifecycle.observation_root = tmp_path / "observations"
    monkeypatch.setattr(
        lifecycle_owner, "_run_shadow_command", lambda _command: aggregate
    )
    monkeypatch.setattr(
        "src.pipeline.runtime_status.update_counts", lambda **_counts: None
    )
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=paths["job_corpus"],
        output_dir=paths["execution_queue"].parent,
    )
    assert outcome["observation_store_status"] == "stored"
    record = parse_observation_json(
        next(lifecycle.observation_root.glob("*.jsonl")).read_bytes()
    )
    persisted = record.production_parity
    assert persisted["version"] == "production-shadow-observation-parity-v1"
    assert persisted["persisted_job_count"] == 1
    rendered = json.dumps(persisted)
    assert "resume-0" not in rendered
    assert "job-0" not in rendered
    assert "SENSITIVE" not in rendered

    disabled_root = tmp_path / "disabled-observations"
    disabled = lifecycle_owner.prepare_post_planning_shadow({})
    disabled.observation_root = disabled_root
    disabled.complete_after_authoritative_success(
        job_corpus_path=tmp_path / "unused",
        output_dir=tmp_path / "unused-output",
    )
    assert not disabled_root.exists()
