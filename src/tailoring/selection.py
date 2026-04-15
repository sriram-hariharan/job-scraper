from typing import List, Dict, Any, Optional

from src.config.consts import REWRITE_DIRECTION_PREFIXES

from src.tailoring.family_matcher import (
    canonical_guardrail_targets,
    guardrail_coverage_targets,
    supported_family_hits,
    supported_term_hits,
)

from src.tailoring.packet_support import (
    _rewrite_source_rows,
    _source_label,
    _row_supported_terms,
    _is_clause_unit,
    _row_evidence_excerpt,
    _short_bullet,
    _truncate_list,
    _unique_preserve_order,
    _direction_mentions_any,
)

from src.tailoring.planner import (
    _plan_unit_key,
    _find_rewrite_row_for_plan_unit,
    _plan_row_key,
    _plan_unit_to_direction,
    _planner_seed_rewrite_directions,
    _fallback_rewrite_directions_from_payload,
)

def _build_bullet_reuse_from_plan_units(
    tailoring_plan: Dict[str, Any],
    limit: int = 6,
) -> List[Dict[str, Any]]:
    rows = (
        list(tailoring_plan.get("primary_anchor_units", []) or [])
        + list(tailoring_plan.get("secondary_support_units", []) or [])
    )[:limit]

    reuse_rows: List[Dict[str, Any]] = []

    for row in rows:
        evidence_type = str(row.get("evidence_type", "") or "").strip() or "same_source_context"
        overlaps = list(row.get("supported_terms", []) or [])
        source = str(row.get("source", "") or "").strip()

        if evidence_type == "direct_overlap":
            reuse_note = (
                "Use this as a primary anchor bullet recovered from packet evidence and keep the JD-facing terms earlier in the wording."
            )
        elif evidence_type == "same_source_context":
            reuse_note = (
                "Use this as supporting context recovered from packet evidence so the main anchor story feels more credible."
            )
        else:
            reuse_note = (
                "Use this as nearby supporting context only if it strengthens the same story truthfully."
            )

        reuse_rows.append(
            {
                "section": row.get("section", ""),
                "source": source,
                "overlaps": overlaps,
                "evidence_type": evidence_type,
                "bullet": row.get("evidence_unit", ""),
                "parent_bullet": row.get("parent_bullet", ""),
                "reuse_note": reuse_note,
                "entry_id": row.get("entry_id", ""),
                "entry_index": row.get("entry_index", -1),
                "bullet_id": row.get("bullet_id", ""),
                "bullet_index": row.get("bullet_index", -1),
            }
        )

    return reuse_rows

