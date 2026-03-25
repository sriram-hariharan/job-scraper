from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
import hashlib
import json
import copy

from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.document_store import load_resume_documents_by_name
from src.resume.evidence_builder import (
    build_resume_evidence,
    build_counterfactual_resume_evidence,
)

from src.tailoring.packet_support import (
    _top_direct_facets,
    _top_adjacent_facets,
    _top_gap_facets,
    _direct_terms,
    _contextual_terms,
    _skills_only_terms,
    _unsupported_terms,
    _adjacent_unsupported_terms,
    _true_gap_terms,
    _unique_preserve_order,
    _truncate_list,
    _facet_display_name,
)

from src.tailoring.planner import (
    _build_tailoring_plan,
    _plan_unit_brief_labels,
    _planner_seed_rewrite_directions,
)

from src.tailoring.selection import (
    _build_bullet_reuse,
    _build_rewrite_candidates,
    _build_evidence_layers,
    _select_operator_rewrite_directions,
    _polish_selected_rewrite_directions,
    _refresh_selected_rewrite_audit_after_polish,
    _rewrite_direction_verifier_report,
)

from src.matching.signal_family_matcher import (
    family_for_term,
    families_for_terms,
    prioritized_family_terms_from_text,
    supported_signal_match_in_text,
)

_PROMOTABLE_SIGNAL_FAMILY_LABELS = {
    "experimentation": "Experimentation",
    "analytics_ml": "Modeling",
}

_PROMOTABLE_SIGNAL_FAMILY_REQUIRED_DIMENSIONS = {
    "experimentation": {"experimentation_depth"},
    "analytics_ml": {"analytics_ml_depth"},
}

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

