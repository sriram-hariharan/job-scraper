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
    workload_qualification_contract_sha256,
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


def test_skill_gets_120b_without_expanding_other_tier_a_workloads():
    plan = _plan()
    identities = {
        (row["workload_id"], row["provider"], row["model"])
        for row in plan["staged_matrix"]
    }

    assert (
        "skill_extraction",
        "groq",
        "openai/gpt-oss-120b",
    ) in identities
    assert (
        "manual_scan_phrase",
        "groq",
        "openai/gpt-oss-120b",
    ) not in identities
    assert len(plan["staged_matrix"]) == 45
    assert len(identities) == 45

    skill_rows = [
        row for row in plan["staged_matrix"]
        if row["workload_id"] == "skill_extraction"
    ]
    assert [
        (row["provider"], row["model"])
        for row in skill_rows
    ] == [
        ("groq", "openai/gpt-oss-20b"),
        ("groq", "openai/gpt-oss-120b"),
        ("openai", "gpt-5-mini"),
    ]


def test_tier_b_and_c_rows_include_all_catalog_eligible_models():
    plan = _plan()

    for alias in {row["case_alias"] for row in plan["staged_matrix"]}:
        rows = [
            row for row in plan["staged_matrix"]
            if row["case_alias"] == alias and row["tier"] in {"B", "C"}
        ]
        if rows:
            assert [row["model"] for row in rows] == [
                "openai/gpt-oss-20b",
                "openai/gpt-oss-120b",
                "gpt-5-mini",
                "gpt-5.1",
            ]


def test_gpt_5_1_is_in_every_currently_eligible_plan_cell():
    plan = _plan()

    rows = [row for row in plan["staged_matrix"] if row["model"] == "gpt-5.1"]
    assert len(rows) == 10
    assert {row["tier"] for row in rows} == {"B", "C"}
    assert all(row["workload_id"] != "skill_extraction" for row in rows)


def test_matrix_matches_contract_tier_eligibility_without_qualification_claim():
    plan = _plan()
    benchmark = build_provider_benchmark_contract()
    candidates = {
        row["candidate_id"]: (row["provider"], row["model"])
        for row in benchmark["candidate_definitions"]
    }
    expected_by_workload = {
        row["workload_id"]: [
            candidates[value] for value in row["candidate_ids"]
        ]
        for row in benchmark["candidate_matrix"]
    }

    for workload_id, expected in expected_by_workload.items():
        actual = [
            (row["provider"], row["model"])
            for row in plan["staged_matrix"]
            if row["workload_id"] == workload_id
        ]
        assert actual == expected
    assert "qualified" not in json.dumps(plan).lower()


def test_proposed_request_counts_are_exact_and_bounded():
    counts = _plan()["request_counts"]

    assert counts["by_provider"] == {"groq": 23, "openai": 22}
    assert counts["by_model"] == {
        "groq/openai/gpt-oss-20b": 12,
        "groq/openai/gpt-oss-120b": 11,
        "openai/gpt-5-mini": 12,
        "openai/gpt-5.1": 10,
    }
    assert counts["maximum_total_requests"] == 45
    assert counts["maximum_requests_per_case"] == 4
    assert all(
        value <= 45
        for value in counts["maximum_requests_per_model"].values()
    )


def test_request_count_by_workload_is_complete():
    counts = _plan()["request_counts"]["by_workload"]

    assert list(counts) == list(WORKLOAD_ORDER)
    assert sum(counts.values()) == 45


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


def test_full_step8l_plan_binding_remains_fail_closed(monkeypatch):
    baseline = _plan()
    manifest = deepcopy(
        build_provider_benchmark_contract()["fixture_manifest"]
    )
    job_fit = next(
        row
        for row in manifest["fixtures"]
        if row["workload_id"] == "job_fit_evaluation"
    )
    job_fit["golden_output_available"] = not job_fit[
        "golden_output_available"
    ]
    changed_contract = build_provider_benchmark_contract(manifest)
    monkeypatch.setattr(
        owner,
        "build_provider_benchmark_contract",
        lambda: deepcopy(changed_contract),
    )

    changed = owner.build_controlled_provider_benchmark_plan()
    assert changed["step8l_contract_sha256"] == (
        provider_benchmark_contract_sha256(changed_contract)
    )
    assert changed["step8l_contract_sha256"] != baseline[
        "step8l_contract_sha256"
    ]
    changed["step8l_contract_sha256"] = baseline["step8l_contract_sha256"]
    with pytest.raises(
        ValueError,
        match="controlled plan benchmark contract digest mismatch",
    ):
        owner.validate_controlled_provider_benchmark_plan(changed)


