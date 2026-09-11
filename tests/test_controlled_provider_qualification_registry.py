from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
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
from src.evaluation.production_task_contract_fingerprints import (
    build_all_production_task_contract_fingerprints,
)


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


def _repository_registry_artifact_snapshot():
    artifact_path = ROOT / registry.REGISTRY_ARTIFACT_PATH
    try:
        artifact_stat = artifact_path.lstat()
    except FileNotFoundError:
        return (False, False, False, None, None, None, None)

    is_file = stat.S_ISREG(artifact_stat.st_mode)
    is_symlink = stat.S_ISLNK(artifact_stat.st_mode)
    return (
        True,
        is_file,
        is_symlink,
        stat.S_IMODE(artifact_stat.st_mode),
        artifact_stat.st_size,
        sha256(artifact_path.read_bytes()).hexdigest() if is_file else None,
        artifact_path.readlink().as_posix() if is_symlink else None,
    )


@pytest.fixture(scope="module", autouse=True)
def repository_registry_artifact_baseline():
    return _repository_registry_artifact_snapshot()


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
    assert len(transport.calls) == 45
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


def test_empty_registry_derives_exact_45_pending_cells(controlled_inputs):
    payload = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0]
    )
    counts = {}
    for cell in payload["cells"]:
        key = f"{cell['provider']}/{cell['model']}"
        counts[key] = counts.get(key, 0) + 1

    assert len(payload["cells"]) == 45
    assert {cell["status"] for cell in payload["cells"]} == {"pending"}
    assert counts == {
        "groq/openai/gpt-oss-20b": 12,
        "groq/openai/gpt-oss-120b": 11,
        "openai/gpt-5-mini": 12,
        "openai/gpt-5.1": 10,
    }
    assert sum(
        cell["workload_id"] == "skill_extraction"
        and cell["provider"] == "groq"
        and cell["model"] == "openai/gpt-oss-120b"
        for cell in payload["cells"]
    ) == 1


def test_new_readback_fingerprint_alone_leaves_ambiguous_cells_pending(
    controlled_inputs,
):
    fingerprints = build_all_production_task_contract_fingerprints()
    payload = registry.build_provider_qualification_registry(
        plan=controlled_inputs[0],
        current_task_contract_sha256_by_workload=fingerprints,
    )
    ambiguous = [
        cell
        for cell in payload["cells"]
        if cell["workload_id"] == "ambiguous_resume_adjudication"
    ]
    preview = [
        cell
        for cell in payload["cells"]
        if cell["workload_id"] == "manual_provider_preview"
    ]

    assert len(ambiguous) == 4
    assert all(cell["current_task_contract_sha256"] for cell in ambiguous)
    assert all(cell["status"] == "pending" for cell in ambiguous)
    assert all("evidence_missing" in cell["status_reasons"] for cell in ambiguous)
    assert all(
        "task_contract_missing" not in cell["status_reasons"]
        for cell in ambiguous
    )
    assert all(cell["current_task_contract_sha256"] for cell in preview)
    assert all(cell["status"] == "pending" for cell in preview)
    assert all("evidence_missing" in cell["status_reasons"] for cell in preview)
    assert all("review_missing" in cell["status_reasons"] for cell in preview)
    assert all(
        "task_contract_missing" not in cell["status_reasons"]
        for cell in preview
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
        range(1, 46)
    )
    assert len(
        {
            (row["workload_id"], row["provider"], row["model"])
            for row in first["cells"]
        }
    ) == 45
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


def test_focused_tests_create_no_repository_registry_artifact(
    repository_registry_artifact_baseline,
):
    assert (
        _repository_registry_artifact_snapshot()
        == repository_registry_artifact_baseline
    )


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
    assert len(payload["cells"]) == 45


