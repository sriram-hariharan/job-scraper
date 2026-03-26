
from typing import Dict, Any, Optional, List, Tuple
import os
import re
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from src.ai.llm_client import (
    FALLBACK_ENABLED as LLM_FALLBACK_ENABLED,
    FALLBACK_MODEL as LLM_FALLBACK_MODEL,
    FALLBACK_PROVIDER as LLM_FALLBACK_PROVIDER,
    run_chat_completion_with_metadata,
)

from src.tailoring.packet_support import (
    _support_tier_prompt_lines,
    _facet_prompt_lines,
    _display_row_source,
    _short_bullet,
    _unique_preserve_order,
)

from src.tailoring.planner import (
    _build_tailoring_plan,
    _tailoring_plan_prompt_lines,
)

from src.tailoring.selection import (
    _build_evidence_layers,
    _build_rewrite_candidates,
)

from src.config.consts import (
    ACTION_VERB_HINTS
)

_PATCH_REFINEMENT_LEAD_VERB_STOPWORDS = set(ACTION_VERB_HINTS)
LLM_TAILOR_PROVIDER = "gemini"
LLM_TAILOR_MODEL = "gemini-2.5-flash"
LLM_TAILOR_MAX_TOKENS = 700
LLM_TAILOR_TEMPERATURE = 0
LLM_TAILOR_PROMPT_VERSION = "v4"

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

PATCH_REFINEMENT_PROVIDER = os.getenv(
    "PATCH_REFINEMENT_PROVIDER",
    "groq",
).strip().lower()

PATCH_REFINEMENT_MODEL = os.getenv(
    "PATCH_REFINEMENT_MODEL",
    "llama-3.3-70b-versatile",
).strip()

PATCH_REFINEMENT_MAX_TOKENS = 260
PATCH_REFINEMENT_TEMPERATURE = 0
PATCH_REFINEMENT_PROMPT_VERSION = "v1"

PATCH_REFINEMENT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "abstain": {"type": "boolean"},
        "refined_patch_text": {"type": "string"},
        "reason": {"type": "string"},
        "preserved_terms": {
            "type": "array",
            "items": {"type": "string"},
        },
        "risk_flags": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "abstain",
        "refined_patch_text",
        "reason",
        "preserved_terms",
        "risk_flags",
    ],
}

def _patch_refinement_protected_phrases(candidate: Dict[str, Any]) -> List[str]:
    original_text = str(candidate.get("original_text", "") or "").strip()

    phrases: List[str] = []

    # Keep supported signals and canonical signal
    phrases.extend(list(candidate.get("supported_jd_signals", []) or []))
    canonical = str(candidate.get("canonical_supported_signal", "") or "").strip()
    if canonical:
        phrases.append(canonical)

    # Capture meaningful phrases after "using", "with", "via", "for"
    for pattern in [
        r"\busing ([^.,;]+)",
        r"\bwith ([^.,;]+)",
        r"\bvia ([^.,;]+)",
        r"\bfor ([^.,;]+)",
    ]:
        for match in re.findall(pattern, original_text, flags=re.IGNORECASE):
            value = re.sub(r"\s+", " ", str(match or "").strip())
            if value:
                phrases.append(value)

    # Capture noun-like technical phrases you already know are meaningful
    for phrase in [
        "customer segmentation",
        "risk mitigation",
        "policyholder default probabilities",
        "early terminations",
        "lapse and retention risk assessments",
    ]:
        if phrase.lower() in original_text.lower():
            phrases.append(phrase)

    return _unique_preserve_order([p for p in phrases if str(p).strip()])

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
    lines.append('- When using Lead with or Support with, copy the exact source label only, for example: "Data Analyst II @ Accenture".')
    lines.append('- Never use section labels like "Primary anchor evidence units 1", "Secondary supporting evidence units", or wrappers like "[experience] ... | type=same_source_context" as the source.')
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

