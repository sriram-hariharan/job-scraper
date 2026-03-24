from typing import Dict, List, Any
import json
from pathlib import Path

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
        or row.get("facet_context_evidence")
        or row.get("context_terms")
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

def _is_clause_unit(row: Dict[str, Any]) -> bool:
    return str(row.get("unit_kind", "")).strip() == "clause_unit"

def _display_row_source(row: Dict[str, Any]) -> str:
    source = str(row.get("source", "") or "").strip()
    if source:
        return source
    return _source_label(row)

def _direction_mentions_any(direction: str, values: List[str]) -> bool:
    text = str(direction or "").strip().lower()
    if not text:
        return False

    for value in values or []:
        candidate = str(value or "").strip().lower()
        if candidate and candidate in text:
            return True

    return False