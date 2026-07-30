from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.evaluation import controlled_provider_benchmark_plan as owner
from src.evaluation import provider_fixture_benchmark as step8o
from src.evaluation.provider_benchmark_contract import (
    MODEL_ORDER,
    WORKLOAD_ORDER,
    build_provider_benchmark_contract,
    provider_benchmark_contract_sha256,
)
from src.evaluation.provider_client_compatibility import (
    provider_client_compatibility_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / "src/evaluation/controlled_provider_benchmark_plan.py"
RUN_PLAN_PATH = ROOT / "tests/fixtures/provider_benchmark/run_plan.json"
RECOVERY_006_STATUS = (
    ROOT
    / "outputs/application_planning"
    / "phase11_controlled_priority_graph_verification_006_status.json"
)
STEP8M_BASELINE_SHA256 = (
    "e798f7d10f67c65c5d02f7531b54c3ce1b18ad0a6db5ec98505b4f1847f23ddd"
)


def _plan():
    return owner.build_controlled_provider_benchmark_plan()


def _eligible_reviews(plan=None):
    payload = _plan() if plan is None else plan
    return [
        row
        for row in payload["transmission_review"]
        if row["eligible_for_later_controlled_transmission"]
    ]


def _first_matrix_row(plan=None):
    payload = _plan() if plan is None else plan
    return payload["staged_matrix"][0]


def _request_packet(plan=None):
    payload = _plan() if plan is None else plan
    row = _first_matrix_row(payload)
    return owner.build_transmittable_request_packet(
        case_alias=row["case_alias"],
        provider=row["provider"],
        model=row["model"],
        plan=payload,
    )


def _result_packet():
    row = _first_matrix_row()
    return {
        "case_alias": row["case_alias"],
        "workload_id": row["workload_id"],
        "provider": row["provider"],
        "model": row["model"],
        "normalized_output": {},
        "schema_valid": True,
        "normalization_succeeded": True,
        "latency_ms": 1,
        "input_token_count": 1,
        "output_token_count": 1,
        "observed_cost": 0.01,
        "provider_outcome_category": "success",
        "fallback_used": False,
        "retry_count": 0,
        "redaction_status": "redacted_normalized_only",
        "hard_failure_status": "none",
    }


def _authorization(plan=None):
    payload = _plan() if plan is None else plan
    return {
        "authorization_version": owner.AUTHORIZATION_VERSION,
        "benchmark_plan_sha256": (
            owner.controlled_provider_benchmark_plan_sha256(payload)
        ),
        "case_corpus_sha256": payload["step8o_case_corpus_sha256"],
        "approved_candidate_pairs": deepcopy(
            payload["candidate_definitions"]
        ),
        "approved_case_aliases": sorted(
            row["case_alias"] for row in _eligible_reviews(payload)
        ),
        "maximum_request_count": payload["request_counts"][
            "maximum_total_requests"
        ],
        "token_budgets": deepcopy(payload["token_budget_schema"]),
        "pricing_table_version": "offline-test-pricing-v1",
        "maximum_observed_cost_per_model": {
            key: 1.0
            for key in payload["request_counts"][
                "maximum_requests_per_model"
            ]
        },
        "maximum_total_observed_cost": 4.0,
        "valid_from_utc": "2026-01-01T00:00:00Z",
        "expires_at_utc": "2026-12-31T23:59:59Z",
        "fallback": False,
        "gemini_allowed": False,
        "production_activation_allowed": False,
        "operator_approved": True,
    }


def _review_with_input_field(field, value, monkeypatch=None):
    corpus = step8o.load_fixture_case_corpus()
    corpus["cases"][0]["normalized_input_packet"][field] = value
    if monkeypatch is not None:
        monkeypatch.setattr(
            owner,
            "fixture_case_corpus_sha256",
            lambda _corpus: "0" * 64,
        )
    return owner.build_transmission_review(corpus)[0]


def test_plan_version_is_exact_and_default_off():
    plan = _plan()

    assert plan["plan_version"] == "controlled-provider-benchmark-plan-v1"
    assert plan["authority_invariants"]["live_execution_authorized"] is False
    assert plan["authority_invariants"]["provider_calls_allowed"] is False


def test_candidates_are_consumed_exactly_from_step8l():
    plan = _plan()
    step8l = build_provider_benchmark_contract()

    assert plan["candidate_definitions"] == [
        {"provider": row["provider"], "model": row["model"]}
        for row in step8l["candidate_definitions"]
    ]


def test_workloads_are_consumed_exactly_from_step8l():
    assert _plan()["workload_order"] == list(WORKLOAD_ORDER)


def test_cases_are_consumed_exactly_from_step8o():
    plan = _plan()
    corpus = step8o.load_fixture_case_corpus()

    assert plan["case_count"] == len(corpus["cases"]) == 15
    assert (
        plan["step8o_case_corpus_sha256"]
        == step8o.fixture_case_corpus_sha256(corpus)
    )


def test_gemini_is_not_a_candidate():
    assert all(
        row["provider"] != "gemini"
        for row in _plan()["candidate_definitions"]
    )


def test_gemini_request_is_rejected():
    packet = _request_packet()
    packet["provider"] = "gemini"
    packet["model"] = "gemini-2.5-flash"

    with pytest.raises(ValueError, match="unsupported|Gemini"):
        owner.validate_transmittable_request_packet(packet)


def test_fallback_is_false_everywhere():
    plan = _plan()

    assert plan["fallback_policy"]["fallback"] is False
    assert all(row["fallback"] is False for row in plan["staged_matrix"])
    assert _request_packet()["fallback"] is False


def test_no_winner_route_or_activation_field_exists():
    serialized = owner.serialize_controlled_provider_benchmark_plan().lower()

    for field in (
        '"recommended_route"',
        '"selected_model"',
        '"selected_provider"',
        '"selected_winner"',
        '"winning_model"',
    ):
        assert field not in serialized


def test_transmission_review_covers_every_case():
    plan = _plan()

    assert len(plan["transmission_review"]) == plan["case_count"] == 15
    assert plan["transmission_review_summary"] == {
        "reviewed_case_count": 15,
        "eligible_case_count": 12,
        "ineligible_case_count": 3,
    }


@pytest.mark.parametrize(
    ("field", "value", "review_flag"),
    [
        ("person_name", "Synthetic Person", "contains_person_name"),
        ("email", "synthetic@example.invalid", "contains_personal_data"),
        ("runtime_record", "synthetic", "contains_runtime_derived_data"),
        (
            "employer",
            "Synthetic Employer",
            "contains_employer_or_company_identity",
        ),
        ("resume_text", "synthetic", "contains_resume_derived_text"),
        (
            "job_description",
            "synthetic",
            "contains_private_job_description_text",
        ),
        (
            "api_key",
            "synthetic-not-a-key",
            "contains_credentials_or_secrets",
        ),
        ("source_path", "/tmp/synthetic", "contains_internal_paths"),
        ("request_id", "synthetic", "contains_request_identifiers"),
        ("database_url", "synthetic", "contains_database_information"),
        (
            "application_status",
            "synthetic",
            "contains_proprietary_application_state",
        ),
        (
            "notes",
            "x" * 161,
            "contains_unsupported_free_form_text",
        ),
    ],
)
def test_sensitive_input_categories_fail_transmission_review(
    field, value, review_flag, monkeypatch
):
    review = _review_with_input_field(field, value, monkeypatch)

    assert review[review_flag] is True
    assert review["requires_additional_redaction"] is True
    assert review["eligible_for_later_controlled_transmission"] is False
    assert review["human_approval_required"] is True


def test_repository_sanitized_cases_are_not_automatically_eligible():
    corpus = step8o.load_fixture_case_corpus()
    reviews = owner.build_transmission_review(corpus)

    for case, review in zip(corpus["cases"], reviews):
        if case["sanitized_classification"] != "synthetic_sanitized":
            assert review["eligible_for_later_controlled_transmission"] is False
            assert "classification_not_wholly_synthetic" in (
                review["eligibility_reasons"]
            )


def test_expected_or_grader_material_stays_local(monkeypatch):
    review = _review_with_input_field(
        "expected_classification", "synthetic", monkeypatch
    )

    assert review["eligible_for_later_controlled_transmission"] is False
    assert "contains_local_only_expected_or_grader_material" in (
        review["eligibility_reasons"]
    )


def test_local_aliases_are_deterministic_unique_and_non_reversible():
    first = owner.build_transmission_review()
    second = owner.build_transmission_review()
    case_ids = {
        case["case_id"]
        for case in step8o.load_fixture_case_corpus()["cases"]
    }

    assert [row["case_alias"] for row in first] == [
        row["case_alias"] for row in second
    ]
    assert len({row["case_alias"] for row in first}) == 15
    assert all(
        alias.startswith("case_")
        and len(alias) == 29
        and alias not in case_ids
        for alias in (row["case_alias"] for row in first)
    )


def test_request_packet_fields_match_the_exact_allowlist():
    packet = _request_packet()
    plan = _plan()

    assert sorted(packet) == plan["request_packet_schema"][
        "allowlisted_fields"
    ]
    assert packet["benchmark_contract_version"] == (
        "provider-benchmark-contract-v1"
    )
    assert packet["run_plan_version"] == (
        "controlled-provider-benchmark-plan-v1"
    )


def test_request_packet_excludes_goldens_and_provenance():
    serialized = json.dumps(_request_packet(), sort_keys=True).lower()

    assert "expected_output" not in serialized
    assert "expected_invariant" not in serialized
    assert "golden" not in serialized
    assert "provenance" not in serialized


@pytest.mark.parametrize(
    "field",
    [
        "expected_classification",
        "grader_threshold",
        "provenance",
        "repository_path",
        "resume_content",
        "request_id",
        "database_metadata",
        "production_run_id",
        "owner_id",
        "application_state",
        "ats_data",
    ],
)
def test_prohibited_request_fields_fail_closed(field):
    packet = _request_packet()
    packet[field] = "synthetic"

    with pytest.raises(ValueError, match="allowlist|prohibited"):
        owner.validate_transmittable_request_packet(packet)


def test_every_proposed_request_packet_validates():
    plan = _plan()

    for row in plan["staged_matrix"]:
        packet = owner.build_transmittable_request_packet(
            case_alias=row["case_alias"],
            provider=row["provider"],
            model=row["model"],
            plan=plan,
        )
        assert owner.validate_transmittable_request_packet(
            packet, plan=plan
        )


def test_execution_matrix_is_stable_and_serial():
    first = _plan()["staged_matrix"]
    second = _plan()["staged_matrix"]

    assert first == second
    assert [row["execution_order"] for row in first] == list(
        range(1, len(first) + 1)
    )


def test_tier_a_starts_with_groq_20b():
    plan = _plan()

    for alias in {row["case_alias"] for row in plan["staged_matrix"]}:
        rows = [
            row for row in plan["staged_matrix"]
            if row["case_alias"] == alias and row["tier"] == "A"
        ]
        if rows:
            assert rows[0]["provider"] == "groq"
            assert rows[0]["model"] == "openai/gpt-oss-20b"


def test_tier_c_starts_with_groq_120b_and_has_20b_baseline():
    plan = _plan()

    for alias in {row["case_alias"] for row in plan["staged_matrix"]}:
        rows = [
            row for row in plan["staged_matrix"]
            if row["case_alias"] == alias and row["tier"] == "C"
        ]
        if rows:
            assert [row["model"] for row in rows] == [
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b",
            ]


def test_gpt_5_1_is_never_automatically_assigned():
    plan = _plan()

    assert plan["request_counts"]["by_model"]["openai/gpt-5.1"] == 0
    assert all(
        row["model"] != "gpt-5.1" for row in plan["staged_matrix"]
    )
    assert plan["conditional_future_comparisons"][
        "gpt_5_1_requires_revised_plan_and_authorization"
    ] is True


def test_proposed_request_counts_are_exact_and_bounded():
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
    assert all(value <= 28 for value in counts["maximum_requests_per_model"].values())


def test_request_count_by_workload_is_complete():
    counts = _plan()["request_counts"]["by_workload"]

    assert list(counts) == list(WORKLOAD_ORDER)
    assert sum(counts.values()) == 28


def test_duplicate_case_provider_model_combination_is_absent():
    matrix = _plan()["staged_matrix"]
    keys = {
        (row["case_alias"], row["provider"], row["model"])
        for row in matrix
    }

    assert len(keys) == len(matrix)


def test_execution_policy_is_serial_nonrecursive_and_stops_on_failure():
    policy = _plan()["execution_policy"]

    assert policy["serial_ordering_required"] is True
    assert policy["parallel_execution_allowed"] is False
    assert policy["recursive_execution_allowed"] is False
    assert policy["immediate_stop_on_hard_safety_failure"] is True
    assert (
        policy["duplicate_request_after_ambiguous_timeout_allowed"] is False
    )


def test_harness_and_ambiguous_timeout_retries_are_prohibited():
    policy = _plan()["retry_policy"]

    assert policy["harness_retry_limit"] == 0
    assert policy["ambiguous_timeout_retry_allowed"] is False
    assert policy["provider_sdk_automatic_retries_required"] == 0


def test_timeout_is_explicit_bounded_and_a_stop_condition():
    policy = _plan()["timeout_policy"]

    assert policy == {
        "timeout_seconds": 30,
        "explicit_timeout_required": True,
        "timeout_is_stop_condition": True,
    }
    assert "ambiguous_timeout" in _plan()["stop_conditions"]


def test_duration_limits_are_explicit():
    policy = _plan()["execution_policy"]

    assert policy["maximum_run_duration_seconds"] == 900
    assert policy["maximum_provider_duration_seconds"] == {
        "groq": 600,
        "openai": 300,
    }


def test_token_budgets_are_positive_bounded_and_observed():
    plan = _plan()
    budget = plan["token_budget_schema"]
    requests = plan["request_counts"]["maximum_total_requests"]

    assert budget["maximum_input_tokens_per_request"] == 4096
    assert budget["maximum_output_tokens_per_request"] == 1024
    assert budget["maximum_total_observed_input_tokens"] == requests * 4096
    assert budget["maximum_total_observed_output_tokens"] == requests * 1024
    assert budget["observed_input_tokens_required"] is True
    assert budget["observed_output_tokens_required"] is True


def test_missing_observed_usage_blocks_cost_comparison():
    assert _plan()["token_budget_schema"][
        "missing_usage_blocks_cost_comparison"
    ] is True
    assert _plan()["cost_ceiling_schema"][
        "missing_cost_blocks_comparison"
    ] is True


def test_cost_ceiling_schema_requires_operator_pricing_and_dollar_bounds():
    schema = _plan()["cost_ceiling_schema"]

    assert schema["currency"] == "USD"
    assert schema["pricing_table_version_required"] is True
    assert schema["operator_approved_pricing_table_required"] is True
    assert schema["maximum_observed_cost_per_model_required"] is True
    assert schema["maximum_total_observed_cost_required"] is True
    assert schema["positive_dollar_ceiling_required"] is True
    assert schema["stop_on_cost_ceiling_exceeded"] is True


def test_no_price_or_estimated_cost_is_hard_coded():
    plan = _plan()
    serialized = owner.serialize_controlled_provider_benchmark_plan(plan)

    assert "price_per" not in serialized
    assert "estimated_cost" not in serialized
    assert "pricing_table_version_required" in serialized


def test_result_packet_fields_match_the_exact_allowlist():
    packet = _result_packet()
    plan = _plan()

    assert sorted(packet) == plan["result_packet_schema"][
        "allowlisted_fields"
    ]
    assert owner.validate_redacted_result_packet(packet)


@pytest.mark.parametrize(
    "field",
    [
        "raw_response",
        "raw_provider_envelope",
        "headers",
        "provider_request_id",
        "credential",
        "prompt",
        "unredacted_provider_error",
        "reasoning_trace",
        "tool_output",
        "transport_log",
    ],
)
def test_prohibited_result_fields_fail_closed(field):
    packet = _result_packet()
    packet[field] = "synthetic"

    with pytest.raises(ValueError, match="allowlist|prohibited"):
        owner.validate_redacted_result_packet(packet)


def test_result_fallback_and_retry_fail_closed():
    fallback = _result_packet()
    fallback["fallback_used"] = True
    retry = _result_packet()
    retry["retry_count"] = 1

    with pytest.raises(ValueError, match="fallback"):
        owner.validate_redacted_result_packet(fallback)
    with pytest.raises(ValueError, match="retries"):
        owner.validate_redacted_result_packet(retry)


def test_raw_response_persistence_is_prohibited():
    plan = _plan()

    assert plan["result_packet_schema"][
        "raw_response_persistence_allowed"
    ] is False
    assert plan["artifact_retention_policy"][
        "raw_sdk_object_allowed"
    ] is False
    assert plan["artifact_retention_policy"][
        "raw_response_envelope_allowed"
    ] is False


def test_artifact_retention_is_ignored_restrictive_and_operator_reviewed():
    policy = _plan()["artifact_retention_policy"]

    assert policy["automatic_persistence"] is False
    assert policy["ignored_artifact_only"] is True
    assert policy["normalized_output_only"] is True
    assert policy["provider_request_id_allowed"] is False
    assert policy["reasoning_trace_allowed"] is False
    assert policy["required_file_mode"] == "0600"
    assert policy["maximum_retention_days"] == 7
    assert policy["operator_review_required_before_deletion"] is True
    assert policy["delete_after_review"] is True


def test_authorization_schema_is_operator_created_and_not_automatic():
    schema = _plan()["authorization_schema"]

    assert schema["authorization_version"] == (
        "controlled-provider-benchmark-authorization-v1"
    )
    assert schema["operator_created_only"] is True
    assert schema["automatic_creation_allowed"] is False
    assert schema["positive_dollar_ceiling_required"] is True
    assert schema["bounded_validity_window_required"] is True


def test_exact_operator_authorization_validates():
    assert owner.validate_operator_authorization(
        _authorization(),
        execution_at_utc="2026-06-01T00:00:00Z",
    )


def test_absent_operator_authorization_fails_closed():
    with pytest.raises(ValueError, match="authorization is required"):
        owner.validate_operator_authorization(
            None,
            execution_at_utc="2026-06-01T00:00:00Z",
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("benchmark_plan_sha256", "0" * 64, "plan hash mismatch"),
        ("case_corpus_sha256", "0" * 64, "corpus hash mismatch"),
        ("maximum_request_count", 999, "request budget mismatch"),
        ("fallback", True, "fallback must be false"),
        ("gemini_allowed", True, "Gemini scope"),
        (
            "production_activation_allowed",
            True,
            "production activation",
        ),
        ("operator_approved", False, "approval Boolean"),
    ],
)
def test_authorization_mismatches_fail_closed(field, value, message):
    authorization = _authorization()
    authorization[field] = value

    with pytest.raises(ValueError, match=message):
        owner.validate_operator_authorization(
            authorization,
            execution_at_utc="2026-06-01T00:00:00Z",
        )


