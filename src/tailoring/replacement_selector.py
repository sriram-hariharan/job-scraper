from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from src.config.consts import (
    _BAD_COUNTERFACTUAL_STATUSES,
    _DIRECT_APPLY_READY_MATERIALITY_STATUSES,
    _DIRECT_APPLY_OPTIONAL_MATERIALITY_STATUSES,
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        key = _text(item)
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered


def _candidate_confidence_rank(candidate: Dict[str, Any]) -> int:
    confidence = _text(candidate.get("confidence", "")).lower()
    if confidence == "high":
        return 3
    if confidence == "medium":
        return 2
    if confidence == "low":
        return 1
    return 0


def _candidate_materiality_rank(candidate: Dict[str, Any]) -> int:
    status = _text(candidate.get("materiality_validation_status", ""))
    if status == "material_candidate":
        return 3
    if status == "export_safe_no_score_lift":
        return 2
    if status == "scorer_neutral_no_evidence_change":
        return 1
    return 0


def _candidate_delta_rank(candidate: Dict[str, Any]) -> float:
    value = candidate.get("projected_overall_delta", None)
    try:
        if value is None:
            return -999.0
        return float(value)
    except Exception:
        return -999.0


def _rewrite_candidate_sort_key(candidate: Dict[str, Any]) -> Tuple:
    proposal_status = _text(candidate.get("proposal_status", ""))
    patch_ready = 1 if proposal_status == "patch_ready" and _text(candidate.get("patch_text", "")) else 0
    llm_used = 1 if bool(candidate.get("llm_refinement_used", False)) else 0

    return (
        patch_ready,
        _candidate_materiality_rank(candidate),
        _candidate_confidence_rank(candidate),
        llm_used,
        _candidate_delta_rank(candidate),
        len(_text(candidate.get("patch_text", ""))),
    )


def _passes_direct_apply_safety(candidate: Dict[str, Any]) -> bool:
    if _text(candidate.get("operation_type", "")) != "rewrite":
        return False
    if _text(candidate.get("proposal_status", "")) != "patch_ready":
        return False
    if not _text(candidate.get("patch_text", "")):
        return False

    if list(candidate.get("unsupported_risk_signals", []) or []):
        return False

    counterfactual_status = _text(candidate.get("counterfactual_status", ""))
    if counterfactual_status in _BAD_COUNTERFACTUAL_STATUSES:
        return False

    return True


def _is_direct_apply_ready(candidate: Dict[str, Any]) -> bool:
    if not _passes_direct_apply_safety(candidate):
        return False

    materiality_status = _text(candidate.get("materiality_validation_status", ""))
    return materiality_status in _DIRECT_APPLY_READY_MATERIALITY_STATUSES


def _is_direct_apply_optional(candidate: Dict[str, Any]) -> bool:
    if not _passes_direct_apply_safety(candidate):
        return False

    materiality_status = _text(candidate.get("materiality_validation_status", ""))
    if materiality_status not in _DIRECT_APPLY_OPTIONAL_MATERIALITY_STATUSES:
        return False

    return _candidate_confidence_rank(candidate) >= 2


def _apply_priority(candidate: Dict[str, Any]) -> str:
    materiality_status = _text(candidate.get("materiality_validation_status", ""))
    confidence_rank = _candidate_confidence_rank(candidate)

    if materiality_status == "material_candidate":
        return "high"
    if materiality_status == "export_safe_no_score_lift" and confidence_rank >= 2:
        return "medium"
    return "low"


def _replacement_source(candidate: Dict[str, Any]) -> str:
    if bool(candidate.get("llm_refinement_used", False)):
        return "deterministic_plus_llm"
    return "deterministic"


def _card_lookup(edit_cards: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}

    for card in edit_cards or []:
        bullet_id = _text(card.get("bullet_id", ""))
        if not bullet_id:
            continue

        existing = lookup.get(bullet_id)
        rank = (
            1 if _text(card.get("replacement_candidate_id", "")) else 0,
            1 if _text(card.get("patch_generation_method", "")) else 0,
            len(_text(card.get("recommended_rewrite", ""))),
        )

        if existing is None:
            lookup[bullet_id] = dict(card)
            lookup[bullet_id]["_rank"] = rank
            continue

        if rank > tuple(existing.get("_rank", (0, 0, 0))):
            lookup[bullet_id] = dict(card)
            lookup[bullet_id]["_rank"] = rank

    for item in lookup.values():
        item.pop("_rank", None)

    return lookup


def _group_rewrite_candidates(
    replacement_candidates: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for candidate in replacement_candidates or []:
        if _text(candidate.get("operation_type", "")) != "rewrite":
            continue

        bullet_id = _text(candidate.get("source_bullet_id", ""))
        if not bullet_id:
            continue

        grouped.setdefault(bullet_id, []).append(candidate)

    return grouped


def build_final_replacement_plan(
    replacement_candidates: List[Dict[str, Any]],
    edit_cards: List[Dict[str, Any]],
) -> Dict[str, Any]:
    card_by_bullet_id = _card_lookup(edit_cards)
    candidates_by_bullet_id = _group_rewrite_candidates(replacement_candidates)

    decisions: List[Dict[str, Any]] = []

    for bullet_id, grouped_candidates in candidates_by_bullet_id.items():
        ordered_candidates = sorted(
            grouped_candidates,
            key=_rewrite_candidate_sort_key,
            reverse=True,
        )
        best_candidate = ordered_candidates[0]
        card = card_by_bullet_id.get(bullet_id, {})

        original_text = _text(best_candidate.get("original_text", "")) or _text(card.get("current_evidence", ""))
        rewrite_direction = _text(best_candidate.get("rewrite_instruction", "")) or _text(card.get("recommended_rewrite", ""))

        if _is_direct_apply_ready(best_candidate):
            decisions.append(
                {
                    "decision_id": f"final_replacement:{bullet_id}",
                    "replacement_status": "direct_apply_ready",
                    "apply_priority": _apply_priority(best_candidate),
                    "source_bullet_id": bullet_id,
                    "source_entry_id": _text(best_candidate.get("source_entry_id", "")),
                    "section": _text(best_candidate.get("section", "")),
                    "source": _text(best_candidate.get("source", "")),
                    "replacement_candidate_id": _text(best_candidate.get("candidate_id", "")),
                    "replacement_source": _replacement_source(best_candidate),
                    "patch_generation_method": _text(best_candidate.get("patch_generation_method", "")),
                    "materiality_validation_status": _text(best_candidate.get("materiality_validation_status", "")),
                    "projected_overall_delta": best_candidate.get("projected_overall_delta", None),
                    "confidence": _text(best_candidate.get("confidence", "")),
                    "original_text": original_text,
                    "final_replacement_text": _text(best_candidate.get("patch_text", "")),
                    "rewrite_direction": rewrite_direction,
                    "why_selected": _text(best_candidate.get("why_this_improves_match", "")),
                    "adjacent_risk_signals": list(best_candidate.get("adjacent_risk_signals", []) or []),
                    "unsupported_risk_signals": list(best_candidate.get("unsupported_risk_signals", []) or []),
                    "likely_impacted_dimensions": list(best_candidate.get("likely_impacted_dimensions", []) or []),
                }
            )
            continue

        if _is_direct_apply_optional(best_candidate):
            decisions.append(
                {
                    "decision_id": f"final_replacement:{bullet_id}",
                    "replacement_status": "direct_apply_optional",
                    "apply_priority": _apply_priority(best_candidate),
                    "source_bullet_id": bullet_id,
                    "source_entry_id": _text(best_candidate.get("source_entry_id", "")),
                    "section": _text(best_candidate.get("section", "")),
                    "source": _text(best_candidate.get("source", "")),
                    "replacement_candidate_id": _text(best_candidate.get("candidate_id", "")),
                    "replacement_source": _replacement_source(best_candidate),
                    "patch_generation_method": _text(best_candidate.get("patch_generation_method", "")),
                    "materiality_validation_status": _text(best_candidate.get("materiality_validation_status", "")),
                    "projected_overall_delta": best_candidate.get("projected_overall_delta", None),
                    "confidence": _text(best_candidate.get("confidence", "")),
                    "original_text": original_text,
                    "final_replacement_text": _text(best_candidate.get("patch_text", "")),
                    "rewrite_direction": rewrite_direction,
                    "why_selected": _text(best_candidate.get("why_this_improves_match", "")),
                    "adjacent_risk_signals": list(best_candidate.get("adjacent_risk_signals", []) or []),
                    "unsupported_risk_signals": list(best_candidate.get("unsupported_risk_signals", []) or []),
                    "likely_impacted_dimensions": list(best_candidate.get("likely_impacted_dimensions", []) or []),
                }
            )
            continue

        if rewrite_direction:
            decisions.append(
                {
                    "decision_id": f"final_replacement:{bullet_id}",
                    "replacement_status": "direction_only",
                    "apply_priority": _apply_priority(best_candidate),
                    "source_bullet_id": bullet_id,
                    "source_entry_id": _text(best_candidate.get("source_entry_id", "")),
                    "section": _text(best_candidate.get("section", "")),
                    "source": _text(best_candidate.get("source", "")),
                    "replacement_candidate_id": _text(best_candidate.get("candidate_id", "")),
                    "replacement_source": _replacement_source(best_candidate),
                    "patch_generation_method": _text(best_candidate.get("patch_generation_method", "")),
                    "materiality_validation_status": _text(best_candidate.get("materiality_validation_status", "")),
                    "projected_overall_delta": best_candidate.get("projected_overall_delta", None),
                    "confidence": _text(best_candidate.get("confidence", "")),
                    "original_text": original_text,
                    "final_replacement_text": "",
                    "rewrite_direction": rewrite_direction,
                    "why_selected": _text(best_candidate.get("why_this_improves_match", "")),
                    "adjacent_risk_signals": list(best_candidate.get("adjacent_risk_signals", []) or []),
                    "unsupported_risk_signals": list(best_candidate.get("unsupported_risk_signals", []) or []),
                    "likely_impacted_dimensions": list(best_candidate.get("likely_impacted_dimensions", []) or []),
                }
            )
            continue

        decisions.append(
            {
                "decision_id": f"final_replacement:{bullet_id}",
                "replacement_status": "keep_original",
                "apply_priority": "low",
                "source_bullet_id": bullet_id,
                "source_entry_id": _text(best_candidate.get("source_entry_id", "")),
                "section": _text(best_candidate.get("section", "")),
                "source": _text(best_candidate.get("source", "")),
                "replacement_candidate_id": _text(best_candidate.get("candidate_id", "")),
                "replacement_source": _replacement_source(best_candidate),
                "patch_generation_method": _text(best_candidate.get("patch_generation_method", "")),
                "materiality_validation_status": _text(best_candidate.get("materiality_validation_status", "")),
                "projected_overall_delta": best_candidate.get("projected_overall_delta", None),
                "confidence": _text(best_candidate.get("confidence", "")),
                "original_text": original_text,
                "final_replacement_text": "",
                "rewrite_direction": "",
                "why_selected": "No safe stronger direct replacement survived final deterministic selection.",
                "adjacent_risk_signals": list(best_candidate.get("adjacent_risk_signals", []) or []),
                "unsupported_risk_signals": list(best_candidate.get("unsupported_risk_signals", []) or []),
                "likely_impacted_dimensions": list(best_candidate.get("likely_impacted_dimensions", []) or []),
            }
        )

    decisions = sorted(
        decisions,
        key=lambda item: (
            3 if _text(item.get("replacement_status", "")) == "direct_apply_ready"
            else 2 if _text(item.get("replacement_status", "")) == "direct_apply_optional"
            else 1 if _text(item.get("replacement_status", "")) == "direction_only"
            else 0,
            1 if _text(item.get("apply_priority", "")) == "high" else 0,
            1 if _text(item.get("apply_priority", "")) == "medium" else 0,
            len(_text(item.get("final_replacement_text", ""))),
        ),
        reverse=True,
    )

    app_ready_replacements = [
        row for row in decisions
        if _text(row.get("replacement_status", "")) == "direct_apply_ready"
    ]
    direct_apply_optional_replacements = [
        row for row in decisions
        if _text(row.get("replacement_status", "")) == "direct_apply_optional"
    ]
    direction_only_replacements = [
        row for row in decisions
        if _text(row.get("replacement_status", "")) == "direction_only"
    ]

    summary = {
        "total_rewrite_bullets": len(decisions),
        "direct_apply_ready_count": len(app_ready_replacements),
        "direct_apply_optional_count": len(direct_apply_optional_replacements),
        "direction_only_count": len(direction_only_replacements),
        "keep_original_count": len(
            [row for row in decisions if _text(row.get("replacement_status", "")) == "keep_original"]
        ),
        "selected_candidate_ids": _unique_preserve_order(
            [_text(row.get("replacement_candidate_id", "")) for row in app_ready_replacements]
        ),
        "optional_candidate_ids": _unique_preserve_order(
            [_text(row.get("replacement_candidate_id", "")) for row in direct_apply_optional_replacements]
        ),
    }

    return {
        "decisions": decisions,
        "app_ready_replacements": app_ready_replacements,
        "direct_apply_optional_replacements": direct_apply_optional_replacements,
        "direction_only_replacements": direction_only_replacements,
        "summary": summary,
    }