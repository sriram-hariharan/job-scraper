from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.evaluation import provider_fixture_benchmark as engine
from src.evaluation.provider_benchmark_contract import (
    HARD_FAILURE_ORDER,
    METRIC_ORDER,
    MODEL_ORDER,
    WORKLOAD_ORDER,
    build_provider_benchmark_contract,
)
from src.evaluation.provider_client_compatibility import (
    provider_client_compatibility_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "src/evaluation/provider_fixture_benchmark.py"
CORPUS_PATH = ROOT / "tests/fixtures/provider_benchmark/cases.json"
MANIFEST_PATH = ROOT / "tests/fixtures/provider_benchmark/manifest.json"
STEP8M_BASELINE_SHA256 = (
    "e798f7d10f67c65c5d02f7531b54c3ce1b18ad0a6db5ec98505b4f1847f23ddd"
)


def _corpus():
    return engine.load_fixture_case_corpus()


def _contract():
    return engine.build_provider_fixture_benchmark_contract()


def _packets():
    return engine.build_synthetic_expected_result_packets()


def _packet(workload_id):
    return next(
        packet
        for packet in _packets()
        if packet["workload_id"] == workload_id
    )


def _result():
    return engine.evaluate_offline_fixture_benchmark(_packets())


def test_contract_version_is_exact_and_default_off():
    payload = _contract()

    assert payload["contract_version"] == "provider-fixture-benchmark-v1"
    assert payload["contract_kind"] == "offline_normalized_fixture_grading"
    assert payload["controls"]["offline_only"] is True
    assert all(
        value is False
        for key, value in payload["controls"].items()
        if key != "offline_only"
    )


def test_candidates_are_consumed_exactly_from_step8l():
    step8l = build_provider_benchmark_contract()
    payload = _contract()

    assert [
        (row["provider"], row["model"])
        for row in payload["candidate_definitions"]
    ] == [
        (row["provider"], row["model"])
        for row in step8l["candidate_definitions"]
    ] == list(MODEL_ORDER)


def test_workloads_and_metrics_are_consumed_from_step8l():
    payload = _contract()

    assert payload["workload_order"] == list(WORKLOAD_ORDER)
    assert payload["metric_order"] == list(METRIC_ORDER)
    assert payload["hard_failure_order"] == list(HARD_FAILURE_ORDER)


def test_gemini_is_not_a_candidate_and_is_rejected():
    assert all(
        row["provider"] != "gemini"
        for row in _contract()["candidate_definitions"]
    )
    packet = _packets()[0]
    packet["provider"] = "gemini"
    packet["model"] = "gemini-2.5-flash"

    with pytest.raises(ValueError, match="unsupported provider/model"):
        engine.validate_normalized_candidate_result(packet)


def test_contract_has_no_route_model_selection_or_activation_fields():
    serialized = engine.serialize_provider_fixture_benchmark_contract().lower()

    for forbidden in (
        '"recommended_route"',
        '"selected_model"',
        '"selected_provider"',
        '"selected_winner"',
        '"winning_model"',
        '"production_activation"',
    ):
        assert forbidden not in serialized


def test_case_ids_are_unique_and_all_provenance_sources_exist():
    cases = _corpus()["cases"]

    assert len({case["case_id"] for case in cases}) == len(cases)
    for case in cases:
        provenance = case["provenance"]
        assert provenance["source_identifier"]
        assert (ROOT / provenance["source_path"]).is_file()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda corpus: corpus["cases"][0].update(
                {"provenance": {"source_path": "", "source_identifier": ""}}
            ),
            "source_path is required",
        ),
        (
            lambda corpus: corpus["cases"][0]["provenance"].update(
                {"source_path": "/tmp/case.json"}
            ),
            "machine-specific or runtime paths",
        ),
        (
            lambda corpus: corpus["cases"][0]["provenance"].update(
                {"source_path": "../case.json"}
            ),
            "machine-specific or runtime paths",
        ),
        (
            lambda corpus: corpus["cases"][0].update(
                {"contains_personal_resume_content": True}
            ),
            "personal resume content",
        ),
        (
            lambda corpus: corpus["cases"][0].update(
                {"live_transmission_eligible": True}
            ),
            "live fixture transmission",
        ),
        (
            lambda corpus: corpus["cases"][0].update(
                {"workload_id": "unknown_workload"}
            ),
            "unknown fixture workload",
        ),
        (
            lambda corpus: corpus["cases"][1].update(
                {"case_id": corpus["cases"][0]["case_id"]}
            ),
            "duplicate fixture case ID",
        ),
        (
            lambda corpus: corpus["cases"][0].pop("schema_id"),
            "missing required fields",
        ),
        (
            lambda corpus: corpus["cases"][0].update(
                {"expected_output": {}, "expected_invariant": {}}
            ),
            "expected output or invariant",
        ),
    ],
)
def test_unsafe_or_malformed_fixture_cases_fail_closed(mutation, message):
    corpus = _corpus()
    mutation(corpus)

    with pytest.raises(ValueError, match=message):
        engine.validate_fixture_case_corpus(corpus)


