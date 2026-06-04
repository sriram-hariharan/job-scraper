from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.agents.dry_run_execution_simulator import validate_dry_run_execution_simulation_result


PLANNER_VERSION = "proposal_only_mutation_planner_v1"
EXECUTION_MODE = "explicit_proposal_only_mutation_planning"
SIMULATION_EXECUTION_MODE = "explicit_dry_run_execution_simulation"
RESULT_JSON_NAME = "proposal_only_mutation_plan_result.json"
REPORT_MD_NAME = "proposal_only_mutation_plan_report.md"
PLANNER_ARTIFACT_NAMES = {RESULT_JSON_NAME, REPORT_MD_NAME}
PRODUCTION_ROOT_ARTIFACT_NAMES = {
    "application_execution_queue.csv",
    "job_prioritization_recommendations.csv",
    "tailoring_decision_recommendations.csv",
    "operator_review_recommendations.csv",
    "dry_run_execution_simulation_result.json",
}
ALLOWED_MUTATION_TYPES = {
    "queue_diagnostic_status_marker",
    "operator_note",
    "artifact_status_marker",
}
FORBIDDEN_MUTATION_TYPES = {
    "application_submission",
    "queue_action_update",
    "tailoring_generation",
    "packet_generation",
    "scoring_update",
    "ranking_update",
    "resume_rewrite",
    "scraper_source_mutation",
    "rag_corpus_mutation",
    "production_record_delete",
}
PROPOSED_NEXT_REVIEW_STEPS = [
    "review_non_executable_proposals",
    "verify_mutation_type_allowlist",
    "require_future_approval_gate",
    "require_future_audit_ledger",
    "require_future_idempotency_locking",
    "block_live_execution",
    "block_application_submission",
    "block_queue_mutation",
]
BLOCKED_EXECUTION_REASONS = [
    "live_execution_disabled",
    "mutation_execution_blocked",
    "approval_action_blocked",
    "approval_storage_missing",
    "approval_api_missing",
    "audit_ledger_missing",
    "idempotency_key_required",
    "execution_lock_required",
    "rollback_plan_required",
    "queue_mutation_blocked",
    "application_submission_blocked",
    "db_write_blocked",
    "scheduler_execution_blocked",
]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _root_file_names(output_dir: str | Path | None) -> List[str]:
    output_text = _clean_text(output_dir)
    if not output_text:
        return []
    root = Path(output_text)
    if not root.exists() or not root.is_dir():
        return []
    return sorted(path.name for path in root.iterdir() if path.is_file())


def build_proposal_only_mutation_planner_context(
    *,
    simulation_result_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    created_at_utc: str = "",
) -> Dict[str, Any]:
    return {
        "planner_version": PLANNER_VERSION,
        "execution_mode": EXECUTION_MODE,
        "simulation_result_path": _clean_text(simulation_result_path),
        "output_dir": _clean_text(output_dir),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "created_at_utc": _clean_text(created_at_utc) or _utc_now_iso(),
        "require_explicit_simulation_result_path": True,
        "require_explicit_output_dir": True,
        "did_execute_live": False,
        "did_mutate_production": False,
        "did_approve": False,
        "did_store_approval": False,
        "did_write_db": False,
        "allow_live_pipeline_wiring": False,
        "allow_application_submission": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_generation_update": False,
        "allow_scoring_update": False,
        "allow_ranking_update": False,
        "allow_db_write": False,
        "allow_scheduler_execution": False,
        "allow_approval_action": False,
        "allow_mutation_execution": False,
    }


def _safety_flags() -> Dict[str, bool]:
    return {
        "did_execute_live": False,
        "did_mutate_production": False,
        "did_approve": False,
        "did_store_approval": False,
        "did_write_db": False,
        "allow_live_pipeline_wiring": False,
        "allow_application_submission": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_generation_update": False,
        "allow_scoring_update": False,
        "allow_ranking_update": False,
        "allow_db_write": False,
        "allow_scheduler_execution": False,
        "allow_approval_action": False,
        "allow_mutation_execution": False,
    }


def _proposal_plan() -> Dict[str, Any]:
    return {
        "plan_mode": "proposal_only_non_executable",
        "can_execute_live": False,
        "can_mutate": False,
        "can_approve": False,
        "requires_operator_approval": True,
        "requires_approval_api": True,
        "requires_approval_storage": True,
        "requires_audit_ledger": True,
        "requires_idempotency_key": True,
        "requires_execution_lock": True,
        "requires_rollback_plan": True,
        "proposed_next_review_steps": list(PROPOSED_NEXT_REVIEW_STEPS),
    }


