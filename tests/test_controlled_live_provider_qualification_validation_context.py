from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import socket
import stat

import pytest

from src.evaluation import controlled_live_provider_qualification as live
from src.evaluation.controlled_production_parity_benchmark import (
    validate_and_grade_production_parity_response,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
)
from src.evaluation.provider_benchmark_contract import WORKLOAD_ORDER
from src.evaluation.provider_fixture_benchmark import load_fixture_case_corpus


ROOT = Path(__file__).resolve().parents[1]
EXECUTION_TIME = "2026-08-10T12:00:00Z"
TEST_CREDENTIAL = "in-memory-validation-context-test-only"
REAL_9C7B = ROOT / (
    "outputs/provider_qualification/"
    "phase1_step9c7b_groq_gpt_oss_20b_skill_extraction_"
    "20260810T075207193158Z.json"
)
REAL_9C7B_SHA256 = (
    "a9dfad7c12e25f6e1512e3c4a587b7ca9e0cf21baf47db23c1eee86166281864"
)
CONTEXT_FIELDS = {
    "context_version",
    "evidence_sha256",
    "authorization_sha256",
    "pricing_sha256",
    "live_authorization",
    "live_pricing",
}


@pytest.fixture(scope="module")
def plan():
    return build_controlled_provider_benchmark_plan()


@pytest.fixture(scope="module")
def row(plan):
    return next(
        item
        for item in live.build_live_qualification_universe(plan)
        if item["live_qualification_eligible"]
        and item["provider"] == "groq"
        and item["model"] == "openai/gpt-oss-20b"
        and item["workload_id"] == "skill_extraction"
    )


def _valid_inputs(plan, row):
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
            "pricing_version": "validation-context-test-v1",
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
    for model_key in authorization["maximum_cost_per_provider_model"]:
        authorization["maximum_cost_per_provider_model"][model_key] = "1"
    return authorization, pricing


def _expected_output(plan, row):
    corpus = load_fixture_case_corpus()
    return deepcopy(
        next(
            case["expected_output"]
            for review, case in zip(plan["transmission_review"], corpus["cases"])
            if review["case_alias"] == row["case_alias"]
        )
    )


class RecordingDispatcher:
    def __init__(self, plan, row):
        self.output = _expected_output(plan, row)
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
        assert api_key == TEST_CREDENTIAL
        assert parity_request["fallback"] is False
        assert parity_request["retry_limit"] == 0
        return {
            "parity_result": validate_and_grade_production_parity_response(
                parity_request,
                deepcopy(self.output),
                plan=plan,
            ),
            "provider": provider,
            "model": scheduled["model"],
            "latency_ms": 25.0,
            "input_token_count": 40,
            "output_token_count": 20,
            "provider_outcome_category": "success",
        }


def _execute(plan, row, *, dispatcher=None, authorization=None, pricing=None, **kwargs):
    if authorization is None or pricing is None:
        authorization, pricing = _valid_inputs(plan, row)
    dispatcher = dispatcher or RecordingDispatcher(plan, row)
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=authorization,
        pricing=pricing,
        requested_schedule_keys=[row["schedule_key"]],
        operator_credentials={"groq": TEST_CREDENTIAL},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers={"groq": dispatcher, "openai": dispatcher},
        monotonic_clock=lambda: 1.0,
        **kwargs,
    )
    return authorization, pricing, dispatcher, evidence