def _build_live_source_alias_map(payload: Dict[str, Any]) -> Dict[str, str]:
    evidence_layers = payload.get("evidence_layers", {}) or {}
    alias_map: Dict[str, str] = {}

    def _register_alias(alias: str, canonical: str) -> None:
        alias_clean = str(alias or "").strip().rstrip(".")
        canonical_clean = str(canonical or "").strip().rstrip(".")
        if alias_clean and canonical_clean:
            alias_map[alias_clean] = canonical_clean

    def _register_row_aliases(prefix: str, rows: List[Dict[str, Any]]) -> None:
        for idx, row in enumerate(rows or [], 1):
            canonical = _display_row_source(row)
            if not canonical:
                continue

            section = str(row.get("section", "") or "").strip()
            evidence_type = str(row.get("evidence_type", "") or "").strip()

            _register_alias(canonical, canonical)
            _register_alias(f"{prefix} {idx}", canonical)
            _register_alias(f"{prefix} {idx}.", canonical)

            if len(rows or []) == 1:
                _register_alias(prefix, canonical)
                _register_alias(f"{prefix}.", canonical)

            if section:
                _register_alias(f"[{section}] {canonical}", canonical)

            if section and evidence_type:
                _register_alias(f"[{section}] {canonical} | type={evidence_type}", canonical)
                _register_alias(f"[{section}] {canonical} | type={evidence_type}.", canonical)

    _register_row_aliases(
        "Primary anchor evidence units",
        list(evidence_layers.get("anchors", []) or [])[:4],
    )
    _register_row_aliases(
        "Secondary supporting evidence units",
        list(evidence_layers.get("supports", []) or [])[:4],
    )
    _register_row_aliases(
        "Same-role context evidence units",
        list(evidence_layers.get("context", []) or [])[:4],
    )

    return alias_map


def _cleanup_live_source_label(source: str) -> str:
    cleaned = str(source or "").strip().rstrip(".")
    cleaned = re.sub(r"^\[[^\]]+\]\s*", "", cleaned).strip()
    cleaned = re.sub(r"\s*\|\s*type=.*$", "", cleaned).strip()
    return cleaned.rstrip(".")


def _canonicalize_live_direction_sources(
    directions: List[str],
    payload: Dict[str, Any],
) -> List[str]:
    alias_map = _build_live_source_alias_map(payload)
    normalized: List[str] = []

    for item in directions or []:
        text = str(item or "").strip()
        if not text.startswith(("Lead with ", "Support with ")):
            normalized.append(text)
            continue

        if " from " not in text:
            normalized.append(text)
            continue

        body, source_part = text.rsplit(" from ", 1)
        source_part = source_part.strip()

        suffix = ""
        if source_part.lower().endswith(" as secondary supporting evidence."):
            suffix = " as secondary supporting evidence"
            source_part = source_part[: -len(" as secondary supporting evidence.")].strip()
        elif source_part.lower().endswith(" as secondary supporting evidence"):
            suffix = " as secondary supporting evidence"
            source_part = source_part[: -len(" as secondary supporting evidence")].strip()

        source_clean = source_part.rstrip(".").strip()
        canonical = alias_map.get(source_clean)
        if canonical is None:
            canonical = alias_map.get(_cleanup_live_source_label(source_clean))
        if canonical is None:
            canonical = _cleanup_live_source_label(source_clean) or source_clean

        rebuilt = f"{body} from {canonical}{suffix}.".strip()
        normalized.append(rebuilt)

    return _unique_preserve_order([item for item in normalized if item])

def _normalize_string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return _unique_preserve_order([str(item).strip() for item in value if str(item).strip()])

def _coerce_live_rewrite_direction(item: Any) -> str:
    if isinstance(item, str):
        return str(item).strip()

    if not isinstance(item, dict):
        return ""

    prefix = str(item.get("prefix", "") or "").strip()
    source = str(item.get("source", "") or "").strip()
    direction = str(item.get("direction", "") or "").strip()

    if prefix not in {"Lead with", "Support with", "Keep gap explicit", "Do not add"}:
        return ""

    if prefix in {"Lead with", "Support with"}:
        parts = [prefix]
        if direction:
            parts.append(direction)
        if source:
            parts.append(f"from {source}")
        text = " ".join(parts).strip()
        return text if text.endswith(".") else f"{text}."

    if prefix == "Keep gap explicit":
        text = direction or source
        text = f"Keep gap explicit {text}".strip()
        return text if text.endswith(".") else f"{text}."

    text = direction or source
    text = f"Do not add {text}".strip()
    return text if text.endswith(".") else f"{text}."