def test_45_cell_plan_and_live_default_off_remain_unchanged(controlled_inputs):
    plan = controlled_inputs[0]

    assert plan["request_counts"]["maximum_total_requests"] == 45
    assert plan["request_counts"]["maximum_requests_per_model"] == {
        "groq/openai/gpt-oss-20b": 12,
        "groq/openai/gpt-oss-120b": 11,
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

    assert sorted(references) == [
        "src/app/provider_model_routing_service.py"
    ]


# ---------------------------------------------------------------------------
# Stage 2A: additive renderer-bound generation + migration primitives.
# V1 remains the authoritative representation; V2 is not activated here.
# ---------------------------------------------------------------------------


CURRENT_V1_REGISTRY_SHA256 = (
    "6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f"
)
CURRENT_CONTROLLED_PLAN_SHA256 = (
    "f2dcf5345442009915819432a9c1fc9342de40561eb6824c1518dcd31e99d3bf"
)
STAGE5C_CURRENT_CONTROLLED_PLAN_SHA256 = (
    "bacc7eaa4524199ba293e2d50232f5a8c6cf61014ad8dc89c3dd30d334654162"
)
CURRENT_FIXTURE_CORPUS_SHA256 = (
    "59180e4064dd74759c6ecd8630478225b191f942b68fb1880e172fe07ee80aec"
)
PROVEN_SUPERSEDED_IDENTITIES = (
    ("job_fit_evaluation", "groq", "openai/gpt-oss-120b"),
    ("job_fit_evaluation", "groq", "openai/gpt-oss-20b"),
    ("job_fit_evaluation", "openai", "gpt-5-mini"),
    ("job_fit_evaluation", "openai", "gpt-5.1"),
    ("tailoring_generation", "groq", "openai/gpt-oss-120b"),
)


def _stage2a_on_disk_registry():
    return json.loads(
        (
            ROOT
            / "outputs"
            / "provider_benchmark"
            / "provider-qualification-registry.json"
        ).read_text(encoding="utf-8")
    )


def _stage2a_current_semantics(registry_payload):
    from src.evaluation import controlled_production_parity_benchmark as parity

    corpus = load_fixture_case_corpus()
    plan = build_controlled_provider_benchmark_plan(corpus=corpus)
    return {
        workload_id: parity.workload_qualification_semantics_sha256(
            workload_id, plan=plan, corpus=corpus
        )
        for workload_id in sorted(
            {cell["workload_id"] for cell in registry_payload["cells"]}
        )
    }


def _stage2a_projection(**overrides):
    payload = _stage2a_on_disk_registry()
    kwargs = {
        "current_workload_qualification_semantics_sha256_by_workload": (
            _stage2a_current_semantics(payload)
        ),
        "superseded_cell_identities": PROVEN_SUPERSEDED_IDENTITIES,
    }
    kwargs.update(overrides)
    return payload, registry.project_registry_to_renderer_bound_generation(
        payload, **kwargs
    )


def test_stage2a_v1_authority_is_unchanged():
    from src.evaluation import provider_model_recommendation_policy as policy
    from src.evaluation.controlled_provider_benchmark_plan import (
        controlled_provider_benchmark_plan_sha256,
        legacy_case_alias_map,
    )
    from src.evaluation.provider_fixture_benchmark import (
        fixture_case_corpus_sha256,
    )

    payload = _stage2a_on_disk_registry()
    corpus = load_fixture_case_corpus()

    assert registry.REGISTRY_CONTRACT_VERSION == (
        "controlled-provider-qualification-registry-v1"
    )
    assert registry.QUALIFICATION_STATUSES == (
        "pending",
        "qualified",
        "rejected",
        "stale",
    )
    assert registry.validate_provider_qualification_registry(deepcopy(payload))
    assert registry.provider_qualification_registry_sha256(payload) == (
        CURRENT_V1_REGISTRY_SHA256
    )
    assert fixture_case_corpus_sha256(corpus) == CURRENT_FIXTURE_CORPUS_SHA256
    assert controlled_provider_benchmark_plan_sha256(
        build_controlled_provider_benchmark_plan(corpus=corpus)
    ) == STAGE5C_CURRENT_CONTROLLED_PLAN_SHA256
    assert STAGE5C_CURRENT_CONTROLLED_PLAN_SHA256 != CURRENT_CONTROLLED_PLAN_SHA256
    assert len(legacy_case_alias_map(corpus)) == 15
    assert len(
        policy.build_provider_model_recommendation_policy(payload)["workloads"]
    ) == 12


def test_stage2a_generation_vocabulary_is_exactly_two():
    assert registry.QUALIFICATION_SEMANTICS_GENERATIONS == (
        "legacy_no_renderer_binding",
        "renderer_bound_v1",
    )
    for reason in (
        "workload_semantics_binding_missing",
        "workload_semantics_binding_stale",
        "renderer_semantics_superseded",
    ):
        assert reason in registry._RENDERER_BOUND_STATUS_REASONS
        assert reason not in registry._STATUS_REASONS


def test_stage2a_migration_projects_the_expected_44_cells():
    source, projected = _stage2a_projection()

    assert registry.validate_renderer_bound_qualification_registry(projected)
    assert len(projected["cells"]) == len(source["cells"]) == 44

    by_identity = {
        (cell["workload_id"], cell["provider"], cell["model"]): cell
        for cell in source["cells"]
    }
    transitions = {}
    for cell in projected["cells"]:
        identity = (cell["workload_id"], cell["provider"], cell["model"])
        key = (by_identity[identity]["status"], cell["status"])
        transitions[key] = transitions.get(key, 0) + 1

    assert transitions == {
        ("qualified", "stale"): 16,
        ("rejected", "rejected"): 22,
        ("stale", "stale"): 6,
    }
    statuses = {}
    for cell in projected["cells"]:
        statuses[cell["status"]] = statuses.get(cell["status"], 0) + 1
    assert statuses == {"stale": 22, "rejected": 22}


def test_stage2a_legacy_cells_never_claim_renderer_bound_qualification():
    _source, projected = _stage2a_projection()

    for cell in projected["cells"]:
        assert cell["qualification_semantics_generation"] == (
            "legacy_no_renderer_binding"
        )
        assert cell["tested_workload_qualification_semantics_sha256"] is None
        assert cell["status"] != "qualified"
        if cell["status"] == "stale":
            assert "workload_semantics_binding_missing" in cell["status_reasons"]
        assert "qualification_requirements_satisfied" not in cell["status_reasons"]


def test_stage2a_superseded_markers_are_explicit_and_fail_closed():
    _source, projected = _stage2a_projection()

    marked = {
        (cell["workload_id"], cell["provider"], cell["model"])
        for cell in projected["cells"]
        if "renderer_semantics_superseded" in cell["status_reasons"]
    }
    assert marked == set(PROVEN_SUPERSEDED_IDENTITIES)
    for cell in projected["cells"]:
        identity = (cell["workload_id"], cell["provider"], cell["model"])
        if identity in marked and identity[0] == "job_fit_evaluation":
            assert cell["status"] == "rejected"

    payload = _stage2a_on_disk_registry()
    with pytest.raises(ValueError):
        registry.project_registry_to_renderer_bound_generation(
            payload,
            current_workload_qualification_semantics_sha256_by_workload=(
                _stage2a_current_semantics(payload)
            ),
            superseded_cell_identities=[
                ("not_a_workload", "groq", "openai/gpt-oss-20b")
            ],
        )
    with pytest.raises(ValueError):
        registry.project_registry_to_renderer_bound_generation(
            payload,
            current_workload_qualification_semantics_sha256_by_workload={},
        )


def test_stage2a_migration_preserves_every_provenance_field():
    source, projected = _stage2a_projection()

    by_identity = {
        (cell["workload_id"], cell["provider"], cell["model"]): cell
        for cell in source["cells"]
    }
    preserved = {
        field: 0
        for field in (
            "evidence_sha256",
            "review_sha256",
            "tested_controlled_plan_sha256",
            "tested_task_contract_sha256",
            "evaluated_at_utc",
            "reviewed_at_utc",
            "schedule_key",
            "case_alias",
        )
    }
    for cell in projected["cells"]:
        original = by_identity[
            (cell["workload_id"], cell["provider"], cell["model"])
        ]
        for field in preserved:
            if cell[field] == original[field]:
                preserved[field] += 1

    assert all(count == 44 for count in preserved.values()), preserved
    # The source registry is never mutated by the projection.
    assert registry.provider_qualification_registry_sha256(source) == (
        CURRENT_V1_REGISTRY_SHA256
    )


def test_stage2a_binding_excludes_global_plan_and_alias_authority():
    _source, projected = _stage2a_projection()
    cell = projected["cells"][0]
    baseline = registry.renderer_bound_qualification_binding_sha256(cell)

    for field, replacement in (
        ("current_controlled_plan_sha256", "a" * 64),
        ("tested_controlled_plan_sha256", "b" * 64),
        ("schedule_key", "schedule_stage2a_probe"),
        ("case_alias", "case_stage2a_probe"),
        ("execution_order", 99),
    ):
        altered = deepcopy(cell)
        altered[field] = replacement
        assert registry.renderer_bound_qualification_binding_sha256(altered) == (
            baseline
        )

    for field, replacement in (
        ("current_workload_qualification_semantics_sha256", "c" * 64),
        ("current_task_contract_sha256", "d" * 64),
        ("evidence_sha256", "e" * 64),
    ):
        altered = deepcopy(cell)
        altered[field] = replacement
        assert registry.renderer_bound_qualification_binding_sha256(altered) != (
            baseline
        )


def test_stage2a_fresh_renderer_bound_cell_requires_supplied_tested_digest():
    source = _stage2a_on_disk_registry()
    base = next(
        cell for cell in source["cells"] if cell["status"] == "qualified"
    )
    current = "f" * 64

    # A renderer-bound projection may never invent the tested digest.
    with pytest.raises(ValueError):
        registry.build_renderer_bound_qualification_cell(
            base_cell=base,
            qualification_semantics_generation="renderer_bound_v1",
            current_workload_qualification_semantics_sha256=current,
            tested_workload_qualification_semantics_sha256=None,
        )
    with pytest.raises(ValueError):
        registry.build_renderer_bound_qualification_cell(
            base_cell=base,
            qualification_semantics_generation="legacy_no_renderer_binding",
            current_workload_qualification_semantics_sha256=current,
            tested_workload_qualification_semantics_sha256=current,
        )
    with pytest.raises(ValueError):
        registry.build_renderer_bound_qualification_cell(
            base_cell=base,
            qualification_semantics_generation="not_a_generation",
            current_workload_qualification_semantics_sha256=current,
        )

    matched = registry.build_renderer_bound_qualification_cell(
        base_cell=base,
        qualification_semantics_generation="renderer_bound_v1",
        current_workload_qualification_semantics_sha256=current,
        tested_workload_qualification_semantics_sha256=current,
    )
    assert matched["status"] == "qualified"
    assert matched["status_reasons"] == [
        "qualification_requirements_satisfied"
    ]

    drifted = registry.build_renderer_bound_qualification_cell(
        base_cell=base,
        qualification_semantics_generation="renderer_bound_v1",
        current_workload_qualification_semantics_sha256=current,
        tested_workload_qualification_semantics_sha256="0" * 64,
    )
    assert drifted["status"] == "stale"
    assert "workload_semantics_binding_stale" in drifted["status_reasons"]
    assert "qualification_requirements_satisfied" not in drifted["status_reasons"]

    rejected_base = next(
        cell for cell in source["cells"] if cell["status"] == "rejected"
    )
    still_rejected = registry.build_renderer_bound_qualification_cell(
        base_cell=rejected_base,
        qualification_semantics_generation="renderer_bound_v1",
        current_workload_qualification_semantics_sha256=current,
        tested_workload_qualification_semantics_sha256="0" * 64,
    )
    assert still_rejected["status"] == "rejected"


def test_stage2a_binding_moves_when_workload_semantics_change():
    _source, projected = _stage2a_projection()
    cell = projected["cells"][0]
    altered = deepcopy(cell)
    altered["current_workload_qualification_semantics_sha256"] = "1" * 64
    assert registry.renderer_bound_qualification_binding_sha256(altered) != (
        registry.renderer_bound_qualification_binding_sha256(cell)
    )

    invalid = deepcopy(projected)
    invalid["cells"][0]["status"] = "qualified"
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_qualification_registry(invalid)


# ---------------------------------------------------------------------------
# Stage 4K: multi-case observations collapse to candidate-level authority.
# All evidence is synthetic and in memory; V1 remains byte-stable.
# ---------------------------------------------------------------------------


STAGE4K_FUTURE_CORPUS_SHA256 = (
    "34a583f29750fe3e1fdc7c951db2c37b39d7561219c0031ac328ae5b0d45f9f2"
)
STAGE4K_FUTURE_PLAN_SHA256 = (
    "ba7adfa64766afc938a2c5aea0215d4a2e42e2c7d0667025ee24cc75010862bc"
)
STAGE4K_FUTURE_SKILL_SEMANTICS = (
    "3e1c457b9636d5ec648b6e24a823df006bad790641b1f831d3bebb34b2ddc362"
)
STAGE4K_SKILL_TASK_CONTRACT = (
    "73784a99de4913b95e2d2a1e8a1b10a9eee1665fd83a179be34a4fe31b82fa4c"
)
STAGE4K_EVIDENCE_SHA256 = "e" * 64


def _stage4k_future_context():
    import test_provider_fixture_benchmark as fixture_suite

    from src.evaluation import controlled_production_parity_benchmark as parity
    from src.evaluation.controlled_provider_benchmark_plan import (
        controlled_provider_benchmark_plan_sha256,
    )
    from src.evaluation.provider_fixture_benchmark import (
        fixture_case_corpus_sha256,
    )

    corpus = deepcopy(load_fixture_case_corpus())
    corpus["cases"] += fixture_suite.stage4b_proposed_skill_cases()
    plan = build_controlled_provider_benchmark_plan(corpus=corpus)
    assert fixture_case_corpus_sha256(corpus) == STAGE4K_FUTURE_CORPUS_SHA256
    assert controlled_provider_benchmark_plan_sha256(plan) == (
        STAGE4K_FUTURE_PLAN_SHA256
    )
    semantics = {
        workload_id: parity.workload_qualification_semantics_sha256(
            workload_id, plan=plan, corpus=corpus
        )
        for workload_id in sorted(
            {row["workload_id"] for row in plan["staged_matrix"]}
        )
    }
    assert semantics["skill_extraction"] == STAGE4K_FUTURE_SKILL_SEMANTICS
    schedule = harness.build_execution_schedule(
        plan=plan,
        authorization={
            "approved_request_matrix": deepcopy(plan["staged_matrix"]),
            "maximum_request_count": plan["request_counts"][
                "maximum_total_requests"
            ],
        },
    )
    return corpus, plan, schedule, semantics


def _stage4k_candidate_rows(schedule, workload_id, provider, model=None):
    candidates = [
        row
        for row in schedule
        if row["workload_id"] == workload_id and row["provider"] == provider
    ]
    model = model or candidates[0]["model"]
    rows = [row for row in candidates if row["model"] == model]
    assert rows
    return rows


def _stage4k_observations(
    *,
    plan,
    rows,
    semantics,
    task_contract,
    evidence_sha256=STAGE4K_EVIDENCE_SHA256,
):
    bindings = registry.build_current_qualification_bindings(plan)
    return [
        {
            "observation_version": (
                "qualification-evidence-observation-renderer-bound-v1"
            ),
            "evidence_kind": "controlled_live_qualification_evidence",
            "evidence_schema_version": (
                "controlled-live-provider-qualification-evidence-"
                "renderer-bound-v1"
            ),
            "evidence_sha256": evidence_sha256,
            "schedule_key": row["schedule_key"],
            "case_alias": row["case_alias"],
            "workload_id": row["workload_id"],
            "provider": row["provider"],
            "model": row["model"],
            "execution_at_utc": "2026-08-29T12:00:00.000000Z",
            "tested_model_catalog_snapshot_sha256": bindings[
                "model_catalog_snapshot_sha256"
            ],
            "tested_benchmark_contract_sha256": bindings[
                "benchmark_contract_sha256"
            ],
            "tested_controlled_plan_sha256": bindings[
                "controlled_plan_sha256"
            ],
            "tested_task_contract_sha256": task_contract,
            "schedule_completed": True,
            "provider_outcome_category": "success",
            "provider_call_count": 1,
            "contract_valid": True,
            "normalization_succeeded": None,
            "quality_gate_passed": True,
            "hard_failure_present": False,
            "input_token_count": 40,
            "output_token_count": 20,
            "human_review_required": False,
            "authority_safety_valid": True,
            "qualification_semantics_generation": "renderer_bound_v1",
            "tested_workload_qualification_semantics_sha256": semantics,
        }
        for row in rows
    ]


def _stage4k_build_skill_candidate(plan, rows, observations, semantics):
    return registry.build_renderer_bound_candidate_qualification_cell(
        plan=plan,
        workload_id="skill_extraction",
        provider=rows[0]["provider"],
        model=rows[0]["model"],
        observations=observations,
        current_task_contract_sha256=STAGE4K_SKILL_TASK_CONTRACT,
        current_workload_qualification_semantics_sha256=semantics,
    )


@pytest.mark.parametrize(
    ("mutation", "expected_status", "expected_reason"),
    (
        (None, "qualified", "qualification_requirements_satisfied"),
        ("rejected", "rejected", "quality_gate_failed"),
        ("pending", "pending", "task_contract_binding_missing"),
        ("stale", "stale", "catalog_binding_stale"),
        ("wrong_semantics", "stale", "workload_semantics_binding_stale"),
        ("wrong_task", "stale", "task_contract_binding_stale"),
    ),
)
def test_stage4k_five_case_status_precedence(
    mutation, expected_status, expected_reason
):
    _corpus, plan, schedule, semantics = _stage4k_future_context()
    rows = _stage4k_candidate_rows(schedule, "skill_extraction", "groq")
    observations = _stage4k_observations(
        plan=plan,
        rows=rows,
        semantics=semantics["skill_extraction"],
        task_contract=STAGE4K_SKILL_TASK_CONTRACT,
    )
    assert len(rows) == len(observations) == 5
    if mutation == "rejected":
        observations[-1]["quality_gate_passed"] = False
    elif mutation == "pending":
        observations[-1]["tested_task_contract_sha256"] = None
    elif mutation == "stale":
        observations[-1]["tested_model_catalog_snapshot_sha256"] = "0" * 64
    elif mutation == "wrong_semantics":
        observations[-1][
            "tested_workload_qualification_semantics_sha256"
        ] = "1" * 64
    elif mutation == "wrong_task":
        observations[-1]["tested_task_contract_sha256"] = "2" * 64

    cell = _stage4k_build_skill_candidate(
        plan, rows, observations, semantics["skill_extraction"]
    )

    assert cell["status"] == expected_status
    assert expected_reason in cell["status_reasons"]
    assert cell["qualification_schedule_keys"] == [
        row["schedule_key"] for row in rows
    ]
    assert cell["qualification_case_aliases"] == [
        row["case_alias"] for row in rows
    ]
    if expected_status == "qualified":
        assert cell["status_reasons"] == [
            "qualification_requirements_satisfied"
        ]


def test_stage4k_partial_coverage_and_definitive_failure_precedence():
    _corpus, plan, schedule, semantics = _stage4k_future_context()
    rows = _stage4k_candidate_rows(schedule, "skill_extraction", "groq")
    observations = _stage4k_observations(
        plan=plan,
        rows=rows,
        semantics=semantics["skill_extraction"],
        task_contract=STAGE4K_SKILL_TASK_CONTRACT,
    )

    partial = _stage4k_build_skill_candidate(
        plan, rows, observations[:2], semantics["skill_extraction"]
    )
    assert partial["status"] == "pending"
    assert "evidence_missing" in partial["status_reasons"]
    assert partial["qualification_schedule_keys"] == [
        row["schedule_key"] for row in rows[:2]
    ]
    assert partial["qualification_case_aliases"] == [
        row["case_alias"] for row in rows[:2]
    ]

    rejected_observation = deepcopy(observations[0])
    rejected_observation["quality_gate_passed"] = False
    rejected = _stage4k_build_skill_candidate(
        plan, rows, [rejected_observation], semantics["skill_extraction"]
    )
    assert rejected["status"] == "rejected"
    assert "evidence_missing" not in rejected["status_reasons"]

    stale_observation = deepcopy(observations[0])
    stale_observation["tested_task_contract_sha256"] = "3" * 64
    stale = _stage4k_build_skill_candidate(
        plan, rows, [stale_observation], semantics["skill_extraction"]
    )
    assert stale["status"] == "stale"
    assert "evidence_missing" not in stale["status_reasons"]

    altered_coverage = deepcopy(partial)
    altered_coverage["qualification_schedule_keys"] = altered_coverage[
        "qualification_schedule_keys"
    ][:1]
    altered_coverage["qualification_case_aliases"] = altered_coverage[
        "qualification_case_aliases"
    ][:1]
    assert registry.renderer_bound_qualification_binding_sha256(
        altered_coverage
    ) != partial["qualification_binding_sha256"]


def test_stage4k_observation_order_is_not_authority():
    _corpus, plan, schedule, semantics = _stage4k_future_context()
    rows = _stage4k_candidate_rows(schedule, "skill_extraction", "groq")
    observations = _stage4k_observations(
        plan=plan,
        rows=rows,
        semantics=semantics["skill_extraction"],
        task_contract=STAGE4K_SKILL_TASK_CONTRACT,
    )
    arbitrary = [observations[index] for index in (2, 4, 0, 3, 1)]

    canonical = _stage4k_build_skill_candidate(
        plan, rows, observations, semantics["skill_extraction"]
    )
    reversed_cell = _stage4k_build_skill_candidate(
        plan, rows, list(reversed(observations)), semantics["skill_extraction"]
    )
    shuffled = _stage4k_build_skill_candidate(
        plan, rows, arbitrary, semantics["skill_extraction"]
    )

    assert canonical == reversed_cell == shuffled


def test_stage4k_structural_observation_failures_return_no_cell():
    _corpus, plan, schedule, semantics = _stage4k_future_context()
    rows = _stage4k_candidate_rows(schedule, "skill_extraction", "groq")
    baseline = _stage4k_observations(
        plan=plan,
        rows=rows,
        semantics=semantics["skill_extraction"],
        task_contract=STAGE4K_SKILL_TASK_CONTRACT,
    )

    malformed = {}
    malformed["duplicate schedule"] = deepcopy(baseline[:2])
    malformed["duplicate schedule"][1]["schedule_key"] = malformed[
        "duplicate schedule"
    ][0]["schedule_key"]
    malformed["duplicate case"] = deepcopy(baseline[:2])
    malformed["duplicate case"][1]["case_alias"] = malformed[
        "duplicate case"
    ][0]["case_alias"]
    for name, field, value in (
        ("unknown case", "case_alias", "case_unknown_stage4k"),
        ("unknown schedule", "schedule_key", "schedule_unknown_stage4k"),
        ("wrong workload", "workload_id", "job_fit_evaluation"),
        ("wrong provider", "provider", "openai"),
        ("wrong model", "model", "model-wrong-stage4k"),
        (
            "legacy observation",
            "qualification_semantics_generation",
            "legacy_no_renderer_binding",
        ),
    ):
        malformed[name] = deepcopy(baseline[:2])
        malformed[name][0][field] = value
    malformed["multiple evidence SHAs"] = deepcopy(baseline[:2])
    malformed["multiple evidence SHAs"][1]["evidence_sha256"] = "4" * 64
    malformed["conflicting execution times"] = deepcopy(baseline[:2])
    malformed["conflicting execution times"][1]["execution_at_utc"] = (
        "2026-08-29T12:00:01.000000Z"
    )
    malformed["conflicting review requirements"] = deepcopy(baseline[:2])
    malformed["conflicting review requirements"][1][
        "human_review_required"
    ] = True

    for name, observations in malformed.items():
        with pytest.raises(ValueError):
            _stage4k_build_skill_candidate(
                plan, rows, observations, semantics["skill_extraction"]
            )


def _stage4k_future_registry():
    _corpus, plan, schedule, semantics = _stage4k_future_context()
    source = _stage2a_on_disk_registry()
    projected = registry.project_registry_to_renderer_bound_generation(
        source,
        current_workload_qualification_semantics_sha256_by_workload={
            cell["workload_id"]: semantics[cell["workload_id"]]
            for cell in source["cells"]
        },
        superseded_cell_identities=PROVEN_SUPERSEDED_IDENTITIES,
    )
    replacements = {}
    for provider, model, evidence_digest in (
        ("groq", "openai/gpt-oss-20b", "5" * 64),
        ("groq", "openai/gpt-oss-120b", "7" * 64),
        ("openai", "gpt-5-mini", "6" * 64),
    ):
        rows = _stage4k_candidate_rows(
            schedule, "skill_extraction", provider, model
        )
        observations = _stage4k_observations(
            plan=plan,
            rows=rows,
            semantics=semantics["skill_extraction"],
            task_contract=STAGE4K_SKILL_TASK_CONTRACT,
            evidence_sha256=evidence_digest,
        )
        cell = _stage4k_build_skill_candidate(
            plan, rows, observations, semantics["skill_extraction"]
        )
        replacements[(cell["workload_id"], cell["provider"], cell["model"])] = cell
    expanded_cells = []
    for cell in projected["cells"]:
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
    projected["cells"] = expanded_cells
    return plan, schedule, projected


def test_stage4k_future_registry_and_stage3_candidate_handoff():
    from src.evaluation import provider_model_recommendation_policy as policy

    plan, schedule, payload = _stage4k_future_registry()
    identities = [
        (cell["workload_id"], cell["provider"], cell["model"])
        for cell in payload["cells"]
    ]
    skill_cells = [
        cell for cell in payload["cells"] if cell["workload_id"] == "skill_extraction"
    ]

    assert len(schedule) == 57
    assert len(payload["cells"]) == len(set(identities)) == 45
    assert len(
        [row for row in schedule if row["workload_id"] == "skill_extraction"]
    ) == 15
    assert len(skill_cells) == 3
    assert all(
        len(cell["qualification_schedule_keys"]) == 5
        for cell in skill_cells
    )
    assert registry.validate_renderer_bound_qualification_registry(
        payload, plan=plan
    )

    universe = [
        {
            "provider": cell["provider"],
            "model": cell["model"],
            "status": cell["status"],
        }
        for cell in skill_cells
    ]
    for cell in skill_cells:
        pin = {
            "pin_version": policy.RENDERER_BOUND_RECOMMENDATION_PIN_VERSION,
            "workload_id": "skill_extraction",
            "provider": cell["provider"],
            "model": cell["model"],
            "selection_basis": "synthetic_stage4k_candidate_proof",
            "expected_status": "qualified",
            "expected_status_reasons": list(cell["status_reasons"]),
            "expected_qualification_semantics_generation": "renderer_bound_v1",
            "expected_current_workload_qualification_semantics_sha256": (
                STAGE4K_FUTURE_SKILL_SEMANTICS
            ),
            "expected_tested_workload_qualification_semantics_sha256": (
                STAGE4K_FUTURE_SKILL_SEMANTICS
            ),
            "expected_current_task_contract_sha256": STAGE4K_SKILL_TASK_CONTRACT,
            "expected_tested_task_contract_sha256": STAGE4K_SKILL_TASK_CONTRACT,
            "expected_qualification_binding_sha256": cell[
                "qualification_binding_sha256"
            ],
            "expected_evidence_sha256": cell["evidence_sha256"],
            "expected_review_sha256": None,
            "expected_candidate_universe": deepcopy(universe),
        }
        assert policy.validate_renderer_bound_workload_recommendation(
            payload, pin=pin
        )


def test_stage4k_registry_validator_fails_closed_on_identity_and_coverage():
    plan, _schedule, payload = _stage4k_future_registry()
    duplicate = deepcopy(payload)
    duplicate["cells"].append(deepcopy(duplicate["cells"][0]))
    with pytest.raises(ValueError, match="duplicate candidate"):
        registry.validate_renderer_bound_qualification_registry(duplicate)

    skill = next(
        cell
        for cell in payload["cells"]
        if cell["workload_id"] == "skill_extraction"
    )
    malformed = deepcopy(payload)
    target = next(
        cell
        for cell in malformed["cells"]
        if (cell["workload_id"], cell["provider"], cell["model"])
        == (skill["workload_id"], skill["provider"], skill["model"])
    )
    target["qualification_case_aliases"] = target[
        "qualification_case_aliases"
    ][:-1]
    target["qualification_binding_sha256"] = (
        registry.renderer_bound_qualification_binding_sha256(target)
    )
    with pytest.raises(ValueError, match="coverage is malformed"):
        registry.validate_renderer_bound_qualification_registry(malformed)

    incomplete = deepcopy(payload)
    target = next(
        cell
        for cell in incomplete["cells"]
        if cell["workload_id"] == "skill_extraction"
    )
    target["qualification_schedule_keys"] = target[
        "qualification_schedule_keys"
    ][:-1]
    target["qualification_case_aliases"] = target[
        "qualification_case_aliases"
    ][:-1]
    target["qualification_binding_sha256"] = (
        registry.renderer_bound_qualification_binding_sha256(target)
    )
    with pytest.raises(ValueError, match="coverage is incomplete"):
        registry.validate_renderer_bound_qualification_registry(
            incomplete, plan=plan
        )

    for field, replacement in (
        ("qualification_schedule_keys", "schedule_unknown_stage4k"),
        ("qualification_case_aliases", "case_unknown_stage4k"),
    ):
        outside = deepcopy(payload)
        target = next(
            cell
            for cell in outside["cells"]
            if cell["workload_id"] == "skill_extraction"
        )
        target[field][0] = replacement
        target["qualification_binding_sha256"] = (
            registry.renderer_bound_qualification_binding_sha256(target)
        )
        with pytest.raises(ValueError, match="outside plan authority"):
            registry.validate_renderer_bound_qualification_registry(
                outside, plan=plan
            )


def test_stage4k_sixth_case_invalidates_semantics_and_coverage():
    import test_provider_fixture_benchmark as fixture_suite

    from src.evaluation import controlled_production_parity_benchmark as parity

    corpus, _five_plan, _schedule, _semantics = _stage4k_future_context()
    sixth = deepcopy(fixture_suite.stage4b_proposed_skill_cases()[0])
    sixth["case_id"] = "skill_extraction_hypothetical_sixth_v1"
    sixth["provenance"]["source_identifier"] = "stage4k_hypothetical_sixth"
    six_corpus = deepcopy(corpus)
    six_corpus["cases"].append(sixth)
    six_plan = build_controlled_provider_benchmark_plan(corpus=six_corpus)
    six_semantics = parity.workload_qualification_semantics_sha256(
        "skill_extraction", plan=six_plan, corpus=six_corpus
    )
    six_schedule = harness.build_execution_schedule(
        plan=six_plan,
        authorization={
            "approved_request_matrix": deepcopy(six_plan["staged_matrix"]),
            "maximum_request_count": six_plan["request_counts"][
                "maximum_total_requests"
            ],
        },
    )
    rows = _stage4k_candidate_rows(
        six_schedule, "skill_extraction", "groq"
    )
    observations = _stage4k_observations(
        plan=six_plan,
        rows=rows[:5],
        semantics=STAGE4K_FUTURE_SKILL_SEMANTICS,
        task_contract=STAGE4K_SKILL_TASK_CONTRACT,
    )
    cell = _stage4k_build_skill_candidate(
        six_plan, rows, observations, six_semantics
    )

    assert len(rows) == 6
    assert six_semantics != STAGE4K_FUTURE_SKILL_SEMANTICS
    assert len(cell["qualification_schedule_keys"]) == 5
    assert cell["status"] == "stale"
    assert "workload_semantics_binding_stale" in cell["status_reasons"]


def test_stage4k_job_fit_single_case_aggregation_is_identity():
    from src.evaluation.production_task_contract_fingerprints import (
        build_all_production_task_contract_fingerprints,
    )

    _corpus, plan, schedule, semantics = _stage4k_future_context()
    task = build_all_production_task_contract_fingerprints()[
        "job_fit_evaluation"
    ]
    cells = []
    for provider in ("groq", "openai"):
        provider_rows = [
            row
            for row in schedule
            if row["workload_id"] == "job_fit_evaluation"
            and row["provider"] == provider
        ]
        for row in provider_rows:
            observations = _stage4k_observations(
                plan=plan,
                rows=[row],
                semantics=semantics["job_fit_evaluation"],
                task_contract=task,
            )
            cells.append(
                registry.build_renderer_bound_candidate_qualification_cell(
                    plan=plan,
                    workload_id="job_fit_evaluation",
                    provider=row["provider"],
                    model=row["model"],
                    observations=observations,
                    current_task_contract_sha256=task,
                    current_workload_qualification_semantics_sha256=semantics[
                        "job_fit_evaluation"
                    ],
                )
            )

    assert len(cells) == 4
    assert all(cell["status"] == "qualified" for cell in cells)
    assert all(len(cell["qualification_schedule_keys"]) == 1 for cell in cells)
    assert len(
        {
            (cell["workload_id"], cell["provider"], cell["model"])
            for cell in cells
        }
    ) == 4


def test_stage4k_v1_authority_remains_byte_stable():
    from src.evaluation import provider_model_recommendation_policy as policy
    from src.evaluation.job_fit_provider_model_qualification_overlay import (
        build_job_fit_provider_model_qualification_overlay,
    )
    from src.evaluation.controlled_provider_benchmark_plan import (
        controlled_provider_benchmark_plan_sha256,
        legacy_case_alias_map,
    )
    from src.evaluation.provider_fixture_benchmark import (
        fixture_case_corpus_sha256,
    )

    source = _stage2a_on_disk_registry()
    corpus = load_fixture_case_corpus()
    plan = build_controlled_provider_benchmark_plan(corpus=corpus)
    assert fixture_case_corpus_sha256(corpus) == CURRENT_FIXTURE_CORPUS_SHA256
    assert controlled_provider_benchmark_plan_sha256(plan) == (
        STAGE5C_CURRENT_CONTROLLED_PLAN_SHA256
    )
    assert registry.provider_qualification_registry_sha256(source) == (
        CURRENT_V1_REGISTRY_SHA256
    )
    assert len(legacy_case_alias_map(corpus)) == 15
    recommendations = policy.build_provider_model_recommendation_policy(source)
    assert len(recommendations["workloads"]) == 12
    job_fit = build_job_fit_provider_model_qualification_overlay(source)
    assert (
        job_fit["recommendation_status"],
        job_fit["provider"],
        job_fit["model"],
    ) == ("recommended", "groq", "openai/gpt-oss-20b")


def _stage5g_current_skill_cell(
    *,
    plan,
    schedule,
    semantics,
    model,
    evidence_sha256,
    evaluated_at_utc,
    corpus,
    expected_v2_binding_sha256,
):
    rows = [
        row
        for row in schedule
        if row["workload_id"] == "skill_extraction"
        and row["provider"] == "groq"
        and row["model"] == model
    ]
    assert len(rows) == 5
    bindings = registry.build_current_qualification_bindings(plan)
    base = registry._build_cell(
        scheduled=rows[0],
        status="qualified",
        reasons={"qualification_requirements_satisfied"},
        review_required=False,
        current_bindings=bindings,
        current_task_contract_sha256=STAGE4K_SKILL_TASK_CONTRACT,
        tested_model_catalog_snapshot_sha256=bindings[
            "model_catalog_snapshot_sha256"
        ],
        tested_benchmark_contract_sha256=bindings[
            "benchmark_contract_sha256"
        ],
        tested_controlled_plan_sha256=bindings["controlled_plan_sha256"],
        tested_task_contract_sha256=STAGE4K_SKILL_TASK_CONTRACT,
        evidence_sha256=evidence_sha256,
        evaluated_at_utc=evaluated_at_utc,
    )
    cell = registry.build_renderer_bound_qualification_cell(
        base_cell=base,
        qualification_semantics_generation="renderer_bound_v1",
        current_workload_qualification_semantics_sha256=semantics,
        tested_workload_qualification_semantics_sha256=semantics,
    )
    cell["qualification_schedule_keys"] = [
        row["schedule_key"] for row in rows
    ]
    cell["qualification_case_aliases"] = [
        row["case_alias"] for row in rows
    ]
    cell["qualification_binding_sha256"] = (
        registry.renderer_bound_qualification_binding_sha256(cell)
    )
    # The V1 binding is deliberately NOT pinned here. It mixes the global
    # benchmark-contract pair and corpus-derived raw coverage into workload
    # authority, so it drifts whenever an unrelated workload's fixtures move
    # even though Skill semantics are unchanged. Pinning that transient value
    # is what this migration exists to stop.
    from src.evaluation.controlled_provider_benchmark_plan import (
        legacy_case_alias_map,
        stable_case_alias,
    )

    case_ids_by_alias = {
        alias: case_id
        for case_id, alias in legacy_case_alias_map(corpus).items()
    }
    stable_aliases = [
        stable_case_alias("skill_extraction", case_ids_by_alias[alias])
        for alias in cell["qualification_case_aliases"]
    ]
    migrated = registry.migrate_renderer_bound_cell_to_v2(
        cell,
        stable_case_aliases=stable_aliases,
    )
    # The V2 binding is workload-local and corpus-independent, so it equals the
    # durable reviewed authority no matter which corpus reconstructed the cell.
    assert migrated["qualification_binding_sha256"] == expected_v2_binding_sha256
    return cell


def test_stage5g_current_skill_winner_pin_preserves_qualified_alternative():
    from src.evaluation import provider_model_recommendation_policy as policy

    _corpus, plan, schedule, semantics = _stage4k_future_context()
    current_semantics = semantics["skill_extraction"]
    current_20b = _stage5g_current_skill_cell(
        plan=plan,
        schedule=schedule,
        semantics=current_semantics,
        model="openai/gpt-oss-20b",
        evidence_sha256=(
            "ca727553032f24749b3ea161188b6c2cd4f7ab4c877b8e7dc7d896a0f186e5ac"
        ),
        evaluated_at_utc="2026-08-31T05:43:16.000000Z",
        corpus=_corpus,
        expected_v2_binding_sha256=(
            "12b2e716ba4c9dffafb4da68344a4b603f8d36eabb9fbd1ed6fdda12f0b2a2e2"
        ),
    )
    current_120b = _stage5g_current_skill_cell(
        plan=plan,
        schedule=schedule,
        semantics=current_semantics,
        model="openai/gpt-oss-120b",
        evidence_sha256=(
            "79e89f604a16f38ea6803bf2669c004b4631ebaf5fd9ef005b3fe57e9f59c6ec"
        ),
        evaluated_at_utc="2026-08-31T05:58:34.000000Z",
        corpus=_corpus,
        expected_v2_binding_sha256=(
            "85b33f3b9289f3aeadacd847a754306aa13fb70154a2dc5e856498bfbbf1564e"
        ),
    )
    source = _stage2a_on_disk_registry()
    projected = registry.project_registry_to_renderer_bound_generation(
        source,
        current_workload_qualification_semantics_sha256_by_workload={
            cell["workload_id"]: semantics[cell["workload_id"]]
            for cell in source["cells"]
        },
    )
    expanded_cells = []
    for cell in projected["cells"]:
        identity = (cell["workload_id"], cell["provider"], cell["model"])
        expanded_cells.append(
            current_20b
            if identity
            == ("skill_extraction", "groq", "openai/gpt-oss-20b")
            else cell
        )
        if identity == (
            "skill_extraction",
            "groq",
            "openai/gpt-oss-20b",
        ):
            expanded_cells.append(current_120b)
    projected["cells"] = expanded_cells

    # The V1 representation still parses and validates: V1 meaning is retained.
    assert registry.validate_renderer_bound_qualification_registry(
        projected, plan=plan
    )
    # The V1 winner pin can no longer validate this reconstruction, because the
    # V1 binding absorbed an unrelated workload's corpus change. That failure is
    # the defect V2 fixes, so recommendation authority is asserted under V2.
    v1_pin = policy.build_finalized_skill_extraction_renderer_bound_pin()
    with pytest.raises(ValueError):
        policy.validate_renderer_bound_workload_recommendation(
            projected, pin=v1_pin
        )

    from src.evaluation.controlled_provider_benchmark_plan import (
        legacy_case_alias_map,
        stable_case_alias,
    )

    case_ids_by_alias = {
        alias: case_id
        for case_id, alias in legacy_case_alias_map(_corpus).items()
    }
    stable_by_identity = {
        ("skill_extraction", cell["provider"], cell["model"]): [
            stable_case_alias("skill_extraction", case_ids_by_alias[alias])
            for alias in cell["qualification_case_aliases"]
        ]
        for cell in (current_20b, current_120b)
    }
    migrated = registry.migrate_renderer_bound_registry_to_v2(
        projected,
        stable_case_aliases_by_identity=stable_by_identity,
    )
    assert registry.validate_renderer_bound_v2_qualification_registry(
        migrated, plan=plan, corpus=_corpus
    )
    pin = policy.build_finalized_skill_extraction_renderer_bound_v2_pin()
    assert policy.validate_renderer_bound_v2_workload_recommendation(
        migrated, pin=pin
    )
    selected = policy.build_renderer_bound_v2_workload_recommendation(
        migrated, pin=pin
    )
    assert (selected["provider"], selected["model"]) == (
        "groq",
        "openai/gpt-oss-20b",
    )
    skill_cells = [
        cell
        for cell in projected["cells"]
        if cell["workload_id"] == "skill_extraction"
    ]
    assert [
        (cell["provider"], cell["model"], cell["status"])
        for cell in skill_cells
    ] == [
        ("groq", "openai/gpt-oss-20b", "qualified"),
        ("groq", "openai/gpt-oss-120b", "qualified"),
        ("openai", "gpt-5-mini", "stale"),
    ]
    assert current_20b["evidence_sha256"] != current_120b["evidence_sha256"]
    assert current_20b["evidence_sha256"] != (
        "ca954448b9dd99f1bc710f16952ff330220ed28da75c0dc095d9e31f463a81ce"
    )
    assert not any(
        row["workload_id"] == "manual_scan_phrase"
        and row["model"] == "openai/gpt-oss-120b"
        for row in schedule
    )
    assert all(
        value is False
        for value in migrated["authority_invariants"].values()
    )


def test_stage6b_durable_skill_registry_loads_exact_bounded_authority():
    artifact_path = ROOT / registry.RENDERER_BOUND_SKILL_REGISTRY_ARTIFACT_PATH
    authority = registry.load_renderer_bound_skill_qualification_registry(
        artifact_path,
        repository_root=ROOT,
    )

    assert registry.validate_renderer_bound_qualification_registry(authority)
    assert registry.renderer_bound_qualification_registry_sha256(authority) == (
        "f25765138187aeae4eddc4f955441a738446493fe58ecc537f1cd9584d7c4cce"
    )
    assert [
        (cell["workload_id"], cell["provider"], cell["model"], cell["status"])
        for cell in authority["cells"]
    ] == [
        (
            "skill_extraction",
            "groq",
            "openai/gpt-oss-20b",
            "qualified",
        ),
        (
            "skill_extraction",
            "groq",
            "openai/gpt-oss-120b",
            "qualified",
        ),
        ("skill_extraction", "openai", "gpt-5-mini", "stale"),
    ]


# ---------------------------------------------------------------------------
# Step 5: renderer-bound V2 authority.
#
# The V1 negative tests above are preserved unchanged. These add the V2
# fail-closed surface and prove the cross-workload isolation that V1 lacked.
# ---------------------------------------------------------------------------

V2_SKILL_ARTIFACT = ROOT / registry.RENDERER_BOUND_V2_SKILL_REGISTRY_ARTIFACT_PATH
V2_JOB_FIT_ARTIFACT = (
    ROOT / registry.RENDERER_BOUND_V2_JOB_FIT_REGISTRY_ARTIFACT_PATH
)


def _v2_skill_authority():
    return registry.load_renderer_bound_v2_skill_qualification_registry(
        V2_SKILL_ARTIFACT,
        repository_root=ROOT,
    )


def _v2_job_fit_authority():
    return registry.load_renderer_bound_v2_job_fit_qualification_registry(
        V2_JOB_FIT_ARTIFACT,
        repository_root=ROOT,
    )


def _v2_winner(payload):
    return next(
        cell
        for cell in payload["cells"]
        if cell["status"] == "qualified"
    )


def _rebind_v2(cell):
    cell["qualification_binding_sha256"] = (
        registry.renderer_bound_v2_qualification_binding_sha256(cell)
    )


def test_step5_v2_durable_artifacts_load_and_preserve_reviewed_selections():
    skill = _v2_skill_authority()
    job_fit = _v2_job_fit_authority()
    assert skill["registry_schema_version"] == (
        registry.RENDERER_BOUND_V2_REGISTRY_SCHEMA_VERSION
    )
    assert skill["registry_contract_version"] == (
        registry.RENDERER_BOUND_V2_REGISTRY_CONTRACT_VERSION
    )
    qualified = [
        (cell["provider"], cell["model"])
        for cell in skill["cells"]
        if cell["status"] == "qualified"
    ]
    assert qualified == [
        ("groq", "openai/gpt-oss-20b"),
        ("groq", "openai/gpt-oss-120b"),
    ]
    assert [
        (cell["provider"], cell["model"])
        for cell in job_fit["cells"]
        if cell["status"] == "qualified"
    ] == [("groq", "openai/gpt-oss-20b")]
    # Legacy rejected candidates stay legacy: the schema migration never
    # promotes them into renderer-bound V2 qualification authority.
    legacy = [
        cell
        for cell in job_fit["cells"]
        if cell["qualification_semantics_generation"]
        == registry.LEGACY_QUALIFICATION_SEMANTICS_GENERATION
    ]
    assert len(legacy) == 3
    assert all(cell["status"] == "rejected" for cell in legacy)
    assert all(
        not cell["qualification_stable_case_aliases"] for cell in legacy
    )


def test_step5_v2_stable_coverage_is_exact_and_workload_scoped():
    skill = _v2_skill_authority()
    for cell in skill["cells"]:
        if cell["status"] != "qualified":
            continue
        assert cell["qualification_stable_case_aliases"] == [
            "case_adb75e8f4222598d01c96632",
            "case_ca4d896b8d25c5f6a33131e6",
            "case_c679d81feddcd209e0923b23",
            "case_155361f163b8a1857f1ea709",
            "case_2e2c04e49f9cdaa7ab5b6422",
        ]
        # Raw provenance is retained but is no longer authority.
        assert len(cell["qualification_case_aliases"]) == 5
        assert len(cell["qualification_schedule_keys"]) == 5
    assert _v2_winner(_v2_job_fit_authority())[
        "qualification_stable_case_aliases"
    ] == ["case_d2afa978996c4d69af1f538b"]


def test_step5_v2_rejects_wrong_schema_version():
    payload = _v2_skill_authority()
    payload["registry_schema_version"] = (
        registry.RENDERER_BOUND_REGISTRY_SCHEMA_VERSION
    )
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)


