from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import socket
import stat
from types import SimpleNamespace

import pytest

from src.evaluation import controlled_live_provider_qualification as live
from src.evaluation import controlled_provider_benchmark_harness as harness
from src.evaluation import controlled_provider_benchmark_human_review as review
from src.evaluation.controlled_production_parity_benchmark import (
    validate_and_grade_production_parity_response,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
)
from src.evaluation.provider_fixture_benchmark import load_fixture_case_corpus
from src.evaluation.provider_benchmark_contract import WORKLOAD_ORDER


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / "src/evaluation/controlled_live_provider_qualification.py"
EXECUTION_TIME = "2026-08-10T12:00:00Z"
OPERATOR_SECRET = "operator-evaluation-secret-memory-only"


@pytest.fixture(scope="module")
def plan():
    return build_controlled_provider_benchmark_plan()


@pytest.fixture(scope="module")
def universe(plan):
    return live.build_live_qualification_universe(plan)


def _eligible(universe, *, provider=None, workload=None):
    return next(
        row
        for row in universe
        if row["live_qualification_eligible"]
        and (provider is None or row["provider"] == provider)
        and (workload is None or row["workload_id"] == workload)
    )


def _valid_inputs(plan, rows):
    keys = [row["schedule_key"] for row in rows]
    authorization = live.build_live_authorization_template(
        approved_schedule_keys=keys,
        plan=plan,
    )
    pricing = live.build_live_pricing_template(
        approved_provider_model_pairs=authorization[
            "approved_provider_model_pairs"
        ]
    )
    pricing.update(
        {
            "pricing_version": "operator-current-2026-08-10",
            "source_classification": (
                live.LIVE_PRICING_SOURCE_CLASSIFICATION
            ),
            "source_effective_at_utc": "2026-08-01T00:00:00Z",
            "valid_from_utc": "2026-08-01T00:00:00Z",
            "expires_at_utc": "2026-09-01T00:00:00Z",
            "operator_approved": True,
        }
    )
    for price in pricing["prices"]:
        price["input_price_per_million_tokens"] = "1.00"
        price["output_price_per_million_tokens"] = "2.00"
    pricing["pricing_table_sha256"] = live.live_pricing_sha256(pricing)
    authorization.update(
        {
            "valid_from_utc": "2026-08-01T00:00:00Z",
            "expires_at_utc": "2026-09-01T00:00:00Z",
            "maximum_request_count": len(keys),
            "token_ceilings": {
                "maximum_input_tokens_per_request": 4096,
                "maximum_output_tokens_per_request": 1024,
                "maximum_total_observed_input_tokens": 4096 * len(keys),
                "maximum_total_observed_output_tokens": 1024 * len(keys),
            },
            "maximum_total_cost": str(len(keys)),
            "pricing_table_sha256": live.live_pricing_sha256(pricing),
            "operator_approved": True,
        }
    )
    for model_key in authorization["maximum_cost_per_provider_model"]:
        authorization["maximum_cost_per_provider_model"][model_key] = str(
            len(keys)
        )
    return authorization, pricing


def _expected_outputs(plan):
    corpus = load_fixture_case_corpus()
    return {
        review["case_alias"]: deepcopy(case["expected_output"])
        for review, case in zip(plan["transmission_review"], corpus["cases"])
        if review["eligible_for_later_controlled_transmission"]
    }


