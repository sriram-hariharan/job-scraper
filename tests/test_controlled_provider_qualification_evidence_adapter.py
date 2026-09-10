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


def _live_evidence(
    plan, workload_id, *, invalid_contract=False, renderer_bound=False
):
    row = _row(plan, workload_id)
    authorization, pricing = _live_inputs(plan, row)
    if renderer_bound:
        authorization = live.build_renderer_bound_live_authorization(
            authorization, plan=plan
        )
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


def test_manual_preview_is_contract_eligible_without_granting_execution(plan):
    universe = live.build_live_qualification_universe(plan)
    blocked = [row for row in universe if not row["live_qualification_eligible"]]
    preview = [
        row for row in universe if row["workload_id"] == "manual_provider_preview"
    ]
    assert len(universe) == 44
    assert sum(row["live_qualification_eligible"] for row in universe) == 44
    assert blocked == []
    assert len(preview) == 4
    assert all(row["production_task_contract_sha256"] for row in preview)
    assert all(row["live_qualification_eligible"] is True for row in preview)
    assert all(row["live_block_reason"] is None for row in preview)


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


# ---------------------------------------------------------------------------
# Stage 2B: additive renderer-bound live evidence handoff.
# V1 evidence, V1 observations, and V1 authority are untouched.
# ---------------------------------------------------------------------------


STAGE2B_ROOT = Path(__file__).resolve().parents[1]
CURRENT_V1_REGISTRY_SHA256 = (
    "6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f"
)
CURRENT_CONTROLLED_PLAN_SHA256 = (
    "bacc7eaa4524199ba293e2d50232f5a8c6cf61014ad8dc89c3dd30d334654162"
)
CURRENT_FIXTURE_CORPUS_SHA256 = (
    "59180e4064dd74759c6ecd8630478225b191f942b68fb1880e172fe07ee80aec"
)


def _stage2b_renderer_bound(plan, workload_id):
    # Stage 4I: the executor emits renderer-bound evidence natively, so this
    # fixture no longer hand-stamps the version or the tested semantics.
    row, renderer_authorization, pricing, renderer_evidence = _live_evidence(
        plan, workload_id, renderer_bound=True
    )
    assert renderer_evidence["evidence_version"] == (
        live.RENDERER_BOUND_LIVE_EVIDENCE_VERSION
    )
    _v1_row, authorization, _v1_pricing, evidence = _live_evidence(
        plan, workload_id
    )
    semantics = live.build_workload_qualification_semantics_fingerprints(plan)
    return {
        "row": row,
        "v1_authorization": authorization,
        "authorization": renderer_authorization,
        "pricing": pricing,
        "v1_evidence": evidence,
        "evidence": renderer_evidence,
        "semantics": semantics,
    }