def _normalize_live_llm_parsed(parsed: Dict[str, Any]) -> Dict[str, Any]:
    raw_rewrite_directions = parsed.get("rewrite_directions", []) or []
    normalized_rewrite_directions = _unique_preserve_order(
        [
            _coerce_live_rewrite_direction(item)
            for item in raw_rewrite_directions
        ]
    )
    normalized_rewrite_directions = [
        item for item in normalized_rewrite_directions
        if item
    ]

    return {
        "recruiter_summary": str(parsed.get("recruiter_summary", "")).strip(),
        "keep_emphasize": _normalize_string_list(parsed.get("keep_emphasize", [])),
        "tailoring_actions": _normalize_string_list(parsed.get("tailoring_actions", [])),
        "do_not_claim": _normalize_string_list(parsed.get("do_not_claim", [])),
        "rewrite_directions": normalized_rewrite_directions,
    }

def _normalize_patch_refinement_parsed(parsed: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "abstain": bool(parsed.get("abstain", False)),
        "refined_patch_text": str(parsed.get("refined_patch_text", "") or "").strip(),
        "reason": str(parsed.get("reason", "") or "").strip(),
        "preserved_terms": _normalize_string_list(parsed.get("preserved_terms", [])),
        "risk_flags": _normalize_string_list(parsed.get("risk_flags", [])),
    }


def _patch_refinement_numeric_tokens(text: str) -> List[str]:
    matches = re.findall(r"\b\d+(?:\.\d+)?(?:k|m)?\+?%?\b", str(text or ""), flags=re.IGNORECASE)
    return _unique_preserve_order([str(item).strip() for item in matches if str(item).strip()])


def _patch_refinement_contains_term(text: str, term: str) -> bool:
    text_norm = re.sub(r"\s+", " ", str(text or "").strip().lower())
    term_norm = re.sub(r"\s+", " ", str(term or "").strip().lower())
    if not text_norm or not term_norm:
        return False
    return term_norm in text_norm


def _patch_refinement_lead_token(text: str) -> str:
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]+", str(text or ""))
    return tokens[0].lower() if tokens else ""


def _collect_patch_refinement_sibling_openings(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
    limit: int = 8,
) -> List[str]:
    source_entry_id = str(
        candidate.get("source_entry_id", "") or candidate.get("entry_id", "")
    ).strip()
    section = str(candidate.get("section", "") or "").strip()
    source = str(candidate.get("source", "") or "").strip()
    original_text = re.sub(r"\s+", " ", str(candidate.get("original_text", "") or "")).strip().lower()

    openings: List[str] = []
    for row in list(payload.get("bullet_diagnoses", []) or []):
        row_text = re.sub(r"\s+", " ", str(row.get("original_text", "") or "")).strip()
        if not row_text or row_text.lower() == original_text:
            continue

        row_entry_id = str(row.get("entry_id", "") or "").strip()
        row_section = str(row.get("section", "") or "").strip()
        row_source = str(row.get("source", "") or "").strip()

        if source_entry_id:
            if row_entry_id != source_entry_id:
                continue
        else:
            if section and row_section != section:
                continue
            if source and row_source != source:
                continue

        lead = _patch_refinement_lead_token(row_text)
        if lead:
            openings.append(lead)

    return _unique_preserve_order(openings)[:limit]


