from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Dict, List

from src.agents import (
    critic_agent,
    job_prioritization_agent,
    operator_review_agent,
    resume_match_agent,
    source_health_agent,
    tailoring_decision_agent,
)


WORKFLOW_NAME = "ApplyLens Agentic Workflow"
WORKFLOW_VERSION = "agentic_workflow_manifest_v1"
MANIFEST_JSON_NAME = "agentic_workflow_manifest.json"
MANIFEST_MD_NAME = "agentic_workflow_manifest.md"

REQUIRED_FEATURE_FLAGS = [
    "APPLYLENS_AGENT_TRACE_ENABLED",
    "APPLYLENS_AGENT_TRACE_STRICT",
    "APPLYLENS_CRITIC_ADVISORY_ENABLED",
    "APPLYLENS_WORKFLOW_VERIFIER_STRICT",
]

ORDERED_AGENT_KEYS = [
    "source_health",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]

GENERATED_ARTIFACT_KINDS = [
    "source_health_report",
    "best_resume_variant_by_job",
    "application_shortlist_by_job",
    "application_execution_queue",
    "job_prioritization_recommendations",
    "job_prioritization_summary",
    "tailoring_decision_recommendations",
    "tailoring_decision_summary",
    "operator_review_recommendations",
    "operator_review_summary",
    "agentic_workflow_summary_json",
    "agentic_workflow_summary_md",
    "agentic_workflow_manifest_json",
    "agentic_workflow_manifest_md",
    "agentic_workflow_execution_plan_json",
    "agentic_workflow_execution_plan_md",
    "agentic_workflow_dry_run_result_json",
    "agentic_workflow_dry_run_report_md",
    "agentic_workflow_verification_json",
    "job_packet_manifest",
]

EXPECTED_AGENTIC_ARTIFACT_KINDS = [
    "source_health_report",
    "job_prioritization_recommendations",
    "tailoring_decision_recommendations",
    "tailoring_decision_summary",
    "operator_review_recommendations",
    "operator_review_summary",
    "agentic_workflow_summary_json",
    "agentic_workflow_summary_md",
    "agentic_workflow_manifest_json",
    "agentic_workflow_manifest_md",
    "agentic_workflow_execution_plan_json",
    "agentic_workflow_execution_plan_md",
    "agentic_workflow_dry_run_result_json",
    "agentic_workflow_dry_run_report_md",
    "agentic_workflow_verification_json",
]

ARTIFACT_DEPENDENCY_ORDER = [
    "source_health_report.csv",
    "best_resume_variant_by_job.csv",
    "application_shortlist_by_job.csv",
    "application_execution_queue.csv",
    "job_prioritization_recommendations.csv",
    "job_prioritization_summary.json",
    "tailoring_decision_recommendations.csv",
    "tailoring_decision_summary.json",
    "operator_review_recommendations.csv",
    "operator_review_summary.json",
    "agentic_workflow_summary.json",
    "agentic_workflow_summary.md",
    "agentic_workflow_manifest.json",
    "agentic_workflow_manifest.md",
    "agentic_workflow_execution_plan.json",
    "agentic_workflow_execution_plan.md",
    "agentic_workflow_dry_run_result.json",
    "agentic_workflow_dry_run_report.md",
    "agentic_workflow_verification.json",
]

SAFETY_GUARANTEES = [
    "No advisory agent overwrites production action.",
    "No advisory agent mutates queue priority or job ordering.",
    "No advisory agent mutates packet generation.",
    "No advisory agent changes tailoring generation.",
    "No advisory agent generates resume text.",
    "Trace recording is disabled by default.",
    "Workflow verification is diagnostic unless strict mode is explicitly enabled.",
]


