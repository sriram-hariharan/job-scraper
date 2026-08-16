from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import socket
import stat

import pytest

from src.evaluation import controlled_provider_benchmark_evidence_runtime as evidence_runtime
from src.evaluation import controlled_provider_benchmark_harness as harness
from src.evaluation import controlled_provider_benchmark_human_review as review
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
)
from src.evaluation.provider_fixture_benchmark import load_fixture_case_corpus


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/evaluation/controlled_provider_benchmark_human_review.py"
)
FIXED_EXECUTION_TIME = "2026-07-25T00:00:00Z"
FIXED_REVIEW_TIME = "2026-07-26T14:30:00Z"
REVIEW_REQUIRED = {
    "jd_intelligence",
    "resume_fallback_ranking",
    "ambiguous_resume_adjudication",
    "critic_evaluation",
    "tailoring_generation",
    "tailoring_refinement",
    "tailoring_judge",
    "manual_scan_phrase",
    "manual_provider_preview",
}
REVIEW_NOT_REQUIRED = {
    "skill_extraction",
    "job_fit_evaluation",
    "grounded_rag_answer",
}
PRIOR_SUBJECTIVE_RUBRIC_CRITERION_IDS = {
    "jd_intelligence": {
        "factual_grounding",
        "semantic_correctness",
        "completeness",
        "instruction_adherence",
    },
    "resume_fallback_ranking": {
        "ranking_consistency",
        "relevance",
        "factual_grounding",
        "usefulness",
    },
    "ambiguous_resume_adjudication": {
        "evidence_preservation",
        "recommendation_consistency",
        "uncertainty_handling",
        "factual_grounding",
    },
    "critic_evaluation": {
        "evidence_support",
        "decision_correctness",
        "reason_relevance",
        "factual_grounding",
    },
    "tailoring_generation": {
        "source_fact_preservation",
        "relevance",
        "semantic_correctness",
        "usefulness",
    },
    "tailoring_refinement": {
        "meaning_preservation",
        "factual_grounding",
        "instruction_adherence",
        "usefulness",
    },
    "tailoring_judge": {
        "winner_consistency",
        "evidence_based_judgment",
        "semantic_correctness",
        "factual_grounding",
    },
    "manual_scan_phrase": {
        "phrase_relevance",
        "source_fact_preservation",
        "scan_usefulness",
        "factual_grounding",
    },
}


@pytest.fixture(scope="module", autouse=True)
def repository_subjective_review_packet_baseline():
    output_root = ROOT / "outputs/provider_benchmark"
    return tuple(
        sorted(
            path.relative_to(ROOT).as_posix()
            for path in output_root.glob("subjective-review-packet-*.json")
        )
    )


class GoldenTransport:
    def __init__(self, outputs, *, fail_workload=None):
        self.outputs = deepcopy(outputs)
        self.fail_workload = fail_workload
        self.calls = []

    def __call__(self, packet, timeout_seconds):
        self.calls.append((deepcopy(packet), timeout_seconds))
        output = deepcopy(self.outputs[packet["case_alias"]])
        if packet["workload_id"] == self.fail_workload:
            output = {}
        return {
            "normalized_output": output,
            "provider": packet["provider"],
            "model": packet["model"],
            "latency_ms": 5.0,
            "input_token_count": 11,
            "output_token_count": 7,
            "provider_outcome_category": "success",
        }


@pytest.fixture(scope="module")
def controlled_inputs():
    plan = build_controlled_provider_benchmark_plan()
    pricing = harness.load_synthetic_pricing_fixture()
    authorization = harness.load_synthetic_authorization_fixture(
        plan=plan,
        pricing=pricing,
    )
    corpus = load_fixture_case_corpus()
    outputs = {
        transmission["case_alias"]: deepcopy(case["expected_output"])
        for transmission, case in zip(
            plan["transmission_review"], corpus["cases"]
        )
        if transmission["eligible_for_later_controlled_transmission"]
    }
    return plan, authorization, pricing, outputs


@pytest.fixture(scope="module")
def completed_evidence(controlled_inputs):
    plan, authorization, pricing, outputs = controlled_inputs
    transport = GoldenTransport(outputs)
    evidence = evidence_runtime.execute_provider_neutral_evidence_run(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        transport=transport,
        execution_time_source=lambda: FIXED_EXECUTION_TIME,
    )
    assert len(transport.calls) == 44
    return evidence


