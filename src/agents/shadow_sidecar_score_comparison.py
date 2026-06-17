from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents import shadow_sidecar


SCORE_COMPARISON_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SCORE_COMPARISON_ENABLED"
GLOBAL_SIDECAR_FLAG = shadow_sidecar.GLOBAL_SIDECAR_FLAG
KILL_SWITCH_FLAG = shadow_sidecar.KILL_SWITCH_FLAG

STATUS_NOT_ENABLED = "comparison_not_enabled"
STATUS_BLOCKED_BY_KILL_SWITCH = "comparison_blocked_by_kill_switch"
STATUS_BLOCKED_MISSING_DETERMINISTIC_CONTEXT = (
    "comparison_blocked_missing_deterministic_context"
)
STATUS_BLOCKED_MISSING_SHADOW_SNAPSHOT = "comparison_blocked_missing_shadow_snapshot"
STATUS_READY = "comparison_ready"
STATUS_READY_WITH_FALLBACK = "comparison_ready_with_fallback"
STATUS_FAILED_NON_BLOCKING = "comparison_failed_non_blocking"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _plain_dict(value: Any) -> dict[str, Any]:
    return _snapshot(value) if isinstance(value, dict) else {}


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = _clean_text(value).lower()
    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _config_bool(config: dict[str, Any], *keys: str, default: bool = False) -> bool:
    for key in keys:
        if key in config:
            return _bool_value(config.get(key), default=default)
    return default


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return [_clean_text(item) for item in value if _clean_text(item)]


def evaluate_shadow_sidecar_score_comparison_safety() -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "score_comparison_only": True,
        "operator_review_only": True,
        "provider_calls_disabled_in_tests": True,
        "did_read_database": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "pipeline_wiring_added": False,
        "api_route_added": False,
        "ui_action_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }


def _deterministic_context(source: dict[str, Any]) -> dict[str, Any]:
    output = _plain_dict(source.get("output_json"))
    nested = _plain_dict(source.get("source_deterministic_context"))
    score_summary = _plain_dict(source.get("score_summary") or output.get("score_summary"))
    score = _first_float(
        source.get("deterministic_score"),
        source.get("final_score"),
        source.get("score"),
        source.get("top_score"),
        output.get("top_score"),
        score_summary.get("max_score"),
        score_summary.get("average_score"),
        source.get("average_score"),
        output.get("average_score"),
        nested.get("source_deterministic_score"),
    )
    decision = _first_text(
        source.get("deterministic_decision"),
        source.get("decision"),
        source.get("status"),
        output.get("status"),
        nested.get("source_deterministic_decision"),
    )
    return {
        "deterministic_score": score,
        "deterministic_decision": decision,
        "score_source": _score_source(source, output, score_summary, nested),
        "decision_counts": _plain_dict(source.get("decision_counts") or output.get("decision_counts")),
        "validation_status": _clean_text(
            _plain_dict(source.get("validation_json") or output.get("validation_json")).get(
                "is_valid"
            )
        ),
        "raw_context": _snapshot(source),
    }


def _first_float(*values: Any) -> float | None:
    for value in values:
        parsed = _safe_float(value)
        if parsed is not None:
            return parsed
    return None


def _first_text(*values: Any) -> str:
    for value in values:
        cleaned = _clean_text(value)
        if cleaned:
            return cleaned
    return ""


def _score_source(
    source: dict[str, Any],
    output: dict[str, Any],
    score_summary: dict[str, Any],
    nested: dict[str, Any],
) -> str:
    for label, value in (
        ("deterministic_score", source.get("deterministic_score")),
        ("final_score", source.get("final_score")),
        ("score", source.get("score")),
        ("top_score", source.get("top_score")),
        ("output_json.top_score", output.get("top_score")),
        ("score_summary.max_score", score_summary.get("max_score")),
        ("score_summary.average_score", score_summary.get("average_score")),
        ("average_score", source.get("average_score")),
        ("output_json.average_score", output.get("average_score")),
        (
            "source_deterministic_context.source_deterministic_score",
            nested.get("source_deterministic_score"),
        ),
    ):
        if _safe_float(value) is not None:
            return label
    return ""


def _shadow_context(snapshot_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "shadow_snapshot_status": _clean_text(snapshot_payload.get("snapshot_status")),
        "shadow_agent_names": _text_list(snapshot_payload.get("agent_names")),
        "shadow_risk_flag_count": int(snapshot_payload.get("risk_flag_count") or 0),
        "shadow_blocking_finding_count": int(
            snapshot_payload.get("blocking_finding_count") or 0
        ),
        "fallback_count": int(snapshot_payload.get("fallback_count") or 0),
        "source_hook_status": _clean_text(snapshot_payload.get("source_hook_status")),
        "source_chain_status": _clean_text(snapshot_payload.get("source_chain_status")),
        "operator_review_summary": _plain_dict(
            snapshot_payload.get("operator_review_summary")
        ),
        "raw_context": _snapshot(snapshot_payload),
    }


