from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List
import asyncio
import json
import os
import time
from uuid import uuid4
from pathlib import Path

from src.pipeline.runtime_status import complete_stage, start_stage, update_counts
from src.utils.log_sections import section
from src.utils.logging import get_logger

logger = get_logger("collector")

THREE_CORE_SHADOW_PIPELINE_HOOK_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_THREE_CORE_SHADOW_PIPELINE_HOOK_ENABLED"
)
ADVISORY_CHAIN_DIAGNOSTICS_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_ADVISORY_CHAIN_DIAGNOSTICS_ENABLED"
)
ADVISORY_CHAIN_TRACE_PERSISTENCE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_ADVISORY_CHAIN_TRACE_PERSISTENCE_ENABLED"
)
JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_ENABLED"
)
JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_SAMPLE_LIMIT_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_SAMPLE_LIMIT"
)
JD_INTELLIGENCE_EXISTING_OUTPUT_TRACE_PERSISTENCE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_EXISTING_OUTPUT_"
    "TRACE_PERSISTENCE_ENABLED"
)
JD_INTELLIGENCE_CONTROLLED_LLM_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_CONTROLLED_LLM_ENABLED"
)
JD_INTELLIGENCE_CONTROLLED_LLM_VERSION = (
    "collector-jd-intelligence-controlled-llm-runtime-v1"
)
EVIDENCE_CHAIN_COLLECTOR_DIAGNOSTICS_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_DIAGNOSTICS_ENABLED"
)
EVIDENCE_CHAIN_COLLECTOR_DIAGNOSTICS_VERSION = (
    "agent-evidence-chain-collector-diagnostics-v1"
)
EVIDENCE_CHAIN_COLLECTOR_EXECUTION_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_EXECUTION_ENABLED"
)
EVIDENCE_CHAIN_COLLECTOR_EXECUTION_SAMPLE_LIMIT_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_EXECUTION_SAMPLE_LIMIT"
)
EVIDENCE_CHAIN_COLLECTOR_EXECUTION_VERSION = (
    "collector-controlled-evidence-chain-execution-v1"
)
EVIDENCE_CHAIN_TRACE_PERSISTENCE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_TRACE_PERSISTENCE_ENABLED"
)
EVIDENCE_CHAIN_TRACE_PERSISTENCE_VERSION = (
    "collector-controlled-evidence-chain-trace-persistence-v1"
)
EVIDENCE_CHAIN_COLLECTOR_EXECUTION_DEFAULT_SAMPLE_LIMIT = 10
EVIDENCE_CHAIN_REQUIRED_ARTIFACT_KEYS = [
    "resume_match_jd_evidence",
    "critic_resume_match_jd_evidence",
    "job_prioritization_critic_evidence",
    "tailoring_decision_priority_evidence",
    "operator_review_tailoring_evidence",
]
EVIDENCE_CHAIN_COLLECTOR_DIAGNOSTICS_FALSE_FLAGS = (
    "provider_call_performed",
    "live_llm_call_performed",
    "evidence_chain_bundle_execution_performed",
    "evidence_chain_trace_payload_execution_performed",
    "evidence_chain_trace_persistence_performed",
    "jd_extraction_performed",
    "jd_wrapper_execution_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
    "tailoring_decision_execution_performed",
    "operator_review_execution_performed",
    "trace_store_write_performed",
    "database_write_performed",
    "collector_output_changed",
    "production_output_changed",
    "evaluable_jobs_changed",
    "scored_jobs_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "cache_behavior_changed",
    "retry_behavior_changed",
    "dedupe_behavior_changed",
    "source_health_behavior_changed",
    "ats_health_behavior_changed",
    "review_queue_mutation_performed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "workflow_runner_executed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
)
EVIDENCE_CHAIN_COLLECTOR_EXECUTION_FALSE_FLAGS = (
    "provider_call_performed",
    "live_llm_call_performed",
    "trace_persistence_performed",
    "trace_store_write_performed",
    "database_write_performed",
    "collector_output_changed",
    "production_output_changed",
    "evaluable_jobs_changed",
    "scored_jobs_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "cache_behavior_changed",
    "retry_behavior_changed",
    "dedupe_behavior_changed",
    "source_health_behavior_changed",
    "ats_health_behavior_changed",
    "review_queue_mutation_performed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "workflow_runner_executed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
    "external_action_automation_performed",
)
EVIDENCE_CHAIN_TRACE_PERSISTENCE_FALSE_FLAGS = (
    "provider_call_performed",
    "live_llm_call_performed",
    "collector_output_changed",
    "production_output_changed",
    "evaluable_jobs_changed",
    "scored_jobs_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "cache_behavior_changed",
    "retry_behavior_changed",
    "dedupe_behavior_changed",
    "source_health_behavior_changed",
    "ats_health_behavior_changed",
    "review_queue_mutation_performed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "workflow_runner_executed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
    "external_action_automation_performed",
)
JD_INTELLIGENCE_CONTROLLED_LLM_FALSE_FLAGS = (
    "database_write_performed",
    "trace_persistence_performed",
    "collector_output_changed",
    "production_output_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "queue_mutation_performed",
    "review_queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
    "external_action_automation_performed",
)