def _empty_result(
    *,
    context: Dict[str, Any],
    reason_codes: List[str] | None = None,
    warning_codes: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "planner_version": PLANNER_VERSION,
        "execution_mode": EXECUTION_MODE,
        "simulation_result_path": _clean_text(context.get("simulation_result_path")),
        "output_dir": _clean_text(context.get("output_dir")),
        "pipeline_run_id": _clean_text(context.get("pipeline_run_id")),
        "owner_user_id": _clean_text(context.get("owner_user_id")),
        "context": dict(context),
        "did_plan": False,
        "did_execute_live": False,
        "did_mutate_production": False,
        "did_approve": False,
        "did_store_approval": False,
        "did_write_db": False,
        "source_simulation_summary": {},
        "proposal_plan": _proposal_plan(),
        "proposal_only_mutation_items": [],
        "blocked_execution_reasons": list(BLOCKED_EXECUTION_REASONS),
        "safety_flags": _safety_flags(),
        "reason_codes": list(reason_codes or []),
        "warning_codes": list(warning_codes or []),
        "planner_artifacts": [],
    }


def _source_simulation_summary(simulation: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
    proposals = list(simulation.get("simulated_mutation_proposals") or [])
    plan = dict(simulation.get("simulated_execution_plan") or {})
    return {
        "present": bool(simulation),
        "execution_mode": _clean_text(simulation.get("execution_mode")),
        "validation_status": _clean_text(validation.get("validation_status")),
        "did_simulate": bool(simulation.get("did_simulate")),
        "did_execute_live": bool(simulation.get("did_execute_live")),
        "did_mutate_production": bool(simulation.get("did_mutate_production")),
        "can_execute_live": bool(plan.get("can_execute_live")),
        "simulated_proposal_count": len(proposals),
        "blocked_live_execution_reasons": list(simulation.get("blocked_live_execution_reasons") or []),
        "reason_codes": list(validation.get("reason_codes") or []),
        "warning_codes": list(validation.get("warning_codes") or []),
    }


def _evidence_refs(source_proposal: Dict[str, Any], simulation_result_path: str) -> List[Dict[str, str]]:
    refs = [
        {
            "artifact_name": "dry_run_execution_simulation_result.json",
            "artifact_path": simulation_result_path,
            "source_proposal_id": _clean_text(source_proposal.get("proposal_id")),
        }
    ]
    for key in ["mutation_type", "proposal_mode"]:
        value = _clean_text(source_proposal.get(key))
        if value:
            refs.append({"source_field": key, "source_value": value})
    return refs


def _proposal_items(simulation: Dict[str, Any], simulation_result_path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for idx, proposal in enumerate(list(simulation.get("simulated_mutation_proposals") or []), start=1):
        source = dict(proposal)
        mutation_type = _clean_text(source.get("mutation_type"))
        items.append(
            {
                "proposal_id": f"proposal_only_item_{idx}",
                "proposal_mode": "proposal_only_non_executable",
                "source_proposal_id": _clean_text(source.get("proposal_id")) or f"simulated_proposal_{idx}",
                "mutation_type": mutation_type,
                "can_execute_live": False,
                "can_mutate": False,
                "can_approve": False,
                "blocked_by_default": True,
                "requires_operator_approval": True,
                "requires_audit_ledger": True,
                "requires_idempotency_key": True,
                "requires_execution_lock": True,
                "requires_rollback_plan": True,
                "reason_codes": sorted(
                    set(
                        list(source.get("reason_codes") or [])
                        + [
                            "proposal_only",
                            "non_executable",
                            "future_approval_required",
                            "future_audit_ledger_required",
                            "future_idempotency_locking_required",
                        ]
                    )
                ),
                "evidence_refs": _evidence_refs(source, simulation_result_path),
                "review_notes": (
                    "Non-executable proposal-only item derived from dry-run simulation; "
                    "requires future approval, audit ledger, idempotency, lock, and rollback gates."
                ),
            }
        )
    return items


def _write_planner_artifacts(*, result: Dict[str, Any], output_dir: str | Path) -> List[str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / RESULT_JSON_NAME
    md_path = root / REPORT_MD_NAME

    serializable = deepcopy(result)
    serializable["planner_artifacts"] = []
    json_path.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_proposal_only_mutation_plan_report_markdown(result), encoding="utf-8")
    return [str(json_path), str(md_path)]


def build_proposal_only_mutation_plan(
    *,
    simulation_result_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    write_report: bool = True,
) -> Dict[str, Any]:
    context = build_proposal_only_mutation_planner_context(
        simulation_result_path=simulation_result_path,
        output_dir=output_dir,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
    )
    simulation_text = _clean_text(simulation_result_path)
    output_text = _clean_text(output_dir)
    reason_codes: List[str] = []
    warning_codes: List[str] = []

    if not simulation_text:
        reason_codes.append("missing_explicit_simulation_result_path")
    if not output_text:
        reason_codes.append("missing_explicit_output_dir")

    simulation_path = Path(simulation_text) if simulation_text else None
    if simulation_path is not None and (not simulation_path.exists() or not simulation_path.is_file()):
        reason_codes.append("simulation_result_path_not_found")

    if reason_codes:
        result = _empty_result(context=context, reason_codes=reason_codes)
        result["validation"] = validate_proposal_only_mutation_plan_result(result)
        return result

    assert simulation_path is not None
    simulation = _read_json(simulation_path)
    simulation_validation = validate_dry_run_execution_simulation_result(simulation)
    if _clean_text(simulation_validation.get("validation_status")) != "passed":
        reason_codes.append("simulation_result_validation_failed")
    if _clean_text(simulation.get("execution_mode")) != SIMULATION_EXECUTION_MODE:
        reason_codes.append("simulation_execution_mode_invalid")
    if bool(simulation.get("did_execute_live")):
        reason_codes.append("simulation_did_execute_live")
    if bool(simulation.get("did_mutate_production")):
        reason_codes.append("simulation_did_mutate_production")
    simulation_plan = dict(simulation.get("simulated_execution_plan") or {})
    if bool(simulation_plan.get("can_execute_live")):
        reason_codes.append("simulation_plan_can_execute_live")

    result = _empty_result(context=context, reason_codes=reason_codes, warning_codes=warning_codes)
    result["source_simulation_summary"] = _source_simulation_summary(simulation, simulation_validation)
    if not reason_codes:
        items = _proposal_items(simulation, simulation_text)
        if not items:
            warning_codes.append("no_simulated_mutation_proposals")
        result.update(
            {
                "did_plan": True,
                "proposal_only_mutation_items": items,
                "warning_codes": warning_codes,
            }
        )

    result["validation"] = validate_proposal_only_mutation_plan_result(result)
    if not reason_codes and write_report:
        result["planner_artifacts"] = _write_planner_artifacts(result=result, output_dir=output_text)
        result["validation"] = validate_proposal_only_mutation_plan_result(result)
    return result


def validate_proposal_only_mutation_plan_result(result: Dict[str, Any]) -> Dict[str, Any]:
    reason_codes: List[str] = list(result.get("reason_codes") or [])
    warning_codes: List[str] = list(result.get("warning_codes") or [])

    if _clean_text(result.get("execution_mode")) != EXECUTION_MODE:
        reason_codes.append("execution_mode_not_explicit_proposal_only_mutation_planning")
    if not _clean_text(result.get("simulation_result_path")):
        reason_codes.append("missing_explicit_simulation_result_path")
    if not _clean_text(result.get("output_dir")):
        reason_codes.append("missing_explicit_output_dir")

    context = dict(result.get("context") or {})
    for flag in ["require_explicit_simulation_result_path", "require_explicit_output_dir"]:
        value = result.get(flag) if flag in result else context.get(flag)
        if not bool(value):
            reason_codes.append(f"{flag}_false")

    for flag in ["did_execute_live", "did_mutate_production", "did_approve", "did_store_approval", "did_write_db"]:
        if bool(result.get(flag)):
            reason_codes.append(f"{flag}_true")

    safety_flags = dict(result.get("safety_flags") or {})
    for flag in [
        "did_execute_live",
        "did_mutate_production",
        "did_approve",
        "did_store_approval",
        "did_write_db",
        "allow_live_pipeline_wiring",
        "allow_application_submission",
        "allow_queue_action_update",
        "allow_packet_update",
        "allow_tailoring_generation_update",
        "allow_scoring_update",
        "allow_ranking_update",
        "allow_db_write",
        "allow_scheduler_execution",
        "allow_approval_action",
        "allow_mutation_execution",
    ]:
        if bool(safety_flags.get(flag)):
            reason_codes.append(f"{flag}_true")

    plan = dict(result.get("proposal_plan") or {})
    if _clean_text(plan.get("plan_mode")) != "proposal_only_non_executable":
        reason_codes.append("proposal_plan_wrong_mode")
    for flag in ["can_execute_live", "can_mutate", "can_approve"]:
        if bool(plan.get(flag)):
            reason_codes.append(f"proposal_plan_{flag}_true")
    for flag in [
        "requires_operator_approval",
        "requires_approval_api",
        "requires_approval_storage",
        "requires_audit_ledger",
        "requires_idempotency_key",
        "requires_execution_lock",
        "requires_rollback_plan",
    ]:
        if not bool(plan.get(flag)):
            reason_codes.append(f"proposal_plan_{flag}_false")

    review_steps = set(plan.get("proposed_next_review_steps") or [])
    for step in PROPOSED_NEXT_REVIEW_STEPS:
        if step not in review_steps:
            reason_codes.append(f"missing_review_step_{step}")

    for item in list(result.get("proposal_only_mutation_items") or []):
        proposal = dict(item)
        mutation_type = _clean_text(proposal.get("mutation_type"))
        if mutation_type in FORBIDDEN_MUTATION_TYPES or mutation_type not in ALLOWED_MUTATION_TYPES:
            reason_codes.append("proposal_item_forbidden_mutation_type")
        if _clean_text(proposal.get("proposal_mode")) != "proposal_only_non_executable":
            reason_codes.append("proposal_item_wrong_mode")
        for flag in ["can_execute_live", "can_mutate", "can_approve"]:
            if bool(proposal.get(flag)):
                reason_codes.append(f"proposal_item_{flag}_true")
        if not bool(proposal.get("blocked_by_default")):
            reason_codes.append("proposal_item_not_blocked_by_default")
        for flag in [
            "requires_operator_approval",
            "requires_audit_ledger",
            "requires_idempotency_key",
            "requires_execution_lock",
            "requires_rollback_plan",
        ]:
            if not bool(proposal.get(flag)):
                reason_codes.append(f"proposal_item_{flag}_false")

    blocked = set(result.get("blocked_execution_reasons") or [])
    for required_reason in [
        "live_execution_disabled",
        "queue_mutation_blocked",
        "application_submission_blocked",
        "db_write_blocked",
    ]:
        if required_reason not in blocked:
            reason_codes.append(f"missing_{required_reason}")

    root_names = set(_root_file_names(result.get("output_dir")))
    production_root_names = sorted(root_names.intersection(PRODUCTION_ROOT_ARTIFACT_NAMES))
    if production_root_names:
        reason_codes.append("production_artifact_name_written_at_output_root")
    unexpected_root_names = sorted(root_names.difference(PLANNER_ARTIFACT_NAMES))
    if bool(result.get("did_plan")) and unexpected_root_names:
        reason_codes.append("non_planner_artifact_written")

    for artifact in list(result.get("planner_artifacts") or []):
        if Path(_clean_text(artifact)).name not in PLANNER_ARTIFACT_NAMES:
            reason_codes.append("non_planner_artifact_recorded")

    unique_reasons = sorted(set(reason_codes))
    unique_warnings = sorted(set(warning_codes))
    status = "failed" if unique_reasons else "warning" if unique_warnings else "passed"
    return {
        "validation_status": status,
        "reason_codes": unique_reasons,
        "warning_codes": unique_warnings,
        "did_plan": bool(result.get("did_plan")),
        "did_execute_live": bool(result.get("did_execute_live")),
        "did_mutate_production": bool(result.get("did_mutate_production")),
        "did_approve": bool(result.get("did_approve")),
        "did_store_approval": bool(result.get("did_store_approval")),
        "did_write_db": bool(result.get("did_write_db")),
        "proposal_item_count": len(list(result.get("proposal_only_mutation_items") or [])),
        "output_root_file_names": sorted(root_names),
    }


def render_proposal_only_mutation_plan_report_markdown(
    result: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(result) if result is not None else build_proposal_only_mutation_plan(
        write_report=False
    )
    validation = dict(payload.get("validation") or validate_proposal_only_mutation_plan_result(payload))
    plan = dict(payload.get("proposal_plan") or {})
    summary = dict(payload.get("source_simulation_summary") or {})
    lines = [
        "# Proposal-Only Mutation Plan",
        "",
        "Explicit/manual proposal-only diagnostic utility. It reads an existing dry-run execution simulation result artifact.",
        "It does not run the simulator, chain, generator, agents, workflow runner, live planning, scheduler, app routes, or storage.",
        "It does not mutate production, approve or reject anything, store approval, write to the database, update queues, submit applications, generate tailoring, generate packets, or change scoring/ranking.",
        "",
        f"Planner version: `{_clean_text(payload.get('planner_version'))}`",
        f"Execution mode: `{_clean_text(payload.get('execution_mode'))}`",
        f"Did plan: `{bool(payload.get('did_plan'))}`",
        f"Did execute live: `{bool(payload.get('did_execute_live'))}`",
        f"Did mutate production: `{bool(payload.get('did_mutate_production'))}`",
        f"Did approve: `{bool(payload.get('did_approve'))}`",
        f"Did store approval: `{bool(payload.get('did_store_approval'))}`",
        f"Did write DB: `{bool(payload.get('did_write_db'))}`",
        f"Can execute live: `{bool(plan.get('can_execute_live'))}`",
        f"Can mutate: `{bool(plan.get('can_mutate'))}`",
        f"Can approve: `{bool(plan.get('can_approve'))}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Inputs",
        "",
        f"- Simulation result: `{_clean_text(payload.get('simulation_result_path')) or 'none'}`",
        f"- Output dir: `{_clean_text(payload.get('output_dir')) or 'none'}`",
        "",
        "## Source Simulation",
        "",
        f"- Simulation validation: `{_clean_text(summary.get('validation_status')) or 'none'}`",
        f"- Simulation proposals: `{int(summary.get('simulated_proposal_count') or 0)}`",
        f"- Simulation can execute live: `{bool(summary.get('can_execute_live'))}`",
        "",
        "## Required Future Gates",
        "",
        f"- Operator approval: `{bool(plan.get('requires_operator_approval'))}`",
        f"- Approval API: `{bool(plan.get('requires_approval_api'))}`",
        f"- Approval storage: `{bool(plan.get('requires_approval_storage'))}`",
        f"- Audit ledger: `{bool(plan.get('requires_audit_ledger'))}`",
        f"- Idempotency key: `{bool(plan.get('requires_idempotency_key'))}`",
        f"- Execution lock: `{bool(plan.get('requires_execution_lock'))}`",
        f"- Rollback plan: `{bool(plan.get('requires_rollback_plan'))}`",
        "",
        "## Proposal-Only Items",
        "",
    ]
    items = list(payload.get("proposal_only_mutation_items") or [])
    if items:
        for item in items:
            lines.append(
                f"- `{item.get('proposal_id')}` `{item.get('mutation_type')}` "
                f"mode=`{item.get('proposal_mode')}` can_mutate=`{bool(item.get('can_mutate'))}`"
            )
    else:
        lines.append("- none")
    if validation.get("reason_codes"):
        lines.extend(["", "## Reason Codes", ""])
        lines.extend(f"- `{code}`" for code in validation.get("reason_codes", []) or [])
    if validation.get("warning_codes"):
        lines.extend(["", "## Warning Codes", ""])
        lines.extend(f"- `{code}`" for code in validation.get("warning_codes", []) or [])
    return "\n".join(lines).strip() + "\n"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Explicit/manual proposal-only mutation planner that reads an existing "
            "dry-run simulation result and writes diagnostic artifacts only."
        )
    )
    parser.add_argument("--simulation-result", default="", help="Required explicit dry_run_execution_simulation_result.json path.")
    parser.add_argument("--output-dir", default="", help="Required explicit output directory for proposal-only diagnostics.")
    parser.add_argument("--pipeline-run-id", default="", help="Optional diagnostic pipeline run id.")
    parser.add_argument("--owner-user-id", default="", help="Optional diagnostic owner user id.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    payload = build_proposal_only_mutation_plan(
        simulation_result_path=args.simulation_result,
        output_dir=args.output_dir,
        pipeline_run_id=args.pipeline_run_id,
        owner_user_id=args.owner_user_id,
    )
    validation = dict(payload.get("validation") or {})
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Proposal-only mutation planning: {validation.get('validation_status', '')}")
        print(f"Did plan: {bool(payload.get('did_plan'))}")
        print(f"Output dir: {_clean_text(payload.get('output_dir')) or 'none'}")
    return 0 if validation.get("validation_status") in {"passed", "warning"} and payload.get("did_plan") else 1


if __name__ == "__main__":
    sys.exit(main())