AGENT_MANIFESTS: Dict[str, Dict[str, Any]] = {
    "source_health": {
        "agent_key": "source_health",
        "agent_name": source_health_agent.AGENT_NAME,
        "agent_version": source_health_agent.AGENT_VERSION,
        "model_provider": "deterministic",
        "model_name": "source_health_rules",
        "phase": "2B",
        "advisory_only": True,
        "diagnostic_only": False,
        "trace_enabled_by_default": False,
        "mutates_production_decisions": False,
        "input_artifacts": ["source_health_report.csv"],
        "output_artifacts": ["source_health_report.csv"],
        "required_feature_flags": ["APPLYLENS_AGENT_TRACE_ENABLED"],
        "benchmark_metric_keys": ["source_health_recommendation_accuracy"],
        "owner_module": "src.agents.source_health_agent",
    },
    "resume_match": {
        "agent_key": "resume_match",
        "agent_name": resume_match_agent.AGENT_NAME,
        "agent_version": resume_match_agent.AGENT_VERSION,
        "model_provider": "deterministic",
        "model_name": "resume_match_rules",
        "phase": "2A",
        "advisory_only": True,
        "diagnostic_only": False,
        "trace_enabled_by_default": False,
        "mutates_production_decisions": False,
        "input_artifacts": ["best_resume_variant_by_job.csv"],
        "output_artifacts": ["best_resume_variant_by_job.csv"],
        "required_feature_flags": ["APPLYLENS_AGENT_TRACE_ENABLED"],
        "benchmark_metric_keys": [
            "fallback_only_block_rate",
            "deterministic_match_allow_rate",
            "low_confidence_block_rate",
        ],
        "owner_module": "src.agents.resume_match_agent",
    },
    "critic": {
        "agent_key": "critic",
        "agent_name": critic_agent.AGENT_NAME,
        "agent_version": critic_agent.AGENT_VERSION,
        "model_provider": "deterministic",
        "model_name": "critic_rules",
        "phase": "5A",
        "advisory_only": True,
        "diagnostic_only": False,
        "trace_enabled_by_default": False,
        "mutates_production_decisions": False,
        "input_artifacts": ["scan suggestions"],
        "output_artifacts": ["critic advisory metadata"],
        "required_feature_flags": [
            "APPLYLENS_CRITIC_ADVISORY_ENABLED",
            "APPLYLENS_AGENT_TRACE_ENABLED",
        ],
        "benchmark_metric_keys": [
            "critic_unsupported_claim_rejection_rate",
            "critic_safe_suggestion_approval_rate",
            "critic_downgrade_rate",
        ],
        "owner_module": "src.agents.critic_agent",
    },
    "job_prioritization": {
        "agent_key": "job_prioritization",
        "agent_name": job_prioritization_agent.AGENT_NAME,
        "agent_version": job_prioritization_agent.AGENT_VERSION,
        "model_provider": "deterministic",
        "model_name": "job_prioritization_rules",
        "phase": "7A",
        "advisory_only": True,
        "diagnostic_only": False,
        "trace_enabled_by_default": False,
        "mutates_production_decisions": False,
        "input_artifacts": ["application_execution_queue.csv", "source_health_report.csv"],
        "output_artifacts": [
            "job_prioritization_recommendations.csv",
            "job_prioritization_summary.json",
        ],
        "required_feature_flags": ["APPLYLENS_AGENT_TRACE_ENABLED"],
        "benchmark_metric_keys": [
            "job_priority_accuracy",
            "fallback_only_skip_rate",
            "high_score_apply_rate",
            "packet_block_skip_rate",
        ],
        "owner_module": "src.agents.job_prioritization_agent",
    },
    "tailoring_decision": {
        "agent_key": "tailoring_decision",
        "agent_name": tailoring_decision_agent.AGENT_NAME,
        "agent_version": tailoring_decision_agent.AGENT_VERSION,
        "model_provider": "deterministic",
        "model_name": "tailoring_decision_rules",
        "phase": "8A",
        "advisory_only": True,
        "diagnostic_only": False,
        "trace_enabled_by_default": False,
        "mutates_production_decisions": False,
        "input_artifacts": [
            "application_execution_queue.csv",
            "job_prioritization_recommendations.csv",
        ],
        "output_artifacts": [
            "tailoring_decision_recommendations.csv",
            "tailoring_decision_summary.json",
        ],
        "required_feature_flags": ["APPLYLENS_AGENT_TRACE_ENABLED"],
        "benchmark_metric_keys": [
            "tailoring_decision_accuracy",
            "fallback_only_do_not_tailor_rate",
            "critic_reject_do_not_tailor_rate",
            "high_score_light_tailoring_rate",
        ],
        "owner_module": "src.agents.tailoring_decision_agent",
    },
    "operator_review": {
        "agent_key": "operator_review",
        "agent_name": operator_review_agent.AGENT_NAME,
        "agent_version": operator_review_agent.AGENT_VERSION,
        "model_provider": "deterministic",
        "model_name": "operator_review_rules",
        "phase": "9A",
        "advisory_only": True,
        "diagnostic_only": False,
        "trace_enabled_by_default": False,
        "mutates_production_decisions": False,
        "input_artifacts": [
            "application_execution_queue.csv",
            "job_prioritization_recommendations.csv",
            "tailoring_decision_recommendations.csv",
        ],
        "output_artifacts": [
            "operator_review_recommendations.csv",
            "operator_review_summary.json",
        ],
        "required_feature_flags": ["APPLYLENS_AGENT_TRACE_ENABLED"],
        "benchmark_metric_keys": [
            "operator_review_accuracy",
            "ready_to_apply_precision",
            "hold_or_skip_block_rate",
            "critic_reject_hold_rate",
        ],
        "owner_module": "src.agents.operator_review_agent",
    },
}