def test_workload_projection_uses_scoped_step8l_qualification_identity():
    from src.evaluation import provider_benchmark_contract as step8l

    plan = _plan()
    projection = owner.build_workload_plan_projection(
        "skill_extraction",
        plan=plan,
    )

    assert plan["step8l_contract_sha256"] == provider_benchmark_contract_sha256()
    assert projection["global_execution_envelope"][
        "step8l_contract_sha256"
    ] == step8l.workload_qualification_contract_sha256("skill_extraction")
    assert projection["global_execution_envelope"][
        "step8l_contract_sha256"
    ] != plan["step8l_contract_sha256"]


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


# ---------------------------------------------------------------------------
# Stage 1: additive stable-alias and workload plan-projection primitives.
# ---------------------------------------------------------------------------


CURRENT_CONTROLLED_PLAN_SHA256 = (
    "bacc7eaa4524199ba293e2d50232f5a8c6cf61014ad8dc89c3dd30d334654162"
)
CURRENT_SKILL_EXTRACTION_ALIAS = "case_ab6a1757752b2853f320aebf"


def _stage1_skill_extraction_only_change(corpus):
    mutated = deepcopy(corpus)
    case = next(
        row
        for row in mutated["cases"]
        if row["workload_id"] == "skill_extraction"
    )
    case["normalized_input_packet"]["preferred_terms"].append("terraform")
    case["normalized_input_packet"]["evidence_tokens"].append("terraform")
    case["expected_output"]["preferred_skills"].append("terraform")
    case["supported_evidence_tokens"].append("terraform")
    return mutated


def test_stage1_current_plan_authority_digests_are_unchanged():
    corpus = step8o.load_fixture_case_corpus()
    plan = owner.build_controlled_provider_benchmark_plan(corpus=corpus)

    assert owner.controlled_provider_benchmark_plan_sha256(plan) == (
        CURRENT_CONTROLLED_PLAN_SHA256
    )
    # Stage 1 primitives must not appear in the authoritative plan payload.
    for field in ("staged_matrix", "transmission_review"):
        for row in plan[field]:
            assert "stable_case_alias" not in row
    assert not any(
        key.startswith("workload_qualification_semantics")
        or key.startswith("workload_plan_projection")
        or key.startswith("stable_case_alias")
        for key in plan
    )


def test_stage1_current_case_aliases_are_unchanged():
    corpus = step8o.load_fixture_case_corpus()
    digest = step8o.fixture_case_corpus_sha256(corpus)
    legacy = owner.legacy_case_alias_map(corpus)

    assert len(legacy) == len(corpus["cases"])
    assert legacy["skill_extraction_required_preferred_v1"] == (
        CURRENT_SKILL_EXTRACTION_ALIAS
    )
    for case in corpus["cases"]:
        assert legacy[case["case_id"]] == owner._case_alias(
            case["case_id"], digest
        )

    planned_aliases = {row["case_alias"] for row in
                       owner.build_controlled_provider_benchmark_plan(
                           corpus=corpus)["transmission_review"]}
    assert planned_aliases == set(legacy.values())


def test_stage1_stable_alias_is_independent_of_global_corpus_digest():
    corpus = step8o.load_fixture_case_corpus()
    mutated = _stage1_skill_extraction_only_change(corpus)
    assert step8o.fixture_case_corpus_sha256(corpus) != (
        step8o.fixture_case_corpus_sha256(mutated)
    )

    for case in corpus["cases"]:
        alias = owner.stable_case_alias(case["workload_id"], case["case_id"])
        assert alias == owner.stable_case_alias(
            case["workload_id"], case["case_id"]
        )
        assert alias.startswith("case_")
        # Corpus content changed; the stable identity did not.
        assert alias == owner.stable_case_alias(
            case["workload_id"], case["case_id"]
        )

    distinct = {
        owner.stable_case_alias(case["workload_id"], case["case_id"])
        for case in corpus["cases"]
    }
    assert len(distinct) == len(corpus["cases"])
    with pytest.raises(ValueError):
        owner.stable_case_alias("", "case")


