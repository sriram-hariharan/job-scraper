
from typing import Dict, Any, Optional, List, Tuple
import os
import re
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from src.ai.llm_client import (
    FALLBACK_ENABLED as LLM_FALLBACK_ENABLED,
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
    ACTION_VERB_HINTS,
    TAILORING_ROLE_FAMILY_FALLBACK,
    TAILORING_ROLE_FRAMING_PROFILES,
    TAILORING_STYLE_ONLY_CHURN_HINTS,
    TAILORING_WRITER_STRONG_GAIN_TARGETS,
    _SKILL_ALIASES,
)

from src.matching.signal_family_matcher import (
    equivalent_signal_terms,
    normalize_signal_text,
)

_PATCH_REFINEMENT_LEAD_VERB_STOPWORDS = set(ACTION_VERB_HINTS)
LLM_TAILOR_PROVIDER = os.getenv("LLM_TAILOR_PROVIDER", "groq").strip().lower()
LLM_TAILOR_MODEL = os.getenv("LLM_TAILOR_MODEL", "llama-3.3-70b-versatile").strip()
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
    "groq",
).strip().lower()

TAILOR_LLM_FALLBACK_MODEL = os.getenv(
    "TAILOR_LLM_FALLBACK_MODEL",
    "llama-3.3-70b-versatile",
).strip()

LIVE_REWRITE_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "rewrite_directions": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "prefix": {
                        "type": "string",
                        "enum": [
                            "Lead with",
                            "Support with",
                            "Keep gap explicit",
                            "Do not add",
                        ],
                    },
                    "source": {"type": "string"},
                    "direction": {"type": "string"},
                },
                "required": ["prefix", "direction"],
            },
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

PATCH_REFINEMENT_WRITER_PROVIDER = os.getenv(
    "PATCH_REFINEMENT_WRITER_PROVIDER",
    PATCH_REFINEMENT_PROVIDER,
).strip().lower()

PATCH_REFINEMENT_WRITER_MODEL = os.getenv(
    "PATCH_REFINEMENT_WRITER_MODEL",
    PATCH_REFINEMENT_MODEL,
).strip()

PATCH_REFINEMENT_WRITER_MAX_TOKENS = 420
PATCH_REFINEMENT_WRITER_TEMPERATURE = 0
PATCH_REFINEMENT_WRITER_PROMPT_VERSION = "v2"

PATCH_REFINEMENT_JUDGE_PROVIDER = os.getenv(
    "PATCH_REFINEMENT_JUDGE_PROVIDER",
    PATCH_REFINEMENT_PROVIDER,
).strip().lower()

PATCH_REFINEMENT_JUDGE_MODEL = os.getenv(
    "PATCH_REFINEMENT_JUDGE_MODEL",
    "llama-3.3-70b-versatile",
).strip()

PATCH_REFINEMENT_JUDGE_MAX_TOKENS = 500
PATCH_REFINEMENT_JUDGE_TEMPERATURE = 0
PATCH_REFINEMENT_JUDGE_PROMPT_VERSION = "v1"

PATCH_REFINEMENT_WRITER_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "abstain": {"type": "boolean"},
        "abstain_reason": {"type": "string"},
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "patch_text": {"type": "string"},
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
                "required": ["patch_text", "reason", "preserved_terms", "risk_flags"],
            },
        },
    },
    "required": ["abstain", "abstain_reason", "options"],
}

PATCH_REFINEMENT_JUDGE_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "winner": {"type": "string"},
        "reason": {"type": "string"},
        "rejected_options": {
            "type": "array",
            "items": {"type": "string"},
        },
        "quality_flags": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["winner", "reason", "rejected_options", "quality_flags"],
}

def _parse_patch_refinement_writer_text(raw_text: str) -> Dict[str, Any]:
    text = str(raw_text or "").strip()
    if not text:
        return {
            "abstain": True,
            "abstain_reason": "empty_writer_response",
            "options": [],
        }

    cleaned = text.replace("```", "").strip()

    if cleaned.startswith("{"):
        try:
            parsed = _extract_json_from_llm_response(cleaned)
            return _normalize_patch_refinement_writer_parsed(parsed)
        except Exception:
            pass

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    options: List[Dict[str, Any]] = []

    abstain_match = re.match(r"(?is)^abstain\s*:\s*(.+)$", cleaned)
    if abstain_match:
        return {
            "abstain": True,
            "abstain_reason": abstain_match.group(1).strip(),
            "options": [],
        }

    for line in lines:
        match = re.match(r"(?i)^option[_ ]?([12])\s*:\s*(.+)$", line)
        if not match:
            continue

        patch_text = str(match.group(2) or "").strip()
        if not patch_text:
            continue

        options.append(
            {
                "patch_text": patch_text,
                "reason": "",
                "preserved_terms": [],
                "risk_flags": [],
            }
        )

    return {
        "abstain": False if options else True,
        "abstain_reason": "" if options else "no_parseable_writer_options",
        "options": options[:2],
    }