def _patch_refinement_core_terms(candidate: Dict[str, Any]) -> List[str]:
    original_text = str(candidate.get("original_text", "") or "").strip()

    supported_terms = _unique_preserve_order(
        list(candidate.get("supported_jd_signals", []) or [])
        + [str(candidate.get("canonical_supported_signal", "") or "").strip()]
    )
    supported_terms = [term for term in supported_terms if str(term or "").strip()]

    raw_tokens = re.findall(
        r"\b(?:[A-Z]{2,}[A-Za-z0-9.+/\-]*|[A-Z][A-Za-z0-9.+/\-]{2,})\b",
        original_text,
    )

    filtered_tokens: List[str] = []
    for token in raw_tokens:
        token_clean = str(token or "").strip()
        if not token_clean:
            continue
        if token_clean.lower() in _PATCH_REFINEMENT_LEAD_VERB_STOPWORDS:
            continue
        filtered_tokens.append(token_clean)

    return _unique_preserve_order(supported_terms + filtered_tokens)

def _build_patch_refinement_prompt(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
) -> str:
    job = payload.get("job", {}) or {}
    section = str(candidate.get("section", "") or "").strip()
    source = str(candidate.get("source", "") or "").strip()
    original_text = str(candidate.get("original_text", "") or "").strip()
    deterministic_patch_text = str(candidate.get("patch_text", "") or "").strip()
    supported_signals = list(candidate.get("supported_jd_signals", []) or [])
    unsupported_risk_signals = list(candidate.get("unsupported_risk_signals", []) or [])
    adjacent_risk_signals = list(candidate.get("adjacent_risk_signals", []) or [])
    protected_numbers = _patch_refinement_numeric_tokens(original_text)
    protected_core_terms = _patch_refinement_core_terms(candidate)
    sibling_openings = _collect_patch_refinement_sibling_openings(payload, candidate)
    original_lead = _patch_refinement_lead_token(original_text)
    protected_phrases = _patch_refinement_protected_phrases(candidate)

    lines: List[str] = []
    lines.append("Return ONLY valid JSON.")
    lines.append("")
    lines.append("Goal:")
    lines.append("Refine one already-approved deterministic resume bullet rewrite into cleaner final wording.")
    lines.append("")
    lines.append("Hard rules:")
    lines.append("1. Use ONLY the evidence already present in the original bullet.")
    lines.append("2. Do NOT invent tools, methods, ownership, scope, domains, metrics, or responsibilities.")
    lines.append("3. Preserve all numbers, percentages, counts, and metrics exactly unless abstaining.")
    lines.append("4. Keep the same claim strength as the original supported evidence.")
    lines.append("5. Do NOT add unsupported JD terms.")
    lines.append("6. Do NOT drop meaningful technical detail, methods, tools, or the second clause if it carries real evidence.")
    lines.append("7. Carry the same tone, specificity, and technical depth as the original bullet.")
    lines.append("8. Prefer a cleaner non-redundant opening structure when it preserves the same meaning.")
    lines.append("9. If nearby bullets already start with similar verbs, prefer a different opening ONLY when it stays equally truthful and natural.")
    lines.append("10. Do NOT force synonym churn just for variety.")
    lines.append("11. If you cannot materially improve clarity safely, set abstain=true.")
    lines.append("12. Output one bullet only, not commentary.")
    lines.append("13. Do NOT drop meaningful multi-word technical or method phrases from the original bullet.")
    lines.append("14. If your reason is that the original bullet is already strong, concise, or clear, abstain instead of rewriting.")
    lines.append("")
    lines.append("Style target:")
    lines.append("- Sound like a strong real resume bullet, not a keyword shuffle.")
    lines.append("- Keep it concise but do not compress away important evidence.")
    lines.append("- Preserve measurable outcomes and technical nouns.")
    lines.append(f"- Protected substantive phrases: {protected_phrases}")
    lines.append("")
    lines.append("Job context:")
    lines.append(f"- Company: {job.get('company', '')}")
    lines.append(f"- Title: {job.get('title', '')}")
    lines.append("")
    lines.append("Source bullet context:")
    lines.append(f"- Section: {section}")
    lines.append(f"- Source: {source}")
    lines.append(f"- Supported JD signals: {supported_signals}")
    lines.append(f"- Unsupported risk signals: {unsupported_risk_signals}")
    lines.append(f"- Adjacent risk signals: {adjacent_risk_signals}")
    lines.append(f"- Protected numeric tokens: {protected_numbers}")
    lines.append(f"- Protected core technical terms: {protected_core_terms}")
    lines.append(f"- Original lead token: {original_lead}")
    lines.append(f"- Sibling bullet lead tokens to avoid repeating when possible: {sibling_openings}")
    lines.append("")
    lines.append("Original bullet:")
    lines.append(original_text)
    lines.append("")
    lines.append("Deterministic patch draft:")
    lines.append(deterministic_patch_text)
    lines.append("")
    lines.append("Output contract:")
    lines.append("- abstain: boolean")
    lines.append("- refined_patch_text: final bullet text, or empty string if abstaining")
    lines.append("- reason: one short sentence")
    lines.append("- preserved_terms: terms or metrics you intentionally preserved")
    lines.append("- risk_flags: empty list when safe")
    return "\n".join(lines)