class RecordingDispatcher:
    def __init__(self, plan, *, mode="success"):
        self.plan = plan
        self.mode = mode
        self.outputs = _expected_outputs(plan)
        self.calls = []

    def __call__(
        self,
        *,
        provider,
        api_key,
        parity_request,
        scheduled,
        plan,
        monotonic_clock,
    ):
        self.calls.append(
            {
                "provider": provider,
                "api_key": api_key,
                "workload_id": scheduled["workload_id"],
                "model": scheduled["model"],
                "fallback": parity_request["fallback"],
                "retry_limit": parity_request["retry_limit"],
            }
        )
        if self.mode == "ambiguous_timeout":
            raise live.LiveQualificationAmbiguousTimeout("bounded")
        if self.mode.startswith("definitive_"):
            raise live.LiveQualificationDefinitiveFailure(self.mode)
        if self.mode == "unrecognized_failure":
            raise live.LiveQualificationDefinitiveFailure(
                "raw provider rejection detail must never be persisted"
            )
        if self.mode == "unknown":
            raise RuntimeError("raw provider detail must be discarded")
        raw = (
            "not-json"
            if self.mode == "hard_failure"
            else self.outputs[scheduled["case_alias"]]
        )
        parity_result = validate_and_grade_production_parity_response(
            parity_request,
            raw,
            plan=plan,
        )
        result = {
            "parity_result": parity_result,
            "provider": provider,
            "model": scheduled["model"],
            "latency_ms": 25.0,
            "input_token_count": 40,
            "output_token_count": 20,
            "provider_outcome_category": "success",
        }
        if self.mode == "missing_usage":
            result.pop("output_token_count")
        if self.mode == "excess_usage":
            result["input_token_count"] = 5000
        return result


def _dispatchers(dispatcher):
    return {"groq": dispatcher, "openai": dispatcher}


def _execute(
    plan,
    rows,
    *,
    dispatcher=None,
    authorization=None,
    pricing=None,
    credentials=None,
    **kwargs,
):
    authorization, pricing = (
        _valid_inputs(plan, rows)
        if authorization is None or pricing is None
        else (authorization, pricing)
    )
    dispatcher = dispatcher or RecordingDispatcher(plan)
    providers = {row["provider"] for row in rows}
    return live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"] for row in rows],
        operator_credentials=(
            {provider: OPERATOR_SECRET for provider in providers}
            if credentials is None
            else credentials
        ),
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers=_dispatchers(dispatcher),
        monotonic_clock=lambda: 1.0,
        **kwargs,
    )


def test_import_build_and_validation_are_offline_and_default_off(
    monkeypatch,
    plan,
    universe,
):
    monkeypatch.setattr(
        socket,
        "socket",
        lambda *args, **kwargs: pytest.fail("network construction is prohibited"),
    )
    row = _eligible(universe)
    authorization, pricing = _valid_inputs(plan, [row])

    assert live.build_live_qualification_universe(plan) == universe
    assert live.validate_live_authorization(
        authorization,
        plan=plan,
        pricing=pricing,
        execution_at_utc=EXECUTION_TIME,
    )
    assert harness.build_controlled_benchmark_harness_contract()["controls"] == {
        "live_execution_default": False,
        "real_transport_authorized": False,
        "injected_fake_transport_only_in_tests": True,
        "serial_concurrency": 1,
        "fallback": False,
        "harness_retry_limit": 0,
        "automatic_persistence": False,
        "winner_selection_allowed": False,
        "production_activation_allowed": False,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
    }


def test_live_universe_contains_all_44_contract_resolved_cells(universe):
    eligible = [row for row in universe if row["live_qualification_eligible"]]
    blocked = [row for row in universe if not row["live_qualification_eligible"]]

    assert len(universe) == 44
    assert len(eligible) == 44
    assert blocked == []
    assert all(row["production_task_contract_sha256"] for row in eligible)
    assert tuple(dict.fromkeys(row["workload_id"] for row in eligible)) == (
        WORKLOAD_ORDER
    )


def test_manual_preview_can_enter_only_default_off_authorization(plan, universe):
    preview = next(
        row
        for row in universe
        if row["workload_id"] == "manual_provider_preview"
    )
    authorization = live.build_live_authorization_template(
        approved_schedule_keys=[preview["schedule_key"]],
        plan=plan,
    )

    assert authorization["approved_workload_ids"] == [
        "manual_provider_preview"
    ]
    assert authorization["production_task_contract_fingerprints"] == {
        "manual_provider_preview": preview[
            "production_task_contract_sha256"
        ]
    }
    assert authorization["operator_approved"] is False
    assert authorization["maximum_request_count"] == 0
    assert authorization["maximum_total_cost"] == 0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("benchmark_contract_sha256", "0" * 64, "identity or authority"),
        ("controlled_plan_sha256", "0" * 64, "identity or authority"),
        ("model_catalog_snapshot_sha256", "0" * 64, "identity or authority"),
        ("fixture_corpus_sha256", "0" * 64, "identity or authority"),
        ("operator_approved", False, "operator approval"),
    ],
)
def test_live_authorization_stale_identity_and_unapproved_fail_closed(
    plan,
    universe,
    field,
    value,
    message,
):
    authorization, pricing = _valid_inputs(plan, [_eligible(universe)])
    authorization[field] = value

    with pytest.raises(ValueError, match=message):
        live.validate_live_authorization(
            authorization,
            plan=plan,
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
        )


