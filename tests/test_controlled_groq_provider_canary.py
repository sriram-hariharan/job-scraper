from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.evaluation import controlled_groq_provider_canary as canary
from src.evaluation import controlled_provider_benchmark_harness as harness
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    controlled_provider_benchmark_plan_sha256,
)
from src.evaluation.provider_benchmark_contract import (
    MODEL_ORDER,
    provider_benchmark_contract_sha256,
)
from src.evaluation.provider_fixture_benchmark import (
    provider_fixture_benchmark_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/evaluation/controlled_groq_provider_canary.py"
)
RUNBOOK_PATH = ROOT / "docs/controlled_groq_provider_canary_runbook.md"
EXECUTION_TIME = "2026-07-25T00:00:00Z"
STEP8L_SHA256 = (
    "ba4e817f4e82f9df967011709a42bc7d2f22998f176f555cfee9dfc9e0071b98"
)
STEP8O_SHA256 = (
    "7a6463fc465d963633f82a18de0b067daab31dc387680b1d004e706c61a55c15"
)
STEP8PA_SHA256 = (
    "a3ef53ff992a2d1daf43f8fa9b0556202268d34e21f7611eb5de4d26e9abe6b6"
)
STEP8Q_SHA256 = (
    "eacf13521305689a0e7c7e3768c5e18c083308d30e6bb6b69f8d5cab1f125572"
)


def _contract():
    return canary.build_controlled_groq_canary_contract()


def _pricing():
    payload = canary.build_groq_pricing_template()
    payload.update(
        {
            "pricing_version": "synthetic-non-current-test-v1",
            "source_classification": "synthetic_non_current_test_only",
            "source_effective_at_utc": "2026-07-01T00:00:00Z",
            "valid_from_utc": "2026-07-01T00:00:00Z",
            "expires_at_utc": "2026-08-01T00:00:00Z",
            "currency": "USD",
            "operator_approved": True,
        }
    )
    for index, row in enumerate(payload["prices"], start=1):
        row["input_price_per_million_tokens"] = f"0.{index}123"
        row["output_price_per_million_tokens"] = f"0.{index}456"
    payload["pricing_table_sha256"] = canary.pricing_table_sha256(payload)
    return payload


def _rehash_pricing(payload):
    payload["pricing_table_sha256"] = canary.pricing_table_sha256(payload)
    return payload


def _authorization(pricing=None):
    pricing_payload = _pricing() if pricing is None else pricing
    payload = canary.build_operator_authorization_template()
    payload.update(
        {
            "maximum_total_observed_cost": "1.5",
            "valid_from_utc": "2026-07-01T00:00:00Z",
            "expires_at_utc": "2026-08-01T00:00:00Z",
            "pricing_table_sha256": canary.pricing_table_sha256(
                pricing_payload
            ),
            "operator_approved": True,
        }
    )
    for key in payload["maximum_observed_cost_per_model"]:
        payload["maximum_observed_cost_per_model"][key] = "1.0"
    return payload


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.active = 0
        self.maximum_active = 0

    def __call__(self, request, timeout_seconds):
        self.active += 1
        self.maximum_active = max(self.maximum_active, self.active)
        self.calls.append(
            (
                request["provider"],
                request["model"],
                timeout_seconds,
                request["fallback"],
            )
        )
        result = {
            "normalized_output": {"synthetic_status": "bounded"},
            "provider": request["provider"],
            "model": request["model"],
            "latency_ms": 1,
            "input_token_count": 2,
            "output_token_count": 3,
            "provider_outcome_category": "success",
        }
        self.active -= 1
        return result


def _valid_preflight(tmp_path, **overrides):
    pricing = _pricing()
    authorization = _authorization(pricing)
    (tmp_path / ".gitignore").write_text("outputs/\n", encoding="utf-8")
    kwargs = {
        "authorization": authorization,
        "pricing": pricing,
        "execution_at_utc": EXECUTION_TIME,
        "result_path": (
            tmp_path / "outputs/provider_benchmark/canary-result.json"
        ),
        "checkpoint_path": (
            tmp_path / "outputs/provider_benchmark/canary-checkpoint.json"
        ),
        "repository_root": tmp_path,
        "graph_verification_enabled": False,
        "recovery_006_present": False,
        "owned_process_count": 0,
        "prior_checkpoint": None,
        "live_execution": False,
    }
    kwargs.update(overrides)
    return canary.validate_live_canary_preflight(**kwargs)


