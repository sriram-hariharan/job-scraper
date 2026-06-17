from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents import shadow_sidecar


EVIDENCE_SNAPSHOT_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_EVIDENCE_SNAPSHOT_ENABLED"
)
GLOBAL_SIDECAR_FLAG = shadow_sidecar.GLOBAL_SIDECAR_FLAG
KILL_SWITCH_FLAG = shadow_sidecar.KILL_SWITCH_FLAG

STATUS_NOT_ENABLED = "snapshot_not_enabled"
STATUS_BLOCKED_BY_KILL_SWITCH = "snapshot_blocked_by_kill_switch"
STATUS_BLOCKED_MISSING_CONTEXT = "snapshot_blocked_missing_context"
STATUS_READY = "snapshot_ready"
STATUS_READY_WITH_FALLBACK = "snapshot_ready_with_fallback"
STATUS_FAILED_NON_BLOCKING = "snapshot_failed_non_blocking"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


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


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return [_clean_text(item) for item in value if _clean_text(item)]


def _plain_dict(value: Any) -> dict[str, Any]:
    return _snapshot(value) if isinstance(value, dict) else {}


def evaluate_shadow_sidecar_evidence_snapshot_safety() -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "evidence_snapshot_only": True,
        "operator_review_only": True,
        "provider_calls_disabled_in_tests": True,
        "did_read_database": False,
        "did_write_database": False,
        "did_write_agent_trace_run": False,
        "did_write_agent_trace_step": False,
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


def _base_payload(
    *,
    status: str,
    sidecar_config: dict[str, Any],
    hook_payload: dict[str, Any] | None,
    trace_persistence_payload: dict[str, Any] | None,
    trace_readback_payload: dict[str, Any] | None,
    error_type: str = "",
) -> dict[str, Any]:
    hook = _plain_dict(hook_payload)
    persistence = _plain_dict(trace_persistence_payload)
    readback = _plain_dict(trace_readback_payload)
    return {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "snapshot_status": status,
        "snapshot_type": "shadow_sidecar_evidence_snapshot",
        "snapshot_flag_name": EVIDENCE_SNAPSHOT_FLAG,
        "snapshot_enabled": status
        in {STATUS_READY, STATUS_READY_WITH_FALLBACK, STATUS_FAILED_NON_BLOCKING},
        "source_hook_status": _clean_text(hook.get("hook_status")),
        "source_chain_status": "",
        "agent_names": [],
        "enabled_agent_count": 0,
        "fallback_count": 0,
        "risk_flag_count": 0,
        "blocking_finding_count": 0,
        "readback_status": _clean_text(readback.get("trace_readback_status")),
        "trace_persistence_status": _clean_text(
            persistence.get("trace_persistence_status")
            or _plain_dict(hook.get("trace_persistence")).get(
                "trace_persistence_status"
            )
        ),
        "source_deterministic_context": _source_deterministic_context(hook, {}),
        "operator_review_summary": {},
        "evidence_items": [],
        "error_type": _clean_text(error_type),
        "sidecar_config": _snapshot(sidecar_config),
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "safety_metadata": evaluate_shadow_sidecar_evidence_snapshot_safety(),
    }


def _status_from_config(
    *,
    sidecar_config: dict[str, Any],
    has_context: bool,
) -> str:
    config = _snapshot(sidecar_config or {})
    if _config_bool(config, KILL_SWITCH_FLAG, "kill_switch_enabled", default=False):
        return STATUS_BLOCKED_BY_KILL_SWITCH
    if not _config_bool(config, GLOBAL_SIDECAR_FLAG, "sidecar_enabled", default=False):
        return STATUS_NOT_ENABLED
    if not _config_bool(
        config,
        EVIDENCE_SNAPSHOT_FLAG,
        "evidence_snapshot_enabled",
        default=False,
    ):
        return STATUS_NOT_ENABLED
    if not has_context:
        return STATUS_BLOCKED_MISSING_CONTEXT
    return STATUS_READY


def _first_dict(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, dict) and value:
            return _snapshot(value)
    return {}


def _chain_payload_from_sources(
    *,
    hook_payload: dict[str, Any],
    trace_capture_payload: dict[str, Any],
) -> dict[str, Any]:
    chain = _first_dict(
        hook_payload.get("chain_payload"),
        trace_capture_payload.get("chain_payload"),
    )
    if chain:
        return chain
    chain_summary = _plain_dict(trace_capture_payload.get("chain_summary"))
    if chain_summary:
        return {
            "chain_status": chain_summary.get("chain_status"),
            "stage_order": chain_summary.get("stage_order"),
            "stage_statuses": chain_summary.get("stage_statuses"),
            "fallback_used": chain_summary.get("fallback_used"),
            "readiness_decision": {
                "readiness_status": chain_summary.get("readiness_status")
            },
        }
    return {}