def test_stale_task_fingerprint_fails_closed(plan, universe):
    authorization, pricing = _valid_inputs(plan, [_eligible(universe)])
    workload = authorization["approved_workload_ids"][0]
    authorization["production_task_contract_fingerprints"][workload] = "0" * 64

    with pytest.raises(ValueError, match="identity or authority"):
        live.validate_live_authorization(
            authorization,
            plan=plan,
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
        )


def test_stale_fingerprint_stops_before_transport_invocation(plan, universe):
    row = _eligible(universe)
    authorization, pricing = _valid_inputs(plan, [row])
    workload = authorization["approved_workload_ids"][0]
    authorization["production_task_contract_fingerprints"][workload] = "0" * 64
    dispatcher = RecordingDispatcher(plan)

    with pytest.raises(ValueError, match="identity or authority"):
        _execute(
            plan,
            [row],
            dispatcher=dispatcher,
            authorization=authorization,
            pricing=pricing,
        )
    assert dispatcher.calls == []


def test_expired_authorization_and_unapproved_expansion_fail_closed(plan, universe):
    first = _eligible(universe)
    second = next(
        row
        for row in universe
        if row["live_qualification_eligible"]
        and row["schedule_key"] != first["schedule_key"]
    )
    authorization, pricing = _valid_inputs(plan, [first])
    expired = deepcopy(authorization)
    expired["expires_at_utc"] = "2026-08-09T00:00:00Z"
    with pytest.raises(ValueError, match="expired"):
        live.validate_live_authorization(
            expired,
            plan=plan,
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
        )
    with pytest.raises(ValueError, match="expands live authorization"):
        live.execute_controlled_live_qualification(
            plan=plan,
            live_authorization=authorization,
            pricing=pricing,
            requested_schedule_keys=[first["schedule_key"], second["schedule_key"]],
            operator_credentials={first["provider"]: OPERATOR_SECRET},
            execution_time_source=lambda: EXECUTION_TIME,
            transport_dispatchers=_dispatchers(RecordingDispatcher(plan)),
        )


def test_authorization_provider_model_and_workload_scope_is_exact(plan, universe):
    row = _eligible(universe)
    authorization, pricing = _valid_inputs(plan, [row])
    authorization["approved_provider_model_pairs"][0]["model"] = "not-authorized"

    with pytest.raises(ValueError, match="identity or authority"):
        live.validate_live_authorization(
            authorization,
            plan=plan,
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
        )


def test_authorization_and_hashes_never_include_credentials(plan, universe):
    authorization, _pricing = _valid_inputs(plan, [_eligible(universe)])
    serialized = json.dumps(authorization, sort_keys=True).lower()

    assert "credential" not in serialized
    assert "api_key" not in serialized
    assert OPERATOR_SECRET not in serialized
    assert live.live_authorization_sha256(authorization) == (
        live.live_authorization_sha256(deepcopy(authorization))
    )
    authorization["credential"] = OPERATOR_SECRET
    with pytest.raises(ValueError, match="exact schema"):
        live.live_authorization_sha256(authorization)


@pytest.mark.parametrize(
    ("field", "unsafe_value"),
    [
        ("serial_execution_required", False),
        ("fallback_allowed", True),
        ("retry_limit", 1),
        ("production_activation_forbidden", False),
        ("application_mutation_forbidden", False),
        ("ats_mutation_forbidden", False),
        ("automatic_persistence_allowed", True),
    ],
)
def test_live_authorization_safety_invariants_cannot_be_weakened(
    plan,
    universe,
    field,
    unsafe_value,
):
    authorization, pricing = _valid_inputs(plan, [_eligible(universe)])
    authorization[field] = unsafe_value

    with pytest.raises(ValueError, match="identity or authority"):
        live.validate_live_authorization(
            authorization,
            plan=plan,
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
        )