def test_canary_version_is_exact():
    assert _contract()["canary_version"] == (
        "controlled-groq-provider-canary-v1"
    )


def test_candidate_registry_is_consumed_from_step8l():
    contract = _contract()
    expected = [
        {"provider": provider, "model": model}
        for provider, model in MODEL_ORDER
        if provider == "groq"
    ]

    assert contract["candidate_provider_models"] == expected
    assert contract["step8l_contract_sha256"] == (
        provider_benchmark_contract_sha256()
    )


def test_aliases_are_consumed_from_step8pa():
    plan = build_controlled_provider_benchmark_plan()
    aliases = {
        row["workload_id"]: row["case_alias"]
        for row in plan["transmission_review"]
        if row["eligible_for_later_controlled_transmission"]
    }

    assert all(
        row["case_alias"] == aliases[row["workload_id"]]
        for row in _contract()["schedule"]
    )


def test_step8q_harness_is_consumed():
    contract = _contract()

    assert contract["harness_version"] == harness.HARNESS_VERSION
    assert contract["harness_sha256"] == (
        harness.controlled_benchmark_harness_sha256()
    )


def test_candidate_set_is_exactly_two_groq_models():
    candidates = _contract()["candidate_provider_models"]

    assert len(candidates) == 2
    assert all(row["provider"] == "groq" for row in candidates)


@pytest.mark.parametrize(
    ("provider", "model"),
    [
        ("openai", "gpt-5-mini"),
        ("openai", "gpt-5.1"),
        ("gemini", "gemini-2.5-flash"),
        ("groq", "unknown-model"),
    ],
)
def test_unapproved_candidate_is_rejected(provider, model):
    contract = _contract()
    contract["candidate_provider_models"].append(
        {"provider": provider, "model": model}
    )

    with pytest.raises(ValueError, match="candidate set"):
        canary.validate_controlled_groq_canary_contract(contract)


def test_no_winner_route_or_production_choice_field_exists():
    serialized = canary.serialize_controlled_groq_canary_contract().lower()

    for field in (
        "selected_winner",
        "winner_selected",
        "recommended_route",
        "production_model_choice",
        "winning_model",
    ):
        assert field not in serialized


def test_schedule_count_is_exactly_four():
    assert len(_contract()["schedule"]) == 4


def test_schedule_has_two_calls_per_model():
    schedule = _contract()["schedule"]
    counts = {
        model: sum(1 for row in schedule if row["model"] == model)
        for _provider, model in MODEL_ORDER
        if _provider == "groq"
    }

    assert set(counts.values()) == {2}


@pytest.mark.parametrize(
    ("position", "workload_id", "candidate_index"),
    [
        (0, "skill_extraction", 0),
        (1, "grounded_rag_answer", 0),
        (2, "jd_intelligence", 1),
        (3, "tailoring_generation", 1),
    ],
)
def test_workload_model_assignment_is_exact(
    position, workload_id, candidate_index
):
    contract = _contract()
    expected = contract["candidate_provider_models"][candidate_index]
    row = contract["schedule"][position]

    assert row["workload_id"] == workload_id
    assert (row["provider"], row["model"]) == (
        expected["provider"],
        expected["model"],
    )


def test_every_scheduled_case_is_transmission_eligible():
    plan = build_controlled_provider_benchmark_plan()
    eligible = {
        row["case_alias"]
        for row in plan["transmission_review"]
        if row["eligible_for_later_controlled_transmission"]
    }

    assert {
        row["case_alias"] for row in _contract()["schedule"]
    }.issubset(eligible)


def test_aliases_and_schedule_order_are_deterministic():
    first = _contract()["schedule"]
    second = _contract()["schedule"]

    assert first == second
    assert [row["execution_order"] for row in first] == [1, 2, 3, 4]


