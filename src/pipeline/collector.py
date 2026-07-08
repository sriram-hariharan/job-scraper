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
