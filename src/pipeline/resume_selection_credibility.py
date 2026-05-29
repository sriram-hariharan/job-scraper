from __future__ import annotations

from typing import Any, Dict

from src.config.settings import SCORER_V2_POLICY


SHORTLIST_POLICY = SCORER_V2_POLICY["shortlist"]
CREDIBLE_DETERMINISTIC_SCORE = float(SHORTLIST_POLICY["borderline_score"])

FALLBACK_ONLY_WARNING = (
    "Fallback suggested a resume, but deterministic scorer found no credible match."
)
LOW_CONFIDENCE_WARNING = (
    "Fallback suggestion has low deterministic support; review before using."
)

CREDIBILITY_COLUMNS = [
    "deterministic_winner_available",
    "deterministic_winner_score",
    "deterministic_prefilter_passed",
    "fallback_used",
    "fallback_only_no_deterministic_match",
    "fallback_low_confidence",
    "resolved_resume_warning",
    "packet_generation_allowed",
    "packet_generation_block_reason",
]


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def parse_bool(value: Any) -> bool:
    return str(value or "").strip().lower() == "true"


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _first_nonblank(row: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _fallback_used(row: Dict[str, Any]) -> bool:
    source = _first_nonblank(row, "resolved_resume_source")
    status = _first_nonblank(row, "llm_fallback_status")
    best_resume = _first_nonblank(row, "llm_fallback_best_resume")

    if source.startswith("llm_fallback"):
        return True
    return bool(best_resume and status in {"generated", "cached"})


def compute_resume_selection_credibility(row: Dict[str, Any]) -> Dict[str, str]:
    if "selector_winner_resume" in row or "selector_winner_score" in row:
        deterministic_resume = str(row.get("selector_winner_resume", "") or "").strip()
        deterministic_score = parse_float(row.get("selector_winner_score", "0"))
    else:
        deterministic_resume = str(row.get("winner_resume", "") or "").strip()
        deterministic_score = parse_float(row.get("winner_score", "0"))
    deterministic_prefilter_passed = parse_bool(
        _first_nonblank(
            row,
            "deterministic_prefilter_passed",
            "winner_prefilter_passed",
            "resolved_prefilter_passed",
        )
    )
    deterministic_winner_available = bool(
        deterministic_resume and deterministic_score > 0.0
    )
    fallback_used = _fallback_used(row)
    fallback_only = bool(fallback_used and not deterministic_winner_available)
    fallback_low_confidence = bool(
        fallback_used
        and deterministic_winner_available
        and deterministic_score < CREDIBLE_DETERMINISTIC_SCORE
    )

    packet_generation_allowed = bool(
        deterministic_winner_available
        and deterministic_score >= CREDIBLE_DETERMINISTIC_SCORE
        and not fallback_only
    )
    block_reason = ""
    warning = ""
    if fallback_only:
        block_reason = "fallback_only_no_deterministic_match"
        warning = FALLBACK_ONLY_WARNING
    elif deterministic_winner_available and deterministic_score < CREDIBLE_DETERMINISTIC_SCORE:
        block_reason = "deterministic_score_below_credible_threshold"
        if fallback_used:
            warning = LOW_CONFIDENCE_WARNING
    elif not deterministic_winner_available:
        block_reason = "no_deterministic_winner"

    return {
        "deterministic_winner_available": bool_text(deterministic_winner_available),
        "deterministic_winner_score": f"{deterministic_score:.6f}",
        "deterministic_prefilter_passed": bool_text(deterministic_prefilter_passed),
        "fallback_used": bool_text(fallback_used),
        "fallback_only_no_deterministic_match": bool_text(fallback_only),
        "fallback_low_confidence": bool_text(fallback_low_confidence),
        "resolved_resume_warning": warning,
        "packet_generation_allowed": bool_text(packet_generation_allowed),
        "packet_generation_block_reason": block_reason,
    }
