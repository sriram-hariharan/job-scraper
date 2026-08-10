from __future__ import annotations

import ast
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.evaluation import controlled_provider_benchmark_harness as harness
from src.evaluation import provider_fixture_benchmark as step8o
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    controlled_provider_benchmark_plan_sha256,
)
from src.evaluation.provider_benchmark_contract import (
    MODEL_ORDER,
    WORKLOAD_ORDER,
    provider_benchmark_contract_sha256,
)
from src.evaluation.provider_client_compatibility import (
    provider_client_compatibility_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/evaluation/controlled_provider_benchmark_harness.py"
)
CANARY_OWNER_PATH = (
    ROOT / "src/evaluation/controlled_groq_provider_canary.py"
)
RECOVERY_006_STATUS = (
    ROOT
    / "outputs/application_planning"
    / "phase11_controlled_priority_graph_verification_006_status.json"
)
EXECUTION_TIME = "2026-07-25T00:00:00Z"
STEP8M_SHA256 = (
    "e798f7d10f67c65c5d02f7531b54c3ce1b18ad0a6db5ec98505b4f1847f23ddd"
)
STEP8PA_PLAN_SHA256 = (
    "16c6d628b20f124322d7b06f45c2ac425f3dfca1b50b5df049a02a4d7b7e5675"
)


def _plan():
    return build_controlled_provider_benchmark_plan()


def _pricing():
    return harness.load_synthetic_pricing_fixture(
        execution_at_utc=EXECUTION_TIME
    )


def _authorization(plan=None, pricing=None):
    controlled_plan = _plan() if plan is None else plan
    pricing_payload = _pricing() if pricing is None else pricing
    return harness.load_synthetic_authorization_fixture(
        plan=controlled_plan,
        pricing=pricing_payload,
        execution_at_utc=EXECUTION_TIME,
    )


def _goldens_by_alias(plan=None):
    controlled_plan = _plan() if plan is None else plan
    corpus = step8o.load_fixture_case_corpus()
    return {
        review["case_alias"]: deepcopy(case["expected_output"])
        for case, review in zip(
            corpus["cases"],
            controlled_plan["transmission_review"],
        )
        if review["eligible_for_later_controlled_transmission"]
    }


class FakeGoldenTransport:
    def __init__(self, plan=None):
        self.goldens = _goldens_by_alias(plan)
        self.calls = []
        self.active = 0
        self.maximum_active = 0

    def __call__(self, request, timeout_seconds):
        self.active += 1
        self.maximum_active = max(self.maximum_active, self.active)
        self.calls.append(
            (
                request["case_alias"],
                request["provider"],
                request["model"],
                timeout_seconds,
                request["fallback"],
            )
        )
        result = {
            "normalized_output": deepcopy(
                self.goldens[request["case_alias"]]
            ),
            "provider": request["provider"],
            "model": request["model"],
            "latency_ms": 1,
            "input_token_count": 2,
            "output_token_count": 3,
            "provider_outcome_category": "success",
        }
        self.active -= 1
        return result


def _dry_run(
    *,
    plan=None,
    authorization=None,
    pricing=None,
    transport=None,
    **kwargs,
):
    controlled_plan = _plan() if plan is None else plan
    pricing_payload = _pricing() if pricing is None else pricing
    authorization_payload = (
        _authorization(controlled_plan, pricing_payload)
        if authorization is None
        else authorization
    )
    execution_transport = (
        FakeGoldenTransport(controlled_plan)
        if transport is None
        else transport
    )
    return harness.run_controlled_provider_benchmark(
        plan=controlled_plan,
        authorization=authorization_payload,
        pricing=pricing_payload,
        transport=execution_transport,
        execution_at_utc=EXECUTION_TIME,
        **kwargs,
    )


def _execute(
    *,
    plan=None,
    authorization=None,
    pricing=None,
    transport=None,
    prior_checkpoint=None,
    maximum_schedule_items=None,
):
    controlled_plan = _plan() if plan is None else plan
    pricing_payload = _pricing() if pricing is None else pricing
    authorization_payload = (
        _authorization(controlled_plan, pricing_payload)
        if authorization is None
        else authorization
    )
    execution_transport = (
        FakeGoldenTransport(controlled_plan)
        if transport is None
        else transport
    )
    return harness.execute_schedule_with_fake_transport(
        plan=controlled_plan,
        authorization=authorization_payload,
        pricing=pricing_payload,
        transport=execution_transport,
        execution_at_utc=EXECUTION_TIME,
        prior_checkpoint=prior_checkpoint,
        maximum_schedule_items=maximum_schedule_items,
    )


def _rehash_pricing(pricing):
    pricing["pricing_table_sha256"] = harness.pricing_table_sha256(pricing)
    return pricing


def test_harness_version_is_exact_and_default_off():
    contract = harness.build_controlled_benchmark_harness_contract()

    assert contract["harness_version"] == (
        "controlled-provider-benchmark-harness-v1"
    )
    assert contract["controls"]["live_execution_default"] is False
    assert contract["controls"]["real_transport_authorized"] is False


def test_plan_cases_graders_and_candidates_are_consumed_from_prior_owners():
    contract = harness.build_controlled_benchmark_harness_contract()
    plan = _plan()

    assert contract["step8pa_plan_sha256"] == (
        controlled_provider_benchmark_plan_sha256(plan)
    )
    assert contract["step8o_engine_sha256"] == plan["step8o_engine_sha256"]
    assert [
        (row["provider"], row["model"])
        for row in contract["candidate_definitions"]
    ] == list(MODEL_ORDER)
    assert contract["workload_order"] == list(WORKLOAD_ORDER)