@pytest.fixture(scope="module")
def failed_review_evidence(controlled_inputs):
    plan, authorization, pricing, outputs = controlled_inputs
    transport = GoldenTransport(outputs, fail_workload="jd_intelligence")
    evidence = evidence_runtime.execute_provider_neutral_evidence_run(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        transport=transport,
        execution_time_source=lambda: FIXED_EXECUTION_TIME,
        maximum_schedule_items=4,
    )
    assert evidence["hard_failure_present"] is True
    return evidence


def _summary(evidence, workload_id, *, provider=None):
    return next(
        row
        for row in evidence["grading_summaries"]
        if row["workload_id"] == workload_id
        and (provider is None or row["provider"] == provider)
    )


def _record(
    controlled_inputs,
    evidence,
    *,
    workload_id="jd_intelligence",
    decision="approved",
    reviewer_id="Reviewer-01",
    review_time=FIXED_REVIEW_TIME,
    provider="groq",
):
    plan, authorization, pricing, _outputs = controlled_inputs
    summary = _summary(evidence, workload_id, provider=provider)
    return review.build_post_result_human_review_record(
        evidence=evidence,
        schedule_key=summary["schedule_key"],
        decision=decision,
        reviewer_id=reviewer_id,
        review_time_source=lambda: review_time,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )


def _validate(controlled_inputs, evidence, record):
    plan, authorization, pricing, _outputs = controlled_inputs
    return review.validate_post_result_human_review_record(
        record,
        evidence=evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )


def _assess(controlled_inputs, evidence, workload_id, record=None):
    plan, authorization, pricing, _outputs = controlled_inputs
    summary = _summary(evidence, workload_id, provider="groq")
    return review.assess_post_result_human_review(
        evidence=evidence,
        schedule_key=summary["schedule_key"],
        review_record=record,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )


def _rebuild_with_summary_mutation(
    controlled_inputs,
    completed_evidence,
    mutation,
):
    plan, authorization, pricing, _outputs = controlled_inputs
    checkpoint = deepcopy(completed_evidence["checkpoint"])
    summary = _summary(checkpoint, "jd_intelligence", provider="groq")
    mutation(summary)
    return evidence_runtime.build_provider_neutral_run_evidence(
        checkpoint=checkpoint,
        execution_at_utc=completed_evidence["execution_at_utc"],
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )


def _iter_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def test_exact_canonical_human_review_requirement_split():
    requirements = review.canonical_human_review_requirements()

    assert {key for key, value in requirements.items() if value} == REVIEW_REQUIRED
    assert {key for key, value in requirements.items() if not value} == REVIEW_NOT_REQUIRED
    assert len(requirements) == 12


def test_subjective_rubrics_cover_exactly_the_reviewable_live_workloads():
    for workload_id in REVIEW_REQUIRED:
        first = review.build_subjective_qualification_rubric(workload_id)
        second = review.build_subjective_qualification_rubric(workload_id)

        assert first == second
        assert first["rubric_version"] == review.SUBJECTIVE_REVIEW_RUBRIC_VERSION
        assert first["workload_id"] == workload_id
        assert len(first["criteria"]) == 4
        assert len({row["criterion_id"] for row in first["criteria"]}) == 4
    for workload_id in REVIEW_NOT_REQUIRED:
        with pytest.raises(ValueError, match="rubric is unavailable"):
            review.build_subjective_qualification_rubric(workload_id)
    with pytest.raises(ValueError, match="rubric is unavailable"):
        review.build_subjective_qualification_rubric("unknown_workload")


def test_manual_provider_preview_rubric_covers_bounded_review_semantics():
    rubric = review.build_subjective_qualification_rubric(
        "manual_provider_preview"
    )
    criterion_ids = [row["criterion_id"] for row in rubric["criteria"]]
    rubric_text = " ".join(
        f"{row['criterion_id']} {row['instruction']}"
        for row in rubric["criteria"]
    ).lower()

    assert rubric == review.build_subjective_qualification_rubric(
        "manual_provider_preview"
    )
    assert rubric["rubric_version"] == review.SUBJECTIVE_REVIEW_RUBRIC_VERSION
    assert rubric["workload_id"] == "manual_provider_preview"
    assert criterion_ids == [
        "evidence_grounding",
        "source_fact_preservation",
        "job_relevance",
        "manual_preview_usefulness_and_safety",
    ]
    assert len(criterion_ids) == len(set(criterion_ids)) == 4
    for concern in (
        "ground",
        "source facts and meaning",
        "job",
        "manual review",
        "advisory",
        "no automatic acceptance",
        "mutation",
        "auto-apply",
        "submission authority",
    ):
        assert concern in rubric_text


