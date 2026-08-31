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
from src.evaluation.provider_benchmark_contract import (
    HARD_FAILURE_ORDER,
    WORKLOAD_ORDER,
)


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


def test_live_universe_contains_all_45_contract_resolved_cells(universe):
    eligible = [row for row in universe if row["live_qualification_eligible"]]
    blocked = [row for row in universe if not row["live_qualification_eligible"]]

    assert len(universe) == 45
    assert len(eligible) == 45
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


@pytest.mark.parametrize(
    ("provider", "status_code", "body", "expected_provider_error"),
    [
        (
            "groq",
            500,
            {
                "error": {
                    "type": "invalid_request_error",
                    "code": "json_validate_failed",
                    "param": "response_format",
                    "message": "raw provider message must not survive",
                    "failed_generation": "raw generation must not survive",
                }
            },
            {
                "provider_error_type": "invalid_request_error",
                "provider_error_code": "json_validate_failed",
                "provider_error_param": "response_format",
                "has_failed_generation": True,
            },
        ),
        (
            "groq",
            None,
            {
                "error": {
                    "type": "unallowlisted_raw_type",
                    "code": "unallowlisted_raw_code",
                    "param": "unallowlisted_raw_param",
                }
            },
            {
                "provider_error_type": None,
                "provider_error_code": None,
                "provider_error_param": None,
                "has_failed_generation": False,
            },
        ),
        (
            "openai",
            500,
            {
                "error": {
                    "type": "invalid_request_error",
                    "code": "json_validate_failed",
                    "param": "response_format",
                    "message": "raw provider message must not survive",
                    "failed_generation": "raw generation must not survive",
                }
            },
            {
                "provider_error_type": "invalid_request_error",
                "provider_error_code": "json_validate_failed",
                "provider_error_param": "response_format",
                "has_failed_generation": True,
            },
        ),
        (
            "openai",
            None,
            {
                "error": {
                    "type": "unallowlisted_raw_type",
                    "code": "unallowlisted_raw_code",
                    "param": "unallowlisted_raw_param",
                }
            },
            {
                "provider_error_type": None,
                "provider_error_code": None,
                "provider_error_param": None,
                "has_failed_generation": False,
            },
        ),
    ],
)
def test_controlled_unknown_diagnostic_survives_transport_dispatch_and_evidence(
    monkeypatch,
    plan,
    universe,
    provider,
    status_code,
    body,
    expected_provider_error,
):
    if provider == "groq":
        from src.evaluation import controlled_groq_canary_transport as transport

        function_name = "execute_groq_production_parity_chat_completion_once"
    else:
        from src.evaluation import controlled_openai_canary_transport as transport

        function_name = "execute_openai_production_parity_chat_completion_once"

    class OpaqueProviderError(Exception):
        pass

    raw = OpaqueProviderError("raw exception message must not survive")
    raw.status_code = status_code
    raw.body = body
    raw.headers = {"authorization": OPERATOR_SECRET}
    raw.request = {"prompt": "raw prompt must not survive"}
    raw.response = {"body": "raw response must not survive"}

    def fail_once(**_kwargs):
        transport._raise_bounded_sdk_failure(raw)

    monkeypatch.setattr(transport, function_name, fail_once)
    row = _eligible(universe, provider=provider)
    authorization, pricing = _valid_inputs(plan, [row])
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"]],
        operator_credentials={provider: OPERATOR_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        monotonic_clock=lambda: 1.0,
    )

    assert transport.classify_sdk_exception(raw) == "unknown_provider_outcome"
    assert evidence["stop_reason"] == "unknown_provider_outcome"
    assert evidence["attempted_schedule_keys"] == [row["schedule_key"]]
    assert evidence["completed_schedule_keys"] == []
    assert evidence["blocked_schedule_keys"] == [row["schedule_key"]]
    assert evidence["grading_summaries"] == []
    assert evidence["failure_diagnostics"] == []
    assert evidence["transport_diagnostics"] == [
        {
            "schedule_key": row["schedule_key"],
            "workload_id": row["workload_id"],
            "provider": row["provider"],
            "model": row["model"],
            "transport_failure_category": "unknown_provider_outcome",
            "http_status_code": status_code,
            **expected_provider_error,
        }
    ]
    assert live.validate_live_qualification_evidence(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    serialized = json.dumps(evidence, sort_keys=True)
    for prohibited in (
        "raw exception",
        "raw provider",
        "raw generation",
        "raw prompt",
        "raw response",
        OPERATOR_SECRET,
        "headers",
        "request_id",
    ):
        assert prohibited not in serialized


def test_generic_internal_exception_stops_without_transport_diagnostic(
    plan,
    universe,
):
    rows = [
        row
        for row in universe
        if row["live_qualification_eligible"] and row["provider"] == "groq"
    ][:2]
    dispatcher = RecordingDispatcher(plan, mode="unknown")
    evidence = _execute(plan, rows, dispatcher=dispatcher)

    assert evidence["stop_reason"] == "unknown_provider_outcome"
    assert evidence["attempted_schedule_keys"] == [rows[0]["schedule_key"]]
    assert evidence["blocked_schedule_keys"] == [rows[0]["schedule_key"]]
    assert evidence["transport_diagnostics"] == []
    assert len(dispatcher.calls) == 1


def test_definitive_and_ambiguous_transport_regressions_remain_distinct(
    plan,
    universe,
):
    rows = [
        row
        for row in universe
        if row["live_qualification_eligible"] and row["provider"] == "groq"
    ][:2]

    class DefinitiveOnce:
        def __init__(self):
            self.calls = 0

        def __call__(self, **_kwargs):
            self.calls += 1
            raise live.LiveQualificationDefinitiveFailure(
                "definitive_invalid_request",
                status_code=400,
                provider_error={
                    "provider_error_type": "invalid_request_error",
                    "provider_error_code": "invalid_request",
                    "provider_error_param": "messages",
                    "has_failed_generation": False,
                },
            )

    definitive = DefinitiveOnce()
    evidence = _execute(plan, rows, dispatcher=definitive)
    assert evidence["stop_reason"] == "definitive_invalid_request"
    assert evidence["attempted_schedule_keys"] == [rows[0]["schedule_key"]]
    assert len(evidence["transport_diagnostics"]) == 1
    assert evidence["transport_diagnostics"][0]["http_status_code"] == 400
    assert definitive.calls == 1

    ambiguous = RecordingDispatcher(plan, mode="ambiguous_timeout")
    evidence = _execute(plan, rows, dispatcher=ambiguous)
    assert evidence["stop_reason"] == "ambiguous_timeout"
    assert evidence["attempted_schedule_keys"] == [rows[0]["schedule_key"]]
    assert evidence["ambiguous_schedule_keys"] == [rows[0]["schedule_key"]]
    assert evidence["transport_diagnostics"] == []
    assert len(ambiguous.calls) == 1


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


def test_hard_failure_evidence_canonical_json_round_trip_is_valid(
    plan,
    universe,
):
    row = next(
        item
        for item in universe
        if item["live_qualification_eligible"]
        and item["provider"] == "groq"
        and item["model"] == "openai/gpt-oss-120b"
        and item["workload_id"] == "tailoring_generation"
    )
    authorization, pricing = _valid_inputs(plan, [row])
    evidence = _execute(
        plan,
        [row],
        dispatcher=RecordingDispatcher(plan, mode="hard_failure"),
        authorization=authorization,
        pricing=pricing,
    )
    hard_failures = evidence["failure_diagnostics"][0]["hard_failures"]

    assert hard_failures["schema_invalid_result_accepted"] == 1
    assert all(
        value == 0
        for key, value in hard_failures.items()
        if key != "schema_invalid_result_accepted"
    )
    assert live.validate_live_qualification_evidence(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    original_digest = live.live_qualification_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )

    serialized = live.serialize_live_qualification_evidence(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    reloaded = json.loads(serialized)
    reloaded_failures = reloaded["failure_diagnostics"][0]["hard_failures"]
    assert tuple(reloaded_failures) != tuple(HARD_FAILURE_ORDER)
    assert set(reloaded_failures) == set(HARD_FAILURE_ORDER)
    assert live.validate_live_qualification_evidence(
        reloaded,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert live.live_qualification_evidence_sha256(
        reloaded,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    ) == original_digest

    context = live.build_live_qualification_validation_context(
        reloaded,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert live.validate_live_qualification_validation_context(
        json.loads(
            live.serialize_live_qualification_validation_context(
                context,
                evidence=reloaded,
                plan=plan,
            )
        ),
        evidence=reloaded,
        plan=plan,
    )
    serialized_lower = serialized.lower()
    assert OPERATOR_SECRET.lower() not in serialized_lower
    assert '"raw_response"' not in serialized_lower


@pytest.mark.parametrize("mutation", ["missing", "extra", "invalid_value"])
def test_hard_failure_evidence_key_and_value_schema_stays_fail_closed(
    mutation,
    plan,
    universe,
):
    row = _eligible(universe)
    authorization, pricing = _valid_inputs(plan, [row])
    evidence = _execute(
        plan,
        [row],
        dispatcher=RecordingDispatcher(plan, mode="hard_failure"),
        authorization=authorization,
        pricing=pricing,
    )
    hard_failures = evidence["failure_diagnostics"][0]["hard_failures"]
    if mutation == "missing":
        hard_failures.pop(HARD_FAILURE_ORDER[0])
    elif mutation == "extra":
        hard_failures["unexpected_failure"] = 0
    else:
        hard_failures[HARD_FAILURE_ORDER[0]] = "1"

    with pytest.raises(
        ValueError,
        match="live evidence failure diagnostic counters are invalid",
    ):
        live.validate_live_qualification_evidence(
            evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )


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


def test_manual_preview_builds_and_validates_standard_subjective_review_packet(
    tmp_path,
    plan,
    universe,
):
    row = _eligible(
        universe,
        provider="groq",
        workload="manual_provider_preview",
    )
    authorization, pricing = _valid_inputs(plan, [row])
    dispatcher = RecordingDispatcher(plan)
    dispatcher.outputs[row["case_alias"]] = {
        "preview_status": "advisory",
        "manual_only": True,
        "suggestions": [
            {
                "suggestion_id": "suggestion-alpha",
                "source_evidence_ids": ["evidence_alpha"],
                "preview_text": "Delivered python through bounded synthetic work.",
                "claims": ["python"],
                "rationale": "Uses the bounded authorized evidence.",
                "risk_flags": [],
            }
        ],
        "resume_mutation_authorized": False,
        "automatic_acceptance_authorized": False,
        "application_mutation_authorized": False,
        "auto_apply_authorized": False,
        "auto_submit_authorized": False,
    }
    evidence_target = (
        tmp_path / live.APPROVED_EVIDENCE_DIRECTORY / "manual-preview.json"
    )
    context_target = (
        tmp_path
        / live.APPROVED_EVIDENCE_DIRECTORY
        / "manual-preview.validation-context.json"
    )
    packet_target = (
        tmp_path
        / review.APPROVED_REVIEW_DIRECTORY
        / "subjective-review-packet-manual-provider-preview.json"
    )

    evidence = _execute(
        plan,
        [row],
        dispatcher=dispatcher,
        authorization=authorization,
        pricing=pricing,
        evidence_target=evidence_target,
        validation_context_target=context_target,
        review_packet_target=packet_target,
        repository_root=tmp_path,
    )
    packet = json.loads(packet_target.read_text(encoding="utf-8"))
    serialized = json.dumps(
        packet,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    assert packet["workload_id"] == "manual_provider_preview"
    assert packet["schedule_key"] == row["schedule_key"]
    assert packet["provider"] == row["provider"]
    assert packet["model"] == row["model"]
    assert packet["evidence_sha256"] == live.live_qualification_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert packet["production_task_contract_sha256"] == row[
        "production_task_contract_sha256"
    ]
    assert packet["rubric"] == review.build_subjective_qualification_rubric(
        "manual_provider_preview"
    )
    assert len(serialized.encode("utf-8")) <= review.MAXIMUM_REVIEW_PACKET_BYTES
    assert review.validate_subjective_qualification_review_packet(
        packet,
        evidence=evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    lowered = serialized.lower()
    assert OPERATOR_SECRET.lower() not in lowered
    for prohibited in (
        '"api_key"',
        '"credential"',
        '"headers"',
        '"messages"',
        '"prompt"',
        '"raw_provider"',
        '"raw_request"',
        '"raw_response"',
        '"reasoning"',
        '"request_id"',
    ):
        assert prohibited not in lowered


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


# ---------------------------------------------------------------------------
# Stage 4E: plan-derived live universe + permanent future-corpus regressions.
# No provider is ever contacted; cases.json is never written.
# ---------------------------------------------------------------------------


FUTURE_CORPUS_SHA256 = (
    "1f11a262af93ec2b1a6eb7fee337e5802cf9f15719618c072b6691613a37d071"
)
FUTURE_PLAN_SHA256 = (
    "f074eaa9f4db1e4d58b0f1530503217c76142477548c07a15fc1f2d9fc4e7fae"
)
FUTURE_SKILL_SEMANTICS_SHA256 = (
    "3e1c457b9636d5ec648b6e24a823df006bad790641b1f831d3bebb34b2ddc362"
)
SKILL_TASK_CONTRACT_SHA256 = (
    "73784a99de4913b95e2d2a1e8a1b10a9eee1665fd83a179be34a4fe31b82fa4c"
)


def _stage4e_future_corpus():
    import test_provider_fixture_benchmark as fixture_suite

    future = deepcopy(load_fixture_case_corpus())
    future["cases"] = future["cases"] + (
        fixture_suite.stage4b_proposed_skill_cases()
    )
    return future


def _stage4e_expected_eligible(rows):
    from src.evaluation.controlled_production_parity_benchmark import (
        PRODUCTION_PARITY_RUNNABLE_WORKLOADS,
    )

    return [
        (
            row["workload_id"] in PRODUCTION_PARITY_RUNNABLE_WORKLOADS
            and row["production_task_contract_sha256"] is not None
        )
        for row in rows
    ]


class Stage4ECorpusAwareDispatcher:
    """Records calls and grades against the exact execution corpus."""

    def __init__(self, plan, corpus):
        from src.evaluation.controlled_provider_benchmark_plan import (
            _case_alias,
        )
        from src.evaluation.provider_fixture_benchmark import (
            fixture_case_corpus_sha256,
        )

        digest = fixture_case_corpus_sha256(corpus)
        reviews = {
            row["case_alias"]: row for row in plan["transmission_review"]
        }
        self.corpus = deepcopy(corpus)
        self.outputs = {
            _case_alias(case["case_id"], digest): deepcopy(
                case["expected_output"]
            )
            for case in corpus["cases"]
            if reviews[_case_alias(case["case_id"], digest)][
                "eligible_for_later_controlled_transmission"
            ]
        }
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
        self.calls.append(scheduled["schedule_key"])
        return {
            "parity_result": validate_and_grade_production_parity_response(
                parity_request,
                deepcopy(self.outputs[scheduled["case_alias"]]),
                plan=plan,
                corpus=self.corpus,
            ),
            "provider": provider,
            "model": scheduled["model"],
            "latency_ms": 25.0,
            "input_token_count": 40,
            "output_token_count": 20,
            "provider_outcome_category": "success",
        }


def test_stage4e_current_universe_matches_the_validated_plan():
    plan = build_controlled_provider_benchmark_plan()
    universe = live.build_live_qualification_universe(plan)

    assert len(universe) == len(plan["staged_matrix"]) == 44
    assert [
        row["live_qualification_eligible"] for row in universe
    ] == _stage4e_expected_eligible(universe)
    assert sum(
        row["live_qualification_eligible"] for row in universe
    ) == 44
    assert not [
        row for row in universe if not row["live_qualification_eligible"]
    ]

    source = (
        ROOT / "src/evaluation/controlled_live_provider_qualification.py"
    ).read_text(encoding="utf-8")
    assert "== 44" not in source
    assert "canonical historical plan size changed" not in source


def test_stage4e_future_universe_accepts_a_larger_validated_plan():
    from src.evaluation.controlled_provider_benchmark_plan import (
        controlled_provider_benchmark_plan_sha256,
    )
    from src.evaluation.provider_fixture_benchmark import (
        fixture_case_corpus_sha256,
    )

    future = _stage4e_future_corpus()
    assert fixture_case_corpus_sha256(future) == FUTURE_CORPUS_SHA256
    plan = build_controlled_provider_benchmark_plan(corpus=future)
    assert controlled_provider_benchmark_plan_sha256(plan) == (
        FUTURE_PLAN_SHA256
    )
    semantics = live.build_workload_qualification_semantics_fingerprints(
        plan, corpus=future
    )
    assert semantics["skill_extraction"] == FUTURE_SKILL_SEMANTICS_SHA256

    universe = live.build_live_qualification_universe(plan)
    assert len(universe) == len(plan["staged_matrix"]) == 57
    assert [
        row["live_qualification_eligible"] for row in universe
    ] == _stage4e_expected_eligible(universe)

    skill_rows = [
        row for row in universe if row["workload_id"] == "skill_extraction"
    ]
    assert len(skill_rows) == 10
    assert all(row["live_qualification_eligible"] for row in skill_rows)
    assert all(
        row["production_task_contract_sha256"] == SKILL_TASK_CONTRACT_SHA256
        for row in skill_rows
    )
    assert len(
        live.build_renderer_bound_live_qualification_universe(
            plan, corpus=future
        )
    ) == 57


def test_stage4e_eligibility_and_blocked_authority_fail_closed(monkeypatch):
    plan = build_controlled_provider_benchmark_plan()

    # A runnable workload that unexpectedly loses its fingerprint.
    real = live.build_all_production_task_contract_fingerprints
    monkeypatch.setattr(
        live,
        "build_all_production_task_contract_fingerprints",
        lambda: {**real(), "skill_extraction": None},
    )
    with pytest.raises(ValueError):
        live.build_live_qualification_universe(plan)


def test_stage4i_native_renderer_bound_emission_two_cases():
    """Stage 4I: the executor itself emits renderer-bound evidence.

    Replaces the former Stage 4E proof, which executed with a V1 authorization
    and then hand-stamped the evidence version and tested semantics. Nothing is
    mutated here after execution.
    """

    from src.evaluation import (
        controlled_provider_qualification_evidence_adapter as adapter,
    )

    future, plan, digest, universe = _stage4i_future_setup()

    for case_id in (
        "skill_extraction_required_preferred_v1",
        "skill_extraction_windowed_mid_required_tail_preferred_v1",
    ):
        row = _stage4i_row(universe, digest, case_id, "groq")
        renderer_authorization, pricing = _stage4i_renderer_bound_inputs(
            plan, future, [row]
        )
        assert renderer_authorization[
            live.APPROVED_WORKLOAD_SEMANTICS_FIELD
        ]["skill_extraction"] == FUTURE_SKILL_SEMANTICS_SHA256

        dispatcher = Stage4ECorpusAwareDispatcher(plan, future)
        evidence = live.execute_controlled_live_qualification(
            plan=plan,
            live_authorization=renderer_authorization,
            pricing=pricing,
            requested_schedule_keys=[row["schedule_key"]],
            operator_credentials={"groq": OPERATOR_SECRET},
            execution_time_source=lambda: EXECUTION_TIME,
            transport_dispatchers=_dispatchers(dispatcher),
            monotonic_clock=lambda: 1.0,
            corpus=future,
        )

        # Native emission: no caller mutation of version or tested semantics.
        assert dispatcher.calls == [row["schedule_key"]]
        assert evidence["evidence_version"] == (
            live.RENDERER_BOUND_LIVE_EVIDENCE_VERSION
        )
        assert evidence["execution_status"] == "completed"
        assert evidence["stop_reason"] is None
        assert evidence["aggregate_usage"]["provider_call_count"] == 1

        summary = evidence["grading_summaries"][0]
        assert summary[live.TESTED_WORKLOAD_SEMANTICS_FIELD] == (
            FUTURE_SKILL_SEMANTICS_SHA256
        )
        assert summary["production_task_contract_sha256"] == (
            SKILL_TASK_CONTRACT_SHA256
        )
        assert summary["provider_outcome_category"] == "success"

        untouched = deepcopy(evidence)
        assert live.validate_renderer_bound_live_qualification_evidence(
            evidence,
            plan=plan,
            authorization=renderer_authorization,
            pricing=pricing,
            corpus=future,
        )
        observation = adapter.build_renderer_bound_qualification_observation(
            evidence=evidence,
            schedule_key=row["schedule_key"],
            plan=plan,
            authorization=renderer_authorization,
            pricing=pricing,
            corpus=future,
        )
        assert evidence == untouched
        assert observation["qualification_semantics_generation"] == (
            "renderer_bound_v1"
        )
        assert observation[
            "tested_workload_qualification_semantics_sha256"
        ] == FUTURE_SKILL_SEMANTICS_SHA256
        assert observation["tested_task_contract_sha256"] == (
            SKILL_TASK_CONTRACT_SHA256
        )


def test_stage4e_corpus_plan_mismatch_fails_before_transport():
    from src.evaluation.controlled_production_parity_benchmark import (
        _case_for_packet,
    )

    current = load_fixture_case_corpus()
    future = _stage4e_future_corpus()
    current_plan = build_controlled_provider_benchmark_plan(corpus=current)
    future_plan = build_controlled_provider_benchmark_plan(corpus=future)

    for plan, corpus in (
        (future_plan, current),
        (current_plan, future),
    ):
        with pytest.raises(ValueError):
            _case_for_packet(
                {"case_alias": "case_probe", "workload_id": "skill_extraction"},
                plan,
                corpus,
            )


def test_stage4e_alias_resolution_survives_corpus_reordering():
    from src.evaluation.controlled_production_parity_benchmark import (
        _case_for_packet,
    )
    from src.evaluation.controlled_provider_benchmark_plan import _case_alias
    from src.evaluation.provider_fixture_benchmark import (
        fixture_case_corpus_sha256,
    )

    reordered = _stage4e_future_corpus()
    reordered["cases"] = list(reversed(reordered["cases"]))
    plan = build_controlled_provider_benchmark_plan(corpus=reordered)
    digest = fixture_case_corpus_sha256(reordered)

    for case_id in (
        "skill_extraction_required_preferred_v1",
        "skill_extraction_windowed_overlap_suppressed_preferred_v1",
    ):
        resolved = _case_for_packet(
            {
                "case_alias": _case_alias(case_id, digest),
                "workload_id": "skill_extraction",
            },
            plan,
            reordered,
        )
        assert resolved["case_id"] == case_id


# ---------------------------------------------------------------------------
# Stage 4I: native renderer-bound live evidence emission.
# ---------------------------------------------------------------------------


def _stage4i_future_setup():
    from src.evaluation.provider_fixture_benchmark import (
        fixture_case_corpus_sha256,
    )

    future = _stage4e_future_corpus()
    plan = build_controlled_provider_benchmark_plan(corpus=future)
    assert fixture_case_corpus_sha256(future) == FUTURE_CORPUS_SHA256
    digest = fixture_case_corpus_sha256(future)
    universe = live.build_live_qualification_universe(plan)
    return future, plan, digest, universe


def _stage4i_row(universe, digest, case_id, provider):
    from src.evaluation.controlled_provider_benchmark_plan import _case_alias

    alias = _case_alias(case_id, digest)
    return next(
        row
        for row in universe
        if row["case_alias"] == alias and row["provider"] == provider
    )


def _stage4i_renderer_bound_inputs(plan, future, rows):
    authorization, pricing = _valid_inputs(plan, rows)
    renderer_authorization = live.build_renderer_bound_live_authorization(
        authorization, plan=plan, corpus=future
    )
    return renderer_authorization, pricing


def _stage4i_skill_rows(plan, future):
    rows = [
        row
        for row in live.build_renderer_bound_live_qualification_universe(
            plan, corpus=future
        )
        if row["workload_id"] == "skill_extraction"
    ]
    return sorted(rows, key=lambda row: row["execution_order"])


@pytest.mark.parametrize(
    ("provider", "expected_schedule_key"),
    [
        ("groq", "schedule_f568003f29c5adb0627851f367bd60c7"),
        ("openai", "schedule_d8b9797dddaec99c41ac8569d76473d1"),
    ],
)
def test_stage4p_default_dispatch_threads_future_corpus_to_real_transport(
    monkeypatch,
    provider,
    expected_schedule_key,
):
    future, plan, _digest, _universe = _stage4i_future_setup()
    row = next(
        candidate
        for candidate in _stage4i_skill_rows(plan, future)
        if candidate["provider"] == provider
    )
    assert row["schedule_key"] == expected_schedule_key
    authorization, pricing = _stage4i_renderer_bound_inputs(
        plan,
        future,
        [row],
    )
    expected_output = Stage4ECorpusAwareDispatcher(
        plan,
        future,
    ).outputs[row["case_alias"]]
    client = _FakeClient(_fake_sdk_response(row, expected_output))
    constructor_calls = []

    def fake_client_factory(*, api_key, sdk_module=None):
        constructor_calls.append(
            {"api_key": api_key, "sdk_module": sdk_module}
        )
        return client

    if provider == "groq":
        from src.evaluation import controlled_groq_canary_transport as transport

        monkeypatch.setattr(
            transport,
            "create_live_groq_client",
            fake_client_factory,
        )
    else:
        from src.evaluation import controlled_openai_canary_transport as transport

        monkeypatch.setattr(
            transport,
            "create_live_openai_client",
            fake_client_factory,
        )

    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"]],
        operator_credentials={provider: OPERATOR_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        monotonic_clock=iter((10.0, 10.05)).__next__,
        corpus=future,
    )

    assert constructor_calls == [
        {"api_key": OPERATOR_SECRET, "sdk_module": None}
    ]
    assert len(client.chat.completions.calls) == 1
    assert evidence["attempted_schedule_keys"] == [row["schedule_key"]]
    assert evidence["completed_schedule_keys"] == [row["schedule_key"]]
    assert evidence["aggregate_usage"]["provider_call_count"] == 1
    assert evidence["execution_status"] == "completed"
    assert evidence["stop_reason"] is None
    assert evidence["grading_summaries"][0][
        live.TESTED_WORKLOAD_SEMANTICS_FIELD
    ] == FUTURE_SKILL_SEMANTICS_SHA256


def _stage5c_execute_fake_skill_model(monkeypatch, *, model):
    from src.evaluation import controlled_groq_canary_transport as transport
    from src.evaluation import (
        controlled_provider_qualification_evidence_adapter as adapter,
    )
    from src.evaluation import (
        controlled_provider_qualification_registry as registry,
    )

    future, plan, _digest, _universe = _stage4i_future_setup()
    rows = [
        row
        for row in _stage4i_skill_rows(plan, future)
        if row["provider"] == "groq" and row["model"] == model
    ]
    assert len(rows) == 5
    outputs = Stage4ECorpusAwareDispatcher(plan, future).outputs
    responses = [
        _fake_sdk_response(row, outputs[row["case_alias"]]) for row in rows
    ]
    clients = []
    constructor_calls = []

    def fake_client_factory(*, api_key, sdk_module=None):
        constructor_calls.append(
            {"api_key": api_key, "sdk_module": sdk_module}
        )
        client = _FakeClient(responses[len(clients)])
        clients.append(client)
        return client

    monkeypatch.setattr(
        transport,
        "create_live_groq_client",
        fake_client_factory,
    )
    authorization, pricing = _stage4i_renderer_bound_inputs(
        plan, future, rows
    )
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"] for row in rows],
        operator_credentials={"groq": OPERATOR_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        monotonic_clock=iter((10.0, 10.05) * 5).__next__,
        corpus=future,
    )
    assert len(constructor_calls) == len(clients) == 5
    assert all(len(client.chat.completions.calls) == 1 for client in clients)
    assert evidence["attempted_schedule_keys"] == [
        row["schedule_key"] for row in rows
    ]
    assert evidence["completed_schedule_keys"] == [
        row["schedule_key"] for row in rows
    ]
    assert evidence["authority_invariants"]["retry_count"] == 0
    assert evidence["authority_invariants"]["fallback_activation_count"] == 0
    assert live.validate_renderer_bound_live_qualification_evidence(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        corpus=future,
    )
    evidence_sha256 = live.renderer_bound_live_qualification_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        corpus=future,
    )
    observations = [
        adapter.build_renderer_bound_qualification_observation(
            evidence=evidence,
            schedule_key=row["schedule_key"],
            plan=plan,
            authorization=authorization,
            pricing=pricing,
            corpus=future,
        )
        for row in rows
    ]
    assert {observation["evidence_sha256"] for observation in observations} == {
        evidence_sha256
    }
    cell = registry.build_renderer_bound_candidate_qualification_cell(
        plan=plan,
        workload_id="skill_extraction",
        provider="groq",
        model=model,
        observations=observations,
        current_task_contract_sha256=SKILL_TASK_CONTRACT_SHA256,
        current_workload_qualification_semantics_sha256=(
            FUTURE_SKILL_SEMANTICS_SHA256
        ),
    )
    assert cell["status"] == "qualified"
    assert len(cell["qualification_schedule_keys"]) == 5
    return {
        "future": future,
        "plan": plan,
        "rows": rows,
        "authorization": authorization,
        "pricing": pricing,
        "evidence": evidence,
        "evidence_sha256": evidence_sha256,
        "observations": observations,
        "cell": cell,
        "constructor_calls": constructor_calls,
        "clients": clients,
    }


def test_stage5c_fake_20b_and_120b_qualify_separately_in_expanded_registry(
    monkeypatch,
):
    from src.evaluation import (
        controlled_provider_qualification_registry as registry,
    )
    from src.evaluation import provider_model_recommendation_policy as policy

    results = {
        model: _stage5c_execute_fake_skill_model(monkeypatch, model=model)
        for model in (
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
        )
    }
    plan = results["openai/gpt-oss-20b"]["plan"]
    future = results["openai/gpt-oss-20b"]["future"]
    assert plan == results["openai/gpt-oss-120b"]["plan"]
    assert future == results["openai/gpt-oss-120b"]["future"]
    assert results["openai/gpt-oss-20b"]["evidence_sha256"] != (
        results["openai/gpt-oss-120b"]["evidence_sha256"]
    )
    assert results["openai/gpt-oss-20b"]["cell"][
        "qualification_binding_sha256"
    ] != results["openai/gpt-oss-120b"]["cell"][
        "qualification_binding_sha256"
    ]

    final_user_message = results["openai/gpt-oss-120b"]["clients"][-1].chat.completions.calls[0][
        "messages"
    ][-1]["content"].lower()
    assert "spark" not in final_user_message
    assert "terraform" not in final_user_message

    semantics = live.build_workload_qualification_semantics_fingerprints(
        plan, corpus=future
    )
    base = json.loads(
        (
            ROOT
            / "outputs"
            / "provider_benchmark"
            / "provider-qualification-registry.json"
        ).read_text(encoding="utf-8")
    )
    expanded = registry.project_registry_to_renderer_bound_generation(
        base,
        current_workload_qualification_semantics_sha256_by_workload=semantics,
    )
    replacements = {
        (
            "skill_extraction",
            "groq",
            model,
        ): result["cell"]
        for model, result in results.items()
    }
    expanded_cells = []
    for cell in expanded["cells"]:
        identity = (cell["workload_id"], cell["provider"], cell["model"])
        expanded_cells.append(replacements.get(identity, cell))
        if identity == (
            "skill_extraction",
            "groq",
            "openai/gpt-oss-20b",
        ):
            expanded_cells.append(
                replacements[
                    (
                        "skill_extraction",
                        "groq",
                        "openai/gpt-oss-120b",
                    )
                ]
            )
    expanded["cells"] = expanded_cells
    assert registry.validate_renderer_bound_qualification_registry(
        expanded, plan=plan
    )
    skill_cells = [
        cell
        for cell in expanded["cells"]
        if cell["workload_id"] == "skill_extraction"
    ]
    assert [
        (cell["provider"], cell["model"])
        for cell in skill_cells
    ] == [
        ("groq", "openai/gpt-oss-20b"),
        ("groq", "openai/gpt-oss-120b"),
        ("openai", "gpt-5-mini"),
    ]
    assert [cell["status"] for cell in skill_cells] == [
        "qualified",
        "qualified",
        "stale",
    ]
    assert not any(
        cell["workload_id"] == "manual_scan_phrase"
        and cell["model"] == "openai/gpt-oss-120b"
        for cell in expanded["cells"]
    )

    universe = [
        {
            "provider": cell["provider"],
            "model": cell["model"],
            "status": cell["status"],
        }
        for cell in skill_cells
    ]
    winner = results["openai/gpt-oss-120b"]["cell"]
    pin = {
        "pin_version": policy.RENDERER_BOUND_RECOMMENDATION_PIN_VERSION,
        "workload_id": "skill_extraction",
        "provider": winner["provider"],
        "model": winner["model"],
        "selection_basis": "stage5c_fake_only_validation",
        "expected_status": winner["status"],
        "expected_status_reasons": list(winner["status_reasons"]),
        "expected_qualification_semantics_generation": (
            winner["qualification_semantics_generation"]
        ),
        "expected_current_workload_qualification_semantics_sha256": (
            winner["current_workload_qualification_semantics_sha256"]
        ),
        "expected_tested_workload_qualification_semantics_sha256": (
            winner["tested_workload_qualification_semantics_sha256"]
        ),
        "expected_current_task_contract_sha256": winner[
            "current_task_contract_sha256"
        ],
        "expected_tested_task_contract_sha256": winner[
            "tested_task_contract_sha256"
        ],
        "expected_qualification_binding_sha256": winner[
            "qualification_binding_sha256"
        ],
        "expected_evidence_sha256": winner["evidence_sha256"],
        "expected_review_sha256": winner["review_sha256"],
        "expected_candidate_universe": universe,
    }
    assert policy.validate_renderer_bound_workload_recommendation(
        expanded, pin=pin
    )
    with pytest.raises(ValueError, match="requires a pin"):
        policy.build_renderer_bound_unpinned_workload_recommendation(
            expanded, workload_id="skill_extraction"
        )


def test_stage4i_v1_authorization_still_emits_v1_evidence(plan, universe):
    """The V1 generation is byte-for-byte unaffected by Stage 4I."""

    row = _eligible(universe, provider="groq", workload="skill_extraction")
    authorization, pricing = _valid_inputs(plan, [row])
    dispatcher = RecordingDispatcher(plan)
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"]],
        operator_credentials={"groq": OPERATOR_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers=_dispatchers(dispatcher),
        monotonic_clock=lambda: 1.0,
    )

    assert evidence["evidence_version"] == live.LIVE_EVIDENCE_VERSION
    assert evidence["execution_status"] == "completed"
    for summary in evidence["grading_summaries"]:
        assert set(summary) == live._SUMMARY_FIELDS
        assert live.TESTED_WORKLOAD_SEMANTICS_FIELD not in summary
    assert live.validate_live_qualification_evidence(
        evidence, plan=plan, authorization=authorization, pricing=pricing
    )
    # The renderer-bound validator must reject plain V1 evidence.
    renderer_authorization = live.build_renderer_bound_live_authorization(
        authorization, plan=plan
    )
    with pytest.raises(ValueError):
        live.validate_renderer_bound_live_qualification_evidence(
            evidence,
            plan=plan,
            authorization=renderer_authorization,
            pricing=pricing,
        )

    # Deterministic re-execution reproduces the identical V1 evidence digest.
    repeat = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"]],
        operator_credentials={"groq": OPERATOR_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers=_dispatchers(RecordingDispatcher(plan)),
        monotonic_clock=lambda: 1.0,
    )
    assert repeat == evidence
    assert live.live_qualification_evidence_sha256(
        repeat, plan=plan, authorization=authorization, pricing=pricing
    ) == live.live_qualification_evidence_sha256(
        evidence, plan=plan, authorization=authorization, pricing=pricing
    )


def test_stage4i_fifteen_row_native_renderer_bound_execution():
    """All fifteen approved Skill rows execute natively through one core loop."""

    from src.evaluation import (
        controlled_provider_qualification_evidence_adapter as adapter,
    )

    future, plan, _digest, _universe = _stage4i_future_setup()
    rows = _stage4i_skill_rows(plan, future)
    assert len(rows) == 15

    renderer_authorization, pricing = _stage4i_renderer_bound_inputs(
        plan, future, rows
    )
    keys = [row["schedule_key"] for row in rows]
    dispatcher = Stage4ECorpusAwareDispatcher(plan, future)
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=renderer_authorization,
        pricing=pricing,
        requested_schedule_keys=keys,
        operator_credentials={
            "groq": OPERATOR_SECRET,
            "openai": OPERATOR_SECRET,
        },
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers=_dispatchers(dispatcher),
        monotonic_clock=lambda: 1.0,
        corpus=future,
    )

    assert dispatcher.calls == keys
    assert evidence["evidence_version"] == (
        live.RENDERER_BOUND_LIVE_EVIDENCE_VERSION
    )
    assert evidence["attempted_schedule_keys"] == keys
    assert evidence["completed_schedule_keys"] == keys
    assert evidence["blocked_schedule_keys"] == []
    assert evidence["ambiguous_schedule_keys"] == []
    assert evidence["execution_status"] == "completed"
    assert evidence["stop_reason"] is None
    assert evidence["aggregate_usage"]["provider_call_count"] == 15
    assert evidence["authority_invariants"]["retry_count"] == 0
    assert evidence["authority_invariants"]["fallback_activation_count"] == 0
    assert len(evidence["grading_summaries"]) == 15
    for summary in evidence["grading_summaries"]:
        assert summary[live.TESTED_WORKLOAD_SEMANTICS_FIELD] == (
            FUTURE_SKILL_SEMANTICS_SHA256
        )
        assert summary["production_task_contract_sha256"] == (
            SKILL_TASK_CONTRACT_SHA256
        )

    assert live.validate_renderer_bound_live_qualification_evidence(
        evidence,
        plan=plan,
        authorization=renderer_authorization,
        pricing=pricing,
        corpus=future,
    )
    for key in keys:
        observation = adapter.build_renderer_bound_qualification_observation(
            evidence=evidence,
            schedule_key=key,
            plan=plan,
            authorization=renderer_authorization,
            pricing=pricing,
            corpus=future,
        )
        assert observation[
            "tested_workload_qualification_semantics_sha256"
        ] == FUTURE_SKILL_SEMANTICS_SHA256


def test_stage4i_tested_semantics_copied_from_authorization_not_recomputed():
    """The tested digest is copied from the validated authorization."""

    future, plan, digest, universe = _stage4i_future_setup()
    row = _stage4i_row(
        universe, digest, "skill_extraction_required_preferred_v1", "groq"
    )
    renderer_authorization, pricing = _stage4i_renderer_bound_inputs(
        plan, future, [row]
    )
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=renderer_authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"]],
        operator_credentials={"groq": OPERATOR_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers=_dispatchers(
            Stage4ECorpusAwareDispatcher(plan, future)
        ),
        monotonic_clock=lambda: 1.0,
        corpus=future,
    )

    # Behavioural invariant: emitted digest == authorized digest.
    approved = renderer_authorization[
        live.APPROVED_WORKLOAD_SEMANTICS_FIELD
    ]["skill_extraction"]
    assert evidence["grading_summaries"][0][
        live.TESTED_WORKLOAD_SEMANTICS_FIELD
    ] == approved

    # Call-flow invariant: the emitter derives no digest of its own.
    tree = ast.parse(OWNER_PATH.read_text())
    executor = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "execute_controlled_live_qualification"
    )
    derivers = {
        "build_workload_qualification_semantics_fingerprints",
        "workload_qualification_semantics_sha256",
        "build_workload_rendered_parity_semantics",
    }
    called = {
        node.func.id
        for node in ast.walk(executor)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not (called & derivers)

    # Source-level proof that native emission exists in production source.
    names = {
        node.id for node in ast.walk(executor) if isinstance(node, ast.Name)
    }
    assert "RENDERER_BOUND_LIVE_EVIDENCE_VERSION" in names
    assert "TESTED_WORKLOAD_SEMANTICS_FIELD" in names
    assert "APPROVED_WORKLOAD_SEMANTICS_FIELD" in names


def test_stage4i_early_stop_preserves_native_renderer_bound_evidence():
    """An existing stop condition still yields valid renderer-bound evidence."""

    future, plan, _digest, _universe = _stage4i_future_setup()
    rows = _stage4i_skill_rows(plan, future)[:3]
    renderer_authorization, pricing = _stage4i_renderer_bound_inputs(
        plan, future, rows
    )
    keys = [row["schedule_key"] for row in rows]

    real = Stage4ECorpusAwareDispatcher(plan, future)

    class StopAfterFirst:
        def __init__(self):
            self.calls = []

        def __call__(self, **kwargs):
            self.calls.append(kwargs["scheduled"]["schedule_key"])
            if len(self.calls) > 1:
                raise live.LiveQualificationAmbiguousTimeout("bounded")
            return real(**kwargs)

    dispatcher = StopAfterFirst()
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=renderer_authorization,
        pricing=pricing,
        requested_schedule_keys=keys,
        operator_credentials={"groq": OPERATOR_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers=_dispatchers(dispatcher),
        monotonic_clock=lambda: 1.0,
        corpus=future,
    )

    assert dispatcher.calls == keys[:2]
    assert evidence["evidence_version"] == (
        live.RENDERER_BOUND_LIVE_EVIDENCE_VERSION
    )
    assert evidence["stop_reason"] == "ambiguous_timeout"
    assert evidence["execution_status"] == "stopped"
    assert evidence["attempted_schedule_keys"] == keys[:2]
    assert evidence["completed_schedule_keys"] == keys[:1]
    assert evidence["ambiguous_schedule_keys"] == keys[1:2]
    assert evidence["blocked_schedule_keys"] == []
    assert len(evidence["grading_summaries"]) == 1
    assert evidence["grading_summaries"][0][
        live.TESTED_WORKLOAD_SEMANTICS_FIELD
    ] == FUTURE_SKILL_SEMANTICS_SHA256
    assert live.validate_renderer_bound_live_qualification_evidence(
        evidence,
        plan=plan,
        authorization=renderer_authorization,
        pricing=pricing,
        corpus=future,
    )


def test_stage4n_stage4m_shape_retains_bounded_unknown_diagnostic(
    monkeypatch,
):
    """Capability proof only: no claim about the real Stage 4M exception."""

    from src.evaluation import controlled_groq_canary_transport as transport
    from src.evaluation import (
        controlled_provider_qualification_evidence_adapter as adapter,
    )

    future, plan, _digest, _universe = _stage4i_future_setup()
    rows = _stage4i_skill_rows(plan, future)
    renderer_authorization, pricing = _stage4i_renderer_bound_inputs(
        plan, future, rows
    )
    keys = [row["schedule_key"] for row in rows]
    assert len(keys) == 10
    assert keys[0] == "schedule_f568003f29c5adb0627851f367bd60c7"

    class OpaqueProviderError(Exception):
        pass

    raw = OpaqueProviderError("raw exception message must not survive")
    raw.status_code = 500
    raw.body = {
        "error": {
            "type": "invalid_request_error",
            "code": "json_validate_failed",
            "param": "response_format",
            "message": "raw provider message must not survive",
            "failed_generation": "raw failed generation must not survive",
        },
        "request_id": "raw request id must not survive",
    }
    raw.headers = {"authorization": OPERATOR_SECRET}
    raw.request = {"prompt": "raw request packet must not survive"}
    raw.response = {"body": "raw response body must not survive"}

    def fail_once(**_kwargs):
        transport._raise_bounded_sdk_failure(raw)

    monkeypatch.setattr(
        transport,
        "execute_groq_production_parity_chat_completion_once",
        fail_once,
    )
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=renderer_authorization,
        pricing=pricing,
        requested_schedule_keys=keys,
        operator_credentials={
            "groq": OPERATOR_SECRET,
            "openai": OPERATOR_SECRET,
        },
        execution_time_source=lambda: EXECUTION_TIME,
        monotonic_clock=lambda: 1.0,
        corpus=future,
    )

    assert transport.classify_sdk_exception(raw) == "unknown_provider_outcome"
    assert evidence["evidence_version"] == (
        live.RENDERER_BOUND_LIVE_EVIDENCE_VERSION
    )
    assert evidence["attempted_schedule_keys"] == keys[:1]
    assert evidence["completed_schedule_keys"] == []
    assert evidence["blocked_schedule_keys"] == keys[:1]
    assert evidence["ambiguous_schedule_keys"] == []
    assert evidence["stop_reason"] == "unknown_provider_outcome"
    assert evidence["grading_summaries"] == []
    assert evidence["failure_diagnostics"] == []
    assert evidence["transport_diagnostics"] == [
        {
            "schedule_key": keys[0],
            "workload_id": "skill_extraction",
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "transport_failure_category": "unknown_provider_outcome",
            "http_status_code": 500,
            "provider_error_type": "invalid_request_error",
            "provider_error_code": "json_validate_failed",
            "provider_error_param": "response_format",
            "has_failed_generation": True,
        }
    ]
    assert live.validate_renderer_bound_live_qualification_evidence(
        evidence,
        plan=plan,
        authorization=renderer_authorization,
        pricing=pricing,
        corpus=future,
    )
    with pytest.raises(
        ValueError,
        match="live pre-grading outcome is not a definitive bounded failure",
    ):
        adapter.build_renderer_bound_qualification_observation(
            evidence=evidence,
            schedule_key=keys[0],
            plan=plan,
            authorization=renderer_authorization,
            pricing=pricing,
            corpus=future,
        )

    serialized = json.dumps(evidence, sort_keys=True)
    for prohibited in (
        "raw exception",
        "raw provider",
        "raw failed generation",
        "raw request id",
        "raw request packet",
        "raw response body",
            OPERATOR_SECRET,
            "headers",
            "request_id",
        ):
        assert prohibited not in serialized


def test_stage4i_renderer_bound_mismatches_make_zero_transport_calls():
    """Every authorization mismatch fails closed before any transport."""

    future, plan, digest, universe = _stage4i_future_setup()
    current = load_fixture_case_corpus()
    current_plan = build_controlled_provider_benchmark_plan(corpus=current)
    row = _stage4i_row(
        universe, digest, "skill_extraction_required_preferred_v1", "groq"
    )
    renderer_authorization, pricing = _stage4i_renderer_bound_inputs(
        plan, future, [row]
    )
    keys = [row["schedule_key"]]

    class CountingDispatcher:
        def __init__(self):
            self.calls = []

        def __call__(self, **kwargs):
            self.calls.append(kwargs["scheduled"]["schedule_key"])
            raise AssertionError("transport must not be reached")

    def _run(authorization, *, run_plan=plan, corpus=future, requested=keys):
        dispatcher = CountingDispatcher()
        with pytest.raises(ValueError):
            live.execute_controlled_live_qualification(
                plan=run_plan,
                live_authorization=authorization,
                pricing=pricing,
                requested_schedule_keys=requested,
                operator_credentials={"groq": OPERATOR_SECRET},
                execution_time_source=lambda: EXECUTION_TIME,
                transport_dispatchers=_dispatchers(dispatcher),
                monotonic_clock=lambda: 1.0,
                corpus=corpus,
            )
        assert dispatcher.calls == []

    # Wrong corpus for the renderer-bound authorization.
    _run(renderer_authorization, corpus=current)

    # Wrong plan for the renderer-bound authorization.
    _run(renderer_authorization, run_plan=current_plan)

    # Missing Skill semantics binding.
    missing = deepcopy(renderer_authorization)
    del missing[live.APPROVED_WORKLOAD_SEMANTICS_FIELD]["skill_extraction"]
    _run(missing)

    # Malformed Skill semantics binding.
    malformed = deepcopy(renderer_authorization)
    malformed[live.APPROVED_WORKLOAD_SEMANTICS_FIELD][
        "skill_extraction"
    ] = "not-a-digest"
    _run(malformed)

    # Unauthorized schedule key.
    other = _stage4i_row(
        universe,
        digest,
        "skill_extraction_windowed_mid_required_tail_preferred_v1",
        "groq",
    )
    _run(renderer_authorization, requested=[other["schedule_key"]])

    # V1 authorization artificially carrying renderer-bound-only fields.
    v1_authorization, _pricing = _valid_inputs(plan, [row])
    smuggled = deepcopy(v1_authorization)
    smuggled[live.APPROVED_WORKLOAD_SEMANTICS_FIELD] = deepcopy(
        renderer_authorization[live.APPROVED_WORKLOAD_SEMANTICS_FIELD]
    )
    _run(smuggled)

    # Renderer-bound version string without the renderer-bound field.
    stripped = deepcopy(renderer_authorization)
    del stripped[live.APPROVED_WORKLOAD_SEMANTICS_FIELD]
    _run(stripped)

    # Unrecognized authorization generation.
    unknown = deepcopy(renderer_authorization)
    unknown["authorization_version"] = "controlled-live-qualification-x"
    _run(unknown)


def test_stage4i_renderer_bound_persistence_fails_closed(tmp_path):
    """No renderer-bound writer exists, so persistence is refused."""

    future, plan, digest, universe = _stage4i_future_setup()
    row = _stage4i_row(
        universe, digest, "skill_extraction_required_preferred_v1", "groq"
    )
    renderer_authorization, pricing = _stage4i_renderer_bound_inputs(
        plan, future, [row]
    )
    dispatcher = Stage4ECorpusAwareDispatcher(plan, future)
    with pytest.raises(ValueError):
        live.execute_controlled_live_qualification(
            plan=plan,
            live_authorization=renderer_authorization,
            pricing=pricing,
            requested_schedule_keys=[row["schedule_key"]],
            operator_credentials={"groq": OPERATOR_SECRET},
            execution_time_source=lambda: EXECUTION_TIME,
            transport_dispatchers=_dispatchers(dispatcher),
            monotonic_clock=lambda: 1.0,
            corpus=future,
            evidence_target="outputs/provider_qualification/stage4i.json",
            repository_root=tmp_path,
        )
    assert dispatcher.calls == []


def test_stage4i_native_evidence_reaches_renderer_bound_registry_cell():
    """Native evidence -> observation -> Stage 2A renderer-bound cell."""

    from src.evaluation import (
        controlled_provider_qualification_evidence_adapter as adapter,
    )
    from src.evaluation import (
        controlled_provider_qualification_registry as registry,
    )
    from src.evaluation.controlled_provider_benchmark_human_review import (
        canonical_human_review_requirements,
    )

    future, plan, digest, universe = _stage4i_future_setup()
    row = _stage4i_row(
        universe, digest, "skill_extraction_required_preferred_v1", "groq"
    )
    renderer_authorization, pricing = _stage4i_renderer_bound_inputs(
        plan, future, [row]
    )
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=renderer_authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"]],
        operator_credentials={"groq": OPERATOR_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers=_dispatchers(
            Stage4ECorpusAwareDispatcher(plan, future)
        ),
        monotonic_clock=lambda: 1.0,
        corpus=future,
    )
    observation = adapter.build_renderer_bound_qualification_observation(
        evidence=evidence,
        schedule_key=row["schedule_key"],
        plan=plan,
        authorization=renderer_authorization,
        pricing=pricing,
        corpus=future,
    )

    # The Stage 2A cell projector consumes an exact V1 base cell, so the V1
    # projections of the SAME native evidence supply it. The tested semantics
    # still come from the renderer-bound observation.
    v1_evidence = live._v1_projection_of_renderer_bound_evidence(evidence)
    v1_authorization = live._v1_projection_of_renderer_bound_authorization(
        renderer_authorization
    )
    scheduled = next(
        candidate
        for candidate in harness.build_execution_schedule(
            plan=plan,
            authorization={
                "approved_request_matrix": deepcopy(plan["staged_matrix"]),
                "maximum_request_count": plan["request_counts"][
                    "maximum_total_requests"
                ],
            },
        )
        if candidate["schedule_key"] == row["schedule_key"]
    )
    base_cell = registry._derive_cell_from_input(
        scheduled=scheduled,
        qualification_input={
            "evidence": deepcopy(v1_evidence),
            "evidence_sha256": live.live_qualification_evidence_sha256(
                v1_evidence,
                plan=plan,
                authorization=v1_authorization,
                pricing=pricing,
            ),
            "authorization": deepcopy(v1_authorization),
            "pricing": deepcopy(pricing),
            "schedule_key": row["schedule_key"],
            "tested_task_contract_sha256": None,
            "review_record": None,
            "review_sha256": None,
        },
        plan=plan,
        current_bindings=registry.build_current_qualification_bindings(plan),
        current_task_contract_sha256=SKILL_TASK_CONTRACT_SHA256,
        review_required=canonical_human_review_requirements()[
            "skill_extraction"
        ],
    )
    cell = registry.build_renderer_bound_qualification_cell(
        base_cell=base_cell,
        qualification_semantics_generation="renderer_bound_v1",
        current_workload_qualification_semantics_sha256=(
            FUTURE_SKILL_SEMANTICS_SHA256
        ),
        tested_workload_qualification_semantics_sha256=observation[
            "tested_workload_qualification_semantics_sha256"
        ],
    )

    assert cell["qualification_semantics_generation"] == "renderer_bound_v1"
    assert cell["tested_workload_qualification_semantics_sha256"] == (
        FUTURE_SKILL_SEMANTICS_SHA256
    )
    assert cell["current_workload_qualification_semantics_sha256"] == (
        FUTURE_SKILL_SEMANTICS_SHA256
    )
    assert cell["tested_task_contract_sha256"] == SKILL_TASK_CONTRACT_SHA256
    assert cell["current_task_contract_sha256"] == SKILL_TASK_CONTRACT_SHA256
    # Status comes from the real gates on a genuinely successful execution.
    assert cell["status"] == "qualified"