def test_expired_operator_authorization_fails_closed():
    with pytest.raises(ValueError, match="expired"):
        owner.validate_operator_authorization(
            _authorization(),
            execution_at_utc="2027-01-01T00:00:00Z",
        )


def test_broader_case_authorization_fails_closed():
    authorization = _authorization()
    authorization["approved_case_aliases"].append("case_" + "f" * 24)

    with pytest.raises(ValueError, match="case scope"):
        owner.validate_operator_authorization(
            authorization,
            execution_at_utc="2026-06-01T00:00:00Z",
        )


def test_provider_model_mismatch_authorization_fails_closed():
    authorization = _authorization()
    authorization["approved_candidate_pairs"][0]["model"] = "gpt-5.1"

    with pytest.raises(ValueError, match="provider/model scope"):
        owner.validate_operator_authorization(
            authorization,
            execution_at_utc="2026-06-01T00:00:00Z",
        )


def test_missing_dollar_ceiling_fails_closed():
    authorization = _authorization()
    authorization.pop("maximum_total_observed_cost")

    with pytest.raises(ValueError, match="malformed"):
        owner.validate_operator_authorization(
            authorization,
            execution_at_utc="2026-06-01T00:00:00Z",
        )


def test_nonpositive_per_model_dollar_ceiling_fails_closed():
    authorization = _authorization()
    first = next(iter(authorization["maximum_observed_cost_per_model"]))
    authorization["maximum_observed_cost_per_model"][first] = 0

    with pytest.raises(ValueError, match="per-model dollar ceilings"):
        owner.validate_operator_authorization(
            authorization,
            execution_at_utc="2026-06-01T00:00:00Z",
        )


