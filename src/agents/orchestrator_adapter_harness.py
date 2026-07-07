from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.agents import (
    fixture_validator,
    orchestrator_adapters,
    trace,
    workflow_planner,
    workflow_registry,
)
from src.storage.agent_trace import store as agent_trace_store


HARNESS_VERSION = "read_only_adapter_harness_v1"
EXECUTION_MODE = "read_only_preflight"
ADVISORY_CHAIN_HARNESS_VERSION = "default_off_advisory_agent_chain_harness_v1"
ADVISORY_CHAIN_EXECUTION_MODE = "default_off_read_only_advisory_chain"
ADVISORY_CHAIN_TRACE_BUNDLE_VERSION = "default_off_advisory_chain_trace_bundle_v1"
ADVISORY_CHAIN_INVOCATION_ADAPTER_VERSION = "explicit_read_only_advisory_chain_invocation_adapter_v1"
ADVISORY_CHAIN_INVOCATION_MODE = "explicit_read_only_advisory_chain_invocation"
ADVISORY_CHAIN_TRACE_PERSISTENCE_VERSION = "controlled_advisory_chain_trace_persistence_v1"
ADVISORY_CHAIN_TRACE_READBACK_COMPATIBILITY_VERSION = "advisory_chain_trace_readback_compatibility_v1"
PREFLIGHT_JSON_NAME = "read_only_adapter_preflight.json"
PREFLIGHT_MD_NAME = "read_only_adapter_preflight.md"
REPO_ROOT = Path(__file__).resolve().parents[2]
APPROVED_FIXTURE_DIR = (
    REPO_ROOT / "tests" / "fixtures" / "agentic_storage_transaction_failure_modes"
)
APPROVED_FIXTURE_FILENAMES = tuple(
    sorted(
        [
            "safe_execution_request_minimal.json",
            "blocked_db_write_request_minimal.json",
            "blocked_application_submission_request_minimal.json",
        ]
    )
)
ADVISORY_CHAIN_FALSE_FLAGS = [
    "allow_agent_execution",
    "did_execute",
    "did_execute_chain",
    "did_mutate_production",
    "did_write_db",
    "mutation_allowed",
    "auto_apply_allowed",
    "ats_submission_allowed",
    "application_submission_allowed",
    "apply_click_allowed",
    "queue_mutation_allowed",
    "scoring_mutation_allowed",
    "ranking_mutation_allowed",
    "filtering_mutation_allowed",
    "tailoring_generation_allowed",
    "tailoring_mutation_allowed",
    "source_resume_mutation_allowed",
    "llm_provider_call_allowed",
    "live_provider_allowed",
    "scheduler_mutation_allowed",
    "workflow_runner_live_execution_allowed",
]
ADVISORY_CHAIN_READBACK_SAFETY_FLAGS = [
    "auto_apply_allowed",
    "ats_submission_allowed",
    "apply_click_allowed",
    "queue_mutation_allowed",
    "ranking_mutation_allowed",
    "scoring_mutation_allowed",
    "filtering_mutation_allowed",
    "tailoring_mutation_allowed",
    "source_resume_mutation_allowed",
    "scheduler_mutation_allowed",
    "live_provider_allowed",
    "workflow_runner_live_execution_allowed",
]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truthy(value: Any) -> bool:
    return _clean_text(value).lower() in {"1", "true", "yes", "y", "on"}


