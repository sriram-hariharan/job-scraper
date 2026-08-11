from __future__ import annotations

from copy import deepcopy
import ast
import json
from pathlib import Path
import socket

import pytest

from src.evaluation import controlled_live_provider_qualification as live
from src.evaluation import controlled_provider_benchmark_evidence_runtime as neutral
from src.evaluation import controlled_provider_benchmark_harness as harness
from src.evaluation import controlled_provider_benchmark_human_review as review
from src.evaluation import controlled_provider_qualification_evidence_adapter as adapter
from src.evaluation import controlled_provider_qualification_registry as registry
from src.evaluation.controlled_production_parity_benchmark import (
    validate_and_grade_production_parity_response,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
)
from src.evaluation.production_task_contract_fingerprints import (
    build_all_production_task_contract_fingerprints,
)
from src.evaluation.provider_fixture_benchmark import load_fixture_case_corpus


EXECUTION_TIME = "2026-08-10T12:00:00Z"
REVIEW_TIME = "2026-08-10T13:00:00Z"
TEST_SECRET = "in-memory-test-credential-only"
RAW_PROVIDER_DETAIL = "raw provider body must never survive"
ADAPTER_PATH = Path(adapter.__file__)


def _expected_outputs(plan):
    corpus = load_fixture_case_corpus()
    return {
        transmission["case_alias"]: deepcopy(case["expected_output"])
        for transmission, case in zip(
            plan["transmission_review"], corpus["cases"]
        )
        if transmission["eligible_for_later_controlled_transmission"]
    }


class NeutralTransport:
    def __init__(self, outputs):
        self.outputs = deepcopy(outputs)
        self.calls = []

    def __call__(self, packet, timeout_seconds):
        self.calls.append(packet["case_alias"])
        return {
            "normalized_output": deepcopy(self.outputs[packet["case_alias"]]),
            "provider": packet["provider"],
            "model": packet["model"],
            "latency_ms": 5.0,
            "input_token_count": 11,
            "output_token_count": 7,
            "provider_outcome_category": "success",
        }


class LiveDispatcher:
    def __init__(self, outputs, *, invalid_contract=False):
        self.outputs = deepcopy(outputs)
        self.invalid_contract = invalid_contract
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
        assert api_key == TEST_SECRET
        response = (
            "not-json"
            if self.invalid_contract
            else deepcopy(self.outputs[scheduled["case_alias"]])
        )
        return {
            "parity_result": validate_and_grade_production_parity_response(
                parity_request,
                response,
                plan=plan,
            ),
            "provider": provider,
            "model": scheduled["model"],
            "latency_ms": 25.0,
            "input_token_count": 40,
            "output_token_count": 20,
            "provider_outcome_category": "success",
        }


class LivePregradingFailureDispatcher:
    def __init__(self, mode):
        self.mode = mode
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
        assert api_key == TEST_SECRET
        if self.mode == "ambiguous_timeout":
            raise live.LiveQualificationAmbiguousTimeout("bounded")
        if self.mode == "unknown_provider_outcome":
            raise RuntimeError(RAW_PROVIDER_DETAIL)
        failure = live.LiveQualificationDefinitiveFailure(self.mode)
        failure.raw_provider_detail = RAW_PROVIDER_DETAIL
        raise failure


def _live_inputs(plan, row):
    authorization = live.build_live_authorization_template(
        approved_schedule_keys=[row["schedule_key"]],
        plan=plan,
    )
    pricing = live.build_live_pricing_template(
        approved_provider_model_pairs=authorization[
            "approved_provider_model_pairs"
        ]
    )
    pricing.update(
        {
            "pricing_version": "in-memory-live-adapter-test-v1",
            "source_classification": live.LIVE_PRICING_SOURCE_CLASSIFICATION,
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
            "maximum_request_count": 1,
            "token_ceilings": {
                "maximum_input_tokens_per_request": 4096,
                "maximum_output_tokens_per_request": 1024,
                "maximum_total_observed_input_tokens": 4096,
                "maximum_total_observed_output_tokens": 1024,
            },
            "maximum_total_cost": "1",
            "pricing_table_sha256": live.live_pricing_sha256(pricing),
            "operator_approved": True,
        }
    )
    for key in authorization["maximum_cost_per_provider_model"]:
        authorization["maximum_cost_per_provider_model"][key] = "1"
    return authorization, pricing


