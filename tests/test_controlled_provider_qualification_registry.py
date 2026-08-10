from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import socket
import stat

import pytest

from src.evaluation import controlled_provider_benchmark_evidence_runtime as evidence_runtime
from src.evaluation import controlled_provider_benchmark_harness as harness
from src.evaluation import controlled_provider_benchmark_human_review as human_review
from src.evaluation import controlled_provider_qualification_registry as registry
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
)
from src.evaluation.provider_fixture_benchmark import load_fixture_case_corpus


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / "src/evaluation/controlled_provider_qualification_registry.py"
FIXED_EXECUTION_TIME = "2026-07-25T00:00:00Z"
FIXED_REVIEW_TIME = "2026-07-26T14:30:00Z"
TASK_FINGERPRINT = "a" * 64
CHANGED_TASK_FINGERPRINT = "b" * 64
REVIEW_REQUIRED = {
    "jd_intelligence",
    "resume_fallback_ranking",
    "ambiguous_resume_adjudication",
    "critic_evaluation",
    "tailoring_generation",
    "tailoring_refinement",
    "tailoring_judge",
    "manual_scan_phrase",
    "manual_provider_preview",
}
REVIEW_NOT_REQUIRED = {
    "skill_extraction",
    "job_fit_evaluation",
    "grounded_rag_answer",
}


class GoldenTransport:
    def __init__(self, outputs):
        self.outputs = deepcopy(outputs)
        self.calls = []

    def __call__(self, packet, timeout_seconds):
        self.calls.append((deepcopy(packet), timeout_seconds))
        return {
            "normalized_output": deepcopy(self.outputs[packet["case_alias"]]),
            "provider": packet["provider"],
            "model": packet["model"],
            "latency_ms": 5.0,
            "input_token_count": 11,
            "output_token_count": 7,
            "provider_outcome_category": "success",
        }


@pytest.fixture(scope="module")
def controlled_inputs():
    plan = build_controlled_provider_benchmark_plan()
    pricing = harness.load_synthetic_pricing_fixture()
    authorization = harness.load_synthetic_authorization_fixture(
        plan=plan,
        pricing=pricing,
    )
    corpus = load_fixture_case_corpus()
    outputs = {
        transmission["case_alias"]: deepcopy(case["expected_output"])
        for transmission, case in zip(
            plan["transmission_review"], corpus["cases"]
        )
        if transmission["eligible_for_later_controlled_transmission"]
    }
    return plan, authorization, pricing, outputs


@pytest.fixture(scope="module")
def completed_evidence(controlled_inputs):
    plan, authorization, pricing, outputs = controlled_inputs
    transport = GoldenTransport(outputs)
    evidence = evidence_runtime.execute_provider_neutral_evidence_run(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        transport=transport,
        execution_time_source=lambda: FIXED_EXECUTION_TIME,
    )
    assert len(transport.calls) == 44
    return evidence


def _summary(evidence, workload_id, *, provider="groq"):
    return next(
        row
        for row in evidence["grading_summaries"]
        if row["workload_id"] == workload_id and row["provider"] == provider
    )


def _review_record(controlled_inputs, evidence, workload_id, decision="approved"):
    plan, authorization, pricing, _outputs = controlled_inputs
    summary = _summary(evidence, workload_id)
    return human_review.build_post_result_human_review_record(
        evidence=evidence,
        schedule_key=summary["schedule_key"],
        decision=decision,
        reviewer_id="registry-reviewer-01",
        review_time_source=lambda: FIXED_REVIEW_TIME,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )


def _qualification_input(
    controlled_inputs,
    evidence,
    workload_id,
    *,
    review_record=None,
    tested_task_contract_sha256=TASK_FINGERPRINT,
):
    plan, authorization, pricing, _outputs = controlled_inputs
    summary = _summary(evidence, workload_id)
    evidence_digest = evidence_runtime.provider_neutral_run_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    if review_record is None:
        review_digest = None
    else:
        review_digest = human_review.post_result_human_review_sha256(
            review_record,
            evidence=evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )
    return summary["schedule_key"], {
        "evidence": deepcopy(evidence),
        "evidence_sha256": evidence_digest,
        "authorization": deepcopy(authorization),
        "pricing": deepcopy(pricing),
        "schedule_key": summary["schedule_key"],
        "tested_task_contract_sha256": tested_task_contract_sha256,
        "review_record": deepcopy(review_record),
        "review_sha256": review_digest,
    }


def _build_with_input(
    controlled_inputs,
    evidence,
    workload_id,
    *,
    review_record=None,
    tested_task_contract_sha256=TASK_FINGERPRINT,
    current_task_contract_sha256=TASK_FINGERPRINT,
    existing_registry=None,
):
    plan = controlled_inputs[0]
    schedule_key, qualification_input = _qualification_input(
        controlled_inputs,
        evidence,
        workload_id,
        review_record=review_record,
        tested_task_contract_sha256=tested_task_contract_sha256,
    )
    return registry.build_provider_qualification_registry(
        plan=plan,
        current_task_contract_sha256_by_workload={
            workload_id: current_task_contract_sha256
        },
        qualification_inputs_by_schedule_key={
            schedule_key: qualification_input
        },
        existing_registry=existing_registry,
    )


def _cell(payload, workload_id, *, provider="groq"):
    return next(
        row
        for row in payload["cells"]
        if row["workload_id"] == workload_id and row["provider"] == provider
    )


def _mutated_evidence(controlled_inputs, completed_evidence, workload_id, mutation):
    plan, authorization, pricing, _outputs = controlled_inputs
    checkpoint = deepcopy(completed_evidence["checkpoint"])
    target = _summary(checkpoint, workload_id)
    mutation(target)
    return evidence_runtime.build_provider_neutral_run_evidence(
        checkpoint=checkpoint,
        execution_at_utc=completed_evidence["execution_at_utc"],
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )


def _iter_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).lower()
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def test_empty_registry_derives_exact_44_pending_cells(controlled_inputs):
    payload = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0]
    )
    counts = {}
    for cell in payload["cells"]:
        key = f"{cell['provider']}/{cell['model']}"
        counts[key] = counts.get(key, 0) + 1

    assert len(payload["cells"]) == 44
    assert {cell["status"] for cell in payload["cells"]} == {"pending"}
    assert counts == {
        "groq/openai/gpt-oss-20b": 12,
        "groq/openai/gpt-oss-120b": 10,
        "openai/gpt-5-mini": 12,
        "openai/gpt-5.1": 10,
    }
    assert not any(
        cell["workload_id"] == "skill_extraction"
        and cell["provider"] == "groq"
        and cell["model"] == "openai/gpt-oss-120b"
        for cell in payload["cells"]
    )


def test_registry_universe_matches_current_plan_order(controlled_inputs):
    plan, authorization, _pricing, _outputs = controlled_inputs
    payload = registry.build_provider_qualification_registry(plan=plan)
    schedule = harness.build_execution_schedule(
        plan=plan,
        authorization=authorization,
    )

    assert [
        (
            row["execution_order"],
            row["schedule_key"],
            row["case_alias"],
            row["workload_id"],
            row["provider"],
            row["model"],
        )
        for row in payload["cells"]
    ] == [
        (
            row["execution_order"],
            row["schedule_key"],
            row["case_alias"],
            row["workload_id"],
            row["provider"],
            row["model"],
        )
        for row in schedule
    ]


def test_status_is_derived_without_caller_qualified_boolean():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_provider_qualification_registry"
    )
    arguments = {
        argument.arg
        for argument in function.args.args + function.args.kwonlyargs
    }

    assert "qualified" not in arguments
    assert "status" not in arguments
    assert '"qualified"' not in registry._QUALIFICATION_INPUT_FIELDS


