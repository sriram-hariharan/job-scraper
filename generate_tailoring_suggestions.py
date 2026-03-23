import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib
from datetime import datetime, timezone
from src.config.consts import (
    REWRITE_DIRECTION_PREFIXES,
)
# from src.ai.llm_client import run_chat_completion
from src.ai.llm_client import (
    FALLBACK_ENABLED as LLM_FALLBACK_ENABLED,
    FALLBACK_MODEL as LLM_FALLBACK_MODEL,
    FALLBACK_PROVIDER as LLM_FALLBACK_PROVIDER,
    run_chat_completion_with_metadata,
)

LLM_TAILOR_PROVIDER = "gemini"
LLM_TAILOR_MODEL = "gemini-2.5-flash"
LLM_TAILOR_MAX_TOKENS = 700
LLM_TAILOR_TEMPERATURE = 0
LLM_TAILOR_PROMPT_VERSION = "v3"

TAILOR_LLM_FALLBACK_ENABLED = (
    os.getenv(
        "TAILOR_LLM_FALLBACK_ENABLED",
        "true" if LLM_FALLBACK_ENABLED else "false",
    ).strip().lower() == "true"
)
TAILOR_LLM_FALLBACK_PROVIDER = os.getenv(
    "TAILOR_LLM_FALLBACK_PROVIDER",
    LLM_FALLBACK_PROVIDER,
).strip().lower()
TAILOR_LLM_FALLBACK_MODEL = os.getenv(
    "TAILOR_LLM_FALLBACK_MODEL",
    LLM_FALLBACK_MODEL,
).strip()

LIVE_REWRITE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "rewrite_directions": {
            "type": "array",
            "items": {"type": "string"},
        }
    },
    "required": ["rewrite_directions"],
}

TAILORING_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "recruiter_summary": {"type": "STRING"},
        "keep_emphasize": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
        "tailoring_actions": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
        "do_not_claim": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
        "rewrite_directions": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
    },
    "required": [
        "recruiter_summary",
        "keep_emphasize",
        "tailoring_actions",
        "do_not_claim",
        "rewrite_directions",
    ],
}

def _load_packet(packet_path: Path) -> Dict[str, Any]:
    if not packet_path.exists():
        raise RuntimeError(f"Missing packet JSON: {packet_path}")

    with packet_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        raise RuntimeError(f"Packet JSON is empty: {packet_path}")

    return data


def _unique_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            ordered.append(cleaned)
    return ordered


def _truncate_list(values: List[str], limit: int) -> List[str]:
    return values[:limit]

def _source_label(row: Dict[str, Any]) -> str:
    source_title = str(row.get("source_title", "") or "").strip()
    source_company = str(row.get("source_company", "") or "").strip()
    return source_title if not source_company else f"{source_title} @ {source_company}"


def _short_bullet(text: str, limit: int = 220) -> str:
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."

def _term_support_rows(packet: Dict[str, Any], bucket: str) -> List[Dict[str, Any]]:
    summary = packet.get("summary", {}) or {}
    term_support = summary.get("term_support", {}) or {}
    rows = term_support.get(bucket, []) or []
    return [row for row in rows if isinstance(row, dict)]


def _terms_by_support_level(rows: List[Dict[str, Any]], *levels: str) -> List[str]:
    level_set = {str(level or "").strip() for level in levels if str(level or "").strip()}
    terms: List[str] = []
    for row in rows:
        if str(row.get("support_level", "")).strip() in level_set:
            term = str(row.get("term", "") or "").strip()
            if term:
                terms.append(term)
    return _unique_preserve_order(terms)


def _direct_terms(packet: Dict[str, Any], bucket: str) -> List[str]:
    return _terms_by_support_level(_term_support_rows(packet, bucket), "direct_bullet")


def _contextual_terms(packet: Dict[str, Any], bucket: str) -> List[str]:
    return _terms_by_support_level(_term_support_rows(packet, bucket), "entry_context")


def _skills_only_terms(packet: Dict[str, Any], bucket: str) -> List[str]:
    return _terms_by_support_level(_term_support_rows(packet, bucket), "skills_section")


def _unsupported_terms(packet: Dict[str, Any], bucket: str) -> List[str]:
    return _terms_by_support_level(_term_support_rows(packet, bucket), "unsupported")


def _support_tier_prompt_lines(packet: Dict[str, Any]) -> List[str]:
    direct_required = _direct_terms(packet, "required")
    contextual_required = _contextual_terms(packet, "required")
    skills_required = _skills_only_terms(packet, "required")
    unsupported_required = _unsupported_terms(packet, "required")

    direct_preferred = _direct_terms(packet, "preferred")
    contextual_preferred = _contextual_terms(packet, "preferred")
    skills_preferred = _skills_only_terms(packet, "preferred")
    unsupported_preferred = _unsupported_terms(packet, "preferred")

    return [
        "Support tiers by JD term:",
        f"- Direct bullet support (required): {direct_required}",
        f"- Entry-context support (required): {contextual_required}",
        f"- Skills-section-only support (required): {skills_required}",
        f"- Unsupported (required): {unsupported_required}",
        f"- Direct bullet support (preferred): {direct_preferred}",
        f"- Entry-context support (preferred): {contextual_preferred}",
        f"- Skills-section-only support (preferred): {skills_preferred}",
        f"- Unsupported (preferred): {unsupported_preferred}",
        "",
    ]

