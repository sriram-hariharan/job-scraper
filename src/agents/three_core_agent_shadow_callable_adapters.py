"""Default-off read-only callable adapters for the three core shadow agents."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents.final_application_scoring import (
    describe_final_application_scoring_result,
)
from src.agents.jd_intelligence import (
    SIGNAL_LIST_FIELDS,
    describe_jd_intelligence_result,
)
from src.agents.relevance_prefilter import (
    describe_relevance_prefilter_result,
)


ADAPTER_VERSION = "phase-17e-three-core-shadow-callable-adapters-v1"
STATUS_DISABLED = (
    "three_core_shadow_callable_adapters_skipped_default_off"
)
STATUS_READY = "three_core_shadow_callable_adapters_ready_shadow_only"
ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _job_payload(request: dict[str, Any]) -> dict[str, Any]:
    job_context = _plain_dict(request.get("job_context"))
    nested = _plain_dict(job_context.get("job_payload"))
    return nested or job_context


def _common_adapter_output(
    *,
    agent_name: str,
    responsibility: str,
    request: dict[str, Any],
    wrapper_result: dict[str, Any],
    separation: dict[str, str],
) -> dict[str, Any]:
    return {
        "agent_name": agent_name,
        "adapter_version": ADAPTER_VERSION,
        "adapter_status": "completed_shadow_only",
        "responsibility": responsibility,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "mutation_authorized": False,
        "workflow_connection_authorized": False,
        "pipeline_connection_authorized": False,
        "pipeline_stage_added": False,
        "job_context": _plain_dict(request.get("job_context")),
        "previous_outputs": _plain_dict(request.get("previous_outputs")),
        "wrapper_result": deepcopy(wrapper_result),
        "separation": deepcopy(separation),
    }


def _relevance_prefilter_adapter(
    request: dict[str, Any],
) -> dict[str, Any]:
    source = _plain_dict(request)
    job = _job_payload(source)
    summary = {
        "input_count": 0,
        "kept_count": 0,
        "dropped_count": 0,
        "reason_counts": {},
        "role_family": job.get("role_family", ""),
        "seniority": job.get("seniority", ""),
        "location_policy": job.get("location_policy", ""),
    }
    wrapper_result = describe_relevance_prefilter_result(summary)
    return _common_adapter_output(
        agent_name="relevance_prefilter",
        responsibility="prefilter_relevance_only",
        request=source,
        wrapper_result=wrapper_result,
        separation={
            "prefilter_relevance": "described_only",
            "jd_intelligence_evaluation": "not_called",
            "final_application_scoring": "not_called",
        },
    )


def _jd_intelligence_adapter(
    request: dict[str, Any],
) -> dict[str, Any]:
    source = _plain_dict(request)
    job = _job_payload(source)
    summary = {
        field_name: (
            deepcopy(job.get(field_name))
            if isinstance(job.get(field_name), list)
            else []
        )
        for field_name in SIGNAL_LIST_FIELDS
    }
    wrapper_result = describe_jd_intelligence_result(summary)
    return _common_adapter_output(
        agent_name="jd_intelligence",
        responsibility="jd_intelligence_evaluation_only",
        request=source,
        wrapper_result=wrapper_result,
        separation={
            "prefilter_relevance": "not_called",
            "jd_intelligence_evaluation": "described_only",
            "final_application_scoring": "not_called",
        },
    )


def _final_application_scoring_adapter(
    request: dict[str, Any],
) -> dict[str, Any]:
    source = _plain_dict(request)
    summary = {
        "input_count": 0,
        "scored_count": 0,
        "qualified_count": 0,
        "disqualified_count": 0,
        "score_summary": {"shadow_descriptor_only": True},
        "threshold_summary": {},
        "decision_counts": {},
    }
    wrapper_result = describe_final_application_scoring_result(summary)
    return _common_adapter_output(
        agent_name="final_application_scoring",
        responsibility="final_application_scoring_only",
        request=source,
        wrapper_result=wrapper_result,
        separation={
            "prefilter_relevance": "not_called",
            "jd_intelligence_evaluation": "not_called",
            "final_application_scoring": "described_only",
        },
    )


def three_core_shadow_callable_adapters_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "callable_adapters_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "pipeline_stage_added": False,
        "provider_runtime_not_invoked": True,
        "provider_sdk_imported": False,
        "environment_secrets_read": False,
        "network_calls_made": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_read_files": False,
        "did_write_files": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_mutate_resume": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }


def build_three_core_agent_shadow_callable_adapters(
    *,
    enabled: bool = False,
    adapter_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build injected read-only callables without connecting them anywhere."""

    context = _plain_dict(adapter_context)
    callable_map: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
    ordered_callable_adapters: list[
        dict[str, Any]
    ] = []
    if enabled is True:
        callable_map = {
            "relevance_prefilter": _relevance_prefilter_adapter,
            "jd_intelligence": _jd_intelligence_adapter,
            "final_application_scoring": (
                _final_application_scoring_adapter
            ),
        }
        ordered_callable_adapters = [
            {
                "agent_name": agent_name,
                "callable": callable_map[agent_name],
                "read_only": True,
                "shadow_only": True,
                "advisory_only": True,
                "mutation_authorized": False,
            }
            for agent_name in ORDERED_CORE_AGENT_NAMES
        ]
        status = STATUS_READY
        next_safe_step = (
            "review_three_core_shadow_callable_adapters_before_wiring"
        )
    else:
        status = STATUS_DISABLED
        next_safe_step = (
            "enable_three_core_shadow_callable_adapters_only"
        )

    return {
        "adapter_version": ADAPTER_VERSION,
        "three_core_shadow_callable_adapters_enabled": enabled is True,
        "adapter_status": status,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "callable_adapters_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "pipeline_stage_added": False,
        "workflow_connection_authorized": False,
        "pipeline_connection_authorized": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "execution_authorized": False,
        "submission_authorized": False,
        "application_execution_authorized": False,
        "final_scoring_mutation_enabled": False,
        "ranking_mutation_enabled": False,
        "queue_mutation_enabled": False,
        "resume_mutation_enabled": False,
        "ordered_core_agent_count": len(ORDERED_CORE_AGENT_NAMES),
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "callable_count": len(callable_map),
        "callable_map": callable_map,
        "ordered_callable_adapters": ordered_callable_adapters,
        "adapter_context": context,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            three_core_shadow_callable_adapters_safety_metadata()
        ),
    }