def test_schedule_keys_are_unique_and_one_call_only():
    schedule = _contract()["schedule"]

    assert len({row["schedule_key"] for row in schedule}) == 4
    assert len(
        {
            (row["case_alias"], row["provider"], row["model"])
            for row in schedule
        }
    ) == 4


def test_concurrency_is_one_without_expansion():
    bounds = _contract()["request_bounds"]

    assert bounds["serial_concurrency"] == 1
    assert bounds["automatic_expansion"] is False
    assert bounds["conditional_additional_calls"] is False


def test_fallback_retry_and_timeout_bounds_are_exact():
    contract = _contract()
    stop = contract["stop_policy"]

    assert stop["fallback"] is False
    assert stop["harness_retry_limit"] == 0
    assert stop["provider_sdk_retry_limit"] == 0
    assert stop["timeout_seconds"] == 30


def test_token_ceilings_are_exact():
    bounds = _contract()["token_bounds"]

    assert bounds["maximum_input_tokens_per_request"] == 4096
    assert bounds["maximum_output_tokens_per_request"] == 1024
    assert bounds["maximum_aggregate_input_tokens"] == 16384
    assert bounds["maximum_aggregate_output_tokens"] == 4096


def test_observed_usage_is_required_and_estimation_prohibited():
    bounds = _contract()["token_bounds"]

    assert bounds["observed_usage_required"] is True
    assert bounds["missing_usage_estimation_allowed"] is False


def test_cost_policy_requires_observed_usage_approved_prices_and_ceilings():
    policy = _contract()["cost_policy"]

    assert policy["positive_per_model_dollar_ceilings_required"] is True
    assert policy["positive_total_dollar_ceiling_required"] is True
    assert policy["total_ceiling_not_greater_than_per_model_sum"] is True
    assert policy["validated_operator_approved_pricing_required"] is True
    assert policy["observed_input_output_usage_only"] is True
    assert policy["missing_usage_estimation_allowed"] is False
    assert policy["stop_before_next_call_on_ceiling"] is True
    assert policy["quality_gates_precede_cost_comparison"] is True


def test_ambiguous_completed_and_hard_failure_keys_cannot_resume():
    stop = _contract()["stop_policy"]

    assert stop["ambiguous_timeout"] == "outcome_unknown_no_retry"
    assert stop["resume_ambiguous_key"] is False
    assert stop["resume_completed_key"] is False
    assert stop["resume_hard_failure_key"] is False


def test_authorization_template_is_unapproved_and_incomplete():
    template = canary.build_operator_authorization_template()

    assert template["operator_approved"] is False
    assert template["valid_from_utc"] is None
    assert template["expires_at_utc"] is None
    assert template["pricing_table_sha256"] is None
    assert template["maximum_total_observed_cost"] is None


def test_authorization_template_has_no_price_values():
    template = canary.build_operator_authorization_template()

    assert all(
        value is None
        for value in template[
            "maximum_observed_cost_per_model"
        ].values()
    )


def test_authorization_template_fixture_matches_builder():
    assert canary.load_authorization_template_fixture() == (
        canary.build_operator_authorization_template()
    )


