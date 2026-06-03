from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.agents import read_only_adapter_chain


GENERATOR_VERSION = "read_only_chain_artifact_generator_v1"
EXECUTION_MODE = "explicit_operator_read_only_chain_artifact_generation"
RESULT_JSON_NAME = "read_only_chain_artifact_generation_result.json"
REPORT_MD_NAME = "read_only_chain_artifact_generation_report.md"

PRODUCTION_ROOT_ARTIFACT_NAMES = {
    "application_execution_queue.csv",
    "job_prioritization_recommendations.csv",
    "tailoring_decision_recommendations.csv",
    "operator_review_recommendations.csv",
}
GENERATOR_ARTIFACT_NAMES = {RESULT_JSON_NAME, REPORT_MD_NAME}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_chain_artifact_generation_context(
    *,
    queue_input_artifact_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    created_at_utc: str = "",
) -> Dict[str, Any]:
    return {
        "generator_version": GENERATOR_VERSION,
        "execution_mode": EXECUTION_MODE,
        "queue_input_artifact_path": _clean_text(queue_input_artifact_path),
        "output_dir": _clean_text(output_dir),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "created_at_utc": _clean_text(created_at_utc) or _utc_now_iso(),
        "require_explicit_input": True,
        "require_explicit_output_dir": True,
        "allow_production_mutation": False,
        "allow_live_pipeline_wiring": False,
        "allow_application_submission": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_generation_update": False,
        "allow_scoring_update": False,
        "allow_ranking_update": False,
    }


def _base_result(
    *,
    context: Dict[str, Any],
    reason_codes: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "generator_version": GENERATOR_VERSION,
        "execution_mode": EXECUTION_MODE,
        "queue_input_artifact_path": _clean_text(context.get("queue_input_artifact_path")),
        "output_dir": _clean_text(context.get("output_dir")),
        "pipeline_run_id": _clean_text(context.get("pipeline_run_id")),
        "owner_user_id": _clean_text(context.get("owner_user_id")),
        "context": dict(context),
        "did_run_chain": False,
        "did_mutate_production": False,
        "require_explicit_input": True,
        "require_explicit_output_dir": True,
        "allow_production_mutation": False,
        "allow_live_pipeline_wiring": False,
        "allow_application_submission": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_generation_update": False,
        "allow_scoring_update": False,
        "allow_ranking_update": False,
        "chain_result_summary": {},
        "chain_result": {},
        "chain_artifacts": [],
        "generator_artifacts": [],
        "reason_codes": list(reason_codes or []),
    }


def _root_file_names(output_dir: str | Path | None) -> List[str]:
    output_text = _clean_text(output_dir)
    if not output_text:
        return []
    root = Path(output_text)
    if not root.exists() or not root.is_dir():
        return []
    return sorted(path.name for path in root.iterdir() if path.is_file())


def _chain_artifacts_from_result(chain_result: Dict[str, Any]) -> List[str]:
    return [
        _clean_text(path)
        for path in list(chain_result.get("artifacts_written") or [])
        if _clean_text(path)
    ]


def _write_generator_artifacts(*, result: Dict[str, Any], output_dir: str | Path) -> List[str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / RESULT_JSON_NAME
    md_path = root / REPORT_MD_NAME

    serializable = deepcopy(result)
    serializable["generator_artifacts"] = []
    json_path.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_chain_artifact_generation_report_markdown(result), encoding="utf-8")
    return [str(json_path), str(md_path)]


