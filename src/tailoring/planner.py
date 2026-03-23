from typing import List, Dict, Any, Optional

from src.tailoring.packet_support import (
    _source_label,
    _row_supported_terms,
    _short_bullet,
    _unique_preserve_order,
    _truncate_list,
    _facet_display_name,
    _rewrite_source_rows,
    _top_direct_facets,
    _top_adjacent_facets,
    _top_gap_facets,
    _direct_terms,
    _contextual_terms,
    _skills_only_terms,
    _adjacent_unsupported_terms,
    _true_gap_terms,
    _direction_mentions_any,
)

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