def test_exact_human_review_split_is_enforced(controlled_inputs):
    payload = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0]
    )
    required = {
        cell["workload_id"]
        for cell in payload["cells"]
        if cell["human_review_required"]
    }
    not_required = {
        cell["workload_id"]
        for cell in payload["cells"]
        if not cell["human_review_required"]
    }

    assert required == REVIEW_REQUIRED
    assert not_required == REVIEW_NOT_REQUIRED


def test_valid_automated_review_cell_qualifies_without_review(
    controlled_inputs,
    completed_evidence,
):
    payload = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
    )
    cell = _cell(payload, "skill_extraction")

    assert cell["status"] == "qualified"
    assert cell["review_sha256"] is None
    assert cell["status_reasons"] == ["qualification_requirements_satisfied"]


def test_missing_task_contract_fingerprint_keeps_passing_evidence_pending(
    controlled_inputs,
    completed_evidence,
):
    payload = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
        current_task_contract_sha256=None,
    )
    cell = _cell(payload, "skill_extraction")

    assert cell["status"] == "pending"
    assert cell["status_reasons"] == ["task_contract_missing"]


def test_missing_tested_task_binding_keeps_passing_evidence_pending(
    controlled_inputs,
    completed_evidence,
):
    payload = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
        tested_task_contract_sha256=None,
    )
    cell = _cell(payload, "skill_extraction")

    assert cell["status"] == "pending"
    assert cell["status_reasons"] == ["task_contract_binding_missing"]


@pytest.mark.parametrize("fingerprint", ["", "A" * 64, "g" * 64, "a" * 63, 1])
def test_malformed_current_task_fingerprint_is_rejected(
    controlled_inputs,
    fingerprint,
):
    with pytest.raises(ValueError, match="task-contract fingerprint"):
        registry.build_provider_qualification_registry(
            plan=controlled_inputs[0],
            current_task_contract_sha256_by_workload={
                "skill_extraction": fingerprint
            },
        )


def test_required_review_missing_is_pending(
    controlled_inputs,
    completed_evidence,
):
    payload = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
    )
    cell = _cell(payload, "jd_intelligence")

    assert cell["status"] == "pending"
    assert cell["status_reasons"] == ["review_missing"]


def test_matching_approved_review_qualifies_required_cell(
    controlled_inputs,
    completed_evidence,
):
    review_record = _review_record(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
    )
    payload = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
        review_record=review_record,
    )
    cell = _cell(payload, "jd_intelligence")

    assert cell["status"] == "qualified"
    assert cell["review_sha256"] is not None


def test_matching_rejected_review_rejects_required_cell(
    controlled_inputs,
    completed_evidence,
):
    review_record = _review_record(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
        decision="rejected",
    )
    payload = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
        review_record=review_record,
    )
    cell = _cell(payload, "jd_intelligence")

    assert cell["status"] == "rejected"
    assert cell["status_reasons"] == ["review_rejected"]


def test_review_for_different_evidence_cannot_satisfy_cell(
    controlled_inputs,
    completed_evidence,
):
    old_review = _review_record(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
    )
    plan, authorization, pricing, _outputs = controlled_inputs
    changed_evidence = evidence_runtime.build_provider_neutral_run_evidence(
        checkpoint=completed_evidence["checkpoint"],
        execution_at_utc="2026-07-25T00:00:01Z",
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )

    with pytest.raises(ValueError, match="binding mismatch"):
        _build_with_input(
            controlled_inputs,
            changed_evidence,
            "jd_intelligence",
            review_record=old_review,
        )