def _patch_refinement_similarity_ratio(a: str, b: str) -> float:
    from difflib import SequenceMatcher

    a_norm = re.sub(r"\s+", " ", str(a or "").strip().lower())
    b_norm = re.sub(r"\s+", " ", str(b or "").strip().lower())
    if not a_norm and not b_norm:
        return 1.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()

def _validate_patch_refinement_output(
    candidate: Dict[str, Any],
    refined_patch_text: str,
) -> Tuple[bool, str]:
    refined = re.sub(r"\s+", " ", str(refined_patch_text or "")).strip()
    if not refined:
        return False, "empty_refined_patch"

    original_text = re.sub(r"\s+", " ", str(candidate.get("original_text", "") or "")).strip()
    deterministic_patch_text = re.sub(r"\s+", " ", str(candidate.get("patch_text", "") or "")).strip()

    if refined.lower() == original_text.lower():
        return False, "same_as_original"

    if refined.lower() == deterministic_patch_text.lower():
        return False, "same_as_deterministic"

    similarity_to_original = _patch_refinement_similarity_ratio(refined, original_text)
    similarity_to_deterministic = _patch_refinement_similarity_ratio(refined, deterministic_patch_text)

    if similarity_to_original >= 0.985:
        return False, "near_same_as_original"

    if similarity_to_deterministic >= 0.985:
        return False, "near_same_as_deterministic"
    
    protected_numbers = _patch_refinement_numeric_tokens(original_text)
    refined_norm = refined.lower()
    for token in protected_numbers:
        if token.lower() not in refined_norm:
            return False, f"missing_numeric_token:{token}"
    
    protected_phrases = _patch_refinement_protected_phrases(candidate)
    for phrase in protected_phrases:
        phrase_clean = str(phrase or "").strip()
        if not phrase_clean:
            continue
        if not _patch_refinement_contains_term(refined, phrase_clean):
            return False, f"missing_protected_phrase:{phrase_clean}"

    supported_terms = _unique_preserve_order(
        list(candidate.get("supported_jd_signals", []) or [])
        + [str(candidate.get("canonical_supported_signal", "") or "").strip()]
    )
    supported_terms = [term for term in supported_terms if str(term or "").strip()]

    if supported_terms and not any(_patch_refinement_contains_term(refined, term) for term in supported_terms):
        return False, "missing_supported_signal"

    protected_core_terms = _patch_refinement_core_terms(candidate)
    for term in protected_core_terms:
        term_clean = str(term or "").strip()
        if not term_clean:
            continue
        if not _patch_refinement_contains_term(refined, term_clean):
            return False, f"missing_core_term:{term_clean}"

    original_norm = original_text.lower()
    for term in list(candidate.get("unsupported_risk_signals", []) or []):
        term_clean = str(term or "").strip()
        if not term_clean:
            continue
        if term_clean.lower() in refined_norm and term_clean.lower() not in original_norm:
            return False, f"introduced_unsupported_term:{term_clean}"

    original_words = re.findall(r"\b[\w.+/\-]+\b", original_text)
    refined_words = re.findall(r"\b[\w.+/\-]+\b", refined)

    if len(original_words) >= 18:
        min_words = max(12, int(len(original_words) * 0.72))
        if len(refined_words) < min_words:
            return False, "possible_information_loss"

    return True, "ok"