def _is_user_pipeline_mode() -> bool:
    return str(os.environ.get("JOB_STACK_USER_PIPELINE_MODE", "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }


def _selected_role_families_from_env() -> List[str]:
    return _json_list_from_env("JOB_STACK_SELECTED_ROLE_FAMILIES")


def _json_list_from_env(env_name: str) -> List[str]:
    raw = str(os.environ.get(env_name, "") or "").strip()
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Ignoring invalid %s JSON.", env_name)
        return []

    if not isinstance(parsed, list):
        logger.warning("Ignoring non-list %s value.", env_name)
        return []

    values: List[str] = []
    for value in parsed:
        text = str(value or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _pipeline_preferences_from_env() -> Dict[str, List[str]]:
    return {
        "selected_role_families": _json_list_from_env("JOB_STACK_SELECTED_ROLE_FAMILIES"),
        "target_seniority": _json_list_from_env("JOB_STACK_TARGET_SENIORITY"),
        "preferred_locations": _json_list_from_env("JOB_STACK_PREFERRED_LOCATIONS"),
        "preferred_skills": _json_list_from_env("JOB_STACK_PREFERRED_SKILLS"),
        "excluded_keywords": _json_list_from_env("JOB_STACK_EXCLUDED_KEYWORDS"),
    }


def _truthy_env_value(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_trace_text(value: Any) -> str:
    return str(value or "").strip()


def _agent_trace_context_from_env(
    *,
    env: Dict[str, str] | None = None,
    context_prefix: str,
) -> Dict[str, str]:
    env_map = env if env is not None else os.environ
    pipeline_run_id = (
        _clean_trace_text(env_map.get("JOB_APP_PIPELINE_RUN_ID"))
        or _clean_trace_text(env_map.get("JOB_STACK_USER_PIPELINE_RUN_ID"))
    )
    owner_user_id = _clean_trace_text(env_map.get("JOB_STACK_OWNER_USER_ID"))
    context_id = _clean_trace_text(env_map.get("APPLYLENS_AGENT_CONTEXT_ID"))
    if not context_id and pipeline_run_id:
        context_id = f"{context_prefix}:{pipeline_run_id}"
    return {
        "pipeline_run_id": pipeline_run_id,
        "owner_user_id": owner_user_id,
        "context_id": context_id,
    }


def _record_relevance_prefilter_agent_trace(
    *,
    prefilter_summary: Dict[str, Any],
    env: Dict[str, str] | None = None,
    trace_module: Any | None = None,
) -> Dict[str, Any]:
    env_map = env if env is not None else os.environ
    if not _truthy_env_value(env_map.get("APPLYLENS_AGENT_TRACE_ENABLED")):
        return {"attempted": False, "reason": "trace_disabled"}

    context = _agent_trace_context_from_env(
        env=env_map,
        context_prefix="relevance_prefilter",
    )
    if not context["owner_user_id"] or not context["pipeline_run_id"]:
        return {"attempted": False, "reason": "missing_trace_context", **context}

    try:
        from src.agents import relevance_prefilter
        from src.agents import trace as default_trace_module

        active_trace_module = trace_module or default_trace_module
        started_at = _utc_now_iso()
        payload = relevance_prefilter.describe_relevance_prefilter_result(
            prefilter_summary
        )
        run_summary = {
            "agent_name": payload["agent_name"],
            "agent_version": payload["agent_version"],
            "pipeline_run_id": context["pipeline_run_id"],
            "status": payload["status"],
            "input_count": payload["input_count"],
            "kept_count": payload["kept_count"],
            "dropped_count": payload["dropped_count"],
            "reason_counts": payload["reason_counts"],
            "live_trace_bridge": True,
            "source_stage": _clean_trace_text(
                prefilter_summary.get("source_stage") or "embedding_prefilter"
            ),
            "preserves_stage_output": True,
        }
        run_payload = active_trace_module.create_agent_run(
            record={
                "owner_user_id": context["owner_user_id"],
                "pipeline_run_id": context["pipeline_run_id"],
                "context_id": context["context_id"],
                "status": "running",
                "started_at": started_at,
                "summary_json": run_summary,
            }
        )
        agent_run_id = _clean_trace_text((run_payload.get("run") or {}).get("agent_run_id"))
        if not agent_run_id:
            raise RuntimeError("Agent trace run did not return agent_run_id.")

        step_payload = active_trace_module.record_agent_step(
            record={
                "agent_run_id": agent_run_id,
                "owner_user_id": context["owner_user_id"],
                "pipeline_run_id": context["pipeline_run_id"],
                "context_id": context["context_id"],
                "agent_name": relevance_prefilter.AGENT_NAME,
                "agent_version": payload["agent_version"],
                "input_json": {
                    "input_count": payload["input_count"],
                    "role_family": payload["role_family"],
                    "seniority": payload["seniority"],
                    "location_policy": payload["location_policy"],
                    "source_stage": run_summary["source_stage"],
                },
                "status": "running",
                "started_at": started_at,
                "model_provider": "deterministic",
                "model_name": "relevance_prefilter_trace_wrapper",
            }
        )
        agent_step_id = _clean_trace_text(
            (step_payload.get("step") or {}).get("agent_step_id")
        )
        if not agent_step_id:
            raise RuntimeError("Agent trace step did not return agent_step_id.")

        completed_at = _utc_now_iso()
        active_trace_module.complete_agent_step(
            agent_step_id=agent_step_id,
            owner_user_id=context["owner_user_id"],
            output_json=payload["output_json"],
            validation_json=payload["validation_json"],
            completed_at=completed_at,
        )
        active_trace_module.complete_agent_run(
            agent_run_id=agent_run_id,
            owner_user_id=context["owner_user_id"],
            summary_json=run_summary,
            completed_at=completed_at,
        )
        return {
            "attempted": True,
            "recorded": True,
            "agent_run_id": agent_run_id,
            "agent_step_id": agent_step_id,
            "summary": run_summary,
            "validation": payload["validation_json"],
        }
    except Exception as exc:
        if _truthy_env_value(env_map.get("APPLYLENS_AGENT_TRACE_STRICT")):
            raise
        return {"attempted": True, "recorded": False, "warning": str(exc)}


def _record_source_health_agent_trace(
    *,
    source_health_rows: List[Dict[str, Any]],
    artifact_path: Path,
) -> Dict[str, Any]:
    try:
        from src.agents.source_health_agent import record_source_health_agent_trace

        return record_source_health_agent_trace(
            rows=source_health_rows,
            artifact_path=str(artifact_path),
            artifact_name=artifact_path.name,
        )
    except Exception as exc:
        if _truthy_env_value(os.environ.get("APPLYLENS_AGENT_TRACE_STRICT")):
            raise
        return {"attempted": True, "recorded": False, "warning": str(exc)}


def _agent_trace_status_counts(trace_result: Dict[str, Any]) -> Dict[str, int]:
    if not trace_result.get("attempted"):
        return {"agent_trace_enabled": 0}
    if trace_result.get("recorded"):
        return {
            "agent_trace_enabled": 1,
            "agent_trace_steps_recorded": 1,
            "agent_trace_write_failed": 0,
        }
    return {
        "agent_trace_enabled": 1,
        "agent_trace_steps_recorded": 0,
        "agent_trace_write_failed": 1,
    }


def _shadow_sidecar_pipeline_config_from_env() -> Dict[str, Any]:
    flag_names = (
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH",
        "APPLYLENS_AGENTIC_PIPELINE_AGENT_RECOMMENDATION_OVERLAY_AUTO_GENERATE_ENABLED",
        THREE_CORE_SHADOW_PIPELINE_HOOK_FLAG,
    )
    return {flag_name: os.environ.get(flag_name, "") for flag_name in flag_names}


def _maybe_run_shadow_sidecar_after_application_priority(
    scored_jobs: List[Dict[str, Any]],
    *,
    vector_evidence_hook_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any] | None:
    sidecar_config = _shadow_sidecar_pipeline_config_from_env()
    if not _truthy_env_value(
        sidecar_config["APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"]
    ):
        return None

    try:
        from src.agents.shadow_sidecar_hook import run_shadow_sidecar_pipeline_hook

        run_id = str(
            os.environ.get("JOB_STACK_PIPELINE_RUN_ID", "") or "collector"
        )
        batch_id = str(
            os.environ.get("JOB_STACK_PIPELINE_BATCH_ID", "")
            or "application_priority"
        )
        job_id = "application_priority_scored_jobs"
        stage_name = "post_final_scoring"
        job_payload = deepcopy(scored_jobs[0]) if scored_jobs else {}
        three_core_hook_enabled = _truthy_env_value(
            sidecar_config[THREE_CORE_SHADOW_PIPELINE_HOOK_FLAG]
        )
        three_core_job_context = (
            {
                "run_id": run_id,
                "batch_id": batch_id,
                "job_id": job_id,
                "stage_name": stage_name,
                "job_payload": deepcopy(job_payload),
            }
            if three_core_hook_enabled
            else None
        )
        three_core_connection_plan = None
        three_core_callable_kwargs: Dict[str, Any] = {}
        if three_core_hook_enabled:
            from src.agents.three_core_agent_shadow_pipeline_connection_plan import (
                build_three_core_agent_shadow_pipeline_connection_plan,
            )

            ordered_core_agent_names = [
                "relevance_prefilter",
                "jd_intelligence",
                "final_application_scoring",
            ]
            three_core_connection_plan = (
                build_three_core_agent_shadow_pipeline_connection_plan(
                    enabled=True,
                    dry_run_readback={
                        "readback_status": (
                            "three_core_shadow_dry_run_readback_ready"
                        ),
                        "dry_run_readback_only": True,
                        "workflow_connection_authorized": False,
                        "dry_run_execution_authorized": False,
                        "ordered_core_agent_names": deepcopy(
                            ordered_core_agent_names
                        ),
                        "mutation_authorized": False,
                    },
                    pipeline_entrypoint_descriptor={
                        "entrypoint_name": (
                            "collector_application_priority_shadow_hook"
                        ),
                        "stage_name": stage_name,
                        "shadow_only": True,
                    },
                    prefilter_connection_descriptor={
                        "agent_name": "relevance_prefilter",
                        "source_stage": (
                            "application_priority_scored_jobs"
                        ),
                        "target_stage": "relevance_prefilter_shadow",
                        "shadow_only": True,
                    },
                    jd_intelligence_connection_descriptor={
                        "agent_name": "jd_intelligence",
                        "source_stage": "relevance_prefilter_shadow",
                        "target_stage": "jd_intelligence_shadow",
                        "shadow_only": True,
                    },
                    final_scoring_connection_descriptor={
                        "agent_name": "final_application_scoring",
                        "source_stage": "jd_intelligence_shadow",
                        "target_stage": (
                            "final_application_scoring_shadow"
                        ),
                        "shadow_only": True,
                    },
                    connection_plan_context={
                        "run_id": run_id,
                        "batch_id": batch_id,
                        "job_id": job_id,
                        "stage_name": stage_name,
                        "collector_hook_point": (
                            "application_priority_scored_jobs"
                        ),
                    },
                )
            )
            from src.agents.three_core_agent_shadow_callable_adapters import (
                build_three_core_agent_shadow_callable_adapters,
            )

            callable_adapters = (
                build_three_core_agent_shadow_callable_adapters(
                    enabled=True,
                    adapter_context={
                        "run_id": run_id,
                        "batch_id": batch_id,
                        "job_id": job_id,
                        "stage_name": stage_name,
                        "collector_hook_point": (
                            "application_priority_scored_jobs"
                        ),
                    },
                )
            )
            callable_map = callable_adapters.get("callable_map")
            if (
                callable_adapters.get("adapter_status")
                == "three_core_shadow_callable_adapters_ready_shadow_only"
                and isinstance(callable_map, dict)
                and all(
                    callable(callable_map.get(agent_name))
                    for agent_name in ordered_core_agent_names
                )
            ):
                three_core_callable_kwargs = {
                    "three_core_relevance_prefilter_callable": (
                        callable_map["relevance_prefilter"]
                    ),
                    "three_core_jd_intelligence_callable": (
                        callable_map["jd_intelligence"]
                    ),
                    "three_core_final_application_scoring_callable": (
                        callable_map["final_application_scoring"]
                    ),
                }
        payload = run_shadow_sidecar_pipeline_hook(
            run_id=run_id,
            batch_id=batch_id,
            job_id=job_id,
            stage_name=stage_name,
            source_deterministic_stage="application_priority",
            source_deterministic_status="completed",
            source_deterministic_score=len(scored_jobs),
            source_deterministic_decision=(
                "scored_jobs_available" if scored_jobs else "no_scored_jobs"
            ),
            source_deterministic_reason_codes=["application_priority_completed"],
            sidecar_config=sidecar_config,
            job_payload=job_payload,
            resume_profile_payload={},
            existing_trace_context={
                "shadow_sidecar_call_site": "collector.application_priority",
                "scored_job_count": len(scored_jobs),
            },
            vector_evidence_hook_payload=vector_evidence_hook_payload,
            three_core_shadow_pipeline_hook_enabled=(
                three_core_hook_enabled
            ),
            three_core_connection_plan=three_core_connection_plan,
            three_core_job_context=three_core_job_context,
            called_by_pipeline=True,
            **three_core_callable_kwargs,
        )
        logger.info(
            "Shadow sidecar hook evaluated after application_priority: %s",
            payload.get("hook_status", "unknown"),
        )
        return payload
    except Exception as exc:
        logger.warning(
            "Shadow sidecar hook failed non-blocking after application_priority: %s",
            exc,
        )
        return None


def _maybe_collect_vector_evidence_after_application_priority(
    scored_jobs: List[Dict[str, Any]],
    *,
    enabled: bool | None = None,
    vector_evidence_service: Any = None,
) -> Dict[str, Any] | None:
    hook_enabled = (
        _truthy_env_value(
            os.environ.get("APPLYLENS_PIPELINE_VECTOR_EVIDENCE_HOOK_ENABLED")
        )
        if enabled is None
        else enabled is True
    )
    if not hook_enabled:
        return None

    try:
        from src.agents.vector_evidence_pipeline_hook import (
            run_vector_evidence_pipeline_hook,
        )

        source_job = dict(scored_jobs[0]) if scored_jobs else {}
        job_id = str(
            source_job.get("id")
            or source_job.get("job_id")
            or "application_priority_scored_jobs"
        )
        query_text = " ".join(
            value
            for value in (
                str(source_job.get("title", "") or "").strip(),
                str(source_job.get("company", "") or "").strip(),
            )
            if value
        )
        payload = run_vector_evidence_pipeline_hook(
            enabled=True,
            run_id=str(
                os.environ.get("JOB_STACK_PIPELINE_RUN_ID", "") or "collector"
            ),
            job_id=job_id,
            stage_name="post_final_scoring",
            query_text=query_text,
            job_payload=source_job,
            vector_evidence_service=vector_evidence_service,
        )
        logger.info(
            "Vector evidence advisory hook evaluated after application_priority: %s",
            payload.get("status", "unknown"),
        )
        return payload
    except Exception as exc:
        logger.warning(
            "Vector evidence advisory hook failed non-blocking after "
            "application_priority: %s",
            exc,
        )
        return None


def _advisory_chain_diagnostics_input_summary(
    scored_jobs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    first_job = dict(scored_jobs[0]) if scored_jobs else {}
    return {
        "stage_name": "post_application_priority",
        "source_stage": "application_priority",
        "scored_job_count": len(scored_jobs),
        "first_job": {
            "id": _clean_trace_text(first_job.get("id") or first_job.get("job_id")),
            "title": _clean_trace_text(first_job.get("title")),
            "company": _clean_trace_text(first_job.get("company")),
        },
    }


def _maybe_invoke_advisory_chain_diagnostics_after_application_priority(
    scored_jobs: List[Dict[str, Any]],
    *,
    enabled: bool | None = None,
    env: Dict[str, str] | None = None,
    advisory_chain_helper: Any = None,
    persistence_helper: Any = None,
    persistence_cursor: Any | None = None,
    persistence_execute_callback: Any | None = None,
) -> Dict[str, Any] | None:
    env_map = env if env is not None else os.environ
    hook_enabled = (
        _truthy_env_value(env_map.get(ADVISORY_CHAIN_DIAGNOSTICS_FLAG))
        if enabled is None
        else enabled is True
    )
    if not hook_enabled:
        return None

    context = _agent_trace_context_from_env(
        env=env_map,
        context_prefix="advisory_chain",
    )
    if not context["owner_user_id"] or not context["pipeline_run_id"]:
        return {
            "attempted": False,
            "reason": "missing_trace_context",
            **context,
        }

    try:
        if advisory_chain_helper is None:
            from src.agents.orchestrator_adapter_harness import (
                invoke_read_only_advisory_chain_from_pipeline_boundary,
            )

            advisory_chain_helper = (
                invoke_read_only_advisory_chain_from_pipeline_boundary
            )

        payload = advisory_chain_helper(
            pipeline_run_id=context["pipeline_run_id"],
            owner_user_id=context["owner_user_id"],
            context_id=context["context_id"],
            input_summary=_advisory_chain_diagnostics_input_summary(scored_jobs),
            env={str(key): str(value) for key, value in dict(env_map).items()},
        )
        persistence_result = {
            "attempted": False,
            "recorded": False,
            "reason": "trace_persistence_disabled",
            "trace_persistence_enabled": False,
            "trace_store_write_enabled": False,
            "did_call_trace_execution_helper": False,
            "did_write_database": False,
            **context,
        }
        if _truthy_env_value(env_map.get(ADVISORY_CHAIN_TRACE_PERSISTENCE_FLAG)):
            if not _truthy_env_value(env_map.get("APPLYLENS_AGENT_TRACE_ENABLED")):
                persistence_result["reason"] = "trace_disabled"
            elif (persistence_cursor is None) == (persistence_execute_callback is None):
                persistence_result["reason"] = "write_executor_missing"
            else:
                try:
                    if persistence_helper is None:
                        from src.agents.orchestrator_adapter_harness import (
                            persist_read_only_advisory_chain_trace,
                        )

                        persistence_helper = persist_read_only_advisory_chain_trace
                    persistence_result = persistence_helper(
                        advisory_result=payload,
                        owner_user_id=context["owner_user_id"],
                        pipeline_run_id=context["pipeline_run_id"],
                        context_id=context["context_id"],
                        env={str(key): str(value) for key, value in dict(env_map).items()},
                        cursor=persistence_cursor,
                        execute_callback=persistence_execute_callback,
                    )
                except Exception as exc:
                    if _truthy_env_value(env_map.get("APPLYLENS_AGENT_TRACE_STRICT")):
                        raise
                    persistence_result = {
                        **persistence_result,
                        "attempted": True,
                        "reason": "trace_persistence_failed",
                        "warning": str(exc),
                    }
        payload["advisory_chain_trace_persistence"] = persistence_result
        logger.info(
            "Advisory chain diagnostics evaluated after application_priority: %s",
            payload.get("validation", {}).get("validation_status", "unknown")
            if isinstance(payload, dict)
            else "unknown",
        )
        return payload
    except Exception as exc:
        if _truthy_env_value(env_map.get("APPLYLENS_AGENT_TRACE_STRICT")):
            raise
        logger.warning(
            "Advisory chain diagnostics failed non-blocking after "
            "application_priority: %s",
            exc,
        )
        return {
            "attempted": True,
            "recorded": False,
            "reason": "advisory_chain_diagnostics_failed",
            "warning": str(exc),
            **context,
        }


def _maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
    intelligent_jobs: List[Dict[str, Any]],
    *,
    enabled: bool | None = None,
    env: Dict[str, str] | None = None,
    payload_builder: Any = None,
    persistence_helper: Any = None,
    persistence_cursor: Any | None = None,
    persistence_execute_callback: Any | None = None,
) -> Dict[str, Any] | None:
    env_map = env if env is not None else os.environ
    diagnostics_enabled = (
        _truthy_env_value(env_map.get(JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_FLAG))
        if enabled is None
        else enabled is True
    )
    if not diagnostics_enabled:
        return None

    sample_limit = env_map.get(
        JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_SAMPLE_LIMIT_FLAG,
        "",
    )
    try:
        if payload_builder is None:
            jd_intelligence_module = __import__(
                "src.agents." "jd_intelligence",
                fromlist=["build_existing_job_intelligence_trace_payload"],
            )
            payload_builder = getattr(
                jd_intelligence_module,
                "build_existing_job_intelligence_trace_payload",
            )

        payload = payload_builder(
            intelligent_jobs,
            sample_limit=sample_limit,
        )
        if isinstance(payload, dict):
            payload.setdefault("attempted", True)
            payload.setdefault("enabled", True)
            payload.setdefault("trace_persistence_requested", False)
            payload.setdefault("trace_persistence_performed", False)
            payload.setdefault("production_output_changed", False)
            persistence_result = {
                "attempted": False,
                "recorded": False,
                "reason": "trace_persistence_disabled",
                "trace_persistence_requested": False,
                "trace_persistence_performed": False,
                "trace_store_write_enabled": False,
                "did_call_trace_execution_helper": False,
                "did_write_database": False,
            }
            if _truthy_env_value(
                env_map.get(JD_INTELLIGENCE_EXISTING_OUTPUT_TRACE_PERSISTENCE_FLAG)
            ):
                context = _agent_trace_context_from_env(
                    env=env_map,
                    context_prefix="jd_intelligence_existing_output",
                )
                persistence_result.update(
                    {
                        "trace_persistence_requested": True,
                        **context,
                    }
                )
                payload["trace_persistence_requested"] = True
                if not _truthy_env_value(env_map.get("APPLYLENS_AGENT_TRACE_ENABLED")):
                    persistence_result["reason"] = "trace_disabled"
                elif (
                    not context["owner_user_id"]
                    or not context["pipeline_run_id"]
                    or not context["context_id"]
                ):
                    persistence_result["reason"] = "missing_trace_context"
                elif (persistence_cursor is None) == (persistence_execute_callback is None):
                    persistence_result["reason"] = "write_executor_missing"
                else:
                    try:
                        if persistence_helper is None:
                            jd_intelligence_module = __import__(
                                "src.agents." "jd_intelligence",
                                fromlist=["persist_existing_job_intelligence_trace_payload"],
                            )
                            persistence_helper = getattr(
                                jd_intelligence_module,
                                "persist_existing_job_intelligence_trace_payload",
                            )
                        persistence_result = persistence_helper(
                            diagnostics_payload=payload,
                            owner_user_id=context["owner_user_id"],
                            pipeline_run_id=context["pipeline_run_id"],
                            context_id=context["context_id"],
                            cursor=persistence_cursor,
                            execute_callback=persistence_execute_callback,
                            strict=_truthy_env_value(
                                env_map.get("APPLYLENS_AGENT_TRACE_STRICT")
                            ),
                            diagnostics_gate_enabled=True,
                            persistence_gate_enabled=True,
                        )
                    except Exception as exc:
                        if _truthy_env_value(env_map.get("APPLYLENS_AGENT_TRACE_STRICT")):
                            raise
                        persistence_result = {
                            **persistence_result,
                            "attempted": True,
                            "recorded": False,
                            "reason": "trace_persistence_failed",
                            "warning": str(exc),
                        }
                payload["trace_persistence_performed"] = bool(
                    persistence_result.get("trace_persistence_performed")
                )
            payload["jd_intelligence_existing_output_trace_persistence"] = (
                persistence_result
            )
            logger.info(
                "JD intelligence existing-output diagnostics evaluated after "
                "intelligence: seen=%s sampled=%s invalid=%s",
                payload.get("job_count_seen", 0),
                payload.get("job_count_sampled", 0),
                (payload.get("validation_summary") or {}).get(
                    "invalid_wrapper_outputs",
                    0,
                ),
            )
        return payload
    except Exception as exc:
        logger.warning(
            "JD intelligence existing-output diagnostics failed non-blocking "
            "after intelligence: %s",
            exc,
        )
        return {
            "attempted": True,
            "enabled": True,
            "reason": "jd_intelligence_existing_output_diagnostics_failed",
            "warning": str(exc),
            "trace_persistence_requested": False,
            "trace_persistence_performed": False,
            "production_output_changed": False,
            "auto_" "apply_performed": False,
            "auto_" "submit_performed": False,
            "ats_submission_performed": False,
            "apply_click_performed": False,
            "recruiter_message_sent": False,
            "mark_applied_performed": False,
            "provider_call_performed": False,
            "duplicate_llm_call_performed": False,
            "database_write_performed": False,
            "scoring_changed": False,
            "ranking_changed": False,
            "filtering_changed": False,
            "queue_changed": False,
            "scheduler_changed": False,
            "tailoring_changed": False,
            "source_resume_changed": False,
            "workflow_" "runner_live_execution_performed": False,
        }


def _jd_controlled_llm_safety_metadata() -> Dict[str, bool]:
    return {
        "read_only": True,
        "diagnostic_only": True,
        "sidecar_only": True,
        **{flag: False for flag in JD_INTELLIGENCE_CONTROLLED_LLM_FALSE_FLAGS},
    }


def _job_intelligence_skill_signals(job: Dict[str, Any]) -> Dict[str, Any]:
    intelligence = job.get("intelligence") if isinstance(job, dict) else {}
    intelligence_map = dict(intelligence or {}) if isinstance(intelligence, dict) else {}
    skills = intelligence_map.get("skills")
    skills_map = dict(skills or {}) if isinstance(skills, dict) else {}
    required = list(skills_map.get("required") or [])
    preferred = list(skills_map.get("preferred") or [])
    all_skills = list(skills_map.get("all") or [])
    if not all_skills:
        all_skills = required + [skill for skill in preferred if skill not in required]
    return {
        "intelligence": deepcopy(intelligence_map),
        "required_skills": required,
        "preferred_skills": preferred,
        "all_skills": all_skills,
        "extraction_ready": isinstance(skills, dict),
        "extraction_source": "existing_build_job_intelligence",
    }


def _jd_controlled_llm_metadata(job: Dict[str, Any]) -> Dict[str, Any]:
    metadata = job.get("_jd_intelligence_llm_metadata")
    if not isinstance(metadata, dict):
        metadata = job.get("jd_intelligence_llm_metadata")
    return deepcopy(dict(metadata or {})) if isinstance(metadata, dict) else {}


def _build_intelligent_jobs_with_controlled_jd_agent_ownership(
    detailed_jobs: List[Dict[str, Any]],
    *,
    build_job_intelligence_func: Any,
    artifact_builder: Any = None,
    enabled: bool | None = None,
    env: Dict[str, str] | None = None,
    strict: bool = True,
) -> Dict[str, Any]:
    env_map = env if env is not None else os.environ
    gate_enabled = (
        _truthy_env_value(env_map.get(JD_INTELLIGENCE_CONTROLLED_LLM_FLAG))
        if enabled is None
        else enabled is True
    )
    if not gate_enabled:
        return {
            "enabled": False,
            "intelligent_jobs": [
                build_job_intelligence_func(job) for job in detailed_jobs
            ],
            "jd_intelligence_controlled_llm_runtime_summary": None,
        }

    if artifact_builder is None:
        from src.agents.jd_intelligence import (
            build_jd_intelligence_controlled_llm_artifact,
        )

        artifact_builder = build_jd_intelligence_controlled_llm_artifact

    intelligent_jobs: List[Dict[str, Any]] = []
    artifacts: List[Dict[str, Any]] = []
    extraction_helper_called_count = 0
    error_count = 0

    for raw_job in list(detailed_jobs or []):
        source_job = deepcopy(dict(raw_job or {}))
        holder: Dict[str, Any] = {"called": False, "job": None}

        def extraction_helper(request_packet: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal extraction_helper_called_count
            extraction_helper_called_count += 1
            holder["called"] = True
            adapter_job = deepcopy(dict(request_packet.get("job") or source_job))
            intelligent_job = build_job_intelligence_func(adapter_job)
            if not isinstance(intelligent_job, dict):
                intelligent_job = adapter_job
            holder["job"] = deepcopy(intelligent_job)
            return {
                **_job_intelligence_skill_signals(intelligent_job),
                **_jd_controlled_llm_metadata(intelligent_job),
            }

        try:
            artifact = artifact_builder(
                source_job,
                enabled=True,
                extraction_helper=extraction_helper,
                env=env_map,
                strict=strict,
            )
        except Exception:
            error_count += 1
            if strict:
                raise
            intelligent_jobs.append(source_job)
            continue

        artifact_map = dict(artifact or {}) if isinstance(artifact, dict) else {}
        artifacts.append(artifact_map)
        if holder["called"] and isinstance(holder.get("job"), dict):
            intelligent_jobs.append(deepcopy(holder["job"]))
        else:
            intelligent_jobs.append(source_job)

    safety_metadata = _jd_controlled_llm_safety_metadata()
    summary = {
        "artifact_type": "jd_intelligence_controlled_llm_runtime_summary",
        "artifact_version": JD_INTELLIGENCE_CONTROLLED_LLM_VERSION,
        "gate_name": JD_INTELLIGENCE_CONTROLLED_LLM_FLAG,
        "enabled": True,
        "default_off": True,
        "collector_stage": "intelligence",
        "total_jobs_seen": len(list(detailed_jobs or [])),
        "artifacts_built": len(artifacts),
        "existing_intelligence_reused_count": sum(
            1 for artifact in artifacts if artifact.get("existing_intelligence_reused")
        ),
        "duplicate_call_avoided_count": sum(
            1
            for artifact in artifacts
            if artifact.get("duplicate_call_avoided")
            or artifact.get("duplicate_llm_call_avoided")
        ),
        "extraction_helper_called_count": extraction_helper_called_count,
        "fallback_used_count": sum(
            1
            for artifact in artifacts
            if artifact.get("fallback_used")
            or artifact.get("deterministic_fallback_used")
        ),
        "provider_call_performed_count": sum(
            1 for artifact in artifacts if artifact.get("provider_call_performed")
        ),
        "token_metrics_available_count": sum(
            1
            for artifact in artifacts
            if (artifact.get("safety_metadata") or {}).get("token_metrics_available")
        ),
        "cost_metrics_available_count": sum(
            1
            for artifact in artifacts
            if (artifact.get("safety_metadata") or {}).get("cost_metrics_available")
        ),
        "latency_metrics_available_count": sum(
            1
            for artifact in artifacts
            if (artifact.get("safety_metadata") or {}).get("latency_metrics_available")
        ),
        "error_count": error_count
        + sum(1 for artifact in artifacts if artifact.get("error_message")),
        "artifacts": artifacts,
        "trace_persistence_requested": False,
        "trace_persistence_performed": False,
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }
    return {
        "enabled": True,
        "intelligent_jobs": intelligent_jobs,
        "jd_intelligence_controlled_llm_runtime_summary": summary,
    }


def _evidence_chain_collector_safety_metadata() -> Dict[str, bool]:
    return {
        flag: False
        for flag in EVIDENCE_CHAIN_COLLECTOR_DIAGNOSTICS_FALSE_FLAGS
    }


def _evidence_chain_execution_safety_metadata(
    *,
    automatic_internal_decisioning_performed: bool = False,
) -> Dict[str, bool]:
    return {
        **{
            flag: False
            for flag in EVIDENCE_CHAIN_COLLECTOR_EXECUTION_FALSE_FLAGS
        },
        "automatic_internal_decisioning_performed": bool(
            automatic_internal_decisioning_performed
        ),
    }


def _evidence_chain_trace_persistence_safety_metadata(
    *,
    persistence_performed: bool = False,
) -> Dict[str, bool]:
    return {
        **{
            flag: False
            for flag in EVIDENCE_CHAIN_TRACE_PERSISTENCE_FALSE_FLAGS
        },
        "database_write_performed": bool(persistence_performed),
        "trace_persistence_performed": bool(persistence_performed),
        "trace_store_write_performed": bool(persistence_performed),
        "observability_mutation_performed": bool(persistence_performed),
    }


def _evidence_chain_execution_sample_limit(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = EVIDENCE_CHAIN_COLLECTOR_EXECUTION_DEFAULT_SAMPLE_LIMIT
    if parsed < 0:
        return 0
    return min(parsed, EVIDENCE_CHAIN_COLLECTOR_EXECUTION_DEFAULT_SAMPLE_LIMIT)


def _valid_evidence_chain_trace_payloads_from_execution_result(
    execution_result: Any,
) -> List[Dict[str, Any]]:
    if not isinstance(execution_result, dict):
        return []

    raw_result = execution_result
    if (
        _clean_trace_text(execution_result.get("artifact_type"))
        == "collector_controlled_evidence_chain_execution_result"
    ):
        raw_result = execution_result.get("execution_result")
    if not isinstance(raw_result, dict):
        return []

    payloads: List[Dict[str, Any]] = []
    for per_job_result in list(raw_result.get("per_job_results") or []):
        if not isinstance(per_job_result, dict):
            continue
        artifacts = per_job_result.get("artifacts")
        if not isinstance(artifacts, dict):
            continue
        payload = artifacts.get("agent_evidence_chain_trace_payload")
        if (
            isinstance(payload, dict)
            and _clean_trace_text(payload.get("artifact_type"))
            == "agent_evidence_chain_trace_payload"
        ):
            payloads.append(deepcopy(payload))
    return payloads


def _mapping_present(value: Any) -> bool:
    return isinstance(value, dict) and bool(value)


def _has_any_key(job: Dict[str, Any], keys: List[str]) -> bool:
    return any(key in job and job.get(key) is not None for key in keys)


def _evidence_chain_missing_artifacts(
    *,
    jobs_inspected_count: int,
    artifact_counts: Dict[str, int],
) -> List[str]:
    if jobs_inspected_count <= 0:
        return list(EVIDENCE_CHAIN_REQUIRED_ARTIFACT_KEYS)
    return [
        key
        for key in EVIDENCE_CHAIN_REQUIRED_ARTIFACT_KEYS
        if int(artifact_counts.get(key, 0) or 0) < jobs_inspected_count
    ]


def _evidence_chain_readiness(
    *,
    jobs_inspected_count: int,
    jd_intelligence_present_count: int,
    artifact_counts: Dict[str, int],
) -> Dict[str, Any]:
    if jobs_inspected_count <= 0:
        return {
            "evidence_chain_readiness": "unavailable",
            "readiness_reason_codes": ["no_jobs_available"],
            "next_recommended_engineering_step": (
                "Run collector with scored jobs before evaluating controlled "
                "evidence-chain execution readiness."
            ),
        }

    missing_artifacts = _evidence_chain_missing_artifacts(
        jobs_inspected_count=jobs_inspected_count,
        artifact_counts=artifact_counts,
    )
    present_artifact_types = [
        key
        for key in EVIDENCE_CHAIN_REQUIRED_ARTIFACT_KEYS
        if int(artifact_counts.get(key, 0) or 0) > 0
    ]

    if not missing_artifacts:
        return {
            "evidence_chain_readiness": "ready_from_existing_artifacts",
            "readiness_reason_codes": ["all_required_evidence_artifacts_present"],
            "next_recommended_engineering_step": (
                "Controlled evidence-chain execution can consume existing "
                "artifacts without creating missing downstream evidence."
            ),
        }

    reason_codes: List[str] = []
    if jd_intelligence_present_count <= 0:
        reason_codes.append("jd_intelligence_missing")

    if present_artifact_types:
        reason_codes.append("partial_evidence_artifacts_present")
        return {
            "evidence_chain_readiness": "degraded",
            "readiness_reason_codes": sorted(set(reason_codes)),
            "next_recommended_engineering_step": (
                "Normalize partial evidence-chain artifacts, then add a "
                "controlled execution path for missing agent evidence."
            ),
        }

    reason_codes.append("downstream_evidence_artifacts_missing")
    return {
        "evidence_chain_readiness": "inputs_missing",
        "readiness_reason_codes": sorted(set(reason_codes)),
        "next_recommended_engineering_step": (
            "Add a controlled evidence-chain execution path to build missing "
            "Phase 89-93 agent evidence artifacts before bundle or trace steps."
        ),
    }


def _maybe_build_evidence_chain_collector_diagnostics(
    scored_jobs: List[Dict[str, Any]],
    *,
    enabled: bool | None = None,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any] | None:
    env_map = env if env is not None else os.environ
    diagnostics_enabled = (
        _truthy_env_value(env_map.get(EVIDENCE_CHAIN_COLLECTOR_DIAGNOSTICS_FLAG))
        if enabled is None
        else enabled is True
    )
    if not diagnostics_enabled:
        return None

    jobs = [
        dict(job)
        for job in list(scored_jobs or [])
        if isinstance(job, dict)
    ]
    jobs_inspected_count = len(jobs)
    artifact_counts = {
        key: sum(1 for job in jobs if _mapping_present(job.get(key)))
        for key in EVIDENCE_CHAIN_REQUIRED_ARTIFACT_KEYS
    }
    jd_intelligence_present_count = sum(
        1 for job in jobs if _mapping_present(job.get("intelligence"))
    )
    ai_evaluation_present_count = sum(
        1
        for job in jobs
        if _has_any_key(
            job,
            [
                "ai_fit",
                "ai_fit_score",
                "ai_relevance",
                "skill_match",
                "seniority_match",
                "learning_opportunity",
            ],
        )
    )
    scoring_present_count = sum(
        1
        for job in jobs
        if _has_any_key(job, ["priority_score", "ai_signal_score"])
    )
    missing_artifacts = _evidence_chain_missing_artifacts(
        jobs_inspected_count=jobs_inspected_count,
        artifact_counts=artifact_counts,
    )
    readiness = _evidence_chain_readiness(
        jobs_inspected_count=jobs_inspected_count,
        jd_intelligence_present_count=jd_intelligence_present_count,
        artifact_counts=artifact_counts,
    )
    safety_metadata = _evidence_chain_collector_safety_metadata()

    return {
        "artifact_type": "agent_evidence_chain_collector_diagnostics",
        "artifact_version": EVIDENCE_CHAIN_COLLECTOR_DIAGNOSTICS_VERSION,
        "gate_name": EVIDENCE_CHAIN_COLLECTOR_DIAGNOSTICS_FLAG,
        "enabled": True,
        "default_off": True,
        "diagnostic_only": True,
        "read_only": True,
        "collector_stage": "post_score_jobs",
        "jobs_inspected_count": jobs_inspected_count,
        "jd_intelligence_present_count": jd_intelligence_present_count,
        "ai_evaluation_present_count": ai_evaluation_present_count,
        "scoring_present_count": scoring_present_count,
        "resume_match_jd_evidence_present_count": artifact_counts[
            "resume_match_jd_evidence"
        ],
        "critic_resume_match_jd_evidence_present_count": artifact_counts[
            "critic_resume_match_jd_evidence"
        ],
        "job_prioritization_critic_evidence_present_count": artifact_counts[
            "job_prioritization_critic_evidence"
        ],
        "tailoring_decision_priority_evidence_present_count": artifact_counts[
            "tailoring_decision_priority_evidence"
        ],
        "operator_review_tailoring_evidence_present_count": artifact_counts[
            "operator_review_tailoring_evidence"
        ],
        "evidence_chain_required_artifacts": list(
            EVIDENCE_CHAIN_REQUIRED_ARTIFACT_KEYS
        ),
        "evidence_chain_missing_artifacts": missing_artifacts,
        "automatic_internal_decisioning_goal": True,
        "external_action_automation_goal": False,
        "next_phase_should_execute_controlled_chain": True,
        "trace_persistence_requested": False,
        "trace_persistence_performed": False,
        "safety_metadata": safety_metadata,
        **readiness,
        **safety_metadata,
    }


def _maybe_run_controlled_evidence_chain_execution_after_application_priority(
    scored_jobs: List[Dict[str, Any]],
    *,
    enabled: bool | None = None,
    env: Dict[str, str] | None = None,
    execution_helper: Any = None,
    sample_limit: Any = None,
    include_trace_payload: bool = True,
) -> Dict[str, Any] | None:
    env_map = env if env is not None else os.environ
    execution_enabled = (
        _truthy_env_value(env_map.get(EVIDENCE_CHAIN_COLLECTOR_EXECUTION_FLAG))
        if enabled is None
        else enabled is True
    )
    if not execution_enabled:
        return None

    requested_sample_limit = (
        sample_limit
        if sample_limit is not None
        else env_map.get(EVIDENCE_CHAIN_COLLECTOR_EXECUTION_SAMPLE_LIMIT_FLAG, "")
    )
    safe_sample_limit = _evidence_chain_execution_sample_limit(
        requested_sample_limit
    )
    context = _agent_trace_context_from_env(
        env=env_map,
        context_prefix="evidence_chain_execution",
    )
    jobs_copy = [
        deepcopy(dict(job))
        for job in list(scored_jobs or [])
        if isinstance(job, dict)
    ][:safe_sample_limit]
    base_payload = {
        "artifact_type": "collector_controlled_evidence_chain_execution_result",
        "artifact_version": EVIDENCE_CHAIN_COLLECTOR_EXECUTION_VERSION,
        "collector_stage": "post_score_jobs",
        "gate_name": EVIDENCE_CHAIN_COLLECTOR_EXECUTION_FLAG,
        "enabled": True,
        "default_off": True,
        "read_only": True,
        "diagnostic_only": True,
        "sidecar_only": True,
        "include_trace_payload": bool(include_trace_payload),
        "sample_limit": safe_sample_limit,
        "jobs_received_count": len(
            [job for job in list(scored_jobs or []) if isinstance(job, dict)]
        ),
        "jobs_sampled_count": len(jobs_copy),
        **context,
    }

    try:
        if execution_helper is None:
            from src.agents.evidence_chain_execution import (
                execute_controlled_evidence_chain,
            )

            execution_helper = execute_controlled_evidence_chain

        execution_result = execution_helper(
            jobs_copy,
            resume_context=None,
            pipeline_run_id=context["pipeline_run_id"],
            owner_user_id=context["owner_user_id"],
            context_id=context["context_id"],
            execution_gate_enabled=True,
            include_trace_payload=include_trace_payload,
            sample_limit=safe_sample_limit,
        )
        automatic_internal_decisioning = bool(
            isinstance(execution_result, dict)
            and execution_result.get("automatic_internal_decisioning_performed")
        )
        safety_metadata = _evidence_chain_execution_safety_metadata(
            automatic_internal_decisioning_performed=automatic_internal_decisioning
        )
        payload = {
            **base_payload,
            "attempted": True,
            "executed": bool(
                isinstance(execution_result, dict)
                and execution_result.get("executed")
            ),
            "reason": (
                execution_result.get("reason", "")
                if isinstance(execution_result, dict)
                else "evidence_chain_execution_completed"
            ),
            "execution_result": execution_result,
            "trace_persistence_requested": False,
            "trace_persistence_performed": False,
            "safety_metadata": safety_metadata,
            **safety_metadata,
        }
        logger.info(
            "Controlled evidence-chain execution sidecar evaluated after "
            "application_priority: %s",
            payload.get("reason", "unknown"),
        )
        return payload
    except Exception as exc:
        safety_metadata = _evidence_chain_execution_safety_metadata(
            automatic_internal_decisioning_performed=False
        )
        logger.warning(
            "Controlled evidence-chain execution sidecar failed non-blocking "
            "after application_priority: %s",
            exc,
        )
        return {
            **base_payload,
            "attempted": True,
            "executed": False,
            "reason": "evidence_chain_execution_failed",
            "warning": str(exc),
            "error_message": str(exc),
            "trace_persistence_requested": False,
            "trace_persistence_performed": False,
            "safety_metadata": safety_metadata,
            **safety_metadata,
        }


def _maybe_persist_controlled_evidence_chain_execution_trace(
    execution_result: Dict[str, Any] | None,
    *,
    enabled: bool | None = None,
    env: Dict[str, str] | None = None,
    execute_callback: Any | None = None,
    cursor: Any | None = None,
    strict: bool = False,
    persistence_helper: Any = None,
) -> Dict[str, Any]:
    env_map = env if env is not None else os.environ
    persistence_enabled = (
        _truthy_env_value(env_map.get(EVIDENCE_CHAIN_TRACE_PERSISTENCE_FLAG))
        if enabled is None
        else enabled is True
    )
    trace_enabled = _truthy_env_value(env_map.get("APPLYLENS_AGENT_TRACE_ENABLED"))
    execution_enabled = _truthy_env_value(
        env_map.get(EVIDENCE_CHAIN_COLLECTOR_EXECUTION_FLAG)
    )
    context = _agent_trace_context_from_env(
        env=env_map,
        context_prefix="evidence_chain_trace_persistence",
    )

    def result(
        *,
        attempted: bool = False,
        persisted: bool = False,
        reason: str = "",
        payloads_found_count: int = 0,
        payloads_attempted_count: int = 0,
        payloads_persisted_count: int = 0,
        payloads_failed_count: int = 0,
        record_count: int = 0,
        run_count: int = 0,
        step_count: int = 0,
        per_payload_results: List[Dict[str, Any]] | None = None,
        error_message: str = "",
    ) -> Dict[str, Any]:
        safety_metadata = _evidence_chain_trace_persistence_safety_metadata(
            persistence_performed=bool(persisted)
        )
        payload = {
            "artifact_type": "collector_controlled_evidence_chain_trace_persistence_result",
            "artifact_version": EVIDENCE_CHAIN_TRACE_PERSISTENCE_VERSION,
            "collector_stage": "post_score_jobs",
            "gate_name": EVIDENCE_CHAIN_TRACE_PERSISTENCE_FLAG,
            "trace_gate_name": "APPLYLENS_AGENT_TRACE_ENABLED",
            "execution_gate_name": EVIDENCE_CHAIN_COLLECTOR_EXECUTION_FLAG,
            "enabled": bool(persistence_enabled),
            "trace_enabled": bool(trace_enabled),
            "execution_enabled": bool(execution_enabled),
            "default_off": True,
            "read_only": True,
            "diagnostic_only": True,
            "sidecar_only": True,
            "attempted": bool(attempted),
            "persisted": bool(persisted),
            "recorded": bool(persisted),
            "reason": reason,
            "payloads_found_count": int(payloads_found_count),
            "payloads_attempted_count": int(payloads_attempted_count),
            "payloads_persisted_count": int(payloads_persisted_count),
            "payloads_failed_count": int(payloads_failed_count),
            "record_count": int(record_count),
            "run_count": int(run_count),
            "step_count": int(step_count),
            "owner_user_id": context["owner_user_id"],
            "pipeline_run_id": context["pipeline_run_id"],
            "context_id": context["context_id"],
            "per_payload_results": list(per_payload_results or []),
            "trace_persistence_requested": bool(persistence_enabled),
            "trace_persistence_performed": bool(persisted),
            "trace_store_write_performed": bool(persisted),
            "database_write_performed": bool(persisted),
            "safety_metadata": safety_metadata,
            **safety_metadata,
        }
        if error_message:
            payload["error_message"] = error_message
            payload["warning"] = error_message
        return payload

    if not execution_enabled:
        return result(reason="execution_gate_disabled")
    if not persistence_enabled:
        return result(reason="trace_persistence_disabled")
    if not trace_enabled:
        return result(reason="trace_disabled")
    if not isinstance(execution_result, dict) or not execution_result:
        return result(reason="execution_result_missing")
    if not (
        context["owner_user_id"]
        and context["pipeline_run_id"]
        and context["context_id"]
    ):
        return result(reason="missing_trace_context")
    if cursor is None and execute_callback is None:
        return result(reason="write_executor_missing")
    if cursor is not None and execute_callback is not None:
        return result(reason="multiple_write_executors")

    trace_payloads = _valid_evidence_chain_trace_payloads_from_execution_result(
        execution_result
    )
    if not trace_payloads:
        return result(reason="trace_payload_missing")

    if persistence_helper is None:
        from src.agents.evidence_chain_composition import (
            persist_agent_evidence_chain_trace_payload,
        )

        persistence_helper = persist_agent_evidence_chain_trace_payload

    per_payload_results: List[Dict[str, Any]] = []
    payloads_persisted_count = 0
    payloads_failed_count = 0
    record_count = 0
    run_count = 0
    step_count = 0
    strict_mode = bool(strict) or _truthy_env_value(
        env_map.get("APPLYLENS_AGENT_TRACE_STRICT")
    )

    for index, trace_payload in enumerate(trace_payloads):
        try:
            persistence_result = persistence_helper(
                trace_payload=trace_payload,
                owner_user_id=context["owner_user_id"],
                pipeline_run_id=context["pipeline_run_id"],
                context_id=context["context_id"],
                cursor=cursor,
                execute_callback=execute_callback,
                persistence_gate_enabled=True,
                strict=strict_mode,
            )
        except Exception as exc:
            if strict_mode:
                raise
            payloads_failed_count += 1
            per_payload_results.append(
                {
                    "payload_index": index,
                    "attempted": True,
                    "recorded": False,
                    "reason": "evidence_chain_trace_persistence_failed",
                    "error_message": str(exc),
                }
            )
            continue

        persisted = bool(
            isinstance(persistence_result, dict)
            and (
                persistence_result.get("recorded")
                or persistence_result.get("trace_persistence_performed")
            )
        )
        if persisted:
            payloads_persisted_count += 1
            record_count += int(persistence_result.get("record_count") or 0)
            run_count += int(persistence_result.get("run_count") or 0)
            step_count += int(persistence_result.get("step_count") or 0)
        else:
            payloads_failed_count += 1
        per_payload_results.append(
            {
                "payload_index": index,
                "attempted": bool(
                    isinstance(persistence_result, dict)
                    and persistence_result.get("attempted")
                ),
                "recorded": persisted,
                "reason": (
                    persistence_result.get("reason", "")
                    if isinstance(persistence_result, dict)
                    else "invalid_persistence_result"
                ),
                "record_count": int(
                    persistence_result.get("record_count") or 0
                )
                if isinstance(persistence_result, dict)
                else 0,
                "run_count": int(persistence_result.get("run_count") or 0)
                if isinstance(persistence_result, dict)
                else 0,
                "step_count": int(persistence_result.get("step_count") or 0)
                if isinstance(persistence_result, dict)
                else 0,
                "agent_run_id": (
                    _clean_trace_text(persistence_result.get("agent_run_id"))
                    if isinstance(persistence_result, dict)
                    else ""
                ),
            }
        )

    persisted_any = payloads_persisted_count > 0
    reason = "" if persisted_any else "evidence_chain_trace_persistence_failed"
    return result(
        attempted=True,
        persisted=persisted_any,
        reason=reason,
        payloads_found_count=len(trace_payloads),
        payloads_attempted_count=len(trace_payloads),
        payloads_persisted_count=payloads_persisted_count,
        payloads_failed_count=payloads_failed_count,
        record_count=record_count,
        run_count=run_count,
        step_count=step_count,
        per_payload_results=per_payload_results,
    )


def log_market_insights(jobs: List[Dict[str, Any]]) -> None:
    from src.intelligence.market_insights import (
        detect_ai_hiring_surges,
        detect_emerging_tech,
        detect_hot_companies,
    )

    section("JOB MARKET INSIGHTS", logger)

    hot_companies = detect_hot_companies(jobs)

    logger.info("")
    logger.info("HOT COMPANIES")
    logger.info("-------------")

    for company, count in hot_companies:
        logger.info(f"{company:25} {count}")

    ai_surges = detect_ai_hiring_surges(jobs)

    logger.info("")
    logger.info("AI HIRING SURGES")
    logger.info("----------------")

    for company, count in ai_surges:
        logger.info(f"{company:25} {count}")

    emerging_tech = detect_emerging_tech(jobs)

    logger.info("")
    logger.info("EMERGING TECH STACK")
    logger.info("-------------------")

    for tech, count in emerging_tech:
        logger.info(f"{tech:20} {count}")


def log_company_hiring(jobs: List[Dict[str, Any]], logger) -> None:
    company_counts = Counter()

    for job in jobs:
        company = job.get("company")
        if company:
            company_counts[company] += 1

    logger.info("")
    logger.info("COMPANY HIRING FREQUENCY")

    for company, count in company_counts.most_common(10):
        logger.info(f"{count:3} | {company}")

    logger.info("")


async def collect_all_jobs_async() -> List[Dict[str, Any]]:
    from src.ai.job_fit_evaluator import evaluate_jobs, get_eval_cache_metrics
    from src.ai.llm_client import get_provider_metrics, reset_provider_metrics
    from src.ai.resume_matcher import match_resumes
    from src.ai.skill_llm_enricher import (
        get_skill_cache_metrics,
        reset_skill_cache_metrics,
    )
    from src.discovery.domain_learner import learn_domains_from_jobs
    from src.discovery.persist_discovered import persist_discovered_companies
    from src.intelligence.job_intelligence import (
        ai_evaluation_skip_summary,
        build_job_intelligence,
        filter_jobs_for_ai_evaluation,
    )
    from src.intelligence.skill_discovery import discover_new_skills
    from src.intelligence.skill_frequency import top_skills
    from src.pipeline.application_scorer import score_jobs
    from src.pipeline.dedupe import dedupe_jobs
    from src.pipeline.embedding_prefilter import prefilter_jobs_by_embedding
    from src.pipeline.job_details import enrich_job_details
    from src.pipeline.job_filter import (
        build_source_health_report_rows,
        filter_jobs,
        role_title_filter_audit_counts,
        write_source_health_report_csv,
        write_role_title_filter_audit_csv,
    )
    from src.pipeline.job_ranker import rank_jobs
    from src.rag.export_job_corpus import export_job_corpus
    from src.scrapers.ashby_scraper import scrape_all_ashby
    from src.scrapers.builtin_scraper import scrape_all_builtin
    from src.scrapers.greenhouse_scraper import scrape_all_greenhouse
    from src.scrapers.jobvite_scraper import scrape_all_jobvite
    from src.scrapers.lever_scraper import scrape_all_lever
    from src.scrapers.smartrecruiters_scraper import scrape_all_smartrecruiters
    from src.scrapers.workable_scraper import scrape_all_workable
    from src.scrapers.workday_scraper import scrape_all_workday
    from src.storage.metrics_store import (
        get_hiring_momentum,
        get_last_ats_counts,
        get_last_run,
        record_ats_counts,
        record_company_hiring,
        record_pipeline_run,
    )
    from src.storage.skill_corpus_store import get_top_corpus_skills, store_job_skills
    from src.utils.ats_health import (
        check_ats_failure,
        check_ats_health,
        check_pipeline_regression,
    )
    from src.utils.job_cache import (
        cache_keys_for_jobs,
        filter_new_jobs,
        load_seen_job_ids,
        save_new_job_ids,
    )
    from src.utils.pipeline_metrics import log_stage_metrics

    scrapers = [
        ("workday", scrape_all_workday),
        ("greenhouse", scrape_all_greenhouse),
        ("lever", scrape_all_lever),
        ("ashby", scrape_all_ashby),
        ("workable", scrape_all_workable),
        ("jobvite", scrape_all_jobvite),
        ("smartrecruiters", scrape_all_smartrecruiters),
        ("builtin", scrape_all_builtin),
    ]

    all_jobs: List[Dict[str, Any]] = []
    seen_job_ids = load_seen_job_ids()
    pipeline_preferences = _pipeline_preferences_from_env()
    selected_role_families = pipeline_preferences["selected_role_families"]
    corpus_path = str(
        os.environ.get("JOB_STACK_JOB_CORPUS_PATH", "")
        or "postgres://rag_job_documents"
    ).strip()
    corpus_file = Path(corpus_path)
    if selected_role_families:
        logger.info(
            "Using selected role families for title filtering/ranking: %s",
            ", ".join(selected_role_families),
        )
    else:
        logger.info("Using default data/AI title filtering/ranking behavior.")
    logger.info(f"Loaded {len(seen_job_ids)} cached job IDs")

    start_total = time.time()
    loop = asyncio.get_running_loop()

    async def run_scraper(name: str, fn):
        start = time.time()
        logger.info("[collector] %s starting", name)
        try:
            jobs = await loop.run_in_executor(None, fn)
            elapsed = round(time.time() - start, 2)
            return name, jobs, elapsed, None
        except Exception as exc:
            elapsed = round(time.time() - start, 2)
            return name, [], elapsed, exc

    start_stage("scraping", "Running ATS scrapers")
    tasks = [
        asyncio.create_task(run_scraper(name, fn))
        for name, fn in scrapers
    ]

    for task in asyncio.as_completed(tasks):
        name, jobs, elapsed, err = await task

        if err:
            logger.error(
                f"[collector] {name} failed | time={elapsed}s | error={err}"
            )
            continue

        logger.info(
            f"[collector] {name} finished | jobs={len(jobs)} | time={elapsed}s"
        )

        if jobs:
            all_jobs.extend(jobs)

    section("SCRAPER RESULTS", logger)

    total_elapsed = round(time.time() - start_total, 2)
    logger.info(f"Total scraping time: {total_elapsed}s")

    scraped_counts = log_stage_metrics("SCRAPED", all_jobs)
    complete_stage("scraping", counts={"scraped_jobs": len(all_jobs)})

    learn_domains_from_jobs(all_jobs)
    check_ats_health(all_jobs)

    section("FILTER PIPELINE", logger)
    start_stage("filtering", f"Filtering {len(all_jobs)} scraped jobs")

    role_title_audit_rows = [] if _is_user_pipeline_mode() and selected_role_families else None
    filter_result = filter_jobs(
        all_jobs,
        selected_role_families=selected_role_families or None,
        filter_mode="user_pipeline" if _is_user_pipeline_mode() else "strict_live",
        return_diagnostics=True,
        role_title_audit_rows=role_title_audit_rows,
        excluded_keywords=pipeline_preferences["excluded_keywords"],
    )
    filtered_jobs, filter_diagnostics = filter_result
    role_title_audit_summary = role_title_filter_audit_counts(role_title_audit_rows or [])
    if role_title_audit_rows is not None:
        audit_path = Path(corpus_path).expanduser().with_name("role_title_filter_audit.csv")
        write_role_title_filter_audit_csv(role_title_audit_rows, audit_path)
        logger.info(
            "Role title filter audit written: %s | total=%s pass=%s reject=%s suspected_false_negative=%s",
            audit_path,
            role_title_audit_summary["role_title_audit_total"],
            role_title_audit_summary["role_title_audit_pass"],
            role_title_audit_summary["role_title_audit_reject"],
            role_title_audit_summary["role_title_audit_suspected_false_negative"],
        )
    logger.info(f"Total filtered jobs: {len(filtered_jobs)}")

    filtered_counts = log_stage_metrics("FILTERED", filtered_jobs)

    drop_pct = 0
    if all_jobs:
        drop_pct = round((1 - len(filtered_jobs) / len(all_jobs)) * 100, 2)

    logger.info(f"Filter drop rate: {drop_pct}%")
    complete_stage(
        "filtering",
        counts={
            "filtered_jobs": len(filtered_jobs),
            "filter_title_mismatch": filter_diagnostics.get("title_mismatch", 0),
            "filter_location_not_us": filter_diagnostics.get("location_not_us", 0),
            "filter_not_recent": filter_diagnostics.get("not_recent", 0),
            "filter_missing_timestamp": filter_diagnostics.get("missing_timestamp", 0),
            "filter_missing_timestamp_allowed": filter_diagnostics.get("missing_timestamp_allowed", 0),
            "filter_title_pass": filter_diagnostics.get("title_pass", 0),
            "filter_location_pass": filter_diagnostics.get("location_pass", 0),
            "filter_excluded_keyword": filter_diagnostics.get("excluded_keyword", 0),
            "ashby_timestamp_cache_hit": filter_diagnostics.get("ashby_timestamp_cache_hit", 0),
            "ashby_timestamp_cache_miss": filter_diagnostics.get("ashby_timestamp_cache_miss", 0),
            "ashby_timestamp_fetch_success": filter_diagnostics.get("ashby_timestamp_fetch_success", 0),
            "ashby_timestamp_fetch_429": filter_diagnostics.get("ashby_timestamp_fetch_429", 0),
            "ashby_timestamp_fetch_failed": filter_diagnostics.get("ashby_timestamp_fetch_failed", 0),
            **role_title_audit_summary,
        },
    )

    section("DEDUPLICATION", logger)
    start_stage("dedupe", f"Deduplicating {len(filtered_jobs)} filtered jobs")

    deduped_jobs = dedupe_jobs(filtered_jobs)
    log_company_hiring(deduped_jobs, logger)

    deduped_counts = log_stage_metrics("DEDUPED", deduped_jobs)
    complete_stage("dedupe", counts={"deduped_jobs": len(deduped_jobs)})

    section("RANKING", logger)
    start_stage("ranking", f"Ranking {len(deduped_jobs)} deduped jobs")

    ranked_jobs = rank_jobs(
        deduped_jobs,
        selected_role_families=selected_role_families or None,
        target_seniority=pipeline_preferences["target_seniority"],
        preferred_locations=pipeline_preferences["preferred_locations"],
        preferred_skills=pipeline_preferences["preferred_skills"],
    )
    preference_counts = {
        "preference_seniority_match": sum(1 for job in ranked_jobs if job.get("_preference_seniority_match")),
        "preference_seniority_unknown": sum(1 for job in ranked_jobs if job.get("_preference_seniority_unknown")),
        "preference_location_match": sum(1 for job in ranked_jobs if job.get("_preference_location_matches")),
        "preference_skill_matches": sum(
            len(job.get("_preference_skill_matches") or [])
            for job in ranked_jobs
        ),
    }
    log_stage_metrics("RANKED", ranked_jobs)
    complete_stage("ranking", counts={"ranked_jobs": len(ranked_jobs), **preference_counts})

    section("CACHE FILTER", logger)
    start_stage("cache_filter", f"Filtering cached jobs from {len(ranked_jobs)} ranked jobs")

    new_jobs, new_job_ids = filter_new_jobs(ranked_jobs, seen_job_ids)
    logger.info(f"New jobs after cache filtering: {len(new_jobs)}")
    complete_stage("cache_filter", counts={"new_jobs": len(new_jobs)})

    section("JOB DETAILS", logger)
    start_stage("details", f"Enriching details for {len(new_jobs)} new jobs")

    detailed_jobs = enrich_job_details(new_jobs)
    details_counts = log_stage_metrics("DETAILS", detailed_jobs)
    complete_stage("details", counts={"detailed_jobs": len(detailed_jobs)})

    section("JOB INTELLIGENCE", logger)
    start_stage("intelligence", f"Building intelligence for {len(detailed_jobs)} detailed jobs")

    reset_provider_metrics()
    reset_skill_cache_metrics()

    if _truthy_env_value(os.environ.get(JD_INTELLIGENCE_CONTROLLED_LLM_FLAG)):
        controlled_jd_result = _build_intelligent_jobs_with_controlled_jd_agent_ownership(
            detailed_jobs,
            build_job_intelligence_func=build_job_intelligence,
            enabled=True,
            env=os.environ,
            strict=True,
        )
        intelligent_jobs = controlled_jd_result["intelligent_jobs"]
        controlled_jd_summary = controlled_jd_result.get(
            "jd_intelligence_controlled_llm_runtime_summary"
        )
        if isinstance(controlled_jd_summary, dict):
            logger.info(
                "JD Intelligence controlled LLM ownership evaluated: seen=%s "
                "artifacts=%s reused=%s extraction_helper_calls=%s",
                controlled_jd_summary.get("total_jobs_seen", 0),
                controlled_jd_summary.get("artifacts_built", 0),
                controlled_jd_summary.get("existing_intelligence_reused_count", 0),
                controlled_jd_summary.get("extraction_helper_called_count", 0),
            )
    else:
        intelligent_jobs = [build_job_intelligence(job) for job in detailed_jobs]
    logger.info(f"Intelligence extracted for {len(intelligent_jobs)} jobs")
    complete_stage("intelligence", counts={"intelligent_jobs": len(intelligent_jobs)})
    _maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        intelligent_jobs
    )

    skill_cache_summary = get_skill_cache_metrics()
    logger.info(
        "SKILL CACHE SUMMARY | hits=%s | misses=%s | stores=%s | cache_only_skips=%s | live_failures=%s",
        skill_cache_summary["cache_hits"],
        skill_cache_summary["cache_misses"],
        skill_cache_summary["cache_stores"],
        skill_cache_summary["cache_only_skips"],
        skill_cache_summary["live_failures"],
    )

    skill_run_id = str(uuid4())
    store_job_skills(skill_run_id, intelligent_jobs)

    logger.info("")
    logger.info("TOP EXTRACTED SKILLS")
    logger.info("--------------------")

    for skill, count in top_skills(intelligent_jobs, top_n=50):
        logger.info(f"{count:3} | {skill}")

    for skill, count in get_top_corpus_skills(limit=100):
        logger.info(f"{count:3} | {skill}")

    section("SKILL DISCOVERY", logger)
    new_skills = discover_new_skills(intelligent_jobs)

    if new_skills:
        logger.info(f"New skills discovered: {len(new_skills)}")
        logger.info(", ".join(new_skills[:10]))

    section("AI EVALUATION FILTER", logger)
    start_stage("ai_evaluation_filter", "Selecting jobs eligible for AI evaluation")

    evaluable_jobs = filter_jobs_for_ai_evaluation(intelligent_jobs)
    skip_summary = ai_evaluation_skip_summary(intelligent_jobs, limit=10)
    skipped_count = int(skip_summary.get("skipped_count", 0) or 0)
    reason_counts = dict(skip_summary.get("reason_counts", {}) or {})
    skipped_samples = list(skip_summary.get("skipped_samples", []) or [])

    if skipped_count:
        logger.info(
            "AI evaluation skipped jobs: count=%s | reason_counts=%s",
            skipped_count,
            reason_counts,
        )
        for index, skipped_job in enumerate(skip_summary.get("skipped_jobs", []) or [], start=1):
            logger.info(
                "AI evaluation skipped #%s | company=%s | title=%s | url=%s | reason=%s",
                index,
                skipped_job.get("company", ""),
                skipped_job.get("title", ""),
                skipped_job.get("url", ""),
                skipped_job.get("reason", ""),
            )
    logger.info(f"Jobs eligible for AI evaluation: {len(evaluable_jobs)}")
    complete_stage(
        "ai_evaluation_filter",
        counts={
            "evaluable_jobs": len(evaluable_jobs),
            "ai_evaluation_skipped_jobs": skipped_count,
            "ai_evaluation_skip_reasons": reason_counts,
            "ai_evaluation_skipped_samples": skipped_samples,
        },
    )

    section("EMBEDDING PREFILTER", logger)
    start_stage("embedding_prefilter", f"Embedding-prefiltering {len(evaluable_jobs)} evaluable jobs")

    prefilter_input_count = len(evaluable_jobs)

    if _is_user_pipeline_mode():
        logger.info(
            "Skipping legacy filesystem embedding prefilter for user pipeline run; "
            "profile resumes are stored in Postgres."
        )
        prefilter_output_count = len(evaluable_jobs)
        complete_stage(
            "embedding_prefilter",
            counts={
                "prefilter_jobs": len(evaluable_jobs),
                "skipped_legacy_resume_dir": True,
                "reason": "user_pipeline_postgres_profile_resumes",
            },
        )
    else:
        evaluable_jobs = prefilter_jobs_by_embedding(
            evaluable_jobs,
            top_n=None,
        )
        prefilter_output_count = len(evaluable_jobs)

        logger.info(
            f"Embedding prefilter reduced AI candidates: "
            f"{prefilter_input_count} -> {prefilter_output_count}"
        )

        if prefilter_input_count:
            reduction_pct = round(
                (1 - prefilter_output_count / prefilter_input_count) * 100,
                2,
            )
            logger.info(f"AI candidate reduction rate: {reduction_pct}%")

        complete_stage("embedding_prefilter", counts={"prefilter_jobs": len(evaluable_jobs)})

    _record_relevance_prefilter_agent_trace(
        prefilter_summary={
            "input_count": prefilter_input_count,
            "kept_count": prefilter_output_count,
            "dropped_count": prefilter_input_count - prefilter_output_count,
            "reason_counts": {
                "embedding_prefilter_kept": prefilter_output_count,
                "embedding_prefilter_dropped": max(
                    prefilter_input_count - prefilter_output_count,
                    0,
                ),
            },
            "role_family": ",".join(selected_role_families),
            "seniority": ",".join(pipeline_preferences["target_seniority"]),
            "location_policy": ",".join(pipeline_preferences["preferred_locations"]),
            "source_stage": "embedding_prefilter",
        }
    )

    section("AI JOB EVALUATION", logger)
    start_stage("ai_evaluation", f"Evaluating {len(evaluable_jobs)} jobs with AI")

    ai_jobs = evaluate_jobs(evaluable_jobs)
    logger.info(f"AI evaluated {len(ai_jobs)} jobs")
    complete_stage("ai_evaluation", counts={"ai_jobs": len(ai_jobs)})

    provider_summary = get_provider_metrics()
    logger.info(
        "LLM PROVIDER SUMMARY | primary_attempts=%s | fallback_attempts=%s | groq_calls=%s | gemini_calls=%s | fallback_successes=%s | provider_failures=%s",
        provider_summary["primary_attempts"],
        provider_summary["fallback_attempts"],
        provider_summary["groq_calls"],
        provider_summary["gemini_calls"],
        provider_summary["fallback_successes"],
        provider_summary["provider_failures"],
    )

    eval_cache_summary = get_eval_cache_metrics()
    logger.info(
        "EVAL CACHE SUMMARY | hits=%s | misses=%s | stores=%s | cache_only_skips=%s | live_failures=%s",
        eval_cache_summary["eval_cache_hits"],
        eval_cache_summary["eval_cache_misses"],
        eval_cache_summary["eval_cache_stores"],
        eval_cache_summary["eval_cache_only_skips"],
        eval_cache_summary["eval_live_failures"],
    )

    section("EMBEDDING RESUME PRIOR", logger)

    if _is_user_pipeline_mode():
        start_stage(
            "resume_matching",
            "Skipping legacy filesystem resume prior for user pipeline run",
        )
        for job in ai_jobs:
            job.setdefault("embedding_resume_prior", None)
            job.setdefault("embedding_resume_prior_score", None)
        logger.info(
            "Skipping legacy filesystem resume matching for user pipeline run; "
            "profile resumes are stored in Postgres."
        )
        complete_stage(
            "resume_matching",
            counts={
                "resume_matched_jobs": 0,
                "skipped_legacy_resume_dir": True,
                "ai_jobs": len(ai_jobs),
            },
        )
    else:
        start_stage(
            "resume_matching",
            f"Computing embedding resume prior for {len(ai_jobs)} AI-evaluated jobs",
        )

        ai_jobs = match_resumes(ai_jobs)
        logger.info("Embedding resume prior completed")
        complete_stage("resume_matching", counts={"resume_matched_jobs": len(ai_jobs)})

    section("APPLICATION PRIORITY", logger)
    start_stage("application_priority", f"Scoring {len(ai_jobs)} jobs for application priority")

    scored_jobs = score_jobs(ai_jobs)
    logger.info(f"Priority scoring completed for {len(scored_jobs)} jobs")
    complete_stage("application_priority", counts={"scored_jobs": len(scored_jobs)})
    vector_evidence_hook_payload = (
        _maybe_collect_vector_evidence_after_application_priority(scored_jobs)
    )
    _maybe_run_shadow_sidecar_after_application_priority(
        scored_jobs,
        vector_evidence_hook_payload=vector_evidence_hook_payload,
    )
    _maybe_invoke_advisory_chain_diagnostics_after_application_priority(scored_jobs)
    _maybe_build_evidence_chain_collector_diagnostics(scored_jobs)
    evidence_chain_execution_result = (
        _maybe_run_controlled_evidence_chain_execution_after_application_priority(scored_jobs)
    )
    _maybe_persist_controlled_evidence_chain_execution_trace(
        evidence_chain_execution_result
    )

    if role_title_audit_rows is not None:
        source_health_path = Path(corpus_path).expanduser().with_name("source_health_report.csv")
        source_health_rows = build_source_health_report_rows(role_title_audit_rows, scored_jobs)
        write_source_health_report_csv(role_title_audit_rows, scored_jobs, source_health_path)
        logger.info("Source health report written: %s", source_health_path)
        trace_result = _record_source_health_agent_trace(
            source_health_rows=source_health_rows,
            artifact_path=source_health_path,
        )
        if trace_result.get("recorded"):
            logger.info(
                "Source Health Agent trace recorded: %s %s",
                trace_result.get("agent_run_id", ""),
                trace_result.get("agent_step_id", ""),
            )
        elif trace_result.get("warning"):
            logger.warning("Source Health Agent trace skipped: %s", trace_result.get("warning"))
        update_counts(**_agent_trace_status_counts(trace_result))

    start_stage("rag_export", f"Exporting {len(scored_jobs)} jobs to RAG corpus")

    if scored_jobs:
        rag_export_count = export_job_corpus(
            scored_jobs,
            corpus_path,
        )
        logger.info(f"RAG corpus exported: {rag_export_count} documents")
    else:
        if corpus_file.exists() and corpus_file.stat().st_size > 0:
            rag_export_count = 0
            logger.info(
                "RAG export skipped because scored_jobs is empty; preserving existing corpus at %s",
                corpus_path,
            )
        else:
            rag_export_count = export_job_corpus(
                scored_jobs,
                corpus_path,
            )
            logger.info(f"RAG corpus exported: {rag_export_count} documents")

    complete_stage("rag_export", counts={"rag_export_count": rag_export_count})

    log_market_insights(detailed_jobs)

    save_new_job_ids(cache_keys_for_jobs(scored_jobs))
    persist_discovered_companies()

    pipeline_runtime = round(time.time() - start_total, 2)
    logger.info(f"Total pipeline runtime: {pipeline_runtime}s")

    current_metrics = {
        "scraped": len(all_jobs),
        "filtered": len(filtered_jobs),
        "deduped": len(deduped_jobs),
        "ranked": len(ranked_jobs),
        "details": len(detailed_jobs),
        "drop_pct": drop_pct,
    }

    if _is_user_pipeline_mode():
        section("PIPELINE HEALTH", logger)
        logger.info(
            "Skipping global pipeline metrics store for user pipeline run. "
            "User run status is persisted in user_pipeline_runs."
        )
    else:
        prev_run = get_last_run()
        prev_ats_counts = get_last_ats_counts("SCRAPED")

        check_ats_failure(prev_ats_counts, scraped_counts, logger)

        section("PIPELINE HEALTH", logger)
        check_pipeline_regression(prev_run, current_metrics, logger)

        run_id = record_pipeline_run(
            runtime=pipeline_runtime,
            scraped=len(all_jobs),
            filtered=len(filtered_jobs),
            deduped=len(deduped_jobs),
            ranked=len(ranked_jobs),
            details=len(detailed_jobs),
            new_jobs=len(new_jobs),
            drop_pct=drop_pct,
        )

        record_company_hiring(run_id, deduped_jobs)

        record_ats_counts(run_id, "SCRAPED", scraped_counts)
        record_ats_counts(run_id, "FILTERED", filtered_counts)
        record_ats_counts(run_id, "DEDUPED", deduped_counts)
        record_ats_counts(run_id, "RANKED", log_stage_metrics("RANKED", ranked_jobs))
        record_ats_counts(run_id, "DETAILS", details_counts)

        logger.info("Pipeline metrics stored")

        momentum = get_hiring_momentum()
        if momentum:
            logger.info("")
            logger.info("HIRING MOMENTUM")
            logger.info("----------------")

            for company, ats, prev, curr, delta in momentum[:10]:
                logger.info(f"{company:25} {ats:12} {prev} → {curr}  (+{delta})")

    return scored_jobs