def test_invalid_evidence_and_claimed_digest_mismatch_fail_closed(
    controlled_inputs,
    completed_evidence,
):
    schedule_key, qualification_input = _qualification_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
    )
    invalid = deepcopy(qualification_input)
    invalid["evidence"]["execution_at_utc"] = "tampered"
    with pytest.raises(ValueError):
        registry.build_provider_qualification_registry(
            plan=controlled_inputs[0],
            current_task_contract_sha256_by_workload={
                "skill_extraction": TASK_FINGERPRINT
            },
            qualification_inputs_by_schedule_key={schedule_key: invalid},
        )

    wrong_digest = deepcopy(qualification_input)
    wrong_digest["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="evidence SHA-256 mismatch"):
        registry.build_provider_qualification_registry(
            plan=controlled_inputs[0],
            current_task_contract_sha256_by_workload={
                "skill_extraction": TASK_FINGERPRINT
            },
            qualification_inputs_by_schedule_key={
                schedule_key: wrong_digest
            },
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("workload_id", "jd_intelligence"),
        ("provider", "openai"),
        ("model", "gpt-5-mini"),
        ("case_alias", "case_identity_tampered"),
    ],
)
def test_evidence_identity_mismatch_fails_closed(
    controlled_inputs,
    completed_evidence,
    field,
    replacement,
):
    plan, authorization, pricing, _outputs = controlled_inputs
    checkpoint = deepcopy(completed_evidence["checkpoint"])
    summary = _summary(checkpoint, "skill_extraction")
    schedule_key = summary["schedule_key"]
    summary[field] = replacement
    altered = evidence_runtime.build_provider_neutral_run_evidence(
        checkpoint=checkpoint,
        execution_at_utc=completed_evidence["execution_at_utc"],
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    _original_key, qualification_input = _qualification_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
    )
    qualification_input["evidence"] = altered
    qualification_input["evidence_sha256"] = (
        evidence_runtime.provider_neutral_run_evidence_sha256(
            altered,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )
    )

    with pytest.raises(ValueError, match="identity"):
        registry.build_provider_qualification_registry(
            plan=plan,
            current_task_contract_sha256_by_workload={
                "skill_extraction": TASK_FINGERPRINT
            },
            qualification_inputs_by_schedule_key={
                schedule_key: qualification_input
            },
        )


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda row: row.update(schema_valid=False), "schema_invalid"),
        (
            lambda row: row.update(normalization_succeeded=False),
            "normalization_failed",
        ),
        (
            lambda row: row.update(quality_gate_passed=False),
            "quality_gate_failed",
        ),
        (
            lambda row: row["hard_failures"].update(hallucination=True),
            "hard_failure",
        ),
    ],
)
def test_failed_benchmark_evidence_is_rejected(
    controlled_inputs,
    completed_evidence,
    mutation,
    reason,
):
    failed = _mutated_evidence(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
        mutation,
    )
    payload = _build_with_input(
        controlled_inputs,
        failed,
        "skill_extraction",
    )
    cell = _cell(payload, "skill_extraction")

    assert cell["status"] == "rejected"
    assert reason in cell["status_reasons"]
    assert "benchmark_failed" in cell["status_reasons"]


def test_human_approval_cannot_override_failed_evidence(
    controlled_inputs,
    completed_evidence,
):
    approval = _review_record(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
    )
    failed = _mutated_evidence(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
        lambda row: row["hard_failures"].update(hallucination=True),
    )

    with pytest.raises(ValueError):
        _build_with_input(
            controlled_inputs,
            failed,
            "jd_intelligence",
            review_record=approval,
        )


def test_cell_represents_all_required_current_and_tested_bindings(
    controlled_inputs,
    completed_evidence,
):
    payload = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
    )
    cell = _cell(payload, "skill_extraction")

    assert cell["current_model_catalog_snapshot_sha256"] == payload[
        "current_bindings"
    ]["model_catalog_snapshot_sha256"]
    assert cell["tested_model_catalog_snapshot_sha256"] == cell[
        "current_model_catalog_snapshot_sha256"
    ]
    assert cell["tested_benchmark_contract_sha256"] == cell[
        "current_benchmark_contract_sha256"
    ]
    assert cell["tested_controlled_plan_sha256"] == cell[
        "current_controlled_plan_sha256"
    ]
    assert cell["tested_task_contract_sha256"] == TASK_FINGERPRINT
    assert cell["evidence_sha256"] is not None
    assert cell["qualification_binding_sha256"] is not None