def test_stage1_workload_plan_projection_isolates_one_workload():
    corpus = step8o.load_fixture_case_corpus()
    mutated = _stage1_skill_extraction_only_change(corpus)

    changed = [
        workload_id
        for workload_id in WORKLOAD_ORDER
        if owner.workload_plan_projection_sha256(workload_id, corpus=corpus)
        != owner.workload_plan_projection_sha256(workload_id, corpus=mutated)
    ]

    assert changed == ["skill_extraction"]


def test_stage1_workload_plan_projection_binds_global_execution_envelope():
    """Every workload digest must move when the shared safety envelope moves.

    The run-plan fixture is a fixed on-disk safety envelope and the plan
    validator always re-reads it, so an altered envelope cannot be pushed
    through the builder. Bind-sensitivity is proven on the canonical projection
    material instead.
    """

    from hashlib import sha256

    corpus = step8o.load_fixture_case_corpus()
    plan = owner.build_controlled_provider_benchmark_plan(corpus=corpus)

    changed = []
    for workload_id in WORKLOAD_ORDER:
        projection = owner.build_workload_plan_projection(
            workload_id, plan=plan, corpus=corpus
        )
        envelope = projection["global_execution_envelope"]
        assert set(envelope) == set(owner._GLOBAL_ENVELOPE_PLAN_FIELDS)
        for field in owner._GLOBAL_ENVELOPE_PLAN_FIELDS:
            if field == "token_budget_schema":
                # Stage 4B: only the independent per-request token policy is
                # bound; corpus-derived run totals are excluded.
                assert envelope[field] == {
                    member: plan[field][member]
                    for member in owner._GLOBAL_TOKEN_POLICY_FIELDS
                }
                continue
            if field == "step8l_contract_sha256":
                assert envelope[field] == (
                    workload_qualification_contract_sha256(workload_id)
                )
                continue
            assert envelope[field] == plan[field]

        baseline = sha256(
            owner._canonical_json(projection).encode("utf-8")
        ).hexdigest()
        altered = deepcopy(projection)
        altered["global_execution_envelope"]["execution_policy"][
            "maximum_run_duration_seconds"
        ] = 600
        moved = sha256(
            owner._canonical_json(altered).encode("utf-8")
        ).hexdigest()
        if moved != baseline:
            changed.append(workload_id)

    assert changed == list(WORKLOAD_ORDER)


def test_stage1_workload_plan_projection_carries_stable_identities_only():
    corpus = step8o.load_fixture_case_corpus()
    projection = owner.build_workload_plan_projection(
        "skill_extraction", corpus=corpus
    )

    assert projection["alias_scheme_version"] == owner.CASE_ALIAS_SCHEME_VERSION
    assert projection["workload_id"] == "skill_extraction"
    for field in ("staged_rows", "transmission_rows"):
        assert projection[field]
        for row in projection[field]:
            assert "case_alias" not in row
            assert row["stable_case_alias"] == owner.stable_case_alias(
                "skill_extraction", "skill_extraction_required_preferred_v1"
            )
    with pytest.raises(ValueError):
        owner.workload_plan_projection_sha256("not_a_workload")


# ---------------------------------------------------------------------------
# Stage 4B: workload-semantics isolation under case ADDITION.
# ---------------------------------------------------------------------------


def _stage4b_future_corpus(corpus):
    import test_provider_fixture_benchmark as fixture_suite

    future = deepcopy(corpus)
    future["cases"] = future["cases"] + (
        fixture_suite.stage4b_proposed_skill_cases()
    )
    return future


def test_stage4b_projection_excludes_global_sequence_and_derived_totals():
    corpus = step8o.load_fixture_case_corpus()
    plan = owner.build_controlled_provider_benchmark_plan(corpus=corpus)

    assert owner._WORKLOAD_PROJECTION_EXCLUDED_ROW_FIELDS == (
        "case_alias",
        "execution_order",
    )
    # execution_order stays in the authoritative V1 plan and schedule.
    assert all("execution_order" in row for row in plan["staged_matrix"])

    projection = owner.build_workload_plan_projection(
        "skill_extraction", plan=plan, corpus=corpus
    )
    for row in projection["staged_rows"]:
        assert "execution_order" not in row
        assert "case_alias" not in row

    token_policy = projection["global_execution_envelope"][
        "token_budget_schema"
    ]
    assert set(token_policy) == set(owner._GLOBAL_TOKEN_POLICY_FIELDS)
    # Derived run-size totals are excluded from workload authority but remain
    # in the authoritative plan.
    for derived in (
        "maximum_total_observed_input_tokens",
        "maximum_total_observed_output_tokens",
    ):
        assert derived not in token_policy
        assert derived in plan["token_budget_schema"]