def generate_read_only_chain_artifacts(
    *,
    queue_input_artifact_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    write_generator_report: bool = True,
) -> Dict[str, Any]:
    context = build_chain_artifact_generation_context(
        queue_input_artifact_path=queue_input_artifact_path,
        output_dir=output_dir,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
    )
    reason_codes: List[str] = []
    input_text = _clean_text(queue_input_artifact_path)
    output_text = _clean_text(output_dir)

    if not input_text:
        reason_codes.append("missing_explicit_queue_input")
    if not output_text:
        reason_codes.append("missing_explicit_output_dir")
    if input_text:
        input_path = Path(input_text)
        if not input_path.exists() or not input_path.is_file():
            reason_codes.append("queue_input_artifact_not_found")

    if reason_codes:
        result = _base_result(context=context, reason_codes=reason_codes)
        result["validation"] = validate_chain_artifact_generation_result(result)
        if output_text and write_generator_report:
            result["generator_artifacts"] = _write_generator_artifacts(result=result, output_dir=output_text)
            result["validation"] = validate_chain_artifact_generation_result(result)
        return result

    chain_result = read_only_adapter_chain.run_read_only_adapter_chain(
        queue_input_artifact_path=input_text,
        output_dir=output_text,
        pipeline_run_id=_clean_text(pipeline_run_id),
        owner_user_id=_clean_text(owner_user_id),
    )
    result = _base_result(context=context)
    result.update(
        {
            "did_run_chain": bool(chain_result.get("did_execute_chain")),
            "did_mutate_production": False,
            "chain_result_summary": dict(chain_result.get("summary") or {}),
            "chain_result": chain_result,
            "chain_artifacts": _chain_artifacts_from_result(chain_result),
        }
    )
    result["validation"] = validate_chain_artifact_generation_result(result)
    if write_generator_report:
        result["generator_artifacts"] = _write_generator_artifacts(result=result, output_dir=output_text)
        result["validation"] = validate_chain_artifact_generation_result(result)
    return result


def validate_chain_artifact_generation_result(result: Dict[str, Any]) -> Dict[str, Any]:
    reason_codes: List[str] = []
    warning_codes: List[str] = []

    if _clean_text(result.get("execution_mode")) != EXECUTION_MODE:
        reason_codes.append("execution_mode_not_explicit_operator_generation")
    if not _clean_text(result.get("queue_input_artifact_path")):
        reason_codes.append("missing_explicit_queue_input")
    if not _clean_text(result.get("output_dir")):
        reason_codes.append("missing_explicit_output_dir")
    context = dict(result.get("context") or {})
    for flag in ["require_explicit_input", "require_explicit_output_dir"]:
        value = result.get(flag) if flag in result else context.get(flag)
        if not bool(value):
            reason_codes.append(f"{flag}_false")
    if bool(result.get("did_mutate_production")):
        reason_codes.append("did_mutate_production")

    for flag in [
        "allow_production_mutation",
        "allow_live_pipeline_wiring",
        "allow_application_submission",
        "allow_queue_action_update",
        "allow_packet_update",
        "allow_tailoring_generation_update",
        "allow_scoring_update",
        "allow_ranking_update",
    ]:
        if bool(result.get(flag)):
            reason_codes.append(f"{flag}_true")

    chain_result = dict(result.get("chain_result") or {})
    if chain_result:
        chain_validation = read_only_adapter_chain.validate_read_only_adapter_chain_result(chain_result)
        if _clean_text(chain_result.get("execution_mode")) != read_only_adapter_chain.EXECUTION_MODE:
            reason_codes.append("chain_execution_mode_not_manual_read_only_adapter_chain")
        if bool(chain_result.get("did_mutate_production")):
            reason_codes.append("chain_did_mutate_production")
        if bool(chain_result.get("allow_live_pipeline_wiring")):
            reason_codes.append("chain_allow_live_pipeline_wiring_true")
        if bool(chain_result.get("allow_application_submission")):
            reason_codes.append("chain_allow_application_submission_true")
        if list(chain_result.get("adapter_execution_order") or []) != read_only_adapter_chain.ADAPTER_EXECUTION_ORDER:
            reason_codes.append("chain_adapter_order_mismatch")
        if _clean_text(chain_validation.get("validation_status")) == "failed":
            reason_codes.append("chain_validation_failed")
        if _clean_text(chain_validation.get("validation_status")) == "warning":
            warning_codes.append("chain_validation_warning")
    elif bool(result.get("did_run_chain")):
        reason_codes.append("did_run_chain_without_chain_result")

    root_names = set(_root_file_names(result.get("output_dir")))
    production_root_names = sorted(root_names.intersection(PRODUCTION_ROOT_ARTIFACT_NAMES))
    if production_root_names:
        reason_codes.append("production_artifact_name_written_at_output_root")

    for artifact in list(result.get("generator_artifacts") or []):
        name = Path(_clean_text(artifact)).name
        if name not in GENERATOR_ARTIFACT_NAMES:
            reason_codes.append("non_generator_artifact_written")

    unique_reasons = sorted(set(reason_codes + list(result.get("reason_codes") or [])))
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
        "did_mutate_production": bool(result.get("did_mutate_production")),
        "did_run_chain": bool(result.get("did_run_chain")),
        "output_root_file_names": sorted(root_names),
    }