def _build_bullet_reuse(
    packet: Dict[str, Any],
    tailoring_plan: Optional[Dict[str, Any]] = None,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    tailoring_plan = tailoring_plan or {}
    rows = _rewrite_source_rows(packet)

    if not rows:
        return _build_bullet_reuse_from_plan_units(
            tailoring_plan,
            limit=limit,
        )

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
                "entry_id": row.get("entry_id", ""),
                "entry_index": row.get("entry_index", -1),
                "bullet_id": row.get("bullet_id", ""),
                "bullet_index": row.get("bullet_index", -1),
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
            row.get("bullet_id", ""),
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

        focused_evidence = str(row.get("clause_text") or row.get("text", "") or "").strip()
        parent_bullet = str(row.get("parent_bullet", "") or "").strip()
        full_evidence = parent_bullet or focused_evidence

        candidates.append(
            {
                "source": source,
                "section": row.get("section", ""),
                "evidence_type": evidence_type,
                "supported_terms": supported_terms[:6],
                "action": action,
                "bullet_excerpt": _row_evidence_excerpt(row),
                "current_evidence": full_evidence,
                "original_text": full_evidence,
                "focused_clause_text": focused_evidence,
                "parent_bullet": parent_bullet or full_evidence,
                "entry_id": row.get("entry_id", ""),
                "entry_index": row.get("entry_index", -1),
                "bullet_id": row.get("bullet_id", ""),
                "bullet_index": row.get("bullet_index", -1),
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

    full_evidence = parent_bullet or evidence_unit

    return {
        "source": source,
        "section": unit.get("section", ""),
        "evidence_type": "direct_overlap" if primary else "same_source_context",
        "supported_terms": supported_terms[:6],
        "action": action,
        "bullet_excerpt": _short_bullet(evidence_unit, 220),
        "current_evidence": full_evidence,
        "original_text": full_evidence,
        "focused_clause_text": evidence_unit,
        "parent_bullet": parent_bullet or full_evidence,
        "entry_id": unit.get("entry_id", ""),
        "entry_index": unit.get("entry_index", -1),
        "bullet_id": unit.get("bullet_id", ""),
        "bullet_index": unit.get("bullet_index", -1),
    }

def _direction_plan_unit_match_score(direction: str, row: Dict[str, Any]) -> int:
    text = str(direction or "").strip()
    if not text:
        return 0

    score = 0

    source = str(row.get("source", "") or "").strip()
    if source and _direction_mentions_any(text, [source]):
        score += 3

    supported_terms = [
        str(term).strip()
        for term in (row.get("supported_terms", []) or [])
        if str(term).strip()
    ]

    raw_hits = supported_term_hits(text, supported_terms)
    family_hits = supported_family_hits(text, supported_terms)

    score += len(raw_hits)
    if not raw_hits:
        score += len(family_hits)

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
    adjacent_targets = guardrail_coverage_targets(adjacent_terms, adjacent_facets)
    if adjacent_targets:
        if not any(
            item.startswith("Do not add") and _direction_mentions_any(item, adjacent_targets)
            for item in actionable
        ):
            return False

    true_gap_terms = plan.get("true_unsupported_terms", []) or []
    true_gap_facets = plan.get("true_gap_facets", []) or []
    true_gap_targets = guardrail_coverage_targets(true_gap_terms, true_gap_facets)
    if true_gap_targets:
        if not any(
            item.startswith("Keep gap explicit") and _direction_mentions_any(item, true_gap_targets)
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
    adjacent_facets = list(plan.get("adjacent_facets", []) or [])
    true_gap_terms = list(plan.get("true_unsupported_terms", []) or [])
    true_gap_facets = list(plan.get("true_gap_facets", []) or [])

    adjacent_targets = canonical_guardrail_targets(adjacent_terms, adjacent_facets)
    true_gap_targets = canonical_guardrail_targets(true_gap_terms, true_gap_facets)

    actionable = [
        _strip_wrapped_clause_quotes(str(item).strip())
        for item in directions or []
        if _is_actionable_rewrite_direction(item)
    ]

    promoted_candidates: List[str] = []
    for item in actionable:
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

            if primary_match is not None and primary_score >= 4 and primary_score > secondary_score:
                item = _replace_direction_prefix(item, "Lead with")

        promoted_candidates.append(item)

    def _best_candidate_for_unit(
        unit: Dict[str, Any],
        allowed_prefixes: set[str],
    ) -> str:
        best_text = ""
        best_score = 0

        for item in promoted_candidates:
            prefix = _direction_prefix(item)
            if prefix not in allowed_prefixes:
                continue

            score = _direction_plan_unit_match_score(item, unit)
            if score > best_score:
                best_score = score
                best_text = item

        if best_score >= 4 and best_text:
            return best_text
        return ""

    normalized: List[str] = []

    # Rebuild required primary anchors in plan order.
    for unit in primary_anchor_units:
        candidate = _best_candidate_for_unit(unit, {"Lead with"})
        if candidate:
            normalized.append(candidate)
        else:
            fallback = _plan_unit_to_direction(unit, primary=True)
            if fallback:
                normalized.append(fallback)

    # Rebuild only the required secondary support coverage.
    if secondary_support_units:
        first_secondary = secondary_support_units[0]
        candidate = _best_candidate_for_unit(first_secondary, {"Support with"})
        if candidate:
            normalized.append(candidate)
        else:
            fallback = _plan_unit_to_direction(first_secondary, primary=False)
            if fallback:
                normalized.append(fallback)

    # Always include required adjacent-support guardrail coverage.
    if adjacent_targets:
        canonical_adjacent = _canonical_adjacent_guardrail_direction(adjacent_targets)
        if canonical_adjacent:
            normalized.append(canonical_adjacent)

    # Always include required true-gap coverage.
    if true_gap_targets:
        canonical_true_gap = _canonical_true_gap_direction(true_gap_targets)
        if canonical_true_gap:
            normalized.append(canonical_true_gap)

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


def _direction_supported_term_hits(direction: str, unit: Dict[str, Any]) -> List[str]:
    text = str(direction or "").strip()
    supported_terms = [
        str(term).strip()
        for term in (unit.get("supported_terms", []) or [])
        if str(term).strip()
    ]

    raw_hits = supported_term_hits(text, supported_terms)
    if raw_hits:
        return raw_hits

    return supported_family_hits(text, supported_terms)


def _direction_mentions_unit_source(direction: str, unit: Dict[str, Any]) -> bool:
    text = str(direction or "").strip()
    source = str(unit.get("source", "") or "").strip()
    return bool(source and _direction_mentions_any(text, [source]))


def _direction_mentions_unit_evidence(direction: str, unit: Dict[str, Any]) -> bool:
    text = str(direction or "").strip()
    evidence_unit = str(unit.get("evidence_unit", "") or "").strip()
    if not evidence_unit:
        return False

    evidence_markers = [
        evidence_unit[:80],
        _short_bullet(evidence_unit, 140),
    ]
    return _direction_mentions_any(text, evidence_markers)


def _best_direction_match_for_unit(
    directions: List[str],
    unit: Dict[str, Any],
    allowed_prefixes: set[str],
) -> Dict[str, Any]:
    best_direction = ""
    best_match_score = 0
    best_supported_term_hits: List[str] = []
    best_mentions_source = False
    best_mentions_evidence = False

    for item in directions or []:
        prefix = _direction_prefix(item)
        if prefix not in allowed_prefixes:
            continue

        match_score = _direction_plan_unit_match_score(item, unit)
        if match_score <= 0:
            continue

        supported_term_hits = _direction_supported_term_hits(item, unit)
        mentions_source = _direction_mentions_unit_source(item, unit)
        mentions_evidence = _direction_mentions_unit_evidence(item, unit)

        sort_key = (
            match_score,
            len(supported_term_hits),
            1 if mentions_source else 0,
            1 if mentions_evidence else 0,
            1 if not _direction_has_truncation(item) else 0,
            1 if not _direction_has_plannerese(item) else 0,
            1 if not _direction_has_generic_skill_tail(item) else 0,
        )
        best_sort_key = (
            best_match_score,
            len(best_supported_term_hits),
            1 if best_mentions_source else 0,
            1 if best_mentions_evidence else 0,
            1 if not _direction_has_truncation(best_direction) else 0,
            1 if not _direction_has_plannerese(best_direction) else 0,
            1 if not _direction_has_generic_skill_tail(best_direction) else 0,
        )

        if sort_key > best_sort_key:
            best_direction = item
            best_match_score = match_score
            best_supported_term_hits = supported_term_hits
            best_mentions_source = mentions_source
            best_mentions_evidence = mentions_evidence

    return {
        "direction": best_direction,
        "match_score": best_match_score,
        "supported_term_hits": best_supported_term_hits,
        "supported_term_hit_count": len(best_supported_term_hits),
        "mentions_source": best_mentions_source,
        "mentions_evidence": best_mentions_evidence,
    }


def _rewrite_direction_quality_report(
    payload: Dict[str, Any],
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

    plan = payload.get("tailoring_plan", {}) or {}
    primary_anchor_units = plan.get("primary_anchor_units", []) or []
    secondary_support_units = plan.get("secondary_support_units", []) or []

    unit_matches: List[Dict[str, Any]] = []
    for idx, unit in enumerate(primary_anchor_units):
        match = _best_direction_match_for_unit(actionable, unit, {"Lead with"})
        match["bucket"] = "primary_anchor"
        match["unit_index"] = idx
        unit_matches.append(match)

    if secondary_support_units:
        match = _best_direction_match_for_unit(
            actionable,
            secondary_support_units[0],
            {"Support with"},
        )
        match["bucket"] = "secondary_support"
        match["unit_index"] = 0
        unit_matches.append(match)

    matched_required_unit_count = sum(1 for item in unit_matches if item.get("direction"))
    strong_required_unit_count = sum(
        1
        for item in unit_matches
        if item.get("direction")
        and int(item.get("match_score", 0)) >= 7
        and int(item.get("supported_term_hit_count", 0)) > 0
    )
    supported_term_hit_count = sum(
        int(item.get("supported_term_hit_count", 0))
        for item in unit_matches
    )
    source_mention_count = sum(1 for item in unit_matches if item.get("mentions_source"))
    evidence_mention_count = sum(1 for item in unit_matches if item.get("mentions_evidence"))

    plan_units = primary_anchor_units + (secondary_support_units[:1] if secondary_support_units else [])
    weak_anchor_lines = [
        item for item in lead_support_lines
        if not any(_direction_supported_term_hits(item, unit) for unit in plan_units)
    ]

    score = (
        2 * len(full_anchor_lines)
        + 2 * matched_required_unit_count
        + 3 * strong_required_unit_count
        + 1 * supported_term_hit_count
        + 1 * source_mention_count
        + 1 * evidence_mention_count
        - 2 * len(truncated_lines)
        - 2 * len(plannerese_lines)
        - 1 * len(generic_skill_tail_lines)
        - 2 * len(weak_anchor_lines)
    )

    return {
        "score": score,
        "full_anchor_line_count": len(full_anchor_lines),
        "matched_required_unit_count": matched_required_unit_count,
        "strong_required_unit_count": strong_required_unit_count,
        "supported_term_hit_count": supported_term_hit_count,
        "source_mention_count": source_mention_count,
        "evidence_mention_count": evidence_mention_count,
        "weak_anchor_line_count": len(weak_anchor_lines),
        "truncated_line_count": len(truncated_lines),
        "plannerese_line_count": len(plannerese_lines),
        "generic_skill_tail_count": len(generic_skill_tail_lines),
        "truncated_lines": truncated_lines,
        "plannerese_lines": plannerese_lines,
        "generic_skill_tail_lines": generic_skill_tail_lines,
        "weak_anchor_lines": weak_anchor_lines,
        "unit_matches": unit_matches,
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
    quality = _rewrite_direction_quality_report(payload, actionable)

    return {
        "count": len(actionable),
        "covers_plan": covers_plan,
        "verifier_ok": bool(verifier.get("ok")),
        "verifier_issues": list(verifier.get("issues", []) or []),
        "quality_score": quality.get("score", 0),
        "quality": quality,
        "directions": actionable[:6],
    }

def _deterministic_candidate_preference_rank(candidate: Dict[str, Any]) -> int:
    candidate_id = str(candidate.get("candidate_id", "") or "").strip()

    preference = {
        "deterministic_planner_term_first": 5,
        "deterministic_planner_evidence_first": 4,
        "deterministic_planner_mixed": 3,
        "deterministic_planner": 2,
        "deterministic_planner_polished": 1,
    }

    return preference.get(candidate_id, 0)

def _rewrite_candidate_sort_key(candidate: Dict[str, Any]) -> tuple:
    audit = candidate.get("audit", {}) or {}
    quality = audit.get("quality", {}) or {}

    return (
        int(audit.get("quality_score", 0)),
        int(quality.get("matched_required_unit_count", 0)),
        int(quality.get("strong_required_unit_count", 0)),
        int(quality.get("supported_term_hit_count", 0)),
        int(quality.get("source_mention_count", 0)),
        int(quality.get("evidence_mention_count", 0)),
        int(quality.get("full_anchor_line_count", 0)),
        -int(quality.get("weak_anchor_line_count", 0)),
        -int(quality.get("truncated_line_count", 0)),
        -int(quality.get("plannerese_line_count", 0)),
        -int(quality.get("generic_skill_tail_count", 0)),
        _deterministic_candidate_preference_rank(candidate),
        1 if candidate.get("is_polished") else 0,
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

def _terminal_resolved_candidate_id(
    candidate_id: str,
    lineage: List[Dict[str, Any]],
) -> str:
    candidate_id = str(candidate_id or "").strip()
    if not candidate_id:
        return ""

    lineage_by_candidate = {
        str(item.get("candidate_id", "") or "").strip(): item
        for item in lineage or []
        if str(item.get("candidate_id", "") or "").strip()
    }

    seen = set()
    current = candidate_id

    while current and current not in seen:
        seen.add(current)
        row = lineage_by_candidate.get(current)
        if not row:
            return current

        status = str(row.get("status", "") or "").strip()
        resolved_to = str(row.get("resolved_to_candidate_id", "") or "").strip()

        if not resolved_to or resolved_to == current or status == "kept_unique":
            return current

        current = resolved_to

    return current

def _equivalent_candidate_ids_for_selected_candidate(
    selected_candidate_id: str,
    candidate_pool: List[Dict[str, Any]],
    lineage: List[Dict[str, Any]],
) -> List[str]:
    selected_candidate_id = str(selected_candidate_id or "").strip()
    if not selected_candidate_id:
        return []

    candidate_by_id = {
        str(candidate.get("candidate_id", "") or "").strip(): candidate
        for candidate in candidate_pool or []
        if str(candidate.get("candidate_id", "") or "").strip()
    }

    selected_terminal = _terminal_resolved_candidate_id(
        selected_candidate_id,
        lineage,
    )
    selected_candidate = (
        candidate_by_id.get(selected_terminal)
        or candidate_by_id.get(selected_candidate_id)
    )
    if selected_candidate is None:
        return []

    selected_sort_key = _rewrite_candidate_sort_key(selected_candidate)
    equivalent_terminal_ids = set()

    for candidate in candidate_pool or []:
        candidate_id = str(candidate.get("candidate_id", "") or "").strip()
        if not candidate_id:
            continue

        audit = candidate.get("audit", {}) or {}
        if not (audit.get("covers_plan") and audit.get("verifier_ok")):
            continue

        if _rewrite_candidate_sort_key(candidate) != selected_sort_key:
            continue

        terminal_id = _terminal_resolved_candidate_id(candidate_id, lineage) or candidate_id
        if terminal_id:
            equivalent_terminal_ids.add(terminal_id)

    if selected_terminal:
        equivalent_terminal_ids.add(selected_terminal)

    equivalent: List[str] = []
    for item in lineage or []:
        candidate_id = str(item.get("candidate_id", "") or "").strip()
        if not candidate_id:
            continue

        candidate_terminal = _terminal_resolved_candidate_id(candidate_id, lineage)
        if candidate_terminal in equivalent_terminal_ids:
            equivalent.append(candidate_id)

    return _unique_preserve_order(equivalent)

def _planner_guardrail_directions(directions: List[str]) -> List[str]:
    rows: List[str] = []

    for item in directions or []:
        text = str(item or "").strip()
        if not _is_actionable_rewrite_direction(text):
            continue

        prefix = _direction_prefix(text)
        if prefix not in {"Lead with", "Support with"}:
            rows.append(text)

    return _unique_preserve_order(rows)


def _structured_direction_from_plan_unit(
    prefix: str,
    unit: Dict[str, Any],
    *,
    mode: str = "term_first",
) -> str:
    source = str(unit.get("source", "") or "").strip()
    evidence_unit = str(unit.get("evidence_unit", "") or "").strip()
    supported_terms = [
        str(term).strip()
        for term in (unit.get("supported_terms", []) or [])
        if str(term).strip()
    ]
    supported_text = ", ".join(supported_terms)

    if mode == "evidence_first":
        head_parts = [prefix]
        if source and supported_text:
            head_parts.append(f"{source} evidence for {supported_text}:")
        elif source:
            head_parts.append(f"{source} evidence:")
        elif supported_text:
            head_parts.append(f"evidence for {supported_text}:")
        else:
            head_parts.append("evidence:")

        text = " ".join(head_parts).strip()
        if evidence_unit:
            text = f"{text} {evidence_unit}".strip()
        return text

    head_parts = [prefix]
    if supported_text:
        head_parts.append(supported_text)

    if source:
        head_parts.append(f"from {source}:")
    elif supported_text:
        head_parts.append(":")

    text = " ".join(head_parts).replace(" :", ":").strip()
    if evidence_unit:
        text = f"{text} {evidence_unit}".strip()

    return text


def _planner_structured_candidate_variants(
    payload: Dict[str, Any],
    planner_directions: List[str],
) -> List[Dict[str, Any]]:
    plan = payload.get("tailoring_plan", {}) or {}
    primary_anchor_units = list(plan.get("primary_anchor_units", []) or [])
    secondary_support_units = list(plan.get("secondary_support_units", []) or [])
    guardrails = _planner_guardrail_directions(planner_directions)

    if not primary_anchor_units:
        return []

    variants: List[Dict[str, Any]] = []

    def _emit(candidate_id: str, lead_mode: str, support_mode: str) -> None:
        rows: List[str] = []

        for unit in primary_anchor_units[:3]:
            line = _structured_direction_from_plan_unit(
                "Lead with",
                unit,
                mode=lead_mode,
            )
            if line:
                rows.append(line)

        for unit in secondary_support_units[:1]:
            line = _structured_direction_from_plan_unit(
                "Support with",
                unit,
                mode=support_mode,
            )
            if line:
                rows.append(line)

        rows.extend(guardrails[:2])
        rows = _unique_preserve_order(
            [
                str(item).strip()
                for item in rows
                if _is_actionable_rewrite_direction(item)
            ]
        )

        if not rows:
            return

        variants.append(
            {
                "candidate_id": candidate_id,
                "source_family": "deterministic_planner",
                "directions": rows[:6],
            }
        )

    _emit(
        "deterministic_planner_term_first",
        "term_first",
        "term_first",
    )
    _emit(
        "deterministic_planner_evidence_first",
        "evidence_first",
        "evidence_first",
    )
    _emit(
        "deterministic_planner_mixed",
        "term_first",
        "evidence_first",
    )

    return variants

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

        for candidate in _planner_structured_candidate_variants(payload, planner_directions):
            _add_candidate(
                candidate["candidate_id"],
                candidate["source_family"],
                candidate["directions"],
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

    candidate_by_id = {
        str(candidate.get("candidate_id", "") or "").strip(): candidate
        for candidate in candidate_pool or []
        if str(candidate.get("candidate_id", "") or "").strip()
    }

    family_rows = [
        item for item in lineage or []
        if item.get("source_family") == source_family
    ]

    resolved_candidates: List[Dict[str, Any]] = []
    seen_ids = set()

    for item in family_rows:
        candidate_id = str(item.get("candidate_id", "") or "").strip()
        if not candidate_id:
            continue

        terminal_id = _terminal_resolved_candidate_id(candidate_id, lineage)
        if not terminal_id or terminal_id in seen_ids:
            continue

        candidate = candidate_by_id.get(terminal_id)
        if candidate is None:
            continue

        seen_ids.add(terminal_id)
        resolved_candidates.append(candidate)

    if not resolved_candidates:
        return None

    resolved_candidates.sort(key=_rewrite_candidate_sort_key, reverse=True)
    return resolved_candidates[0]

def _effective_best_candidate_for_source_family(
    source_family: str,
    candidate_pool: List[Dict[str, Any]],
    lineage: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    candidate_by_id = {
        str(candidate.get("candidate_id", "") or "").strip(): candidate
        for candidate in candidate_pool or []
        if str(candidate.get("candidate_id", "") or "").strip()
    }

    family_rows = [
        row for row in lineage or []
        if row.get("source_family") == source_family
    ]
    if not family_rows:
        return None

    resolved_candidates: List[Dict[str, Any]] = []
    seen_ids = set()

    for row in family_rows:
        candidate_id = str(row.get("candidate_id", "") or "").strip()
        if not candidate_id:
            continue

        terminal_id = _terminal_resolved_candidate_id(candidate_id, lineage)
        if not terminal_id or terminal_id in seen_ids:
            continue

        candidate = candidate_by_id.get(terminal_id)
        if candidate is None:
            continue

        seen_ids.add(terminal_id)
        resolved_candidates.append(candidate)

    if not resolved_candidates:
        return None

    resolved_candidates.sort(key=_rewrite_candidate_sort_key, reverse=True)
    return resolved_candidates[0]

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
                "matched_required_unit_count": int(quality.get("matched_required_unit_count", 0)),
                "strong_required_unit_count": int(quality.get("strong_required_unit_count", 0)),
                "supported_term_hit_count": int(quality.get("supported_term_hit_count", 0)),
                "source_mention_count": int(quality.get("source_mention_count", 0)),
                "evidence_mention_count": int(quality.get("evidence_mention_count", 0)),
                "full_anchor_line_count": int(quality.get("full_anchor_line_count", 0)),
                "weak_anchor_line_count": int(quality.get("weak_anchor_line_count", 0)),
                "truncated_line_count": int(quality.get("truncated_line_count", 0)),
                "plannerese_line_count": int(quality.get("plannerese_line_count", 0)),
                "generic_skill_tail_count": int(quality.get("generic_skill_tail_count", 0)),
                "verifier_issues": list(audit.get("verifier_issues", []) or []),
                "directions": list(audit.get("directions", []) or []),
            }
        )

    return rows

def _choose_best_valid_rewrite_path(
    deterministic_candidate: Optional[Dict[str, Any]],
    live_candidate: Optional[Dict[str, Any]],
    blended_candidate: Optional[Dict[str, Any]],
) -> tuple[str, str]:
    deterministic_audit = (deterministic_candidate or {}).get("audit", {}) or {}
    live_audit = (live_candidate or {}).get("audit", {}) or {}
    blended_audit = (blended_candidate or {}).get("audit", {}) or {}

    deterministic_valid = bool(
        deterministic_candidate
        and deterministic_audit.get("covers_plan")
        and deterministic_audit.get("verifier_ok")
    )

    candidates: List[tuple[str, Dict[str, Any], Dict[str, Any]]] = []
    for source, candidate, audit in [
        ("live_llm", live_candidate, live_audit),
        ("live_llm_blended", blended_candidate, blended_audit),
    ]:
        if candidate and audit.get("covers_plan") and audit.get("verifier_ok"):
            candidates.append((source, candidate, audit))

    if not candidates:
        if deterministic_valid:
            return "deterministic_planner", "no_live_candidate_passed_all_gates"
        return "deterministic", "no_valid_candidate_passed_all_gates"

    candidates.sort(
        key=lambda item: _rewrite_candidate_sort_key(item[1]),
        reverse=True,
    )
    best_source, best_candidate, best_audit = candidates[0]
    best_score = int(best_audit.get("quality_score", 0))

    if not deterministic_valid:
        return best_source, f"{best_source}_only_valid_candidate"

    deterministic_score = int(deterministic_audit.get("quality_score", 0))
    deterministic_key = _candidate_directions_key(
        (deterministic_candidate or {}).get("audit", {}).get("directions", []) or []
    )
    best_key = _candidate_directions_key(best_audit.get("directions", []) or [])

    if best_key and deterministic_key and best_key == deterministic_key:
        return "deterministic_planner", "deterministic_kept_as_identical_best_candidate"

    deterministic_sort_key = _rewrite_candidate_sort_key(deterministic_candidate)
    best_sort_key = _rewrite_candidate_sort_key(best_candidate)

    if best_sort_key == deterministic_sort_key:
        return "deterministic_planner", "deterministic_kept_as_equivalent_quality_candidate"

    best_quality = best_audit.get("quality", {}) or {}
    deterministic_quality = deterministic_audit.get("quality", {}) or {}

    if int(best_quality.get("matched_required_unit_count", 0)) > int(
        deterministic_quality.get("matched_required_unit_count", 0)
    ):
        return best_source, f"{best_source}_wins_on_required_unit_coverage"

    if int(best_quality.get("strong_required_unit_count", 0)) > int(
        deterministic_quality.get("strong_required_unit_count", 0)
    ):
        return best_source, f"{best_source}_wins_on_anchor_fidelity"

    if int(best_quality.get("supported_term_hit_count", 0)) > int(
        deterministic_quality.get("supported_term_hit_count", 0)
    ):
        return best_source, f"{best_source}_wins_on_supported_term_specificity"

    if best_score >= deterministic_score + 2:
        return best_source, f"{best_source}_quality_beats_deterministic"

    if (
        best_score > deterministic_score
        and best_quality.get("truncated_line_count", 0)
        < deterministic_quality.get("truncated_line_count", 0)
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
        audit["llm_strong_enough"] = _llm_output_is_strong_enough(parsed)
        audit["live_llm_raw_directions"] = raw_llm_directions[:6]

        if audit["llm_strong_enough"] and raw_llm_directions:
            llm_directions = _normalize_live_rewrite_directions(
                payload,
                raw_llm_directions,
                limit=6,
            )
            audit["live_llm_normalized_directions"] = llm_directions[:6]

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
            llm_directions = []
            blended_directions = []
            audit["live_llm_normalized_directions"] = []
            audit["live_llm_blended_normalized_directions"] = []
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

    effective_deterministic = _effective_best_candidate_for_source_family(
        "deterministic_planner",
        candidate_pool,
        candidate_lineage,
    )
    effective_live = _effective_best_candidate_for_source_family(
        "live_llm",
        candidate_pool,
        candidate_lineage,
    )
    effective_blended = _effective_best_candidate_for_source_family(
        "live_llm_blended",
        candidate_pool,
        candidate_lineage,
    )

    chosen_source, chosen_reason = _choose_best_valid_rewrite_path(
        effective_deterministic,
        effective_live,
        effective_blended,
    )
    audit["selected_reason"] = chosen_reason

    if chosen_source == "live_llm" and best_live is not None:
        audit["selected_source"] = "live_llm"
        audit["selected_candidate_id"] = best_live.get("candidate_id", "")
        audit["selected_equivalent_candidate_ids"] = _equivalent_candidate_ids_for_selected_candidate(
            best_live.get("candidate_id", ""),
            candidate_pool,
            candidate_lineage,
        )
        audit["fallback_reason_codes"] = _unique_preserve_order(audit["fallback_reason_codes"])
        return best_live["audit"]["directions"][:6], "live_llm", audit

    if chosen_source == "live_llm_blended" and best_blended is not None:
        audit["selected_source"] = "live_llm_blended"
        audit["selected_candidate_id"] = best_blended.get("candidate_id", "")
        audit["selected_equivalent_candidate_ids"] = _equivalent_candidate_ids_for_selected_candidate(
            best_blended.get("candidate_id", ""),
            candidate_pool,
            candidate_lineage,
        )
        audit["fallback_reason_codes"] = _unique_preserve_order(audit["fallback_reason_codes"])
        return best_blended["audit"]["directions"][:6], "live_llm_blended", audit

    if chosen_source == "deterministic_planner" and best_deterministic is not None:
        audit["selected_source"] = "deterministic_planner"
        audit["selected_candidate_id"] = best_deterministic.get("candidate_id", "")
        audit["selected_equivalent_candidate_ids"] = _equivalent_candidate_ids_for_selected_candidate(
            best_deterministic.get("candidate_id", ""),
            candidate_pool,
            candidate_lineage,
        )
        audit["fallback_reason_codes"] = _unique_preserve_order(audit["fallback_reason_codes"])
        return best_deterministic["audit"]["directions"][:6], "deterministic_planner", audit

    fallback = _fallback_rewrite_directions_from_payload(payload)
    audit["selected_source"] = "deterministic"
    audit["selected_candidate_id"] = ""
    audit["selected_equivalent_candidate_ids"] = []
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