def test_stop_conditions_are_complete_and_unique():
    stop_conditions = _plan()["stop_conditions"]
    required = {
        "provider_model_mismatch",
        "unapproved_case",
        "unapproved_model",
        "fallback_attempted",
        "retry_attempted",
        "request_budget_exceeded",
        "input_token_budget_exceeded",
        "output_token_budget_exceeded",
        "cost_ceiling_exceeded",
        "raw_response_persistence",
        "sensitive_information_detected",
        "schema_invalid_response_accepted",
        "unsupported_claim",
        "hallucination",
        "deterministic_authority_mutation",
        "application_or_ats_reach",
        "unknown_provider_error",
        "missing_usage_metadata",
        "duplicate_call_uncertainty",
        "ambiguous_timeout",
    }

    assert set(stop_conditions) == required
    assert len(stop_conditions) == len(required)


def test_rollback_contract_preserves_default_off_state():
    rollback = _plan()["rollback_contract"]

    assert rollback["production_routing_change_allowed"] is False
    assert rollback["provider_default_change_allowed"] is False
    assert rollback["cache_promotion_allowed"] is False
    assert rollback["model_selection_publication_allowed"] is False
    assert rollback["application_planning_integration_allowed"] is False
    assert rollback[
        "ignored_redacted_evidence_preserved_for_review"
    ] is True
    assert rollback["return_to_default_off_required"] is True


