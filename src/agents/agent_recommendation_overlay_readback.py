from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents import shadow_sidecar


STATUS_NOT_FOUND = "pipeline_generated_overlay_not_found"
STATUS_READY = "pipeline_generated_overlay_readback_ready"
STATUS_FAILED_NON_BLOCKING = "pipeline_generated_overlay_readback_failed_non_blocking"


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def evaluate_pipeline_generated_overlay_readback_safety() -> dict[str, bool]:
    return {
        "read_only": True,
        "readback_only": True,
        "advisory_only": True,
        "pipeline_generated_overlay_readback": True,
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


def _direct_auto_payload(source: dict[str, Any]) -> dict[str, Any]:
    if _clean_text(source.get("auto_generation_status")):
        return source
    return _plain_dict(source.get("agent_recommendation_overlay_auto_generation"))


def _auto_payload_from_step(step: dict[str, Any]) -> dict[str, Any]:
    output = _plain_dict(step.get("output_json"))
    direct = _direct_auto_payload(output)
    if direct:
        return direct
    trace_capture = _plain_dict(output.get("trace_capture"))
    return _direct_auto_payload(trace_capture)


def _extract_auto_payload(source: Any) -> dict[str, Any]:
    payload = _plain_dict(source)
    if not payload:
        return {}

    direct = _direct_auto_payload(payload)
    if direct:
        return direct

    trace_capture = _plain_dict(payload.get("trace_capture"))
    direct = _direct_auto_payload(trace_capture)
    if direct:
        return direct

    trace_persistence = _plain_dict(payload.get("trace_persistence"))
    direct = _extract_auto_payload(trace_persistence)
    if direct:
        return direct

    persistence_records = _plain_dict(payload.get("persistence_records"))
    direct = _extract_auto_payload(persistence_records)
    if direct:
        return direct

    agent_step = _plain_dict(payload.get("agent_step_record"))
    if agent_step:
        direct = _auto_payload_from_step(agent_step)
        if direct:
            return direct

    steps = []
    if isinstance(payload.get("agent_steps"), list):
        steps = payload.get("agent_steps") or []
    elif isinstance(payload.get("steps"), list):
        steps = payload.get("steps") or []
    elif isinstance(_plain_dict(payload.get("trace_readback")).get("agent_steps"), list):
        steps = _plain_dict(payload.get("trace_readback")).get("agent_steps") or []
    for step in steps:
        direct = _auto_payload_from_step(_plain_dict(step))
        if direct:
            return direct

    nested = _plain_dict(payload.get("trace_readback"))
    if nested:
        return _extract_auto_payload(nested)

    return {}


def _readback_status(auto_payload: dict[str, Any]) -> str:
    if not auto_payload:
        return STATUS_NOT_FOUND
    status = _clean_text(auto_payload.get("auto_generation_status"))
    if not status:
        return STATUS_NOT_FOUND
    return STATUS_READY


def build_pipeline_generated_agent_recommendation_overlay_readback_payload(
    *,
    hook_payload: dict[str, Any] | None = None,
    trace_capture_payload: dict[str, Any] | None = None,
    trace_persistence_payload: dict[str, Any] | None = None,
    trace_readback_payload: dict[str, Any] | None = None,
    readback_source: dict[str, Any] | None = None,
    readback_reader: Any = None,
) -> dict[str, Any]:
    """Read back a pipeline-generated overlay without regenerating or mutating it."""

    sources = [
        _plain_dict(hook_payload),
        _plain_dict(trace_capture_payload),
        _plain_dict(trace_persistence_payload),
        _plain_dict(trace_readback_payload),
        _plain_dict(readback_source),
    ]
    reader_result: dict[str, Any] = {}
    readback_attempted = False
    if not any(sources) and readback_reader is not None:
        try:
            readback_attempted = True
            sources.append(_plain_dict(readback_reader({})))
            reader_result = {"ok": True}
        except Exception as exc:
            return {
                "schema_version": shadow_sidecar.SCHEMA_VERSION,
                "readback_status": STATUS_FAILED_NON_BLOCKING,
                "readback_only": True,
                "readback_attempted": True,
                "reader_result": {"ok": False, "error_type": exc.__class__.__name__},
                "pipeline_generated_overlay_found": False,
                "pipeline_generated_overlay": {},
                "agent_recommendation_overlay": {},
                "auto_generation_status": "",
                "provider_calls_disabled_in_tests": True,
                "requires_live_database": False,
                "live_provider_backed_automated_agents": 0,
                "mutation_authorized_agents": 0,
                "safety_metadata": evaluate_pipeline_generated_overlay_readback_safety(),
            }

    auto_payload: dict[str, Any] = {}
    for source in sources:
        auto_payload = _extract_auto_payload(source)
        if auto_payload:
            break

    overlay = _plain_dict(auto_payload.get("agent_recommendation_overlay"))
    status = _readback_status(auto_payload)
    return {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "readback_status": status,
        "readback_only": True,
        "readback_attempted": readback_attempted,
        "reader_result": reader_result,
        "pipeline_generated_overlay_found": bool(auto_payload),
        "pipeline_generated_overlay": auto_payload,
        "agent_recommendation_overlay": overlay,
        "auto_generation_status": _clean_text(auto_payload.get("auto_generation_status")),
        "overlay_status": _clean_text(overlay.get("overlay_status")),
        "recommended_review_action": _clean_text(
            overlay.get("recommended_review_action")
        ),
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "safety_metadata": evaluate_pipeline_generated_overlay_readback_safety(),
    }


def build_pipeline_generated_agent_recommendation_overlay_readback_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    return build_pipeline_generated_agent_recommendation_overlay_readback_payload(
        **kwargs
    )