def test_existing_subjective_rubric_criterion_ids_remain_unchanged():
    observed = {
        workload_id: {
            row["criterion_id"]
            for row in review.build_subjective_qualification_rubric(
                workload_id
            )["criteria"]
        }
        for workload_id in PRIOR_SUBJECTIVE_RUBRIC_CRITERION_IDS
    }

    assert observed == PRIOR_SUBJECTIVE_RUBRIC_CRITERION_IDS


def test_requirement_is_derived_without_caller_boolean():
    signature = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    build_function = next(
        node
        for node in ast.walk(signature)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "build_post_result_human_review_record"
    )
    argument_names = {
        argument.arg
        for argument in build_function.args.args + build_function.args.kwonlyargs
    }

    assert "human_review_required" not in argument_names
    assert review.human_review_required_for_workload("jd_intelligence") is True
    assert review.human_review_required_for_workload("skill_extraction") is False
    with pytest.raises(ValueError, match="unknown benchmark workload"):
        review.human_review_required_for_workload("caller_supplied_workload")


@pytest.mark.parametrize("decision", ["approved", "rejected"])
def test_valid_required_workload_decisions_are_accepted(
    controlled_inputs,
    completed_evidence,
    decision,
):
    record = _record(
        controlled_inputs,
        completed_evidence,
        decision=decision,
    )

    assert _validate(controlled_inputs, completed_evidence, record) is True
    assert record["decision"] == decision
    assert record["human_review_required"] is True


def test_absent_decision_is_pending_and_not_satisfied(
    controlled_inputs,
    completed_evidence,
):
    assessment = _assess(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
    )

    assert assessment["decision"] == "pending"
    assert assessment["review_requirement_satisfied"] is False
    assert assessment["negative_resolution"] is False


def test_nonrequired_workload_needs_no_record_and_rejects_one(
    controlled_inputs,
    completed_evidence,
):
    assessment = _assess(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
    )

    assert assessment["decision"] == "not_required"
    assert assessment["review_requirement_satisfied"] is True
    with pytest.raises(ValueError, match="does not require review"):
        _record(
            controlled_inputs,
            completed_evidence,
            workload_id="skill_extraction",
        )


def test_approved_and_rejected_assessments_have_narrow_semantics(
    controlled_inputs,
    completed_evidence,
):
    approved = _record(controlled_inputs, completed_evidence)
    rejected = _record(
        controlled_inputs,
        completed_evidence,
        decision="rejected",
    )

    approved_assessment = _assess(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
        approved,
    )
    rejected_assessment = _assess(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
        rejected,
    )
    assert approved_assessment["review_requirement_satisfied"] is True
    assert approved_assessment["negative_resolution"] is False
    assert rejected_assessment["review_requirement_satisfied"] is False
    assert rejected_assessment["negative_resolution"] is True


def test_review_binds_to_exact_step9c3_evidence_digest(
    controlled_inputs,
    completed_evidence,
):
    record = _record(controlled_inputs, completed_evidence)
    plan, authorization, pricing, _outputs = controlled_inputs

    assert record["evidence_sha256"] == (
        evidence_runtime.provider_neutral_run_evidence_sha256(
            completed_evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )
    )


def test_altered_evidence_and_hash_mismatch_fail_closed(
    controlled_inputs,
    completed_evidence,
):
    record = _record(controlled_inputs, completed_evidence)
    altered_evidence = deepcopy(completed_evidence)
    altered_evidence["execution_at_utc"] = "2026-07-25T00:00:01.000000Z"
    altered_record = deepcopy(record)
    altered_record["evidence_sha256"] = "0" * 64

    with pytest.raises(ValueError):
        _validate(controlled_inputs, altered_evidence, record)
    with pytest.raises(ValueError, match="binding mismatch"):
        _validate(controlled_inputs, completed_evidence, altered_record)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("provider", "openai"),
        ("model", "gpt-5-mini"),
        ("workload_id", "tailoring_generation"),
        ("schedule_key", "not-a-controlled-schedule-key"),
    ],
)
def test_record_identity_mutations_fail_closed(
    controlled_inputs,
    completed_evidence,
    field,
    replacement,
):
    record = _record(controlled_inputs, completed_evidence)
    record[field] = replacement

    with pytest.raises(ValueError):
        _validate(controlled_inputs, completed_evidence, record)