def test_quality_precedes_cost_and_same_safety_floor_is_required():
    evidence = _plan()["model_selection_evidence_requirements"]

    assert evidence["quality_precedes_cost"] is True
    assert evidence["lower_cost_must_meet_same_quality_and_safety"] is True
    assert evidence[
        "gpt_5_1_requires_observed_material_quality_improvement"
    ] is True


def test_model_selection_does_not_execute():
    evidence = _plan()["model_selection_evidence_requirements"]

    assert evidence["selection_execution_allowed"] is False
    assert _plan()["rollback_contract"][
        "model_selection_publication_allowed"
    ] is False


def test_model_selection_evidence_requirements_are_complete():
    evidence = _plan()["model_selection_evidence_requirements"]

    for field in (
        "controlled_live_results_required",
        "minimum_case_coverage_required",
        "all_hard_failures_zero_required",
        "schema_valid_rate_threshold_required",
        "normalization_threshold_required",
        "unsupported_claims_zero_required",
        "hallucinations_zero_required",
        "deterministic_authority_required",
        "task_specific_quality_thresholds_required",
        "observed_latency_required",
        "observed_token_counts_required",
        "observed_cost_required",
        "repeatability_evidence_when_required",
        "human_review_for_critical_workloads",
    ):
        assert evidence[field] is True