def test_gemini_is_rejected_and_absent():
    contract = harness.build_controlled_benchmark_harness_contract()

    assert all(
        row["provider"] != "gemini"
        for row in contract["candidate_definitions"]
    )
    pricing = _pricing()
    pricing["prices"][0]["provider"] = "gemini"
    _rehash_pricing(pricing)
    with pytest.raises(ValueError, match="provider/model set"):
        harness.validate_operator_approved_pricing(
            pricing,
            execution_at_utc=EXECUTION_TIME,
        )


def test_harness_contract_has_no_winner_route_or_production_choice():
    serialized = harness.serialize_controlled_benchmark_harness_contract()

    for forbidden in (
        '"recommended_route"',
        '"selected_model"',
        '"selected_provider"',
        '"selected_winner"',
        '"winning_model"',
    ):
        assert forbidden not in serialized.lower()


def test_valid_synthetic_authorization_passes_exact_harness_validation():
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)

    assert harness.validate_harness_operator_authorization(
        authorization,
        plan=plan,
        pricing=pricing,
        execution_at_utc=EXECUTION_TIME,
    )


def test_absent_authorization_fails_before_transport():
    transport = FakeGoldenTransport()
    with pytest.raises(ValueError, match="authorization is required"):
        harness.run_controlled_provider_benchmark(
            plan=_plan(),
            authorization=None,
            pricing=_pricing(),
            transport=transport,
            execution_at_utc=EXECUTION_TIME,
        )
    assert transport.calls == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value.pop("operator_approved"),
            "exact harness schema",
        ),
        (
            lambda value: value.update(
                {"expires_at_utc": "2026-01-02T00:00:00Z"}
            ),
            "expired",
        ),
        (
            lambda value: value.update(
                {"valid_from_utc": "2026-12-01T00:00:00Z"}
            ),
            "not yet valid",
        ),
        (
            lambda value: value.update({"benchmark_plan_sha256": "0" * 64}),
            "plan hash mismatch",
        ),
        (
            lambda value: value.update({"case_corpus_sha256": "0" * 64}),
            "corpus hash mismatch",
        ),
        (
            lambda value: value["approved_candidate_pairs"][0].update(
                {"model": "gpt-5.1"}
            ),
            "provider/model scope",
        ),
        (
            lambda value: value["approved_case_aliases"].pop(),
            "case scope",
        ),
        (
            lambda value: value["approved_case_aliases"].append(
                "case_" + "f" * 24
            ),
            "case scope",
        ),
        (
            lambda value: value.update({"maximum_request_count": 27}),
            "request budget",
        ),
        (
            lambda value: value["token_budgets"].update(
                {"maximum_total_observed_input_tokens": 1}
            ),
            "token budget",
        ),
        (
            lambda value: value.pop("maximum_total_observed_cost"),
            "exact harness schema",
        ),
        (
            lambda value: value.update({"fallback": True}),
            "fallback",
        ),
        (
            lambda value: value.update({"gemini_allowed": True}),
            "Gemini",
        ),
        (
            lambda value: value.update(
                {"production_activation_allowed": True}
            ),
            "production activation",
        ),
        (
            lambda value: value["approved_request_matrix"].pop(),
            "request matrix",
        ),
        (
            lambda value: value[
                "maximum_requests_per_provider_model"
            ].update({"groq/openai/gpt-oss-20b": 99}),
            "provider/model request bounds",
        ),
        (
            lambda value: value.update({"maximum_requests_per_case": 99}),
            "per-case request bound",
        ),
    ],
)
def test_authorization_failures_leave_transport_unentered(mutation, message):
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)
    mutation(authorization)
    transport = FakeGoldenTransport(plan)

    with pytest.raises(ValueError, match=message):
        harness.run_controlled_provider_benchmark(
            plan=plan,
            authorization=authorization,
            pricing=pricing,
            transport=transport,
            execution_at_utc=EXECUTION_TIME,
        )
    assert transport.calls == []


def test_valid_synthetic_pricing_passes_and_hashes_exactly():
    pricing = _pricing()

    assert harness.validate_operator_approved_pricing(
        pricing,
        execution_at_utc=EXECUTION_TIME,
    )
    assert pricing["pricing_table_sha256"] == (
        harness.pricing_table_sha256(pricing)
    )


@pytest.mark.parametrize(
    ("mutation", "message", "rehash"),
    [
        (
            lambda value: value["prices"].pop(),
            "provider/model set",
            True,
        ),
        (
            lambda value: value["prices"].append(
                deepcopy(value["prices"][0])
            ),
            "provider/model set",
            True,
        ),
        (
            lambda value: value["prices"][0].update(
                {"input_price_per_million_tokens": 0}
            ),
            "input price must be positive",
            True,
        ),
        (
            lambda value: value["prices"][0].update(
                {"output_price_per_million_tokens": -1}
            ),
            "output price must be positive",
            True,
        ),
        (
            lambda value: value.update(
                {"expires_at_utc": "2026-01-02T00:00:00Z"}
            ),
            "expired",
            True,
        ),
        (
            lambda value: value.update({"operator_approved": False}),
            "operator approval",
            True,
        ),
        (
            lambda value: value.update({"currency": "SYN"}),
            "currency",
            True,
        ),
        (
            lambda value: value.update({"pricing_table_sha256": "0" * 64}),
            "hash mismatch",
            False,
        ),
    ],
)
def test_pricing_failures_leave_transport_unentered(
    mutation, message, rehash
):
    plan = _plan()
    pricing = _pricing()
    mutation(pricing)
    if rehash:
        _rehash_pricing(pricing)
    authorization = _authorization(plan, _pricing())
    transport = FakeGoldenTransport(plan)

    with pytest.raises(ValueError, match=message):
        harness.run_controlled_provider_benchmark(
            plan=plan,
            authorization=authorization,
            pricing=pricing,
            transport=transport,
            execution_at_utc=EXECUTION_TIME,
        )
    assert transport.calls == []


