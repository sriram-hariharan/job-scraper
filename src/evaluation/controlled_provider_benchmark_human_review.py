"""Immutable post-result human-review records for controlled benchmarks.

This evaluation-only owner binds a bounded operator decision to one exact,
natively validated qualification-evidence digest and one executed schedule
row.  It does not execute providers, grade output, select routes, or access
application data.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
from typing import Any, Callable, Dict

from src.evaluation.controlled_provider_qualification_evidence_adapter import (
    PROVIDER_NEUTRAL_EVIDENCE_KIND,
    build_qualification_observation,
)
from src.evaluation.provider_benchmark_contract import (
    WORKLOAD_ORDER,
    build_provider_benchmark_contract,
    validate_provider_benchmark_contract,
)


HUMAN_REVIEW_CONTRACT_VERSION = (
    "controlled-provider-benchmark-human-review-contract-v1"
)
HUMAN_REVIEW_RECORD_VERSION = (
    "controlled-provider-benchmark-human-review-record-v1"
)
DECISION_SCOPE = "post_result_human_review_requirement_only"
APPROVED_REVIEW_DIRECTORY = Path("outputs/provider_benchmark")
MAXIMUM_REVIEWER_ID_LENGTH = 64

_RECORDED_DECISIONS = frozenset({"approved", "rejected"})
_REVIEW_RECORD_FIELDS = {
    "review_record_version",
    "review_contract_version",
    "decision_scope",
    "evidence_sha256",
    "schedule_key",
    "workload_id",
    "provider",
    "model",
    "human_review_required",
    "decision",
    "reviewer_id",
    "reviewed_at_utc",
}
_ASSESSMENT_FIELDS = {
    "review_contract_version",
    "decision_scope",
    "evidence_sha256",
    "schedule_key",
    "workload_id",
    "provider",
    "model",
    "human_review_required",
    "decision",
    "review_requirement_satisfied",
    "negative_resolution",
}
_PROHIBITED_REVIEW_KEY_PARTS = {
    "active_model",
    "api_key",
    "credential",
    "evidence_payload",
    "full_evidence",
    "normalized_output",
    "production_qualified",
    "prompt",
    "raw_exception",
    "raw_provider",
    "raw_request",
    "raw_response",
    "reasoning",
    "recommended_route",
    "request_id",
    "routing_allowed",
    "sdk_object",
    "selected_model",
    "synthetic_input",
}
_REVIEWER_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9._:-]*\Z")


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


def _contains_prohibited_review_key(value: Any) -> bool:
    return any(
        prohibited in key
        for key in _iter_keys(value)
        for prohibited in _PROHIBITED_REVIEW_KEY_PARTS
    )


def canonical_human_review_requirements() -> Dict[str, bool]:
    """Derive the review requirement solely from the canonical contract."""

    contract = build_provider_benchmark_contract()
    validate_provider_benchmark_contract(contract)
    definitions = contract["workloads"]
    requirements = {
        row["workload_id"]: row["human_review_required"]
        for row in definitions
    }
    _require(
        tuple(requirements) == WORKLOAD_ORDER,
        "human-review workload coverage mismatch",
    )
    _require(
        all(type(value) is bool for value in requirements.values()),
        "human-review requirement must be Boolean",
    )
    return deepcopy(requirements)


def human_review_required_for_workload(workload_id: Any) -> bool:
    _require(isinstance(workload_id, str), "workload ID must be text")
    normalized = workload_id.strip()
    requirements = canonical_human_review_requirements()
    _require(normalized in requirements, "unknown benchmark workload")
    return requirements[normalized]


def normalize_reviewer_id(value: Any) -> str:
    _require(isinstance(value, str), "reviewer ID must be text")
    normalized = value.strip().lower()
    _require(bool(normalized), "reviewer ID is required")
    _require(
        len(normalized) <= MAXIMUM_REVIEWER_ID_LENGTH,
        "reviewer ID exceeds the maximum length",
    )
    _require(
        _REVIEWER_ID_PATTERN.fullmatch(normalized) is not None,
        "reviewer ID contains unsupported characters",
    )
    return normalized


def normalize_review_timestamp(value: Any) -> str:
    _require(
        isinstance(value, str) and bool(value.strip()),
        "review timestamp is required",
    )
    text = value.strip()
    parseable = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(parseable)
    except ValueError as exc:
        raise ValueError("review timestamp must be valid UTC") from exc
    _require(
        parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed),
        "review timestamp must be timezone-aware UTC",
    )
    return parsed.astimezone(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


def _normalize_decision(value: Any) -> str:
    _require(isinstance(value, str), "review decision must be text")
    normalized = value.strip().lower()
    _require(
        normalized in _RECORDED_DECISIONS,
        "review decision must be approved or rejected",
    )
    return normalized


def _validated_evidence_row(
    *,
    evidence: Dict[str, Any],
    schedule_key: Any,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> tuple[str, Dict[str, Any]]:
    observation = build_qualification_observation(
        evidence=deepcopy(evidence),
        schedule_key=schedule_key,
        plan=deepcopy(plan),
        authorization=deepcopy(authorization),
        pricing=deepcopy(pricing),
    )
    return observation["evidence_sha256"], observation


def _require_approval_safe(
    observation: Dict[str, Any],
) -> None:
    _require(
        observation["hard_failure_present"] is False,
        "approval cannot override benchmark hard failure",
    )
    _require(
        observation["schedule_completed"] is True,
        "reviewed schedule row did not complete successfully",
    )
    _require(
        observation["contract_valid"] is True,
        (
            "approval requires valid schema"
            if observation["evidence_kind"] == PROVIDER_NEUTRAL_EVIDENCE_KIND
            else "approval requires a valid production contract"
        ),
    )
    _require(
        observation["normalization_succeeded"] is not False,
        "approval requires successful normalization when separately evidenced",
    )
    _require(
        observation["quality_gate_passed"] is True,
        "approval requires passed deterministic quality gate",
    )
    _require(
        observation["provider_outcome_category"] == "success"
        and observation["provider_call_count"] == 1,
        "approval requires successful provider outcome",
    )
    _require(
        observation["authority_safety_valid"] is True,
        "approval cannot override deterministic authority invariant",
    )


def _expected_review_record(
    *,
    evidence: Dict[str, Any],
    schedule_key: Any,
    decision: Any,
    reviewer_id: Any,
    reviewed_at_utc: Any,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    evidence_digest, observation = _validated_evidence_row(
        evidence=evidence,
        schedule_key=schedule_key,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    _require(
        human_review_required_for_workload(observation["workload_id"]),
        "review record is prohibited for a workload that does not require review",
    )
    normalized_decision = _normalize_decision(decision)
    if normalized_decision == "approved":
        _require_approval_safe(observation)
    return {
        "review_record_version": HUMAN_REVIEW_RECORD_VERSION,
        "review_contract_version": HUMAN_REVIEW_CONTRACT_VERSION,
        "decision_scope": DECISION_SCOPE,
        "evidence_sha256": evidence_digest,
        "schedule_key": observation["schedule_key"],
        "workload_id": observation["workload_id"],
        "provider": observation["provider"],
        "model": observation["model"],
        "human_review_required": True,
        "decision": normalized_decision,
        "reviewer_id": normalize_reviewer_id(reviewer_id),
        "reviewed_at_utc": normalize_review_timestamp(reviewed_at_utc),
    }


def build_post_result_human_review_record(
    *,
    evidence: Dict[str, Any],
    schedule_key: str,
    decision: str,
    reviewer_id: str,
    review_time_source: Callable[[], str],
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    """Build one decision overlay without mutating its evidence input."""

    _require(callable(review_time_source), "review time source is required")
    record = _expected_review_record(
        evidence=deepcopy(evidence),
        schedule_key=schedule_key,
        decision=decision,
        reviewer_id=reviewer_id,
        reviewed_at_utc=review_time_source(),
        plan=deepcopy(plan),
        authorization=deepcopy(authorization),
        pricing=deepcopy(pricing),
    )
    validate_post_result_human_review_record(
        record,
        evidence=evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    return deepcopy(record)


def validate_post_result_human_review_record(
    record: Dict[str, Any],
    *,
    evidence: Dict[str, Any],
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> bool:
    _require(
        isinstance(record, dict) and set(record) == _REVIEW_RECORD_FIELDS,
        "human-review record fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_review_key(record),
        "human-review record contains prohibited material",
    )
    expected = _expected_review_record(
        evidence=deepcopy(evidence),
        schedule_key=record.get("schedule_key"),
        decision=record.get("decision"),
        reviewer_id=record.get("reviewer_id"),
        reviewed_at_utc=record.get("reviewed_at_utc"),
        plan=deepcopy(plan),
        authorization=deepcopy(authorization),
        pricing=deepcopy(pricing),
    )
    _require(record == expected, "human-review record evidence binding mismatch")
    return True


def assess_post_result_human_review(
    *,
    evidence: Dict[str, Any],
    schedule_key: str,
    review_record: Dict[str, Any] | None,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    evidence_digest, observation = _validated_evidence_row(
        evidence=evidence,
        schedule_key=schedule_key,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    required = human_review_required_for_workload(observation["workload_id"])
    if not required:
        _require(
            review_record is None,
            "review record is prohibited for a workload that does not require review",
        )
        decision = "not_required"
    elif review_record is None:
        decision = "pending"
    else:
        validate_post_result_human_review_record(
            review_record,
            evidence=evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        )
        _require(
            review_record["schedule_key"] == observation["schedule_key"],
            "review record schedule binding mismatch",
        )
        decision = review_record["decision"]
    assessment = {
        "review_contract_version": HUMAN_REVIEW_CONTRACT_VERSION,
        "decision_scope": DECISION_SCOPE,
        "evidence_sha256": evidence_digest,
        "schedule_key": observation["schedule_key"],
        "workload_id": observation["workload_id"],
        "provider": observation["provider"],
        "model": observation["model"],
        "human_review_required": required,
        "decision": decision,
        "review_requirement_satisfied": (
            not required or decision == "approved"
        ),
        "negative_resolution": decision == "rejected",
    }
    _require(set(assessment) == _ASSESSMENT_FIELDS, "review assessment mismatch")
    return deepcopy(assessment)


def serialize_post_result_human_review_record(
    record: Dict[str, Any],
    *,
    evidence: Dict[str, Any],
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> str:
    payload = deepcopy(record)
    validate_post_result_human_review_record(
        payload,
        evidence=evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    return _canonical_json(payload)


def post_result_human_review_sha256(
    record: Dict[str, Any],
    *,
    evidence: Dict[str, Any],
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> str:
    serialized = serialize_post_result_human_review_record(
        record,
        evidence=evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def _prepare_review_path(
    artifact_path: str | Path,
    *,
    repository_root: str | Path,
) -> Path:
    root = Path(repository_root).resolve()
    _require(root.is_dir() and not root.is_symlink(), "repository root is unsafe")
    candidate = Path(artifact_path)
    _require(candidate.is_absolute(), "review path must be absolute")
    _require(".." not in candidate.parts, "review path traversal is prohibited")
    approved = root / APPROVED_REVIEW_DIRECTORY
    _require(
        candidate.parent == approved
        and candidate.name.startswith("human-review-")
        and candidate.suffix == ".json"
        and candidate.name != "human-review-.json",
        "review path is outside the approved benchmark namespace",
    )
    current = root
    for part in APPROVED_REVIEW_DIRECTORY.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            _require(
                current.is_dir() and not current.is_symlink(),
                "review parent path is unsafe",
            )
        else:
            current.mkdir(mode=0o700)
        _require(
            not stat.S_IMODE(current.stat().st_mode)
            & (stat.S_IWGRP | stat.S_IWOTH),
            "review parent permissions are unsafe",
        )
    _require(
        not candidate.exists() and not candidate.is_symlink(),
        "review overwrite is prohibited",
    )
    return candidate


def write_post_result_human_review_record_exclusive(
    artifact_path: str | Path,
    record: Dict[str, Any],
    *,
    repository_root: str | Path,
    evidence: Dict[str, Any],
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Path:
    """Persist one separate immutable review artifact with mode 0600."""

    encoded = serialize_post_result_human_review_record(
        record,
        evidence=evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    ).encode("utf-8")
    path = _prepare_review_path(
        artifact_path,
        repository_root=repository_root,
    )
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
    _require(stat.S_IMODE(path.stat().st_mode) == 0o600, "mode must be 0600")
    try:
        persisted = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("persisted review record is malformed") from None
    _require(persisted == record, "persisted review verification failed")
    return path