def _workflow_metadata() -> Dict[str, Any]:
    return {
        "workflow_name": WORKFLOW_NAME,
        "workflow_version": WORKFLOW_VERSION,
        "ordered_agent_keys": list(ORDERED_AGENT_KEYS),
        "artifact_dependency_order": list(ARTIFACT_DEPENDENCY_ORDER),
        "safety_guarantees": list(SAFETY_GUARANTEES),
        "feature_flags": list(REQUIRED_FEATURE_FLAGS),
        "generated_artifact_kinds": list(GENERATED_ARTIFACT_KINDS),
    }


def get_agentic_workflow_manifest() -> Dict[str, Any]:
    manifest = _workflow_metadata()
    manifest["agents"] = {
        key: deepcopy(AGENT_MANIFESTS[key])
        for key in ORDERED_AGENT_KEYS
    }
    return manifest


def list_agentic_agents() -> List[Dict[str, Any]]:
    return [deepcopy(AGENT_MANIFESTS[key]) for key in ORDERED_AGENT_KEYS]


def get_agent_manifest(agent_key: str) -> Dict[str, Any]:
    key = str(agent_key or "").strip()
    if key not in AGENT_MANIFESTS:
        raise KeyError(f"Unknown agentic agent key: {agent_key}")
    return deepcopy(AGENT_MANIFESTS[key])