def test_exact_44_key_schedule_is_deterministic_and_unique():
    plan = _plan()
    authorization = _authorization(plan, _pricing())
    first = harness.build_execution_schedule(
        plan=plan,
        authorization=authorization,
    )
    second = harness.build_execution_schedule(
        plan=plan,
        authorization=authorization,
    )

    assert first == second
    assert len(first) == 44
    assert len({row["schedule_key"] for row in first}) == 44
    assert len(
        {
            (row["case_alias"], row["provider"], row["model"])
            for row in first
        }
    ) == 44


def test_schedule_model_counts_are_exact_and_include_gpt_5_1():
    plan = _plan()
    schedule = harness.build_execution_schedule(
        plan=plan,
        authorization=_authorization(plan, _pricing()),
    )
    counts = {
        pair: sum(
            row["provider"] == pair[0] and row["model"] == pair[1]
            for row in schedule
        )
        for pair in MODEL_ORDER
    }

    assert counts == {
        ("groq", "openai/gpt-oss-20b"): 12,
        ("groq", "openai/gpt-oss-120b"): 10,
        ("openai", "gpt-5-mini"): 12,
        ("openai", "gpt-5.1"): 10,
    }


def test_schedule_per_case_bound_and_serial_concurrency_are_exact():
    plan = _plan()
    authorization = _authorization(plan, _pricing())
    schedule = harness.build_execution_schedule(
        plan=plan,
        authorization=authorization,
    )
    aliases = {row["case_alias"] for row in schedule}

    assert max(
        sum(row["case_alias"] == alias for row in schedule)
        for alias in aliases
    ) == authorization["maximum_requests_per_case"] == 4
    assert harness.build_controlled_benchmark_harness_contract()[
        "controls"
    ]["serial_concurrency"] == 1


def test_duplicate_schedule_key_is_rejected():
    plan = _plan()
    authorization = _authorization(plan, _pricing())
    schedule = harness.build_execution_schedule(
        plan=plan,
        authorization=authorization,
    )
    schedule[1] = deepcopy(schedule[0])

    with pytest.raises(ValueError, match="differs|duplicate"):
        harness.validate_execution_schedule(
            schedule,
            plan=plan,
            authorization=authorization,
        )


def test_unauthorized_schedule_difference_is_rejected():
    plan = _plan()
    authorization = _authorization(plan, _pricing())
    schedule = harness.build_execution_schedule(
        plan=plan,
        authorization=authorization,
    )
    schedule[0]["model"] = "gpt-5.1"

    with pytest.raises(ValueError, match="differs"):
        harness.validate_execution_schedule(
            schedule,
            plan=plan,
            authorization=authorization,
        )


def test_dry_run_validates_but_makes_zero_transport_calls():
    transport = FakeGoldenTransport()
    summary = _dry_run(transport=transport)

    assert summary["schedule_count"] == 44
    assert summary["transport_calls"] == 0
    assert summary["live_execution"] is False
    assert summary["winner_selected"] is False
    assert summary["production_activation"] is False
    assert transport.calls == []


def test_dry_run_requires_an_explicit_transport_without_entering_it():
    with pytest.raises(ValueError, match="explicit execution transport"):
        harness.run_controlled_provider_benchmark(
            plan=_plan(),
            authorization=_authorization(),
            pricing=_pricing(),
            transport=None,
            execution_at_utc=EXECUTION_TIME,
        )


def test_live_execution_is_rejected_without_entering_transport():
    plan = _plan()
    transport = FakeGoldenTransport(plan)

    with pytest.raises(ValueError, match="not authorized"):
        _dry_run(plan=plan, transport=transport, live_execution=True)
    assert transport.calls == []


def test_fake_transport_executes_full_matrix_once_per_key_and_serially():
    plan = _plan()
    transport = FakeGoldenTransport(plan)
    result = _execute(plan=plan, transport=transport)

    assert result["transport_calls"] == 44
    assert len(transport.calls) == 44
    assert len(set(transport.calls)) == 44
    assert transport.maximum_active == 1
    assert len(result["checkpoint"]["completed_schedule_keys"]) == 44
    assert result["checkpoint"]["stop_reason"] is None


def test_fake_requests_preserve_fallback_false_timeout_and_no_retry():
    plan = _plan()
    transport = FakeGoldenTransport(plan)
    result = _execute(
        plan=plan,
        transport=transport,
        maximum_schedule_items=1,
    )

    assert transport.calls[0][3:] == (30, False)
    assert result["checkpoint"]["authority_invariants"][
        "fallback_activation_count"
    ] == 0
    assert result["checkpoint"]["authority_invariants"]["retry_count"] == 0