def test_valid_synthetic_authorization_passes():
    pricing = _pricing()

    assert canary.validate_operator_authorization(
        _authorization(pricing),
        pricing=pricing,
        execution_at_utc=EXECUTION_TIME,
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda row: row.update({"operator_approved": False}),
            "approval",
        ),
        (
            lambda row: row.pop("pricing_table_sha256"),
            "fields",
        ),
        (
            lambda row: row.update({"canary_sha256": "0" * 64}),
            "scope",
        ),
        (
            lambda row: row["candidate_provider_models"].append(
                {"provider": "openai", "model": "gpt-5-mini"}
            ),
            "scope",
        ),
        (
            lambda row: row["approved_schedule_keys"].pop(),
            "scope",
        ),
        (
            lambda row: row["approved_case_aliases"].pop(),
            "scope",
        ),
        (
            lambda row: row.update({"openai_allowed": True}),
            "scope",
        ),
        (
            lambda row: row.update({"gemini_allowed": True}),
            "scope",
        ),
        (
            lambda row: row.update(
                {"production_activation_allowed": True}
            ),
            "scope",
        ),
        (
            lambda row: row.update(
                {"application_authority_allowed": True}
            ),
            "scope",
        ),
        (
            lambda row: row.update({"ats_authority_allowed": True}),
            "scope",
        ),
        (
            lambda row: row.update({"fallback_allowed": True}),
            "scope",
        ),
        (
            lambda row: row.update({"retry_count": 1}),
            "scope",
        ),
        (
            lambda row: row.update(
                {"valid_from_utc": "2026-09-01T00:00:00Z"}
            ),
            "validity|expired|not yet",
        ),
        (
            lambda row: row.update(
                {"expires_at_utc": "2026-07-02T00:00:00Z"}
            ),
            "expired|not yet",
        ),
        (
            lambda row: row.update(
                {"maximum_total_observed_cost": None}
            ),
            "numeric",
        ),
        (
            lambda row: row.update(
                {"maximum_total_observed_cost": "3.0"}
            ),
            "exceeds",
        ),
    ],
)
def test_authorization_mutation_fails_closed(mutation, message):
    pricing = _pricing()
    authorization = _authorization(pricing)
    mutation(authorization)

    with pytest.raises((ValueError, KeyError), match=message):
        canary.validate_operator_authorization(
            authorization,
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
        )


def test_pricing_template_is_unapproved_incomplete_and_two_model():
    template = canary.build_groq_pricing_template()

    assert template["operator_approved"] is False
    assert template["pricing_version"] is None
    assert template["currency"] is None
    assert len(template["prices"]) == 2
    assert all(row["provider"] == "groq" for row in template["prices"])


def test_pricing_template_contains_no_price_values():
    template = canary.load_pricing_template_fixture()

    assert all(
        row["input_price_per_million_tokens"] is None
        and row["output_price_per_million_tokens"] is None
        for row in template["prices"]
    )


def test_valid_synthetic_non_current_pricing_passes():
    assert canary.validate_operator_approved_pricing(
        _pricing(),
        execution_at_utc=EXECUTION_TIME,
    )


@pytest.mark.parametrize(
    ("mutation", "message", "rehash"),
    [
        (
            lambda row: row["prices"].pop(),
            "exactly",
            True,
        ),
        (
            lambda row: row["prices"].append(
                {
                    "provider": "openai",
                    "model": "gpt-5-mini",
                    "input_price_per_million_tokens": "1",
                    "output_price_per_million_tokens": "1",
                }
            ),
            "exactly",
            True,
        ),
        (
            lambda row: row["prices"][0].update(
                {"input_price_per_million_tokens": "0"}
            ),
            "positive",
            True,
        ),
        (
            lambda row: row["prices"][0].update(
                {"output_price_per_million_tokens": "-1"}
            ),
            "positive",
            True,
        ),
        (
            lambda row: row["prices"][0].update(
                {"input_price_per_million_tokens": "invalid"}
            ),
            "numeric",
            True,
        ),
        (
            lambda row: row.update(
                {"expires_at_utc": "2026-07-02T00:00:00Z"}
            ),
            "expired",
            True,
        ),
        (
            lambda row: row.update({"operator_approved": False}),
            "approval",
            True,
        ),
        (
            lambda row: row.update({"currency": "OTHER"}),
            "currency",
            True,
        ),
        (
            lambda row: row.update({"pricing_table_sha256": "0" * 64}),
            "digest",
            False,
        ),
    ],
)
def test_pricing_mutation_fails_closed(mutation, message, rehash):
    pricing = _pricing()
    mutation(pricing)
    if rehash:
        _rehash_pricing(pricing)

    with pytest.raises(ValueError, match=message):
        canary.validate_operator_approved_pricing(
            pricing,
            execution_at_utc=EXECUTION_TIME,
        )


