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

def _build_recruiter_summary(packet: Dict[str, Any]) -> str:
    job = packet.get("job", {})
    selection = packet.get("selection", {})
    resume_name = selection.get("selected_resume", "selected resume")
    score = selection.get("selected_score", 0.0)
    company = job.get("company", "")
    title = job.get("title", "")

    direct_terms = _unique_preserve_order(
        _direct_terms(packet, "required") + _direct_terms(packet, "preferred")
    )
    contextual_terms = _unique_preserve_order(
        _contextual_terms(packet, "required") + _contextual_terms(packet, "preferred")
    )
    skills_only_terms = _unique_preserve_order(
        _skills_only_terms(packet, "required") + _skills_only_terms(packet, "preferred")
    )
    unsupported_terms = _unique_preserve_order(
        _unsupported_terms(packet, "required") + _unsupported_terms(packet, "preferred")
    )

    sentences: List[str] = [
        f"{resume_name} is the selected variant for {company} | {title} with a deterministic score of {score:.3f}."
    ]

    if direct_terms:
        sentences.append(
            f"It has direct bullet support for {', '.join(_truncate_list(direct_terms, 8))}."
        )
    else:
        sentences.append(
            "It does not yet show strong direct bullet support for the main JD terms."
        )

    contextual_parts: List[str] = []
    if contextual_terms:
        contextual_parts.append(
            f"adjacent entry-context support for {', '.join(_truncate_list(contextual_terms, 6))}"
        )
    if skills_only_terms:
        contextual_parts.append(
            f"skills-section-only support for {', '.join(_truncate_list(skills_only_terms, 6))}"
        )

    if contextual_parts:
        sentences.append(
            "It also has "
            + " and ".join(contextual_parts)
            + ", which should be framed carefully rather than presented as direct hands-on experience."
        )

    if unsupported_terms:
        sentences.append(
            f"The clearest unsupported gaps still showing are {', '.join(_truncate_list(unsupported_terms, 6))}."
        )
    else:
        sentences.append(
            "It does not show major unsupported JD terms after the support-tier pass."
        )

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


def _build_bullet_reuse(packet: Dict[str, Any], limit: int = 6) -> List[Dict[str, Any]]:
    rows = packet.get("top_relevant_bullets", []) or []
    selected = rows[:limit]

    reuse_rows = []
    for row in selected:
        source = _source_label(row)
        overlaps = row.get("overlaps", []) or []
        evidence_type = row.get("evidence_type", "direct_overlap")

        if evidence_type == "direct_overlap":
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
                "bullet feels more credible and less isolated."
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
                "bullet": row.get("text", ""),
                "reuse_note": reuse_note,
            }
        )

    return reuse_rows

def _build_rewrite_candidates(packet: Dict[str, Any], limit: int = 4) -> List[Dict[str, Any]]:
    rows = packet.get("top_relevant_bullets", []) or []
    candidates: List[Dict[str, Any]] = []
    used_sources = set()

    for row in rows:
        overlaps = row.get("overlaps", []) or []
        if not overlaps:
            continue

        source = _source_label(row)
        evidence_type = row.get("evidence_type", "direct_overlap")
        source_key = (row.get("section", ""), source, evidence_type)

        if source_key in used_sources:
            continue

        if evidence_type == "direct_overlap":
            action = (
                f"Lead with {', '.join(overlaps[:4])} in the opening clause of this bullet, "
                "then keep the outcome/impact at the end."
            )
        elif evidence_type == "same_source_context":
            action = (
                "Use this as a second supporting bullet under the same role so the stronger anchor bullet "
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
                "supported_terms": overlaps[:6],
                "action": action,
                "bullet_excerpt": _short_bullet(row.get("text", "")),
            }
        )
        used_sources.add(source_key)

        if len(candidates) >= limit:
            break

    return candidates

def _build_evidence_layers(packet: Dict[str, Any], limit_per_group: int = 4) -> Dict[str, List[Dict[str, Any]]]:
    rows = packet.get("top_relevant_bullets", []) or []

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