def test_canonical_serialization_is_stable_and_round_trips():
    serialized = owner.serialize_controlled_provider_benchmark_plan()

    assert serialized == owner.serialize_controlled_provider_benchmark_plan()
    assert json.dumps(
        json.loads(serialized),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) == serialized


def test_plan_digest_is_stable_in_process():
    plan = _plan()

    assert owner.controlled_provider_benchmark_plan_sha256(plan) == (
        owner.controlled_provider_benchmark_plan_sha256(deepcopy(plan))
    )


def test_plan_digest_is_stable_in_a_fresh_process():
    expected = owner.controlled_provider_benchmark_plan_sha256()
    command = (
        "from src.evaluation.controlled_provider_benchmark_plan import "
        "controlled_provider_benchmark_plan_sha256;"
        "print(controlled_provider_benchmark_plan_sha256())"
    )

    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )

    assert completed.stdout.strip() == expected


def test_plan_digest_excludes_machine_specific_state():
    serialized = owner.serialize_controlled_provider_benchmark_plan()

    assert str(ROOT) not in serialized
    assert '"timestamp"' not in serialized.lower()
    assert '".env"' not in serialized.lower()
    assert "synthetic-not-a-key" not in serialized.lower()


def test_plan_and_packets_are_deep_copy_contained():
    first = _plan()
    first["candidate_definitions"][0]["provider"] = "mutated"
    second = _plan()
    packet = _request_packet(second)
    packet["synthetic_input"]["local_mutation"] = True

    assert second["candidate_definitions"][0]["provider"] == "groq"
    assert "local_mutation" not in _request_packet(second)["synthetic_input"]