def test_omitted_workload_requires_an_explicit_coverage_gap():
    corpus = _corpus()
    corpus["cases"] = [
        case
        for case in corpus["cases"]
        if case["workload_id"] != "manual_provider_preview"
    ]

    with pytest.raises(ValueError, match="every workload"):
        engine.validate_fixture_case_corpus(corpus)


def test_explicit_coverage_gap_is_valid_and_counted():
    corpus = _corpus()
    case = next(
        row
        for row in corpus["cases"]
        if row["workload_id"] == "manual_provider_preview"
    )
    case["comparison_type"] = "coverage_gap"
    case["expected_output"] = {}
    case["expected_invariant"] = {
        "coverage_gap_reason": "sanitized_case_not_available"
    }

    assert engine.validate_fixture_case_corpus(corpus) is True
    coverage = engine.fixture_case_coverage_summary(corpus)
    assert coverage["coverage_gap_count"] == 1


def test_machine_readable_corpus_has_exact_workload_coverage():
    coverage = engine.fixture_case_coverage_summary()

    assert coverage["workload_count"] == 12
    assert coverage["total_case_count"] == 15
    assert coverage["exact_golden_count"] == 15
    assert coverage["invariant_only_count"] == 0
    assert coverage["schema_only_count"] == 0
    assert coverage["coverage_gap_count"] == 0
    assert coverage["additional_redaction_required_count"] == 0
    assert coverage["live_transmission_eligible_count"] == 0
    assert [row["workload_id"] for row in coverage["workloads"]] == list(
        WORKLOAD_ORDER
    )
    expected_case_counts = {
        workload_id: (
            2
            if workload_id
            in {
                "job_fit_evaluation",
                "grounded_rag_answer",
                "critic_evaluation",
            }
            else 1
        )
        for workload_id in WORKLOAD_ORDER
    }
    assert {
        row["workload_id"]: row["machine_readable_case_count"]
        for row in coverage["workloads"]
    } == expected_case_counts
    assert {
        row["workload_id"]: row["exact_golden_count"]
        for row in coverage["workloads"]
    } == expected_case_counts
    assert all(
        row["live_transmission_eligible_count"] == 0
        for row in coverage["workloads"]
    )


def test_corpus_contains_no_personal_runtime_or_live_authorization():
    corpus = _corpus()
    serialized = json.dumps(corpus, sort_keys=True).lower()

    assert all(
        case["contains_personal_resume_content"] is False
        and case["live_transmission_eligible"] is False
        and case["offline_only"] is True
        for case in corpus["cases"]
    )
    for forbidden in (
        "/users/",
        "database_url",
        "profile_resumes",
        "raw_provider_response",
        "request_id",
        "skill_eval.txt",
        "outputs/",
        "data/",
    ):
        assert forbidden not in serialized