def _facet_rows(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    summary = packet.get("summary", {}) or {}
    rows = summary.get("facet_support", []) or []
    return [row for row in rows if isinstance(row, dict)]


def _facet_row(packet: Dict[str, Any], facet_name: str) -> Dict[str, Any]:
    for row in _facet_rows(packet):
        if str(row.get("facet", "")).strip() == facet_name:
            return row
    return {}


def _facet_display_name(name: str) -> str:
    return str(name or "").replace("_", " ").strip()


def _facet_support_score(row: Dict[str, Any]) -> tuple:
    direct_terms = row.get("direct_terms", []) or []
    context_terms = row.get("context_terms", []) or []
    skills_only_terms = row.get("skills_only_terms", []) or []
    unsupported_terms = row.get("unsupported_terms", []) or []
    anchor_evidence = row.get("anchor_evidence", []) or []
    facet_direct_evidence = row.get("facet_direct_evidence", []) or []
    facet_context_terms = row.get("facet_context_terms", []) or []
    facet_context_evidence = row.get("facet_context_evidence", []) or []

    direct_score = (
        len(direct_terms) * 12
        + min(len(anchor_evidence), 4) * 4
        + min(len(facet_direct_evidence), 4) * 3
    )
    context_score = (
        len(context_terms) * 6
        + min(len(facet_context_terms), 4) * 2
        + min(len(facet_context_evidence), 4) * 2
    )
    skills_only_score = len(skills_only_terms)
    unsupported_penalty = len(unsupported_terms) * 2

    return (
        direct_score,
        context_score,
        skills_only_score,
        -unsupported_penalty,
    )

def _facet_has_direct_support(row: Dict[str, Any]) -> bool:
    return bool(row.get("direct_terms"))


def _facet_has_adjacent_support(row: Dict[str, Any]) -> bool:
    if _facet_has_direct_support(row):
        return False

    return bool(
        row.get("facet_direct_evidence")
        or row.get("facet_context_terms")
        or row.get("facet_context_evidence")
        or row.get("context_terms")
        or row.get("skills_only_terms")
    )


def _facet_is_true_gap(row: Dict[str, Any]) -> bool:
    return (
        not _facet_has_direct_support(row)
        and not _facet_has_adjacent_support(row)
        and bool(row.get("unsupported_terms"))
    )


def _adjacent_unsupported_terms(packet: Dict[str, Any]) -> List[str]:
    terms: List[str] = []
    for row in _facet_rows(packet):
        if _facet_has_adjacent_support(row):
            terms.extend(row.get("unsupported_terms", []) or [])
    return _unique_preserve_order(terms)


def _true_gap_terms(packet: Dict[str, Any]) -> List[str]:
    terms: List[str] = []
    for row in _facet_rows(packet):
        if _facet_is_true_gap(row):
            terms.extend(row.get("unsupported_terms", []) or [])
    return _unique_preserve_order(terms)


def _top_direct_facets(packet: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    rows = [row for row in _facet_rows(packet) if _facet_has_direct_support(row)]
    rows.sort(
        key=lambda row: (
            -_facet_support_score(row)[0],
            -_facet_support_score(row)[1],
            -_facet_support_score(row)[2],
            _facet_support_score(row)[3],
            _facet_display_name(row.get("facet", "")),
        )
    )
    return rows[:limit]


def _top_adjacent_facets(packet: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    rows = [row for row in _facet_rows(packet) if _facet_has_adjacent_support(row)]
    rows.sort(
        key=lambda row: (
            -_facet_support_score(row)[0],
            -_facet_support_score(row)[1],
            -_facet_support_score(row)[2],
            _facet_support_score(row)[3],
            _facet_display_name(row.get("facet", "")),
        )
    )
    return rows[:limit]

def _top_supported_facets(packet: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    return _top_direct_facets(packet, limit=limit)


def _top_gap_facets(packet: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    rows = [row for row in _facet_rows(packet) if _facet_is_true_gap(row)]
    rows.sort(
        key=lambda row: (
            -len(row.get("unsupported_terms", []) or []),
            _facet_display_name(row.get("facet", "")),
        )
    )
    return rows[:limit]


def _facet_prompt_lines(packet: Dict[str, Any]) -> List[str]:
    lines: List[str] = ["JD facet support:"]

    for row in _facet_rows(packet):
        facet_name = _facet_display_name(row.get("facet", ""))
        lines.append(
            f"- {facet_name}: "
            f"direct={row.get('direct_terms', [])}; "
            f"context={row.get('context_terms', [])}; "
            f"skills_only={row.get('skills_only_terms', [])}; "
            f"unsupported={row.get('unsupported_terms', [])}"
        )

        facet_direct_sources = _unique_preserve_order(
            [_source_label(ev) for ev in (row.get("facet_direct_evidence", []) or [])[:2]]
        )
        facet_context_sources = _unique_preserve_order(
            [_source_label(ev) for ev in (row.get("facet_context_evidence", []) or [])[:2]]
        )

        if facet_direct_sources:
            lines.append(f"  direct_facet_evidence_sources={facet_direct_sources}")
        if row.get("facet_context_terms"):
            lines.append(f"  context_facet_terms={row.get('facet_context_terms', [])}")
        if facet_context_sources:
            lines.append(f"  context_facet_evidence_sources={facet_context_sources}")

    lines.append("")
    return lines

def _build_recruiter_summary(packet: Dict[str, Any]) -> str:
    job = packet.get("job", {})
    selection = packet.get("selection", {})

    resume_name = selection.get("selected_resume", "selected resume")
    score = selection.get("selected_score", 0.0)
    company = job.get("company", "")
    title = job.get("title", "")

    direct_facets = _top_direct_facets(packet, limit=3)
    adjacent_facets = _top_adjacent_facets(packet, limit=3)
    gap_facets = _top_gap_facets(packet, limit=3)

    direct_terms = _unique_preserve_order(
        _direct_terms(packet, "required") + _direct_terms(packet, "preferred")
    )
    contextual_terms = _unique_preserve_order(
        _contextual_terms(packet, "required")
        + _contextual_terms(packet, "preferred")
        + _skills_only_terms(packet, "required")
        + _skills_only_terms(packet, "preferred")
    )
    adjacent_unsupported = _adjacent_unsupported_terms(packet)
    true_gap_terms = _true_gap_terms(packet)

    sentences: List[str] = [
        f"{resume_name} is the selected variant for {company} | {title} with a deterministic score of {score:.3f}."
    ]

    if direct_facets:
        facet_text = ", ".join(
            _facet_display_name(row.get("facet", "")) for row in direct_facets
        )
        sentences.append(f"The strongest directly supported JD facets are {facet_text}.")

    if adjacent_facets:
        facet_text = ", ".join(
            _facet_display_name(row.get("facet", "")) for row in adjacent_facets
        )
        sentences.append(
            f"It also has adjacent facet-level support for {facet_text}, but the exact JD terms in those areas should still be framed carefully."
        )

    if direct_terms:
        sentences.append(
            f"Direct bullet support includes {', '.join(_truncate_list(direct_terms, 8))}."
        )

    if contextual_terms:
        sentences.append(
            f"Additional adjacent or skills-only support exists for {', '.join(_truncate_list(contextual_terms, 8))}, which should not be presented as direct hands-on ownership."
        )

    if adjacent_unsupported:
        sentences.append(
            f"Within the adjacent-support areas, the exact JD terms still not directly proven are {', '.join(_truncate_list(adjacent_unsupported, 6))}."
        )

    if gap_facets:
        gap_text = ", ".join(
            _facet_display_name(row.get("facet", "")) for row in gap_facets
        )
        sentences.append(f"The main true JD facet gaps still showing are {gap_text}.")
    elif true_gap_terms:
        sentences.append(
            f"The clearest true unsupported JD terms still showing are {', '.join(_truncate_list(true_gap_terms, 6))}."
        )
    else:
        sentences.append("It does not show major true JD facet gaps after the facet pass.")

    return " ".join(sentences)


def _build_keep_emphasize(packet: Dict[str, Any]) -> List[str]:
    direct_required = _direct_terms(packet, "required")
    direct_preferred = _direct_terms(packet, "preferred")
    contextual_terms = _unique_preserve_order(
        _contextual_terms(packet, "required") + _contextual_terms(packet, "preferred")
    )
    skills_only_terms = _unique_preserve_order(
        _skills_only_terms(packet, "required") + _skills_only_terms(packet, "preferred")
    )
    matched_terms = (packet.get("summary", {}) or {}).get("matched_terms", [])

    items: List[str] = []

    if direct_required:
        items.append(
            f"Keep direct bullet evidence visible for required terms: {', '.join(_truncate_list(direct_required, 8))}."
        )
    if direct_preferred:
        items.append(
            f"Keep direct bullet evidence visible for preferred terms: {', '.join(_truncate_list(direct_preferred, 6))}."
        )
    if contextual_terms:
        items.append(
            f"Use adjacent entry-context support only as secondary framing: {', '.join(_truncate_list(contextual_terms, 6))}."
        )
    if skills_only_terms:
        items.append(
            f"Use skills-section-only support carefully and only as light supporting context: {', '.join(_truncate_list(skills_only_terms, 6))}."
        )
    if matched_terms:
        items.append(
            f"Preserve the strongest JD-aligned language already present: {', '.join(_truncate_list(matched_terms, 8))}."
        )

    return _unique_preserve_order(items)


def _build_do_not_claim(packet: Dict[str, Any]) -> List[str]:
    unsupported_required = _unsupported_terms(packet, "required")
    unsupported_preferred = _unsupported_terms(packet, "preferred")
    contextual_or_skills_only = _unique_preserve_order(
        _contextual_terms(packet, "required")
        + _contextual_terms(packet, "preferred")
        + _skills_only_terms(packet, "required")
        + _skills_only_terms(packet, "preferred")
    )
    guardrail = packet.get(
        "guardrail",
        "Only add or strengthen resume language when it is already truthful and supported by your actual work.",
    )

    items: List[str] = []

    if unsupported_required:
        items.append(
            f"Do not claim unsupported required skills unless you can support them truthfully: {', '.join(_truncate_list(unsupported_required, 8))}."
        )
    if unsupported_preferred:
        items.append(
            f"Do not add unsupported preferred-skill claims: {', '.join(_truncate_list(unsupported_preferred, 8))}."
        )
    if contextual_or_skills_only:
        items.append(
            f"Do not rewrite these as direct hands-on experience unless a bullet proves them: {', '.join(_truncate_list(contextual_or_skills_only, 8))}."
        )

    items.append(guardrail)
    return _unique_preserve_order(items)

def _evidence_unit_rows(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = packet.get("top_relevant_evidence_units", []) or []
    return [row for row in rows if isinstance(row, dict)]


def _rewrite_source_rows(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    unit_rows = _evidence_unit_rows(packet)
    if unit_rows:
        return unit_rows
    return packet.get("top_relevant_bullets", []) or []


def _row_supported_terms(row: Dict[str, Any]) -> List[str]:
    return _unique_preserve_order(
        list(row.get("overlaps", []) or []) + list(row.get("context_terms", []) or [])
    )


def _row_evidence_excerpt(row: Dict[str, Any], max_len: int = 220) -> str:
    text = row.get("clause_text") or row.get("text", "")
    return _short_bullet(text, max_len)


def _row_parent_bullet_excerpt(row: Dict[str, Any], max_len: int = 260) -> str:
    return _short_bullet(row.get("parent_bullet", ""), max_len)


def _is_clause_unit(row: Dict[str, Any]) -> bool:
    return str(row.get("unit_kind", "")).strip() == "clause_unit"

def _build_bullet_reuse(packet: Dict[str, Any], limit: int = 6) -> List[Dict[str, Any]]:
    rows = _rewrite_source_rows(packet)
    selected = rows[:limit]

    reuse_rows = []
    for row in selected:
        source = _source_label(row)
        overlaps = _row_supported_terms(row)
        evidence_type = row.get("evidence_type", "direct_overlap")
        is_clause = _is_clause_unit(row)

        if evidence_type == "direct_overlap":
            if is_clause:
                reuse_note = (
                    "Use this clause as a primary anchor and only keep the rest of the parent bullet "
                    f"if it strengthens the same supported story truthfully: {', '.join(overlaps[:6])}"
                )
            else:
                reuse_note = (
                    "Use this as a primary anchor bullet and move the matched JD terms "
                    f"earlier in the sentence: {', '.join(overlaps[:6])}"
                )
        elif evidence_type == "semantic_similarity":
            reuse_note = (
                "Use this as supporting evidence only. It is meaning-aligned with the JD, "
                "but it is not the strongest exact-term anchor."
            )
        elif evidence_type == "same_source_context":
            reuse_note = (
                "Use this as supporting context from the same role/project so the main anchor "
                "evidence feels more credible and less isolated."
            )
        else:
            reuse_note = (
                "Use this as nearby supporting context if it strengthens the same story truthfully."
            )

        reuse_rows.append(
            {
                "section": row.get("section", ""),
                "source": source,
                "overlaps": overlaps,
                "evidence_type": evidence_type,
                "bullet": row.get("clause_text") or row.get("text", ""),
                "parent_bullet": row.get("parent_bullet", ""),
                "reuse_note": reuse_note,
            }
        )

    return reuse_rows

def _build_rewrite_candidates(
    packet: Dict[str, Any],
    tailoring_plan: Optional[Dict[str, Any]] = None,
    limit: int = 4,
) -> List[Dict[str, Any]]:
    tailoring_plan = tailoring_plan or {}
    candidates: List[Dict[str, Any]] = []
    used_keys = set()

    primary_units = tailoring_plan.get("primary_anchor_units", []) or []
    secondary_units = tailoring_plan.get("secondary_support_units", []) or []

    for unit in primary_units:
        key = _plan_unit_key(unit)
        if key in used_keys:
            continue
        used_keys.add(key)
        candidates.append(_rewrite_candidate_from_plan_unit(unit, primary=True))
        if len(candidates) >= limit:
            return candidates

    for unit in secondary_units:
        key = _plan_unit_key(unit)
        if key in used_keys:
            continue
        used_keys.add(key)
        candidates.append(_rewrite_candidate_from_plan_unit(unit, primary=False))
        if len(candidates) >= limit:
            return candidates

    rows = _rewrite_source_rows(packet)

    for row in rows:
        supported_terms = _row_supported_terms(row)
        if not supported_terms:
            continue

        source = _source_label(row)
        evidence_type = row.get("evidence_type", "direct_overlap")
        source_key = (
            row.get("section", ""),
            source,
            evidence_type,
            row.get("clause_text") or row.get("text", ""),
        )

        if source_key in used_keys:
            continue

        is_clause = _is_clause_unit(row)

        if evidence_type == "direct_overlap":
            if is_clause:
                action = (
                    f"Lead with {', '.join(supported_terms[:4])} in this opening clause, "
                    "then keep the remaining parent-bullet context only if it preserves a clean story."
                )
            else:
                action = (
                    f"Lead with {', '.join(supported_terms[:4])} in the opening clause of this bullet, "
                    "then keep the outcome/impact at the end."
                )
        elif evidence_type == "same_source_context":
            action = (
                "Use this as a second supporting line under the same role so the stronger anchor evidence "
                "looks backed by related work."
            )
        else:
            action = (
                "Use this as adjacent support only if it keeps the same story truthful and consistent."
            )

        candidates.append(
            {
                "source": source,
                "section": row.get("section", ""),
                "evidence_type": evidence_type,
                "supported_terms": supported_terms[:6],
                "action": action,
                "bullet_excerpt": _row_evidence_excerpt(row),
                "parent_bullet": row.get("parent_bullet", ""),
            }
        )
        used_keys.add(source_key)

        if len(candidates) >= limit:
            break

    return candidates

def _build_evidence_layers(
    packet: Dict[str, Any],
    tailoring_plan: Optional[Dict[str, Any]] = None,
    limit_per_group: int = 4,
) -> Dict[str, List[Dict[str, Any]]]:
    tailoring_plan = tailoring_plan or {}
    rows = _rewrite_source_rows(packet)

    primary_units = tailoring_plan.get("primary_anchor_units", []) or []
    secondary_units = tailoring_plan.get("secondary_support_units", []) or []

    if primary_units or secondary_units:
        anchors = [
            _find_rewrite_row_for_plan_unit(rows, unit)
            for unit in primary_units[:limit_per_group]
        ]
        supports = [
            _find_rewrite_row_for_plan_unit(rows, unit)
            for unit in secondary_units[:limit_per_group]
        ]

        used_keys = {
            _plan_row_key(row)
            for row in anchors + supports
        }

        context = [
            row for row in rows
            if row.get("evidence_type") in {"same_source_context", "adjacent_context"}
            and _plan_row_key(row) not in used_keys
        ][:limit_per_group]

        return {
            "anchors": anchors,
            "supports": supports,
            "context": context,
        }

    anchors = [row for row in rows if row.get("evidence_type") == "direct_overlap"][:limit_per_group]
    supports = [row for row in rows if row.get("evidence_type") == "semantic_similarity"][:limit_per_group]
    context = [
        row for row in rows
        if row.get("evidence_type") in {"same_source_context", "adjacent_context"}
    ][:limit_per_group]

    return {
        "anchors": anchors,
        "supports": supports,
        "context": context,
    }

def _display_row_source(row: Dict[str, Any]) -> str:
    source = str(row.get("source", "") or "").strip()
    if source:
        return source
    return _source_label(row)


def _plan_unit_key(unit: Dict[str, Any]) -> tuple:
    return (
        str(unit.get("section", "") or "").strip(),
        str(unit.get("source", "") or "").strip(),
        str(unit.get("evidence_type", "") or "").strip(),
        str(unit.get("evidence_unit", "") or "").strip(),
    )


def _find_rewrite_row_for_plan_unit(
    rows: List[Dict[str, Any]],
    unit: Dict[str, Any],
) -> Dict[str, Any]:
    target_key = _plan_unit_key(unit)

    for row in rows:
        if _plan_row_key(row) == target_key:
            return row

    return {
        "section": unit.get("section", ""),
        "source": unit.get("source", ""),
        "evidence_type": unit.get("evidence_type", ""),
        "overlaps": list(unit.get("supported_terms", []) or []),
        "context_terms": [],
        "clause_text": unit.get("evidence_unit", ""),
        "parent_bullet": unit.get("parent_bullet", ""),
        "unit_kind": "clause_unit",
    }


def _rewrite_candidate_from_plan_unit(
    unit: Dict[str, Any],
    *,
    primary: bool,
) -> Dict[str, Any]:
    supported_terms = list(unit.get("supported_terms", []) or [])
    source = str(unit.get("source", "") or "").strip()
    evidence_unit = str(unit.get("evidence_unit", "") or "").strip()
    parent_bullet = str(unit.get("parent_bullet", "") or "").strip()

    if primary:
        if supported_terms:
            action = (
                f"Lead with {', '.join(supported_terms[:4])} in this opening clause, "
                "then keep the remaining parent-bullet context only if it preserves the same story truthfully."
            )
        else:
            action = (
                "Lead with this opening clause, then keep the remaining parent-bullet context only if it preserves the same story truthfully."
            )
    else:
        if supported_terms:
            action = (
                f"Support with {', '.join(supported_terms[:4])} only after the primary anchors, "
                "and keep it as reinforcing evidence rather than the main ownership claim."
            )
        else:
            action = (
                "Use this only as secondary supporting evidence after the primary anchors, "
                "not as the main ownership claim."
            )

    return {
        "source": source,
        "section": unit.get("section", ""),
        "evidence_type": unit.get("evidence_type", ""),
        "supported_terms": supported_terms[:6],
        "action": action,
        "bullet_excerpt": _short_bullet(evidence_unit, 220),
        "parent_bullet": parent_bullet,
    }

def _plan_unit_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "section": row.get("section", ""),
        "source": _source_label(row),
        "evidence_type": row.get("evidence_type", ""),
        "supported_terms": _row_supported_terms(row)[:6],
        "evidence_unit": row.get("clause_text") or row.get("text", ""),
        "parent_bullet": row.get("parent_bullet", ""),
    }

def _plan_row_key(row: Dict[str, Any]) -> tuple:
    return (
        str(row.get("section", "") or "").strip(),
        _source_label(row),
        str(row.get("evidence_type", "") or "").strip(),
        str(row.get("clause_text") or row.get("text") or "").strip(),
    )


def _facet_evidence_texts(facet_row: Dict[str, Any]) -> List[str]:
    texts: List[str] = []

    for key in ("anchor_evidence", "facet_direct_evidence", "facet_context_evidence"):
        for evidence in facet_row.get(key, []) or []:
            if not isinstance(evidence, dict):
                continue

            text = str(evidence.get("text", "") or "").strip()
            if text:
                texts.append(text)

    return _unique_preserve_order(texts)


def _row_matches_facet(row: Dict[str, Any], facet_row: Dict[str, Any]) -> bool:
    row_terms = _row_supported_terms(row)
    row_text = str(row.get("clause_text") or row.get("text") or "").strip()
    parent_text = str(row.get("parent_bullet", "") or "").strip()

    facet_terms = _unique_preserve_order(
        list(facet_row.get("direct_terms", []) or [])
        + list(facet_row.get("context_terms", []) or [])
        + list(facet_row.get("skills_only_terms", []) or [])
        + list(facet_row.get("facet_context_terms", []) or [])
        + list(facet_row.get("job_terms", []) or [])
    )
    facet_evidence_texts = _facet_evidence_texts(facet_row)

    # 1) explicit term overlap on the selected row itself
    if any(term in row_terms for term in facet_terms):
        return True

    # 2) facet language actually appears in the selected clause or its parent bullet
    for candidate_text in (row_text, parent_text):
        if candidate_text and _direction_mentions_any(candidate_text, facet_terms):
            return True

    # 3) the selected clause/parent bullet actually corresponds to one of the facet evidence texts
    for candidate_text in (row_text, parent_text):
        if not candidate_text:
            continue

        for evidence_text in facet_evidence_texts:
            if (
                candidate_text == evidence_text
                or candidate_text in evidence_text
                or evidence_text in candidate_text
            ):
                return True

    return False

def _select_plan_rows_for_facet(
    rows: List[Dict[str, Any]],
    facet_row: Dict[str, Any],
    used_keys: set,
    *,
    limit: int = 1,
    allowed_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    allowed = set(allowed_types or [])
    selected: List[Dict[str, Any]] = []

    for row in rows:
        evidence_type = str(row.get("evidence_type", "") or "").strip()
        if allowed and evidence_type not in allowed:
            continue

        if not _row_matches_facet(row, facet_row):
            continue

        key = _plan_row_key(row)
        if key in used_keys:
            continue

        used_keys.add(key)
        selected.append(_plan_unit_row(row))

        if len(selected) >= limit:
            break

    return selected

def _plan_unit_match_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "overlaps": list(row.get("supported_terms", []) or []),
        "context_terms": [],
        "clause_text": row.get("evidence_unit", ""),
        "parent_bullet": row.get("parent_bullet", ""),
    }

def _plan_unit_brief_label(unit: Dict[str, Any], max_evidence_len: int = 120) -> str:
    source = str(unit.get("source", "") or "").strip()
    supported_terms = list(unit.get("supported_terms", []) or [])
    evidence_unit = _short_bullet(str(unit.get("evidence_unit", "") or "").strip(), max_evidence_len)

    parts: List[str] = []
    if source:
        parts.append(source)
    if supported_terms:
        parts.append(f"supports={', '.join(_truncate_list(supported_terms, 4))}")
    if evidence_unit:
        parts.append(f"evidence={evidence_unit}")

    return " | ".join(parts)


def _plan_unit_brief_labels(
    units: List[Dict[str, Any]],
    *,
    limit: int,
    max_evidence_len: int = 120,
) -> List[str]:
    labels: List[str] = []
    seen = set()

    for unit in units:
        label = _plan_unit_brief_label(unit, max_evidence_len=max_evidence_len)
        if not label or label in seen:
            continue
        seen.add(label)
        labels.append(label)
        if len(labels) >= limit:
            break

    return labels

def _covered_facet_names_for_plan_units(
    plan_units: List[Dict[str, Any]],
    facet_rows: List[Dict[str, Any]],
) -> List[str]:
    covered: List[str] = []

    for facet_row in facet_rows:
        facet_name = _facet_display_name(facet_row.get("facet", ""))
        if not facet_name:
            continue

        if any(
            _row_matches_facet(_plan_unit_match_row(unit), facet_row)
            for unit in plan_units
        ):
            covered.append(facet_name)

    return _unique_preserve_order(covered)

def _build_narrative_angle(packet: Dict[str, Any]) -> str:
    direct_facets = _top_direct_facets(packet, limit=2)
    adjacent_facets = _top_adjacent_facets(packet, limit=2)
    gap_facets = _top_gap_facets(packet, limit=1)

    direct_facet_names = [
        _facet_display_name(row.get("facet", "")) for row in direct_facets
    ]
    adjacent_facet_names = [
        _facet_display_name(row.get("facet", "")) for row in adjacent_facets
    ]
    gap_facet_names = [
        _facet_display_name(row.get("facet", "")) for row in gap_facets
    ]

    if direct_facet_names:
        sentence = f"Lead with {', '.join(_truncate_list(direct_facet_names, 2))} as the core story"
        if adjacent_facet_names:
            sentence += (
                f"; use {', '.join(_truncate_list(adjacent_facet_names, 2))} only as adjacent support"
            )
        if gap_facet_names:
            sentence += (
                f"; keep {', '.join(_truncate_list(gap_facet_names, 1))} explicit instead of overstating ownership"
            )
        return sentence + "."

    direct_terms = _unique_preserve_order(
        _direct_terms(packet, "required") + _direct_terms(packet, "preferred")
    )
    if direct_terms:
        sentence = f"Lead with direct bullet evidence for {', '.join(_truncate_list(direct_terms, 4))}"
        if gap_facet_names:
            sentence += (
                f"; keep {', '.join(_truncate_list(gap_facet_names, 1))} explicit instead of overstating ownership"
            )
        return sentence + "."

    return "Use the strongest direct bullet evidence first and keep unsupported areas explicit."


def _build_anchor_plan(packet: Dict[str, Any]) -> Dict[str, Any]:
    rows = _rewrite_source_rows(packet)

    direct_anchor_rows = [
        row for row in rows
        if str(row.get("evidence_type", "") or "").strip() == "direct_overlap"
    ]
    support_rows = [
        row for row in rows
        if str(row.get("evidence_type", "") or "").strip()
        in {"direct_overlap", "semantic_similarity", "same_source_context", "adjacent_context"}
    ]
    secondary_only_rows = [
        row for row in rows
        if str(row.get("evidence_type", "") or "").strip()
        in {"semantic_similarity", "same_source_context", "adjacent_context"}
    ]

    direct_facets = _top_direct_facets(packet, limit=3)
    adjacent_facets = _top_adjacent_facets(packet, limit=3)

    used_keys = set()
    primary_anchor_units: List[Dict[str, Any]] = []
    secondary_support_units: List[Dict[str, Any]] = []

    # Step 1: guarantee one primary anchor per top direct facet where possible
    for facet_row in direct_facets[:2]:
        selected = _select_plan_rows_for_facet(
            direct_anchor_rows,
            facet_row,
            used_keys,
            limit=1,
            allowed_types=["direct_overlap"],
        )
        if selected:
            primary_anchor_units.extend(selected)

    # Step 2: backfill remaining primary anchors from strongest direct-overlap rows
    for row in direct_anchor_rows:
        if len(primary_anchor_units) >= 3:
            break

        key = _plan_row_key(row)
        if key in used_keys:
            continue

        used_keys.add(key)
        primary_anchor_units.append(_plan_unit_row(row))

    primary_facet_coverage = _covered_facet_names_for_plan_units(
        primary_anchor_units,
        direct_facets,
    )

    # Step 3: if any direct facet still lacks primary coverage, force secondary coverage for it
    covered_direct_facets = set(primary_facet_coverage)
    for facet_row in direct_facets[:2]:
        facet_name = _facet_display_name(facet_row.get("facet", ""))
        if facet_name in covered_direct_facets:
            continue

        selected = _select_plan_rows_for_facet(
            support_rows,
            facet_row,
            used_keys,
            limit=1,
            allowed_types=["direct_overlap", "semantic_similarity", "same_source_context", "adjacent_context"],
        )
        if selected:
            secondary_support_units.extend(selected)

    # Step 4: add one adjacent-support unit for the strongest adjacent facets
    for facet_row in adjacent_facets[:2]:
        selected = _select_plan_rows_for_facet(
            support_rows,
            facet_row,
            used_keys,
            limit=1,
            allowed_types=["semantic_similarity", "same_source_context", "adjacent_context", "direct_overlap"],
        )
        if selected:
            secondary_support_units.extend(selected)

    # Step 5: backfill remaining secondary support slots
    for row in secondary_only_rows:
        if len(secondary_support_units) >= 3:
            break

        key = _plan_row_key(row)
        if key in used_keys:
            continue

        used_keys.add(key)
        secondary_support_units.append(_plan_unit_row(row))

    primary_facet_coverage = _covered_facet_names_for_plan_units(
        primary_anchor_units,
        direct_facets,
    )
    secondary_facet_coverage = [
        name
        for name in _covered_facet_names_for_plan_units(
            secondary_support_units,
            direct_facets + adjacent_facets,
        )
        if name not in set(primary_facet_coverage)
    ]

    return {
        "primary_anchor_units": primary_anchor_units,
        "secondary_support_units": secondary_support_units,
        "primary_facet_coverage": primary_facet_coverage,
        "secondary_facet_coverage": secondary_facet_coverage,
    }


def _build_gap_plan(packet: Dict[str, Any]) -> Dict[str, Any]:
    contextual_terms_to_frame_carefully = _unique_preserve_order(
        _contextual_terms(packet, "required")
        + _contextual_terms(packet, "preferred")
        + _skills_only_terms(packet, "required")
        + _skills_only_terms(packet, "preferred")
    )

    adjacent_terms_to_keep_explicit = _adjacent_unsupported_terms(packet)
    true_unsupported_terms = _true_gap_terms(packet)

    direct_facets = [
        _facet_display_name(row.get("facet", ""))
        for row in _top_direct_facets(packet, limit=3)
    ]
    adjacent_facets = [
        _facet_display_name(row.get("facet", ""))
        for row in _top_adjacent_facets(packet, limit=3)
    ]
    true_gap_facets = [
        _facet_display_name(row.get("facet", ""))
        for row in _top_gap_facets(packet, limit=3)
    ]

    return {
        "direct_facets": _unique_preserve_order(direct_facets),
        "adjacent_facets": _unique_preserve_order(adjacent_facets),
        "true_gap_facets": _unique_preserve_order(true_gap_facets),
        "contextual_terms_to_frame_carefully": contextual_terms_to_frame_carefully,
        "adjacent_terms_to_keep_explicit": adjacent_terms_to_keep_explicit,
        "true_unsupported_terms": true_unsupported_terms,
    }

def _build_compatibility_anchor_plan(packet: Dict[str, Any]) -> Dict[str, Any]:
    rows = _rewrite_source_rows(packet)

    direct_facets = _top_direct_facets(packet, limit=3)
    adjacent_facets = _top_adjacent_facets(packet, limit=3)

    primary_anchor_units: List[Dict[str, Any]] = []
    secondary_support_units: List[Dict[str, Any]] = []
    used_keys = set()

    supported_rows = [row for row in rows if _row_supported_terms(row)]
    if not supported_rows:
        return {
            "primary_anchor_units": [],
            "secondary_support_units": [],
            "primary_facet_coverage": [],
            "secondary_facet_coverage": [],
            "compatibility_mode": False,
            "compatibility_reason": "",
        }

    # Treat legacy rows with supported terms as usable anchors even if newer facet-plan fields are missing.
    anchor_candidates: List[Dict[str, Any]] = []
    support_candidates: List[Dict[str, Any]] = []

    for row in supported_rows:
        evidence_type = str(row.get("evidence_type", "") or "").strip()
        if evidence_type in {"same_source_context", "adjacent_context"}:
            support_candidates.append(row)
        else:
            anchor_candidates.append(row)

    if not anchor_candidates:
        anchor_candidates = supported_rows[:]

    for row in anchor_candidates:
        key = _plan_row_key(row)
        if key in used_keys:
            continue
        used_keys.add(key)
        primary_anchor_units.append(_plan_unit_row(row))
        if len(primary_anchor_units) >= 3:
            break

    for row in support_candidates:
        key = _plan_row_key(row)
        if key in used_keys:
            continue
        used_keys.add(key)
        secondary_support_units.append(_plan_unit_row(row))
        if len(secondary_support_units) >= 1:
            break

    # If no explicit support row exists, preserve one additional supported row as secondary evidence.
    if not secondary_support_units:
        for row in supported_rows:
            key = _plan_row_key(row)
            if key in used_keys:
                continue
            used_keys.add(key)
            secondary_support_units.append(_plan_unit_row(row))
            break

    primary_facet_coverage = (
        _covered_facet_names_for_plan_units(primary_anchor_units, direct_facets)
        if direct_facets
        else []
    )

    secondary_facet_coverage = (
        [
            name
            for name in _covered_facet_names_for_plan_units(
                secondary_support_units,
                direct_facets + adjacent_facets,
            )
            if name not in set(primary_facet_coverage)
        ]
        if (direct_facets or adjacent_facets)
        else []
    )

    return {
        "primary_anchor_units": primary_anchor_units,
        "secondary_support_units": secondary_support_units,
        "primary_facet_coverage": primary_facet_coverage,
        "secondary_facet_coverage": secondary_facet_coverage,
        "compatibility_mode": True,
        "compatibility_reason": "legacy_packet_missing_planner_seed_structure",
    }

def _build_tailoring_plan(packet: Dict[str, Any]) -> Dict[str, Any]:
    anchor_plan = _build_anchor_plan(packet)
    gap_plan = _build_gap_plan(packet)

    compatibility_mode = False
    compatibility_reason = ""

    if not anchor_plan.get("primary_anchor_units") and not anchor_plan.get("secondary_support_units"):
        compatibility_anchor_plan = _build_compatibility_anchor_plan(packet)
        if (
            compatibility_anchor_plan.get("primary_anchor_units")
            or compatibility_anchor_plan.get("secondary_support_units")
        ):
            anchor_plan = compatibility_anchor_plan
            compatibility_mode = bool(compatibility_anchor_plan.get("compatibility_mode"))
            compatibility_reason = str(compatibility_anchor_plan.get("compatibility_reason", "") or "").strip()

    return {
        "narrative_angle": _build_narrative_angle(packet),
        **anchor_plan,
        **gap_plan,
        "compatibility_mode": compatibility_mode,
        "compatibility_reason": compatibility_reason,
    }


def _tailoring_plan_prompt_lines(plan: Dict[str, Any]) -> List[str]:
    lines: List[str] = ["Deterministic tailoring plan:"]
    lines.append(f"- Narrative angle: {plan.get('narrative_angle', '')}")
    lines.append(f"- Compatibility mode: {plan.get('compatibility_mode', False)}")
    lines.append(f"- Compatibility reason: {plan.get('compatibility_reason', '')}")
    lines.append(f"- Direct facets to lead with: {plan.get('direct_facets', [])}")
    lines.append(f"- Adjacent facets to frame carefully: {plan.get('adjacent_facets', [])}")
    lines.append(f"- True facet gaps to keep explicit: {plan.get('true_gap_facets', [])}")
    lines.append(
        f"- Contextual/skills-only terms to frame carefully: {plan.get('contextual_terms_to_frame_carefully', [])}"
    )
    lines.append(
        f"- Adjacent terms still not directly proven: {plan.get('adjacent_terms_to_keep_explicit', [])}"
    )
    lines.append(
        f"- True unsupported exact JD terms: {plan.get('true_unsupported_terms', [])}"
    )

    lines.append("- Primary anchor units:")
    primary_anchor_units = plan.get("primary_anchor_units", []) or []
    if primary_anchor_units:
        for idx, row in enumerate(primary_anchor_units, 1):
            lines.append(
                f"  {idx}. [{row.get('section', '')}] {row.get('source', '')} | "
                f"type={row.get('evidence_type', '')} | supports={row.get('supported_terms', [])}"
            )
            lines.append(f"     Evidence unit: {_short_bullet(row.get('evidence_unit', ''), 220)}")
            if row.get("parent_bullet"):
                lines.append(f"     Parent bullet: {_short_bullet(row.get('parent_bullet', ''), 220)}")
    else:
        lines.append("  - none")

    lines.append("- Secondary support units:")
    secondary_support_units = plan.get("secondary_support_units", []) or []
    if secondary_support_units:
        for idx, row in enumerate(secondary_support_units, 1):
            lines.append(
                f"  {idx}. [{row.get('section', '')}] {row.get('source', '')} | "
                f"type={row.get('evidence_type', '')} | supports={row.get('supported_terms', [])}"
            )
            lines.append(f"     Evidence unit: {_short_bullet(row.get('evidence_unit', ''), 220)}")
            if row.get("parent_bullet"):
                lines.append(f"     Parent bullet: {_short_bullet(row.get('parent_bullet', ''), 220)}")
    else:
        lines.append("  - none")

    lines.append("")
    return lines

def _fallback_rewrite_directions_from_payload(
    payload: Dict[str, Any],
    limit: int = 6,
) -> List[str]:
    rows = payload.get("rewrite_candidates", []) or []
    directions: List[str] = []

    for row in rows[:limit]:
        section = row.get("section", "")
        source = row.get("source", "")
        action = str(row.get("action", "") or "").strip()
        evidence = str(row.get("bullet_excerpt", "") or "").strip()
        if not action:
            continue

        directions.append(
            f"{action} Source: [{section}] {source}. Evidence: {evidence}"
        )

    return directions

def _plan_unit_to_direction(
    row: Dict[str, Any],
    *,
    primary: bool,
) -> str:
    source = str(row.get("source", "") or "").strip()
    evidence_unit = _short_bullet(str(row.get("evidence_unit", "") or "").strip(), 180)
    supported_terms = row.get("supported_terms", []) or []

    if primary:
        if source and evidence_unit and supported_terms:
            return (
                f"Lead with {evidence_unit} from {source} to anchor "
                f"{', '.join(_truncate_list(supported_terms, 4))}."
            )
        if source and evidence_unit:
            return f"Lead with {evidence_unit} from {source} as a primary anchor."
    else:
        if source and evidence_unit and supported_terms:
            return (
                f"Support with {evidence_unit} from {source} to reinforce "
                f"{', '.join(_truncate_list(supported_terms, 4))} without overstating ownership."
            )
        if source and evidence_unit:
            return (
                f"Support with {evidence_unit} from {source} to reinforce the main story "
                f"without overstating ownership."
            )

    return ""

def _planner_seed_rewrite_directions(
    payload: Dict[str, Any],
    limit: int = 6,
) -> List[str]:
    plan = payload.get("tailoring_plan", {}) or {}
    directions: List[str] = []

    primary_anchor_units = plan.get("primary_anchor_units", []) or []
    secondary_support_units = plan.get("secondary_support_units", []) or []

    # Always cover every selected primary anchor first.
    for row in primary_anchor_units:
        direction = _plan_unit_to_direction(row, primary=True)
        if direction:
            directions.append(direction)

    # Only then add secondary support lines if there is still room.
    remaining_slots = max(0, limit - len(directions))
    if remaining_slots > 0:
        for row in secondary_support_units[:remaining_slots]:
            direction = _plan_unit_to_direction(row, primary=False)
            if direction:
                directions.append(direction)

    adjacent_terms = plan.get("adjacent_terms_to_keep_explicit", []) or []
    adjacent_facets = plan.get("adjacent_facets", []) or []
    if adjacent_terms:
        directions.append(
            f"Do not add direct ownership claims for {', '.join(_truncate_list(adjacent_terms, 4))}; use related evidence only as adjacent support."
        )
    elif adjacent_facets:
        directions.append(
            f"Do not add direct ownership claims for {', '.join(_truncate_list(adjacent_facets, 2))}; use related evidence only as adjacent support."
        )

    true_gap_terms = plan.get("true_unsupported_terms", []) or []
    true_gap_facets = plan.get("true_gap_facets", []) or []
    if true_gap_terms:
        directions.append(
            f"Keep gap explicit for {', '.join(_truncate_list(true_gap_terms, 4))}."
        )
    elif true_gap_facets:
        directions.append(
            f"Keep gap explicit for {', '.join(_truncate_list(true_gap_facets, 2))}."
        )

    return _unique_preserve_order(directions)[:limit]

def _direction_mentions_any(direction: str, values: List[str]) -> bool:
    text = str(direction or "").strip().lower()
    if not text:
        return False

    for value in values or []:
        candidate = str(value or "").strip().lower()
        if candidate and candidate in text:
            return True

    return False

def _direction_plan_unit_match_score(direction: str, row: Dict[str, Any]) -> int:
    text = str(direction or "").strip()
    if not text:
        return 0

    score = 0

    source = str(row.get("source", "") or "").strip()
    if source and _direction_mentions_any(text, [source]):
        score += 3

    supported_terms = [str(term).strip() for term in (row.get("supported_terms", []) or []) if str(term).strip()]
    matched_terms = [term for term in supported_terms if _direction_mentions_any(text, [term])]
    score += len(matched_terms)

    evidence_unit = str(row.get("evidence_unit", "") or "").strip()
    evidence_markers: List[str] = []
    if evidence_unit:
        evidence_markers.append(evidence_unit[:80])
        evidence_markers.append(_short_bullet(evidence_unit, 140))

    if evidence_markers and _direction_mentions_any(text, evidence_markers):
        score += 4

    return score


def _best_matching_plan_unit(
    direction: str,
    plan_units: List[Dict[str, Any]],
    min_score: int = 4,
) -> Optional[Dict[str, Any]]:
    best_row: Optional[Dict[str, Any]] = None
    best_score = 0

    for row in plan_units:
        score = _direction_plan_unit_match_score(direction, row)
        if score > best_score:
            best_score = score
            best_row = row

    if best_score < min_score:
        return None

    return best_row

def _direction_matches_plan_unit(direction: str, row: Dict[str, Any]) -> bool:
    return _direction_plan_unit_match_score(direction, row) >= 4


def _rewrite_directions_cover_plan(
    payload: Dict[str, Any],
    directions: List[str],
) -> bool:
    actionable = [
        str(item).strip()
        for item in directions or []
        if _is_actionable_rewrite_direction(item)
    ]
    if not actionable:
        return False

    plan = payload.get("tailoring_plan", {}) or {}

    primary_anchor_units = plan.get("primary_anchor_units", []) or []
    lead_directions = [item for item in actionable if item.startswith("Lead with")]
    support_directions = [item for item in actionable if item.startswith("Support with")]

    for row in primary_anchor_units:
        if not any(_direction_matches_plan_unit(item, row) for item in lead_directions):
            return False

    secondary_support_units = plan.get("secondary_support_units", []) or []
    if secondary_support_units:
        first_secondary = secondary_support_units[0]
        if not any(
            _direction_matches_plan_unit(item, first_secondary)
            for item in support_directions
        ):
            return False

    adjacent_terms = plan.get("adjacent_terms_to_keep_explicit", []) or []
    adjacent_facets = plan.get("adjacent_facets", []) or []
    if adjacent_terms or adjacent_facets:
        targets = adjacent_terms if adjacent_terms else adjacent_facets
        if not any(
            item.startswith("Do not add") and _direction_mentions_any(item, targets)
            for item in actionable
        ):
            return False

    true_gap_terms = plan.get("true_unsupported_terms", []) or []
    true_gap_facets = plan.get("true_gap_facets", []) or []
    if true_gap_terms or true_gap_facets:
        targets = true_gap_terms if true_gap_terms else true_gap_facets
        if not any(
            item.startswith("Keep gap explicit") and _direction_mentions_any(item, targets)
            for item in actionable
        ):
            return False

    return True

def _normalize_direction_text(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _direction_prefix(value: str) -> str:
    text = str(value or "").strip()
    for prefix in REWRITE_DIRECTION_PREFIXES:
        if text.startswith(prefix):
            return prefix
    return ""


def _direction_matches_any_plan_unit(
    direction: str,
    plan_units: List[Dict[str, Any]],
) -> bool:
    return any(_direction_matches_plan_unit(direction, row) for row in plan_units)


def _rewrite_direction_verifier_report(
    payload: Dict[str, Any],
    directions: List[str],
) -> Dict[str, Any]:
    actionable = [
        str(item).strip()
        for item in directions or []
        if _is_actionable_rewrite_direction(item)
    ]

    plan = payload.get("tailoring_plan", {}) or {}
    primary_anchor_units = plan.get("primary_anchor_units", []) or []
    secondary_support_units = plan.get("secondary_support_units", []) or []

    blocked_direct_claim_terms = _unique_preserve_order(
        list(plan.get("contextual_terms_to_frame_carefully", []) or [])
        + list(plan.get("adjacent_terms_to_keep_explicit", []) or [])
        + list(plan.get("true_unsupported_terms", []) or [])
    )

    seen_text = set()
    duplicate_directions: List[str] = []
    unmapped_lead_support: List[str] = []
    blocked_term_directions: List[str] = []
    duplicate_primary_anchor_directions: List[str] = []
    duplicate_secondary_support_directions: List[str] = []

    covered_primary_keys = set()
    covered_secondary_keys = set()

    for item in actionable:
        normalized = _normalize_direction_text(item)
        if normalized in seen_text:
            duplicate_directions.append(item)
            continue
        seen_text.add(normalized)

        prefix = _direction_prefix(item)

        if prefix == "Lead with":
            matched_primary_unit = _best_matching_plan_unit(item, primary_anchor_units)
            if not matched_primary_unit:
                unmapped_lead_support.append(item)
                continue

            if blocked_direct_claim_terms and _direction_mentions_any(item, blocked_direct_claim_terms):
                blocked_term_directions.append(item)

            matched_key = _plan_unit_key(matched_primary_unit)
            if matched_key in covered_primary_keys:
                duplicate_primary_anchor_directions.append(item)
            else:
                covered_primary_keys.add(matched_key)

        elif prefix == "Support with":
            support_pool = secondary_support_units or (primary_anchor_units + secondary_support_units)
            matched_support_unit = _best_matching_plan_unit(item, support_pool)
            if not matched_support_unit:
                unmapped_lead_support.append(item)
                continue

            if blocked_direct_claim_terms and _direction_mentions_any(item, blocked_direct_claim_terms):
                blocked_term_directions.append(item)

            matched_key = _plan_unit_key(matched_support_unit)
            if matched_key in covered_secondary_keys:
                duplicate_secondary_support_directions.append(item)
            else:
                covered_secondary_keys.add(matched_key)

    issues = _unique_preserve_order(
        (["duplicate_directions"] if duplicate_directions else [])
        + (["unmapped_lead_support"] if unmapped_lead_support else [])
        + (["blocked_term_directions"] if blocked_term_directions else [])
        + (["duplicate_primary_anchor_directions"] if duplicate_primary_anchor_directions else [])
        + (["duplicate_secondary_support_directions"] if duplicate_secondary_support_directions else [])
    )

    return {
        "ok": not issues,
        "issues": issues,
        "duplicate_directions": duplicate_directions,
        "unmapped_lead_support": unmapped_lead_support,
        "blocked_term_directions": blocked_term_directions,
        "duplicate_primary_anchor_directions": duplicate_primary_anchor_directions,
        "duplicate_secondary_support_directions": duplicate_secondary_support_directions,
    }


def _rewrite_directions_pass_verifier(
    payload: Dict[str, Any],
    directions: List[str],
) -> bool:
    return bool(_rewrite_direction_verifier_report(payload, directions).get("ok"))

def _blend_live_and_planner_directions(
    payload: Dict[str, Any],
    llm_directions: List[str],
    limit: int = 6,
) -> List[str]:
    planner_directions = _planner_seed_rewrite_directions(payload, limit=limit)
    blended = _unique_preserve_order(
        [str(item).strip() for item in llm_directions if _is_actionable_rewrite_direction(item)]
        + planner_directions
    )
    return blended[:limit]

def _is_actionable_rewrite_direction(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return text.startswith(REWRITE_DIRECTION_PREFIXES)

def _llm_output_is_strong_enough(parsed: Dict[str, Any]) -> bool:
    rewrite_directions = [
        str(item).strip()
        for item in parsed.get("rewrite_directions", []) or []
        if _is_actionable_rewrite_direction(item)
    ]
    if len(rewrite_directions) < 2:
        return False

    lead_count = sum(1 for item in rewrite_directions if item.startswith("Lead with"))
    support_count = sum(1 for item in rewrite_directions if item.startswith("Support with"))
    gap_count = sum(1 for item in rewrite_directions if item.startswith("Keep gap explicit"))

    if (lead_count + support_count) < 1:
        return False

    if gap_count >= len(rewrite_directions):
        return False

    return True

def _replace_direction_prefix(direction: str, new_prefix: str) -> str:
    text = str(direction or "").strip()
    old_prefix = _direction_prefix(text)
    if not old_prefix:
        return text
    return f"{new_prefix}{text[len(old_prefix):]}"


def _strip_wrapped_clause_quotes(direction: str) -> str:
    text = str(direction or "").strip()

    for prefix in ("Lead with ", "Support with "):
        if not text.startswith(prefix):
            continue

        remainder = text[len(prefix):]
        if not remainder:
            return text

        quote_char = ""
        if remainder.startswith('"'):
            quote_char = '"'
        elif remainder.startswith("'"):
            quote_char = "'"

        if not quote_char:
            return text

        marker = f"{quote_char} from "
        marker_index = remainder.find(marker)
        if marker_index <= 0:
            return text

        clause_text = remainder[1:marker_index].strip()
        suffix = remainder[marker_index + 1 :]
        return f"{prefix}{clause_text}{suffix}"

    return text

def _direction_list_mentions_term(directions: List[str], term: str) -> bool:
    term = str(term or "").strip()
    if not term:
        return False
    return any(_direction_mentions_any(item, [term]) for item in directions or [])


def _canonical_adjacent_guardrail_direction(adjacent_terms: List[str]) -> str:
    terms = [str(term).strip() for term in adjacent_terms or [] if str(term).strip()]
    if not terms:
        return ""
    return (
        f"Do not add direct ownership claims for {', '.join(_truncate_list(terms, 4))}; "
        "use related evidence only as adjacent support."
    )


def _canonical_true_gap_direction(true_gap_terms: List[str]) -> str:
    terms = [str(term).strip() for term in true_gap_terms or [] if str(term).strip()]
    if not terms:
        return ""
    return f"Keep gap explicit for {', '.join(_truncate_list(terms, 4))}."


def _drop_term_only_gap_lines(
    directions: List[str],
    blocked_terms: List[str],
) -> List[str]:
    blocked = {str(term).strip().lower() for term in blocked_terms or [] if str(term).strip()}
    cleaned: List[str] = []

    for item in directions or []:
        text = str(item or "").strip()
        if not text.startswith("Keep gap explicit for"):
            cleaned.append(text)
            continue

        lowered = text.lower()
        matched = [term for term in blocked if term in lowered]
        if matched:
            continue

        cleaned.append(text)

    return cleaned

def _normalize_live_rewrite_directions(
    payload: Dict[str, Any],
    directions: List[str],
    limit: int = 6,
) -> List[str]:
    plan = payload.get("tailoring_plan", {}) or {}
    primary_anchor_units = plan.get("primary_anchor_units", []) or []
    secondary_support_units = plan.get("secondary_support_units", []) or []
    adjacent_terms = list(plan.get("adjacent_terms_to_keep_explicit", []) or [])
    true_gap_terms = list(plan.get("true_unsupported_terms", []) or [])

    normalized: List[str] = []
    covered_primary_keys = set()

    actionable = [
        str(item).strip()
        for item in directions or []
        if _is_actionable_rewrite_direction(item)
    ]

    for item in actionable:
        item = _strip_wrapped_clause_quotes(item)
        prefix = _direction_prefix(item)

        if prefix == "Support with":
            primary_match = _best_matching_plan_unit(item, primary_anchor_units)
            secondary_match = _best_matching_plan_unit(item, secondary_support_units)

            primary_score = (
                _direction_plan_unit_match_score(item, primary_match)
                if primary_match is not None
                else 0
            )
            secondary_score = (
                _direction_plan_unit_match_score(item, secondary_match)
                if secondary_match is not None
                else 0
            )

            if (
                primary_match is not None
                and _plan_unit_key(primary_match) not in covered_primary_keys
                and primary_score >= 4
                and primary_score > secondary_score
            ):
                item = _replace_direction_prefix(item, "Lead with")
                prefix = "Lead with"

        if prefix == "Lead with":
            matched_primary = _best_matching_plan_unit(item, primary_anchor_units)
            if matched_primary is not None:
                covered_primary_keys.add(_plan_unit_key(matched_primary))

        normalized.append(item)

    normalized = _unique_preserve_order(normalized)

    # Canonicalize adjacent-support guardrail coverage.
    if adjacent_terms:
        adjacent_terms_covered_individually = all(
            _direction_list_mentions_term(normalized, term)
            for term in adjacent_terms
        )
        has_canonical_adjacent = any(
            text.startswith("Do not add")
            and _direction_mentions_any(text, adjacent_terms)
            for text in normalized
        )

        if adjacent_terms_covered_individually and not has_canonical_adjacent:
            normalized = _drop_term_only_gap_lines(normalized, adjacent_terms)
            canonical_adjacent = _canonical_adjacent_guardrail_direction(adjacent_terms)
            if canonical_adjacent:
                normalized.append(canonical_adjacent)

    # Canonicalize true-gap coverage to the full deterministic gap line.
    if true_gap_terms:
        has_any_true_gap_line = any(
            text.startswith("Keep gap explicit")
            and _direction_mentions_any(text, true_gap_terms)
            for text in normalized
        )

        if has_any_true_gap_line:
            normalized = _drop_term_only_gap_lines(normalized, true_gap_terms)
            canonical_true_gap = _canonical_true_gap_direction(true_gap_terms)
            if canonical_true_gap:
                normalized.append(canonical_true_gap)

    # Ensure at least one selected secondary support unit is preserved when the plan has one.
    if secondary_support_units:
        has_secondary_support = any(
            _direction_prefix(text) == "Support with"
            and _best_matching_plan_unit(text, secondary_support_units) is not None
            for text in normalized
        )
        if not has_secondary_support:
            fallback_support = _plan_unit_to_direction(secondary_support_units[0], primary=False)
            if fallback_support:
                normalized.append(fallback_support)

    # Reorder to deterministic plan shape before truncation.
    lead_lines = [text for text in normalized if _direction_prefix(text) == "Lead with"]
    support_lines = [text for text in normalized if _direction_prefix(text) == "Support with"]
    do_not_add_lines = [text for text in normalized if _direction_prefix(text) == "Do not add"]
    gap_lines = [text for text in normalized if _direction_prefix(text) == "Keep gap explicit"]

    ordered = lead_lines + support_lines + do_not_add_lines + gap_lines
    return _unique_preserve_order(ordered)[:limit]

def _direction_has_truncation(direction: str) -> bool:
    return "..." in str(direction or "")


def _direction_has_plannerese(direction: str) -> bool:
    text = str(direction or "").lower()
    return (" to anchor " in text) or ("without overstating ownership" in text)


def _direction_has_generic_skill_tail(direction: str) -> bool:
    text = str(direction or "").lower()
    generic_markers = [
        "to highlight",
        "to emphasize",
        "to further demonstrate",
        "to demonstrate",
        "skills.",
        "skills,",
        "experience.",
        "experience,",
        "proficiency.",
        "proficiency,",
    ]
    return any(marker in text for marker in generic_markers)


def _rewrite_direction_quality_report(
    directions: List[str],
) -> Dict[str, Any]:
    actionable = [
        str(item).strip()
        for item in directions or []
        if _is_actionable_rewrite_direction(item)
    ]

    lead_support_lines = [
        item for item in actionable
        if _direction_prefix(item) in {"Lead with", "Support with"}
    ]

    truncated_lines = [item for item in actionable if _direction_has_truncation(item)]
    plannerese_lines = [item for item in actionable if _direction_has_plannerese(item)]
    generic_skill_tail_lines = [item for item in actionable if _direction_has_generic_skill_tail(item)]
    full_anchor_lines = [
        item for item in lead_support_lines
        if not _direction_has_truncation(item)
    ]

    score = (
        2 * len(full_anchor_lines)
        - 2 * len(truncated_lines)
        - 2 * len(plannerese_lines)
        - 1 * len(generic_skill_tail_lines)
    )

    return {
        "score": score,
        "full_anchor_line_count": len(full_anchor_lines),
        "truncated_line_count": len(truncated_lines),
        "plannerese_line_count": len(plannerese_lines),
        "generic_skill_tail_count": len(generic_skill_tail_lines),
        "truncated_lines": truncated_lines,
        "plannerese_lines": plannerese_lines,
        "generic_skill_tail_lines": generic_skill_tail_lines,
    }

def _rewrite_path_audit(
    payload: Dict[str, Any],
    directions: List[str],
) -> Dict[str, Any]:
    actionable = [
        str(item).strip()
        for item in directions or []
        if _is_actionable_rewrite_direction(item)
    ]
    verifier = _rewrite_direction_verifier_report(payload, actionable)
    covers_plan = _rewrite_directions_cover_plan(payload, actionable)
    quality = _rewrite_direction_quality_report(actionable)

    return {
        "count": len(actionable),
        "covers_plan": covers_plan,
        "verifier_ok": bool(verifier.get("ok")),
        "verifier_issues": list(verifier.get("issues", []) or []),
        "quality_score": quality.get("score", 0),
        "quality": quality,
        "directions": actionable[:6],
    }

def _rewrite_candidate_sort_key(candidate: Dict[str, Any]) -> tuple:
    audit = candidate.get("audit", {}) or {}
    quality = audit.get("quality", {}) or {}

    return (
        int(audit.get("quality_score", 0)),
        1 if candidate.get("is_polished") else 0,
        int(quality.get("full_anchor_line_count", 0)),
        -int(quality.get("truncated_line_count", 0)),
        -int(quality.get("plannerese_line_count", 0)),
        -int(quality.get("generic_skill_tail_count", 0)),
    )

def _candidate_directions_key(directions: List[str]) -> tuple:
    return tuple(str(item).strip() for item in directions or [])


def _candidate_pool_lineage_rows(lineage: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for item in lineage:
        rows.append(
            {
                "candidate_id": item.get("candidate_id", ""),
                "source_family": item.get("source_family", ""),
                "is_polished": bool(item.get("is_polished")),
                "status": item.get("status", ""),
                "resolved_to_candidate_id": item.get("resolved_to_candidate_id", ""),
                "resolved_to_source_family": item.get("resolved_to_source_family", ""),
                "dedupe_reason": item.get("dedupe_reason", ""),
                "directions": list(item.get("directions", []) or []),
            }
        )

    return rows

def _build_rewrite_candidate_pool(
    payload: Dict[str, Any],
    planner_directions: List[str],
    live_directions: Optional[List[str]],
    blended_directions: Optional[List[str]],
) -> Dict[str, Any]:
    raw_candidates: List[Dict[str, Any]] = []

    def _add_candidate(candidate_id: str, source_family: str, directions: Optional[List[str]]) -> None:
        actionable = [
            str(item).strip()
            for item in directions or []
            if _is_actionable_rewrite_direction(item)
        ]
        if not actionable:
            return

        raw_candidates.append(
            {
                "candidate_id": candidate_id,
                "source_family": source_family,
                "is_polished": candidate_id.endswith("_polished"),
                "directions": actionable[:6],
            }
        )

    if planner_directions:
        _add_candidate("deterministic_planner", "deterministic_planner", planner_directions)
        _add_candidate(
            "deterministic_planner_polished",
            "deterministic_planner",
            _polish_selected_rewrite_directions(payload, planner_directions),
        )

    if live_directions:
        _add_candidate("live_llm", "live_llm", live_directions)
        _add_candidate(
            "live_llm_polished",
            "live_llm",
            _polish_selected_rewrite_directions(payload, live_directions),
        )

    if blended_directions:
        _add_candidate("live_llm_blended", "live_llm_blended", blended_directions)
        _add_candidate(
            "live_llm_blended_polished",
            "live_llm_blended",
            _polish_selected_rewrite_directions(payload, blended_directions),
        )

    unique_candidates: List[Dict[str, Any]] = []
    lineage: List[Dict[str, Any]] = []
    key_to_winner: Dict[tuple, Dict[str, Any]] = {}

    for candidate in raw_candidates:
        key = _candidate_directions_key(candidate.get("directions", []) or [])

        if key in key_to_winner:
            winner = key_to_winner[key]
            lineage.append(
                {
                    "candidate_id": candidate.get("candidate_id", ""),
                    "source_family": candidate.get("source_family", ""),
                    "is_polished": bool(candidate.get("is_polished")),
                    "status": "deduped_same_directions",
                    "resolved_to_candidate_id": winner.get("candidate_id", ""),
                    "resolved_to_source_family": winner.get("source_family", ""),
                    "dedupe_reason": "same_directions_as_existing_candidate",
                    "directions": list(candidate.get("directions", []) or []),
                }
            )
            continue

        audit = _rewrite_path_audit(payload, candidate["directions"])
        winner = {
            **candidate,
            "audit": audit,
        }
        key_to_winner[key] = winner
        unique_candidates.append(winner)

        lineage.append(
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "source_family": candidate.get("source_family", ""),
                "is_polished": bool(candidate.get("is_polished")),
                "status": "kept_unique",
                "resolved_to_candidate_id": candidate.get("candidate_id", ""),
                "resolved_to_source_family": candidate.get("source_family", ""),
                "dedupe_reason": "",
                "directions": list(candidate.get("directions", []) or []),
            }
        )

    return {
        "unique_candidates": unique_candidates,
        "lineage": lineage,
    }


def _best_rewrite_candidate_for_source_family(
    candidates: List[Dict[str, Any]],
    source_family: str,
    *,
    require_valid: bool = True,
) -> Optional[Dict[str, Any]]:
    filtered = [
        candidate
        for candidate in candidates
        if candidate.get("source_family") == source_family
    ]

    if require_valid:
        filtered = [
            candidate
            for candidate in filtered
            if candidate.get("audit", {}).get("covers_plan")
            and candidate.get("audit", {}).get("verifier_ok")
        ]

    if not filtered:
        return None

    filtered.sort(key=_rewrite_candidate_sort_key, reverse=True)
    return filtered[0]

def _resolved_candidate_for_source_family(
    source_family: str,
    candidate_pool: List[Dict[str, Any]],
    lineage: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    direct = _best_rewrite_candidate_for_source_family(
        candidate_pool,
        source_family,
        require_valid=False,
    )
    if direct is not None:
        return direct

    resolved_ids = [
        item.get("resolved_to_candidate_id", "")
        for item in lineage
        if item.get("source_family") == source_family
        and item.get("status") == "deduped_same_directions"
        and item.get("resolved_to_candidate_id")
    ]

    if not resolved_ids:
        return None

    for candidate in candidate_pool:
        if candidate.get("candidate_id", "") in resolved_ids:
            return candidate

    return None

def _candidate_pool_audit_rows(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for candidate in candidates:
        audit = candidate.get("audit", {}) or {}
        quality = audit.get("quality", {}) or {}

        rows.append(
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "source_family": candidate.get("source_family", ""),
                "is_polished": bool(candidate.get("is_polished")),
                "covers_plan": bool(audit.get("covers_plan")),
                "verifier_ok": bool(audit.get("verifier_ok")),
                "quality_score": int(audit.get("quality_score", 0)),
                "full_anchor_line_count": int(quality.get("full_anchor_line_count", 0)),
                "truncated_line_count": int(quality.get("truncated_line_count", 0)),
                "plannerese_line_count": int(quality.get("plannerese_line_count", 0)),
                "generic_skill_tail_count": int(quality.get("generic_skill_tail_count", 0)),
                "verifier_issues": list(audit.get("verifier_issues", []) or []),
                "directions": list(audit.get("directions", []) or []),
            }
        )

    return rows

def _choose_best_valid_rewrite_path(
    deterministic_audit: Optional[Dict[str, Any]],
    live_audit: Optional[Dict[str, Any]],
    blended_audit: Optional[Dict[str, Any]],
) -> tuple[str, str]:
    deterministic_valid = bool(
        deterministic_audit
        and deterministic_audit.get("covers_plan")
        and deterministic_audit.get("verifier_ok")
    )

    candidates: List[tuple[str, Dict[str, Any]]] = []
    for source, audit in [
        ("live_llm", live_audit),
        ("live_llm_blended", blended_audit),
    ]:
        if audit and audit.get("covers_plan") and audit.get("verifier_ok"):
            candidates.append((source, audit))

    if not candidates:
        if deterministic_valid:
            return "deterministic_planner", "no_live_candidate_passed_all_gates"
        return "deterministic", "no_valid_candidate_passed_all_gates"

    candidates.sort(
        key=lambda item: (
            int(item[1].get("quality_score", 0)),
            1 if item[0] == "live_llm" else 0,
        ),
        reverse=True,
    )
    best_source, best_audit = candidates[0]
    best_score = int(best_audit.get("quality_score", 0))

    if not deterministic_valid:
        return best_source, f"{best_source}_only_valid_candidate"

    deterministic_score = int(deterministic_audit.get("quality_score", 0))

    if best_score >= deterministic_score + 2:
        return best_source, f"{best_source}_quality_beats_deterministic"
    if (
        best_score > deterministic_score
        and best_audit.get("quality", {}).get("truncated_line_count", 0)
        < deterministic_audit.get("quality", {}).get("truncated_line_count", 0)
    ):
        return best_source, f"{best_source}_wins_on_truncation_quality"

    return "deterministic_planner", "deterministic_kept_as_quality_baseline"

def _select_operator_rewrite_directions(
    payload: Dict[str, Any],
    llm_output: Optional[Dict[str, Any]],
) -> tuple[List[str], str, Dict[str, Any]]:
    parsed = {}
    parse_ok = bool(isinstance(llm_output, dict) and llm_output.get("parse_ok"))
    if parse_ok:
        parsed = llm_output.get("parsed", {}) or {}

    planner_directions = _planner_seed_rewrite_directions(payload)

    audit: Dict[str, Any] = {
        "llm_requested": bool(llm_output is not None),
        "llm_parse_ok": parse_ok,
        "llm_strong_enough": False,
        "live_llm": None,
        "live_llm_blended": None,
        "deterministic_planner": None,
        "selected_source": "",
        "selected_reason": "",
        "fallback_reason_codes": [],
        "candidate_pool": [],
    }

    llm_directions: List[str] = []
    blended_directions: List[str] = []

    if parsed:
        raw_llm_directions = [
            str(item).strip()
            for item in parsed.get("rewrite_directions", []) or []
            if _is_actionable_rewrite_direction(item)
        ]
        llm_directions = _normalize_live_rewrite_directions(
            payload,
            raw_llm_directions,
            limit=6,
        )
        audit["llm_strong_enough"] = _llm_output_is_strong_enough(parsed)
        audit["live_llm_raw_directions"] = raw_llm_directions[:6]
        audit["live_llm_normalized_directions"] = llm_directions[:6]

        if audit["llm_strong_enough"]:
            blended = _blend_live_and_planner_directions(
                payload,
                llm_directions,
                limit=6,
            )
            blended_directions = _normalize_live_rewrite_directions(
                payload,
                blended,
                limit=6,
            )
            audit["live_llm_blended_normalized_directions"] = blended_directions[:6]
        else:
            audit["fallback_reason_codes"].append("live_llm_not_strong_enough")
    else:
        if llm_output is not None:
            audit["fallback_reason_codes"].append("live_llm_parse_failed_or_missing")

    candidate_pool_bundle = _build_rewrite_candidate_pool(
        payload,
        planner_directions,
        llm_directions if audit["llm_strong_enough"] else None,
        blended_directions if audit["llm_strong_enough"] else None,
    )
    candidate_pool = candidate_pool_bundle["unique_candidates"]
    candidate_lineage = candidate_pool_bundle["lineage"]

    audit["candidate_pool"] = _candidate_pool_audit_rows(candidate_pool)
    audit["candidate_pool_lineage"] = _candidate_pool_lineage_rows(candidate_lineage)

    best_deterministic = _best_rewrite_candidate_for_source_family(
        candidate_pool,
        "deterministic_planner",
        require_valid=True,
    )
    best_live = _best_rewrite_candidate_for_source_family(
        candidate_pool,
        "live_llm",
        require_valid=True,
    )
    best_blended = _best_rewrite_candidate_for_source_family(
        candidate_pool,
        "live_llm_blended",
        require_valid=True,
    )

    resolved_deterministic = _resolved_candidate_for_source_family(
        "deterministic_planner",
        candidate_pool,
        candidate_lineage,
    )
    resolved_live = _resolved_candidate_for_source_family(
        "live_llm",
        candidate_pool,
        candidate_lineage,
    )
    resolved_blended = _resolved_candidate_for_source_family(
        "live_llm_blended",
        candidate_pool,
        candidate_lineage,
    )

    if best_deterministic is not None:
        audit["deterministic_planner"] = best_deterministic["audit"]
    elif resolved_deterministic is not None:
        audit["deterministic_planner"] = resolved_deterministic["audit"]
    else:
        audit["deterministic_planner"] = _rewrite_path_audit(payload, planner_directions)

    audit["live_llm"] = resolved_live["audit"] if resolved_live is not None else None
    audit["live_llm_blended"] = resolved_blended["audit"] if resolved_blended is not None else None

    if audit["live_llm"] is not None:
        if not audit["live_llm"]["covers_plan"]:
            audit["fallback_reason_codes"].append("live_llm_failed_plan_coverage")
        if not audit["live_llm"]["verifier_ok"]:
            audit["fallback_reason_codes"].append("live_llm_failed_verifier")

    if audit["live_llm_blended"] is not None:
        if not audit["live_llm_blended"]["covers_plan"]:
            audit["fallback_reason_codes"].append("live_llm_blended_failed_plan_coverage")
        if not audit["live_llm_blended"]["verifier_ok"]:
            audit["fallback_reason_codes"].append("live_llm_blended_failed_verifier")

    chosen_source, chosen_reason = _choose_best_valid_rewrite_path(
        audit["deterministic_planner"],
        audit["live_llm"],
        audit["live_llm_blended"],
    )
    audit["selected_reason"] = chosen_reason

    if chosen_source == "live_llm" and best_live is not None:
        audit["selected_source"] = "live_llm"
        audit["fallback_reason_codes"] = _unique_preserve_order(audit["fallback_reason_codes"])
        return best_live["audit"]["directions"][:6], "live_llm", audit

    if chosen_source == "live_llm_blended" and best_blended is not None:
        audit["selected_source"] = "live_llm_blended"
        audit["fallback_reason_codes"] = _unique_preserve_order(audit["fallback_reason_codes"])
        return best_blended["audit"]["directions"][:6], "live_llm_blended", audit

    if chosen_source == "deterministic_planner" and best_deterministic is not None:
        audit["selected_source"] = "deterministic_planner"
        audit["fallback_reason_codes"] = _unique_preserve_order(audit["fallback_reason_codes"])
        return best_deterministic["audit"]["directions"][:6], "deterministic_planner", audit

    fallback = _fallback_rewrite_directions_from_payload(payload)
    audit["selected_source"] = "deterministic"
    audit["fallback_reason_codes"] = _unique_preserve_order(
        audit["fallback_reason_codes"] + ["deterministic_planner_empty"]
    )
    if not audit.get("selected_reason"):
        audit["selected_reason"] = "deterministic_planner_empty"
    return fallback, "deterministic", audit

def _canonical_selected_direction_for_plan_unit(
    row: Dict[str, Any],
    *,
    primary: bool,
) -> str:
    source = str(row.get("source", "") or "").strip()
    evidence_unit = str(row.get("evidence_unit", "") or "").strip()

    if not evidence_unit:
        return ""

    if primary:
        if source:
            return f"Lead with {evidence_unit} from {source}."
        return f"Lead with {evidence_unit}."
    else:
        if source:
            return f"Support with {evidence_unit} from {source} as secondary supporting evidence."
        return f"Support with {evidence_unit} as secondary supporting evidence."


def _polish_selected_rewrite_directions(
    payload: Dict[str, Any],
    directions: List[str],
) -> List[str]:
    plan = payload.get("tailoring_plan", {}) or {}
    primary_anchor_units = plan.get("primary_anchor_units", []) or []
    secondary_support_units = plan.get("secondary_support_units", []) or []

    polished: List[str] = []

    for item in directions or []:
        text = str(item or "").strip()
        prefix = _direction_prefix(text)

        if prefix == "Lead with":
            matched_primary = _best_matching_plan_unit(text, primary_anchor_units)
            if matched_primary is not None:
                polished_text = _canonical_selected_direction_for_plan_unit(
                    matched_primary,
                    primary=True,
                )
                polished.append(polished_text or text)
                continue

        if prefix == "Support with":
            matched_support = _best_matching_plan_unit(text, secondary_support_units)
            if matched_support is not None:
                polished_text = _canonical_selected_direction_for_plan_unit(
                    matched_support,
                    primary=False,
                )
                polished.append(polished_text or text)
                continue

        polished.append(text)

    return _unique_preserve_order(polished)

def _refresh_selected_rewrite_audit_after_polish(
    payload: Dict[str, Any],
    preferred_rewrite_source: str,
    preferred_rewrite_directions: List[str],
    selection_audit: Dict[str, Any],
) -> Dict[str, Any]:
    refreshed = dict(selection_audit or {})
    final_path_audit = _rewrite_path_audit(payload, preferred_rewrite_directions)

    refreshed["selected_source"] = preferred_rewrite_source

    if preferred_rewrite_source == "live_llm":
        refreshed["live_llm"] = final_path_audit
        refreshed["live_llm_normalized_directions"] = preferred_rewrite_directions[:6]
    elif preferred_rewrite_source == "live_llm_blended":
        refreshed["live_llm_blended"] = final_path_audit
        refreshed["live_llm_blended_normalized_directions"] = preferred_rewrite_directions[:6]
    elif preferred_rewrite_source == "deterministic_planner":
        refreshed["deterministic_planner"] = final_path_audit

    return refreshed

def _build_operator_markdown_payload(
    payload: Dict[str, Any],
    llm_output: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    operator_payload = dict(payload)

    preferred_rewrite_directions, preferred_rewrite_source, preferred_rewrite_selection_audit = _select_operator_rewrite_directions(
        payload,
        llm_output,
    )

    preferred_rewrite_directions = _polish_selected_rewrite_directions(
        payload,
        preferred_rewrite_directions,
    )

    preferred_rewrite_selection_audit = _refresh_selected_rewrite_audit_after_polish(
        payload,
        preferred_rewrite_source,
        preferred_rewrite_directions,
        preferred_rewrite_selection_audit,
    )

    operator_payload["preferred_rewrite_directions"] = preferred_rewrite_directions
    operator_payload["preferred_rewrite_source"] = preferred_rewrite_source
    operator_payload["preferred_rewrite_verifier"] = _rewrite_direction_verifier_report(
        payload,
        preferred_rewrite_directions,
    )
    operator_payload["preferred_rewrite_selection_audit"] = preferred_rewrite_selection_audit
    return operator_payload

def _build_tailoring_actions(packet: Dict[str, Any]) -> List[str]:
    tailoring_plan = _build_tailoring_plan(packet)

    direct_required = _direct_terms(packet, "required")
    direct_preferred = _direct_terms(packet, "preferred")

    actions: List[str] = []

    if tailoring_plan.get("narrative_angle"):
        actions.append(f"Follow this narrative angle: {tailoring_plan.get('narrative_angle')}")

    if tailoring_plan.get("direct_facets"):
        actions.append(
            f"Build the main story around these directly supported JD facets: {', '.join(_truncate_list(tailoring_plan.get('direct_facets', []), 3))}."
        )

    if tailoring_plan.get("adjacent_facets"):
        actions.append(
            f"Use these adjacent facet-support areas only as secondary framing, not as direct ownership claims: {', '.join(_truncate_list(tailoring_plan.get('adjacent_facets', []), 3))}."
        )

    if direct_required:
        actions.append(
            f"Lead the tailored version with direct-bullet required terms: {', '.join(_truncate_list(direct_required, 6))}."
        )
    elif direct_preferred:
        actions.append(
            f"Lead with the strongest directly supported preferred terms already proven in bullets: {', '.join(_truncate_list(direct_preferred, 6))}."
        )

    primary_anchor_units = tailoring_plan.get("primary_anchor_units", []) or []
    if primary_anchor_units:
        anchor_labels = _plan_unit_brief_labels(
            primary_anchor_units,
            limit=3,
            max_evidence_len=110,
        )
        actions.append(
            f"Use these evidence units as the primary anchors: {'; '.join(anchor_labels)}."
        )

    secondary_support_units = tailoring_plan.get("secondary_support_units", []) or []
    if secondary_support_units:
        support_labels = _plan_unit_brief_labels(
            secondary_support_units,
            limit=3,
            max_evidence_len=110,
        )
        actions.append(
            f"Use these secondary support units only to reinforce the main anchor story: {'; '.join(support_labels)}."
        )

    contextual_terms = tailoring_plan.get("contextual_terms_to_frame_carefully", []) or []
    if contextual_terms:
        actions.append(
            f"Use these contextual or skills-only terms carefully and never present them as direct hands-on ownership: {', '.join(_truncate_list(contextual_terms, 6))}."
        )

    adjacent_terms = tailoring_plan.get("adjacent_terms_to_keep_explicit", []) or []
    if adjacent_terms:
        actions.append(
            f"Even where related facet evidence exists, keep these exact JD terms explicit unless a bullet proves them directly: {', '.join(_truncate_list(adjacent_terms, 6))}."
        )

    true_gap_facets = tailoring_plan.get("true_gap_facets", []) or []
    if true_gap_facets:
        actions.append(
            f"Keep these true JD facet gaps explicit unless you can support them truthfully: {', '.join(_truncate_list(true_gap_facets, 3))}."
        )

    true_gap_terms = tailoring_plan.get("true_unsupported_terms", []) or []
    if true_gap_terms:
        actions.append(
            f"Keep these truly unsupported exact JD terms explicit unless you can support them truthfully: {', '.join(_truncate_list(true_gap_terms, 6))}."
        )

    return _unique_preserve_order(actions)


def _build_llm_prompt(
    packet: Dict[str, Any],
    tailoring_plan: Optional[Dict[str, Any]] = None,
) -> str:
    job = packet.get("job", {})
    selection = packet.get("selection", {})
    summary = packet.get("summary", {})
    tailoring_plan = tailoring_plan or _build_tailoring_plan(packet)

    evidence_layers = _build_evidence_layers(packet, tailoring_plan=tailoring_plan)
    rewrite_candidates = _build_rewrite_candidates(packet, tailoring_plan=tailoring_plan)

    anchor_rows = evidence_layers.get("anchors", [])[:4]
    semantic_support_rows = evidence_layers.get("supports", [])[:4]
    context_rows = evidence_layers.get("context", [])[:4]

    lines: List[str] = []

    lines.append("Return ONLY JSON that matches the required schema.")
    lines.append("")
    lines.append("Goal:")
    lines.append("Produce evidence-anchored tailoring guidance for ONE selected resume variant.")
    lines.append("")
    lines.append("Hard rules:")
    lines.append("1. Use ONLY the evidence below.")
    lines.append("2. Do NOT invent tools, methods, responsibilities, metrics, or domains.")
    lines.append("3. Treat missing unsupported skills as gaps, not rewrite opportunities.")
    lines.append("4. Prefer concrete rewrite directions tied to a specific source entry.")
    lines.append("5. Use direct-overlap bullets as primary anchors.")
    lines.append("6. Use semantic-similarity bullets only as supporting evidence.")
    lines.append("7. Use same-role/context bullets only as lowest-priority supporting context.")
    lines.append("8. Avoid generic advice like 'highlight', 'showcase', or 'emphasize' unless you name the exact supported term and source entry.")
    lines.append("9. In rewrite_directions, each item should start with one of: 'Lead with', 'Support with', 'Keep gap explicit', or 'Do not add'.")
    lines.append("10. Keep every list concise and recruiter-usable.")
    lines.append("")
    lines.append("Job:")
    lines.append(f"- Company: {job.get('company', '')}")
    lines.append(f"- Title: {job.get('title', '')}")
    lines.append("")
    lines.append("Selected resume:")
    lines.append(f"- Resume: {selection.get('selected_resume', '')}")
    lines.append(f"- Score: {selection.get('selected_score', '')}")
    lines.append("")
    lines.append("Matched / missing skills:")
    lines.append(f"- Matched required: {summary.get('matched_required', [])}")
    lines.append(f"- Missing required: {summary.get('missing_required', [])}")
    lines.append(f"- Matched preferred: {summary.get('matched_preferred', [])}")
    lines.append(f"- Missing preferred: {summary.get('missing_preferred', [])}")
    lines.append(f"- Matched terms from prefilter: {summary.get('matched_terms', [])}")
    lines.append("")
    lines.extend(_support_tier_prompt_lines(packet))
    lines.extend(_facet_prompt_lines(packet))
    lines.extend(_tailoring_plan_prompt_lines(tailoring_plan))

    lines.append("Primary anchor evidence units:")
    if anchor_rows:
        for idx, row in enumerate(anchor_rows, 1):
            lines.append(
                f"{idx}. [{row.get('section', '')}] {_display_row_source(row)} | "
                f"supports={row.get('overlaps', [])}"
            )
            lines.append(f"   Evidence unit: {_short_bullet(row.get('text', ''), 320)}")
            if row.get("parent_bullet"):
                lines.append(f"   Parent bullet: {_short_bullet(row.get('parent_bullet', ''), 320)}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("Secondary supporting evidence units:")
    if semantic_support_rows:
        for idx, row in enumerate(semantic_support_rows, 1):
            lines.append(
                f"{idx}. [{row.get('section', '')}] {_display_row_source(row)} | "
                f"type={row.get('evidence_type', '')}"
            )
            if row.get("semantic_score") is not None:
                lines.append(f"   semantic_score={row.get('semantic_score')}")
            lines.append(f"   Evidence unit: {_short_bullet(row.get('text', ''), 320)}")

            if row.get("parent_bullet"):
                lines.append(f"   Parent bullet: {_short_bullet(row.get('parent_bullet', ''), 320)}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("Same-role context evidence units:")
    if context_rows:
        for idx, row in enumerate(context_rows, 1):
            lines.append(
                f"{idx}. [{row.get('section', '')}] {_display_row_source(row)} | "
                f"type={row.get('evidence_type', '')} | supports={row.get('overlaps', [])}"
            )

            lines.append(f"   Evidence unit: {_short_bullet(row.get('text', ''), 320)}")
            if row.get("parent_bullet"):
                lines.append(f"   Parent bullet: {_short_bullet(row.get('parent_bullet', ''), 320)}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("Evidence-backed rewrite candidates:")
    if rewrite_candidates:
        for idx, row in enumerate(rewrite_candidates, 1):
            lines.append(
                f"{idx}. [{row.get('section', '')}] {row.get('source', '')} | "
                f"type={row.get('evidence_type', '')} | supports={row.get('supported_terms', [])}"
            )
            lines.append(f"   Action: {row.get('action', '')}")
            lines.append(f"   Evidence: {row.get('bullet_excerpt', '')}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("Guardrail:")
    lines.append(str(packet.get("guardrail", "")))
    lines.append("")
    lines.append("Output expectations:")
    lines.append("- recruiter_summary: 1 sentence only.")
    lines.append("- keep_emphasize: only already-supported terms or phrases.")
    lines.append("- tailoring_actions: concrete operator actions tied to the evidence above.")
    lines.append("- do_not_claim: unsupported skills, tools, or responsibilities only.")
    lines.append("- rewrite_directions: REQUIRED. Return at least 3 items if 3 or more anchor bullets exist.")
    lines.append("- At least 1 rewrite_directions item must start with 'Lead with' or 'Support with' when anchor bullets are present.")
    lines.append("- Do not return only 'Keep gap explicit' items when anchor bullets are present.")
    lines.append("- Every rewrite_directions item must start with one of: Lead with, Support with, Keep gap explicit, Do not add.")
    lines.append("- Every rewrite_directions item must reference a specific source entry from the evidence above when using Lead with or Support with.")
    lines.append("- Avoid generic actions like Ensure, Verify, Confirm, Highlight, Showcase, or Emphasize.")

    return "\n".join(lines)

def _build_live_rewrite_prompt(packet: Dict[str, Any], payload: Dict[str, Any]) -> str:
    job = packet.get("job", {})
    selection = packet.get("selection", {})
    summary = packet.get("summary", {})
    evidence_layers = payload.get("evidence_layers", {}) or {}
    anchors = evidence_layers.get("anchors", [])[:4]
    supports = evidence_layers.get("supports", [])[:4]
    context = evidence_layers.get("context", [])[:4]
    tailoring_plan = payload.get("tailoring_plan", {}) or _build_tailoring_plan(packet)

    lines: List[str] = []

    lines.append("Return ONLY valid JSON with one top-level key: rewrite_directions.")
    lines.append("")
    lines.append("Goal:")
    lines.append("Produce concrete, source-tied rewrite directions for ONE selected resume variant.")
    lines.append("")
    lines.append("Hard rules:")
    lines.append("1. Use ONLY the evidence below.")
    lines.append("2. Do NOT invent tools, methods, metrics, domains, or responsibilities.")
    lines.append("3. Direct-overlap bullets are the only primary anchors.")
    lines.append("4. Semantic-similarity bullets are support only.")
    lines.append("5. Same-role context bullets are lowest-priority support only.")
    lines.append("6. If anchor bullets exist, return at least 3 rewrite_directions.")
    lines.append("7. At least 1 rewrite_directions item must start with 'Lead with' or 'Support with' when anchor bullets exist.")
    lines.append("8. Do not return only gap-explicit directions when anchor bullets exist.")
    lines.append("9. Every Lead with / Support with item must reference a specific source entry.")
    lines.append("10. Keep gap explicit only for truly unsupported skills.")
    lines.append("")
    lines.append("Job:")
    lines.append(f"- Company: {job.get('company', '')}")
    lines.append(f"- Title: {job.get('title', '')}")
    lines.append("")
    lines.append("Selected resume:")
    lines.append(f"- Resume: {selection.get('selected_resume', '')}")
    lines.append(f"- Score: {selection.get('selected_score', '')}")
    lines.append("")
    lines.append("Matched / missing skills:")
    lines.append(f"- Matched required: {summary.get('matched_required', [])}")
    lines.append(f"- Missing required: {summary.get('missing_required', [])}")
    lines.append(f"- Missing preferred: {summary.get('missing_preferred', [])}")
    lines.append("")
    lines.extend(_support_tier_prompt_lines(packet))
    lines.extend(_facet_prompt_lines(packet))
    lines.extend(_tailoring_plan_prompt_lines(tailoring_plan))
    lines.append("Primary anchor evidence units:")
    for idx, row in enumerate(anchors, 1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] {_display_row_source(row)} | supports={row.get('overlaps', [])}"
        )
        lines.append(f"   Evidence unit: {_short_bullet(row.get('text', ''), 300)}")
        if row.get("parent_bullet"):
            lines.append(f"   Parent bullet: {_short_bullet(row.get('parent_bullet', ''), 300)}")
    lines.append("")
    lines.append("Secondary supporting evidence units:")
    for idx, row in enumerate(supports, 1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] {_display_row_source(row)} | type={row.get('evidence_type', '')}"
        )
        if row.get("semantic_score") is not None:
            lines.append(f"   semantic_score={row.get('semantic_score')}")

        lines.append(f"   Evidence unit: {_short_bullet(row.get('text', ''), 300)}")
        if row.get("parent_bullet"):
            lines.append(f"   Parent bullet: {_short_bullet(row.get('parent_bullet', ''), 300)}")

    lines.append("")
    lines.append("Same-role context evidence units:")
    for idx, row in enumerate(context, 1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] {_display_row_source(row)} | type={row.get('evidence_type', '')}"           )
        lines.append(f"   Evidence unit: {_short_bullet(row.get('text', ''), 300)}")
        if row.get("parent_bullet"):
            lines.append(f"   Parent bullet: {_short_bullet(row.get('parent_bullet', ''), 300)}")

    lines.append("")
    lines.append("Guardrail:")
    lines.append(str(packet.get("guardrail", "")))
    lines.append("")
    lines.append("Output requirements:")
    lines.append("- Return JSON only.")
    lines.append("- Output key: rewrite_directions")
    lines.append("- Allowed prefixes only: Lead with, Support with, Keep gap explicit, Do not add")
    lines.append("- Prefer anchor-led rewrite directions first, then support if needed.")

    return "\n".join(lines)

def _escape_control_chars_inside_json_strings(text: str) -> str:
    chars: List[str] = []
    in_string = False
    escape = False

    for ch in text:
        if in_string:
            if escape:
                chars.append(ch)
                escape = False
                continue

            if ch == "\\":
                chars.append(ch)
                escape = True
                continue

            if ch == '"':
                chars.append(ch)
                in_string = False
                continue

            if ch == "\n":
                chars.append("\\n")
                continue

            if ch == "\r":
                chars.append("\\r")
                continue

            if ch == "\t":
                chars.append("\\t")
                continue

            chars.append(ch)
            continue

        chars.append(ch)
        if ch == '"':
            in_string = True

    return "".join(chars)

def _extract_json_from_llm_response(response: str) -> dict:
    raw = str(response or "").strip()
    if not raw:
        raise ValueError("Empty LLM response")

    cleaned = raw.replace("```json", "```").replace("```JSON", "```")
    cleaned = cleaned.replace("```", "").strip()

    candidates: List[str] = []

    def _add_candidate(text: str) -> None:
        candidate = str(text or "").strip()
        if not candidate:
            return
        if candidate not in candidates:
            candidates.append(candidate)

        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            sliced = candidate[start:end + 1].strip()
            if sliced and sliced not in candidates:
                candidates.append(sliced)

    _add_candidate(cleaned)
    _add_candidate(_escape_control_chars_inside_json_strings(cleaned))

    last_error = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception as exc:
            last_error = exc

    raise ValueError(
        f"Could not parse LLM response as JSON. "
        f"Raw response preview: {raw[:400]!r}"
    ) from last_error


def _empty_live_llm_parsed() -> Dict[str, Any]:
    return {
        "recruiter_summary": "",
        "keep_emphasize": [],
        "tailoring_actions": [],
        "do_not_claim": [],
        "rewrite_directions": [],
    }


def _normalize_string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return _unique_preserve_order([str(item).strip() for item in value if str(item).strip()])


def _normalize_live_llm_parsed(parsed: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "recruiter_summary": str(parsed.get("recruiter_summary", "")).strip(),
        "keep_emphasize": _normalize_string_list(parsed.get("keep_emphasize", [])),
        "tailoring_actions": _normalize_string_list(parsed.get("tailoring_actions", [])),
        "do_not_claim": _normalize_string_list(parsed.get("do_not_claim", [])),
        "rewrite_directions": _normalize_string_list(parsed.get("rewrite_directions", [])),
    }

def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _compute_live_llm_cache_meta(packet: Dict[str, Any]) -> Dict[str, Any]:
    packet_sha256 = _sha256_text(_canonical_json(packet))

    job_doc_id = str(
        packet.get("job_doc_id")
        or packet.get("job_id")
        or ""
    ).strip()

    selected_resume = str(
        packet.get("selected_resume")
        or packet.get("selected_resume_name")
        or packet.get("resume_name")
        or ""
    ).strip()

    cache_key_material = _canonical_json(
        {
            "job_doc_id": job_doc_id,
            "selected_resume": selected_resume,
            "packet_sha256": packet_sha256,
            "requested_provider": LLM_TAILOR_PROVIDER,
            "requested_model": LLM_TAILOR_MODEL,
            "fallback_enabled": TAILOR_LLM_FALLBACK_ENABLED,
            "fallback_provider": TAILOR_LLM_FALLBACK_PROVIDER if TAILOR_LLM_FALLBACK_ENABLED else "",
            "fallback_model": TAILOR_LLM_FALLBACK_MODEL if TAILOR_LLM_FALLBACK_ENABLED else "",
            "prompt_version": LLM_TAILOR_PROMPT_VERSION,
        }
    )

    return {
        "job_doc_id": job_doc_id,
        "selected_resume": selected_resume,
        "packet_sha256": packet_sha256,
        "cache_key": _sha256_text(cache_key_material),
        "prompt_version": LLM_TAILOR_PROMPT_VERSION,
        "requested_provider": LLM_TAILOR_PROVIDER,
        "requested_model": LLM_TAILOR_MODEL,
        "fallback_enabled": TAILOR_LLM_FALLBACK_ENABLED,
        "fallback_provider": TAILOR_LLM_FALLBACK_PROVIDER if TAILOR_LLM_FALLBACK_ENABLED else "",
        "fallback_model": TAILOR_LLM_FALLBACK_MODEL if TAILOR_LLM_FALLBACK_ENABLED else "",
    }


def _load_live_llm_cache(
    output_llm_json: str,
    expected_meta: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if not output_llm_json:
        return None

    path = Path(output_llm_json)
    if not path.exists():
        return None

    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(cached, dict):
        return None

    if not cached.get("parse_ok"):
        return None

    if cached.get("cache_key") != expected_meta["cache_key"]:
        return None

    if cached.get("packet_sha256") != expected_meta["packet_sha256"]:
        return None

    if cached.get("requested_provider") != expected_meta["requested_provider"]:
        return None

    if cached.get("requested_model") != expected_meta["requested_model"]:
        return None

    if cached.get("fallback_enabled") != expected_meta["fallback_enabled"]:
        return None

    if cached.get("fallback_provider") != expected_meta["fallback_provider"]:
        return None

    if cached.get("fallback_model") != expected_meta["fallback_model"]:
        return None

    if cached.get("prompt_version") != LLM_TAILOR_PROMPT_VERSION:
        return None

    cached["cache_hit"] = True
    return cached


def _attach_live_llm_cache_meta(
    result: Dict[str, Any],
    cache_meta: Dict[str, Any],
    *,
    cache_hit: bool,
) -> Dict[str, Any]:
    enriched = dict(result)
    enriched.update(cache_meta)
    enriched["cache_hit"] = cache_hit
    enriched.setdefault(
        "generated_at",
        datetime.now(timezone.utc).isoformat(),
    )
    return enriched

def _run_live_llm_tailoring(
    packet: Dict[str, Any],
    payload: Dict[str, Any],
    output_llm_json: str = "",
    refresh_llm_cache: bool = False,
) -> Dict[str, Any]:
    cache_meta = _compute_live_llm_cache_meta(packet)

    if not refresh_llm_cache:
        cached_result = _load_live_llm_cache(
            output_llm_json=output_llm_json,
            expected_meta=cache_meta,
        )
        if cached_result is not None:
            return cached_result

    prompt = payload["live_rewrite_prompt"]

#     primary_system_prompt = """
# You generate evidence-anchored resume tailoring JSON.

# You MUST obey these rules:
# 1. Return content that is fully grounded in the supplied packet evidence.
# 2. Do NOT invent tools, methods, metrics, skills, domains, or responsibilities.
# 3. Direct-overlap bullets are the only primary anchors for rewrite advice.
# 4. Semantic-similarity bullets are supporting evidence only; use them to reinforce an anchor, not to replace it.
# 5. Same-role or adjacent-context bullets are lowest-priority support and should only reinforce the same story.
# 6. Prefer rewrite_directions that follow the pattern: one anchor bullet first, then one support bullet if needed.
# 7. At least one rewrite_directions item must start with 'Lead with' or 'Support with' when anchor bullets are present.
# 8. Do not return only gap-explicit rewrite directions when anchor bullets are present.
# 9. rewrite_directions must be concrete and source-tied, not vague writing advice.
# 10. Do not use generic action verbs like Ensure, Verify, Confirm, Highlight, Showcase, or Emphasize.
# 11. Keep recruiter_summary to one sentence.
# 12. Keep lists concise, practical, and recruiter-usable.
# """

    primary_system_prompt = """
You generate evidence-anchored resume rewrite directions.

You MUST obey these rules:
1. Return ONLY JSON with one top-level key: rewrite_directions.
2. Use ONLY the supplied evidence.
3. Do NOT invent tools, methods, metrics, skills, domains, or responsibilities.
4. Direct-overlap bullets are the only primary anchors.
5. Semantic-similarity bullets are support only.
6. Same-role or adjacent-context bullets are lowest-priority support only.
7. If anchor bullets exist, return at least 3 rewrite_directions.
8. At least 1 rewrite_directions item must start with 'Lead with' or 'Support with' when anchor bullets exist.
9. Do not return only gap-explicit rewrite directions when anchor bullets exist.
10. Every Lead with / Support with item must reference a specific source entry.
11. Use only these prefixes: Lead with, Support with, Keep gap explicit, Do not add.
"""

#     retry_system_prompt = """
# You are returning JSON for a strict Python parser.

# You MUST obey these rules:
# 1. Return ONLY valid JSON.
# 2. Do NOT return markdown, code fences, commentary, or explanatory text.
# 3. Keep the entire JSON on a single line.
# 4. Do NOT include literal newlines, carriage returns, or tabs inside any string value.
# 5. Use empty arrays instead of null.
# 6. Keep recruiter_summary to exactly 1 sentence.
# 7. Keep each list short and concrete.
# 8. Use ONLY the supplied evidence. Do NOT invent anything.
# 9. rewrite_directions is REQUIRED and must contain at least 3 concrete items when anchor bullets are present.
# 10. At least 1 rewrite_directions item must start with 'Lead with' or 'Support with' when anchor bullets are present.
# 11. Do not return only gap-explicit rewrite directions when anchor bullets are present.
# 12. Do not use generic action verbs like Ensure, Verify, Confirm, Highlight, Showcase, or Emphasize.
# """

    retry_system_prompt = """
You are returning JSON for a strict Python parser.

You MUST obey these rules:
1. Return ONLY valid JSON.
2. Do NOT return markdown, code fences, commentary, or explanatory text.
3. Keep the entire JSON on a single line.
4. Do NOT include literal newlines, carriage returns, or tabs inside any string value.
5. Use empty arrays instead of null.
6. Output ONLY one top-level key: rewrite_directions.
7. rewrite_directions is REQUIRED and must contain at least 3 concrete items when anchor bullets are present.
8. At least 1 rewrite_directions item must start with 'Lead with' or 'Support with' when anchor bullets are present.
9. Do not return only gap-explicit rewrite directions when anchor bullets are present.
10. Use ONLY the supplied evidence. Do NOT invent anything.
"""

    fallback_attempted = bool(
        TAILOR_LLM_FALLBACK_ENABLED
        and LLM_TAILOR_PROVIDER != TAILOR_LLM_FALLBACK_PROVIDER
    )
    attempted_providers = [LLM_TAILOR_PROVIDER]
    if fallback_attempted:
        attempted_providers.append(TAILOR_LLM_FALLBACK_PROVIDER)

    def _call_llm(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return run_chat_completion_with_metadata(
            provider=LLM_TAILOR_PROVIDER,
            model=LLM_TAILOR_MODEL,
            temperature=LLM_TAILOR_TEMPERATURE,
            max_tokens=LLM_TAILOR_MAX_TOKENS,
            response_mime_type="application/json",
            response_schema=LIVE_REWRITE_RESPONSE_SCHEMA,
            return_parsed=True,
            thinking_budget=0,
            fallback_enabled=TAILOR_LLM_FALLBACK_ENABLED,
            fallback_provider=TAILOR_LLM_FALLBACK_PROVIDER,
            fallback_model=TAILOR_LLM_FALLBACK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

    def _raw_text(value: Any) -> str:
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False, default=str)
        return str(value or "").strip()

    def _base_result_meta(result_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result_meta = result_meta or {}
        resolved_provider = str(result_meta.get("provider", "") or "").strip()
        resolved_model = str(result_meta.get("model", "") or "").strip()
        fallback_used = bool(result_meta.get("fallback_used", False))

        return {
            "requested_provider": LLM_TAILOR_PROVIDER,
            "requested_model": LLM_TAILOR_MODEL,
            "provider": resolved_provider or LLM_TAILOR_PROVIDER,
            "model": resolved_model or LLM_TAILOR_MODEL,
            "resolved_provider": resolved_provider,
            "resolved_model": resolved_model,
            "fallback_used": fallback_used,
            "fallback_attempted": fallback_attempted,
            "fallback_provider": TAILOR_LLM_FALLBACK_PROVIDER if TAILOR_LLM_FALLBACK_ENABLED else "",
            "fallback_model": TAILOR_LLM_FALLBACK_MODEL if TAILOR_LLM_FALLBACK_ENABLED else "",
            "attempted_providers": _unique_preserve_order(
                [LLM_TAILOR_PROVIDER, TAILOR_LLM_FALLBACK_PROVIDER if fallback_used else ""]
                if resolved_provider
                else attempted_providers
            ),
        }

    def _success_result(
        llm_result: Dict[str, Any],
        *,
        retry_used: bool,
        raw_response: str,
        retry_raw_response: str,
    ) -> Dict[str, Any]:
        value = llm_result.get("content")

        if isinstance(value, dict):
            normalized = _normalize_live_llm_parsed(value)
            return _attach_live_llm_cache_meta(
                {
                    **_base_result_meta(llm_result),
                    "parse_ok": True,
                    "parse_error": "",
                    "retry_used": retry_used,
                    "raw_response": raw_response,
                    "retry_raw_response": retry_raw_response,
                    "parsed": normalized,
                },
                cache_meta,
                cache_hit=False,
            )

        raw = _raw_text(value)
        parsed = _extract_json_from_llm_response(raw)
        normalized = _normalize_live_llm_parsed(parsed)
        return _attach_live_llm_cache_meta(
            {
                **_base_result_meta(llm_result),
                "parse_ok": True,
                "parse_error": "",
                "retry_used": retry_used,
                "raw_response": raw_response,
                "retry_raw_response": retry_raw_response,
                "parsed": normalized,
            },
            cache_meta,
            cache_hit=False,
        )

    try:
        primary_result = _call_llm(primary_system_prompt, prompt)
    except Exception as exc:
        return _attach_live_llm_cache_meta(
            {
                **_base_result_meta(),
                "parse_ok": False,
                "parse_error": f"Primary LLM call failed: {exc}",
                "retry_used": False,
                "raw_response": "",
                "retry_raw_response": "",
                "parsed": _empty_live_llm_parsed(),
            },
            cache_meta,
            cache_hit=False,
        )

    primary_response = primary_result.get("content")
    primary_raw = _raw_text(primary_response)

    try:
        return _success_result(
            primary_result,
            retry_used=False,
            raw_response=primary_raw,
            retry_raw_response="",
        )
    except Exception as primary_parse_exc:
        retry_prompt = (
            "Return EXACTLY one-line valid JSON only for the task below. "
            "No markdown. No code fences. No commentary. "
            "No literal newline characters inside string values. "
            "Use empty arrays when needed.\n\n"
            f"{prompt}"
        )

        try:
            retry_result = _call_llm(retry_system_prompt, retry_prompt)
        except Exception as retry_exc:
            return _attach_live_llm_cache_meta(
                {
                    **_base_result_meta(),
                    "parse_ok": False,
                    "parse_error": (
                        f"Primary parse failed: {primary_parse_exc}. "
                        f"Retry LLM call failed: {retry_exc}"
                    ),
                    "retry_used": True,
                    "raw_response": primary_raw,
                    "retry_raw_response": "",
                    "parsed": _empty_live_llm_parsed(),
                },
                cache_meta,
                cache_hit=False,
            )

        retry_response = retry_result.get("content")
        retry_raw = _raw_text(retry_response)

        try:
            return _success_result(
                retry_result,
                retry_used=True,
                raw_response=primary_raw,
                retry_raw_response=retry_raw,
            )
        except Exception as retry_parse_exc:
            return _attach_live_llm_cache_meta(
                {
                    **_base_result_meta(retry_result),
                    "parse_ok": False,
                    "parse_error": (
                        f"Primary parse failed: {primary_parse_exc}. "
                        f"Retry parse failed: {retry_parse_exc}"
                    ),
                    "retry_used": True,
                    "raw_response": primary_raw,
                    "retry_raw_response": retry_raw,
                    "parsed": _empty_live_llm_parsed(),
                },
                cache_meta,
                cache_hit=False,
            )

def _build_payload(packet: Dict[str, Any]) -> Dict[str, Any]:
    recruiter_summary = _build_recruiter_summary(packet)
    keep_emphasize = _build_keep_emphasize(packet)
    do_not_claim = _build_do_not_claim(packet)
    bullet_reuse = _build_bullet_reuse(packet)
    tailoring_plan = _build_tailoring_plan(packet)
    rewrite_candidates = _build_rewrite_candidates(packet, tailoring_plan=tailoring_plan)
    evidence_layers = _build_evidence_layers(packet, tailoring_plan=tailoring_plan)
    tailoring_actions = _build_tailoring_actions(packet)
    llm_prompt = _build_llm_prompt(packet, tailoring_plan=tailoring_plan)
    live_rewrite_prompt = _build_live_rewrite_prompt(
        packet,
        {
            "rewrite_candidates": rewrite_candidates,
            "evidence_layers": evidence_layers,
            "tailoring_plan": tailoring_plan,
        },
    )

    return {
        "job": packet.get("job", {}),
        "selection": packet.get("selection", {}),
        "summary": packet.get("summary", {}),
        "recruiter_summary": recruiter_summary,
        "keep_emphasize": keep_emphasize,
        "tailoring_actions": tailoring_actions,
        "tailoring_plan": tailoring_plan,
        "rewrite_candidates": rewrite_candidates,
        "evidence_layers": evidence_layers,
        "planner_seed_rewrite_directions": _planner_seed_rewrite_directions(
            {
                "tailoring_plan": tailoring_plan,
                "rewrite_candidates": rewrite_candidates,
            }
        ),
        "do_not_claim": do_not_claim,
        "bullet_reuse_candidates": bullet_reuse,
        "llm_prompt": llm_prompt,
        "live_rewrite_prompt": live_rewrite_prompt,
        "guardrail": packet.get(
            "guardrail",
            "Only add or strengthen resume language when it is already truthful and supported by your actual work.",
        ),
    }


def _markdown_from_payload(payload: Dict[str, Any]) -> str:
    job = payload.get("job", {})
    selection = payload.get("selection", {})
    tailoring_plan = payload.get("tailoring_plan", {}) or {}
    lines: List[str] = []

    lines.append(f"# Tailoring Suggestions")
    lines.append("")
    lines.append(f"**Job:** {job.get('company', '')} | {job.get('title', '')}")
    lines.append(f"**Selected resume:** {selection.get('selected_resume', '')}")
    lines.append(f"**Selected score:** {selection.get('selected_score', 0.0):.3f}")
    lines.append("")

    lines.append("## Recruiter Summary")
    lines.append(payload.get("recruiter_summary", ""))
    lines.append("")

    lines.append("## Keep / Emphasize")
    for item in payload.get("keep_emphasize", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Tailoring Actions")
    for item in payload.get("tailoring_actions", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Tailoring Plan")
    lines.append(f"- Narrative angle: {tailoring_plan.get('narrative_angle', '')}")
    lines.append(f"- Compatibility mode: {tailoring_plan.get('compatibility_mode', False)}")
    lines.append(f"- Compatibility reason: {tailoring_plan.get('compatibility_reason', '')}")
    lines.append(f"- Direct facets: {tailoring_plan.get('direct_facets', [])}")
    lines.append(f"- Adjacent facets: {tailoring_plan.get('adjacent_facets', [])}")
    lines.append(f"- True gap facets: {tailoring_plan.get('true_gap_facets', [])}")
    lines.append(f"- Primary facet coverage: {tailoring_plan.get('primary_facet_coverage', [])}")
    lines.append(f"- Secondary facet coverage: {tailoring_plan.get('secondary_facet_coverage', [])}")
    lines.append(
        f"- Contextual terms to frame carefully: {tailoring_plan.get('contextual_terms_to_frame_carefully', [])}"
    )
    lines.append(
        f"- Adjacent terms to keep explicit: {tailoring_plan.get('adjacent_terms_to_keep_explicit', [])}"
    )
    lines.append(
        f"- True unsupported terms: {tailoring_plan.get('true_unsupported_terms', [])}"
    )
    lines.append("")

    lines.append("## Priority Rewrite Directions")
    lines.append(f"- Source: {payload.get('preferred_rewrite_source', 'deterministic')}")
    for item in payload.get("preferred_rewrite_directions", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Planner Seed Rewrite Directions")
    for item in payload.get("planner_seed_rewrite_directions", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Evidence-Backed Rewrite Ideas")
    for row in payload.get("rewrite_candidates", []):
        lines.append(
            f"- **[{row.get('section', '')}] {row.get('source', '')}** | "
            f"type={row.get('evidence_type', '')} | supports={row.get('supported_terms', [])}"
        )
        lines.append(f"  - Action: {row.get('action', '')}")
        lines.append(f"  - Evidence unit: {row.get('bullet_excerpt', '')}")
        if row.get("parent_bullet"):
            lines.append(f"  - Parent bullet: {row.get('parent_bullet', '')}")
    lines.append("")

    lines.append("## Do Not Claim")
    for item in payload.get("do_not_claim", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Bullet Reuse Candidates")
    for row in payload.get("bullet_reuse_candidates", []):
        lines.append(
            f"- **[{row.get('section', '')}] {row.get('source', '')}** | "
            f"type={row.get('evidence_type', '')} | overlaps={row.get('overlaps', [])}"
        )
        lines.append(f"  - Evidence unit: {row.get('bullet', '')}")
        if row.get("parent_bullet"):
            lines.append(f"  - Parent bullet: {row.get('parent_bullet', '')}")
        lines.append(f"  - Reuse note: {row.get('reuse_note', '')}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate grounded tailoring suggestions from a JD diff packet."
    )
    parser.add_argument(
        "--packet-json",
        required=True,
        help="Path to one JD diff packet JSON.",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path to write the tailoring suggestions JSON.",
    )
    parser.add_argument(
        "--output-md",
        default="",
        help="Optional path to write the tailoring suggestions Markdown.",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Run a live grounded LLM tailoring pass on top of the deterministic payload.",
    )
    parser.add_argument(
        "--output-llm-json",
        default="",
        help="Optional path to write the live LLM tailoring output JSON.",
    )
    parser.add_argument(
        "--refresh-llm-cache",
        action="store_true",
        help="Ignore any existing live LLM cache and regenerate the LLM tailoring output.",
    )
    args = parser.parse_args()

    packet = _load_packet(Path(args.packet_json))
    payload = _build_payload(packet)
    final_payload = _build_operator_markdown_payload(payload, None)
    markdown = _markdown_from_payload(final_payload)

    print("=" * 100)
    print("GROUNDED TAILORING SUGGESTIONS")
    print("=" * 100)
    print(f"JOB: {payload['job'].get('company', '')} | {payload['job'].get('title', '')}")
    print(f"SELECTED RESUME: {payload['selection'].get('selected_resume', '')}")
    print()

    print("-" * 100)
    print("RECRUITER SUMMARY")
    print("-" * 100)
    print(payload["recruiter_summary"])
    print()

    print("-" * 100)
    print("KEEP / EMPHASIZE")
    print("-" * 100)
    for item in payload["keep_emphasize"]:
        print(f"- {item}")
    print()

    print("-" * 100)
    print("TAILORING ACTIONS")
    print("-" * 100)
    for item in payload["tailoring_actions"]:
        print(f"- {item}")
    print()

    print("-" * 100)
    print("EVIDENCE-BACKED REWRITE IDEAS")
    print("-" * 100)
    for row in payload.get("rewrite_candidates", []):
        print(
            f"- [{row.get('section', '')}] {row.get('source', '')} | "
            f"type={row.get('evidence_type', '')} | supports={row.get('supported_terms', [])}"
        )
        print(f"  Action: {row.get('action', '')}")
        print(f"  Evidence: {row.get('bullet_excerpt', '')}")
    print()

    print("-" * 100)
    print("EVIDENCE LAYERS")
    print("-" * 100)
    evidence_layers = payload.get("evidence_layers", {})
    for label in ["anchors", "supports", "context"]:
        print(label.upper())
        for row in evidence_layers.get(label, []):
            print(f"- {_source_label(row)} | {row.get('evidence_type')}")
        print()

    print("-" * 100)
    print("DO NOT CLAIM")
    print("-" * 100)
    for item in payload["do_not_claim"]:
        print(f"- {item}")
    print()

    output_json_path = None
    if args.output_json.strip():
        output_json_path = Path(args.output_json)

    output_md_path = None
    if args.output_md.strip():
        output_md_path = Path(args.output_md)
    
    if args.use_llm:
        llm_output = _run_live_llm_tailoring(
            packet=packet,
            payload=payload,
            output_llm_json=args.output_llm_json or "",
            refresh_llm_cache=args.refresh_llm_cache,
        )

        print("-" * 100)
        print("LIVE LLM TAILORING OUTPUT")
        print("-" * 100)
        print(f"Requested provider: {llm_output.get('requested_provider', '')}")
        print(f"Requested model: {llm_output.get('requested_model', '')}")
        print(f"Resolved provider: {llm_output.get('resolved_provider', '') or '<none>'}")
        print(f"Resolved model: {llm_output.get('resolved_model', '') or '<none>'}")
        print(f"Fallback used: {llm_output.get('fallback_used', False)}")
        print(f"Parse OK: {llm_output['parse_ok']}")
        print(f"Cache hit: {llm_output.get('cache_hit', False)}")
        if llm_output["parse_error"]:
            print(f"Parse error: {llm_output['parse_error']}")
        print()

        parsed = llm_output["parsed"]

        if llm_output["parse_ok"]:
            print("Recruiter summary:")
            print(parsed.get("recruiter_summary", ""))
            print()

            print("Keep / emphasize:")
            for item in parsed.get("keep_emphasize", []):
                print(f"- {item}")
            print()

            print("Tailoring actions:")
            for item in parsed.get("tailoring_actions", []):
                print(f"- {item}")
            print()

            print("Do not claim:")
            for item in parsed.get("do_not_claim", []):
                print(f"- {item}")
            print()

            print("Rewrite directions:")
            for item in llm_output["parsed"].get("rewrite_directions", []):
                print(f"- {item}")
        else:
            print("Raw response preview:")
            print(llm_output["raw_response"][:1200])
            print()

        if args.output_llm_json.strip():
            output_llm_json_path = Path(args.output_llm_json)
            output_llm_json_path.write_text(
                json.dumps(llm_output, indent=2),
                encoding="utf-8",
            )
            print(f"LLM JSON written: {output_llm_json_path}")
        
        final_payload = _build_operator_markdown_payload(payload, llm_output)
        markdown = _markdown_from_payload(final_payload)

        if output_json_path is not None:
            output_json_path.write_text(json.dumps(final_payload, indent=2), encoding="utf-8")
            print(f"JSON written: {output_json_path}")

        if output_md_path is not None:
            output_md_path.write_text(markdown, encoding="utf-8")
            print(
                f"Markdown written with {final_payload.get('preferred_rewrite_source', 'deterministic')} rewrite directions: "
                f"{args.output_md}"
            )

    if not args.use_llm:
        if output_json_path is not None:
            output_json_path.write_text(json.dumps(final_payload, indent=2), encoding="utf-8")
            print(f"JSON written: {output_json_path}")

        if output_md_path is not None:
            output_md_path.write_text(markdown, encoding="utf-8")
            print(f"Markdown written: {args.output_md}")

if __name__ == "__main__":
    main()