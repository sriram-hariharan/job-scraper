"""Bounded wrapper for the canonical production job-priority renderer."""

from __future__ import annotations

from copy import deepcopy
import math
import re
import time
from typing import Any, Dict, Mapping

from src.agents.evidence_chain_shadow_parity import canonical_artifact_digest


PRODUCTION_SHADOW_PRIORITY_OWNER_VERSION = (
    "production-shadow-job-priority-owner-v1"
)
_IDENTITY = re.compile(r"[A-Za-z0-9_.:@/-]{1,200}")
_TEXT = re.compile(r"[A-Za-z0-9 _.,:@/+&()'-]{1,200}")
_ENUM = re.compile(r"[A-Za-z0-9_.:-]{1,120}")
_PRIORITIES = {
    "apply_now",
    "tailor_first",
    "manual_review",
    "skip_for_now",
    "watch_source",
}
_REQUIRED_INPUT_FIELDS = (
    "job_id",
    "company",
    "title",
    "action",
    "deterministic_winner_score",
    "deterministic_winner_available",
    "fallback_only_no_deterministic_match",
    "packet_generation_allowed",
    "packet_generation_block_reason",
)
_DIRECT_FIELDS = (
    ("job_id", True),
    ("advisory_priority", True),
    ("advisory_reason_codes", False),
    ("existing_action", True),
    ("packet_generation_allowed", True),
)


def _codes(value: Any) -> list[str] | None:
    if value is None or value == "":
        return None
    candidates = value if isinstance(value, list) else str(value).split("|")
    result: list[str] = []
    for candidate in candidates:
        code = str(candidate or "").strip().lower()
        if not _ENUM.fullmatch(code):
            return None
        if code not in result:
            result.append(code)
    return sorted(result)[:25]


def _bool_text(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes"}:
        return "true"
    if text in {"false", "0", "no"}:
        return "false"
    return None


def _input_row(facts: Mapping[str, Any]) -> Dict[str, Any] | None:
    if not isinstance(facts, Mapping) or any(
        field not in facts for field in _REQUIRED_INPUT_FIELDS
    ):
        return None
    job_id = str(facts.get("job_id") or "").strip()
    company = str(facts.get("company") or "").strip()
    title = str(facts.get("title") or "").strip()
    action = str(facts.get("action") or "").strip()
    score = str(facts.get("deterministic_winner_score") or "").strip()
    if (
        not _IDENTITY.fullmatch(job_id)
        or not _TEXT.fullmatch(company)
        or not _TEXT.fullmatch(title)
        or not _ENUM.fullmatch(action)
    ):
        return None
    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric_score):
        return None
    deterministic = _bool_text(facts.get("deterministic_winner_available"))
    fallback_only = _bool_text(
        facts.get("fallback_only_no_deterministic_match")
    )
    packet_allowed = _bool_text(facts.get("packet_generation_allowed"))
    if None in {deterministic, fallback_only, packet_allowed}:
        return None
    block_reason = str(
        facts.get("packet_generation_block_reason") or ""
    ).strip()
    if block_reason and not _ENUM.fullmatch(block_reason):
        return None
    row: Dict[str, Any] = {
        "job_id": job_id,
        "company": company,
        "title": title,
        "action": action,
        "deterministic_winner_score": score,
        "deterministic_winner_available": deterministic,
        "fallback_only_no_deterministic_match": fallback_only,
        "packet_generation_allowed": packet_allowed,
        "packet_generation_block_reason": block_reason,
    }
    for field in ("source_recommendation", "critic_decision"):
        value = str(facts.get(field) or "").strip()
        if value:
            if not _ENUM.fullmatch(value):
                return None
            row[field] = value
    return row


def _bounded_output(value: Any, expected_job_id: str) -> Dict[str, Any] | None:
    if (
        not isinstance(value, list)
        or len(value) != 1
        or not isinstance(value[0], Mapping)
    ):
        return None
    row = dict(value[0])
    job_id = str(row.get("job_id") or "").strip()
    priority = str(row.get("advisory_priority") or "").strip()
    action = str(row.get("existing_action") or "").strip()
    packet_raw = row.get("packet_generation_allowed")
    packet_present = packet_raw is not None and packet_raw != ""
    packet_allowed = _bool_text(packet_raw) if packet_present else None
    reason_raw = row.get("advisory_reason_codes")
    reason_present = reason_raw is not None and reason_raw != ""
    reasons = _codes(reason_raw)
    if job_id != expected_job_id:
        return None
    if priority and priority not in _PRIORITIES:
        return None
    if action and not _ENUM.fullmatch(action):
        return None
    if packet_present and packet_allowed is None:
        return None
    if reason_present and reasons is None:
        return None
    bounded: Dict[str, Any] = {"job_id": job_id}
    if priority:
        bounded["advisory_priority"] = priority
    if reasons:
        bounded["advisory_reason_codes"] = reasons
    if action:
        bounded["existing_action"] = action
    if packet_allowed is not None:
        bounded["packet_generation_allowed"] = packet_allowed == "true"
    return bounded