def test_ambiguous_timeout_is_called_once_and_not_retried():
    class Ambiguous:
        def __init__(self):
            self.calls = 0

        def __call__(self, request, timeout_seconds):
            self.calls += 1
            raise harness.AmbiguousTransportTimeout()

    transport = Ambiguous()
    result = _execute(transport=transport)

    assert transport.calls == 1
    assert result["transport_calls"] == 1
    assert result["checkpoint"]["stop_reason"] == "ambiguous_timeout"
    assert len(result["checkpoint"]["ambiguous_schedule_keys"]) == 1
    assert result["checkpoint"]["authority_invariants"]["retry_count"] == 0


def test_ambiguous_checkpoint_key_is_skipped_on_explicit_resume():
    plan = _plan()

    class Ambiguous:
        def __call__(self, request, timeout_seconds):
            raise harness.AmbiguousTransportTimeout()

    first = _execute(plan=plan, transport=Ambiguous())
    ambiguous_key = first["checkpoint"]["ambiguous_schedule_keys"][0]
    transport = FakeGoldenTransport(plan)
    resumed = _execute(
        plan=plan,
        transport=transport,
        prior_checkpoint=first["checkpoint"],
        maximum_schedule_items=1,
    )

    assert ambiguous_key in resumed["checkpoint"]["ambiguous_schedule_keys"]
    assert resumed["transport_calls"] == 2
    assert len(transport.calls) == 1
    schedule = harness.build_execution_schedule(
        plan=plan,
        authorization=_authorization(plan, _pricing()),
    )
    ambiguous_row = next(
        row for row in schedule if row["schedule_key"] == ambiguous_key
    )
    assert transport.calls[0][:3] != (
        ambiguous_row["case_alias"],
        ambiguous_row["provider"],
        ambiguous_row["model"],
    )


def test_completed_checkpoint_key_is_not_repeated_on_resume():
    plan = _plan()
    first_transport = FakeGoldenTransport(plan)
    first = _execute(
        plan=plan,
        transport=first_transport,
        maximum_schedule_items=1,
    )
    completed_key = first["checkpoint"]["completed_schedule_keys"][0]
    second_transport = FakeGoldenTransport(plan)
    resumed = _execute(
        plan=plan,
        transport=second_transport,
        prior_checkpoint=first["checkpoint"],
        maximum_schedule_items=1,
    )

    assert completed_key in resumed["checkpoint"]["completed_schedule_keys"]
    assert resumed["transport_calls"] == 2
    assert second_transport.calls[0] != first_transport.calls[0]


def test_definitive_failure_stops_without_retry():
    class Definitive:
        def __init__(self):
            self.calls = 0

        def __call__(self, request, timeout_seconds):
            self.calls += 1
            raise harness.DefinitiveTransportFailure()

    transport = Definitive()
    result = _execute(transport=transport)

    assert transport.calls == 1
    assert result["checkpoint"]["stop_reason"] == (
        "definitive_transport_failure"
    )
    assert len(result["checkpoint"]["blocked_schedule_keys"]) == 1


def test_unknown_provider_exception_stops_without_continuation():
    class Unknown:
        def __init__(self):
            self.calls = 0

        def __call__(self, request, timeout_seconds):
            self.calls += 1
            raise RuntimeError("bounded synthetic failure")

    transport = Unknown()
    result = _execute(transport=transport)

    assert transport.calls == 1
    assert result["checkpoint"]["stop_reason"] == "unknown_provider_outcome"
    assert len(result["checkpoint"]["blocked_schedule_keys"]) == 1


