import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib
from datetime import datetime, timezone

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
LLM_TAILOR_PROMPT_VERSION = "v1"

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


def _build_recruiter_summary(packet: Dict[str, Any]) -> str:
    job = packet.get("job", {})
    selection = packet.get("selection", {})
    summary = packet.get("summary", {})

    resume_name = selection.get("selected_resume", "selected resume")
    score = selection.get("selected_score", 0.0)
    company = job.get("company", "")
    title = job.get("title", "")
    matched_required = summary.get("matched_required", [])
    missing_required = summary.get("missing_required", [])

    matched_text = ", ".join(_truncate_list(matched_required, 6)) if matched_required else "core requirements"
    missing_text = ", ".join(_truncate_list(missing_required, 4)) if missing_required else "no major explicit gaps"

    return (
        f"{resume_name} is the selected variant for {company} | {title} with a deterministic score of {score:.3f}. "
        f"It already aligns on {matched_text}. "
        f"The main explicit gaps still showing are {missing_text}."
    )


def _build_keep_emphasize(packet: Dict[str, Any]) -> List[str]:
    summary = packet.get("summary", {})
    matched_required = summary.get("matched_required", [])
    matched_preferred = summary.get("matched_preferred", [])
    matched_terms = summary.get("matched_terms", [])

    items = []
    if matched_required:
        items.append(
            f"Keep explicit required-skill evidence visible: {', '.join(_truncate_list(matched_required, 8))}."
        )
    if matched_preferred:
        items.append(
            f"Keep preferred-skill evidence visible: {', '.join(_truncate_list(matched_preferred, 6))}."
        )
    if matched_terms:
        items.append(
            f"Preserve the strongest JD-aligned language already present: {', '.join(_truncate_list(matched_terms, 8))}."
        )

    return _unique_preserve_order(items)


def _build_do_not_claim(packet: Dict[str, Any]) -> List[str]:
    summary = packet.get("summary", {})
    missing_required = summary.get("missing_required", [])
    missing_preferred = summary.get("missing_preferred", [])
    guardrail = packet.get(
        "guardrail",
        "Only add or strengthen resume language when it is already truthful and supported by your actual work.",
    )

    items = []
    if missing_required:
        items.append(
            f"Do not claim missing required skills unless you can support them truthfully: {', '.join(_truncate_list(missing_required, 8))}."
        )
    if missing_preferred:
        items.append(
            f"Do not add unsupported preferred-skill claims: {', '.join(_truncate_list(missing_preferred, 8))}."
        )
    items.append(guardrail)

    return _unique_preserve_order(items)


