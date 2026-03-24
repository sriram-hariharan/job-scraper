from typing import List, Dict, Any, Optional

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

from src.tailoring.llm import (
    _build_llm_prompt,
    _build_live_rewrite_prompt,
)

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

    return {
        "schema_version": "tailoring_training_log_v1",
        "generated_at_utc": str(generated_at_utc or ""),
        "artifacts": {
            "output_json_path": str(output_json_path or ""),
            "output_md_path": str(output_md_path or ""),
            "output_llm_json_path": str(output_llm_json_path or ""),
        },
        "packet_json_path": str(packet_json_path or ""),
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
