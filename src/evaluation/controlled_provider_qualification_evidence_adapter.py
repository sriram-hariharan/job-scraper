"""Version-aware, bounded qualification evidence observations.

This evaluation-only owner validates an existing provider-neutral or
controlled-live evidence object through its native owner and projects one
schedule result into the minimum shared semantics consumed by qualification
and human review.  It never calls providers, reads credentials, persists
artifacts, mutates qualification state, or grants routing authority.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import re
from typing import Any, Dict, Mapping

from src.evaluation.controlled_provider_benchmark_evidence_runtime import (
    EVIDENCE_SCHEMA_VERSION,
    normalize_execution_timestamp,
    provider_neutral_run_evidence_sha256,
    validate_provider_neutral_run_evidence,
)
from src.evaluation.controlled_provider_benchmark_harness import (
    build_execution_schedule,
)
from src.evaluation.provider_benchmark_contract import (
    build_provider_benchmark_contract,
    validate_provider_benchmark_contract,
)


QUALIFICATION_OBSERVATION_VERSION = "qualification-evidence-observation-v1"
PROVIDER_NEUTRAL_EVIDENCE_KIND = "provider_neutral_controlled_evidence"
CONTROLLED_LIVE_EVIDENCE_KIND = "controlled_live_qualification_evidence"
SUPPORTED_EVIDENCE_KINDS = (
    PROVIDER_NEUTRAL_EVIDENCE_KIND,
    CONTROLLED_LIVE_EVIDENCE_KIND,
)

_OBSERVATION_FIELDS = {
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
}
_PROHIBITED_OBSERVATION_KEY_PARTS = {
    "api_key",
    "authorization_body",
    "checkpoint",
    "credential",
    "headers",
    "messages",
    "normalized_output",
    "pricing_body",
    "prompt",
    "raw_request",
    "raw_response",
    "reasoning",
    "request_id",
    "sdk_object",
    "synthetic_input",
}
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


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


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None


def _review_requirements() -> Dict[str, bool]:
    contract = build_provider_benchmark_contract()
    validate_provider_benchmark_contract(contract)
    return {
        row["workload_id"]: row["human_review_required"]
        for row in contract["workloads"]
    }


def qualification_evidence_kind(evidence: Mapping[str, Any]) -> str:
    """Return the explicitly versioned evidence kind, or fail closed."""

    _require(isinstance(evidence, Mapping), "qualification evidence must be an object")
    legacy_version = evidence.get("evidence_schema_version")
    live_version = evidence.get("evidence_version")
    if legacy_version == EVIDENCE_SCHEMA_VERSION and live_version is None:
        return PROVIDER_NEUTRAL_EVIDENCE_KIND

    # Lazy import avoids a human-review/live-owner import cycle.  The live
    # owner remains the sole validator and digest owner for this evidence kind.
    from src.evaluation.controlled_live_provider_qualification import (
        LIVE_EVIDENCE_VERSION,
    )

    if live_version == LIVE_EVIDENCE_VERSION and legacy_version is None:
        return CONTROLLED_LIVE_EVIDENCE_KIND
    raise ValueError("unsupported qualification evidence schema version")


def _exact_summary(
    evidence: Mapping[str, Any],
    *,
    schedule_key: str,
) -> Dict[str, Any]:
    _require(
        isinstance(schedule_key, str) and bool(schedule_key.strip()),
        "qualification schedule key is required",
    )
    normalized_key = schedule_key.strip()
    matches = [
        row
        for row in evidence["grading_summaries"]
        if row["schedule_key"] == normalized_key
    ]
    _require(
        len(matches) == 1,
        "qualification evidence is missing the exact schedule result",
    )
    return deepcopy(matches[0])


def _require_schedule_identity(
    summary: Mapping[str, Any],
    scheduled: Mapping[str, Any],
) -> None:
    _require(
        all(
            summary[field] == scheduled[field]
            for field in (
                "schedule_key",
                "case_alias",
                "workload_id",
                "provider",
                "model",
            )
        ),
        "qualification evidence schedule identity mismatch",
    )


def _live_pregrading_failure_observation(
    *,
    evidence: Dict[str, Any],
    schedule_key: str,
    scheduled: Mapping[str, Any],
    digest: str,
    live: Any,
) -> Dict[str, Any]:
    _require(
        schedule_key in evidence["attempted_schedule_keys"]
        and schedule_key not in evidence["completed_schedule_keys"],
        "live pre-grading failure schedule state is invalid",
    )
    stop_reason = evidence["stop_reason"]
    _require(
        stop_reason in live._BOUNDED_TRANSPORT_FAILURE_STOP_REASONS,
        "live pre-grading outcome is not a definitive bounded failure",
    )
    _require(
        schedule_key in evidence["blocked_schedule_keys"]
        and schedule_key not in evidence["ambiguous_schedule_keys"],
        "live pre-grading failure schedule state is invalid",
    )
    authority = evidence["authority_invariants"]
    authority_safety_valid = (
        authority["fallback_activation_count"] == 0
        and authority["retry_count"] == 0
        and authority["application_mutation_count"] == 0
        and authority["ats_mutation_count"] == 0
        and authority["raw_response_persisted_count"] == 0
        and authority["qualification_promotion_count"] == 0
        and authority["routing_change_count"] == 0
    )
    return {
        "observation_version": QUALIFICATION_OBSERVATION_VERSION,
        "evidence_kind": CONTROLLED_LIVE_EVIDENCE_KIND,
        "evidence_schema_version": live.LIVE_EVIDENCE_VERSION,
        "evidence_sha256": digest,
        "schedule_key": scheduled["schedule_key"],
        "case_alias": scheduled["case_alias"],
        "workload_id": scheduled["workload_id"],
        "provider": scheduled["provider"],
        "model": scheduled["model"],
        "execution_at_utc": normalize_execution_timestamp(
            evidence["execution_at_utc"]
        ),
        "tested_model_catalog_snapshot_sha256": evidence[
            "model_catalog_snapshot_sha256"
        ],
        "tested_benchmark_contract_sha256": evidence[
            "benchmark_contract_sha256"
        ],
        "tested_controlled_plan_sha256": evidence["controlled_plan_sha256"],
        "tested_task_contract_sha256": scheduled[
            "production_task_contract_sha256"
        ],
        "schedule_completed": False,
        "provider_outcome_category": stop_reason,
        "provider_call_count": 1,
        "contract_valid": False,
        "normalization_succeeded": None,
        "quality_gate_passed": False,
        "hard_failure_present": False,
        "input_token_count": 0,
        "output_token_count": 0,
        "human_review_required": _review_requirements()[
            scheduled["workload_id"]
        ],
        "authority_safety_valid": authority_safety_valid,
    }


def _legacy_observation(
    *,
    evidence: Dict[str, Any],
    schedule_key: str,
    plan: Dict[str, Any],
    authorization: Dict[str, Any] | None,
    pricing: Dict[str, Any] | None,
    tested_task_contract_sha256: str | None,
) -> Dict[str, Any]:
    validate_provider_neutral_run_evidence(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    digest = provider_neutral_run_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    summary = _exact_summary(evidence, schedule_key=schedule_key)
    schedule = build_execution_schedule(plan=plan, authorization=authorization)
    scheduled_rows = [
        row for row in schedule if row["schedule_key"] == summary["schedule_key"]
    ]
    _require(len(scheduled_rows) == 1, "unknown controlled schedule key")
    _require_schedule_identity(summary, scheduled_rows[0])
    if tested_task_contract_sha256 is not None:
        _require(
            _is_sha256(tested_task_contract_sha256),
            "tested task-contract fingerprint must be a lowercase SHA-256 digest",
        )
    authority = evidence["checkpoint"]["authority_invariants"]
    authority_safety_valid = (
        authority["fallback_activation_count"] == 0
        and authority["retry_count"] == 0
        and authority["mutation_count"] == 0
        and authority["application_action_count"] == 0
        and authority["ats_action_count"] == 0
        and authority["raw_response_persisted_count"] == 0
        and authority["production_activation"] is False
        and authority["winner_selected"] is False
        and evidence["authority_invariants"]["routing_change_allowed"] is False
        and evidence["authority_invariants"]["registry_write_allowed"] is False
    )
    return {
        "observation_version": QUALIFICATION_OBSERVATION_VERSION,
        "evidence_kind": PROVIDER_NEUTRAL_EVIDENCE_KIND,
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "evidence_sha256": digest,
        "schedule_key": summary["schedule_key"],
        "case_alias": summary["case_alias"],
        "workload_id": summary["workload_id"],
        "provider": summary["provider"],
        "model": summary["model"],
        "execution_at_utc": normalize_execution_timestamp(
            evidence["execution_at_utc"]
        ),
        "tested_model_catalog_snapshot_sha256": evidence[
            "model_catalog_snapshot_sha256"
        ],
        "tested_benchmark_contract_sha256": plan["step8l_contract_sha256"],
        "tested_controlled_plan_sha256": evidence["plan_sha256"],
        "tested_task_contract_sha256": tested_task_contract_sha256,
        "schedule_completed": summary["schedule_key"]
        in evidence["checkpoint"]["completed_schedule_keys"],
        "provider_outcome_category": summary["provider_outcome_category"],
        "provider_call_count": summary["provider_call_count"],
        "contract_valid": summary["schema_valid"],
        "normalization_succeeded": summary["normalization_succeeded"],
        "quality_gate_passed": summary["quality_gate_passed"],
        "hard_failure_present": evidence["hard_failure_present"]
        or any(summary["hard_failures"].values()),
        "input_token_count": summary["input_token_count"],
        "output_token_count": summary["output_token_count"],
        "human_review_required": _review_requirements()[summary["workload_id"]],
        "authority_safety_valid": authority_safety_valid,
    }


def _live_observation(
    *,
    evidence: Dict[str, Any],
    schedule_key: str,
    plan: Dict[str, Any],
    authorization: Dict[str, Any] | None,
    pricing: Dict[str, Any] | None,
    tested_task_contract_sha256: str | None,
) -> Dict[str, Any]:
    _require(authorization is not None, "exact live authorization context is required")
    _require(pricing is not None, "exact live pricing context is required")
    _require(
        tested_task_contract_sha256 is None,
        "live tested task fingerprint must come from validated live evidence",
    )
    from src.evaluation import controlled_live_provider_qualification as live

    live.validate_live_qualification_evidence(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    digest = live.live_qualification_evidence_sha256(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    eligible = {
        row["schedule_key"]: row
        for row in live.build_live_qualification_universe(plan)
        if row["live_qualification_eligible"]
    }
    _require(
        isinstance(schedule_key, str) and bool(schedule_key.strip()),
        "qualification schedule key is required",
    )
    normalized_key = schedule_key.strip()
    _require(
        normalized_key in eligible,
        "schedule key is not live production-qualifiable",
    )
    scheduled = eligible[normalized_key]
    matches = [
        row
        for row in evidence["grading_summaries"]
        if row["schedule_key"] == normalized_key
    ]
    if not matches:
        return _live_pregrading_failure_observation(
            evidence=evidence,
            schedule_key=normalized_key,
            scheduled=scheduled,
            digest=digest,
            live=live,
        )
    summary = _exact_summary(evidence, schedule_key=normalized_key)
    _require_schedule_identity(summary, scheduled)
    _require(
        summary["schedule_key"] in evidence["attempted_schedule_keys"],
        "live grading summary lacks one attempted provider call",
    )
    authority = evidence["authority_invariants"]
    authority_safety_valid = (
        authority["fallback_activation_count"] == 0
        and authority["retry_count"] == 0
        and authority["application_mutation_count"] == 0
        and authority["ats_mutation_count"] == 0
        and authority["raw_response_persisted_count"] == 0
        and authority["qualification_promotion_count"] == 0
        and authority["routing_change_count"] == 0
    )
    return {
        "observation_version": QUALIFICATION_OBSERVATION_VERSION,
        "evidence_kind": CONTROLLED_LIVE_EVIDENCE_KIND,
        "evidence_schema_version": live.LIVE_EVIDENCE_VERSION,
        "evidence_sha256": digest,
        "schedule_key": summary["schedule_key"],
        "case_alias": summary["case_alias"],
        "workload_id": summary["workload_id"],
        "provider": summary["provider"],
        "model": summary["model"],
        "execution_at_utc": normalize_execution_timestamp(
            evidence["execution_at_utc"]
        ),
        "tested_model_catalog_snapshot_sha256": evidence[
            "model_catalog_snapshot_sha256"
        ],
        "tested_benchmark_contract_sha256": evidence[
            "benchmark_contract_sha256"
        ],
        "tested_controlled_plan_sha256": evidence["controlled_plan_sha256"],
        "tested_task_contract_sha256": summary[
            "production_task_contract_sha256"
        ],
        "schedule_completed": summary["schedule_key"]
        in evidence["completed_schedule_keys"],
        "provider_outcome_category": summary["provider_outcome_category"],
        # The native live validator proves attempted keys are unique and every
        # retained summary belongs to an attempted key.  The serial gate makes
        # exactly one provider invocation for each such key.
        "provider_call_count": 1,
        "contract_valid": summary["production_contract_valid"],
        # Live evidence retains the combined production-contract result but no
        # separate legacy normalization flag.  Preserve that absence.
        "normalization_succeeded": None,
        "quality_gate_passed": summary["benchmark_quality_passed"],
        "hard_failure_present": summary["hard_failure_present"],
        "input_token_count": summary["input_token_count"],
        "output_token_count": summary["output_token_count"],
        "human_review_required": summary["human_review_required"],
        "authority_safety_valid": authority_safety_valid,
    }


def build_qualification_observation(
    *,
    evidence: Dict[str, Any],
    schedule_key: str,
    plan: Dict[str, Any],
    authorization: Dict[str, Any] | None,
    pricing: Dict[str, Any] | None,
    tested_task_contract_sha256: str | None = None,
) -> Dict[str, Any]:
    """Validate native evidence and return one bounded schedule observation."""

    payload = deepcopy(evidence)
    kind = qualification_evidence_kind(payload)
    kwargs = {
        "evidence": payload,
        "schedule_key": schedule_key,
        "plan": deepcopy(plan),
        "authorization": deepcopy(authorization),
        "pricing": deepcopy(pricing),
        "tested_task_contract_sha256": tested_task_contract_sha256,
    }
    if kind == PROVIDER_NEUTRAL_EVIDENCE_KIND:
        observation = _legacy_observation(**kwargs)
    elif kind == CONTROLLED_LIVE_EVIDENCE_KIND:
        observation = _live_observation(**kwargs)
    else:  # pragma: no cover - qualification_evidence_kind fails closed first.
        raise ValueError("unsupported qualification evidence kind")
    validate_qualification_observation(observation)
    return deepcopy(observation)


def validate_qualification_observation(observation: Dict[str, Any]) -> bool:
    _require(
        isinstance(observation, dict) and set(observation) == _OBSERVATION_FIELDS,
        "qualification observation fields must match the exact schema",
    )
    _require(
        not any(
            prohibited in key
            for key in _iter_keys(observation)
            for prohibited in _PROHIBITED_OBSERVATION_KEY_PARTS
        ),
        "qualification observation contains prohibited material",
    )
    _require(
        observation["observation_version"] == QUALIFICATION_OBSERVATION_VERSION
        and observation["evidence_kind"] in SUPPORTED_EVIDENCE_KINDS,
        "qualification observation version or evidence kind is invalid",
    )
    for field in (
        "evidence_sha256",
        "tested_model_catalog_snapshot_sha256",
        "tested_benchmark_contract_sha256",
        "tested_controlled_plan_sha256",
    ):
        _require(_is_sha256(observation[field]), f"{field} is invalid")
    task_fingerprint = observation["tested_task_contract_sha256"]
    _require(
        task_fingerprint is None or _is_sha256(task_fingerprint),
        "tested task-contract fingerprint is invalid",
    )
    for field in (
        "evidence_schema_version",
        "schedule_key",
        "case_alias",
        "workload_id",
        "provider",
        "model",
        "execution_at_utc",
        "provider_outcome_category",
    ):
        _require(
            isinstance(observation[field], str) and bool(observation[field].strip()),
            f"qualification observation {field} is invalid",
        )
    for field in (
        "schedule_completed",
        "contract_valid",
        "quality_gate_passed",
        "hard_failure_present",
        "human_review_required",
        "authority_safety_valid",
    ):
        _require(type(observation[field]) is bool, f"{field} must be Boolean")
    normalization = observation["normalization_succeeded"]
    _require(
        type(normalization) is bool
        or (
            normalization is None
            and observation["evidence_kind"] == CONTROLLED_LIVE_EVIDENCE_KIND
        ),
        "normalization evidence is invalid for the evidence kind",
    )
    _require(
        isinstance(observation["provider_call_count"], int)
        and not isinstance(observation["provider_call_count"], bool)
        and observation["provider_call_count"] >= 0,
        "provider call count is invalid",
    )
    from src.evaluation import controlled_live_provider_qualification as live

    pregrading_definitive_failure = (
        observation["evidence_kind"] == CONTROLLED_LIVE_EVIDENCE_KIND
        and observation["schedule_completed"] is False
        and observation["provider_outcome_category"]
        in live._BOUNDED_TRANSPORT_FAILURE_STOP_REASONS
        and observation["provider_call_count"] == 1
        and observation["contract_valid"] is False
        and observation["normalization_succeeded"] is None
        and observation["quality_gate_passed"] is False
        and observation["hard_failure_present"] is False
        and observation["input_token_count"] == 0
        and observation["output_token_count"] == 0
    )
    for field in ("input_token_count", "output_token_count"):
        _require(
            isinstance(observation[field], int)
            and not isinstance(observation[field], bool)
            and observation[field] >= 0,
            f"qualification observation {field} is invalid",
        )
    if not pregrading_definitive_failure:
        for field in ("input_token_count", "output_token_count"):
            _require(
                observation[field] > 0,
                f"qualification observation {field} is invalid",
            )
    _require(
        observation["authority_safety_valid"] is True,
        "qualification evidence authority or safety invariants are invalid",
    )
    return True


def serialize_qualification_observation(observation: Dict[str, Any]) -> str:
    payload = deepcopy(observation)
    validate_qualification_observation(payload)
    return _canonical_json(payload)


def qualification_observation_sha256(observation: Dict[str, Any]) -> str:
    return sha256(
        serialize_qualification_observation(observation).encode("utf-8")
    ).hexdigest()
