from copy import deepcopy

import pytest

from src.evaluation import controlled_groq_canary_run_005_plan as owner
from src.evaluation.controlled_groq_canary_transport import (
    build_groq_chat_completion_arguments,
    conservative_local_input_size_bytes,
    validate_groq_chat_completion_arguments,
)


PLAN_SHA = "57c46f89f3d53ab3e8a82f73a7fffdd9e5157db5459521f06950f74d679f5e62"
SCHEDULE_KEY = (
    "canary_run_005_"
    "a8a5414230a2a0da4a3bfb532df06b0dc4b17eb062076909a77c855d26bdae7c"
)
BASE_KEY = "canary_969374f055f6d3a74a60a3e4ce6ee440"


def test_exact_tailoring_only_plan_and_bounds_are_default_off():
    plan = owner.build_run_005_plan_contract()

    assert plan["run_identifier"] == "phase11-groq-canary-005"
    assert plan["target_case_aliases"] == ["case_ece85e9411ca52b579359fb8"]
    assert plan["target_workloads"] == ["tailoring_generation"]
    assert len(plan["schedule"]) == 1
    assert plan["schedule"][0] == {
        "execution_order": 1,
        "case_alias": "case_ece85e9411ca52b579359fb8",
        "workload_id": "tailoring_generation",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "timeout_seconds": 30,
        "fallback": False,
        "harness_retry_limit": 0,
        "provider_sdk_retry_limit": 0,
        "schedule_key": SCHEDULE_KEY,
    }
    assert plan["request_bounds"] == {
        "maximum_total_requests": 1,
        "maximum_requests_per_provider_model": 1,
        "maximum_requests_per_case": 1,
        "serial_concurrency": 1,
        "automatic_expansion": False,
        "conditional_additional_calls": False,
    }
    assert plan["token_bounds"]["maximum_input_tokens_per_request"] == 4096
    assert plan["token_bounds"]["maximum_output_tokens_per_request"] == 1024
    assert plan["token_bounds"]["maximum_aggregate_input_tokens"] == 4096
    assert plan["token_bounds"]["maximum_aggregate_output_tokens"] == 1024
    assert all(
        value is False
        for key, value in plan["authority_invariants"].items()
        if not key.endswith("_count")
    )


def test_selected_fixture_is_exactly_one_transmission_safe_synthetic_case():
    _corpus, _benchmark, _plan, _engine, _fixture, rows, _canary = (
        owner._committed_ownership()
    )

    assert len(rows) == 1
    review = rows[0]["review"]
    case = rows[0]["case"]
    assert review["case_alias"] == "case_ece85e9411ca52b579359fb8"
    assert review["eligible_for_later_controlled_transmission"] is True
    assert review["wholly_synthetic"] is True
    assert review["requires_additional_redaction"] is False
    assert review["human_approval_required"] is True
    assert all(review[field] is False for field in owner._REVIEW_FALSE_FIELDS)
    assert case["contains_personal_resume_content"] is False


def test_fresh_key_does_not_collide_with_prior_or_base_keys():
    prohibited = {
        "canary_run_002_f6a3df4b6caa7e82e229efc59bea7687",
        "canary_run_003_0ba1bf8c9270b5bbe777b6a27c05342cb906ab2e0e25609714a81dde9cf4fb46",
        "canary_run_004_db0b880f7fdc091fd113a70d6e277b5890770f2d9e8301de5e750b821bb8c3b9",
        "canary_run_004_c2f21c6c570b6361605978732fcdc603f2884c2764194e66b541a84ca4438b69",
        "canary_8b167323a8667845ab0e26083b5294f5",
        BASE_KEY,
    }
    assert SCHEDULE_KEY.startswith("canary_run_005_")
    assert SCHEDULE_KEY not in prohibited


def test_mapping_and_base_transport_reuse_are_exact():
    plan = owner.build_run_005_plan_contract()
    fresh, base, packet = owner.resolve_run_005_transport_inputs(SCHEDULE_KEY)

    assert fresh == plan["schedule"][0]
    assert base == plan["base_transport_mapping"][0]["base_transport_row"]
    assert base["schedule_key"] == BASE_KEY
    arguments = build_groq_chat_completion_arguments(
        packet=packet,
        scheduled=base,
        plan=owner._committed_ownership()[2],
    )
    assert validate_groq_chat_completion_arguments(
        arguments,
        packet=packet,
        scheduled=base,
        plan=owner._committed_ownership()[2],
    )
    assert conservative_local_input_size_bytes(arguments) == 641


@pytest.mark.parametrize(
    ("target", "field", "value"),
    [
        ("schedule", "workload_id", "skill_extraction"),
        ("schedule", "model", "openai/gpt-oss-20b"),
        ("mapping", "base_schedule_key", "wrong"),
        ("base", "provider", "openai"),
        ("base", "schedule_key", "wrong"),
    ],
)
def test_mapping_and_plan_drift_are_rejected(target, field, value):
    plan = owner.build_run_005_plan_contract()
    if target == "schedule":
        plan["schedule"][0][field] = value
    elif target == "mapping":
        plan["base_transport_mapping"][0][field] = value
    else:
        plan["base_transport_mapping"][0]["base_transport_row"][field] = value

    with pytest.raises(ValueError):
        owner.validate_run_005_plan_contract(plan)


def test_packet_unknown_key_live_request_and_forbidden_fields_are_rejected():
    with pytest.raises(ValueError):
        owner.resolve_run_005_transport_inputs("unknown")
    with pytest.raises(ValueError):
        owner.build_run_005_transmittable_request_packet(
            schedule_key=SCHEDULE_KEY,
            live_execution_requested=True,
        )
    packet = owner.build_run_005_transmittable_request_packet(
        schedule_key=SCHEDULE_KEY
    )
    packet["expected_output"] = {}
    with pytest.raises(ValueError):
        owner.validate_run_005_transmittable_request_packet(
            packet,
            schedule_key=SCHEDULE_KEY,
        )


def test_plan_digest_is_stable_and_callers_are_not_mutated():
    plan = owner.build_run_005_plan_contract()
    before = deepcopy(plan)

    assert owner.run_005_plan_sha256(plan) == PLAN_SHA
    assert owner.run_005_plan_sha256() == PLAN_SHA
    assert plan == before