def test_step5_v2_rejects_wrong_contract_version():
    payload = _v2_skill_authority()
    payload["registry_contract_version"] = (
        registry.RENDERER_BOUND_REGISTRY_CONTRACT_VERSION
    )
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)


def test_step5_v1_artifact_is_rejected_by_the_v2_validator():
    v1 = registry.load_renderer_bound_skill_qualification_registry(
        ROOT / registry.RENDERER_BOUND_SKILL_REGISTRY_ARTIFACT_PATH,
        repository_root=ROOT,
    )
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(v1)


def test_step5_v2_artifact_is_rejected_by_the_v1_validator():
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_qualification_registry(
            _v2_skill_authority()
        )


def test_step5_v2_rejects_missing_stable_coverage_field():
    payload = _v2_skill_authority()
    del _v2_winner(payload)["qualification_stable_case_aliases"]
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)


def test_step5_v2_rejects_empty_stable_coverage_on_qualified_candidate():
    payload = _v2_skill_authority()
    cell = _v2_winner(payload)
    cell["qualification_stable_case_aliases"] = []
    _rebind_v2(cell)
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)


def test_step5_v2_rejects_duplicate_stable_alias():
    payload = _v2_skill_authority()
    cell = _v2_winner(payload)
    aliases = cell["qualification_stable_case_aliases"]
    cell["qualification_stable_case_aliases"] = [aliases[0]] * len(aliases)
    _rebind_v2(cell)
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)