@pytest.mark.parametrize("value", [None, "", "pending", "accept", "maybe", 1])
def test_malformed_or_unrecorded_decisions_are_rejected(
    controlled_inputs,
    completed_evidence,
    value,
):
    with pytest.raises(ValueError, match="review decision"):
        _record(
            controlled_inputs,
            completed_evidence,
            decision=value,
        )


def test_approval_never_emits_routing_or_production_status(
    controlled_inputs,
    completed_evidence,
):
    record = _record(controlled_inputs, completed_evidence)
    assessment = _assess(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
        record,
    )
    keys = {key.lower() for key in _iter_keys([record, assessment])}

    assert not any("qualified" in key for key in keys)
    assert not any("routing" in key for key in keys)
    assert "selected_model" not in keys
    assert record["decision_scope"] == "post_result_human_review_requirement_only"


def test_hard_failure_cannot_be_approved_but_can_be_rejected_for_audit(
    controlled_inputs,
    failed_review_evidence,
):
    with pytest.raises(ValueError, match="hard failure"):
        _record(controlled_inputs, failed_review_evidence)

    rejected = _record(
        controlled_inputs,
        failed_review_evidence,
        decision="rejected",
    )
    assert _validate(controlled_inputs, failed_review_evidence, rejected) is True


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda row: row.update(schema_valid=False), "valid schema"),
        (
            lambda row: row.update(normalization_succeeded=False),
            "successful normalization",
        ),
        (
            lambda row: row.update(quality_gate_passed=False),
            "quality gate",
        ),
        (
            lambda row: row["hard_failures"].update(hallucination=True),
            "hard failure",
        ),
    ],
)
def test_approval_cannot_override_grading_or_safety_failures(
    controlled_inputs,
    completed_evidence,
    mutation,
    message,
):
    unsafe_evidence = _rebuild_with_summary_mutation(
        controlled_inputs,
        completed_evidence,
        mutation,
    )

    with pytest.raises(ValueError, match=message):
        _record(controlled_inputs, unsafe_evidence)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("hard_failure_present", True, "hard failure"),
        ("schedule_completed", False, "did not complete"),
        ("contract_valid", False, "valid production contract"),
        ("normalization_succeeded", False, "successful normalization"),
        ("quality_gate_passed", False, "quality gate"),
        ("provider_outcome_category", "definitive_failure", "provider outcome"),
        ("provider_call_count", 0, "provider outcome"),
        ("authority_safety_valid", False, "authority invariant"),
    ],
)
def test_approval_safety_guard_rejects_every_unsafe_observation(
    field,
    replacement,
    message,
):
    observation = {
        "evidence_kind": "controlled_live_qualification_evidence",
        "hard_failure_present": False,
        "schedule_completed": True,
        "contract_valid": True,
        "normalization_succeeded": None,
        "quality_gate_passed": True,
        "provider_outcome_category": "success",
        "provider_call_count": 1,
        "authority_safety_valid": True,
    }
    observation[field] = replacement

    with pytest.raises(ValueError, match=message):
        review._require_approval_safe(observation)


def test_reviewer_and_time_are_normalized_once_and_deterministically(
    controlled_inputs,
    completed_evidence,
):
    plan, authorization, pricing, _outputs = controlled_inputs
    summary = _summary(completed_evidence, "jd_intelligence", provider="groq")
    time_calls = []

    def fixed_time():
        time_calls.append(True)
        return FIXED_REVIEW_TIME

    record = review.build_post_result_human_review_record(
        evidence=completed_evidence,
        schedule_key=summary["schedule_key"],
        decision="APPROVED",
        reviewer_id="Reviewer.Main:01",
        review_time_source=fixed_time,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )

    assert time_calls == [True]
    assert record["reviewer_id"] == "reviewer.main:01"
    assert record["reviewed_at_utc"] == "2026-07-26T14:30:00.000000Z"
    assert record["decision"] == "approved"