def _adapter_specs_by_key(contract: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    specs = contract.get("adapter_specs") if isinstance(contract, dict) else {}
    return dict(specs) if isinstance(specs, dict) else {}


def _artifact_presence(artifact_root: str | Path | None, artifact_names: List[str]) -> Dict[str, Dict[str, Any]]:
    root_text = _clean_text(artifact_root)
    if not root_text:
        return {}
    root = Path(root_text)
    return {
        artifact: {
            "path": str(root / artifact),
            "exists": (root / artifact).exists(),
        }
        for artifact in artifact_names
        if _clean_text(artifact)
    }


def build_read_only_adapter_harness_context(
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    artifact_root: str | Path | None = None,
    created_at_utc: str = "",
    manifest: Dict[str, Any] | None = None,
    contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    workflow_manifest = deepcopy(manifest) if manifest is not None else workflow_registry.get_agentic_workflow_manifest()
    adapter_contract = deepcopy(contract) if contract is not None else orchestrator_adapters.get_orchestrator_adapter_contract()
    return {
        "harness_version": HARNESS_VERSION,
        "execution_mode": EXECUTION_MODE,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "artifact_root": _clean_text(artifact_root),
        "created_at_utc": _clean_text(created_at_utc) or _utc_now_iso(),
        "workflow_name": _clean_text(workflow_manifest.get("workflow_name")),
        "workflow_version": _clean_text(workflow_manifest.get("workflow_version")),
        "adapter_contract_version": _clean_text(adapter_contract.get("contract_version")),
        "allow_agent_execution": False,
    }


def _preflight_status(spec: Dict[str, Any]) -> str:
    adapter_status = _clean_text(spec.get("adapter_status"))
    allowed_mode = _clean_text(spec.get("allowed_execution_mode"))
    if (
        adapter_status == "blocked"
        or bool(spec.get("mutates_production_decisions"))
        or bool(spec.get("llm_call_expected"))
        or allowed_mode in orchestrator_adapters.LIVE_EXECUTION_MODES
    ):
        return "blocked"
    if adapter_status == "ready_for_read_only_adapter":
        return "ready_read_only_contract"
    return "needs_adapter"


def _reason_codes_for_result(spec: Dict[str, Any], presence: Dict[str, Dict[str, Any]]) -> List[str]:
    reason_codes = [
        _clean_text(item)
        for item in list(spec.get("reason_codes") or [])
        if _clean_text(item)
    ]
    reason_codes.extend(["read_only_preflight", "agent_execution_disabled"])
    if presence and any(not bool(item.get("exists")) for item in presence.values()):
        reason_codes.append("missing_required_artifacts")
    return sorted(set(reason_codes))


def _advisory_chain_agent_status(*, enabled: bool, spec: Dict[str, Any]) -> str:
    if (
        bool(spec.get("mutates_production_decisions"))
        or bool(spec.get("llm_call_expected"))
        or _clean_text(spec.get("allowed_execution_mode")) in orchestrator_adapters.LIVE_EXECUTION_MODES
    ):
        return "blocked_non_read_only"
    if enabled and _clean_text(spec.get("adapter_status")) == "ready_for_read_only_adapter":
        return "ready_read_only_advisory"
    if enabled:
        return "contract_only_not_executable"
    return "disabled_default_off"


def _build_advisory_chain_agent(
    *,
    index: int,
    agent: Dict[str, Any],
    spec: Dict[str, Any],
    enabled: bool,
) -> Dict[str, Any]:
    agent_key = _clean_text(agent.get("agent_key"))
    return {
        "chain_index": index,
        "agent_key": agent_key,
        "agent_name": _clean_text(agent.get("agent_name")),
        "agent_version": _clean_text(agent.get("agent_version")),
        "owner_module": _clean_text(spec.get("owner_module") or agent.get("owner_module")),
        "adapter_status": _clean_text(spec.get("adapter_status")),
        "chain_status": _advisory_chain_agent_status(enabled=enabled, spec=spec),
        "advisory_only": bool(agent.get("advisory_only")),
        "read_only": True,
        "diagnostic_only": bool(agent.get("diagnostic_only")),
        "execution_enabled": False,
        "did_execute": False,
        "mutation_allowed": False,
        "auto_apply_allowed": False,
        "ats_submission_allowed": False,
        "application_submission_allowed": False,
        "apply_click_allowed": False,
        "queue_mutation_allowed": False,
        "scoring_mutation_allowed": False,
        "ranking_mutation_allowed": False,
        "filtering_mutation_allowed": False,
        "tailoring_generation_allowed": False,
        "tailoring_mutation_allowed": False,
        "source_resume_mutation_allowed": False,
        "llm_provider_call_allowed": False,
        "live_provider_allowed": False,
        "scheduler_mutation_allowed": False,
        "mutates_production_decisions": bool(spec.get("mutates_production_decisions")),
        "llm_call_expected": bool(spec.get("llm_call_expected")),
        "allowed_execution_mode": _clean_text(spec.get("allowed_execution_mode")),
        "trace_supported": bool(spec.get("trace_supported")),
        "reason_codes": sorted(
            {
                "default_off_advisory_chain",
                "agent_execution_disabled",
                "production_mutation_disabled",
                "auto_apply_disabled",
                "ats_submission_disabled",
                *[
                    _clean_text(item)
                    for item in list(spec.get("reason_codes") or [])
                    if _clean_text(item)
                ],
            }
        ),
    }


def _deterministic_advisory_chain_run_id(
    *,
    workflow_manifest: Dict[str, Any],
    ordered_keys: List[str],
    pipeline_run_id: str,
    owner_user_id: str,
) -> str:
    seed = {
        "bundle_version": ADVISORY_CHAIN_TRACE_BUNDLE_VERSION,
        "workflow_name": _clean_text(workflow_manifest.get("workflow_name")),
        "workflow_version": _clean_text(workflow_manifest.get("workflow_version")),
        "ordered_agent_keys": list(ordered_keys),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
    }
    digest = hashlib.sha256(json.dumps(seed, sort_keys=True).encode("utf-8")).hexdigest()
    return f"advisory_chain_{digest[:16]}"


def _advisory_chain_safety_summary() -> Dict[str, Any]:
    return {
        "trace_persistence_enabled": False,
        "trace_store_write_enabled": False,
        "did_prepare_trace_recording_payload": False,
        "did_call_trace_execution_helper": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_create_agent_run": False,
        "did_create_agent_step": False,
        "did_update_agent_run": False,
        "did_update_agent_step": False,
        "did_call_llm": False,
        "did_call_live_provider": False,
        "did_change_pipeline": False,
        "did_change_scoring": False,
        "did_change_ranking": False,
        "did_change_filtering": False,
        "did_change_queue": False,
        "did_change_tailoring": False,
        "did_mutate_source_resume": False,
        "did_execute_scheduler": False,
        "did_click_apply": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "did_send_recruiter_message": False,
        "did_mark_applied": False,
    }


def _build_advisory_chain_trace_ready_bundle(
    *,
    chain_run_id: str,
    chain_agents: List[Dict[str, Any]],
    workflow_manifest: Dict[str, Any],
    pipeline_run_id: str,
    owner_user_id: str,
    created_at_utc: str,
    validation: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    run_snapshot = {
        "agent_run_id": chain_run_id,
        "owner_user_id": _clean_text(owner_user_id) or "read_only_advisory_chain",
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "context_id": "default_off_advisory_chain",
        "status": "skipped_default_off",
        "started_at": _clean_text(created_at_utc),
        "completed_at": _clean_text(created_at_utc),
        "summary_json": {
            "workflow_name": _clean_text(workflow_manifest.get("workflow_name")),
            "workflow_version": _clean_text(workflow_manifest.get("workflow_version")),
            "agent_count": len(chain_agents),
            "did_execute": False,
            "mutation_allowed": False,
            "auto_apply_allowed": False,
        },
        "error": "",
    }
    step_summaries = [
        {
            "agent_step_id": f"{chain_run_id}:{int(agent.get('chain_index') or 0):02d}:{_clean_text(agent.get('agent_key'))}",
            "agent_run_id": chain_run_id,
            "owner_user_id": _clean_text(owner_user_id) or "read_only_advisory_chain",
            "pipeline_run_id": _clean_text(pipeline_run_id),
            "context_id": "default_off_advisory_chain",
            "agent_name": _clean_text(agent.get("agent_name")),
            "agent_version": _clean_text(agent.get("agent_version")),
            "step_name": _clean_text(agent.get("agent_key")),
            "step_index": int(agent.get("chain_index") or 0),
            "status": _clean_text(agent.get("chain_status")) or "disabled_default_off",
            "started_at": _clean_text(created_at_utc),
            "completed_at": _clean_text(created_at_utc),
            "input_json": {
                "adapter_status": _clean_text(agent.get("adapter_status")),
                "allowed_execution_mode": _clean_text(agent.get("allowed_execution_mode")),
            },
            "output_json": {
                "advisory_only": bool(agent.get("advisory_only")),
                "read_only": bool(agent.get("read_only")),
                "did_execute": False,
                "mutation_allowed": False,
            },
            "validation_json": {
                "reason_codes": list(agent.get("reason_codes") or []),
                "safety_flags": {
                    flag: bool(agent.get(flag))
                    for flag in ADVISORY_CHAIN_FALSE_FLAGS
                    if flag in agent
                },
            },
            "latency_ms": 0,
            "model_provider": "deterministic",
            "model_name": "default_off_advisory_chain_harness",
            "token_usage_json": {},
            "cost_json": {},
            "error": "",
            "did_execute": False,
            "mutation_allowed": False,
        }
        for agent in chain_agents
    ]
    stage_trace_bundle = trace.build_stage_trace_bundle_payload(
        run_snapshot=run_snapshot,
        step_snapshots=step_summaries,
        expected_stage_order=list(workflow_manifest.get("ordered_agent_keys") or []),
    )
    return {
        "bundle_version": ADVISORY_CHAIN_TRACE_BUNDLE_VERSION,
        "bundle_type": "default_off_advisory_chain_trace_ready_bundle",
        "trace_ready": True,
        "trace_persistence_enabled": False,
        "trace_store_write_enabled": False,
        "chain_run_id": chain_run_id,
        "agent_run_id": chain_run_id,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "ordered_agent_keys": list(workflow_manifest.get("ordered_agent_keys") or []),
        "run_snapshot": run_snapshot,
        "step_summaries": step_summaries,
        "stage_trace_bundle": stage_trace_bundle,
        "trace_summary": dict(stage_trace_bundle.get("trace_summary") or {}),
        "validation_safety_summary": {
            "harness_validation_status": _clean_text(dict(validation or {}).get("validation_status")),
            "harness_reason_codes": list(dict(validation or {}).get("reason_codes") or []),
            **_advisory_chain_safety_summary(),
        },
        "safety_metadata": _advisory_chain_safety_summary(),
    }


def build_default_off_advisory_agent_chain_harness(
    *,
    enabled: bool = False,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    created_at_utc: str = "",
    chain_run_id: str = "",
    manifest: Dict[str, Any] | None = None,
    contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    workflow_manifest = deepcopy(manifest) if manifest is not None else workflow_registry.get_agentic_workflow_manifest()
    adapter_contract = deepcopy(contract) if contract is not None else orchestrator_adapters.get_orchestrator_adapter_contract()
    specs_by_key = _adapter_specs_by_key(adapter_contract)
    agents_by_key = dict(workflow_manifest.get("agents") or {})
    ordered_keys = list(workflow_manifest.get("ordered_agent_keys") or [])
    chain_agents = [
        _build_advisory_chain_agent(
            index=index,
            agent=dict(agents_by_key.get(agent_key) or {}),
            spec=specs_by_key.get(_clean_text(agent_key), {}),
            enabled=enabled,
        )
        for index, agent_key in enumerate(ordered_keys, start=1)
    ]
    status_counts = Counter(agent.get("chain_status", "") for agent in chain_agents)
    observed_at = _clean_text(created_at_utc) or _utc_now_iso()
    resolved_chain_run_id = _clean_text(chain_run_id) or _deterministic_advisory_chain_run_id(
        workflow_manifest=workflow_manifest,
        ordered_keys=ordered_keys,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
    )
    payload = {
        "harness_version": ADVISORY_CHAIN_HARNESS_VERSION,
        "execution_mode": ADVISORY_CHAIN_EXECUTION_MODE,
        "workflow_name": _clean_text(workflow_manifest.get("workflow_name")),
        "workflow_version": _clean_text(workflow_manifest.get("workflow_version")),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "created_at_utc": observed_at,
        "chain_run_id": resolved_chain_run_id,
        "default_off": True,
        "enabled": bool(enabled),
        "explicit_invocation_required": True,
        "read_only": True,
        "advisory_only": True,
        "allow_agent_execution": False,
        "did_execute": False,
        "did_execute_chain": False,
        "did_mutate_production": False,
        "did_write_db": False,
        "mutation_allowed": False,
        "auto_apply_allowed": False,
        "ats_submission_allowed": False,
        "application_submission_allowed": False,
        "apply_click_allowed": False,
        "queue_mutation_allowed": False,
        "scoring_mutation_allowed": False,
        "ranking_mutation_allowed": False,
        "filtering_mutation_allowed": False,
        "tailoring_generation_allowed": False,
        "tailoring_mutation_allowed": False,
        "source_resume_mutation_allowed": False,
        "llm_provider_call_allowed": False,
        "live_provider_allowed": False,
        "scheduler_mutation_allowed": False,
        "workflow_runner_live_execution_allowed": False,
        "ordered_agent_keys": ordered_keys,
        "chain_agents": chain_agents,
        "summary": {
            "agent_count": len(chain_agents),
            "execution_enabled_count": sum(1 for agent in chain_agents if agent.get("execution_enabled")),
            "did_execute_count": sum(1 for agent in chain_agents if agent.get("did_execute")),
            "mutation_allowed_count": sum(1 for agent in chain_agents if agent.get("mutation_allowed")),
            "production_mutating_agent_count": sum(
                1 for agent in chain_agents if agent.get("mutates_production_decisions")
            ),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "safety_guarantees": [
            "Default-off advisory chain artifact only.",
            "No agents execute in this harness.",
            "No automatic job application submission, ATS submission, or apply clicking is allowed.",
            "No queue, ranking, scoring, filtering, tailoring, scheduler, or source resume mutation is allowed.",
            "workflow_runner.py remains dry-run only.",
        ],
    }
    payload["validation"] = validate_default_off_advisory_agent_chain_harness(
        payload,
        manifest=workflow_manifest,
    )
    payload["trace_ready_bundle"] = _build_advisory_chain_trace_ready_bundle(
        chain_run_id=resolved_chain_run_id,
        chain_agents=chain_agents,
        workflow_manifest=workflow_manifest,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        created_at_utc=observed_at,
        validation=payload["validation"],
    )
    payload["validation"] = validate_default_off_advisory_agent_chain_harness(
        payload,
        manifest=workflow_manifest,
    )
    return payload


def validate_default_off_advisory_agent_chain_harness(
    payload: Dict[str, Any],
    *,
    manifest: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    workflow_manifest = deepcopy(manifest) if manifest is not None else workflow_registry.get_agentic_workflow_manifest()
    expected_order = list(workflow_manifest.get("ordered_agent_keys") or [])
    chain_agents = list(payload.get("chain_agents") or [])
    actual_order = [_clean_text(agent.get("agent_key")) for agent in chain_agents]
    reason_codes: List[str] = []

    if _clean_text(payload.get("execution_mode")) != ADVISORY_CHAIN_EXECUTION_MODE:
        reason_codes.append("execution_mode_not_default_off_read_only_advisory_chain")
    if payload.get("default_off") is not True:
        reason_codes.append("default_off_not_true")
    if payload.get("explicit_invocation_required") is not True:
        reason_codes.append("explicit_invocation_required_not_true")
    if actual_order != expected_order:
        reason_codes.append("agent_order_mismatch")

    false_flags = list(ADVISORY_CHAIN_FALSE_FLAGS)
    for flag in false_flags:
        if payload.get(flag) is not False:
            reason_codes.append(f"{flag}_not_false")

    for agent in chain_agents:
        agent_key = _clean_text(agent.get("agent_key")) or "<unknown>"
        for flag in false_flags:
            if flag in agent and agent.get(flag) is not False:
                reason_codes.append(f"{agent_key}:{flag}_not_false")
        if agent.get("advisory_only") is not True:
            reason_codes.append(f"{agent_key}:advisory_only_not_true")
        if agent.get("read_only") is not True:
            reason_codes.append(f"{agent_key}:read_only_not_true")
        if agent.get("execution_enabled") is not False:
            reason_codes.append(f"{agent_key}:execution_enabled")
        if agent.get("did_execute") is not False:
            reason_codes.append(f"{agent_key}:did_execute")
        if agent.get("mutation_allowed") is not False:
            reason_codes.append(f"{agent_key}:mutation_allowed")
        if agent.get("mutates_production_decisions"):
            reason_codes.append(f"{agent_key}:mutates_production_decisions")
        if agent.get("llm_call_expected"):
            reason_codes.append(f"{agent_key}:llm_call_expected")
        if _clean_text(agent.get("allowed_execution_mode")) in orchestrator_adapters.LIVE_EXECUTION_MODES:
            reason_codes.append(f"{agent_key}:live_execution_mode")

    bundle = payload.get("trace_ready_bundle") if isinstance(payload, dict) else {}
    if bundle:
        if dict(bundle).get("trace_ready") is not True:
            reason_codes.append("trace_ready_bundle_not_trace_ready")
        if dict(bundle).get("trace_persistence_enabled") is not False:
            reason_codes.append("trace_persistence_enabled_not_false")
        if dict(bundle).get("trace_store_write_enabled") is not False:
            reason_codes.append("trace_store_write_enabled_not_false")
        if list(dict(bundle).get("ordered_agent_keys") or []) != expected_order:
            reason_codes.append("trace_ready_bundle_order_mismatch")
        step_summaries = list(dict(bundle).get("step_summaries") or [])
        if [_clean_text(step.get("step_name")) for step in step_summaries] != expected_order:
            reason_codes.append("trace_ready_bundle_step_order_mismatch")
        safety = dict(dict(bundle).get("validation_safety_summary") or {})
        for safety_flag, value in safety.items():
            if safety_flag.startswith("did_") and value is not False:
                reason_codes.append(f"trace_ready_bundle:{safety_flag}_not_false")
        trace_summary = dict(dict(bundle).get("trace_summary") or {})
        if trace_summary and trace_summary.get("all_required_fields_present") is not True:
            reason_codes.append("trace_ready_bundle_missing_required_trace_fields")

    return {
        "validation_status": "failed" if reason_codes else "passed",
        "reason_codes": sorted(set(reason_codes)),
        "expected_order": expected_order,
        "actual_order": actual_order,
        "agent_count": len(chain_agents),
    }


def invoke_read_only_advisory_chain(
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    created_at_utc: str = "",
    chain_run_id: str = "",
    manifest: Dict[str, Any] | None = None,
    contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    harness_result = build_default_off_advisory_agent_chain_harness(
        enabled=True,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        created_at_utc=created_at_utc,
        chain_run_id=chain_run_id,
        manifest=manifest,
        contract=contract,
    )
    trace_ready_result = dict(harness_result.get("trace_ready_bundle") or {})
    payload = {
        "adapter_version": ADVISORY_CHAIN_INVOCATION_ADAPTER_VERSION,
        "invocation_mode": ADVISORY_CHAIN_INVOCATION_MODE,
        "explicitly_invoked": True,
        "default_off": True,
        "read_only": True,
        "dry_run": True,
        "advisory_only": True,
        "pipeline_run_id": _clean_text(harness_result.get("pipeline_run_id")),
        "owner_user_id": _clean_text(harness_result.get("owner_user_id")),
        "chain_run_id": _clean_text(harness_result.get("chain_run_id")),
        "ordered_agent_keys": list(harness_result.get("ordered_agent_keys") or []),
        "trace_ready_advisory_result": trace_ready_result,
        "harness_result": harness_result,
        "summary": {
            "agent_count": int(dict(harness_result.get("summary") or {}).get("agent_count") or 0),
            "trace_ready": bool(trace_ready_result.get("trace_ready")),
            "step_count": int(dict(trace_ready_result.get("trace_summary") or {}).get("step_count") or 0),
            "did_invoke_adapter": True,
            "did_execute_agent_count": int(dict(harness_result.get("summary") or {}).get("did_execute_count") or 0),
            "mutation_allowed_count": int(dict(harness_result.get("summary") or {}).get("mutation_allowed_count") or 0),
            "production_mutating_agent_count": int(
                dict(harness_result.get("summary") or {}).get("production_mutating_agent_count") or 0
            ),
        },
        "trace_persistence_enabled": False,
        "trace_store_write_enabled": False,
        "did_call_trace_execution_helper": False,
        "did_call_workflow_runner": False,
        "did_call_live_workflow_runner": False,
        "did_call_llm": False,
        "did_call_live_provider": False,
        "did_change_pipeline": False,
        "did_change_queue": False,
        "did_change_scoring": False,
        "did_change_ranking": False,
        "did_change_filtering": False,
        "did_change_tailoring": False,
        "did_mutate_source_resume": False,
        "did_execute_scheduler": False,
        "did_click_apply": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "did_send_recruiter_message": False,
        "did_mark_applied": False,
    }
    for flag in ADVISORY_CHAIN_FALSE_FLAGS:
        payload[flag] = False
    payload["validation"] = validate_read_only_advisory_chain_invocation(payload)
    return payload


def validate_read_only_advisory_chain_invocation(payload: Dict[str, Any]) -> Dict[str, Any]:
    reason_codes: List[str] = []
    if _clean_text(payload.get("invocation_mode")) != ADVISORY_CHAIN_INVOCATION_MODE:
        reason_codes.append("invocation_mode_not_explicit_read_only")
    if payload.get("explicitly_invoked") is not True:
        reason_codes.append("explicitly_invoked_not_true")
    if payload.get("default_off") is not True:
        reason_codes.append("default_off_not_true")
    if payload.get("read_only") is not True:
        reason_codes.append("read_only_not_true")
    if payload.get("dry_run") is not True:
        reason_codes.append("dry_run_not_true")

    for flag in ADVISORY_CHAIN_FALSE_FLAGS:
        if payload.get(flag) is not False:
            reason_codes.append(f"{flag}_not_false")
    for flag in [
        "trace_persistence_enabled",
        "trace_store_write_enabled",
        "did_call_trace_execution_helper",
        "did_call_workflow_runner",
        "did_call_live_workflow_runner",
        "did_call_llm",
        "did_call_live_provider",
        "did_change_pipeline",
        "did_change_queue",
        "did_change_scoring",
        "did_change_ranking",
        "did_change_filtering",
        "did_change_tailoring",
        "did_mutate_source_resume",
        "did_execute_scheduler",
        "did_click_apply",
        "did_execute_application",
        "did_submit_application",
        "did_send_recruiter_message",
        "did_mark_applied",
    ]:
        if payload.get(flag) is not False:
            reason_codes.append(f"{flag}_not_false")

    harness_result = dict(payload.get("harness_result") or {})
    harness_validation = dict(harness_result.get("validation") or {})
    if _clean_text(harness_validation.get("validation_status")) != "passed":
        reason_codes.append("harness_validation_not_passed")

    trace_ready_result = dict(payload.get("trace_ready_advisory_result") or {})
    if trace_ready_result.get("trace_ready") is not True:
        reason_codes.append("trace_ready_advisory_result_not_trace_ready")
    if trace_ready_result.get("trace_store_write_enabled") is not False:
        reason_codes.append("trace_ready_advisory_result_trace_store_write_enabled")
    if list(trace_ready_result.get("ordered_agent_keys") or []) != list(payload.get("ordered_agent_keys") or []):
        reason_codes.append("trace_ready_advisory_result_order_mismatch")
    if int(dict(payload.get("summary") or {}).get("did_execute_agent_count") or 0) != 0:
        reason_codes.append("did_execute_agent_count_nonzero")
    if int(dict(payload.get("summary") or {}).get("mutation_allowed_count") or 0) != 0:
        reason_codes.append("mutation_allowed_count_nonzero")

    return {
        "validation_status": "failed" if reason_codes else "passed",
        "reason_codes": sorted(set(reason_codes)),
        "ordered_agent_keys": list(payload.get("ordered_agent_keys") or []),
    }


def _advisory_chain_bundle_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    source = dict(payload or {})
    if source.get("bundle_type") == "default_off_advisory_chain_trace_ready_bundle":
        return source
    if isinstance(source.get("trace_ready_advisory_result"), dict):
        return dict(source.get("trace_ready_advisory_result") or {})
    if isinstance(source.get("trace_ready_bundle"), dict):
        return dict(source.get("trace_ready_bundle") or {})
    return {}


def _advisory_chain_trace_context(
    *,
    bundle: Dict[str, Any],
    env: Dict[str, str],
    owner_user_id: str = "",
    pipeline_run_id: str = "",
    context_id: str = "",
) -> Dict[str, str]:
    run_snapshot = dict(bundle.get("run_snapshot") or {})
    owner = (
        _clean_text(owner_user_id)
        or _clean_text(bundle.get("owner_user_id"))
        or _clean_text(run_snapshot.get("owner_user_id"))
        or _clean_text(env.get("JOB_STACK_OWNER_USER_ID"))
    )
    pipeline = (
        _clean_text(pipeline_run_id)
        or _clean_text(bundle.get("pipeline_run_id"))
        or _clean_text(run_snapshot.get("pipeline_run_id"))
        or _clean_text(env.get("JOB_APP_PIPELINE_RUN_ID"))
        or _clean_text(env.get("JOB_STACK_USER_PIPELINE_RUN_ID"))
    )
    context = (
        _clean_text(context_id)
        or _clean_text(env.get("APPLYLENS_AGENT_CONTEXT_ID"))
        or _clean_text(run_snapshot.get("context_id"))
    )
    return {
        "owner_user_id": owner,
        "pipeline_run_id": pipeline,
        "context_id": context,
    }


def _with_advisory_chain_trace_context(
    *,
    bundle: Dict[str, Any],
    context: Dict[str, str],
) -> Dict[str, Any]:
    run_snapshot = dict(bundle.get("run_snapshot") or {})
    run_snapshot.update(context)
    step_summaries = []
    for step in list(bundle.get("step_summaries") or []):
        step_copy = dict(step)
        step_copy.update(context)
        step_copy["agent_run_id"] = _clean_text(run_snapshot.get("agent_run_id"))
        step_summaries.append(step_copy)
    return {
        "run_snapshot": run_snapshot,
        "step_summaries": step_summaries,
    }


def _build_advisory_chain_trace_recording_payload(
    *,
    run_snapshot: Dict[str, Any],
    step_summaries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    run_payload = agent_trace_store.create_agent_run_postgres_payload(
        record=run_snapshot,
        print_only=True,
        ensure_schema=False,
    )
    step_payloads = [
        agent_trace_store.record_agent_step_postgres_payload(
            record=step,
            print_only=True,
            ensure_schema=False,
        )
        for step in step_summaries
    ]
    records = [
        {
            "record_type": "agent_run",
            "table": "agent_runs",
            "sql": run_payload.get("sql", ""),
            "params": (),
            "snapshot": dict(run_payload.get("run") or {}),
        },
        *[
            {
                "record_type": "agent_step",
                "table": "agent_steps",
                "sql": payload.get("sql", ""),
                "params": (),
                "snapshot": dict(payload.get("step") or {}),
            }
            for payload in step_payloads
        ],
    ]
    return {
        "operation": "build_controlled_advisory_chain_trace_recording_payload",
        "run_count": 1,
        "step_count": len(step_payloads),
        "record_count": len(records),
        "records": records,
    }


def _execute_advisory_chain_trace_recording(
    recording_payload: Dict[str, Any],
    *,
    cursor: Any | None = None,
    execute_callback: Any | None = None,
) -> Dict[str, Any]:
    executed_operations: List[Dict[str, Any]] = []
    for record in list(recording_payload.get("records") or []):
        operation = {
            "record_type": _clean_text(dict(record).get("record_type")),
            "table": _clean_text(dict(record).get("table")),
            "sql": _clean_text(dict(record).get("sql")),
            "params": tuple(dict(record).get("params") or ()),
        }
        if cursor is not None:
            cursor.execute(operation["sql"], operation["params"])
        else:
            execute_callback(deepcopy(operation))
        executed_operations.append(
            {
                "record_type": operation["record_type"],
                "table": operation["table"],
            }
        )
    return {
        "operation": "execute_controlled_advisory_chain_trace_recording",
        "executed_record_count": len(executed_operations),
        "executed_operations": executed_operations,
    }


def persist_read_only_advisory_chain_trace(
    *,
    advisory_result: Dict[str, Any] | None = None,
    trace_ready_bundle: Dict[str, Any] | None = None,
    owner_user_id: str = "",
    pipeline_run_id: str = "",
    context_id: str = "",
    env: Dict[str, str] | None = None,
    cursor: Any | None = None,
    execute_callback: Any | None = None,
    trace_module: Any = trace,
) -> Dict[str, Any]:
    env_map = env if env is not None else os.environ
    base_result = {
        "persistence_version": ADVISORY_CHAIN_TRACE_PERSISTENCE_VERSION,
        "attempted": False,
        "recorded": False,
        "record_count": 0,
        "run_count": 0,
        "step_count": 0,
        "trace_persistence_enabled": False,
        "trace_store_write_enabled": False,
        "did_prepare_trace_recording_payload": False,
        "did_call_trace_execution_helper": False,
        "did_write_database": False,
        "did_call_llm": False,
        "did_call_live_provider": False,
        "did_change_pipeline": False,
        "did_change_queue": False,
        "did_change_scoring": False,
        "did_change_ranking": False,
        "did_change_filtering": False,
        "did_change_tailoring": False,
        "did_mutate_source_resume": False,
        "did_execute_scheduler": False,
        "did_click_apply": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "did_send_recruiter_message": False,
        "did_mark_applied": False,
    }
    for flag in ADVISORY_CHAIN_FALSE_FLAGS:
        base_result[flag] = False

    if not _truthy(env_map.get("APPLYLENS_AGENT_TRACE_ENABLED")):
        return {**base_result, "reason": "trace_disabled"}

    source_payload = dict(trace_ready_bundle or {}) if trace_ready_bundle is not None else dict(advisory_result or {})
    bundle = _advisory_chain_bundle_from_payload(source_payload)
    context = _advisory_chain_trace_context(
        bundle=bundle,
        env=env_map,
        owner_user_id=owner_user_id,
        pipeline_run_id=pipeline_run_id,
        context_id=context_id,
    )
    if not context["owner_user_id"] or not context["pipeline_run_id"] or not context["context_id"]:
        return {
            **base_result,
            "reason": "missing_trace_context",
            **context,
        }

    if not bundle:
        return {
            **base_result,
            "reason": "missing_trace_ready_bundle",
            **context,
        }

    if (cursor is None) == (execute_callback is None):
        return {
            **base_result,
            "reason": "write_executor_missing",
            **context,
        }

    strict = _truthy(env_map.get("APPLYLENS_AGENT_TRACE_STRICT"))
    try:
        shaped = _with_advisory_chain_trace_context(bundle=bundle, context=context)
        recording_payload = _build_advisory_chain_trace_recording_payload(
            run_snapshot=shaped["run_snapshot"],
            step_summaries=shaped["step_summaries"],
        )
        execution_result = _execute_advisory_chain_trace_recording(
            recording_payload,
            cursor=cursor,
            execute_callback=execute_callback,
        )
        return {
            **base_result,
            "attempted": True,
            "recorded": True,
            "reason": "",
            "record_count": int(recording_payload.get("record_count") or 0),
            "run_count": int(recording_payload.get("run_count") or 0),
            "step_count": int(recording_payload.get("step_count") or 0),
            "trace_persistence_enabled": True,
            "trace_store_write_enabled": True,
            "did_prepare_trace_recording_payload": True,
            "did_call_trace_execution_helper": True,
            "did_write_database": True,
            "recording_payload": recording_payload,
            "execution_result": execution_result,
            **context,
        }
    except Exception as exc:
        if strict:
            raise
        return {
            **base_result,
            "attempted": True,
            "recorded": False,
            "reason": "trace_persistence_failed",
            "warning": str(exc),
            **context,
        }


def _advisory_chain_readback_empty_result() -> Dict[str, Any]:
    safety_flags = {flag: False for flag in ADVISORY_CHAIN_READBACK_SAFETY_FLAGS}
    return {
        "compatibility_version": ADVISORY_CHAIN_TRACE_READBACK_COMPATIBILITY_VERSION,
        "compatible": False,
        "read_only": True,
        "db_reads_performed": False,
        "db_writes_performed": False,
        "api_changed": False,
        "ui_changed": False,
        "pipeline_changed": False,
        "run_count": 0,
        "step_count": 0,
        "expected_agent_order": list(workflow_registry.ORDERED_AGENT_KEYS),
        "observed_agent_order": [],
        "missing_agents": list(workflow_registry.ORDERED_AGENT_KEYS),
        "unexpected_agents": [],
        "duplicate_agents": [],
        "reason_codes": [],
        "safety_flags_summary": safety_flags,
        "unsafe_safety_flags": [],
        "did_call_llm": False,
        "did_call_live_provider": False,
        "did_call_workflow_runner": False,
        "did_call_live_workflow_runner": False,
        "did_change_queue": False,
        "did_change_scoring": False,
        "did_change_ranking": False,
        "did_change_filtering": False,
        "did_change_tailoring": False,
        "did_mutate_source_resume": False,
        "did_execute_scheduler": False,
        "did_click_apply": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "did_send_recruiter_message": False,
        "did_mark_applied": False,
    }


def _advisory_chain_readback_agent_key(value: Any) -> str:
    text = _clean_text(value).lower()
    if not text:
        return ""
    normalized = (
        text.replace("-", "_")
        .replace("/", "_")
        .replace(" ", "_")
        .replace("__", "_")
        .strip("_")
    )
    aliases = {
        "source_health_agent": "source_health",
        "resume_match_agent": "resume_match",
        "critic_agent": "critic",
        "job_prioritization_agent": "job_prioritization",
        "tailoring_decision_agent": "tailoring_decision",
        "operator_review_agent": "operator_review",
    }
    return aliases.get(normalized, normalized)


def _advisory_chain_readback_step_key(step: Dict[str, Any]) -> str:
    for field in ("step_name", "agent_key", "agent_name"):
        key = _advisory_chain_readback_agent_key(step.get(field))
        if key:
            return key
    return ""


def _advisory_chain_readback_steps(agent_runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    for run in agent_runs:
        for step in list(dict(run).get("steps") or []):
            if isinstance(step, dict):
                steps.append(dict(step))
    return steps


def _advisory_chain_readback_metadata_values(
    *,
    agent_runs: List[Dict[str, Any]],
    steps: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    values: List[Dict[str, Any]] = []
    for run in agent_runs:
        summary = dict(run).get("summary_json")
        if isinstance(summary, dict):
            values.append(dict(summary))
    for step in steps:
        for field in ("validation_json", "output_json", "input_json"):
            value = dict(step).get(field)
            if isinstance(value, dict):
                values.append(dict(value))
                safety_flags = value.get("safety_flags")
                if isinstance(safety_flags, dict):
                    values.append(dict(safety_flags))
    return values


def build_advisory_chain_trace_readback_compatibility(
    agent_trace_payload: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Validate an existing generic agent_trace_payload result for advisory-chain readback.

    The helper is intentionally in-memory only. It does not call services,
    storage, trace persistence, providers, workflow runners, API routes, or UI code.
    """

    payload = dict(agent_trace_payload or {})
    result = _advisory_chain_readback_empty_result()
    reason_codes: List[str] = []
    expected_order = list(workflow_registry.ORDERED_AGENT_KEYS)
    agent_runs = [
        dict(run)
        for run in list(payload.get("agent_runs") or [])
        if isinstance(run, dict)
    ]
    steps = _advisory_chain_readback_steps(agent_runs)
    observed_order = [_advisory_chain_readback_step_key(step) for step in steps]
    observed_order = [key for key in observed_order if key]
    observed_counts = Counter(observed_order)
    unexpected_agents = sorted(key for key in observed_counts if key not in expected_order)
    missing_agents = [key for key in expected_order if observed_counts.get(key, 0) == 0]
    duplicate_agents = sorted(key for key, count in observed_counts.items() if count > 1)

    if not agent_runs:
        reason_codes.append("missing_advisory_chain_run")
    if len(agent_runs) != 1:
        reason_codes.append("advisory_chain_run_count_not_one")
    if len(steps) != len(expected_order):
        reason_codes.append("advisory_chain_step_count_mismatch")
    if observed_order != expected_order:
        reason_codes.append("advisory_chain_agent_order_mismatch")
    if missing_agents:
        reason_codes.append("advisory_chain_agents_missing")
    if unexpected_agents:
        reason_codes.append("advisory_chain_agents_unexpected")
    if duplicate_agents:
        reason_codes.append("advisory_chain_agents_duplicated")

    safety_summary = {flag: False for flag in ADVISORY_CHAIN_READBACK_SAFETY_FLAGS}
    metadata_values = _advisory_chain_readback_metadata_values(
        agent_runs=agent_runs,
        steps=steps,
    )
    for metadata in metadata_values:
        for flag in ADVISORY_CHAIN_READBACK_SAFETY_FLAGS:
            if metadata.get(flag) is True:
                safety_summary[flag] = True
    unsafe_flags = sorted(flag for flag, value in safety_summary.items() if value is True)
    if unsafe_flags:
        reason_codes.append("advisory_chain_unsafe_safety_flags_present")

    result.update(
        {
            "compatible": not reason_codes,
            "run_count": len(agent_runs),
            "step_count": len(steps),
            "observed_agent_order": observed_order,
            "missing_agents": missing_agents,
            "unexpected_agents": unexpected_agents,
            "duplicate_agents": duplicate_agents,
            "reason_codes": sorted(set(reason_codes)),
            "safety_flags_summary": safety_summary,
            "unsafe_safety_flags": unsafe_flags,
        }
    )
    return result


def _expected_fixture_status(expected_validation: Dict[str, Any]) -> str:
    status = _clean_text(expected_validation.get("validation_status"))
    if status:
        return status
    if expected_validation.get("should_be_valid_fixture") is True:
        return "passed"
    return "failed"


def _expected_fixture_reason_codes(expected_validation: Dict[str, Any]) -> List[str]:
    reason_codes = expected_validation.get("reason_codes")
    if reason_codes is None:
        reason_codes = expected_validation.get("expected_reason_codes")
    return sorted(_clean_text(item) for item in list(reason_codes or []) if _clean_text(item))


def _load_fixture_payload(fixture_path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _build_fixture_validation_preflight_summary(
    fixture_dir: Path = APPROVED_FIXTURE_DIR,
    fixture_filenames: tuple[str, ...] = APPROVED_FIXTURE_FILENAMES,
) -> Dict[str, Any]:
    expected_filenames = sorted(fixture_filenames)
    existing_filenames = sorted(path.name for path in fixture_dir.iterdir()) if fixture_dir.is_dir() else []
    unexpected_filenames = [
        name for name in existing_filenames if name != ".gitkeep" and name not in expected_filenames
    ]
    missing_filenames = [name for name in expected_filenames if name not in existing_filenames]

    results: List[Dict[str, Any]] = []
    failed_fixture_ids: List[str] = []
    observed_reason_codes: List[str] = []

    for filename in expected_filenames:
        fixture_path = fixture_dir / filename
        payload = _load_fixture_payload(fixture_path)
        expected_validation = payload.get("expected_validation") if isinstance(payload, dict) else {}
        if not isinstance(expected_validation, dict):
            expected_validation = {}

        actual_result = fixture_validator.validate_fixture_file(fixture_path)
        expected_status = _expected_fixture_status(expected_validation)
        expected_reason_codes = _expected_fixture_reason_codes(expected_validation)
        actual_reason_codes = sorted(
            _clean_text(item)
            for item in list(actual_result.get("reason_codes") or [])
            if _clean_text(item)
        )
        expected_flags = {
            "did_execute_fixture": expected_validation.get("did_execute_fixture") is False,
            "did_mutate_production": expected_validation.get("did_mutate_production") is False,
            "did_write_db": expected_validation.get("did_write_db") is False,
        }
        actual_flags = {
            "did_execute_fixture": actual_result.get("did_execute_fixture") is False,
            "did_mutate_production": actual_result.get("did_mutate_production") is False,
            "did_write_db": actual_result.get("did_write_db") is False,
        }
        missing_expected_reason_codes = [
            reason_code
            for reason_code in expected_reason_codes
            if reason_code not in actual_reason_codes
        ]
        matches_expected = (
            fixture_path.is_file()
            and _clean_text(actual_result.get("validation_status")) == expected_status
            and not missing_expected_reason_codes
            and all(expected_flags.values())
            and all(actual_flags.values())
        )
        fixture_id = _clean_text(payload.get("fixture_id")) or filename
        if not matches_expected:
            failed_fixture_ids.append(fixture_id)

        observed_reason_codes.extend(actual_reason_codes)
        results.append(
            {
                "fixture_filename": filename,
                "fixture_path": str(fixture_path.relative_to(REPO_ROOT)),
                "fixture_exists": fixture_path.is_file(),
                "fixture_id": fixture_id,
                "fixture_family": _clean_text(payload.get("fixture_family")),
                "expected_validation_status": expected_status,
                "actual_validation_status": _clean_text(actual_result.get("validation_status")),
                "expected_reason_codes": expected_reason_codes,
                "actual_reason_codes": actual_reason_codes,
                "missing_expected_reason_codes": missing_expected_reason_codes,
                "expected_matches_actual": matches_expected,
                "did_execute_fixture": bool(actual_result.get("did_execute_fixture")),
                "did_mutate_production": bool(actual_result.get("did_mutate_production")),
                "did_write_db": bool(actual_result.get("did_write_db")),
            }
        )

    reason_codes = sorted(set(observed_reason_codes))
    if unexpected_filenames:
        reason_codes.append("unexpected_fixture_file")
        failed_fixture_ids.extend(unexpected_filenames)
    if missing_filenames:
        reason_codes.append("missing_fixture_file")
        failed_fixture_ids.extend(missing_filenames)

    fixture_validation_passed = not failed_fixture_ids
    return {
        "fixture_validation_enabled": True,
        "fixture_validation_status": "passed" if fixture_validation_passed else "failed",
        "fixture_validation_passed": fixture_validation_passed,
        "fixture_validation_checked_count": len(results),
        "fixture_validation_expected_fixture_count": len(expected_filenames),
        "fixture_validation_results": results,
        "fixture_validation_failed_fixture_ids": sorted(set(failed_fixture_ids)),
        "fixture_validation_reason_codes": sorted(set(reason_codes)),
        "fixture_validation_approved_fixture_filenames": expected_filenames,
        "fixture_validation_unexpected_fixture_filenames": unexpected_filenames,
        "fixture_validation_missing_fixture_filenames": missing_filenames,
    }


def _build_preflight_result(
    *,
    step: Dict[str, Any],
    spec: Dict[str, Any],
    artifact_root: str | Path | None = None,
) -> Dict[str, Any]:
    required_artifacts = list(spec.get("required_artifacts") or [])
    presence = _artifact_presence(artifact_root, required_artifacts)
    result = {
        "step_index": int(step.get("step_index") or 0),
        "agent_key": _clean_text(step.get("agent_key")),
        "agent_name": _clean_text(step.get("agent_name")),
        "owner_module": _clean_text(spec.get("owner_module") or step.get("owner_module")),
        "adapter_status": _clean_text(spec.get("adapter_status")),
        "allowed_execution_mode": _clean_text(spec.get("allowed_execution_mode")),
        "would_call_entrypoints": [
            _clean_text(item)
            for item in list(spec.get("callable_entrypoint_names") or [])
            if _clean_text(item)
        ],
        "required_artifacts": required_artifacts,
        "produced_artifacts": list(spec.get("produced_artifacts") or []),
        "input_loader_required": bool(spec.get("input_loader_required")),
        "output_validator_required": bool(spec.get("output_validator_required")),
        "artifact_writer_available": bool(spec.get("artifact_writer_available")),
        "trace_supported": bool(spec.get("trace_supported")),
        "db_access_required": bool(spec.get("db_access_required")),
        "env_context_required": bool(spec.get("env_context_required")),
        "llm_call_expected": bool(spec.get("llm_call_expected")),
        "mutates_production_decisions": bool(spec.get("mutates_production_decisions")),
        "preflight_status": _preflight_status(spec),
        "execution_enabled": False,
        "did_execute": False,
    }
    if presence:
        result["artifact_presence"] = presence
    result["reason_codes"] = _reason_codes_for_result(spec, presence)
    return result


def build_read_only_adapter_preflight_plan(
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    artifact_root: str | Path | None = None,
    created_at_utc: str = "",
    manifest: Dict[str, Any] | None = None,
    contract: Dict[str, Any] | None = None,
    execution_plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    workflow_manifest = deepcopy(manifest) if manifest is not None else workflow_registry.get_agentic_workflow_manifest()
    adapter_contract = deepcopy(contract) if contract is not None else orchestrator_adapters.get_orchestrator_adapter_contract()
    planner_payload = (
        deepcopy(execution_plan)
        if execution_plan is not None
        else workflow_planner.build_agentic_workflow_execution_plan(workflow_manifest)
    )
    specs_by_key = _adapter_specs_by_key(adapter_contract)
    context = build_read_only_adapter_harness_context(
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        artifact_root=artifact_root,
        created_at_utc=created_at_utc,
        manifest=workflow_manifest,
        contract=adapter_contract,
    )
    results = [
        _build_preflight_result(
            step=step,
            spec=specs_by_key.get(_clean_text(step.get("agent_key")), {}),
            artifact_root=artifact_root,
        )
        for step in list(planner_payload.get("ordered_steps") or [])
    ]
    status_counts = Counter(result.get("preflight_status", "") for result in results)
    missing_required_artifact_count = sum(
        1
        for result in results
        for artifact in dict(result.get("artifact_presence") or {}).values()
        if not bool(artifact.get("exists"))
    )
    fixture_validation = _build_fixture_validation_preflight_summary()
    plan = {
        "harness_version": HARNESS_VERSION,
        "execution_mode": EXECUTION_MODE,
        "workflow_name": _clean_text(workflow_manifest.get("workflow_name")),
        "workflow_version": _clean_text(workflow_manifest.get("workflow_version")),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "allow_agent_execution": False,
        "planned_adapter_count": len(results),
        "executable_adapter_count": 0,
        "did_execute_live": False,
        "did_mutate_production": False,
        "did_write_db": False,
        "fixture_validation": fixture_validation,
        "fixture_validation_enabled": fixture_validation["fixture_validation_enabled"],
        "fixture_validation_status": fixture_validation["fixture_validation_status"],
        "fixture_validation_passed": fixture_validation["fixture_validation_passed"],
        "fixture_validation_checked_count": fixture_validation[
            "fixture_validation_checked_count"
        ],
        "fixture_validation_expected_fixture_count": fixture_validation[
            "fixture_validation_expected_fixture_count"
        ],
        "fixture_validation_results": fixture_validation["fixture_validation_results"],
        "fixture_validation_failed_fixture_ids": fixture_validation[
            "fixture_validation_failed_fixture_ids"
        ],
        "fixture_validation_reason_codes": fixture_validation[
            "fixture_validation_reason_codes"
        ],
        "adapter_preflight_results": results,
        "context": context,
        "summary": {
            "status_counts": dict(sorted(status_counts.items())),
            "ready_read_only_contract_count": int(status_counts.get("ready_read_only_contract", 0)),
            "needs_adapter_count": int(status_counts.get("needs_adapter", 0)),
            "blocked_count": int(status_counts.get("blocked", 0)),
            "execution_enabled_count": sum(1 for result in results if result.get("execution_enabled")),
            "did_execute_count": sum(1 for result in results if result.get("did_execute")),
            "missing_required_artifact_count": missing_required_artifact_count,
        },
    }
    plan["validation"] = validate_read_only_adapter_preflight_plan(plan, manifest=workflow_manifest)
    return plan


def validate_read_only_adapter_preflight_plan(
    plan: Dict[str, Any],
    *,
    manifest: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    workflow_manifest = deepcopy(manifest) if manifest is not None else workflow_registry.get_agentic_workflow_manifest()
    expected_order = list(workflow_manifest.get("ordered_agent_keys") or [])
    results = list(plan.get("adapter_preflight_results") or [])
    actual_order = [_clean_text(result.get("agent_key")) for result in results]
    reason_codes: List[str] = []
    warning_codes: List[str] = []

    if _clean_text(plan.get("execution_mode")) != EXECUTION_MODE:
        reason_codes.append("execution_mode_not_read_only_preflight")
    if bool(plan.get("allow_agent_execution")):
        reason_codes.append("allow_agent_execution_true")
    if int(plan.get("executable_adapter_count") or 0) != 0:
        reason_codes.append("executable_adapter_count_nonzero")
    if bool(plan.get("did_execute_live")):
        reason_codes.append("did_execute_live_true")
    if bool(plan.get("did_mutate_production")):
        reason_codes.append("did_mutate_production_true")
    if bool(plan.get("did_write_db")):
        reason_codes.append("did_write_db_true")
    if plan.get("fixture_validation") and not bool(plan.get("fixture_validation_passed")):
        reason_codes.append("fixture_validation_failed")
    if actual_order != expected_order:
        reason_codes.append("adapter_order_mismatch")

    for result in results:
        agent_key = _clean_text(result.get("agent_key")) or "<unknown>"
        if bool(result.get("execution_enabled")):
            reason_codes.append(f"{agent_key}:execution_enabled")
        if bool(result.get("did_execute")):
            reason_codes.append(f"{agent_key}:did_execute")
        if bool(result.get("mutates_production_decisions")):
            reason_codes.append(f"{agent_key}:mutates_production_decisions")
        if bool(result.get("llm_call_expected")):
            reason_codes.append(f"{agent_key}:llm_call_expected")
        if _clean_text(result.get("allowed_execution_mode")) in orchestrator_adapters.LIVE_EXECUTION_MODES:
            reason_codes.append(f"{agent_key}:live_execution_mode")
        if not list(result.get("reason_codes") or []):
            reason_codes.append(f"{agent_key}:missing_reason_codes")
        if _clean_text(result.get("preflight_status")) not in {
            "ready_read_only_contract",
            "needs_adapter",
            "blocked",
        }:
            reason_codes.append(f"{agent_key}:unknown_preflight_status")
        missing_artifacts = [
            artifact
            for artifact, presence in dict(result.get("artifact_presence") or {}).items()
            if not bool(dict(presence).get("exists"))
        ]
        if missing_artifacts:
            warning_codes.append(f"{agent_key}:missing_required_artifacts")

    missing_results = [key for key in expected_order if key not in actual_order]
    if missing_results:
        reason_codes.append("missing_adapter_preflight_results")

    unique_reasons = sorted(set(reason_codes))
    unique_warnings = sorted(set(warning_codes))
    if unique_reasons:
        status = "failed"
    elif unique_warnings:
        status = "warning"
    else:
        status = "passed"
    return {
        "validation_status": status,
        "reason_codes": unique_reasons,
        "warning_codes": unique_warnings,
        "expected_order": expected_order,
        "actual_order": actual_order,
        "planned_adapter_count": len(results),
        "execution_mode": _clean_text(plan.get("execution_mode")),
    }


def render_read_only_adapter_preflight_markdown(
    plan: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(plan) if plan is not None else build_read_only_adapter_preflight_plan()
    validation = dict(payload.get("validation") or validate_read_only_adapter_preflight_plan(payload))
    lines = [
        "# Read-Only Adapter Preflight",
        "",
        "Preflight-only warning: this harness does not execute agents, enable autonomous execution,",
        "call LLMs, wire into live planning, or change production behavior.",
        "",
        f"Workflow: `{_clean_text(payload.get('workflow_name'))}`",
        f"Workflow version: `{_clean_text(payload.get('workflow_version'))}`",
        f"Harness version: `{_clean_text(payload.get('harness_version'))}`",
        f"Execution mode: `{_clean_text(payload.get('execution_mode'))}`",
        f"Allow agent execution: `{bool(payload.get('allow_agent_execution'))}`",
        f"Executable adapter count: `{int(payload.get('executable_adapter_count') or 0)}`",
        f"Fixture validation: `{_clean_text(payload.get('fixture_validation_status'))}`",
        f"Fixture validation checked count: `{int(payload.get('fixture_validation_checked_count') or 0)}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Adapter Results",
        "",
    ]
    for result in list(payload.get("adapter_preflight_results") or []):
        lines.extend(
            [
                f"### {result.get('step_index')}. {result.get('agent_name', '')}",
                "",
                f"- Agent key: `{_clean_text(result.get('agent_key'))}`",
                f"- Owner module: `{_clean_text(result.get('owner_module'))}`",
                f"- Adapter status: `{_clean_text(result.get('adapter_status'))}`",
                f"- Preflight status: `{_clean_text(result.get('preflight_status'))}`",
                f"- Execution enabled: `{bool(result.get('execution_enabled'))}`",
                f"- Did execute: `{bool(result.get('did_execute'))}`",
                f"- Mutates production decisions: `{bool(result.get('mutates_production_decisions'))}`",
                f"- LLM call expected: `{bool(result.get('llm_call_expected'))}`",
                f"- Reasons: {', '.join(f'`{item}`' for item in list(result.get('reason_codes') or [])) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def write_read_only_adapter_preflight_artifacts(
    *,
    output_dir: str | Path,
    plan_json_path: str | Path | None = None,
    report_md_path: str | Path | None = None,
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    root = Path(output_dir)
    json_path = Path(plan_json_path) if plan_json_path else root / PREFLIGHT_JSON_NAME
    md_path = Path(report_md_path) if report_md_path else root / PREFLIGHT_MD_NAME
    payload = deepcopy(plan) if plan is not None else build_read_only_adapter_preflight_plan()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_read_only_adapter_preflight_markdown(payload), encoding="utf-8")
    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "payload": payload,
        "validation_status": payload.get("validation", {}).get("validation_status", ""),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only adapter preflight plan.")
    parser.add_argument("--preflight", action="store_true", help="Generate preflight metadata without executing agents.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--pipeline-run-id", default="", help="Optional pipeline run id for the preflight context.")
    parser.add_argument("--owner-user-id", default="", help="Optional owner user id for the preflight context.")
    parser.add_argument("--artifact-root", default="", help="Optional artifact root to inspect for artifact presence.")
    args = parser.parse_args(argv)

    if not args.preflight:
        parser.error("Only --preflight mode is supported.")

    payload = build_read_only_adapter_preflight_plan(
        pipeline_run_id=args.pipeline_run_id,
        owner_user_id=args.owner_user_id,
        artifact_root=args.artifact_root,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        validation = dict(payload.get("validation") or {})
        print(f"Read-only adapter preflight: {validation.get('validation_status', '')}")
        print(f"Planned adapters: {payload.get('planned_adapter_count', 0)}")
        print(f"Executable adapters: {payload.get('executable_adapter_count', 0)}")
    return 0 if payload.get("validation", {}).get("validation_status") in {"passed", "warning"} else 1


if __name__ == "__main__":
    sys.exit(main())