@pytest.fixture()
def live_context(plan, row):
    authorization, pricing, dispatcher, evidence = _execute(plan, row)
    assert dispatcher.calls == [row["schedule_key"]]
    context = live.build_live_qualification_validation_context(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    return authorization, pricing, evidence, context


def test_context_exact_schema_originals_and_native_digests(plan, live_context):
    authorization, pricing, evidence, context = live_context

    assert set(context) == CONTEXT_FIELDS
    assert context["context_version"] == (
        "controlled-live-qualification-validation-context-v1"
    )
    assert context["live_authorization"] == authorization
    assert context["live_pricing"] == pricing
    assert context["evidence_sha256"] == live.live_qualification_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert context["authorization_sha256"] == evidence["authorization_sha256"]
    assert context["authorization_sha256"] == live.live_authorization_sha256(
        authorization
    )
    assert context["pricing_sha256"] == evidence["pricing_sha256"]
    assert context["pricing_sha256"] == live.live_pricing_sha256(pricing)
    serialized = json.dumps(context, sort_keys=True).lower()
    assert TEST_CREDENTIAL.lower() not in serialized
    for prohibited in (
        '"api_key"',
        '"headers"',
        '"messages"',
        '"normalized_output"',
        '"prompt"',
        '"raw_request"',
        '"raw_response"',
        '"reasoning"',
        '"request_id"',
        '"synthetic_input"',
    ):
        assert prohibited not in serialized
    assert live.validate_live_qualification_validation_context(
        context,
        evidence=evidence,
        plan=plan,
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["live_pricing"]["prices"][0].update(
            {"api_key": "prohibited"}
        ),
        lambda value: value["live_pricing"].update(
            {"pricing_version": "gsk_secret-like-value"}
        ),
        lambda value: value["live_authorization"].update(
            {"maximum_total_cost": "0.50"}
        ),
        lambda value: value["live_pricing"]["prices"][0].update(
            {"input_price_per_million_tokens": "9.00"}
        ),
    ],
)
def test_context_prohibited_or_modified_inputs_fail_closed(
    mutation,
    plan,
    live_context,
):
    _, _, evidence, context = live_context
    changed = deepcopy(context)
    mutation(changed)

    with pytest.raises(ValueError):
        live.load_live_qualification_validation_context(
            changed,
            evidence=evidence,
            plan=plan,
        )


def test_modified_evidence_fails_closed(plan, live_context):
    _, _, evidence, context = live_context
    changed = deepcopy(evidence)
    changed["execution_at_utc"] = "2026-08-10T12:00:01Z"

    with pytest.raises(ValueError, match="evidence digest"):
        live.load_live_qualification_validation_context(
            context,
            evidence=changed,
            plan=plan,
        )


@pytest.mark.parametrize(
    "field",
    ["evidence_sha256", "authorization_sha256", "pricing_sha256"],
)
def test_wrong_context_digest_fails_closed(field, plan, live_context):
    _, _, evidence, context = live_context
    changed = deepcopy(context)
    changed[field] = "0" * 64

    with pytest.raises(ValueError, match="digest mismatch"):
        live.load_live_qualification_validation_context(
            changed,
            evidence=evidence,
            plan=plan,
        )


def test_writer_persists_exact_content_mode_and_loader_round_trip(
    tmp_path,
    plan,
    live_context,
):
    authorization, pricing, evidence, context = live_context
    target = (
        tmp_path
        / live.APPROVED_EVIDENCE_DIRECTORY
        / "future-run.validation-context.json"
    )

    written = live.write_live_qualification_validation_context_exclusive(
        target,
        context,
        evidence=evidence,
        repository_root=tmp_path,
        plan=plan,
    )
    persisted = json.loads(target.read_text(encoding="utf-8"))

    assert written == target
    assert persisted == context
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert target.read_text(encoding="utf-8") == (
        live.serialize_live_qualification_validation_context(
            context,
            evidence=evidence,
            plan=plan,
        )
    )
    assert live.load_live_qualification_validation_context(
        persisted,
        evidence=evidence,
        plan=plan,
    ) == {"authorization": authorization, "pricing": pricing}


def test_loader_returns_defensive_copies(plan, live_context):
    authorization, pricing, evidence, context = live_context

    loaded = live.load_live_qualification_validation_context(
        context,
        evidence=evidence,
        plan=plan,
    )
    loaded["authorization"]["operator_approved"] = False
    loaded["pricing"]["operator_approved"] = False

    assert context["live_authorization"] == authorization
    assert context["live_pricing"] == pricing
    assert authorization["operator_approved"] is True
    assert pricing["operator_approved"] is True