def test_provider_model_mismatch_stops_before_grading():
    base = FakeGoldenTransport()

    def mismatch(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result["provider"] = "openai"
        result["model"] = "gpt-5-mini"
        return result

    result = _execute(transport=mismatch)

    assert result["transport_calls"] == 1
    assert result["checkpoint"]["stop_reason"] == "provider_model_mismatch"
    assert result["checkpoint"]["grading_summaries"] == []


def test_request_budget_never_exceeds_exact_authorized_matrix():
    result = _execute()

    assert result["transport_calls"] == 44
    assert result["transport_calls"] == _authorization()[
        "maximum_request_count"
    ]
    assert all(
        value <= _authorization()[
            "maximum_requests_per_provider_model"
        ][key]
        for key, value in result["checkpoint"]["aggregate_usage"][
            "by_model"
        ].items()
    )


def test_per_request_token_ceiling_stops_before_a_second_call():
    base = FakeGoldenTransport()

    def too_many_tokens(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result["input_token_count"] = 4097
        return result

    result = _execute(transport=too_many_tokens)

    assert result["transport_calls"] == 1
    assert result["checkpoint"]["stop_reason"] == "token_budget_exceeded"
    assert len(result["checkpoint"]["blocked_schedule_keys"]) == 1


@pytest.mark.parametrize("missing_field", ["input_token_count", "output_token_count"])
def test_missing_usage_stops_and_blocks_cost_comparison(missing_field):
    base = FakeGoldenTransport()

    def missing_usage(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result[missing_field] = None
        return result

    result = _execute(transport=missing_usage)

    assert result["transport_calls"] == 1
    assert result["checkpoint"]["stop_reason"] == "missing_usage_metadata"
    assert result["result_packets"] == []


def test_cost_ceiling_stops_before_a_second_call():
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)
    authorization["maximum_observed_cost_per_model"] = {
        key: 0.000000000001
        for key in authorization["maximum_observed_cost_per_model"]
    }
    authorization["maximum_total_observed_cost"] = 0.000000000001
    result = _execute(
        plan=plan,
        pricing=pricing,
        authorization=authorization,
    )

    assert result["transport_calls"] == 1
    assert result["checkpoint"]["stop_reason"] == "cost_ceiling_exceeded"
    assert len(result["checkpoint"]["blocked_schedule_keys"]) == 1


def test_observed_cost_calculation_is_deterministic():
    pricing = _pricing()
    first = harness._observed_cost(
        provider="groq",
        model="openai/gpt-oss-20b",
        input_tokens=2,
        output_tokens=3,
        pricing=pricing,
    )
    second = harness._observed_cost(
        provider="groq",
        model="openai/gpt-oss-20b",
        input_tokens=2,
        output_tokens=3,
        pricing=deepcopy(pricing),
    )
    row = pricing["prices"][0]
    expected = (
        Decimal(2) * Decimal(str(row["input_price_per_million_tokens"]))
        + Decimal(3) * Decimal(str(row["output_price_per_million_tokens"]))
    ) / Decimal(1_000_000)

    assert Decimal(str(first)) == Decimal(str(second))
    assert Decimal(str(first)) == expected.quantize(
        Decimal("0.000000000001")
    )


def test_latency_beyond_timeout_is_ambiguous_and_not_retried():
    base = FakeGoldenTransport()

    def slow(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result["latency_ms"] = 30001
        return result

    result = _execute(transport=slow)

    assert result["transport_calls"] == 1
    assert result["checkpoint"]["stop_reason"] == "ambiguous_timeout"
    assert len(result["checkpoint"]["ambiguous_schedule_keys"]) == 1


def test_normalized_result_packets_match_step8p_allowlist_and_step8o_grades():
    result = _execute(maximum_schedule_items=1)
    packet = result["result_packets"][0]
    summary = result["checkpoint"]["grading_summaries"][0]

    assert set(packet) == set(
        _plan()["result_packet_schema"]["allowlisted_fields"]
    )
    assert packet["schema_valid"] is True
    assert packet["normalization_succeeded"] is True
    assert packet["fallback_used"] is False
    assert packet["retry_count"] == 0
    assert summary["quality_gate_passed"] is True
    assert all(value == 0 for value in summary["hard_failures"].values())


def test_every_workload_is_graded_by_full_fake_matrix():
    result = _execute()
    summaries = result["checkpoint"]["grading_summaries"]

    assert {row["workload_id"] for row in summaries} == set(WORKLOAD_ORDER)
    assert len(summaries) == 44
    assert all(row["quality_gate_passed"] for row in summaries)


def test_schema_failure_stops_immediately():
    base = FakeGoldenTransport()

    def invalid_schema(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result["normalized_output"].pop(
            next(iter(result["normalized_output"]))
        )
        return result

    result = _execute(transport=invalid_schema)

    assert result["transport_calls"] == 1
    assert result["checkpoint"]["stop_reason"] == "hard_safety_failure"
    assert result["checkpoint"]["grading_summaries"][0][
        "schema_valid"
    ] is False
    assert result["result_packets"] == []


def test_unsupported_claim_and_hallucination_stop_immediately():
    base = FakeGoldenTransport()

    def unsupported(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result["normalized_output"]["required_skills"].append(
            "synthetic_unsupported_claim"
        )
        return result

    result = _execute(transport=unsupported)
    hard = result["checkpoint"]["grading_summaries"][0]["hard_failures"]

    assert result["checkpoint"]["stop_reason"] == "hard_safety_failure"
    assert hard["unsupported_claim"] > 0
    assert hard["hallucination"] > 0
    assert result["transport_calls"] == 1


def test_deterministic_authority_mutation_stops_immediately():
    base = FakeGoldenTransport()

    def authority_mutation(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result["normalized_output"]["mutation_authorized"] = True
        return result

    result = _execute(transport=authority_mutation)
    hard = result["checkpoint"]["grading_summaries"][0]["hard_failures"]

    assert result["checkpoint"]["stop_reason"] == "hard_safety_failure"
    assert hard["deterministic_authority_mutation"] == 1
    assert result["result_packets"] == []


@pytest.mark.parametrize(
    ("outcome", "stop_reason"),
    [
        ("application_action", "application_action"),
        ("ats_action", "ats_action"),
        ("raw_response_persistence", "raw_response_persistence"),
        ("fallback_attempt", "fallback_attempted"),
        ("retry_attempt", "retry_attempted"),
        ("unknown_provider_outcome", "unknown_provider_outcome"),
        ("definitive_failure", "definitive_transport_failure"),
    ],
)
def test_bounded_provider_outcome_hard_failures_stop(
    outcome, stop_reason
):
    base = FakeGoldenTransport()

    def hard_outcome(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result["provider_outcome_category"] = outcome
        return result

    result = _execute(transport=hard_outcome)

    assert result["transport_calls"] == 1
    assert result["checkpoint"]["stop_reason"] == stop_reason
    assert len(result["checkpoint"]["blocked_schedule_keys"]) == 1
    assert result["checkpoint"]["completed_schedule_keys"] == []


def test_hard_failure_key_is_not_repeated_on_resume():
    plan = _plan()
    base = FakeGoldenTransport(plan)

    def unsupported(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result["normalized_output"]["required_skills"].append(
            "synthetic_unsupported_claim"
        )
        return result

    first = _execute(plan=plan, transport=unsupported)
    blocked_key = first["checkpoint"]["blocked_schedule_keys"][0]
    resumed_transport = FakeGoldenTransport(plan)
    resumed = _execute(
        plan=plan,
        transport=resumed_transport,
        prior_checkpoint=first["checkpoint"],
        maximum_schedule_items=1,
    )

    assert blocked_key in resumed["checkpoint"]["blocked_schedule_keys"]
    assert resumed["transport_calls"] == 2
    assert len(resumed_transport.calls) == 1
    schedule = harness.build_execution_schedule(
        plan=plan,
        authorization=_authorization(plan, _pricing()),
    )
    blocked_row = next(
        row for row in schedule if row["schedule_key"] == blocked_key
    )
    assert resumed_transport.calls[0][:3] != (
        blocked_row["case_alias"],
        blocked_row["provider"],
        blocked_row["model"],
    )


def test_false_authority_declarations_are_safe_in_normalized_result():
    plan = _plan()
    corpus = step8o.load_fixture_case_corpus()
    manual_case = next(
        case
        for case in corpus["cases"]
        if case["workload_id"] == "manual_provider_preview"
    )
    assert manual_case["expected_output"].get("ats_authorized") is False

    result = _execute(plan=plan)
    manual_summaries = [
        row
        for row in result["checkpoint"]["grading_summaries"]
        if row["workload_id"] == "manual_provider_preview"
    ]
    assert manual_summaries
    assert all(row["quality_gate_passed"] for row in manual_summaries)


def test_true_authority_declaration_is_rejected_by_result_contract():
    plan = _plan()
    result = _execute(plan=plan, maximum_schedule_items=1)
    packet = result["result_packets"][0]
    packet["normalized_output"]["application_authorized"] = True

    from src.evaluation.controlled_provider_benchmark_plan import (
        validate_redacted_result_packet,
    )

    with pytest.raises(ValueError, match="authoritative action"):
        validate_redacted_result_packet(packet)


def test_no_model_winner_or_production_activation_is_emitted():
    result = _execute(maximum_schedule_items=1)
    checkpoint = result["checkpoint"]

    assert result["winner_selected"] is False
    assert result["production_activation"] is False
    assert checkpoint["authority_invariants"]["winner_selected"] is False
    assert checkpoint["authority_invariants"]["production_activation"] is False
    assert checkpoint["authority_invariants"]["mutation_count"] == 0
    assert checkpoint["authority_invariants"]["application_action_count"] == 0
    assert checkpoint["authority_invariants"]["ats_action_count"] == 0


def test_empty_checkpoint_schema_validates_and_is_canonical():
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)
    checkpoint = harness.build_empty_checkpoint(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )

    assert harness.validate_checkpoint(
        checkpoint,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    serialized = harness.serialize_checkpoint(
        checkpoint,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert serialized == json.dumps(
        json.loads(serialized),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def test_checkpoint_digest_is_stable():
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)
    checkpoint = _execute(
        plan=plan,
        pricing=pricing,
        authorization=authorization,
        maximum_schedule_items=1,
    )["checkpoint"]

    assert harness.checkpoint_sha256(
        checkpoint,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    ) == harness.checkpoint_sha256(
        deepcopy(checkpoint),
        plan=deepcopy(plan),
        authorization=deepcopy(authorization),
        pricing=deepcopy(pricing),
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("plan_sha256", "0" * 64, "plan hash"),
        ("corpus_sha256", "0" * 64, "corpus hash"),
        ("authorization_sha256", "0" * 64, "authorization hash"),
        ("pricing_sha256", "0" * 64, "pricing hash"),
    ],
)
def test_checkpoint_hash_mismatch_is_rejected(field, value, message):
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)
    checkpoint = harness.build_empty_checkpoint(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    checkpoint[field] = value

    with pytest.raises(ValueError, match=message):
        harness.validate_checkpoint(
            checkpoint,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )


@pytest.mark.parametrize(
    "field",
    [
        "raw_response",
        "prompt",
        "credential",
        "request_id",
        "headers",
        "reasoning_trace",
        "provider_error",
        "environment",
        "request_packet",
    ],
)
def test_checkpoint_prohibited_raw_fields_are_rejected(field):
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)
    checkpoint = harness.build_empty_checkpoint(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    checkpoint[field] = "synthetic"

    with pytest.raises(ValueError, match="schema|prohibited"):
        harness.validate_checkpoint(
            checkpoint,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )


def test_duplicate_completed_checkpoint_key_is_rejected():
    result = _execute(maximum_schedule_items=1)
    checkpoint = result["checkpoint"]
    checkpoint["completed_schedule_keys"].append(
        checkpoint["completed_schedule_keys"][0]
    )

    with pytest.raises(ValueError, match="completed_schedule_keys"):
        harness.validate_checkpoint(
            checkpoint,
            plan=_plan(),
            authorization=_authorization(),
            pricing=_pricing(),
        )


def test_checkpoint_missing_completed_key_evidence_is_rejected():
    result = _execute(maximum_schedule_items=1)
    checkpoint = result["checkpoint"]
    checkpoint["grading_summaries"] = []

    with pytest.raises(ValueError, match="missing completed-key evidence"):
        harness.validate_checkpoint(
            checkpoint,
            plan=_plan(),
            authorization=_authorization(),
            pricing=_pricing(),
        )


def test_checkpoint_inconsistent_aggregate_count_is_rejected():
    result = _execute(maximum_schedule_items=1)
    checkpoint = result["checkpoint"]
    checkpoint["aggregate_usage"]["transport_calls"] = 2

    with pytest.raises(ValueError, match="invocation counts"):
        harness.validate_checkpoint(
            checkpoint,
            plan=_plan(),
            authorization=_authorization(),
            pricing=_pricing(),
        )


def test_checkpoint_created_under_different_authorization_is_rejected():
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)
    checkpoint = harness.build_empty_checkpoint(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    changed = deepcopy(authorization)
    changed["maximum_total_observed_cost"] = 5.0

    with pytest.raises(ValueError, match="authorization hash"):
        harness.validate_checkpoint(
            checkpoint,
            plan=plan,
            authorization=changed,
            pricing=pricing,
        )


def test_result_artifact_serialization_excludes_raw_material():
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)
    checkpoint = _execute(
        plan=plan,
        pricing=pricing,
        authorization=authorization,
        maximum_schedule_items=1,
    )["checkpoint"]
    artifact = harness.build_result_artifact(
        checkpoint=checkpoint,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    serialized = harness.serialize_result_artifact(
        artifact,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    ).lower()

    for forbidden in (
        '"raw_response"',
        '"prompt"',
        '"credential"',
        '"request_id"',
        '"reasoning_trace"',
        '"provider_error"',
        '"normalized_output"',
    ):
        assert forbidden not in serialized


def test_result_artifact_retention_and_permissions_are_exact():
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)
    checkpoint = harness.build_empty_checkpoint(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    policy = harness.build_result_artifact(
        checkpoint=checkpoint,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )["retention_policy"]

    assert policy == {
        "automatic_persistence": False,
        "ignored_artifact_only": True,
        "required_file_mode": "0600",
        "maximum_retention_days": 7,
        "operator_review_required": True,
        "deletion_required": True,
        "overwrite_allowed": False,
    }


def test_valid_ignored_result_path_is_accepted_without_creation(tmp_path):
    candidate = (
        tmp_path / "outputs/provider_benchmark/synthetic-result.json"
    )

    assert harness.validate_ignored_result_path(
        candidate,
        repository_root=tmp_path,
    ) == candidate
    assert not candidate.exists()


def test_result_path_traversal_is_rejected(tmp_path):
    candidate = (
        tmp_path
        / "outputs/provider_benchmark/../outside/synthetic-result.json"
    )

    with pytest.raises(ValueError, match="traversal"):
        harness.validate_ignored_result_path(
            candidate,
            repository_root=tmp_path,
        )


def test_result_path_outside_approved_directory_is_rejected(tmp_path):
    candidate = tmp_path / "outputs/other/synthetic-result.json"

    with pytest.raises(ValueError, match="outside"):
        harness.validate_ignored_result_path(
            candidate,
            repository_root=tmp_path,
        )


def test_result_path_symlink_escape_is_rejected(tmp_path):
    approved = tmp_path / "outputs/provider_benchmark"
    approved.parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    approved.symlink_to(outside, target_is_directory=True)
    candidate = approved / "synthetic-result.json"

    with pytest.raises(ValueError, match="outside|symlink"):
        harness.validate_ignored_result_path(
            candidate,
            repository_root=tmp_path,
        )


def test_result_path_overwrite_is_rejected(tmp_path):
    approved = tmp_path / "outputs/provider_benchmark"
    approved.mkdir(parents=True)
    candidate = approved / "synthetic-result.json"
    candidate.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="overwrite"):
        harness.validate_ignored_result_path(
            candidate,
            repository_root=tmp_path,
        )


def test_dry_run_validates_explicit_result_path_without_writing(tmp_path):
    candidate = (
        tmp_path / "outputs/provider_benchmark/synthetic-result.json"
    )
    summary = _dry_run(
        result_path=candidate,
        repository_root=tmp_path,
    )

    assert summary["transport_calls"] == 0
    assert not candidate.exists()


def test_harness_contract_digest_is_stable_and_canonical():
    first = harness.controlled_benchmark_harness_sha256()
    second = harness.controlled_benchmark_harness_sha256(
        harness.build_controlled_benchmark_harness_contract()
    )

    assert first == second
    assert len(first) == 64


def test_checkpoint_serialization_is_stable_across_fresh_process():
    plan = _plan()
    pricing = _pricing()
    authorization = _authorization(plan, pricing)
    checkpoint = harness.build_empty_checkpoint(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    expected = harness.checkpoint_sha256(
        checkpoint,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    script = (
        "from src.evaluation import controlled_provider_benchmark_harness as h;"
        f"p=h.load_synthetic_pricing_fixture(execution_at_utc={EXECUTION_TIME!r});"
        "q=h.load_synthetic_authorization_fixture("
        f"pricing=p,execution_at_utc={EXECUTION_TIME!r});"
        "c=h.build_empty_checkpoint("
        "plan=h.build_controlled_provider_benchmark_plan(),"
        "authorization=q,pricing=p);"
        "print(h.checkpoint_sha256("
        "c,plan=h.build_controlled_provider_benchmark_plan(),"
        "authorization=q,pricing=p))"
    )
    observed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(ROOT)},
    ).stdout.strip()

    assert observed == expected


def test_contract_schedule_and_execution_inputs_are_deep_copy_contained():
    plan = _plan()
    original = deepcopy(plan)
    contract = harness.build_controlled_benchmark_harness_contract(plan)
    authorization = _authorization(plan)
    schedule = harness.build_execution_schedule(
        plan=plan,
        authorization=authorization,
    )

    contract["candidate_definitions"][0]["provider"] = "changed"
    schedule[0]["provider"] = "changed"
    authorization["approved_case_aliases"].append("changed")
    assert plan == original
    assert harness.build_controlled_benchmark_harness_contract()[
        "candidate_definitions"
    ][0]["provider"] == MODEL_ORDER[0][0]


def test_harness_owner_has_no_live_provider_or_system_reach_imports():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    prohibited_roots = {
        "dotenv",
        "google",
        "groq",
        "httpx",
        "openai",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "subprocess",
        "threading",
        "urllib",
    }
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(prohibited_roots)


def test_harness_owner_has_no_environment_or_write_primitive_calls():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    prohibited_calls = {
        "dotenv_values",
        "getenv",
        "load_dotenv",
        "open",
        "putenv",
        "setdefault",
        "write_bytes",
        "write_text",
    }
    observed = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            observed.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            observed.add(node.func.attr)

    assert observed.isdisjoint(prohibited_calls)


def test_fresh_harness_import_does_not_reach_provider_clients_or_database():
    script = (
        "import json,sys;"
        "import src.evaluation.controlled_provider_benchmark_harness;"
        "blocked=('openai','groq','google.generativeai','dotenv',"
        "'src.ai.llm_client','psycopg','sqlalchemy');"
        "print(json.dumps([name for name in blocked if name in sys.modules]))"
    )
    observed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(ROOT)},
    ).stdout.strip()

    assert json.loads(observed) == []


def test_fake_execution_creates_no_repository_benchmark_artifact():
    output_root = ROOT / "outputs/provider_benchmark"
    before = (
        sorted(path.relative_to(ROOT).as_posix() for path in output_root.rglob("*"))
        if output_root.exists()
        else []
    )

    _execute(maximum_schedule_items=1)

    after = (
        sorted(path.relative_to(ROOT).as_posix() for path in output_root.rglob("*"))
        if output_root.exists()
        else []
    )
    assert after == before


def test_fake_matrix_authority_counts_remain_bounded_and_non_authoritative():
    result = _execute()
    authority = result["checkpoint"]["authority_invariants"]

    assert authority["provider_call_count"] == 44
    assert all(
        row["provider_call_count"] == 1
        for row in result["checkpoint"]["grading_summaries"]
    )
    assert authority["fallback_activation_count"] == 0
    assert authority["retry_count"] == 0
    assert authority["mutation_count"] == 0
    assert authority["application_action_count"] == 0
    assert authority["ats_action_count"] == 0
    assert authority["raw_response_persisted_count"] == 0


def test_steps_8l_through_8pa_digests_remain_stable():
    contract = harness.build_controlled_benchmark_harness_contract()

    assert provider_benchmark_contract_sha256() == (
        "5e39da6e518a4870a37aba10b1bac162ddd7dbb0bf20bb5cef7171598a4e5a52"
    )
    assert provider_client_compatibility_sha256() == STEP8M_SHA256
    assert step8o.provider_fixture_benchmark_sha256() == (
        "7a6463fc465d963633f82a18de0b067daab31dc387680b1d004e706c61a55c15"
    )
    assert step8o.fixture_case_corpus_sha256() == (
        "0ddc82e62745856c0d5d4d3f0efbe3fc86bd4e84e5da070f54f4ea635e74b05c"
    )
    assert controlled_provider_benchmark_plan_sha256() == (
        STEP8PA_PLAN_SHA256
    )
    assert contract["step8m_contract_sha256"] == STEP8M_SHA256


def test_recovery_006_status_remains_absent():
    assert not RECOVERY_006_STATUS.exists()


@pytest.mark.parametrize(
    "fixture_path",
    [
        harness.DEFAULT_AUTHORIZATION_PATH,
        harness.DEFAULT_PRICING_PATH,
    ],
)
def test_synthetic_execution_inputs_are_regular_non_symlink_files(fixture_path):
    assert fixture_path.is_file()
    assert not fixture_path.is_symlink()


def test_no_production_source_imports_or_calls_the_harness_owner():
    references = []
    for source_root in (ROOT / "src", ROOT / "main.py"):
        paths = (
            [source_root]
            if source_root.is_file()
            else list(source_root.rglob("*.py"))
        )
        for path in paths:
            if path in {OWNER_PATH, CANARY_OWNER_PATH}:
                continue
            text = path.read_text(encoding="utf-8")
            if "controlled_provider_benchmark_harness" in text:
                references.append(path.relative_to(ROOT).as_posix())

    assert references == [
        "src/evaluation/controlled_groq_canary_run_003_transport.py",
        "src/evaluation/controlled_openai_canary_transport.py",
        "src/evaluation/controlled_groq_canary_evidence_runtime.py",
        "src/evaluation/controlled_groq_tailoring_canary_transport.py",
        "src/evaluation/controlled_groq_canary_run_004_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_transport.py",
        "src/evaluation/controlled_groq_canary_run_005_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_run_003_evidence_runtime.py",
        "src/evaluation/controlled_provider_benchmark_evidence_runtime.py",
    ]