def test_owner_imports_no_user_settings_routing_or_registry_and_reads_no_env():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    assert not any("user_ai_settings" in name for name in imports)
    assert not any("user_provider_runtime" in name for name in imports)
    assert not any("qualification_registry" in name for name in imports)
    assert "os.environ" not in source
    assert "os.getenv" not in source
    assert "preferred_provider" not in source

    entrypoint = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "execute_controlled_live_qualification"
    )
    entrypoint_arguments = {
        argument.arg
        for argument in entrypoint.args.args + entrypoint.args.kwonlyargs
    }
    assert "request" not in entrypoint_arguments
    assert "messages" not in entrypoint_arguments
    assert "raw_response" not in entrypoint_arguments


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda pricing: pricing.update({"source_classification": "synthetic_non_current_test_only"}), "synthetic or non-current"),
        (lambda pricing: pricing.update({"expires_at_utc": "2026-08-09T00:00:00Z"}), "expired"),
        (lambda pricing: pricing["prices"].pop(), "scope mismatch"),
        (lambda pricing: pricing["prices"][0].update({"input_price_per_million_tokens": 0}), "invalid"),
    ],
)
def test_live_pricing_must_be_current_complete_and_positive(
    plan,
    universe,
    mutation,
    message,
):
    authorization, pricing = _valid_inputs(plan, [_eligible(universe)])
    mutation(pricing)
    pricing["pricing_table_sha256"] = live.live_pricing_sha256(pricing)
    authorization["pricing_table_sha256"] = live.live_pricing_sha256(pricing)

    with pytest.raises(ValueError, match=message):
        live.validate_live_authorization(
            authorization,
            plan=plan,
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
        )


def test_missing_pricing_and_nonpositive_cost_ceiling_fail_closed(plan, universe):
    authorization, pricing = _valid_inputs(plan, [_eligible(universe)])
    with pytest.raises(ValueError, match="pricing"):
        live.validate_live_authorization(
            authorization,
            plan=plan,
            pricing=None,
            execution_at_utc=EXECUTION_TIME,
        )
    model_key = next(iter(authorization["maximum_cost_per_provider_model"]))
    authorization["maximum_cost_per_provider_model"][model_key] = 0
    with pytest.raises(ValueError, match="cost ceiling"):
        live.validate_live_authorization(
            authorization,
            plan=plan,
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
        )


@pytest.mark.parametrize("provider", ["groq", "openai"])
def test_one_cell_dispatches_only_its_provider_with_parity_and_no_retry(
    plan,
    universe,
    provider,
):
    row = _eligible(universe, provider=provider)
    dispatcher = RecordingDispatcher(plan)
    evidence = _execute(plan, [row], dispatcher=dispatcher)

    assert evidence["execution_status"] == "completed"
    assert evidence["completed_schedule_keys"] == [row["schedule_key"]]
    assert len(dispatcher.calls) == 1
    assert dispatcher.calls[0] == {
        "provider": provider,
        "api_key": OPERATOR_SECRET,
        "workload_id": row["workload_id"],
        "model": row["model"],
        "fallback": False,
        "retry_limit": 0,
    }
    assert evidence["grading_summaries"][0][
        "production_task_contract_sha256"
    ] == row["production_task_contract_sha256"]


def test_wrong_provider_credential_cannot_be_substituted(plan, universe):
    row = _eligible(universe, provider="groq")
    dispatcher = RecordingDispatcher(plan)

    with pytest.raises(ValueError, match="exact explicit"):
        _execute(
            plan,
            [row],
            dispatcher=dispatcher,
            credentials={"openai": OPERATOR_SECRET},
        )
    assert dispatcher.calls == []