def test_task_contract_change_makes_prior_qualification_stale(
    controlled_inputs,
    completed_evidence,
):
    qualified = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
    )
    reconciled = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0],
        current_task_contract_sha256_by_workload={
            "skill_extraction": CHANGED_TASK_FINGERPRINT
        },
        existing_registry=qualified,
    )
    cell = _cell(reconciled, "skill_extraction")

    assert cell["status"] == "stale"
    assert cell["status_reasons"] == ["task_contract_binding_stale"]
    assert cell["status"] not in {"pending", "rejected", "qualified"}


def test_missing_tested_binding_remains_pending_when_current_binding_changes(
    controlled_inputs,
    completed_evidence,
):
    pending = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
        tested_task_contract_sha256=None,
    )
    reconciled = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0],
        current_task_contract_sha256_by_workload={
            "skill_extraction": CHANGED_TASK_FINGERPRINT
        },
        existing_registry=pending,
    )
    cell = _cell(reconciled, "skill_extraction")

    assert cell["status"] == "pending"
    assert cell["status_reasons"] == ["task_contract_binding_missing"]


@pytest.mark.parametrize(
    ("binding_field", "reason"),
    [
        ("model_catalog_snapshot_sha256", "catalog_binding_stale"),
        ("benchmark_contract_sha256", "benchmark_contract_binding_stale"),
        ("controlled_plan_sha256", "controlled_plan_binding_stale"),
    ],
)
def test_current_static_binding_change_makes_prior_qualification_stale(
    monkeypatch,
    controlled_inputs,
    completed_evidence,
    binding_field,
    reason,
):
    qualified = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
    )
    original = registry.build_current_qualification_bindings

    def changed(plan):
        bindings = original(plan)
        bindings[binding_field] = "c" * 64
        return bindings

    monkeypatch.setattr(registry, "build_current_qualification_bindings", changed)
    reconciled = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0],
        current_task_contract_sha256_by_workload={
            "skill_extraction": TASK_FINGERPRINT
        },
        existing_registry=qualified,
    )
    cell = _cell(reconciled, "skill_extraction")

    assert cell["status"] == "stale"
    assert reason in cell["status_reasons"]


def test_old_evidence_or_review_identity_cannot_silently_survive_update(
    controlled_inputs,
    completed_evidence,
):
    review_record = _review_record(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
    )
    first = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "jd_intelligence",
        review_record=review_record,
    )
    plan, authorization, pricing, _outputs = controlled_inputs
    changed_evidence = evidence_runtime.build_provider_neutral_run_evidence(
        checkpoint=completed_evidence["checkpoint"],
        execution_at_utc="2026-07-25T00:00:01Z",
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    changed_review = _review_record(
        controlled_inputs,
        changed_evidence,
        "jd_intelligence",
    )
    second = _build_with_input(
        controlled_inputs,
        changed_evidence,
        "jd_intelligence",
        review_record=changed_review,
        existing_registry=first,
    )

    first_cell = _cell(first, "jd_intelligence")
    second_cell = _cell(second, "jd_intelligence")
    assert second_cell["status"] == "qualified"
    assert second_cell["evidence_sha256"] != first_cell["evidence_sha256"]
    assert second_cell["review_sha256"] != first_cell["review_sha256"]
    assert second_cell["qualification_binding_sha256"] != first_cell[
        "qualification_binding_sha256"
    ]


def test_unrelated_cell_update_does_not_mutate_other_cells(
    controlled_inputs,
    completed_evidence,
):
    initial = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0]
    )
    updated = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
        existing_registry=initial,
    )

    before = {
        (row["workload_id"], row["provider"], row["model"]): row
        for row in initial["cells"]
        if row["workload_id"] != "skill_extraction"
    }
    after = {
        (row["workload_id"], row["provider"], row["model"]): row
        for row in updated["cells"]
        if row["workload_id"] != "skill_extraction"
    }
    assert after == before