def _ordered_agent_names(
    *,
    chain_payload: dict[str, Any],
    trace_readback_payload: dict[str, Any],
) -> list[str]:
    names = _text_list(chain_payload.get("stage_order"))
    for result in list(chain_payload.get("ordered_agent_results") or []):
        if isinstance(result, dict):
            names.extend(_text_list([result.get("agent_name")]))
    readback = _plain_dict(trace_readback_payload.get("trace_readback"))
    for step in list(readback.get("agent_steps") or []):
        if isinstance(step, dict):
            names.extend(_text_list([step.get("agent_name")]))
    ordered: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name not in seen:
            ordered.append(name)
            seen.add(name)
    return ordered


def _recursive_count(value: Any, target_keys: set[str]) -> int:
    if isinstance(value, dict):
        count = 0
        for key, item in value.items():
            if key in target_keys:
                if isinstance(item, (list, tuple, set)):
                    count += len([entry for entry in item if _clean_text(entry)])
                elif isinstance(item, dict):
                    count += len(item)
                elif _clean_text(item):
                    count += 1
            count += _recursive_count(item, target_keys)
        return count
    if isinstance(value, (list, tuple, set)):
        return sum(_recursive_count(item, target_keys) for item in value)
    return 0


def _fallback_count(chain_payload: dict[str, Any], hook_payload: dict[str, Any]) -> int:
    count = 0
    if bool(chain_payload.get("fallback_used")):
        count += 1
    for status in _text_list(
        [
            chain_payload.get("chain_status"),
            chain_payload.get("sidecar_chain_status"),
            hook_payload.get("hook_status"),
        ]
    ):
        if any(marker in status for marker in ("fallback", "skipped", "not_enabled")):
            count += 1
    for status in _plain_dict(chain_payload.get("stage_statuses")).values():
        cleaned = _clean_text(status)
        if any(marker in cleaned for marker in ("fallback", "skipped", "not_enabled")):
            count += 1
    return count


def _source_deterministic_context(
    hook_payload: dict[str, Any],
    trace_capture_payload: dict[str, Any],
) -> dict[str, Any]:
    source = hook_payload if hook_payload else trace_capture_payload
    return {
        "source_deterministic_stage": _clean_text(
            source.get("source_deterministic_stage")
        ),
        "source_deterministic_status": _clean_text(
            source.get("source_deterministic_status")
        ),
        "source_deterministic_score": source.get("source_deterministic_score"),
        "source_deterministic_decision": _clean_text(
            source.get("source_deterministic_decision")
        ),
        "source_deterministic_reason_codes": _text_list(
            source.get("source_deterministic_reason_codes")
        ),
    }


def _operator_review_summary(
    *,
    snapshot_status: str,
    agent_names: list[str],
    fallback_count: int,
    risk_flag_count: int,
    blocking_finding_count: int,
) -> dict[str, Any]:
    focus: list[str] = []
    if fallback_count:
        focus.append("review_shadow_fallbacks")
    if risk_flag_count:
        focus.append("review_shadow_risk_flags")
    if blocking_finding_count:
        focus.append("review_shadow_blocking_findings")
    if not agent_names:
        focus.append("confirm_shadow_agents_were_available")
    if not focus:
        focus.append("review_shadow_sidecar_summary")
    return {
        "summary_type": "shadow_sidecar_evidence_snapshot",
        "review_status": (
            "ready_with_fallback"
            if snapshot_status == STATUS_READY_WITH_FALLBACK
            else "ready"
        ),
        "read_only": True,
        "operator_review_only": True,
        "recommended_review_focus": focus,
    }


def _evidence_items(
    *,
    source_hook_status: str,
    source_chain_status: str,
    agent_names: list[str],
    readback_status: str,
    trace_persistence_status: str,
    source_deterministic_context: dict[str, Any],
) -> list[dict[str, Any]]:
    fields = [
        ("hook_status", source_hook_status, "shadow_sidecar_hook"),
        ("chain_status", source_chain_status, "shadow_sidecar_chain"),
        ("agent_names", agent_names, "shadow_sidecar_chain"),
        ("trace_readback_status", readback_status, "shadow_sidecar_trace_readback"),
        (
            "trace_persistence_status",
            trace_persistence_status,
            "shadow_sidecar_trace_persistence",
        ),
        (
            "source_deterministic_context",
            source_deterministic_context,
            "deterministic_pipeline_context",
        ),
    ]
    return [
        {
            "evidence_id": f"shadow_snapshot_{index}_{label}",
            "label": label,
            "value": _snapshot(value),
            "source": source,
            "read_only": True,
        }
        for index, (label, value, source) in enumerate(fields, start=1)
        if value not in ("", [], {})
    ]


