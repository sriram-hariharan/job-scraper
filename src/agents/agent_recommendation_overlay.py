from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents import shadow_sidecar


AGENT_RECOMMENDATION_OVERLAY_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_AGENT_RECOMMENDATION_OVERLAY_ENABLED"
)
KILL_SWITCH_FLAG = shadow_sidecar.KILL_SWITCH_FLAG

STATUS_NOT_ENABLED = "overlay_not_enabled"
STATUS_BLOCKED_BY_KILL_SWITCH = "overlay_blocked_by_kill_switch"
STATUS_BLOCKED_MISSING_DETERMINISTIC_CONTEXT = (
    "overlay_blocked_missing_deterministic_context"
)
STATUS_PARTIAL = "overlay_partial_insufficient_context"
STATUS_READY = "overlay_ready"
STATUS_FAILED_NON_BLOCKING = "overlay_failed_non_blocking"


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


def evaluate_agent_recommendation_overlay_safety() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "overlay_only": True,
        "human_review_required": True,
        "approval_gate_required_for_influence": True,
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
        "ui_action_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }


def _deterministic_context(source: dict[str, Any]) -> dict[str, Any]:
    nested = _plain_dict(source.get("source_deterministic_context"))
    output = _plain_dict(source.get("output_json"))
    score_summary = _plain_dict(source.get("score_summary") or output.get("score_summary"))
    score = _first_float(
        source.get("deterministic_score"),
        source.get("final_score"),
        source.get("score"),
        source.get("top_score"),
        output.get("top_score"),
        score_summary.get("max_score"),
        score_summary.get("average_score"),
        nested.get("deterministic_score"),
        nested.get("source_deterministic_score"),
    )
    decision = _first_text(
        source.get("deterministic_decision"),
        source.get("decision"),
        source.get("status"),
        output.get("status"),
        nested.get("deterministic_decision"),
        nested.get("source_deterministic_decision"),
    )
    return {
        "deterministic_score": score,
        "deterministic_decision": decision,
        "decision_counts": _plain_dict(source.get("decision_counts") or output.get("decision_counts")),
        "raw_context": _snapshot(source),
    }


def _comparison_context(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "comparison_status": _clean_text(source.get("comparison_status")),
        "agreement_level": _clean_text(source.get("agreement_level")),
        "shadow_snapshot_status": _clean_text(source.get("shadow_snapshot_status")),
        "shadow_risk_flag_count": int(source.get("shadow_risk_flag_count") or 0),
        "shadow_blocking_finding_count": int(
            source.get("shadow_blocking_finding_count") or 0
        ),
        "operator_review_summary": _plain_dict(source.get("operator_review_summary")),
        "raw_context": _snapshot(source),
    }


def _influence_preview_context(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "preview_status": _clean_text(source.get("preview_status")),
        "preview_type": _clean_text(source.get("preview_type")),
        "proposed_influence_summary": _plain_dict(
            source.get("proposed_influence_summary")
        ),
        "proposed_score_adjustment_preview": _plain_dict(
            source.get("proposed_score_adjustment_preview")
        ),
        "proposed_ranking_effect_preview": _plain_dict(
            source.get("proposed_ranking_effect_preview")
        ),
        "operator_review_summary": _plain_dict(source.get("operator_review_summary")),
        "raw_context": _snapshot(source),
    }


def _approval_request_context(source: dict[str, Any]) -> dict[str, Any]:
    approval_request = _plain_dict(source.get("approval_request"))
    return {
        "request_status": _clean_text(
            source.get("request_status") or source.get("approval_creation_status")
        ),
        "created_approval_request_id": _clean_text(
            source.get("created_approval_request_id")
        ),
        "approval_request_created": bool(source.get("approval_request_created")),
        "approval_status": _clean_text(approval_request.get("approval_status")),
        "approval_request": approval_request,
        "raw_context": _snapshot(source),
    }


def _status_from_config(
    *,
    overlay_config: dict[str, Any],
    deterministic: dict[str, Any],
) -> str:
    config = _snapshot(overlay_config or {})
    if _config_bool(config, KILL_SWITCH_FLAG, "kill_switch_enabled", default=False):
        return STATUS_BLOCKED_BY_KILL_SWITCH
    if not _config_bool(
        config,
        AGENT_RECOMMENDATION_OVERLAY_FLAG,
        "agent_recommendation_overlay_enabled",
        default=False,
    ):
        return STATUS_NOT_ENABLED
    if deterministic.get("deterministic_score") is None and not _clean_text(
        deterministic.get("deterministic_decision")
    ):
        return STATUS_BLOCKED_MISSING_DETERMINISTIC_CONTEXT
    return STATUS_READY


