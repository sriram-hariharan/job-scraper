from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents import shadow_sidecar


INFLUENCE_PREVIEW_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_HUMAN_REVIEWED_INFLUENCE_PREVIEW_ENABLED"
)
KILL_SWITCH_FLAG = shadow_sidecar.KILL_SWITCH_FLAG

STATUS_NOT_ENABLED = "preview_not_enabled"
STATUS_BLOCKED_BY_KILL_SWITCH = "preview_blocked_by_kill_switch"
STATUS_BLOCKED_MISSING_DETERMINISTIC_CONTEXT = (
    "preview_blocked_missing_deterministic_context"
)
STATUS_BLOCKED_MISSING_SHADOW_COMPARISON = (
    "preview_blocked_missing_shadow_comparison"
)
STATUS_READY = "preview_ready"
STATUS_READY_WITH_FALLBACK = "preview_ready_with_fallback"
STATUS_FAILED_NON_BLOCKING = "preview_failed_non_blocking"

PREVIEW_TYPE = "human_reviewed_shadow_score_influence_preview"


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _plain_dict(value: Any) -> dict[str, Any]:
    return _snapshot(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


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


def evaluate_human_reviewed_influence_preview_safety() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "human_review_required": True,
        "approval_gate_required": True,
        "influence_preview_only": True,
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
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
        "service_wiring_added": False,
        "ui_action_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }


def _deterministic_context(source: dict[str, Any]) -> dict[str, Any]:
    nested = _plain_dict(source.get("source_deterministic_context"))
    score = _first_float(
        source.get("deterministic_score"),
        source.get("final_score"),
        source.get("score"),
        nested.get("deterministic_score"),
        nested.get("source_deterministic_score"),
    )
    decision = _first_text(
        source.get("deterministic_decision"),
        source.get("decision"),
        source.get("status"),
        nested.get("deterministic_decision"),
        nested.get("source_deterministic_decision"),
    )
    return {
        "deterministic_score": score,
        "deterministic_decision": decision,
        "score_source": _score_source(source, nested),
        "decision_counts": _plain_dict(
            source.get("decision_counts") or nested.get("decision_counts")
        ),
        "raw_context": _snapshot(source),
    }


def _shadow_comparison_context(source: dict[str, Any]) -> dict[str, Any]:
    source_shadow = _plain_dict(source.get("source_shadow_snapshot_context"))
    return {
        "comparison_status": _clean_text(source.get("comparison_status")),
        "comparison_type": _clean_text(source.get("comparison_type")),
        "agreement_level": _clean_text(source.get("agreement_level")),
        "shadow_snapshot_status": _clean_text(
            source.get("shadow_snapshot_status")
            or source_shadow.get("shadow_snapshot_status")
        ),
        "shadow_agent_names": _text_list(
            source.get("shadow_agent_names") or source_shadow.get("shadow_agent_names")
        ),
        "shadow_risk_flag_count": _safe_int(
            source.get("shadow_risk_flag_count")
            if "shadow_risk_flag_count" in source
            else source_shadow.get("shadow_risk_flag_count")
        ),
        "shadow_blocking_finding_count": _safe_int(
            source.get("shadow_blocking_finding_count")
            if "shadow_blocking_finding_count" in source
            else source_shadow.get("shadow_blocking_finding_count")
        ),
        "comparison_findings": _snapshot(source.get("comparison_findings") or []),
        "operator_review_summary": _plain_dict(
            source.get("operator_review_summary")
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


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _score_source(source: dict[str, Any], nested: dict[str, Any]) -> str:
    for label, value in (
        ("deterministic_score", source.get("deterministic_score")),
        ("final_score", source.get("final_score")),
        ("score", source.get("score")),
        ("source_deterministic_context.deterministic_score", nested.get("deterministic_score")),
        (
            "source_deterministic_context.source_deterministic_score",
            nested.get("source_deterministic_score"),
        ),
    ):
        if _safe_float(value) is not None:
            return label
    return ""


def _status_from_config(
    *,
    preview_config: dict[str, Any],
    deterministic: dict[str, Any],
    shadow_comparison_payload: dict[str, Any],
) -> str:
    config = _snapshot(preview_config or {})
    if _config_bool(config, KILL_SWITCH_FLAG, "kill_switch_enabled", default=False):
        return STATUS_BLOCKED_BY_KILL_SWITCH
    if not _config_bool(
        config,
        INFLUENCE_PREVIEW_FLAG,
        "influence_preview_enabled",
        default=False,
    ):
        return STATUS_NOT_ENABLED
    if deterministic.get("deterministic_score") is None and not _clean_text(
        deterministic.get("deterministic_decision")
    ):
        return STATUS_BLOCKED_MISSING_DETERMINISTIC_CONTEXT
    if not shadow_comparison_payload or not _clean_text(
        shadow_comparison_payload.get("comparison_status")
    ):
        return STATUS_BLOCKED_MISSING_SHADOW_COMPARISON
    return STATUS_READY


def _preview_status(shadow: dict[str, Any]) -> str:
    status = _clean_text(shadow.get("comparison_status"))
    snapshot_status = _clean_text(shadow.get("shadow_snapshot_status")).lower()
    if "fallback" in status or "fallback" in snapshot_status:
        return STATUS_READY_WITH_FALLBACK
    return STATUS_READY


def _proposed_influence_summary(
    *,
    deterministic: dict[str, Any],
    shadow: dict[str, Any],
    preview_status: str,
) -> dict[str, Any]:
    agreement_level = _clean_text(shadow.get("agreement_level"))
    risk_count = _safe_int(shadow.get("shadow_risk_flag_count"))
    blocker_count = _safe_int(shadow.get("shadow_blocking_finding_count"))
    review_focus = _text_list(
        _plain_dict(shadow.get("operator_review_summary")).get(
            "recommended_review_focus"
        )
    )
    if blocker_count:
        recommendation = "review_blocking_shadow_findings_before_any_future_influence"
    elif risk_count:
        recommendation = "review_shadow_risk_flags_before_any_future_influence"
    elif agreement_level == "aligned":
        recommendation = "no_influence_needed_without_human_approval"
    else:
        recommendation = "review_shadow_context_before_any_future_influence"
    return {
        "summary_type": "human_reviewed_influence_preview",
        "preview_status": preview_status,
        "deterministic_score_preserved": deterministic.get("deterministic_score"),
        "deterministic_decision_preserved": _clean_text(
            deterministic.get("deterministic_decision")
        ),
        "agreement_level": agreement_level,
        "shadow_risk_flag_count": risk_count,
        "shadow_blocking_finding_count": blocker_count,
        "recommended_operator_review": recommendation,
        "recommended_review_focus": review_focus,
        "read_only": True,
        "advisory_only": True,
    }


def _score_adjustment_preview(
    *,
    deterministic: dict[str, Any],
    shadow: dict[str, Any],
) -> dict[str, Any]:
    return {
        "adjustment_preview_type": "human_review_required_no_score_change",
        "source_deterministic_score": deterministic.get("deterministic_score"),
        "proposed_score_delta": 0.0,
        "score_after_preview": deterministic.get("deterministic_score"),
        "would_require_separate_approval_gate": True,
        "reason_codes": _score_preview_reason_codes(shadow),
        "did_mutate_scoring": False,
    }


def _ranking_effect_preview(shadow: dict[str, Any]) -> dict[str, Any]:
    return {
        "ranking_effect_preview_type": "human_review_required_no_ranking_change",
        "proposed_ranking_delta": 0,
        "ranking_after_preview": "unchanged",
        "would_require_separate_approval_gate": True,
        "reason_codes": _ranking_preview_reason_codes(shadow),
        "did_change_ranking": False,
    }


def _score_preview_reason_codes(shadow: dict[str, Any]) -> list[str]:
    codes = ["deterministic_score_preserved"]
    if _safe_int(shadow.get("shadow_blocking_finding_count")):
        codes.append("shadow_blockers_require_human_review")
    if _safe_int(shadow.get("shadow_risk_flag_count")):
        codes.append("shadow_risks_require_human_review")
    if "fallback" in _clean_text(shadow.get("comparison_status")):
        codes.append("shadow_fallback_requires_review")
    return codes


def _ranking_preview_reason_codes(shadow: dict[str, Any]) -> list[str]:
    codes = ["deterministic_ranking_preserved"]
    if _safe_int(shadow.get("shadow_blocking_finding_count")):
        codes.append("shadow_blockers_do_not_reorder_queue")
    if _safe_int(shadow.get("shadow_risk_flag_count")):
        codes.append("shadow_risks_do_not_reorder_queue")
    return codes


def _preview_findings(
    *,
    deterministic: dict[str, Any],
    shadow: dict[str, Any],
    preview_status: str,
) -> list[dict[str, Any]]:
    findings = [
        {
            "finding_code": "deterministic_score_context_copied",
            "severity": "info",
            "read_only": True,
        },
        {
            "finding_code": "shadow_comparison_context_copied",
            "severity": "info",
            "read_only": True,
        },
        {
            "finding_code": "human_review_and_approval_gate_required",
            "severity": "warning",
            "read_only": True,
        },
    ]
    if preview_status == STATUS_READY_WITH_FALLBACK:
        findings.append(
            {
                "finding_code": "shadow_comparison_fallback_present",
                "severity": "warning",
                "read_only": True,
            }
        )
    if _safe_int(shadow.get("shadow_risk_flag_count")):
        findings.append(
            {
                "finding_code": "shadow_risk_flags_present",
                "severity": "warning",
                "count": _safe_int(shadow.get("shadow_risk_flag_count")),
                "read_only": True,
            }
        )
    if _safe_int(shadow.get("shadow_blocking_finding_count")):
        findings.append(
            {
                "finding_code": "shadow_blocking_findings_present",
                "severity": "warning",
                "count": _safe_int(shadow.get("shadow_blocking_finding_count")),
                "read_only": True,
            }
        )
    if deterministic.get("deterministic_score") is None:
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
    preview_status: str,
    proposed_influence_summary: dict[str, Any],
    preview_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "summary_type": "human_reviewed_influence_preview",
        "review_status": (
            "ready_with_fallback"
            if preview_status == STATUS_READY_WITH_FALLBACK
            else "ready"
        ),
        "operator_review_only": True,
        "read_only": True,
        "advisory_only": True,
        "required_human_review": True,
        "approval_gate_required": True,
        "recommended_operator_review": _clean_text(
            proposed_influence_summary.get("recommended_operator_review")
        ),
        "recommended_review_focus": [
            finding["finding_code"] for finding in preview_findings
        ],
    }


def _base_payload(
    *,
    preview_status: str,
    preview_config: dict[str, Any],
    deterministic: dict[str, Any],
    shadow: dict[str, Any],
    error_type: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "preview_status": preview_status,
        "preview_type": PREVIEW_TYPE,
        "preview_flag_name": INFLUENCE_PREVIEW_FLAG,
        "preview_enabled": preview_status
        in {STATUS_READY, STATUS_READY_WITH_FALLBACK, STATUS_FAILED_NON_BLOCKING},
        "deterministic_score_context": _snapshot(deterministic),
        "shadow_comparison_context": _snapshot(shadow),
        "proposed_influence_summary": {},
        "proposed_score_adjustment_preview": {},
        "proposed_ranking_effect_preview": {},
        "required_human_review": True,
        "approval_gate_required": True,
        "operator_review_summary": {},
        "preview_findings": [],
        "error_type": _clean_text(error_type),
        "preview_config": _snapshot(preview_config),
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "safety_metadata": evaluate_human_reviewed_influence_preview_safety(),
    }


def build_human_reviewed_influence_preview_payload(
    *,
    deterministic_score_context: dict[str, Any] | None = None,
    shadow_score_comparison_context: dict[str, Any] | None = None,
    preview_config: dict[str, Any] | None = None,
    preview_builder: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    deterministic = _deterministic_context(_plain_dict(deterministic_score_context))
    shadow = _shadow_comparison_context(_plain_dict(shadow_score_comparison_context))
    config = _snapshot(preview_config or {})
    status = _status_from_config(
        preview_config=config,
        deterministic=deterministic,
        shadow_comparison_payload=_plain_dict(shadow_score_comparison_context),
    )
    payload = _base_payload(
        preview_status=status,
        preview_config=config,
        deterministic=deterministic,
        shadow=shadow,
    )
    if status != STATUS_READY:
        return payload

    try:
        if preview_builder is not None:
            builder_payload = preview_builder(
                deterministic_score_context=_snapshot(deterministic),
                shadow_score_comparison_context=_snapshot(shadow),
            )
            if isinstance(builder_payload, dict):
                shadow = _shadow_comparison_context(
                    {
                        **_plain_dict(shadow_score_comparison_context),
                        **_snapshot(builder_payload),
                    }
                )
        preview_status = _preview_status(shadow)
        influence_summary = _proposed_influence_summary(
            deterministic=deterministic,
            shadow=shadow,
            preview_status=preview_status,
        )
        findings = _preview_findings(
            deterministic=deterministic,
            shadow=shadow,
            preview_status=preview_status,
        )
        payload.update(
            {
                "preview_status": preview_status,
                "preview_enabled": True,
                "shadow_comparison_context": _snapshot(shadow),
                "proposed_influence_summary": influence_summary,
                "proposed_score_adjustment_preview": _score_adjustment_preview(
                    deterministic=deterministic,
                    shadow=shadow,
                ),
                "proposed_ranking_effect_preview": _ranking_effect_preview(shadow),
                "operator_review_summary": _operator_review_summary(
                    preview_status=preview_status,
                    proposed_influence_summary=influence_summary,
                    preview_findings=findings,
                ),
                "preview_findings": findings,
            }
        )
    except Exception as exc:
        payload["preview_status"] = STATUS_FAILED_NON_BLOCKING
        payload["preview_enabled"] = True
        payload["error_type"] = exc.__class__.__name__
        payload["operator_review_summary"] = {
            "summary_type": "human_reviewed_influence_preview",
            "review_status": "failed_non_blocking",
            "operator_review_only": True,
            "read_only": True,
            "advisory_only": True,
            "required_human_review": True,
            "approval_gate_required": True,
            "recommended_review_focus": ["retry_preview_with_safe_inputs"],
        }
    return payload


def build_human_reviewed_influence_preview_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    return build_human_reviewed_influence_preview_payload(**kwargs)