@pytest.mark.parametrize(
    ("mode", "stop_reason", "state_field"),
    [
        ("ambiguous_timeout", "ambiguous_timeout", "ambiguous_schedule_keys"),
        ("unknown", "unknown_provider_outcome", "blocked_schedule_keys"),
        ("hard_failure", "hard_safety_failure", "blocked_schedule_keys"),
        ("missing_usage", "missing_usage_metadata", "blocked_schedule_keys"),
    ],
)
def test_first_failure_stops_serial_subset_without_retry(
    plan,
    universe,
    mode,
    stop_reason,
    state_field,
):
    rows = [
        row
        for row in universe
        if row["live_qualification_eligible"] and row["provider"] == "groq"
    ][:2]
    dispatcher = RecordingDispatcher(plan, mode=mode)
    evidence = _execute(plan, rows, dispatcher=dispatcher)

    assert evidence["stop_reason"] == stop_reason
    assert evidence[state_field] == [rows[0]["schedule_key"]]
    assert evidence["attempted_schedule_keys"] == [rows[0]["schedule_key"]]
    assert len(dispatcher.calls) == 1
    assert evidence["authority_invariants"]["retry_count"] == 0
    assert evidence["authority_invariants"]["fallback_activation_count"] == 0


@pytest.mark.parametrize(
    "category",
    [
        "definitive_invalid_request",
        "definitive_authentication_failure",
        "definitive_provider_rejection",
        "definitive_connection_failure",
        "definitive_transport_failure",
    ],
)
def test_bounded_definitive_transport_category_is_persisted_without_raw_detail(
    plan,
    universe,
    category,
):
    row = _eligible(universe, provider="groq")
    dispatcher = RecordingDispatcher(plan, mode=category)
    evidence = _execute(plan, [row], dispatcher=dispatcher)
    serialized = json.dumps(evidence, sort_keys=True)

    assert evidence["stop_reason"] == category
    assert evidence["blocked_schedule_keys"] == [row["schedule_key"]]
    assert evidence["aggregate_usage"]["provider_call_count"] == 1
    assert evidence["authority_invariants"]["retry_count"] == 0
    assert evidence["authority_invariants"]["fallback_activation_count"] == 0
    assert evidence["authority_invariants"]["registry_mutation_count"] == 0
    assert "raw provider" not in serialized
    for prohibited in (
        '"api_key"',
        '"credential"',
        '"raw_request"',
        '"raw_response"',
        '"request_id"',
        '"response_envelope"',
    ):
        assert prohibited not in serialized


def test_unrecognized_definitive_failure_text_fails_closed_without_persistence(
    plan,
    universe,
):
    row = _eligible(universe, provider="groq")
    dispatcher = RecordingDispatcher(plan, mode="unrecognized_failure")
    evidence = _execute(plan, [row], dispatcher=dispatcher)
    serialized = json.dumps(evidence, sort_keys=True)

    assert evidence["stop_reason"] == "unknown_provider_outcome"
    assert "raw provider rejection detail" not in serialized


@pytest.mark.parametrize(
    ("provider", "category"),
    [
        ("groq", "definitive_invalid_request"),
        ("openai", "definitive_authentication_failure"),
    ],
)
def test_default_dispatch_preserves_transport_owned_bounded_category(
    monkeypatch,
    provider,
    category,
):
    if provider == "groq":
        from src.evaluation import controlled_groq_canary_transport as transport

        function_name = "execute_groq_production_parity_chat_completion_once"
    else:
        from src.evaluation import controlled_openai_canary_transport as transport

        function_name = "execute_openai_production_parity_chat_completion_once"

    def fail_once(**_kwargs):
        raise transport.DefinitiveTransportFailure(category)

    monkeypatch.setattr(transport, function_name, fail_once)

    with pytest.raises(live.LiveQualificationDefinitiveFailure, match=category):
        live._default_dispatch(
            provider=provider,
            api_key="fixture-secret",
            parity_request={},
            scheduled={},
            plan={},
            monotonic_clock=lambda: 0.0,
        )


def test_default_dispatch_discards_unrecognized_transport_exception_text(
    monkeypatch,
):
    from src.evaluation import controlled_groq_canary_transport as transport

    raw_detail = "arbitrary provider response body"

    def fail_once(**_kwargs):
        raise transport.DefinitiveTransportFailure(raw_detail)

    monkeypatch.setattr(
        transport,
        "execute_groq_production_parity_chat_completion_once",
        fail_once,
    )

    with pytest.raises(
        live.LiveQualificationUnknownOutcome,
        match="unknown_provider_outcome",
    ) as caught:
        live._default_dispatch(
            provider="groq",
            api_key="fixture-secret",
            parity_request={},
            scheduled={},
            plan={},
            monotonic_clock=lambda: 0.0,
        )
    assert raw_detail not in str(caught.value)


