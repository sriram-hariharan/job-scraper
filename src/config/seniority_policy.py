from __future__ import annotations

import re
from typing import Any, List, Tuple


PUBLIC_SENIORITY_IDS: Tuple[str, ...] = (
    "entry",
    "mid",
    "senior",
    "staff",
)

SENIORITY_CLASSIFICATION_OUTCOMES: Tuple[str, ...] = (
    "intern",
    "entry",
    "mid",
    "senior",
    "staff",
    "manager_or_above",
    "unknown",
)

DEFAULT_PREFILTER_ELIGIBLE_SENIORITY_OUTCOMES: Tuple[str, ...] = (
    "entry",
    "mid",
    "senior",
    "staff",
    "unknown",
)

DEFAULT_PREFILTER_REJECTED_SENIORITY_OUTCOMES: Tuple[str, ...] = (
    "intern",
    "manager_or_above",
)

_LEGACY_TARGET_SENIORITY_ALIASES = {
    "staff_or_above": "staff",
}

_WHITESPACE_REGEX = re.compile(r"\s+")
_PUNCTUATION_REGEX = re.compile(r"[^\w\s]")
_EXECUTIVE_REGEX = re.compile(r"\b(?:director|vp|vice president)\b|\bhead of\b", re.I)
_PEOPLE_MANAGER_REGEX = re.compile(r"\bmanager\b", re.I)
_INTERN_REGEX = re.compile(r"\b(?:intern|internship|student)\b", re.I)
_STAFF_REGEX = re.compile(
    r"\b(?:staff|principal|lead|member of technical staff|mts)\b",
    re.I,
)
_SENIOR_REGEX = re.compile(r"\b(?:senior|sr)\b", re.I)
_ENTRY_REGEX = re.compile(
    r"\b(?:entry|junior|jr|new grad|graduate|associate)\b",
    re.I,
)
_MID_REGEX = re.compile(
    r"\b(?:mid|software engineer ii|engineer ii|level 2)\b",
    re.I,
)


def _target_values(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, set):
        return sorted(value, key=lambda item: str(item or ""))
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def normalize_target_seniority_ids(value: Any) -> List[str]:
    normalized: List[str] = []
    unsupported: List[str] = []

    for item in _target_values(value):
        candidate = _WHITESPACE_REGEX.sub(
            " ",
            str(item or "").strip().lower(),
        )
        if not candidate:
            continue
        canonical = _LEGACY_TARGET_SENIORITY_ALIASES.get(candidate, candidate)
        if canonical not in PUBLIC_SENIORITY_IDS:
            if candidate not in unsupported:
                unsupported.append(candidate)
            continue
        if canonical not in normalized:
            normalized.append(canonical)

    if unsupported:
        allowed = ", ".join(PUBLIC_SENIORITY_IDS)
        raise ValueError(
            "Unsupported target seniority value(s): "
            f"{', '.join(unsupported)}. Allowed: {allowed}."
        )

    return normalized


def normalize_seniority_filter_preferences(
    target_seniority: Any,
    seniority_strict_match: Any = False,
) -> Tuple[List[str], bool]:
    if not isinstance(seniority_strict_match, bool):
        raise ValueError("seniority_strict_match must be a boolean")
    normalized_targets = normalize_target_seniority_ids(target_seniority)
    if seniority_strict_match and not normalized_targets:
        raise ValueError(
            "target_seniority must contain at least one value when "
            "seniority_strict_match is enabled"
        )
    return normalized_targets, seniority_strict_match


def classify_title_seniority(
    title: Any,
    *,
    technical_management_role: bool = False,
) -> str:
    text = _WHITESPACE_REGEX.sub(
        " ",
        _PUNCTUATION_REGEX.sub(" ", str(title or "").lower()),
    ).strip()

    if _EXECUTIVE_REGEX.search(text):
        return "manager_or_above"
    if not technical_management_role and _PEOPLE_MANAGER_REGEX.search(text):
        return "manager_or_above"
    if _INTERN_REGEX.search(text):
        return "intern"
    if _STAFF_REGEX.search(text):
        return "staff"
    if _SENIOR_REGEX.search(text):
        return "senior"
    if _ENTRY_REGEX.search(text):
        return "entry"
    if _MID_REGEX.search(text):
        return "mid"
    return "unknown"


def default_prefilter_seniority_is_eligible(classification: Any) -> bool:
    return str(classification or "").strip().lower() in (
        DEFAULT_PREFILTER_ELIGIBLE_SENIORITY_OUTCOMES
    )


def seniority_prefilter_decision(
    classification: Any,
    *,
    target_seniority: Any = None,
    seniority_strict_match: Any = False,
):
    targets, strict_match = normalize_seniority_filter_preferences(
        target_seniority,
        seniority_strict_match,
    )
    outcome = str(classification or "unknown").strip().lower()
    if outcome == "intern":
        return {"eligible": False, "decision": "reject", "reason": "intern_rejected"}
    if outcome == "manager_or_above":
        return {
            "eligible": False,
            "decision": "reject",
            "reason": "manager_or_above_rejected",
        }
    if not strict_match:
        eligible = outcome in DEFAULT_PREFILTER_ELIGIBLE_SENIORITY_OUTCOMES
        return {
            "eligible": eligible,
            "decision": "allow" if eligible else "reject",
            "reason": "flexible_level_allowed",
        }
    if outcome == "unknown":
        return {
            "eligible": False,
            "decision": "reject",
            "reason": "strict_unknown_rejected",
        }
    if outcome in targets:
        return {
            "eligible": True,
            "decision": "allow",
            "reason": "strict_selected_level_match",
        }
    return {
        "eligible": False,
        "decision": "reject",
        "reason": "strict_selected_level_mismatch",
    }
