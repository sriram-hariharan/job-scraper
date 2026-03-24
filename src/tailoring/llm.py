
from typing import Dict, Any, Optional, List
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