def _build_snapshot_body(
    *,
    status: str,
    hook_payload: dict[str, Any],
    trace_capture_payload: dict[str, Any],
    trace_persistence_payload: dict[str, Any],
    trace_readback_payload: dict[str, Any],
) -> dict[str, Any]:
    chain_payload = _chain_payload_from_sources(
        hook_payload=hook_payload,
        trace_capture_payload=trace_capture_payload,
    )
    agent_names = _ordered_agent_names(
        chain_payload=chain_payload,
        trace_readback_payload=trace_readback_payload,
    )
    fallback_count = _fallback_count(chain_payload, hook_payload)
    risk_flag_count = _recursive_count(
        [chain_payload, trace_capture_payload],
        {"risk_flags", "agent_risk_flags", "unsupported_claim_risks"},
    )
    blocking_finding_count = _recursive_count(
        [chain_payload, trace_capture_payload],
        {"blocking_findings", "agent_blocking_findings", "evidence_gaps"},
    )
    final_status = STATUS_READY_WITH_FALLBACK if fallback_count else status
    source_hook_status = _clean_text(
        hook_payload.get("hook_status") or trace_capture_payload.get("hook_status")
    )
    source_chain_status = _clean_text(
        chain_payload.get("chain_status") or chain_payload.get("sidecar_chain_status")
    )
    readback_status = _clean_text(trace_readback_payload.get("trace_readback_status"))
    trace_persistence_status = _clean_text(
        trace_persistence_payload.get("trace_persistence_status")
        or _plain_dict(hook_payload.get("trace_persistence")).get(
            "trace_persistence_status"
        )
    )
    deterministic_context = _source_deterministic_context(
        hook_payload,
        trace_capture_payload,
    )
    return {
        "snapshot_status": final_status,
        "source_hook_status": source_hook_status,
        "source_chain_status": source_chain_status,
        "agent_names": agent_names,
        "enabled_agent_count": len(agent_names),
        "fallback_count": fallback_count,
        "risk_flag_count": risk_flag_count,
        "blocking_finding_count": blocking_finding_count,
        "readback_status": readback_status,
        "trace_persistence_status": trace_persistence_status,
        "source_deterministic_context": deterministic_context,
        "operator_review_summary": _operator_review_summary(
            snapshot_status=final_status,
            agent_names=agent_names,
            fallback_count=fallback_count,
            risk_flag_count=risk_flag_count,
            blocking_finding_count=blocking_finding_count,
        ),
        "evidence_items": _evidence_items(
            source_hook_status=source_hook_status,
            source_chain_status=source_chain_status,
            agent_names=agent_names,
            readback_status=readback_status,
            trace_persistence_status=trace_persistence_status,
            source_deterministic_context=deterministic_context,
        ),
    }


def build_shadow_sidecar_evidence_snapshot_payload(
    *,
    hook_payload: dict[str, Any] | None = None,
    trace_capture_payload: dict[str, Any] | None = None,
    trace_persistence_payload: dict[str, Any] | None = None,
    trace_readback_payload: dict[str, Any] | None = None,
    sidecar_config: dict[str, Any] | None = None,
    snapshot_builder: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    hook = _plain_dict(hook_payload)
    trace_capture = _plain_dict(trace_capture_payload)
    persistence = _plain_dict(trace_persistence_payload)
    readback = _plain_dict(trace_readback_payload)
    config = _snapshot(sidecar_config or {})
    status = _status_from_config(
        sidecar_config=config,
        has_context=bool(hook or trace_capture or persistence or readback),
    )
    payload = _base_payload(
        status=status,
        sidecar_config=config,
        hook_payload=hook,
        trace_persistence_payload=persistence,
        trace_readback_payload=readback,
    )
    if status != STATUS_READY:
        return payload

    try:
        if snapshot_builder is not None:
            builder_payload = _snapshot(
                snapshot_builder(
                    hook_payload=_snapshot(hook),
                    trace_capture_payload=_snapshot(trace_capture),
                    trace_persistence_payload=_snapshot(persistence),
                    trace_readback_payload=_snapshot(readback),
                )
            )
            if isinstance(builder_payload, dict):
                trace_capture = _first_dict(builder_payload, trace_capture)
        payload.update(
            _build_snapshot_body(
                status=status,
                hook_payload=hook,
                trace_capture_payload=trace_capture,
                trace_persistence_payload=persistence,
                trace_readback_payload=readback,
            )
        )
    except Exception as exc:
        payload["snapshot_status"] = STATUS_FAILED_NON_BLOCKING
        payload["snapshot_enabled"] = True
        payload["error_type"] = exc.__class__.__name__
        payload["operator_review_summary"] = {
            "summary_type": "shadow_sidecar_evidence_snapshot",
            "review_status": "failed_non_blocking",
            "read_only": True,
            "operator_review_only": True,
            "recommended_review_focus": ["retry_snapshot_with_safe_inputs"],
        }
    return payload


def build_shadow_sidecar_evidence_snapshot_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    return build_shadow_sidecar_evidence_snapshot_payload(**kwargs)