def render_chain_artifact_generation_report_markdown(result: Dict[str, Any] | None = None) -> str:
    payload = deepcopy(result) if result is not None else generate_read_only_chain_artifacts(
        write_generator_report=False
    )
    validation = dict(payload.get("validation") or validate_chain_artifact_generation_result(payload))
    summary = dict(payload.get("chain_result_summary") or {})
    lines = [
        "# Explicit Read-Only Chain Artifact Generation",
        "",
        "Operator-triggered diagnostic utility only. It requires an explicit queue input and explicit output directory.",
        "It does not update queue action, packet generation, tailoring generation, scoring, ranking, live pipeline wiring, or application submission.",
        "",
        f"Generator version: `{_clean_text(payload.get('generator_version'))}`",
        f"Execution mode: `{_clean_text(payload.get('execution_mode'))}`",
        f"Did run chain: `{bool(payload.get('did_run_chain'))}`",
        f"Did mutate production: `{bool(payload.get('did_mutate_production'))}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Inputs",
        "",
        f"- Queue input: `{_clean_text(payload.get('queue_input_artifact_path')) or 'none'}`",
        f"- Output dir: `{_clean_text(payload.get('output_dir')) or 'none'}`",
        "",
        "## Chain Summary",
        "",
        f"- Input rows: `{int(summary.get('input_row_count') or 0)}`",
        f"- Adapters executed: `{int(summary.get('adapters_executed_count') or 0)}`",
        f"- Job prioritization recommendations: `{int(summary.get('job_prioritization_recommendation_count') or 0)}`",
        f"- Tailoring decisions: `{int(summary.get('tailoring_decision_count') or 0)}`",
        f"- Operator review lanes: `{int(summary.get('operator_review_lane_count') or 0)}`",
        "",
        "## Artifacts",
        "",
    ]
    for artifact in list(payload.get("chain_artifacts") or []):
        lines.append(f"- Chain: `{artifact}`")
    for artifact in list(payload.get("generator_artifacts") or []):
        lines.append(f"- Generator: `{artifact}`")
    if not list(payload.get("chain_artifacts") or []) and not list(payload.get("generator_artifacts") or []):
        lines.append("- none")
    if validation.get("reason_codes"):
        lines.extend(["", "## Reason Codes", ""])
        lines.extend(f"- `{code}`" for code in validation.get("reason_codes", []) or [])
    return "\n".join(lines).strip() + "\n"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate manual read-only adapter chain diagnostics.")
    parser.add_argument("--queue-input", default="", help="Required explicit application_execution_queue.csv-like input path.")
    parser.add_argument("--output-dir", default="", help="Required explicit output directory for diagnostics.")
    parser.add_argument("--pipeline-run-id", default="", help="Optional diagnostic pipeline run id.")
    parser.add_argument("--owner-user-id", default="", help="Optional diagnostic owner user id.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    payload = generate_read_only_chain_artifacts(
        queue_input_artifact_path=args.queue_input,
        output_dir=args.output_dir,
        pipeline_run_id=args.pipeline_run_id,
        owner_user_id=args.owner_user_id,
    )
    validation = dict(payload.get("validation") or {})
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Read-only chain artifact generation: {validation.get('validation_status', '')}")
        print(f"Did run chain: {bool(payload.get('did_run_chain'))}")
        print(f"Output dir: {_clean_text(payload.get('output_dir')) or 'none'}")
    return 0 if validation.get("validation_status") == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