def _build_bullet_reuse(packet: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    rows = packet.get("top_relevant_bullets", []) or []
    selected = rows[:limit]

    reuse_rows = []
    for row in selected:
        source_title = row.get("source_title", "")
        source_company = row.get("source_company", "")
        source = source_title if not source_company else f"{source_title} @ {source_company}"
        reuse_rows.append(
            {
                "section": row.get("section", ""),
                "source": source,
                "overlaps": row.get("overlaps", []),
                "bullet": row.get("text", ""),
                "reuse_note": (
                    f"Reuse/review this bullet because it already supports: "
                    f"{', '.join(row.get('overlaps', [])[:6])}"
                ),
            }
        )

    return reuse_rows


def _build_tailoring_actions(packet: Dict[str, Any]) -> List[str]:
    summary = packet.get("summary", {})
    missing_required = summary.get("missing_required", [])
    matched_required = summary.get("matched_required", [])
    bullets = packet.get("top_relevant_bullets", []) or []

    actions: List[str] = []

    if matched_required:
        actions.append(
            f"Move the strongest already-supported required skills higher in the resume or summary: "
            f"{', '.join(_truncate_list(matched_required, 6))}."
        )

    if bullets:
        top_overlap_terms = _unique_preserve_order(
            [term for row in bullets[:5] for term in row.get("overlaps", [])]
        )
        if top_overlap_terms:
            actions.append(
                f"Reuse or strengthen bullets that already prove these JD-aligned terms: "
                f"{', '.join(_truncate_list(top_overlap_terms, 8))}."
            )

    if missing_required:
        actions.append(
            f"Review whether you have truthful evidence for the missing required skills before editing anything: "
            f"{', '.join(_truncate_list(missing_required, 6))}."
        )
        actions.append(
            "If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; "
            "otherwise leave the gap visible instead of inventing coverage."
        )

    return _unique_preserve_order(actions)


def _build_llm_prompt(packet: Dict[str, Any], bullet_limit: int = 6) -> str:
    job = packet.get("job", {})
    selection = packet.get("selection", {})
    summary = packet.get("summary", {})
    bullets = packet.get("top_relevant_bullets", [])[:bullet_limit]
    guardrail = packet.get(
        "guardrail",
        "Only add or strengthen resume language when it is already truthful and supported by your actual work.",
    )

    lines = []
    lines.append("You are helping tailor a resume for one job.")
    lines.append("You must stay grounded only in the provided evidence.")
    lines.append("Do not invent skills, tools, projects, outcomes, or responsibilities.")
    lines.append("")
    lines.append(f"Job company: {job.get('company', '')}")
    lines.append(f"Job title: {job.get('title', '')}")
    lines.append(f"Selected resume: {selection.get('selected_resume', '')}")
    lines.append(f"Selected score: {selection.get('selected_score', 0.0):.3f}")
    lines.append("")
    lines.append(f"Matched required skills: {summary.get('matched_required', [])}")
    lines.append(f"Missing required skills: {summary.get('missing_required', [])}")
    lines.append(f"Matched preferred skills: {summary.get('matched_preferred', [])}")
    lines.append(f"Missing preferred skills: {summary.get('missing_preferred', [])}")
    lines.append(f"Matched terms: {summary.get('matched_terms', [])}")
    lines.append(f"Top dimensions: {summary.get('top_dimensions', '')}")
    lines.append("")
    lines.append("Best existing bullets to reuse/review:")
    for idx, row in enumerate(bullets, start=1):
        lines.append(
            f"{idx}. [{row.get('section', '')}] "
            f"{row.get('source_title', '')} @ {row.get('source_company', '')} | "
            f"overlaps={row.get('overlaps', [])} | bullet={row.get('text', '')}"
        )
    lines.append("")
    lines.append(f"Guardrail: {guardrail}")
    lines.append("")
    lines.append("Return compact JSON only with:")
    lines.append("1. recruiter_summary: max 2 sentences")
    lines.append("2. keep_emphasize: max 4 items")
    lines.append("3. tailoring_actions: max 4 items")
    lines.append("4. do_not_claim: max 4 items")
    lines.append("5. rewrite_directions: max 3 items")
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
            "fallback_enabled": LLM_FALLBACK_ENABLED,
            "fallback_provider": LLM_FALLBACK_PROVIDER if LLM_FALLBACK_ENABLED else "",
            "fallback_model": LLM_FALLBACK_MODEL if LLM_FALLBACK_ENABLED else "",
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
        "fallback_enabled": LLM_FALLBACK_ENABLED,
        "fallback_provider": LLM_FALLBACK_PROVIDER if LLM_FALLBACK_ENABLED else "",
        "fallback_model": LLM_FALLBACK_MODEL if LLM_FALLBACK_ENABLED else "",
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

    prompt = payload["llm_prompt"]

    primary_system_prompt = """
You generate grounded resume tailoring suggestions.

You MUST obey these rules:
1. Use ONLY the evidence provided by the user.
2. Do NOT invent tools, methods, skills, outcomes, metrics, domains, or responsibilities.
3. If the evidence is weak for a missing skill, say it is unsupported.
4. Keep outputs concise, practical, and recruiter-usable.
5. Keep list items short and concrete.
"""

    retry_system_prompt = """
You are returning JSON for a strict Python parser.

You MUST obey these rules:
1. Return ONLY valid JSON.
2. Do NOT return markdown, code fences, commentary, or explanatory text.
3. Keep the entire JSON on a single line.
4. Do NOT include literal newlines, carriage returns, or tabs inside any string value.
5. Use empty arrays instead of null.
6. Keep recruiter_summary to 1 sentence.
7. Keep each list short and concrete.
8. Use ONLY the evidence provided. Do NOT invent anything.
"""

    fallback_attempted = bool(
        LLM_FALLBACK_ENABLED
        and LLM_TAILOR_PROVIDER != LLM_FALLBACK_PROVIDER
    )
    attempted_providers = [LLM_TAILOR_PROVIDER]
    if fallback_attempted:
        attempted_providers.append(LLM_FALLBACK_PROVIDER)

    def _call_llm(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return run_chat_completion_with_metadata(
            provider=LLM_TAILOR_PROVIDER,
            model=LLM_TAILOR_MODEL,
            temperature=LLM_TAILOR_TEMPERATURE,
            max_tokens=LLM_TAILOR_MAX_TOKENS,
            response_mime_type="application/json",
            response_schema=TAILORING_RESPONSE_SCHEMA,
            return_parsed=True,
            thinking_budget=0,
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
            "fallback_provider": LLM_FALLBACK_PROVIDER if LLM_FALLBACK_ENABLED else "",
            "fallback_model": LLM_FALLBACK_MODEL if LLM_FALLBACK_ENABLED else "",
            "attempted_providers": _unique_preserve_order(
                [LLM_TAILOR_PROVIDER, LLM_FALLBACK_PROVIDER if fallback_used else ""]
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
    tailoring_actions = _build_tailoring_actions(packet)
    llm_prompt = _build_llm_prompt(packet)

    return {
        "job": packet.get("job", {}),
        "selection": packet.get("selection", {}),
        "summary": packet.get("summary", {}),
        "recruiter_summary": recruiter_summary,
        "keep_emphasize": keep_emphasize,
        "tailoring_actions": tailoring_actions,
        "do_not_claim": do_not_claim,
        "bullet_reuse_candidates": bullet_reuse,
        "llm_prompt": llm_prompt,
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

    lines.append("## Do Not Claim")
    for item in payload.get("do_not_claim", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Bullet Reuse Candidates")
    for row in payload.get("bullet_reuse_candidates", []):
        lines.append(
            f"- **[{row.get('section', '')}] {row.get('source', '')}** | "
            f"overlaps={row.get('overlaps', [])}"
        )
        lines.append(f"  - {row.get('bullet', '')}")
        lines.append(f"  - {row.get('reuse_note', '')}")
    lines.append("")

    lines.append("## LLM Prompt")
    lines.append("```text")
    lines.append(payload.get("llm_prompt", ""))
    lines.append("```")
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
    markdown = _markdown_from_payload(payload)

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
    print("DO NOT CLAIM")
    print("-" * 100)
    for item in payload["do_not_claim"]:
        print(f"- {item}")
    print()

    if args.output_json.strip():
        output_json_path = Path(args.output_json)
        output_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"JSON written: {output_json_path}")

    if args.output_md.strip():
        output_md_path = Path(args.output_md)
        output_md_path.write_text(markdown, encoding="utf-8")
        print(f"Markdown written: {output_md_path}")
    
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
            for item in parsed.get("rewrite_directions", []):
                print(f"- {item}")
            print()
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


if __name__ == "__main__":
    main()