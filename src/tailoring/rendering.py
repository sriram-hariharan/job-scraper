from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
import hashlib
import json

from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.document_store import load_resume_documents_by_name
from src.resume.evidence_builder import (
    build_resume_evidence,
    build_counterfactual_resume_evidence,
    build_counterfactual_resume_evidence_for_patches,
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
    expandable_aliases_for_supported_term,
    family_for_term,
    families_for_terms,
    prioritized_family_terms_from_text,
    supported_signal_match_in_text,
)

from src.config.consts import (
    ACTION_VERB_HINTS, 
    _CLAUSE_SPLIT_ACTION_VERBS,
    _STRUCTURAL_CLAUSE_FAMILY_PRIORITY,
    _PROMOTABLE_SIGNAL_FAMILY_LABELS,
    _PROMOTABLE_SIGNAL_FAMILY_REQUIRED_DIMENSIONS,
    _REWRITE_CLAIM_SAFETY_DISPLAY_LABELS,
    _REWRITE_GROUP_DISPLAY_LABELS,
    _REWRITE_OUTCOME_DISPLAY_LABELS,
    _REWRITE_REVIEW_STATE_DISPLAY_LABELS
)

_ACTION_VERB_HINTS_LOWER = {
    str(item).strip().lower()
    for item in ACTION_VERB_HINTS
    if str(item).strip()
}

def _rewrite_lead_token(text: str) -> str:
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]+", str(text or ""))
    return tokens[0].lower() if tokens else ""

def _using_phrase_fronting_would_break_bullet_tone(original_text: str) -> bool:
    lead = _rewrite_lead_token(original_text)
    if not lead:
        return False

    if lead in {"using", "with", "via", "by", "through"}:
        return False

    return lead in _ACTION_VERB_HINTS_LOWER or lead.endswith("ed")

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