def test_normalized_result_packet_schema_is_explicit():
    schema = _contract()["result_packet_schema"]

    assert set(schema["required_fields"]) == engine._REQUIRED_RESULT_FIELDS
    assert set(schema["optional_execution_fields"]) == {
        "latency_ms",
        "input_token_count",
        "output_token_count",
        "estimated_cost",
    }
    assert schema["fallback_used"] is False
    assert schema["provider_call_count"] == 0
    assert schema["mutation_count"] == 0
    assert schema["application_action_count"] == 0
    assert schema["ats_action_count"] == 0
    assert schema["raw_response_persisted"] is False
    assert schema["live_execution"] is False


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda packet: packet.update(
                {"provider": "openai", "model": "openai/gpt-oss-20b"}
            ),
            "unsupported provider/model",
        ),
        (
            lambda packet: packet.update({"fallback_used": True}),
            "fallback is prohibited",
        ),
        (
            lambda packet: packet.update({"live_execution": True}),
            "live execution is prohibited",
        ),
        (
            lambda packet: packet.update({"provider_call_count": 1}),
            "provider calls are prohibited",
        ),
        (
            lambda packet: packet.update({"raw_response": {"unsafe": True}}),
            "unsupported fields",
        ),
        (
            lambda packet: packet["normalized_output"].update(
                {"raw_provider_response": {"unsafe": True}}
            ),
            "raw response",
        ),
        (
            lambda packet: packet.update({"mutation_count": 1}),
            "mutation is prohibited",
        ),
        (
            lambda packet: packet.update({"application_action_count": 1}),
            "application actions are prohibited",
        ),
        (
            lambda packet: packet.update({"ats_action_count": 1}),
            "ATS actions are prohibited",
        ),
        (
            lambda packet: packet.pop("schema_valid"),
            "missing required fields",
        ),
    ],
)
def test_unsafe_or_malformed_candidate_results_fail_closed(mutation, message):
    packet = _packets()[0]
    mutation(packet)

    with pytest.raises(ValueError, match=message):
        engine.validate_normalized_candidate_result(packet)


def test_duplicate_candidate_result_packets_fail_closed():
    packet = _packets()[0]

    with pytest.raises(ValueError, match="duplicate candidate result"):
        engine.evaluate_offline_fixture_benchmark([packet, deepcopy(packet)])


def test_skill_precision_recall_bucket_and_unsupported_detection_are_exact():
    grade = engine.grade_normalized_candidate_result(
        _packet("skill_extraction")
    )

    assert grade["skill_extraction_precision"] == 1.0
    assert grade["skill_extraction_recall"] == 1.0
    assert grade["workload_metrics"]["bucket_correctness"] == 1.0
    assert grade["workload_metrics"]["unsupported_skill_count"] == 0

    unsafe = _packet("skill_extraction")
    unsafe["normalized_output"]["required_skills"].append("kubernetes")
    unsafe_grade = engine.grade_normalized_candidate_result(unsafe)
    assert unsafe_grade["workload_metrics"]["unsupported_skill_count"] == 1
    assert unsafe_grade["hard_failures"]["unsupported_claim"] == 1


def test_job_fit_metrics_and_score_bounds_are_exact():
    grade = engine.grade_normalized_candidate_result(
        _packet("job_fit_evaluation")
    )

    assert grade["required_field_completeness"] == 1.0
    assert grade["workload_metrics"]["bounded_score_ranges"] == 1.0
    assert grade["workload_metrics"]["classification_agreement"] == 1.0
    assert grade["missing_requirement_accuracy"] == 1.0

    invalid = _packet("job_fit_evaluation")
    invalid["normalized_output"]["fit_score"] = 1.2
    assert (
        engine.grade_normalized_candidate_result(invalid)["workload_metrics"][
            "bounded_score_ranges"
        ]
        == 0.0
    )