@pytest.mark.parametrize(
    "malformed",
    [
        "case_NOTHEX4222598d01c96632",
        "case_adb75e8f4222598d01c9663",
        "case_adb75e8f4222598d01c966322",
        "adb75e8f4222598d01c96632",
        "",
    ],
)
def test_step5_v2_rejects_malformed_stable_alias(malformed):
    payload = _v2_skill_authority()
    cell = _v2_winner(payload)
    cell["qualification_stable_case_aliases"][0] = malformed
    _rebind_v2(cell)
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)


def test_step5_v2_rejects_removed_stable_alias():
    payload = _v2_skill_authority()
    cell = _v2_winner(payload)
    cell["qualification_stable_case_aliases"].pop()
    _rebind_v2(cell)
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)


def test_step5_v2_rejects_added_unauthorized_stable_alias():
    payload = _v2_skill_authority()
    cell = _v2_winner(payload)
    cell["qualification_stable_case_aliases"].append("case_" + "f" * 24)
    _rebind_v2(cell)
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)


def test_step5_v2_substituted_stable_alias_changes_the_binding():
    payload = _v2_skill_authority()
    cell = _v2_winner(payload)
    original = cell["qualification_binding_sha256"]
    cell["qualification_stable_case_aliases"][2] = "case_" + "a" * 24
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)
    _rebind_v2(cell)
    # Even after an honest rebind the substitution is visible: the binding moved.
    assert cell["qualification_binding_sha256"] != original
    from src.evaluation import provider_model_recommendation_policy as policy

    with pytest.raises(ValueError):
        policy.validate_finalized_skill_extraction_renderer_bound_v2_authority(
            payload
        )