def _partition_writer_options_by_validation(
    candidate: Dict[str, Any],
    writer_options: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    valid_options: List[Dict[str, Any]] = []
    invalid_options: List[Dict[str, Any]] = []

    for idx, option in enumerate(writer_options or [], start=1):
        patch_text = str(option.get("patch_text", "") or "").strip()
        normalized = {
            "option_id": f"writer_option_{idx}",
            "patch_text": patch_text,
            "reason": str(option.get("reason", "") or "").strip(),
            "preserved_terms": list(option.get("preserved_terms", []) or []),
            "risk_flags": list(option.get("risk_flags", []) or []),
        }

        is_valid, validation_reason = _validate_patch_refinement_output(candidate, patch_text)
        if is_valid:
            valid_options.append(normalized)
        else:
            invalid_options.append(
                {
                    **normalized,
                    "validation_reason": str(validation_reason or "").strip(),
                }
            )

    return valid_options, invalid_options

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
    lines.append('- Each rewrite_directions item must be an object with exactly these keys: {"prefix": "...", "source": "...", "direction": "..."}')
    lines.append('- Allowed prefix values only: "Lead with", "Support with", "Keep gap explicit", "Do not add"')
    lines.append('- For "Lead with" and "Support with", source is REQUIRED and must be the exact source label copied from the evidence.')
    lines.append('- For "Keep gap explicit" and "Do not add", source may be an empty string.')
    lines.append('- Never return free-form string items inside rewrite_directions.')
    lines.append('- When using Lead with or Support with, copy the exact source label only, for example: "Data Analyst II @ Accenture".')
    lines.append('- Never use section labels like "Primary anchor evidence units 1", "Secondary supporting evidence units", or wrappers like "[experience] ... | type=same_source_context" as the source.')
    lines.append("- Prefer anchor-led rewrite directions first, then support if needed.")
    lines.append('- direction must be a short edit-instruction fragment, not a full rewritten bullet.')
    lines.append('- For "Lead with" and "Support with", direction must be 20 words or fewer.')
    lines.append('- Do NOT paste or closely paraphrase the evidence bullet text into direction.')
    lines.append('- Good direction example: "sql and python in opening clause; preserve risk-reduction outcome"')
    lines.append('- Bad direction example: "Drove lapse and retention risk assessments using Python and customer segmentation with SQL..."')

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

def _coerce_llm_content_text(value: Any) -> str:
    if isinstance(value, str):
        return str(value).strip()

    if isinstance(value, dict):
        if "text" in value and value.get("text"):
            return str(value.get("text") or "").strip()
        if "content" in value and value.get("content"):
            return str(value.get("content") or "").strip()

    if isinstance(value, list):
        parts: List[str] = []
        for item in value:
            if isinstance(item, str):
                text = str(item).strip()
                if text:
                    parts.append(text)
                continue

            if isinstance(item, dict):
                if item.get("type") == "text" and item.get("text"):
                    text = str(item.get("text") or "").strip()
                    if text:
                        parts.append(text)
                    continue

                if item.get("content"):
                    text = str(item.get("content") or "").strip()
                    if text:
                        parts.append(text)
                    continue

        return "\n".join(parts).strip()

    return str(value or "").strip()


def _normalize_json_like_text(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""

    value = value.replace("```json", "```").replace("```JSON", "```")
    value = value.replace("```", "").strip()

    value = (
        value.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )

    value = re.sub(r",(\s*[}\]])", r"\1", value)
    return value.strip()


def _extract_first_balanced_json_object(text: str) -> str:
    value = str(text or "")
    start = value.find("{")
    if start == -1:
        return ""

    depth = 0
    in_string = False
    escape = False

    for idx in range(start, len(value)):
        ch = value[idx]

        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            depth += 1
            continue

        if ch == "}":
            depth -= 1
            if depth == 0:
                return value[start : idx + 1].strip()

    return ""

def _parse_patch_refinement_judge_text(raw_text: str) -> Dict[str, Any]:
    text = str(raw_text or "").strip()
    if not text:
        return {
            "winner": "abstain",
            "reason": "empty_judge_response",
            "rejected_options": [],
            "quality_flags": [],
        }

    cleaned = text.replace("```", "").strip()

    if cleaned.startswith("{"):
        try:
            parsed = _extract_json_from_llm_response(cleaned)
            return _normalize_patch_refinement_judge_parsed(parsed)
        except Exception:
            pass

    winner = "abstain"
    reason = ""
    rejected_options: List[str] = []
    quality_flags: List[str] = []

    for line in [line.strip() for line in cleaned.splitlines() if line.strip()]:
        winner_match = re.match(r"(?i)^winner\s*:\s*(.+)$", line)
        if winner_match:
            candidate = winner_match.group(1).strip()
            if candidate in {"deterministic", "writer_option_1", "writer_option_2", "abstain"}:
                winner = candidate
            continue

        reason_match = re.match(r"(?i)^reason\s*:\s*(.+)$", line)
        if reason_match:
            reason = reason_match.group(1).strip()
            continue

        rejected_match = re.match(r"(?i)^rejected(?:_options)?\s*:\s*(.+)$", line)
        if rejected_match:
            raw = rejected_match.group(1).strip()
            if raw.lower() != "none":
                rejected_options = [part.strip() for part in raw.split(",") if part.strip()]
            continue

        flags_match = re.match(r"(?i)^quality_flags?\s*:\s*(.+)$", line)
        if flags_match:
            raw = flags_match.group(1).strip()
            if raw.lower() != "none":
                quality_flags = [part.strip() for part in raw.split(",") if part.strip()]
            continue

    return {
        "winner": winner,
        "reason": reason,
        "rejected_options": rejected_options,
        "quality_flags": quality_flags,
    }

def _run_patch_refinement_judge_plain_call(
    *,
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    system_prompt: str,
    user_prompt: str,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, str], Optional[str], str]:
    requested_provider = str(provider or "").strip().lower()
    requested_model = str(model or "").strip()

    metadata = {
        "requested_provider": requested_provider,
        "requested_model": requested_model,
        "provider": requested_provider,
        "model": requested_model,
    }

    try:
        llm_result = run_chat_completion_with_metadata(
            provider=requested_provider,
            model=requested_model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_mime_type=None,
            response_schema=None,
            return_parsed=False,
            thinking_budget=0,
            fallback_enabled=False,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        return None, metadata, "call_failed", str(exc)

    metadata["provider"] = str(llm_result.get("provider", "") or requested_provider).strip()
    metadata["model"] = str(llm_result.get("model", "") or requested_model).strip()

    raw_text = _coerce_llm_content_text(llm_result.get("content"))
    if not raw_text:
        return None, metadata, "empty_llm_response", ""

    parsed = _parse_patch_refinement_judge_text(raw_text)
    return parsed, metadata, None, raw_text

def _extract_json_from_llm_response(response: str) -> dict:
    raw = _normalize_json_like_text(response)
    if not raw:
        raise ValueError("Empty LLM response")

    candidates: List[str] = []

    def _add_candidate(text: str) -> None:
        candidate = _normalize_json_like_text(text)
        if not candidate:
            return

        if candidate not in candidates:
            candidates.append(candidate)

        balanced = _extract_first_balanced_json_object(candidate)
        if balanced and balanced not in candidates:
            candidates.append(balanced)

        escaped = _escape_control_chars_inside_json_strings(candidate)
        if escaped and escaped not in candidates:
            candidates.append(escaped)

        balanced_escaped = _extract_first_balanced_json_object(escaped)
        if balanced_escaped and balanced_escaped not in candidates:
            candidates.append(balanced_escaped)

    _add_candidate(raw)

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

def _live_rewrite_similarity_ratio(a: str, b: str) -> float:
    from difflib import SequenceMatcher

    a_norm = re.sub(r"\s+", " ", str(a or "").strip().lower())
    b_norm = re.sub(r"\s+", " ", str(b or "").strip().lower())

    if not a_norm or not b_norm:
        return 0.0

    return SequenceMatcher(None, a_norm, b_norm).ratio()


def _live_rewrite_source_texts_for_label(
    payload: Dict[str, Any],
    source_label: str,
) -> List[str]:
    evidence_layers = payload.get("evidence_layers", {}) or {}
    alias_map = _build_live_source_alias_map(payload)

    source_key = str(source_label or "").strip().rstrip(".")
    canonical = (
        alias_map.get(source_key)
        or alias_map.get(_cleanup_live_source_label(source_key))
        or _cleanup_live_source_label(source_key)
    )

    texts: List[str] = []

    for bucket in ("anchors", "supports", "context"):
        for row in list(evidence_layers.get(bucket, []) or [])[:4]:
            if _display_row_source(row) != canonical:
                continue

            for value in (row.get("text"), row.get("parent_bullet")):
                text = re.sub(r"\s+", " ", str(value or "").strip())
                if text:
                    texts.append(text)

    return _unique_preserve_order(texts)

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

def _canonicalize_live_direction_objects(
    directions: List[Dict[str, Any]],
    payload: Dict[str, Any],
) -> List[Dict[str, str]]:
    alias_map = _build_live_source_alias_map(payload)
    normalized: List[Dict[str, str]] = []
    seen = set()

    for item in directions or []:
        if not isinstance(item, dict):
            continue

        prefix = str(item.get("prefix", "") or "").strip()
        source = str(item.get("source", "") or "").strip()
        direction = str(item.get("direction", "") or "").strip()

        if prefix not in {"Lead with", "Support with", "Keep gap explicit", "Do not add"}:
            continue
        if not direction:
            continue

        canonical_source = source
        if prefix in {"Lead with", "Support with"}:
            source_clean = source.rstrip(".").strip()
            canonical_source = alias_map.get(source_clean)
            if canonical_source is None:
                canonical_source = alias_map.get(_cleanup_live_source_label(source_clean))
            if canonical_source is None:
                canonical_source = _cleanup_live_source_label(source_clean) or source_clean
        else:
            canonical_source = ""

        normalized_item = {
            "prefix": prefix,
            "source": canonical_source,
            "direction": direction,
        }

        dedupe_key = (
            normalized_item["prefix"],
            normalized_item["source"],
            normalized_item["direction"],
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(normalized_item)

    return normalized

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

def _validate_live_llm_parsed_contract(
    parsed: Dict[str, Any],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(parsed, dict):
        raise ValueError("live_llm_contract_not_object")

    directions = parsed.get("rewrite_directions", [])
    if not isinstance(directions, list):
        raise ValueError("live_llm_contract_rewrite_directions_not_list")
    if not directions:
        raise ValueError("live_llm_contract_empty_rewrite_directions")

    anchors = list(((payload.get("evidence_layers", {}) or {}).get("anchors", []) or []))[:4]
    alias_map = _build_live_source_alias_map(payload)

    validated: List[Dict[str, str]] = []

    for idx, item in enumerate(directions, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"live_llm_contract_direction_{idx}_not_object")

        prefix = str(item.get("prefix", "") or "").strip()
        source = str(item.get("source", "") or "").strip()
        direction = str(item.get("direction", "") or "").strip()

        if prefix not in {"Lead with", "Support with", "Keep gap explicit", "Do not add"}:
            raise ValueError(f"live_llm_contract_direction_{idx}_bad_prefix:{prefix}")

        if not direction:
            raise ValueError(f"live_llm_contract_direction_{idx}_missing_direction")

        if prefix in {"Lead with", "Support with"}:
            if not source:
                raise ValueError(f"live_llm_contract_direction_{idx}_missing_source")

            source_key = source.rstrip(".").strip()
            if (
                source_key not in alias_map
                and _cleanup_live_source_label(source_key) not in alias_map
            ):
                raise ValueError(
                    f"live_llm_contract_direction_{idx}_unknown_source:{source_key}"
                )
            
            direction_word_count = len(re.findall(r"\b[\w.+/\-]+\b", direction))
            if direction_word_count > 20:
                raise ValueError(
                    f"live_llm_contract_direction_{idx}_too_long:{direction_word_count}"
                )

            source_texts = _live_rewrite_source_texts_for_label(payload, source_key)
            if any(
                _live_rewrite_similarity_ratio(direction, source_text) >= 0.82
                for source_text in source_texts
            ):
                raise ValueError(
                    f"live_llm_contract_direction_{idx}_copies_source_text"
                )

        validated.append(
            {
                "prefix": prefix,
                "source": source,
                "direction": direction,
            }
        )

    if anchors:
        if len(validated) < 3:
            raise ValueError("live_llm_contract_anchor_case_requires_3_directions")

        if not any(item["prefix"] in {"Lead with", "Support with"} for item in validated):
            raise ValueError("live_llm_contract_anchor_case_requires_anchor_direction")

        if all(item["prefix"] == "Keep gap explicit" for item in validated):
            raise ValueError("live_llm_contract_anchor_case_gap_only")

    return {
        "rewrite_directions": validated,
    }

def _normalize_live_llm_parsed(parsed: Dict[str, Any]) -> Dict[str, Any]:
    raw_rewrite_directions = parsed.get("rewrite_directions", []) or []

    structured_rewrite_directions: List[Dict[str, str]] = []
    if isinstance(raw_rewrite_directions, list):
        for item in raw_rewrite_directions:
            if not isinstance(item, dict):
                continue

            prefix = str(item.get("prefix", "") or "").strip()
            source = str(item.get("source", "") or "").strip()
            direction = str(item.get("direction", "") or "").strip()

            if prefix not in {"Lead with", "Support with", "Keep gap explicit", "Do not add"}:
                continue
            if not direction:
                continue

            structured_rewrite_directions.append(
                {
                    "prefix": prefix,
                    "source": source,
                    "direction": direction,
                }
            )

    normalized_rewrite_directions = _unique_preserve_order(
        [
            _coerce_live_rewrite_direction(item)
            for item in structured_rewrite_directions
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
        "rewrite_directions_structured": structured_rewrite_directions,
    }

def _stamp_patch_refinement_baseline(candidate: Dict[str, Any]) -> Dict[str, Any]:
    stamped = dict(candidate)
    stamped["llm_pre_refinement_patch_text"] = str(candidate.get("patch_text", "") or "").strip()
    stamped["llm_pre_refinement_patch_generation_method"] = str(candidate.get("patch_generation_method", "") or "").strip()
    stamped["llm_pre_refinement_materiality_validation_status"] = str(candidate.get("materiality_validation_status", "") or "").strip()
    stamped["llm_pre_refinement_materiality_validation_note"] = str(candidate.get("materiality_validation_note", "") or "").strip()
    stamped["llm_pre_refinement_precheck_projected_overall_delta"] = candidate.get("precheck_projected_overall_delta")
    stamped["llm_pre_refinement_precheck_projected_dimension_deltas"] = dict(candidate.get("precheck_projected_dimension_deltas", {}) or {})
    stamped["llm_pre_refinement_precheck_scorer_visible_evidence_changed"] = bool(
        candidate.get("precheck_scorer_visible_evidence_changed", False)
    )
    stamped["llm_pre_refinement_precheck_evidence_delta"] = dict(candidate.get("precheck_evidence_delta", {}) or {})
    return stamped

def _normalize_patch_refinement_parsed(parsed: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "abstain": bool(parsed.get("abstain", False)),
        "refined_patch_text": str(parsed.get("refined_patch_text", "") or "").strip(),
        "reason": str(parsed.get("reason", "") or "").strip(),
        "preserved_terms": _normalize_string_list(parsed.get("preserved_terms", [])),
        "risk_flags": _normalize_string_list(parsed.get("risk_flags", [])),
    }

def _normalize_patch_refinement_writer_parsed(parsed: Dict[str, Any]) -> Dict[str, Any]:
    raw_options = parsed.get("options", []) or []
    options: List[Dict[str, Any]] = []
    seen = set()

    for item in raw_options:
        if not isinstance(item, dict):
            continue

        patch_text = str(item.get("patch_text", "") or "").strip()
        reason = str(item.get("reason", "") or "").strip()

        if not patch_text:
            continue

        key = re.sub(r"\s+", " ", patch_text.strip().lower())
        if key in seen:
            continue
        seen.add(key)

        options.append(
            {
                "patch_text": patch_text,
                "reason": reason,
                "preserved_terms": _normalize_string_list(item.get("preserved_terms", [])),
                "risk_flags": _normalize_string_list(item.get("risk_flags", [])),
            }
        )

        if len(options) >= 2:
            break

    return {
        "abstain": bool(parsed.get("abstain", False)),
        "abstain_reason": str(parsed.get("abstain_reason", "") or "").strip(),
        "options": options,
    }

def _partition_writer_options_by_validation(
    candidate: Dict[str, Any],
    writer_options: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    valid_options: List[Dict[str, Any]] = []
    invalid_options: List[Dict[str, Any]] = []

    for idx, option in enumerate(writer_options or [], start=1):
        patch_text = str(option.get("patch_text", "") or "").strip()
        normalized = {
            "option_id": f"writer_option_{idx}",
            "patch_text": patch_text,
            "reason": str(option.get("reason", "") or "").strip(),
            "preserved_terms": list(option.get("preserved_terms", []) or []),
            "risk_flags": list(option.get("risk_flags", []) or []),
        }

        is_valid, validation_reason = _validate_patch_refinement_output(candidate, patch_text)
        if is_valid:
            valid_options.append(normalized)
        else:
            invalid_options.append(
                {
                    **normalized,
                    "validation_reason": str(validation_reason or "").strip(),
                }
            )

    return valid_options, invalid_options

def _normalize_patch_refinement_judge_parsed(parsed: Dict[str, Any]) -> Dict[str, Any]:
    winner = str(parsed.get("winner", "") or "").strip()
    if winner not in {"deterministic", "writer_option_1", "writer_option_2", "abstain"}:
        winner = "abstain"

    return {
        "winner": winner,
        "reason": str(parsed.get("reason", "") or "").strip(),
        "rejected_options": _normalize_string_list(parsed.get("rejected_options", [])),
        "quality_flags": _normalize_string_list(parsed.get("quality_flags", [])),
    }


def _run_patch_refinement_structured_call(
    *,
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    response_mime_type: Optional[str] = "application/json",
    response_schema: Optional[Dict[str, Any]] = None,
    system_prompt: str,
    user_prompt: str,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, str], Optional[str], str]:
    requested_provider = str(provider or "").strip().lower()
    requested_model = str(model or "").strip()

    metadata = {
        "requested_provider": requested_provider,
        "requested_model": requested_model,
        "provider": requested_provider,
        "model": requested_model,
    }

    try:
        llm_result = run_chat_completion_with_metadata(
            provider=requested_provider,
            model=requested_model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_mime_type=response_mime_type,
            response_schema=response_schema,
            return_parsed=True,
            thinking_budget=0,
            fallback_enabled=False,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        return None, metadata, "call_failed", str(exc)

    metadata["provider"] = str(
        llm_result.get("provider", "") or requested_provider
    ).strip()
    metadata["model"] = str(
        llm_result.get("model", "") or requested_model
    ).strip()

    value = llm_result.get("content")
    parsed_raw = None
    raw_text = ""

    if isinstance(value, dict):
        parsed_raw = value
    else:
        parsed_candidate = llm_result.get("parsed")
        if isinstance(parsed_candidate, dict):
            parsed_raw = parsed_candidate
        else:
            raw_text = _coerce_llm_content_text(value)
            if raw_text:
                try:
                    parsed_raw = _extract_json_from_llm_response(raw_text)
                except Exception as exc:
                    return None, metadata, "parse_failed", str(exc)
            else:
                return None, metadata, "parse_failed", "empty_llm_response"

    return parsed_raw or {}, metadata, None, raw_text

def _run_patch_refinement_writer_plain_call(
    *,
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    system_prompt: str,
    user_prompt: str,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, str], Optional[str], str]:
    requested_provider = str(provider or "").strip().lower()
    requested_model = str(model or "").strip()

    metadata = {
        "requested_provider": requested_provider,
        "requested_model": requested_model,
        "provider": requested_provider,
        "model": requested_model,
    }

    try:
        llm_result = run_chat_completion_with_metadata(
            provider=requested_provider,
            model=requested_model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_mime_type=None,
            response_schema=None,
            return_parsed=False,
            thinking_budget=0,
            fallback_enabled=False,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        return None, metadata, "call_failed", str(exc)

    metadata["provider"] = str(llm_result.get("provider", "") or requested_provider).strip()
    metadata["model"] = str(llm_result.get("model", "") or requested_model).strip()

    raw_text = _coerce_llm_content_text(llm_result.get("content"))
    if not raw_text:
        return None, metadata, "empty_llm_response", ""

    parsed = _parse_patch_refinement_writer_text(raw_text)
    return parsed, metadata, None, raw_text

def _patch_refinement_job_text_blocks(payload: Dict[str, Any]) -> List[str]:
    job = payload.get("job", {}) or {}
    blocks: List[str] = []

    for key in (
        "description",
        "job_description",
        "text",
        "content",
        "summary",
        "responsibilities",
        "requirements",
        "qualifications",
        "preferred_qualifications",
        "basic_qualifications",
    ):
        value = job.get(key)
        if isinstance(value, str):
            text = re.sub(r"\s+", " ", value).strip()
            if text:
                blocks.append(text)
        elif isinstance(value, list):
            for item in value:
                text = re.sub(r"\s+", " ", str(item or "")).strip()
                if text:
                    blocks.append(text)

    return _unique_preserve_order(blocks)


def _patch_refinement_title_terms(payload: Dict[str, Any]) -> List[str]:
    job = payload.get("job", {}) or {}
    title = str(job.get("title", "") or "").strip()
    if not title:
        return []

    raw_terms = re.findall(r"[A-Za-z0-9\+\#\-]+", title.lower())
    return _unique_preserve_order(
        [term for term in raw_terms if len(term) > 2 and term not in {"and", "senior"}]
    )


def _patch_refinement_alignment_terms(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
) -> List[str]:
    summary = payload.get("summary", {}) or {}

    supported_terms = [
        str(item).strip()
        for item in (
            list(candidate.get("supported_jd_signals", []) or [])
            + [str(candidate.get("canonical_supported_signal", "") or "").strip()]
            + list(summary.get("matched_terms", []) or [])
        )
        if str(item).strip()
    ]

    expanded: List[str] = []
    for term in supported_terms:
        expanded.append(term)
        expanded.extend(list(equivalent_signal_terms(term) or []))

    return _unique_preserve_order(
        [str(term).strip() for term in expanded if str(term).strip()]
    )


def _split_patch_refinement_jd_snippets(text: str) -> List[str]:
    raw = re.split(r"(?<=[.!?])\s+|\n+", str(text or ""))
    snippets: List[str] = []

    for item in raw:
        snippet = re.sub(r"\s+", " ", str(item or "").strip())
        if len(snippet) >= 40:
            snippets.append(snippet)

    return _unique_preserve_order(snippets)


def _patch_refinement_alignment_context(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
    max_snippets: int = 2,
) -> Dict[str, Any]:
    matched_terms = _patch_refinement_alignment_terms(payload, candidate)
    normalized_terms = {
        normalize_signal_text(term)
        for term in matched_terms
        if normalize_signal_text(term)
    }
    title_terms = set(_patch_refinement_title_terms(payload))

    scored: List[Tuple[int, int, str]] = []

    for block in _patch_refinement_job_text_blocks(payload):
        for snippet in _split_patch_refinement_jd_snippets(block):
            normalized_snippet = normalize_signal_text(snippet)
            snippet_lower = snippet.lower()

            matched_hits = [
                term for term in normalized_terms
                if term and term in normalized_snippet
            ]
            title_hits = [
                term for term in title_terms
                if term and term in snippet_lower
            ]

            if not matched_hits and not title_hits:
                continue

            score = len(matched_hits) * 10 + len(title_hits)
            scored.append((score, len(snippet), snippet))

    scored.sort(key=lambda row: (-row[0], row[1], row[2]))

    matched_snippets: List[str] = []
    for _, _, snippet in scored:
        if snippet not in matched_snippets:
            matched_snippets.append(snippet)
        if len(matched_snippets) >= max_snippets:
            break

    return {
        "matched_jd_terms": matched_terms[:12],
        "matched_jd_snippets": matched_snippets,
        "title_terms": sorted(title_terms),
    }

def _patch_refinement_role_family(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
) -> str:
    job = payload.get("job", {}) or {}
    title = str(job.get("title", "") or "").lower()

    candidate_terms = _unique_preserve_order(
        [
            str(item).strip().lower()
            for item in (
                list(candidate.get("supported_jd_signals", []) or [])
                + [str(candidate.get("canonical_supported_signal", "") or "").strip()]
            )
            if str(item).strip()
        ]
    )
    candidate_terms.extend(
        [
            str(item).strip().lower()
            for item in list(payload.get("summary", {}).get("matched_terms", []) or [])
            if str(item).strip()
        ]
    )
    candidate_term_text = " ".join(_unique_preserve_order(candidate_terms))

    best_family = TAILORING_ROLE_FAMILY_FALLBACK
    best_score = -1

    for family_name, profile in TAILORING_ROLE_FRAMING_PROFILES.items():
        score = 0

        for token in profile.get("title_tokens_any", []) or []:
            token_clean = str(token).strip().lower()
            if token_clean and token_clean in title:
                score += 3

        for term in profile.get("signal_terms_any", []) or []:
            term_clean = str(term).strip().lower()
            if term_clean and term_clean in candidate_term_text:
                score += 1

        if score > best_score:
            best_score = score
            best_family = family_name

    return best_family


def _patch_refinement_role_profile(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
) -> Dict[str, Any]:
    family = _patch_refinement_role_family(payload, candidate)
    profile = dict(TAILORING_ROLE_FRAMING_PROFILES.get(family, {}) or {})
    profile["family_name"] = family
    return profile


def _patch_refinement_style_only_delta(
    deterministic_patch_text: str,
    candidate_patch_text: str,
) -> bool:
    det = str(deterministic_patch_text or "").strip().lower()
    cand = str(candidate_patch_text or "").strip().lower()

    if not det or not cand or det == cand:
        return True

    det_tokens = re.findall(r"[a-zA-Z0-9\+\#\-]+", det)
    cand_tokens = re.findall(r"[a-zA-Z0-9\+\#\-]+", cand)

    det_set = set(det_tokens)
    cand_set = set(cand_tokens)
    added = cand_set - det_set

    if not added:
        return True

    meaningful_added = {
        token for token in added
        if token not in {item.lower() for item in TAILORING_STYLE_ONLY_CHURN_HINTS}
    }

    return len(meaningful_added) == 0


def _patch_refinement_deterministic_alignment_sufficient(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
) -> Tuple[bool, str]:
    deterministic_patch_text = str(candidate.get("patch_text", "") or "").strip()
    if not deterministic_patch_text:
        return False, ""

    alignment = _patch_refinement_alignment_context(payload, candidate)
    matched_terms = [
        str(term).strip()
        for term in list(alignment.get("matched_jd_terms", []) or [])
        if str(term).strip()
    ]
    if not matched_terms:
        return False, ""

    surfaced_terms = [
        term for term in matched_terms
        if _patch_refinement_contains_term_or_alias(deterministic_patch_text, term)
    ]

    protected_phrases = _patch_refinement_protected_phrases(candidate)
    supported_phrase_set = {
        normalize_signal_text(term)
        for term in (
            list(candidate.get("supported_jd_signals", []) or [])
            + [str(candidate.get("canonical_supported_signal", "") or "").strip()]
        )
        if str(term or "").strip()
    }

    missing_protected = []
    for phrase in protected_phrases:
        phrase_clean = str(phrase or "").strip()
        if not phrase_clean:
            continue

        phrase_norm = normalize_signal_text(phrase_clean)
        if phrase_norm in supported_phrase_set:
            if not _patch_refinement_contains_term_or_alias(deterministic_patch_text, phrase_clean):
                missing_protected.append(phrase_clean)
            continue

        if phrase_clean.lower() not in deterministic_patch_text.lower():
            missing_protected.append(phrase_clean)

    if surfaced_terms and not missing_protected:
        return True, (
            "deterministic patch already surfaces matched JD vocabulary clearly "
            "while preserving protected phrases"
        )

    return False, ""

def _patch_refinement_protected_numbers(candidate: Dict[str, Any]) -> List[str]:
    original_text = str(candidate.get("original_text", "") or "").strip()
    return _patch_refinement_numeric_tokens(original_text)


def _patch_refinement_protected_core_terms(candidate: Dict[str, Any]) -> List[str]:
    return _patch_refinement_core_terms(candidate)


def _patch_refinement_sibling_openings(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
) -> List[str]:
    return _collect_patch_refinement_sibling_openings(payload, candidate)

def _build_patch_refinement_writer_prompt(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
) -> str:
    job = payload.get("job", {}) or {}
    original_text = str(candidate.get("original_text", "") or "").strip()
    deterministic_patch_text = str(candidate.get("patch_text", "") or "").strip()
    original_lead = _patch_refinement_lead_token(original_text)

    supported_signals = _unique_preserve_order(
        [
            str(item).strip()
            for item in (
                list(candidate.get("supported_jd_signals", []) or [])
                + [str(candidate.get("canonical_supported_signal", "") or "").strip()]
            )
            if str(item).strip()
        ]
    )
    protected_numbers = _patch_refinement_protected_numbers(candidate)
    protected_core_terms = _patch_refinement_protected_core_terms(candidate)
    protected_phrases = _patch_refinement_protected_phrases(candidate)
    sibling_openings = _patch_refinement_sibling_openings(payload, candidate)
    alignment = _patch_refinement_alignment_context(payload, candidate)
    role_profile = _patch_refinement_role_profile(payload, candidate)

    lines: List[str] = []
    lines.append("Return plain text only.")
    lines.append("")
    lines.append("You are the WRITER stage for one resume-bullet rewrite.")
    lines.append("")
    lines.append("Primary objective:")
    lines.append("Produce up to 2 stronger final bullet options only when they are clearly better than the deterministic draft in supported JD alignment or supported business/result framing.")
    lines.append("")
    lines.append("Improvement priority order:")
    lines.append("1. Stronger supported JD signal salience.")
    lines.append("2. Stronger supported business/result framing.")
    lines.append("3. Stronger specificity.")
    lines.append("4. Otherwise abstain.")
    lines.append("")
    lines.append("Hard rules:")
    lines.append("1. Use ONLY the original bullet evidence.")
    lines.append("2. Do NOT invent tools, methods, scope, ownership, metrics, or domains.")
    lines.append("3. Preserve every numeric token exactly.")
    lines.append("4. Preserve protected phrases and core technical terms.")
    lines.append("5. Preserve the same factual claim strength.")
    lines.append("6. Keep the same opening tense/style as the original bullet.")
    lines.append("7. Keep the same original lead action word.")
    lines.append("8. Do NOT switch to gerund/opening-phrase style like Using, With, By, Through, or Via.")
    lines.append("9. Do NOT output keyword shuffle, synonym churn, or style-only smoothing.")
    lines.append("10. Do NOT mirror JD phrasing unless the mirrored term is already supported by the bullet.")
    lines.append("11. Borrow terminology, not whole JD sentence structure.")
    lines.append("12. If the best change is only stylistic, abstain.")
    lines.append("13. Do NOT replace a preserved protected phrase with a broader paraphrase.")
    lines.append("14. Do NOT change only connective wording such as using, leveraging, to enhance, or which improved unless the rewrite also adds stronger supported alignment.")
    lines.append("")
    lines.append("Quality bar:")
    lines.append("- stronger supported alignment, not just smoother wording")
    lines.append("- stronger supported business/result framing when available")
    lines.append("- same claim, same evidence, same tone")
    lines.append("- no keyword stuffing")
    lines.append("- no awkward ATS bait phrasing")
    lines.append("")
    lines.append(f"Resolved role family: {role_profile.get('family_name', TAILORING_ROLE_FAMILY_FALLBACK)}")
    lines.append(f"Role-family ATS priority terms: {role_profile.get('ats_priority_terms_any', [])}")
    lines.append(f"Role-family facet priority order: {role_profile.get('facet_priority_order', [])}")
    lines.append(f"Strong gain targets: {TAILORING_WRITER_STRONG_GAIN_TARGETS}")
    lines.append("Role-family appeal targets:")
    for item in role_profile.get("appeal_targets", []) or []:
        lines.append(f"- {item}")
    if not (role_profile.get("appeal_targets", []) or []):
        lines.append("- none")
    lines.append("")
    lines.append(f"Job company: {job.get('company', '')}")
    lines.append(f"Job title: {job.get('title', '')}")
    lines.append(f"Original lead token: {original_lead}")
    lines.append(f"Sibling bullet openings to avoid repeating when possible: {sibling_openings or []}")
    lines.append(f"Supported JD signals: {supported_signals}")
    lines.append(f"Matched JD terms you may surface more clearly: {alignment.get('matched_jd_terms', [])}")
    lines.append(f"Protected numeric tokens: {protected_numbers}")
    lines.append(f"Protected core technical terms: {protected_core_terms}")
    lines.append(f"Protected substantive phrases: {protected_phrases}")
    lines.append("")
    lines.append("Matched JD snippets (borrow terminology only, do not copy long phrasing):")
    for snippet in alignment.get("matched_jd_snippets", []) or []:
        lines.append(f"- {snippet}")
    if not (alignment.get("matched_jd_snippets", []) or []):
        lines.append("- none")
    lines.append("")
    lines.append("Original bullet:")
    lines.append(original_text)
    lines.append("")
    lines.append("Deterministic draft:")
    lines.append(deterministic_patch_text)
    lines.append("")
    lines.append("Output contract:")
    lines.append("Return plain text only.")
    lines.append("Do NOT use markdown.")
    lines.append("Do NOT use code fences.")
    lines.append("Either return exactly:")
    lines.append("ABSTAIN: <short reason>")
    lines.append("Or return up to two lines in exactly this format:")
    lines.append("OPTION_1: <single rewritten bullet>")
    lines.append("OPTION_2: <single rewritten bullet>")
    return "\n".join(lines)


def _build_patch_refinement_judge_prompt(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
    writer_options: List[Dict[str, Any]],
) -> str:
    original_text = str(candidate.get("original_text", "") or "").strip()
    deterministic_patch_text = str(candidate.get("patch_text", "") or "").strip()
    original_lead = _patch_refinement_lead_token(original_text)
    alignment = _patch_refinement_alignment_context(payload, candidate)
    role_profile = _patch_refinement_role_profile(payload, candidate)

    lines: List[str] = []
    lines.append("Return plain text only.")
    lines.append("")
    lines.append("You are the JUDGE stage for one resume-bullet rewrite.")
    lines.append("")
    lines.append("Choose one winner:")
    lines.append("- deterministic")
    lines.append("- writer_option_1")
    lines.append("- writer_option_2")
    lines.append("- abstain")
    lines.append("")
    lines.append("Judging rules:")
    lines.append("1. Truthfulness beats polish.")
    lines.append("2. The winner must keep the same claim, same tone, and same lead-token style.")
    lines.append("3. Reject keyword shuffle, near-duplicates, awkward phrasing, and trivial term swaps.")
    lines.append("4. Choose deterministic unless a writer option is clearly stronger.")
    lines.append("5. Choose abstain if none are good enough to surface.")
    lines.append("6. Prefer stronger supported JD alignment over generic smoothness.")
    lines.append("7. Prefer stronger supported business/result framing over style-only improvement.")
    lines.append("8. Reject options whose best improvement is only stylistic.")
    lines.append("9. Reject long-copying of JD sentence phrasing.")
    lines.append("10. Reject options that only change connective or stylistic wording without net supported alignment gain over deterministic.")
    lines.append("")
    lines.append(f"Original lead token: {original_lead}")
    lines.append(f"Matched JD terms: {alignment.get('matched_jd_terms', [])}")
    lines.append("Matched JD snippets:")
    for snippet in alignment.get("matched_jd_snippets", []) or []:
        lines.append(f"- {snippet}")
    if not (alignment.get("matched_jd_snippets", []) or []):
        lines.append("- none")
    lines.append("")
    lines.append("Original bullet:")
    lines.append(original_text)
    lines.append("")
    lines.append(f"Resolved role family: {role_profile.get('family_name', TAILORING_ROLE_FAMILY_FALLBACK)}")
    lines.append(f"Role-family ATS priority terms: {role_profile.get('ats_priority_terms_any', [])}")
    lines.append(f"Role-family facet priority order: {role_profile.get('facet_priority_order', [])}")
    lines.append("Role-family appeal targets:")
    for item in role_profile.get("appeal_targets", []) or []:
        lines.append(f"- {item}")
    if not (role_profile.get("appeal_targets", []) or []):
        lines.append("- none")
    lines.append("")
    lines.append("Deterministic draft:")
    lines.append(deterministic_patch_text)
    lines.append("")

    for idx, option in enumerate(writer_options, start=1):
        lines.append(f"writer_option_{idx}:")
        lines.append(str(option.get("patch_text", "") or "").strip())
        lines.append(f"writer_option_{idx}_reason: {str(option.get('reason', '') or '').strip()}")
        lines.append("")

    lines.append("Output contract:")
    lines.append("Return plain text only.")
    lines.append("Do NOT use markdown.")
    lines.append("Do NOT use code fences.")
    lines.append("Use exactly these lines:")
    lines.append("WINNER: deterministic | writer_option_1 | writer_option_2 | abstain")
    lines.append("REASON: <one short sentence>")
    lines.append("REJECTED: <comma-separated option ids or none>")
    lines.append("QUALITY_FLAGS: <comma-separated tags or none>")
    return "\n".join(lines)


def _keep_deterministic_with_status(
    candidate: Dict[str, Any],
    *,
    status: str,
    note: str,
    writer_metadata: Optional[Dict[str, str]] = None,
    judge_metadata: Optional[Dict[str, str]] = None,
    rejected_text: str = "",
    writer_options: Optional[List[Dict[str, Any]]] = None,
    invalid_writer_options: Optional[List[Dict[str, Any]]] = None,
    judge_winner: str = "",
    judge_reason: str = "",
    judge_rejected_options: Optional[List[str]] = None,
    judge_quality_flags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    updated = dict(candidate)
    updated["llm_refinement_used"] = False
    updated["llm_refinement_status"] = status
    updated["llm_refinement_note"] = note
    updated["llm_refinement_rejected_text"] = str(rejected_text or "").strip()

    updated["llm_writer_options"] = list(writer_options or [])
    updated["llm_writer_invalid_options"] = list(invalid_writer_options or [])

    updated["llm_judge_winner"] = str(judge_winner or "").strip()
    updated["llm_judge_reason"] = str(judge_reason or "").strip()
    updated["llm_judge_rejected_options"] = list(judge_rejected_options or [])
    updated["llm_judge_quality_flags"] = list(judge_quality_flags or [])

    writer_metadata = writer_metadata or {}
    judge_metadata = judge_metadata or {}

    updated["llm_writer_provider"] = str(writer_metadata.get("provider", "") or "").strip()
    updated["llm_writer_model"] = str(writer_metadata.get("model", "") or "").strip()
    updated["llm_writer_requested_provider"] = str(writer_metadata.get("requested_provider", "") or "").strip()
    updated["llm_writer_requested_model"] = str(writer_metadata.get("requested_model", "") or "").strip()

    updated["llm_judge_provider"] = str(judge_metadata.get("provider", "") or "").strip()
    updated["llm_judge_model"] = str(judge_metadata.get("model", "") or "").strip()
    updated["llm_judge_requested_provider"] = str(judge_metadata.get("requested_provider", "") or "").strip()
    updated["llm_judge_requested_model"] = str(judge_metadata.get("requested_model", "") or "").strip()

    return updated

def _patch_refinement_numeric_tokens(text: str) -> List[str]:
    matches = re.findall(r"\b\d+(?:\.\d+)?(?:k|m)?\+?%?\b", str(text or ""), flags=re.IGNORECASE)
    return _unique_preserve_order([str(item).strip() for item in matches if str(item).strip()])


def _patch_refinement_contains_term(text: str, term: str) -> bool:
    text_norm = re.sub(r"\s+", " ", str(text or "").strip().lower())
    term_norm = re.sub(r"\s+", " ", str(term or "").strip().lower())
    if not text_norm or not term_norm:
        return False
    return term_norm in text_norm

def _patch_refinement_term_variants(term: str) -> List[str]:
    raw = str(term or "").strip()
    normalized = normalize_signal_text(raw)
    if not normalized:
        return []

    variants: List[str] = [raw]

    canonical_from_alias = _SKILL_ALIASES.get(normalized, "")
    if canonical_from_alias:
        variants.append(canonical_from_alias)

    variants.extend(equivalent_signal_terms(raw))

    reverse_aliases = [
        alias
        for alias, canonical in _SKILL_ALIASES.items()
        if normalize_signal_text(canonical) == normalized
    ]
    variants.extend(reverse_aliases)

    return _unique_preserve_order([str(item).strip() for item in variants if str(item).strip()])


def _patch_refinement_contains_term_or_alias(text: str, term: str) -> bool:
    variants = _patch_refinement_term_variants(term)
    if not variants:
        return _patch_refinement_contains_term(text, term)

    return any(_patch_refinement_contains_term(text, variant) for variant in variants)
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
    lines.append("15. Keep the same opening tense/style as the original bullet.")
    lines.append("16. Preserve the original lead action word unless abstaining.")
    lines.append("17. If the original bullet starts with a past-tense action word, the refined bullet must also start with that same past-tense action word.")
    lines.append("18. Do NOT switch a past-tense bullet into gerund/opening-phrase style such as Using, With, By, Through, or Via.")
    lines.append("")
    lines.append("Style target:")
    lines.append("- Sound like a strong real resume bullet, not a keyword shuffle.")
    lines.append("- Keep it concise but do not compress away important evidence.")
    lines.append("- Preserve measurable outcomes and technical nouns.")
    lines.append(f"- Protected substantive phrases: {protected_phrases}")
    lines.append("- Match the original bullet's opening verb style and tense.")
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
    lines.append("")
    lines.append("Opening-style constraints:")
    lines.append(f"- Original lead token: {original_lead or '<none>'}")
    lines.append(f"- Nearby sibling bullet openings: {sibling_openings or []}")
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
    supported_phrase_set = {
        normalize_signal_text(term)
        for term in (
            list(candidate.get("supported_jd_signals", []) or [])
            + [str(candidate.get("canonical_supported_signal", "") or "").strip()]
        )
        if str(term or "").strip()
    }

    for phrase in protected_phrases:
        phrase_clean = str(phrase or "").strip()
        if not phrase_clean:
            continue

        phrase_norm = normalize_signal_text(phrase_clean)
        if phrase_norm in supported_phrase_set:
            if not _patch_refinement_contains_term_or_alias(refined, phrase_clean):
                return False, f"missing_protected_phrase:{phrase_clean}"
            continue

        if not _patch_refinement_contains_term(refined, phrase_clean):
            return False, f"missing_protected_phrase:{phrase_clean}"

    supported_terms = _unique_preserve_order(
        list(candidate.get("supported_jd_signals", []) or [])
        + [str(candidate.get("canonical_supported_signal", "") or "").strip()]
    )
    supported_terms = [term for term in supported_terms if str(term or "").strip()]

    if supported_terms and not any(_patch_refinement_contains_term_or_alias(refined, term) for term in supported_terms):
        return False, "missing_supported_signal"

    protected_core_terms = _patch_refinement_core_terms(candidate)
    for term in protected_core_terms:
        term_clean = str(term or "").strip()
        if not term_clean:
            continue
        if not _patch_refinement_contains_term_or_alias(refined, term_clean):
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

    original_lead = _patch_refinement_lead_token(original_text)
    refined_lead = _patch_refinement_lead_token(refined)

    if original_lead and refined_lead and refined_lead != original_lead:
        return False, f"lead_token_changed:{original_lead}->{refined_lead}"
    
    return True, "ok"


def _maybe_refine_patch_ready_rewrite_candidate(
    payload: Dict[str, Any],
    candidate: Dict[str, Any],
) -> Dict[str, Any]:
    if str(candidate.get("operation_type", "") or "").strip() != "rewrite":
        return candidate

    if str(candidate.get("proposal_status", "") or "").strip() != "patch_ready":
        return candidate

    if str(candidate.get("materiality_validation_status", "") or "").strip() != "material_candidate":
        return candidate

    deterministic_patch_text = str(candidate.get("patch_text", "") or "").strip()
    if not deterministic_patch_text:
        return candidate

    candidate = _stamp_patch_refinement_baseline(candidate)
    deterministic_sufficient, deterministic_sufficient_note = _patch_refinement_deterministic_alignment_sufficient(
        payload,
        candidate,
    )
    if deterministic_sufficient:
        return _keep_deterministic_with_status(
            candidate,
            status="deterministic_alignment_sufficient_kept_deterministic",
            note=deterministic_sufficient_note,
        )

    writer_system_prompt = """
You are the writer stage for one resume bullet under strict evidence constraints.
Return plain text only.
Do not use markdown.
Do not use code fences.
Either return:
ABSTAIN: <short reason>
or up to two lines:
OPTION_1: <single rewritten bullet>
OPTION_2: <single rewritten bullet>
"""
    writer_prompt = _build_patch_refinement_writer_prompt(payload, candidate)

    writer_raw, writer_metadata, writer_error_type, writer_error_note = _run_patch_refinement_writer_plain_call(
        provider=PATCH_REFINEMENT_WRITER_PROVIDER,
        model=PATCH_REFINEMENT_WRITER_MODEL,
        temperature=PATCH_REFINEMENT_WRITER_TEMPERATURE,
        max_tokens=PATCH_REFINEMENT_WRITER_MAX_TOKENS,
        system_prompt=writer_system_prompt,
        user_prompt=writer_prompt,
    )

    if writer_error_type:
        return _keep_deterministic_with_status(
            candidate,
            status=f"{writer_error_type}_kept_deterministic",
            note=writer_error_note,
            writer_metadata=writer_metadata,
        )

    writer_parsed = _normalize_patch_refinement_writer_parsed(writer_raw or {})
    if writer_parsed.get("abstain", False):
        return _keep_deterministic_with_status(
            candidate,
            status="writer_abstained_kept_deterministic",
            note=str(writer_parsed.get("abstain_reason", "") or "").strip() or "writer_abstained",
            writer_metadata=writer_metadata,
        )

    validated_writer_options, invalid_writer_options = _partition_writer_options_by_validation(
        candidate,
        list(writer_parsed.get("options", []) or []),
    )
    filtered_writer_options: List[Dict[str, Any]] = []
    for option in validated_writer_options:
        patch_text = str(option.get("patch_text", "") or "").strip()
        if _patch_refinement_style_only_delta(deterministic_patch_text, patch_text):
            invalid_writer_options.append(
                {
                    **dict(option),
                    "validation_reason": "style_only_delta_vs_deterministic",
                }
            )
            continue
        filtered_writer_options.append(option)

    validated_writer_options = filtered_writer_options

    if not validated_writer_options:
        return _keep_deterministic_with_status(
            candidate,
            status="writer_no_valid_options_kept_deterministic",
            note="writer produced no valid rewrite options better than deterministic",
            writer_metadata=writer_metadata,
            writer_options=[],
            invalid_writer_options=invalid_writer_options,
        )

    judge_system_prompt = """
You are the judge stage for one resume bullet rewrite.
Return plain text only.
Do not use markdown.
Do not use code fences.
"""
    judge_prompt = _build_patch_refinement_judge_prompt(
        payload,
        candidate,
        validated_writer_options,
    )

    judge_raw, judge_metadata, judge_error_type, judge_error_note = _run_patch_refinement_judge_plain_call(
        provider=PATCH_REFINEMENT_JUDGE_PROVIDER,
        model=PATCH_REFINEMENT_JUDGE_MODEL,
        temperature=PATCH_REFINEMENT_JUDGE_TEMPERATURE,
        max_tokens=PATCH_REFINEMENT_JUDGE_MAX_TOKENS,
        system_prompt=judge_system_prompt,
        user_prompt=judge_prompt,
    )

    if judge_error_type:
        return _keep_deterministic_with_status(
            candidate,
            status=f"judge_{judge_error_type}_kept_deterministic",
            note=judge_error_note,
            writer_metadata=writer_metadata,
            judge_metadata=judge_metadata,
            writer_options=validated_writer_options,
            invalid_writer_options=invalid_writer_options,
        )

    judge_parsed = _normalize_patch_refinement_judge_parsed(judge_raw or {})
    winner = str(judge_parsed.get("winner", "") or "").strip()

    if winner in {"deterministic", "abstain"}:
        return _keep_deterministic_with_status(
            candidate,
            status="judge_kept_deterministic",
            note=str(judge_parsed.get("reason", "") or "").strip() or "judge_kept_deterministic",
            writer_metadata=writer_metadata,
            judge_metadata=judge_metadata,
            writer_options=validated_writer_options,
            invalid_writer_options=invalid_writer_options,
            judge_winner=winner,
            judge_reason=str(judge_parsed.get("reason", "") or "").strip(),
            judge_rejected_options=list(judge_parsed.get("rejected_options", []) or []),
            judge_quality_flags=list(judge_parsed.get("quality_flags", []) or []),
        )

    selected_option = next(
        (item for item in validated_writer_options if str(item.get("option_id", "") or "").strip() == winner),
        None,
    )

    if selected_option is None:
        return _keep_deterministic_with_status(
            candidate,
            status="judge_invalid_winner_kept_deterministic",
            note="judge selected an unavailable option",
            writer_metadata=writer_metadata,
            judge_metadata=judge_metadata,
            writer_options=validated_writer_options,
            invalid_writer_options=invalid_writer_options,
            judge_winner=winner,
            judge_reason="judge selected an unavailable option",
            judge_rejected_options=list(judge_parsed.get("rejected_options", []) or []),
            judge_quality_flags=list(judge_parsed.get("quality_flags", []) or []),
        )

    updated = dict(candidate)
    updated["patch_text"] = str(selected_option.get("patch_text", "") or "").strip()
    updated["proposed_text"] = updated["patch_text"]
    updated["llm_refinement_used"] = True
    updated["llm_refinement_status"] = "judge_selected_writer_option"
    updated["llm_refinement_note"] = str(judge_parsed.get("reason", "") or "").strip()
    updated["llm_refinement_reason"] = str(selected_option.get("reason", "") or "").strip()
    updated["llm_refinement_preserved_terms"] = list(selected_option.get("preserved_terms", []) or [])
    updated["llm_refinement_risk_flags"] = list(selected_option.get("risk_flags", []) or [])
    updated["llm_refinement_selected_option_id"] = str(selected_option.get("option_id", "") or "").strip()
    updated["llm_writer_options"] = validated_writer_options
    updated["llm_judge_winner"] = winner
    updated["llm_writer_invalid_options"] = invalid_writer_options
    updated["llm_judge_reason"] = str(judge_parsed.get("reason", "") or "").strip()
    updated["llm_judge_rejected_options"] = list(judge_parsed.get("rejected_options", []) or [])
    updated["llm_judge_quality_flags"] = list(judge_parsed.get("quality_flags", []) or [])

    updated["llm_refinement_provider"] = str(writer_metadata.get("provider", "") or "").strip()
    updated["llm_refinement_model"] = str(writer_metadata.get("model", "") or "").strip()
    updated["llm_refinement_requested_provider"] = str(writer_metadata.get("requested_provider", "") or "").strip()
    updated["llm_refinement_requested_model"] = str(writer_metadata.get("requested_model", "") or "").strip()

    updated["llm_writer_provider"] = str(writer_metadata.get("provider", "") or "").strip()
    updated["llm_writer_model"] = str(writer_metadata.get("model", "") or "").strip()
    updated["llm_writer_requested_provider"] = str(writer_metadata.get("requested_provider", "") or "").strip()
    updated["llm_writer_requested_model"] = str(writer_metadata.get("requested_model", "") or "").strip()

    updated["llm_judge_provider"] = str(judge_metadata.get("provider", "") or "").strip()
    updated["llm_judge_model"] = str(judge_metadata.get("model", "") or "").strip()
    updated["llm_judge_requested_provider"] = str(judge_metadata.get("requested_provider", "") or "").strip()
    updated["llm_judge_requested_model"] = str(judge_metadata.get("requested_model", "") or "").strip()

    updated["llm_selected_patch_text"] = str(selected_option.get("patch_text", "") or "").strip()
    updated["llm_selected_patch_reason"] = str(judge_parsed.get("reason", "") or "").strip()
    updated["llm_export_decision"] = "pending_post_validation"

    updated["patch_generation_method"] = (
        str(updated.get("patch_generation_method", "") or "").strip() + "+llm_writer_judge"
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
            parsed = _validate_live_llm_parsed_contract(value, payload)
            parsed["rewrite_directions"] = _canonicalize_live_direction_objects(
                parsed.get("rewrite_directions", []),
                payload,
            )
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

        raw = _raw_text(value)
        parsed = _extract_json_from_llm_response(raw)
        parsed = _validate_live_llm_parsed_contract(parsed, payload)
        parsed["rewrite_directions"] = _canonicalize_live_direction_objects(
            parsed.get("rewrite_directions", []),
            payload,
        )
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