def test_writer_rejects_namespace_traversal_and_overwrite(
    tmp_path,
    plan,
    live_context,
):
    _, _, evidence, context = live_context
    approved = tmp_path / live.APPROVED_EVIDENCE_DIRECTORY
    approved.mkdir(parents=True, mode=0o700)
    outside = tmp_path / "outside.validation-context.json"
    traversal = approved / ".." / "escape.validation-context.json"
    target = approved / "existing.validation-context.json"

    with pytest.raises(ValueError, match="absolute"):
        live.write_live_qualification_validation_context_exclusive(
            Path("outputs/provider_qualification/relative.validation-context.json"),
            context,
            evidence=evidence,
            repository_root=tmp_path,
            plan=plan,
        )
    with pytest.raises(ValueError, match="approved namespace"):
        live.write_live_qualification_validation_context_exclusive(
            outside,
            context,
            evidence=evidence,
            repository_root=tmp_path,
            plan=plan,
        )
    with pytest.raises(ValueError, match="traversal"):
        live.write_live_qualification_validation_context_exclusive(
            traversal,
            context,
            evidence=evidence,
            repository_root=tmp_path,
            plan=plan,
        )
    target.write_text("preserve", encoding="utf-8")
    with pytest.raises(ValueError, match="overwrite"):
        live.write_live_qualification_validation_context_exclusive(
            target,
            context,
            evidence=evidence,
            repository_root=tmp_path,
            plan=plan,
        )
    assert target.read_text(encoding="utf-8") == "preserve"


def test_writer_rejects_symlink_target_and_unsafe_parent(
    tmp_path,
    plan,
    live_context,
):
    _, _, evidence, context = live_context
    approved = tmp_path / live.APPROVED_EVIDENCE_DIRECTORY
    approved.mkdir(parents=True, mode=0o700)
    external = tmp_path / "external.json"
    external.write_text("preserve", encoding="utf-8")
    symlink_target = approved / "linked.validation-context.json"
    symlink_target.symlink_to(external)

    with pytest.raises(ValueError, match="overwrite"):
        live.write_live_qualification_validation_context_exclusive(
            symlink_target,
            context,
            evidence=evidence,
            repository_root=tmp_path,
            plan=plan,
        )
    assert external.read_text(encoding="utf-8") == "preserve"

    unsafe_root = tmp_path / "unsafe-root"
    unsafe_parent = unsafe_root / live.APPROVED_EVIDENCE_DIRECTORY
    unsafe_parent.mkdir(parents=True, mode=0o700)
    unsafe_parent.chmod(0o770)
    with pytest.raises(ValueError, match="permissions are unsafe"):
        live.write_live_qualification_validation_context_exclusive(
            unsafe_parent / "blocked.validation-context.json",
            context,
            evidence=evidence,
            repository_root=unsafe_root,
            plan=plan,
        )


def test_loader_has_no_environment_network_or_provider_side_effects(
    monkeypatch,
    plan,
    live_context,
):
    authorization, pricing, evidence, context = live_context

    def prohibited(*args, **kwargs):
        pytest.fail("loader attempted a prohibited external operation")

    monkeypatch.setattr(os, "getenv", prohibited)
    monkeypatch.setattr(socket, "socket", prohibited)
    monkeypatch.setattr(live, "_default_dispatch", prohibited)
    source = inspect.getsource(live.load_live_qualification_validation_context)
    assert "environ" not in source
    assert "dispatch" not in source
    assert live.load_live_qualification_validation_context(
        context,
        evidence=evidence,
        plan=plan,
    ) == {"authorization": authorization, "pricing": pricing}


def test_execute_default_off_and_evidence_only_remain_backward_compatible(
    tmp_path,
    plan,
    row,
):
    _, _, default_dispatcher, default_evidence = _execute(plan, row)
    assert default_dispatcher.calls == [row["schedule_key"]]
    assert list(tmp_path.rglob("*.json")) == []

    evidence_target = (
        tmp_path / live.APPROVED_EVIDENCE_DIRECTORY / "evidence-only.json"
    )
    _, _, evidence_dispatcher, persisted_evidence = _execute(
        plan,
        row,
        evidence_target=evidence_target,
        repository_root=tmp_path,
    )
    assert evidence_dispatcher.calls == [row["schedule_key"]]
    assert json.loads(evidence_target.read_text(encoding="utf-8")) == (
        persisted_evidence
    )
    assert default_evidence == persisted_evidence
    assert list(tmp_path.rglob("*.validation-context.json")) == []