@pytest.mark.parametrize(
    "field,replacement",
    [
        ("workload_id", "job_fit_evaluation"),
        ("provider", "openai"),
        ("model", "gpt-5.1"),
        ("current_task_contract_sha256", "c" * 64),
        ("tested_task_contract_sha256", "d" * 64),
        ("current_workload_qualification_semantics_sha256", "e" * 64),
        ("tested_workload_qualification_semantics_sha256", "f" * 64),
        ("evidence_sha256", "1" * 64),
        ("review_sha256", "2" * 64),
    ],
)
def test_step5_v2_authority_field_mutation_fails_closed(field, replacement):
    from src.evaluation import provider_model_recommendation_policy as policy

    payload = _v2_skill_authority()
    cell = _v2_winner(payload)
    cell[field] = replacement
    # Without an honest rebind the stored binding no longer matches.
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)
    # With an honest rebind the mutation is still caught by pinned authority.
    _rebind_v2(cell)
    with pytest.raises(ValueError):
        policy.validate_finalized_skill_extraction_renderer_bound_v2_authority(
            payload
        )


def test_step5_v2_rejects_binding_mutation():
    payload = _v2_skill_authority()
    _v2_winner(payload)["qualification_binding_sha256"] = "9" * 64
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(payload)


def test_step5_v2_rejects_registry_digest_mutation():
    from src.evaluation import provider_model_recommendation_policy as policy

    payload = _v2_skill_authority()
    # A structurally valid but non-pinned registry must not pass finalized
    # authority: the whole-registry digest is part of that authority.
    cell = _v2_winner(payload)
    cell["evaluated_at_utc"] = "2026-08-31T05:43:17.000000Z"
    _rebind_v2(cell)
    assert registry.validate_renderer_bound_v2_qualification_registry(payload)
    assert (
        registry.renderer_bound_v2_qualification_registry_sha256(payload)
        != policy.FINALIZED_SKILL_EXTRACTION_RENDERER_BOUND_V2_REGISTRY_SHA256
    )
    with pytest.raises(ValueError):
        policy.validate_finalized_skill_extraction_renderer_bound_v2_authority(
            payload
        )