def test_preparation_preflight_passes_without_credential_status(tmp_path):
    result = _valid_preflight(tmp_path)

    assert result["credential_configuration_presence"] == (
        "not_checked_in_preparation"
    )
    assert result["live_transport_readiness"] is False
    assert result["execution_authorization"] is False
    assert result["live_execution"] is False
    assert not (
        tmp_path / "outputs/provider_benchmark/canary-result.json"
    ).exists()
    assert not (
        tmp_path / "outputs/provider_benchmark/canary-checkpoint.json"
    ).exists()


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"graph_verification_enabled": True}, "graph"),
        ({"recovery_006_present": True}, "recovery"),
        ({"owned_process_count": 1}, "process"),
        ({"prior_checkpoint": {"ambiguous_schedule_keys": ["bounded"]}}, "checkpoint"),
        ({"live_execution": True}, "live execution"),
    ],
)
def test_preflight_safety_mismatch_fails_closed(
    tmp_path, override, message
):
    with pytest.raises(ValueError, match=message):
        _valid_preflight(tmp_path, **override)


def test_preflight_rejects_same_result_and_checkpoint_path(tmp_path):
    shared = tmp_path / "outputs/provider_benchmark/shared.json"

    with pytest.raises(ValueError, match="differ"):
        _valid_preflight(
            tmp_path,
            result_path=shared,
            checkpoint_path=shared,
        )


def test_preflight_rejects_outside_path(tmp_path):
    with pytest.raises(ValueError, match="outside"):
        _valid_preflight(
            tmp_path,
            result_path=tmp_path / "outputs/other/result.json",
        )


def test_preflight_rejects_existing_result(tmp_path):
    target = tmp_path / "outputs/provider_benchmark/result.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="overwrite"):
        _valid_preflight(tmp_path, result_path=target)


def test_preflight_rejects_symlink_escape(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    approved = tmp_path / "outputs/provider_benchmark"
    approved.parent.mkdir()
    approved.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="outside|symlink"):
        _valid_preflight(
            tmp_path,
            result_path=approved / "result.json",
        )


def test_preflight_rejects_unignored_output_root(tmp_path):
    pricing = _pricing()
    (tmp_path / ".gitignore").write_text("other/\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not ignored"):
        canary.validate_live_canary_preflight(
            authorization=_authorization(pricing),
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
            result_path=(
                tmp_path / "outputs/provider_benchmark/result.json"
            ),
            checkpoint_path=(
                tmp_path / "outputs/provider_benchmark/checkpoint.json"
            ),
            repository_root=tmp_path,
            graph_verification_enabled=False,
            recovery_006_present=False,
            owned_process_count=0,
            prior_checkpoint=None,
        )


def test_preflight_rejects_group_or_world_writable_parent(tmp_path):
    approved = tmp_path / "outputs/provider_benchmark"
    approved.mkdir(parents=True)
    approved.chmod(0o777)

    with pytest.raises(ValueError, match="permissions"):
        _valid_preflight(tmp_path)


def test_future_transport_contract_is_exact_and_default_off():
    contract = canary.build_future_live_transport_adapter_contract()

    assert contract["timeout_seconds"] == 30
    assert contract["provider_sdk_retry_limit"] == 0
    assert contract["fallback"] is False
    assert contract["live_execution_authorized"] is False
    assert contract["generic_fallback_router_allowed"] is False
    assert contract["openai_allowed"] is False
    assert contract["gemini_allowed"] is False


def test_exact_transport_request_is_accepted():
    plan = build_controlled_provider_benchmark_plan()
    scheduled = _contract()["schedule"][0]
    packet = canary.build_transmittable_request_packet(
        case_alias=scheduled["case_alias"],
        provider=scheduled["provider"],
        model=scheduled["model"],
        plan=plan,
        live_execution_requested=False,
    )

    assert canary.validate_canary_transport_request(
        packet,
        scheduled=scheduled,
        plan=plan,
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda packet: packet.update({"extra": "blocked"}),
        lambda packet: packet.update({"provider": "openai"}),
        lambda packet: packet.update({"fallback": True}),
        lambda packet: packet.update({"timeout_seconds": 31}),
        lambda packet: packet.update({"live_execution_requested": True}),
    ],
)
def test_transport_request_mutation_is_rejected(mutation):
    plan = build_controlled_provider_benchmark_plan()
    scheduled = _contract()["schedule"][0]
    packet = canary.build_transmittable_request_packet(
        case_alias=scheduled["case_alias"],
        provider=scheduled["provider"],
        model=scheduled["model"],
        plan=plan,
        live_execution_requested=False,
    )
    mutation(packet)

    with pytest.raises(ValueError, match="allowlisted"):
        canary.validate_canary_transport_request(
            packet,
            scheduled=scheduled,
            plan=plan,
        )


