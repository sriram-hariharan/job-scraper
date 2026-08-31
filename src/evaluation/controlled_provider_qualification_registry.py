"""Durable, evaluation-only provider qualification registry.

The registry reconciles the current controlled benchmark universe with
validated run evidence, required human review, and explicit production
task-contract fingerprints.  It never calls providers, selects winners, or
grants production routing authority.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Dict, Mapping

from src.evaluation.controlled_provider_benchmark_evidence_runtime import (
    normalize_execution_timestamp,
)
from src.evaluation.controlled_provider_benchmark_harness import (
    build_execution_schedule,
)
from src.evaluation.controlled_provider_benchmark_human_review import (
    assess_post_result_human_review,
    canonical_human_review_requirements,
    normalize_review_timestamp,
    post_result_human_review_sha256,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    controlled_provider_benchmark_plan_sha256,
    validate_controlled_provider_benchmark_plan,
)
from src.evaluation.controlled_provider_qualification_evidence_adapter import (
    CONTROLLED_LIVE_EVIDENCE_KIND,
    RENDERER_BOUND_OBSERVATION_VERSION,
    build_qualification_observation,
)
from src.evaluation.provider_benchmark_contract import (
    provider_benchmark_contract_sha256,
)


REGISTRY_CONTRACT_VERSION = "controlled-provider-qualification-registry-v1"
REGISTRY_SCHEMA_VERSION = "controlled-provider-qualification-registry-artifact-v1"
REGISTRY_SCOPE = "evaluation_qualification_state_only"
REGISTRY_ARTIFACT_PATH = Path(
    "outputs/provider_benchmark/provider-qualification-registry.json"
)
RENDERER_BOUND_SKILL_REGISTRY_ARTIFACT_PATH = Path(
    "src/evaluation/renderer_bound_skill_qualification_registry.json"
)
QUALIFICATION_STATUSES = ("pending", "qualified", "rejected", "stale")

_HEX_DIGEST_LENGTH = 64
_REGISTRY_FIELDS = {
    "registry_schema_version",
    "registry_contract_version",
    "registry_scope",
    "qualification_statuses",
    "current_bindings",
    "task_contract_fingerprint_policy",
    "cells",
    "authority_invariants",
}
_CURRENT_BINDING_FIELDS = {
    "model_catalog_snapshot_sha256",
    "benchmark_contract_sha256",
    "controlled_plan_sha256",
}
_CELL_FIELDS = {
    "execution_order",
    "schedule_key",
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "status",
    "status_reasons",
    "human_review_required",
    "current_model_catalog_snapshot_sha256",
    "tested_model_catalog_snapshot_sha256",
    "current_benchmark_contract_sha256",
    "tested_benchmark_contract_sha256",
    "current_controlled_plan_sha256",
    "tested_controlled_plan_sha256",
    "current_task_contract_sha256",
    "tested_task_contract_sha256",
    "evidence_sha256",
    "review_sha256",
    "qualification_binding_sha256",
    "evaluated_at_utc",
    "reviewed_at_utc",
}
RENDERER_BOUND_REGISTRY_CONTRACT_VERSION = (
    "controlled-provider-qualification-registry-renderer-bound-v1"
)
RENDERER_BOUND_REGISTRY_SCHEMA_VERSION = (
    "controlled-provider-qualification-registry-artifact-renderer-bound-v1"
)
LEGACY_QUALIFICATION_SEMANTICS_GENERATION = "legacy_no_renderer_binding"
RENDERER_BOUND_QUALIFICATION_SEMANTICS_GENERATION = "renderer_bound_v1"
QUALIFICATION_SEMANTICS_GENERATIONS = (
    LEGACY_QUALIFICATION_SEMANTICS_GENERATION,
    RENDERER_BOUND_QUALIFICATION_SEMANTICS_GENERATION,
)
_RENDERER_BOUND_CELL_ADDED_FIELDS = {
    "qualification_semantics_generation",
    "current_workload_qualification_semantics_sha256",
    "tested_workload_qualification_semantics_sha256",
    "qualification_schedule_keys",
    "qualification_case_aliases",
}
# Provenance retained on the next-generation cell but deliberately excluded
# from renderer-bound qualification authority: the controlled-plan pair is a
# global digest, and schedule_key/case_alias inherit the global corpus digest.
_RENDERER_BOUND_NON_AUTHORITY_FIELDS = (
    "execution_order",
    "schedule_key",
    "case_alias",
    "current_controlled_plan_sha256",
    "tested_controlled_plan_sha256",
    "evaluated_at_utc",
    "reviewed_at_utc",
    "qualification_binding_sha256",
    "status_reasons",
    "human_review_required",
)


_QUALIFICATION_INPUT_FIELDS = {
    "evidence",
    "evidence_sha256",
    "authorization",
    "pricing",
    "schedule_key",
    "tested_task_contract_sha256",
    "review_record",
    "review_sha256",
}
_STATUS_REASON_ORDER = (
    "hard_failure",
    "contract_invalid",
    "schema_invalid",
    "normalization_failed",
    "quality_gate_failed",
    "benchmark_failed",
    "review_rejected",
    "catalog_binding_stale",
    "benchmark_contract_binding_stale",
    "controlled_plan_binding_stale",
    "task_contract_binding_stale",
    "evidence_missing",
    "task_contract_missing",
    "task_contract_binding_missing",
    "review_missing",
    "qualification_requirements_satisfied",
)
_STATUS_REASONS = frozenset(_STATUS_REASON_ORDER)
_RENDERER_BOUND_STATUS_REASON_ORDER = _STATUS_REASON_ORDER[:-1] + (
    "workload_semantics_binding_missing",
    "workload_semantics_binding_stale",
    "renderer_semantics_superseded",
    _STATUS_REASON_ORDER[-1],
)
_RENDERER_BOUND_STATUS_REASONS = frozenset(_RENDERER_BOUND_STATUS_REASON_ORDER)
_PROHIBITED_KEY_PARTS = {
    "active_model",
    "api_key",
    "credential",
    "evidence_payload",
    "full_evidence",
    "normalized_output",
    "preferred_provider",
    "prompt",
    "raw_exception",
    "raw_provider",
    "raw_request",
    "raw_response",
    "reasoning",
    "recommended_model",
    "recommended_route",
    "request_id",
    "route_priority",
    "routing_allowed",
    "sdk_object",
    "selected_model",
    "synthetic_input",
    "user_override",
    "winner",
}
_AUTHORITY_INVARIANTS = {
    "recommendation_selection_allowed": False,
    "production_routing_change_allowed": False,
    "user_task_override_allowed": False,
    "provider_call_allowed": False,
    "secret_access_allowed": False,
    "application_mutation_allowed": False,
    "ats_mutation_allowed": False,
}
_TASK_FINGERPRINT_POLICY = {
    "required_for_qualification": True,
    "canonical_repository_fingerprints_available": False,
    "missing_fingerprint_status": "pending",
    "changed_fingerprint_status": "stale",
    "production_values_invented": False,
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _iter_keys(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).strip().lower()
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _contains_prohibited_key(value: Any) -> bool:
    return any(
        prohibited in key
        for key in _iter_keys(value)
        for prohibited in _PROHIBITED_KEY_PARTS
    )


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _HEX_DIGEST_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _optional_sha256(value: Any, label: str) -> str | None:
    if value is None:
        return None
    _require(_is_sha256(value), f"{label} must be a lowercase SHA-256 digest")
    return value


def _ordered_reasons(reasons: set[str]) -> list[str]:
    _require(reasons.issubset(_STATUS_REASONS), "unknown qualification reason")
    return [reason for reason in _STATUS_REASON_ORDER if reason in reasons]


def build_current_qualification_bindings(
    plan: Dict[str, Any],
) -> Dict[str, str]:
    """Return current canonical invalidation hashes without source-file hashing."""

    controlled_plan = deepcopy(plan)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    contract_digest = provider_benchmark_contract_sha256()
    _require(
        controlled_plan["step8l_contract_sha256"] == contract_digest,
        "controlled plan benchmark-contract binding mismatch",
    )
    bindings = {
        "model_catalog_snapshot_sha256": controlled_plan[
            "model_catalog_snapshot_sha256"
        ],
        "benchmark_contract_sha256": contract_digest,
        "controlled_plan_sha256": controlled_provider_benchmark_plan_sha256(
            controlled_plan
        ),
    }
    _require(
        set(bindings) == _CURRENT_BINDING_FIELDS
        and all(_is_sha256(value) for value in bindings.values()),
        "current qualification bindings are malformed",
    )
    return deepcopy(bindings)


def _normalize_task_contract_fingerprints(
    value: Mapping[str, str | None] | None,
    *,
    workloads: set[str],
) -> Dict[str, str | None]:
    if value is None:
        supplied: Dict[str, str | None] = {}
    else:
        _require(
            isinstance(value, Mapping),
            "task-contract fingerprints must be a mapping",
        )
        supplied = dict(value)
    _require(
        set(supplied).issubset(workloads),
        "task-contract fingerprint references an unknown workload",
    )
    normalized = {}
    for workload_id in workloads:
        normalized[workload_id] = _optional_sha256(
            supplied.get(workload_id),
            "task-contract fingerprint",
        )
    return normalized


def _qualification_binding_payload(cell: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schedule_key": cell["schedule_key"],
        "case_alias": cell["case_alias"],
        "workload_id": cell["workload_id"],
        "provider": cell["provider"],
        "model": cell["model"],
        "current_model_catalog_snapshot_sha256": cell[
            "current_model_catalog_snapshot_sha256"
        ],
        "tested_model_catalog_snapshot_sha256": cell[
            "tested_model_catalog_snapshot_sha256"
        ],
        "current_benchmark_contract_sha256": cell[
            "current_benchmark_contract_sha256"
        ],
        "tested_benchmark_contract_sha256": cell[
            "tested_benchmark_contract_sha256"
        ],
        "current_controlled_plan_sha256": cell[
            "current_controlled_plan_sha256"
        ],
        "tested_controlled_plan_sha256": cell[
            "tested_controlled_plan_sha256"
        ],
        "current_task_contract_sha256": cell[
            "current_task_contract_sha256"
        ],
        "tested_task_contract_sha256": cell[
            "tested_task_contract_sha256"
        ],
        "evidence_sha256": cell["evidence_sha256"],
        "review_sha256": cell["review_sha256"],
    }


def _qualification_binding_sha256(cell: Mapping[str, Any]) -> str:
    return sha256(
        _canonical_json(_qualification_binding_payload(cell)).encode("utf-8")
    ).hexdigest()


def _build_cell(
    *,
    scheduled: Mapping[str, Any],
    status: str,
    reasons: set[str],
    review_required: bool,
    current_bindings: Mapping[str, str],
    current_task_contract_sha256: str | None,
    tested_model_catalog_snapshot_sha256: str | None = None,
    tested_benchmark_contract_sha256: str | None = None,
    tested_controlled_plan_sha256: str | None = None,
    tested_task_contract_sha256: str | None = None,
    evidence_sha256: str | None = None,
    review_sha256: str | None = None,
    evaluated_at_utc: str | None = None,
    reviewed_at_utc: str | None = None,
) -> Dict[str, Any]:
    _require(status in QUALIFICATION_STATUSES, "unsupported qualification status")
    cell = {
        "execution_order": scheduled["execution_order"],
        "schedule_key": scheduled["schedule_key"],
        "case_alias": scheduled["case_alias"],
        "workload_id": scheduled["workload_id"],
        "provider": scheduled["provider"],
        "model": scheduled["model"],
        "status": status,
        "status_reasons": _ordered_reasons(reasons),
        "human_review_required": review_required,
        "current_model_catalog_snapshot_sha256": current_bindings[
            "model_catalog_snapshot_sha256"
        ],
        "tested_model_catalog_snapshot_sha256": (
            tested_model_catalog_snapshot_sha256
        ),
        "current_benchmark_contract_sha256": current_bindings[
            "benchmark_contract_sha256"
        ],
        "tested_benchmark_contract_sha256": (
            tested_benchmark_contract_sha256
        ),
        "current_controlled_plan_sha256": current_bindings[
            "controlled_plan_sha256"
        ],
        "tested_controlled_plan_sha256": tested_controlled_plan_sha256,
        "current_task_contract_sha256": current_task_contract_sha256,
        "tested_task_contract_sha256": tested_task_contract_sha256,
        "evidence_sha256": evidence_sha256,
        "review_sha256": review_sha256,
        "qualification_binding_sha256": "",
        "evaluated_at_utc": evaluated_at_utc,
        "reviewed_at_utc": reviewed_at_utc,
    }
    cell["qualification_binding_sha256"] = _qualification_binding_sha256(cell)
    return cell


def _pending_cell(
    *,
    scheduled: Mapping[str, Any],
    review_required: bool,
    current_bindings: Mapping[str, str],
    current_task_contract_sha256: str | None,
) -> Dict[str, Any]:
    reasons = {"evidence_missing"}
    if current_task_contract_sha256 is None:
        reasons.add("task_contract_missing")
    if review_required:
        reasons.add("review_missing")
    return _build_cell(
        scheduled=scheduled,
        status="pending",
        reasons=reasons,
        review_required=review_required,
        current_bindings=current_bindings,
        current_task_contract_sha256=current_task_contract_sha256,
    )


def _qualification_status_from_observation(
    *,
    observation: Mapping[str, Any],
    current_bindings: Mapping[str, str],
    current_task_contract_sha256: str | None,
    review_required: bool,
    review_decision: str,
    review_requirement_satisfied: bool,
) -> tuple[str, set[str], str | None]:
    """Interpret one validated observation using the V1 status contract."""

    tested_task = _optional_sha256(
        observation["tested_task_contract_sha256"],
        "tested task-contract fingerprint",
    )
    stale_reasons = set()
    if (
        observation["tested_model_catalog_snapshot_sha256"]
        != current_bindings["model_catalog_snapshot_sha256"]
    ):
        stale_reasons.add("catalog_binding_stale")
    if (
        observation["tested_benchmark_contract_sha256"]
        != current_bindings["benchmark_contract_sha256"]
    ):
        stale_reasons.add("benchmark_contract_binding_stale")
    if (
        observation["tested_controlled_plan_sha256"]
        != current_bindings["controlled_plan_sha256"]
    ):
        stale_reasons.add("controlled_plan_binding_stale")
    failure_reasons = set()
    if observation["hard_failure_present"]:
        failure_reasons.add("hard_failure")
    if observation["contract_valid"] is not True:
        failure_reasons.add(
            "contract_invalid"
            if observation["evidence_kind"] == CONTROLLED_LIVE_EVIDENCE_KIND
            else "schema_invalid"
        )
    if observation["normalization_succeeded"] is False:
        failure_reasons.add("normalization_failed")
    if observation["quality_gate_passed"] is not True:
        failure_reasons.add("quality_gate_failed")
    if (
        observation["schedule_completed"] is not True
        or observation["provider_outcome_category"] != "success"
        or observation["provider_call_count"] != 1
        or observation["input_token_count"] <= 0
        or observation["output_token_count"] <= 0
    ):
        failure_reasons.add("benchmark_failed")
    if stale_reasons:
        return "stale", stale_reasons, tested_task
    if failure_reasons:
        return "rejected", failure_reasons | {"benchmark_failed"}, tested_task
    if review_decision == "rejected":
        return "rejected", {"review_rejected"}, tested_task
    if current_task_contract_sha256 is None:
        reasons = {"task_contract_missing"}
        if review_required and review_decision == "pending":
            reasons.add("review_missing")
        return "pending", reasons, tested_task
    if tested_task is None:
        reasons = {"task_contract_binding_missing"}
        if review_required and review_decision == "pending":
            reasons.add("review_missing")
        return "pending", reasons, tested_task
    if tested_task != current_task_contract_sha256:
        return "stale", {"task_contract_binding_stale"}, tested_task
    if review_required and review_decision == "pending":
        return "pending", {"review_missing"}, tested_task
    _require(
        review_requirement_satisfied is True,
        "human-review requirement is not satisfied",
    )
    return "qualified", {"qualification_requirements_satisfied"}, tested_task


def _derive_cell_from_input(
    *,
    scheduled: Mapping[str, Any],
    qualification_input: Mapping[str, Any],
    plan: Dict[str, Any],
    current_bindings: Mapping[str, str],
    current_task_contract_sha256: str | None,
    review_required: bool,
) -> Dict[str, Any]:
    payload = dict(qualification_input)
    _require(
        set(payload) == _QUALIFICATION_INPUT_FIELDS,
        "qualification input fields must match the exact schema",
    )
    _require(
        payload["schedule_key"] == scheduled["schedule_key"],
        "qualification input schedule mismatch",
    )
    evidence = deepcopy(payload["evidence"])
    authorization = deepcopy(payload["authorization"])
    pricing = deepcopy(payload["pricing"])
    observation = build_qualification_observation(
        evidence=evidence,
        schedule_key=scheduled["schedule_key"],
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        tested_task_contract_sha256=payload[
            "tested_task_contract_sha256"
        ],
    )
    evidence_digest = observation["evidence_sha256"]
    _require(
        payload["evidence_sha256"] == evidence_digest,
        "qualification evidence SHA-256 mismatch",
    )
    _require(
        all(
            observation[field] == scheduled[field]
            for field in (
                "schedule_key",
                "case_alias",
                "workload_id",
                "provider",
                "model",
            )
        ),
        "qualification observation identity mismatch",
    )
    review_record = deepcopy(payload["review_record"])
    assessment = assess_post_result_human_review(
        evidence=evidence,
        schedule_key=scheduled["schedule_key"],
        review_record=review_record,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    _require(
        assessment["workload_id"] == scheduled["workload_id"]
        and assessment["provider"] == scheduled["provider"]
        and assessment["model"] == scheduled["model"]
        and assessment["human_review_required"] is review_required,
        "human-review assessment identity mismatch",
    )
    if review_record is None:
        _require(
            payload["review_sha256"] is None,
            "review SHA-256 requires a review record",
        )
        review_digest = None
        reviewed_at_utc = None
    else:
        review_digest = post_result_human_review_sha256(
            review_record,
            evidence=evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )
        _require(
            payload["review_sha256"] == review_digest,
            "qualification review SHA-256 mismatch",
        )
        reviewed_at_utc = review_record["reviewed_at_utc"]
    status, reasons, tested_task = _qualification_status_from_observation(
        observation=observation,
        current_bindings=current_bindings,
        current_task_contract_sha256=current_task_contract_sha256,
        review_required=review_required,
        review_decision=assessment["decision"],
        review_requirement_satisfied=assessment[
            "review_requirement_satisfied"
        ],
    )
    return _build_cell(
        scheduled=scheduled,
        status=status,
        reasons=reasons,
        review_required=review_required,
        current_bindings=current_bindings,
        current_task_contract_sha256=current_task_contract_sha256,
        tested_model_catalog_snapshot_sha256=observation[
            "tested_model_catalog_snapshot_sha256"
        ],
        tested_benchmark_contract_sha256=observation[
            "tested_benchmark_contract_sha256"
        ],
        tested_controlled_plan_sha256=observation[
            "tested_controlled_plan_sha256"
        ],
        tested_task_contract_sha256=tested_task,
        evidence_sha256=evidence_digest,
        review_sha256=review_digest,
        evaluated_at_utc=observation["execution_at_utc"],
        reviewed_at_utc=reviewed_at_utc,
    )


def _reconcile_existing_cell(
    *,
    existing: Mapping[str, Any],
    scheduled: Mapping[str, Any],
    current_bindings: Mapping[str, str],
    current_task_contract_sha256: str | None,
    review_required: bool,
) -> Dict[str, Any]:
    if existing["evidence_sha256"] is None:
        return _pending_cell(
            scheduled=scheduled,
            review_required=review_required,
            current_bindings=current_bindings,
            current_task_contract_sha256=current_task_contract_sha256,
        )
    stale_reasons = set()
    comparisons = (
        (
            existing["tested_model_catalog_snapshot_sha256"],
            current_bindings["model_catalog_snapshot_sha256"],
            "catalog_binding_stale",
        ),
        (
            existing["tested_benchmark_contract_sha256"],
            current_bindings["benchmark_contract_sha256"],
            "benchmark_contract_binding_stale",
        ),
        (
            existing["tested_controlled_plan_sha256"],
            current_bindings["controlled_plan_sha256"],
            "controlled_plan_binding_stale",
        ),
    )
    for tested, current, reason in comparisons:
        if tested != current:
            stale_reasons.add(reason)
    if (
        existing["tested_task_contract_sha256"] is not None
        and existing["tested_task_contract_sha256"]
        != current_task_contract_sha256
    ):
        stale_reasons.add("task_contract_binding_stale")
    if stale_reasons or existing["status"] == "stale":
        if not stale_reasons:
            stale_reasons.add("task_contract_binding_stale")
        return _build_cell(
            scheduled=scheduled,
            status="stale",
            reasons=stale_reasons,
            review_required=review_required,
            current_bindings=current_bindings,
            current_task_contract_sha256=current_task_contract_sha256,
            tested_model_catalog_snapshot_sha256=existing[
                "tested_model_catalog_snapshot_sha256"
            ],
            tested_benchmark_contract_sha256=existing[
                "tested_benchmark_contract_sha256"
            ],
            tested_controlled_plan_sha256=existing[
                "tested_controlled_plan_sha256"
            ],
            tested_task_contract_sha256=existing[
                "tested_task_contract_sha256"
            ],
            evidence_sha256=existing["evidence_sha256"],
            review_sha256=existing["review_sha256"],
            evaluated_at_utc=existing["evaluated_at_utc"],
            reviewed_at_utc=existing["reviewed_at_utc"],
        )
    if existing["tested_task_contract_sha256"] is None:
        reasons = set(existing["status_reasons"])
        reasons.discard("task_contract_missing")
        reasons.discard("task_contract_binding_missing")
        if existing["status"] == "pending":
            reasons.add(
                "task_contract_missing"
                if current_task_contract_sha256 is None
                else "task_contract_binding_missing"
            )
        return _build_cell(
            scheduled=scheduled,
            status=existing["status"],
            reasons=reasons,
            review_required=review_required,
            current_bindings=current_bindings,
            current_task_contract_sha256=current_task_contract_sha256,
            tested_model_catalog_snapshot_sha256=existing[
                "tested_model_catalog_snapshot_sha256"
            ],
            tested_benchmark_contract_sha256=existing[
                "tested_benchmark_contract_sha256"
            ],
            tested_controlled_plan_sha256=existing[
                "tested_controlled_plan_sha256"
            ],
            tested_task_contract_sha256=None,
            evidence_sha256=existing["evidence_sha256"],
            review_sha256=existing["review_sha256"],
            evaluated_at_utc=existing["evaluated_at_utc"],
            reviewed_at_utc=existing["reviewed_at_utc"],
        )
    return deepcopy(dict(existing))


def build_provider_qualification_registry(
    *,
    plan: Dict[str, Any],
    current_task_contract_sha256_by_workload: Mapping[
        str, str | None
    ] | None = None,
    qualification_inputs_by_schedule_key: Mapping[
        str, Mapping[str, Any]
    ] | None = None,
    existing_registry: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build or reconcile current qualification state without caller status flags."""

    controlled_plan = deepcopy(plan)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    current_bindings = build_current_qualification_bindings(controlled_plan)
    schedule = build_execution_schedule(
        plan=controlled_plan,
        authorization={
            "approved_request_matrix": deepcopy(controlled_plan["staged_matrix"]),
            "maximum_request_count": controlled_plan["request_counts"][
                "maximum_total_requests"
            ],
        },
    )
    # build_execution_schedule validates more authorization fields only through
    # its explicit schedule contract; the two values above are the fields read.
    requirements = canonical_human_review_requirements()
    workloads = set(requirements)
    task_fingerprints = _normalize_task_contract_fingerprints(
        current_task_contract_sha256_by_workload,
        workloads=workloads,
    )
    inputs = (
        {}
        if qualification_inputs_by_schedule_key is None
        else dict(qualification_inputs_by_schedule_key)
    )
    schedule_keys = {row["schedule_key"] for row in schedule}
    _require(
        set(inputs).issubset(schedule_keys),
        "qualification input references an unknown schedule key",
    )
    existing_by_identity = {}
    if existing_registry is not None:
        validate_provider_qualification_registry(existing_registry)
        existing_by_identity = {
            (row["workload_id"], row["provider"], row["model"]): row
            for row in existing_registry["cells"]
        }
    cells = []
    for scheduled in schedule:
        review_required = requirements[scheduled["workload_id"]]
        current_task = task_fingerprints[scheduled["workload_id"]]
        qualification_input = inputs.get(scheduled["schedule_key"])
        identity = (
            scheduled["workload_id"],
            scheduled["provider"],
            scheduled["model"],
        )
        if qualification_input is not None:
            cell = _derive_cell_from_input(
                scheduled=scheduled,
                qualification_input=qualification_input,
                plan=controlled_plan,
                current_bindings=current_bindings,
                current_task_contract_sha256=current_task,
                review_required=review_required,
            )
        elif identity in existing_by_identity:
            cell = _reconcile_existing_cell(
                existing=existing_by_identity[identity],
                scheduled=scheduled,
                current_bindings=current_bindings,
                current_task_contract_sha256=current_task,
                review_required=review_required,
            )
        else:
            cell = _pending_cell(
                scheduled=scheduled,
                review_required=review_required,
                current_bindings=current_bindings,
                current_task_contract_sha256=current_task,
            )
        cells.append(cell)
    registry = {
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_contract_version": REGISTRY_CONTRACT_VERSION,
        "registry_scope": REGISTRY_SCOPE,
        "qualification_statuses": list(QUALIFICATION_STATUSES),
        "current_bindings": deepcopy(current_bindings),
        "task_contract_fingerprint_policy": deepcopy(
            _TASK_FINGERPRINT_POLICY
        ),
        "cells": cells,
        "authority_invariants": deepcopy(_AUTHORITY_INVARIANTS),
    }
    validate_provider_qualification_registry(registry, plan=controlled_plan)
    return deepcopy(registry)