def test_execute_persists_matching_evidence_and_context(
    tmp_path,
    plan,
    row,
):
    evidence_target = (
        tmp_path / live.APPROVED_EVIDENCE_DIRECTORY / "future-evidence.json"
    )
    context_target = (
        tmp_path
        / live.APPROVED_EVIDENCE_DIRECTORY
        / "future-evidence.validation-context.json"
    )
    authorization, pricing, dispatcher, evidence = _execute(
        plan,
        row,
        evidence_target=evidence_target,
        validation_context_target=context_target,
        repository_root=tmp_path,
    )
    context = json.loads(context_target.read_text(encoding="utf-8"))

    assert dispatcher.calls == [row["schedule_key"]]
    assert json.loads(evidence_target.read_text(encoding="utf-8")) == evidence
    assert live.load_live_qualification_validation_context(
        context,
        evidence=evidence,
        plan=plan,
    ) == {"authorization": authorization, "pricing": pricing}
    assert context["evidence_sha256"] == live.live_qualification_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert stat.S_IMODE(evidence_target.stat().st_mode) == 0o600
    assert stat.S_IMODE(context_target.stat().st_mode) == 0o600


def test_context_write_failure_preserves_evidence_without_retry_or_fallback(
    tmp_path,
    plan,
    row,
):
    evidence_target = (
        tmp_path / live.APPROVED_EVIDENCE_DIRECTORY / "partial-evidence.json"
    )
    context_target = (
        tmp_path
        / live.APPROVED_EVIDENCE_DIRECTORY
        / "partial-evidence.validation-context.json"
    )
    context_target.parent.mkdir(parents=True, mode=0o700)
    context_target.write_text("preserve", encoding="utf-8")
    authorization, pricing = _valid_inputs(plan, row)
    dispatcher = RecordingDispatcher(plan, row)

    with pytest.raises(
        live.LiveQualificationPersistenceFailure,
        match="context persistence failed after live evidence persistence",
    ):
        _execute(
            plan,
            row,
            dispatcher=dispatcher,
            authorization=authorization,
            pricing=pricing,
            evidence_target=evidence_target,
            validation_context_target=context_target,
            repository_root=tmp_path,
        )

    persisted_evidence = json.loads(evidence_target.read_text(encoding="utf-8"))
    assert dispatcher.calls == [row["schedule_key"]]
    assert context_target.read_text(encoding="utf-8") == "preserve"
    assert live.validate_live_qualification_evidence(
        persisted_evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    assert persisted_evidence["authority_invariants"]["retry_count"] == 0
    assert (
        persisted_evidence["authority_invariants"]["fallback_activation_count"]
        == 0
    )
    assert persisted_evidence["authority_invariants"]["registry_mutation_count"] == 0
    assert (
        persisted_evidence["authority_invariants"]["qualification_promotion_count"]
        == 0
    )


def test_context_target_requires_matching_evidence_before_dispatch(
    tmp_path,
    plan,
    row,
):
    dispatcher = RecordingDispatcher(plan, row)
    with pytest.raises(ValueError, match="matching evidence"):
        _execute(
            plan,
            row,
            dispatcher=dispatcher,
            validation_context_target=(
                tmp_path
                / live.APPROVED_EVIDENCE_DIRECTORY
                / "orphan.validation-context.json"
            ),
            repository_root=tmp_path,
        )
    assert dispatcher.calls == []


def test_real_9c7b_artifact_is_unchanged_and_contract_universe_is_current(plan):
    artifact_bytes = REAL_9C7B.read_bytes()
    universe = live.build_live_qualification_universe(plan)
    eligible = [item for item in universe if item["live_qualification_eligible"]]
    blocked = [item for item in universe if not item["live_qualification_eligible"]]
    fake_context = REAL_9C7B.with_name(
        f"{REAL_9C7B.stem}.validation-context.json"
    )

    assert sha256(artifact_bytes).hexdigest() == REAL_9C7B_SHA256
    assert stat.S_IMODE(REAL_9C7B.stat().st_mode) == 0o600
    assert not fake_context.exists()
    assert len(universe) == 44
    assert len(eligible) == 44
    assert blocked == []
    assert tuple(dict.fromkeys(item["workload_id"] for item in eligible)) == (
        WORKLOAD_ORDER
    )