def test_jd_signal_and_missing_requirement_agreement_are_deterministic():
    grade = engine.grade_normalized_candidate_result(
        _packet("jd_intelligence")
    )

    metrics = grade["workload_metrics"]
    assert metrics["required_signals_agreement"] == 1.0
    assert metrics["preferred_signals_agreement"] == 1.0
    assert metrics["workflow_context_agreement"] == 1.0
    assert metrics["missing_requirement_accuracy"] == 1.0
    assert metrics["unsupported_signal_count"] == 0


def test_rag_grounding_and_unsupported_claim_detection_are_exact():
    grade = engine.grade_normalized_candidate_result(
        _packet("grounded_rag_answer")
    )

    assert grade["grounded_evidence_precision"] == 1.0
    assert grade["workload_metrics"]["unsupported_citation_count"] == 0
    assert grade["unsupported_claim_count"] == 0

    unsafe = _packet("grounded_rag_answer")
    unsafe["normalized_output"]["claims"].append("kubernetes")
    unsafe_grade = engine.grade_normalized_candidate_result(unsafe)
    assert unsafe_grade["grounded_evidence_precision"] < 1.0
    assert unsafe_grade["hard_failures"]["unsupported_claim"] == 1
    assert unsafe_grade["hard_failures"]["hallucination"] == 1


def test_resume_candidate_and_ranking_agreement_are_deterministic():
    grade = engine.grade_normalized_candidate_result(
        _packet("resume_fallback_ranking")
    )

    assert grade["winner_agreement"] == 1.0
    assert grade["ranking_agreement"] == 1.0
    assert (
        grade["workload_metrics"]["candidate_identity_preservation"] == 1.0
    )
    assert grade["workload_metrics"]["unsupported_candidate_count"] == 0
    assert grade["deterministic_authority_preservation"] == 1.0


def test_adjudication_is_advisory_and_preserves_deterministic_result():
    grade = engine.grade_normalized_candidate_result(
        _packet("ambiguous_resume_adjudication")
    )

    assert grade["winner_agreement"] == 1.0
    assert grade["workload_metrics"]["advisory_decision_agreement"] == 1.0
    assert grade["workload_metrics"]["reason_code_agreement"] == 1.0
    assert (
        grade["workload_metrics"]["deterministic_result_preservation"] == 1.0
    )


def test_critic_agreement_and_safe_suggestion_approval_are_exact():
    grade = engine.grade_normalized_candidate_result(
        _packet("critic_evaluation")
    )

    assert grade["critic_agreement"] == 1.0
    assert grade["workload_metrics"]["reason_code_agreement"] == 1.0
    assert grade["workload_metrics"]["safe_suggestion_approval"] == 1.0
    assert grade["workload_metrics"]["unsupported_claim_rejection"] == 1.0


@pytest.mark.parametrize(
    "workload_id",
    [
        "tailoring_generation",
        "tailoring_refinement",
        "tailoring_judge",
    ],
)
def test_tailoring_graders_are_evidence_bound_and_non_authoritative(
    workload_id,
):
    grade = engine.grade_normalized_candidate_result(_packet(workload_id))

    assert grade["quality_gate_passed"] is True
    assert grade["deterministic_authority_preservation"] == 1.0
    assert grade["unsupported_claim_count"] == 0
    assert grade["workload_metrics"]["task_quality_passed"] is True


def _tailoring_case_and_output():
    case = next(
        row
        for row in _corpus()["cases"]
        if row["workload_id"] == "tailoring_generation"
    )
    return case, deepcopy(case["expected_output"])


