from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from src.evaluation import controlled_provider_benchmark_plan as plan_owner
from src.evaluation import provider_fixture_benchmark as fixture_owner
from src.evaluation.provider_benchmark_contract import WORKLOAD_ORDER


ROOT = Path(__file__).resolve().parents[1]
RECOVERY_006_STATUS = (
    ROOT
    / "outputs/application_planning"
    / "phase11_controlled_priority_graph_verification_006_status.json"
)
BLOCKED_CASES = {
    "job_fit_evaluation": (
        "job_fit_bounded_scores_v1",
        "classification_not_wholly_synthetic",
    ),
    "grounded_rag_answer": (
        "grounded_rag_supported_sources_v1",
        "classification_not_wholly_synthetic",
    ),
    "critic_evaluation": (
        "critic_supported_claim_v1",
        "contains_local_only_expected_or_grader_material",
    ),
}
NEW_CASES = {
    "job_fit_evaluation": "job_fit_synthetic_transmission_safe_v1",
    "grounded_rag_answer": (
        "grounded_rag_synthetic_transmission_safe_v1"
    ),
    "critic_evaluation": "critic_synthetic_transmission_safe_v1",
}
ORIGINAL_CASE_SHA256 = {
    "job_fit_bounded_scores_v1": (
        "d3a1ff81a8336ce602ecacb0bac35b7d85d174f58ea27fd18d5f2f86f769b142"
    ),
    "grounded_rag_supported_sources_v1": (
        "e6913dd316df3e54d946bfad292e929863d7ebb66992d4a2158b158a977f19cd"
    ),
    "critic_supported_claim_v1": (
        "2de3e31ad88e90fa9a75a49940058fa48e09958efb4765bb670f1a829cb10fd8"
    ),
}
REVIEW_SENSITIVE_FIELDS = (
    "contains_personal_data",
    "contains_runtime_derived_data",
    "contains_employer_or_company_identity",
    "contains_person_name",
    "contains_resume_derived_text",
    "contains_private_job_description_text",
    "contains_credentials_or_secrets",
    "contains_internal_paths",
    "contains_request_identifiers",
    "contains_database_information",
    "contains_proprietary_application_state",
    "contains_unsupported_free_form_text",
)


def _corpus():
    return fixture_owner.load_fixture_case_corpus()


def _plan():
    return plan_owner.build_controlled_provider_benchmark_plan()


def _case(case_id):
    return next(row for row in _corpus()["cases"] if row["case_id"] == case_id)


def _review_by_case_id():
    corpus = _corpus()
    reviews = plan_owner.build_transmission_review(corpus)
    aliases = {
        review["case_alias"]: case["case_id"]
        for case, review in zip(corpus["cases"], reviews)
    }
    return {aliases[row["case_alias"]]: row for row in reviews}


