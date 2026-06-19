"""Deterministic, default-off quality gate for semantic evidence."""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any


QUALITY_GATE_VERSION = "phase-9i-semantic-evidence-quality-gate-v1"

STATUS_SKIPPED = "semantic_evidence_quality_gate_skipped_default_off"
STATUS_PASSED = "evidence_quality_passed"
STATUS_FAILED = "evidence_quality_failed"
STATUS_PARTIAL = "evidence_quality_partial"


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _score(item: dict[str, Any]) -> float | None:
    for key in ("retrieval_score", "similarity_score", "score"):
        value = item.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        score = float(value)
        if math.isfinite(score):
            return score
    return None


def semantic_evidence_quality_gate_safety_metadata(
    *,
    enabled: bool = False,
    passed: bool = False,
    attached: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "semantic_evidence_quality_gate": True,
        "semantic_evidence_quality_gate_enabled": bool(enabled),
        "semantic_evidence_quality_passed": bool(passed),
        "semantic_evidence_attached": bool(attached),
        "semantic_evidence_used_for_scoring": False,
        "semantic_evidence_used_for_ranking": False,
        "semantic_evidence_used_for_queue": False,
        "semantic_evidence_used_for_application": False,
        "provider_calls_made": False,
        "embeddings_created": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "api_route_added": False,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
    }


def run_semantic_evidence_quality_gate(
    *,
    enabled: bool = False,
    evidence_items: list[dict[str, Any]] | None = None,
    minimum_similarity_score: float = 0.75,
    minimum_evidence_count: int = 1,
    max_evidence_count: int = 5,
) -> dict[str, Any]:
    """Filter and assess semantic evidence without external side effects."""

    source_items = deepcopy(evidence_items) if isinstance(evidence_items, list) else []
    minimum_count = _positive_int(minimum_evidence_count, default=1)
    maximum_count = _positive_int(max_evidence_count, default=5)
    try:
        minimum_score = float(minimum_similarity_score)
    except (TypeError, ValueError):
        minimum_score = 0.75
    if not math.isfinite(minimum_score):
        minimum_score = 0.75

    payload = {
        "quality_gate_version": QUALITY_GATE_VERSION,
        "status": STATUS_SKIPPED,
        "default_off": True,
        "semantic_evidence_quality_gate_enabled": enabled is True,
        "semantic_evidence_quality_passed": False,
        "semantic_evidence_attached": False,
        "minimum_similarity_score": minimum_score,
        "minimum_evidence_count": minimum_count,
        "max_evidence_count": maximum_count,
        "input_count": len(source_items),
        "valid_count": 0,
        "filtered_count": 0,
        "duplicate_count": 0,
        "capped_count": 0,
        "quality_evidence": [],
        "rejected_reasons": [],
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "safety_metadata": semantic_evidence_quality_gate_safety_metadata(),
    }
    if enabled is not True:
        return payload

    quality_items: list[dict[str, Any]] = []
    rejected_reasons: list[str] = []
    seen: set[tuple[str, str, str, str]] = set()
    duplicate_count = 0
    for source in source_items:
        if not isinstance(source, dict):
            rejected_reasons.append("evidence_item_must_be_object")
            continue
        evidence_text = _clean_text(
            source.get("evidence_text") or source.get("text")
        )
        title = _clean_text(source.get("title"))
        source_name = _clean_text(
            source.get("source")
            or source.get("source_type")
            or source.get("source_id")
        )
        chunk_id = _clean_text(source.get("chunk_id"))
        if not (evidence_text or title or source_name):
            rejected_reasons.append("evidence_content_required")
            continue
        score = _score(source)
        if score is None:
            rejected_reasons.append("similarity_score_required")
            continue
        if score < minimum_score:
            rejected_reasons.append("similarity_below_minimum")
            continue
        duplicate_key = (
            evidence_text.lower(),
            title.lower(),
            source_name.lower(),
            chunk_id.lower(),
        )
        if duplicate_key in seen:
            duplicate_count += 1
            rejected_reasons.append("duplicate_evidence")
            continue
        seen.add(duplicate_key)
        item = deepcopy(source)
        item["retrieval_score"] = score
        if evidence_text:
            item["evidence_text"] = evidence_text
        if title:
            item["title"] = title
        if source_name:
            item["source"] = source_name
        quality_items.append(item)

    quality_items.sort(
        key=lambda item: (
            -float(item.get("retrieval_score", 0.0)),
            _clean_text(item.get("chunk_id")),
            _clean_text(item.get("evidence_text")),
        )
    )
    uncapped_count = len(quality_items)
    quality_items = quality_items[:maximum_count]
    capped_count = max(uncapped_count - len(quality_items), 0)
    passed = len(quality_items) >= minimum_count
    status = STATUS_PASSED if passed else (
        STATUS_PARTIAL if quality_items else STATUS_FAILED
    )
    payload.update(
        {
            "status": status,
            "semantic_evidence_quality_passed": passed,
            "semantic_evidence_attached": passed,
            "valid_count": len(quality_items),
            "filtered_count": len(source_items) - uncapped_count,
            "duplicate_count": duplicate_count,
            "capped_count": capped_count,
            "quality_evidence": quality_items,
            "rejected_reasons": rejected_reasons,
            "safety_metadata": semantic_evidence_quality_gate_safety_metadata(
                enabled=True,
                passed=passed,
                attached=passed,
            ),
        }
    )
    return payload