def test_tailoring_diagnostics_pass_without_generated_content():
    case, output = _tailoring_case_and_output()
    diagnostics = engine.build_tailoring_generation_diagnostics(case, output)

    assert diagnostics == {
        "suggestion_count": 1,
        "unsupported_claim_count": 0,
        "unsupported_source_id_count": 0,
        "human_review_required_passed": True,
        "authority_preserved": True,
        "tailoring_failure_codes": [],
    }
    assert set(diagnostics) == {
        "suggestion_count",
        "unsupported_claim_count",
        "unsupported_source_id_count",
        "human_review_required_passed",
        "authority_preserved",
        "tailoring_failure_codes",
    }
    serialized = json.dumps(diagnostics, sort_keys=True)
    for suggestion in output["suggestions"]:
        assert suggestion["suggestion_id"] not in serialized
        assert suggestion["source_bullet_id"] not in serialized
        assert all(claim not in serialized for claim in suggestion["claims"])


def test_tailoring_diagnostics_empty_suggestions_is_exact():
    case, output = _tailoring_case_and_output()
    output["suggestions"] = []

    diagnostics = engine.build_tailoring_generation_diagnostics(case, output)

    assert diagnostics["suggestion_count"] == 0
    assert diagnostics["tailoring_failure_codes"] == ["suggestions_empty"]


def test_tailoring_diagnostics_unsupported_claim_is_exact():
    case, output = _tailoring_case_and_output()
    output["suggestions"][0]["claims"].append("unsupported_test_claim")

    diagnostics = engine.build_tailoring_generation_diagnostics(case, output)

    assert diagnostics["unsupported_claim_count"] == 1
    assert diagnostics["tailoring_failure_codes"] == ["unsupported_claim"]


def test_tailoring_diagnostics_unsupported_source_id_is_exact():
    case, output = _tailoring_case_and_output()
    output["suggestions"][0]["source_bullet_id"] = "unsupported_test_source"

    diagnostics = engine.build_tailoring_generation_diagnostics(case, output)

    assert diagnostics["unsupported_source_id_count"] == 1
    assert diagnostics["tailoring_failure_codes"] == [
        "unsupported_source_bullet_id"
    ]


@pytest.mark.parametrize("missing", [False, True])
def test_tailoring_diagnostics_human_review_failure_is_exact(missing):
    case, output = _tailoring_case_and_output()
    if missing:
        output.pop("human_review_required")
    else:
        output["human_review_required"] = False

    diagnostics = engine.build_tailoring_generation_diagnostics(case, output)

    assert diagnostics["human_review_required_passed"] is False
    assert diagnostics["tailoring_failure_codes"] == [
        "human_review_required_false"
    ]


def test_tailoring_diagnostics_authority_failure_is_exact():
    case, output = _tailoring_case_and_output()
    output["authority_mutated"] = True

    diagnostics = engine.build_tailoring_generation_diagnostics(case, output)

    assert diagnostics["authority_preserved"] is False
    assert diagnostics["tailoring_failure_codes"] == [
        "deterministic_authority_not_preserved"
    ]


def test_tailoring_diagnostics_multiple_failures_are_sorted_and_defensive():
    case, output = _tailoring_case_and_output()
    case_before = deepcopy(case)
    output["suggestions"][0]["claims"].append("unsupported_test_claim")
    output["suggestions"][0]["source_bullet_id"] = "unsupported_test_source"
    output["human_review_required"] = False
    output["authority_mutated"] = True
    output_before = deepcopy(output)

    diagnostics = engine.build_tailoring_generation_diagnostics(case, output)

    assert diagnostics["tailoring_failure_codes"] == sorted(
        {
            "unsupported_claim",
            "unsupported_source_bullet_id",
            "human_review_required_false",
            "deterministic_authority_not_preserved",
        }
    )
    assert diagnostics["tailoring_failure_codes"] == sorted(
        set(diagnostics["tailoring_failure_codes"])
    )
    assert case == case_before
    assert output == output_before


