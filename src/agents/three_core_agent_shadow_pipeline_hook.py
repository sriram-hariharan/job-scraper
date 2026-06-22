"""Default-off agent-side shadow hook for the three core agents."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable


HOOK_VERSION = "phase-17a-three-core-agent-shadow-pipeline-hook-v1"
STATUS_DISABLED = "three_core_shadow_pipeline_hook_skipped_default_off"
STATUS_BLOCKED = "three_core_shadow_pipeline_hook_blocked"
STATUS_COMPLETED = "three_core_shadow_pipeline_hook_completed_shadow_only"
STATUS_FAILED = "three_core_shadow_pipeline_hook_failed_closed"
READY_CONNECTION_PLAN_STATUS = (
    "three_core_shadow_pipeline_connection_plan_ready_no_pipeline_change"
)
ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)


def three_core_agent_shadow_pipeline_hook_safety_metadata(
) -> dict[str, bool]:
    return {
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "shadow_pipeline_hook_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "pipeline_stage_not_added": True,
        "provider_runtime_not_invoked": True,
        "provider_execution_added": False,
        "provider_client_constructed": False,
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


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _ordered_names(plan: dict[str, Any]) -> tuple[str, ...]:
    names = plan.get("ordered_core_agent_names")
    if not isinstance(names, (list, tuple)):
        return ()
    return tuple(str(name or "").strip() for name in names)


def _planned_connections_are_shadow_only(
    plan: dict[str, Any],
) -> bool:
    connections = plan.get("ordered_planned_connections")
    if not isinstance(connections, list):
        return False
    if len(connections) != len(ORDERED_CORE_AGENT_NAMES):
        return False
    return all(
        isinstance(item, dict) and item.get("shadow_only") is True
        for item in connections
    )


def _connection_plan_ready(plan: dict[str, Any]) -> bool:
    return all(
        (
            bool(plan),
            plan.get("connection_plan_status")
            == READY_CONNECTION_PLAN_STATUS,
            plan.get("shadow_only") is True,
            plan.get("pipeline_not_connected") is True,
            plan.get("pipeline_stage_not_added") is True,
            plan.get("workflow_connection_authorized") is False,
            plan.get("pipeline_connection_authorized") is False,
            _ordered_names(plan) == ORDERED_CORE_AGENT_NAMES,
            _planned_connections_are_shadow_only(plan),
        )
    )


def _normalized_shadow_result(
    agent_name: str,
    response: Any,
) -> dict[str, Any]:
    output = (
        deepcopy(response)
        if isinstance(response, dict)
        else {"value": deepcopy(response)}
    )
    return {
        "agent_name": agent_name,
        "status": "completed_shadow_only",
        "shadow_only": True,
        "advisory_only": True,
        "mutation_authorized": False,
        "workflow_connection_authorized": False,
        "pipeline_connection_authorized": False,
        "pipeline_stage_added": False,
        "output": output,
    }


def run_three_core_agent_shadow_pipeline_hook(
    *,
    enabled: bool = False,
    connection_plan: dict[str, Any] | None = None,
    job_context: dict[str, Any] | None = None,
    relevance_prefilter_callable: Callable[
        [dict[str, Any]], dict[str, Any]
    ]
    | None = None,
    jd_intelligence_callable: Callable[
        [dict[str, Any]], dict[str, Any]
    ]
    | None = None,
    final_application_scoring_callable: Callable[
        [dict[str, Any]], dict[str, Any]
    ]
    | None = None,
    hook_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run only explicitly supplied shadow callables after strict checks."""

    plan = _plain_dict(connection_plan)
    job = _plain_dict(job_context)
    context = _plain_dict(hook_context)
    names_match = _ordered_names(plan) == ORDERED_CORE_AGENT_NAMES
    planned_connections_shadow_only = (
        _planned_connections_are_shadow_only(plan)
    )
    plan_ready = _connection_plan_ready(plan)
    callables = (
        relevance_prefilter_callable,
        jd_intelligence_callable,
        final_application_scoring_callable,
    )
    callable_checks = tuple(callable(item) for item in callables)
    checks = {
        "connection_plan_supplied": bool(plan),
        "connection_plan_ready": plan_ready,
        "job_context_supplied": bool(job),
        "relevance_prefilter_callable_supplied": callable_checks[0],
        "jd_intelligence_callable_supplied": callable_checks[1],
        "final_application_scoring_callable_supplied": callable_checks[2],
        "ordered_core_agent_names_match": names_match,
        "planned_connections_are_shadow_only": (
            planned_connections_shadow_only
        ),
        "pipeline_not_connected": True,
        "pipeline_stage_not_added": True,
        "workflow_connection_not_authorized": True,
        "pipeline_connection_not_authorized": True,
        "mutation_not_authorized": True,
        "scoring_mutation_blocked": True,
        "ranking_mutation_blocked": True,
        "queue_mutation_blocked": True,
        "resume_mutation_blocked": True,
        "application_execution_blocked": True,
        "application_submission_blocked": True,
        "prefilter_relevance_separation_preserved": True,
        "jd_intelligence_evaluation_separation_preserved": True,
        "final_application_scoring_separation_preserved": True,
        "hook_context_supplied": bool(context),
    }
    complete = all(
        (
            plan_ready,
            bool(job),
            *callable_checks,
            names_match,
            planned_connections_shadow_only,
        )
    )
    ordered_results: list[dict[str, Any]] = []
    previous_outputs: dict[str, dict[str, Any]] = {}
    failure: dict[str, Any] = {}

    if enabled is not True:
        status = STATUS_DISABLED
        next_safe_step = "enable_three_core_shadow_pipeline_hook_only"
    elif not complete:
        status = STATUS_BLOCKED
        next_safe_step = "complete_three_core_shadow_pipeline_hook_inputs"
    else:
        status = STATUS_COMPLETED
        next_safe_step = (
            "review_three_core_shadow_pipeline_hook_before_pipeline_wiring"
        )
        for agent_name, agent_callable in zip(
            ORDERED_CORE_AGENT_NAMES,
            callables,
        ):
            request = {
                "agent_name": agent_name,
                "ordered_core_agent_names": list(
                    ORDERED_CORE_AGENT_NAMES
                ),
                "job_context": deepcopy(job),
                "previous_outputs": deepcopy(previous_outputs),
                "shadow_only": True,
                "mutation_authorized": False,
                "workflow_connection_authorized": False,
                "pipeline_stage_added": False,
            }
            try:
                response = agent_callable(request)
            except Exception as error:
                status = STATUS_FAILED
                next_safe_step = (
                    "fix_three_core_shadow_pipeline_hook_error_before_retry"
                )
                failure = {
                    "failed_agent_name": agent_name,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "failed_closed": True,
                }
                break
            result = _normalized_shadow_result(agent_name, response)
            ordered_results.append(result)
            previous_outputs[agent_name] = deepcopy(result["output"])

    return {
        "hook_version": HOOK_VERSION,
        "three_core_shadow_pipeline_hook_enabled": enabled is True,
        "hook_status": status,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "shadow_pipeline_hook_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "pipeline_stage_not_added": True,
        "provider_runtime_not_invoked": True,
        "ordered_core_agent_count": len(ORDERED_CORE_AGENT_NAMES),
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "workflow_connection_authorized": False,
        "pipeline_connection_authorized": False,
        "pipeline_stage_added": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "application_execution_authorized": False,
        "final_scoring_mutation_enabled": False,
        "ranking_mutation_enabled": False,
        "queue_mutation_enabled": False,
        "resume_mutation_enabled": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "connection_plan_summary": {
            "connection_plan_supplied": bool(plan),
            "connection_plan_status": str(
                plan.get("connection_plan_status") or ""
            ).strip(),
            "connection_plan_ready": plan_ready,
            "shadow_only": plan.get("shadow_only") is True,
            "source_connection_plan": plan,
        },
        "job_context_summary": {
            "job_context_supplied": bool(job),
            "source_job_context": job,
        },
        "hook_context_summary": {
            "hook_context_supplied": bool(context),
            "source_hook_context": context,
        },
        "three_core_shadow_pipeline_hook": {
            "scope": "three_core_agent_shadow_pipeline_hook",
            "hook_checks": checks,
            "hook_state": {
                "workflow_connection_authorized": False,
                "pipeline_connection_authorized": False,
                "pipeline_stage_added": False,
                "execution_authorized": False,
                "submission_authorized": False,
                "mutation_authorized": False,
            },
        },
        "ordered_shadow_results": ordered_results,
        "shadow_result_count": len(ordered_results),
        "previous_outputs": deepcopy(previous_outputs),
        "failure": failure,
        "decision_boundaries": {
            "prefilter_relevance_is_separate": True,
            "jd_intelligence_evaluation_is_separate": True,
            "final_application_scoring_is_separate": True,
            "prefilter_output_modified": False,
            "jd_evaluation_behavior_modified": False,
            "final_scoring_behavior_modified": False,
        },
        "forbidden_mutation_and_application_paths": {
            "workflow_connection_allowed": False,
            "pipeline_connection_allowed": False,
            "pipeline_stage_addition_allowed": False,
            "provider_execution_allowed": False,
            "scoring_mutation_allowed": False,
            "ranking_mutation_allowed": False,
            "queue_mutation_allowed": False,
            "resume_mutation_allowed": False,
            "application_execution_allowed": False,
            "application_submission_allowed": False,
        },
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            three_core_agent_shadow_pipeline_hook_safety_metadata()
        ),
    }
