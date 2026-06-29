"""Default-off exact resume change-set proposal builder."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "42A"
CHANGE_TYPES = ("summary", "skill", "bullet", "project", "evidence_note")
FALSE_ACTION_KEYS = (
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "scoring_feature_preparation_performed",
    "contribution_preview_performed",
    "score_impact_preview_performed",
    "planning_annotation_performed",
    "review_packet_building_performed",
    "review_queue_building_performed",
    "final_scoring_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
)


def _string(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return " ".join(_string(value).lower().replace("_", " ").split())


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y"}:
            return True
        if text in {"0", "false", "no", "n"}:
            return False
    return default if value is None else bool(value)


def _int_at_least(value: Any, default: int, minimum: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= minimum else default


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    return {
        "max_change_proposals": _int_at_least(
            supplied.get("max_change_proposals"),
            8,
            0,
        ),
        "max_changes_per_queue_item": _int_at_least(
            supplied.get("max_changes_per_queue_item"),
            3,
            0,
        ),
        "minimum_evidence_terms": _int_at_least(
            supplied.get("minimum_evidence_terms"),
            1,
            0,
        ),
        "allow_summary_changes": _bool(
            supplied.get("allow_summary_changes"),
            True,
        ),
        "allow_skill_changes": _bool(supplied.get("allow_skill_changes"), True),
        "allow_bullet_changes": _bool(supplied.get("allow_bullet_changes"), True),
        "allow_project_changes": _bool(supplied.get("allow_project_changes"), True),
        "require_source_evidence": _bool(
            supplied.get("require_source_evidence"),
            True,
        ),
        "include_before_after_text": _bool(
            supplied.get("include_before_after_text"),
            True,
        ),
    }


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        return list(value)
    return [value]


def _text_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for key in sorted(value.keys()):
            values.extend(_text_values(value.get(key)))
        return values
    for item in _as_list(value):
        if isinstance(item, dict):
            for key in sorted(item.keys()):
                values.extend(_text_values(item.get(key)))
        else:
            text = _string(item)
            if text:
                values.append(text)
    return values


def _unique_text(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _string(value)
        key = _norm(text)
        if not text or not key or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _terms_from_context(
    jd_context: dict[str, Any] | None,
    tailoring_context: dict[str, Any] | None,
) -> tuple[list[str], list[str]]:
    jd = jd_context if isinstance(jd_context, dict) else {}
    tailoring = tailoring_context if isinstance(tailoring_context, dict) else {}
    important_values: list[Any] = []
    missing_values: list[Any] = []
    for key in (
        "required_skills",
        "preferred_skills",
        "tools",
        "responsibilities",
        "domain",
        "seniority",
        "red_flags",
    ):
        important_values.extend(_as_list(jd.get(key)))
    for key in (
        "matched_required_skills",
        "matched_tools",
        "suggested_focus",
    ):
        important_values.extend(_as_list(tailoring.get(key)))
    for key in ("missing_required_skills", "missing_tools", "resume_evidence_needed"):
        missing_values.extend(_as_list(tailoring.get(key)))
        important_values.extend(_as_list(tailoring.get(key)))
    for key in ("normalized_tailoring_suggestions", "tailoring_suggestions", "suggestions"):
        for text in _text_values(tailoring.get(key)):
            important_values.append(text)
    return _unique_text(important_values), _unique_text(missing_values)


def _resume_texts(resume_context: dict[str, Any] | None) -> dict[str, list[dict[str, str]]]:
    resume = resume_context if isinstance(resume_context, dict) else {}
    sections: list[dict[str, str]] = []
    bullets: list[dict[str, str]] = []
    projects: list[dict[str, str]] = []
    skills: list[dict[str, str]] = []
    summary: list[dict[str, str]] = []

    profile_summary = _string(resume.get("profile_summary"))
    if profile_summary:
        summary.append(
            {
                "section": "summary",
                "identifier": "profile_summary",
                "text": profile_summary,
            }
        )
    for section_name, section_value in (
        resume.get("resume_sections") if isinstance(resume.get("resume_sections"), dict) else {}
    ).items():
        for index, text in enumerate(_text_values(section_value)):
            sections.append(
                {
                    "section": _string(section_name) or "resume_sections",
                    "identifier": f"{_string(section_name) or 'section'}-{index + 1}",
                    "text": text,
                }
            )
    for index, item in enumerate(_as_list(resume.get("resume_bullets"))):
        if isinstance(item, dict):
            text = _string(
                item.get("text")
                or item.get("bullet")
                or item.get("current_text")
                or item.get("content")
            )
            identifier = _string(item.get("id") or item.get("bullet_id"))
        else:
            text = _string(item)
            identifier = ""
        if text:
            bullets.append(
                {
                    "section": "experience",
                    "identifier": identifier or f"bullet-{index + 1}",
                    "text": text,
                }
            )
    for index, text in enumerate(_text_values(resume.get("experience"))):
        bullets.append(
            {
                "section": "experience",
                "identifier": f"experience-{index + 1}",
                "text": text,
            }
        )
    for index, text in enumerate(_text_values(resume.get("projects"))):
        projects.append(
            {
                "section": "projects",
                "identifier": f"project-{index + 1}",
                "text": text,
            }
        )
    for index, text in enumerate(_text_values(resume.get("skills"))):
        skills.append(
            {
                "section": "skills",
                "identifier": f"skill-{index + 1}",
                "text": text,
            }
        )
    return {
        "summary": summary,
        "skills": skills,
        "bullets": bullets,
        "projects": projects,
        "sections": sections,
    }


def _evidence_matrix_texts(tailoring_context: dict[str, Any] | None) -> list[str]:
    if not isinstance(tailoring_context, dict):
        return []
    return _text_values(tailoring_context.get("evidence_matrix"))


def _term_in_text(term: str, text: str) -> bool:
    needle = _norm(term)
    haystack = _norm(text)
    return bool(needle and haystack and needle in haystack)


def _find_evidence(
    term: str,
    resume_sources: dict[str, list[dict[str, str]]],
    matrix_texts: list[str],
) -> dict[str, Any]:
    matched: list[dict[str, str]] = []
    for source_type in ("summary", "skills", "bullets", "projects", "sections"):
        for source in resume_sources[source_type]:
            if _term_in_text(term, source["text"]):
                matched.append(
                    {
                        "source_type": source_type,
                        "target_section": source["section"],
                        "target_identifier": source["identifier"],
                        "text": source["text"],
                    }
                )
    for index, text in enumerate(matrix_texts):
        if _term_in_text(term, text):
            matched.append(
                {
                    "source_type": "evidence_matrix",
                    "target_section": "evidence_matrix",
                    "target_identifier": f"evidence-{index + 1}",
                    "text": text,
                }
            )
    return {"term": term, "matches": matched}


def _flatten_grouped(value: Any) -> list[Any]:
    if not isinstance(value, dict):
        return []
    rows: list[Any] = []
    keys = sorted(
        value.keys(),
        key=lambda key: (
            -int(key) if str(key).lstrip("-").isdigit() else 0,
            str(key),
        ),
    )
    for key in keys:
        grouped = value.get(key)
        if isinstance(grouped, list):
            rows.extend(grouped)
    return rows


def _rows_from_queue_result(queue_result: dict[str, Any] | None) -> tuple[list[Any], str]:
    if not isinstance(queue_result, dict):
        return [], "missing"
    if isinstance(queue_result.get("review_queue"), list):
        return list(queue_result["review_queue"]), "queue_result.review_queue"
    nested = queue_result.get("queue_result")
    if isinstance(nested, dict) and isinstance(nested.get("review_queue"), list):
        return (
            list(nested["review_queue"]),
            "queue_result.queue_result.review_queue",
        )
    grouped = _flatten_grouped(queue_result.get("review_queue_by_priority"))
    if grouped:
        return grouped, "queue_result.review_queue_by_priority"
    if isinstance(nested, dict):
        grouped = _flatten_grouped(nested.get("review_queue_by_priority"))
        if grouped:
            return (
                grouped,
                "queue_result.queue_result.review_queue_by_priority",
            )
    return [], "missing"


def _resolve_queue(
    review_queue: list[Any] | None,
    queue_result: dict[str, Any] | None,
) -> tuple[list[Any], str, list[str]]:
    if isinstance(review_queue, list):
        return list(review_queue), "review_queue", []
    rows, source = _rows_from_queue_result(queue_result)
    if rows:
        return rows, source, []
    return [], source, ["review_queue"]


def _item_field(item: dict[str, Any], key: str) -> Any:
    return deepcopy(item.get(key))


def _proposal(
    *,
    index: int,
    item: dict[str, Any],
    change_type: str,
    target_section: str,
    target_identifier: str,
    current_text: str,
    proposed_text: str,
    change_reason: str,
    jd_terms_supported: list[str],
    resume_evidence_used: list[str],
    risk_flags: list[str],
    include_text: bool,
) -> dict[str, Any]:
    proposal = {
        "proposal_id": f"phase42a-{index:03d}",
        "item_id": _item_field(item, "item_id"),
        "job_id": _item_field(item, "job_id"),
        "title": _item_field(item, "title"),
        "company": _item_field(item, "company"),
        "change_type": change_type,
        "target_section": target_section,
        "target_identifier": target_identifier,
        "current_text": current_text if include_text else "",
        "proposed_text": proposed_text if include_text else "",
        "change_reason": change_reason,
        "jd_terms_supported": list(jd_terms_supported),
        "resume_evidence_used": list(resume_evidence_used),
        "risk_flags": list(risk_flags),
        "manual_review_required": True,
        "requires_user_acceptance": True,
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
    }
    return proposal


def _summary_candidate(
    term: str,
    item: dict[str, Any],
    evidence: dict[str, Any],
    include_text: bool,
    proposal_index: int,
) -> dict[str, Any] | None:
    for match in evidence["matches"]:
        if match["source_type"] == "summary":
            current = match["text"]
            proposed = current
            if not _term_in_text(term, current):
                proposed = f"{current} Focus: {term}."
            return _proposal(
                index=proposal_index,
                item=item,
                change_type="summary",
                target_section=match["target_section"],
                target_identifier=match["target_identifier"],
                current_text=current,
                proposed_text=proposed,
                change_reason=f"Surface supplied resume evidence for JD term: {term}",
                jd_terms_supported=[term],
                resume_evidence_used=[current],
                risk_flags=[],
                include_text=include_text,
            )
    return None


def _skill_candidate(
    term: str,
    item: dict[str, Any],
    evidence: dict[str, Any],
    skills_text: str,
    include_text: bool,
    proposal_index: int,
) -> dict[str, Any] | None:
    has_resume_evidence = any(
        match["source_type"] in {"skills", "bullets", "projects", "sections", "summary"}
        for match in evidence["matches"]
    )
    if not has_resume_evidence:
        return None
    current = skills_text
    proposed = current if _term_in_text(term, current) else f"{current}, {term}".strip(", ")
    evidence_text = [match["text"] for match in evidence["matches"][:2]]
    return _proposal(
        index=proposal_index,
        item=item,
        change_type="skill",
        target_section="skills",
        target_identifier="skills",
        current_text=current,
        proposed_text=proposed,
        change_reason=f"Add or retain verified JD skill from supplied resume evidence: {term}",
        jd_terms_supported=[term],
        resume_evidence_used=evidence_text,
        risk_flags=[],
        include_text=include_text,
    )


def _bullet_candidate(
    term: str,
    item: dict[str, Any],
    evidence: dict[str, Any],
    include_text: bool,
    proposal_index: int,
) -> dict[str, Any] | None:
    for match in evidence["matches"]:
        if match["source_type"] == "bullets":
            current = match["text"]
            proposed = f"{current} [Emphasize: {term}]"
            return _proposal(
                index=proposal_index,
                item=item,
                change_type="bullet",
                target_section=match["target_section"],
                target_identifier=match["target_identifier"],
                current_text=current,
                proposed_text=proposed,
                change_reason=f"Use supplied existing bullet evidence to emphasize JD term: {term}",
                jd_terms_supported=[term],
                resume_evidence_used=[current],
                risk_flags=[],
                include_text=include_text,
            )
    return None


def _project_candidate(
    term: str,
    item: dict[str, Any],
    evidence: dict[str, Any],
    include_text: bool,
    proposal_index: int,
) -> dict[str, Any] | None:
    for match in evidence["matches"]:
        if match["source_type"] == "projects":
            current = match["text"]
            proposed = f"{current} [Align with JD term: {term}]"
            return _proposal(
                index=proposal_index,
                item=item,
                change_type="project",
                target_section=match["target_section"],
                target_identifier=match["target_identifier"],
                current_text=current,
                proposed_text=proposed,
                change_reason=f"Use supplied project evidence to support JD term: {term}",
                jd_terms_supported=[term],
                resume_evidence_used=[current],
                risk_flags=[],
                include_text=include_text,
            )
    return None


def _evidence_note_candidate(
    term: str,
    item: dict[str, Any],
    include_text: bool,
    proposal_index: int,
) -> dict[str, Any]:
    return _proposal(
        index=proposal_index,
        item=item,
        change_type="evidence_note",
        target_section="manual_review_notes",
        target_identifier=f"missing-evidence-{_norm(term).replace(' ', '-')}",
        current_text="",
        proposed_text=f"Do not add '{term}' unless source evidence is supplied.",
        change_reason=f"JD term lacks supplied resume evidence: {term}",
        jd_terms_supported=[term],
        resume_evidence_used=[],
        risk_flags=["missing_source_evidence"],
        include_text=include_text,
    )


def _group_by_type(proposals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for change_type in CHANGE_TYPES:
        grouped[change_type] = []
    for proposal in proposals:
        change_type = _string(proposal.get("change_type")) or "evidence_note"
        if change_type not in grouped:
            grouped[change_type] = []
        grouped[change_type].append(deepcopy(proposal))
    return grouped


def _proposal_key(
    *,
    queue_count: int,
    valid_count: int,
    invalid_count: int,
    proposals: list[dict[str, Any]],
) -> str:
    counts: dict[str, int] = {}
    for change_type in CHANGE_TYPES:
        counts[change_type] = 0
    for proposal in proposals:
        change_type = _string(proposal.get("change_type")) or "evidence_note"
        if change_type not in counts:
            counts[change_type] = 0
        counts[change_type] = counts[change_type] + 1
    parts = [
        f"phase={PHASE}",
        f"queue={queue_count}",
        f"valid={valid_count}",
        f"invalid={invalid_count}",
        f"proposals={len(proposals)}",
    ]
    for change_type in CHANGE_TYPES:
        parts.append(f"{change_type}={counts.get(change_type, 0)}")
    return "|".join(parts)


def build_exact_resume_change_set_proposal_builder_default_off(
    review_queue: list[Any] | None = None,
    queue_result: dict[str, Any] | None = None,
    resume_context: dict[str, Any] | None = None,
    jd_context: dict[str, Any] | None = None,
    tailoring_context: dict[str, Any] | None = None,
    proposal_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build exact resume change proposals for manual review only."""

    policy = _policy(proposal_policy)
    rows, source, missing_inputs = _resolve_queue(review_queue, queue_result)
    resume_copy = deepcopy(resume_context) if isinstance(resume_context, dict) else None
    jd_copy = deepcopy(jd_context) if isinstance(jd_context, dict) else None
    tailoring_copy = (
        deepcopy(tailoring_context) if isinstance(tailoring_context, dict) else None
    )
    resume_sources = _resume_texts(resume_copy)
    matrix_texts = _evidence_matrix_texts(tailoring_copy)
    terms, missing_terms = _terms_from_context(jd_copy, tailoring_copy)
    invalid_items: list[dict[str, Any]] = []
    valid_items: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    skipped_terms: list[dict[str, Any]] = []

    if not isinstance(resume_context, dict) or not resume_sources:
        missing_inputs.append("resume_context")
    if not isinstance(jd_context, dict) or not terms:
        missing_inputs.append("jd_context")
    if not isinstance(tailoring_context, dict):
        missing_inputs.append("tailoring_context")

    skills_text = ", ".join(source["text"] for source in resume_sources["skills"])
    proposal_index = 1
    for input_index, row in enumerate(rows):
        if not isinstance(row, dict):
            invalid_items.append(
                {
                    "input_index": input_index,
                    "reason": "review queue item must be a dictionary",
                }
            )
            continue
        item = deepcopy(row)
        valid_items.append(item)
        per_item_count = 0
        for term in terms:
            if len(proposals) >= policy["max_change_proposals"]:
                break
            if per_item_count >= policy["max_changes_per_queue_item"]:
                break
            evidence = _find_evidence(term, resume_sources, matrix_texts)
            evidence_count = len(evidence["matches"])
            if evidence_count < policy["minimum_evidence_terms"]:
                if policy["require_source_evidence"] and term in missing_terms:
                    proposal = _evidence_note_candidate(
                        term,
                        item,
                        policy["include_before_after_text"],
                        proposal_index,
                    )
                    proposals.append(proposal)
                    proposal_index = proposal_index + 1
                    per_item_count = per_item_count + 1
                else:
                    skipped_terms.append(
                        {
                            "item_id": deepcopy(item.get("item_id")),
                            "term": term,
                            "reason": "insufficient_supplied_evidence",
                        }
                    )
                continue

            candidates: list[dict[str, Any] | None] = []
            if policy["allow_skill_changes"]:
                candidates.append(
                    _skill_candidate(
                        term,
                        item,
                        evidence,
                        skills_text,
                        policy["include_before_after_text"],
                        proposal_index,
                    )
                )
            if policy["allow_bullet_changes"]:
                candidates.append(
                    _bullet_candidate(
                        term,
                        item,
                        evidence,
                        policy["include_before_after_text"],
                        proposal_index,
                    )
                )
            if policy["allow_summary_changes"]:
                candidates.append(
                    _summary_candidate(
                        term,
                        item,
                        evidence,
                        policy["include_before_after_text"],
                        proposal_index,
                    )
                )
            if policy["allow_project_changes"]:
                candidates.append(
                    _project_candidate(
                        term,
                        item,
                        evidence,
                        policy["include_before_after_text"],
                        proposal_index,
                    )
                )
            selected = next((candidate for candidate in candidates if candidate), None)
            if selected is None:
                skipped_terms.append(
                    {
                        "item_id": deepcopy(item.get("item_id")),
                        "term": term,
                        "reason": "change_type_not_allowed_or_no_target",
                    }
                )
                continue
            proposals.append(selected)
            proposal_index = proposal_index + 1
            per_item_count = per_item_count + 1

    if not rows and "review_queue" not in missing_inputs:
        missing_inputs.append("review_queue")

    summary = {
        "change_proposal_count": len(proposals),
        "proposal_blocked": bool(not rows or not proposals),
        "full_resume_produced": False,
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "manual_review_required": True,
        "requires_user_acceptance": True,
    }
    findings = {
        "review_queue_source": source,
        "invalid_review_queue_items": deepcopy(invalid_items),
        "skipped_terms": deepcopy(skipped_terms),
        "source_evidence_required": policy["require_source_evidence"],
        "copied_inputs_only": True,
        "full_resume_included": False,
        "executable_callbacks_included": False,
        "mutation_commands_included": False,
        "db_write_commands_included": False,
        "application_submission_commands_included": False,
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "exact_resume_change_set_proposal_builder": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "review_queue_present": bool(rows),
        "review_queue_count": len(rows),
        "valid_review_queue_item_count": len(valid_items),
        "invalid_review_queue_item_count": len(invalid_items),
        "resume_context_present": isinstance(resume_context, dict),
        "jd_context_present": isinstance(jd_context, dict),
        "tailoring_context_present": isinstance(tailoring_context, dict),
        "proposal_policy": deepcopy(policy),
        "change_proposals": deepcopy(proposals),
        "change_proposals_by_type": _group_by_type(proposals),
        "change_set_summary": summary,
        "proposal_findings": findings,
        "missing_inputs": _unique_text(missing_inputs),
        "proposal_key": _proposal_key(
            queue_count=len(rows),
            valid_count=len(valid_items),
            invalid_count=len(invalid_items),
            proposals=proposals,
        ),
        "resume_change_proposals_created": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