def _row(plan, workload_id):
    return next(
        row
        for row in live.build_live_qualification_universe(plan)
        if row["live_qualification_eligible"]
        and row["provider"] == "groq"
        and row["model"] == "openai/gpt-oss-20b"
        and row["workload_id"] == workload_id
    )


def _live_evidence(plan, workload_id, *, invalid_contract=False):
    row = _row(plan, workload_id)
    authorization, pricing = _live_inputs(plan, row)
    outputs = _expected_outputs(plan)
    if workload_id == "jd_intelligence":
        outputs[row["case_alias"]] = {
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
    dispatcher = LiveDispatcher(
        outputs,
        invalid_contract=invalid_contract,
    )
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"]],
        operator_credentials={"groq": TEST_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers={"groq": dispatcher, "openai": dispatcher},
        monotonic_clock=lambda: 1.0,
    )
    assert dispatcher.calls == [row["schedule_key"]]
    return row, authorization, pricing, evidence


def _live_pregrading_failure_evidence(plan, workload_id, stop_reason):
    row = _row(plan, workload_id)
    authorization, pricing = _live_inputs(plan, row)
    dispatcher = LivePregradingFailureDispatcher(stop_reason)
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"]],
        operator_credentials={"groq": TEST_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers={"groq": dispatcher, "openai": dispatcher},
        monotonic_clock=lambda: 1.0,
    )
    assert dispatcher.calls == [row["schedule_key"]]
    return row, authorization, pricing, evidence


@pytest.fixture(scope="module")
def plan():
    return build_controlled_provider_benchmark_plan()


@pytest.fixture(scope="module")
def legacy_context(plan):
    pricing = harness.load_synthetic_pricing_fixture()
    authorization = harness.load_synthetic_authorization_fixture(
        plan=plan,
        pricing=pricing,
    )
    transport = NeutralTransport(_expected_outputs(plan))
    evidence = neutral.execute_provider_neutral_evidence_run(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        transport=transport,
        execution_time_source=lambda: "2026-07-25T00:00:00Z",
    )
    assert len(transport.calls) == 44
    return authorization, pricing, evidence


@pytest.fixture(scope="module")
def live_skill(plan):
    return _live_evidence(plan, "skill_extraction")


@pytest.fixture(scope="module")
def live_review_required(plan):
    return _live_evidence(plan, "jd_intelligence")


def _observation(plan, context, *, tested_task=None):
    row, authorization, pricing, evidence = context
    return adapter.build_qualification_observation(
        evidence=evidence,
        schedule_key=row["schedule_key"],
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        tested_task_contract_sha256=tested_task,
    )


def _live_qualification_input(plan, context, *, review_record=None):
    row, authorization, pricing, evidence = context
    digest = live.live_qualification_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    review_digest = None
    if review_record is not None:
        review_digest = review.post_result_human_review_sha256(
            review_record,
            evidence=evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )
    return {
        "evidence": deepcopy(evidence),
        "evidence_sha256": digest,
        "authorization": deepcopy(authorization),
        "pricing": deepcopy(pricing),
        "schedule_key": row["schedule_key"],
        "tested_task_contract_sha256": None,
        "review_record": deepcopy(review_record),
        "review_sha256": review_digest,
    }


def _registry_with_live(plan, context, *, review_record=None):
    row = context[0]
    return registry.build_provider_qualification_registry(
        plan=plan,
        current_task_contract_sha256_by_workload=(
            build_all_production_task_contract_fingerprints()
        ),
        qualification_inputs_by_schedule_key={
            row["schedule_key"]: _live_qualification_input(
                plan,
                context,
                review_record=review_record,
            )
        },
    )


def _cell(payload, row):
    return next(
        cell for cell in payload["cells"] if cell["schedule_key"] == row["schedule_key"]
    )


def test_legacy_evidence_uses_native_digest_and_preserves_semantics(
    plan,
    legacy_context,
):
    authorization, pricing, evidence = legacy_context
    summary = next(
        row for row in evidence["grading_summaries"] if row["workload_id"] == "skill_extraction"
    )
    task = "a" * 64
    observation = adapter.build_qualification_observation(
        evidence=evidence,
        schedule_key=summary["schedule_key"],
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        tested_task_contract_sha256=task,
    )

    assert observation["evidence_kind"] == adapter.PROVIDER_NEUTRAL_EVIDENCE_KIND
    assert observation["evidence_sha256"] == neutral.provider_neutral_run_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert observation["tested_task_contract_sha256"] == task
    assert observation["contract_valid"] is summary["schema_valid"]
    assert observation["normalization_succeeded"] is summary[
        "normalization_succeeded"
    ]
    assert observation["quality_gate_passed"] is summary["quality_gate_passed"]


def test_legacy_registry_and_human_review_paths_remain_compatible(
    plan,
    legacy_context,
):
    authorization, pricing, evidence = legacy_context
    skill = next(
        row for row in evidence["grading_summaries"] if row["workload_id"] == "skill_extraction"
    )
    task = "a" * 64
    qualification_input = {
        "evidence": deepcopy(evidence),
        "evidence_sha256": neutral.provider_neutral_run_evidence_sha256(
            evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        ),
        "authorization": deepcopy(authorization),
        "pricing": deepcopy(pricing),
        "schedule_key": skill["schedule_key"],
        "tested_task_contract_sha256": task,
        "review_record": None,
        "review_sha256": None,
    }
    payload = registry.build_provider_qualification_registry(
        plan=plan,
        current_task_contract_sha256_by_workload={"skill_extraction": task},
        qualification_inputs_by_schedule_key={skill["schedule_key"]: qualification_input},
    )
    assert _cell(payload, skill)["status"] == "qualified"

    jd = next(
        row for row in evidence["grading_summaries"] if row["workload_id"] == "jd_intelligence"
    )
    record = review.build_post_result_human_review_record(
        evidence=evidence,
        schedule_key=jd["schedule_key"],
        decision="approved",
        reviewer_id="legacy-reviewer",
        review_time_source=lambda: REVIEW_TIME,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert review.assess_post_result_human_review(
        evidence=evidence,
        schedule_key=jd["schedule_key"],
        review_record=record,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )["review_requirement_satisfied"] is True


def test_valid_live_evidence_produces_exact_bounded_observation(plan, live_skill):
    row, authorization, pricing, evidence = live_skill
    before = deepcopy((authorization, pricing, evidence))
    observation = _observation(plan, live_skill)
    summary = evidence["grading_summaries"][0]

    assert observation["evidence_kind"] == adapter.CONTROLLED_LIVE_EVIDENCE_KIND
    assert observation["evidence_sha256"] == live.live_qualification_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    for field in ("schedule_key", "case_alias", "workload_id", "provider", "model"):
        assert observation[field] == row[field]
    assert observation["tested_task_contract_sha256"] == summary[
        "production_task_contract_sha256"
    ]
    assert observation["tested_model_catalog_snapshot_sha256"] == evidence[
        "model_catalog_snapshot_sha256"
    ]
    assert observation["tested_benchmark_contract_sha256"] == evidence[
        "benchmark_contract_sha256"
    ]
    assert observation["tested_controlled_plan_sha256"] == evidence[
        "controlled_plan_sha256"
    ]
    assert observation["contract_valid"] is True
    assert observation["normalization_succeeded"] is None
    assert observation["quality_gate_passed"] is True
    assert observation["hard_failure_present"] is False
    assert observation["provider_call_count"] == 1
    assert observation["authority_safety_valid"] is True
    assert (authorization, pricing, evidence) == before

    serialized = adapter.serialize_qualification_observation(observation)
    lowered = serialized.lower()
    assert TEST_SECRET not in serialized
    for prohibited in (
        '"checkpoint"',
        '"credential"',
        '"messages"',
        '"normalized_output"',
        '"prompt"',
        '"raw_request"',
        '"raw_response"',
        '"synthetic_input"',
    ):
        assert prohibited not in lowered
    assert json.loads(serialized) == observation


@pytest.mark.parametrize(("missing", "message"), [("authorization", "authorization"), ("pricing", "pricing")])
def test_live_evidence_requires_exact_original_validation_context(
    plan,
    live_skill,
    missing,
    message,
):
    row, authorization, pricing, evidence = live_skill
    kwargs = {
        "evidence": evidence,
        "schedule_key": row["schedule_key"],
        "plan": plan,
        "authorization": authorization,
        "pricing": pricing,
    }
    kwargs[missing] = None
    with pytest.raises(ValueError, match=message):
        adapter.build_qualification_observation(**kwargs)


def test_mismatched_live_authorization_and_pricing_fail_closed(plan, live_skill):
    row, authorization, pricing, evidence = live_skill
    changed_authorization = deepcopy(authorization)
    changed_authorization["maximum_total_cost"] = "2"
    with pytest.raises(ValueError):
        adapter.build_qualification_observation(
            evidence=evidence,
            schedule_key=row["schedule_key"],
            plan=plan,
            authorization=changed_authorization,
            pricing=pricing,
        )

    changed_pricing = deepcopy(pricing)
    changed_pricing["prices"][0]["input_price_per_million_tokens"] = "3"
    with pytest.raises(ValueError):
        adapter.build_qualification_observation(
            evidence=evidence,
            schedule_key=row["schedule_key"],
            plan=plan,
            authorization=authorization,
            pricing=changed_pricing,
        )

    with pytest.raises(ValueError, match="must come from validated live evidence"):
        adapter.build_qualification_observation(
            evidence=evidence,
            schedule_key=row["schedule_key"],
            plan=plan,
            authorization=authorization,
            pricing=pricing,
            tested_task_contract_sha256="a" * 64,
        )


def test_unknown_version_and_changed_live_digest_fail_closed(plan, live_skill):
    row, authorization, pricing, evidence = live_skill
    unknown = deepcopy(evidence)
    unknown["evidence_version"] = "unknown-evidence-v1"
    with pytest.raises(ValueError, match="unsupported"):
        adapter.build_qualification_observation(
            evidence=unknown,
            schedule_key=row["schedule_key"],
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )

    qualification_input = _live_qualification_input(plan, live_skill)
    qualification_input["evidence"]["execution_at_utc"] = "2026-08-10T12:00:01Z"
    with pytest.raises(ValueError, match="evidence SHA-256 mismatch"):
        registry.build_provider_qualification_registry(
            plan=plan,
            current_task_contract_sha256_by_workload=(
                build_all_production_task_contract_fingerprints()
            ),
            qualification_inputs_by_schedule_key={
                row["schedule_key"]: qualification_input
            },
        )


def test_live_no_review_cell_qualifies_only_through_full_registry_requirements(
    plan,
    live_skill,
):
    payload = _registry_with_live(plan, live_skill)
    cell = _cell(payload, live_skill[0])
    assert cell["status"] == "qualified"
    assert cell["review_sha256"] is None
    assert cell["status_reasons"] == ["qualification_requirements_satisfied"]


def test_live_required_review_pending_then_approved_or_rejected(
    plan,
    live_review_required,
):
    row, authorization, pricing, evidence = live_review_required
    pending = _registry_with_live(plan, live_review_required)
    assert _cell(pending, row)["status_reasons"] == ["review_missing"]

    approved = review.build_post_result_human_review_record(
        evidence=evidence,
        schedule_key=row["schedule_key"],
        decision="approved",
        reviewer_id="live-reviewer",
        review_time_source=lambda: REVIEW_TIME,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    approved_registry = _registry_with_live(
        plan,
        live_review_required,
        review_record=approved,
    )
    assert _cell(approved_registry, row)["status"] == "qualified"

    rejected = review.build_post_result_human_review_record(
        evidence=evidence,
        schedule_key=row["schedule_key"],
        decision="rejected",
        reviewer_id="live-reviewer",
        review_time_source=lambda: REVIEW_TIME,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    rejected_registry = _registry_with_live(
        plan,
        live_review_required,
        review_record=rejected,
    )
    assert _cell(rejected_registry, row)["status"] == "rejected"
    assert _cell(rejected_registry, row)["status_reasons"] == ["review_rejected"]


def test_live_task_and_static_binding_changes_become_stale(
    monkeypatch,
    plan,
    live_skill,
):
    qualified = _registry_with_live(plan, live_skill)
    row = live_skill[0]
    fingerprints = build_all_production_task_contract_fingerprints()
    changed = deepcopy(fingerprints)
    changed[row["workload_id"]] = "b" * 64
    stale_task = registry.build_provider_qualification_registry(
        plan=plan,
        current_task_contract_sha256_by_workload=changed,
        existing_registry=qualified,
    )
    assert _cell(stale_task, row)["status_reasons"] == [
        "task_contract_binding_stale"
    ]

    original = registry.build_current_qualification_bindings

    for field, reason in (
        ("model_catalog_snapshot_sha256", "catalog_binding_stale"),
        ("benchmark_contract_sha256", "benchmark_contract_binding_stale"),
        ("controlled_plan_sha256", "controlled_plan_binding_stale"),
    ):
        def changed_bindings(current_plan, *, binding_field=field):
            bindings = original(current_plan)
            bindings[binding_field] = "c" * 64
            return bindings

        monkeypatch.setattr(
            registry,
            "build_current_qualification_bindings",
            changed_bindings,
        )
        stale = registry.build_provider_qualification_registry(
            plan=plan,
            current_task_contract_sha256_by_workload=fingerprints,
            existing_registry=qualified,
        )
        assert _cell(stale, row)["status"] == "stale"
        assert reason in _cell(stale, row)["status_reasons"]
        monkeypatch.setattr(
            registry,
            "build_current_qualification_bindings",
            original,
        )


def test_failed_live_contract_quality_and_hard_failure_cannot_qualify(plan):
    context = _live_evidence(plan, "skill_extraction", invalid_contract=True)
    observation = _observation(plan, context)
    assert observation["contract_valid"] is False
    assert observation["quality_gate_passed"] is False
    assert observation["hard_failure_present"] is True
    payload = _registry_with_live(plan, context)
    cell = _cell(payload, context[0])
    assert cell["status"] == "rejected"
    assert "contract_invalid" in cell["status_reasons"]
    assert "quality_gate_failed" in cell["status_reasons"]


def test_definitive_pregrading_live_failure_is_rejected_without_review(plan):
    context = _live_pregrading_failure_evidence(
        plan,
        "tailoring_generation",
        "definitive_invalid_request",
    )
    row, _authorization, _pricing, evidence = context

    assert evidence["attempted_schedule_keys"] == [row["schedule_key"]]
    assert evidence["blocked_schedule_keys"] == [row["schedule_key"]]
    assert evidence["completed_schedule_keys"] == []
    assert evidence["grading_summaries"] == []
    assert evidence["aggregate_usage"]["provider_call_count"] == 1

    observation = _observation(plan, context)
    assert observation["provider_outcome_category"] == (
        "definitive_invalid_request"
    )
    assert observation["schedule_completed"] is False
    assert observation["provider_call_count"] == 1
    assert observation["contract_valid"] is False
    assert observation["quality_gate_passed"] is False
    assert observation["input_token_count"] == 0
    assert observation["output_token_count"] == 0
    assert observation["tested_task_contract_sha256"] == row[
        "production_task_contract_sha256"
    ]

    payload = _registry_with_live(plan, context)
    cell = _cell(payload, row)
    assert cell["status"] == "rejected"
    assert cell["current_task_contract_sha256"] == row[
        "production_task_contract_sha256"
    ]
    assert cell["tested_task_contract_sha256"] == row[
        "production_task_contract_sha256"
    ]
    assert cell["review_sha256"] is None
    assert cell["reviewed_at_utc"] is None
    assert "review_missing" not in cell["status_reasons"]

    serialized_evidence = json.dumps(evidence, sort_keys=True)
    serialized_observation = adapter.serialize_qualification_observation(
        observation
    )
    serialized_registry = registry.serialize_provider_qualification_registry(
        payload,
        plan=plan,
    )
    for serialized in (
        serialized_evidence,
        serialized_observation,
        serialized_registry,
    ):
        assert RAW_PROVIDER_DETAIL not in serialized
        assert TEST_SECRET not in serialized


@pytest.mark.parametrize(
    "stop_reason",
    ["ambiguous_timeout", "unknown_provider_outcome"],
)
def test_nondefinitive_pregrading_live_outcome_is_not_adapted_as_rejection(
    plan,
    stop_reason,
):
    context = _live_pregrading_failure_evidence(
        plan,
        "tailoring_generation",
        stop_reason,
    )
    row, authorization, pricing, evidence = context
    assert RAW_PROVIDER_DETAIL not in json.dumps(evidence, sort_keys=True)

    with pytest.raises(ValueError, match="not a definitive bounded failure"):
        adapter.build_qualification_observation(
            evidence=evidence,
            schedule_key=row["schedule_key"],
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )
    with pytest.raises(ValueError, match="not a definitive bounded failure"):
        _registry_with_live(plan, context)


def test_live_authority_tampering_fails_native_validation(plan, live_skill):
    row, authorization, pricing, evidence = live_skill
    changed = deepcopy(evidence)
    changed["authority_invariants"]["retry_count"] = 1
    with pytest.raises(ValueError, match="authority"):
        adapter.build_qualification_observation(
            evidence=changed,
            schedule_key=row["schedule_key"],
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )


def test_manual_preview_stays_blocked_and_universes_stay_fixed(plan):
    universe = live.build_live_qualification_universe(plan)
    blocked = [row for row in universe if not row["live_qualification_eligible"]]
    assert len(universe) == 44
    assert sum(row["live_qualification_eligible"] for row in universe) == 40
    assert {row["workload_id"] for row in blocked} == {"manual_provider_preview"}
    with pytest.raises(ValueError, match="live-blocked"):
        live.build_live_authorization_template(
            approved_schedule_keys=[blocked[0]["schedule_key"]],
            plan=plan,
        )


def test_adapter_and_integrations_are_offline_and_do_not_persist(
    monkeypatch,
    plan,
    live_skill,
    tmp_path,
):
    monkeypatch.setattr(
        socket,
        "socket",
        lambda *args, **kwargs: pytest.fail("network access is prohibited"),
    )
    before = list(tmp_path.rglob("*"))
    _observation(plan, live_skill)
    _registry_with_live(plan, live_skill)
    assert list(tmp_path.rglob("*")) == before


def test_adapter_owner_has_no_network_environment_or_persistence_access():
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not {"groq", "openai", "dotenv", "requests", "httpx"}.intersection(
        imports
    )
    assert "getenv" not in source
    assert not any(
        isinstance(node, ast.Attribute) and node.attr in {"getenv", "environ"}
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr
        in {"write_text", "write_bytes", "open", "replace", "unlink"}
        for node in ast.walk(tree)
    )