def test_cost_ceiling_blocks_before_any_call(plan, universe):
    row = _eligible(universe)
    authorization, pricing = _valid_inputs(plan, [row])
    model_key = next(iter(authorization["maximum_cost_per_provider_model"]))
    authorization["maximum_cost_per_provider_model"][model_key] = "0.000001"
    authorization["maximum_total_cost"] = "0.000001"
    dispatcher = RecordingDispatcher(plan)

    evidence = _execute(
        plan,
        [row],
        dispatcher=dispatcher,
        authorization=authorization,
        pricing=pricing,
    )

    assert evidence["stop_reason"] == "cost_ceiling_exceeded"
    assert evidence["attempted_schedule_keys"] == []
    assert dispatcher.calls == []


def test_observed_usage_is_recorded_before_token_stop(plan, universe):
    row = _eligible(universe)
    dispatcher = RecordingDispatcher(plan, mode="excess_usage")

    evidence = _execute(plan, [row], dispatcher=dispatcher)

    assert evidence["stop_reason"] == "token_budget_exceeded"
    assert evidence["aggregate_usage"]["provider_call_count"] == 1
    assert evidence["aggregate_usage"]["input_token_count"] == 5000
    assert evidence["grading_summaries"][0]["input_token_count"] == 5000


def test_observed_cost_prevents_the_next_authorized_call(plan, universe):
    rows = [
        row
        for row in universe
        if row["live_qualification_eligible"] and row["provider"] == "groq"
    ][:2]
    authorization, pricing = _valid_inputs(plan, rows)
    one_call_ceiling = "0.0051"
    model_key = next(iter(authorization["maximum_cost_per_provider_model"]))
    authorization["maximum_cost_per_provider_model"][model_key] = one_call_ceiling
    authorization["maximum_total_cost"] = one_call_ceiling
    dispatcher = RecordingDispatcher(plan)

    evidence = _execute(
        plan,
        rows,
        dispatcher=dispatcher,
        authorization=authorization,
        pricing=pricing,
    )

    assert evidence["completed_schedule_keys"] == [rows[0]["schedule_key"]]
    assert evidence["stop_reason"] == "cost_ceiling_exceeded"
    assert len(dispatcher.calls) == 1


def test_evidence_is_bounded_nonqualifying_and_not_automatically_persisted(
    tmp_path,
    plan,
    universe,
):
    row = _eligible(universe)
    evidence = _execute(plan, [row])
    serialized = json.dumps(evidence, sort_keys=True).lower()

    assert OPERATOR_SECRET not in serialized
    for prohibited in (
        '"api_key"',
        '"credential"',
        '"headers"',
        '"prompt"',
        '"raw_request"',
        '"raw_response"',
        '"reasoning"',
        '"request_id"',
        '"synthetic_input"',
    ):
        assert prohibited not in serialized
    assert evidence["retention_policy"]["automatic_persistence"] is False
    assert evidence["authority_invariants"] == {
        "fallback_activation_count": 0,
        "retry_count": 0,
        "registry_mutation_count": 0,
        "human_review_fabricated_count": 0,
        "qualification_promotion_count": 0,
        "recommendation_count": 0,
        "routing_change_count": 0,
        "application_mutation_count": 0,
        "ats_mutation_count": 0,
        "raw_response_persisted_count": 0,
        "raw_request_persisted_count": 0,
    }
    assert list(tmp_path.rglob("*.json")) == []