def _maybe_refine_patch_ready_rewrite_candidate(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
) -> Dict[str, Any]:
    if str(candidate.get("operation_type", "") or "").strip() != "rewrite":
        return candidate

    if str(candidate.get("proposal_status", "") or "").strip() != "patch_ready":
        return candidate

    deterministic_patch_text = str(candidate.get("patch_text", "") or "").strip()
    if not deterministic_patch_text:
        return candidate

    prompt = _build_patch_refinement_prompt(payload, candidate)

    system_prompt = """
You rewrite one resume bullet under strict evidence constraints.

Rules:
1. Use only the supplied original bullet evidence.
2. Do not invent tools, methods, metrics, scope, or ownership.
3. Preserve every numeric metric exactly.
4. Keep the same support level as the original evidence.
5. If the deterministic draft is already as good as you can make it safely, abstain.
6. Return valid JSON only.
"""

    requested_provider = "groq"
    requested_model = "llama-3.3-70b-versatile"

    try:
        llm_result = run_chat_completion_with_metadata(
            provider=requested_provider,
            model=requested_model,
            temperature=PATCH_REFINEMENT_TEMPERATURE,
            max_tokens=PATCH_REFINEMENT_MAX_TOKENS,
            response_mime_type="application/json",
            response_schema=PATCH_REFINEMENT_RESPONSE_SCHEMA,
            return_parsed=True,
            thinking_budget=0,
            fallback_enabled=False,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:
        updated = dict(candidate)
        updated["llm_refinement_used"] = False
        updated["llm_refinement_status"] = "call_failed"
        updated["llm_refinement_note"] = str(exc)
        updated["llm_refinement_requested_provider"] = requested_provider
        updated["llm_refinement_requested_model"] = requested_model
        return updated

    value = llm_result.get("content")
    parsed_raw = None

    if isinstance(value, dict):
        parsed_raw = value
    else:
        parsed_candidate = llm_result.get("parsed")
        if isinstance(parsed_candidate, dict):
            parsed_raw = parsed_candidate
        else:
            raw_text = str(value or "").strip()
            if raw_text:
                try:
                    parsed_raw = _extract_json_from_llm_response(raw_text)
                except Exception as exc:
                    updated = dict(candidate)
                    updated["llm_refinement_used"] = False
                    updated["llm_refinement_status"] = "parse_failed"
                    updated["llm_refinement_note"] = str(exc)
                    updated["llm_refinement_rejected_text"] = raw_text
                    updated["llm_refinement_provider"] = str(
                        llm_result.get("provider", "") or requested_provider
                    ).strip()
                    updated["llm_refinement_model"] = str(
                        llm_result.get("model", "") or requested_model
                    ).strip()
                    updated["llm_refinement_requested_provider"] = requested_provider
                    updated["llm_refinement_requested_model"] = requested_model
                    return updated
            else:
                updated = dict(candidate)
                updated["llm_refinement_used"] = False
                updated["llm_refinement_status"] = "parse_failed"
                updated["llm_refinement_note"] = "empty_llm_response"
                updated["llm_refinement_rejected_text"] = ""
                updated["llm_refinement_provider"] = str(
                    llm_result.get("provider", "") or requested_provider
                ).strip()
                updated["llm_refinement_model"] = str(
                    llm_result.get("model", "") or requested_model
                ).strip()
                updated["llm_refinement_requested_provider"] = requested_provider
                updated["llm_refinement_requested_model"] = requested_model
                return updated

    parsed = _normalize_patch_refinement_parsed(parsed_raw or {})

    updated = dict(candidate)

    reason_text = str(parsed.get("reason", "") or "").strip().lower()
    refined_patch_text = str(parsed.get("refined_patch_text", "") or "").strip()

    if (
        refined_patch_text
        and any(token in reason_text for token in ["already clear", "already concise", "already strong"])
    ):
        updated["llm_refinement_used"] = False
        updated["llm_refinement_status"] = "validation_failed"
        updated["llm_refinement_note"] = "should_have_abstained"
        updated["llm_refinement_rejected_text"] = refined_patch_text
        updated["llm_refinement_provider"] = str(
            llm_result.get("provider", "") or requested_provider
        ).strip()
        updated["llm_refinement_model"] = str(
            llm_result.get("model", "") or requested_model
        ).strip()
        updated["llm_refinement_requested_provider"] = requested_provider
        updated["llm_refinement_requested_model"] = requested_model
        updated["proposal_status"] = "direction_only"
        updated["patch_ready"] = False
        updated["material_delta_found"] = False
        updated["patch_text"] = ""
        updated["proposed_text"] = ""
        updated["materiality_validation_status"] = "llm_abstained_keep_original"
        updated["materiality_validation_note"] = (
            "LLM refinement determined the original bullet is already the best safe wording, "
            "so no final rewrite patch is surfaced."
        )
        return updated

    updated["llm_refinement_provider"] = str(
        llm_result.get("provider", "") or requested_provider
    ).strip()
    updated["llm_refinement_model"] = str(
        llm_result.get("model", "") or requested_model
    ).strip()
    updated["llm_refinement_requested_provider"] = requested_provider
    updated["llm_refinement_requested_model"] = requested_model
    updated["llm_refinement_reason"] = parsed.get("reason", "")
    updated["llm_refinement_preserved_terms"] = list(parsed.get("preserved_terms", []) or [])
    updated["llm_refinement_risk_flags"] = list(parsed.get("risk_flags", []) or [])

    if parsed.get("abstain", False):
        updated["llm_refinement_used"] = False
        updated["llm_refinement_status"] = "abstained"
        updated["llm_refinement_note"] = parsed.get("reason", "")
        updated["llm_refinement_rejected_text"] = str(parsed.get("refined_patch_text", "") or "").strip()
        updated["proposal_status"] = "direction_only"
        updated["patch_ready"] = False
        updated["material_delta_found"] = False
        updated["patch_text"] = ""
        updated["proposed_text"] = ""
        updated["materiality_validation_status"] = "llm_abstained_keep_original"
        updated["materiality_validation_note"] = (
            "LLM refinement abstained because the original bullet is already the strongest safe wording."
        )
        return updated

    is_valid, validation_reason = _validate_patch_refinement_output(candidate, refined_patch_text)

    if not is_valid:
        updated["llm_refinement_used"] = False
        updated["llm_refinement_status"] = "validation_failed"
        updated["llm_refinement_note"] = validation_reason
        updated["llm_refinement_rejected_text"] = refined_patch_text

        if validation_reason in {
            "same_as_original",
            "near_same_as_original",
            "should_have_abstained",
        }:
            updated["proposal_status"] = "direction_only"
            updated["patch_ready"] = False
            updated["material_delta_found"] = False
            updated["patch_text"] = ""
            updated["proposed_text"] = ""
            updated["materiality_validation_status"] = "llm_abstained_keep_original"
            updated["materiality_validation_note"] = (
                "LLM refinement did not produce a materially better final rewrite, so the original bullet is kept."
            )

        return updated

    updated["deterministic_patch_text"] = deterministic_patch_text
    updated["patch_text"] = refined_patch_text
    updated["proposed_text"] = refined_patch_text
    updated["llm_refinement_used"] = True
    updated["llm_refinement_status"] = "accepted"
    updated["llm_refinement_note"] = parsed.get("reason", "")
    updated["patch_generation_method"] = (
        f"{str(candidate.get('patch_generation_method', '') or '').strip()}+llm_refine"
    ).strip("+")

    return updated

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
            normalized["rewrite_directions"] = _canonicalize_live_direction_sources(
                normalized.get("rewrite_directions", []),
                payload,
            )
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
        normalized["rewrite_directions"] = _canonicalize_live_direction_sources(
            normalized.get("rewrite_directions", []),
            payload,
        )
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

