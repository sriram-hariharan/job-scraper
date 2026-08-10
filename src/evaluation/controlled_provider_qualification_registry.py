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
    provider_neutral_run_evidence_sha256,
    validate_provider_neutral_run_evidence,
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
from src.evaluation.provider_benchmark_contract import (
    provider_benchmark_contract_sha256,
)


REGISTRY_CONTRACT_VERSION = "controlled-provider-qualification-registry-v1"
REGISTRY_SCHEMA_VERSION = "controlled-provider-qualification-registry-artifact-v1"
REGISTRY_SCOPE = "evaluation_qualification_state_only"
REGISTRY_ARTIFACT_PATH = Path(
    "outputs/provider_benchmark/provider-qualification-registry.json"
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


def _summary_for_schedule(
    evidence: Mapping[str, Any],
    scheduled: Mapping[str, Any],
) -> Dict[str, Any]:
    summaries = [
        row
        for row in evidence["grading_summaries"]
        if row["schedule_key"] == scheduled["schedule_key"]
    ]
    _require(len(summaries) == 1, "evidence is missing the exact schedule result")
    summary = summaries[0]
    _require(
        all(
            summary[field] == scheduled[field]
            for field in ("case_alias", "workload_id", "provider", "model")
        ),
        "evidence workload/provider/model identity mismatch",
    )
    return deepcopy(summary)


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
    validate_provider_neutral_run_evidence(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    evidence_digest = provider_neutral_run_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    _require(
        payload["evidence_sha256"] == evidence_digest,
        "qualification evidence SHA-256 mismatch",
    )
    summary = _summary_for_schedule(evidence, scheduled)
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
    tested_task = _optional_sha256(
        payload["tested_task_contract_sha256"],
        "tested task-contract fingerprint",
    )
    stale_reasons = set()
    if (
        evidence["model_catalog_snapshot_sha256"]
        != current_bindings["model_catalog_snapshot_sha256"]
    ):
        stale_reasons.add("catalog_binding_stale")
    if (
        plan["step8l_contract_sha256"]
        != current_bindings["benchmark_contract_sha256"]
    ):
        stale_reasons.add("benchmark_contract_binding_stale")
    if evidence["plan_sha256"] != current_bindings["controlled_plan_sha256"]:
        stale_reasons.add("controlled_plan_binding_stale")
    failure_reasons = set()
    if evidence["hard_failure_present"]:
        failure_reasons.add("hard_failure")
    if summary["schema_valid"] is not True:
        failure_reasons.add("schema_invalid")
    if summary["normalization_succeeded"] is not True:
        failure_reasons.add("normalization_failed")
    if (
        summary["quality_gate_passed"] is not True
        or any(summary["hard_failures"].values())
    ):
        failure_reasons.add("quality_gate_failed")
    if (
        summary["provider_outcome_category"] != "success"
        or summary["provider_call_count"] != 1
        or summary["input_token_count"] <= 0
        or summary["output_token_count"] <= 0
    ):
        failure_reasons.add("benchmark_failed")
    if stale_reasons:
        status = "stale"
        reasons = stale_reasons
    elif failure_reasons:
        status = "rejected"
        reasons = failure_reasons | {"benchmark_failed"}
    elif assessment["decision"] == "rejected":
        status = "rejected"
        reasons = {"review_rejected"}
    elif current_task_contract_sha256 is None:
        status = "pending"
        reasons = {"task_contract_missing"}
        if review_required and assessment["decision"] == "pending":
            reasons.add("review_missing")
    elif tested_task is None:
        status = "pending"
        reasons = {"task_contract_binding_missing"}
        if review_required and assessment["decision"] == "pending":
            reasons.add("review_missing")
    elif tested_task != current_task_contract_sha256:
        status = "stale"
        reasons = {"task_contract_binding_stale"}
    elif review_required and assessment["decision"] == "pending":
        status = "pending"
        reasons = {"review_missing"}
    else:
        _require(
            assessment["review_requirement_satisfied"] is True,
            "human-review requirement is not satisfied",
        )
        status = "qualified"
        reasons = {"qualification_requirements_satisfied"}
    return _build_cell(
        scheduled=scheduled,
        status=status,
        reasons=reasons,
        review_required=review_required,
        current_bindings=current_bindings,
        current_task_contract_sha256=current_task_contract_sha256,
        tested_model_catalog_snapshot_sha256=evidence[
            "model_catalog_snapshot_sha256"
        ],
        tested_benchmark_contract_sha256=plan["step8l_contract_sha256"],
        tested_controlled_plan_sha256=evidence["plan_sha256"],
        tested_task_contract_sha256=tested_task,
        evidence_sha256=evidence_digest,
        review_sha256=review_digest,
        evaluated_at_utc=evidence["execution_at_utc"],
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
) -> Path:
    root = Path(repository_root).resolve()
    _require(root.is_dir() and not root.is_symlink(), "repository root is unsafe")
    candidate = Path(artifact_path)
    _require(candidate.is_absolute(), "registry path must be absolute")
    _require(".." not in candidate.parts, "registry path traversal is prohibited")
    expected = root / REGISTRY_ARTIFACT_PATH
    _require(candidate == expected, "registry path is outside the approved namespace")
    current = root
    for part in REGISTRY_ARTIFACT_PATH.parts[:-1]:
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