@pytest.mark.parametrize(
    "reviewer_id",
    [None, "", "contains space", "slash/not-allowed", "x" * 65, 42],
)
def test_reviewer_id_is_required_bounded_and_machine_safe(
    controlled_inputs,
    completed_evidence,
    reviewer_id,
):
    with pytest.raises(ValueError, match="reviewer ID"):
        _record(
            controlled_inputs,
            completed_evidence,
            reviewer_id=reviewer_id,
        )


@pytest.mark.parametrize(
    "timestamp",
    [None, "", "not-a-time", "2026-07-26T14:30:00", "2026-07-26T10:30:00-04:00"],
)
def test_review_timestamp_requires_explicit_utc(
    controlled_inputs,
    completed_evidence,
    timestamp,
):
    with pytest.raises(ValueError, match="review timestamp"):
        _record(
            controlled_inputs,
            completed_evidence,
            review_time=timestamp,
        )


@pytest.mark.parametrize(
    "prohibited_field",
    [
        "raw_provider_output",
        "raw_response",
        "prompt",
        "reasoning",
        "credential",
        "provider_request_id",
        "full_evidence",
    ],
)
def test_raw_sensitive_or_duplicated_evidence_fields_are_rejected(
    controlled_inputs,
    completed_evidence,
    prohibited_field,
):
    record = _record(controlled_inputs, completed_evidence)
    record[prohibited_field] = "must-not-be-retained"

    with pytest.raises(ValueError, match="exact schema"):
        _validate(controlled_inputs, completed_evidence, record)


def test_record_is_bounded_and_does_not_duplicate_evidence(
    controlled_inputs,
    completed_evidence,
):
    record = _record(controlled_inputs, completed_evidence)
    serialized = json.dumps(record, sort_keys=True)

    assert len(record) == 12
    assert len(serialized.encode("utf-8")) < 2048
    assert "checkpoint" not in record
    assert "grading_summaries" not in record
    assert "aggregate_usage" not in record
    assert "normalized_output" not in serialized


