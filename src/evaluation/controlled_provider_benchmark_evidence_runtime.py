"""Provider-neutral controlled benchmark run-evidence ownership.

This evaluation-only runtime consumes an explicitly injected transport through
the generic benchmark harness. It imports no provider SDK, reads no credential
or environment configuration, selects no route, and grants no live authority.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
from typing import Any, Callable, Dict

from src.evaluation.controlled_provider_benchmark_harness import (
    HARNESS_VERSION,
    TRANSPORT_RESULT_FIELDS,
    authorization_sha256,
    build_controlled_benchmark_harness_contract,
    build_result_artifact,
    checkpoint_sha256,
    controlled_benchmark_harness_sha256,
    execute_schedule_with_fake_transport,
    pricing_table_sha256,
    validate_checkpoint,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    controlled_provider_benchmark_plan_sha256,
    validate_controlled_provider_benchmark_plan,
)


EVIDENCE_RUNTIME_VERSION = (
    "controlled-provider-benchmark-evidence-runtime-v1"
)
EVIDENCE_SCHEMA_VERSION = "controlled-provider-benchmark-run-evidence-v1"
APPROVED_ARTIFACT_DIRECTORY = Path("outputs/provider_benchmark")

_EVIDENCE_FIELDS = {
    "evidence_schema_version",
    "evidence_runtime_version",
    "harness_version",
    "harness_sha256",
    "transport_result_fields",
    "execution_at_utc",
    "plan_sha256",
    "model_catalog_snapshot_sha256",
    "corpus_sha256",
    "authorization_sha256",
    "pricing_sha256",
    "checkpoint_sha256",
    "execution_status",
    "state_counts",
    "checkpoint",
    "aggregate_usage",
    "grading_summaries",
    "all_executed_quality_gates_passed",
    "hard_failure_present",
    "retention_policy",
    "authority_invariants",
}
_PROHIBITED_EVIDENCE_KEYS = {
    "api_key",
    "credential",
    "environment",
    "golden",
    "header",
    "normalized_output",
    "prompt",
    "raw_exception",
    "raw_provider",
    "raw_request",
    "raw_response",
    "reasoning",
    "repository_path",
    "request_id",
    "request_packet",
    "response_envelope",
    "sdk_object",
    "synthetic_input",
}
_RETENTION_POLICY = {
    "automatic_persistence": False,
    "ignored_artifact_only": True,
    "required_file_mode": "0600",
    "maximum_retention_days": 7,
    "operator_review_required": True,
    "deletion_required": True,
    "overwrite_allowed": False,
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


def _contains_prohibited_evidence(value: Any) -> bool:
    return any(key in _PROHIBITED_EVIDENCE_KEYS for key in _iter_keys(value))


def normalize_execution_timestamp(value: Any) -> str:
    """Return one canonical UTC timestamp for deterministic run provenance."""

    _require(isinstance(value, str) and bool(value.strip()), "execution time is required")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("execution time must be a valid UTC timestamp") from exc
    _require(parsed.tzinfo is not None, "execution time must include a timezone")
    normalized = parsed.astimezone(timezone.utc)
    return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _state_counts(checkpoint: Dict[str, Any], schedule_count: int) -> Dict[str, int]:
    completed = len(checkpoint["completed_schedule_keys"])
    blocked = len(checkpoint["blocked_schedule_keys"])
    ambiguous = len(checkpoint["ambiguous_schedule_keys"])
    finalized = completed + blocked + ambiguous
    _require(finalized <= schedule_count, "checkpoint state count exceeds schedule")
    return {
        "completed": completed,
        "blocked": blocked,
        "ambiguous": ambiguous,
        "pending": schedule_count - finalized,
    }


def _execution_status(
    checkpoint: Dict[str, Any],
    state_counts: Dict[str, int],
) -> str:
    if checkpoint["stop_reason"] is not None:
        return "stopped"
    if state_counts["pending"] == 0:
        return "completed"
    return "partial"


def _expected_evidence(
    *,
    checkpoint: Dict[str, Any],
    execution_at_utc: str,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    validate_controlled_provider_benchmark_plan(plan)
    validate_checkpoint(
        checkpoint,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    harness_artifact = build_result_artifact(
        checkpoint=checkpoint,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    schedule_count = plan["request_counts"]["maximum_total_requests"]
    counts = _state_counts(checkpoint, schedule_count)
    summaries = checkpoint["grading_summaries"]
    hard_failure_present = (
        checkpoint["stop_reason"] is not None
        or any(
            any(value for value in summary["hard_failures"].values())
            for summary in summaries
        )
    )
    return {
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "evidence_runtime_version": EVIDENCE_RUNTIME_VERSION,
        "harness_version": HARNESS_VERSION,
        "harness_sha256": controlled_benchmark_harness_sha256(
            build_controlled_benchmark_harness_contract(plan=plan)
        ),
        "transport_result_fields": sorted(TRANSPORT_RESULT_FIELDS),
        "execution_at_utc": execution_at_utc,
        "plan_sha256": controlled_provider_benchmark_plan_sha256(plan),
        "model_catalog_snapshot_sha256": plan[
            "model_catalog_snapshot_sha256"
        ],
        "corpus_sha256": plan["step8o_case_corpus_sha256"],
        "authorization_sha256": authorization_sha256(authorization),
        "pricing_sha256": pricing_table_sha256(pricing),
        "checkpoint_sha256": checkpoint_sha256(
            checkpoint,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        ),
        "execution_status": _execution_status(checkpoint, counts),
        "state_counts": counts,
        "checkpoint": deepcopy(checkpoint),
        "aggregate_usage": deepcopy(checkpoint["aggregate_usage"]),
        "grading_summaries": deepcopy(summaries),
        "all_executed_quality_gates_passed": (
            bool(summaries)
            and all(summary["quality_gate_passed"] for summary in summaries)
            and not hard_failure_present
        ),
        "hard_failure_present": hard_failure_present,
        "retention_policy": deepcopy(harness_artifact["retention_policy"]),
        "authority_invariants": {
            **deepcopy(harness_artifact["authority_invariants"]),
            "routing_change_allowed": False,
            "registry_write_allowed": False,
        },
    }


def build_provider_neutral_run_evidence(
    *,
    checkpoint: Dict[str, Any],
    execution_at_utc: str,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    normalized_time = normalize_execution_timestamp(execution_at_utc)
    evidence = _expected_evidence(
        checkpoint=deepcopy(checkpoint),
        execution_at_utc=normalized_time,
        plan=deepcopy(plan),
        authorization=deepcopy(authorization),
        pricing=deepcopy(pricing),
    )
    validate_provider_neutral_run_evidence(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    return deepcopy(evidence)


def validate_provider_neutral_run_evidence(
    evidence: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> bool:
    _require(
        isinstance(evidence, dict) and set(evidence) == _EVIDENCE_FIELDS,
        "run evidence fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_evidence(evidence),
        "run evidence contains prohibited provider material",
    )
    expected = _expected_evidence(
        checkpoint=deepcopy(evidence.get("checkpoint")),
        execution_at_utc=normalize_execution_timestamp(
            evidence.get("execution_at_utc")
        ),
        plan=deepcopy(plan),
        authorization=deepcopy(authorization),
        pricing=deepcopy(pricing),
    )
    _require(evidence == expected, "run evidence binding or schema mismatch")
    return True


def serialize_provider_neutral_run_evidence(
    evidence: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> str:
    payload = deepcopy(evidence)
    validate_provider_neutral_run_evidence(
        payload,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    return _canonical_json(payload)


def provider_neutral_run_evidence_sha256(
    evidence: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> str:
    return sha256(
        serialize_provider_neutral_run_evidence(
            evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        ).encode("utf-8")
    ).hexdigest()


def execute_provider_neutral_evidence_run(
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    transport: Callable[[Dict[str, Any], int], Dict[str, Any]],
    execution_time_source: Callable[[], str],
    prior_checkpoint: Dict[str, Any] | None = None,
    maximum_schedule_items: int | None = None,
) -> Dict[str, Any]:
    """Execute only through the harness's explicitly injected fake seam."""

    _require(callable(transport), "injected transport is required")
    _require(
        callable(execution_time_source),
        "injected execution time source is required",
    )
    if maximum_schedule_items is not None:
        _require(
            isinstance(maximum_schedule_items, int)
            and not isinstance(maximum_schedule_items, bool)
            and maximum_schedule_items > 0,
            "maximum schedule items must be a positive integer",
        )
    execution_at_utc = normalize_execution_timestamp(execution_time_source())
    execution = execute_schedule_with_fake_transport(
        plan=deepcopy(plan),
        authorization=deepcopy(authorization),
        pricing=deepcopy(pricing),
        transport=transport,
        execution_at_utc=execution_at_utc,
        prior_checkpoint=deepcopy(prior_checkpoint),
        maximum_schedule_items=maximum_schedule_items,
    )
    return build_provider_neutral_run_evidence(
        checkpoint=execution["checkpoint"],
        execution_at_utc=execution_at_utc,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )


def _prepare_artifact_path(
    artifact_path: str | Path,
    *,
    repository_root: str | Path,
) -> Path:
    root = Path(repository_root).resolve()
    _require(root.is_dir() and not root.is_symlink(), "repository root is unsafe")
    candidate = Path(artifact_path)
    _require(candidate.is_absolute(), "evidence path must be absolute")
    _require(".." not in candidate.parts, "evidence path traversal is prohibited")
    approved = root / APPROVED_ARTIFACT_DIRECTORY
    _require(
        candidate.parent == approved
        and candidate.suffix == ".json"
        and candidate.name not in {"", ".json"},
        "evidence path is outside the approved benchmark namespace",
    )
    current = root
    for part in APPROVED_ARTIFACT_DIRECTORY.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            _require(
                current.is_dir() and not current.is_symlink(),
                "evidence parent path is unsafe",
            )
        else:
            current.mkdir(mode=0o700)
        _require(
            not stat.S_IMODE(current.stat().st_mode)
            & (stat.S_IWGRP | stat.S_IWOTH),
            "evidence parent permissions are unsafe",
        )
    _require(
        not candidate.exists() and not candidate.is_symlink(),
        "evidence overwrite is prohibited",
    )
    return candidate


def write_provider_neutral_run_evidence_exclusive(
    artifact_path: str | Path,
    evidence: Dict[str, Any],
    *,
    repository_root: str | Path,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Path:
    """Persist one bounded evidence artifact with exclusive 0600 creation."""

    encoded = serialize_provider_neutral_run_evidence(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    ).encode("utf-8")
    path = _prepare_artifact_path(
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
        raise ValueError("persisted evidence is malformed") from None
    _require(persisted == evidence, "persisted evidence verification failed")
    return path