def test_plan_validator_rejects_authority_mutation():
    plan = _plan()
    plan["authority_invariants"]["provider_calls_allowed"] = True

    with pytest.raises(ValueError, match="authority changed"):
        owner.validate_controlled_provider_benchmark_plan(plan)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("fallback_policy", "fallback"), True, "fallback"),
        (("retry_policy", "harness_retry_limit"), 1, "retries"),
        (
            ("execution_policy", "parallel_execution_allowed"),
            True,
            "execution policy",
        ),
        (
            ("result_packet_schema", "raw_response_persistence_allowed"),
            True,
            "result packet schema",
        ),
        (
            ("artifact_retention_policy", "automatic_persistence"),
            True,
            "retention",
        ),
        (
            ("model_selection_evidence_requirements", "quality_precedes_cost"),
            False,
            "evidence contract",
        ),
    ],
)
def test_controlled_plan_safety_contract_mutations_fail_closed(
    path, value, message
):
    plan = _plan()
    plan[path[0]][path[1]] = value

    with pytest.raises(ValueError, match=message):
        owner.validate_controlled_provider_benchmark_plan(plan)


def test_owner_has_no_provider_or_shared_client_import():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    assert not any(
        name == "src.ai.llm_client"
        or name.startswith(("openai", "groq", "google.generativeai"))
        for name in imported
    )


