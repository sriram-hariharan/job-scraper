from copy import deepcopy

import pytest

from src.evaluation import controlled_groq_canary_run_004_plan as owner
from src.evaluation.controlled_provider_benchmark_plan import (
    build_transmittable_request_packet,
)
from src.evaluation.controlled_groq_canary_transport import (
    build_groq_chat_completion_arguments,
    conservative_local_input_size_bytes,
    validate_groq_chat_completion_arguments,
)


EXPECTED_WORKLOADS = ["jd_intelligence", "tailoring_generation"]
EXPECTED_BASE_KEYS = [
    "canary_8b167323a8667845ab0e26083b5294f5",
    "canary_969374f055f6d3a74a60a3e4ce6ee440",
]
EXPECTED_SIZES = [768, 641]


def test_exact_two_case_plan_and_default_off_authority():
    plan = owner.build_run_004_plan_contract()
    assert plan["run_identifier"] == "phase11-groq-canary-004"
    assert [r["workload_id"] for r in plan["schedule"]] == EXPECTED_WORKLOADS
    assert [r["execution_order"] for r in plan["schedule"]] == [1, 2]
    assert {(r["provider"], r["model"]) for r in plan["schedule"]} == {
        ("groq", "openai/gpt-oss-120b")
    }
    assert plan["request_bounds"] == {
        "maximum_total_requests": 2,
        "maximum_requests_per_provider_model": 2,
        "maximum_requests_per_case": 1,
        "serial_concurrency": 1,
        "automatic_expansion": False,
        "conditional_additional_calls": False,
    }
    assert plan["token_bounds"]["maximum_aggregate_input_tokens"] == 8192
    assert plan["token_bounds"]["maximum_aggregate_output_tokens"] == 2048
    assert plan["authority_invariants"]["provider_calls_allowed"] is False
    assert plan["authority_invariants"]["live_execution_authorized"] is False


def test_selected_fixtures_are_exactly_transmission_safe():
    _corpus, _benchmark, _plan, _engine, _fixture, rows, _canary = (
        owner._committed_ownership()
    )
    assert len(rows) == 2
    for item in rows:
        review = item["review"]
        assert review["eligible_for_later_controlled_transmission"] is True
        assert review["wholly_synthetic"] is True
        assert review["requires_additional_redaction"] is False
        assert review["human_approval_required"] is True
        assert all(review[field] is False for field in owner._REVIEW_FALSE_FIELDS)


def test_fresh_keys_are_unique_and_do_not_collide_with_prior_or_base_keys():
    plan = owner.build_run_004_plan_contract()
    keys = [r["schedule_key"] for r in plan["schedule"]]
    prohibited = set(EXPECTED_BASE_KEYS) | {
        "canary_run_002_f6a3df4b6caa7e82e229efc59bea7687",
        "canary_run_003_0ba1bf8c9270b5bbe777b6a27c05342cb906ab2e0e25609714a81dde9cf4fb46",
    }
    assert len(keys) == len(set(keys)) == 2
    assert all(k.startswith("canary_run_004_") and k not in prohibited for k in keys)


def test_historical_mapping_is_exact():
    plan = owner.build_run_004_plan_contract()
    assert [m["base_schedule_key"] for m in plan["base_transport_mapping"]] == EXPECTED_BASE_KEYS
    for row in plan["schedule"]:
        fresh, base, packet = owner.resolve_run_004_transport_inputs(
            row["schedule_key"]
        )
        assert fresh == row
        assert packet["case_alias"] == row["case_alias"]
        assert base["case_alias"] == row["case_alias"]


def test_current_semantic_transport_compatibility_is_exact():
    _corpus, _benchmark, current_plan, _engine, _fixture, rows, _canary = (
        owner._committed_ownership()
    )
    for owned, size in zip(rows, EXPECTED_SIZES):
        review = owned["review"]
        base = owned["base_transport_row"]
        packet = build_transmittable_request_packet(
            case_alias=review["case_alias"],
            provider=base["provider"],
            model=base["model"],
            plan=current_plan,
            live_execution_requested=False,
        )
        args = build_groq_chat_completion_arguments(
            packet=packet,
            scheduled=base,
            plan=current_plan,
        )
        assert validate_groq_chat_completion_arguments(
            args,
            packet=packet,
            scheduled=base,
            plan=current_plan,
        )
        assert conservative_local_input_size_bytes(args) == size


@pytest.mark.parametrize("mutation", ["key", "order", "workload", "provider", "model"])
def test_mapping_drift_is_rejected(mutation):
    plan = owner.build_run_004_plan_contract()
    if mutation == "key":
        plan["base_transport_mapping"][0]["base_schedule_key"] = "wrong"
    elif mutation == "order":
        plan["base_transport_mapping"].reverse()
    else:
        target = "base_transport_row"
        field = mutation
        plan["base_transport_mapping"][0][target][field] = "wrong"
    with pytest.raises(ValueError):
        owner.validate_run_004_plan_contract(plan)


def test_unknown_key_and_live_packet_are_rejected():
    with pytest.raises(ValueError):
        owner.resolve_run_004_transport_inputs("unknown")
    key = owner.build_run_004_plan_contract()["schedule"][0]["schedule_key"]
    with pytest.raises(ValueError):
        owner.build_run_004_transmittable_request_packet(
            schedule_key=key, live_execution_requested=True
        )


def test_digest_stability_and_caller_immutability():
    plan = owner.build_run_004_plan_contract()
    before = deepcopy(plan)
    assert owner.run_004_plan_sha256(plan) == owner.run_004_plan_sha256()
    assert plan == before
    plan["authority_invariants"]["provider_calls_allowed"] = True
    with pytest.raises(ValueError):
        owner.validate_run_004_plan_contract(plan)