def test_registry_order_serialization_and_digest_are_deterministic(
    controlled_inputs,
):
    first = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0]
    )
    second = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0],
        existing_registry=first,
    )

    assert second == first
    assert [row["execution_order"] for row in first["cells"]] == list(
        range(1, 45)
    )
    assert len(
        {
            (row["workload_id"], row["provider"], row["model"])
            for row in first["cells"]
        }
    ) == 44
    assert registry.serialize_provider_qualification_registry(
        first,
        plan=controlled_inputs[0],
    ) == registry.serialize_provider_qualification_registry(
        second,
        plan=controlled_inputs[0],
    )
    assert registry.provider_qualification_registry_sha256(
        first,
        plan=controlled_inputs[0],
    ) == registry.provider_qualification_registry_sha256(
        second,
        plan=controlled_inputs[0],
    )


def test_registry_validator_rejects_noncanonical_evidence_timestamp(
    controlled_inputs,
    completed_evidence,
):
    payload = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
    )
    cell = _cell(payload, "skill_extraction")
    cell["evaluated_at_utc"] = "2026-07-24T20:00:00-04:00"

    with pytest.raises(ValueError, match="evaluated_at_utc"):
        registry.validate_provider_qualification_registry(payload)


def test_registry_retains_no_raw_provider_or_user_data(
    controlled_inputs,
    completed_evidence,
):
    payload = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
    )
    serialized = json.dumps(payload, sort_keys=True).lower()
    keys = set(_iter_keys(payload))

    assert len(serialized.encode("utf-8")) < 200_000
    for prohibited in (
        "raw_response",
        "normalized_output",
        "prompt",
        "reasoning",
        "credential",
        "api_key",
        "request_id",
        "checkpoint",
        "grading_summaries",
        "reviewer_id",
    ):
        assert prohibited not in keys
    assert "evidence_payload" not in keys
    assert "review_record" not in keys


def test_registry_contains_no_recommendation_ranking_or_user_override_fields(
    controlled_inputs,
):
    payload = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0]
    )
    keys = set(_iter_keys(payload))

    for prohibited in (
        "recommended_model",
        "best_model",
        "winner",
        "rank",
        "routing_priority",
        "selected_model",
        "user_override",
        "preferred_provider_resolution",
    ):
        assert prohibited not in keys


def test_initial_and_atomic_registry_persistence_are_safe_and_immutable(
    tmp_path,
    controlled_inputs,
    completed_evidence,
):
    plan = controlled_inputs[0]
    initial = registry.build_provider_qualification_registry(plan=plan)
    updated = _build_with_input(
        controlled_inputs,
        completed_evidence,
        "skill_extraction",
        existing_registry=initial,
    )
    evidence_snapshot = json.dumps(completed_evidence, sort_keys=True).encode("utf-8")
    evidence_file = tmp_path / "evidence-input.json"
    review_file = tmp_path / "review-input.json"
    evidence_file.write_bytes(evidence_snapshot)
    review_file.write_text("{}", encoding="utf-8")
    review_snapshot = review_file.read_bytes()
    target = tmp_path / registry.REGISTRY_ARTIFACT_PATH

    registry.write_initial_provider_qualification_registry(
        target,
        initial,
        repository_root=tmp_path,
        plan=plan,
    )
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    prior_digest = registry.provider_qualification_registry_sha256(initial)
    registry.replace_provider_qualification_registry_atomic(
        target,
        updated,
        expected_prior_sha256=prior_digest,
        repository_root=tmp_path,
        plan=plan,
    )
    assert registry.load_provider_qualification_registry(
        target,
        repository_root=tmp_path,
        plan=plan,
    ) == updated
    assert evidence_file.read_bytes() == evidence_snapshot
    assert review_file.read_bytes() == review_snapshot
    with pytest.raises(ValueError, match="prior digest mismatch"):
        registry.replace_provider_qualification_registry_atomic(
            target,
            initial,
            expected_prior_sha256=prior_digest,
            repository_root=tmp_path,
            plan=plan,
        )