def test_stage4b_adding_cases_isolates_workload_plan_projections():
    corpus = step8o.load_fixture_case_corpus()
    future = _stage4b_future_corpus(corpus)
    current_plan = owner.build_controlled_provider_benchmark_plan(
        corpus=corpus
    )
    future_plan = owner.build_controlled_provider_benchmark_plan(corpus=future)

    # The global run totals really do move; that must not leak into workloads.
    assert (
        current_plan["token_budget_schema"][
            "maximum_total_observed_input_tokens"
        ]
        != future_plan["token_budget_schema"][
            "maximum_total_observed_input_tokens"
        ]
    )

    changed = [
        workload_id
        for workload_id in WORKLOAD_ORDER
        if owner.workload_plan_projection_sha256(
            workload_id, plan=current_plan, corpus=corpus
        )
        != owner.workload_plan_projection_sha256(
            workload_id, plan=future_plan, corpus=future
        )
    ]
    assert changed == ["skill_extraction"]


def test_stage4b_genuine_global_safety_policy_still_invalidates_everything():
    """A real global safety-policy change must still invalidate all workloads.

    The plan validator ties the safety envelope to the on-disk run-plan
    fixture, so bind-sensitivity is proven on the canonical projection material
    rather than by pushing an unvalidatable plan through the builder.
    """

    from hashlib import sha256

    corpus = step8o.load_fixture_case_corpus()
    plan = owner.build_controlled_provider_benchmark_plan(corpus=corpus)

    def _moved(mutator):
        moved = []
        for workload_id in WORKLOAD_ORDER:
            projection = owner.build_workload_plan_projection(
                workload_id, plan=plan, corpus=corpus
            )
            baseline = sha256(
                owner._canonical_json(projection).encode("utf-8")
            ).hexdigest()
            altered = deepcopy(projection)
            mutator(altered["global_execution_envelope"])
            if sha256(
                owner._canonical_json(altered).encode("utf-8")
            ).hexdigest() != baseline:
                moved.append(workload_id)
        return moved

    # A genuine per-request token safety limit.
    assert _moved(
        lambda envelope: envelope["token_budget_schema"].__setitem__(
            "maximum_input_tokens_per_request", 2048
        )
    ) == list(WORKLOAD_ORDER)

    # An independent global execution-envelope limit.
    assert _moved(
        lambda envelope: envelope["execution_policy"].__setitem__(
            "maximum_run_duration_seconds", 600
        )
    ) == list(WORKLOAD_ORDER)


def test_stage4b_future_staged_matrix_projection():
    corpus = step8o.load_fixture_case_corpus()
    future = _stage4b_future_corpus(corpus)
    reviews = owner.build_transmission_review(corpus=future)
    plan = owner.build_controlled_provider_benchmark_plan(corpus=future)

    skill_reviews = [
        row for row in reviews if row["workload_id"] == "skill_extraction"
    ]
    eligible = [
        row
        for row in skill_reviews
        if row["eligible_for_later_controlled_transmission"]
    ]
    for row in skill_reviews:
        assert row["eligibility_reasons"] == [] or not row[
            "eligible_for_later_controlled_transmission"
        ]

    rows = [
        row
        for row in plan["staged_matrix"]
        if row["workload_id"] == "skill_extraction"
    ]
    candidates = {(row["provider"], row["model"]) for row in rows}

    assert len(skill_reviews) == 5
    assert len(eligible) == 5
    assert len(candidates) == 3
    assert len(rows) == 15

    # Current authority is untouched by the in-memory projection.
    assert step8o.fixture_case_corpus_sha256(
        step8o.load_fixture_case_corpus()
    ) == "59180e4064dd74759c6ecd8630478225b191f942b68fb1880e172fe07ee80aec"


