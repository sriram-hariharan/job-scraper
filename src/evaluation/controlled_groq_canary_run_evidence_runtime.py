"""Offline run-002 evidence adapter over the committed v1 Groq runtime."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Dict, Mapping

from src.evaluation import controlled_groq_canary_evidence_runtime as v1
from src.evaluation.controlled_groq_canary_run_identity import (
    RUN_IDENTIFIER,
    RUN_IDENTITY_VERSION,
    RUN_002_ARTIFACT_PATHS,
    build_run_authorization_template,
    build_run_identity_contract,
    run_identity_sha256,
)
from src.evaluation.controlled_groq_provider_canary import (
    AUTHORIZATION_VERSION,
    build_controlled_groq_canary_contract,
    build_operator_authorization_template,
    pricing_table_sha256,
    validate_controlled_groq_canary_contract,
    validate_operator_approved_pricing,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    validate_controlled_provider_benchmark_plan,
)
from src.evaluation.provider_fixture_benchmark import (
    load_fixture_case_corpus,
    validate_fixture_case_corpus,
)


RUN_EVIDENCE_RUNTIME_VERSION = (
    "controlled-groq-canary-run-evidence-runtime-v1"
)
RUN_CHECKPOINT_SCHEMA_VERSION = "controlled-groq-canary-run-checkpoint-v1"
RUN_RESULT_SCHEMA_VERSION = "controlled-groq-canary-run-result-v1"

_STATE_FIELDS = (
    "completed_schedule_keys",
    "blocked_schedule_keys",
    "ambiguous_schedule_keys",
    "hard_failure_schedule_keys",
)
_CHECKPOINT_FIELDS = {
    "run_evidence_runtime_version",
    "checkpoint_schema_version",
    "run_identity_version",
    "run_identifier",
    "run_identity_sha256",
    "base_canary_version",
    "base_canary_sha256",
    "transport_version",
    "transport_sha256",
    "base_evidence_runtime_version",
    "authorization_sha256",
    "pricing_sha256",
    "run_schedule",
    "run_schedule_keys",
    *_STATE_FIELDS,
    "aggregate_usage",
    "grading_summaries",
    "stop_reason",
    "quality_gate_status",
    "cost_comparison_eligibility",
    "authority_invariants",
}
_RESULT_FIELDS = {
    "result_schema_version",
    "run_evidence_runtime_version",
    "run_identifier",
    "run_identity_sha256",
    "authorization_sha256",
    "pricing_sha256",
    "checkpoint",
    "final_status",
    "state_counts",
    "aggregate_usage",
    "grading_summaries",
    "quality_gate_status",
    "cost_comparison_eligibility",
    "winner_selected",
    "production_activation",
    "mutation_count",
    "application_action_count",
    "ats_action_count",
    "retention_policy",
}
_PROHIBITED_EVIDENCE_KEYS = {
    "api_key",
    "credential",
    "header",
    "normalized_output",
    "prompt",
    "raw_request",
    "raw_response",
    "reasoning",
    "request_id",
    "request_packet",
}
_RETENTION_POLICY = {
    "ignored_artifact_only": True,
    "required_file_mode": "0600",
    "maximum_retention_days": 7,
    "operator_review_required": True,
    "overwrite_allowed": False,
}
_CURRENT_SEMANTIC_OWNERSHIP = {
    "canary_run_002_f6a3df4b6caa7e82e229efc59bea7687": {
        "execution_order": 1,
        "workload_id": "skill_extraction",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "case_alias": "case_eff6ed2fb3643d23b87bab48",
        "base_schedule_key": "canary_9c6a5ef970de552a6f830054e635ecd4",
        "case_id": "skill_extraction_required_preferred_v1",
        "schema_id": "skill_extraction_result_v1",
    },
    "canary_run_002_19cfcee433993511035305348b7503f1": {
        "execution_order": 2,
        "workload_id": "grounded_rag_answer",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "case_alias": "case_8e43ca2af1d94798ae9d5167",
        "base_schedule_key": "canary_8443c4b254128440d76bab0163f78454",
        "case_id": "grounded_rag_synthetic_transmission_safe_v1",
        "schema_id": "grounded_rag_answer_result_v1",
    },
    "canary_run_002_d592a547c5344cdbdf3ba926b0806c69": {
        "execution_order": 3,
        "workload_id": "jd_intelligence",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "case_alias": "case_c4f73240ce6ff98809579b5d",
        "base_schedule_key": "canary_d57f61cec14a93f0e9658ae9e04f18bb",
        "case_id": "jd_intelligence_signals_v1",
        "schema_id": "jd_intelligence_result_v1",
    },
    "canary_run_002_03e1b156d6ef1d8401c99298bdf09942": {
        "execution_order": 4,
        "workload_id": "tailoring_generation",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "case_alias": "case_3dddc5f43be918e0932d3bb2",
        "base_schedule_key": "canary_38aa2602e052b5c5ae84772abee84708",
        "case_id": "tailoring_generation_evidence_bound_v1",
        "schema_id": "tailoring_generation_result_v1",
    },
}
_REVIEW_FALSE_FIELDS = {
    "contains_personal_data",
    "contains_runtime_derived_data",
    "contains_employer_or_company_identity",
    "contains_person_name",
    "contains_resume_derived_text",
    "contains_private_job_description_text",
    "contains_credentials_or_secrets",
    "contains_internal_paths",
    "contains_request_identifiers",
    "contains_database_information",
    "contains_proprietary_application_state",
    "contains_unsupported_free_form_text",
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


def _canonical_sha256(value: Any) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _iter_keys(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).strip().lower()
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _contains_prohibited_evidence(value: Any) -> bool:
    return any(key in _PROHIBITED_EVIDENCE_KEYS for key in _iter_keys(value))


def _parse_utc(value: Any, label: str) -> datetime:
    _require(isinstance(value, str) and value.endswith("Z"), f"{label} is invalid")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{label} is invalid") from exc
    _require(parsed.tzinfo is not None, f"{label} is invalid")
    return parsed.astimezone(timezone.utc)


def _positive_decimal(value: Any, label: str) -> Decimal:
    _require(not isinstance(value, bool), f"{label} must be positive")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be positive") from exc
    _require(number.is_finite() and number > 0, f"{label} must be positive")
    return number


@lru_cache(maxsize=1)
def _identity_contract_cached() -> Dict[str, Any]:
    return build_run_identity_contract()


@lru_cache(maxsize=1)
def _authorization_template_cached() -> Dict[str, Any]:
    return build_run_authorization_template()


@lru_cache(maxsize=1)
def _base_authorization_template_cached() -> Dict[str, Any]:
    return build_operator_authorization_template()


def validate_active_run_authorization(
    authorization: Dict[str, Any],
    *,
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> bool:
    template = _authorization_template_cached()
    _require(
        isinstance(authorization, dict)
        and set(authorization) == set(template),
        "active authorization fields must match the inactive template",
    )
    operator_fields = {
        "maximum_observed_cost_per_model",
        "maximum_total_observed_cost",
        "pricing_table_sha256",
        "valid_from_utc",
        "expires_at_utc",
        "operator_approved",
        "live_execution_authorized",
    }
    _require(
        all(
            authorization[field] == template[field]
            for field in set(template) - operator_fields
        ),
        "active authorization scope differs from run identity",
    )
    validate_operator_approved_pricing(
        pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(
        authorization["operator_approved"] is True
        and authorization["live_execution_authorized"] is True,
        "active authorization requires explicit operator and live approval",
    )
    valid_from = _parse_utc(authorization["valid_from_utc"], "valid_from_utc")
    expires_at = _parse_utc(authorization["expires_at_utc"], "expires_at_utc")
    execution_at = _parse_utc(execution_at_utc, "execution_at_utc")
    _require(valid_from < expires_at, "authorization validity is invalid")
    _require(
        valid_from <= execution_at <= expires_at,
        "authorization is expired or not yet valid",
    )
    per_model = authorization["maximum_observed_cost_per_model"]
    expected_models = {
        f"{row['provider']}/{row['model']}"
        for row in template["candidate_provider_models"]
    }
    _require(
        isinstance(per_model, dict) and set(per_model) == expected_models,
        "per-model cost ceilings are incomplete",
    )
    ceilings = [
        _positive_decimal(value, "per-model cost ceiling")
        for value in per_model.values()
    ]
    total = _positive_decimal(
        authorization["maximum_total_observed_cost"],
        "total cost ceiling",
    )
    _require(
        total <= sum(ceilings, Decimal("0")),
        "total cost ceiling exceeds per-model ceilings",
    )
    _require(
        authorization["pricing_table_sha256"] == pricing_table_sha256(pricing),
        "authorization pricing digest mismatch",
    )
    return True


def _base_authorization(
    authorization: Dict[str, Any],
    *,
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    validate_active_run_authorization(
        authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    base = deepcopy(_base_authorization_template_cached())
    base.update(
        {
            "authorization_version": AUTHORIZATION_VERSION,
            "maximum_observed_cost_per_model": deepcopy(
                authorization["maximum_observed_cost_per_model"]
            ),
            "maximum_total_observed_cost": authorization[
                "maximum_total_observed_cost"
            ],
            "valid_from_utc": authorization["valid_from_utc"],
            "expires_at_utc": authorization["expires_at_utc"],
            "pricing_table_sha256": authorization["pricing_table_sha256"],
            "operator_approved": True,
        }
    )
    return base


@lru_cache(maxsize=1)
def _identity_maps():
    identity = _identity_contract_cached()
    corpus = load_fixture_case_corpus()
    validate_fixture_case_corpus(corpus)
    controlled_plan = build_controlled_provider_benchmark_plan(corpus=corpus)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    base = build_controlled_groq_canary_contract(controlled_plan)
    validate_controlled_groq_canary_contract(base)
    run_rows = identity["schedule"]
    base_rows = base["schedule"]
    _require(len(run_rows) == len(base_rows) == 4, "schedule count changed")
    run_to_base: Dict[str, str] = {}
    base_to_run: Dict[str, str] = {}
    run_by_key: Dict[str, Dict[str, Any]] = {}
    base_by_key: Dict[str, Dict[str, Any]] = {}
    reviews = controlled_plan["transmission_review"]
    cases = corpus["cases"]
    _require(len(reviews) == len(cases), "current review/corpus count changed")
    for run_row in run_rows:
        target = _CURRENT_SEMANTIC_OWNERSHIP.get(run_row["run_schedule_key"])
        _require(target is not None, "historical run schedule ownership changed")
        matches = [
            (review, case)
            for review, case in zip(reviews, cases)
            if review["case_alias"] == target["case_alias"]
            and case["case_id"] == target["case_id"]
        ]
        _require(len(matches) == 1, "current semantic case ownership changed")
        review, case = matches[0]
        base_matches = [
            row
            for row in base_rows
            if row["schedule_key"] == target["base_schedule_key"]
            and row["case_alias"] == target["case_alias"]
        ]
        _require(len(base_matches) == 1, "current semantic base row changed")
        base_row = base_matches[0]
        _require(
            all(
                run_row[field] == target[field] == base_row[field]
                for field in (
                    "execution_order",
                    "workload_id",
                    "provider",
                    "model",
                )
            )
            and all(
                run_row[field] == base_row[field] == expected
                for field, expected in (
                    ("timeout_seconds", 30),
                    ("fallback", False),
                    ("harness_retry_limit", 0),
                    ("provider_sdk_retry_limit", 0),
                )
            ),
            "run/current semantic schedule projection changed",
        )
        _require(
            case["workload_id"] == target["workload_id"]
            and case["schema_id"] == target["schema_id"]
            and case["sanitized_classification"] == "synthetic_sanitized"
            and case["contains_personal_resume_content"] is False
            and case["additional_redaction_required"] is False,
            "current semantic fixture safety changed",
        )
        _require(
            review["workload_id"] == target["workload_id"]
            and review["eligible_for_later_controlled_transmission"] is True
            and review["wholly_synthetic"] is True
            and review["requires_additional_redaction"] is False
            and review["human_approval_required"] is True
            and review["eligibility_reasons"] == []
            and all(review[field] is False for field in _REVIEW_FALSE_FIELDS),
            "current semantic transmission safety changed",
        )
        run_key = run_row["run_schedule_key"]
        base_key = base_row["schedule_key"]
        run_to_base[run_key] = base_key
        base_to_run[base_key] = run_key
        run_by_key[run_key] = deepcopy(run_row)
        base_by_key[base_key] = deepcopy(base_row)
    _require(
        len(run_to_base) == len(base_to_run) == 4
        and set(run_to_base).isdisjoint(base_to_run),
        "run/base schedule keys are unsafe",
    )
    return identity, base, run_to_base, base_to_run, run_by_key, base_by_key


def _bindings(
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    identity = _identity_contract_cached()
    return {
        "run_evidence_runtime_version": RUN_EVIDENCE_RUNTIME_VERSION,
        "checkpoint_schema_version": RUN_CHECKPOINT_SCHEMA_VERSION,
        "run_identity_version": RUN_IDENTITY_VERSION,
        "run_identifier": RUN_IDENTIFIER,
        "run_identity_sha256": run_identity_sha256(identity),
        "base_canary_version": identity["base_canary_version"],
        "base_canary_sha256": identity["base_canary_sha256"],
        "transport_version": identity["transport_version"],
        "transport_sha256": identity["transport_sha256"],
        "base_evidence_runtime_version": identity[
            "evidence_runtime_version"
        ],
        "authorization_sha256": _canonical_sha256(authorization),
        "pricing_sha256": pricing_table_sha256(pricing),
        "run_schedule": deepcopy(identity["schedule"]),
        "run_schedule_keys": [
            row["run_schedule_key"] for row in identity["schedule"]
        ],
    }


def _map_aggregate_keys(
    aggregate: Mapping[str, Any],
    mapping: Mapping[str, str],
) -> Dict[str, Any]:
    updated = deepcopy(dict(aggregate))
    updated["by_schedule_key"] = {
        mapping[key]: value
        for key, value in aggregate["by_schedule_key"].items()
    }
    return updated


def _to_base_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    (
        _identity,
        base_canary,
        run_to_base,
        _base_to_run,
        _run_by_key,
        _base_by_key,
    ) = _identity_maps()
    base_authorization = _base_authorization(
        authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    base_checkpoint = v1.build_empty_checkpoint(
        authorization=base_authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=base_canary,
    )
    for field in _STATE_FIELDS:
        base_checkpoint[field] = [
            run_to_base[key] for key in checkpoint[field]
        ]
    base_checkpoint["aggregate_usage"] = _map_aggregate_keys(
        checkpoint["aggregate_usage"], run_to_base
    )
    base_checkpoint["grading_summaries"] = deepcopy(
        checkpoint["grading_summaries"]
    )
    for summary in base_checkpoint["grading_summaries"]:
        summary["schedule_key"] = run_to_base[summary["schedule_key"]]
    for field in (
        "stop_reason",
        "quality_gate_status",
        "cost_comparison_eligibility",
        "authority_invariants",
    ):
        base_checkpoint[field] = deepcopy(checkpoint[field])
    v1.validate_checkpoint(
        base_checkpoint,
        authorization=base_authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=base_canary,
    )
    return base_checkpoint, base_authorization, base_canary


def _from_base_checkpoint(
    base_checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    (
        identity,
        _base_canary,
        _run_to_base,
        base_to_run,
        _run_by_key,
        _base_by_key,
    ) = _identity_maps()
    checkpoint = {
        **_bindings(authorization, pricing),
        **{
            field: [base_to_run[key] for key in base_checkpoint[field]]
            for field in _STATE_FIELDS
        },
        "aggregate_usage": _map_aggregate_keys(
            base_checkpoint["aggregate_usage"], base_to_run
        ),
        "grading_summaries": deepcopy(base_checkpoint["grading_summaries"]),
        "stop_reason": base_checkpoint["stop_reason"],
        "quality_gate_status": base_checkpoint["quality_gate_status"],
        "cost_comparison_eligibility": base_checkpoint[
            "cost_comparison_eligibility"
        ],
        "authority_invariants": deepcopy(
            base_checkpoint["authority_invariants"]
        ),
    }
    for summary in checkpoint["grading_summaries"]:
        summary["schedule_key"] = base_to_run[summary["schedule_key"]]
    _require(
        checkpoint["run_schedule"] == identity["schedule"],
        "run schedule binding changed",
    )
    return checkpoint


def build_empty_run_checkpoint(
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    base_authorization = _base_authorization(
        authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    base = v1.build_empty_checkpoint(
        authorization=base_authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    checkpoint = _from_base_checkpoint(
        base, authorization=authorization, pricing=pricing
    )
    validate_run_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(checkpoint)


def validate_run_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> bool:
    _require(
        isinstance(checkpoint, dict)
        and set(checkpoint) == _CHECKPOINT_FIELDS,
        "run checkpoint fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_evidence(checkpoint),
        "run checkpoint contains prohibited evidence",
    )
    bindings = _bindings(authorization, pricing)
    _require(
        all(checkpoint[field] == value for field, value in bindings.items()),
        "run checkpoint ownership changed",
    )
    run_keys = set(bindings["run_schedule_keys"])
    for field in _STATE_FIELDS:
        values = checkpoint[field]
        _require(
            isinstance(values, list)
            and len(values) == len(set(values))
            and set(values).issubset(run_keys),
            f"{field} is invalid",
        )
    _to_base_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return True


def get_next_run_row(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    validate_run_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    identity = _identity_contract_cached()
    invoked = set().union(*(set(checkpoint[field]) for field in _STATE_FIELDS))
    _require(
        not checkpoint["blocked_schedule_keys"]
        and not checkpoint["ambiguous_schedule_keys"]
        and not checkpoint["hard_failure_schedule_keys"]
        and checkpoint["stop_reason"] is None,
        "terminal run checkpoint cannot resume",
    )
    _require(len(invoked) < 4, "run schedule is complete")
    return deepcopy(identity["schedule"][len(invoked)])


def _project_scheduled(
    checkpoint: Dict[str, Any],
    scheduled: Mapping[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    expected = get_next_run_row(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(dict(scheduled) == expected, "run schedule row is not the exact next row")
    (
        _identity,
        _base,
        run_to_base,
        _base_to_run,
        _run_by_key,
        base_by_key,
    ) = _identity_maps()
    base_checkpoint, base_authorization, base_canary = _to_base_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    base_row = base_by_key[run_to_base[expected["run_schedule_key"]]]
    return base_checkpoint, base_authorization, base_canary, base_row


def _transition(
    operation,
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    **kwargs,
) -> Dict[str, Any]:
    base_checkpoint, base_authorization, base_canary, base_row = (
        _project_scheduled(
            checkpoint,
            scheduled,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
        )
    )
    updated_base = operation(
        base_checkpoint,
        scheduled=base_row,
        authorization=base_authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=base_canary,
        **kwargs,
    )
    updated = _from_base_checkpoint(
        updated_base,
        authorization=authorization,
        pricing=pricing,
    )
    validate_run_checkpoint(
        updated,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(updated)


def record_completed_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    transport_result: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    return _transition(
        v1.record_completed_call,
        checkpoint,
        scheduled=scheduled,
        transport_result=transport_result,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )


def record_blocked_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    reason: str = "definitive_transport_failure",
) -> Dict[str, Any]:
    return _transition(
        v1.record_blocked_call,
        checkpoint,
        scheduled=scheduled,
        reason=reason,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )


def record_ambiguous_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    return _transition(
        v1.record_ambiguous_call,
        checkpoint,
        scheduled=scheduled,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )


def record_hard_failure_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    reason: str = "hard_safety_failure",
) -> Dict[str, Any]:
    return _transition(
        v1.record_hard_failure_call,
        checkpoint,
        scheduled=scheduled,
        reason=reason,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )


def serialize_run_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> str:
    payload = deepcopy(checkpoint)
    validate_run_checkpoint(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return _canonical_json(payload)


def run_checkpoint_sha256(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> str:
    return sha256(
        serialize_run_checkpoint(
            checkpoint,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
        ).encode("utf-8")
    ).hexdigest()


def _validate_artifact_path(
    artifact_path: str | Path,
    *,
    repository_root: str | Path,
    kind: str,
    require_existing: bool,
) -> Path:
    root = Path(repository_root).resolve()
    candidate = Path(artifact_path)
    _require(candidate.is_absolute(), "artifact path must be absolute")
    _require(".." not in candidate.parts, "artifact path traversal is prohibited")
    expected_relative = RUN_002_ARTIFACT_PATHS[kind]
    expected = root / expected_relative
    _require(candidate == expected, f"only the exact run-002 {kind} path is allowed")
    approved = expected.parent
    _require(
        approved.is_dir() and not approved.is_symlink(),
        "artifact parent is unsafe",
    )
    current = root
    for part in expected.relative_to(root).parts[:-1]:
        current = current / part
        _require(not current.is_symlink(), "artifact path contains a symlink")
    mode = stat.S_IMODE(approved.stat().st_mode)
    _require(
        mode & stat.S_IWUSR and not mode & (stat.S_IWGRP | stat.S_IWOTH),
        "artifact parent permissions are unsafe",
    )
    ignore_lines = {
        line.strip()
        for line in (root / ".gitignore").read_text(encoding="utf-8").splitlines()
    }
    _require(
        "outputs/" in ignore_lines or "/outputs/" in ignore_lines,
        "artifact directory is not ignored",
    )
    if require_existing:
        _require(
            candidate.is_file() and not candidate.is_symlink(),
            "artifact is missing or unsafe",
        )
    else:
        _require(
            not candidate.exists() and not candidate.is_symlink(),
            "artifact overwrite is prohibited",
        )
    return candidate


def _write_exclusive(path: Path, encoded: bytes) -> None:
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
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


def load_run_checkpoint(
    checkpoint_path: str | Path,
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    path = _validate_artifact_path(
        checkpoint_path,
        repository_root=repository_root,
        kind="checkpoint",
        require_existing=True,
    )
    _require(stat.S_IMODE(path.stat().st_mode) == 0o600, "mode must be 0600")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("persisted checkpoint is malformed") from None
    validate_run_checkpoint(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(payload)


def write_initial_run_checkpoint(
    checkpoint_path: str | Path,
    checkpoint: Dict[str, Any],
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Path:
    path = _validate_artifact_path(
        checkpoint_path,
        repository_root=repository_root,
        kind="checkpoint",
        require_existing=False,
    )
    encoded = serialize_run_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    ).encode("utf-8")
    _write_exclusive(path, encoded)
    load_run_checkpoint(
        path,
        repository_root=repository_root,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return path


def replace_run_checkpoint_atomic(
    checkpoint_path: str | Path,
    checkpoint: Dict[str, Any],
    *,
    expected_prior_sha256: str,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Path:
    path = _validate_artifact_path(
        checkpoint_path,
        repository_root=repository_root,
        kind="checkpoint",
        require_existing=True,
    )
    kwargs = {
        "repository_root": repository_root,
        "authorization": authorization,
        "pricing": pricing,
        "execution_at_utc": execution_at_utc,
    }
    prior = load_run_checkpoint(path, **kwargs)
    observed = run_checkpoint_sha256(
        prior,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(observed == expected_prior_sha256, "prior digest mismatch")
    encoded = serialize_run_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    ).encode("utf-8")
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.close(descriptor)
        descriptor = -1
        current = load_run_checkpoint(path, **kwargs)
        _require(
            run_checkpoint_sha256(
                current,
                authorization=authorization,
                pricing=pricing,
                execution_at_utc=execution_at_utc,
            )
            == expected_prior_sha256,
            "checkpoint changed before replacement",
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
    _require(load_run_checkpoint(path, **kwargs) == checkpoint, "replacement failed")
    return path


def build_run_result_artifact(
    *,
    checkpoint: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    validate_run_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    counts = {
        field.removesuffix("_schedule_keys"): len(checkpoint[field])
        for field in _STATE_FIELDS
    }
    _require(
        sum(counts.values()) == 4 or checkpoint["stop_reason"] is not None,
        "result requires a terminal checkpoint",
    )
    if counts["completed"] == 4:
        final_status = "completed"
    elif counts["ambiguous"]:
        final_status = "stopped_ambiguous"
    elif counts["hard_failure"]:
        final_status = "stopped_hard_failure"
    else:
        final_status = "stopped_blocked"
    artifact = {
        "result_schema_version": RUN_RESULT_SCHEMA_VERSION,
        "run_evidence_runtime_version": RUN_EVIDENCE_RUNTIME_VERSION,
        "run_identifier": RUN_IDENTIFIER,
        "run_identity_sha256": checkpoint["run_identity_sha256"],
        "authorization_sha256": checkpoint["authorization_sha256"],
        "pricing_sha256": checkpoint["pricing_sha256"],
        "checkpoint": deepcopy(checkpoint),
        "final_status": final_status,
        "state_counts": counts,
        "aggregate_usage": deepcopy(checkpoint["aggregate_usage"]),
        "grading_summaries": deepcopy(checkpoint["grading_summaries"]),
        "quality_gate_status": checkpoint["quality_gate_status"],
        "cost_comparison_eligibility": checkpoint[
            "cost_comparison_eligibility"
        ],
        "winner_selected": False,
        "production_activation": False,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "retention_policy": deepcopy(_RETENTION_POLICY),
    }
    validate_run_result_artifact(
        artifact,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(artifact)


def validate_run_result_artifact(
    artifact: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> bool:
    _require(
        isinstance(artifact, dict) and set(artifact) == _RESULT_FIELDS,
        "run result fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_evidence(artifact),
        "run result contains prohibited evidence",
    )
    checkpoint = artifact["checkpoint"]
    validate_run_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    counts = {
        field.removesuffix("_schedule_keys"): len(checkpoint[field])
        for field in _STATE_FIELDS
    }
    status = (
        "completed"
        if counts["completed"] == 4
        else "stopped_ambiguous"
        if counts["ambiguous"]
        else "stopped_hard_failure"
        if counts["hard_failure"]
        else "stopped_blocked"
    )
    _require(
        artifact["result_schema_version"] == RUN_RESULT_SCHEMA_VERSION
        and artifact["run_evidence_runtime_version"]
        == RUN_EVIDENCE_RUNTIME_VERSION
        and artifact["run_identifier"] == RUN_IDENTIFIER
        and artifact["run_identity_sha256"] == checkpoint["run_identity_sha256"]
        and artifact["authorization_sha256"] == checkpoint["authorization_sha256"]
        and artifact["pricing_sha256"] == checkpoint["pricing_sha256"]
        and artifact["state_counts"] == counts
        and artifact["final_status"] == status
        and artifact["aggregate_usage"] == checkpoint["aggregate_usage"]
        and artifact["grading_summaries"] == checkpoint["grading_summaries"]
        and artifact["quality_gate_status"] == checkpoint["quality_gate_status"]
        and artifact["cost_comparison_eligibility"]
        is checkpoint["cost_comparison_eligibility"]
        and artifact["retention_policy"] == _RETENTION_POLICY,
        "run result and checkpoint disagree",
    )
    _require(
        artifact["winner_selected"] is False
        and artifact["production_activation"] is False
        and artifact["mutation_count"] == 0
        and artifact["application_action_count"] == 0
        and artifact["ats_action_count"] == 0,
        "run result authority changed",
    )
    return True


def serialize_run_result_artifact(
    artifact: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> str:
    payload = deepcopy(artifact)
    validate_run_result_artifact(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return _canonical_json(payload)


def run_result_sha256(
    artifact: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> str:
    return sha256(
        serialize_run_result_artifact(
            artifact,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
        ).encode("utf-8")
    ).hexdigest()


def load_run_result_artifact(
    result_path: str | Path,
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    path = _validate_artifact_path(
        result_path,
        repository_root=repository_root,
        kind="result",
        require_existing=True,
    )
    _require(stat.S_IMODE(path.stat().st_mode) == 0o600, "mode must be 0600")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("persisted result is malformed") from None
    validate_run_result_artifact(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(payload)


def write_run_result_exclusive(
    result_path: str | Path,
    artifact: Dict[str, Any],
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Path:
    path = _validate_artifact_path(
        result_path,
        repository_root=repository_root,
        kind="result",
        require_existing=False,
    )
    encoded = serialize_run_result_artifact(
        artifact,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    ).encode("utf-8")
    _write_exclusive(path, encoded)
    load_run_result_artifact(
        path,
        repository_root=repository_root,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return path


calculate_observed_cost = v1.calculate_observed_cost