def _canonical_case_sha256(case):
    return hashlib.sha256(
        json.dumps(
            case,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


@pytest.mark.parametrize(
    ("workload_id", "case_id", "reason"),
    [
        (workload_id, case_id, reason)
        for workload_id, (case_id, reason) in BLOCKED_CASES.items()
    ],
)
def test_blocked_workload_mapping_and_reason_are_exact(
    workload_id, case_id, reason
):
    review = _review_by_case_id()[case_id]

    assert _case(case_id)["workload_id"] == workload_id
    assert review["eligible_for_later_controlled_transmission"] is False
    assert review["eligibility_reasons"] == [reason]


@pytest.mark.parametrize(
    ("case_id", "expected_sha256"),
    list(ORIGINAL_CASE_SHA256.items()),
)
def test_original_offline_cases_remain_exactly_preserved(
    case_id, expected_sha256
):
    case = _case(case_id)

    assert _canonical_case_sha256(case) == expected_sha256
    assert case["comparison_type"] == "exact_golden"
    assert case["offline_only"] is True


@pytest.mark.parametrize(
    ("workload_id", "case_id"),
    list(NEW_CASES.items()),
)
def test_new_wholly_synthetic_case_is_present_and_eligible(
    workload_id, case_id
):
    case = _case(case_id)
    review = _review_by_case_id()[case_id]

    assert case["workload_id"] == workload_id
    assert case["sanitized_classification"] == "synthetic_sanitized"
    assert case["additional_redaction_required"] is False
    assert case["contains_personal_resume_content"] is False
    assert case["live_transmission_eligible"] is False
    assert case["offline_only"] is True
    assert review["wholly_synthetic"] is True
    assert review["eligible_for_later_controlled_transmission"] is True
    assert review["requires_additional_redaction"] is False
    assert review["human_approval_required"] is True


@pytest.mark.parametrize(
    ("case_id", "review_field"),
    [
        (case_id, review_field)
        for case_id in NEW_CASES.values()
        for review_field in REVIEW_SENSITIVE_FIELDS
    ],
)
def test_new_case_actual_field_review_has_no_sensitive_classification(
    case_id, review_field
):
    assert _review_by_case_id()[case_id][review_field] is False


@pytest.mark.parametrize("case_id", list(NEW_CASES.values()))
def test_new_case_goldens_and_provenance_remain_local_only(case_id):
    case = _case(case_id)
    review = _review_by_case_id()[case_id]
    plan = _plan()
    matrix_row = next(
        row
        for row in plan["staged_matrix"]
        if row["case_alias"] == review["case_alias"]
    )
    packet = plan_owner.build_transmittable_request_packet(
        case_alias=matrix_row["case_alias"],
        provider=matrix_row["provider"],
        model=matrix_row["model"],
        plan=plan,
    )
    serialized = json.dumps(packet, sort_keys=True).lower()

    assert case["expected_output"]
    assert case["provenance"]
    assert "expected_output" not in serialized
    assert "expected_invariant" not in serialized
    assert "golden" not in serialized
    assert "provenance" not in serialized
    assert "threshold" not in serialized


def test_job_fit_case_reuses_exact_schema_and_bounded_score_contract():
    original = _case(BLOCKED_CASES["job_fit_evaluation"][0])
    synthetic = _case(NEW_CASES["job_fit_evaluation"])

    assert synthetic["schema_id"] == original["schema_id"]
    assert synthetic["required_fields"] == original["required_fields"]
    assert synthetic["expected_invariant"]["score_min"] == 0.0
    assert synthetic["expected_invariant"]["score_max"] == 1.0
    assert synthetic["expected_invariant"][
        "evidence_grounded_reason_required"
    ] is True
    assert synthetic["expected_invariant"]["unsupported_claim_count"] == 0


def test_grounded_rag_case_reuses_schema_and_grounding_contract():
    original = _case(BLOCKED_CASES["grounded_rag_answer"][0])
    synthetic = _case(NEW_CASES["grounded_rag_answer"])

    assert synthetic["schema_id"] == original["schema_id"]
    assert synthetic["required_fields"] == original["required_fields"]
    assert synthetic["supported_evidence_ids"]
    assert synthetic["expected_invariant"]["unsupported_claim_count"] == 0
    assert synthetic["expected_invariant"]["unsupported_source_count"] == 0
    assert synthetic["expected_invariant"]["insufficient_evidence_status"]


def test_critic_case_reuses_schema_and_advisory_authority_contract():
    original = _case(BLOCKED_CASES["critic_evaluation"][0])
    synthetic = _case(NEW_CASES["critic_evaluation"])
    invariant = synthetic["expected_invariant"]

    assert synthetic["schema_id"] == original["schema_id"]
    assert synthetic["required_fields"] == original["required_fields"]
    assert "expected_decision" not in synthetic["normalized_input_packet"]
    assert "expected_reason_code" not in synthetic["normalized_input_packet"]
    assert invariant["advisory_only"] is True
    assert invariant["human_review_required"] is True
    assert invariant["mutation_authorized"] is False
    assert invariant["application_authorized"] is False
    assert invariant["ats_authorized"] is False


def test_complete_corpus_has_fifteen_exact_goldens_and_no_gap():
    coverage = fixture_owner.fixture_case_coverage_summary()

    assert coverage["total_case_count"] == 15
    assert coverage["exact_golden_count"] == 15
    assert coverage["invariant_only_count"] == 0
    assert coverage["coverage_gap_count"] == 0
    assert coverage["additional_redaction_required_count"] == 0
    assert coverage["live_transmission_eligible_count"] == 0


def test_every_workload_has_exactly_one_transmission_eligible_case():
    reviews = plan_owner.build_transmission_review()
    per_workload = {
        workload_id: sum(
            row["workload_id"] == workload_id
            and row["eligible_for_later_controlled_transmission"]
            for row in reviews
        )
        for workload_id in WORKLOAD_ORDER
    }

    assert per_workload == {workload_id: 1 for workload_id in WORKLOAD_ORDER}


def test_transmission_review_counts_are_complete():
    summary = _plan()["transmission_review_summary"]

    assert summary == {
        "reviewed_case_count": 15,
        "eligible_case_count": 12,
        "ineligible_case_count": 3,
    }


def test_all_new_exact_goldens_pass_existing_deterministic_graders():
    corpus = _corpus()
    packets = fixture_owner.build_synthetic_expected_result_packets(
        corpus=corpus
    )
    new_ids = set(NEW_CASES.values())

    for packet in packets:
        if packet["case_id"] not in new_ids:
            continue
        grade = fixture_owner.grade_normalized_candidate_result(
            packet, corpus=corpus
        )
        assert grade["quality_gate_passed"] is True
        assert all(value == 0 for value in grade["hard_failures"].values())


def test_complete_offline_fixture_benchmark_remains_green():
    corpus = _corpus()
    packets = fixture_owner.build_synthetic_expected_result_packets(
        corpus=corpus
    )
    result = fixture_owner.evaluate_offline_fixture_benchmark(
        packets,
        corpus=corpus,
    )

    assert result["candidate_result_count"] == 15
    assert result["quality_gate_passed"] is True
    assert result["hard_failures_all_zero"] is True
    assert result["coverage_sufficient"] is True
    assert result["authority_invariants"] == {
        "deterministic_authority_preserved": True,
        "provider_call_count": 0,
        "fallback_activation_count": 0,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "raw_response_persisted_count": 0,
        "live_execution": False,
    }


def test_rebuilt_matrix_counts_are_exact_and_bounded():
    counts = _plan()["request_counts"]

    assert counts["by_provider"] == {"groq": 22, "openai": 6}
    assert counts["by_model"] == {
        "groq/openai/gpt-oss-20b": 12,
        "groq/openai/gpt-oss-120b": 10,
        "openai/gpt-5-mini": 6,
        "openai/gpt-5.1": 0,
    }
    assert counts["maximum_total_requests"] == 28
    assert counts["maximum_requests_per_case"] == 3


def test_rebuilt_matrix_workload_counts_are_exact():
    assert _plan()["request_counts"]["by_workload"] == {
        "skill_extraction": 2,
        "job_fit_evaluation": 2,
        "jd_intelligence": 2,
        "grounded_rag_answer": 3,
        "resume_fallback_ranking": 3,
        "ambiguous_resume_adjudication": 3,
        "critic_evaluation": 3,
        "tailoring_generation": 2,
        "tailoring_refinement": 2,
        "tailoring_judge": 2,
        "manual_scan_phrase": 2,
        "manual_provider_preview": 2,
    }


def test_rebuilt_matrix_preserves_serial_no_fallback_no_retry_policy():
    plan = _plan()

    assert [row["execution_order"] for row in plan["staged_matrix"]] == list(
        range(1, 29)
    )
    assert all(row["fallback"] is False for row in plan["staged_matrix"])
    assert all(
        row["harness_retry_limit"] == 0
        for row in plan["staged_matrix"]
    )
    assert plan["execution_policy"]["serial_ordering_required"] is True
    assert plan["execution_policy"]["parallel_execution_allowed"] is False
    assert plan["retry_policy"]["harness_retry_limit"] == 0
    assert plan["timeout_policy"]["timeout_seconds"] == 30


def test_gpt_5_1_remains_conditional_and_unscheduled():
    plan = _plan()

    assert plan["request_counts"]["by_model"]["openai/gpt-5.1"] == 0
    assert plan["conditional_future_comparisons"][
        "gpt_5_1_automatic_assignment"
    ] is False
    assert plan["conditional_future_comparisons"][
        "gpt_5_1_requires_revised_plan_and_authorization"
    ] is True


def test_aggregate_token_budgets_recalculate_from_request_count():
    budget = _plan()["token_budget_schema"]

    assert budget["maximum_input_tokens_per_request"] == 4096
    assert budget["maximum_output_tokens_per_request"] == 1024
    assert budget["maximum_total_observed_input_tokens"] == 28 * 4096
    assert budget["maximum_total_observed_output_tokens"] == 28 * 1024
    assert budget["missing_usage_blocks_cost_comparison"] is True


def test_authorization_redaction_retention_and_quality_contracts_remain_safe():
    plan = _plan()

    assert plan["authorization_schema"]["operator_created_only"] is True
    assert plan["authorization_schema"]["automatic_creation_allowed"] is False
    assert plan["cost_ceiling_schema"]["positive_dollar_ceiling_required"] is True
    assert plan["result_packet_schema"][
        "raw_response_persistence_allowed"
    ] is False
    assert plan["artifact_retention_policy"]["automatic_persistence"] is False
    assert plan["artifact_retention_policy"]["required_file_mode"] == "0600"
    assert plan["artifact_retention_policy"]["maximum_retention_days"] == 7
    assert plan["model_selection_evidence_requirements"][
        "quality_precedes_cost"
    ] is True
    assert plan["model_selection_evidence_requirements"][
        "selection_execution_allowed"
    ] is False


def test_corpus_plan_and_engine_digests_are_stable_and_deep_copy_contained():
    corpus = _corpus()
    plan = _plan()

    assert fixture_owner.fixture_case_corpus_sha256(corpus) == (
        fixture_owner.fixture_case_corpus_sha256(deepcopy(corpus))
    )
    assert fixture_owner.provider_fixture_benchmark_sha256() == (
        fixture_owner.provider_fixture_benchmark_sha256()
    )
    assert plan_owner.controlled_provider_benchmark_plan_sha256(plan) == (
        plan_owner.controlled_provider_benchmark_plan_sha256(deepcopy(plan))
    )
    corpus["cases"][-1]["case_id"] = "mutated"
    assert _corpus()["cases"][-1]["case_id"] != "mutated"


def test_controlled_plan_engine_digest_is_bound_to_the_supplied_corpus():
    corpus = _corpus()
    corpus["cases"] = corpus["cases"][:-1]
    plan = plan_owner.build_controlled_provider_benchmark_plan(corpus=corpus)

    assert plan["step8o_case_corpus_sha256"] == (
        fixture_owner.fixture_case_corpus_sha256(corpus)
    )
    assert plan["step8o_engine_sha256"] == (
        fixture_owner.provider_fixture_benchmark_sha256(
            fixture_owner.build_provider_fixture_benchmark_contract(corpus)
        )
    )


def test_no_winner_route_or_execution_authority_is_added():
    plan = _plan()
    serialized = plan_owner.serialize_controlled_provider_benchmark_plan(
        plan
    ).lower()

    for key in (
        '"recommended_route"',
        '"selected_model"',
        '"selected_provider"',
        '"selected_winner"',
        '"winning_model"',
    ):
        assert key not in serialized
    assert plan["authority_invariants"] == {
        "live_execution_authorized": False,
        "provider_calls_allowed": False,
        "fallback_allowed": False,
        "production_activation_allowed": False,
        "routing_change_allowed": False,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "recovery_006_authorized": False,
    }


def test_recovery_006_remains_absent_and_unauthorized():
    assert not RECOVERY_006_STATUS.exists()
    assert _plan()["authority_invariants"]["recovery_006_authorized"] is False