def test_stage2b_v1_evidence_and_observation_remain_unchanged(plan):
    row, authorization, pricing, evidence = _live_evidence(
        plan, "skill_extraction"
    )

    assert live.LIVE_EVIDENCE_VERSION == (
        "controlled-live-qualification-evidence-v1"
    )
    assert live.RENDERER_BOUND_LIVE_EVIDENCE_VERSION != (
        live.LIVE_EVIDENCE_VERSION
    )
    assert evidence["evidence_version"] == live.LIVE_EVIDENCE_VERSION
    for summary in evidence["grading_summaries"]:
        assert live.TESTED_WORKLOAD_SEMANTICS_FIELD not in summary

    observation = adapter.build_qualification_observation(
        evidence=evidence,
        schedule_key=row["schedule_key"],
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert adapter.validate_qualification_observation(observation)
    assert set(observation) == adapter._OBSERVATION_FIELDS
    assert "tested_workload_qualification_semantics_sha256" not in observation
    assert "qualification_semantics_generation" not in observation
    assert observation["observation_version"] == (
        adapter.QUALIFICATION_OBSERVATION_VERSION
    )


def test_stage2b_v1_evidence_cannot_gain_a_tested_semantics_digest(plan):
    row, authorization, pricing, evidence = _live_evidence(
        plan, "skill_extraction"
    )
    semantics = live.build_workload_qualification_semantics_fingerprints(plan)

    # The V1 builder exposes no parameter that could carry it.
    with pytest.raises(TypeError):
        adapter.build_qualification_observation(
            evidence=evidence,
            schedule_key=row["schedule_key"],
            plan=plan,
            authorization=authorization,
            pricing=pricing,
            tested_workload_qualification_semantics_sha256=semantics[
                "skill_extraction"
            ],
        )

    # The renderer-bound builder refuses V1 evidence outright.
    renderer_authorization = live.build_renderer_bound_live_authorization(
        authorization, plan=plan
    )
    with pytest.raises(ValueError):
        adapter.build_renderer_bound_qualification_observation(
            evidence=evidence,
            schedule_key=row["schedule_key"],
            plan=plan,
            authorization=renderer_authorization,
            pricing=pricing,
        )


def test_stage2b_renderer_bound_observation_carries_validated_digest(plan):
    context = _stage2b_renderer_bound(plan, "skill_extraction")

    observation = adapter.build_renderer_bound_qualification_observation(
        evidence=context["evidence"],
        schedule_key=context["row"]["schedule_key"],
        plan=plan,
        authorization=context["authorization"],
        pricing=context["pricing"],
    )

    assert set(observation) == adapter._RENDERER_BOUND_OBSERVATION_FIELDS
    assert observation["observation_version"] == (
        adapter.RENDERER_BOUND_OBSERVATION_VERSION
    )
    assert observation["qualification_semantics_generation"] == (
        "renderer_bound_v1"
    )
    assert observation["tested_workload_qualification_semantics_sha256"] == (
        context["semantics"]["skill_extraction"]
    )
    assert observation["evidence_schema_version"] == (
        live.RENDERER_BOUND_LIVE_EVIDENCE_VERSION
    )
    assert observation["tested_task_contract_sha256"] == (
        context["row"]["production_task_contract_sha256"]
    )


def test_stage2b_renderer_bound_observation_refuses_caller_supplied_digest(plan):
    context = _stage2b_renderer_bound(plan, "skill_extraction")

    with pytest.raises(ValueError):
        adapter.build_renderer_bound_qualification_observation(
            evidence=context["evidence"],
            schedule_key=context["row"]["schedule_key"],
            plan=plan,
            authorization=context["authorization"],
            pricing=context["pricing"],
            tested_workload_qualification_semantics_sha256=context[
                "semantics"
            ]["skill_extraction"],
        )


def test_stage2b_missing_or_mismatched_tested_semantics_fails_closed(plan):
    context = _stage2b_renderer_bound(plan, "skill_extraction")

    missing = deepcopy(context["evidence"])
    for summary in missing["grading_summaries"]:
        del summary[live.TESTED_WORKLOAD_SEMANTICS_FIELD]
    with pytest.raises(ValueError):
        live.validate_renderer_bound_live_qualification_evidence(
            missing,
            plan=plan,
            authorization=context["authorization"],
            pricing=context["pricing"],
        )

    mismatched = deepcopy(context["evidence"])
    for summary in mismatched["grading_summaries"]:
        summary[live.TESTED_WORKLOAD_SEMANTICS_FIELD] = "0" * 64
    with pytest.raises(ValueError):
        live.validate_renderer_bound_live_qualification_evidence(
            mismatched,
            plan=plan,
            authorization=context["authorization"],
            pricing=context["pricing"],
        )
    with pytest.raises(ValueError):
        adapter.build_renderer_bound_qualification_observation(
            evidence=mismatched,
            schedule_key=context["row"]["schedule_key"],
            plan=plan,
            authorization=context["authorization"],
            pricing=context["pricing"],
        )

    unauthorized = deepcopy(context["authorization"])
    unauthorized[live.APPROVED_WORKLOAD_SEMANTICS_FIELD] = {
        workload_id: "1" * 64
        for workload_id in unauthorized[
            live.APPROVED_WORKLOAD_SEMANTICS_FIELD
        ]
    }
    with pytest.raises(ValueError):
        live.validate_renderer_bound_live_qualification_evidence(
            context["evidence"],
            plan=plan,
            authorization=unauthorized,
            pricing=context["pricing"],
        )


def test_stage2b_tampering_with_tested_digest_moves_the_evidence_digest(plan):
    context = _stage2b_renderer_bound(plan, "skill_extraction")

    baseline = live.renderer_bound_live_qualification_evidence_sha256(
        context["evidence"],
        plan=plan,
        authorization=context["authorization"],
        pricing=context["pricing"],
    )
    assert baseline != live.live_qualification_evidence_sha256(
        context["v1_evidence"],
        plan=plan,
        authorization=context["v1_authorization"],
        pricing=context["pricing"],
    )

    tampered = deepcopy(context["evidence"])
    for summary in tampered["grading_summaries"]:
        summary[live.TESTED_WORKLOAD_SEMANTICS_FIELD] = "2" * 64
    with pytest.raises(ValueError):
        live.renderer_bound_live_qualification_evidence_sha256(
            tampered,
            plan=plan,
            authorization=context["authorization"],
            pricing=context["pricing"],
        )


def test_stage2b_execution_contract_binds_workload_local_semantics(plan):
    from src.evaluation import controlled_production_parity_benchmark as parity
    from src.evaluation.provider_fixture_benchmark import (
        fixture_case_corpus_sha256,
        load_fixture_case_corpus,
    )

    corpus = load_fixture_case_corpus()
    universe = live.build_renderer_bound_live_qualification_universe(plan)
    assert len(universe) == 44

    skill = parity.workload_qualification_semantics_sha256(
        "skill_extraction", plan=plan, corpus=corpus
    )
    judge = parity.workload_qualification_semantics_sha256(
        "tailoring_judge", plan=plan, corpus=corpus
    )
    assert skill != judge

    by_workload = {
        row["workload_id"]: row[live.TESTED_WORKLOAD_SEMANTICS_FIELD]
        for row in universe
    }
    assert by_workload["skill_extraction"] == skill
    assert by_workload["tailoring_judge"] == judge
    assert fixture_case_corpus_sha256(corpus) not in set(by_workload.values())


def test_stage2b_registry_boundary_consumes_the_adapter_digest(plan):
    from src.evaluation import (
        controlled_provider_qualification_registry as registry,
    )

    context = _stage2b_renderer_bound(plan, "skill_extraction")
    observation = adapter.build_renderer_bound_qualification_observation(
        evidence=context["evidence"],
        schedule_key=context["row"]["schedule_key"],
        plan=plan,
        authorization=context["authorization"],
        pricing=context["pricing"],
    )

    source = json.loads(
        (
            STAGE2B_ROOT
            / "outputs"
            / "provider_benchmark"
            / "provider-qualification-registry.json"
        ).read_text(encoding="utf-8")
    )
    base_cell = next(
        cell
        for cell in source["cells"]
        if cell["workload_id"] == "skill_extraction"
        and cell["provider"] == "groq"
    )

    cell = registry.build_renderer_bound_qualification_cell(
        base_cell=base_cell,
        qualification_semantics_generation=observation[
            "qualification_semantics_generation"
        ],
        current_workload_qualification_semantics_sha256=context["semantics"][
            "skill_extraction"
        ],
        tested_workload_qualification_semantics_sha256=observation[
            "tested_workload_qualification_semantics_sha256"
        ],
    )
    assert cell["qualification_semantics_generation"] == "renderer_bound_v1"
    assert cell["tested_workload_qualification_semantics_sha256"] == (
        observation["tested_workload_qualification_semantics_sha256"]
    )
    assert cell["status"] == "qualified"

    # The registry artifact itself is never written by this handoff.
    assert registry.provider_qualification_registry_sha256(source) == (
        CURRENT_V1_REGISTRY_SHA256
    )


def test_stage2b_v1_authority_invariants_hold(plan):
    from src.evaluation import (
        controlled_provider_qualification_registry as registry,
    )
    from src.evaluation import provider_model_recommendation_policy as policy
    from src.evaluation.controlled_provider_benchmark_plan import (
        controlled_provider_benchmark_plan_sha256,
        legacy_case_alias_map,
    )
    from src.evaluation.provider_fixture_benchmark import (
        fixture_case_corpus_sha256,
        load_fixture_case_corpus,
    )

    corpus = load_fixture_case_corpus()
    source = json.loads(
        (
            STAGE2B_ROOT
            / "outputs"
            / "provider_benchmark"
            / "provider-qualification-registry.json"
        ).read_text(encoding="utf-8")
    )

    assert fixture_case_corpus_sha256(corpus) == CURRENT_FIXTURE_CORPUS_SHA256
    assert controlled_provider_benchmark_plan_sha256(plan) == (
        CURRENT_CONTROLLED_PLAN_SHA256
    )
    assert len(legacy_case_alias_map(corpus)) == 15
    assert registry.provider_qualification_registry_sha256(source) == (
        CURRENT_V1_REGISTRY_SHA256
    )
    assert len(
        policy.build_provider_model_recommendation_policy(source)["workloads"]
    ) == 12


# ---------------------------------------------------------------------------
# Stage 4F: explicit future corpus through the renderer-bound adapter.
# V1 observations are untouched; cases.json is never written.
# ---------------------------------------------------------------------------


STAGE4F_FUTURE_CORPUS_SHA256 = (
    "1f11a262af93ec2b1a6eb7fee337e5802cf9f15719618c072b6691613a37d071"
)
STAGE4F_FUTURE_PLAN_SHA256 = (
    "c2a1b03e834e8707fbd4647bff53a537e00c65e4cf135d71bd15cf660a2d3ec1"
)
STAGE4F_FUTURE_SKILL_SEMANTICS = (
    "2cb1da2c7cbfab3ed3a296e5e1c2ade48c0ffc7b608da984fce5668d29551aa9"
)
STAGE4F_SKILL_TASK_CONTRACT = (
    "73784a99de4913b95e2d2a1e8a1b10a9eee1665fd83a179be34a4fe31b82fa4c"
)


def _stage4f_future_corpus():
    import test_provider_fixture_benchmark as fixture_suite

    from src.evaluation.provider_fixture_benchmark import (
        load_fixture_case_corpus,
    )

    future = deepcopy(load_fixture_case_corpus())
    future["cases"] = future["cases"] + (
        fixture_suite.stage4b_proposed_skill_cases()
    )
    return future


class _Stage4FDispatcher:
    def __init__(self, plan, corpus):
        from src.evaluation.controlled_production_parity_benchmark import (
            validate_and_grade_production_parity_response,
        )
        from src.evaluation.controlled_provider_benchmark_plan import (
            _case_alias,
        )
        from src.evaluation.provider_fixture_benchmark import (
            fixture_case_corpus_sha256,
        )

        self._grade = validate_and_grade_production_parity_response
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
        self, *, provider, api_key, parity_request, scheduled, plan,
        monotonic_clock,
    ):
        self.calls.append(scheduled["schedule_key"])
        return {
            "parity_result": self._grade(
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


def _stage4f_execute(case_id):
    """Run one future-corpus skill row end to end with an injected transport."""

    from src.evaluation.controlled_provider_benchmark_plan import (
        _case_alias,
        build_controlled_provider_benchmark_plan,
        controlled_provider_benchmark_plan_sha256,
    )
    from src.evaluation.provider_fixture_benchmark import (
        fixture_case_corpus_sha256,
    )

    future = _stage4f_future_corpus()
    assert fixture_case_corpus_sha256(future) == STAGE4F_FUTURE_CORPUS_SHA256
    plan = build_controlled_provider_benchmark_plan(corpus=future)
    assert controlled_provider_benchmark_plan_sha256(plan) == (
        STAGE4F_FUTURE_PLAN_SHA256
    )
    semantics = live.build_workload_qualification_semantics_fingerprints(
        plan, corpus=future
    )
    assert semantics["skill_extraction"] == STAGE4F_FUTURE_SKILL_SEMANTICS

    alias = _case_alias(case_id, fixture_case_corpus_sha256(future))
    row = next(
        candidate
        for candidate in live.build_live_qualification_universe(plan)
        if candidate["case_alias"] == alias
        and candidate["provider"] == "groq"
    )
    authorization, pricing = _live_inputs(plan, row)
    renderer_authorization = live.build_renderer_bound_live_authorization(
        authorization, plan=plan, corpus=future
    )
    dispatcher = _Stage4FDispatcher(plan, future)
    # Stage 4I: executed with the renderer-bound authorization, so the evidence
    # is renderer-bound natively and is never stamped afterwards.
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=renderer_authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"]],
        operator_credentials={"groq": TEST_SECRET},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers={"groq": dispatcher, "openai": dispatcher},
        monotonic_clock=lambda: 1.0,
        corpus=future,
    )
    assert evidence["evidence_version"] == (
        live.RENDERER_BOUND_LIVE_EVIDENCE_VERSION
    )
    assert evidence["grading_summaries"][0][
        live.TESTED_WORKLOAD_SEMANTICS_FIELD
    ] == semantics["skill_extraction"]
    renderer_evidence = evidence
    return {
        "future": future,
        "plan": plan,
        "row": row,
        "authorization": renderer_authorization,
        "pricing": pricing,
        "dispatcher": dispatcher,
        "evidence": evidence,
        "renderer_evidence": renderer_evidence,
    }


@pytest.mark.parametrize(
    "case_id",
    (
        "skill_extraction_required_preferred_v1",
        "skill_extraction_windowed_mid_required_tail_preferred_v1",
    ),
)
def test_stage4f_future_corpus_reaches_the_renderer_bound_observation(case_id):
    context = _stage4f_execute(case_id)
    evidence = context["evidence"]

    assert context["dispatcher"].calls == [context["row"]["schedule_key"]]
    assert evidence["execution_status"] == "completed"
    assert evidence["stop_reason"] is None
    assert evidence["aggregate_usage"]["provider_call_count"] == 1

    summary = context["renderer_evidence"]["grading_summaries"][0]
    assert summary[live.TESTED_WORKLOAD_SEMANTICS_FIELD] == (
        STAGE4F_FUTURE_SKILL_SEMANTICS
    )
    assert summary["production_task_contract_sha256"] == (
        STAGE4F_SKILL_TASK_CONTRACT
    )

    observation = adapter.build_renderer_bound_qualification_observation(
        evidence=context["renderer_evidence"],
        schedule_key=context["row"]["schedule_key"],
        plan=context["plan"],
        authorization=context["authorization"],
        pricing=context["pricing"],
        corpus=context["future"],
    )
    assert observation["qualification_semantics_generation"] == (
        "renderer_bound_v1"
    )
    assert observation[
        "tested_workload_qualification_semantics_sha256"
    ] == STAGE4F_FUTURE_SKILL_SEMANTICS
    assert observation["tested_task_contract_sha256"] == (
        STAGE4F_SKILL_TASK_CONTRACT
    )
    assert set(observation) == adapter._RENDERER_BOUND_OBSERVATION_FIELDS


def test_stage4f_adapter_corpus_plan_mismatch_fails_closed():
    from src.evaluation.controlled_provider_benchmark_plan import (
        build_controlled_provider_benchmark_plan,
    )
    from src.evaluation.provider_fixture_benchmark import (
        load_fixture_case_corpus,
    )

    context = _stage4f_execute("skill_extraction_required_preferred_v1")
    current_corpus = load_fixture_case_corpus()
    current_plan = build_controlled_provider_benchmark_plan(
        corpus=current_corpus
    )

    # future plan + current corpus
    with pytest.raises(ValueError):
        adapter.build_renderer_bound_qualification_observation(
            evidence=context["renderer_evidence"],
            schedule_key=context["row"]["schedule_key"],
            plan=context["plan"],
            authorization=context["authorization"],
            pricing=context["pricing"],
            corpus=current_corpus,
        )

    # current plan + future corpus
    with pytest.raises(ValueError):
        adapter.build_renderer_bound_qualification_observation(
            evidence=context["renderer_evidence"],
            schedule_key=context["row"]["schedule_key"],
            plan=current_plan,
            authorization=context["authorization"],
            pricing=context["pricing"],
            corpus=context["future"],
        )

    # omitting the corpus falls back to disk and cannot validate a future plan
    with pytest.raises(ValueError):
        adapter.build_renderer_bound_qualification_observation(
            evidence=context["renderer_evidence"],
            schedule_key=context["row"]["schedule_key"],
            plan=context["plan"],
            authorization=context["authorization"],
            pricing=context["pricing"],
        )


def test_stage4f_v1_observation_path_is_untouched(plan):
    row, authorization, pricing, evidence = _live_evidence(
        plan, "skill_extraction"
    )

    # The V1 builder still has no corpus parameter at all.
    import inspect

    assert "corpus" not in inspect.signature(
        adapter.build_qualification_observation
    ).parameters

    observation = adapter.build_qualification_observation(
        evidence=evidence,
        schedule_key=row["schedule_key"],
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert adapter.validate_qualification_observation(observation)
    assert set(observation) == adapter._OBSERVATION_FIELDS
    assert "tested_workload_qualification_semantics_sha256" not in observation
    assert "qualification_semantics_generation" not in observation

    # The adapter never computes workload semantics to invent provenance.
    source = (
        STAGE2B_ROOT
        / "src/evaluation/controlled_provider_qualification_evidence_adapter.py"
    ).read_text(encoding="utf-8")
    assert "workload_qualification_semantics_sha256(" not in source


def test_stage4f_registry_and_prospective_policy_handoff():
    from src.evaluation import (
        controlled_provider_qualification_registry as registry,
    )
    from src.evaluation import provider_model_recommendation_policy as policy

    context = _stage4f_execute("skill_extraction_required_preferred_v1")
    observation = adapter.build_renderer_bound_qualification_observation(
        evidence=context["renderer_evidence"],
        schedule_key=context["row"]["schedule_key"],
        plan=context["plan"],
        authorization=context["authorization"],
        pricing=context["pricing"],
        corpus=context["future"],
    )

    source_registry = json.loads(
        (
            STAGE2B_ROOT
            / "outputs"
            / "provider_benchmark"
            / "provider-qualification-registry.json"
        ).read_text(encoding="utf-8")
    )
    base_cell = next(
        cell
        for cell in source_registry["cells"]
        if cell["workload_id"] == "skill_extraction"
        and cell["provider"] == "groq"
    )
    base_cell = deepcopy(base_cell)
    base_cell["status"] = "qualified"
    base_cell["status_reasons"] = ["qualification_requirements_satisfied"]
    base_cell["current_task_contract_sha256"] = STAGE4F_SKILL_TASK_CONTRACT
    base_cell["tested_task_contract_sha256"] = observation[
        "tested_task_contract_sha256"
    ]

    cell = registry.build_renderer_bound_qualification_cell(
        base_cell=base_cell,
        qualification_semantics_generation=observation[
            "qualification_semantics_generation"
        ],
        current_workload_qualification_semantics_sha256=(
            STAGE4F_FUTURE_SKILL_SEMANTICS
        ),
        tested_workload_qualification_semantics_sha256=observation[
            "tested_workload_qualification_semantics_sha256"
        ],
    )
    assert cell["qualification_semantics_generation"] == "renderer_bound_v1"
    assert (
        cell["tested_workload_qualification_semantics_sha256"]
        == cell["current_workload_qualification_semantics_sha256"]
        == STAGE4F_FUTURE_SKILL_SEMANTICS
    )
    assert (
        cell["tested_task_contract_sha256"]
        == cell["current_task_contract_sha256"]
        == STAGE4F_SKILL_TASK_CONTRACT
    )
    assert cell["status"] == "qualified"

    # Stage 3 workload-local validation accepts only an explicit pin.
    renderer_registry = {
        **{
            field: deepcopy(source_registry[field])
            for field in source_registry
            if field != "cells"
        },
        "registry_schema_version": (
            registry.RENDERER_BOUND_REGISTRY_SCHEMA_VERSION
        ),
        "registry_contract_version": (
            registry.RENDERER_BOUND_REGISTRY_CONTRACT_VERSION
        ),
        "qualification_semantics_generations": list(
            registry.QUALIFICATION_SEMANTICS_GENERATIONS
        ),
        "cells": [cell]
        + [
            registry.build_renderer_bound_qualification_cell(
                base_cell=other,
                qualification_semantics_generation=(
                    "legacy_no_renderer_binding"
                ),
                current_workload_qualification_semantics_sha256=(
                    STAGE4F_FUTURE_SKILL_SEMANTICS
                ),
            )
            for other in source_registry["cells"]
            if other["workload_id"] == "skill_extraction"
            and other["provider"] != "groq"
        ],
    }
    assert registry.validate_renderer_bound_qualification_registry(
        renderer_registry
    )

    pin = {
        "pin_version": policy.RENDERER_BOUND_RECOMMENDATION_PIN_VERSION,
        "workload_id": "skill_extraction",
        "provider": cell["provider"],
        "model": cell["model"],
        "selection_basis": "synthetic_stage4f_basis_pending_review",
        "expected_status": "qualified",
        "expected_status_reasons": list(cell["status_reasons"]),
        "expected_qualification_semantics_generation": "renderer_bound_v1",
        "expected_current_workload_qualification_semantics_sha256": (
            STAGE4F_FUTURE_SKILL_SEMANTICS
        ),
        "expected_tested_workload_qualification_semantics_sha256": (
            STAGE4F_FUTURE_SKILL_SEMANTICS
        ),
        "expected_current_task_contract_sha256": STAGE4F_SKILL_TASK_CONTRACT,
        "expected_tested_task_contract_sha256": STAGE4F_SKILL_TASK_CONTRACT,
        "expected_qualification_binding_sha256": cell[
            "qualification_binding_sha256"
        ],
        "expected_evidence_sha256": cell["evidence_sha256"],
        "expected_review_sha256": cell["review_sha256"],
        "expected_candidate_universe": [
            {
                "provider": row["provider"],
                "model": row["model"],
                "status": row["status"],
            }
            for row in renderer_registry["cells"]
        ],
    }
    assert policy.validate_renderer_bound_workload_recommendation(
        renderer_registry, pin=pin
    )

    # The V1 frozen recommendation is never usable as a renderer-bound pin.
    with pytest.raises(ValueError):
        policy.validate_renderer_bound_recommendation_pin(
            {
                "workload_id": "skill_extraction",
                **policy._FROZEN_RECOMMENDATIONS["skill_extraction"],
            }
        )