def _display_resume_name(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "The selected resume"

    base = raw.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if base.lower().endswith(".pdf"):
        base = base[:-4]

    return base.replace("_", " ")

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

def _build_claim_safety_notes(
    packet: Dict[str, Any],
    tailoring_plan: Dict[str, Any],
) -> Dict[str, Any]:
    safe_to_strengthen = _unique_preserve_order(
        _direct_terms(packet, "required") + _direct_terms(packet, "preferred")
    )
    frame_carefully = _unique_preserve_order(
        _contextual_terms(packet, "required")
        + _contextual_terms(packet, "preferred")
        + _skills_only_terms(packet, "required")
        + _skills_only_terms(packet, "preferred")
        + list(tailoring_plan.get("adjacent_terms_to_keep_explicit", []) or [])
    )
    do_not_add = _unique_preserve_order(
        _unsupported_terms(packet, "required")
        + _unsupported_terms(packet, "preferred")
        + list(tailoring_plan.get("true_unsupported_terms", []) or [])
    )

    return {
        "safe_to_strengthen": _truncate_list(safe_to_strengthen, 8),
        "frame_carefully": _truncate_list(frame_carefully, 8),
        "do_not_add": _truncate_list(do_not_add, 8),
        "guardrail": packet.get(
            "guardrail",
            "Only add or strengthen resume language when it is already truthful and supported by your actual work.",
        ),
    }


def _build_material_gaps(
    packet: Dict[str, Any],
    tailoring_plan: Dict[str, Any],
    limit: int = 6,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    seen = set()

    for facet in tailoring_plan.get("true_gap_facets", []) or []:
        label = _facet_display_name(facet)
        norm = label.strip().lower()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        items.append(
            {
                "gap_type": "facet",
                "label": label,
                "severity": "high",
                "guidance": "This is a real JD gap. Do not invent it. Only address it if you have truthful evidence elsewhere.",
            }
        )
        if len(items) >= limit:
            return items

    for term in _true_gap_terms(packet):
        label = str(term or "").strip()
        norm = label.lower()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        items.append(
            {
                "gap_type": "exact_term",
                "label": label,
                "severity": "high",
                "guidance": "This exact JD term is not directly supported. Leave it out unless you can prove it truthfully.",
            }
        )
        if len(items) >= limit:
            break

    return items


def _build_keep_as_is(
    keep_emphasize: List[str],
    bullet_reuse: List[Dict[str, Any]],
    limit: int = 4,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for row in bullet_reuse:
        if row.get("evidence_type") != "direct_overlap":
            continue

        items.append(
            {
                "section": row.get("section", ""),
                "source": row.get("source", ""),
                "reason": "This already looks like a strong anchor. Keep the evidence, and only tighten wording if it improves JD alignment without changing the claim.",
                "evidence": row.get("bullet", "") or row.get("parent_bullet", ""),
                "overlaps": row.get("overlaps", []) or [],
                "entry_id": row.get("entry_id", ""),
                "entry_index": row.get("entry_index", -1),
                "bullet_id": row.get("bullet_id", ""),
                "bullet_index": row.get("bullet_index", -1),
            }
        )
        if len(items) >= limit:
            return items

    for item in keep_emphasize[:limit]:
        items.append(
            {
                "section": "",
                "source": "",
                "reason": str(item or "").strip(),
                "evidence": "",
                "overlaps": [],
            }
        )

    return items[:limit]

def _build_keep_visible_now(
    keep_as_is: List[Dict[str, Any]],
    limit: int = 3,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for row in keep_as_is[:limit]:
        label_parts = [
            str(row.get("section", "") or "").strip(),
            str(row.get("source", "") or "").strip(),
        ]
        label = " • ".join(part for part in label_parts if part)

        overlaps = [
            str(item or "").strip()
            for item in (row.get("overlaps", []) or [])
            if str(item or "").strip()
        ]

        items.append(
            {
                "label": label,
                "evidence": str(row.get("evidence", "") or "").strip(),
                "reason": str(row.get("reason", "") or "").strip(),
                "overlaps": _truncate_list(overlaps, 4),
            }
        )

    return items


def _build_resume_limitation_summary(
    packet: Dict[str, Any],
    blocker_labels: List[str],
    direct_terms: List[str],
    adjacent_terms: List[str],
) -> str:
    selection = packet.get("selection", {}) or {}
    resume_name = _display_resume_name(selection.get("selected_resume", ""))

    if direct_terms and blocker_labels:
        return (
            f"{resume_name} already has some direct JD-aligned evidence, but it still does not show grounded "
            f"bullet proof for {', '.join(_truncate_list(blocker_labels, 3))}."
        )

    if blocker_labels:
        return (
            f"{resume_name} is missing grounded bullet evidence for {', '.join(_truncate_list(blocker_labels, 3))}, "
            "so this is a keep-visible and gap-explicit case, not a rewrite-heavy case."
        )

    if adjacent_terms:
        return (
            f"{resume_name} has related context for {', '.join(_truncate_list(adjacent_terms, 3))}, "
            "but not enough bullet-level proof to recommend stronger rewrite claims safely."
        )

    return (
        f"{resume_name} does not provide enough bullet-level evidence for stronger tailoring edits on this JD."
    )

def _build_empty_state_reason(
    packet: Dict[str, Any],
    tailoring_plan: Dict[str, Any],
    rewrite_candidates: List[Dict[str, Any]],
    bullet_reuse: List[Dict[str, Any]],
    keep_as_is: List[Dict[str, Any]],
    claim_safety_notes: Dict[str, Any],
    material_gaps: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if rewrite_candidates or bullet_reuse:
        return {}

    direct_terms = _unique_preserve_order(
        _direct_terms(packet, "required") + _direct_terms(packet, "preferred")
    )
    frame_carefully = _unique_preserve_order(
        list(claim_safety_notes.get("frame_carefully", []) or [])
    )
    do_not_add = _unique_preserve_order(
        list(claim_safety_notes.get("do_not_add", []) or [])
    )
    blocker_labels = _unique_preserve_order(
        [
            str(item.get("label", "")).strip()
            for item in material_gaps
            if str(item.get("label", "")).strip()
        ]
        + list(tailoring_plan.get("true_unsupported_terms", []) or [])
    )

    keep_visible_now = _build_keep_visible_now(keep_as_is, limit=3)

    adjacent_facets = _top_adjacent_facets(packet, limit=6)
    adjacent_evidence_backed = [
        row for row in adjacent_facets
        if row.get("facet_direct_evidence") or row.get("facet_context_evidence") or row.get("context_terms")
    ]
    adjacent_useful_terms = _unique_preserve_order(
        [
            str(term).strip()
            for row in adjacent_evidence_backed
            for term in (
                list(row.get("job_terms", []) or [])
                + list(row.get("facet_context_terms", []) or [])
                + list(row.get("context_terms", []) or [])
            )
            if str(term).strip()
        ]
    )

    resume_limitation_summary = _build_resume_limitation_summary(
        packet,
        blocker_labels,
        direct_terms,
        adjacent_useful_terms or frame_carefully,
    )

    if direct_terms:
        return {
            "code": "keep_existing_direct_evidence",
            "title": "The best evidence is already in place",
            "summary": (
                "This resume already has some direct JD-aligned evidence, but there is no additional "
                "bullet-level rewrite target strong enough to recommend safely."
            ),
            "main_blockers": _truncate_list(blocker_labels, 6),
            "still_useful": _truncate_list(direct_terms, 6),
            "next_step": (
                "Keep the strongest matching bullets visible and focus on ordering, emphasis, "
                "and truthful positioning rather than adding new JD claims."
            ),
            "missing_jd_focus": _truncate_list(blocker_labels, 6),
            "keep_visible_now": keep_visible_now,
            "resume_limitation_summary": resume_limitation_summary,
        }

    adjacent_facets = _top_adjacent_facets(packet, limit=6)
    adjacent_evidence_backed = [
        row for row in adjacent_facets
        if row.get("facet_direct_evidence") or row.get("facet_context_evidence") or row.get("context_terms")
    ]

    if adjacent_evidence_backed:
        useful_terms = _unique_preserve_order(
            [
                str(term).strip()
                for row in adjacent_evidence_backed
                for term in (
                    list(row.get("job_terms", []) or [])
                    + list(row.get("facet_context_terms", []) or [])
                    + list(row.get("context_terms", []) or [])
                )
                if str(term).strip()
            ]
        )

        return {
            "code": "adjacent_support_only",
            "title": "Only adjacent support was found",
            "summary": (
                "There is related context, but not enough bullet-level proof to turn it into a safe rewrite."
            ),
            "main_blockers": _truncate_list(blocker_labels, 6),
            "still_useful": _truncate_list(useful_terms or frame_carefully, 6),
            "next_step": (
                "Use those areas only as secondary framing, and keep unsupported JD language explicit "
                "unless a bullet proves it directly."
            ),
            "missing_jd_focus": _truncate_list(blocker_labels, 6),
            "keep_visible_now": keep_visible_now,
            "resume_limitation_summary": resume_limitation_summary,
        }

    if blocker_labels or do_not_add:
        return {
            "code": "material_gap_without_anchor",
            "title": "Material gaps are still blocking safe edits",
            "summary": (
                "The selected resume does not show enough grounded bullet evidence for the missing JD areas, "
                "so the safest output is to keep those gaps explicit."
            ),
            "main_blockers": _truncate_list(blocker_labels or do_not_add, 6),
            "still_useful": [],
            "next_step": (
                "Do not invent missing skills or ownership claims. Keep the strongest existing evidence visible "
                "and address true gaps only if you can support them truthfully."
            ),
            "missing_jd_focus": _truncate_list(blocker_labels or do_not_add, 6),
            "keep_visible_now": keep_visible_now,
            "resume_limitation_summary": resume_limitation_summary,
        }

    return {
        "code": "no_grounded_rewrite_evidence",
        "title": "No grounded rewrite anchors were found",
        "summary": (
            "This JD/resume pair does not have enough bullet-level evidence to suggest safe rewrite edits."
        ),
        "main_blockers": [],
        "still_useful": [],
        "next_step": (
            "Keep the current resume truthful. Add JD language only where your existing experience actually proves it."
        ),
        "missing_jd_focus": [],
        "keep_visible_now": keep_visible_now,
        "resume_limitation_summary": resume_limitation_summary,
    }

def _fallback_recommended_rewrite_from_reuse(
    preferred_rewrite_directions: List[str],
    row: Dict[str, Any],
) -> str:
    overlaps = [
        str(item or "").strip().lower()
        for item in (row.get("overlaps", []) or [])
        if str(item or "").strip()
    ]
    source = str(row.get("source", "") or "").strip().lower()
    reuse_note = str(row.get("reuse_note", "") or "").strip()

    for direction in preferred_rewrite_directions or []:
        direction_text = str(direction or "").strip()
        direction_lower = direction_text.lower()

        if overlaps and any(term in direction_lower for term in overlaps):
            return direction_text
        if source and source in direction_lower:
            return direction_text

    if reuse_note:
        return reuse_note

    if overlaps:
        return (
            f"Keep this bullet, but tighten the wording so "
            f"{', '.join(_truncate_list(overlaps, 4))} shows up earlier and more clearly."
        )

    return "Keep this bullet, but sharpen the wording around the strongest JD-aligned evidence already present."


def _fallback_why_current_is_weak_from_reuse(row: Dict[str, Any]) -> str:
    overlaps = row.get("overlaps", []) or []
    evidence_type = str(row.get("evidence_type", "") or "").strip()

    if overlaps:
        if evidence_type == "direct_overlap":
            return (
                f"This bullet already overlaps with {', '.join(_truncate_list(overlaps, 4))}, "
                "but the overlap is not yet doing enough work up front."
            )
        return (
            f"This bullet is directionally useful for {', '.join(_truncate_list(overlaps, 4))}, "
            "but it currently reads more like background support than a strong JD-facing anchor."
        )

    return "This bullet is relevant, but the JD-facing signal is still too muted."


def _fallback_why_rewrite_is_better_from_reuse(row: Dict[str, Any]) -> str:
    overlaps = row.get("overlaps", []) or []
    if overlaps:
        return (
            f"It surfaces {', '.join(_truncate_list(overlaps, 4))} earlier without adding any unsupported claim."
        )
    return "It improves JD alignment while staying anchored to evidence already in the resume."


def _fallback_why_it_matters_from_reuse(row: Dict[str, Any]) -> str:
    overlaps = row.get("overlaps", []) or []
    evidence_type = str(row.get("evidence_type", "") or "").strip()

    if overlaps and evidence_type == "direct_overlap":
        return (
            f"This is already one of the strongest truthful anchors for {', '.join(_truncate_list(overlaps, 4))}."
        )
    if overlaps:
        return (
            f"This can support the JD story around {', '.join(_truncate_list(overlaps, 4))} without overstating ownership."
        )
    return "This is one of the stronger existing bullets to tighten before editing weaker sections."


def _fallback_claim_safety_from_reuse(row: Dict[str, Any]) -> str:
    evidence_type = str(row.get("evidence_type", "") or "").strip()
    if evidence_type == "direct_overlap":
        return "safe_strengthen"
    if evidence_type in {"same_source_context", "semantic_similarity"}:
        return "adjacent_only"
    return "adjacent_only"


def _fallback_edit_type_from_reuse(row: Dict[str, Any]) -> str:
    evidence_type = str(row.get("evidence_type", "") or "").strip()
    if evidence_type == "direct_overlap":
        return "tighten"
    if evidence_type == "same_source_context":
        return "reinforce"
    return "support"


def _fallback_priority_from_reuse(index: int, row: Dict[str, Any]) -> str:
    evidence_type = str(row.get("evidence_type", "") or "").strip()
    overlaps = row.get("overlaps", []) or []

    if evidence_type == "direct_overlap":
        return "high"
    if overlaps and index < 2:
        return "medium"
    return "low"

_PROMOTABLE_REUSE_FAMILY_PRIORITY = {
    "experimentation": 0,
    "analytics_ml": 1,
    "tooling": 2,
}


def _resolved_reuse_signal_match(
    payload: Dict[str, Any],
    row: Dict[str, Any],
) -> Dict[str, str]:
    packet_supported_terms = _packet_term_support_terms(payload)
    source_text = str(row.get("bullet", "") or row.get("parent_bullet", "") or "").strip()
    return supported_signal_match_in_text(source_text, packet_supported_terms)


def _reuse_row_rank(
    payload: Dict[str, Any],
    row: Dict[str, Any],
) -> Tuple[int, int, int]:
    signal_match = _resolved_reuse_signal_match(payload, row)
    family = str(signal_match.get("family", "") or "").strip()
    evidence_type = str(row.get("evidence_type", "") or "").strip()

    family_rank = _PROMOTABLE_REUSE_FAMILY_PRIORITY.get(family, 99)
    evidence_rank = 0 if evidence_type == "direct_overlap" else 1
    text_rank = abs(140 - len(str(row.get("bullet", "") or row.get("parent_bullet", "") or "").strip()))

    return (family_rank, evidence_rank, text_rank)

def _reuse_candidate_to_edit_card(
    payload: Dict[str, Any],
    row: Dict[str, Any],
    preferred_rewrite_directions: List[str],
    index: int,
) -> Dict[str, Any]:
    evidence = str(row.get("bullet", "") or row.get("parent_bullet", "") or "").strip()
    signal_match = _resolved_reuse_signal_match(payload, row)

    matched_surface_signal = str(signal_match.get("matched_term", "") or "").strip()
    canonical_supported_signal = str(signal_match.get("supported_term", "") or "").strip()

    jd_signal_terms = [canonical_supported_signal] if canonical_supported_signal else list(row.get("overlaps", []) or [])

    evidence_type = str(row.get("evidence_type", "") or "").strip()
    claim_safety = "safe_strengthen" if evidence_type == "direct_overlap" and jd_signal_terms else _fallback_claim_safety_from_reuse(row)

    return {
        "card_id": f"edit_card_reuse_{index}",
        "priority": _fallback_priority_from_reuse(index - 1, row),
        "edit_type": "rewrite" if jd_signal_terms and evidence_type == "direct_overlap" else _fallback_edit_type_from_reuse(row),
        "section": row.get("section", ""),
        "source": row.get("source", ""),
        "jd_signal_terms": jd_signal_terms,
        "current_evidence": evidence,
        "parent_bullet": row.get("parent_bullet", ""),
        "recommended_rewrite": _fallback_recommended_rewrite_from_reuse(
            preferred_rewrite_directions,
            row,
        ),
        "why_current_is_weak": _fallback_why_current_is_weak_from_reuse(row),
        "why_rewrite_is_better": _fallback_why_rewrite_is_better_from_reuse(row),
        "why_it_matters": _fallback_why_it_matters_from_reuse(row),
        "claim_safety": claim_safety,
        "placement_guidance": _placement_guidance(row),
        "entry_id": row.get("entry_id", ""),
        "entry_index": row.get("entry_index", -1),
        "bullet_id": row.get("bullet_id", ""),
        "bullet_index": row.get("bullet_index", -1),
        "matched_surface_signal": matched_surface_signal,
        "canonical_supported_signal": canonical_supported_signal,
    }


def _backfill_edit_cards_from_bullet_reuse(
    payload: Dict[str, Any],
    preferred_rewrite_directions: List[str],
    existing_cards: List[Dict[str, Any]],
    limit: int,
) -> List[Dict[str, Any]]:
    if len(existing_cards) >= limit:
        return existing_cards[:limit]

    cards = list(existing_cards)
    seen_keys = {
        (
            str(card.get("section", "") or "").strip().lower(),
            str(card.get("source", "") or "").strip().lower(),
            str(card.get("current_evidence", "") or "").strip().lower(),
        )
        for card in cards
    }

    bullet_reuse_candidates = payload.get("bullet_reuse_candidates", []) or []

    preferred_rows = []
    secondary_rows = []

    for row in bullet_reuse_candidates:
        evidence_type = str(row.get("evidence_type", "") or "").strip()
        if evidence_type == "direct_overlap":
            preferred_rows.append(row)
        elif evidence_type in {"same_source_context", "semantic_similarity"}:
            secondary_rows.append(row)

    candidate_rows = sorted(
        preferred_rows + secondary_rows,
        key=lambda row: _reuse_row_rank(payload, row),
    )

    for row in candidate_rows:
        if len(cards) >= limit:
            break

        evidence = str(row.get("bullet", "") or row.get("parent_bullet", "") or "").strip()
        key = (
            str(row.get("section", "") or "").strip().lower(),
            str(row.get("source", "") or "").strip().lower(),
            evidence.lower(),
        )
        if key in seen_keys:
            continue

        card = _reuse_candidate_to_edit_card(
            payload,
            row,
            preferred_rewrite_directions,
            len(cards) + 1,
        )
        cards.append(card)
        seen_keys.add(key)

    return cards[:limit]

def _card_priority(index: int, evidence_type: str) -> str:
    if evidence_type == "direct_overlap":
        return "high"
    if index < 2:
        return "high"
    if evidence_type in {"same_source_context", "semantic_similarity"}:
        return "medium"
    return "low"


def _card_edit_type(evidence_type: str) -> str:
    if evidence_type == "direct_overlap":
        return "rewrite"
    if evidence_type == "same_source_context":
        return "reinforce"
    return "support"


def _card_claim_safety(evidence_type: str) -> str:
    if evidence_type == "direct_overlap":
        return "safe_strengthen"
    if evidence_type in {"same_source_context", "semantic_similarity", "adjacent_context"}:
        return "adjacent_only"
    return "do_not_claim"


def _recommended_rewrite_text(
    preferred_rewrite_directions: List[str],
    candidate: Dict[str, Any],
    supported_terms: List[str],
) -> str:
    local_terms = [
        str(item or "").strip().lower()
        for item in (supported_terms or [])
        if str(item or "").strip()
    ]
    evidence_type = str(candidate.get("evidence_type", "") or "").strip()
    action = str(candidate.get("action", "") or "").strip()

    # Preserve only explicit structural instructions that should not be rephrased.
    if action and (
        action.startswith("Use this clause as a primary anchor")
        or action.startswith("Move this bullet earlier")
        or action.startswith("Keep this bullet")
    ):
        return action

    # If this card already has grounded local supported terms, force a local rewrite
    # so broader same-source directions cannot leak in.
    if local_terms:
        lead = ", ".join(_truncate_list(local_terms, 4))
        if evidence_type == "same_source_context":
            return (
                f"Support with {lead} only after the primary anchors, and keep it as reinforcing evidence "
                "rather than the main ownership claim."
            )
        return (
            f"Lead with {lead} in this opening clause, then keep the remaining parent-bullet context "
            "only if it preserves the same story truthfully."
        )

    source = str(candidate.get("source", "") or "").strip().lower()

    for direction in preferred_rewrite_directions or []:
        direction_text = str(direction or "").strip()
        direction_lower = direction_text.lower()

        if source and source in direction_lower:
            return direction_text

    return action

def _why_current_is_weak(candidate: Dict[str, Any], supported_terms: List[str]) -> str:
    evidence_type = str(candidate.get("evidence_type", "") or "").strip()

    if evidence_type == "direct_overlap":
        if supported_terms:
            return (
                f"The evidence is relevant, but {', '.join(_truncate_list(supported_terms, 4))} "
                "is not yet leading the bullet clearly."
            )
        return "The evidence is relevant, but the JD-aligned language is not yet leading the bullet clearly."

    if evidence_type == "same_source_context":
        return "This evidence helps credibility, but it reads more like supporting context than the main JD-facing claim."

    if evidence_type == "semantic_similarity":
        return "This is directionally relevant, but it is still too indirect to carry the main JD story by itself."

    return "This evidence should support the story, not act as the primary ownership claim."


def _why_rewrite_is_better(candidate: Dict[str, Any], supported_terms: List[str]) -> str:
    if supported_terms:
        return (
            f"It brings {', '.join(_truncate_list(supported_terms, 4))} forward while staying anchored to work you already did."
        )
    return "It makes the JD connection clearer without requiring a new unsupported claim."


def _placement_guidance(candidate: Dict[str, Any]) -> str:
    section = str(candidate.get("section", "") or "").strip()
    source = str(candidate.get("source", "") or "").strip()

    if section and source:
        return f"Edit the {section} bullet tied to {source} before changing lower-priority sections."
    if section:
        return f"Edit this in the {section} section before changing lower-priority sections."
    return "Update the strongest matching experience bullet first, then reorder only if needed."


def _why_it_matters(candidate: Dict[str, Any], supported_terms: List[str]) -> str:
    evidence_type = str(candidate.get("evidence_type", "") or "").strip()

    if supported_terms:
        lead = ", ".join(_truncate_list(supported_terms, 4))
        if evidence_type == "direct_overlap":
            return f"This is one of the clearest truthful ways to surface {lead} earlier for the JD."
        if evidence_type == "same_source_context":
            return f"This can strengthen the main story around {lead} without overclaiming direct ownership."
        return f"This can add adjacent support around {lead}, but it should not become the main claim."

    if evidence_type == "direct_overlap":
        return "This is directly supported evidence and should be one of the first bullets you tighten."
    return "This can help support the JD story, but it is not the strongest anchor."

def _packet_term_support_terms(packet: Dict[str, Any]) -> List[str]:
    summary = packet.get("summary", {}) or {}
    term_support = summary.get("term_support", {}) or {}

    terms: List[str] = []
    for bucket in ("required", "preferred"):
        for row in (term_support.get(bucket, []) or []):
            term = str(row.get("term", "") or "").strip()
            if term:
                terms.append(term)

    terms.extend(
        str(item).strip()
        for item in (summary.get("matched_terms", []) or [])
        if str(item).strip()
    )
    return _unique_preserve_order(terms)

def _resolved_edit_card_evidence_type(
    candidate: Dict[str, Any],
    supported_terms: List[str],
    source_text: str,
) -> str:
    evidence_type = str(candidate.get("evidence_type", "") or "").strip()
    if evidence_type:
        return evidence_type

    text_norm = _diagnosis_normalize_term(source_text)
    supported_norm = [
        _diagnosis_normalize_term(term)
        for term in (supported_terms or [])
        if _diagnosis_normalize_term(term)
    ]

    if text_norm and supported_norm and any(term in text_norm for term in supported_norm):
        return "direct_overlap"

    if source_text:
        return "same_source_context"

    return ""

_CLAUSE_SPLIT_ACTION_VERBS = (
    "Implemented",
    "Designed",
    "Developed",
    "Built",
    "Created",
    "Led",
    "Ran",
    "Conducted",
    "Engineered",
    "Automated",
    "Performed",
)

_STRUCTURAL_CLAUSE_FAMILY_PRIORITY = {
    "experimentation": 0,
    "analytics_ml": 1,
}


def _split_promotable_clauses(text: str) -> List[str]:
    full_text = re.sub(r"\s+", " ", str(text or "").strip())
    if not full_text:
        return []

    clauses: List[str] = []
    sentence_parts = re.split(r"(?<=[.;])\s+", full_text)

    verb_pattern = (
        r"(?<!^)\s+(?=(?:"
        + "|".join(re.escape(verb) for verb in _CLAUSE_SPLIT_ACTION_VERBS)
        + r")\b)"
    )

    for part in sentence_parts:
        for subpart in re.split(verb_pattern, part):
            clause = str(subpart or "").strip(" ;,.")
            if len(clause) >= 45:
                clauses.append(clause)

    return _unique_preserve_order(clauses)

def _structural_source_text_from_reuse_row(row: Dict[str, Any]) -> str:
    bullet = str(row.get("bullet", "") or "").strip()
    parent_bullet = str(row.get("parent_bullet", "") or "").strip()

    if parent_bullet and len(parent_bullet) > len(bullet):
        return parent_bullet
    return bullet or parent_bullet

def _best_structural_clause_candidate(
    text: str,
    packet_supported_terms: List[str],
) -> Dict[str, str]:
    full_text = re.sub(r"\s+", " ", str(text or "").strip())
    if not full_text:
        return {}

    clauses = _split_promotable_clauses(full_text)
    if len(clauses) < 2:
        return {}

    best: Dict[str, str] = {}
    best_rank: Optional[Tuple[int, int, int]] = None

    for clause_index, clause_text in enumerate(clauses):
        signal_match = supported_signal_match_in_text(
            clause_text,
            packet_supported_terms,
        )

        matched_surface_signal = str(signal_match.get("matched_term", "") or "").strip()
        canonical_supported_signal = str(signal_match.get("supported_term", "") or "").strip()
        family = str(signal_match.get("family", "") or "").strip()

        if not matched_surface_signal or not canonical_supported_signal or not family:
            continue

        if family not in _STRUCTURAL_CLAUSE_FAMILY_PRIORITY:
            continue

        normalized_clause = _diagnosis_normalize_term(clause_text)
        normalized_full = _diagnosis_normalize_term(full_text)
        if normalized_clause == normalized_full:
            continue

        rank = (
            _STRUCTURAL_CLAUSE_FAMILY_PRIORITY.get(family, 99),
            0 if clause_index > 0 else 1,
            abs(140 - len(clause_text)),
        )

        if best_rank is None or rank < best_rank:
            best_rank = rank
            best = {
                "clause_text": clause_text,
                "matched_surface_signal": matched_surface_signal,
                "canonical_supported_signal": canonical_supported_signal,
                "family": family,
            }

    return best


def _structural_clause_edit_card_from_reuse(
    row: Dict[str, Any],
    clause_candidate: Dict[str, str],
    index: int,
) -> Dict[str, Any]:
    full_evidence = _structural_source_text_from_reuse_row(row)
    clause_text = str(clause_candidate.get("clause_text", "") or "").strip()
    matched_surface_signal = str(clause_candidate.get("matched_surface_signal", "") or "").strip()
    canonical_supported_signal = str(clause_candidate.get("canonical_supported_signal", "") or "").strip()

    return {
        "card_id": f"edit_card_struct_{index}",
        "evidence_type": "direct_overlap",
        "priority": "high",
        "edit_type": "rewrite",
        "section": row.get("section", ""),
        "source": row.get("source", ""),
        "jd_signal_terms": [canonical_supported_signal] if canonical_supported_signal else [],
        # IMPORTANT: current_evidence must remain the original full bullet so patch application
        # can target the stored resume bullet truthfully and deterministically.
        "current_evidence": full_evidence,
        "parent_bullet": full_evidence,
        "recommended_rewrite": clause_text,
        "why_current_is_weak": (
            "The strongest JD-relevant signal is buried inside a longer multi-claim bullet instead of standing on its own."
        ),
        "why_rewrite_is_better": (
            f"It isolates the already-explicit {canonical_supported_signal} evidence without inventing any new claim."
        ),
        "why_it_matters": (
            f"This is the clearest grounded path to surface {canonical_supported_signal} as direct bullet evidence."
        ),
        "claim_safety": "safe_strengthen",
        "placement_guidance": (
            "Replace the original bullet with this already-explicit clause only if the shorter bullet still tells the story truthfully."
        ),
        "entry_id": row.get("entry_id", ""),
        "entry_index": row.get("entry_index", -1),
        "bullet_id": row.get("bullet_id", ""),
        "bullet_index": row.get("bullet_index", -1),
        "matched_surface_signal": matched_surface_signal,
        "canonical_supported_signal": canonical_supported_signal,
        "structural_operation": "extract_clause",
        "structural_clause_text": clause_text,
        # Optional display/debug aid
        "focused_clause_text": clause_text,
    }

def _build_edit_cards(
    payload: Dict[str, Any],
    preferred_rewrite_directions: List[str],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    seen_bullet_ids = set()

    rewrite_candidates = payload.get("rewrite_candidates", []) or []
    bullet_reuse_candidates = payload.get("bullet_reuse_candidates", []) or []
    packet_supported_terms = _packet_term_support_terms(payload)

    # Pass 0: prioritize structural hidden-clause candidates from grounded reuse bullets
    for row in bullet_reuse_candidates:
        if len(cards) >= limit:
            break

        evidence_type = str(row.get("evidence_type", "") or "").strip()
        if evidence_type != "direct_overlap":
            continue

        bullet_id = str(row.get("bullet_id", "") or "").strip()
        if bullet_id and bullet_id in seen_bullet_ids:
            continue

        full_evidence = _structural_source_text_from_reuse_row(row)
        clause_candidate = _best_structural_clause_candidate(
            full_evidence,
            packet_supported_terms,
        )
        if not clause_candidate:
            continue

        card = _structural_clause_edit_card_from_reuse(
            row,
            clause_candidate,
            len(cards) + 1,
        )
        cards.append(card)

        if bullet_id:
            seen_bullet_ids.add(bullet_id)

    # Pass 1: current rewrite candidates
    for index, candidate in enumerate(rewrite_candidates[:limit], start=1):
        if len(cards) >= limit:
            break

        bullet_id = str(candidate.get("bullet_id", "") or "").strip()
        if bullet_id and bullet_id in seen_bullet_ids:
            continue

        seed_terms = list(candidate.get("supported_terms", []) or [])
        current_evidence = str(candidate.get("bullet_excerpt", "") or "").strip()
        parent_bullet = str(candidate.get("parent_bullet", "") or "").strip()
        source_text = parent_bullet or current_evidence

        signal_match = supported_signal_match_in_text(
            source_text,
            packet_supported_terms,
        )

        matched_surface_signal = str(signal_match.get("matched_term", "") or "").strip()
        canonical_supported_signal = str(signal_match.get("supported_term", "") or "").strip()

        supported_terms = [canonical_supported_signal] if canonical_supported_signal else seed_terms
        evidence_type = _resolved_edit_card_evidence_type(
            candidate,
            supported_terms,
            source_text,
        )

        recommended_rewrite = _recommended_rewrite_text(
            preferred_rewrite_directions,
            candidate,
            supported_terms,
        )

        cards.append(
            {
                "card_id": f"edit_card_{index}",
                "evidence_type": evidence_type,
                "priority": _card_priority(index - 1, evidence_type),
                "edit_type": _card_edit_type(evidence_type),
                "section": candidate.get("section", ""),
                "source": candidate.get("source", ""),
                "jd_signal_terms": supported_terms,
                "current_evidence": current_evidence,
                "parent_bullet": parent_bullet,
                "recommended_rewrite": recommended_rewrite,
                "why_current_is_weak": _why_current_is_weak(candidate, supported_terms),
                "why_rewrite_is_better": _why_rewrite_is_better(candidate, supported_terms),
                "why_it_matters": _why_it_matters(candidate, supported_terms),
                "claim_safety": _card_claim_safety(evidence_type),
                "placement_guidance": _placement_guidance(candidate),
                "entry_id": candidate.get("entry_id", ""),
                "entry_index": candidate.get("entry_index", -1),
                "bullet_id": candidate.get("bullet_id", ""),
                "bullet_index": candidate.get("bullet_index", -1),
                "matched_surface_signal": matched_surface_signal,
                "canonical_supported_signal": canonical_supported_signal,
            }
        )

        if bullet_id:
            seen_bullet_ids.add(bullet_id)

    cards = _backfill_edit_cards_from_bullet_reuse(
        payload,
        preferred_rewrite_directions,
        cards,
        limit,
    )

    return cards


def _build_top_edit_priorities(
    edit_cards: List[Dict[str, Any]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    priorities: List[Dict[str, Any]] = []

    for card in edit_cards[:limit]:
        priorities.append(
            {
                "priority": card.get("priority", ""),
                "edit_type": card.get("edit_type", ""),
                "jd_signal": ", ".join(card.get("jd_signal_terms", []) or []),
                "why_it_matters": card.get("why_it_matters", ""),
                "target_section": card.get("section", ""),
                "recommended_rewrite": card.get("recommended_rewrite", ""),
            }
        )

    return priorities

def _diagnosis_normalize_term(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _likely_impacted_dimensions(
    packet: Dict[str, Any],
    section: str,
    jd_signal_terms: List[str],
) -> List[str]:
    summary = packet.get("summary", {}) or {}
    term_support = summary.get("term_support", {}) or {}

    terms = [
        _diagnosis_normalize_term(item)
        for item in (jd_signal_terms or [])
        if _diagnosis_normalize_term(item)
    ]

    required_terms = {
        _diagnosis_normalize_term(str(row.get("term", "") or ""))
        for row in (term_support.get("required", []) or [])
        if _diagnosis_normalize_term(str(row.get("term", "") or ""))
    }
    preferred_terms = {
        _diagnosis_normalize_term(str(row.get("term", "") or ""))
        for row in (term_support.get("preferred", []) or [])
        if _diagnosis_normalize_term(str(row.get("term", "") or ""))
    }

    families = set(families_for_terms(terms))
    impacted: List[str] = []

    if set(terms) & required_terms:
        impacted.append("required_skills_alignment")
    if set(terms) & preferred_terms:
        impacted.append("preferred_skills_alignment")
    if "tooling" in families:
        impacted.append("tooling_alignment")
    if "analytics_ml" in families:
        impacted.append("analytics_ml_depth")
    if "experimentation" in families:
        impacted.append("experimentation_depth")
    if "domain" in families:
        impacted.append("domain_relevance")
    if str(section or "").strip() == "project":
        impacted.append("project_relevance")

    return _unique_preserve_order(impacted)


def _bullet_diagnosis_key(item: Dict[str, Any]) -> tuple:
    bullet_id = str(item.get("bullet_id", "") or "").strip()
    if bullet_id:
        return ("bullet", bullet_id)

    return (
        "fallback",
        str(item.get("section", "") or "").strip(),
        str(item.get("source", "") or "").strip(),
        str(item.get("current_evidence", "") or item.get("evidence", "") or "").strip(),
    )


def _edit_card_to_bullet_diagnosis(
    packet: Dict[str, Any],
    card: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:
    jd_signal_terms = list(card.get("jd_signal_terms", []) or [])
    current_evidence = str(card.get("current_evidence", "") or "").strip()
    parent_bullet = str(card.get("parent_bullet", "") or "").strip()

    return {
        "diagnosis_id": f"bullet_diag_{index}",
        "diagnosis_action": "rewrite",
        "diagnosis_reason_type": str(card.get("edit_type", "") or "").strip(),
        "priority": str(card.get("priority", "") or "").strip(),
        "section": str(card.get("section", "") or "").strip(),
        "source": str(card.get("source", "") or "").strip(),
        "entry_id": str(card.get("entry_id", "") or "").strip(),
        "entry_index": card.get("entry_index", -1),
        "bullet_id": str(card.get("bullet_id", "") or "").strip(),
        "bullet_index": card.get("bullet_index", -1),
        "original_text": parent_bullet or current_evidence,
        "current_evidence": current_evidence,
        "evidence_type": str(card.get("evidence_type", "") or "").strip(),
        "jd_signal_terms": jd_signal_terms,
        "likely_impacted_dimensions": _likely_impacted_dimensions(
            packet,
            str(card.get("section", "") or ""),
            jd_signal_terms,
        ),
        "why": str(card.get("why_it_matters", "") or card.get("why_rewrite_is_better", "") or "").strip(),
        "recommended_rewrite": str(card.get("recommended_rewrite", "") or "").strip(),
        "claim_safety": str(card.get("claim_safety", "") or "").strip(),
        "placement_guidance": str(card.get("placement_guidance", "") or "").strip(),
        "matched_surface_signal": str(card.get("matched_surface_signal", "") or "").strip(),
        "canonical_supported_signal": str(card.get("canonical_supported_signal", "") or "").strip(),
        "structural_operation": str(card.get("structural_operation", "") or "").strip(),
        "structural_clause_text": str(card.get("structural_clause_text", "") or "").strip(),
    }


def _keep_as_is_to_bullet_diagnosis(
    packet: Dict[str, Any],
    row: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:
    overlaps = list(row.get("overlaps", []) or [])
    evidence = str(row.get("evidence", "") or "").strip()

    return {
        "diagnosis_id": f"bullet_diag_keep_{index}",
        "diagnosis_action": "keep",
        "diagnosis_reason_type": "keep_as_is",
        "priority": "medium",
        "section": str(row.get("section", "") or "").strip(),
        "source": str(row.get("source", "") or "").strip(),
        "entry_id": str(row.get("entry_id", "") or "").strip(),
        "entry_index": row.get("entry_index", -1),
        "bullet_id": str(row.get("bullet_id", "") or "").strip(),
        "bullet_index": row.get("bullet_index", -1),
        "original_text": evidence,
        "current_evidence": evidence,
        "jd_signal_terms": overlaps,
        "likely_impacted_dimensions": _likely_impacted_dimensions(
            packet,
            str(row.get("section", "") or ""),
            overlaps,
        ),
        "why": str(row.get("reason", "") or "").strip(),
        "recommended_rewrite": "",
        "claim_safety": "keep_visible",
        "placement_guidance": "Keep this bullet visible before editing lower-value evidence.",
    }

def _replacement_candidate_confidence(diagnosis: Dict[str, Any]) -> str:
    score = 0

    if str(diagnosis.get("claim_safety", "") or "").strip() == "safe_strengthen":
        score += 2
    elif str(diagnosis.get("claim_safety", "") or "").strip() == "adjacent_only":
        score += 1

    if str(diagnosis.get("priority", "") or "").strip() == "high":
        score += 2
    elif str(diagnosis.get("priority", "") or "").strip() == "medium":
        score += 1

    if diagnosis.get("likely_impacted_dimensions"):
        score += 1

    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _replacement_candidate_risks(
    payload: Dict[str, Any],
    diagnosis: Dict[str, Any],
) -> Dict[str, List[str]]:
    claim_safety_notes = payload.get("claim_safety_notes", {}) or {}

    jd_terms_raw = [
        str(item or "").strip()
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if str(item or "").strip()
    ]
    jd_terms_norm = {_diagnosis_normalize_term(item) for item in jd_terms_raw}

    frame_terms_raw = [
        str(item or "").strip()
        for item in (claim_safety_notes.get("frame_carefully", []) or [])
        if str(item or "").strip()
    ]
    do_not_add_raw = [
        str(item or "").strip()
        for item in (claim_safety_notes.get("do_not_add", []) or [])
        if str(item or "").strip()
    ]

    frame_terms_norm = {_diagnosis_normalize_term(item) for item in frame_terms_raw}
    do_not_add_norm = {_diagnosis_normalize_term(item) for item in do_not_add_raw}

    adjacent_risk_signals = [
        item for item in jd_terms_raw
        if _diagnosis_normalize_term(item) in frame_terms_norm
    ]
    unsupported_risk_signals = [
        item for item in jd_terms_raw
        if _diagnosis_normalize_term(item) in do_not_add_norm
    ]

    evidence_type = str(diagnosis.get("evidence_type", "") or "").strip()
    claim_safety = str(diagnosis.get("claim_safety", "") or "").strip()

    # Bullet-level direct proof should override packet-level contextual/default risk notes
    # for the exact supported terms attached to this diagnosis.
    if evidence_type == "direct_overlap" and claim_safety == "safe_strengthen":
        adjacent_risk_signals = [
            item for item in adjacent_risk_signals
            if _diagnosis_normalize_term(item) not in jd_terms_norm
        ]
        unsupported_risk_signals = [
            item for item in unsupported_risk_signals
            if _diagnosis_normalize_term(item) not in jd_terms_norm
        ]

    return {
        "adjacent_risk_signals": _unique_preserve_order(adjacent_risk_signals),
        "unsupported_risk_signals": _unique_preserve_order(unsupported_risk_signals),
    }


def _diagnosis_to_replacement_candidate(
    payload: Dict[str, Any],
    diagnosis: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:
    risks = _replacement_candidate_risks(payload, diagnosis)

    bullet_id = str(diagnosis.get("bullet_id", "") or "").strip()
    diagnosis_id = str(diagnosis.get("diagnosis_id", "") or f"bullet_diag_{index}").strip()
    candidate_id = diagnosis_id.replace("bullet_diag", "replacement", 1)

    rewrite_instruction = str(diagnosis.get("recommended_rewrite", "") or "").strip()

    proposal_status, patch_text, patch_generation_method = _deterministic_patch_text_from_diagnosis(
        diagnosis,
        risks["adjacent_risk_signals"],
        risks["unsupported_risk_signals"],
    )

    return {
        "candidate_id": candidate_id,
        "source_bullet_id": bullet_id,
        "source_entry_id": str(diagnosis.get("entry_id", "") or "").strip(),
        "section": str(diagnosis.get("section", "") or "").strip(),
        "evidence_type": str(diagnosis.get("evidence_type", "") or "").strip(),
        "source": str(diagnosis.get("source", "") or "").strip(),
        "operation_type": "rewrite",
        "proposal_type": "directional_rewrite" if proposal_status == "direction_only" else "patch_ready_rewrite",
        "proposal_status": proposal_status,
        "original_text": str(diagnosis.get("original_text", "") or "").strip(),
        "current_evidence": str(diagnosis.get("current_evidence", "") or "").strip(),
        "rewrite_instruction": rewrite_instruction,
        "proposed_text": patch_text,
        "patch_text": patch_text,
        "patch_ready": proposal_status == "patch_ready",
        "patch_generation_method": patch_generation_method,
        "supported_jd_signals": list(diagnosis.get("jd_signal_terms", []) or []),
        "adjacent_risk_signals": risks["adjacent_risk_signals"],
        "unsupported_risk_signals": risks["unsupported_risk_signals"],
        "likely_impacted_dimensions": list(diagnosis.get("likely_impacted_dimensions", []) or []),
        "why_this_improves_match": str(diagnosis.get("why", "") or "").strip(),
        "claim_safety": str(diagnosis.get("claim_safety", "") or "").strip(),
        "safety_status": str(diagnosis.get("claim_safety", "") or "").strip(),
        "placement_guidance": str(diagnosis.get("placement_guidance", "") or "").strip(),
        "confidence": _replacement_candidate_confidence(diagnosis),
        "conflicts_with": [],
        "entry_index": diagnosis.get("entry_index", -1),
        "bullet_index": diagnosis.get("bullet_index", -1),
        "llm_refinement_used": False,
        "material_delta_found": proposal_status == "patch_ready",
        "projected_dimension_deltas": {},
        "projected_overall_delta": None,
        "matched_surface_signal": str(diagnosis.get("matched_surface_signal", "") or "").strip(),
        "canonical_supported_signal": str(diagnosis.get("canonical_supported_signal", "") or "").strip(),
    }

def _keep_candidate_confidence(diagnosis: Dict[str, Any]) -> str:
    impacted = list(diagnosis.get("likely_impacted_dimensions", []) or [])
    terms = list(diagnosis.get("jd_signal_terms", []) or [])

    score = 0
    if terms:
        score += 1
    if impacted:
        score += 1
    if str(diagnosis.get("priority", "") or "").strip() in {"high", "medium"}:
        score += 1

    if score >= 3:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _should_create_reorder_candidate(diagnosis: Dict[str, Any]) -> bool:
    if str(diagnosis.get("diagnosis_action", "") or "").strip() != "keep":
        return False

    section = str(diagnosis.get("section", "") or "").strip()
    if section not in {"experience", "project"}:
        return False

    jd_signal_terms = list(diagnosis.get("jd_signal_terms", []) or [])
    if not jd_signal_terms:
        return False

    impacted = list(diagnosis.get("likely_impacted_dimensions", []) or [])
    if not impacted:
        return False

    claim_safety = str(diagnosis.get("claim_safety", "") or "").strip()
    if claim_safety not in {"keep_visible", "safe_strengthen"}:
        return False

    return True


def _diagnosis_to_keep_candidate(
    diagnosis: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:
    diagnosis_id = str(diagnosis.get("diagnosis_id", "") or f"bullet_diag_keep_{index}").strip()
    candidate_id = diagnosis_id.replace("bullet_diag", "replacement", 1)

    return {
        "candidate_id": candidate_id,
        "source_bullet_id": str(diagnosis.get("bullet_id", "") or "").strip(),
        "source_entry_id": str(diagnosis.get("entry_id", "") or "").strip(),
        "section": str(diagnosis.get("section", "") or "").strip(),
        "source": str(diagnosis.get("source", "") or "").strip(),
        "operation_type": "keep",
        "proposal_type": "keep_visible",
        "proposal_status": "patch_ready",
        "original_text": str(diagnosis.get("original_text", "") or "").strip(),
        "current_evidence": str(diagnosis.get("current_evidence", "") or "").strip(),
        "rewrite_instruction": "",
        "proposed_text": str(diagnosis.get("original_text", "") or "").strip(),
        "patch_text": str(diagnosis.get("original_text", "") or "").strip(),
        "patch_ready": True,
        "patch_generation_method": "deterministic_keep_existing",
        "supported_jd_signals": list(diagnosis.get("jd_signal_terms", []) or []),
        "adjacent_risk_signals": [],
        "unsupported_risk_signals": [],
        "likely_impacted_dimensions": list(diagnosis.get("likely_impacted_dimensions", []) or []),
        "why_this_improves_match": str(diagnosis.get("why", "") or "").strip(),
        "claim_safety": str(diagnosis.get("claim_safety", "") or "").strip(),
        "safety_status": str(diagnosis.get("claim_safety", "") or "").strip(),
        "placement_guidance": "Keep this bullet visible in the final tailored resume.",
        "confidence": _keep_candidate_confidence(diagnosis),
        "conflicts_with": [],
        "entry_index": diagnosis.get("entry_index", -1),
        "bullet_index": diagnosis.get("bullet_index", -1),
        "llm_refinement_used": False,
        "material_delta_found": True,
        "projected_dimension_deltas": {},
        "projected_overall_delta": None,
    }


def _diagnosis_to_reorder_candidate(
    diagnosis: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:
    diagnosis_id = str(diagnosis.get("diagnosis_id", "") or f"bullet_diag_keep_{index}").strip()
    candidate_id = diagnosis_id.replace("bullet_diag", "replacement_reorder", 1)

    section = str(diagnosis.get("section", "") or "").strip()

    return {
        "candidate_id": candidate_id,
        "source_bullet_id": str(diagnosis.get("bullet_id", "") or "").strip(),
        "source_entry_id": str(diagnosis.get("entry_id", "") or "").strip(),
        "section": section,
        "source": str(diagnosis.get("source", "") or "").strip(),
        "operation_type": "reorder",
        "proposal_type": "directional_reorder",
        "proposal_status": "direction_only",
        "original_text": str(diagnosis.get("original_text", "") or "").strip(),
        "current_evidence": str(diagnosis.get("current_evidence", "") or "").strip(),
        "rewrite_instruction": "Move this bullet earlier in the same section so it appears before weaker or less relevant bullets.",
        "proposed_text": "",
        "patch_text": "",
        "patch_ready": False,
        "patch_generation_method": "deterministic_reorder_signal",
        "supported_jd_signals": list(diagnosis.get("jd_signal_terms", []) or []),
        "adjacent_risk_signals": [],
        "unsupported_risk_signals": [],
        "likely_impacted_dimensions": list(diagnosis.get("likely_impacted_dimensions", []) or []),
        "why_this_improves_match": str(diagnosis.get("why", "") or "").strip(),
        "claim_safety": "safe_reorder",
        "safety_status": "safe_reorder",
        "placement_guidance": f"Move this bullet earlier within the {section} section before lower-value evidence.",
        "confidence": _keep_candidate_confidence(diagnosis),
        "conflicts_with": [],
        "entry_index": diagnosis.get("entry_index", -1),
        "bullet_index": diagnosis.get("bullet_index", -1),
        "llm_refinement_used": False,
        "material_delta_found": False,
        "materiality_validation_status": "order_not_modeled_in_v1",
        "materiality_validation_note": (
            "Bullet order is not modeled as an exportable deterministic patch in v1, so this remains directional guidance."
        ),
        "projected_dimension_deltas": {},
        "projected_overall_delta": None,
    }

def _should_create_reorder_companion(candidate: Dict[str, Any]) -> bool:
    if str(candidate.get("operation_type", "") or "").strip() != "rewrite":
        return False

    if str(candidate.get("proposal_status", "") or "").strip() != "patch_ready":
        return False

    if str(candidate.get("confidence", "") or "").strip() not in {"high", "medium"}:
        return False

    section = str(candidate.get("section", "") or "").strip()
    if section not in {"experience", "project"}:
        return False

    supported_terms = list(candidate.get("supported_jd_signals", []) or [])
    if not supported_terms:
        return False

    return True


def _rewrite_candidate_to_reorder_companion(
    candidate: Dict[str, Any],
) -> Dict[str, Any]:
    base_candidate_id = str(candidate.get("candidate_id", "") or "").strip()
    reorder_candidate_id = f"{base_candidate_id}__reorder"

    return {
        "candidate_id": reorder_candidate_id,
        "source_bullet_id": str(candidate.get("source_bullet_id", "") or "").strip(),
        "source_entry_id": str(candidate.get("source_entry_id", "") or "").strip(),
        "section": str(candidate.get("section", "") or "").strip(),
        "source": str(candidate.get("source", "") or "").strip(),
        "operation_type": "reorder",
        "proposal_type": "directional_reorder",
        "proposal_status": "direction_only",
        "original_text": str(candidate.get("original_text", "") or "").strip(),
        "current_evidence": str(candidate.get("current_evidence", "") or "").strip(),
        "rewrite_instruction": "Move this bullet earlier in the same section so it appears before weaker or less relevant bullets.",
        "proposed_text": "",
        "patch_text": "",
        "patch_ready": False,
        "patch_generation_method": "deterministic_reorder_signal",
        "supported_jd_signals": list(candidate.get("supported_jd_signals", []) or []),
        "adjacent_risk_signals": [],
        "unsupported_risk_signals": [],
        "likely_impacted_dimensions": list(candidate.get("likely_impacted_dimensions", []) or []),
        "why_this_improves_match": str(candidate.get("why_this_improves_match", "") or "").strip(),
        "claim_safety": "safe_reorder",
        "safety_status": "safe_reorder",
        "placement_guidance": (
            f"Move this bullet earlier within the {str(candidate.get('section', '') or '').strip()} section "
            "before lower-value evidence."
        ),
        "confidence": str(candidate.get("confidence", "") or "medium").strip(),
        "conflicts_with": [base_candidate_id],
        "entry_index": candidate.get("entry_index", -1),
        "bullet_index": candidate.get("bullet_index", -1),
        "llm_refinement_used": False,
        "material_delta_found": False,
        "materiality_validation_status": "order_not_modeled_in_v1",
        "materiality_validation_note": (
            "Bullet order is not modeled as an exportable deterministic patch in v1, so this remains directional guidance."
        ),
        "projected_dimension_deltas": {},
        "projected_overall_delta": None,
    }

def _candidate_source_group_id(candidate: Dict[str, Any]) -> str:
    source_bullet_id = str(candidate.get("source_bullet_id", "") or "").strip()
    candidate_id = str(candidate.get("candidate_id", "") or "").strip()

    if source_bullet_id:
        return f"source_group:{source_bullet_id}"

    return f"source_group:{candidate_id}"


def _candidate_conflict_group_id(candidate: Dict[str, Any]) -> str:
    source_bullet_id = str(candidate.get("source_bullet_id", "") or "").strip()
    candidate_id = str(candidate.get("candidate_id", "") or "").strip()

    if source_bullet_id:
        return f"conflict_group:{source_bullet_id}"

    return f"conflict_group:{candidate_id}"


def _apply_candidate_grouping(
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    conflict_buckets: Dict[str, List[Dict[str, Any]]] = {}

    for candidate in candidates:
        source_bullet_id = str(candidate.get("source_bullet_id", "") or "").strip()
        source_group_id = _candidate_source_group_id(candidate)
        conflict_group_id = _candidate_conflict_group_id(candidate)

        candidate["source_group_id"] = source_group_id
        candidate["source_group_type"] = "single_bullet"
        candidate["source_bullet_ids"] = [source_bullet_id] if source_bullet_id else []
        candidate["conflict_group_id"] = conflict_group_id

        conflict_buckets.setdefault(conflict_group_id, []).append(candidate)

    for conflict_group_id, group_rows in conflict_buckets.items():
        group_candidate_ids = [
            str(row.get("candidate_id", "") or "").strip()
            for row in group_rows
            if str(row.get("candidate_id", "") or "").strip()
        ]

        for row in group_rows:
            current_id = str(row.get("candidate_id", "") or "").strip()
            existing_conflicts = list(row.get("conflicts_with", []) or [])

            derived_conflicts = [
                candidate_id
                for candidate_id in group_candidate_ids
                if candidate_id and candidate_id != current_id
            ]

            row["conflicts_with"] = _unique_preserve_order(
                [*existing_conflicts, *derived_conflicts]
            )

    return candidates

DEFAULT_COUNTERFACTUAL_JOB_CORPUS = Path("data/rag/job_corpus.jsonl")


def _normalize_resume_text_for_counterfactual(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _load_job_record_by_doc_id(
    job_doc_id: str,
    job_corpus_path: Path = DEFAULT_COUNTERFACTUAL_JOB_CORPUS,
) -> Optional[Dict[str, Any]]:
    target = str(job_doc_id or "").strip()
    if not target or not job_corpus_path.exists():
        return None

    with job_corpus_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)
            job_evidence = build_job_evidence(record)
            if str(getattr(job_evidence, "job_doc_id", "") or "").strip() == target:
                return record

    return None


def _counterfactual_context_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    selection = payload.get("selection", {}) or {}
    job = payload.get("job", {}) or {}
    job_snapshot = payload.get("job_snapshot", {}) or {}

    selected_resume_name = str(selection.get("selected_resume", "") or "").strip()
    job_doc_id = str(job.get("job_doc_id", "") or "").strip()

    if not selected_resume_name:
        return {
            "ok": False,
            "reason": "missing_selected_resume",
        }

    if not job_doc_id:
        return {
            "ok": False,
            "reason": "missing_job_doc_id",
        }

    docs = load_resume_documents_by_name([selected_resume_name])
    if not docs:
        return {
            "ok": False,
            "reason": "resume_not_found",
            "selected_resume_name": selected_resume_name,
            "job_doc_id": job_doc_id,
        }

    job_record = None

    if isinstance(job_snapshot, dict) and job_snapshot:
        job_record = dict(job_snapshot)

    if job_record is None:
        job_record = _load_job_record_by_doc_id(job_doc_id)

    if job_record is None:
        return {
            "ok": False,
            "reason": "job_record_not_found",
            "selected_resume_name": selected_resume_name,
            "job_doc_id": job_doc_id,
        }

    original_doc = docs[0]
    original_resume = build_resume_evidence(original_doc)
    job_evidence = build_job_evidence(job_record)
    original_result = score_resume_job_match(original_resume, job_evidence)

    return {
        "ok": True,
        "reason": "",
        "resume_doc": original_doc,
        "original_resume": original_resume,
        "job_evidence": job_evidence,
        "original_result": original_result,
        "selected_resume_name": selected_resume_name,
        "job_doc_id": job_doc_id,
    }

def _sorted_unique_strings(values: List[Any]) -> List[str]:
    cleaned = sorted(
        {
            str(value).strip()
            for value in (values or [])
            if str(value).strip()
        }
    )
    return cleaned


def _resume_counterfactual_snapshot(resume: Any) -> Dict[str, List[str]]:
    explicit_skills = set()

    explicit_skills.update(
        str(value).strip().lower()
        for value in list(getattr(resume, "skills", []) or [])
        if str(value).strip()
    )

    for entry in list(getattr(resume, "experience_entries", []) or []):
        explicit_skills.update(
            str(value).strip().lower()
            for value in list(getattr(entry, "normalized_skills", []) or [])
            if str(value).strip()
        )

    for entry in list(getattr(resume, "project_entries", []) or []):
        explicit_skills.update(
            str(value).strip().lower()
            for value in list(getattr(entry, "normalized_skills", []) or [])
            if str(value).strip()
        )

    titles = list(getattr(resume, "titles", []) or [])
    for entry in list(getattr(resume, "experience_entries", []) or []):
        title = str(getattr(entry, "title", "") or "").strip()
        if title:
            titles.append(title)

    project_skills: List[str] = []
    for entry in list(getattr(resume, "project_entries", []) or []):
        project_skills.extend(list(getattr(entry, "normalized_skills", []) or []))

    return {
        "explicit_skills": _sorted_unique_strings(list(explicit_skills)),
        "titles": _sorted_unique_strings(titles),
        "domain_signals": _sorted_unique_strings(list(getattr(resume, "domain_signals", []) or [])),
        "analytics_ml_signals": _sorted_unique_strings(list(getattr(resume, "analytics_ml_signals", []) or [])),
        "experimentation_signals": _sorted_unique_strings(list(getattr(resume, "experimentation_signals", []) or [])),
        "tooling_signals": _sorted_unique_strings(list(getattr(resume, "tooling_signals", []) or [])),
        "project_skills": _sorted_unique_strings(project_skills),
    }


def _counterfactual_snapshot_delta(
    original_snapshot: Dict[str, List[str]],
    patched_snapshot: Dict[str, List[str]],
) -> Dict[str, Dict[str, List[str]]]:
    keys = sorted(set(original_snapshot) | set(patched_snapshot))
    delta: Dict[str, Dict[str, List[str]]] = {}

    for key in keys:
        original_values = set(original_snapshot.get(key, []) or [])
        patched_values = set(patched_snapshot.get(key, []) or [])

        added = sorted(patched_values - original_values)
        removed = sorted(original_values - patched_values)

        if added or removed:
            delta[key] = {
                "added": added,
                "removed": removed,
            }

    return delta

def _weighted_dimension_map(result: Any) -> Dict[str, float]:
    output: Dict[str, float] = {}
    for row in list(getattr(result, "dimension_scores", []) or []):
        name = str(getattr(row, "name", "") or "").strip()
        if not name:
            continue
        output[name] = float(getattr(row, "weighted_score", 0.0) or 0.0)
    return output


def _nonzero_dimension_deltas(original_result: Any, patched_result: Any) -> Dict[str, float]:
    original_map = _weighted_dimension_map(original_result)
    patched_map = _weighted_dimension_map(patched_result)

    names = sorted(set(original_map) | set(patched_map))
    deltas: Dict[str, float] = {}

    for name in names:
        delta = round(float(patched_map.get(name, 0.0)) - float(original_map.get(name, 0.0)), 6)
        if abs(delta) > 0:
            deltas[name] = delta

    return deltas


def _patched_resume_evidence_for_candidate(
    original_resume: Any,
    candidate: Dict[str, Any],
) -> Tuple[Optional[Any], str]:
    operation_type = str(candidate.get("operation_type", "") or "").strip()
    proposal_status = str(candidate.get("proposal_status", "") or "").strip()

    if proposal_status != "patch_ready":
        return None, "not_patch_ready"

    if operation_type == "rewrite":
        return build_counterfactual_resume_evidence(
            original_resume,
            str(candidate.get("source_bullet_id", "") or "").strip(),
            str(candidate.get("patch_text", "") or "").strip(),
            str(candidate.get("original_text", "") or "").strip(),
        )

    if operation_type == "reorder":
        return original_resume, "order_not_modeled_in_v1"

    if operation_type == "keep":
        return original_resume, "keep_existing_baseline"

    return None, "unsupported_operation"

def _apply_single_candidate_counterfactuals(
    payload: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    context = _counterfactual_context_from_payload(payload)

    original_result = context["original_result"] if context.get("ok", False) else None
    original_score = (
        round(float(getattr(original_result, "final_score", 0.0) or 0.0), 6)
        if original_result is not None else None
    )

    for row in candidates:
        row["original_final_score"] = original_score

        if str(row.get("operation_type", "") or "").strip() == "keep":
            row["counterfactual_status"] = "keep_existing_anchor"
            row["counterfactual_note"] = (
                "Existing anchor preserved for operator reference and not treated as a rewrite patch candidate."
            )
            row["projected_final_score"] = original_score
            row["projected_overall_delta"] = 0.0 if original_score is not None else None
            row["projected_dimension_deltas"] = {}
            continue

        if str(row.get("proposal_status", "") or "").strip() != "patch_ready":
            row["counterfactual_status"] = "not_patch_ready"
            row["counterfactual_note"] = "Projected scoring is only available for patch-ready candidates."
            row["projected_final_score"] = None
            row["projected_overall_delta"] = None
            row["projected_dimension_deltas"] = {}
            continue

        if not context.get("ok", False):
            reason = str(context.get("reason", "") or "context_unavailable").strip()
            row["counterfactual_status"] = reason
            row["counterfactual_note"] = (
                f"Could not load counterfactual context for projected scoring: {reason}."
            )
            row["projected_final_score"] = None
            row["projected_overall_delta"] = None
            row["projected_dimension_deltas"] = {}
            continue

        patched_resume, status = _patched_resume_evidence_for_candidate(
            context["original_resume"],
            row,
        )

        if status == "not_patch_ready":
            row["counterfactual_status"] = "not_patch_ready"
            row["counterfactual_note"] = "Projected scoring is only available for patch-ready candidates."
            row["projected_final_score"] = None
            row["projected_overall_delta"] = None
            row["projected_dimension_deltas"] = {}
            continue

        if status in {
            "bullet_id_not_found",
            "bullet_id_not_unique",
            "bullet_index_out_of_range",
            "raw_text_bullet_not_found",
            "raw_text_bullet_not_unique",
        }:
            row["counterfactual_status"] = status
            row["counterfactual_note"] = (
                "Could not safely apply the patch to the source resume text with a unique deterministic match."
            )
            row["projected_final_score"] = None
            row["projected_overall_delta"] = None
            row["projected_dimension_deltas"] = {}
            continue

        if status == "missing_patch_inputs":
            row["counterfactual_status"] = "missing_patch_inputs"
            row["counterfactual_note"] = "Projected scoring could not run because patch inputs were incomplete."
            row["projected_final_score"] = None
            row["projected_overall_delta"] = None
            row["projected_dimension_deltas"] = {}
            continue

        if status == "unsupported_operation":
            row["counterfactual_status"] = "unsupported_operation"
            row["counterfactual_note"] = "Projected scoring is not implemented yet for this operation type."
            row["projected_final_score"] = None
            row["projected_overall_delta"] = None
            row["projected_dimension_deltas"] = {}
            continue

        if status in {"order_not_modeled_in_v1", "keep_existing_baseline"}:
            row["counterfactual_status"] = status
            row["counterfactual_note"] = (
                "Current frozen evaluator does not model bullet order directly, so reorder is neutral in v1."
                if status == "order_not_modeled_in_v1"
                else "Keeping the bullet unchanged does not change the frozen evaluator score."
            )
            row["projected_final_score"] = original_score
            row["projected_overall_delta"] = 0.0
            row["projected_dimension_deltas"] = {}
            continue

        patched_result = score_resume_job_match(patched_resume, context["job_evidence"])
        patched_score = round(float(getattr(patched_result, "final_score", 0.0) or 0.0), 6)
        overall_delta = round(patched_score - original_score, 6)

        row["counterfactual_status"] = "scored"
        row["counterfactual_note"] = "Projected delta computed under the frozen deterministic evaluator."
        row["projected_final_score"] = patched_score
        row["projected_overall_delta"] = overall_delta
        row["projected_dimension_deltas"] = _nonzero_dimension_deltas(original_result, patched_result)

    return candidates

def _lowercase_first_character(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text[:1].lower() + text[1:]

def _deterministic_clause_extract_patch(
    diagnosis: Dict[str, Any],
) -> Optional[str]:
    if str(diagnosis.get("structural_operation", "") or "").strip() != "extract_clause":
        return None

    original_text = str(diagnosis.get("original_text", "") or "").strip()
    clause_text = str(
        diagnosis.get("structural_clause_text", "") or diagnosis.get("current_evidence", "") or ""
    ).strip()

    if not original_text or not clause_text:
        return None

    normalized_original = _diagnosis_normalize_term(original_text)
    normalized_clause = _diagnosis_normalize_term(clause_text)

    if normalized_clause == normalized_original:
        return None

    if normalized_clause not in normalized_original:
        return None

    matched_surface_signal = _diagnosis_normalize_term(
        str(diagnosis.get("matched_surface_signal", "") or "").strip()
    )
    canonical_supported_signal = _diagnosis_normalize_term(
        str(diagnosis.get("canonical_supported_signal", "") or "").strip()
    )

    promoted_clause = clause_text
    if (
        matched_surface_signal
        and canonical_supported_signal
        and matched_surface_signal != canonical_supported_signal
        and matched_surface_signal in _diagnosis_normalize_term(promoted_clause)
        and canonical_supported_signal not in _diagnosis_normalize_term(promoted_clause)
    ):
        promoted_clause = re.sub(
            rf"\b{re.escape(matched_surface_signal)}\b",
            canonical_supported_signal,
            promoted_clause,
            count=1,
            flags=re.IGNORECASE,
        ).strip()

    clauses = _split_promotable_clauses(original_text)
    if len(clauses) < 2:
        return None

    remaining_clauses: List[str] = []
    for clause in clauses:
        if _diagnosis_normalize_term(clause) == normalized_clause:
            continue
        cleaned = str(clause or "").strip().rstrip(" .")
        if cleaned:
            remaining_clauses.append(cleaned)

    promoted_clean = str(promoted_clause or "").strip().rstrip(" .")
    if not promoted_clean:
        return None

    patch_parts = [promoted_clean] + remaining_clauses
    patch_text = ". ".join(part for part in patch_parts if part).strip()

    if original_text.endswith("."):
        patch_text += "."

    if _diagnosis_normalize_term(patch_text) == normalized_original:
        return None

    return patch_text

def _deterministic_exact_signal_variant_patch(
    diagnosis: Dict[str, Any],
) -> Optional[Tuple[str, str]]:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    if not original_text:
        return None

    matched_surface_signal = _diagnosis_normalize_term(
        str(diagnosis.get("matched_surface_signal", "") or "").strip()
    )
    canonical_supported_signal = _diagnosis_normalize_term(
        str(diagnosis.get("canonical_supported_signal", "") or "").strip()
    )

    if not matched_surface_signal or not canonical_supported_signal:
        return None

    if matched_surface_signal == canonical_supported_signal:
        return None

    normalized_text = _diagnosis_normalize_term(original_text)
    if matched_surface_signal not in normalized_text:
        return None

    if canonical_supported_signal in normalized_text:
        return None

    supported_families = families_for_terms([canonical_supported_signal])
    if len(supported_families) != 1:
        return None

    supported_family = supported_families[0]
    impacted_dimensions = {
        str(item).strip()
        for item in (diagnosis.get("likely_impacted_dimensions", []) or [])
        if str(item).strip()
    }
    required_dimensions = _PROMOTABLE_SIGNAL_FAMILY_REQUIRED_DIMENSIONS.get(
        supported_family,
        set(),
    )
    if required_dimensions and not (impacted_dimensions & required_dimensions):
        return None

    patch_text = re.sub(
        rf"\b{re.escape(matched_surface_signal)}\b",
        canonical_supported_signal,
        original_text,
        count=1,
        flags=re.IGNORECASE,
    ).strip()

    if _diagnosis_normalize_term(patch_text) == normalized_text:
        return None

    return canonical_supported_signal, patch_text

def _deterministic_parent_signal_label_patch(
    diagnosis: Dict[str, Any],
) -> Optional[Tuple[str, str]]:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    if not original_text:
        return None

    supported_terms = [
        _diagnosis_normalize_term(item)
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if _diagnosis_normalize_term(item)
    ]
    if len(supported_terms) != 1:
        return None

    supported_families = [
        family
        for family in families_for_terms(supported_terms)
        if family in _PROMOTABLE_SIGNAL_FAMILY_LABELS
    ]
    if len(supported_families) != 1:
        return None

    supported_family = supported_families[0]

    impacted_dimensions = {
        str(item).strip()
        for item in (diagnosis.get("likely_impacted_dimensions", []) or [])
        if str(item).strip()
    }
    required_dimensions = _PROMOTABLE_SIGNAL_FAMILY_REQUIRED_DIMENSIONS.get(
        supported_family,
        set(),
    )
    if required_dimensions and not (impacted_dimensions & required_dimensions):
        return None

    label = _PROMOTABLE_SIGNAL_FAMILY_LABELS[supported_family]
    normalized_text = _diagnosis_normalize_term(original_text)
    normalized_label = _diagnosis_normalize_term(label)

    if normalized_label in normalized_text:
        return None

    if re.match(rf"^\s*{re.escape(label)}\s*:", original_text, flags=re.IGNORECASE):
        return None

    patch_text = f"{label}: {original_text}".strip()
    if _diagnosis_normalize_term(patch_text) == normalized_text:
        return None

    return supported_family, patch_text

def _using_phrase_match_for_supported_term(
    original_text: str,
    supported_terms: List[str],
) -> Optional[re.Match]:
    text = str(original_text or "").strip()
    if not text:
        return None

    normalized_supported = {
        _diagnosis_normalize_term(item)
        for item in (supported_terms or [])
        if _diagnosis_normalize_term(item)
    }
    if not normalized_supported:
        return None

    for match in re.finditer(r"\busing\s+(?P<phrase>[^,.;]+)", text, flags=re.IGNORECASE):
        phrase = str(match.group("phrase") or "").strip()
        phrase_norm = _diagnosis_normalize_term(phrase)
        if any(term in phrase_norm for term in normalized_supported):
            return match

    return None


def _deterministic_patch_text_from_diagnosis(
    diagnosis: Dict[str, Any],
    adjacent_risk_signals: List[str],
    unsupported_risk_signals: List[str],
) -> Tuple[str, str, str]:
    claim_safety = str(diagnosis.get("claim_safety", "") or "").strip()
    confidence = _replacement_candidate_confidence(diagnosis)
    supported_terms = list(diagnosis.get("jd_signal_terms", []) or [])
    original_text = str(diagnosis.get("original_text", "") or "").strip()

    if claim_safety != "safe_strengthen":
        return "direction_only", "", ""

    if confidence != "high":
        return "direction_only", "", ""

    if adjacent_risk_signals or unsupported_risk_signals:
        return "direction_only", "", ""

    if len(supported_terms) != 1:
        return "direction_only", "", ""

    clause_patch = _deterministic_clause_extract_patch(diagnosis)
    if clause_patch:
        return "patch_ready", clause_patch, "deterministic_clause_extract"

    exact_signal_patch = _deterministic_exact_signal_variant_patch(diagnosis)
    if exact_signal_patch:
        _, patch_text = exact_signal_patch
        return "patch_ready", patch_text, "deterministic_exact_signal_variant"

    parent_signal_patch = _deterministic_parent_signal_label_patch(diagnosis)
    if parent_signal_patch:
        _, patch_text = parent_signal_patch
        return "patch_ready", patch_text, "deterministic_parent_signal_label"

    match = _using_phrase_match_for_supported_term(original_text, supported_terms)
    if not match:
        return "direction_only", "", ""

    phrase = str(match.group("phrase") or "").strip()
    before = original_text[: match.start()].strip(" ,")
    after = original_text[match.end() :].lstrip(" ,")

    if not before:
        return "direction_only", "", ""

    rest = " ".join(part for part in [before, after] if str(part or "").strip()).strip()
    if not rest:
        return "direction_only", "", ""

    rest = re.sub(r"\s+", " ", rest)
    rest = _lowercase_first_character(rest)

    patch_text = f"Using {phrase}, {rest}".strip()
    patch_text = re.sub(r"\s+,", ",", patch_text)
    patch_text = patch_text.rstrip(" .")
    if original_text.endswith("."):
        patch_text += "."

    if _diagnosis_normalize_term(patch_text) == _diagnosis_normalize_term(original_text):
        return "direction_only", "", ""

    return "patch_ready", patch_text, "deterministic_using_phrase"

def _materiality_validate_rewrite_candidate(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
    context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if str(candidate.get("operation_type", "") or "").strip() != "rewrite":
        return candidate

    if str(candidate.get("proposal_status", "") or "").strip() != "patch_ready":
        return candidate

    if not context.get("ok", False):
        reason = str(context.get("reason", "") or "context_unavailable").strip()
        candidate["materiality_validation_status"] = reason
        candidate["materiality_validation_note"] = (
            f"Could not pre-validate patch materiality because counterfactual context was unavailable: {reason}."
        )
        return candidate

    patched_resume, status = _patched_resume_evidence_for_candidate(
        context["original_resume"],
        candidate,
    )

    candidate["materiality_validation_status"] = status
    candidate["materiality_validation_note"] = ""
    candidate["precheck_projected_overall_delta"] = None
    candidate["precheck_projected_dimension_deltas"] = {}
    candidate["precheck_scorer_visible_evidence_changed"] = False
    candidate["precheck_evidence_delta"] = {}

    if patched_resume is None or status not in {"ok"}:
        candidate["proposal_status"] = "direction_only"
        candidate["proposal_type"] = "directional_rewrite"
        candidate["patch_ready"] = False
        candidate["material_delta_found"] = False
        candidate["materiality_validation_note"] = (
            "Deterministic patch could not be pre-validated as a safe material candidate."
        )
        return candidate

    original_result = context["original_result"]
    original_score = round(float(getattr(original_result, "final_score", 0.0) or 0.0), 6)
    original_snapshot = _resume_counterfactual_snapshot(context["original_resume"])

    patched_result = score_resume_job_match(patched_resume, context["job_evidence"])
    patched_score = round(float(getattr(patched_result, "final_score", 0.0) or 0.0), 6)
    overall_delta = round(patched_score - original_score, 6)

    patched_snapshot = _resume_counterfactual_snapshot(patched_resume)
    evidence_delta = _counterfactual_snapshot_delta(original_snapshot, patched_snapshot)
    evidence_changed = bool(evidence_delta)

    candidate["precheck_projected_overall_delta"] = overall_delta
    candidate["precheck_projected_dimension_deltas"] = _nonzero_dimension_deltas(
        original_result,
        patched_result,
    )
    candidate["precheck_scorer_visible_evidence_changed"] = evidence_changed
    candidate["precheck_evidence_delta"] = evidence_delta

    patch_generation_method = str(candidate.get("patch_generation_method", "") or "").strip()

    export_safe_neutral_methods = {
        "deterministic_clause_extract",
        "deterministic_exact_signal_variant",
        "deterministic_parent_signal_label",
        "deterministic_using_phrase",
    }

    if overall_delta == 0.0 and patch_generation_method in export_safe_neutral_methods:
        candidate["material_delta_found"] = False
        candidate["materiality_validation_status"] = "export_safe_no_score_lift"
        candidate["materiality_validation_note"] = (
            "Deterministic rewrite is grounded and patch-safe for export, but the frozen scorer shows no projected score lift."
        )
        return candidate

    if overall_delta == 0.0 and not evidence_changed:
        candidate["proposal_status"] = "direction_only"
        candidate["proposal_type"] = "directional_rewrite"
        candidate["patch_ready"] = False
        candidate["material_delta_found"] = False
        candidate["materiality_validation_status"] = "scorer_neutral_no_evidence_change"
        candidate["materiality_validation_note"] = (
            "Deterministic rewrite changes phrasing only and does not change scorer-visible evidence, so it remains directional."
        )
        return candidate

    candidate["material_delta_found"] = True
    candidate["materiality_validation_status"] = "material_candidate"
    candidate["materiality_validation_note"] = (
        "Deterministic rewrite survived pre-validation as a scorer-material patch candidate."
    )
    return candidate

def _build_replacement_candidates(
    payload: Dict[str, Any],
    bullet_diagnoses: List[Dict[str, Any]],
    limit: int = 12,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    seen_keys = set()
    counterfactual_context = _counterfactual_context_from_payload(payload)

    # Pass 1: primary candidates from diagnoses
    for index, diagnosis in enumerate(bullet_diagnoses, start=1):
        action = str(diagnosis.get("diagnosis_action", "") or "").strip()
        key = _bullet_diagnosis_key(diagnosis)

        if action == "rewrite":
            if key in seen_keys:
                continue
            seen_keys.add(key)

            candidate = _diagnosis_to_replacement_candidate(payload, diagnosis, index)
            candidate = _materiality_validate_rewrite_candidate(
                payload,
                candidate,
                counterfactual_context,
            )
            candidates.append(candidate)

        elif action == "keep":
            keep_key = ("keep",) + key
            if keep_key not in seen_keys:
                seen_keys.add(keep_key)
                keep_candidate = _diagnosis_to_keep_candidate(diagnosis, index)
                keep_candidate = _normalize_keep_candidate_for_existing_anchor(
                    keep_candidate
                )
                candidates.append(keep_candidate)

        if len(candidates) >= limit:
            break

    # Pass 2: reorder companions for strong patch-ready rewrite candidates
    expanded: List[Dict[str, Any]] = []
    for candidate in candidates:
        expanded.append(candidate)

        if len(expanded) >= limit:
            continue

        if _should_create_reorder_companion(candidate):
            reorder_candidate = _rewrite_candidate_to_reorder_companion(candidate)
            reorder_id = str(reorder_candidate.get("candidate_id", "") or "").strip()

            candidate_conflicts = list(candidate.get("conflicts_with", []) or [])
            if reorder_id not in candidate_conflicts:
                candidate_conflicts.append(reorder_id)
            candidate["conflicts_with"] = candidate_conflicts

            expanded.append(reorder_candidate)

    return _apply_candidate_grouping(expanded[:limit])

def _is_parent_signal_material_rewrite_diagnosis(
    diagnosis: Dict[str, Any],
) -> bool:
    if str(diagnosis.get("diagnosis_action", "") or "").strip() != "rewrite":
        return False

    return any([
        _deterministic_clause_extract_patch(diagnosis) is not None,
        _deterministic_exact_signal_variant_patch(diagnosis) is not None,
        _deterministic_parent_signal_label_patch(diagnosis) is not None,
    ])


def _normalize_keep_candidate_for_existing_anchor(
    candidate: Dict[str, Any],
) -> Dict[str, Any]:
    candidate["proposal_status"] = "keep_only"
    candidate["proposal_type"] = "keep_existing_anchor"
    candidate["patch_ready"] = False
    candidate["material_delta_found"] = False
    candidate["materiality_validation_status"] = "not_applicable_keep_existing"
    candidate["materiality_validation_note"] = (
        "Existing anchor preserved for operator reference and not treated as a rewrite patch candidate."
    )
    candidate["precheck_projected_overall_delta"] = None
    candidate["precheck_projected_dimension_deltas"] = {}
    candidate["precheck_scorer_visible_evidence_changed"] = False
    candidate["precheck_evidence_delta"] = {}
    return candidate

def _build_bullet_diagnoses(
    packet: Dict[str, Any],
    edit_cards: List[Dict[str, Any]],
    keep_as_is: List[Dict[str, Any]],
    limit: int = 12,
) -> List[Dict[str, Any]]:
    prioritized_edit_diagnoses: List[Dict[str, Any]] = []
    regular_edit_diagnoses: List[Dict[str, Any]] = []
    diagnoses: List[Dict[str, Any]] = []
    seen_keys = set()

    for index, card in enumerate(edit_cards, start=1):
        diagnosis = _edit_card_to_bullet_diagnosis(packet, card, index)
        key = _bullet_diagnosis_key(diagnosis)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        if _is_parent_signal_material_rewrite_diagnosis(diagnosis):
            prioritized_edit_diagnoses.append(diagnosis)
        else:
            regular_edit_diagnoses.append(diagnosis)

    diagnoses.extend(prioritized_edit_diagnoses)
    diagnoses.extend(regular_edit_diagnoses)
    diagnoses = diagnoses[:limit]

    if len(diagnoses) >= limit:
        return diagnoses

    for index, row in enumerate(keep_as_is, start=1):
        diagnosis = _keep_as_is_to_bullet_diagnosis(packet, row, index)
        key = _bullet_diagnosis_key(diagnosis)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        diagnoses.append(diagnosis)
        if len(diagnoses) >= limit:
            break

    return diagnoses

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

    edit_cards = _build_edit_cards(
        operator_payload,
        preferred_rewrite_directions,
    )
    operator_payload["edit_cards"] = edit_cards
    operator_payload["top_edit_priorities"] = _build_top_edit_priorities(edit_cards)
    operator_payload["bullet_diagnoses"] = _build_bullet_diagnoses(
        operator_payload,
        edit_cards,
        operator_payload.get("keep_as_is", []) or [],
    )
    operator_payload["replacement_candidates"] = _build_replacement_candidates(
        operator_payload,
        operator_payload.get("bullet_diagnoses", []) or [],
    )
    operator_payload["replacement_candidates"] = _apply_single_candidate_counterfactuals(
        operator_payload,
        operator_payload.get("replacement_candidates", []) or [],
    )

    return operator_payload

def _build_payload(
    packet: Dict[str, Any],
    include_llm_prompts: bool = False,
) -> Dict[str, Any]:
    recruiter_summary = _build_recruiter_summary(packet)
    keep_emphasize = _build_keep_emphasize(packet)
    do_not_claim = _build_do_not_claim(packet)
    tailoring_plan = _build_tailoring_plan(packet)
    bullet_reuse = _build_bullet_reuse(packet, tailoring_plan=tailoring_plan)
    rewrite_candidates = _build_rewrite_candidates(packet, tailoring_plan=tailoring_plan)
    evidence_layers = _build_evidence_layers(packet, tailoring_plan=tailoring_plan)
    tailoring_actions = _build_tailoring_actions(packet)
    claim_safety_notes = _build_claim_safety_notes(packet, tailoring_plan)
    material_gaps = _build_material_gaps(packet, tailoring_plan)
    keep_as_is = _build_keep_as_is(keep_emphasize, bullet_reuse)
    empty_state_reason = _build_empty_state_reason(
        packet,
        tailoring_plan,
        rewrite_candidates,
        bullet_reuse,
        keep_as_is,
        claim_safety_notes,
        material_gaps,
    )
    
    llm_prompt = ""
    live_rewrite_prompt = ""

    if include_llm_prompts:
        from src.tailoring.llm import (
            _build_llm_prompt,
            _build_live_rewrite_prompt,
        )

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
        "keep_as_is": keep_as_is,
        "empty_state_reason": empty_state_reason,
        "claim_safety_notes": claim_safety_notes,
        "material_gaps": material_gaps,
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

def _slugify_training_key(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\.[a-z0-9]+$", "", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def _packet_stem_key(path_value: str) -> str:
    raw = str(path_value or "").strip()
    if not raw:
        return ""
    return Path(raw).stem.strip()

def _directions_fingerprint(directions: List[str]) -> str:
    normalized = [
        str(item or "").strip()
        for item in (directions or [])
        if str(item or "").strip()
    ]
    if not normalized:
        return ""
    payload = "\n".join(normalized)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]

def _build_training_log_row(
    payload: Dict[str, Any],
    llm_output: Optional[Dict[str, Any]],
    packet_json_path: str = "",
    generated_at_utc: str = "",
    output_json_path: str = "",
    output_md_path: str = "",
    output_llm_json_path: str = "",
) -> Dict[str, Any]:
    job = payload.get("job", {}) or {}
    selection = payload.get("selection", {}) or {}
    summary = payload.get("summary", {}) or {}
    audit = payload.get("preferred_rewrite_selection_audit", {}) or {}
    verifier = payload.get("preferred_rewrite_verifier", {}) or {}
    llm_output = llm_output or {}
    tailoring_plan = payload.get("tailoring_plan", {}) or {}

    company_slug = _slugify_training_key(job.get("company", ""))
    job_slug = _slugify_training_key(job.get("title", ""))
    resume_slug = _slugify_training_key(selection.get("selected_resume", ""))
    packet_key = _packet_stem_key(packet_json_path)

    job_key = ""
    if company_slug and job_slug:
        job_key = f"{company_slug}__{job_slug}"
    else:
        job_key = company_slug or job_slug

    candidate_pool = audit.get("candidate_pool", []) or []
    candidate_lineage = audit.get("candidate_pool_lineage", []) or []

    def _candidate_by_id(candidate_id: str) -> Dict[str, Any]:
        for candidate in candidate_pool:
            if str(candidate.get("candidate_id", "") or "").strip() == str(candidate_id or "").strip():
                return candidate
        return {}

    def _max_quality_score_for_family(prefix: str) -> Optional[float]:
        scores: List[float] = []
        for candidate in candidate_pool:
            source_family = str(candidate.get("source_family", "") or "").strip()
            if source_family == prefix:
                score = candidate.get("quality_score")
                if isinstance(score, (int, float)):
                    scores.append(float(score))
        return max(scores) if scores else None

    def _count_valid_kept_family_candidates(prefix: str) -> int:
        count = 0
        for candidate in candidate_pool:
            source_family = str(candidate.get("source_family", "") or "").strip()
            if source_family != prefix:
                continue
            if candidate.get("covers_plan") and candidate.get("verifier_ok"):
                count += 1
        return count

    def _has_lineage_family_candidate(prefix: str) -> bool:
        for candidate in candidate_lineage:
            source_family = str(candidate.get("source_family", "") or "").strip()
            if source_family == prefix:
                return True
        return False

    def _has_valid_lineage_family_candidate(prefix: str) -> bool:
        for candidate in candidate_lineage:
            source_family = str(candidate.get("source_family", "") or "").strip()
            if source_family != prefix:
                continue
            resolved_to_candidate_id = str(candidate.get("resolved_to_candidate_id", "") or "").strip()
            resolved_candidate = _candidate_by_id(resolved_to_candidate_id) if resolved_to_candidate_id else {}
            if resolved_candidate.get("covers_plan") and resolved_candidate.get("verifier_ok"):
                return True
        return False
    
    def _count_valid_lineage_family_candidates(prefix: str) -> int:
        count = 0
        for candidate in candidate_lineage:
            source_family = str(candidate.get("source_family", "") or "").strip()
            if source_family != prefix:
                continue
            resolved_to_candidate_id = str(candidate.get("resolved_to_candidate_id", "") or "").strip()
            resolved_candidate = _candidate_by_id(resolved_to_candidate_id) if resolved_to_candidate_id else {}
            if resolved_candidate.get("covers_plan") and resolved_candidate.get("verifier_ok"):
                count += 1
        return count
    
    selected_candidate_id = str(audit.get("selected_candidate_id", "") or "").strip()
    selected_candidate = _candidate_by_id(selected_candidate_id)
    selected_equivalent_candidate_ids = audit.get("selected_equivalent_candidate_ids", []) or []

    live_equivalent_candidate_ids = [
        candidate_id
        for candidate_id in selected_equivalent_candidate_ids
        if str(candidate_id).startswith("live_llm")
    ]

    combined_candidates: List[Dict[str, Any]] = []
    seen_candidate_ids = set()

    for candidate in list(candidate_pool) + list(candidate_lineage):
        candidate_id = str(candidate.get("candidate_id", "") or "").strip()
        if not candidate_id or candidate_id in seen_candidate_ids:
            continue
        combined_candidates.append(candidate)
        seen_candidate_ids.add(candidate_id)

    candidate_lookup = {
        str(candidate.get("candidate_id", "") or "").strip(): candidate
        for candidate in combined_candidates
        if str(candidate.get("candidate_id", "") or "").strip()
    }

    def _candidate_fingerprint_by_id(candidate_id: str) -> str:
        candidate = candidate_lookup.get(str(candidate_id or "").strip(), {})
        return _directions_fingerprint(candidate.get("directions", []) or [])

    preferred_rewrite_fingerprint = _directions_fingerprint(
        payload.get("preferred_rewrite_directions", []) or []
    )
    selected_candidate_fingerprint = _candidate_fingerprint_by_id(selected_candidate_id)

    selected_equivalent_candidate_fingerprints = [
        {
            "candidate_id": str(candidate_id or "").strip(),
            "directions_fingerprint": _candidate_fingerprint_by_id(str(candidate_id or "").strip()),
        }
        for candidate_id in selected_equivalent_candidate_ids
        if str(candidate_id or "").strip()
    ]

    candidate_fingerprints = []
    for candidate in combined_candidates:
        candidate_id = str(candidate.get("candidate_id", "") or "").strip()
        resolved_to_candidate_id = str(candidate.get("resolved_to_candidate_id", "") or "").strip()

        candidate_fingerprints.append(
            {
                "candidate_id": candidate_id,
                "source_family": str(candidate.get("source_family", "") or "").strip(),
                "is_polished": bool(candidate.get("is_polished", False)),
                "status": str(candidate.get("status", "") or "").strip(),
                "directions_fingerprint": _directions_fingerprint(candidate.get("directions", []) or []),
                "resolved_to_candidate_id": resolved_to_candidate_id,
                "resolved_to_directions_fingerprint": (
                    _candidate_fingerprint_by_id(resolved_to_candidate_id)
                    if resolved_to_candidate_id else ""
                ),
            }
        )
    
    def _resolved_candidate_for_lineage_item(candidate: Dict[str, Any]) -> Dict[str, Any]:
        
        resolved_to_candidate_id = str(candidate.get("resolved_to_candidate_id", "") or "").strip()
        if resolved_to_candidate_id:
            resolved = candidate_lookup.get(resolved_to_candidate_id, {})
            if resolved:
                return resolved
        return candidate_lookup.get(str(candidate.get("candidate_id", "") or "").strip(), {})

    def _candidate_rank_tuple(candidate: Dict[str, Any]) -> tuple:
        quality_score = candidate.get("quality_score")
        quality_value = float(quality_score) if isinstance(quality_score, (int, float)) else float("-inf")
        is_polished = 1 if candidate.get("is_polished", False) else 0
        candidate_id = str(candidate.get("candidate_id", "") or "").strip()
        return (quality_value, is_polished, candidate_id)

    def _best_family_effective_candidate(prefix: str) -> Dict[str, Any]:
        best_lineage_item: Optional[Dict[str, Any]] = None
        best_effective_candidate: Optional[Dict[str, Any]] = None
        best_rank: Optional[tuple] = None

        for lineage_item in candidate_lineage:
            source_family = str(lineage_item.get("source_family", "") or "").strip()
            if source_family != prefix:
                continue

            effective_candidate = _resolved_candidate_for_lineage_item(lineage_item)
            if not effective_candidate:
                continue

            if not (effective_candidate.get("covers_plan") and effective_candidate.get("verifier_ok")):
                continue

            rank = _candidate_rank_tuple(effective_candidate)
            if best_rank is None or rank > best_rank:
                best_rank = rank
                best_lineage_item = lineage_item
                best_effective_candidate = effective_candidate

        if best_lineage_item is None or best_effective_candidate is None:
            return {}

        return {
            "lineage_candidate_id": str(best_lineage_item.get("candidate_id", "") or "").strip(),
            "effective_candidate_id": str(best_effective_candidate.get("candidate_id", "") or "").strip(),
            "effective_source_family": str(best_effective_candidate.get("source_family", "") or "").strip(),
            "directions_fingerprint": _directions_fingerprint(best_effective_candidate.get("directions", []) or []),
        }

    deterministic_family_fingerprint_info = _best_family_effective_candidate("deterministic_planner")
    live_family_fingerprint_info = _best_family_effective_candidate("live_llm")
    live_blended_family_fingerprint_info = _best_family_effective_candidate("live_llm_blended")

    deterministic_family_fingerprint = str(
        deterministic_family_fingerprint_info.get("directions_fingerprint", "") or ""
    )
    live_family_fingerprint = str(
        live_family_fingerprint_info.get("directions_fingerprint", "") or ""
    )
    live_blended_family_fingerprint = str(
        live_blended_family_fingerprint_info.get("directions_fingerprint", "") or ""
    )

    selected_matches_deterministic_family = (
        bool(selected_candidate_fingerprint)
        and bool(deterministic_family_fingerprint)
        and selected_candidate_fingerprint == deterministic_family_fingerprint
    )
    selected_matches_live_family = (
        bool(selected_candidate_fingerprint)
        and bool(live_family_fingerprint)
        and selected_candidate_fingerprint == live_family_fingerprint
    )
    selected_matches_live_blended_family = (
        bool(selected_candidate_fingerprint)
        and bool(live_blended_family_fingerprint)
        and selected_candidate_fingerprint == live_blended_family_fingerprint
    )
    deterministic_matches_live_family = (
        bool(deterministic_family_fingerprint)
        and bool(live_family_fingerprint)
        and deterministic_family_fingerprint == live_family_fingerprint
    )
    deterministic_matches_live_blended_family = (
        bool(deterministic_family_fingerprint)
        and bool(live_blended_family_fingerprint)
        and deterministic_family_fingerprint == live_blended_family_fingerprint
    )
    live_matches_live_blended_family = (
        bool(live_family_fingerprint)
        and bool(live_blended_family_fingerprint)
        and live_family_fingerprint == live_blended_family_fingerprint
    )
    selected_source = str(audit.get("selected_source", "") or "").strip()
    selected_reason = str(audit.get("selected_reason", "") or "").strip()

    has_valid_live_lineage_candidate = _has_valid_lineage_family_candidate("live_llm")
    has_valid_live_blended_lineage_candidate = _has_valid_lineage_family_candidate("live_llm_blended")
    has_any_valid_live_family_candidate = (
        has_valid_live_lineage_candidate or has_valid_live_blended_lineage_candidate
    )

    has_live_equivalent = len(live_equivalent_candidate_ids) > 0

    if selected_source == "deterministic_planner":
        if has_live_equivalent:
            selection_outcome_bucket = "deterministic_kept_equivalent_live"
        elif has_any_valid_live_family_candidate:
            selection_outcome_bucket = "deterministic_kept_live_valid_but_not_equivalent"
        else:
            selection_outcome_bucket = "deterministic_kept_no_valid_live"
    elif selected_source.startswith("live_llm"):
        selection_outcome_bucket = "live_selected"
    else:
        selection_outcome_bucket = "other_selected"

    if has_any_valid_live_family_candidate:
        if has_live_equivalent:
            live_outcome_bucket = "valid_live_equivalent_to_selected"
        else:
            live_outcome_bucket = "valid_live_present"
    else:
        if audit.get("llm_requested"):
            live_outcome_bucket = "no_valid_live_after_llm"
        else:
            live_outcome_bucket = "llm_not_requested"

    if has_live_equivalent:
        equivalence_outcome_bucket = "live_equivalent_selected"
    elif has_any_valid_live_family_candidate:
        equivalence_outcome_bucket = "valid_live_not_equivalent"
    else:
        equivalence_outcome_bucket = "no_live_equivalence"

    if "identical_best" in selected_reason:
        equivalence_outcome_bucket = "identical_best"
    elif "equivalent_quality" in selected_reason:
        equivalence_outcome_bucket = "equivalent_quality"

    return {
        "schema_version": "tailoring_training_log_v6",
        "generated_at_utc": str(generated_at_utc or ""),
        "artifacts": {
            "output_json_path": str(output_json_path or ""),
            "output_md_path": str(output_md_path or ""),
            "output_llm_json_path": str(output_llm_json_path or ""),
        },
        "analysis_keys": {
            "packet_key": packet_key,
            "job_key": job_key,
            "resume_key": resume_slug,
            "company_slug": company_slug,
            "job_slug": job_slug,
            "resume_slug": resume_slug,
        },
        "packet_json_path": str(packet_json_path or ""),
        "compatibility_mode": bool(tailoring_plan.get("compatibility_mode", False)),
        "compatibility_reason": str(tailoring_plan.get("compatibility_reason", "") or ""),
        "job": {
            "company": job.get("company", ""),
            "title": job.get("title", ""),
            "location": job.get("location", ""),
            "link": job.get("link", "") or job.get("url", ""),
        },
        "selection": {
            "selected_resume": selection.get("selected_resume", ""),
            "selected_score": selection.get("selected_score", 0.0),
        },
        "summary": summary,
        "preferred_rewrite_source": payload.get("preferred_rewrite_source", ""),
        "preferred_rewrite_directions": payload.get("preferred_rewrite_directions", []) or [],
        "preferred_rewrite_verifier": verifier,
        "selected_candidate_id": audit.get("selected_candidate_id", ""),
        "selected_source": audit.get("selected_source", ""),
        "selected_reason": audit.get("selected_reason", ""),
        "selected_equivalent_candidate_ids": audit.get("selected_equivalent_candidate_ids", []) or [],
        "selection_outcome_bucket": selection_outcome_bucket,
        "live_outcome_bucket": live_outcome_bucket,
        "equivalence_outcome_bucket": equivalence_outcome_bucket,
        "fingerprints": {
            "preferred_rewrite_fingerprint": preferred_rewrite_fingerprint,
            "selected_candidate_fingerprint": selected_candidate_fingerprint,
            "selected_equivalent_candidate_fingerprints": selected_equivalent_candidate_fingerprints,
            "candidate_fingerprints": candidate_fingerprints,
            "family_fingerprints": {
                "deterministic_planner": deterministic_family_fingerprint_info,
                "live_llm": live_family_fingerprint_info,
                "live_llm_blended": live_blended_family_fingerprint_info,
            },
            "family_fingerprint_matches": {
                "selected_matches_deterministic_family": selected_matches_deterministic_family,
                "selected_matches_live_family": selected_matches_live_family,
                "selected_matches_live_blended_family": selected_matches_live_blended_family,
                "deterministic_matches_live_family": deterministic_matches_live_family,
                "deterministic_matches_live_blended_family": deterministic_matches_live_blended_family,
                "live_matches_live_blended_family": live_matches_live_blended_family,
            },
        },
        "fallback_reason_codes": audit.get("fallback_reason_codes", []) or [],
        "llm": {
            "requested": audit.get("llm_requested", False),
            "parse_ok": audit.get("llm_parse_ok", False),
            "strong_enough": audit.get("llm_strong_enough", False),
            "requested_provider": llm_output.get("requested_provider", ""),
            "requested_model": llm_output.get("requested_model", ""),
            "resolved_provider": llm_output.get("resolved_provider", ""),
            "resolved_model": llm_output.get("resolved_model", ""),
            "fallback_used": llm_output.get("fallback_used", False),
            "cache_hit": llm_output.get("cache_hit", False),
            "parse_error": llm_output.get("parse_error", ""),
            "prompt_version": llm_output.get("prompt_version", ""),
        },
        "eval_summary": {
            "candidate_pool_count": len(candidate_pool),
            "candidate_lineage_count": len(candidate_lineage),
            "valid_candidate_count": sum(
                1 for candidate in candidate_pool
                if candidate.get("covers_plan") and candidate.get("verifier_ok")
            ),
            "selected_candidate_quality_score": selected_candidate.get("quality_score"),
            "deterministic_best_quality_score": _max_quality_score_for_family("deterministic_planner"),
            "live_best_quality_score": _max_quality_score_for_family("live_llm"),
            "live_blended_best_quality_score": _max_quality_score_for_family("live_llm_blended"),
            "deterministic_valid_kept_candidate_count": _count_valid_kept_family_candidates("deterministic_planner"),
            "live_valid_kept_candidate_count": _count_valid_kept_family_candidates("live_llm"),
            "live_blended_valid_kept_candidate_count": _count_valid_kept_family_candidates("live_llm_blended"),
            "deterministic_valid_lineage_candidate_count": _count_valid_lineage_family_candidates("deterministic_planner"),
            "live_valid_lineage_candidate_count": _count_valid_lineage_family_candidates("live_llm"),
            "live_blended_valid_lineage_candidate_count": _count_valid_lineage_family_candidates("live_llm_blended"),
            "has_live_lineage_candidate": _has_lineage_family_candidate("live_llm"),
            "has_live_blended_lineage_candidate": _has_lineage_family_candidate("live_llm_blended"),
            "has_valid_live_lineage_candidate": _has_valid_lineage_family_candidate("live_llm"),
            "has_valid_live_blended_lineage_candidate": _has_valid_lineage_family_candidate("live_llm_blended"),
            "selected_has_live_equivalent": len(live_equivalent_candidate_ids) > 0,
            "live_equivalent_candidate_ids": live_equivalent_candidate_ids,
            "selected_is_deterministic": str(audit.get("selected_source", "") or "") == "deterministic_planner",
            "selected_reason": str(audit.get("selected_reason", "") or ""),
            "selection_outcome_bucket": selection_outcome_bucket,
            "live_outcome_bucket": live_outcome_bucket,
            "equivalence_outcome_bucket": equivalence_outcome_bucket,
            "preferred_rewrite_fingerprint": preferred_rewrite_fingerprint,
            "selected_candidate_fingerprint": selected_candidate_fingerprint,
            "deterministic_family_fingerprint": deterministic_family_fingerprint,
            "live_family_fingerprint": live_family_fingerprint,
            "live_blended_family_fingerprint": live_blended_family_fingerprint,
            "selected_matches_deterministic_family": selected_matches_deterministic_family,
            "selected_matches_live_family": selected_matches_live_family,
            "selected_matches_live_blended_family": selected_matches_live_blended_family,
            "deterministic_matches_live_family": deterministic_matches_live_family,
            "deterministic_matches_live_blended_family": deterministic_matches_live_blended_family,
            "live_matches_live_blended_family": live_matches_live_blended_family,
        },
        "source_family_audits": {
            "deterministic_planner": audit.get("deterministic_planner"),
            "live_llm": audit.get("live_llm"),
            "live_llm_blended": audit.get("live_llm_blended"),
        },
        "candidate_pool": audit.get("candidate_pool", []) or [],
        "candidate_pool_lineage": audit.get("candidate_pool_lineage", []) or [],
        "planner_seed_rewrite_directions": payload.get("planner_seed_rewrite_directions", []) or [],
        "tailoring_plan": payload.get("tailoring_plan", {}) or {},
        "do_not_claim": payload.get("do_not_claim", []) or [],
        "guardrail": payload.get("guardrail", ""),
    }

def _markdown_from_payload(payload: Dict[str, Any]) -> str:
    job = payload.get("job", {}) or {}
    selection = payload.get("selection", {}) or {}
    tailoring_plan = payload.get("tailoring_plan", {}) or {}
    top_edit_priorities = payload.get("top_edit_priorities", []) or []
    edit_cards = payload.get("edit_cards", []) or []
    keep_as_is = payload.get("keep_as_is", []) or []
    claim_safety_notes = payload.get("claim_safety_notes", {}) or {}
    material_gaps = payload.get("material_gaps", []) or []

    lines: List[str] = []

    lines.append("# Tailoring Suggestions")
    lines.append("")
    lines.append(f"**Job:** {job.get('company', '')} | {job.get('title', '')}")
    lines.append(f"**Selected resume:** {_display_resume_name(selection.get('selected_resume', ''))}")
    lines.append(f"**Selected score:** {selection.get('selected_score', 0.0):.3f}")
    lines.append("")

    lines.append("## Start Here")
    lines.append("- Work from the highest-impact edits first.")
    lines.append("- Rewrite only what is already supported by real resume evidence.")
    lines.append("- Use the claim-safety notes before adding JD language.")
    lines.append("")

    if top_edit_priorities:
        lines.append("## Highest-Impact Edits")
        for index, item in enumerate(top_edit_priorities, start=1):
            lines.append(
                f"### {index}. {str(item.get('priority', '')).title()} priority • "
                f"{str(item.get('edit_type', '')).replace('_', ' ').title()}"
            )
            if item.get("jd_signal"):
                lines.append(f"- JD signal: {item.get('jd_signal', '')}")
            if item.get("target_section"):
                lines.append(f"- Where to edit: {item.get('target_section', '')}")
            if item.get("why_it_matters"):
                lines.append(f"- Why this matters: {item.get('why_it_matters', '')}")
            if item.get("recommended_rewrite"):
                lines.append(f"- Safer rewrite direction: {item.get('recommended_rewrite', '')}")
            lines.append("")

    if edit_cards:
        lines.append("## Bullet-Level Edit Cards")
        for index, card in enumerate(edit_cards, start=1):
            lines.append(
                f"### Card {index} · {str(card.get('priority', '')).title()} priority · "
                f"{str(card.get('edit_type', '')).replace('_', ' ').title()}"
            )
            if card.get("section"):
                lines.append(f"- Section: {card.get('section', '')}")
            if card.get("source"):
                lines.append(f"- Evidence source: {card.get('source', '')}")
            
            if card.get("entry_id"):
                lines.append(f"- Entry ID: {card.get('entry_id', '')}")
            if card.get("bullet_id"):
                lines.append(f"- Bullet ID: {card.get('bullet_id', '')}")
            if card.get("bullet_index", -1) is not None and int(card.get("bullet_index", -1)) >= 0:
                lines.append(f"- Bullet index: {card.get('bullet_index', -1)}")

            if card.get("jd_signal_terms"):
                lines.append(
                    f"- JD signal terms: {', '.join(card.get('jd_signal_terms', []) or [])}"
                )
            if card.get("current_evidence"):
                lines.append("- Current evidence:")
                lines.append(f"  > {card.get('current_evidence', '')}")
            if card.get("parent_bullet"):
                lines.append("- Parent bullet:")
                lines.append(f"  > {card.get('parent_bullet', '')}")
            if card.get("recommended_rewrite"):
                lines.append("- Recommended rewrite direction:")
                lines.append(f"  > {card.get('recommended_rewrite', '')}")
            if card.get("why_current_is_weak"):
                lines.append(f"- Why current wording is weak: {card.get('why_current_is_weak', '')}")
            if card.get("why_rewrite_is_better"):
                lines.append(f"- Why this rewrite is better: {card.get('why_rewrite_is_better', '')}")
            if card.get("claim_safety"):
                lines.append(f"- Claim safety: {card.get('claim_safety', '')}")
            if card.get("placement_guidance"):
                lines.append(f"- Placement guidance: {card.get('placement_guidance', '')}")
            lines.append("")

    bullet_diagnoses = payload.get("bullet_diagnoses", []) or []
    if bullet_diagnoses:
        lines.append("## Bullet Diagnoses")
        for index, row in enumerate(bullet_diagnoses, start=1):
            lines.append(
                f"### Diagnosis {index} · {str(row.get('diagnosis_action', '')).replace('_', ' ').title()} · "
                f"{str(row.get('priority', '')).title()} priority"
            )
            if row.get("section"):
                lines.append(f"- Section: {row.get('section', '')}")
            if row.get("source"):
                lines.append(f"- Source: {row.get('source', '')}")
            if row.get("entry_id"):
                lines.append(f"- Entry ID: {row.get('entry_id', '')}")
            if row.get("bullet_id"):
                lines.append(f"- Bullet ID: {row.get('bullet_id', '')}")
            if row.get("bullet_index", -1) is not None and int(row.get("bullet_index", -1)) >= 0:
                lines.append(f"- Bullet index: {row.get('bullet_index', -1)}")
            if row.get("jd_signal_terms"):
                lines.append(f"- JD signals: {', '.join(row.get('jd_signal_terms', []) or [])}")
            if row.get("likely_impacted_dimensions"):
                lines.append(
                    f"- Likely impacted dimensions: {', '.join(row.get('likely_impacted_dimensions', []) or [])}"
                )
            if row.get("original_text"):
                lines.append(f"- Original text: {row.get('original_text', '')}")
            if row.get("why"):
                lines.append(f"- Why: {row.get('why', '')}")
            if row.get("recommended_rewrite"):
                lines.append(f"- Recommended rewrite: {row.get('recommended_rewrite', '')}")
            if row.get("claim_safety"):
                lines.append(f"- Claim safety: {row.get('claim_safety', '')}")
            lines.append("")

    replacement_candidates = payload.get("replacement_candidates", []) or []
    if replacement_candidates:
        lines.append("## Replacement Candidates")
        for index, row in enumerate(replacement_candidates, start=1):
            lines.append(
                f"### Candidate {index} · {str(row.get('operation_type', '')).replace('_', ' ').title()} · "
                f"{str(row.get('confidence', '')).title()} confidence"
            )
            if row.get("section"):
                lines.append(f"- Section: {row.get('section', '')}")
            if row.get("source"):
                lines.append(f"- Source: {row.get('source', '')}")
            if row.get("source_entry_id"):
                lines.append(f"- Entry ID: {row.get('source_entry_id', '')}")
            if row.get("source_bullet_id"):
                lines.append(f"- Bullet ID: {row.get('source_bullet_id', '')}")
            if row.get("source_group_id"):
                lines.append(f"- Source group ID: {row.get('source_group_id', '')}")
            if row.get("source_group_type"):
                lines.append(f"- Source group type: {row.get('source_group_type', '')}")
            if row.get("conflict_group_id"):
                lines.append(f"- Conflict group ID: {row.get('conflict_group_id', '')}")
            if row.get("conflicts_with"):
                lines.append(f"- Conflicts with: {', '.join(row.get('conflicts_with', []) or [])}")
            if row.get("supported_jd_signals"):
                lines.append(f"- Supported JD signals: {', '.join(row.get('supported_jd_signals', []) or [])}")
            if row.get("likely_impacted_dimensions"):
                lines.append(
                    f"- Likely impacted dimensions: {', '.join(row.get('likely_impacted_dimensions', []) or [])}"
                )
            if row.get("original_text"):
                lines.append(f"- Original text: {row.get('original_text', '')}")
            if row.get("proposal_status"):
                lines.append(f"- Proposal status: {row.get('proposal_status', '')}")
            if row.get("proposal_type"):
                lines.append(f"- Proposal type: {row.get('proposal_type', '')}")
            if row.get("patch_generation_method"):
                lines.append(f"- Patch generation method: {row.get('patch_generation_method', '')}")
            if row.get("rewrite_instruction"):
                lines.append(f"- Rewrite instruction: {row.get('rewrite_instruction', '')}")
            if row.get("patch_text"):
                lines.append(f"- Patch text: {row.get('patch_text', '')}")
            if row.get("original_final_score") is not None:
                lines.append(f"- Original final score: {row.get('original_final_score')}")
            if row.get("projected_final_score") is not None:
                lines.append(f"- Projected final score: {row.get('projected_final_score')}")
            if row.get("projected_overall_delta") is not None:
                lines.append(f"- Projected overall delta: {row.get('projected_overall_delta')}")
            if row.get("projected_dimension_deltas"):
                formatted = ", ".join(
                    f"{name}={value}"
                    for name, value in (row.get("projected_dimension_deltas", {}) or {}).items()
                )
                lines.append(f"- Projected dimension deltas: {formatted}")
            if row.get("counterfactual_status"):
                lines.append(f"- Counterfactual status: {row.get('counterfactual_status', '')}")
            if row.get("counterfactual_note"):
                lines.append(f"- Counterfactual note: {row.get('counterfactual_note', '')}")
            if row.get("why_this_improves_match"):
                lines.append(f"- Why this improves match: {row.get('why_this_improves_match', '')}")
            if row.get("adjacent_risk_signals"):
                lines.append(
                    f"- Adjacent-risk signals: {', '.join(row.get('adjacent_risk_signals', []) or [])}"
                )
            if row.get("unsupported_risk_signals"):
                lines.append(
                    f"- Unsupported-risk signals: {', '.join(row.get('unsupported_risk_signals', []) or [])}"
                )
            if row.get("claim_safety"):
                lines.append(f"- Claim safety: {row.get('claim_safety', '')}")
            if row.get("placement_guidance"):
                lines.append(f"- Placement guidance: {row.get('placement_guidance', '')}")
            lines.append("")

    empty_state_reason = payload.get("empty_state_reason", {}) or {}

    if not edit_cards and empty_state_reason:
        lines.append("## Why There Are No Edit Cards")

        if empty_state_reason.get("title"):
            lines.append(f"- {empty_state_reason.get('title', '')}")

        if empty_state_reason.get("summary"):
            lines.append(f"- {empty_state_reason.get('summary', '')}")

        main_blockers = empty_state_reason.get("main_blockers", []) or []
        if main_blockers:
            lines.append("### Main Blockers")
            for item in main_blockers:
                lines.append(f"- {item}")
            lines.append("")

        still_useful = empty_state_reason.get("still_useful", []) or []
        if still_useful:
            lines.append("### Still Useful")
            for item in still_useful:
                lines.append(f"- {item}")
            lines.append("")
        
        missing_jd_focus = empty_state_reason.get("missing_jd_focus", []) or []
        if missing_jd_focus:
            lines.append("### Missing JD Focus")
            for item in missing_jd_focus:
                lines.append(f"- {item}")
            lines.append("")

        if empty_state_reason.get("resume_limitation_summary"):
            lines.append("### Selected Resume Limitation")
            lines.append(f"- {empty_state_reason.get('resume_limitation_summary', '')}")
            lines.append("")

        keep_visible_now = empty_state_reason.get("keep_visible_now", []) or []
        if keep_visible_now:
            lines.append("### Keep Visible Now")
            for item in keep_visible_now:
                label = str(item.get("label", "") or "").strip()
                evidence = str(item.get("evidence", "") or "").strip()
                reason = str(item.get("reason", "") or "").strip()
                overlaps = item.get("overlaps", []) or []

                if label:
                    lines.append(f"- **{label}**")
                else:
                    lines.append("- **Existing anchor**")

                if overlaps:
                    lines.append(f"  - Overlap: {', '.join(overlaps)}")
                if evidence:
                    lines.append(f"  - Evidence: {evidence}")
                if reason:
                    lines.append(f"  - Why keep it visible: {reason}")
            lines.append("")

        if empty_state_reason.get("next_step"):
            lines.append(f"### Recommended Next Step")
            lines.append(f"- {empty_state_reason.get('next_step', '')}")
            lines.append("")

    if keep_as_is:
        lines.append("## Keep / Do Not Over-Edit")
        for item in keep_as_is:
            overlaps = item.get("overlaps", []) or []
            if item.get("section") or item.get("source"):
                lines.append(
                    f"- **[{item.get('section', '')}] {item.get('source', '')}**"
                )
            if overlaps:
                lines.append(f"  - Strong overlap: {', '.join(overlaps)}")
            if item.get("evidence"):
                lines.append(f"  - Evidence: {item.get('evidence', '')}")
            if item.get("reason"):
                lines.append(f"  - Why keep it: {item.get('reason', '')}")
        lines.append("")

    lines.append("## Claim Safety Notes")
    safe_to_strengthen = claim_safety_notes.get("safe_to_strengthen", []) or []
    frame_carefully = claim_safety_notes.get("frame_carefully", []) or []
    do_not_add = claim_safety_notes.get("do_not_add", []) or []

    if safe_to_strengthen:
        lines.append("### Safe to Strengthen")
        for item in safe_to_strengthen:
            lines.append(f"- {item}")
        lines.append("")

    if frame_carefully:
        lines.append("### Frame Carefully")
        for item in frame_carefully:
            lines.append(f"- {item}")
        lines.append("")

    if do_not_add:
        lines.append("### Do Not Add Unless Truly Supported")
        for item in do_not_add:
            lines.append(f"- {item}")
        lines.append("")

    if claim_safety_notes.get("guardrail"):
        lines.append(f"**Guardrail:** {claim_safety_notes.get('guardrail', '')}")
        lines.append("")

    if material_gaps:
        lines.append("## Material Gaps")
        for item in material_gaps:
            lines.append(
                f"- **{item.get('label', '')}** | type={item.get('gap_type', '')} | severity={item.get('severity', '')}"
            )
            if item.get("guidance"):
                lines.append(f"  - Guidance: {item.get('guidance', '')}")
        lines.append("")

    lines.append("## Audit Appendix")
    lines.append("### Positioning Summary")
    lines.append(payload.get("recruiter_summary", ""))
    lines.append("")

    lines.append("### Tailoring Actions")
    for item in payload.get("tailoring_actions", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("### Preferred Rewrite Directions")
    lines.append(f"- Source: {payload.get('preferred_rewrite_source', 'deterministic')}")
    for item in payload.get("preferred_rewrite_directions", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("### Planner Seed Rewrite Directions")
    for item in payload.get("planner_seed_rewrite_directions", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("### Tailoring Plan Snapshot")
    lines.append(f"- Narrative angle: {tailoring_plan.get('narrative_angle', '')}")
    lines.append(f"- Compatibility mode: {tailoring_plan.get('compatibility_mode', False)}")
    lines.append(f"- Compatibility reason: {tailoring_plan.get('compatibility_reason', '')}")
    lines.append(f"- Direct facets: {tailoring_plan.get('direct_facets', [])}")
    lines.append(f"- Adjacent facets: {tailoring_plan.get('adjacent_facets', [])}")
    lines.append(f"- True gap facets: {tailoring_plan.get('true_gap_facets', [])}")
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

    lines.append("### Evidence-Backed Rewrite Ideas")
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

    lines.append("### Bullet Reuse Candidates")
    for row in payload.get("bullet_reuse_candidates", []):
        lines.append(
            f"- **[{row.get('section', '')}] {row.get('source', '')}** | "
            f"type={row.get('evidence_type', '')} | overlaps={row.get('overlaps', [])}"
        )
        if row.get("entry_id"):
            lines.append(f"  - Entry ID: {row.get('entry_id', '')}")
        if row.get("bullet_id"):
            lines.append(f"  - Bullet ID: {row.get('bullet_id', '')}")
        if row.get("bullet_index", -1) is not None and int(row.get("bullet_index", -1)) >= 0:
            lines.append(f"  - Bullet index: {row.get('bullet_index', -1)}")
        lines.append(f"  - Evidence unit: {row.get('bullet', '')}")
        if row.get("parent_bullet"):
            lines.append(f"  - Parent bullet: {row.get('parent_bullet', '')}")
        lines.append(f"  - Reuse note: {row.get('reuse_note', '')}")
    lines.append("")

    return "\n".join(lines)