def _status_from_config(
    *,
    sidecar_config: dict[str, Any],
    deterministic_context: dict[str, Any],
    shadow_snapshot_payload: dict[str, Any],
) -> str:
    config = _snapshot(sidecar_config or {})
    if _config_bool(config, KILL_SWITCH_FLAG, "kill_switch_enabled", default=False):
        return STATUS_BLOCKED_BY_KILL_SWITCH
    if not _config_bool(config, GLOBAL_SIDECAR_FLAG, "sidecar_enabled", default=False):
        return STATUS_NOT_ENABLED
    if not _config_bool(
        config,
        SCORE_COMPARISON_FLAG,
        "score_comparison_enabled",
        default=False,
    ):
        return STATUS_NOT_ENABLED
    if deterministic_context.get("deterministic_score") is None and not _clean_text(
        deterministic_context.get("deterministic_decision")
    ):
        return STATUS_BLOCKED_MISSING_DETERMINISTIC_CONTEXT
    if not shadow_snapshot_payload or not _clean_text(
        shadow_snapshot_payload.get("snapshot_status")
    ):
        return STATUS_BLOCKED_MISSING_SHADOW_SNAPSHOT
    return STATUS_READY


def _agreement_level(
    *,
    deterministic_score: float | None,
    deterministic_decision: str,
    shadow_risk_flag_count: int,
    shadow_blocking_finding_count: int,
    fallback_count: int,
) -> str:
    decision = deterministic_decision.lower()
    high_score = deterministic_score is not None and deterministic_score >= 0.75
    low_score = deterministic_score is not None and deterministic_score < 0.5
    positive_decision = any(
        marker in decision
        for marker in ("qualified", "approve", "ready", "recommended", "priority")
    )
    negative_decision = any(
        marker in decision
        for marker in ("disqualified", "reject", "skip", "blocked")
    )
    has_blockers = shadow_blocking_finding_count > 0
    has_risks = shadow_risk_flag_count > 0
    if has_blockers and (high_score or positive_decision):
        return "blocked_by_shadow_findings"
    if has_risks and (high_score or positive_decision):
        return "needs_operator_review"
    if fallback_count and not has_blockers:
        return "aligned_with_shadow_fallback"
    if (low_score or negative_decision) and (has_risks or has_blockers):
        return "aligned_on_caution"
    if high_score or positive_decision:
        return "aligned"
    return "insufficient_information"


def _comparison_findings(
    *,
    deterministic: dict[str, Any],
    shadow: dict[str, Any],
    agreement_level: str,
) -> list[dict[str, Any]]:
    findings = [
        {
            "finding_code": "deterministic_score_preserved",
            "severity": "info",
            "message": "Deterministic score is copied for review only.",
            "read_only": True,
        },
        {
            "finding_code": f"agreement_{agreement_level}",
            "severity": "warning"
            if agreement_level
            in {"needs_operator_review", "blocked_by_shadow_findings"}
            else "info",
            "message": "Shadow evidence is advisory and does not change scoring.",
            "read_only": True,
        },
    ]
    if shadow["shadow_risk_flag_count"]:
        findings.append(
            {
                "finding_code": "shadow_risk_flags_present",
                "severity": "warning",
                "count": shadow["shadow_risk_flag_count"],
                "read_only": True,
            }
        )
    if shadow["shadow_blocking_finding_count"]:
        findings.append(
            {
                "finding_code": "shadow_blocking_findings_present",
                "severity": "warning",
                "count": shadow["shadow_blocking_finding_count"],
                "read_only": True,
            }
        )
    if shadow["fallback_count"]:
        findings.append(
            {
                "finding_code": "shadow_fallback_present",
                "severity": "info",
                "count": shadow["fallback_count"],
                "read_only": True,
            }
        )
    if deterministic["deterministic_score"] is None:
        findings.append(
            {
                "finding_code": "deterministic_score_missing",
                "severity": "warning",
                "read_only": True,
            }
        )
    return findings