def test_explicit_persistence_is_exclusive_symlink_safe_and_0600(
    tmp_path,
    plan,
    universe,
):
    row = _eligible(universe)
    authorization, pricing = _valid_inputs(plan, [row])
    dispatcher = RecordingDispatcher(plan)
    target = tmp_path / live.APPROVED_EVIDENCE_DIRECTORY / "canary.json"
    evidence = _execute(
        plan,
        [row],
        dispatcher=dispatcher,
        authorization=authorization,
        pricing=pricing,
        evidence_target=target,
        repository_root=tmp_path,
    )

    assert json.loads(target.read_text(encoding="utf-8")) == evidence
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    with pytest.raises(ValueError, match="overwrite"):
        live.write_live_qualification_evidence_exclusive(
            target,
            evidence,
            repository_root=tmp_path,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )

    symlink_root = tmp_path / "symlink-root"
    symlink_root.mkdir()
    (symlink_root / "outputs").symlink_to(tmp_path / "outputs", target_is_directory=True)
    unsafe_target = (
        symlink_root / live.APPROVED_EVIDENCE_DIRECTORY / "unsafe.json"
    )
    with pytest.raises(ValueError, match="unsafe"):
        live.write_live_qualification_evidence_exclusive(
            unsafe_target,
            evidence,
            repository_root=symlink_root,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )


def test_successful_subjective_cell_persists_bounded_review_packet(
    tmp_path,
    plan,
    universe,
):
    row = _eligible(universe, provider="groq", workload="jd_intelligence")
    authorization, pricing = _valid_inputs(plan, [row])
    authorization_before = deepcopy(authorization)
    pricing_before = deepcopy(pricing)
    plan_before = deepcopy(plan)
    dispatcher = RecordingDispatcher(plan)
    dispatcher.outputs[row["case_alias"]] = {
        "required_skills": ["python", "sql"],
        "preferred_skills": ["dbt"],
        "required_tools": [],
        "preferred_tools": [],
        "workflows": ["analytics"],
        "methods": [],
        "business_contexts": [],
        "stakeholder_contexts": [],
        "ownership_signals": [],
        "seniority_signals": [],
        "risk_flags": [],
        "extraction_confidence": 0.9,
    }
    evidence_target = (
        tmp_path / live.APPROVED_EVIDENCE_DIRECTORY / "subjective-cell.json"
    )
    context_target = (
        tmp_path
        / live.APPROVED_EVIDENCE_DIRECTORY
        / "subjective-cell.validation-context.json"
    )
    packet_target = (
        tmp_path
        / review.APPROVED_REVIEW_DIRECTORY
        / "subjective-review-packet-jd-intelligence.json"
    )

    evidence = _execute(
        plan,
        [row],
        dispatcher=dispatcher,
        evidence_target=evidence_target,
        validation_context_target=context_target,
        review_packet_target=packet_target,
        repository_root=tmp_path,
    )
    packet = json.loads(packet_target.read_text(encoding="utf-8"))
    serialized = json.dumps(packet, sort_keys=True).lower()

    assert stat.S_IMODE(packet_target.stat().st_mode) == 0o600
    assert packet["schedule_key"] == row["schedule_key"]
    assert packet["workload_id"] == "jd_intelligence"
    assert packet["synthetic_task_material"]
    assert packet["validated_production_parity_result"][
        "production_normalized_output"
    ]
    assert packet["validated_production_parity_result"][
        "benchmark_quality"
    ]["quality_gate_passed"] is True
    assert review.validate_subjective_qualification_review_packet(
        packet,
        evidence=evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert set(json.loads(evidence_target.read_text(encoding="utf-8"))) == set(
        evidence
    )
    assert OPERATOR_SECRET.lower() not in serialized
    for prohibited in (
        '"api_key"',
        '"credential"',
        '"headers"',
        '"messages"',
        '"prompt"',
        '"raw_request"',
        '"raw_response"',
        '"reasoning"',
        '"request_id"',
    ):
        assert prohibited not in serialized
    assert plan == plan_before
    assert authorization == authorization_before
    assert pricing == pricing_before

    for field, replacement in (
        ("evidence_sha256", "0" * 64),
        ("model", "wrong-model"),
        ("production_task_contract_sha256", "0" * 64),
    ):
        altered = deepcopy(packet)
        altered[field] = replacement
        with pytest.raises(ValueError):
            review.validate_subjective_qualification_review_packet(
                altered,
                evidence=evidence,
                plan=plan,
                authorization=authorization,
                pricing=pricing,
            )


def test_review_packet_rejects_no_review_workload_before_dispatch(
    tmp_path,
    plan,
    universe,
):
    row = _eligible(universe, workload="skill_extraction")
    dispatcher = RecordingDispatcher(plan)

    with pytest.raises(ValueError, match="exactly one subjective workload"):
        _execute(
            plan,
            [row],
            dispatcher=dispatcher,
            evidence_target=(
                tmp_path / live.APPROVED_EVIDENCE_DIRECTORY / "objective.json"
            ),
            validation_context_target=(
                tmp_path
                / live.APPROVED_EVIDENCE_DIRECTORY
                / "objective.validation-context.json"
            ),
            review_packet_target=(
                tmp_path
                / review.APPROVED_REVIEW_DIRECTORY
                / "subjective-review-packet-objective.json"
            ),
            repository_root=tmp_path,
        )

    assert dispatcher.calls == []
    assert list(tmp_path.rglob("*.json")) == []


def _fake_sdk_response(row, output):
    return SimpleNamespace(
        model=row["model"],
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(output))
            )
        ],
        usage=SimpleNamespace(prompt_tokens=31, completion_tokens=17),
        id="must-not-be-returned",
        headers={"must": "not-be-returned"},
    )