def test_stage4b_recipe_cases_pass_transmission_safety_unmodified():
    corpus = step8o.load_fixture_case_corpus()
    future = _stage4b_future_corpus(corpus)
    digest = step8o.fixture_case_corpus_sha256(future)
    reviews = {
        row["case_alias"]: row
        for row in owner.build_transmission_review(corpus=future)
    }
    import test_provider_fixture_benchmark as fixture_suite

    flags = (
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
    for case in fixture_suite.stage4b_proposed_skill_cases():
        review = reviews[owner._case_alias(case["case_id"], digest)]
        for flag in flags:
            assert review[flag] is False, (case["case_id"], flag)
        assert review["eligible_for_later_controlled_transmission"] is True
        assert review["eligibility_reasons"] == []


# ---------------------------------------------------------------------------
# Step 14: controlled-canary current-case ownership.
#
# Historical canary identity stays immutable; current compatibility binds to the
# workload-stable case identity so unrelated corpus churn cannot invalidate a
# historical canary, while any real target-case change still fails closed.
# ---------------------------------------------------------------------------

STEP14_TARGETS = (
    ("skill_extraction", "skill_extraction_required_preferred_v1",
     "case_adb75e8f4222598d01c96632"),
    ("jd_intelligence", "jd_intelligence_signals_v1",
     "case_2f47393a4efcbe220d325519"),
    ("tailoring_generation", "tailoring_generation_evidence_bound_v1",
     "case_ff24f23eeb3e0bed33bfaefa"),
)


def test_step14_historical_canary_aliases_and_keys_remain_unchanged():
    from src.evaluation import controlled_groq_canary_run_003_plan as run003
    from src.evaluation import controlled_groq_canary_run_004_plan as run004
    from src.evaluation import controlled_groq_canary_run_005_plan as run005

    # Historical raw aliases - immutable execution evidence.
    assert run003.TARGET_CASE_ALIAS == "case_fb2b069aa9340571b60e1fb5"
    assert run004.HISTORICAL_TARGET_ALIASES == {
        "jd_intelligence": "case_db0a584dd7f8653ca842281f",
        "tailoring_generation": "case_ece85e9411ca52b579359fb8",
    }
    assert run005.TARGET_CASE_ALIAS == "case_ece85e9411ca52b579359fb8"
    # Historical base transport key and historical digests stay pinned.
    assert run005.EXPECTED_BASE_TRANSPORT_KEY == (
        "canary_969374f055f6d3a74a60a3e4ce6ee440"
    )
    for module in (run004, run005):
        assert module._HISTORICAL_FIXTURE_CORPUS_SHA256 == (
            "0ddc82e62745856c0d5d4d3f0efbe3fc86bd4e84e5da070f54f4ea635e74b05c"
        )
        assert module._HISTORICAL_CONTROLLED_PLAN_SHA256 == (
            "a3ef53ff992a2d1daf43f8fa9b0556202268d34e21f7611eb5de4d26e9abe6b6"
        )
    assert run005._HISTORICAL_RUN_005_SCHEDULE_KEY.startswith(
        "canary_run_005_"
    )


def test_step14_current_stable_identities_are_exact_and_corpus_independent():
    from src.evaluation import controlled_groq_canary_run_003_plan as run003
    from src.evaluation import controlled_groq_canary_run_004_plan as run004
    from src.evaluation import controlled_groq_canary_run_005_plan as run005

    assert run003.CURRENT_TARGET_STABLE_CASE_ALIAS == (
        "case_adb75e8f4222598d01c96632"
    )
    assert run005.CURRENT_TARGET_STABLE_CASE_ALIAS == (
        "case_ff24f23eeb3e0bed33bfaefa"
    )
    assert {
        workload: row["stable_case_alias"]
        for workload, row in run004.CURRENT_TARGET_OWNERSHIP.items()
    } == {
        "jd_intelligence": "case_2f47393a4efcbe220d325519",
        "tailoring_generation": "case_ff24f23eeb3e0bed33bfaefa",
    }
    # No canary pins a CURRENT raw alias any more: raw aliases are derived.
    assert not hasattr(run003, "CURRENT_TARGET_CASE_ALIAS")
    assert not hasattr(run005, "CURRENT_TARGET_CASE_ALIAS")
    assert all(
        "case_alias" not in row
        for row in run004.CURRENT_TARGET_OWNERSHIP.values()
    )
    for workload, case_id, stable in STEP14_TARGETS:
        assert owner.stable_case_alias(workload, case_id) == stable


def test_step14_current_ownership_accepts_the_approved_case():
    for workload, case_id, stable in STEP14_TARGETS:
        observed = owner.current_case_alias(workload, case_id)
        assert owner.validate_current_case_ownership(
            workload_id=workload,
            case_id=case_id,
            expected_stable_case_alias=stable,
            observed_case_alias=observed,
        ) == observed


def _corpus_with_unrelated_workload_drift():
    """Mutate only an UNRELATED workload's case so the global digest moves."""

    corpus = deepcopy(step8o.load_fixture_case_corpus())
    unrelated = next(
        case
        for case in corpus["cases"]
        if case["workload_id"] == "job_fit_evaluation"
    )
    unrelated["supported_evidence_tokens"] = list(
        unrelated.get("supported_evidence_tokens", [])
    ) + ["step14_unrelated_drift_token"]
    return corpus


def test_step14_unrelated_workload_drift_does_not_invalidate_the_canary():
    drifted = _corpus_with_unrelated_workload_drift()
    assert step8o.fixture_case_corpus_sha256(drifted) != (
        step8o.fixture_case_corpus_sha256()
    )
    for workload, case_id, stable in STEP14_TARGETS:
        if workload == "job_fit_evaluation":
            continue
        observed = owner.current_case_alias(workload, case_id, corpus=drifted)
        # The raw alias genuinely moved because the global digest moved...
        assert observed != owner.current_case_alias(workload, case_id)
        # ...yet current ownership still validates the same approved case.
        assert owner.validate_current_case_ownership(
            workload_id=workload,
            case_id=case_id,
            expected_stable_case_alias=stable,
            observed_case_alias=observed,
            corpus=drifted,
        ) == observed


def test_step14_rejects_changed_case_id():
    workload, case_id, stable = STEP14_TARGETS[0]
    with pytest.raises(ValueError):
        owner.validate_current_case_ownership(
            workload_id=workload,
            case_id="skill_extraction_some_other_case_v1",
            expected_stable_case_alias=stable,
            observed_case_alias=owner.current_case_alias(workload, case_id),
        )


def test_step14_rejects_changed_workload_id():
    workload, case_id, stable = STEP14_TARGETS[0]
    with pytest.raises(ValueError):
        owner.validate_current_case_ownership(
            workload_id="job_fit_evaluation",
            case_id=case_id,
            expected_stable_case_alias=stable,
            observed_case_alias=owner.current_case_alias(workload, case_id),
        )


def test_step14_rejects_substituted_stable_identity():
    workload, case_id, _stable = STEP14_TARGETS[0]
    with pytest.raises(ValueError):
        owner.validate_current_case_ownership(
            workload_id=workload,
            case_id=case_id,
            expected_stable_case_alias="case_" + "0" * 24,
            observed_case_alias=owner.current_case_alias(workload, case_id),
        )


def test_step14_rejects_observed_alias_from_a_different_case():
    workload, case_id, stable = STEP14_TARGETS[0]
    other_workload, other_case_id, _ = STEP14_TARGETS[1]
    with pytest.raises(ValueError):
        owner.validate_current_case_ownership(
            workload_id=workload,
            case_id=case_id,
            expected_stable_case_alias=stable,
            observed_case_alias=owner.current_case_alias(
                other_workload, other_case_id
            ),
        )


def test_step14_rejects_a_removed_target_case():
    workload, case_id, stable = STEP14_TARGETS[0]
    pruned = deepcopy(step8o.load_fixture_case_corpus())
    pruned["cases"] = [
        case for case in pruned["cases"] if case["case_id"] != case_id
    ]
    with pytest.raises(ValueError):
        owner.current_case_alias(workload, case_id, corpus=pruned)


def test_step14_target_case_semantic_change_still_moves_its_derived_alias():
    """A change to the target case itself remains visible, not absorbed."""

    workload, case_id, _stable = STEP14_TARGETS[0]
    mutated = deepcopy(step8o.load_fixture_case_corpus())
    target = next(
        case for case in mutated["cases"] if case["case_id"] == case_id
    )
    target["supported_evidence_tokens"] = list(
        target.get("supported_evidence_tokens", [])
    ) + ["step14_target_drift_token"]
    assert owner.current_case_alias(
        workload, case_id, corpus=mutated
    ) != owner.current_case_alias(workload, case_id)