def _step5_full_universe_v2_registry():
    """Build a complete-universe V2 registry so plan-aware rules can apply.

    Plan-aware validation checks the whole candidate universe against the
    execution schedule, so it needs every workload's cells, not one workload's
    durable slice.
    """

    from src.evaluation.controlled_provider_benchmark_plan import (
        legacy_case_alias_map,
        stable_case_alias,
    )

    corpus, plan, schedule, semantics = _stage4k_future_context()
    case_ids_by_alias = {
        alias: case_id
        for case_id, alias in legacy_case_alias_map(corpus).items()
    }
    source = _stage2a_on_disk_registry()
    projected = registry.project_registry_to_renderer_bound_generation(
        source,
        current_workload_qualification_semantics_sha256_by_workload={
            cell["workload_id"]: semantics[cell["workload_id"]]
            for cell in source["cells"]
        },
    )
    skill_cells = []
    for model, evidence, evaluated in (
        (
            "openai/gpt-oss-20b",
            "ca727553032f24749b3ea161188b6c2cd4f7ab4c877b8e7dc7d896a0f186e5ac",
            "2026-08-31T05:43:16.000000Z",
        ),
        (
            "openai/gpt-oss-120b",
            "79e89f604a16f38ea6803bf2669c004b4631ebaf5fd9ef005b3fe57e9f59c6ec",
            "2026-08-31T05:58:34.000000Z",
        ),
    ):
        skill_cells.append(
            _stage5g_current_skill_cell(
                plan=plan,
                schedule=schedule,
                semantics=semantics["skill_extraction"],
                model=model,
                evidence_sha256=evidence,
                evaluated_at_utc=evaluated,
                corpus=corpus,
                expected_v2_binding_sha256=(
                    "12b2e716ba4c9dffafb4da68344a4b603f8d36eabb9fbd1ed6fdda12f0b2a2e2"
                    if model == "openai/gpt-oss-20b"
                    else "85b33f3b9289f3aeadacd847a754306aa13fb70154a2dc5e856498bfbbf1564e"
                ),
            )
        )
    expanded = []
    for cell in projected["cells"]:
        identity = (cell["workload_id"], cell["provider"], cell["model"])
        if identity == ("skill_extraction", "groq", "openai/gpt-oss-20b"):
            expanded.extend(skill_cells)
        else:
            expanded.append(cell)
    projected["cells"] = expanded
    stable_by_identity = {
        ("skill_extraction", cell["provider"], cell["model"]): [
            stable_case_alias("skill_extraction", case_ids_by_alias[alias])
            for alias in cell["qualification_case_aliases"]
        ]
        for cell in skill_cells
    }
    migrated = registry.migrate_renderer_bound_registry_to_v2(
        projected,
        stable_case_aliases_by_identity=stable_by_identity,
    )
    return migrated, plan, corpus


