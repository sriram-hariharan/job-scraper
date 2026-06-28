"""Default-off deterministic JD signal to resume evidence matrix builder."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any


PHASE = "35A"
LIST_SIGNAL_FIELDS = (
    "required_skills",
    "preferred_skills",
    "responsibilities",
    "tools",
    "location_constraints",
    "visa_constraints",
    "resume_evidence_needed",
    "red_flags",
)
TEXT_SIGNAL_FIELDS = ("domain", "seniority")
RESUME_DICT_FIELDS = (
    "resume_text",
    "summary",
    "skills",
    "projects",
    "experience",
    "tools",
    "domains",
    "certifications",
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    minimum = supplied.get("minimum_token_length", 2)
    try:
        minimum_int = int(minimum)
    except (TypeError, ValueError):
        minimum_int = 2
    return {
        "case_sensitive": bool(supplied.get("case_sensitive", False)),
        "minimum_token_length": max(1, minimum_int),
        "include_partial_matches": supplied.get("include_partial_matches", True)
        is not False,
    }


def _list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return _unique(_text(item) for item in value)
    if isinstance(value, dict):
        return _unique(_text(item) for item in value.values())
    text = _text(value)
    return [text] if text else []


def _unique(values: Any) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        cleaned = _text(value)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(cleaned)
    return ordered


def _normalize_for_search(value: str, *, case_sensitive: bool) -> str:
    text = _text(value)
    if not case_sensitive:
        text = text.lower()
    return re.sub(r"\s+", " ", text).strip()


def _tokens(value: str, *, policy: dict[str, Any]) -> set[str]:
    normalized = _normalize_for_search(
        value,
        case_sensitive=bool(policy["case_sensitive"]),
    )
    minimum = int(policy["minimum_token_length"])
    return {
        token
        for token in re.split(r"[^A-Za-z0-9+#/.-]+", normalized)
        if len(token) >= minimum
    }


def _normalized_signals(jd_signals: dict[str, Any]) -> dict[str, Any]:
    normalized = {field: _list(jd_signals.get(field)) for field in LIST_SIGNAL_FIELDS}
    for field in TEXT_SIGNAL_FIELDS:
        normalized[field] = _list(jd_signals.get(field))
    return normalized


def _flatten_resume_evidence(value: Any) -> list[dict[str, Any]]:
    snippets: list[dict[str, Any]] = []

    def add(source: str, item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                add(f"{source}.{key}", nested)
            return
        if isinstance(item, (list, tuple, set)):
            for index, nested in enumerate(item):
                add(f"{source}.{index}", nested)
            return
        text = _text(item)
        if text:
            snippets.append(
                {
                    "source": source,
                    "text": text,
                }
            )

    if isinstance(value, dict):
        for field in RESUME_DICT_FIELDS:
            if field in value:
                add(field, value[field])
        for key, item in value.items():
            if key not in RESUME_DICT_FIELDS:
                add(str(key), item)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            add(f"list.{index}", item)
    else:
        add("resume_text", value)

    return snippets


def _match_term(
    term: str,
    snippets: list[dict[str, Any]],
    *,
    policy: dict[str, Any],
) -> dict[str, Any]:
    case_sensitive = bool(policy["case_sensitive"])
    normalized_term = _normalize_for_search(term, case_sensitive=case_sensitive)
    term_tokens = _tokens(term, policy=policy)
    exact: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []

    for snippet in snippets:
        text = str(snippet["text"])
        normalized_text = _normalize_for_search(text, case_sensitive=case_sensitive)
        if normalized_term and normalized_term in normalized_text:
            exact.append(deepcopy(snippet))
            continue
        if policy["include_partial_matches"] and term_tokens:
            snippet_tokens = _tokens(text, policy=policy)
            overlaps = sorted(term_tokens & snippet_tokens)
            if overlaps:
                found = deepcopy(snippet)
                found["matched_tokens"] = overlaps
                partial.append(found)

    status = "matched" if exact or partial else "missing"
    return {
        "signal": term,
        "status": status,
        "match_type": "exact" if exact else ("partial" if partial else "none"),
        "evidence": exact or partial,
    }


def _field_matrix(
    field: str,
    terms: list[str],
    snippets: list[dict[str, Any]],
    *,
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "field": field,
            **_match_term(term, snippets, policy=policy),
        }
        for term in terms
    ]


def _matched(matrix: list[dict[str, Any]]) -> list[str]:
    return [row["signal"] for row in matrix if row["status"] == "matched"]


def _missing(matrix: list[dict[str, Any]]) -> list[str]:
    return [row["signal"] for row in matrix if row["status"] == "missing"]


def _ratio(matched: list[str], missing: list[str]) -> float:
    total = len(matched) + len(missing)
    return round(len(matched) / total, 6) if total else 0.0


def _matrix_key(*, ready: bool, required_ratio: float, preferred_ratio: float) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"ready={ready}",
            f"required={required_ratio:.6f}",
            f"preferred={preferred_ratio:.6f}",
        )
    )


def build_jd_signal_resume_evidence_matrix_default_off(
    jd_signals: dict[str, Any] | None = None,
    resume_evidence: Any = None,
    evidence_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare supplied JD signals with resume/profile evidence without scoring."""

    policy = _policy(evidence_policy)
    missing_inputs: list[str] = []
    blocked_reasons: list[str] = []

    if not isinstance(jd_signals, dict):
        missing_inputs.append("jd_signals")
        blocked_reasons.append("jd_signals must be supplied as a dictionary")
        safe_signals: dict[str, Any] = {}
    else:
        safe_signals = deepcopy(jd_signals)

    snippets = _flatten_resume_evidence(resume_evidence)
    if not snippets:
        missing_inputs.append("resume_evidence")
        blocked_reasons.append("resume_evidence must include searchable text")

    normalized_signals = _normalized_signals(safe_signals)
    evidence_ready = not missing_inputs
    matrix: dict[str, list[dict[str, Any]]] = {}
    for field in (
        "required_skills",
        "preferred_skills",
        "tools",
        "responsibilities",
        "domain",
        "seniority",
        "location_constraints",
        "visa_constraints",
        "resume_evidence_needed",
        "red_flags",
    ):
        matrix[field] = _field_matrix(
            field,
            normalized_signals.get(field, []),
            snippets,
            policy=policy,
        )

    matched_required = _matched(matrix["required_skills"])
    missing_required = _missing(matrix["required_skills"])
    matched_preferred = _matched(matrix["preferred_skills"])
    missing_preferred = _missing(matrix["preferred_skills"])
    matched_tools = _matched(matrix["tools"])
    missing_tools = _missing(matrix["tools"])
    matched_responsibilities = _matched(matrix["responsibilities"])
    missing_responsibilities = _missing(matrix["responsibilities"])
    matched_domains = _matched(matrix["domain"])
    missing_domains = _missing(matrix["domain"])
    matched_needed = _matched(matrix["resume_evidence_needed"])
    missing_needed = _missing(matrix["resume_evidence_needed"])

    required_ratio = _ratio(matched_required, missing_required)
    preferred_ratio = _ratio(matched_preferred, missing_preferred)
    tool_ratio = _ratio(matched_tools, missing_tools)
    responsibility_ratio = _ratio(matched_responsibilities, missing_responsibilities)

    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_signal_resume_evidence_matrix": True,
        "read_only": True,
        "advisory_only": True,
        "deterministic_evidence_matching": True,
        "requires_manual_user_control": True,
        "jd_signals_present": isinstance(jd_signals, dict) and bool(jd_signals),
        "resume_evidence_present": bool(snippets),
        "evidence_policy": deepcopy(policy),
        "normalized_jd_signals": deepcopy(normalized_signals),
        "normalized_resume_evidence": deepcopy(snippets),
        "evidence_matrix": deepcopy(matrix),
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "matched_tools": matched_tools,
        "missing_tools": missing_tools,
        "matched_responsibilities": matched_responsibilities,
        "missing_responsibilities": missing_responsibilities,
        "matched_domains": matched_domains,
        "missing_domains": missing_domains,
        "matched_resume_evidence_needed": matched_needed,
        "missing_resume_evidence_needed": missing_needed,
        "red_flag_findings": deepcopy(matrix["red_flags"]),
        "coverage_summary": {
            "required_skill_total": len(matched_required) + len(missing_required),
            "preferred_skill_total": len(matched_preferred) + len(missing_preferred),
            "tool_total": len(matched_tools) + len(missing_tools),
            "responsibility_total": len(matched_responsibilities)
            + len(missing_responsibilities),
            "domain_total": len(matched_domains) + len(missing_domains),
            "resume_evidence_needed_total": len(matched_needed) + len(missing_needed),
            "final_application_score_created": False,
            "existing_score_changed": False,
        },
        "required_skill_coverage_ratio": required_ratio,
        "preferred_skill_coverage_ratio": preferred_ratio,
        "tool_coverage_ratio": tool_ratio,
        "responsibility_coverage_ratio": responsibility_ratio,
        "evidence_ready": evidence_ready,
        "missing_inputs": missing_inputs,
        "blocked_reasons": blocked_reasons,
        "evidence_findings": {
            "searchable_snippet_count": len(snippets),
            "deterministic_matching_only": True,
            "final_scoring_performed": False,
            "existing_score_changed": False,
        },
        "evidence_matrix_key": _matrix_key(
            ready=evidence_ready,
            required_ratio=required_ratio,
            preferred_ratio=preferred_ratio,
        ),
        "llm_call_performed": False,
        "provider_call_performed": False,
        "network_call_performed": False,
        "stage_execution_performed": False,
        "relevance_prefilter_performed": False,
        "jd_intelligence_extraction_performed": False,
        "final_scoring_performed": False,
        "tailoring_opportunity_check_performed": False,
        "tailoring_runtime_call_performed": False,
        "ai_tailoring_generation_performed": False,
        "real_tailoring_output_created": False,
        "resume_rewrite_performed": False,
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
        "database_write_performed": False,
        "persistence_performed": False,
        "execution_performed": False,
        "submission_performed": False,
        "auto_apply_performed": False,
        "auto_submit_performed": False,
    }
    return payload
