"""Deterministic diagnostics for active TS clearance hard requirements."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re


_NEGATED_REQUIREMENT_PATTERNS = (
    re.compile(
        r"\b(?:ability|able|eligible|eligibility)\s+to\s+(?:obtain|receive|hold|maintain)\b"
        r".{0,80}\b(?:clearance|ts|top\s+secret|ts/sci|sci)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:obtain|receive|hold|maintain)\b.{0,60}\b(?:clearance|ts|top\s+secret|ts/sci|sci)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:preferred|nice\s+to\s+have|bonus|plus)\b.{0,80}"
        r"\b(?:clearance|ts|top\s+secret|ts/sci|sci)\b",
        re.IGNORECASE,
    ),
)

_ACTIVE_TS_REQUIREMENT_PATTERNS = (
    re.compile(
        r"\b(?:active|current)\s+(?:ts|top\s+secret|ts/sci|ts\s+sci)\b"
        r".{0,50}\b(?:clearance|required|requirement|must|needed|eligible)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:ts/sci|ts\s+sci|top\s+secret|ts)\b.{0,50}"
        r"\b(?:clearance|required|requirement|must|needed)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:must|requires?|required|requirement|need(?:ed)?|possess|have)\b"
        r".{0,80}\b(?:active|current)\s+(?:ts|top\s+secret|ts/sci|ts\s+sci)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:must|requires?|required|requirement|need(?:ed)?|possess|have)\b"
        r".{0,80}\b(?:active|current)\s+security\s+clearance\b"
        r".{0,80}\b(?:ts|top\s+secret|ts/sci|ts\s+sci)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:active|current)\s+security\s+clearance\b"
        r".{0,80}\b(?:ts|top\s+secret|ts/sci|ts\s+sci)\b",
        re.IGNORECASE,
    ),
)

_ACTIVE_TS_RESUME_PATTERNS = (
    re.compile(
        r"\b(?:active|current)\s+(?:ts|top\s+secret|ts/sci|ts\s+sci)\b"
        r".{0,50}\bclearance\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bts/sci\b", re.IGNORECASE),
    re.compile(
        r"\b(?:active|current)\s+security\s+clearance\b"
        r".{0,80}\b(?:ts|top\s+secret|ts/sci|ts\s+sci)\b",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class ClearanceRequirementDiagnostic:
    code: str
    severity: str
    requirement: str
    message: str
    score_cap_applied: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalize_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def requires_active_ts_clearance(job_text: str | None) -> bool:
    """Return true only for explicit active/current TS-style requirements."""
    text = _normalize_text(job_text)
    if not text:
        return False
    if any(pattern.search(text) for pattern in _NEGATED_REQUIREMENT_PATTERNS):
        return False
    return any(pattern.search(text) for pattern in _ACTIVE_TS_REQUIREMENT_PATTERNS)


def has_active_ts_clearance_evidence(resume_text: str | None) -> bool:
    """Return true only for explicit active/current TS-style resume evidence."""
    text = _normalize_text(resume_text)
    if not text:
        return False
    return any(pattern.search(text) for pattern in _ACTIVE_TS_RESUME_PATTERNS)


def active_ts_clearance_diagnostic(
    job_text: str | None,
    resume_text: str | None,
) -> dict[str, object] | None:
    """Return a diagnostic when an active TS requirement is unmet."""
    if not requires_active_ts_clearance(job_text):
        return None
    if has_active_ts_clearance_evidence(resume_text):
        return None
    return ClearanceRequirementDiagnostic(
        code="missing_active_ts_clearance",
        severity="hard_requirement_gap",
        requirement="active_ts_clearance",
        message="Active TS clearance is required but was not found in this resume.",
        score_cap_applied=False,
    ).to_dict()