def test_step5_v2_plan_aware_raw_provenance_mismatch_fails_closed():
    payload, plan, corpus = _step5_full_universe_v2_registry()
    assert registry.validate_renderer_bound_v2_qualification_registry(
        payload, plan=plan, corpus=corpus
    )
    broken = deepcopy(payload)
    cell = _v2_winner(broken)
    cell["qualification_schedule_keys"][1] = "schedule_" + "0" * 32
    _rebind_v2(cell)
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(
            broken, plan=plan, corpus=corpus
        )


def test_step5_v2_plan_aware_stable_coverage_mismatch_fails_closed():
    payload, plan, corpus = _step5_full_universe_v2_registry()
    broken = deepcopy(payload)
    cell = _v2_winner(broken)
    coverage = cell["qualification_stable_case_aliases"]
    coverage[0], coverage[1] = coverage[1], coverage[0]
    _rebind_v2(cell)
    # Reordered coverage is a different coverage claim: order is authoritative.
    with pytest.raises(ValueError):
        registry.validate_renderer_bound_v2_qualification_registry(
            broken, plan=plan, corpus=corpus
        )


def _step5_current_corpus_v2_skill_registry():
    """Rebuild the Skill V2 authority from the CURRENT corpus.

    The durable artifact was minted from the historical qualification corpus.
    Rebuilding from the current corpus yields different raw provenance but must
    yield identical stable coverage and an identical V2 binding.
    """

    from src.evaluation.controlled_provider_benchmark_plan import (
        legacy_case_alias_map,
        stable_case_alias,
    )

    corpus, plan, schedule, semantics = _stage4k_future_context()
    case_ids_by_alias = {
        alias: case_id
        for case_id, alias in legacy_case_alias_map(corpus).items()
    }
    payload = _v2_skill_authority()
    for cell in payload["cells"]:
        if cell["status"] != "qualified":
            continue
        rows = [
            row
            for row in schedule
            if row["workload_id"] == "skill_extraction"
            and row["provider"] == cell["provider"]
            and row["model"] == cell["model"]
        ]
        representative = rows[0]
        cell["execution_order"] = representative["execution_order"]
        cell["schedule_key"] = representative["schedule_key"]
        cell["case_alias"] = representative["case_alias"]
        cell["qualification_schedule_keys"] = [
            row["schedule_key"] for row in rows
        ]
        cell["qualification_case_aliases"] = [
            row["case_alias"] for row in rows
        ]
        cell["qualification_stable_case_aliases"] = [
            stable_case_alias("skill_extraction", case_ids_by_alias[row["case_alias"]])
            for row in rows
        ]
        cell["current_workload_qualification_semantics_sha256"] = semantics[
            "skill_extraction"
        ]
        cell["tested_workload_qualification_semantics_sha256"] = semantics[
            "skill_extraction"
        ]
        _rebind_v2(cell)
    return payload, corpus


