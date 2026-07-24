"""Versioned, bounded comparison primitives for evidence-chain shadow parity."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Dict, List, Mapping, Sequence, TypedDict


PARITY_CONTRACT_VERSION = "evidence-chain-shadow-parity-v1"
_MODES = {"exact", "ordered", "set", "numeric", "digest", "incomparable"}
_STATUSES = {
    "match",
    "mismatch",
    "missing_authoritative",
    "missing_shadow",
    "malformed",
    "intentionally_incomparable",
}


class ParityFieldSpec(TypedDict, total=False):
    field: str
    mode: str
    authoritative_value: Any
    shadow_value: Any
    authoritative_present: bool
    shadow_present: bool
    absolute_tolerance: float
    relative_tolerance: float
    reason: str


class ParityFieldResult(TypedDict, total=False):
    field: str
    mode: str
    status: str
    delta: float
    authoritative_value: float
    shadow_value: float
    authoritative_digest: str
    shadow_digest: str
    reason: str


def canonical_artifact_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _bounded_code(value: Any, fallback: str) -> str:
    text = _clean_text(value)
    return text[:120] if re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", text) else fallback


def _safe_sequence(value: Any) -> List[str] | None:
    if not isinstance(value, (list, tuple)):
        return None
    result: List[str] = []
    for item in value:
        if not isinstance(item, (str, int)) or isinstance(item, bool):
            return None
        result.append(str(item))
    return result


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    normalized = float(value)
    return normalized if math.isfinite(normalized) else None


def _field_result(spec: Mapping[str, Any]) -> ParityFieldResult:
    field = _clean_text(spec.get("field"))
    mode = _clean_text(spec.get("mode"))
    base: ParityFieldResult = {"field": field, "mode": mode, "status": "malformed"}
    if not field or mode not in _MODES:
        return base
    if mode == "incomparable":
        reason = _bounded_code(spec.get("reason"), "intentionally_incomparable")
        return {**base, "status": "intentionally_incomparable", "reason": reason}
    if spec.get("authoritative_present", "authoritative_value" in spec) is False:
        return {**base, "status": "missing_authoritative"}
    if spec.get("shadow_present", "shadow_value" in spec) is False:
        return {**base, "status": "missing_shadow"}
    if "authoritative_value" not in spec:
        return {**base, "status": "missing_authoritative"}
    if "shadow_value" not in spec:
        return {**base, "status": "missing_shadow"}

    authoritative = spec["authoritative_value"]
    shadow = spec["shadow_value"]
    if mode == "exact":
        if not isinstance(authoritative, (str, int, bool)) or not isinstance(
            shadow, (str, int, bool)
        ):
            return base
        return {**base, "status": "match" if authoritative == shadow else "mismatch"}
    if mode in {"ordered", "set"}:
        left, right = _safe_sequence(authoritative), _safe_sequence(shadow)
        if left is None or right is None:
            return base
        matches = left == right if mode == "ordered" else set(left) == set(right)
        return {**base, "status": "match" if matches else "mismatch"}
    if mode == "numeric":
        left, right = _finite_number(authoritative), _finite_number(shadow)
        absolute = _finite_number(spec.get("absolute_tolerance", 0.0))
        relative = _finite_number(spec.get("relative_tolerance", 0.0))
        if (
            left is None
            or right is None
            or absolute is None
            or relative is None
            or absolute < 0
            or relative < 0
        ):
            return base
        delta = abs(left - right)
        allowed = max(absolute, relative * max(abs(left), abs(right)))
        return {
            **base,
            "status": "match" if delta <= allowed else "mismatch",
            "authoritative_value": left,
            "shadow_value": right,
            "delta": delta,
        }
    try:
        left_digest = canonical_artifact_digest(authoritative)
        right_digest = canonical_artifact_digest(shadow)
    except (TypeError, ValueError):
        return base
    return {
        **base,
        "status": "match" if left_digest == right_digest else "mismatch",
        "authoritative_digest": left_digest,
        "shadow_digest": right_digest,
    }


def compare_shadow_parity(
    *,
    pipeline_run_id: str,
    job_id: str,
    selected_resume_id: str,
    fields: Sequence[Mapping[str, Any]],
    warnings: Sequence[str] = (),
) -> Dict[str, Any]:
    """Compare explicit bounded facts without executing or reading either path."""

    results = [_field_result(spec) for spec in fields]
    results.sort(key=lambda row: (row["field"], row["mode"]))
    counts = {status: 0 for status in _STATUSES}
    for result in results:
        counts[result["status"]] += 1
    missing_count = counts["missing_authoritative"] + counts["missing_shadow"]
    if counts["malformed"]:
        overall = "malformed"
    elif counts["mismatch"]:
        overall = "mismatch"
    elif missing_count:
        overall = "incomplete"
    else:
        overall = "match"
    bounded_warnings = sorted(
        {
            _bounded_code(warning, "warning_redacted")
            for warning in warnings
            if _clean_text(warning)
        }
    )[:20]
    return {
        "contract_version": PARITY_CONTRACT_VERSION,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "job_id": _clean_text(job_id),
        "selected_resume_id": _clean_text(selected_resume_id),
        "overall_classification": overall,
        "field_results": results,
        "match_count": counts["match"],
        "mismatch_count": counts["mismatch"],
        "missing_count": missing_count,
        "malformed_count": counts["malformed"],
        "intentionally_incomparable_count": counts["intentionally_incomparable"],
        "warnings": bounded_warnings,
    }