def test_owner_has_no_dotenv_network_database_subprocess_or_thread_import():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append((node.module or "").split(".")[0])

    assert not set(imported) & {
        "dotenv",
        "httpx",
        "requests",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "subprocess",
        "threading",
        "multiprocessing",
    }


def test_owner_has_no_runtime_write_primitive():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    prohibited_attributes = {
        "write_text",
        "write_bytes",
        "mkdir",
        "touch",
        "unlink",
        "rename",
    }

    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in prohibited_attributes
        for node in ast.walk(tree)
    )


def test_import_build_serialize_and_hash_load_no_provider_modules():
    command = (
        "import sys;"
        "from src.evaluation.controlled_provider_benchmark_plan import "
        "build_controlled_provider_benchmark_plan,"
        "serialize_controlled_provider_benchmark_plan,"
        "controlled_provider_benchmark_plan_sha256;"
        "p=build_controlled_provider_benchmark_plan();"
        "serialize_controlled_provider_benchmark_plan(p);"
        "controlled_provider_benchmark_plan_sha256(p);"
        "print(','.join(sorted(n for n in sys.modules if "
        "n.split('.')[0] in {'openai','groq','google'} "
        "or n == 'src.ai.llm_client')))"
    )

    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )

    assert completed.stdout.strip() == ""