def _operator_review_summary(
    *,
    comparison_status: str,
    agreement_level: str,
    comparison_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    focus = [finding["finding_code"] for finding in comparison_findings]
    return {
        "summary_type": "shadow_sidecar_score_comparison",
        "review_status": (
            "ready_with_fallback"
            if comparison_status == STATUS_READY_WITH_FALLBACK
            else "ready"
        ),
        "agreement_level": agreement_level,
        "operator_review_only": True,
        "read_only": True,
        "recommended_review_focus": focus,
    }


def _base_payload(
    *,
    comparison_status: str,
    sidecar_config: dict[str, Any],
    deterministic: dict[str, Any],
    shadow: dict[str, Any],
    error_type: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "comparison_status": comparison_status,
        "comparison_type": "shadow_sidecar_vs_deterministic_score",
        "comparison_flag_name": SCORE_COMPARISON_FLAG,
        "comparison_enabled": comparison_status
        in {STATUS_READY, STATUS_READY_WITH_FALLBACK, STATUS_FAILED_NON_BLOCKING},
        "deterministic_score": deterministic.get("deterministic_score"),
        "deterministic_decision": _clean_text(
            deterministic.get("deterministic_decision")
        ),
        "shadow_snapshot_status": _clean_text(shadow.get("shadow_snapshot_status")),
        "shadow_agent_names": _text_list(shadow.get("shadow_agent_names")),
        "shadow_risk_flag_count": int(shadow.get("shadow_risk_flag_count") or 0),
        "shadow_blocking_finding_count": int(
            shadow.get("shadow_blocking_finding_count") or 0
        ),
        "agreement_level": "",
        "operator_review_summary": {},
        "comparison_findings": [],
        "source_deterministic_context": _snapshot(deterministic),
        "source_shadow_snapshot_context": _snapshot(shadow),
        "error_type": _clean_text(error_type),
        "sidecar_config": _snapshot(sidecar_config),
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "safety_metadata": evaluate_shadow_sidecar_score_comparison_safety(),
    }


def build_shadow_sidecar_score_comparison_payload(
    *,
    deterministic_score_context: dict[str, Any] | None = None,
    shadow_evidence_snapshot_payload: dict[str, Any] | None = None,
    sidecar_config: dict[str, Any] | None = None,
    comparison_builder: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    deterministic = _deterministic_context(_plain_dict(deterministic_score_context))
    shadow = _shadow_context(_plain_dict(shadow_evidence_snapshot_payload))
    config = _snapshot(sidecar_config or {})
    status = _status_from_config(
        sidecar_config=config,
        deterministic_context=deterministic,
        shadow_snapshot_payload=_plain_dict(shadow_evidence_snapshot_payload),
    )
    payload = _base_payload(
        comparison_status=status,
        sidecar_config=config,
        deterministic=deterministic,
        shadow=shadow,
    )
    if status != STATUS_READY:
        return payload

    try:
        if comparison_builder is not None:
            builder_payload = _snapshot(
                comparison_builder(
                    deterministic_score_context=_snapshot(deterministic),
                    shadow_evidence_snapshot_payload=_snapshot(shadow),
                )
            )
            if isinstance(builder_payload, dict):
                shadow = _shadow_context(
                    {
                        **_plain_dict(shadow_evidence_snapshot_payload),
                        **builder_payload,
                    }
                )
        agreement_level = _agreement_level(
            deterministic_score=deterministic.get("deterministic_score"),
            deterministic_decision=_clean_text(
                deterministic.get("deterministic_decision")
            ),
            shadow_risk_flag_count=shadow["shadow_risk_flag_count"],
            shadow_blocking_finding_count=shadow["shadow_blocking_finding_count"],
            fallback_count=int(shadow.get("fallback_count") or 0),
        )
        comparison_status = (
            STATUS_READY_WITH_FALLBACK
            if int(shadow.get("fallback_count") or 0)
            or "fallback" in _clean_text(shadow.get("shadow_snapshot_status"))
            else STATUS_READY
        )
        findings = _comparison_findings(
            deterministic=deterministic,
            shadow=shadow,
            agreement_level=agreement_level,
        )
        payload.update(
            {
                "comparison_status": comparison_status,
                "comparison_enabled": True,
                "shadow_snapshot_status": shadow["shadow_snapshot_status"],
                "shadow_agent_names": shadow["shadow_agent_names"],
                "shadow_risk_flag_count": shadow["shadow_risk_flag_count"],
                "shadow_blocking_finding_count": shadow[
                    "shadow_blocking_finding_count"
                ],
                "agreement_level": agreement_level,
                "comparison_findings": findings,
                "operator_review_summary": _operator_review_summary(
                    comparison_status=comparison_status,
                    agreement_level=agreement_level,
                    comparison_findings=findings,
                ),
                "source_shadow_snapshot_context": _snapshot(shadow),
            }
        )
    except Exception as exc:
        payload["comparison_status"] = STATUS_FAILED_NON_BLOCKING
        payload["comparison_enabled"] = True
        payload["error_type"] = exc.__class__.__name__
        payload["operator_review_summary"] = {
            "summary_type": "shadow_sidecar_score_comparison",
            "review_status": "failed_non_blocking",
            "operator_review_only": True,
            "read_only": True,
            "recommended_review_focus": ["retry_comparison_with_safe_inputs"],
        }
    return payload


def build_shadow_sidecar_score_comparison_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    return build_shadow_sidecar_score_comparison_payload(**kwargs)