def test_tailoring_diagnostic_refactor_preserves_grade_and_semantic_digests():
    packet = _packet("tailoring_generation")
    grade = engine.grade_normalized_candidate_result(packet)

    assert grade["workload_metrics"] == {
        "tailoring_evidence_support": 1.0,
        "unsupported_claim_count": 0,
        "invented_content_count": 0,
        "source_bullet_identity_preservation": 1.0,
        "human_review_requirement": 1.0,
        "task_quality_passed": True,
    }
    assert grade["quality_gate_passed"] is True
    assert engine.fixture_case_corpus_sha256() == (
        "0ddc82e62745856c0d5d4d3f0efbe3fc86bd4e84e5da070f54f4ea635e74b05c"
    )
    assert engine.provider_fixture_benchmark_sha256() == (
        "7a6463fc465d963633f82a18de0b067daab31dc387680b1d004e706c61a55c15"
    )


def test_unsupported_tailoring_claim_is_a_hard_failure():
    packet = _packet("tailoring_generation")
    packet["normalized_output"]["suggestions"][0]["claims"].append(
        "kubernetes"
    )
    grade = engine.grade_normalized_candidate_result(packet)

    assert grade["hard_failures"]["unsupported_claim"] == 1
    assert grade["hard_failures"]["hallucination"] == 1
    assert grade["quality_gate_passed"] is False


@pytest.mark.parametrize(
    "workload_id",
    ["manual_scan_phrase", "manual_provider_preview"],
)
def test_manual_workloads_remain_manual_only_and_non_authoritative(
    workload_id,
):
    grade = engine.grade_normalized_candidate_result(_packet(workload_id))

    assert grade["quality_gate_passed"] is True
    assert grade["deterministic_authority_preservation"] == 1.0
    assert grade["workload_metrics"]["task_quality_passed"] is True


def test_schema_normalization_and_contract_metrics_are_exact():
    result = _result()
    metrics = result["metrics"]

    assert list(metrics) == list(METRIC_ORDER)
    assert metrics["schema_valid_response_rate"] == 1.0
    assert metrics["normalization_success_rate"] == 1.0
    assert metrics["grounded_evidence_precision"] == 1.0
    assert metrics["unsupported_claim_count"] == 0
    assert metrics["hallucination_count"] == 0
    assert metrics["required_field_completeness"] == 1.0
    assert metrics["deterministic_authority_preservation"] == 1.0
    assert metrics["persisted_raw_response_count"] == 0
    assert metrics["mutation_count"] == 0
    assert metrics["application_action_count"] == 0
    assert metrics["ats_action_count"] == 0


def test_hard_failures_are_exact_for_safe_synthetic_outputs():
    result = _result()

    assert list(result["hard_failures"]) == list(HARD_FAILURE_ORDER)
    assert result["hard_failures"] == {
        failure_id: 0 for failure_id in HARD_FAILURE_ORDER
    }
    assert result["hard_failures_all_zero"] is True


def test_schema_invalid_output_is_not_accepted_as_quality_passing():
    packet = _packet("skill_extraction")
    packet["schema_valid"] = False
    grade = engine.grade_normalized_candidate_result(packet)

    assert grade["hard_failures"]["schema_invalid_result_accepted"] == 1
    assert grade["quality_gate_passed"] is False


def test_deterministic_authority_mutation_is_a_hard_failure():
    packet = _packet("resume_fallback_ranking")
    packet["normalized_output"]["authority_mutated"] = True
    grade = engine.grade_normalized_candidate_result(packet)

    assert grade["hard_failures"]["deterministic_authority_mutation"] == 1
    assert grade["hard_failures"]["ranking_mutation"] == 1
    assert grade["hard_failures"]["selected_resume_mutation"] == 1


