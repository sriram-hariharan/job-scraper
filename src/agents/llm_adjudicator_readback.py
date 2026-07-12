"""Readback-only LLM adjudicator summary for deterministic resume selection."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from typing import Any, Callable, Mapping

from src.ai.llm_client import run_chat_completion


GATE_ENV = "APPLYLENS_LLM_ADJUDICATOR_READBACK_ENABLED"
MODE_ENV = "APPLYLENS_LLM_ADJUDICATOR_READBACK_MODE"
TRUE_VALUES = {"1", "true", "yes", "on"}
VALID_MODES = {"off", "auto", "always"}
MAX_PREVIEW_CHARS = 600


def llm_adjudicator_readback_enabled(value: Any | None = None) -> bool:
    raw = os.getenv(GATE_ENV, "") if value is None else value
    return str(raw or "").strip().lower() in TRUE_VALUES


def resolve_llm_adjudicator_readback_mode(
    environ: Mapping[str, Any] | None = None,
) -> str:
    """Resolve the policy mode while preserving the legacy boolean override."""
    source = os.environ if environ is None else environ
    if MODE_ENV in source:
        mode = str(source.get(MODE_ENV, "") or "").strip().lower()
        return mode if mode in VALID_MODES else "invalid"
    if GATE_ENV in source:
        return (
            "always"
            if llm_adjudicator_readback_enabled(source.get(GATE_ENV))
            else "off"
        )
    return "auto"


def llm_adjudicator_provider_configured(
    *,
    provider: str | None,
    model: str | None,
    provider_callable: Callable[[dict[str, Any]], Any] | None = None,
    environ: Mapping[str, Any] | None = None,
) -> bool:
    """Return whether an eligible readback can safely reach its provider."""
    if callable(provider_callable):
        return True
    safe_provider = str(provider or "").strip().lower()
    safe_model = str(model or "").strip()
    credential_env = {
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(safe_provider)
    if not credential_env or not safe_model:
        return False
    source = os.environ if environ is None else environ
    return bool(str(source.get(credential_env, "") or "").strip())


def _candidate_is_viable(candidate: Mapping[str, Any]) -> bool:
    value = candidate.get("prefilter_passed")
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in TRUE_VALUES


def _candidate_semantic_score(candidate: Mapping[str, Any]) -> float | None:
    semantic = candidate.get("semantic_alignment")
    if not isinstance(semantic, Mapping) or semantic.get("score") in {None, ""}:
        return None
    try:
        return float(semantic.get("score"))
    except (TypeError, ValueError):
        return None


def should_run_llm_adjudicator_readback(
    *,
    ranked_candidates: list[dict[str, Any]],
    mode: str,
    provider_configured: bool,
    close_gap_threshold: float = 0.05,
    borderline_score_threshold: float = 0.60,
    borderline_gap_threshold: float = 0.10,
) -> tuple[bool, str]:
    """Return a deterministic provider eligibility decision and reason."""
    safe_mode = str(mode or "").strip().lower()
    if safe_mode == "off":
        return False, "explicit_off"
    if safe_mode not in VALID_MODES:
        return False, "invalid_mode"
    if not provider_configured:
        return False, "provider_not_configured"

    viable = [candidate for candidate in ranked_candidates if _candidate_is_viable(candidate)]
    if len(viable) < 2:
        return False, "insufficient_candidates"
    if safe_mode == "always":
        return True, "forced_always"

    winner, runner_up = viable[:2]
    winner_score = _safe_float(winner.get("final_score"))
    runner_up_score = _safe_float(runner_up.get("final_score"))
    score_gap = round(abs(winner_score - runner_up_score), 6)
    if score_gap <= close_gap_threshold:
        return True, "close_score_gap"
    if (
        winner_score < borderline_score_threshold
        and score_gap <= borderline_gap_threshold
    ):
        return True, "borderline_close_candidates"

    semantic_scores = [
        (candidate, _candidate_semantic_score(candidate))
        for candidate in viable
    ]
    semantic_scores = [item for item in semantic_scores if item[1] is not None]
    if len(semantic_scores) >= 2:
        semantic_ranked = sorted(
            semantic_scores,
            key=lambda item: (-float(item[1]), str(item[0].get("resume_name", ""))),
        )
        semantic_winner, semantic_top_score = semantic_ranked[0]
        deterministic_semantic_score = _candidate_semantic_score(winner)
        if (
            semantic_winner is not winner
            and deterministic_semantic_score is not None
            and round(float(semantic_top_score) - deterministic_semantic_score, 6)
            >= 0.05
        ):
            return True, "semantic_deterministic_disagreement"

    if any(
        isinstance(candidate.get("hard_requirement_diagnostics"), list)
        and bool(candidate.get("hard_requirement_diagnostics"))
        for candidate in viable
    ):
        return True, "hard_requirement_diagnostic"
    return False, "clear_deterministic_winner"


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
        "policy_mode": "off" if not enabled else "always",
        "policy_eligible": bool(enabled),
        "policy_reason": "legacy_enabled" if enabled else "explicit_off",
        "provider_configured": False,
        "provider_call_attempted": False,
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
    policy_mode: str | None = None,
    policy_reason: str | None = None,
    provider_configured: bool | None = None,
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
    if policy_mode is not None:
        readback["policy_mode"] = _clean_text(policy_mode)
    if policy_reason is not None:
        readback["policy_reason"] = _clean_text(policy_reason)
    readback["policy_eligible"] = bool(enabled)
    if provider_configured is not None:
        readback["provider_configured"] = bool(provider_configured)
    if not enabled:
        return readback
    if not candidate_payload:
        readback["status"] = "skipped"
        readback["error"] = "No candidates supplied."
        return readback

    readback["provider_call_attempted"] = True
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


def _policy_skip_status(reason: str) -> str:
    return {
        "explicit_off": "disabled",
        "invalid_mode": "skipped_invalid_mode",
        "provider_not_configured": "skipped_provider_not_configured",
        "insufficient_candidates": "skipped_insufficient_candidates",
        "clear_deterministic_winner": "skipped_clear_winner",
    }.get(reason, "skipped_policy_not_needed")


def build_policy_driven_llm_adjudicator_readback(
    *,
    candidates: list[dict[str, Any]],
    provider: str | None,
    model: str | None,
    mode: str | None = None,
    provider_callable: Callable[[dict[str, Any]], Any] | None = None,
    environ: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply auto policy and optionally build advisory provider readback."""
    candidate_payload = deepcopy(candidates)
    resolved_mode = (
        resolve_llm_adjudicator_readback_mode(environ)
        if mode is None
        else str(mode or "").strip().lower()
    )
    configured = llm_adjudicator_provider_configured(
        provider=provider,
        model=model,
        provider_callable=provider_callable,
        environ=environ,
    )
    should_run, reason = should_run_llm_adjudicator_readback(
        ranked_candidates=candidate_payload,
        mode=resolved_mode,
        provider_configured=configured,
    )
    if should_run:
        return build_llm_adjudicator_readback(
            candidates=candidate_payload,
            provider=provider,
            model=model,
            enabled=True,
            provider_callable=provider_callable,
            policy_mode=resolved_mode,
            policy_reason=reason,
            provider_configured=configured,
        )

    readback = build_llm_adjudicator_readback(
        candidates=candidate_payload,
        provider=provider,
        model=model,
        enabled=False,
        policy_mode=resolved_mode,
        policy_reason=reason,
        provider_configured=configured,
    )
    readback["status"] = _policy_skip_status(reason)
    return readback
