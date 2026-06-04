from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.agents.read_only_adapter_chain import validate_read_only_adapter_chain_result
from src.agents.read_only_chain_artifact_generator import validate_chain_artifact_generation_result


SIMULATOR_VERSION = "dry_run_execution_simulator_v1"
EXECUTION_MODE = "explicit_dry_run_execution_simulation"
RESULT_JSON_NAME = "dry_run_execution_simulation_result.json"
REPORT_MD_NAME = "dry_run_execution_simulation_report.md"
SIMULATOR_ARTIFACT_NAMES = {RESULT_JSON_NAME, REPORT_MD_NAME}
CHAIN_RESULT_JSON_NAME = "read_only_adapter_chain_result.json"
GENERATOR_RESULT_JSON_NAME = "read_only_chain_artifact_generation_result.json"
PRODUCTION_ROOT_ARTIFACT_NAMES = {
    "application_execution_queue.csv",
    "job_prioritization_recommendations.csv",
    "tailoring_decision_recommendations.csv",
    "operator_review_recommendations.csv",
}

SIMULATED_PLAN_STEPS = [
    "review_chain_recommendations",
    "classify_allowed_diagnostic_outputs",
    "classify_blocked_mutation_types",
    "require_operator_approval_for_any_future_mutation",
    "block_application_submission",
    "block_queue_mutation",
    "block_tailoring_generation",
    "block_packet_generation",
    "block_scoring_ranking_changes",
]
BLOCKED_LIVE_EXECUTION_REASONS = [
    "live_execution_disabled",
    "queue_mutation_blocked",
    "application_submission_blocked",
    "tailoring_generation_blocked",
    "packet_generation_blocked",
    "scoring_ranking_changes_blocked",
    "approval_gate_missing",
    "audit_ledger_missing",
    "idempotency_key_required",
    "execution_lock_required",
    "rollback_plan_required",
]
SIMULATED_MUTATION_TYPES = [
    "queue_diagnostic_status_marker",
    "operator_note",
    "artifact_status_marker",
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


def build_dry_run_execution_simulation_context(
    *,
    input_artifact_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    created_at_utc: str = "",
) -> Dict[str, Any]:
    return {
        "simulator_version": SIMULATOR_VERSION,
        "execution_mode": EXECUTION_MODE,
        "input_artifact_dir": _clean_text(input_artifact_dir),
        "output_dir": _clean_text(output_dir),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "created_at_utc": _clean_text(created_at_utc) or _utc_now_iso(),
        "require_explicit_input_artifact_dir": True,
        "require_explicit_output_dir": True,
        "did_execute_live": False,
        "did_mutate_production": False,
        "allow_live_pipeline_wiring": False,
        "allow_application_submission": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_generation_update": False,
        "allow_scoring_update": False,
        "allow_ranking_update": False,
        "allow_db_write": False,
        "allow_scheduler_execution": False,
    }


def _safety_flags() -> Dict[str, bool]:
    return {
        "did_execute_live": False,
        "did_mutate_production": False,
        "allow_live_pipeline_wiring": False,
        "allow_application_submission": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_generation_update": False,
        "allow_scoring_update": False,
        "allow_ranking_update": False,
        "allow_db_write": False,
        "allow_scheduler_execution": False,
    }


def _simulated_execution_plan() -> Dict[str, Any]:
    return {
        "plan_mode": "diagnostic_dry_run_only",
        "proposed_steps": list(SIMULATED_PLAN_STEPS),
        "can_execute_live": False,
        "requires_operator_approval": True,
        "requires_audit_ledger": True,
        "requires_idempotency_key": True,
        "requires_execution_lock": True,
        "requires_rollback_plan": True,
    }


def _empty_result(
    *,
    context: Dict[str, Any],
    reason_codes: List[str] | None = None,
    warning_codes: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "simulator_version": SIMULATOR_VERSION,
        "execution_mode": EXECUTION_MODE,
        "input_artifact_dir": _clean_text(context.get("input_artifact_dir")),
        "output_dir": _clean_text(context.get("output_dir")),
        "pipeline_run_id": _clean_text(context.get("pipeline_run_id")),
        "owner_user_id": _clean_text(context.get("owner_user_id")),
        "context": dict(context),
        "did_simulate": False,
        "did_execute_live": False,
        "did_mutate_production": False,
        "chain_artifact_summary": {},
        "generator_artifact_summary": {},
        "simulated_execution_plan": _simulated_execution_plan(),
        "simulated_mutation_proposals": [],
        "blocked_live_execution_reasons": list(BLOCKED_LIVE_EXECUTION_REASONS),
        "safety_flags": _safety_flags(),
        "reason_codes": list(reason_codes or []),
        "warning_codes": list(warning_codes or []),
    }


def _artifact_summary(payload: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
    summary = dict(payload.get("summary") or payload.get("chain_result_summary") or {})
    return {
        "present": bool(payload),
        "execution_mode": _clean_text(payload.get("execution_mode")),
        "validation_status": _clean_text(validation.get("validation_status")),
        "reason_codes": list(validation.get("reason_codes") or []),
        "warning_codes": list(validation.get("warning_codes") or []),
        "input_row_count": int(summary.get("input_row_count") or 0),
        "adapters_executed_count": int(summary.get("adapters_executed_count") or 0),
        "job_prioritization_recommendation_count": int(
            summary.get("job_prioritization_recommendation_count") or 0
        ),
        "tailoring_decision_count": int(summary.get("tailoring_decision_count") or 0),
        "operator_review_lane_count": int(summary.get("operator_review_lane_count") or 0),
    }


def _simulated_mutation_proposals(chain_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    counts = [
        ("queue_diagnostic_status_marker", int(chain_summary.get("job_prioritization_recommendation_count") or 0)),
        ("operator_note", int(chain_summary.get("operator_review_lane_count") or 0)),
        ("artifact_status_marker", int(chain_summary.get("adapters_executed_count") or 0)),
    ]
    proposals: List[Dict[str, Any]] = []
    for idx, (mutation_type, source_count) in enumerate(counts, start=1):
        if source_count <= 0:
            continue
        proposals.append(
            {
                "proposal_id": f"simulated_proposal_{idx}",
                "proposal_mode": "simulated_non_executable",
                "mutation_type": mutation_type,
                "source_summary_count": source_count,
                "can_execute_live": False,
                "requires_approval": True,
                "blocked_by_default": True,
                "reason_codes": [
                    "diagnostic_only",
                    "non_executable",
                    "future_approval_required",
                ],
            }
        )
    return proposals


def _root_file_names(output_dir: str | Path | None) -> List[str]:
    output_text = _clean_text(output_dir)
    if not output_text:
        return []
    root = Path(output_text)
    if not root.exists() or not root.is_dir():
        return []
    return sorted(path.name for path in root.iterdir() if path.is_file())


def _write_simulation_artifacts(*, result: Dict[str, Any], output_dir: str | Path) -> List[str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / RESULT_JSON_NAME
    md_path = root / REPORT_MD_NAME

    serializable = deepcopy(result)
    serializable["simulator_artifacts"] = []
    json_path.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_dry_run_execution_simulation_report_markdown(result), encoding="utf-8")
    return [str(json_path), str(md_path)]


def simulate_dry_run_execution(
    *,
    input_artifact_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    write_report: bool = True,
) -> Dict[str, Any]:
    context = build_dry_run_execution_simulation_context(
        input_artifact_dir=input_artifact_dir,
        output_dir=output_dir,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
    )
    input_text = _clean_text(input_artifact_dir)
    output_text = _clean_text(output_dir)
    reason_codes: List[str] = []

    if not input_text:
        reason_codes.append("missing_explicit_input_artifact_dir")
    if not output_text:
        reason_codes.append("missing_explicit_output_dir")

    input_root = Path(input_text) if input_text else None
    if input_root is not None and (not input_root.exists() or not input_root.is_dir()):
        reason_codes.append("input_artifact_dir_not_found")

    if reason_codes:
        result = _empty_result(context=context, reason_codes=reason_codes)
        result["validation"] = validate_dry_run_execution_simulation_result(result)
        result["simulator_artifacts"] = []
        return result

    assert input_root is not None
    chain_path = input_root / CHAIN_RESULT_JSON_NAME
    generator_path = input_root / GENERATOR_RESULT_JSON_NAME
    if not chain_path.exists() or not chain_path.is_file():
        reason_codes.append("missing_read_only_adapter_chain_result")
    if not generator_path.exists() or not generator_path.is_file():
        reason_codes.append("missing_read_only_chain_artifact_generation_result")

    if reason_codes:
        result = _empty_result(context=context, reason_codes=reason_codes)
        result["validation"] = validate_dry_run_execution_simulation_result(result)
        result["simulator_artifacts"] = []
        return result

    chain_payload = _read_json(chain_path)
    generator_payload = _read_json(generator_path)
    chain_validation = validate_read_only_adapter_chain_result(chain_payload)
    generator_validation = validate_chain_artifact_generation_result(generator_payload)

    if _clean_text(chain_validation.get("validation_status")) == "failed":
        reason_codes.append("read_only_adapter_chain_validation_failed")
    if _clean_text(generator_validation.get("validation_status")) == "failed":
        reason_codes.append("read_only_chain_artifact_generation_validation_failed")

    chain_summary = _artifact_summary(chain_payload, chain_validation)
    generator_summary = _artifact_summary(generator_payload, generator_validation)
    result = _empty_result(context=context, reason_codes=reason_codes)
    result.update(
        {
            "did_simulate": not reason_codes,
            "chain_artifact_summary": chain_summary,
            "generator_artifact_summary": generator_summary,
            "simulated_execution_plan": _simulated_execution_plan(),
            "simulated_mutation_proposals": _simulated_mutation_proposals(chain_summary)
            if not reason_codes
            else [],
        }
    )
    result["validation"] = validate_dry_run_execution_simulation_result(result)
    result["simulator_artifacts"] = []
    if not reason_codes and write_report:
        result["simulator_artifacts"] = _write_simulation_artifacts(result=result, output_dir=output_text)
        result["validation"] = validate_dry_run_execution_simulation_result(result)
    return result


def validate_dry_run_execution_simulation_result(result: Dict[str, Any]) -> Dict[str, Any]:
    reason_codes: List[str] = list(result.get("reason_codes") or [])
    warning_codes: List[str] = list(result.get("warning_codes") or [])

    if _clean_text(result.get("execution_mode")) != EXECUTION_MODE:
        reason_codes.append("execution_mode_not_explicit_dry_run_execution_simulation")
    if not _clean_text(result.get("input_artifact_dir")):
        reason_codes.append("missing_explicit_input_artifact_dir")
    if not _clean_text(result.get("output_dir")):
        reason_codes.append("missing_explicit_output_dir")
    if bool(result.get("did_execute_live")):
        reason_codes.append("did_execute_live")
    if bool(result.get("did_mutate_production")):
        reason_codes.append("did_mutate_production")

    context = dict(result.get("context") or {})
    for flag in ["require_explicit_input_artifact_dir", "require_explicit_output_dir"]:
        value = result.get(flag) if flag in result else context.get(flag)
        if not bool(value):
            reason_codes.append(f"{flag}_false")

    safety_flags = dict(result.get("safety_flags") or {})
    for flag in [
        "did_execute_live",
        "did_mutate_production",
        "allow_live_pipeline_wiring",
        "allow_application_submission",
        "allow_queue_action_update",
        "allow_packet_update",
        "allow_tailoring_generation_update",
        "allow_scoring_update",
        "allow_ranking_update",
        "allow_db_write",
        "allow_scheduler_execution",
    ]:
        if bool(safety_flags.get(flag)):
            reason_codes.append(f"{flag}_true")

    plan = dict(result.get("simulated_execution_plan") or {})
    if bool(plan.get("can_execute_live")):
        reason_codes.append("simulated_plan_can_execute_live")
    for flag in [
        "requires_operator_approval",
        "requires_audit_ledger",
        "requires_idempotency_key",
        "requires_execution_lock",
        "requires_rollback_plan",
    ]:
        if not bool(plan.get(flag)):
            reason_codes.append(f"simulated_plan_{flag}_false")

    for proposal in list(result.get("simulated_mutation_proposals") or []):
        mutation_type = _clean_text(dict(proposal).get("mutation_type"))
        if mutation_type not in SIMULATED_MUTATION_TYPES:
            reason_codes.append("simulated_proposal_forbidden_mutation_type")
        if _clean_text(dict(proposal).get("proposal_mode")) != "simulated_non_executable":
            reason_codes.append("simulated_proposal_wrong_mode")
        if bool(dict(proposal).get("can_execute_live")):
            reason_codes.append("simulated_proposal_can_execute_live")
        if not bool(dict(proposal).get("requires_approval")):
            reason_codes.append("simulated_proposal_missing_approval_requirement")
        if not bool(dict(proposal).get("blocked_by_default")):
            reason_codes.append("simulated_proposal_not_blocked_by_default")

    blocked = set(result.get("blocked_live_execution_reasons") or [])
    for required_reason in ["queue_mutation_blocked", "application_submission_blocked"]:
        if required_reason not in blocked:
            reason_codes.append(f"missing_{required_reason}")

    root_names = set(_root_file_names(result.get("output_dir")))
    production_root_names = sorted(root_names.intersection(PRODUCTION_ROOT_ARTIFACT_NAMES))
    if production_root_names:
        reason_codes.append("production_artifact_name_written_at_output_root")
    unexpected_root_names = sorted(root_names.difference(SIMULATOR_ARTIFACT_NAMES))
    if bool(result.get("did_simulate")) and unexpected_root_names:
        reason_codes.append("non_simulator_artifact_written")

    for artifact in list(result.get("simulator_artifacts") or []):
        if Path(_clean_text(artifact)).name not in SIMULATOR_ARTIFACT_NAMES:
            reason_codes.append("non_simulator_artifact_recorded")

    unique_reasons = sorted(set(reason_codes))
    unique_warnings = sorted(set(warning_codes))
    status = "failed" if unique_reasons else "warning" if unique_warnings else "passed"
    return {
        "validation_status": status,
        "reason_codes": unique_reasons,
        "warning_codes": unique_warnings,
        "did_simulate": bool(result.get("did_simulate")),
        "did_execute_live": bool(result.get("did_execute_live")),
        "did_mutate_production": bool(result.get("did_mutate_production")),
        "output_root_file_names": sorted(root_names),
    }


def render_dry_run_execution_simulation_report_markdown(
    result: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(result) if result is not None else simulate_dry_run_execution(write_report=False)
    validation = dict(payload.get("validation") or validate_dry_run_execution_simulation_result(payload))
    plan = dict(payload.get("simulated_execution_plan") or {})
    chain_summary = dict(payload.get("chain_artifact_summary") or {})
    generator_summary = dict(payload.get("generator_artifact_summary") or {})
    lines = [
        "# Dry-Run Execution Simulation",
        "",
        "Explicit/manual diagnostic simulation only. It consumes existing read-only diagnostics and does not run the chain, generator, agents, live planning, scheduler, or workflow runner.",
        "It does not mutate production, write to the database, update queues, submit applications, generate tailoring, generate packets, or change scoring/ranking.",
        "",
        f"Simulator version: `{_clean_text(payload.get('simulator_version'))}`",
        f"Execution mode: `{_clean_text(payload.get('execution_mode'))}`",
        f"Did simulate: `{bool(payload.get('did_simulate'))}`",
        f"Did execute live: `{bool(payload.get('did_execute_live'))}`",
        f"Did mutate production: `{bool(payload.get('did_mutate_production'))}`",
        f"Can execute live: `{bool(plan.get('can_execute_live'))}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Inputs",
        "",
        f"- Input artifact dir: `{_clean_text(payload.get('input_artifact_dir')) or 'none'}`",
        f"- Output dir: `{_clean_text(payload.get('output_dir')) or 'none'}`",
        "",
        "## Artifact Summaries",
        "",
        f"- Chain validation: `{_clean_text(chain_summary.get('validation_status')) or 'none'}`",
        f"- Generator validation: `{_clean_text(generator_summary.get('validation_status')) or 'none'}`",
        f"- Input rows: `{int(chain_summary.get('input_row_count') or 0)}`",
        f"- Adapters executed in source diagnostics: `{int(chain_summary.get('adapters_executed_count') or 0)}`",
        "",
        "## Simulated Plan",
        "",
    ]
    for step in list(plan.get("proposed_steps") or []):
        lines.append(f"- `{step}`")
    lines.extend(["", "## Simulated Non-Executable Proposals", ""])
    proposals = list(payload.get("simulated_mutation_proposals") or [])
    if proposals:
        for proposal in proposals:
            lines.append(
                f"- `{proposal.get('proposal_id')}` `{proposal.get('mutation_type')}` "
                f"mode=`{proposal.get('proposal_mode')}` can_execute_live=`{bool(proposal.get('can_execute_live'))}`"
            )
    else:
        lines.append("- none")
    if validation.get("reason_codes"):
        lines.extend(["", "## Reason Codes", ""])
        lines.extend(f"- `{code}`" for code in validation.get("reason_codes", []) or [])
    return "\n".join(lines).strip() + "\n"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Explicit/manual dry-run execution simulator that reads existing diagnostics only; "
            "it does not run agents or mutate production."
        )
    )
    parser.add_argument("--input-artifact-dir", default="", help="Required explicit directory containing read-only diagnostic artifacts.")
    parser.add_argument("--output-dir", default="", help="Required explicit directory for simulator diagnostic artifacts.")
    parser.add_argument("--pipeline-run-id", default="", help="Optional diagnostic pipeline run id.")
    parser.add_argument("--owner-user-id", default="", help="Optional diagnostic owner user id.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    payload = simulate_dry_run_execution(
        input_artifact_dir=args.input_artifact_dir,
        output_dir=args.output_dir,
        pipeline_run_id=args.pipeline_run_id,
        owner_user_id=args.owner_user_id,
    )
    validation = dict(payload.get("validation") or {})
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Dry-run execution simulation: {validation.get('validation_status', '')}")
        print(f"Did simulate: {bool(payload.get('did_simulate'))}")
        print(f"Output dir: {_clean_text(payload.get('output_dir')) or 'none'}")
    return 0 if validation.get("validation_status") == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