def test_fake_transport_verification_is_four_call_serial():
    transport = FakeTransport()

    result = canary.verify_canary_with_injected_fake_transport(
        transport=transport
    )

    assert result["fake_transport_calls"] == 4
    assert result["maximum_calls_per_key"] == 1
    assert result["serial_concurrency"] == 1
    assert transport.maximum_active == 1
    assert len(transport.calls) == 4


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("request_id", "blocked", "allowlist"),
        ("reasoning_trace", "blocked", "allowlist"),
        ("raw_response_envelope", {}, "allowlist"),
        ("headers", {}, "allowlist"),
    ],
)
def test_fake_transport_result_forbidden_field_is_rejected(
    field, value, message
):
    base = FakeTransport()

    def unsafe(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result[field] = value
        return result

    with pytest.raises(ValueError, match=message):
        canary.verify_canary_with_injected_fake_transport(
            transport=unsafe
        )


def test_fake_transport_provider_model_mismatch_is_rejected():
    base = FakeTransport()

    def mismatch(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result["model"] = "unknown-model"
        return result

    with pytest.raises(ValueError, match="provider/model"):
        canary.verify_canary_with_injected_fake_transport(
            transport=mismatch
        )


@pytest.mark.parametrize(
    "field",
    ["input_token_count", "output_token_count"],
)
def test_fake_transport_missing_usage_is_rejected(field):
    base = FakeTransport()

    def missing(request, timeout_seconds):
        result = base(request, timeout_seconds)
        result[field] = None
        return result

    with pytest.raises(ValueError, match="missing|invalid"):
        canary.verify_canary_with_injected_fake_transport(
            transport=missing
        )


def test_result_checkpoint_contract_reuses_step8q_and_is_non_authoritative():
    contract = canary.build_canary_result_checkpoint_contract()

    assert contract["harness_version"] == harness.HARNESS_VERSION
    assert contract["step8q_result_artifact_version"] == (
        harness.RESULT_ARTIFACT_VERSION
    )
    assert len(contract["schedule_keys"]) == 4
    assert contract["resume_completed_key"] is False
    assert contract["resume_ambiguous_key"] is False
    assert contract["resume_hard_failure_key"] is False
    assert contract["winner_selected"] is False
    assert contract["production_activation"] is False
    assert contract["automatic_persistence"] is False


def test_runbook_covers_all_bounded_steps_without_execution_command():
    text = RUNBOOK_PATH.read_text(encoding="utf-8").lower()

    for marker in (
        "repository and index are clean",
        "authorization and pricing",
        "exactly four calls",
        "fallback false",
        "sdk retries zero",
        "stop on the first hard failure",
        "delete ignored result and checkpoint artifacts within seven days",
        "do not publish a model winner",
    ):
        assert marker in text
    assert "export " not in text


def test_canary_serialization_and_digest_are_stable():
    contract = _contract()

    assert canary.serialize_controlled_groq_canary_contract(contract) == (
        canary.serialize_controlled_groq_canary_contract()
    )
    assert canary.controlled_groq_canary_sha256(contract) == (
        canary.controlled_groq_canary_sha256()
    )


def test_canary_digest_is_stable_across_fresh_process():
    script = (
        "from src.evaluation.controlled_groq_provider_canary "
        "import controlled_groq_canary_sha256;"
        "print(controlled_groq_canary_sha256())"
    )
    observed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(ROOT)},
    ).stdout.strip()

    assert observed == canary.controlled_groq_canary_sha256()