def _recommended_review_action(
    *,
    overlay_status: str,
    comparison: dict[str, Any],
    influence_preview: dict[str, Any],
    approval_request: dict[str, Any],
) -> str:
    if overlay_status in {
        STATUS_NOT_ENABLED,
        STATUS_BLOCKED_BY_KILL_SWITCH,
        STATUS_BLOCKED_MISSING_DETERMINISTIC_CONTEXT,
    }:
        return "insufficient_context"

    approval_status = _clean_text(approval_request.get("approval_status")).lower()
    request_status = _clean_text(approval_request.get("request_status"))
    if approval_status == "approved":
        return "approved_influence_available"
    if request_status == "created" or approval_request.get("approval_request_created") is True:
        return "approval_pending"

    preview_status = _clean_text(influence_preview.get("preview_status"))
    if preview_status in {"preview_ready", "preview_ready_with_fallback"}:
        return "request_influence_approval"

    comparison_status = _clean_text(comparison.get("comparison_status"))
    if comparison_status:
        agreement = _clean_text(comparison.get("agreement_level"))
        risk_count = int(comparison.get("shadow_risk_flag_count") or 0)
        blocker_count = int(comparison.get("shadow_blocking_finding_count") or 0)
        if agreement == "aligned" and risk_count == 0 and blocker_count == 0:
            return "no_agent_action"
        return "review_agent_preview"

    return "insufficient_context"


def _overlay_findings(
    *,
    deterministic: dict[str, Any],
    comparison: dict[str, Any],
    influence_preview: dict[str, Any],
    approval_request: dict[str, Any],
) -> list[dict[str, Any]]:
    findings = [
        {
            "finding_code": "deterministic_context_preserved",
            "severity": "info",
            "read_only": True,
        }
    ]
    if comparison.get("comparison_status"):
        findings.append(
            {
                "finding_code": "shadow_score_comparison_available",
                "severity": "info",
                "read_only": True,
            }
        )
    else:
        findings.append(
            {
                "finding_code": "shadow_score_comparison_missing",
                "severity": "warning",
                "read_only": True,
            }
        )
    if influence_preview.get("preview_status"):
        findings.append(
            {
                "finding_code": "human_reviewed_influence_preview_available",
                "severity": "info",
                "read_only": True,
            }
        )
    else:
        findings.append(
            {
                "finding_code": "human_reviewed_influence_preview_missing",
                "severity": "warning",
                "read_only": True,
            }
        )
    if approval_request.get("request_status") or approval_request.get("approval_status"):
        findings.append(
            {
                "finding_code": "approval_request_context_available",
                "severity": "info",
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


def build_agent_recommendation_overlay_payload(
    *,
    deterministic_score_context: dict[str, Any] | None = None,
    shadow_score_comparison_context: dict[str, Any] | None = None,
    human_reviewed_influence_preview_payload: dict[str, Any] | None = None,
    influence_approval_request_payload: dict[str, Any] | None = None,
    overlay_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = _plain_dict(overlay_config)
    deterministic = _deterministic_context(_plain_dict(deterministic_score_context))
    comparison = _comparison_context(_plain_dict(shadow_score_comparison_context))
    influence_preview = _influence_preview_context(
        _plain_dict(human_reviewed_influence_preview_payload)
    )
    approval_request = _approval_request_context(
        _plain_dict(influence_approval_request_payload)
    )
    overlay_status = _status_from_config(
        overlay_config=config,
        deterministic=deterministic,
    )
    if overlay_status == STATUS_READY and (
        not comparison.get("comparison_status") or not influence_preview.get("preview_status")
    ):
        overlay_status = STATUS_PARTIAL
    recommended_action = _recommended_review_action(
        overlay_status=overlay_status,
        comparison=comparison,
        influence_preview=influence_preview,
        approval_request=approval_request,
    )
    findings = _overlay_findings(
        deterministic=deterministic,
        comparison=comparison,
        influence_preview=influence_preview,
        approval_request=approval_request,
    )
    return {
        "schema_version": "phase6_agent_recommendation_overlay_v1",
        "overlay_status": overlay_status,
        "overlay_type": "agent_recommendation_overlay",
        "overlay_enabled": overlay_status
        not in {STATUS_NOT_ENABLED, STATUS_BLOCKED_BY_KILL_SWITCH},
        "deterministic_decision_context": deterministic,
        "shadow_score_comparison": comparison,
        "human_reviewed_influence_preview": influence_preview,
        "approval_request_context": approval_request,
        "recommended_review_action": recommended_action,
        "recommended_review_label": recommended_action.replace("_", " ").title(),
        "overlay_findings": findings,
        "operator_review_summary": {
            "summary_type": "agent_recommendation_overlay",
            "review_status": overlay_status,
            "recommended_review_action": recommended_action,
            "operator_review_only": True,
            "read_only": True,
            "advisory_only": True,
            "human_review_required": True,
            "approval_gate_required_for_influence": True,
        },
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "safety_metadata": evaluate_agent_recommendation_overlay_safety(),
    }