def _direct_parity(
    authoritative: Mapping[str, Any],
    rendered: Mapping[str, Any],
) -> Dict[str, Any]:
    records: list[Dict[str, Any]] = []
    mismatch = False
    incomplete = False
    for field, required in _DIRECT_FIELDS:
        left_present = (
            field in authoritative
            and authoritative[field] is not None
            and authoritative[field] != ""
        )
        right_present = (
            field in rendered
            and rendered[field] is not None
            and rendered[field] != ""
        )
        if not left_present and not right_present:
            classification = "both_missing"
        elif not left_present:
            classification = "authoritative_missing"
        elif not right_present:
            classification = "shadow_missing"
        else:
            left = (
                _codes(authoritative[field])
                if field == "advisory_reason_codes"
                else authoritative[field]
            )
            right = (
                _codes(rendered[field])
                if field == "advisory_reason_codes"
                else rendered[field]
            )
            if left is None or right is None:
                classification = "incomparable"
            else:
                classification = (
                    "exact_match"
                    if canonical_artifact_digest(left)
                    == canonical_artifact_digest(right)
                    else "mismatch"
                )
        mismatch = mismatch or classification == "mismatch"
        incomplete = incomplete or (
            required
            and classification
            in {"authoritative_missing", "shadow_missing", "both_missing"}
        )
        records.append(
            {
                "field": field,
                "classification": classification,
                "authoritative_present": left_present,
                "rendered_present": right_present,
            }
        )
    status = "mismatch" if mismatch else "incomplete" if incomplete else "passed"
    return {
        "status": status,
        "exact_match_count": sum(
            row["classification"] == "exact_match" for row in records
        ),
        "mismatch_count": sum(
            row["classification"] == "mismatch" for row in records
        ),
        "incomplete_count": sum(
            row["classification"]
            in {"authoritative_missing", "shadow_missing", "both_missing"}
            for row in records
        ),
        "comparison_records": records,
    }


def invoke_job_prioritization_owner(
    *,
    input_facts: Mapping[str, Any],
    authoritative_priority_facts: Mapping[str, Any],
    _renderer: Any = None,
) -> Dict[str, Any]:
    """Invoke the canonical renderer once and return bounded detached facts."""

    row = _input_row(deepcopy(dict(input_facts)))
    if row is None:
        return {
            "wrapper_version": PRODUCTION_SHADOW_PRIORITY_OWNER_VERSION,
            "status": "owner_input_incomplete",
            "failure_code": "required_renderer_input_missing_or_invalid",
            "invocation_attempted": False,
            "invocation_completed": False,
            "invocation_count": 0,
            "invocation_latency_ms": 0,
            "rendered_priority_facts": {},
            "direct_owner_parity": {"status": "incomplete"},
        }
    renderer_input = [deepcopy(row)]
    before = deepcopy(renderer_input)
    started = time.perf_counter_ns()
    try:
        if _renderer is None:
            from src.agents.job_prioritization_agent import (
                render_job_prioritization_recommendation_rows,
            )

            renderer = render_job_prioritization_recommendation_rows
        else:
            renderer = _renderer
        raw_output = renderer(deepcopy(renderer_input))
    except Exception:
        return {
            "wrapper_version": PRODUCTION_SHADOW_PRIORITY_OWNER_VERSION,
            "status": "owner_invocation_failed",
            "failure_code": "renderer_invocation_failed",
            "invocation_attempted": True,
            "invocation_completed": False,
            "invocation_count": 1,
            "invocation_latency_ms": max(
                0, int((time.perf_counter_ns() - started) / 1_000_000)
            ),
            "rendered_priority_facts": {},
            "direct_owner_parity": {"status": "failed"},
        }
    latency_ms = max(
        0, int((time.perf_counter_ns() - started) / 1_000_000)
    )
    if renderer_input != before:
        return {
            "wrapper_version": PRODUCTION_SHADOW_PRIORITY_OWNER_VERSION,
            "status": "owner_output_invalid",
            "failure_code": "renderer_input_mutated",
            "invocation_attempted": True,
            "invocation_completed": False,
            "invocation_count": 1,
            "invocation_latency_ms": latency_ms,
            "rendered_priority_facts": {},
            "direct_owner_parity": {"status": "failed"},
        }
    bounded = _bounded_output(raw_output, row["job_id"])
    if bounded is None:
        return {
            "wrapper_version": PRODUCTION_SHADOW_PRIORITY_OWNER_VERSION,
            "status": "owner_output_invalid",
            "failure_code": "renderer_output_invalid",
            "invocation_attempted": True,
            "invocation_completed": False,
            "invocation_count": 1,
            "invocation_latency_ms": latency_ms,
            "rendered_priority_facts": {},
            "direct_owner_parity": {"status": "failed"},
        }
    parity = _direct_parity(
        deepcopy(dict(authoritative_priority_facts)), bounded
    )
    status = {
        "passed": "owner_parity_passed",
        "mismatch": "owner_parity_mismatch",
        "incomplete": "owner_invocation_completed",
    }[parity["status"]]
    return {
        "wrapper_version": PRODUCTION_SHADOW_PRIORITY_OWNER_VERSION,
        "status": status,
        "failure_code": "",
        "invocation_attempted": True,
        "invocation_completed": True,
        "invocation_count": 1,
        "invocation_latency_ms": latency_ms,
        "rendered_priority_facts": deepcopy(bounded),
        "direct_owner_parity": deepcopy(parity),
    }