def test_plan_construction_creates_no_repository_artifact():
    before = {
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }

    owner.build_controlled_provider_benchmark_plan()
    owner.serialize_controlled_provider_benchmark_plan()
    owner.controlled_provider_benchmark_plan_sha256()

    after = {
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }
    assert after == before


def test_authority_mutation_application_and_ats_counts_remain_zero():
    authority = _plan()["authority_invariants"]

    assert authority["mutation_count"] == 0
    assert authority["application_action_count"] == 0
    assert authority["ats_action_count"] == 0
    assert authority["routing_change_allowed"] is False
    assert authority["production_activation_allowed"] is False


def test_step8l_contract_digest_remains_stable():
    assert _plan()["step8l_contract_sha256"] == (
        provider_benchmark_contract_sha256()
    )


def test_step8m_compatibility_digest_remains_at_baseline():
    assert provider_client_compatibility_sha256() == STEP8M_BASELINE_SHA256


def test_step8o_case_and_engine_digests_remain_stable():
    plan = _plan()

    assert plan["step8o_case_corpus_sha256"] == (
        step8o.fixture_case_corpus_sha256()
    )
    assert plan["step8o_engine_sha256"] == (
        step8o.provider_fixture_benchmark_sha256()
    )


def test_run_plan_fixture_validates_and_is_versioned():
    fixture = owner.load_run_plan_fixture()

    assert fixture["fixture_version"] == (
        "controlled-provider-benchmark-run-plan-fixture-v1"
    )
    assert owner.validate_run_plan_fixture(fixture)
    assert RUN_PLAN_PATH.is_file()


@pytest.mark.parametrize(
    ("section", "field", "value", "message"),
    [
        ("request_limits", "temperature", 0.2, "temperature"),
        ("request_limits", "harness_retry_limit", 1, "retries"),
        (
            "request_limits",
            "parallel_execution_allowed",
            True,
            "serial",
        ),
        (
            "request_limits",
            "ambiguous_timeout_retry_allowed",
            True,
            "serial",
        ),
        (
            "artifact_retention_policy",
            "automatic_persistence",
            True,
            "retention",
        ),
        (
            "artifact_retention_policy",
            "provider_request_id_allowed",
            True,
            "retention",
        ),
    ],
)
def test_unsafe_run_plan_fixture_mutations_fail_closed(
    section, field, value, message
):
    fixture = owner.load_run_plan_fixture()
    fixture[section][field] = value

    with pytest.raises(ValueError, match=message):
        owner.validate_run_plan_fixture(fixture)


def test_recovery_006_status_remains_absent_and_unauthorized():
    assert not RECOVERY_006_STATUS.exists()
    assert _plan()["authority_invariants"]["recovery_006_authorized"] is False


def test_plan_owner_is_evaluation_infrastructure_only():
    assert owner.STEP8L_CONTRACT_SOURCE.startswith("src/evaluation/")
    assert owner.STEP8O_ENGINE_SOURCE.startswith("src/evaluation/")
    assert owner.RUN_PLAN_FIXTURE_SOURCE.startswith(
        "tests/fixtures/provider_benchmark/"
    )