def _select_operator_rewrite_directions(
    payload: Dict[str, Any],
    llm_output: Optional[Dict[str, Any]],
) -> tuple[List[str], str]:
    parsed = {}
    if isinstance(llm_output, dict) and llm_output.get("parse_ok"):
        parsed = llm_output.get("parsed", {}) or {}

    if parsed and _llm_output_is_strong_enough(parsed):
        llm_directions = [
            str(item).strip()
            for item in parsed.get("rewrite_directions", []) or []
            if _is_actionable_rewrite_direction(item)
        ]
        return llm_directions[:6], "live_llm"

    return _fallback_rewrite_directions_from_payload(payload), "deterministic"


def _build_operator_markdown_payload(
    payload: Dict[str, Any],
    llm_output: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    operator_payload = dict(payload)
    preferred_rewrite_directions, preferred_rewrite_source = _select_operator_rewrite_directions(
        payload,
        llm_output,
    )
    operator_payload["preferred_rewrite_directions"] = preferred_rewrite_directions
    operator_payload["preferred_rewrite_source"] = preferred_rewrite_source
    return operator_payload

def _build_tailoring_actions(packet: Dict[str, Any]) -> List[str]:
    evidence_layers = _build_evidence_layers(packet)

    anchors = evidence_layers.get("anchors", [])
    supports = evidence_layers.get("supports", [])
    context = evidence_layers.get("context", [])

    direct_required = _direct_terms(packet, "required")
    direct_preferred = _direct_terms(packet, "preferred")
    secondary_terms = _unique_preserve_order(
        _contextual_terms(packet, "required")
        + _contextual_terms(packet, "preferred")
        + _skills_only_terms(packet, "required")
        + _skills_only_terms(packet, "preferred")
    )
    unsupported_required = _unsupported_terms(packet, "required")
    unsupported_preferred = _unsupported_terms(packet, "preferred")

    actions: List[str] = []

    if direct_required:
        actions.append(
            f"Lead the tailored version with direct-bullet required terms: {', '.join(_truncate_list(direct_required, 6))}."
        )
    elif direct_preferred:
        actions.append(
            f"Lead with the strongest directly supported preferred terms already proven in bullets: {', '.join(_truncate_list(direct_preferred, 6))}."
        )

    if anchors:
        anchor_sources = _unique_preserve_order([_source_label(row) for row in anchors[:3]])
        actions.append(
            f"Use these direct-match bullets as primary anchors: {', '.join(_truncate_list(anchor_sources, 4))}."
        )

    if secondary_terms:
        actions.append(
            f"Use these adjacent or skills-only terms only as secondary framing, not as direct hands-on claims: {', '.join(_truncate_list(secondary_terms, 6))}."
        )

    if supports:
        support_sources = _unique_preserve_order([_source_label(row) for row in supports[:3]])
        actions.append(
            f"Use semantically aligned bullets only as supporting proof after the anchors: {', '.join(_truncate_list(support_sources, 4))}."
        )

    if context:
        context_sources = _unique_preserve_order([_source_label(row) for row in context[:3]])
        actions.append(
            f"Use same-role context bullets only to reinforce the anchor story: {', '.join(_truncate_list(context_sources, 4))}."
        )

    true_gaps = _unique_preserve_order(unsupported_required + unsupported_preferred)
    if true_gaps:
        actions.append(
            f"Keep these truly unsupported gaps explicit unless you can support them truthfully: {', '.join(_truncate_list(true_gaps, 6))}."
        )

    return _unique_preserve_order(actions)


def _build_llm_prompt(packet: Dict[str, Any]) -> str:
    job = packet.get("job", {})
    selection = packet.get("selection", {})
    summary = packet.get("summary", {})
    bullets = packet.get("top_relevant_bullets", []) or []
    rewrite_candidates = packet.get("rewrite_candidates", []) or []

    evidence_layers = packet.get("evidence_layers", {}) or {}
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
    lines.append("Primary anchor bullets:")
    for idx, row in enumerate(anchor_rows, 1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] {_source_label(row)} | "
            f"supports={row.get('overlaps', [])}"
        )
        lines.append(f"   Bullet: {_short_bullet(row.get('text', ''), 320)}")
    lines.append("")
    lines.append("Semantic supporting bullets:")
    for idx, row in enumerate(semantic_support_rows, 1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] {_source_label(row)} | "
            f"type={row.get('evidence_type', '')}"
        )
        if row.get("semantic_score") is not None:
            lines.append(f"   semantic_score={row.get('semantic_score')}")
        lines.append(f"   Bullet: {_short_bullet(row.get('text', ''), 320)}")
    lines.append("")

    lines.append("Same-role context bullets:")
    for idx, row in enumerate(context_rows, 1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] {_source_label(row)} | "
            f"type={row.get('evidence_type', '')} | supports={row.get('overlaps', [])}"
        )
        lines.append(f"   Bullet: {_short_bullet(row.get('text', ''), 320)}")
    lines.append("")
    lines.append("Evidence-backed rewrite candidates:")
    for idx, row in enumerate(rewrite_candidates, 1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] {row.get('source', '')} | "
            f"type={row.get('evidence_type', '')} | supports={row.get('supported_terms', [])}"
        )
        lines.append(f"   Action: {row.get('action', '')}")
        lines.append(f"   Evidence: {row.get('bullet_excerpt', '')}")
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
    lines.append("Primary anchor bullets:")
    for idx, row in enumerate(anchors, 1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] {_source_label(row)} | supports={row.get('overlaps', [])}"
        )
        lines.append(f"   Bullet: {_short_bullet(row.get('text', ''), 320)}")
    lines.append("")
    lines.append("Semantic supporting bullets:")
    for idx, row in enumerate(supports, 1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] {_source_label(row)} | type={row.get('evidence_type', '')}"
        )
        if row.get("semantic_score") is not None:
            lines.append(f"   semantic_score={row.get('semantic_score')}")
        lines.append(f"   Bullet: {_short_bullet(row.get('text', ''), 320)}")
    lines.append("")
    lines.append("Same-role context bullets:")
    for idx, row in enumerate(context, 1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] {_source_label(row)} | type={row.get('evidence_type', '')}"
        )
        lines.append(f"   Bullet: {_short_bullet(row.get('text', ''), 320)}")
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
    rewrite_candidates = _build_rewrite_candidates(packet)
    evidence_layers = _build_evidence_layers(packet)
    tailoring_actions = _build_tailoring_actions(packet)
    llm_prompt = _build_llm_prompt(packet)
    live_rewrite_prompt = _build_live_rewrite_prompt(packet, {
        "rewrite_candidates": rewrite_candidates,
        "evidence_layers": evidence_layers,
    })

    return {
        "job": packet.get("job", {}),
        "selection": packet.get("selection", {}),
        "summary": packet.get("summary", {}),
        "recruiter_summary": recruiter_summary,
        "keep_emphasize": keep_emphasize,
        "tailoring_actions": tailoring_actions,
        "rewrite_candidates": rewrite_candidates,
        "evidence_layers": evidence_layers,
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

    lines.append("## Priority Rewrite Directions")
    lines.append(f"- Source: {payload.get('preferred_rewrite_source', 'deterministic')}")
    for item in payload.get("preferred_rewrite_directions", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Evidence-Backed Rewrite Ideas")
    for row in payload.get("rewrite_candidates", []):
        lines.append(
            f"- **[{row.get('section', '')}] {row.get('source', '')}** | "
            f"type={row.get('evidence_type', '')} | supports={row.get('supported_terms', [])}"
        )
        lines.append(f"  - Action: {row.get('action', '')}")
        lines.append(f"  - Evidence: {row.get('bullet_excerpt', '')}")
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
        lines.append(f"  - Bullet: {row.get('bullet', '')}")
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
    markdown_payload = _build_operator_markdown_payload(payload, None)
    markdown = _markdown_from_payload(markdown_payload)

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

    if args.output_json.strip():
        output_json_path = Path(args.output_json)
        output_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"JSON written: {output_json_path}")

    output_md_path = None
    if args.output_md.strip():
        output_md_path = Path(args.output_md)
        output_md_path.write_text(markdown, encoding="utf-8")
        print(f"Markdown written: {args.output_md}")
    
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
        
        if llm_output.get("parse_ok") and output_md_path is not None:
            markdown_payload = _build_operator_markdown_payload(payload, llm_output)
            output_md_path.write_text(_markdown_from_payload(markdown_payload), encoding="utf-8")
            print(
                f"Markdown updated with {markdown_payload.get('preferred_rewrite_source', 'deterministic')} rewrite directions: "
                f"{args.output_md}"
            )

if __name__ == "__main__":
    main()