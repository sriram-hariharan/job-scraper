"""Readback-only LLM adjudicator summary for deterministic resume selection."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from typing import Any, Callable

from src.ai.llm_client import run_chat_completion


GATE_ENV = "APPLYLENS_LLM_ADJUDICATOR_READBACK_ENABLED"
TRUE_VALUES = {"1", "true", "yes", "on"}
MAX_PREVIEW_CHARS = 600


def llm_adjudicator_readback_enabled(value: Any | None = None) -> bool:
    raw = os.getenv(GATE_ENV, "") if value is None else value
    return str(raw or "").strip().lower() in TRUE_VALUES


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _truncate(value: Any, limit: int = MAX_PREVIEW_CHARS) -> str:
    text = _clean_text(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _candidate_names(candidates: list[dict[str, Any]]) -> list[str]:
    return [
        name
        for name in (_clean_text(candidate.get("resume_name")) for candidate in candidates)
        if name
    ]


def _candidate_scores(candidates: list[dict[str, Any]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for candidate in candidates:
        name = _clean_text(candidate.get("resume_name"))
        if not name:
            continue
        scores[name] = round(_safe_float(candidate.get("final_score")), 6)
    return scores


def _semantic_alignment_by_candidate(
    candidates: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    semantic: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        name = _clean_text(candidate.get("resume_name"))
        value = candidate.get("semantic_alignment")
        if name and isinstance(value, dict) and value:
            semantic[name] = deepcopy(value)
    return semantic


def _hard_requirement_diagnostics_by_candidate(
    candidates: list[dict[str, Any]],
) -> dict[str, list[Any]]:
    diagnostics: dict[str, list[Any]] = {}
    for candidate in candidates:
        name = _clean_text(candidate.get("resume_name"))
        value = candidate.get("hard_requirement_diagnostics")
        if name and isinstance(value, list) and value:
            diagnostics[name] = deepcopy(value)
    return diagnostics


def _base_readback(
    *,
    enabled: bool,
    candidates: list[dict[str, Any]],
    provider: str | None,
    model: str | None,
) -> dict[str, Any]:
    copied_candidates = deepcopy(candidates)
    return {
        "enabled": bool(enabled),
        "status": "disabled" if not enabled else "skipped",
        "readback_only": True,
        "no_winner_override": True,
        "no_score_override": True,
        "no_queue_mutation": True,
        "provider_requested": _clean_text(provider),
        "model_requested": _clean_text(model),
        "provider_used": "",
        "model_used": "",
        "candidate_resume_names": _candidate_names(copied_candidates),
        "candidate_scores": _candidate_scores(copied_candidates),
        "semantic_alignment": _semantic_alignment_by_candidate(copied_candidates),
        "hard_requirement_diagnostics": _hard_requirement_diagnostics_by_candidate(
            copied_candidates
        ),
        "candidates": copied_candidates,
        "adjudicator_summary": "",
        "adjudicator_recommendation_label": "",
        "raw_response_preview": "",
        "error": "",
    }


def _parse_provider_response(raw_response: Any) -> dict[str, Any]:
    value = raw_response
    if isinstance(value, dict):
        output = value.get("output")
        if isinstance(output, dict):
            value = output
        elif "content" in value:
            value = value.get("content")
        elif "raw_response" in value:
            value = value.get("raw_response")
        else:
            return value

    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("empty provider response")
        return json.loads(text)

    raise ValueError("provider response must be JSON object or JSON string")


def _normalize_provider_response(parsed: dict[str, Any]) -> tuple[str, str]:
    summary = _clean_text(
        parsed.get("adjudicator_summary")
        or parsed.get("summary")
        or parsed.get("reason")
    )
    label = _clean_text(
        parsed.get("adjudicator_recommendation_label")
        or parsed.get("recommendation_label")
        or parsed.get("recommendation")
    )
    if not summary and not label:
        raise ValueError("missing summary or recommendation label")
    return _truncate(summary), _truncate(label, 160)


def _provider_prompt(candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a read-only resume selector reviewer. Summarize the "
                "deterministic top candidates. Do not override winners or scores. "
                "Return JSON with adjudicator_summary and "
                "adjudicator_recommendation_label."
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"candidates": candidates}, ensure_ascii=False),
        },
    ]


def _call_provider(
    *,
    candidates: list[dict[str, Any]],
    provider: str | None,
    model: str | None,
    provider_callable: Callable[[dict[str, Any]], Any] | None,
) -> Any:
    request_payload = {
        "readback_only": True,
        "no_winner_override": True,
        "no_score_override": True,
        "no_queue_mutation": True,
        "candidates": deepcopy(candidates),
    }
    if callable(provider_callable):
        return provider_callable(deepcopy(request_payload))

    return run_chat_completion(
        messages=_provider_prompt(candidates),
        provider=_clean_text(provider) or None,
        model=_clean_text(model) or None,
        temperature=0,
        max_tokens=int(os.getenv("LLM_ADJUDICATOR_READBACK_MAX_TOKENS", "500")),
        response_mime_type="application/json",
        fallback_enabled=False,
    )


def build_llm_adjudicator_readback(
    *,
    candidates: list[dict[str, Any]],
    provider: str | None,
    model: str | None,
    enabled: bool = False,
    provider_callable: Callable[[dict[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    """Build a readback-only LLM adjudicator summary.

    The return value is advisory metadata only. It intentionally contains no
    selected resume field and cannot be used as a winner or score override.
    """

    candidate_payload = deepcopy(candidates)
    readback = _base_readback(
        enabled=enabled,
        candidates=candidate_payload,
        provider=provider,
        model=model,
    )
    if not enabled:
        return readback
    if not candidate_payload:
        readback["status"] = "skipped"
        readback["error"] = "No candidates supplied."
        return readback

    try:
        raw_response = _call_provider(
            candidates=candidate_payload,
            provider=provider,
            model=model,
            provider_callable=provider_callable,
        )
    except Exception as exc:
        readback["status"] = "provider_error"
        readback["error"] = _truncate(f"{exc.__class__.__name__}: {exc}")
        return readback

    readback["raw_response_preview"] = _truncate(raw_response)
    try:
        parsed = _parse_provider_response(raw_response)
        summary, label = _normalize_provider_response(parsed)
    except Exception as exc:
        readback["status"] = "malformed_response"
        readback["error"] = _truncate(f"{exc.__class__.__name__}: {exc}")
        return readback

    readback.update(
        {
            "status": "ok",
            "provider_used": _clean_text(provider),
            "model_used": _clean_text(model),
            "adjudicator_summary": summary,
            "adjudicator_recommendation_label": label,
        }
    )
    return readback