def validate_provider_qualification_registry(
    registry: Dict[str, Any],
    *,
    plan: Dict[str, Any] | None = None,
) -> bool:
    _require(
        isinstance(registry, dict) and set(registry) == _REGISTRY_FIELDS,
        "qualification registry fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_key(registry),
        "qualification registry contains prohibited provider or routing data",
    )
    _require(
        registry["registry_schema_version"] == REGISTRY_SCHEMA_VERSION
        and registry["registry_contract_version"] == REGISTRY_CONTRACT_VERSION
        and registry["registry_scope"] == REGISTRY_SCOPE,
        "qualification registry version or scope mismatch",
    )
    _require(
        registry["qualification_statuses"] == list(QUALIFICATION_STATUSES),
        "qualification status vocabulary changed",
    )
    bindings = registry["current_bindings"]
    _require(
        isinstance(bindings, dict)
        and set(bindings) == _CURRENT_BINDING_FIELDS
        and all(_is_sha256(value) for value in bindings.values()),
        "qualification registry current bindings are malformed",
    )
    _require(
        registry["task_contract_fingerprint_policy"] == _TASK_FINGERPRINT_POLICY,
        "task-contract fingerprint policy changed",
    )
    _require(
        registry["authority_invariants"] == _AUTHORITY_INVARIANTS,
        "qualification registry authority changed",
    )
    cells = registry["cells"]
    _require(
        isinstance(cells, list) and 0 < len(cells) <= 256,
        "qualification registry cells are missing or unbounded",
    )
    identities = []
    schedule_keys = []
    for index, cell in enumerate(cells, start=1):
        _require(
            isinstance(cell, dict) and set(cell) == _CELL_FIELDS,
            "qualification cell fields must match the exact schema",
        )
        _require(
            cell["execution_order"] == index,
            "qualification cell order is unstable",
        )
        _require(
            cell["status"] in QUALIFICATION_STATUSES,
            "qualification cell status is unsupported",
        )
        reasons = cell["status_reasons"]
        _require(
            isinstance(reasons, list)
            and bool(reasons)
            and reasons == _ordered_reasons(set(reasons))
            and len(reasons) == len(set(reasons)),
            "qualification status reasons are malformed",
        )
        _require(
            type(cell["human_review_required"]) is bool,
            "human-review requirement must be Boolean",
        )
        for field in (
            "current_model_catalog_snapshot_sha256",
            "current_benchmark_contract_sha256",
            "current_controlled_plan_sha256",
            "qualification_binding_sha256",
        ):
            _require(_is_sha256(cell[field]), f"{field} is malformed")
        for field in (
            "tested_model_catalog_snapshot_sha256",
            "tested_benchmark_contract_sha256",
            "tested_controlled_plan_sha256",
            "current_task_contract_sha256",
            "tested_task_contract_sha256",
            "evidence_sha256",
            "review_sha256",
        ):
            _optional_sha256(cell[field], field)
        _require(
            cell["current_model_catalog_snapshot_sha256"]
            == bindings["model_catalog_snapshot_sha256"]
            and cell["current_benchmark_contract_sha256"]
            == bindings["benchmark_contract_sha256"]
            and cell["current_controlled_plan_sha256"]
            == bindings["controlled_plan_sha256"],
            "qualification cell current bindings differ from registry",
        )
        _require(
            cell["qualification_binding_sha256"]
            == _qualification_binding_sha256(cell),
            "qualification cell binding digest mismatch",
        )
        _require(
            isinstance(cell["schedule_key"], str)
            and bool(cell["schedule_key"])
            and isinstance(cell["case_alias"], str)
            and bool(cell["case_alias"])
            and isinstance(cell["workload_id"], str)
            and bool(cell["workload_id"])
            and isinstance(cell["provider"], str)
            and bool(cell["provider"])
            and isinstance(cell["model"], str)
            and bool(cell["model"]),
            "qualification cell identity is malformed",
        )
        _require(
            cell["evaluated_at_utc"] is None
            or normalize_execution_timestamp(cell["evaluated_at_utc"])
            == cell["evaluated_at_utc"],
            "qualification cell evaluated_at_utc is malformed",
        )
        _require(
            cell["reviewed_at_utc"] is None
            or normalize_review_timestamp(cell["reviewed_at_utc"])
            == cell["reviewed_at_utc"],
            "qualification cell reviewed_at_utc is malformed",
        )
        if cell["status"] == "qualified":
            _require(
                cell["evidence_sha256"] is not None
                and cell["current_task_contract_sha256"] is not None
                and cell["tested_task_contract_sha256"]
                == cell["current_task_contract_sha256"]
                and cell["status_reasons"]
                == ["qualification_requirements_satisfied"],
                "qualified cell is missing a required binding",
            )
            if cell["human_review_required"]:
                _require(
                    cell["review_sha256"] is not None,
                    "qualified review-required cell is missing review binding",
                )
        elif cell["status"] == "pending":
            _require(
                "qualification_requirements_satisfied" not in reasons
                and set(reasons).issubset(
                    {
                        "evidence_missing",
                        "task_contract_missing",
                        "task_contract_binding_missing",
                        "review_missing",
                    }
                ),
                "pending cell has a non-pending reason",
            )
        elif cell["status"] == "rejected":
            _require(
                cell["evidence_sha256"] is not None
                and bool(
                    set(reasons)
                    & {
                        "hard_failure",
                        "contract_invalid",
                        "schema_invalid",
                        "normalization_failed",
                        "quality_gate_failed",
                        "benchmark_failed",
                        "review_rejected",
                    }
                ),
                "rejected cell lacks bounded failure evidence",
            )
        elif cell["status"] == "stale":
            _require(
                cell["evidence_sha256"] is not None
                and bool(
                    set(reasons)
                    & {
                        "catalog_binding_stale",
                        "benchmark_contract_binding_stale",
                        "controlled_plan_binding_stale",
                        "task_contract_binding_stale",
                    }
                ),
                "stale cell lacks an invalidation reason",
            )
        identities.append(
            (cell["workload_id"], cell["provider"], cell["model"])
        )
        schedule_keys.append(cell["schedule_key"])
    _require(
        len(identities) == len(set(identities))
        and len(schedule_keys) == len(set(schedule_keys)),
        "qualification registry contains duplicate cells",
    )
    if plan is not None:
        controlled_plan = deepcopy(plan)
        validate_controlled_provider_benchmark_plan(controlled_plan)
        current = build_current_qualification_bindings(controlled_plan)
        _require(bindings == current, "qualification registry bindings are not current")
        schedule = build_execution_schedule(
            plan=controlled_plan,
            authorization={
                "approved_request_matrix": deepcopy(
                    controlled_plan["staged_matrix"]
                ),
                "maximum_request_count": controlled_plan["request_counts"][
                    "maximum_total_requests"
                ],
            },
        )
        expected = [
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
        actual = [
            (
                row["execution_order"],
                row["schedule_key"],
                row["case_alias"],
                row["workload_id"],
                row["provider"],
                row["model"],
            )
            for row in cells
        ]
        _require(actual == expected, "qualification registry universe changed")
    return True


def _renderer_bound_ordered_reasons(reasons: set[str]) -> list[str]:
    _require(
        reasons.issubset(_RENDERER_BOUND_STATUS_REASONS),
        "unknown renderer-bound qualification reason",
    )
    return [
        reason
        for reason in _RENDERER_BOUND_STATUS_REASON_ORDER
        if reason in reasons
    ]


def _renderer_bound_qualification_binding_payload(
    cell: Mapping[str, Any],
) -> Dict[str, Any]:
    """Return only the material that may invalidate renderer-bound authority.

    The global controlled-plan pair and the globally derived schedule_key /
    case_alias remain on the cell as provenance but are intentionally absent
    here, so one workload's qualification cannot be invalidated by an unrelated
    workload's fixture change.
    """

    return {
        "workload_id": cell["workload_id"],
        "provider": cell["provider"],
        "model": cell["model"],
        "status": cell["status"],
        "current_model_catalog_snapshot_sha256": cell[
            "current_model_catalog_snapshot_sha256"
        ],
        "tested_model_catalog_snapshot_sha256": cell[
            "tested_model_catalog_snapshot_sha256"
        ],
        "current_benchmark_contract_sha256": cell[
            "current_benchmark_contract_sha256"
        ],
        "tested_benchmark_contract_sha256": cell[
            "tested_benchmark_contract_sha256"
        ],
        "current_task_contract_sha256": cell["current_task_contract_sha256"],
        "tested_task_contract_sha256": cell["tested_task_contract_sha256"],
        "qualification_semantics_generation": cell[
            "qualification_semantics_generation"
        ],
        "current_workload_qualification_semantics_sha256": cell[
            "current_workload_qualification_semantics_sha256"
        ],
        "tested_workload_qualification_semantics_sha256": cell[
            "tested_workload_qualification_semantics_sha256"
        ],
        "qualification_schedule_keys": cell["qualification_schedule_keys"],
        "qualification_case_aliases": cell["qualification_case_aliases"],
        "evidence_sha256": cell["evidence_sha256"],
        "review_sha256": cell["review_sha256"],
    }


def renderer_bound_qualification_binding_sha256(
    cell: Mapping[str, Any],
) -> str:
    """Return the renderer-bound qualification binding digest for one cell."""

    return sha256(
        _canonical_json(
            _renderer_bound_qualification_binding_payload(cell)
        ).encode("utf-8")
    ).hexdigest()


def build_renderer_bound_qualification_cell(
    *,
    base_cell: Mapping[str, Any],
    qualification_semantics_generation: str,
    current_workload_qualification_semantics_sha256: str,
    tested_workload_qualification_semantics_sha256: str | None = None,
    renderer_semantics_superseded: bool = False,
) -> Dict[str, Any]:
    """Project one V1 cell into the renderer-bound generation.

    Pure. The tested workload-semantics digest is never derived from current
    code: legacy cells must supply ``None`` and renderer-bound cells must supply
    the digest their own fresh evidence actually recorded.
    """

    _require(
        isinstance(base_cell, Mapping)
        and set(base_cell) == _CELL_FIELDS,
        "renderer-bound projection requires an exact V1 cell",
    )
    generation = str(qualification_semantics_generation or "").strip()
    _require(
        generation in QUALIFICATION_SEMANTICS_GENERATIONS,
        "unsupported qualification semantics generation",
    )
    current_semantics = current_workload_qualification_semantics_sha256
    _require(
        _is_sha256(current_semantics),
        "current workload semantics digest must be a lowercase SHA-256 digest",
    )
    tested_semantics = _optional_sha256(
        tested_workload_qualification_semantics_sha256,
        "tested workload semantics digest",
    )

    status = base_cell["status"]
    _require(status in QUALIFICATION_STATUSES, "unsupported qualification status")
    reasons = set(base_cell["status_reasons"])

    if generation == LEGACY_QUALIFICATION_SEMANTICS_GENERATION:
        _require(
            tested_semantics is None,
            "legacy generation must not carry a tested workload semantics digest",
        )
        if status in {"qualified", "stale"}:
            # A legacy positive never proves current renderer-bound
            # qualification, so it fails closed into the existing stale status.
            if status == "qualified":
                reasons.discard("qualification_requirements_satisfied")
            status = "stale"
            reasons.add("workload_semantics_binding_missing")
    else:
        _require(
            tested_semantics is not None,
            "renderer-bound generation requires a tested workload semantics digest",
        )
        if tested_semantics != current_semantics and status != "rejected":
            reasons.discard("qualification_requirements_satisfied")
            status = "stale"
            reasons.add("workload_semantics_binding_stale")

    if renderer_semantics_superseded:
        reasons.add("renderer_semantics_superseded")

    cell = {
        field: deepcopy(base_cell[field])
        for field in _CELL_FIELDS
        if field != "qualification_binding_sha256"
    }
    cell["status"] = status
    cell["status_reasons"] = _renderer_bound_ordered_reasons(reasons)
    cell["qualification_semantics_generation"] = generation
    cell["current_workload_qualification_semantics_sha256"] = current_semantics
    cell["tested_workload_qualification_semantics_sha256"] = tested_semantics
    if generation == RENDERER_BOUND_QUALIFICATION_SEMANTICS_GENERATION:
        cell["qualification_schedule_keys"] = [cell["schedule_key"]]
        cell["qualification_case_aliases"] = [cell["case_alias"]]
    else:
        # Migrated historical evidence has no renderer-bound case-coverage
        # authority. Preserve that absence explicitly instead of inventing it.
        cell["qualification_schedule_keys"] = []
        cell["qualification_case_aliases"] = []
    cell["qualification_binding_sha256"] = (
        renderer_bound_qualification_binding_sha256(cell)
    )
    return cell


def _validate_renderer_bound_candidate_observation(
    observation: Any,
) -> Mapping[str, Any]:
    required_fields = {
        "observation_version",
        "evidence_kind",
        "evidence_schema_version",
        "evidence_sha256",
        "schedule_key",
        "case_alias",
        "workload_id",
        "provider",
        "model",
        "execution_at_utc",
        "tested_model_catalog_snapshot_sha256",
        "tested_benchmark_contract_sha256",
        "tested_controlled_plan_sha256",
        "tested_task_contract_sha256",
        "schedule_completed",
        "provider_outcome_category",
        "provider_call_count",
        "contract_valid",
        "normalization_succeeded",
        "quality_gate_passed",
        "hard_failure_present",
        "input_token_count",
        "output_token_count",
        "human_review_required",
        "authority_safety_valid",
        "qualification_semantics_generation",
        "tested_workload_qualification_semantics_sha256",
    }
    _require(
        isinstance(observation, Mapping)
        and set(observation) == required_fields,
        "renderer-bound candidate observation is malformed",
    )
    _require(
        observation["observation_version"]
        == RENDERER_BOUND_OBSERVATION_VERSION
        and observation["evidence_kind"] == CONTROLLED_LIVE_EVIDENCE_KIND
        and observation["qualification_semantics_generation"]
        == RENDERER_BOUND_QUALIFICATION_SEMANTICS_GENERATION,
        "renderer-bound candidate observation generation is invalid",
    )
    for field in (
        "evidence_sha256",
        "tested_model_catalog_snapshot_sha256",
        "tested_benchmark_contract_sha256",
        "tested_controlled_plan_sha256",
        "tested_workload_qualification_semantics_sha256",
    ):
        _require(_is_sha256(observation[field]), f"{field} is malformed")
    _optional_sha256(
        observation["tested_task_contract_sha256"],
        "tested task-contract fingerprint",
    )
    for field in (
        "evidence_schema_version",
        "schedule_key",
        "case_alias",
        "workload_id",
        "provider",
        "model",
        "provider_outcome_category",
    ):
        _require(
            isinstance(observation[field], str)
            and bool(observation[field].strip()),
            f"renderer-bound candidate observation {field} is malformed",
        )
    for field in (
        "schedule_completed",
        "contract_valid",
        "quality_gate_passed",
        "hard_failure_present",
        "human_review_required",
        "authority_safety_valid",
    ):
        _require(
            type(observation[field]) is bool,
            f"renderer-bound candidate observation {field} must be Boolean",
        )
    _require(
        observation["authority_safety_valid"] is True,
        "renderer-bound candidate observation authority safety is invalid",
    )
    normalization = observation["normalization_succeeded"]
    _require(
        type(normalization) is bool or normalization is None,
        "renderer-bound candidate observation normalization is malformed",
    )
    for field in ("provider_call_count", "input_token_count", "output_token_count"):
        _require(
            type(observation[field]) is int and observation[field] >= 0,
            f"renderer-bound candidate observation {field} is malformed",
        )
    _require(
        normalize_execution_timestamp(observation["execution_at_utc"])
        == observation["execution_at_utc"],
        "renderer-bound candidate observation execution timestamp is malformed",
    )
    return observation


def build_renderer_bound_candidate_qualification_cell(
    *,
    plan: Dict[str, Any],
    workload_id: str,
    provider: str,
    model: str,
    observations: list[Mapping[str, Any]],
    current_task_contract_sha256: str | None,
    current_workload_qualification_semantics_sha256: str,
) -> Dict[str, Any]:
    """Aggregate one run's case observations into one candidate authority cell.

    Required coverage comes exclusively from the validated plan. Observations
    are normalized to that plan order and interpreted through the existing
    single-case renderer-bound primitive before status aggregation.
    """

    controlled_plan = deepcopy(plan)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    identity = (workload_id, provider, model)
    _require(
        all(isinstance(part, str) and bool(part.strip()) for part in identity),
        "renderer-bound candidate identity is malformed",
    )
    schedule = build_execution_schedule(
        plan=controlled_plan,
        authorization={
            "approved_request_matrix": deepcopy(
                controlled_plan["staged_matrix"]
            ),
            "maximum_request_count": controlled_plan["request_counts"][
                "maximum_total_requests"
            ],
        },
    )
    required = [
        row
        for row in schedule
        if (row["workload_id"], row["provider"], row["model"]) == identity
    ]
    _require(required, "renderer-bound candidate is absent from the plan")
    _require(
        isinstance(observations, list)
        and 0 < len(observations) <= len(required),
        "renderer-bound candidate observations are missing or unbounded",
    )

    required_by_schedule = {row["schedule_key"]: row for row in required}
    required_by_case = {row["case_alias"]: row for row in required}
    _require(
        len(required_by_schedule) == len(required)
        and len(required_by_case) == len(required),
        "renderer-bound candidate plan coverage is not unique",
    )
    by_schedule = {}
    seen_cases = set()
    evidence_digests = set()
    evaluated_at_values = set()
    human_review_values = set()
    for supplied in observations:
        observation = _validate_renderer_bound_candidate_observation(supplied)
        _require(
            (
                observation["workload_id"],
                observation["provider"],
                observation["model"],
            )
            == identity,
            "renderer-bound candidate observation identity mismatch",
        )
        schedule_key = observation["schedule_key"]
        case_alias = observation["case_alias"]
        _require(
            schedule_key in required_by_schedule,
            "renderer-bound candidate observation schedule is unknown",
        )
        _require(
            case_alias in required_by_case,
            "renderer-bound candidate observation case is unknown",
        )
        _require(
            schedule_key not in by_schedule,
            "renderer-bound candidate observation schedule is duplicated",
        )
        _require(
            case_alias not in seen_cases,
            "renderer-bound candidate observation case is duplicated",
        )
        _require(
            required_by_schedule[schedule_key]["case_alias"] == case_alias
            and required_by_case[case_alias]["schedule_key"] == schedule_key,
            "renderer-bound candidate observation schedule/case mismatch",
        )
        by_schedule[schedule_key] = observation
        seen_cases.add(case_alias)
        evidence_digests.add(observation["evidence_sha256"])
        evaluated_at_values.add(observation["execution_at_utc"])
        human_review_values.add(observation["human_review_required"])

    _require(
        len(evidence_digests) == 1,
        "renderer-bound candidate observations span multiple evidence runs",
    )
    _require(
        len(evaluated_at_values) == 1,
        "renderer-bound candidate observations have conflicting execution times",
    )
    _require(
        len(human_review_values) == 1,
        "renderer-bound candidate observations have conflicting review requirements",
    )
    requirements = canonical_human_review_requirements()
    _require(
        workload_id in requirements
        and human_review_values == {requirements[workload_id]},
        "renderer-bound candidate human-review authority mismatch",
    )

    current_bindings = build_current_qualification_bindings(controlled_plan)
    current_task = _optional_sha256(
        current_task_contract_sha256,
        "current task-contract fingerprint",
    )
    current_semantics = current_workload_qualification_semantics_sha256
    _require(
        _is_sha256(current_semantics),
        "current workload semantics digest must be a lowercase SHA-256 digest",
    )
    canonical_observations = [
        (row, by_schedule[row["schedule_key"]])
        for row in required
        if row["schedule_key"] in by_schedule
    ]
    primitive_cells = []
    for scheduled, observation in canonical_observations:
        review_required = requirements[workload_id]
        status, reasons, tested_task = _qualification_status_from_observation(
            observation=observation,
            current_bindings=current_bindings,
            current_task_contract_sha256=current_task,
            review_required=review_required,
            review_decision="pending" if review_required else "not_required",
            review_requirement_satisfied=not review_required,
        )
        base_cell = _build_cell(
            scheduled=scheduled,
            status=status,
            reasons=reasons,
            review_required=review_required,
            current_bindings=current_bindings,
            current_task_contract_sha256=current_task,
            tested_model_catalog_snapshot_sha256=observation[
                "tested_model_catalog_snapshot_sha256"
            ],
            tested_benchmark_contract_sha256=observation[
                "tested_benchmark_contract_sha256"
            ],
            tested_controlled_plan_sha256=observation[
                "tested_controlled_plan_sha256"
            ],
            tested_task_contract_sha256=tested_task,
            evidence_sha256=observation["evidence_sha256"],
            evaluated_at_utc=observation["execution_at_utc"],
        )
        primitive_cells.append(
            build_renderer_bound_qualification_cell(
                base_cell=base_cell,
                qualification_semantics_generation=observation[
                    "qualification_semantics_generation"
                ],
                current_workload_qualification_semantics_sha256=(
                    current_semantics
                ),
                tested_workload_qualification_semantics_sha256=observation[
                    "tested_workload_qualification_semantics_sha256"
                ],
            )
        )

    complete = len(primitive_cells) == len(required)
    if any(cell["status"] == "rejected" for cell in primitive_cells):
        status = "rejected"
    elif any(cell["status"] == "stale" for cell in primitive_cells):
        status = "stale"
    elif not complete or any(
        cell["status"] == "pending" for cell in primitive_cells
    ):
        status = "pending"
    else:
        status = "qualified"

    winning_cells = [
        cell for cell in primitive_cells if cell["status"] == status
    ]
    source = winning_cells[0] if winning_cells else primitive_cells[0]
    reasons = {
        reason
        for cell in winning_cells
        for reason in cell["status_reasons"]
    }
    if status == "pending" and not complete:
        reasons.add("evidence_missing")
    if status == "qualified":
        reasons = {"qualification_requirements_satisfied"}

    candidate = deepcopy(source)
    representative = required[0]
    candidate["execution_order"] = representative["execution_order"]
    candidate["schedule_key"] = representative["schedule_key"]
    candidate["case_alias"] = representative["case_alias"]
    candidate["status"] = status
    candidate["status_reasons"] = _renderer_bound_ordered_reasons(reasons)
    candidate["qualification_schedule_keys"] = [
        row["schedule_key"] for row, _observation in canonical_observations
    ]
    candidate["qualification_case_aliases"] = [
        row["case_alias"] for row, _observation in canonical_observations
    ]
    candidate["qualification_binding_sha256"] = (
        renderer_bound_qualification_binding_sha256(candidate)
    )
    return candidate


def _normalize_superseded_cell_identities(
    value: Any,
    *,
    known_identities: set[tuple[str, str, str]],
) -> set[tuple[str, str, str]]:
    if value is None:
        return set()
    normalized = set()
    for entry in value:
        _require(
            isinstance(entry, (tuple, list)) and len(entry) == 3,
            "superseded identity must be a (workload_id, provider, model) triple",
        )
        identity = tuple(str(part or "").strip() for part in entry)
        _require(
            all(identity),
            "superseded identity must be fully specified",
        )
        _require(
            identity in known_identities,
            "superseded identity is not present in the source registry",
        )
        normalized.add(identity)
    return normalized


def project_registry_to_renderer_bound_generation(
    registry: Dict[str, Any],
    *,
    current_workload_qualification_semantics_sha256_by_workload: Mapping[
        str, str
    ],
    superseded_cell_identities: Any = None,
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Project a validated V1 registry into the renderer-bound generation.

    Pure and in-memory: the source registry is never mutated, no artifact is
    written, and no evidence, review, or historical tested semantics digest is
    invented.
    """

    payload = deepcopy(registry)
    validate_provider_qualification_registry(payload, plan=plan)

    semantics = current_workload_qualification_semantics_sha256_by_workload
    _require(
        isinstance(semantics, Mapping),
        "current workload semantics digests must be a mapping",
    )
    workloads = {cell["workload_id"] for cell in payload["cells"]}
    _require(
        workloads.issubset(set(semantics)),
        "current workload semantics digests are missing a registry workload",
    )

    known_identities = {
        (cell["workload_id"], cell["provider"], cell["model"])
        for cell in payload["cells"]
    }
    superseded = _normalize_superseded_cell_identities(
        superseded_cell_identities,
        known_identities=known_identities,
    )

    cells = [
        build_renderer_bound_qualification_cell(
            base_cell=cell,
            qualification_semantics_generation=(
                LEGACY_QUALIFICATION_SEMANTICS_GENERATION
            ),
            current_workload_qualification_semantics_sha256=semantics[
                cell["workload_id"]
            ],
            tested_workload_qualification_semantics_sha256=None,
            renderer_semantics_superseded=(
                (cell["workload_id"], cell["provider"], cell["model"])
                in superseded
            ),
        )
        for cell in payload["cells"]
    ]
    projected = {
        field: deepcopy(payload[field])
        for field in _REGISTRY_FIELDS
        if field != "cells"
    }
    projected["registry_schema_version"] = (
        RENDERER_BOUND_REGISTRY_SCHEMA_VERSION
    )
    projected["registry_contract_version"] = (
        RENDERER_BOUND_REGISTRY_CONTRACT_VERSION
    )
    projected["qualification_semantics_generations"] = list(
        QUALIFICATION_SEMANTICS_GENERATIONS
    )
    projected["cells"] = cells
    validate_renderer_bound_qualification_registry(projected)
    return projected


def validate_renderer_bound_qualification_registry(
    registry: Dict[str, Any],
    *,
    plan: Dict[str, Any] | None = None,
) -> bool:
    """Validate the next-generation representation without touching V1."""

    expected_fields = set(_REGISTRY_FIELDS) | {
        "qualification_semantics_generations"
    }
    _require(
        isinstance(registry, dict) and set(registry) == expected_fields,
        "renderer-bound registry fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_key(registry),
        "renderer-bound registry contains prohibited provider or routing data",
    )
    _require(
        registry["registry_schema_version"]
        == RENDERER_BOUND_REGISTRY_SCHEMA_VERSION
        and registry["registry_contract_version"]
        == RENDERER_BOUND_REGISTRY_CONTRACT_VERSION
        and registry["registry_scope"] == REGISTRY_SCOPE,
        "renderer-bound registry version or scope mismatch",
    )
    _require(
        registry["qualification_statuses"] == list(QUALIFICATION_STATUSES),
        "qualification status vocabulary changed",
    )
    _require(
        registry["qualification_semantics_generations"]
        == list(QUALIFICATION_SEMANTICS_GENERATIONS),
        "qualification semantics generation vocabulary changed",
    )
    expected_cell_fields = set(_CELL_FIELDS) | _RENDERER_BOUND_CELL_ADDED_FIELDS
    cells = registry["cells"]
    _require(
        isinstance(cells, list) and bool(cells),
        "renderer-bound cells are invalid",
    )
    identities = []
    for cell in cells:
        _require(
            isinstance(cell, dict) and set(cell) == expected_cell_fields,
            "renderer-bound cell fields must match the exact schema",
        )
        _require(
            cell["status"] in QUALIFICATION_STATUSES,
            "renderer-bound cell status is invalid",
        )
        _require(
            all(
                isinstance(cell[field], str) and bool(cell[field].strip())
                for field in ("workload_id", "provider", "model")
            ),
            "renderer-bound cell identity is invalid",
        )
        reasons = cell["status_reasons"]
        _require(
            isinstance(reasons, list)
            and bool(reasons)
            and reasons == _renderer_bound_ordered_reasons(set(reasons))
            and len(reasons) == len(set(reasons)),
            "renderer-bound cell reasons are invalid",
        )
        _require(
            cell["qualification_semantics_generation"]
            in QUALIFICATION_SEMANTICS_GENERATIONS,
            "renderer-bound cell generation is invalid",
        )
        _require(
            _is_sha256(
                cell["current_workload_qualification_semantics_sha256"]
            ),
            "renderer-bound current workload semantics digest is invalid",
        )
        tested_semantics = cell[
            "tested_workload_qualification_semantics_sha256"
        ]
        if (
            cell["qualification_semantics_generation"]
            == LEGACY_QUALIFICATION_SEMANTICS_GENERATION
        ):
            _require(
                tested_semantics is None,
                "legacy cell must not carry a tested workload semantics digest",
            )
            _require(
                cell["status"] != "qualified",
                "legacy cell must not claim renderer-bound qualification",
            )
        else:
            _require(
                _is_sha256(tested_semantics),
                "renderer-bound tested workload semantics digest is invalid",
            )
        schedule_keys = cell["qualification_schedule_keys"]
        case_aliases = cell["qualification_case_aliases"]
        _require(
            isinstance(schedule_keys, list)
            and isinstance(case_aliases, list)
            and len(schedule_keys) == len(case_aliases)
            and len(schedule_keys) == len(set(schedule_keys))
            and len(case_aliases) == len(set(case_aliases))
            and all(
                isinstance(value, str) and bool(value.strip())
                for value in schedule_keys + case_aliases
            ),
            "renderer-bound qualification coverage is malformed",
        )
        if (
            cell["qualification_semantics_generation"]
            == LEGACY_QUALIFICATION_SEMANTICS_GENERATION
        ):
            _require(
                not schedule_keys and not case_aliases,
                "legacy cell must not claim renderer-bound case coverage",
            )
        else:
            _require(
                bool(schedule_keys),
                "renderer-bound cell must record observed case coverage",
            )
        _require(
            set(cell["status_reasons"]).issubset(
                _RENDERER_BOUND_STATUS_REASONS
            ),
            "renderer-bound cell reasons are invalid",
        )
        _require(
            cell["qualification_binding_sha256"]
            == renderer_bound_qualification_binding_sha256(cell),
            "renderer-bound qualification binding digest mismatch",
        )
        identities.append(
            (cell["workload_id"], cell["provider"], cell["model"])
        )
    _require(
        len(identities) == len(set(identities)),
        "renderer-bound registry contains duplicate candidate cells",
    )
    if plan is not None:
        controlled_plan = deepcopy(plan)
        validate_controlled_provider_benchmark_plan(controlled_plan)
        schedule = build_execution_schedule(
            plan=controlled_plan,
            authorization={
                "approved_request_matrix": deepcopy(
                    controlled_plan["staged_matrix"]
                ),
                "maximum_request_count": controlled_plan["request_counts"][
                    "maximum_total_requests"
                ],
            },
        )
        required_by_identity = {}
        for row in schedule:
            identity = (row["workload_id"], row["provider"], row["model"])
            required_by_identity.setdefault(identity, []).append(row)
        _require(
            identities == list(required_by_identity),
            "renderer-bound registry candidate universe changed",
        )
        for cell in cells:
            if (
                cell["qualification_semantics_generation"]
                == LEGACY_QUALIFICATION_SEMANTICS_GENERATION
            ):
                continue
            identity = (cell["workload_id"], cell["provider"], cell["model"])
            required = required_by_identity[identity]
            representative = required[0]
            _require(
                cell["execution_order"] == representative["execution_order"]
                and cell["schedule_key"] == representative["schedule_key"]
                and cell["case_alias"] == representative["case_alias"],
                "renderer-bound candidate representative schedule is invalid",
            )
            required_pairs = [
                (row["schedule_key"], row["case_alias"])
                for row in required
            ]
            observed_pairs = list(
                zip(
                    cell["qualification_schedule_keys"],
                    cell["qualification_case_aliases"],
                )
            )
            _require(
                observed_pairs
                == [pair for pair in required_pairs if pair in observed_pairs],
                "renderer-bound candidate coverage is outside plan authority",
            )
            if cell["status"] == "qualified":
                _require(
                    observed_pairs == required_pairs,
                    "qualified renderer-bound candidate coverage is incomplete",
                )
    return True


def serialize_renderer_bound_qualification_registry(
    registry: Dict[str, Any],
) -> str:
    payload = deepcopy(registry)
    validate_renderer_bound_qualification_registry(payload)
    return _canonical_json(payload)


def renderer_bound_qualification_registry_sha256(
    registry: Dict[str, Any],
) -> str:
    return sha256(
        serialize_renderer_bound_qualification_registry(registry).encode(
            "utf-8"
        )
    ).hexdigest()


def serialize_provider_qualification_registry(
    registry: Dict[str, Any],
    *,
    plan: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(registry)
    validate_provider_qualification_registry(payload, plan=plan)
    return _canonical_json(payload)


def provider_qualification_registry_sha256(
    registry: Dict[str, Any],
    *,
    plan: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_provider_qualification_registry(
            registry,
            plan=plan,
        ).encode("utf-8")
    ).hexdigest()


def _prepare_registry_path(
    artifact_path: str | Path,
    *,
    repository_root: str | Path,
    require_existing: bool,
    approved_relative_path: Path = REGISTRY_ARTIFACT_PATH,
) -> Path:
    root = Path(repository_root).resolve()
    _require(root.is_dir() and not root.is_symlink(), "repository root is unsafe")
    candidate = Path(artifact_path)
    _require(candidate.is_absolute(), "registry path must be absolute")
    _require(".." not in candidate.parts, "registry path traversal is prohibited")
    expected = root / approved_relative_path
    _require(candidate == expected, "registry path is outside the approved namespace")
    current = root
    for part in approved_relative_path.parts[:-1]:
        current = current / part
        if current.exists() or current.is_symlink():
            _require(
                current.is_dir() and not current.is_symlink(),
                "registry parent path is unsafe",
            )
        else:
            current.mkdir(mode=0o700)
        _require(
            not stat.S_IMODE(current.stat().st_mode)
            & (stat.S_IWGRP | stat.S_IWOTH),
            "registry parent permissions are unsafe",
        )
    if require_existing:
        _require(
            candidate.is_file() and not candidate.is_symlink(),
            "registry artifact is missing or unsafe",
        )
    else:
        _require(
            not candidate.exists() and not candidate.is_symlink(),
            "registry artifact overwrite is prohibited",
        )
    return candidate


def _write_exclusive(path: Path, encoded: bytes) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise
    finally:
        os.close(descriptor)
    os.chmod(path, 0o600)


def load_provider_qualification_registry(
    artifact_path: str | Path,
    *,
    repository_root: str | Path,
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    path = _prepare_registry_path(
        artifact_path,
        repository_root=repository_root,
        require_existing=True,
    )
    _require(stat.S_IMODE(path.stat().st_mode) == 0o600, "registry mode must be 0600")
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("persisted qualification registry is malformed") from None
    validate_provider_qualification_registry(registry, plan=plan)
    return deepcopy(registry)


def load_renderer_bound_skill_qualification_registry(
    artifact_path: str | Path,
    *,
    repository_root: str | Path,
) -> Dict[str, Any]:
    """Load the versioned Skill-only renderer-bound authority artifact."""

    path = _prepare_registry_path(
        artifact_path,
        repository_root=repository_root,
        require_existing=True,
        approved_relative_path=RENDERER_BOUND_SKILL_REGISTRY_ARTIFACT_PATH,
    )
    _require(
        not stat.S_IMODE(path.stat().st_mode) & (stat.S_IWGRP | stat.S_IWOTH),
        "renderer-bound Skill registry permissions are unsafe",
    )
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError(
            "persisted renderer-bound Skill registry is malformed"
        ) from None
    validate_renderer_bound_qualification_registry(registry)
    return deepcopy(registry)


def write_initial_renderer_bound_skill_qualification_registry(
    artifact_path: str | Path,
    registry: Dict[str, Any],
    *,
    repository_root: str | Path,
) -> Path:
    """Persist one new validated Skill-only renderer-bound authority."""

    encoded = serialize_renderer_bound_qualification_registry(
        registry
    ).encode("utf-8")
    path = _prepare_registry_path(
        artifact_path,
        repository_root=repository_root,
        require_existing=False,
        approved_relative_path=RENDERER_BOUND_SKILL_REGISTRY_ARTIFACT_PATH,
    )
    _write_exclusive(path, encoded)
    loaded = load_renderer_bound_skill_qualification_registry(
        path,
        repository_root=repository_root,
    )
    _require(
        loaded == registry,
        "persisted renderer-bound Skill registry changed during creation",
    )
    return path


def write_initial_provider_qualification_registry(
    artifact_path: str | Path,
    registry: Dict[str, Any],
    *,
    repository_root: str | Path,
    plan: Dict[str, Any],
) -> Path:
    encoded = serialize_provider_qualification_registry(
        registry,
        plan=plan,
    ).encode("utf-8")
    path = _prepare_registry_path(
        artifact_path,
        repository_root=repository_root,
        require_existing=False,
    )
    _write_exclusive(path, encoded)
    loaded = load_provider_qualification_registry(
        path,
        repository_root=repository_root,
        plan=plan,
    )
    _require(loaded == registry, "persisted registry changed during creation")
    return path


def replace_provider_qualification_registry_atomic(
    artifact_path: str | Path,
    registry: Dict[str, Any],
    *,
    expected_prior_sha256: str,
    repository_root: str | Path,
    plan: Dict[str, Any],
) -> Path:
    path = _prepare_registry_path(
        artifact_path,
        repository_root=repository_root,
        require_existing=True,
    )
    prior = load_provider_qualification_registry(
        path,
        repository_root=repository_root,
    )
    observed_prior = provider_qualification_registry_sha256(prior)
    _require(
        expected_prior_sha256 == observed_prior,
        "qualification registry prior digest mismatch",
    )
    encoded = serialize_provider_qualification_registry(
        registry,
        plan=plan,
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.close(descriptor)
        descriptor = -1
        current = load_provider_qualification_registry(
            path,
            repository_root=repository_root,
        )
        _require(
            provider_qualification_registry_sha256(current)
            == expected_prior_sha256,
            "qualification registry changed before replacement",
        )
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    loaded = load_provider_qualification_registry(
        path,
        repository_root=repository_root,
        plan=plan,
    )
    _require(loaded == registry, "atomic registry replacement changed payload")
    return path