def test_contract_and_templates_are_deep_copy_contained():
    contract = _contract()
    authorization = canary.build_operator_authorization_template(contract)
    pricing = canary.build_groq_pricing_template()
    original = _contract()

    contract["schedule"][0]["provider"] = "changed"
    authorization["approved_schedule_keys"].clear()
    pricing["prices"].clear()

    assert _contract() == original
    assert len(canary.build_operator_authorization_template()[
        "approved_schedule_keys"
    ]) == 4
    assert len(canary.build_groq_pricing_template()["prices"]) == 2


def test_owner_imports_no_provider_network_database_or_runtime_modules():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    prohibited = {
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
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])

    assert imported.isdisjoint(prohibited)


def test_owner_has_no_environment_credential_or_write_reach():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    prohibited_calls = {
        "getenv",
        "load_dotenv",
        "open",
        "putenv",
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
    assert "API_KEY" not in source


def test_fresh_import_reaches_no_provider_client_or_database_module():
    script = (
        "import json,sys;"
        "import src.evaluation.controlled_groq_provider_canary;"
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


def test_fake_verification_creates_no_repository_runtime_artifact():
    output_root = ROOT / "outputs/provider_benchmark"
    before = (
        sorted(path.relative_to(ROOT).as_posix() for path in output_root.rglob("*"))
        if output_root.exists()
        else []
    )

    canary.verify_canary_with_injected_fake_transport(
        transport=FakeTransport()
    )

    after = (
        sorted(path.relative_to(ROOT).as_posix() for path in output_root.rglob("*"))
        if output_root.exists()
        else []
    )
    assert after == before


def test_authority_mutation_application_and_ats_counts_remain_zero():
    result = canary.verify_canary_with_injected_fake_transport(
        transport=FakeTransport()
    )

    assert result["mutation_count"] == 0
    assert result["application_action_count"] == 0
    assert result["ats_action_count"] == 0
    assert result["winner_selected"] is False
    assert result["production_activation"] is False


def test_steps_8l_through_8q_digests_remain_stable():
    assert provider_benchmark_contract_sha256() == STEP8L_SHA256
    assert provider_fixture_benchmark_sha256() == STEP8O_SHA256
    assert controlled_provider_benchmark_plan_sha256() == STEP8PA_SHA256
    assert harness.controlled_benchmark_harness_sha256() == STEP8Q_SHA256


def test_recovery_006_remains_absent():
    assert not (ROOT / canary.RECOVERY_006_STATUS_PATH).exists()


def test_full_twenty_eight_request_benchmark_remains_unauthorized():
    contract = _contract()

    assert contract["request_bounds"]["maximum_total_requests"] == 4
    assert contract["authority_invariants"][
        "full_benchmark_authorized"
    ] is False
    assert contract["authority_invariants"][
        "live_execution_authorized"
    ] is False


@pytest.mark.parametrize(
    "fixture_path",
    [
        canary.DEFAULT_AUTHORIZATION_TEMPLATE_PATH,
        canary.DEFAULT_PRICING_TEMPLATE_PATH,
    ],
)
def test_template_fixture_is_regular_non_symlink_file(fixture_path):
    assert fixture_path.is_file()
    assert not fixture_path.is_symlink()


def test_no_production_source_imports_the_canary_owner():
    references = []
    for path in (ROOT / "src").rglob("*.py"):
        if path == OWNER_PATH:
            continue
        if "controlled_groq_provider_canary" in path.read_text(
            encoding="utf-8"
        ):
            references.append(path.relative_to(ROOT).as_posix())

    assert references == [
        "src/evaluation/controlled_groq_canary_run_identity.py",
        "src/evaluation/controlled_groq_canary_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_run_evidence_runtime.py",
        "src/evaluation/controlled_groq_tailoring_canary_transport.py",
        "src/evaluation/controlled_groq_canary_run_004_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_transport.py",
        "src/evaluation/controlled_groq_canary_run_005_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_run_005_plan.py",
        "src/evaluation/controlled_groq_canary_run_003_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_run_004_plan.py",
    ]