def test_registry_persistence_rejects_outside_and_symlink_paths(
    tmp_path,
    controlled_inputs,
):
    plan = controlled_inputs[0]
    payload = registry.build_provider_qualification_registry(plan=plan)

    with pytest.raises(ValueError, match="approved namespace"):
        registry.write_initial_provider_qualification_registry(
            tmp_path / "registry.json",
            payload,
            repository_root=tmp_path,
            plan=plan,
        )
    assert not (tmp_path / "outputs").exists()

    root = tmp_path / "symlink-root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "outputs").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="unsafe"):
        registry.write_initial_provider_qualification_registry(
            root / registry.REGISTRY_ARTIFACT_PATH,
            payload,
            repository_root=root,
            plan=plan,
        )


def test_invalid_registry_fails_before_creating_persistence_namespace(
    tmp_path,
    controlled_inputs,
):
    plan = controlled_inputs[0]
    payload = registry.build_provider_qualification_registry(plan=plan)
    payload["cells"][0]["status"] = "not-a-registry-status"
    target = tmp_path / registry.REGISTRY_ARTIFACT_PATH

    with pytest.raises(ValueError, match="status"):
        registry.write_initial_provider_qualification_registry(
            target,
            payload,
            repository_root=tmp_path,
            plan=plan,
        )
    assert not (tmp_path / "outputs").exists()


def test_focused_tests_create_no_repository_registry_artifact():
    assert not (ROOT / registry.REGISTRY_ARTIFACT_PATH).exists()


def test_owner_has_no_sdk_transport_environment_user_or_application_access():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert not {"groq", "openai", "dotenv", "requests", "httpx"}.intersection(imports)
    assert "controlled_groq_canary_transport" not in source
    assert "controlled_openai_canary_transport" not in source
    assert "execute_provider_neutral_evidence_run" not in source
    assert "user_provider_runtime" not in source
    assert "user_ai_settings" not in source
    assert "operator_decisions" not in source
    assert "DATABASE_URL" not in source
    assert "API_KEY" not in source
    assert "getenv" not in source
    assert not any(
        isinstance(node, ast.Attribute) and node.attr in {"getenv", "environ"}
        for node in ast.walk(tree)
    )


def test_registry_construction_never_reaches_network(
    monkeypatch,
    controlled_inputs,
):
    def blocked(*_args, **_kwargs):
        raise AssertionError("network access is prohibited")

    monkeypatch.setattr(socket, "socket", blocked)
    payload = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0]
    )
    assert len(payload["cells"]) == 44


def test_44_cell_plan_and_live_default_off_remain_unchanged(controlled_inputs):
    plan = controlled_inputs[0]

    assert plan["request_counts"]["maximum_total_requests"] == 44
    assert plan["request_counts"]["maximum_requests_per_model"] == {
        "groq/openai/gpt-oss-20b": 12,
        "groq/openai/gpt-oss-120b": 10,
        "openai/gpt-5-mini": 12,
        "openai/gpt-5.1": 10,
    }
    assert plan["authority_invariants"]["live_execution_authorized"] is False
    assert plan["authority_invariants"]["routing_change_allowed"] is False


def test_no_production_source_imports_qualification_registry_owner():
    references = []
    for path in (ROOT / "src").rglob("*.py"):
        if path == OWNER_PATH or "evaluation" in path.relative_to(ROOT / "src").parts:
            continue
        if "controlled_provider_qualification_registry" in path.read_text(
            encoding="utf-8"
        ):
            references.append(path.relative_to(ROOT).as_posix())

    assert references == []