def test_serialization_and_digest_are_canonical_and_deterministic(
    controlled_inputs,
    completed_evidence,
):
    plan, authorization, pricing, _outputs = controlled_inputs
    first = _record(controlled_inputs, completed_evidence)
    second = _record(controlled_inputs, completed_evidence)
    first_json = review.serialize_post_result_human_review_record(
        first,
        evidence=completed_evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    second_json = review.serialize_post_result_human_review_record(
        second,
        evidence=completed_evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )

    assert first_json == second_json
    assert json.dumps(json.loads(first_json), sort_keys=True, separators=(",", ":")) == first_json
    assert review.post_result_human_review_sha256(
        first,
        evidence=completed_evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    ) == review.post_result_human_review_sha256(
        second,
        evidence=completed_evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )


def test_decision_reviewer_and_evidence_changes_change_digest(
    controlled_inputs,
    completed_evidence,
):
    plan, authorization, pricing, _outputs = controlled_inputs
    approved = _record(controlled_inputs, completed_evidence)
    rejected = _record(
        controlled_inputs,
        completed_evidence,
        decision="rejected",
    )
    other_reviewer = _record(
        controlled_inputs,
        completed_evidence,
        reviewer_id="reviewer-02",
    )
    changed_evidence = evidence_runtime.build_provider_neutral_run_evidence(
        checkpoint=completed_evidence["checkpoint"],
        execution_at_utc="2026-07-25T00:00:01Z",
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    changed_evidence_record = _record(
        controlled_inputs,
        changed_evidence,
    )

    def digest(record, evidence):
        return review.post_result_human_review_sha256(
            record,
            evidence=evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )

    baseline = digest(approved, completed_evidence)
    assert digest(rejected, completed_evidence) != baseline
    assert digest(other_reviewer, completed_evidence) != baseline
    assert digest(changed_evidence_record, changed_evidence) != baseline


def test_evidence_remains_immutable_through_build_validate_and_assess(
    controlled_inputs,
    completed_evidence,
):
    before = deepcopy(completed_evidence)
    record = _record(controlled_inputs, completed_evidence)
    _validate(controlled_inputs, completed_evidence, record)
    _assess(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
        record,
    )

    assert completed_evidence == before


def test_persistence_is_separate_exclusive_and_mode_0600(
    tmp_path,
    controlled_inputs,
    completed_evidence,
):
    plan, authorization, pricing, _outputs = controlled_inputs
    record = _record(controlled_inputs, completed_evidence)
    evidence_snapshot = json.dumps(completed_evidence, sort_keys=True).encode("utf-8")
    evidence_path = tmp_path / "evidence-input.json"
    evidence_path.write_bytes(evidence_snapshot)
    target = tmp_path / "outputs/provider_benchmark/human-review-test.json"

    written = review.write_post_result_human_review_record_exclusive(
        target,
        record,
        repository_root=tmp_path,
        evidence=completed_evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )

    assert written == target
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert json.loads(target.read_text(encoding="utf-8")) == record
    assert evidence_path.read_bytes() == evidence_snapshot
    with pytest.raises(ValueError, match="overwrite"):
        review.write_post_result_human_review_record_exclusive(
            target,
            record,
            repository_root=tmp_path,
            evidence=completed_evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )


def test_persistence_rejects_outside_namespace_and_symlink_parent(
    tmp_path,
    controlled_inputs,
    completed_evidence,
):
    plan, authorization, pricing, _outputs = controlled_inputs
    record = _record(controlled_inputs, completed_evidence)

    with pytest.raises(ValueError, match="approved benchmark namespace"):
        review.write_post_result_human_review_record_exclusive(
            tmp_path / "human-review-outside.json",
            record,
            repository_root=tmp_path,
            evidence=completed_evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )
    assert not (tmp_path / "outputs").exists()

    root = tmp_path / "symlink-root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "outputs").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="unsafe"):
        review.write_post_result_human_review_record_exclusive(
            root / "outputs/provider_benchmark/human-review-test.json",
            record,
            repository_root=root,
            evidence=completed_evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )


def test_focused_tests_create_no_repository_benchmark_output(
    repository_subjective_review_packet_baseline,
):
    output_root = ROOT / "outputs/provider_benchmark"

    current = tuple(
        sorted(
            path.relative_to(ROOT).as_posix()
            for path in output_root.glob("subjective-review-packet-*.json")
        )
    )
    assert current == repository_subjective_review_packet_baseline


def test_owner_has_no_sdk_network_environment_or_user_state_access():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert not {"groq", "openai", "dotenv", "requests", "httpx"}.intersection(imports)
    assert "user_provider_runtime" not in source
    assert "user_ai_settings" not in source
    assert "operator_decisions" not in source
    assert "DATABASE_URL" not in source
    assert "API_KEY" not in source
    assert "getenv" not in source
    assert not any(
        isinstance(node, ast.Attribute) and node.attr in {"getenv", "environ"}
        for node in ast.walk(tree)
    )
    assert "execute_provider_neutral_evidence_run" not in source
    assert "controlled_groq_canary_transport" not in source
    assert "controlled_openai_canary_transport" not in source


def test_review_construction_never_reaches_network(
    monkeypatch,
    controlled_inputs,
    completed_evidence,
):
    def blocked(*_args, **_kwargs):
        raise AssertionError("network access is prohibited")

    monkeypatch.setattr(socket, "socket", blocked)
    record = _record(controlled_inputs, completed_evidence)

    assert record["decision"] == "approved"


def test_44_cell_plan_and_live_default_off_remain_unchanged(controlled_inputs):
    plan = controlled_inputs[0]
    counts = plan["request_counts"]["maximum_requests_per_model"]

    assert plan["request_counts"]["maximum_total_requests"] == 44
    assert counts == {
        "groq/openai/gpt-oss-20b": 12,
        "groq/openai/gpt-oss-120b": 10,
        "openai/gpt-5-mini": 12,
        "openai/gpt-5.1": 10,
    }
    assert plan["authority_invariants"]["live_execution_authorized"] is False
    assert all(
        not (
            row["workload_id"] == "skill_extraction"
            and row["provider"] == "groq"
            and row["model"] == "openai/gpt-oss-120b"
        )
        for row in plan["staged_matrix"]
    )


def test_no_production_source_imports_human_review_owner():
    consumers = []
    for path in (ROOT / "src").rglob("*.py"):
        if path == OWNER_PATH or "evaluation" in path.relative_to(ROOT / "src").parts:
            continue
        if "controlled_provider_benchmark_human_review" in path.read_text(
            encoding="utf-8"
        ):
            consumers.append(path.relative_to(ROOT).as_posix())

    assert consumers == []