def validate_agentic_workflow_manifest(
    manifest: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = deepcopy(manifest) if manifest is not None else get_agentic_workflow_manifest()
    agents = dict(payload.get("agents") or {})
    ordered = list(payload.get("ordered_agent_keys") or [])
    generated_artifact_kinds = set(payload.get("generated_artifact_kinds") or [])
    feature_flags = set(payload.get("feature_flags") or [])
    reason_codes: List[str] = []

    if len(ordered) != len(set(ordered)):
        reason_codes.append("duplicate_ordered_agent_keys")
    missing_ordered = [key for key in ordered if key not in agents]
    if missing_ordered:
        reason_codes.append("ordered_agent_key_missing_manifest")
    extra_agents = [key for key in agents if key not in ordered]
    if extra_agents:
        reason_codes.append("agent_not_in_order")

    for key, agent in agents.items():
        if not str(agent.get("agent_key") or "").strip():
            reason_codes.append(f"{key}:missing_agent_key")
        if not str(agent.get("agent_name") or "").strip():
            reason_codes.append(f"{key}:missing_agent_name")
        if not str(agent.get("agent_version") or "").strip():
            reason_codes.append(f"{key}:missing_agent_version")
        if not str(agent.get("model_provider") or "").strip():
            reason_codes.append(f"{key}:missing_model_provider")
        if not str(agent.get("model_name") or "").strip():
            reason_codes.append(f"{key}:missing_model_name")
        if agent.get("mutates_production_decisions"):
            reason_codes.append(f"{key}:mutates_production_decisions")
        if not agent.get("diagnostic_only") and not agent.get("advisory_only"):
            reason_codes.append(f"{key}:not_advisory_or_diagnostic")
        if agent.get("trace_enabled_by_default"):
            reason_codes.append(f"{key}:trace_enabled_by_default")

    missing_feature_flags = [flag for flag in REQUIRED_FEATURE_FLAGS if flag not in feature_flags]
    if missing_feature_flags:
        reason_codes.append("missing_required_feature_flags")

    missing_artifact_kinds = [
        kind for kind in EXPECTED_AGENTIC_ARTIFACT_KINDS if kind not in generated_artifact_kinds
    ]
    if missing_artifact_kinds:
        reason_codes.append("missing_expected_artifact_kinds")

    benchmark_metric_keys = sorted(
        {
            metric
            for agent in agents.values()
            for metric in list(agent.get("benchmark_metric_keys") or [])
        }
    )
    if not benchmark_metric_keys:
        reason_codes.append("missing_benchmark_metric_keys")

    return {
        "validation_status": "failed" if reason_codes else "passed",
        "reason_codes": sorted(set(reason_codes)),
        "agent_count": len(agents),
        "ordered_agent_count": len(ordered),
        "missing_ordered_agent_keys": missing_ordered,
        "extra_agent_keys": extra_agents,
        "missing_feature_flags": missing_feature_flags,
        "missing_artifact_kinds": missing_artifact_kinds,
        "benchmark_metric_keys": benchmark_metric_keys,
    }


def render_agentic_workflow_manifest_markdown(
    manifest: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(manifest) if manifest is not None else get_agentic_workflow_manifest()
    validation = validate_agentic_workflow_manifest(payload)
    agents = [payload["agents"][key] for key in payload.get("ordered_agent_keys", []) if key in payload.get("agents", {})]
    lines = [
        "# Agentic Workflow Manifest",
        "",
        f"Workflow: `{payload.get('workflow_name', '')}`",
        f"Version: `{payload.get('workflow_version', '')}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Agents",
        "",
    ]
    for agent in agents:
        lines.extend(
            [
                f"### {agent.get('agent_name', '')}",
                "",
                f"- Key: `{agent.get('agent_key', '')}`",
                f"- Version: `{agent.get('agent_version', '')}`",
                f"- Model: `{agent.get('model_provider', '')}/{agent.get('model_name', '')}`",
                f"- Advisory only: `{bool(agent.get('advisory_only'))}`",
                f"- Mutates production decisions: `{bool(agent.get('mutates_production_decisions'))}`",
                f"- Inputs: {', '.join(f'`{item}`' for item in agent.get('input_artifacts', []) or [])}",
                f"- Outputs: {', '.join(f'`{item}`' for item in agent.get('output_artifacts', []) or [])}",
                "",
            ]
        )
    lines.extend(["## Artifact Flow", ""])
    for artifact in payload.get("artifact_dependency_order", []) or []:
        lines.append(f"- `{artifact}`")
    lines.extend(["", "## Feature Flags", ""])
    for flag in payload.get("feature_flags", []) or []:
        lines.append(f"- `{flag}`")
    lines.extend(["", "## Generated Artifact Kinds", ""])
    for kind in payload.get("generated_artifact_kinds", []) or []:
        lines.append(f"- `{kind}`")
    lines.extend(["", "## Safety Guarantees", ""])
    for guarantee in payload.get("safety_guarantees", []) or []:
        lines.append(f"- {guarantee}")
    return "\n".join(lines).strip() + "\n"


def build_agentic_workflow_manifest_artifact_payload() -> Dict[str, Any]:
    manifest = get_agentic_workflow_manifest()
    manifest["validation"] = validate_agentic_workflow_manifest(manifest)
    return manifest


def write_agentic_workflow_manifest_artifacts(
    *,
    output_dir: str | Path,
    manifest_json_path: str | Path | None = None,
    manifest_md_path: str | Path | None = None,
) -> Dict[str, Any]:
    root = Path(output_dir)
    json_path = Path(manifest_json_path) if manifest_json_path else root / MANIFEST_JSON_NAME
    md_path = Path(manifest_md_path) if manifest_md_path else root / MANIFEST_MD_NAME
    payload = build_agentic_workflow_manifest_artifact_payload()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_agentic_workflow_manifest_markdown(payload), encoding="utf-8")
    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "payload": payload,
        "validation_status": payload.get("validation", {}).get("validation_status", ""),
    }
