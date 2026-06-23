"""Default-off read-only acceptance summary for three-core shadow runtime."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


READBACK_VERSION = "phase-17g-three-core-shadow-runtime-readback-v1"
STATUS_DISABLED = (
    "three_core_shadow_runtime_readback_skipped_default_off"
)
STATUS_COMPLETED = "three_core_shadow_runtime_readback_completed"
STATUS_INCOMPLETE = "three_core_shadow_runtime_readback_incomplete"
STATUS_FAILED = "three_core_shadow_runtime_readback_failed_closed"
COMPLETED_HOOK_STATUS = (
    "three_core_shadow_pipeline_hook_completed_shadow_only"
)
FAILED_HOOK_STATUS = "three_core_shadow_pipeline_hook_failed_closed"
ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _ordered_result_names(
    three_core_payload: dict[str, Any],
) -> list[str]:
    results = three_core_payload.get("ordered_shadow_results")
    if not isinstance(results, list):
        return []
    return [
        str(result.get("agent_name") or "").strip()
        for result in results
        if isinstance(result, dict)
    ]


def three_core_shadow_runtime_readback_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "runtime_readback_only": True,
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


def build_three_core_agent_shadow_runtime_readback(
    *,
    enabled: bool = False,
    shadow_sidecar_hook_payload: dict[str, Any] | None = None,
    readback_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize a caller-supplied shadow payload without executing it."""

    source = _plain_dict(shadow_sidecar_hook_payload)
    context = _plain_dict(readback_context)
    three_core = _plain_dict(
        source.get("three_core_shadow_pipeline_hook_payload")
    )
    connection_plan = _plain_dict(
        three_core.get("connection_plan_summary")
    )
    hook_contract = _plain_dict(
        three_core.get("three_core_shadow_pipeline_hook")
    )
    checks = _plain_dict(hook_contract.get("hook_checks"))
    forbidden_paths = _plain_dict(
        three_core.get("forbidden_mutation_and_application_paths")
    )
    ordered_names = _ordered_result_names(three_core)
    callable_checks = {
        "relevance_prefilter_callable_supplied": (
            checks.get("relevance_prefilter_callable_supplied") is True
        ),
        "jd_intelligence_callable_supplied": (
            checks.get("jd_intelligence_callable_supplied") is True
        ),
        "final_application_scoring_callable_supplied": (
            checks.get("final_application_scoring_callable_supplied")
            is True
        ),
    }
    acceptance_checks = {
        "shadow_sidecar_hook_payload_supplied": bool(source),
        "three_core_shadow_pipeline_hook_payload_supplied": bool(
            three_core
        ),
        "three_core_hook_completed_shadow_only": (
            three_core.get("hook_status") == COMPLETED_HOOK_STATUS
        ),
        "shadow_result_count_is_three": (
            three_core.get("shadow_result_count") == 3
        ),
        "ordered_core_agent_names_match": (
            tuple(ordered_names) == ORDERED_CORE_AGENT_NAMES
        ),
        "connection_plan_ready": (
            connection_plan.get("connection_plan_ready") is True
        ),
        **callable_checks,
        "mutation_not_authorized": (
            three_core.get("mutation_authorized") is False
        ),
        "workflow_connection_not_authorized": (
            three_core.get("workflow_connection_authorized") is False
        ),
        "pipeline_connection_not_authorized": (
            three_core.get("pipeline_connection_authorized") is False
        ),
        "pipeline_stage_not_added": (
            three_core.get("pipeline_stage_added") is False
        ),
        "execution_not_authorized": (
            three_core.get("execution_authorized") is False
        ),
        "submission_not_authorized": (
            three_core.get("submission_authorized") is False
        ),
        "forbidden_mutation_and_application_paths_all_false": (
            bool(forbidden_paths)
            and all(value is False for value in forbidden_paths.values())
        ),
    }
    incomplete_checks = [
        key for key, passed in acceptance_checks.items() if passed is not True
    ]
    completed = not incomplete_checks
    nested_status = str(three_core.get("hook_status") or "").strip()
    failure_summary = _plain_dict(three_core.get("failure"))

    if enabled is not True:
        status = STATUS_DISABLED
        next_safe_step = (
            "enable_three_core_shadow_runtime_readback_only"
        )
    elif nested_status == FAILED_HOOK_STATUS:
        status = STATUS_FAILED
        next_safe_step = (
            "fix_three_core_shadow_runtime_failure_before_retry"
        )
    elif completed:
        status = STATUS_COMPLETED
        next_safe_step = (
            "review_three_core_shadow_runtime_readback_"
            "before_operator_canary"
        )
    else:
        status = STATUS_INCOMPLETE
        next_safe_step = (
            "complete_three_core_shadow_runtime_readback_inputs"
        )

    return {
        "readback_version": READBACK_VERSION,
        "three_core_shadow_runtime_readback_enabled": enabled is True,
        "readback_status": status,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "runtime_readback_only": True,
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
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "runtime_readback_summary": {
            "source_hook_status": str(
                source.get("hook_status") or ""
            ).strip(),
            "three_core_hook_status": nested_status,
            "ordered_agent_names_found": ordered_names,
            "shadow_result_count": (
                three_core.get("shadow_result_count")
            ),
            "connection_plan_ready": (
                connection_plan.get("connection_plan_ready") is True
            ),
            "callable_checks": callable_checks,
            "completion": completed,
            "failure_summary": failure_summary,
            "incomplete_checks": incomplete_checks,
            "acceptance_checks": acceptance_checks,
        },
        "source_payload_summary": {
            "source_payload_supplied": bool(source),
            "source_hook_status": str(
                source.get("hook_status") or ""
            ).strip(),
            "three_core_payload_supplied": bool(three_core),
            "source_shadow_sidecar_hook_payload": source,
        },
        "readback_context": context,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            three_core_shadow_runtime_readback_safety_metadata()
        ),
    }