def test_step5_v2_binding_survives_an_unrelated_workload_corpus_change():
    """Cross-workload isolation: the defect V2 exists to fix.

    The durable Skill authority was minted against the historical corpus. The
    current corpus differs because an unrelated workload's fixtures changed.
    V1 bindings move under that change; V2 bindings must not.
    """

    durable = _v2_skill_authority()
    rebuilt, _corpus = _step5_current_corpus_v2_skill_registry()

    durable_by_identity = {
        (cell["provider"], cell["model"]): cell for cell in durable["cells"]
    }
    moved_raw = 0
    for cell in rebuilt["cells"]:
        if cell["status"] != "qualified":
            continue
        original = durable_by_identity[(cell["provider"], cell["model"])]
        # Raw provenance genuinely moved with the unrelated corpus change...
        if cell["qualification_case_aliases"] != (
            original["qualification_case_aliases"]
        ):
            moved_raw += 1
        # ...while stable coverage and V2 authority did not.
        assert cell["qualification_stable_case_aliases"] == (
            original["qualification_stable_case_aliases"]
        )
        assert cell["qualification_binding_sha256"] == (
            original["qualification_binding_sha256"]
        )
    assert moved_raw == 2


def test_step5_v1_skill_binding_moves_under_the_same_unrelated_change():
    """Control: prove the V1 binding really is contaminated.

    Without this the isolation test above could pass vacuously.
    """

    v1 = registry.load_renderer_bound_skill_qualification_registry(
        ROOT / registry.RENDERER_BOUND_SKILL_REGISTRY_ARTIFACT_PATH,
        repository_root=ROOT,
    )
    _corpus, _plan, schedule, semantics = _stage4k_future_context()
    for cell in v1["cells"]:
        if cell["status"] != "qualified":
            continue
        rows = [
            row
            for row in schedule
            if row["workload_id"] == "skill_extraction"
            and row["provider"] == cell["provider"]
            and row["model"] == cell["model"]
        ]
        rebuilt = deepcopy(cell)
        rebuilt["qualification_schedule_keys"] = [
            row["schedule_key"] for row in rows
        ]
        rebuilt["qualification_case_aliases"] = [
            row["case_alias"] for row in rows
        ]
        # Workload semantics are unchanged, so only unrelated-corpus material
        # differs - yet the V1 binding still moves.
        assert rebuilt[
            "current_workload_qualification_semantics_sha256"
        ] == semantics["skill_extraction"]
        assert registry.renderer_bound_qualification_binding_sha256(
            rebuilt
        ) != cell["qualification_binding_sha256"]