def test_unobserved_live_metrics_are_not_fabricated_as_zero():
    metrics = _result()["metrics"]

    assert metrics["provider_call_success_rate"] == "not_observed_offline"
    for metric_id in (
        "latency_ms",
        "input_token_count",
        "output_token_count",
        "estimated_cost",
        "timeout_count",
        "retry_count",
        "rate_limit_count",
        "cache_hit_count",
    ):
        assert metrics[metric_id] == "not_observed_offline"
    assert metrics["fallback_activation_count"] == 0
    assert (
        metrics["fallback_correctness"]
        == "not_applicable_fallback_disabled"
    )
    assert metrics["duplicate_call_count"] == 0


def test_quality_gate_precedes_cost_and_latency_comparison():
    result = _result()
    policy = _contract()["quality_before_cost_policy"]

    assert policy["quality_evaluated_first"] is True
    assert policy["observed_cost_required_for_cost_comparison"] is True
    assert policy["observed_latency_required_for_latency_comparison"] is True
    assert result["quality_gate_passed"] is True
    assert result["cost_comparison_eligible"] is False
    assert result["latency_comparison_eligible"] is False
    assert result["live_evidence_required"] is True


def test_observed_metadata_never_bypasses_a_failed_quality_gate():
    packet = _packet("skill_extraction")
    packet.update(
        {
            "latency_ms": 10,
            "input_token_count": 20,
            "output_token_count": 10,
            "estimated_cost": 0.01,
        }
    )
    packet["normalized_output"]["required_skills"].append("kubernetes")
    grade = engine.grade_normalized_candidate_result(packet)

    assert grade["quality_gate_passed"] is False
    assert grade["cost_comparison_eligible"] is False
    assert grade["latency_comparison_eligible"] is False


def test_no_model_route_or_recommendation_is_selected_in_result():
    serialized = engine.serialize_offline_fixture_benchmark_result(
        _result()
    ).lower()

    for forbidden in (
        '"recommended_route"',
        '"selected_model"',
        '"selected_provider"',
        '"selected_winner"',
        '"winning_model"',
    ):
        assert forbidden not in serialized


def test_serialization_and_digests_are_deterministic():
    corpus = _corpus()
    contract = _contract()
    result = _result()

    assert engine.serialize_fixture_case_corpus(corpus) == (
        engine.serialize_fixture_case_corpus(deepcopy(corpus))
    )
    assert engine.fixture_case_corpus_sha256(corpus) == (
        engine.fixture_case_corpus_sha256(deepcopy(corpus))
    )
    assert engine.serialize_provider_fixture_benchmark_contract(contract) == (
        engine.serialize_provider_fixture_benchmark_contract(
            deepcopy(contract)
        )
    )
    assert engine.provider_fixture_benchmark_sha256(contract) == (
        engine.provider_fixture_benchmark_sha256(deepcopy(contract))
    )
    assert engine.serialize_offline_fixture_benchmark_result(result) == (
        engine.serialize_offline_fixture_benchmark_result(deepcopy(result))
    )
    assert engine.offline_fixture_benchmark_result_sha256(result) == (
        engine.offline_fixture_benchmark_result_sha256(deepcopy(result))
    )