def _looks_like_resume_header_metadata(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return False

    normalized = re.sub(r"\s+", " ", raw).strip()

    # Strong signals of entry/header metadata rather than a bullet clause.
    if "|" in normalized:
        return True

    if re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b", normalized, flags=re.IGNORECASE):
        if re.search(r"\b20\d{2}\b", normalized):
            return True

    if re.search(r"\b(?:usa|united states|remote)\b", normalized, flags=re.IGNORECASE):
        return True

    # Header-like noun stacks with no clear action verb.
    if not re.search(r"\b(?:built|automated|developed|deployed|implemented|performed|designed|created|improved|reduced|increased|identified|partnered|launched|evaluated|trained|optimized|analyzed)\b", normalized, flags=re.IGNORECASE):
        comma_chunks = [part.strip() for part in normalized.split(",") if part.strip()]
        if len(comma_chunks) >= 2 and len(normalized.split()) <= 14:
            return True

    return False


def _clause_extract_candidate_is_safe(clause_text: str, original_text: str) -> bool:
    candidate = str(clause_text or "").strip()
    original = str(original_text or "").strip()

    if not candidate or not original:
        return False

    if _looks_like_resume_header_metadata(candidate):
        return False

    # Reject tiny fragments that are likely labels/headers rather than real clauses.
    if len(candidate.split()) < 5:
        return False

    return True

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
    reuse_note = str(row.get("reuse_note", "") or "").strip()
    if reuse_note:
        return reuse_note

    overlaps = [
        str(item or "").strip()
        for item in (row.get("overlaps", []) or [])
        if str(item or "").strip()
    ]

    if overlaps:
        return (
            f"Keep this bullet visible and, if needed, tighten the wording so "
            f"{', '.join(_truncate_list(overlaps, 4))} shows up earlier and more clearly."
        )

    return "Keep this bullet visible and tighten wording only if it improves JD alignment without changing the claim."


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

def _direct_reuse_jd_signal_terms(
    row: Dict[str, Any],
    canonical_supported_signal: str,
) -> List[str]:
    evidence_type = str(row.get("evidence_type", "") or "").strip()

    if evidence_type != "direct_overlap":
        return []

    if canonical_supported_signal:
        return [canonical_supported_signal]

    return [
        str(item).strip()
        for item in (row.get("overlaps", []) or [])
        if str(item).strip()
    ]


def _context_reuse_signal_terms(
    row: Dict[str, Any],
    canonical_supported_signal: str,
) -> List[str]:
    evidence_type = str(row.get("evidence_type", "") or "").strip()

    if evidence_type == "direct_overlap":
        return []

    context_terms = [
        str(item).strip()
        for item in (row.get("context_terms", []) or [])
        if str(item).strip()
    ]
    if context_terms:
        return context_terms

    if canonical_supported_signal:
        return [canonical_supported_signal]

    return []


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

    jd_signal_terms = _direct_reuse_jd_signal_terms(
        row,
        canonical_supported_signal,
    )
    context_signal_terms = _context_reuse_signal_terms(
        row,
        canonical_supported_signal,
    )

    evidence_type = _resolved_edit_card_evidence_type(
        row,
        jd_signal_terms,
        evidence,
    )
    claim_safety = (
        "safe_strengthen"
        if evidence_type == "direct_overlap" and jd_signal_terms
        else _fallback_claim_safety_from_reuse(row)
    )

    return {
        "card_id": f"edit_card_reuse_{index}",
        "evidence_type": evidence_type,
        "priority": _fallback_priority_from_reuse(index - 1, row),
        "edit_type": (
            "rewrite"
            if evidence_type == "direct_overlap" and jd_signal_terms
            else _fallback_edit_type_from_reuse(row)
        ),
        "section": row.get("section", ""),
        "source": row.get("source", ""),
        "jd_signal_terms": jd_signal_terms,
        "context_signal_terms": context_signal_terms,
        "current_evidence": evidence,
        "parent_bullet": row.get("parent_bullet", ""),
        "recommended_rewrite": (
            _fallback_recommended_rewrite_from_reuse(
                preferred_rewrite_directions,
                row,
            )
            if evidence_type == "direct_overlap" and jd_signal_terms
            else _fallback_recommended_rewrite_from_reuse(
                preferred_rewrite_directions,
                row,
            )
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
        "outcome_label": (
            "directional_only"
            if evidence_type == "direct_overlap" and jd_signal_terms
            else ""
        ),
        "outcome_reason": (
            "direct_overlap_reuse_directional_anchor"
            if evidence_type == "direct_overlap" and jd_signal_terms
            else ""
        ),
        "final_diagnosis_action": (
            "rewrite"
            if evidence_type == "direct_overlap" and jd_signal_terms
            else ""
        ),
        "final_diagnosis_reason_type": (
            "directional_rewrite"
            if evidence_type == "direct_overlap" and jd_signal_terms
            else ""
        ),
    }


def _backfill_edit_cards_from_bullet_reuse(
    payload: Dict[str, Any],
    preferred_rewrite_directions: List[str],
    existing_cards: List[Dict[str, Any]],
    seen_family_keys: set,
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

    local_seen_family_keys = set(seen_family_keys)
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

        family_key = _edit_card_family_dedup_key(card)
        if family_key and family_key in local_seen_family_keys:
            continue

        cards.append(card)
        seen_keys.add(key)
        if family_key:
            local_seen_family_keys.add(family_key)

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

def _primary_promotable_family_from_terms(terms: List[str]) -> str:
    normalized_terms = [
        str(term or "").strip()
        for term in (terms or [])
        if str(term or "").strip()
    ]
    if not normalized_terms:
        return ""

    for term in normalized_terms:
        family = str(family_for_term(term) or "").strip()
        if family in _PROMOTABLE_REUSE_FAMILY_PRIORITY:
            return family

    for family in families_for_terms(normalized_terms):
        family = str(family or "").strip()
        if family in _PROMOTABLE_REUSE_FAMILY_PRIORITY:
            return family

    return ""


def _edit_card_family_dedup_key(card: Dict[str, Any]) -> Tuple[str, str]:
    evidence_type = str(card.get("evidence_type", "") or "").strip()
    edit_type = str(card.get("edit_type", "") or "").strip()
    section = str(card.get("section", "") or "").strip().lower()

    if evidence_type != "direct_overlap":
        return ()

    if edit_type != "rewrite":
        return ()

    if section not in {"experience", "project"}:
        return ()

    family = _primary_promotable_family_from_terms(
        list(card.get("jd_signal_terms", []) or [])
    )
    if not family:
        return ()

    return (section, family)


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

def _replacement_candidate_lookup_keys(item: Dict[str, Any]) -> List[tuple]:
    source_bullet_id = str(
        item.get("source_bullet_id", "") or item.get("bullet_id", "") or ""
    ).strip()

    source_entry_id = str(
        item.get("source_entry_id", "") or item.get("entry_id", "") or ""
    ).strip()
    section = str(item.get("section", "") or "").strip()
    source = str(item.get("source", "") or "").strip()

    supported_terms = tuple(sorted({
        _diagnosis_normalize_term(str(term))
        for term in (
            list(item.get("supported_jd_signals", []) or [])
            + list(item.get("supported_terms", []) or [])
            + list(item.get("jd_signal_terms", []) or [])
        )
        if _diagnosis_normalize_term(str(term))
    }))

    current_evidence = (
        str(item.get("current_evidence", "") or "").strip()
        or str(item.get("bullet_excerpt", "") or "").strip()
        or str(item.get("focused_clause_text", "") or "").strip()
        or str(item.get("structural_clause_text", "") or "").strip()
        or str(item.get("parent_bullet", "") or "").strip()
        or str(item.get("original_text", "") or "").strip()
    )

    keys: List[tuple] = []

    if source_bullet_id:
        keys.append(("bullet", source_bullet_id))

    if source_entry_id and supported_terms:
        keys.append(("entry_terms", source_entry_id, section, source, supported_terms))

    if source_entry_id and current_evidence:
        keys.append(("entry_evidence", source_entry_id, current_evidence))

    if current_evidence:
        keys.append(("fallback", section, source, current_evidence))

    seen = set()
    unique_keys: List[tuple] = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        unique_keys.append(key)

    return unique_keys


def _replacement_candidate_lookup_key(item: Dict[str, Any]) -> tuple:
    keys = _replacement_candidate_lookup_keys(item)
    return keys[0] if keys else ("fallback", "", "", "")


def _patch_ready_rewrite_lookup(
    payload: Dict[str, Any],
) -> Dict[tuple, Dict[str, Any]]:
    lookup: Dict[tuple, Dict[str, Any]] = {}

    for candidate in (payload.get("replacement_candidates", []) or []):
        if str(candidate.get("operation_type", "") or "").strip() != "rewrite":
            continue
        if str(candidate.get("proposal_status", "") or "").strip() != "patch_ready":
            continue

        patch_text = str(candidate.get("patch_text", "") or "").strip()
        if not patch_text:
            continue

        def _rank(row: Dict[str, Any]) -> tuple:
            status = str(row.get("materiality_validation_status", "") or "").strip()
            return (
                1 if status == "material_candidate" else 0,
                1 if status == "export_safe_no_score_lift" else 0,
                len(str(row.get("patch_text", "") or "").strip()),
            )

        for key in _replacement_candidate_lookup_keys(candidate):
            existing = lookup.get(key)
            if existing is None or _rank(candidate) > _rank(existing):
                lookup[key] = candidate

    return lookup

def _directional_rewrite_lookup(
    payload: Dict[str, Any],
) -> Dict[tuple, Dict[str, Any]]:
    lookup: Dict[tuple, Dict[str, Any]] = {}

    for candidate in (payload.get("replacement_candidates", []) or []):
        if str(candidate.get("operation_type", "") or "").strip() != "rewrite":
            continue
        if str(candidate.get("proposal_status", "") or "").strip() != "direction_only":
            continue

        def _rank(row: Dict[str, Any]) -> tuple:
            reason = str(row.get("direction_only_reason", "") or "").strip()
            return (
                1 if reason == "multi_signal_already_explicit_reorder_preferred" else 0,
                1 if reason == "single_signal_already_explicit_reorder_preferred" else 0,
                1 if reason == "supported_terms_too_generic_to_front" else 0,
                len(str(row.get("rewrite_instruction", "") or "").strip()),
            )

        for key in _replacement_candidate_lookup_keys(candidate):
            existing = lookup.get(key)
            if existing is None or _rank(candidate) > _rank(existing):
                lookup[key] = candidate

    return lookup

def _rewrite_outcome_label_from_candidate(candidate: Dict[str, Any]) -> str:
    proposal_status = str(candidate.get("proposal_status", "") or "").strip()
    materiality_status = str(candidate.get("materiality_validation_status", "") or "").strip()
    direction_only_reason = str(candidate.get("direction_only_reason", "") or "").strip()

    if proposal_status == "patch_ready":
        if materiality_status == "material_candidate":
            return "material_candidate"
        if materiality_status == "export_safe_no_score_lift":
            return "export_safe_no_score_lift"
        return "patch_ready"

    if proposal_status == "direction_only":
        if materiality_status == "cosmetic_patch_not_exportable" or direction_only_reason == "cosmetic_patch_not_exportable":
            return "cosmetic_only"
        return "directional_only"

    return proposal_status or "unknown"

def _rendered_candidate_current_evidence(replacement_candidate: Dict[str, Any]) -> str:
    parent_bullet = str(replacement_candidate.get("parent_bullet", "") or "").strip()
    original_text = str(replacement_candidate.get("original_text", "") or "").strip()
    current_evidence = str(replacement_candidate.get("current_evidence", "") or "").strip()
    focused_clause_text = str(replacement_candidate.get("focused_clause_text", "") or "").strip()
    structural_clause_text = str(replacement_candidate.get("structural_clause_text", "") or "").strip()

    full_bullet = max(
        [value for value in [parent_bullet, original_text, current_evidence] if value],
        key=len,
        default="",
    )
    if full_bullet:
        return full_bullet

    return focused_clause_text or structural_clause_text

def _display_candidate_current_bullet(candidate: Dict[str, Any]) -> str:
    parent_bullet = str(candidate.get("parent_bullet", "") or "").strip()
    original_text = str(candidate.get("original_text", "") or "").strip()
    current_evidence = _rendered_candidate_current_evidence(candidate)

    values = [value for value in [parent_bullet, original_text, current_evidence] if value]
    if not values:
        return ""

    return max(values, key=len)

def _looks_like_directional_instruction_text(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return False

    normalized = re.sub(r"\s+", " ", raw).strip().lower()

    instruction_prefixes = (
        "lead with ",
        "support with ",
        "keep this bullet",
        "move this bullet",
        "do not rewrite ",
        "review this bullet",
        "treat this as ",
        "if space is tight, ",
        "if you want a tighter one-bullet story, ",
        "replace the original bullet with ",
        "only merge if ",
        "keep gap explicit ",
    )

    if normalized.startswith(instruction_prefixes):
        return True

    if normalized.endswith(" truthfully.") and (
        normalized.startswith("lead with ")
        or normalized.startswith("support with ")
    ):
        return True

    return False

def _rewrite_card_fields_from_patch_ready_candidate(
    replacement_candidate: Dict[str, Any],
    supported_terms: List[str],
) -> Dict[str, Any]:
    patch_text = str(replacement_candidate.get("patch_text", "") or "").strip()
    status = str(replacement_candidate.get("materiality_validation_status", "") or "").strip()
    patch_method = str(replacement_candidate.get("patch_generation_method", "") or "").strip()

    current_evidence = _display_candidate_current_bullet(replacement_candidate)
    parent_bullet = str(
        replacement_candidate.get("parent_bullet", "") or current_evidence
    ).strip()

    if _looks_like_directional_instruction_text(patch_text):
        directional_text = (
            patch_text
            or str(replacement_candidate.get("rewrite_instruction", "") or "").strip()
        )

        return {
            "edit_type": "keep_visible",
            "claim_safety": "keep_visible",
            "recommended_rewrite": "",
            "why_current_is_weak": (
                f"The evidence is relevant, but {', '.join(_truncate_list(supported_terms, 4))} is not yet leading the bullet clearly."
                if supported_terms
                else "The evidence is relevant, but the JD-aligned language is not yet leading the bullet clearly."
            ),
            "why_rewrite_is_better": (
                "This surfaced text is directional guidance, not a literal replacement bullet, so it should stay in review instead of the rewrite lane."
            ),
            "why_it_matters": directional_text,
            "patch_generation_method": patch_method,
            "replacement_candidate_id": str(replacement_candidate.get("candidate_id", "") or "").strip(),
            "replacement_materiality_validation_status": status,
            "replacement_materiality_validation_note": str(
                replacement_candidate.get("materiality_validation_note", "") or ""
            ).strip(),
            "original_text": current_evidence,
            "current_evidence": current_evidence,
            "parent_bullet": parent_bullet,
            "supported_jd_signals": list(supported_terms or []),
            "outcome_label": "directional_only",
            "outcome_reason": "instructional_patch_text_not_literal_bullet",
            "placement_guidance": (
                str(replacement_candidate.get("placement_guidance", "") or "").strip()
                or "Treat this as review guidance only unless a literal replacement bullet is generated."
            ),
        }

    if status == "material_candidate":
        why_it_matters = (
            "This deterministic rewrite survived pre-validation as a scorer-material patch candidate."
        )
    elif status == "export_safe_no_score_lift":
        lead = ", ".join(_truncate_list(supported_terms, 4)) if supported_terms else "the JD signal"
        why_it_matters = (
            f"This deterministic rewrite safely surfaces {lead} earlier and is export-safe, even though the frozen scorer shows no projected score lift."
        )
    else:
        why_it_matters = (
            "This deterministic rewrite survived validation as a grounded patch-ready candidate."
        )

    return {
        "edit_type": "rewrite",
        "claim_safety": "safe_strengthen",
        "recommended_rewrite": patch_text,
        "why_current_is_weak": (
            f"The evidence is relevant, but {', '.join(_truncate_list(supported_terms, 4))} "
            "is not yet leading the bullet clearly."
            if supported_terms
            else "The evidence is relevant, but the JD-aligned language is not yet leading the bullet clearly."
        ),
        "why_rewrite_is_better": (
            "It replaces generic direction-only guidance with a grounded deterministic bullet patch."
        ),
        "why_it_matters": why_it_matters,
        "patch_generation_method": patch_method,
        "replacement_candidate_id": str(replacement_candidate.get("candidate_id", "") or "").strip(),
        "replacement_materiality_validation_status": status,
        "replacement_materiality_validation_note": str(
            replacement_candidate.get("materiality_validation_note", "") or ""
        ).strip(),
        "original_text": current_evidence,
        "current_evidence": current_evidence,
        "parent_bullet": parent_bullet,
        "supported_jd_signals": list(supported_terms or []),
        "outcome_label": _rewrite_outcome_label_from_candidate(replacement_candidate),
        "outcome_reason": str(
            replacement_candidate.get("materiality_validation_note", "") or ""
        ).strip(),
    }


def _rewrite_card_fields_from_directional_candidate(
    replacement_candidate: Dict[str, Any],
    supported_terms: List[str],
) -> Dict[str, Any]:
    reason = str(replacement_candidate.get("direction_only_reason", "") or "").strip()
    rewrite_instruction = str(replacement_candidate.get("rewrite_instruction", "") or "").strip()

    current_evidence = _display_candidate_current_bullet(replacement_candidate)
    parent_bullet = str(
        replacement_candidate.get("parent_bullet", "") or current_evidence
    ).strip()

    common_fields = {
        "direction_only_reason": reason,
        "replacement_candidate_id": str(replacement_candidate.get("candidate_id", "") or "").strip(),
        "original_text": current_evidence,
        "current_evidence": current_evidence,
        "parent_bullet": parent_bullet,
        "supported_jd_signals": list(supported_terms or []),
        "outcome_label": _rewrite_outcome_label_from_candidate(replacement_candidate),
        "outcome_reason": str(
            replacement_candidate.get("materiality_validation_note", "") or ""
        ).strip()
        or str(replacement_candidate.get("direction_only_reason", "") or "").strip(),
    }

    lead = ", ".join(_truncate_list(supported_terms, 4)) if supported_terms else "the supported JD signals"

    if reason == "multi_signal_already_explicit_reorder_preferred":
        return {
            "edit_type": "keep_visible",
            "claim_safety": "keep_visible",
            "recommended_rewrite": "",
            "why_current_is_weak": (
                f"The bullet already surfaces {lead} early enough, so the issue is visibility/order, not wording."
            ),
            "why_rewrite_is_better": (
                "A textual rewrite is unnecessary here. Moving this bullet earlier is the cleaner ATS and recruiter-facing action."
            ),
            "why_it_matters": (
                f"This bullet already has the right signal set ({lead}) in a strong early position; keep it highly visible instead of rewriting it."
            ),
            "placement_guidance": (
                "Move this bullet earlier within the section if stronger ATS visibility is needed."
            ),
            **common_fields,
        }

    if reason == "single_signal_already_explicit_reorder_preferred":
        return {
            "edit_type": "keep_visible",
            "claim_safety": "keep_visible",
            "recommended_rewrite": "",
            "why_current_is_weak": (
                f"The bullet already surfaces {lead} early enough, so the issue is visibility/order, not missing wording."
            ),
            "why_rewrite_is_better": (
                "A textual rewrite is unnecessary here. Keeping this bullet visible or moving it earlier is cleaner than forcing a one-signal fronting edit."
            ),
            "why_it_matters": (
                f"This bullet already proves {lead} clearly enough in an early position; treat it as an anchor instead of a rewrite target."
            ),
            "placement_guidance": (
                "Keep this bullet visible and move it earlier within the section only if stronger ATS visibility is needed."
            ),
            **common_fields,
        }

    if reason == "supported_terms_too_generic_to_front":
        return {
            "edit_type": "support",
            "claim_safety": "adjacent_only",
            "recommended_rewrite": "",
            "why_current_is_weak": (
                "The matched supported term is too generic to front safely as a standalone rewrite target."
            ),
            "why_rewrite_is_better": (
                "The safer move is to keep this bullet as secondary support rather than force a direct rewrite around a generic term."
            ),
            "why_it_matters": (
                "This helps preserve truthfulness and avoids ATS-looking but weak rewrites."
            ),
            "placement_guidance": (
                "Keep this bullet as supporting context only unless a stronger direct signal is available."
            ),
            **common_fields,
        }

    if reason == "rewrite_instruction_pathological":
        return {
            "edit_type": "suppress_rewrite",
            "claim_safety": "keep_visible",
            "recommended_rewrite": "",
            "why_current_is_weak": (
                "The current rewrite instruction is malformed, overlong, or too close to the original bullet to trust as a grounded operator action."
            ),
            "why_rewrite_is_better": (
                "The safer move is to suppress the rewrite itself and keep the bullet unchanged until a grounded deterministic patch exists."
            ),
            "why_it_matters": (
                "This prevents malformed rewrite guidance from being surfaced as if it were a legitimate text edit."
            ),
            "placement_guidance": (
                "Do not apply the current rewrite instruction. Keep the bullet visible as-is unless a grounded deterministic patch is generated later."
            ),
            **common_fields,
        }

    if reason == "scorer_neutral_no_evidence_change":
        return {
            "edit_type": "keep_visible",
            "claim_safety": "keep_visible",
            "recommended_rewrite": "",
            "why_current_is_weak": (
                "The proposed rewrite is grounded, but it does not change scorer-visible evidence in the frozen validation pass."
            ),
            "why_rewrite_is_better": (
                "This is optional phrasing polish only, not a materially stronger evidence claim."
            ),
            "why_it_matters": (
                "Keep the bullet visible as-is unless you specifically want minor wording cleanup that stays literally true."
            ),
            "placement_guidance": (
                "Do not treat this as a required patch. Keep the current bullet unless you want cosmetic phrasing cleanup only."
            ),
            **common_fields,
        }

    if reason == "materiality_prevalidation_failed":
        return {
            "edit_type": "suppress_rewrite",
            "claim_safety": "keep_visible",
            "recommended_rewrite": "",
            "why_current_is_weak": (
                "This rewrite candidate could not be pre-validated as a safe material change."
            ),
            "why_rewrite_is_better": (
                "Until deterministic counterfactual validation succeeds, the safer move is to suppress the rewrite and keep the bullet unchanged."
            ),
            "why_it_matters": (
                "This avoids surfacing an unvalidated rewrite as if it were a trustworthy patch."
            ),
            "placement_guidance": (
                "Keep the bullet unchanged unless a later deterministic rerun validates the rewrite as material."
            ),
            **common_fields,
        }

    if reason == "cosmetic_patch_not_exportable":
        return {
            "edit_type": "keep_visible",
            "claim_safety": "keep_visible",
            "recommended_rewrite": "",
            "why_current_is_weak": (
                "This candidate only normalizes punctuation or terminology and does not materially strengthen the bullet."
            ),
            "why_rewrite_is_better": (
                "Leave the bullet as-is. Cosmetic normalization is not a strong enough reason to replace truthful existing wording."
            ),
            "why_it_matters": (
                "A replacement bullet should improve JD-facing substance, not just expand acronyms or smooth punctuation."
            ),
            "placement_guidance": (
                "Keep the bullet as-is unless a later rewrite materially improves JD alignment while preserving truth."
            ),
            **common_fields,
        }
    
    if reason == "deterministic_patch_not_available":
        directional_text = rewrite_instruction or (
            f"Lead with {lead} in this opening clause, then keep the remaining parent-bullet context only if it preserves the same story truthfully."
            if supported_terms
            else "Review this bullet manually and bring the strongest supported JD signal earlier without changing the claim."
        )

        return {
            "edit_type": "rewrite",
            "claim_safety": "safe_strengthen",
            "recommended_rewrite": directional_text,
            "why_current_is_weak": (
                f"The evidence is relevant, but {lead} is not yet leading the bullet clearly."
                if supported_terms
                else "The evidence is relevant, but the JD-aligned language is not yet leading the bullet clearly."
            ),
            "why_rewrite_is_better": (
                "No deterministic export-safe patch survived, but the evidence still supports a directional rewrite recommendation."
            ),
            "why_it_matters": directional_text,
            "placement_guidance": (
                str(replacement_candidate.get("placement_guidance", "") or "").strip()
                or "Treat this as directional-only guidance. Review manually before changing lower-priority sections."
            ),
            "final_diagnosis_action": "rewrite",
            "final_diagnosis_reason_type": "directional_rewrite",
            **common_fields,
        }
    
    if rewrite_instruction:
        return {
            "edit_type": "rewrite",
            "claim_safety": "safe_strengthen",
            "recommended_rewrite": rewrite_instruction,
            "why_current_is_weak": (
                "This candidate does not justify a grounded deterministic patch yet, but it still carries a valid directional rewrite recommendation."
            ),
            "why_rewrite_is_better": (
                "The safer action is to preserve it as directional rewrite guidance instead of collapsing it into a keep-only card."
            ),
            "why_it_matters": rewrite_instruction,
            "placement_guidance": (
                "Treat this as directional-only guidance. Do not convert it into a literal replacement bullet unless a grounded deterministic patch exists."
            ),
            "final_diagnosis_action": "rewrite",
            "final_diagnosis_reason_type": "directional_rewrite",
            **common_fields,
        }

    return {
        "edit_type": "keep_visible",
        "claim_safety": "keep_visible",
        "recommended_rewrite": "",
        "why_current_is_weak": (
            "This candidate does not justify a grounded text rewrite."
        ),
        "why_rewrite_is_better": (
            "The safer action is to keep it in the directional-only lane instead of fabricating a rewrite."
        ),
        "why_it_matters": (
            "This is a legitimate directional-only recommendation, not a text rewrite candidate."
        ),
        "placement_guidance": (
            "Keep this bullet visible only if it strengthens stronger primary anchors or ordering decisions."
        ),
        **common_fields,
    }

def _edit_card_dedupe_rank(card: Dict[str, Any]) -> tuple:
    priority = str(card.get("priority", "") or "").strip().lower()
    edit_type = str(card.get("edit_type", "") or "").strip().lower()
    claim_safety = str(card.get("claim_safety", "") or "").strip().lower()
    recommended_rewrite = str(card.get("recommended_rewrite", "") or "").strip()
    current_evidence = str(card.get("current_evidence", "") or "").strip()

    priority_rank = 3 if priority == "high" else 2 if priority == "medium" else 1 if priority == "low" else 0
    edit_type_rank = 3 if edit_type == "rewrite" else 2 if edit_type == "reinforce" else 1 if edit_type == "support" else 0
    claim_safety_rank = 2 if claim_safety == "safe_strengthen" else 1 if claim_safety == "adjacent_only" else 0

    return (
        1 if recommended_rewrite else 0,
        edit_type_rank,
        claim_safety_rank,
        priority_rank,
        len(recommended_rewrite),
        len(current_evidence),
    )


def _dedupe_edit_cards_by_candidate_id(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best_by_candidate_id: Dict[str, Dict[str, Any]] = {}
    ordered_keys: List[tuple] = []

    for index, card in enumerate(cards):
        candidate_id = str(card.get("replacement_candidate_id", "") or "").strip()

        if not candidate_id:
            ordered_keys.append(("free", index))
            best_by_candidate_id[f"__free__{index}"] = card
            continue

        key = ("candidate", candidate_id)
        existing = best_by_candidate_id.get(candidate_id)

        if existing is None:
            best_by_candidate_id[candidate_id] = card
            ordered_keys.append(key)
            continue

        if _edit_card_dedupe_rank(card) > _edit_card_dedupe_rank(existing):
            best_by_candidate_id[candidate_id] = card

    deduped: List[Dict[str, Any]] = []
    for key_type, key_value in ordered_keys:
        if key_type == "free":
            free_card = best_by_candidate_id.get(f"__free__{key_value}")
            if free_card is not None:
                deduped.append(free_card)
            continue

        candidate_card = best_by_candidate_id.get(key_value)
        if candidate_card is not None:
            deduped.append(candidate_card)

    return deduped

def _is_low_value_keep_visible_card(card: Dict[str, Any]) -> bool:
    edit_type = str(card.get("edit_type", "") or "").strip()
    if edit_type != "keep_visible":
        return False

    jd_signal_terms = [
        str(item).strip()
        for item in (card.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]
    if jd_signal_terms:
        return False

    evidence_type = str(card.get("evidence_type", "") or "").strip()
    if evidence_type not in {"same_source_context", "semantic_similarity", "adjacent_context", ""}:
        return False

    why_it_matters = str(card.get("why_it_matters", "") or "").strip()

    generic_keep_visible_messages = {
        "This is one of the stronger existing bullets to tighten before editing weaker sections.",
        "This can help support the JD story, but it is not the strongest anchor.",
    }

    return not why_it_matters or why_it_matters in generic_keep_visible_messages


def _edit_card_operator_rank(card: Dict[str, Any]) -> tuple:
    priority = str(card.get("priority", "") or "").strip().lower()
    evidence_type = str(card.get("evidence_type", "") or "").strip()
    edit_type = str(card.get("edit_type", "") or "").strip()
    jd_signal_terms = [
        str(item).strip()
        for item in (card.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]

    priority_rank = 3 if priority == "high" else 2 if priority == "medium" else 1 if priority == "low" else 0
    evidence_rank = 2 if evidence_type == "direct_overlap" else 1 if evidence_type == "same_source_context" else 0

    if edit_type == "rewrite":
        edit_rank = 5
    elif edit_type == "keep_visible" and jd_signal_terms:
        edit_rank = 4
    elif edit_type == "reinforce":
        edit_rank = 3
    elif edit_type == "support":
        edit_rank = 2
    else:
        edit_rank = 1

    return (
        priority_rank,
        edit_rank,
        evidence_rank,
        len(jd_signal_terms),
        len(str(card.get("why_it_matters", "") or "").strip()),
    )


def _rank_and_suppress_edit_cards(
    cards: List[Dict[str, Any]],
    limit: int,
) -> List[Dict[str, Any]]:
    meaningful_cards = [card for card in cards if not _is_low_value_keep_visible_card(card)]
    low_value_cards = [card for card in cards if _is_low_value_keep_visible_card(card)]

    meaningful_cards = sorted(
        meaningful_cards,
        key=_edit_card_operator_rank,
        reverse=True,
    )

    if len(meaningful_cards) >= 2:
        return meaningful_cards[:limit]

    if meaningful_cards:
        return (meaningful_cards + low_value_cards[:1])[:limit]

    return cards[:limit]

def _is_actionable_edit_card(card: Dict[str, Any]) -> bool:
    edit_type = str(card.get("edit_type", "") or "").strip()
    recommended_rewrite = str(card.get("recommended_rewrite", "") or "").strip()
    outcome_label = str(card.get("outcome_label", "") or "").strip()

    if edit_type == "rewrite" and recommended_rewrite:
        return True

    if outcome_label in {
        "material_candidate",
        "export_safe_no_score_lift",
    }:
        return True

    return False

def _looks_like_fronting_direction(text: str) -> bool:
    normalized = str(text or "").strip().lower()
    return normalized.startswith(("lead with ", "support with ", "consider fronting "))

def _anchor_review_case(card: Dict[str, Any]) -> str:
    why_it_matters = str(card.get("why_it_matters", "") or "").strip()
    recommended_rewrite = str(card.get("recommended_rewrite", "") or "").strip()
    edit_type = str(card.get("edit_type", "") or "").strip()
    claim_safety = str(card.get("claim_safety", "") or "").strip()

    if _looks_like_fronting_direction(why_it_matters) or _looks_like_fronting_direction(recommended_rewrite):
        return "fronting"

    if edit_type in {"support", "reinforce"} or claim_safety == "adjacent_only":
        return "support"

    return "preserve"

def _anchor_review_case_rank(card: Dict[str, Any]) -> int:
    review_case = _anchor_review_case(card)
    if review_case == "fronting":
        return 3
    if review_case == "support":
        return 2
    return 1

def _anchor_review_label(card: Dict[str, Any]) -> str:
    review_case = _anchor_review_case(card)
    if review_case == "fronting":
        return "Consider fronting"
    if review_case == "support":
        return "Supporting context"
    return "Preserve evidence"

def _anchor_review_tone(card: Dict[str, Any]) -> str:
    review_case = _anchor_review_case(card)
    if review_case == "fronting":
        return "caution"
    if review_case == "support":
        return "neutral"
    return "muted"

def _anchor_review_note(card: Dict[str, Any]) -> str:
    why_it_matters = str(card.get("why_it_matters", "") or "").strip()
    recommended_rewrite = str(card.get("recommended_rewrite", "") or "").strip()

    if _looks_like_fronting_direction(why_it_matters):
        return why_it_matters
    if _looks_like_fronting_direction(recommended_rewrite):
        return recommended_rewrite
    return ""

def _anchor_editable_in_free_edit(card: Dict[str, Any]) -> bool:
    return _anchor_review_case(card) != "preserve"

def _annotate_anchor_card(card: Dict[str, Any]) -> Dict[str, Any]:
    annotated = dict(card)
    annotated["review_case"] = _anchor_review_case(card)
    annotated["review_case_rank"] = _anchor_review_case_rank(card)
    annotated["review_label"] = _anchor_review_label(card)
    annotated["review_tone"] = _anchor_review_tone(card)
    annotated["review_note"] = _anchor_review_note(card)
    annotated["editable_in_free_edit"] = _anchor_editable_in_free_edit(card)
    return annotated

def _anchor_card_rank(card: Dict[str, Any]) -> tuple:
    priority = str(card.get("priority", "") or "").strip().lower()
    evidence_type = str(card.get("evidence_type", "") or "").strip()
    jd_signal_terms = [
        str(item).strip()
        for item in (card.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]
    why_it_matters = str(card.get("why_it_matters", "") or "").strip()

    priority_rank = 3 if priority == "high" else 2 if priority == "medium" else 1 if priority == "low" else 0
    evidence_rank = 2 if evidence_type == "direct_overlap" else 1 if evidence_type == "same_source_context" else 0
    review_case_rank = _anchor_review_case_rank(card)

    return (
        review_case_rank,
        priority_rank,
        evidence_rank,
        len(jd_signal_terms),
        len(why_it_matters),
    )


def _dedupe_anchor_cards(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best_by_key: Dict[tuple, Dict[str, Any]] = {}
    order: List[tuple] = []

    for card in cards or []:
        key = (
            str(card.get("section", "") or "").strip().lower(),
            str(card.get("source", "") or "").strip().lower(),
            tuple(
                sorted(
                    str(item).strip().lower()
                    for item in (card.get("jd_signal_terms", []) or [])
                    if str(item).strip()
                )
            ),
            str(card.get("current_evidence", "") or "").strip().lower(),
        )

        existing = best_by_key.get(key)
        if existing is None:
            best_by_key[key] = card
            order.append(key)
            continue

        if _anchor_card_rank(card) > _anchor_card_rank(existing):
            best_by_key[key] = card

    return [best_by_key[key] for key in order if key in best_by_key]


def _split_actionable_and_anchor_cards(
    cards: List[Dict[str, Any]],
    action_limit: int = 5,
    anchor_limit: int = 5,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    actionable_cards = [
        card for card in (cards or [])
        if _is_actionable_edit_card(card)
    ]
    anchor_cards = [
        card for card in (cards or [])
        if not _is_actionable_edit_card(card)
    ]

    actionable_cards = _rank_and_suppress_edit_cards(actionable_cards, action_limit)
    anchor_cards = [
        _annotate_anchor_card(card)
        for card in sorted(
            _dedupe_anchor_cards(anchor_cards),
            key=_anchor_card_rank,
            reverse=True,
        )[:anchor_limit]
    ]

    return actionable_cards[:action_limit], anchor_cards[:anchor_limit]


def _build_edit_cards(
    payload: Dict[str, Any],
    preferred_rewrite_directions: List[str],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    seen_bullet_ids = set()
    seen_family_keys = set()

    rewrite_candidates = payload.get("rewrite_candidates", []) or []
    bullet_reuse_candidates = payload.get("bullet_reuse_candidates", []) or []
    packet_supported_terms = _packet_term_support_terms(payload)
    patch_ready_lookup = _patch_ready_rewrite_lookup(payload)
    directional_lookup = _directional_rewrite_lookup(payload)

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
        family_key = _edit_card_family_dedup_key(card)
        if family_key and family_key in seen_family_keys:
            continue

        cards.append(card)

        if bullet_id:
            seen_bullet_ids.add(bullet_id)
        if family_key:
            seen_family_keys.add(family_key)

    # Pass 1: current rewrite candidates
    for index, candidate in enumerate(rewrite_candidates[:limit], start=1):
        if len(cards) >= limit:
            break

        bullet_id = str(candidate.get("bullet_id", "") or "").strip()
        if bullet_id and bullet_id in seen_bullet_ids:
            continue

        seed_terms = [
            str(term).strip()
            for term in (candidate.get("supported_terms", []) or [])
            if str(term).strip()
        ]
        parent_bullet = str(candidate.get("parent_bullet", "") or "").strip()
        current_evidence = _display_candidate_current_bullet(candidate)
        source_text = current_evidence or parent_bullet

        signal_match = supported_signal_match_in_text(
            source_text,
            packet_supported_terms,
        )

        matched_surface_signal = str(signal_match.get("matched_term", "") or "").strip()
        canonical_supported_signal = str(signal_match.get("supported_term", "") or "").strip()

        supported_terms = _unique_preserve_order(
            ([canonical_supported_signal] if canonical_supported_signal else []) + seed_terms
        )
        evidence_type = _resolved_edit_card_evidence_type(
            candidate,
            supported_terms,
            source_text,
        )

        candidate_lookup_payload = {
            "bullet_id": candidate.get("bullet_id", ""),
            "source_bullet_id": candidate.get("source_bullet_id", ""),
            "entry_id": candidate.get("entry_id", ""),
            "source_entry_id": candidate.get("source_entry_id", ""),
            "section": candidate.get("section", ""),
            "source": candidate.get("source", ""),
            "current_evidence": current_evidence,
            "parent_bullet": parent_bullet,
            "bullet_excerpt": current_evidence,
            "original_text": source_text,
            "supported_terms": supported_terms,
            "supported_jd_signals": supported_terms,
            "jd_signal_terms": supported_terms,
        }

        candidate_lookup_keys = _replacement_candidate_lookup_keys(candidate_lookup_payload)

        patch_ready_candidate = next(
            (patch_ready_lookup.get(key) for key in candidate_lookup_keys if patch_ready_lookup.get(key) is not None),
            None,
        )

        directional_candidate = None
        if patch_ready_candidate is None:
            directional_candidate = next(
                (directional_lookup.get(key) for key in candidate_lookup_keys if directional_lookup.get(key) is not None),
                None,
            )

        recommended_rewrite = _recommended_rewrite_text(
            preferred_rewrite_directions,
            candidate,
            supported_terms,
        )
        edit_type = _card_edit_type(evidence_type)
        claim_safety = _card_claim_safety(evidence_type)
        why_current_is_weak = _why_current_is_weak(candidate, supported_terms)
        why_rewrite_is_better = _why_rewrite_is_better(candidate, supported_terms)
        why_it_matters = _why_it_matters(candidate, supported_terms)

        card = {
            "card_id": f"edit_card_{index}",
            "evidence_type": evidence_type,
            "priority": _card_priority(index - 1, evidence_type),
            "edit_type": edit_type,
            "section": candidate.get("section", ""),
            "source": candidate.get("source", ""),
            "jd_signal_terms": supported_terms,
            "current_evidence": current_evidence,
            "parent_bullet": parent_bullet,
            "recommended_rewrite": recommended_rewrite,
            "why_current_is_weak": why_current_is_weak,
            "why_rewrite_is_better": why_rewrite_is_better,
            "why_it_matters": why_it_matters,
            "claim_safety": claim_safety,
            "placement_guidance": _placement_guidance(candidate),
            "entry_id": candidate.get("entry_id", ""),
            "entry_index": candidate.get("entry_index", -1),
            "bullet_id": candidate.get("bullet_id", ""),
            "bullet_index": candidate.get("bullet_index", -1),
            "matched_surface_signal": matched_surface_signal,
            "canonical_supported_signal": canonical_supported_signal,
        }

        if patch_ready_candidate is not None:
            card.update(
                _rewrite_card_fields_from_patch_ready_candidate(
                    patch_ready_candidate,
                    supported_terms,
                )
            )
        elif directional_candidate is not None:
            card.update(
                _rewrite_card_fields_from_directional_candidate(
                    directional_candidate,
                    supported_terms,
                )
            )
        elif _looks_like_directional_instruction_text(
            str(card.get("recommended_rewrite", "") or "")
        ):
            directional_text = str(card.get("recommended_rewrite", "") or "").strip()

            preview_diagnosis = {
                "diagnosis_action": "rewrite",
                "diagnosis_reason_type": "rewrite",
                "priority": str(card.get("priority", "") or "").strip(),
                "section": str(card.get("section", "") or "").strip(),
                "source": str(card.get("source", "") or "").strip(),
                "entry_id": str(card.get("entry_id", "") or "").strip(),
                "entry_index": card.get("entry_index", -1),
                "bullet_id": str(card.get("bullet_id", "") or "").strip(),
                "bullet_index": card.get("bullet_index", -1),
                "parent_bullet": parent_bullet,
                "original_text": source_text,
                "current_evidence": current_evidence or parent_bullet,
                "evidence_type": evidence_type,
                "jd_signal_terms": supported_terms,
                "likely_impacted_dimensions": _likely_impacted_dimensions(
                    payload,
                    str(card.get("section", "") or ""),
                    supported_terms,
                ),
                "why": str(card.get("why_it_matters", "") or "").strip(),
                "recommended_rewrite": directional_text,
                "claim_safety": claim_safety,
                "placement_guidance": str(card.get("placement_guidance", "") or "").strip(),
                "matched_surface_signal": matched_surface_signal,
                "canonical_supported_signal": canonical_supported_signal,
                "structural_operation": str(card.get("structural_operation", "") or "").strip(),
                "structural_clause_text": str(card.get("structural_clause_text", "") or "").strip(),
            }

            preview_risks = _replacement_candidate_risks(payload, preview_diagnosis)
            preview_status, preview_patch_text, preview_patch_method, _ = _deterministic_patch_text_from_diagnosis(
                preview_diagnosis,
                preview_risks["adjacent_risk_signals"],
                preview_risks["unsupported_risk_signals"],
            )

            if preview_status == "patch_ready" and preview_patch_text:
                card.update(
                    {
                        "recommended_rewrite": preview_patch_text,
                        "why_rewrite_is_better": (
                            "It replaces generic direction-only guidance with a grounded deterministic bullet patch."
                        ),
                        "patch_generation_method": preview_patch_method,
                    }
                )
            else:
                card.update(
                    {
                        "edit_type": "rewrite",
                        "claim_safety": "safe_strengthen",
                        "recommended_rewrite": directional_text,
                        "why_rewrite_is_better": (
                            "No grounded deterministic replacement candidate survived for this bullet, "
                            "but the evidence still supports a directional rewrite recommendation."
                        ),
                        "why_it_matters": directional_text or str(card.get("why_it_matters", "") or "").strip(),
                        "outcome_label": "directional_only",
                        "outcome_reason": "instructional_rewrite_without_grounded_candidate",
                        "final_diagnosis_action": "rewrite",
                        "final_diagnosis_reason_type": "directional_rewrite",
                    }
                )

        family_key = _edit_card_family_dedup_key(card)
        if family_key and family_key in seen_family_keys:
            continue

        cards.append(card)

        if bullet_id:
            seen_bullet_ids.add(bullet_id)
        if family_key:
            seen_family_keys.add(family_key)

    cards = _backfill_edit_cards_from_bullet_reuse(
        payload,
        preferred_rewrite_directions,
        cards,
        seen_family_keys,
        limit,
    )

    cards = _dedupe_edit_cards_by_candidate_id(cards)
    cards = _rank_and_suppress_edit_cards(cards, limit)

    return cards[:limit]


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

def _curated_rewrite_candidate_key(row: Dict[str, Any]) -> tuple:
    return (
        str(row.get("bullet_id", "") or "").strip(),
        str(row.get("section", "") or "").strip(),
        str(row.get("source", "") or "").strip(),
        str(row.get("parent_bullet", "") or row.get("current_evidence", "") or row.get("original_text", "") or "").strip(),
    )


def _curated_rewrite_candidate_key_from_diagnosis(diagnosis: Dict[str, Any]) -> tuple:
    return (
        str(diagnosis.get("bullet_id", "") or "").strip(),
        str(diagnosis.get("section", "") or "").strip(),
        str(diagnosis.get("source", "") or "").strip(),
        str(diagnosis.get("original_text", "") or "").strip(),
    )


def _curated_rewrite_candidate_key_set(payload: Dict[str, Any]) -> set[tuple]:
    keys = set()

    for row in list(payload.get("rewrite_candidates", []) or []):
        key = _curated_rewrite_candidate_key(row)
        if any(key):
            keys.add(key)

    return keys

def _bullet_diagnosis_dedupe_key(item: Dict[str, Any]) -> tuple:
    bullet_id = str(item.get("bullet_id", "") or "").strip()
    if bullet_id:
        return ("bullet", bullet_id)

    section = str(item.get("section", "") or "").strip()
    source = str(item.get("source", "") or "").strip()
    entry_id = str(item.get("entry_id", "") or "").strip()
    bullet_index = item.get("bullet_index", -1)
    diagnosis_action = str(item.get("diagnosis_action", "") or "").strip()

    jd_terms = tuple(sorted({
        _diagnosis_normalize_term(str(term))
        for term in (
            list(item.get("jd_signal_terms", []) or [])
            + list(item.get("overlaps", []) or [])
        )
        if _diagnosis_normalize_term(str(term))
    }))

    if entry_id and isinstance(bullet_index, int) and bullet_index >= 0:
        return (
            "entry_bullet",
            section,
            source,
            entry_id,
            bullet_index,
            diagnosis_action,
            jd_terms,
        )

    if entry_id:
        return (
            "entry",
            section,
            source,
            entry_id,
            diagnosis_action,
            jd_terms,
        )

    return (
        "source_terms",
        section,
        source,
        diagnosis_action,
        jd_terms,
    )

def _edit_card_to_bullet_diagnosis(
    packet: Dict[str, Any],
    card: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:
    jd_signal_terms = list(card.get("jd_signal_terms", []) or [])
    current_evidence = str(card.get("current_evidence", "") or "").strip()
    parent_bullet = str(card.get("parent_bullet", "") or "").strip()

    edit_type = str(card.get("edit_type", "") or "").strip()
    final_diagnosis_action = str(card.get("final_diagnosis_action", "") or "").strip()
    final_diagnosis_reason_type = str(card.get("final_diagnosis_reason_type", "") or "").strip()

    if final_diagnosis_action:
        diagnosis_action = final_diagnosis_action
    elif edit_type == "rewrite":
        diagnosis_action = "rewrite"
    else:
        diagnosis_action = "keep"

    if final_diagnosis_reason_type:
        diagnosis_reason_type = final_diagnosis_reason_type
    elif edit_type in {"support", "supporting_context"}:
        diagnosis_reason_type = "keep_context_anchor"
    elif diagnosis_action == "keep":
        diagnosis_reason_type = "keep_existing_anchor"
    else:
        diagnosis_reason_type = edit_type

    recommended_rewrite = str(card.get("recommended_rewrite", "") or "").strip()
    if diagnosis_action != "rewrite":
        recommended_rewrite = ""

    why = (
        str(card.get("why_it_matters", "") or "").strip()
        or str(card.get("why_rewrite_is_better", "") or "").strip()
    )

    return {
        "diagnosis_id": f"bullet_diag_{index}",
        "diagnosis_action": diagnosis_action,
        "diagnosis_reason_type": diagnosis_reason_type,
        "priority": str(card.get("priority", "") or "").strip(),
        "section": str(card.get("section", "") or "").strip(),
        "source": str(card.get("source", "") or "").strip(),
        "entry_id": str(card.get("entry_id", "") or "").strip(),
        "entry_index": card.get("entry_index", -1),
        "bullet_id": str(card.get("bullet_id", "") or "").strip(),
        "bullet_index": card.get("bullet_index", -1),
        "parent_bullet": parent_bullet,
        "original_text": current_evidence or parent_bullet,
        "current_evidence": current_evidence or parent_bullet,
        "evidence_type": str(card.get("evidence_type", "") or "").strip(),
        "jd_signal_terms": jd_signal_terms,
        "likely_impacted_dimensions": _likely_impacted_dimensions(
            packet,
            str(card.get("section", "") or ""),
            jd_signal_terms,
        ),
        "why": why,
        "recommended_rewrite": recommended_rewrite,
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

def _diagnosis_direct_signal_terms(diagnosis: Dict[str, Any]) -> List[str]:
    evidence_type = str(diagnosis.get("evidence_type", "") or "").strip()
    if evidence_type != "direct_overlap":
        return []

    direct_terms = _unique_preserve_order(
        list(diagnosis.get("jd_signal_terms", []) or [])
        + [str(diagnosis.get("canonical_supported_signal", "") or "").strip()]
    )
    return [term for term in direct_terms if str(term or "").strip()]


def _diagnosis_context_signal_terms(diagnosis: Dict[str, Any]) -> List[str]:
    evidence_type = str(diagnosis.get("evidence_type", "") or "").strip()
    if evidence_type == "direct_overlap":
        return []

    context_terms = _unique_preserve_order(
        list(diagnosis.get("context_signal_terms", []) or [])
        + list(diagnosis.get("jd_signal_terms", []) or [])
        + [str(diagnosis.get("canonical_supported_signal", "") or "").strip()]
    )
    return [term for term in context_terms if str(term or "").strip()]


def _normalize_diagnosis_signal_fields(diagnosis: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(diagnosis)
    normalized["jd_signal_terms"] = _diagnosis_direct_signal_terms(diagnosis)
    normalized["context_signal_terms"] = _diagnosis_context_signal_terms(diagnosis)
    return normalized

def _normalize_reinforce_context_diagnosis(
    diagnosis: Dict[str, Any],
) -> Dict[str, Any]:
    diagnosis = _normalize_diagnosis_signal_fields(diagnosis)

    if str(diagnosis.get("diagnosis_action", "") or "").strip() != "rewrite":
        return diagnosis

    evidence_type = str(diagnosis.get("evidence_type", "") or "").strip()
    reason_type = str(diagnosis.get("diagnosis_reason_type", "") or "").strip()
    claim_safety = str(diagnosis.get("claim_safety", "") or "").strip()
    matched_surface_signal = str(diagnosis.get("matched_surface_signal", "") or "").strip()
    canonical_supported_signal = str(diagnosis.get("canonical_supported_signal", "") or "").strip()

    should_keep_context = (
        evidence_type == "same_source_context"
        and (
            reason_type == "reinforce"
            or claim_safety == "adjacent_only"
            or (not matched_surface_signal and not canonical_supported_signal)
        )
    )

    if not should_keep_context:
        return diagnosis

    normalized = dict(diagnosis)
    normalized["diagnosis_action"] = "keep"
    normalized["diagnosis_reason_type"] = "keep_context_anchor"
    normalized["claim_safety"] = "keep_visible"
    normalized["recommended_rewrite"] = ""
    normalized["jd_signal_terms"] = []
    normalized["context_signal_terms"] = _diagnosis_context_signal_terms(diagnosis)
    normalized["why"] = (
        str(normalized.get("why", "") or "").strip()
        or "This bullet is reinforcing context for the main story and should stay visible instead of entering the rewrite lane."
    )
    normalized["placement_guidance"] = "Keep this supporting bullet visible near the main anchor."
    return normalized

def _supported_term_already_explicit_anywhere(
    text: str,
    supported_terms: List[str],
) -> bool:
    raw_text = str(text or "").strip()
    if not raw_text:
        return False

    normalized_text = _diagnosis_normalize_term(raw_text)
    normalized_terms = [
        _diagnosis_normalize_term(term)
        for term in (supported_terms or [])
        if _diagnosis_normalize_term(term)
    ]
    if not normalized_terms:
        return False

    return any(term in normalized_text for term in normalized_terms)

def _normalize_direct_overlap_rewrite_diagnosis(
    packet: Dict[str, Any],
    diagnosis: Dict[str, Any],
) -> Dict[str, Any]:
    diagnosis = _normalize_diagnosis_signal_fields(diagnosis)

    if str(diagnosis.get("diagnosis_action", "") or "").strip() != "rewrite":
        return diagnosis

    if str(diagnosis.get("evidence_type", "") or "").strip() != "direct_overlap":
        return diagnosis

    if str(diagnosis.get("claim_safety", "") or "").strip() != "safe_strengthen":
        return diagnosis

    supported_terms = _diagnosis_direct_signal_terms(diagnosis)
    original_text = str(diagnosis.get("original_text", "") or "").strip()

    risks = _replacement_candidate_risks(packet, diagnosis)

    proposal_status, _, patch_generation_method, _ = _deterministic_patch_text_from_diagnosis(
        diagnosis,
        risks["adjacent_risk_signals"],
        risks["unsupported_risk_signals"],
    )

    normalized = dict(diagnosis)
    normalized["jd_signal_terms"] = supported_terms
    normalized["context_signal_terms"] = []
    normalized["precomputed_patch_generation_method"] = patch_generation_method

    # If the deterministic patch builder can make a real patch, keep this in rewrite lane.
    if proposal_status == "patch_ready":
        return normalized

    if not supported_terms:
        return normalized

    # IMPORTANT:
    # Keep multi-signal explicit bullets in the rewrite lane.
    # Those are the exact cases the bounded substantive LLM lane should see.
    if len(supported_terms) >= 2:
        return normalized

    # For single-signal cases that are already explicit early, do not collapse them to keep-only.
    # Let the rewrite lane preserve them as directional-only so replacement selection can still
    # surface grounded operator guidance.
    if _all_supported_terms_already_salient_early(original_text, supported_terms):
        normalized["diagnosis_action"] = "rewrite"
        normalized["diagnosis_reason_type"] = "directional_rewrite"
        normalized["claim_safety"] = "safe_strengthen"
        return normalized

    # Otherwise, keep it in rewrite lane even if the signal is already explicit somewhere later.
    return normalized

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

    jd_terms_raw = _diagnosis_direct_signal_terms(diagnosis)
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

    directional_only_reason = ""

    reroute_directional_only, reroute_reason = _should_reroute_rewrite_to_directional_only(diagnosis)
    if reroute_directional_only:
        proposal_status = "direction_only"
        patch_text = ""
        patch_generation_method = ""
        directional_only_reason = reroute_reason

        if reroute_reason == "multi_signal_already_explicit_reorder_preferred":
            rewrite_instruction = (
                "Do not rewrite this bullet text. The supported JD signals are already explicit. "
                "Prefer moving this bullet earlier within the section if stronger ATS visibility is needed."
            )
        elif reroute_reason == "single_signal_already_explicit_reorder_preferred":
            supported_terms = [
                str(item).strip()
                for item in (diagnosis.get("jd_signal_terms", []) or [])
                if str(item).strip()
            ]
            lead = supported_terms[0] if supported_terms else "the supported JD signal"
            rewrite_instruction = (
                f"Do not rewrite this bullet text. {lead} is already stated explicitly. "
                "Keep this bullet visible and move it earlier within the section only if stronger ATS visibility is needed."
            )
        elif reroute_reason == "supported_terms_too_generic_to_front":
            rewrite_instruction = (
                "Do not force a rewrite around generic supported terms. Keep this directional only unless a stronger direct signal is available."
            )
        elif reroute_reason == "rewrite_instruction_pathological":
            rewrite_instruction = (
                "Do not rewrite this bullet from the current instruction because the rewrite instruction is malformed or overlong. Keep this directional only."
            )
    else:
        proposal_status, patch_text, patch_generation_method, deterministic_directional_reason = _deterministic_patch_text_from_diagnosis(
            diagnosis,
            risks["adjacent_risk_signals"],
            risks["unsupported_risk_signals"],
        )
        if proposal_status == "direction_only":
            directional_only_reason = (
                str(directional_only_reason or "").strip()
                or str(deterministic_directional_reason or "").strip()
            )

            # Only fall back to the pathological-instruction label AFTER
            # deterministic patch generation has failed.
            if (
                not directional_only_reason
                and _rewrite_instruction_is_pathological(diagnosis)
            ):
                directional_only_reason = "rewrite_instruction_pathological"

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
        "direction_only_reason": directional_only_reason,
        "original_text": str(diagnosis.get("original_text", "") or "").strip(),
        "current_evidence": str(diagnosis.get("current_evidence", "") or "").strip(),
        "parent_bullet": str(diagnosis.get("parent_bullet", "") or "").strip(),
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

    jd_signal_terms = [
        str(item).strip()
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]
    if not jd_signal_terms:
        return False

    impacted = list(diagnosis.get("likely_impacted_dimensions", []) or [])
    if not impacted:
        return False

    claim_safety = str(diagnosis.get("claim_safety", "") or "").strip()
    if claim_safety not in {"keep_visible", "safe_strengthen"}:
        return False

    # Reorder companions are useful for stronger anchors, but single-signal tooling
    # anchors are currently over-produced and create a lot of low-value noise
    # (for example python/sql/tableau-only keeps). Keep multi-signal anchors eligible,
    # and keep single-signal non-tooling anchors eligible.
    normalized_terms = _unique_preserve_order(jd_signal_terms)
    if len(normalized_terms) == 1:
        family = str(family_for_term(normalized_terms[0]) or "").strip()
        if family == "tooling":
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

def _candidate_promotable_family(candidate: Dict[str, Any]) -> str:
    terms = list(candidate.get("supported_jd_signals", []) or candidate.get("jd_signal_terms", []) or [])
    return _primary_promotable_family_from_terms(terms)

def _rewrite_review_state_display_label(value: str) -> str:
    key = str(value or "").strip()
    if not key:
        return "Pending"
    return _REWRITE_REVIEW_STATE_DISPLAY_LABELS.get(key, key.replace("_", " ").title())

def _promotable_family_display_label(family: str) -> str:
    raw_family = str(family or "").strip()
    if not raw_family:
        return ""

    label = _PROMOTABLE_SIGNAL_FAMILY_LABELS.get(raw_family, "")
    if label:
        return label.strip().lower()

    return raw_family.replace("_", " ").strip().lower()


def _rationale_focus_label_from_terms(terms: List[str]) -> str:
    normalized_terms = _unique_preserve_order(
        [
            str(term or "").strip().lower()
            for term in (terms or [])
            if str(term or "").strip()
        ]
    )
    if not normalized_terms:
        return "target"

    promotable_families = _unique_preserve_order(
        [
            family
            for family in (
                str(family_for_term(term) or "").strip()
                for term in normalized_terms
            )
            if family in _PROMOTABLE_REUSE_FAMILY_PRIORITY
        ]
    )

    explicit_focus = " / ".join(_truncate_list(normalized_terms, 3))

    if len(promotable_families) == 1:
        family = promotable_families[0]

        # "tooling" is too vague for operator-facing rationale text.
        # Prefer the actual surfaced terms in that case.
        if family == "tooling":
            return explicit_focus or "tooling"

        return _promotable_family_display_label(family) or explicit_focus or "target"

    if len(promotable_families) > 1:
        return explicit_focus or "multi-signal evidence"

    return explicit_focus or "target"

def _suppress_anchor_candidates_for_diagnosis(
    diagnosis: Dict[str, Any],
    existing_candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if str(diagnosis.get("diagnosis_action", "") or "").strip() != "rewrite":
        return []

    if str(diagnosis.get("diagnosis_reason_type", "") or "").strip() not in {"reinforce", "support"}:
        return []

    if str(diagnosis.get("evidence_type", "") or "").strip() != "same_source_context":
        return []

    if str(diagnosis.get("claim_safety", "") or "").strip() != "adjacent_only":
        return []

    section = str(diagnosis.get("section", "") or "").strip()
    if section not in {"experience", "project"}:
        return []

    family = _primary_promotable_family_from_terms(
        list(diagnosis.get("jd_signal_terms", []) or [])
    )
    if not family:
        return []

    anchors: List[Dict[str, Any]] = []
    for candidate in existing_candidates:
        if str(candidate.get("operation_type", "") or "").strip() != "rewrite":
            continue
        if str(candidate.get("proposal_status", "") or "").strip() != "patch_ready":
            continue
        if str(candidate.get("evidence_type", "") or "").strip() != "direct_overlap":
            continue
        if str(candidate.get("section", "") or "").strip() != section:
            continue
        if _candidate_promotable_family(candidate) != family:
            continue
        anchors.append(candidate)

    return anchors


def _diagnosis_to_suppress_candidate(
    diagnosis: Dict[str, Any],
    index: int,
    anchor_candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    diagnosis_id = str(diagnosis.get("diagnosis_id", "") or f"bullet_diag_{index}").strip()
    candidate_id = diagnosis_id.replace("bullet_diag", "replacement_suppress", 1)

    focus_label = _rationale_focus_label_from_terms(
        list(diagnosis.get("jd_signal_terms", []) or [])
    )
    anchor_ids = [
        str(row.get("candidate_id", "") or "").strip()
        for row in anchor_candidates
        if str(row.get("candidate_id", "") or "").strip()
    ]
    anchor_sources = _unique_preserve_order([
        str(row.get("source", "") or "").strip()
        for row in anchor_candidates
        if str(row.get("source", "") or "").strip()
    ])

    if anchor_sources:
        rewrite_instruction = (
            f"If space is tight, suppress this bullet or move it below a stronger anchor for {focus_label} "
            f"because the clearest direct evidence for {focus_label} is already covered more directly by {', '.join(anchor_sources)}."
        )
    else:
        rewrite_instruction = (
            f"If space is tight, suppress this bullet or move it below a stronger anchor for {focus_label} "
            f"because the clearest direct evidence for {focus_label} is already covered more directly elsewhere in this section."
        )

    return {
        "candidate_id": candidate_id,
        "source_bullet_id": str(diagnosis.get("bullet_id", "") or "").strip(),
        "source_entry_id": str(diagnosis.get("entry_id", "") or "").strip(),
        "section": str(diagnosis.get("section", "") or "").strip(),
        "evidence_type": str(diagnosis.get("evidence_type", "") or "").strip(),
        "source": str(diagnosis.get("source", "") or "").strip(),
        "operation_type": "suppress",
        "proposal_type": "directional_suppress",
        "proposal_status": "direction_only",
        "original_text": str(diagnosis.get("original_text", "") or "").strip(),
        "current_evidence": str(diagnosis.get("current_evidence", "") or "").strip(),
        "rewrite_instruction": rewrite_instruction,
        "proposed_text": "",
        "patch_text": "",
        "patch_ready": False,
        "patch_generation_method": "deterministic_suppress_direction",
        "supported_jd_signals": list(diagnosis.get("jd_signal_terms", []) or []),
        "adjacent_risk_signals": [],
        "unsupported_risk_signals": [],
        "likely_impacted_dimensions": list(diagnosis.get("likely_impacted_dimensions", []) or []),
        "why_this_improves_match": (
            f"This bullet reads more like supporting context, while a stronger direct anchor already carries "
            f"the clearest evidence for {focus_label}."
        ),
        "claim_safety": "safe_suppress",
        "safety_status": "safe_suppress",
        "placement_guidance": (
            "Only suppress this bullet if space is limited and the stronger direct anchor remains visible."
        ),
        "confidence": "medium",
        "conflicts_with": anchor_ids,
        "entry_index": diagnosis.get("entry_index", -1),
        "bullet_index": diagnosis.get("bullet_index", -1),
        "llm_refinement_used": False,
        "material_delta_found": False,
        "materiality_validation_status": "suppression_not_modeled_in_v1",
        "materiality_validation_note": (
            "Bullet suppression is not modeled as an exportable deterministic patch in v1, so this remains directional guidance."
        ),
        "projected_dimension_deltas": {},
        "projected_overall_delta": None,
        "matched_surface_signal": str(diagnosis.get("matched_surface_signal", "") or "").strip(),
        "canonical_supported_signal": str(diagnosis.get("canonical_supported_signal", "") or "").strip(),
    }

def _merge_anchor_candidates_for_diagnosis(
    diagnosis: Dict[str, Any],
    existing_candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    diagnosis_entry_id = str(diagnosis.get("entry_id", "") or "").strip()
    diagnosis_bullet_id = str(diagnosis.get("bullet_id", "") or "").strip()

    if not diagnosis_entry_id:
        return []

    anchors = _suppress_anchor_candidates_for_diagnosis(
        diagnosis,
        existing_candidates,
    )

    same_entry_anchors: List[Dict[str, Any]] = []
    for candidate in anchors:
        if str(candidate.get("source_entry_id", "") or "").strip() != diagnosis_entry_id:
            continue
        if diagnosis_bullet_id and str(candidate.get("source_bullet_id", "") or "").strip() == diagnosis_bullet_id:
            continue
        same_entry_anchors.append(candidate)

    return same_entry_anchors


def _diagnosis_to_merge_candidate(
    diagnosis: Dict[str, Any],
    index: int,
    anchor_candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    diagnosis_id = str(diagnosis.get("diagnosis_id", "") or f"bullet_diag_{index}").strip()
    candidate_id = diagnosis_id.replace("bullet_diag", "replacement_merge", 1)

    focus_label = _rationale_focus_label_from_terms(
        list(diagnosis.get("jd_signal_terms", []) or [])
    )

    anchor_ids = _unique_preserve_order([
        str(row.get("candidate_id", "") or "").strip()
        for row in anchor_candidates
        if str(row.get("candidate_id", "") or "").strip()
    ])
    anchor_sources = _unique_preserve_order([
        str(row.get("source", "") or "").strip()
        for row in anchor_candidates
        if str(row.get("source", "") or "").strip()
    ])
    source_bullet_ids = _unique_preserve_order([
        str(diagnosis.get("bullet_id", "") or "").strip(),
        *[
            str(row.get("source_bullet_id", "") or "").strip()
            for row in anchor_candidates
            if str(row.get("source_bullet_id", "") or "").strip()
        ],
    ])

    group_key = "|".join(source_bullet_ids) if source_bullet_ids else candidate_id

    if anchor_sources:
        rewrite_instruction = (
            f"If you want a tighter one-bullet story, merge the supporting context from this bullet into the stronger "
            f"direct anchor for {focus_label} from {', '.join(anchor_sources)}. Keep the direct anchor as the lead claim "
            "and borrow only details from this bullet that remain literally true."
        )
    else:
        rewrite_instruction = (
            f"If you want a tighter one-bullet story, merge the supporting context from this bullet into the stronger "
            f"direct anchor for {focus_label} in the same role entry. Keep the direct anchor as the lead claim and borrow "
            "only details from this bullet that remain literally true."
        )

    return {
        "candidate_id": candidate_id,
        "source_bullet_id": str(diagnosis.get("bullet_id", "") or "").strip(),
        "source_entry_id": str(diagnosis.get("entry_id", "") or "").strip(),
        "section": str(diagnosis.get("section", "") or "").strip(),
        "evidence_type": str(diagnosis.get("evidence_type", "") or "").strip(),
        "source": str(diagnosis.get("source", "") or "").strip(),
        "operation_type": "merge",
        "proposal_type": "directional_merge",
        "proposal_status": "direction_only",
        "original_text": str(diagnosis.get("original_text", "") or "").strip(),
        "current_evidence": str(diagnosis.get("current_evidence", "") or "").strip(),
        "rewrite_instruction": rewrite_instruction,
        "proposed_text": "",
        "patch_text": "",
        "patch_ready": False,
        "patch_generation_method": "deterministic_merge_direction",
        "supported_jd_signals": list(diagnosis.get("jd_signal_terms", []) or []),
        "adjacent_risk_signals": [],
        "unsupported_risk_signals": [],
        "likely_impacted_dimensions": list(diagnosis.get("likely_impacted_dimensions", []) or []),
        "why_this_improves_match": (
            f"This bullet adds supporting context for {focus_label}, but a stronger direct anchor in the same role entry "
            "already carries the lead claim more clearly."
        ),
        "claim_safety": "safe_merge",
        "safety_status": "safe_merge",
        "placement_guidance": (
            "Only merge if the stronger direct anchor stays intact and the added detail remains literally supported by this bullet."
        ),
        "confidence": "medium",
        "conflicts_with": anchor_ids,
        "entry_index": diagnosis.get("entry_index", -1),
        "bullet_index": diagnosis.get("bullet_index", -1),
        "llm_refinement_used": False,
        "material_delta_found": False,
        "materiality_validation_status": "merge_not_modeled_in_v1",
        "materiality_validation_note": (
            "Bullet merge is not modeled as an exportable deterministic patch in v1, so this remains directional guidance."
        ),
        "projected_dimension_deltas": {},
        "projected_overall_delta": None,
        "matched_surface_signal": str(diagnosis.get("matched_surface_signal", "") or "").strip(),
        "canonical_supported_signal": str(diagnosis.get("canonical_supported_signal", "") or "").strip(),
        "source_group_id": f"source_group_merge:{group_key}",
        "source_group_type": "bullet_group",
        "source_bullet_ids": source_bullet_ids,
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

        existing_source_group_id = str(candidate.get("source_group_id", "") or "").strip()
        existing_source_group_type = str(candidate.get("source_group_type", "") or "").strip()
        existing_source_bullet_ids = [
            str(item or "").strip()
            for item in (candidate.get("source_bullet_ids", []) or [])
            if str(item or "").strip()
        ]
        existing_conflict_group_id = str(candidate.get("conflict_group_id", "") or "").strip()

        source_bullet_ids = existing_source_bullet_ids or ([source_bullet_id] if source_bullet_id else [])
        source_group_id = existing_source_group_id or _candidate_source_group_id(candidate)
        source_group_type = existing_source_group_type or ("bullet_group" if len(source_bullet_ids) > 1 else "single_bullet")
        conflict_group_id = existing_conflict_group_id or _candidate_conflict_group_id(candidate)

        candidate["source_group_id"] = source_group_id
        candidate["source_group_type"] = source_group_type
        candidate["source_bullet_ids"] = source_bullet_ids
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

_COUNTERFACTUAL_JOB_IDENTITY_KEYS = {
    "job_doc_id",
    "company",
    "title",
    "link",
    "url",
    "job_url",
}


def _job_record_has_substantive_context(value: Any, *, top_level: bool = True) -> bool:
    if isinstance(value, dict):
        for raw_key, child in value.items():
            key = str(raw_key or "").strip().lower()
            if top_level and key in _COUNTERFACTUAL_JOB_IDENTITY_KEYS:
                continue
            if _job_record_has_substantive_context(child, top_level=False):
                return True
        return False

    if isinstance(value, (list, tuple, set)):
        return any(
            _job_record_has_substantive_context(item, top_level=False)
            for item in value
        )

    if isinstance(value, str):
        text = str(value or "").strip()
        if not text:
            return False
        if re.fullmatch(r"https?://\S+", text):
            return False
        return True

    return False


def _counterfactual_job_doc_id(
    job: Dict[str, Any],
    job_snapshot: Dict[str, Any],
) -> str:
    return str(
        (job_snapshot.get("job_doc_id", "") if isinstance(job_snapshot, dict) else "")
        or (job.get("job_doc_id", "") if isinstance(job, dict) else "")
        or ""
    ).strip()


def _resolve_counterfactual_job_record(
    job: Dict[str, Any],
    job_snapshot: Dict[str, Any],
    job_doc_id: str,
) -> Tuple[Optional[Dict[str, Any]], str]:
    if isinstance(job_snapshot, dict) and _job_record_has_substantive_context(job_snapshot):
        return dict(job_snapshot), "job_snapshot"

    if job_doc_id:
        corpus_record = _load_job_record_by_doc_id(job_doc_id)
        if isinstance(corpus_record, dict) and _job_record_has_substantive_context(corpus_record):
            return corpus_record, "job_corpus"

    if isinstance(job, dict) and _job_record_has_substantive_context(job):
        return dict(job), "payload_job"

    return None, "job_record_insufficient_context"

def _counterfactual_context_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    selection = payload.get("selection", {}) or {}
    job = payload.get("job", {}) or {}
    job_snapshot = payload.get("job_snapshot", {}) or {}

    selected_resume_name = str(selection.get("selected_resume", "") or "").strip()
    job_doc_id = _counterfactual_job_doc_id(job, job_snapshot)

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

    job_record, job_record_source = _resolve_counterfactual_job_record(
        job,
        job_snapshot,
        job_doc_id,
    )

    if job_record is None:
        return {
            "ok": False,
            "reason": job_record_source or "job_record_not_found",
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
        "job_record_source": job_record_source,
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

def _entry_text_fragments(entry: Any) -> List[str]:
    fragments: List[str] = []

    def _append_value(value: Any) -> None:
        if isinstance(value, str):
            text = str(value).strip()
            if text:
                fragments.append(text)
            return

        if isinstance(value, dict):
            for key in ("text", "bullet", "content", "description", "summary"):
                text = str(value.get(key, "") or "").strip()
                if text:
                    fragments.append(text)
                    return
            return

        text = str(getattr(value, "text", "") or getattr(value, "content", "") or "").strip()
        if text:
            fragments.append(text)

    for attr in (
        "bullets",
        "bullet_texts",
        "highlights",
        "accomplishments",
        "responsibilities",
    ):
        raw = getattr(entry, attr, None)
        if isinstance(raw, (list, tuple)):
            for item in raw:
                _append_value(item)

    for attr in (
        "summary",
        "description",
        "text",
        "raw_text",
    ):
        raw = getattr(entry, attr, None)
        if raw:
            _append_value(raw)

    return _sorted_unique_strings(fragments)


def _resume_lead_signal_snapshot(
    resume: Any,
    max_words: int = 10,
) -> Dict[str, List[str]]:
    lead_family_terms: List[str] = []
    lead_explicit_skills: List[str] = []

    explicit_skill_lexicon = {
        str(value).strip().lower()
        for value in list(getattr(resume, "skills", []) or [])
        if str(value).strip()
    }

    for entry in list(getattr(resume, "experience_entries", []) or []):
        explicit_skill_lexicon.update(
            str(value).strip().lower()
            for value in list(getattr(entry, "normalized_skills", []) or [])
            if str(value).strip()
        )

    for entry in list(getattr(resume, "project_entries", []) or []):
        explicit_skill_lexicon.update(
            str(value).strip().lower()
            for value in list(getattr(entry, "normalized_skills", []) or [])
            if str(value).strip()
        )

    for entry in list(getattr(resume, "experience_entries", []) or []) + list(getattr(resume, "project_entries", []) or []):
        for fragment in _entry_text_fragments(entry):
            words = re.findall(r"\S+", fragment)
            lead_text = " ".join(words[:max_words]).strip()
            if not lead_text:
                continue

            lead_family_terms.extend(prioritized_family_terms_from_text(lead_text))

            lead_text_norm = _diagnosis_normalize_term(lead_text)
            for skill in explicit_skill_lexicon:
                if skill and skill in lead_text_norm:
                    lead_explicit_skills.append(skill)

    return {
        "lead_family_terms": _sorted_unique_strings(lead_family_terms),
        "lead_explicit_skills": _sorted_unique_strings(lead_explicit_skills),
    }

def _entry_ordered_text_fragments(entry: Any) -> List[Tuple[str, str]]:
    def _coerce_text(value: Any) -> str:
        if isinstance(value, str):
            return str(value).strip()

        if isinstance(value, dict):
            for key in ("text", "bullet", "content", "description", "summary"):
                text = str(value.get(key, "") or "").strip()
                if text:
                    return text
            return ""

        return str(
            getattr(value, "text", "") or getattr(value, "content", "") or ""
        ).strip()

    for attr in (
        "bullets",
        "bullet_texts",
        "highlights",
        "accomplishments",
        "responsibilities",
    ):
        raw = getattr(entry, attr, None)
        if isinstance(raw, (list, tuple)) and raw:
            output: List[Tuple[str, str]] = []
            for idx, item in enumerate(raw):
                text = _coerce_text(item)
                if text:
                    output.append((f"{attr}:{idx}", text))
            if output:
                return output

    fallback: List[Tuple[str, str]] = []
    for attr in ("summary", "description", "text", "raw_text"):
        raw = getattr(entry, attr, None)
        text = _coerce_text(raw)
        if text:
            fallback.append((attr, text))

    return fallback


def _resume_lead_signal_snapshot_by_bullet(
    resume: Any,
    max_words: int = 10,
) -> Dict[str, Dict[str, List[str]]]:
    explicit_skill_lexicon = {
        str(value).strip().lower()
        for value in list(getattr(resume, "skills", []) or [])
        if str(value).strip()
    }

    for entry in list(getattr(resume, "experience_entries", []) or []):
        explicit_skill_lexicon.update(
            str(value).strip().lower()
            for value in list(getattr(entry, "normalized_skills", []) or [])
            if str(value).strip()
        )

    for entry in list(getattr(resume, "project_entries", []) or []):
        explicit_skill_lexicon.update(
            str(value).strip().lower()
            for value in list(getattr(entry, "normalized_skills", []) or [])
            if str(value).strip()
        )

    by_bullet: Dict[str, Dict[str, List[str]]] = {}

    def _collect(entries: List[Any], prefix: str) -> None:
        for idx, entry in enumerate(entries):
            raw_entry_id = str(getattr(entry, "entry_id", "") or "").strip()
            entry_id = raw_entry_id or f"{prefix}:{idx}"

            for fragment_key, fragment_text in _entry_ordered_text_fragments(entry):
                words = re.findall(r"\S+", fragment_text)
                lead_text = " ".join(words[:max_words]).strip()
                if not lead_text:
                    continue

                lead_family_terms = prioritized_family_terms_from_text(lead_text)

                lead_text_norm = _diagnosis_normalize_term(lead_text)
                lead_explicit_skills = [
                    skill
                    for skill in explicit_skill_lexicon
                    if skill and skill in lead_text_norm
                ]

                bullet_key = f"{prefix}:{entry_id}:{fragment_key}"
                by_bullet[bullet_key] = {
                    "lead_family_terms": _sorted_unique_strings(lead_family_terms),
                    "lead_explicit_skills": _sorted_unique_strings(lead_explicit_skills),
                }

    _collect(list(getattr(resume, "experience_entries", []) or []), "experience")
    _collect(list(getattr(resume, "project_entries", []) or []), "project")

    return by_bullet

def _resume_lead_signal_snapshot_by_entry(
    resume: Any,
    max_words: int = 10,
) -> Dict[str, Dict[str, List[str]]]:
    explicit_skill_lexicon = {
        str(value).strip().lower()
        for value in list(getattr(resume, "skills", []) or [])
        if str(value).strip()
    }

    for entry in list(getattr(resume, "experience_entries", []) or []):
        explicit_skill_lexicon.update(
            str(value).strip().lower()
            for value in list(getattr(entry, "normalized_skills", []) or [])
            if str(value).strip()
        )

    for entry in list(getattr(resume, "project_entries", []) or []):
        explicit_skill_lexicon.update(
            str(value).strip().lower()
            for value in list(getattr(entry, "normalized_skills", []) or [])
            if str(value).strip()
        )

    by_entry: Dict[str, Dict[str, List[str]]] = {}

    def _collect(entries: List[Any], prefix: str) -> None:
        for idx, entry in enumerate(entries):
            raw_entry_id = str(getattr(entry, "entry_id", "") or "").strip()
            entry_id = raw_entry_id or f"{prefix}:{idx}"
            entry_key = f"{prefix}:{entry_id}"

            lead_family_terms: List[str] = []
            lead_explicit_skills: List[str] = []

            for fragment in _entry_text_fragments(entry):
                words = re.findall(r"\S+", fragment)
                lead_text = " ".join(words[:max_words]).strip()
                if not lead_text:
                    continue

                lead_family_terms.extend(prioritized_family_terms_from_text(lead_text))

                lead_text_norm = _diagnosis_normalize_term(lead_text)
                for skill in explicit_skill_lexicon:
                    if skill and skill in lead_text_norm:
                        lead_explicit_skills.append(skill)

            by_entry[entry_key] = {
                "lead_family_terms": _sorted_unique_strings(lead_family_terms),
                "lead_explicit_skills": _sorted_unique_strings(lead_explicit_skills),
            }

    _collect(list(getattr(resume, "experience_entries", []) or []), "experience")
    _collect(list(getattr(resume, "project_entries", []) or []), "project")

    return by_entry

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

    lead_snapshot = _resume_lead_signal_snapshot(resume)
    entry_lead_snapshot = _resume_lead_signal_snapshot_by_entry(resume)
    bullet_lead_snapshot = _resume_lead_signal_snapshot_by_bullet(resume)

    entry_lead_family_terms: List[str] = []
    entry_lead_explicit_skills: List[str] = []
    bullet_lead_family_terms: List[str] = []
    bullet_lead_explicit_skills: List[str] = []

    for entry_key, snapshot in entry_lead_snapshot.items():
        entry_lead_family_terms.extend(
            f"{entry_key}|{term}"
            for term in list(snapshot.get("lead_family_terms", []) or [])
            if str(term).strip()
        )
        entry_lead_explicit_skills.extend(
            f"{entry_key}|{skill}"
            for skill in list(snapshot.get("lead_explicit_skills", []) or [])
            if str(skill).strip()
        )
    
    for bullet_key, snapshot in bullet_lead_snapshot.items():
        bullet_lead_family_terms.extend(
            f"{bullet_key}|{term}"
            for term in list(snapshot.get("lead_family_terms", []) or [])
            if str(term).strip()
        )
        bullet_lead_explicit_skills.extend(
            f"{bullet_key}|{skill}"
            for skill in list(snapshot.get("lead_explicit_skills", []) or [])
            if str(skill).strip()
        )

    return {
        "explicit_skills": _sorted_unique_strings(list(explicit_skills)),
        "titles": _sorted_unique_strings(titles),
        "domain_signals": _sorted_unique_strings(list(getattr(resume, "domain_signals", []) or [])),
        "analytics_ml_signals": _sorted_unique_strings(list(getattr(resume, "analytics_ml_signals", []) or [])),
        "experimentation_signals": _sorted_unique_strings(list(getattr(resume, "experimentation_signals", []) or [])),
        "tooling_signals": _sorted_unique_strings(list(getattr(resume, "tooling_signals", []) or [])),
        "project_skills": _sorted_unique_strings(project_skills),
        "lead_family_terms": lead_snapshot["lead_family_terms"],
        "lead_explicit_skills": lead_snapshot["lead_explicit_skills"],
        "entry_lead_family_terms": _sorted_unique_strings(entry_lead_family_terms),
        "entry_lead_explicit_skills": _sorted_unique_strings(entry_lead_explicit_skills),
        "bullet_lead_family_terms": _sorted_unique_strings(bullet_lead_family_terms),
        "bullet_lead_explicit_skills": _sorted_unique_strings(bullet_lead_explicit_skills),
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
            _patch_candidate_bullet_id(candidate),
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

def _patch_candidate_bullet_id(candidate: Dict[str, Any]) -> str:
    return (
        str(candidate.get("source_bullet_id", "") or "").strip()
        or str(candidate.get("bullet_id", "") or "").strip()
    )

def _resolve_patch_set_selection(
    candidates: List[Dict[str, Any]],
    selected_candidate_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    explicit_selection = selected_candidate_ids is not None

    requested_candidate_ids = _unique_preserve_order(
        [
            str(candidate_id or "").strip()
            for candidate_id in (selected_candidate_ids or [])
            if str(candidate_id or "").strip()
        ]
    )

    candidate_by_id: Dict[str, Dict[str, Any]] = {}
    patch_ready_rewrite_ids: List[str] = []

    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id", "") or "").strip()
        if candidate_id and candidate_id not in candidate_by_id:
            candidate_by_id[candidate_id] = candidate

        operation_type = str(candidate.get("operation_type", "") or "").strip()
        proposal_status = str(candidate.get("proposal_status", "") or "").strip()
        source_bullet_id = _patch_candidate_bullet_id(candidate)
        patch_text = str(candidate.get("patch_text", "") or "").strip()

        if (
            operation_type == "rewrite"
            and proposal_status == "patch_ready"
            and source_bullet_id
            and patch_text
            and candidate_id
        ):
            patch_ready_rewrite_ids.append(candidate_id)

    selection_mode = "selected_candidate_ids" if explicit_selection else "all_patch_ready_rewrites"
    candidate_ids_to_evaluate = requested_candidate_ids if explicit_selection else patch_ready_rewrite_ids

    selected_candidates: List[Dict[str, Any]] = []
    skipped_candidate_ids: List[str] = []
    missing_candidate_ids: List[str] = []
    ineligible_candidate_ids: List[str] = []
    duplicate_bullet_ids: List[str] = []

    seen_bullet_ids = set()

    for candidate_id in candidate_ids_to_evaluate:
        candidate = candidate_by_id.get(candidate_id)
        if candidate is None:
            missing_candidate_ids.append(candidate_id)
            skipped_candidate_ids.append(candidate_id)
            continue

        operation_type = str(candidate.get("operation_type", "") or "").strip()
        proposal_status = str(candidate.get("proposal_status", "") or "").strip()
        source_bullet_id = _patch_candidate_bullet_id(candidate)
        patch_text = str(candidate.get("patch_text", "") or "").strip()

        if operation_type != "rewrite" or proposal_status != "patch_ready" or not source_bullet_id or not patch_text:
            ineligible_candidate_ids.append(candidate_id)
            skipped_candidate_ids.append(candidate_id)
            continue

        if source_bullet_id in seen_bullet_ids:
            duplicate_bullet_ids.append(source_bullet_id)
            skipped_candidate_ids.append(candidate_id)
            continue

        seen_bullet_ids.add(source_bullet_id)
        selected_candidates.append(candidate)

    return {
        "selection_mode": selection_mode,
        "requested_candidate_ids": requested_candidate_ids,
        "selected_candidates": selected_candidates,
        "selected_candidate_ids": [
            str(candidate.get("candidate_id", "") or "").strip()
            for candidate in selected_candidates
            if str(candidate.get("candidate_id", "") or "").strip()
        ],
        "skipped_candidate_ids": skipped_candidate_ids,
        "missing_candidate_ids": missing_candidate_ids,
        "ineligible_candidate_ids": ineligible_candidate_ids,
        "duplicate_source_bullet_ids": duplicate_bullet_ids,
        "explicit_selection": explicit_selection,
    }

def _apply_patch_set_counterfactual_preview(
    payload: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    selected_candidate_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    context = _counterfactual_context_from_payload(payload)

    original_result = context["original_result"] if context.get("ok", False) else None
    original_score = (
        round(float(getattr(original_result, "final_score", 0.0) or 0.0), 6)
        if original_result is not None else None
    )

    selection = _resolve_patch_set_selection(
        candidates,
        selected_candidate_ids=selected_candidate_ids,
    )
    explicit_selection = bool(selection.get("explicit_selection", False))
    selected_candidates = list(selection.get("selected_candidates", []) or [])
    skipped_candidate_ids = list(selection.get("skipped_candidate_ids", []) or [])
    duplicate_bullet_ids = list(selection.get("duplicate_source_bullet_ids", []) or [])
    missing_candidate_ids = list(selection.get("missing_candidate_ids", []) or [])
    ineligible_candidate_ids = list(selection.get("ineligible_candidate_ids", []) or [])

    preview = {
        "selection_mode": str(selection.get("selection_mode", "") or "").strip(),
        "requested_candidate_ids": list(selection.get("requested_candidate_ids", []) or []),
        "selected_candidate_ids": list(selection.get("selected_candidate_ids", []) or []),
        "skipped_candidate_ids": skipped_candidate_ids,
        "missing_candidate_ids": missing_candidate_ids,
        "ineligible_candidate_ids": ineligible_candidate_ids,
        "selected_patch_count": len(selected_candidates),
        "status": "",
        "note": "",
        "original_final_score": original_score,
        "projected_final_score": None,
        "projected_overall_delta": None,
        "projected_dimension_deltas": {},
        "scorer_visible_evidence_changed": False,
        "evidence_delta": {},
        "duplicate_source_bullet_ids": duplicate_bullet_ids,
    }

    if duplicate_bullet_ids:
        preview["status"] = "duplicate_source_bullet_id"
        preview["note"] = (
            "Could not compute a multi-patch preview because multiple patch-ready candidates target the same bullet."
        )
        return preview

    if not selected_candidates:
        if explicit_selection and not preview["requested_candidate_ids"]:
            preview["status"] = "no_selected_candidates"
            preview["note"] = "No patch candidates are currently selected."
            preview["projected_final_score"] = original_score
            preview["projected_overall_delta"] = 0.0 if original_score is not None else None
            return preview

        if explicit_selection:
            preview["status"] = "no_valid_selected_candidates"
            preview["note"] = (
                "None of the requested candidate IDs resolved to a valid patch-ready rewrite set."
            )
        else:
            preview["status"] = "no_patch_ready_rewrites"
            preview["note"] = "No patch-ready rewrite candidates were available for a selected-set preview."
        return preview

    if not context.get("ok", False):
        reason = str(context.get("reason", "") or "context_unavailable").strip()
        preview["status"] = reason
        preview["note"] = f"Could not load counterfactual context for selected-set preview: {reason}."
        return preview

    patches = [
        {
            "source_bullet_id": _patch_candidate_bullet_id(candidate),
            "patch_text": str(candidate.get("patch_text", "") or "").strip(),
        }
        for candidate in selected_candidates
    ]

    patched_resume, status = build_counterfactual_resume_evidence_for_patches(
        context["original_resume"],
        patches,
    )

    preview["status"] = status

    if patched_resume is None or status != "ok":
        preview["note"] = "Could not apply the selected patch set as a deterministic counterfactual resume state."
        return preview

    patched_result = score_resume_job_match(patched_resume, context["job_evidence"])
    patched_score = round(float(getattr(patched_result, "final_score", 0.0) or 0.0), 6)
    overall_delta = round(patched_score - original_score, 6)

    original_snapshot = _resume_counterfactual_snapshot(context["original_resume"])
    patched_snapshot = _resume_counterfactual_snapshot(patched_resume)
    evidence_delta = _counterfactual_snapshot_delta(original_snapshot, patched_snapshot)

    preview["status"] = "scored"
    preview["note"] = (
        "Projected delta computed under the frozen deterministic evaluator for the full selected patch set."
    )
    preview["projected_final_score"] = patched_score
    preview["projected_overall_delta"] = overall_delta
    preview["projected_dimension_deltas"] = _nonzero_dimension_deltas(
        original_result,
        patched_result,
    )
    preview["scorer_visible_evidence_changed"] = bool(evidence_delta)
    preview["evidence_delta"] = evidence_delta

    return preview

def build_selected_patch_set_counterfactual_preview(
    payload: Dict[str, Any],
    selected_candidate_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return _apply_patch_set_counterfactual_preview(
        payload,
        list(payload.get("replacement_candidates", []) or []),
        selected_candidate_ids=selected_candidate_ids,
    )

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

    if not _clause_extract_candidate_is_safe(clause_text, original_text):
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

    if _looks_like_resume_header_metadata(promoted_clean):
        return None
    
    patch_parts = [promoted_clean] + remaining_clauses
    patch_text = ". ".join(part for part in patch_parts if part).strip()

    if original_text.endswith("."):
        patch_text += "."

    if _diagnosis_normalize_term(patch_text) == normalized_original:
        return None

    return patch_text

def _deterministic_fronted_using_phrase_patch(
    diagnosis: Dict[str, Any],
) -> Optional[str]:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    supported_terms = [
        str(item).strip()
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]

    if not original_text or not supported_terms:
        return None

    if len(supported_terms) > 3:
        return None

    match = _using_phrase_match_for_supported_term(original_text, supported_terms)
    if not match:
        return None

    surface_segments = _supported_using_phrase_segments(match, supported_terms)
    phrase = _natural_join_surface_segments(surface_segments)
    if not phrase:
        return None

    before = re.sub(r"\s+", " ", original_text[: match.start()].strip(" ,"))
    if not before:
        return None

    after_raw = original_text[match.end() :]
    after_has_leading_comma = bool(re.match(r"^\s*,", str(after_raw or "")))
    after = re.sub(r"^\s*,\s*", "", str(after_raw or "").strip())
    after = re.sub(r"\s+", " ", after).strip()

    patch_text = f"Using {phrase}, {_lowercase_first_character(before)}".strip()

    if after:
        patch_text = f"{patch_text}, {after}" if after_has_leading_comma else f"{patch_text} {after}"

    patch_text = re.sub(r"\s+", " ", patch_text)
    patch_text = re.sub(r"\s+,", ",", patch_text)
    patch_text = patch_text.rstrip(" .")

    if original_text.endswith("."):
        patch_text += "."

    if _diagnosis_normalize_term(patch_text) == _diagnosis_normalize_term(original_text):
        return None

    return patch_text

def _deterministic_family_alias_expansion_patch(
    diagnosis: Dict[str, Any],
) -> Optional[str]:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    if not original_text:
        return None

    raw_supported_terms = [
        str(item).strip()
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]
    normalized_supported_terms = [
        _diagnosis_normalize_term(item)
        for item in raw_supported_terms
        if _diagnosis_normalize_term(item)
    ]
    if len(normalized_supported_terms) != 1:
        return None

    supported_term = normalized_supported_terms[0]
    supported_surface = next(
        (
            raw
            for raw in raw_supported_terms
            if _diagnosis_normalize_term(raw) == supported_term
        ),
        supported_term,
    )

    if _supported_term_already_salient_early(original_text, [supported_term]):
        return None

    opening_clause = original_text.split(",", 1)[0].strip()
    if not opening_clause:
        return None

    alias_variants = expandable_aliases_for_supported_term(supported_term)
    if not alias_variants:
        return None

    for alias in alias_variants:
        pattern = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])",
            flags=re.IGNORECASE,
        )
        if not pattern.search(opening_clause):
            continue

        patch_text = pattern.sub(supported_surface, original_text, count=1).strip()

        if _diagnosis_normalize_term(patch_text) == _diagnosis_normalize_term(original_text):
            continue

        return patch_text

    return None

def _diagnosis_contains_supported_term_alias(
    text: str,
    supported_term: str,
) -> bool:
    raw_text = str(text or "").strip()
    if not raw_text or not str(supported_term or "").strip():
        return False

    normalized_text = _diagnosis_normalize_term(raw_text)
    canonical = _diagnosis_normalize_term(supported_term)
    if canonical and canonical in normalized_text:
        return True

    for alias in expandable_aliases_for_supported_term(str(supported_term).strip()):
        alias_norm = _diagnosis_normalize_term(alias)
        if alias_norm and alias_norm in normalized_text:
            return True

    return False


def _all_supported_terms_already_explicit(
    diagnosis: Dict[str, Any],
) -> bool:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    supported_terms = [
        str(item).strip()
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]
    if not original_text or not supported_terms:
        return False

    return all(
        _diagnosis_contains_supported_term_alias(original_text, term)
        for term in supported_terms
    )

def _single_supported_term_already_explicit(
    diagnosis: Dict[str, Any],
) -> bool:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    supported_terms = [
        str(item).strip()
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]

    if not original_text or len(supported_terms) != 1:
        return False

    return _diagnosis_contains_supported_term_alias(
        original_text,
        supported_terms[0],
    )

def _rewrite_instruction_is_pathological(
    diagnosis: Dict[str, Any],
) -> bool:
    instruction = str(
        diagnosis.get("rewrite_instruction", "") or diagnosis.get("recommended_rewrite", "") or ""
    ).strip()
    original_text = str(diagnosis.get("original_text", "") or "").strip()

    if not instruction:
        return False

    if original_text and len(instruction) >= len(original_text) * 0.9:
        return True

    normalized_instruction = _diagnosis_normalize_term(instruction)
    normalized_original = _diagnosis_normalize_term(original_text)
    if normalized_original and normalized_original in normalized_instruction:
        return True

    return False


def _supported_terms_too_generic_to_front(
    diagnosis: Dict[str, Any],
) -> bool:
    supported_terms = [
        str(item).strip().lower()
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]
    canonical_supported_signal = str(diagnosis.get("canonical_supported_signal", "") or "").strip().lower()

    generic_terms = {
        "validation",
        "etl pipelines",
        "analysis",
        "analytics",
        "reporting",
    }

    if canonical_supported_signal:
        return False

    if not supported_terms:
        return False

    return all(term in generic_terms for term in supported_terms)


def _should_reroute_rewrite_to_directional_only(
    diagnosis: Dict[str, Any],
) -> Tuple[bool, str]:
    supported_terms = [
        str(item).strip()
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]
    original_text = str(diagnosis.get("original_text", "") or "").strip()

    if _supported_terms_too_generic_to_front(diagnosis):
        return True, "supported_terms_too_generic_to_front"

    # IMPORTANT:
    # Do NOT pre-reroute multi-signal explicit bullets to direction_only.
    # Those are the exact candidates the bounded substantive LLM lane should see.
    if len(supported_terms) >= 2:
        return False, ""

    if len(supported_terms) == 1 and _supported_term_already_salient_early(
        original_text,
        supported_terms,
    ):
        return True, "single_signal_already_explicit_reorder_preferred"

    # IMPORTANT:
    # Do NOT reroute just because the operator-facing rewrite instruction is ugly.
    # Let deterministic patch generation try first.
    return False, ""

def _supported_signal_surface_pairs(
    diagnosis: Dict[str, Any],
) -> List[Tuple[str, str]]:
    raw_supported_terms = [
        str(item).strip()
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]

    pairs: List[Tuple[str, str]] = []
    seen = set()

    for raw in raw_supported_terms:
        normalized = _diagnosis_normalize_term(raw)
        if not normalized:
            continue

        surface = raw
        key = (normalized, surface.lower())
        if key in seen:
            continue
        seen.add(key)
        pairs.append((normalized, surface))

    return pairs


def _replace_earliest_supported_alias(
    text: str,
    supported_term: str,
    supported_surface: str,
) -> Optional[str]:
    raw_text = str(text or "").strip()
    if not raw_text:
        return None

    normalized_text = _diagnosis_normalize_term(raw_text)
    normalized_surface = _diagnosis_normalize_term(supported_surface)

    if normalized_surface and normalized_surface in normalized_text:
        return None

    alias_variants = [
        alias
        for alias in expandable_aliases_for_supported_term(supported_term)
        if _diagnosis_normalize_term(alias) != normalized_surface
    ]
    if not alias_variants:
        return None

    best_match = None

    for alias in alias_variants:
        pattern = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])",
            flags=re.IGNORECASE,
        )
        match = pattern.search(raw_text)
        if not match:
            continue

        if best_match is None or match.start() < best_match[0]:
            best_match = (match.start(), pattern)

    if best_match is None:
        return None

    _, pattern = best_match
    patched = pattern.sub(supported_surface, raw_text, count=1).strip()

    if _diagnosis_normalize_term(patched) == normalized_text:
        return None

    return patched


def _deterministic_supported_alias_expansion_patch(
    diagnosis: Dict[str, Any],
) -> Optional[str]:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    if not original_text:
        return None

    supported_pairs = _supported_signal_surface_pairs(diagnosis)
    if not supported_pairs or len(supported_pairs) > 3:
        return None

    patch_text = original_text
    changed = False

    for supported_term, supported_surface in supported_pairs:
        patched = _replace_earliest_supported_alias(
            patch_text,
            supported_term,
            supported_surface,
        )
        if not patched:
            continue

        patch_text = patched
        changed = True

    if not changed:
        return None

    if _diagnosis_normalize_term(patch_text) == _diagnosis_normalize_term(original_text):
        return None

    return patch_text

def _split_result_clause(text: str) -> Tuple[str, str]:
    raw = str(text or "").strip()
    if not raw:
        return "", ""

    markers = [
        ", informing ",
        ", improving ",
        ", enabling ",
        ", achieving ",
        ", resulting in ",
        ", leading to ",
        ", reducing ",
        ", increasing ",
        ", enhancing ",
        ", driving ",
    ]

    lowered = raw.lower()
    for marker in markers:
        idx = lowered.find(marker)
        if idx != -1:
            return raw[:idx].strip(), raw[idx:].strip()

    return raw, ""


def _compression_candidate_is_cluttered(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return False

    comma_count = raw.count(",")
    word_count = len(raw.split())
    has_using_span = " using " in raw.lower()
    has_result_clause = any(
        marker in raw.lower()
        for marker in [
            ", informing ",
            ", improving ",
            ", enabling ",
            ", resulting in ",
            ", leading to ",
            ", reducing ",
            ", increasing ",
            ", enhancing ",
            ", driving ",
        ]
    )

    return (
        word_count >= 22
        and comma_count >= 2
        and has_using_span
        and has_result_clause
    )


def _deterministic_using_coordination_cleanup_patch(
    diagnosis: Dict[str, Any],
) -> Optional[str]:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    if not original_text:
        return None

    intro, result_clause = _split_result_clause(original_text)
    if not intro or not result_clause:
        return None

    using_match = re.search(
        r"^(?P<lead>.+?\busing\b)\s+(?P<body>.+)$",
        intro,
        flags=re.IGNORECASE,
    )
    if not using_match:
        return None

    lead = str(using_match.group("lead") or "").strip()
    body = str(using_match.group("body") or "").strip()
    if not lead or not body:
        return None

    patched_body = body.replace(" & ", " and ")
    patched_body = re.sub(r"\band\s+and\b", "and", patched_body, flags=re.IGNORECASE)
    patched_body = re.sub(
        r",\s*and\s+(leveraging|using)\b",
        r", \1",
        patched_body,
        flags=re.IGNORECASE,
    )
    patched_body = re.sub(r"\s+", " ", patched_body).strip(" ,")

    patch_text = f"{lead} {patched_body}{result_clause}"
    patch_text = re.sub(r"\s+", " ", patch_text).strip()

    if _diagnosis_normalize_term(patch_text) == _diagnosis_normalize_term(original_text):
        return None

    if not _compression_patch_preserves_evidence(diagnosis, patch_text):
        return None

    return patch_text


def _deterministic_using_leveraging_cleanup_patch(
    diagnosis: Dict[str, Any],
) -> Optional[str]:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    if not original_text:
        return None

    intro, result_clause = _split_result_clause(original_text)
    if not intro or not result_clause:
        return None

    using_match = re.search(
        r"^(?P<lead>.+?\busing\b)\s+(?P<body>.+)$",
        intro,
        flags=re.IGNORECASE,
    )
    if not using_match:
        return None

    lead = str(using_match.group("lead") or "").strip()
    body = str(using_match.group("body") or "").strip()
    if not lead or not body:
        return None

    segments = [seg.strip(" ,") for seg in body.replace(" & ", " and ").split(",") if seg.strip(" ,")]
    if len(segments) != 2:
        return None

    first, second = segments
    if not re.match(r"^leveraging\b", second, flags=re.IGNORECASE):
        return None

    leveraged = re.sub(r"^leveraging\s+", "", second, flags=re.IGNORECASE).strip()
    if not leveraged:
        return None

    if re.match(
        r"^(hitting|improving|reducing|increasing|driving|informing|enabling|resulting|leading)\b",
        leveraged,
        flags=re.IGNORECASE,
    ):
        return None

    patch_text = f"{lead} {first}, {leveraged}{result_clause}"
    patch_text = re.sub(r"\s+", " ", patch_text).strip()

    if _diagnosis_normalize_term(patch_text) == _diagnosis_normalize_term(original_text):
        return None

    if not _compression_patch_preserves_evidence(diagnosis, patch_text):
        return None

    return patch_text


def _build_clarity_preserving_compression_patch(
    diagnosis: Dict[str, Any],
) -> Optional[str]:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    if not _compression_candidate_is_cluttered(original_text):
        return None

    intro, result_clause = _split_result_clause(original_text)
    if not intro or not result_clause:
        return None

    using_match = re.search(
        r"^(?P<lead>.+?\busing\b)\s+(?P<body>.+)$",
        intro,
        flags=re.IGNORECASE,
    )
    if not using_match:
        return None

    lead = str(using_match.group("lead") or "").strip()
    body = str(using_match.group("body") or "").strip()
    if not lead or not body:
        return None

    body = body.replace(" & ", ", ")
    body = re.sub(r"\s+", " ", body).strip()

    segments = [seg.strip(" ,") for seg in body.split(",") if seg.strip(" ,")]
    if len(segments) < 2:
        return None

    compact_body = ", ".join(segments[:-1])
    final_segment = re.sub(r"^(?:and\s+)+", "", segments[-1], flags=re.IGNORECASE).strip()

    gerund_like_tail = bool(
        re.match(
            r"^(leveraging|using|hitting|improving|reducing|increasing|driving|informing|enabling|resulting|leading)\b",
            final_segment,
            flags=re.IGNORECASE,
        )
    )

    if compact_body:
        joiner = ", " if gerund_like_tail else ", and "
        compressed_intro = f"{lead} {compact_body}{joiner}{final_segment}"
    else:
        compressed_intro = f"{lead} {final_segment}"

    patch_text = f"{compressed_intro}{result_clause}"
    patch_text = re.sub(r"\s+", " ", patch_text).strip()

    if _diagnosis_normalize_term(patch_text) == _diagnosis_normalize_term(original_text):
        return None

    return patch_text


def _compression_patch_preserves_evidence(
    diagnosis: Dict[str, Any],
    patch_text: str,
) -> bool:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    patched_text = str(patch_text or "").strip()

    if not original_text or not patched_text:
        return False

    original_norm = _diagnosis_normalize_term(original_text)
    patched_norm = _diagnosis_normalize_term(patched_text)

    if not original_norm or not patched_norm:
        return False

    if original_norm == patched_norm:
        return False

    def _contains_term_or_alias_local(text: str, term: str) -> bool:
        text_norm = _diagnosis_normalize_term(text)
        raw_term = str(term or "").strip()
        if not text_norm or not raw_term:
            return False

        variants = _unique_preserve_order(
            [raw_term] + list(expandable_aliases_for_supported_term(raw_term))
        )

        for variant in variants:
            variant_norm = _diagnosis_normalize_term(variant)
            if variant_norm and variant_norm in text_norm:
                return True

        return False

    # 1) Preserve all numeric evidence exactly.
    original_numbers = re.findall(
        r"\b\d+(?:\.\d+)?(?:k|m)?\+?%?\b",
        original_text,
        flags=re.IGNORECASE,
    )
    for token in _unique_preserve_order([str(item).strip() for item in original_numbers if str(item).strip()]):
        if token.lower() not in patched_text.lower():
            return False

    # 2) Preserve supported JD signals / canonical signal, allowing alias equivalence.
    supported_terms = _unique_preserve_order(
        [
            str(item).strip()
            for item in (
                list(diagnosis.get("jd_signal_terms", []) or [])
                + [str(diagnosis.get("canonical_supported_signal", "") or "").strip()]
            )
            if str(item).strip()
        ]
    )
    for term in supported_terms:
        if not _contains_term_or_alias_local(patched_text, term):
            return False

    # 3) Preserve important capitalized / acronym technical tokens from the original.
    raw_tokens = re.findall(
        r"\b(?:[A-Z]{2,}[A-Za-z0-9.+/\-]*|[A-Z][A-Za-z0-9.+/\-]{2,})\b",
        original_text,
    )
    protected_core_terms = _unique_preserve_order(
        [
            str(token).strip()
            for token in raw_tokens
            if str(token).strip() and str(token).strip().lower() not in _ACTION_VERB_HINTS_LOWER
        ]
    )

    def _protected_token_preserved(term: str) -> bool:
        term_norm = _diagnosis_normalize_term(term)
        if not term_norm:
            return False

        if term_norm in patched_norm:
            return True

        if term_norm.endswith("-based"):
            base_term_norm = _diagnosis_normalize_term(term_norm[:-6])
            if base_term_norm and base_term_norm in patched_norm:
                return True

        return False

    for term in protected_core_terms:
        if not _protected_token_preserved(term):
            return False

    # 4) Preserve the result clause verbatim in normalized form.
    _, original_result_clause = _split_result_clause(original_text)
    _, patched_result_clause = _split_result_clause(patched_text)

    original_result_norm = _diagnosis_normalize_term(original_result_clause)
    patched_result_norm = _diagnosis_normalize_term(patched_result_clause)

    if original_result_norm:
        if not patched_result_norm:
            return False
        if original_result_norm != patched_result_norm:
            return False

    return True


def _deterministic_clarity_preserving_compression_patch(
    diagnosis: Dict[str, Any],
) -> Optional[str]:
    patch_text = _build_clarity_preserving_compression_patch(diagnosis)
    if not patch_text:
        return None

    if not _compression_patch_preserves_evidence(diagnosis, patch_text):
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
    if _family_already_explicit_in_text(original_text, supported_family):
        return None

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

def _supported_term_already_salient_early(
    text: str,
    supported_terms: List[str],
    max_word_index: int = 2,
    max_char_index: int = 18,
) -> bool:
    raw_text = str(text or "").strip()
    if not raw_text:
        return False

    normalized_terms = [
        _diagnosis_normalize_term(term)
        for term in (supported_terms or [])
        if _diagnosis_normalize_term(term)
    ]
    if not normalized_terms:
        return False

    lower_text = raw_text.lower()

    earliest_word_index: Optional[int] = None
    earliest_char_index: Optional[int] = None

    for term in normalized_terms:
        char_index = lower_text.find(term.lower())
        if char_index < 0:
            continue

        word_index = len(re.findall(r"\S+", raw_text[:char_index]))

        if earliest_char_index is None or char_index < earliest_char_index:
            earliest_char_index = char_index

        if earliest_word_index is None or word_index < earliest_word_index:
            earliest_word_index = word_index

    if earliest_char_index is None or earliest_word_index is None:
        return False

    return (
        earliest_word_index <= max_word_index
        or earliest_char_index <= max_char_index
    )


def _family_already_explicit_in_text(
    text: str,
    family: str,
) -> bool:
    raw_text = str(text or "").strip()
    if not raw_text:
        return False

    normalized_text = _diagnosis_normalize_term(raw_text)
    family_terms = prioritized_family_terms_from_text(raw_text)

    for term in family_terms:
        if str(family_for_term(term) or "").strip() == family:
            return True

    if family == "analytics_ml":
        if any(token in normalized_text for token in [
            "machine learning",
            "ml ",
            " ml",
            "model ",
            "models",
            "supervised ml",
            "gradient boosting",
        ]):
            return True

    if family == "experimentation":
        if any(token in normalized_text for token in [
            "experiment",
            "experiments",
            "a/b",
            "ab test",
            "testing",
        ]):
            return True

    return False

def _all_supported_terms_already_salient_early(
    text: str,
    supported_terms: List[str],
) -> bool:
    normalized_supported = [
        _diagnosis_normalize_term(item)
        for item in (supported_terms or [])
        if _diagnosis_normalize_term(item)
    ]
    if not normalized_supported:
        return False

    return all(
        _supported_term_already_salient_early(text, [term])
        for term in normalized_supported
    )

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

    if len(normalized_supported) == 1:
        if _supported_term_already_salient_early(text, list(normalized_supported)):
            return None
    else:
        if _all_supported_terms_already_salient_early(text, list(normalized_supported)):
            return None

    using_pattern = re.compile(
        r"""
        \busing\s+
        (?P<phrase>
            .*?
        )
        (?=
            ,\s+(?:informing|enhancing|improving|ensuring|reducing|leveraging|driving|leading|resulting|enabling|achieving|revealing|uncovering|which|that)\b
            |[.;]
            |$
        )
        """,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    for match in using_pattern.finditer(text):
        phrase = str(match.group("phrase") or "").strip()
        phrase_norm = _diagnosis_normalize_term(phrase)
        if any(term in phrase_norm for term in normalized_supported):
            return match

    return None

def _deterministic_front_supported_phrase_patch(
    diagnosis: Dict[str, Any],
) -> Optional[str]:
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

    matched_surface_signal = _diagnosis_normalize_term(
        str(diagnosis.get("matched_surface_signal", "") or "").strip()
    )
    canonical_supported_signal = _diagnosis_normalize_term(
        str(diagnosis.get("canonical_supported_signal", "") or "").strip()
    )

    supported_targets = {
        term
        for term in [
            supported_terms[0],
            matched_surface_signal,
            canonical_supported_signal,
        ]
        if term
    }
    if not supported_targets:
        return None

    lead_match = re.match(r"^(?P<verb>[A-Za-z][A-Za-z-]+)\s+(?P<body>.+)$", original_text)
    if not lead_match:
        return None

    verb = str(lead_match.group("verb") or "").strip()
    body = str(lead_match.group("body") or "").strip()
    if not verb or not body:
        return None

    verb = verb[:1].upper() + verb[1:]

    tail_match = re.match(
        r"^(?P<head>.+?)(?P<tail>\s+(?:to|for|on|in|with|by|under|across|within|against|of)\b.*)?$",
        body,
        flags=re.IGNORECASE,
    )
    if tail_match:
        head = str(tail_match.group("head") or "").strip()
        tail = str(tail_match.group("tail") or "").rstrip()

        if head:
            parts = re.split(r"\s+and\s+", head, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) == 2:
                left = str(parts[0] or "").strip()
                right = str(parts[1] or "").strip()

                if left and right:
                    left_tokens = left.split()
                    right_tokens = right.split()

                    blocked_phrase_markers = {
                        "using",
                        "with",
                        "to",
                        "for",
                        "on",
                        "in",
                        "by",
                        "under",
                        "across",
                        "within",
                        "against",
                        "of",
                    }

                    if (
                        len(left_tokens) >= 2
                        and len(right_tokens) >= 2
                        and not any(token.lower() in blocked_phrase_markers for token in left_tokens)
                        and not any(token.lower() in blocked_phrase_markers for token in right_tokens)
                    ):
                        left_last = left_tokens[-1].lower()
                        right_last = right_tokens[-1].lower()

                        generic_heads = {
                            "experiment",
                            "experiments",
                            "test",
                            "tests",
                            "assessment",
                            "assessments",
                            "analysis",
                            "analyses",
                            "model",
                            "models",
                            "rule",
                            "rules",
                            "policy",
                            "policies",
                            "risk",
                            "risks",
                        }

                        left_norm = _diagnosis_normalize_term(left)
                        right_norm = _diagnosis_normalize_term(right)

                        left_has_supported = any(term in left_norm for term in supported_targets)
                        right_has_supported = any(term in right_norm for term in supported_targets)

                        if (
                            right_has_supported
                            and not left_has_supported
                            and left_last != right_last
                            and not (left_last in generic_heads and right_last in generic_heads)
                        ):
                            reordered_head = f"{right} and {left}".strip()
                            patch_text = f"{verb} {reordered_head}{tail}".strip()

                            if _diagnosis_normalize_term(patch_text) != _diagnosis_normalize_term(original_text):
                                return patch_text

    using_match = _using_phrase_match_for_supported_term(
        original_text,
        list(supported_targets),
    )
    if not using_match:
        return None

    phrase = re.sub(r"\s+", " ", str(using_match.group("phrase") or "").strip())
    if not phrase:
        return None

    parts = re.split(r"\s+and\s+", phrase, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return None

    left = str(parts[0] or "").strip(" ,")
    right = str(parts[1] or "").strip(" ,")
    if not left or not right:
        return None

    left_norm = _diagnosis_normalize_term(left)
    right_norm = _diagnosis_normalize_term(right)

    left_has_supported = any(term in left_norm for term in supported_targets)
    right_has_supported = any(term in right_norm for term in supported_targets)

    if left_has_supported or not right_has_supported:
        return None

    if len(left.split()) > 4 or len(right.split()) > 4:
        return None

    reordered_phrase = f"{right} and {left}"
    patch_text = (
        original_text[: using_match.start("phrase")]
        + reordered_phrase
        + original_text[using_match.end("phrase") :]
    )
    patch_text = re.sub(r"\s+", " ", patch_text).strip()
    patch_text = re.sub(r"\s+,", ",", patch_text)

    if _diagnosis_normalize_term(patch_text) == _diagnosis_normalize_term(original_text):
        return None

    return patch_text

def _deterministic_based_modifier_head_patch(
    diagnosis: Dict[str, Any],
) -> Optional[str]:
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

    supported_term = supported_terms[0]
    if _supported_term_already_salient_early(original_text, [supported_term]):
        return None

    intro, result_clause = _split_result_clause(original_text)
    if not intro:
        return None

    lead_match = re.match(
        r"^(?P<verb>[A-Za-z][A-Za-z-]+)\s+(?P<body>.+)$",
        intro,
    )
    if not lead_match:
        return None

    verb = str(lead_match.group("verb") or "").strip()
    body = str(lead_match.group("body") or "").strip()
    if not verb or not body:
        return None

    head_noun_pattern = (
        r"(?:models|model|forecasts|forecast|analyses|analysis|analytics|"
        r"pipelines|pipeline|frameworks|framework|systems|system|"
        r"assessments|assessment|strategies|strategy|workflows|workflow)"
    )

    match = re.search(
        rf"^(?P<method>[A-Za-z0-9.+/\-]+)-based\s+"
        rf"(?P<prefix>.*?)\b(?P<term>{re.escape(supported_term)})\b\s+"
        rf"(?P<head>{head_noun_pattern})(?P<suffix>.*)$",
        body,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    method = str(match.group("method") or "").strip()
    prefix = re.sub(r"\s+", " ", str(match.group("prefix") or "").strip())
    term_surface = str(match.group("term") or "").strip()
    head = str(match.group("head") or "").strip()
    suffix = re.sub(r"\s+", " ", str(match.group("suffix") or "").rstrip())

    if not method or not term_surface or not head:
        return None

    phrase_parts = [part for part in [prefix, term_surface, head] if part]
    rewritten_head = " ".join(phrase_parts).strip()
    if not rewritten_head:
        return None

    patch_intro = f"{verb} {rewritten_head}{suffix}".strip()
    patch_intro = re.sub(r"\s+", " ", patch_intro).strip()

    patch_text = f"{patch_intro} using {method}".strip()
    if result_clause:
        patch_text = f"{patch_text}{result_clause}"

    if _diagnosis_normalize_term(patch_text) == _diagnosis_normalize_term(original_text):
        return None

    if not _compression_patch_preserves_evidence(diagnosis, patch_text):
        return None

    return patch_text


def _using_phrase_supported_term_count(
    original_text: str,
    supported_terms: List[str],
) -> int:
    match = _using_phrase_match_for_supported_term(original_text, supported_terms)
    if not match:
        return 0

    phrase = str(match.group("phrase") or "").strip()
    phrase_norm = _diagnosis_normalize_term(phrase)

    normalized_supported = [
        _diagnosis_normalize_term(item)
        for item in (supported_terms or [])
        if _diagnosis_normalize_term(item)
    ]

    return sum(1 for term in normalized_supported if term in phrase_norm)

def _natural_join_terms(terms: List[str]) -> str:
    items = [
        str(item).strip()
        for item in (terms or [])
        if str(item).strip()
    ]
    items = _unique_preserve_order(items)

    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"

def _cleanup_using_phrase_segment(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    text = re.sub(r"^&\s*", "", text)
    return text.strip(" ,")


def _natural_join_surface_segments(segments: List[str]) -> str:
    items = [
        _cleanup_using_phrase_segment(item)
        for item in (segments or [])
        if _cleanup_using_phrase_segment(item)
    ]
    items = _unique_preserve_order(items)

    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _supported_using_phrase_segments(
    match: re.Match,
    supported_terms: List[str],
) -> List[str]:
    phrase = str(match.group("phrase") or "").strip()
    if not phrase:
        return []

    normalized_supported = [
        _diagnosis_normalize_term(item)
        for item in (supported_terms or [])
        if _diagnosis_normalize_term(item)
    ]
    if not normalized_supported:
        return []

    raw_segments = re.split(r"\s*,\s*", phrase)
    kept_segments: List[str] = []
    seen_supported = set()

    for raw_segment in raw_segments:
        segment = _cleanup_using_phrase_segment(raw_segment)
        if not segment:
            continue

        segment_norm = _diagnosis_normalize_term(segment)
        matched_terms = [
            term
            for term in normalized_supported
            if term in segment_norm and term not in seen_supported
        ]
        if not matched_terms:
            continue

        kept_segments.append(segment)
        seen_supported.update(matched_terms)

    if kept_segments:
        return kept_segments

    fallback_phrase = _cleanup_using_phrase_segment(phrase)
    return [fallback_phrase] if fallback_phrase else []

def _deterministic_lead_preserving_using_phrase_patch(
    diagnosis: Dict[str, Any],
    supported_terms: List[str],
    match: re.Match,
) -> Optional[str]:
    original_text = str(diagnosis.get("original_text", "") or "").strip()
    if not original_text:
        return None

    before = re.sub(r"\s+", " ", original_text[: match.start()].strip(" ,"))
    after_raw = original_text[match.end() :]

    if not before:
        return None

    surface_segments = _supported_using_phrase_segments(
        match,
        supported_terms,
    )
    phrase = _natural_join_surface_segments(surface_segments)
    if not phrase:
        phrase = str(match.group("phrase") or "").strip()

    phrase = re.sub(r"\s+", " ", str(phrase or "").strip())
    if not phrase:
        return None

    after_has_leading_comma = bool(re.match(r"^\s*,", str(after_raw or "")))
    after = re.sub(r"^\s*,\s*", "", str(after_raw or "").strip())
    after = re.sub(r"\s+", " ", after).strip()

    patch_text = f"{before} using {phrase}".strip()
    if after:
        patch_text = f"{patch_text}, {after}" if after_has_leading_comma else f"{patch_text} {after}"

    patch_text = re.sub(r"\s+", " ", patch_text)
    patch_text = re.sub(r"\s+,", ",", patch_text)
    patch_text = patch_text.rstrip(" .")

    if original_text.endswith("."):
        patch_text += "."

    if _diagnosis_normalize_term(patch_text) == _diagnosis_normalize_term(original_text):
        return None

    return patch_text

def _deterministic_patch_text_from_diagnosis(
    diagnosis: Dict[str, Any],
    adjacent_risk_signals: List[str],
    unsupported_risk_signals: List[str],
) -> Tuple[str, str, str, str]:
    claim_safety = str(diagnosis.get("claim_safety", "") or "").strip()
    confidence = _replacement_candidate_confidence(diagnosis)
    supported_terms = [
        str(item).strip()
        for item in (diagnosis.get("jd_signal_terms", []) or [])
        if str(item).strip()
    ]
    original_text = str(diagnosis.get("original_text", "") or "").strip()

    if claim_safety != "safe_strengthen":
        return "direction_only", "", "", "claim_safety_not_safe_strengthen"

    if confidence != "high":
        return "direction_only", "", "", "insufficient_confidence"

    if adjacent_risk_signals or unsupported_risk_signals:
        return "direction_only", "", "", "risk_signals_present"

    if not supported_terms:
        return "direction_only", "", "", "missing_supported_terms"

    # Keep the narrower single-signal operators exactly as they are.
    if len(supported_terms) == 1:
        clause_patch = _deterministic_clause_extract_patch(diagnosis)
        if clause_patch:
            return "patch_ready", clause_patch, "deterministic_clause_extract", ""

        exact_signal_patch = _deterministic_exact_signal_variant_patch(diagnosis)
        if exact_signal_patch:
            _, patch_text = exact_signal_patch
            return "patch_ready", patch_text, "deterministic_exact_signal_variant", ""
        
        front_supported_patch = _deterministic_front_supported_phrase_patch(diagnosis)
        if front_supported_patch:
            return "patch_ready", front_supported_patch, "deterministic_front_supported_phrase", ""
        
        based_modifier_patch = _deterministic_based_modifier_head_patch(diagnosis)
        if based_modifier_patch:
            return "patch_ready", based_modifier_patch, "deterministic_based_modifier_head", ""

        family_alias_patch = _deterministic_family_alias_expansion_patch(diagnosis)
        if family_alias_patch:
            return "direction_only", "", "deterministic_family_alias_expansion", "cosmetic_patch_not_exportable"

        supported_alias_patch = _deterministic_supported_alias_expansion_patch(diagnosis)
        if supported_alias_patch:
            return "direction_only", "", "deterministic_supported_alias_expansion", "cosmetic_patch_not_exportable"

        coordination_cleanup_patch = _deterministic_using_coordination_cleanup_patch(diagnosis)
        if coordination_cleanup_patch:
            return "direction_only", "", "deterministic_using_coordination_cleanup", "cosmetic_patch_not_exportable"

        leveraging_cleanup_patch = _deterministic_using_leveraging_cleanup_patch(diagnosis)
        if leveraging_cleanup_patch:
            return "direction_only", "", "deterministic_using_leveraging_cleanup", "cosmetic_patch_not_exportable"

        compression_patch = _deterministic_clarity_preserving_compression_patch(diagnosis)
        if compression_patch:
            return "direction_only", "", "deterministic_clarity_preserving_compression", "cosmetic_patch_not_exportable"

        parent_signal_patch = _deterministic_parent_signal_label_patch(diagnosis)
        if parent_signal_patch:
            _, patch_text = parent_signal_patch
            return "patch_ready", patch_text, "deterministic_parent_signal_label", ""

        if _supported_term_already_salient_early(original_text, supported_terms):
            return "direction_only", "", "", "single_signal_already_explicit_reorder_preferred"

    if len(supported_terms) >= 2 and _all_supported_terms_already_salient_early(
        original_text,
        supported_terms,
    ):
        return "direction_only", "", "", "multi_signal_already_explicit_reorder_preferred"
    
    # The current using-phrase operator is intentionally quarantined from exportable
    # patch generation because span surgery on multi-tool "using ..." bullets has shown
    # malformed outputs and no material lift in regression batches.

    supported_alias_patch = _deterministic_supported_alias_expansion_patch(diagnosis)
    if supported_alias_patch:
        return "direction_only", "", "deterministic_supported_alias_expansion", "cosmetic_patch_not_exportable"

    compression_patch = _deterministic_clarity_preserving_compression_patch(diagnosis)
    if compression_patch:
        return "direction_only", "", "deterministic_clarity_preserving_compression", "cosmetic_patch_not_exportable"

    return "direction_only", "", "", "deterministic_patch_not_available"
    
    
def _fronting_rewrite_counts_as_material_without_score_lift(
    candidate: Dict[str, Any],
    evidence_changed: bool,
) -> bool:
    if not evidence_changed:
        return False

    supported_jd_signals = [
        str(item).strip()
        for item in (candidate.get("supported_jd_signals", []) or [])
        if str(item).strip()
    ]
    if not supported_jd_signals:
        return False

    patch_generation_method = str(candidate.get("patch_generation_method", "") or "").strip()
    patch_generation_method_base = patch_generation_method.split("+", 1)[0].strip()

    signal_fronting_methods = {
        "deterministic_using_phrase",
        "deterministic_lead_preserving_using_phrase",
        "deterministic_front_supported_phrase",
        "deterministic_based_modifier_head",
        "deterministic_clause_extract",
        "deterministic_exact_signal_variant",
        "deterministic_family_alias_expansion",
        "deterministic_supported_alias_expansion",
        "deterministic_clarity_preserving_compression",
        "deterministic_fronted_using_phrase",
        "deterministic_using_coordination_cleanup",
        "deterministic_using_leveraging_cleanup",
        "llm_substantive_multisignal_reframe",
    }

    return patch_generation_method_base in signal_fronting_methods

def _fronting_rewrite_can_remain_patch_ready_without_evidence_delta(
    candidate: Dict[str, Any],
) -> bool:
    supported_jd_signals = [
        str(item).strip()
        for item in (candidate.get("supported_jd_signals", []) or [])
        if str(item).strip()
    ]
    if not supported_jd_signals:
        return False

    patch_generation_method = str(candidate.get("patch_generation_method", "") or "").strip()
    patch_generation_method_base = patch_generation_method.split("+", 1)[0].strip()

    return patch_generation_method_base in {
        "deterministic_using_phrase",
        "deterministic_lead_preserving_using_phrase",
        "deterministic_front_supported_phrase",
        "deterministic_clause_extract",
        "deterministic_based_modifier_head",
        "deterministic_exact_signal_variant",
        "deterministic_parent_signal_label",
        "deterministic_fronted_using_phrase",
        "llm_substantive_multisignal_reframe",
    }

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
        candidate["direction_only_reason"] = (
            str(candidate.get("direction_only_reason", "") or "").strip()
            or "materiality_prevalidation_failed"
        )
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
    patch_generation_method_base = patch_generation_method.split("+", 1)[0].strip()

    cosmetic_non_export_methods = {
        "deterministic_clarity_preserving_compression",
        "deterministic_family_alias_expansion",
        "deterministic_supported_alias_expansion",
        "deterministic_using_coordination_cleanup",
        "deterministic_using_leveraging_cleanup",
    }

    if patch_generation_method_base in cosmetic_non_export_methods:
        candidate["proposal_status"] = "direction_only"
        candidate["proposal_type"] = "directional_rewrite"
        candidate["direction_only_reason"] = (
            str(candidate.get("direction_only_reason", "") or "").strip()
            or "cosmetic_patch_not_exportable"
        )
        candidate["patch_ready"] = False
        candidate["material_delta_found"] = False
        candidate["materiality_validation_status"] = "cosmetic_patch_not_exportable"
        candidate["materiality_validation_note"] = (
            "This deterministic rewrite is cosmetic normalization only and is not exportable as a replacement bullet."
        )
        return candidate

    export_safe_neutral_methods = {
        "deterministic_clause_extract",
        "deterministic_exact_signal_variant",
        "deterministic_parent_signal_label",
        "deterministic_using_phrase",
        "deterministic_lead_preserving_using_phrase",
        "deterministic_based_modifier_head",
        "deterministic_front_supported_phrase",
        "deterministic_family_alias_expansion",
        "deterministic_fronted_using_phrase",
    }

    if overall_delta < 0.0:
        candidate["proposal_status"] = "direction_only"
        candidate["proposal_type"] = "directional_rewrite"
        candidate["direction_only_reason"] = (
            str(candidate.get("direction_only_reason", "") or "").strip()
            or "negative_projected_score_delta"
        )
        candidate["patch_ready"] = False
        candidate["material_delta_found"] = False
        candidate["materiality_validation_status"] = "negative_projected_score_delta"
        candidate["materiality_validation_note"] = (
            "Deterministic rewrite reduced the projected frozen score during counterfactual pre-validation, so it cannot remain patch-ready."
        )
        return candidate

    if overall_delta == 0.0 and not evidence_changed:
        if _fronting_rewrite_can_remain_patch_ready_without_evidence_delta(candidate):
            candidate["material_delta_found"] = False
            candidate["materiality_validation_status"] = "export_safe_no_score_lift"
            candidate["materiality_validation_note"] = (
                "Deterministic signal-fronting rewrite is grounded and patch-safe for export, but the scorer-visible evidence snapshot did not change and the frozen scorer shows no projected score lift."
            )
            return candidate

        candidate["proposal_status"] = "direction_only"
        candidate["proposal_type"] = "directional_rewrite"
        candidate["direction_only_reason"] = (
            str(candidate.get("direction_only_reason", "") or "").strip()
            or "scorer_neutral_no_evidence_change"
        )
        candidate["patch_ready"] = False
        candidate["material_delta_found"] = False
        candidate["materiality_validation_status"] = "scorer_neutral_no_evidence_change"
        candidate["materiality_validation_note"] = (
            "Deterministic rewrite changes phrasing only and does not change scorer-visible evidence, so it remains directional."
        )
        return candidate

    if overall_delta == 0.0 and _fronting_rewrite_counts_as_material_without_score_lift(
        candidate,
        evidence_changed,
    ):
        candidate["material_delta_found"] = True
        candidate["materiality_validation_status"] = "material_candidate"
        candidate["materiality_validation_note"] = (
            "Deterministic signal-fronting rewrite changed scorer-visible evidence and is treated as materially better even though the frozen scorer shows no projected score lift."
        )
        return candidate

    if overall_delta == 0.0 and patch_generation_method_base in export_safe_neutral_methods:
        candidate["material_delta_found"] = False
        candidate["materiality_validation_status"] = "export_safe_no_score_lift"
        candidate["materiality_validation_note"] = (
            "Deterministic rewrite is grounded and patch-safe for export, but the frozen scorer shows no projected score lift."
        )
        return candidate

    candidate["material_delta_found"] = True
    candidate["materiality_validation_status"] = "material_candidate"
    candidate["materiality_validation_note"] = (
        "Deterministic rewrite survived pre-validation as a scorer-material patch candidate."
    )
    return candidate

def _apply_post_refinement_export_gate(
    candidate: Dict[str, Any],
) -> Dict[str, Any]:
    if str(candidate.get("operation_type", "") or "").strip() != "rewrite":
        return candidate

    if str(candidate.get("llm_refinement_status", "") or "").strip() != "judge_selected_writer_option":
        if str(candidate.get("llm_refinement_status", "") or "").strip():
            candidate["llm_export_decision"] = str(candidate.get("llm_export_decision", "") or "deterministic_kept").strip()
        return candidate

    if str(candidate.get("materiality_validation_status", "") or "").strip() == "material_candidate":
        candidate["llm_export_decision"] = "writer_kept_material"
        return candidate

    baseline_patch_text = str(candidate.get("llm_pre_refinement_patch_text", "") or "").strip()
    baseline_method = str(candidate.get("llm_pre_refinement_patch_generation_method", "") or "").strip()
    baseline_status = str(candidate.get("llm_pre_refinement_materiality_validation_status", "") or "").strip()
    baseline_note = str(candidate.get("llm_pre_refinement_materiality_validation_note", "") or "").strip()

    if not baseline_patch_text:
        candidate["llm_export_decision"] = "writer_selected_nonmaterial_no_baseline_available"
        return candidate

    reverted = dict(candidate)

    reverted["llm_export_decision"] = "writer_selected_nonmaterial_reverted_to_deterministic"
    reverted["llm_shadow_selected_patch_text"] = str(candidate.get("patch_text", "") or "").strip()
    reverted["llm_shadow_selected_materiality_validation_status"] = str(candidate.get("materiality_validation_status", "") or "").strip()
    reverted["llm_shadow_selected_materiality_validation_note"] = str(candidate.get("materiality_validation_note", "") or "").strip()

    reverted["patch_text"] = baseline_patch_text
    reverted["proposed_text"] = baseline_patch_text
    reverted["patch_generation_method"] = baseline_method or str(candidate.get("patch_generation_method", "") or "").strip()

    reverted["materiality_validation_status"] = baseline_status or "material_candidate"
    reverted["materiality_validation_note"] = (
        baseline_note
        or "Writer-selected patch was kept for shadow evaluation only; shipped export reverted to the last scorer-material deterministic patch."
    )
    reverted["material_delta_found"] = True
    reverted["proposal_status"] = "patch_ready"
    reverted["proposal_type"] = "patch_ready_rewrite"

    reverted["precheck_projected_overall_delta"] = candidate.get(
        "llm_pre_refinement_precheck_projected_overall_delta"
    )
    reverted["precheck_projected_dimension_deltas"] = dict(
        candidate.get("llm_pre_refinement_precheck_projected_dimension_deltas", {}) or {}
    )
    reverted["precheck_scorer_visible_evidence_changed"] = bool(
        candidate.get("llm_pre_refinement_precheck_scorer_visible_evidence_changed", False)
    )
    reverted["precheck_evidence_delta"] = dict(
        candidate.get("llm_pre_refinement_precheck_evidence_delta", {}) or {}
    )

    return reverted

def _should_emit_reorder_companion(
    candidate: Dict[str, Any],
    patch_ready_rewrite_bullet_ids: set[str],
) -> bool:
    source_bullet_id = str(candidate.get("source_bullet_id", "") or "").strip()
    operation_type = str(candidate.get("operation_type", "") or "").strip()
    proposal_status = str(candidate.get("proposal_status", "") or "").strip()

    # If this bullet already has a real exportable rewrite, do not emit a reorder
    # shadow for the same bullet. Reorder adds no additional export value and only
    # creates duplicate operator clutter.
    if (
        source_bullet_id
        and operation_type == "rewrite"
        and proposal_status == "patch_ready"
        and source_bullet_id in patch_ready_rewrite_bullet_ids
    ):
        return False

    return _should_create_reorder_companion(candidate)

def _has_concrete_keep_anchor(candidate: Dict[str, Any]) -> bool:
    source_bullet_id = str(candidate.get("source_bullet_id", "") or "").strip()
    original_text = str(candidate.get("original_text", "") or "").strip()
    current_evidence = str(candidate.get("current_evidence", "") or "").strip()
    source = str(candidate.get("source", "") or "").strip()
    section = str(candidate.get("section", "") or "").strip()

    if not source_bullet_id:
        return False
    if not (original_text or current_evidence):
        return False
    if not (source or section):
        return False

    supported_terms = [
        str(item).strip()
        for item in (candidate.get("supported_jd_signals", []) or [])
        if str(item).strip()
    ]
    claim_safety = str(candidate.get("claim_safety", "") or "").strip()
    confidence = str(candidate.get("confidence", "") or "").strip()

    evidence_text = current_evidence or original_text
    word_count = len(re.findall(r"\S+", evidence_text))

    # Strong surfaced anchors should stay.
    if supported_terms:
        return True

    # Zero-signal adjacent-only low-confidence keeps are operator noise, not real anchors.
    if claim_safety == "adjacent_only" and confidence == "low":
        return False

    # Drop obvious fragment/noise rows even if metadata exists.
    if word_count < 6:
        return False

    return True

def _build_replacement_candidates(
    payload: Dict[str, Any],
    bullet_diagnoses: List[Dict[str, Any]],
    llm_output: Optional[Dict[str, Any]] = None,
    limit: int = 12,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    seen_keys = set()
    counterfactual_context = _counterfactual_context_from_payload(payload)
    curated_rewrite_keys = _curated_rewrite_candidate_key_set(payload)
    
    # Pass 1: primary candidates from diagnoses
    for index, diagnosis in enumerate(bullet_diagnoses, start=1):
        action = str(diagnosis.get("diagnosis_action", "") or "").strip()
        key = _bullet_diagnosis_key(diagnosis)

        if action == "rewrite":
            if curated_rewrite_keys:
                curated_key = _curated_rewrite_candidate_key_from_diagnosis(diagnosis)
                if curated_key not in curated_rewrite_keys:
                    continue

            if key in seen_keys:
                continue
            seen_keys.add(key)

            merge_anchors = _merge_anchor_candidates_for_diagnosis(
                diagnosis,
                candidates,
            )
            if merge_anchors:
                candidate = _diagnosis_to_merge_candidate(
                    diagnosis,
                    index,
                    merge_anchors,
                )
                candidates.append(candidate)
            else:
                suppress_anchors = _suppress_anchor_candidates_for_diagnosis(
                    diagnosis,
                    candidates,
                )
                if suppress_anchors:
                    candidate = _diagnosis_to_suppress_candidate(
                        diagnosis,
                        index,
                        suppress_anchors,
                    )
                    candidates.append(candidate)
                else:
                    candidate = _diagnosis_to_replacement_candidate(payload, diagnosis, index)

                    from src.tailoring.llm import _maybe_promote_multisignal_directional_candidate
                    candidate = _maybe_promote_multisignal_directional_candidate(
                        payload,
                        candidate,
                    )

                    candidate = _materiality_validate_rewrite_candidate(
                        payload,
                        candidate,
                        counterfactual_context,
                    )

                    patch_method_base = str(candidate.get("patch_generation_method", "") or "").strip().split("+", 1)[0].strip()
                    skip_llm_refinement_methods = {
                        "deterministic_family_alias_expansion",
                        "deterministic_supported_alias_expansion",
                    }
                    if (
                        str(candidate.get("operation_type", "") or "").strip() == "rewrite"
                        and str(candidate.get("proposal_status", "") or "").strip() == "patch_ready"
                        and str(candidate.get("materiality_validation_status", "") or "").strip() == "material_candidate"
                        and patch_method_base not in skip_llm_refinement_methods
                        and patch_method_base != "llm_substantive_multisignal_reframe"
                    ):
                        from src.tailoring.llm import _maybe_refine_patch_ready_rewrite_candidate
                        candidate = _maybe_refine_patch_ready_rewrite_candidate(
                            payload,
                            candidate,
                        )
                        candidate = _materiality_validate_rewrite_candidate(
                            payload,
                            candidate,
                            counterfactual_context,
                        )
                        candidate = _apply_post_refinement_export_gate(candidate)
                        
                    candidates.append(candidate)

        elif action == "keep":
            keep_key = ("keep",) + key
            if keep_key not in seen_keys:
                keep_candidate = _diagnosis_to_keep_candidate(diagnosis, index)
                keep_candidate = _normalize_keep_candidate_for_existing_anchor(
                    keep_candidate
                )

                if not _has_concrete_keep_anchor(keep_candidate):
                    continue

                seen_keys.add(keep_key)
                candidates.append(keep_candidate)

                reorder_key = ("reorder",) + key
                if (
                    len(candidates) < limit
                    and reorder_key not in seen_keys
                    and _should_create_reorder_candidate(diagnosis)
                ):
                    reorder_candidate = _diagnosis_to_reorder_candidate(diagnosis, index)
                    seen_keys.add(reorder_key)
                    candidates.append(reorder_candidate)

        if len(candidates) >= limit:
            break

    # Pass 2: reorder companions only when the bullet does not already have a
    # grounded patch-ready rewrite. Otherwise reorder is just duplicate noise.
    patch_ready_rewrite_bullet_ids = {
        str(row.get("source_bullet_id", "") or "").strip()
        for row in candidates
        if (
            str(row.get("operation_type", "") or "").strip() == "rewrite"
            and str(row.get("proposal_status", "") or "").strip() == "patch_ready"
            and str(row.get("source_bullet_id", "") or "").strip()
        )
    }

    expanded: List[Dict[str, Any]] = []
    for candidate in candidates:
        expanded.append(candidate)

        if len(expanded) >= limit:
            continue

        if _should_emit_reorder_companion(candidate, patch_ready_rewrite_bullet_ids):
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
    return any([
        _deterministic_clause_extract_patch(diagnosis) is not None,
        _deterministic_exact_signal_variant_patch(diagnosis) is not None,
        _deterministic_parent_signal_label_patch(diagnosis) is not None,
        _deterministic_front_supported_phrase_patch(diagnosis) is not None,
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
        diagnosis = _normalize_reinforce_context_diagnosis(diagnosis)
        diagnosis = _normalize_direct_overlap_rewrite_diagnosis(packet, diagnosis)

        key = _bullet_diagnosis_dedupe_key(diagnosis)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        if (
            str(diagnosis.get("diagnosis_action", "") or "").strip() == "rewrite"
            and _is_parent_signal_material_rewrite_diagnosis(diagnosis)
        ):
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
        key = _bullet_diagnosis_dedupe_key(diagnosis)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        diagnoses.append(diagnosis)
        if len(diagnoses) >= limit:
            break

    return diagnoses

def _keep_style_edit_type_from_diagnosis_reason(reason_type: str) -> str:
    reason = str(reason_type or "").strip()
    if reason == "keep_context_anchor":
        return "supporting_context"
    return "keep_visible"


def _align_edit_card_with_final_diagnosis(
    card: Dict[str, Any],
    diagnosis: Dict[str, Any],
) -> Dict[str, Any]:
    reason_type = str(diagnosis.get("diagnosis_reason_type", "") or "").strip()
    if reason_type not in {"keep_existing_anchor", "keep_context_anchor"}:
        return card

    aligned = dict(card)
    aligned["final_diagnosis_action"] = str(diagnosis.get("diagnosis_action", "") or "").strip()
    aligned["final_diagnosis_reason_type"] = reason_type
    aligned["edit_type"] = _keep_style_edit_type_from_diagnosis_reason(reason_type)
    aligned["claim_safety"] = "keep_visible"
    aligned["recommended_rewrite"] = ""
    aligned["why_current_is_weak"] = ""
    aligned["why_rewrite_is_better"] = ""
    aligned["why_it_matters"] = (
        str(diagnosis.get("why", "") or "").strip()
        or str(card.get("why_it_matters", "") or "").strip()
    )
    aligned["placement_guidance"] = (
        str(diagnosis.get("placement_guidance", "") or "").strip()
        or str(card.get("placement_guidance", "") or "").strip()
    )

    return aligned


def _align_edit_cards_with_final_diagnoses(
    edit_cards: List[Dict[str, Any]],
    bullet_diagnoses: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    diagnosis_by_key: Dict[tuple, Dict[str, Any]] = {}

    for diagnosis in bullet_diagnoses or []:
        key = _bullet_diagnosis_key(diagnosis)
        diagnosis_by_key[key] = diagnosis

    aligned_cards: List[Dict[str, Any]] = []

    for card in edit_cards or []:
        key = _bullet_diagnosis_key(
            {
                "bullet_id": str(card.get("bullet_id", "") or "").strip(),
                "section": str(card.get("section", "") or "").strip(),
                "source": str(card.get("source", "") or "").strip(),
                "current_evidence": str(card.get("current_evidence", "") or "").strip(),
            }
        )
        diagnosis = diagnosis_by_key.get(key)
        if diagnosis is None:
            aligned_cards.append(card)
            continue

        aligned_cards.append(_align_edit_card_with_final_diagnosis(card, diagnosis))

    return aligned_cards

def _apply_rewrite_review_state_to_edit_cards(
    edit_cards: List[Dict[str, Any]],
    payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    decision_lookup = _rewrite_review_decisions_by_candidate_id(payload)
    output: List[Dict[str, Any]] = []

    for card in (edit_cards or []):
        updated = dict(card)
        replacement_candidate_id = str(updated.get("replacement_candidate_id", "") or "").strip()

        decision = decision_lookup.get(
            replacement_candidate_id,
            {"state": "pending", "note": ""},
        )
        review_state = str(decision.get("state", "") or "pending").strip()
        review_note = str(decision.get("note", "") or "").strip()

        updated["review_state"] = review_state
        updated["review_state_display_label"] = _rewrite_review_state_display_label(review_state)
        updated["review_note"] = review_note

        output.append(updated)

    return output

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

    backend_edit_card_limit = max(
        12,
        len(operator_payload.get("rewrite_candidates", []) or []),
        len(operator_payload.get("bullet_reuse_candidates", []) or []),
    )

    initial_edit_cards = _build_edit_cards(
        operator_payload,
        preferred_rewrite_directions,
        limit=backend_edit_card_limit,
    )

    bullet_diagnoses = _build_bullet_diagnoses(
        operator_payload,
        initial_edit_cards,
        operator_payload.get("keep_as_is", []) or [],
    )

    operator_payload["bullet_diagnoses"] = bullet_diagnoses

    operator_payload["replacement_candidates"] = _build_replacement_candidates(
        operator_payload,
        bullet_diagnoses,
        llm_output=llm_output,
    )
    operator_payload["replacement_candidates"] = _apply_single_candidate_counterfactuals(
        operator_payload,
        operator_payload.get("replacement_candidates", []) or [],
    )

    edit_cards = _build_edit_cards(
        operator_payload,
        preferred_rewrite_directions,
        limit=backend_edit_card_limit,
    )

    edit_cards = _align_edit_cards_with_final_diagnoses(
        edit_cards,
        bullet_diagnoses,
    )

    edit_cards = _rank_and_suppress_edit_cards(
        edit_cards,
        limit=5,
    )

    actionable_edit_cards, anchor_cards = _split_actionable_and_anchor_cards(
        edit_cards,
        action_limit=5,
        anchor_limit=5,
    )

    operator_payload["edit_cards"] = _apply_rewrite_review_state_to_edit_cards(
        actionable_edit_cards,
        operator_payload,
    )
    operator_payload["anchor_cards"] = anchor_cards

    final_bullet_diagnoses = _build_bullet_diagnoses(
        operator_payload,
        actionable_edit_cards,
        operator_payload.get("keep_as_is", []) or [],
    )
    operator_payload["bullet_diagnoses"] = final_bullet_diagnoses

    from src.tailoring.replacement_selector import build_final_replacement_plan

    final_replacement_plan = build_final_replacement_plan(
        operator_payload.get("replacement_candidates", []) or [],
        actionable_edit_cards,
    )

    operator_payload["final_replacement_decisions"] = final_replacement_plan.get("decisions", [])
    operator_payload["app_ready_replacements"] = final_replacement_plan.get("app_ready_replacements", [])
    operator_payload["direct_apply_optional_replacements"] = final_replacement_plan.get("direct_apply_optional_replacements", [])
    operator_payload["ai_optimize_optional_replacements"] = final_replacement_plan.get("ai_optimize_optional_replacements", [])
    operator_payload["direction_only_replacements"] = final_replacement_plan.get("direction_only_replacements", [])
    operator_payload["final_replacement_summary"] = final_replacement_plan.get("summary", {})
    operator_payload["rewrite_review_decisions"] = dict(
        payload.get("rewrite_review_decisions", {}) or {}
    )
    operator_payload["rewrite_review_telemetry"] = dict(
        payload.get("rewrite_review_telemetry", {}) or {}
    )
    operator_payload["rewrite_review_groups"] = _build_rewrite_review_groups(operator_payload)
    operator_payload["rewrite_review_summary"] = _build_rewrite_review_summary(
        operator_payload.get("rewrite_review_groups", []) or [],
        workspace_review_telemetry=operator_payload.get("rewrite_review_telemetry", {}) or {},
    )
    operator_payload["rewrite_review_filters"] = _build_rewrite_review_filters(
        operator_payload.get("rewrite_review_groups", []) or []
    )
    operator_payload["rewrite_review_presets"] = _build_rewrite_review_presets(
        operator_payload.get("rewrite_review_groups", []) or []
    )
    operator_payload["rewrite_review_defaults"] = _build_rewrite_review_defaults(
        operator_payload.get("rewrite_review_summary", {}) or {},
        operator_payload.get("rewrite_review_filters", {}) or {},
        operator_payload.get("rewrite_review_presets", []) or [],
    )
    operator_payload["top_edit_priorities"] = _build_top_edit_priorities(actionable_edit_cards)
    operator_payload["top_anchor_priorities"] = _build_top_edit_priorities(anchor_cards)

    operator_payload["patch_set_counterfactual_preview"] = _apply_patch_set_counterfactual_preview(
        operator_payload,
        operator_payload.get("replacement_candidates", []) or [],
    )

    selected_patch_candidate_ids = list(payload.get("selected_patch_candidate_ids", []) or [])
    if selected_patch_candidate_ids:
        operator_payload["selected_patch_candidate_ids"] = selected_patch_candidate_ids
        operator_payload["selected_patch_set_counterfactual_preview"] = _apply_patch_set_counterfactual_preview(
            operator_payload,
            operator_payload.get("replacement_candidates", []) or [],
            selected_candidate_ids=selected_patch_candidate_ids,
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
        "job_snapshot": dict(packet.get("job_snapshot", {}) or {}),
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

def _rewrite_idea_card_lookup(payload: Dict[str, Any]) -> Dict[tuple, Dict[str, Any]]:
    lookup: Dict[tuple, Dict[str, Any]] = {}

    for card in (payload.get("edit_cards", []) or []):
        if str(card.get("edit_type", "") or "").strip() != "rewrite":
            continue

        recommended_rewrite = str(card.get("recommended_rewrite", "") or "").strip()
        if not recommended_rewrite:
            continue

        key = _replacement_candidate_lookup_key(
            {
                "bullet_id": card.get("bullet_id", ""),
                "source_bullet_id": card.get("source_bullet_id", ""),
                "entry_id": card.get("entry_id", ""),
                "source_entry_id": card.get("source_entry_id", ""),
                "section": card.get("section", ""),
                "source": card.get("source", ""),
                "current_evidence": card.get("current_evidence", "") or card.get("parent_bullet", ""),
                "parent_bullet": card.get("parent_bullet", ""),
                "bullet_excerpt": card.get("current_evidence", "") or card.get("parent_bullet", ""),
                "original_text": card.get("original_text", "") or card.get("current_evidence", "") or card.get("parent_bullet", ""),
            }
        )

        existing = lookup.get(key)

        def _rank(item: Dict[str, Any]) -> tuple:
            return (
                1 if str(item.get("replacement_candidate_id", "") or "").strip() else 0,
                1 if str(item.get("patch_generation_method", "") or "").strip() else 0,
                len(str(item.get("recommended_rewrite", "") or "").strip()),
            )

        if existing is None or _rank(card) > _rank(existing):
            lookup[key] = card

    return lookup


def _rewrite_idea_override_card(
    payload: Dict[str, Any],
    rewrite_candidate: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    lookup = _rewrite_idea_card_lookup(payload)

    key = _replacement_candidate_lookup_key(
        {
            "bullet_id": rewrite_candidate.get("bullet_id", ""),
            "source_bullet_id": rewrite_candidate.get("source_bullet_id", ""),
            "entry_id": rewrite_candidate.get("entry_id", ""),
            "source_entry_id": rewrite_candidate.get("source_entry_id", ""),
            "section": rewrite_candidate.get("section", ""),
            "source": rewrite_candidate.get("source", ""),
            "current_evidence": rewrite_candidate.get("bullet_excerpt", "") or rewrite_candidate.get("current_evidence", "") or rewrite_candidate.get("parent_bullet", ""), 
            "parent_bullet": rewrite_candidate.get("parent_bullet", ""),
            "bullet_excerpt": rewrite_candidate.get("bullet_excerpt", ""),
            "original_text": rewrite_candidate.get("original_text", "") or rewrite_candidate.get("bullet_excerpt", "") or rewrite_candidate.get("current_evidence", "") or rewrite_candidate.get("parent_bullet", ""),
        }
    )

    return lookup.get(key)

def _rewrite_review_card_lookup_by_candidate_id(
    payload: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}

    def _text(value: Any) -> str:
        return str(value or "").strip()

    def _norm(value: Any) -> str:
        return _diagnosis_normalize_term(_text(value))

    def _canonical_bullet(item: Dict[str, Any]) -> str:
        values = [
            _text(item.get("parent_bullet", "")),
            _text(item.get("current_evidence", "")),
            _text(item.get("original_text", "")),
        ]
        values = [value for value in values if value]
        if not values:
            return ""
        return max(values, key=len)

    def _rank(item: Dict[str, Any]) -> tuple:
        parent_bullet = _text(item.get("parent_bullet", ""))
        current_evidence = _text(item.get("current_evidence", ""))
        original_text = _text(item.get("original_text", ""))
        canonical_bullet = _canonical_bullet(item)

        parent_norm = _norm(parent_bullet)
        current_norm = _norm(current_evidence)
        original_norm = _norm(original_text)
        canonical_norm = _norm(canonical_bullet)

        # Prefer cards whose bullet provenance is internally consistent.
        current_matches_canonical = 1 if canonical_norm and current_norm == canonical_norm else 0
        original_matches_canonical = 1 if canonical_norm and original_norm == canonical_norm else 0
        parent_matches_canonical = 1 if canonical_norm and parent_norm == canonical_norm else 0

        # Penalize obviously conflicting rows like:
        # original/current = bullet A, parent_bullet = unrelated bullet B
        conflicting_parent = (
            1
            if parent_norm
            and canonical_norm
            and parent_norm != canonical_norm
            and (current_norm == canonical_norm or original_norm == canonical_norm)
            else 0
        )

        return (
            1 if canonical_bullet else 0,
            parent_matches_canonical,
            current_matches_canonical,
            original_matches_canonical,
            0 if conflicting_parent else 1,
            len(canonical_bullet),
            1 if _text(item.get("replacement_candidate_id", "")) else 0,
            1 if _text(item.get("patch_generation_method", "")) else 0,
            1 if _text(item.get("outcome_label", "")) else 0,
            1 if _text(item.get("claim_safety", "")) else 0,
            1 if _text(item.get("placement_guidance", "")) else 0,
            len(_text(item.get("recommended_rewrite", ""))),
        )

    for card in (payload.get("edit_cards", []) or []):
        candidate_id = _text(card.get("replacement_candidate_id", ""))
        if not candidate_id:
            continue

        existing = lookup.get(candidate_id)
        if existing is None or _rank(card) > _rank(existing):
            lookup[candidate_id] = dict(card)

    return lookup


def _rewrite_outcome_display_label(value: str) -> str:
    key = str(value or "").strip()
    if not key:
        return ""
    return _REWRITE_OUTCOME_DISPLAY_LABELS.get(key, key.replace("_", " ").title())


def _rewrite_claim_safety_display_label(value: str) -> str:
    key = str(value or "").strip()
    if not key:
        return ""
    return _REWRITE_CLAIM_SAFETY_DISPLAY_LABELS.get(key, key.replace("_", " ").title())



def _rewrite_group_display_label(value: str) -> str:
    key = str(value or "").strip()
    if not key:
        return ""
    return _REWRITE_GROUP_DISPLAY_LABELS.get(key, key.replace("_", " ").title())

def _build_rewrite_review_filters(
    rewrite_review_groups: List[Dict[str, Any]],
) -> Dict[str, Any]:
    
    group_options: List[Dict[str, Any]] = []
    outcome_counts: Dict[str, int] = {}
    claim_safety_counts: Dict[str, int] = {}
    review_state_counts: Dict[str, int] = {}
    signal_counts: Dict[str, int] = {}

    for group in (rewrite_review_groups or []):
        group_id = str(group.get("group_id", "") or "").strip()
        title = str(group.get("title", "") or "").strip()
        items = list(group.get("items", []) or [])

        if group_id:
            group_options.append(
                {
                    "value": group_id,
                    "label": _rewrite_group_display_label(group_id),
                    "raw_label": title or group_id,
                    "count": len(items),
                }
            )

        for item in items:
            outcome_label = str(item.get("outcome_label", "") or "").strip()
            claim_safety = str(item.get("claim_safety", "") or "").strip()
            review_state = str(item.get("review_state", "") or "").strip()

            if outcome_label:
                outcome_counts[outcome_label] = outcome_counts.get(outcome_label, 0) + 1

            if claim_safety:
                claim_safety_counts[claim_safety] = claim_safety_counts.get(claim_safety, 0) + 1

            if review_state:
                review_state_counts[review_state] = review_state_counts.get(review_state, 0) + 1

            for signal in list(item.get("supported_jd_signals", []) or []):
                signal_text = str(signal or "").strip()
                if not signal_text:
                    continue
                signal_counts[signal_text] = signal_counts.get(signal_text, 0) + 1

    outcome_options = [
        {
            "value": key,
            "label": _rewrite_outcome_display_label(key),
            "raw_label": key,
            "count": value,
        }
        for key, value in sorted(outcome_counts.items(), key=lambda pair: (-pair[1], pair[0].lower()))
    ]

    claim_safety_options = [
        {
            "value": key,
            "label": _rewrite_claim_safety_display_label(key),
            "raw_label": key,
            "count": value,
        }
        for key, value in sorted(claim_safety_counts.items(), key=lambda pair: (-pair[1], pair[0].lower()))
    ]

    review_state_options = [
        {
            "value": key,
            "label": _rewrite_review_state_display_label(key),
            "raw_label": key,
            "count": value,
        }
        for key, value in sorted(
            review_state_counts.items(),
            key=lambda pair: (_rewrite_review_state_sort_rank(pair[0]), pair[0].lower()),
        )
    ]

    supported_signal_options = [
        {"value": key, "label": key, "count": value}
        for key, value in sorted(signal_counts.items(), key=lambda pair: (-pair[1], pair[0].lower()))
    ]

    return {
        "groups": group_options,
        "outcome_labels": outcome_options,
        "claim_safety": claim_safety_options,
        "review_states": review_state_options,
        "supported_signals": supported_signal_options,
    }

def _rewrite_review_preset_sort_key(row: Dict[str, Any]) -> tuple:
    preset_id = str(row.get("preset_id", "") or "").strip()

    priority = {
        "pending_review": 0,
        "best_now": 1,
        "safe_but_optional": 2,
        "direction_only": 3,
        "directly_supported": 4,
        "accepted": 5,
        "edited_after_accept": 6,
        "rejected": 7,
    }.get(preset_id, 50)

    label = str(row.get("label", "") or "").strip().lower()
    return (priority, label)

def _build_rewrite_review_presets(
    rewrite_review_groups: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    items = [
        item
        for group in (rewrite_review_groups or [])
        for item in list(group.get("items", []) or [])
    ]

    def _count(predicate) -> int:
        return sum(1 for item in items if predicate(item))

    all_signals = sorted(
        {
            str(signal).strip()
            for item in items
            for signal in list(item.get("supported_jd_signals", []) or [])
            if str(signal).strip()
        },
        key=lambda x: x.lower(),
    )

    presets: List[Dict[str, Any]] = [
        {
            "preset_id": "best_now",
            "label": "Best now",
            "count": _count(lambda item: str(item.get("bucket_id", "") or "").strip() == "high_confidence_rewrites"),
            "filters": {"groups": ["high_confidence_rewrites"]},
        },
        {
            "preset_id": "safe_but_optional",
            "label": "Safe but optional",
            "count": _count(lambda item: str(item.get("bucket_id", "") or "").strip() == "export_safe_rewrites"),
            "filters": {"groups": ["export_safe_rewrites"]},
        },
        {
            "preset_id": "direction_only",
            "label": "Direction only",
            "count": _count(lambda item: str(item.get("bucket_id", "") or "").strip() == "directional_only"),
            "filters": {"groups": ["directional_only"]},
        },
        {
            "preset_id": "directly_supported",
            "label": "Directly supported",
            "count": _count(lambda item: str(item.get("claim_safety", "") or "").strip() == "safe_strengthen"),
            "filters": {"claim_safety": ["safe_strengthen"]},
        },
        {
            "preset_id": "pending_review",
            "label": "Pending review",
            "count": _count(lambda item: str(item.get("review_state", "") or "").strip() == "pending"),
            "filters": {"review_states": ["pending"]},
        },
        {
            "preset_id": "accepted",
            "label": "Accepted",
            "count": _count(lambda item: str(item.get("review_state", "") or "").strip() == "accepted"),
            "filters": {"review_states": ["accepted"]},
        },
        {
            "preset_id": "rejected",
            "label": "Rejected",
            "count": _count(lambda item: str(item.get("review_state", "") or "").strip() == "rejected"),
            "filters": {"review_states": ["rejected"]},
        },
        {
            "preset_id": "edited_after_accept",
            "label": "Edited after accept",
            "count": _count(lambda item: str(item.get("review_state", "") or "").strip() == "edited_after_accept"),
            "filters": {"review_states": ["edited_after_accept"]},
        },
    ]

    for signal in all_signals[:8]:
        presets.append(
            {
                "preset_id": f"signal::{signal}",
                "label": signal,
                "count": _count(lambda item, s=signal: s in list(item.get("supported_jd_signals", []) or [])),
                "filters": {"supported_signals": [signal]},
            }
        )

    visible_presets = [
        preset for preset in presets
        if int(preset.get("count", 0) or 0) > 0
    ]
    return sorted(visible_presets, key=_rewrite_review_preset_sort_key)

def _build_rewrite_review_defaults(
    rewrite_review_summary: Dict[str, Any],
    rewrite_review_filters: Dict[str, Any],
    rewrite_review_presets: List[Dict[str, Any]],
) -> Dict[str, Any]:
    review_state_counts = dict(rewrite_review_summary.get("review_state_counts", {}) or {})
    preset_ids = [
        str(row.get("preset_id", "") or "").strip()
        for row in (rewrite_review_presets or [])
        if str(row.get("preset_id", "") or "").strip()
    ]

    if int(review_state_counts.get("pending", 0) or 0) > 0 and "pending_review" in preset_ids:
        default_preset_id = "pending_review"
    elif "best_now" in preset_ids:
        default_preset_id = "best_now"
    elif "accepted" in preset_ids:
        default_preset_id = "accepted"
    elif preset_ids:
        default_preset_id = preset_ids[0]
    else:
        default_preset_id = ""

    default_hidden_review_states: List[str] = []
    if int(review_state_counts.get("rejected", 0) or 0) > 0:
        default_hidden_review_states.append("rejected")

    review_state_options = list(rewrite_review_filters.get("review_states", []) or [])
    visible_review_states = [
        str(row.get("value", "") or "").strip()
        for row in review_state_options
        if str(row.get("value", "") or "").strip() and str(row.get("value", "") or "").strip() not in default_hidden_review_states
    ]

    return {
        "default_preset_id": default_preset_id,
        "default_hidden_review_states": default_hidden_review_states,
        "default_visible_review_states": visible_review_states,
    }

def _build_rewrite_review_summary(
    rewrite_review_groups: List[Dict[str, Any]],
    workspace_review_telemetry: Optional[Dict[str, Any]] = None,
    top_signal_limit: int = 8,
) -> Dict[str, Any]:
    group_counts: Dict[str, int] = {}
    outcome_label_counts: Dict[str, int] = {}
    claim_safety_counts: Dict[str, int] = {}
    review_state_counts: Dict[str, int] = {}
    signal_counts: Dict[str, int] = {}

    for group in (rewrite_review_groups or []):
        group_id = str(group.get("group_id", "") or "").strip()
        items = list(group.get("items", []) or [])

        if group_id:
            group_counts[group_id] = len(items)

        for item in items:
            outcome_label = str(item.get("outcome_label", "") or "").strip()
            claim_safety = str(item.get("claim_safety", "") or "").strip()
            review_state = str(item.get("review_state", "") or "").strip()

            if outcome_label:
                outcome_label_counts[outcome_label] = outcome_label_counts.get(outcome_label, 0) + 1

            if claim_safety:
                claim_safety_counts[claim_safety] = claim_safety_counts.get(claim_safety, 0) + 1

            if review_state:
                review_state_counts[review_state] = review_state_counts.get(review_state, 0) + 1

            for signal in list(item.get("supported_jd_signals", []) or []):
                signal_text = str(signal or "").strip()
                if not signal_text:
                    continue
                signal_counts[signal_text] = signal_counts.get(signal_text, 0) + 1

    top_supported_signals = [
        {"signal": signal, "count": count}
        for signal, count in sorted(
            signal_counts.items(),
            key=lambda pair: (-pair[1], pair[0].lower()),
        )[:top_signal_limit]
    ]

    telemetry = dict(workspace_review_telemetry or {})

    pending_count = int(
        telemetry.get("pending_count", review_state_counts.get("pending", 0)) or 0
    )
    accepted_as_is_count = int(
        telemetry.get("accepted_as_is_count", review_state_counts.get("accepted", 0)) or 0
    )
    edited_after_accept_count = int(
        telemetry.get("edited_after_accept_count", review_state_counts.get("edited_after_accept", 0)) or 0
    )
    rejected_count = int(
        telemetry.get("rejected_count", review_state_counts.get("rejected", 0)) or 0
    )
    accepted_count = int(
        telemetry.get(
            "accepted_count",
            accepted_as_is_count + edited_after_accept_count,
        ) or 0
    )
    reviewed_count = int(
        telemetry.get(
            "reviewed_count",
            accepted_count + rejected_count,
        ) or 0
    )
    remaining_to_review_count = int(
        telemetry.get("remaining_to_review_count", pending_count) or 0
    )
    selected_candidate_count = int(
        telemetry.get("selected_candidate_count", 0) or 0
    )
    manual_edit_count = int(
        telemetry.get("manual_edit_count", 0) or 0
    )

    reviewed_candidate_ids = [
        str(candidate_id or "").strip()
        for candidate_id in (telemetry.get("reviewed_candidate_ids", []) or [])
        if str(candidate_id or "").strip()
    ]
    pending_candidate_ids = [
        str(candidate_id or "").strip()
        for candidate_id in (telemetry.get("pending_candidate_ids", []) or [])
        if str(candidate_id or "").strip()
    ]

    return {
        "group_counts": group_counts,
        "outcome_label_counts": outcome_label_counts,
        "claim_safety_counts": claim_safety_counts,
        "review_state_counts": review_state_counts,
        "top_supported_signals": top_supported_signals,
        "pending_count": pending_count,
        "accepted_count": accepted_count,
        "accepted_as_is_count": accepted_as_is_count,
        "edited_after_accept_count": edited_after_accept_count,
        "rejected_count": rejected_count,
        "reviewed_count": reviewed_count,
        "remaining_to_review_count": remaining_to_review_count,
        "selected_candidate_count": selected_candidate_count,
        "manual_edit_count": manual_edit_count,
        "reviewed_candidate_ids": reviewed_candidate_ids,
        "pending_candidate_ids": pending_candidate_ids,
        "total_grouped_items": sum(group_counts.values()),
    }

def _rewrite_review_state_sort_rank(value: str) -> int:
    key = str(value or "").strip().lower()

    return {
        "accepted": 0,
        "edited_after_accept": 1,
        "pending": 2,
        "rejected": 3,
    }.get(key, 9)

def _rewrite_review_item_sort_key(item: Dict[str, Any]) -> tuple:
    apply_priority = str(item.get("apply_priority", "") or "").strip().lower()
    outcome_label = str(item.get("outcome_label", "") or "").strip().lower()
    claim_safety = str(item.get("claim_safety", "") or "").strip().lower()
    review_state = str(item.get("review_state", "") or "").strip().lower()

    priority_rank = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }.get(apply_priority, 9)

    outcome_rank = {
        "material_candidate": 0,
        "export_safe_no_score_lift": 1,
        "patch_ready": 2,
        "directional_only": 3,
        "cosmetic_only": 4,
    }.get(outcome_label, 9)

    claim_safety_rank = {
        "safe_strengthen": 0,
        "keep_visible": 1,
        "adjacent_only": 2,
        "safe_reorder": 3,
        "safe_merge": 4,
        "safe_suppress": 5,
    }.get(claim_safety, 9)

    review_state_rank = _rewrite_review_state_sort_rank(review_state)

    supported_signal_count = len(list(item.get("supported_jd_signals", []) or []))

    return (
        review_state_rank,
        priority_rank,
        outcome_rank,
        claim_safety_rank,
        -supported_signal_count,
        str(item.get("section", "") or "").strip().lower(),
        str(item.get("source", "") or "").strip().lower(),
        str(item.get("replacement_candidate_id", "") or "").strip().lower(),
        str(item.get("recommended_rewrite", "") or "").strip().lower(),
    )

def _rewrite_review_decisions_by_candidate_id(
    payload: Dict[str, Any],
) -> Dict[str, Dict[str, str]]:
    raw = payload.get("rewrite_review_decisions", {}) or {}
    if not isinstance(raw, dict):
        return {}

    normalized: Dict[str, Dict[str, str]] = {}

    for raw_key, raw_value in raw.items():
        candidate_id = str(raw_key or "").strip()
        if not candidate_id:
            continue

        if isinstance(raw_value, dict):
            state = str(raw_value.get("state", "") or "").strip().lower() or "pending"
            note = str(raw_value.get("note", "") or "").strip()
        else:
            state = str(raw_value or "").strip().lower() or "pending"
            note = ""

        normalized[candidate_id] = {
            "state": state,
            "note": note,
        }

    return normalized

def _build_rewrite_review_groups(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    app_ready_replacements = list(payload.get("app_ready_replacements", []) or [])
    direct_apply_optional_replacements = list(payload.get("direct_apply_optional_replacements", []) or [])
    ai_optimize_optional_replacements = list(payload.get("ai_optimize_optional_replacements", []) or [])
    direction_only_replacements = list(payload.get("direction_only_replacements", []) or [])
    card_lookup = _rewrite_review_card_lookup_by_candidate_id(payload)
    decision_lookup = _rewrite_review_decisions_by_candidate_id(payload)

    def _rewrite_group_item(row: Dict[str, Any], bucket_id: str) -> Dict[str, Any]:
        replacement_candidate_id = str(row.get("replacement_candidate_id", "") or "").strip()
        review_decision = decision_lookup.get(
            replacement_candidate_id,
            {"state": "pending", "note": ""},
        )
        review_state = str(review_decision.get("state", "") or "pending").strip()
        review_note = str(review_decision.get("note", "") or "").strip()
        override_card = card_lookup.get(replacement_candidate_id, {}) if replacement_candidate_id else {}

        supported_jd_signals = list(
            row.get("supported_jd_signals", []) or
            row.get("jd_signal_terms", []) or
            override_card.get("supported_jd_signals", []) or
            override_card.get("jd_signal_terms", []) or
            []
        )

        outcome_label = str(
            row.get("materiality_validation_status", "") or
            row.get("outcome_label", "") or
            override_card.get("outcome_label", "") or
            ""
        ).strip()

        outcome_reason = str(
            row.get("materiality_validation_note", "") or
            row.get("outcome_reason", "") or
            override_card.get("outcome_reason", "") or
            row.get("why_selected", "") or
            ""
        ).strip()

        claim_safety = str(
            row.get("claim_safety", "") or
            override_card.get("claim_safety", "") or
            ""
        ).strip()

        placement_guidance = str(
            row.get("placement_guidance", "") or
            override_card.get("placement_guidance", "") or
            ""
        ).strip()

        parent_bullet = str(
            override_card.get("parent_bullet", "") or
            row.get("parent_bullet", "") or
            ""
        ).strip()

        original_text = str(
            override_card.get("original_text", "") or
            row.get("original_text", "") or
            override_card.get("current_evidence", "") or
            row.get("current_evidence", "") or
            parent_bullet
        ).strip()

        current_evidence = str(
            override_card.get("current_evidence", "") or
            row.get("current_evidence", "") or
            override_card.get("original_text", "") or
            row.get("original_text", "") or
            parent_bullet
        ).strip()

        recommended_rewrite = str(
            row.get("final_replacement_text", "") or
            override_card.get("recommended_rewrite", "") or
            row.get("rewrite_direction", "") or
            ""
        ).strip()

        return {
            "bucket_id": bucket_id,
            "replacement_candidate_id": replacement_candidate_id,
            "section": str(row.get("section", "") or "").strip(),
            "source": str(row.get("source", "") or "").strip(),
            "original_text": original_text,
            "current_evidence": current_evidence,
            "parent_bullet": parent_bullet,
            "recommended_rewrite": recommended_rewrite,
            "supported_jd_signals": supported_jd_signals,
            "outcome_label": outcome_label,
            "outcome_reason": outcome_reason,
            "claim_safety": claim_safety,
            "placement_guidance": placement_guidance,
            "apply_priority": str(row.get("apply_priority", "") or "").strip(),
            "why_selected": str(row.get("why_selected", "") or "").strip(),
            "group_display_label": _rewrite_group_display_label(bucket_id),
            "outcome_display_label": _rewrite_outcome_display_label(outcome_label),
            "claim_safety_display_label": _rewrite_claim_safety_display_label(claim_safety),
            "review_state": review_state,
            "review_state_display_label": _rewrite_review_state_display_label(review_state),
            "review_note": review_note,
        }

    groups: List[Dict[str, Any]] = []

    if app_ready_replacements:
        groups.append(
            {
                "group_id": "high_confidence_rewrites",
                "title": "High-Confidence Rewrites",
                "description": "Grounded rewrites that are ready to apply now.",
                "items": sorted(
                    [
                        _rewrite_group_item(row, "high_confidence_rewrites")
                        for row in app_ready_replacements
                    ],
                    key=_rewrite_review_item_sort_key,
                ),
            }
        )

    if ai_optimize_optional_replacements:
        groups.append(
            {
                "group_id": "ai_optimize_optional",
                "title": "AI-Optimize Optional",
                "description": "AI-augmented exploratory rewrites that should stay optional and must not be treated like trusted Ready patches.",
                "items": sorted(
                    [
                        _rewrite_group_item(row, "ai_optimize_optional")
                        for row in ai_optimize_optional_replacements
                    ],
                    key=_rewrite_review_item_sort_key,
                ),
            }
        )

    if direct_apply_optional_replacements:
        groups.append(
            {
                "group_id": "export_safe_rewrites",
                "title": "Export-Safe Rewrites",
                "description": "Grounded rewrites that are safe to export but are not top-priority score-lift changes.",
                "items": sorted(
                    [
                        _rewrite_group_item(row, "export_safe_rewrites")
                        for row in direct_apply_optional_replacements
                    ],
                    key=_rewrite_review_item_sort_key,
                ),
            }
        )

    if direction_only_replacements:
        groups.append(
            {
                "group_id": "directional_only",
                "title": "Directional Only",
                "description": "Useful guidance, but not a grounded replacement bullet yet.",
                "items": sorted(
                    [
                        _rewrite_group_item(row, "directional_only")
                        for row in direction_only_replacements
                    ],
                    key=_rewrite_review_item_sort_key,
                ),
            }
        )

    return groups

def _ordered_rewrite_review_state_rows(counts: Dict[str, int]) -> List[tuple]:
    ordered_keys = [
        "pending",
        "accepted",
        "edited_after_accept",
        "rejected",
    ]

    rows: List[tuple] = []
    seen = set()

    for key in ordered_keys:
        if key in counts:
            rows.append((key, int(counts.get(key, 0) or 0)))
            seen.add(key)

    for key in sorted(counts.keys()):
        if key in seen:
            continue
        rows.append((key, int(counts.get(key, 0) or 0)))

    return rows

def _markdown_from_payload(payload: Dict[str, Any]) -> str:
    job = payload.get("job", {}) or {}
    selection = payload.get("selection", {}) or {}
    tailoring_plan = payload.get("tailoring_plan", {}) or {}
    top_edit_priorities = payload.get("top_edit_priorities", []) or []
    top_anchor_priorities = payload.get("top_anchor_priorities", []) or []
    edit_cards = payload.get("edit_cards", []) or []
    anchor_cards = payload.get("anchor_cards", []) or []
    keep_as_is = payload.get("keep_as_is", []) or []
    claim_safety_notes = payload.get("claim_safety_notes", {}) or {}
    material_gaps = payload.get("material_gaps", []) or []

    final_replacement_decisions = payload.get("final_replacement_decisions", []) or []
    app_ready_replacements = payload.get("app_ready_replacements", []) or []
    direct_apply_optional_replacements = payload.get("direct_apply_optional_replacements", []) or []
    direction_only_replacements = payload.get("direction_only_replacements", []) or []
    final_replacement_summary = payload.get("final_replacement_summary", {}) or {}
    rewrite_review_groups = payload.get("rewrite_review_groups", []) or []
    rewrite_review_summary = payload.get("rewrite_review_summary", {}) or {}
    rewrite_review_filters = payload.get("rewrite_review_filters", {}) or {}
    rewrite_review_presets = payload.get("rewrite_review_presets", []) or []
    rewrite_review_defaults = payload.get("rewrite_review_defaults", {}) or {}

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
    
    if top_anchor_priorities:
        lines.append("## Highest-Value Anchors")
        for index, item in enumerate(top_anchor_priorities, start=1):
            lines.append(
                f"### {index}. {str(item.get('priority', '')).title()} priority • "
                f"{str(item.get('edit_type', '')).replace('_', ' ').title()}"
            )
            if item.get("jd_signal"):
                lines.append(f"- JD signal: {item.get('jd_signal', '')}")
            if item.get("target_section"):
                lines.append(f"- Where to keep visible: {item.get('target_section', '')}")
            if item.get("why_it_matters"):
                lines.append(f"- Why this anchor matters: {item.get('why_it_matters', '')}")
            lines.append("")

    if final_replacement_summary:
        lines.append("## Final Replacement Summary")
        if final_replacement_summary.get("total_rewrite_bullets") is not None:
            lines.append(
                f"- Total rewrite-tracked bullets: {final_replacement_summary.get('total_rewrite_bullets', 0)}"
            )
        lines.append(
            f"- Direct apply ready: {final_replacement_summary.get('direct_apply_ready_count', 0)}"
        )
        lines.append(
            f"- Direct apply optional: {final_replacement_summary.get('direct_apply_optional_count', 0)}"
        )
        lines.append(
            f"- AI-optimize optional: {final_replacement_summary.get('ai_optimize_optional_count', 0)}"
        )
        lines.append(
            f"- Direction only: {final_replacement_summary.get('direction_only_count', 0)}"
        )
        lines.append(
            f"- Keep original: {final_replacement_summary.get('keep_original_count', 0)}"
        )
        lines.append("")

    if rewrite_review_summary:
        lines.append("## Rewrite Review Summary")

        group_counts = rewrite_review_summary.get("group_counts", {}) or {}
        outcome_label_counts = rewrite_review_summary.get("outcome_label_counts", {}) or {}
        claim_safety_counts = rewrite_review_summary.get("claim_safety_counts", {}) or {}
        review_state_counts = rewrite_review_summary.get("review_state_counts", {}) or {}
        top_supported_signals = rewrite_review_summary.get("top_supported_signals", []) or []

        pending_count = int(rewrite_review_summary.get("pending_count", 0) or 0)
        accepted_count = int(rewrite_review_summary.get("accepted_count", 0) or 0)
        accepted_as_is_count = int(rewrite_review_summary.get("accepted_as_is_count", 0) or 0)
        edited_after_accept_count = int(
            rewrite_review_summary.get("edited_after_accept_count", 0) or 0
        )
        rejected_count = int(rewrite_review_summary.get("rejected_count", 0) or 0)
        remaining_to_review_count = int(
            rewrite_review_summary.get("remaining_to_review_count", 0) or 0
        )
        reviewed_count = int(rewrite_review_summary.get("reviewed_count", 0) or 0)
        selected_candidate_count = int(
            rewrite_review_summary.get("selected_candidate_count", 0) or 0
        )
        manual_edit_count = int(
            rewrite_review_summary.get("manual_edit_count", 0) or 0
        )

        lines.append(f"- Remaining to review: {remaining_to_review_count}")
        lines.append(f"- Reviewed: {reviewed_count}")
        lines.append(f"- Accepted: {accepted_count}")
        lines.append(f"- Accepted as-is: {accepted_as_is_count}")
        lines.append(f"- Edited after accept: {edited_after_accept_count}")
        lines.append(f"- Rejected: {rejected_count}")
        lines.append(f"- Selected candidate count: {selected_candidate_count}")
        lines.append(f"- Manual edit count: {manual_edit_count}")

        if rewrite_review_summary.get("total_grouped_items") is not None:
            lines.append(
                f"- Total grouped rewrite items: {rewrite_review_summary.get('total_grouped_items', 0)}"
            )

        if group_counts:
            lines.append(
                f"- High-confidence rewrites: {group_counts.get('high_confidence_rewrites', 0)}"
            )
            lines.append(
                f"- Export-safe rewrites: {group_counts.get('export_safe_rewrites', 0)}"
            )
            lines.append(
                f"- AI-optimize optional: {group_counts.get('ai_optimize_optional', 0)}"
            )
            lines.append(
                f"- Directional only: {group_counts.get('directional_only', 0)}"
            )

        if outcome_label_counts:
            lines.append(
                "- Outcome labels: "
                + ", ".join(
                    f"{key}={value}"
                    for key, value in sorted(outcome_label_counts.items())
                )
            )

        if claim_safety_counts:
            lines.append(
                "- Claim safety: "
                + ", ".join(
                    f"{key}={value}"
                    for key, value in sorted(claim_safety_counts.items())
                )
            )

        if review_state_counts:
            lines.append(
                "- Review states: "
                + ", ".join(
                    f"{_rewrite_review_state_display_label(key)}={value}"
                    for key, value in _ordered_rewrite_review_state_rows(review_state_counts)
                )
            )

        if top_supported_signals:
            lines.append(
                "- Top supported signals: "
                + ", ".join(
                    f"{row.get('signal', '')} ({row.get('count', 0)})"
                    for row in top_supported_signals
                )
            )

        lines.append("")

    if rewrite_review_filters:
        lines.append("## Rewrite Review Filters")

        group_options = rewrite_review_filters.get("groups", []) or []
        outcome_options = rewrite_review_filters.get("outcome_labels", []) or []
        claim_safety_options = rewrite_review_filters.get("claim_safety", []) or []
        review_state_options = rewrite_review_filters.get("review_states", []) or []
        supported_signal_options = rewrite_review_filters.get("supported_signals", []) or []

        if group_options:
            lines.append(
                "- Groups: "
                + ", ".join(
                    f"{row.get('label', '')} ({row.get('count', 0)})"
                    for row in group_options
                )
            )

        if outcome_options:
            lines.append(
                "- Outcome labels: "
                + ", ".join(
                    f"{row.get('label', '')} ({row.get('count', 0)})"
                    for row in outcome_options
                )
            )

        if claim_safety_options:
            lines.append(
                "- Claim safety: "
                + ", ".join(
                    f"{row.get('label', '')} ({row.get('count', 0)})"
                    for row in claim_safety_options
                )
            )
        
        if review_state_options:
            lines.append(
                "- Review states: "
                + ", ".join(
                    f"{row.get('label', '')} ({row.get('count', 0)})"
                    for row in review_state_options
                )
            )

        if supported_signal_options:
            lines.append(
                "- Supported signals: "
                + ", ".join(
                    f"{row.get('label', '')} ({row.get('count', 0)})"
                    for row in supported_signal_options[:12]
                )
            )

        lines.append("")

    if rewrite_review_presets:
        lines.append("## Rewrite Review Presets")
        lines.append(
            "- Presets: "
            + ", ".join(
                f"{row.get('label', '')} ({row.get('count', 0)})"
                for row in rewrite_review_presets
            )
        )
        default_preset_id = str(rewrite_review_defaults.get("default_preset_id", "") or "").strip()
        default_hidden_review_states = list(
            rewrite_review_defaults.get("default_hidden_review_states", []) or []
        )

        if default_preset_id:
            matching = [
                row for row in rewrite_review_presets
                if str(row.get("preset_id", "") or "").strip() == default_preset_id
            ]
            if matching:
                lines.append(f"- Default preset: {matching[0].get('label', '')}")

        if default_hidden_review_states:
            lines.append(
                "- Default hidden review states: "
                + ", ".join(
                    _rewrite_review_state_display_label(value)
                    for value in default_hidden_review_states
                )
            )
        lines.append("")

    if rewrite_review_groups:
        lines.append("## Rewrite Review Buckets")
        lines.append("")

        for group in rewrite_review_groups:
            title = str(group.get("title", "") or "").strip()
            description = str(group.get("description", "") or "").strip()
            items = list(group.get("items", []) or [])

            lines.append(f"### {title} ({len(items)})")
            if description:
                lines.append(description)
            lines.append("")

            for index, row in enumerate(items, start=1):
                priority = str(row.get("apply_priority", "") or "").strip()
                priority_prefix = f"{priority.title()} priority · " if priority else ""
                lines.append(f"#### {index}. {priority_prefix}{title[:-1] if title.endswith('s') else title}")

                if row.get("section"):
                    lines.append(f"- Section: {row.get('section', '')}")
                if row.get("source"):
                    lines.append(f"- Source: {row.get('source', '')}")
                if row.get("supported_jd_signals"):
                    lines.append(
                        f"- Supported JD signals: {', '.join(row.get('supported_jd_signals', []) or [])}"
                    )
                if row.get("outcome_label"):
                    lines.append(f"- Outcome label: {row.get('outcome_label', '')}")
                if row.get("review_state_display_label"):
                    lines.append(f"- Review state: {row.get('review_state_display_label', '')}")
                if row.get("review_note"):
                    lines.append(f"- Review note: {row.get('review_note', '')}")
                if row.get("outcome_reason"):
                    lines.append(f"- Outcome reason: {row.get('outcome_reason', '')}")
                if row.get("original_text"):
                    lines.append("- Original text:")
                    lines.append(f"  > {row.get('original_text', '')}")
                if row.get("recommended_rewrite"):
                    if str(group.get("group_id", "") or "").strip() == "directional_only":
                        lines.append("- Recommended action:")
                    else:
                        lines.append("- Recommended rewrite:")
                    lines.append(f"  > {row.get('recommended_rewrite', '')}")
                if row.get("why_selected"):
                    lines.append(f"- Why selected: {row.get('why_selected', '')}")
                if row.get("placement_guidance"):
                    lines.append(f"- Placement guidance: {row.get('placement_guidance', '')}")
                lines.append("")

    if app_ready_replacements:
        lines.append("## Apply Now")
        for index, row in enumerate(app_ready_replacements, start=1):
            lines.append(
                f"### Apply {index} · {str(row.get('apply_priority', '')).title()} priority · Direct Apply Ready"
            )
            if row.get("section"):
                lines.append(f"- Section: {row.get('section', '')}")
            if row.get("source"):
                lines.append(f"- Source: {row.get('source', '')}")
            if row.get("materiality_validation_status"):
                lines.append(
                    f"- Validation status: {row.get('materiality_validation_status', '')}"
                )
            if row.get("original_text"):
                lines.append("- Original text:")
                lines.append(f"  > {row.get('original_text', '')}")
            if row.get("final_replacement_text"):
                lines.append("- Final replacement text:")
                lines.append(f"  > {row.get('final_replacement_text', '')}")
            if row.get("why_selected"):
                lines.append(f"- Why selected: {row.get('why_selected', '')}")
            lines.append("")

    if direct_apply_optional_replacements:
        lines.append("## Optional Direct-Apply Replacements")
        for index, row in enumerate(direct_apply_optional_replacements, start=1):
            lines.append(
                f"### Optional {index} · {str(row.get('apply_priority', '')).title()} priority · Direct Apply Optional"
            )
            if row.get("section"):
                lines.append(f"- Section: {row.get('section', '')}")
            if row.get("source"):
                lines.append(f"- Source: {row.get('source', '')}")
            if row.get("materiality_validation_status"):
                lines.append(
                    f"- Validation status: {row.get('materiality_validation_status', '')}"
                )
            if row.get("original_text"):
                lines.append("- Original text:")
                lines.append(f"  > {row.get('original_text', '')}")
            if row.get("final_replacement_text"):
                lines.append("- Optional replacement text:")
                lines.append(f"  > {row.get('final_replacement_text', '')}")
            if row.get("why_selected"):
                lines.append(f"- Why selected: {row.get('why_selected', '')}")
            lines.append("")

    if direction_only_replacements:
        lines.append("## Direction-Only Recommendations")
        for index, row in enumerate(direction_only_replacements, start=1):
            lines.append(
                f"### Direction {index} · {str(row.get('apply_priority', '')).title()} priority"
            )
            if row.get("section"):
                lines.append(f"- Section: {row.get('section', '')}")
            if row.get("source"):
                lines.append(f"- Source: {row.get('source', '')}")
            current_bullet = str(row.get("current_evidence", "") or row.get("original_text", "") or "").strip()
            if current_bullet:
                lines.append("- Current bullet:")
                lines.append(f"  > {current_bullet}")
            if row.get("rewrite_direction"):
                lines.append(f"- Recommended action: {row.get('rewrite_direction', '')}")
            if row.get("why_selected"):
                lines.append(f"- Why selected: {row.get('why_selected', '')}")
            lines.append("")

    if anchor_cards:
        lines.append("## Anchor Evidence to Keep Visible")
        for index, card in enumerate(anchor_cards, start=1):
            lines.append(
                f"### Anchor {index} · {str(card.get('priority', '')).title()} priority · "
                f"{str(card.get('edit_type', '')).replace('_', ' ').title()}"
            )
            if card.get("section"):
                lines.append(f"- Section: {card.get('section', '')}")
            if card.get("source"):
                lines.append(f"- Evidence source: {card.get('source', '')}")
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
            if card.get("why_it_matters"):
                lines.append(f"- Why keep it visible: {card.get('why_it_matters', '')}")
            if card.get("claim_safety"):
                lines.append(f"- Claim safety: {card.get('claim_safety', '')}")
            if card.get("placement_guidance"):
                lines.append(f"- Placement guidance: {card.get('placement_guidance', '')}")
            lines.append("")

    if edit_cards:
        lines.append("## Appendix: Bullet-Level Edit Cards")
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
        lines.append("## Appendix: Bullet Diagnoses")
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
        lines.append("## Appendix: Raw Replacement Candidate Inventory")
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
            if row.get("direction_only_reason"):
                lines.append(f"- Direction-only reason: {row.get('direction_only_reason', '')}")
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

    if not edit_cards and not anchor_cards and empty_state_reason:
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
        override_card = _rewrite_idea_override_card(payload, row)

        action_text = str(row.get("action", "") or "").strip()
        action_label = "Action"

        if override_card is not None and str(override_card.get("recommended_rewrite", "") or "").strip():
            action_text = str(override_card.get("recommended_rewrite", "") or "").strip()
            action_label = "Proposed rewrite"

        lines.append(
            f"- **[{row.get('section', '')}] {row.get('source', '')}** | "
            f"type={row.get('evidence_type', '')} | supports={row.get('supported_terms', [])}"
        )

        if override_card is not None and str(override_card.get("replacement_materiality_validation_status", "") or "").strip():
            lines.append(
                f"  - Patch status: {override_card.get('replacement_materiality_validation_status', '')}"
            )

        if override_card is not None and str(override_card.get("patch_generation_method", "") or "").strip():
            lines.append(
                f"  - Patch method: {override_card.get('patch_generation_method', '')}"
            )

        lines.append(f"  - {action_label}: {action_text}")
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