class _FakeCompletions:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        return self.response


class _FakeClient:
    def __init__(self, response):
        self.chat = SimpleNamespace(
            completions=_FakeCompletions(response)
        )


class _FakeSDK:
    def __init__(self, provider, response):
        self.provider = provider
        self.response = response
        self.constructor_calls = []
        self.client = None

    def Groq(self, **kwargs):
        assert self.provider == "groq"
        self.constructor_calls.append(deepcopy(kwargs))
        self.client = _FakeClient(self.response)
        return self.client

    def OpenAI(self, **kwargs):
        assert self.provider == "openai"
        self.constructor_calls.append(deepcopy(kwargs))
        self.client = _FakeClient(self.response)
        return self.client


@pytest.mark.parametrize("provider", ["groq", "openai"])
def test_existing_controlled_transport_executes_parity_once_with_fresh_client(
    plan,
    universe,
    provider,
):
    from src.evaluation.controlled_provider_benchmark_plan import (
        build_transmittable_request_packet,
    )
    from src.evaluation.controlled_production_parity_benchmark import (
        build_production_parity_request,
    )

    row = _eligible(universe, provider=provider)
    packet = build_transmittable_request_packet(
        case_alias=row["case_alias"],
        provider=row["provider"],
        model=row["model"],
        plan=plan,
    )
    request = build_production_parity_request(packet, plan=plan)
    output = _expected_outputs(plan)[row["case_alias"]]
    sdk = _FakeSDK(provider, _fake_sdk_response(row, output))
    consumer = lambda raw: validate_and_grade_production_parity_response(
        request,
        raw,
        plan=plan,
    )
    clock_values = iter((10.0, 10.05))
    if provider == "groq":
        from src.evaluation.controlled_groq_canary_transport import (
            execute_groq_production_parity_chat_completion_once,
        )

        result = execute_groq_production_parity_chat_completion_once(
            api_key=OPERATOR_SECRET,
            parity_request=request,
            scheduled=row,
            parity_response_consumer=consumer,
            monotonic_clock=lambda: next(clock_values),
            sdk_module=sdk,
            plan=plan,
        )
    else:
        from src.evaluation.controlled_openai_canary_transport import (
            execute_openai_production_parity_chat_completion_once,
        )

        result = execute_openai_production_parity_chat_completion_once(
            api_key=OPERATOR_SECRET,
            parity_request=request,
            scheduled=row,
            parity_response_consumer=consumer,
            monotonic_clock=lambda: next(clock_values),
            sdk_module=sdk,
            plan=plan,
        )

    assert result["provider"] == provider
    assert result["provider_outcome_category"] == "success"
    assert result["parity_result"]["production_contract_valid"] is True
    assert len(sdk.constructor_calls) == 1
    assert sdk.constructor_calls[0]["api_key"] == OPERATOR_SECRET
    assert sdk.constructor_calls[0]["max_retries"] == 0
    assert len(sdk.client.chat.completions.calls) == 1
    assert "id" not in result
    assert "headers" not in result
    assert "raw_response" not in result