def test_digests_are_stable_in_a_fresh_process():
    local = (
        engine.fixture_case_corpus_sha256(),
        engine.provider_fixture_benchmark_sha256(),
    )
    code = (
        "from src.evaluation.provider_fixture_benchmark import "
        "fixture_case_corpus_sha256,provider_fixture_benchmark_sha256;"
        "print(fixture_case_corpus_sha256());"
        "print(provider_fixture_benchmark_sha256())"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env={},
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stderr == ""
    assert tuple(completed.stdout.strip().splitlines()) == local


def test_returned_structures_are_defensive_copies():
    first_corpus = _corpus()
    first_contract = _contract()
    first_result = _result()
    corpus_digest = engine.fixture_case_corpus_sha256()
    contract_digest = engine.provider_fixture_benchmark_sha256()

    first_corpus["cases"][0]["case_id"] = "mutated"
    first_contract["candidate_definitions"][0]["provider"] = "mutated"
    first_result["case_grades"][0]["workload_id"] = "mutated"

    assert _corpus()["cases"][0]["case_id"] != "mutated"
    assert _contract()["candidate_definitions"][0]["provider"] == "groq"
    assert _result()["case_grades"][0]["workload_id"] != "mutated"
    assert engine.fixture_case_corpus_sha256() == corpus_digest
    assert engine.provider_fixture_benchmark_sha256() == contract_digest


def test_engine_import_and_grading_import_no_provider_modules():
    code = (
        "import json,sys;"
        "from src.evaluation import provider_fixture_benchmark as e;"
        "e.evaluate_offline_fixture_benchmark("
        "e.build_synthetic_expected_result_packets());"
        "print(json.dumps({name:(name in sys.modules) for name in "
        "['groq','openai','google.genai','src.ai.llm_client']},sort_keys=True))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env={},
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == {
        "google.genai": False,
        "groq": False,
        "openai": False,
        "src.ai.llm_client": False,
    }
    assert completed.stderr == ""


def test_engine_has_no_dotenv_credential_network_database_or_runtime_imports():
    tree = ast.parse(ENGINE_PATH.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")

    assert imports == {
        "__future__",
        "copy",
        "hashlib",
        "json",
        "pathlib",
        "typing",
        "src.evaluation.provider_benchmark_contract",
    }
    assert not imports.intersection(
        {
            "os",
            "dotenv",
            "groq",
            "openai",
            "google",
            "requests",
            "urllib",
            "socket",
            "subprocess",
            "threading",
            "psycopg",
            "src.ai.llm_client",
            "src.pipeline",
            "src.graph",
        }
    )


def test_engine_exposes_no_write_execution_subprocess_or_thread_surface():
    tree = ast.parse(ENGINE_PATH.read_text(encoding="utf-8"))
    call_names = set()
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        try:
            call_names.add(ast.unparse(node.func))
        except Exception:
            pass

    assert not any(
        name.endswith(
            (
                ".write_text",
                ".write_bytes",
                ".mkdir",
                ".touch",
                ".open",
                ".connect",
                ".submit",
                ".send",
                ".start",
                ".run",
                ".Popen",
            )
        )
        for name in call_names
    )
    assert not {
        "call_provider",
        "execute_benchmark",
        "run_live_benchmark",
        "write_artifact",
        "submit_application",
        "mutate_queue",
    }.intersection(function_names)


def test_loading_grading_and_hashing_write_no_files(monkeypatch):
    original_open = Path.open

    def guarded_open(path, mode="r", *args, **kwargs):
        if any(token in str(mode) for token in ("w", "a", "x", "+")):
            raise AssertionError("filesystem write attempted")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    result = _result()
    engine.offline_fixture_benchmark_result_sha256(result)
    assert result["authority_invariants"]["provider_call_count"] == 0


def test_repository_owned_inputs_remain_unchanged_during_evaluation():
    paths = (CORPUS_PATH, MANIFEST_PATH)
    before = {path: path.read_bytes() for path in paths}

    _contract()
    _result()
    engine.fixture_case_corpus_sha256()
    engine.provider_fixture_benchmark_sha256()

    assert {path: path.read_bytes() for path in paths} == before


def test_authority_mutation_application_and_ats_counts_remain_zero():
    result = _result()
    authority = result["authority_invariants"]

    assert authority == {
        "deterministic_authority_preserved": True,
        "provider_call_count": 0,
        "fallback_activation_count": 0,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "raw_response_persisted_count": 0,
        "live_execution": False,
    }


def test_step8m_compatibility_digest_remains_stable():
    assert provider_client_compatibility_sha256() == STEP8M_BASELINE_SHA256


def test_recovery_006_status_remains_absent():
    status_path = (
        ROOT
        / "outputs/application_planning"
        / "phase11_controlled_priority_graph_verification_006_status.json"
    )

    assert not status_path.exists()
