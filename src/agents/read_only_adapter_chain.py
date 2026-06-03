from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.agents import (
    read_only_job_prioritization_adapter,
    read_only_operator_review_adapter,
    read_only_tailoring_decision_adapter,
)


CHAIN_VERSION = "manual_read_only_adapter_chain_v1"
EXECUTION_MODE = "manual_read_only_adapter_chain"
RESULT_JSON_NAME = "read_only_adapter_chain_result.json"
REPORT_MD_NAME = "read_only_adapter_chain_report.md"
ADAPTER_EXECUTION_ORDER = ["job_prioritization", "tailoring_decision", "operator_review"]

SAFE_CHAIN_ARTIFACT_NAMES = {RESULT_JSON_NAME, REPORT_MD_NAME}
SAFE_ADAPTER_ARTIFACT_NAMES = {
    read_only_job_prioritization_adapter.RESULT_JSON_NAME,
    read_only_job_prioritization_adapter.REPORT_MD_NAME,
    read_only_job_prioritization_adapter.RECOMMENDATIONS_CSV_NAME,
    read_only_tailoring_decision_adapter.RESULT_JSON_NAME,
    read_only_tailoring_decision_adapter.REPORT_MD_NAME,
    read_only_tailoring_decision_adapter.DECISIONS_CSV_NAME,
    read_only_operator_review_adapter.RESULT_JSON_NAME,
    read_only_operator_review_adapter.REPORT_MD_NAME,
    read_only_operator_review_adapter.REVIEWS_CSV_NAME,
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_read_only_adapter_chain_context(
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    queue_input_artifact_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    created_at_utc: str = "",
) -> Dict[str, Any]:
    return {
        "chain_version": CHAIN_VERSION,
        "execution_mode": EXECUTION_MODE,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "queue_input_artifact_path": _clean_text(queue_input_artifact_path),
        "output_dir": _clean_text(output_dir),
        "created_at_utc": _clean_text(created_at_utc) or _utc_now_iso(),
        "allow_production_mutation": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_generation_update": False,
        "allow_scoring_update": False,
        "allow_ranking_update": False,
        "allow_application_submission": False,
        "allow_live_pipeline_wiring": False,
    }


def load_read_only_adapter_chain_inputs(
    *,
    queue_rows: List[Dict[str, Any]] | None = None,
    queue_input_artifact_path: str | Path | None = None,
) -> Dict[str, Any]:
    if queue_rows is not None:
        rows = [dict(row) for row in deepcopy(queue_rows)]
        return {
            "load_status": "loaded",
            "input_source": "queue_rows",
            "queue_input_artifact_path": "",
            "rows": rows,
            "row_count": len(rows),
            "reason_codes": [],
        }

    path_text = _clean_text(queue_input_artifact_path)
    if path_text:
        path = Path(path_text)
        if not path.exists() or not path.is_file():
            return {
                "load_status": "warning",
                "input_source": "queue_input_artifact_path",
                "queue_input_artifact_path": path_text,
                "rows": [],
                "row_count": 0,
                "reason_codes": ["input_artifact_not_found"],
            }
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = [dict(row) for row in csv.DictReader(handle)]
        return {
            "load_status": "loaded",
            "input_source": "queue_input_artifact_path",
            "queue_input_artifact_path": path_text,
            "rows": rows,
            "row_count": len(rows),
            "reason_codes": [],
        }

    return {
        "load_status": "warning",
        "input_source": "none",
        "queue_input_artifact_path": "",
        "rows": [],
        "row_count": 0,
        "reason_codes": ["no_queue_rows_or_path"],
    }


def _base_result(
    *,
    context: Dict[str, Any],
    rows: List[Dict[str, Any]],
    reason_codes: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "chain_version": CHAIN_VERSION,
        "execution_mode": EXECUTION_MODE,
        "pipeline_run_id": _clean_text(context.get("pipeline_run_id")),
        "owner_user_id": _clean_text(context.get("owner_user_id")),
        "context": dict(context),
        "did_execute_chain": False,
        "did_mutate_production": False,
        "allow_production_mutation": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_generation_update": False,
        "allow_scoring_update": False,
        "allow_ranking_update": False,
        "allow_application_submission": False,
        "allow_live_pipeline_wiring": False,
        "adapter_execution_order": list(ADAPTER_EXECUTION_ORDER),
        "adapter_results": {},
        "summary": {
            "input_row_count": len(rows),
            "job_prioritization_recommendation_count": 0,
            "tailoring_decision_count": 0,
            "operator_review_lane_count": 0,
            "adapters_executed_count": 0,
            "warning_count": len(reason_codes or []),
        },
        "artifacts_written": [],
        "reason_codes": list(reason_codes or []),
    }


def _adapter_output_dir(output_dir: str | Path | None, adapter_key: str) -> str:
    if not output_dir:
        return ""
    return str(Path(output_dir) / adapter_key)


def run_read_only_adapter_chain(
    *,
    queue_rows: List[Dict[str, Any]] | None = None,
    queue_input_artifact_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
) -> Dict[str, Any]:
    context = build_read_only_adapter_chain_context(
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        queue_input_artifact_path=queue_input_artifact_path,
        output_dir=output_dir,
    )
    loaded = load_read_only_adapter_chain_inputs(
        queue_rows=queue_rows,
        queue_input_artifact_path=queue_input_artifact_path,
    )
    loaded_rows = [dict(row) for row in list(loaded.get("rows") or [])]
    reason_codes = list(loaded.get("reason_codes") or [])

    if not loaded_rows:
        result = _base_result(context=context, rows=loaded_rows, reason_codes=reason_codes or ["no_queue_rows_or_path"])
        result["validation"] = validate_read_only_adapter_chain_result(result)
        if output_dir:
            result["artifacts_written"] = _write_chain_artifacts(result=result, output_dir=output_dir)
            result["validation"] = validate_read_only_adapter_chain_result(result)
        return result

    job_result = read_only_job_prioritization_adapter.run_job_prioritization_read_only_adapter(
        rows=deepcopy(loaded_rows),
        output_dir=_adapter_output_dir(output_dir, "job_prioritization"),
        pipeline_run_id=_clean_text(context.get("pipeline_run_id")),
        owner_user_id=_clean_text(context.get("owner_user_id")),
    )
    prioritization_rows = [dict(row) for row in list(job_result.get("recommendations") or [])]

    tailoring_result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_rows=deepcopy(loaded_rows),
        prioritization_rows=prioritization_rows,
        output_dir=_adapter_output_dir(output_dir, "tailoring_decision"),
        pipeline_run_id=_clean_text(context.get("pipeline_run_id")),
        owner_user_id=_clean_text(context.get("owner_user_id")),
    )
    tailoring_rows = [dict(row) for row in list(tailoring_result.get("decisions") or [])]

    operator_result = read_only_operator_review_adapter.run_operator_review_read_only_adapter(
        queue_rows=deepcopy(loaded_rows),
        prioritization_rows=prioritization_rows,
        tailoring_rows=tailoring_rows,
        output_dir=_adapter_output_dir(output_dir, "operator_review"),
        pipeline_run_id=_clean_text(context.get("pipeline_run_id")),
        owner_user_id=_clean_text(context.get("owner_user_id")),
    )

    adapter_results = {
        "job_prioritization": job_result,
        "tailoring_decision": tailoring_result,
        "operator_review": operator_result,
    }
    warning_count = len(reason_codes)
    warning_count += sum(
        1
        for item in adapter_results.values()
        if _clean_text(dict(item.get("validation") or {}).get("validation_status")) == "warning"
    )
    result = _base_result(context=context, rows=loaded_rows, reason_codes=reason_codes)
    result.update(
        {
            "did_execute_chain": any(bool(item.get("did_execute_agent")) for item in adapter_results.values()),
            "adapter_results": adapter_results,
            "summary": {
                "input_row_count": len(loaded_rows),
                "job_prioritization_recommendation_count": int(job_result.get("recommendation_count") or 0),
                "tailoring_decision_count": int(tailoring_result.get("decision_count") or 0),
                "operator_review_lane_count": int(operator_result.get("lane_count") or 0),
                "adapters_executed_count": sum(
                    1 for item in adapter_results.values() if bool(item.get("did_execute_agent"))
                ),
                "warning_count": warning_count,
            },
        }
    )
    result["validation"] = validate_read_only_adapter_chain_result(result)
    if output_dir:
        result["artifacts_written"] = _collect_adapter_artifacts(adapter_results)
        result["artifacts_written"].extend(_write_chain_artifacts(result=result, output_dir=output_dir))
        result["validation"] = validate_read_only_adapter_chain_result(result)
    return result


def _adapter_result_has_unsafe_flags(result: Dict[str, Any]) -> bool:
    for flag in [
        "allow_production_mutation",
        "allow_queue_action_update",
        "allow_packet_update",
        "allow_tailoring_update",
        "allow_tailoring_generation_update",
        "allow_scoring_update",
        "allow_ranking_update",
        "allow_application_submission",
    ]:
        if bool(result.get(flag)):
            return True
    return False


def validate_read_only_adapter_chain_result(result: Dict[str, Any]) -> Dict[str, Any]:
    reason_codes: List[str] = []
    warning_codes: List[str] = []

    if _clean_text(result.get("execution_mode")) != EXECUTION_MODE:
        reason_codes.append("execution_mode_not_manual_read_only_adapter_chain")
    if bool(result.get("did_mutate_production")):
        reason_codes.append("did_mutate_production")
    for flag in [
        "allow_production_mutation",
        "allow_queue_action_update",
        "allow_packet_update",
        "allow_tailoring_generation_update",
        "allow_scoring_update",
        "allow_ranking_update",
        "allow_application_submission",
        "allow_live_pipeline_wiring",
    ]:
        if bool(result.get(flag)):
            reason_codes.append(f"{flag}_true")
    if list(result.get("adapter_execution_order") or []) != ADAPTER_EXECUTION_ORDER:
        reason_codes.append("adapter_order_mismatch")

    adapter_results = dict(result.get("adapter_results") or {})
    for adapter_key in ADAPTER_EXECUTION_ORDER:
        adapter_result = dict(adapter_results.get(adapter_key) or {})
        if not adapter_result:
            continue
        if bool(adapter_result.get("did_mutate_production")):
            reason_codes.append(f"{adapter_key}:did_mutate_production")
        if _adapter_result_has_unsafe_flags(adapter_result):
            reason_codes.append(f"{adapter_key}:unsafe_flag_true")
        adapter_validation = dict(adapter_result.get("validation") or {})
        if _clean_text(adapter_validation.get("validation_status")) == "failed":
            reason_codes.append(f"{adapter_key}:validation_failed")
        if _clean_text(adapter_validation.get("validation_status")) == "warning":
            warning_codes.append(f"{adapter_key}:validation_warning")

    if not bool(result.get("did_execute_chain")):
        warning_codes.append("chain_not_executed")

    bad_artifacts = []
    for artifact in list(result.get("artifacts_written") or []):
        name = Path(_clean_text(artifact)).name
        if name not in SAFE_CHAIN_ARTIFACT_NAMES and name not in SAFE_ADAPTER_ARTIFACT_NAMES:
            bad_artifacts.append(artifact)
    if bad_artifacts:
        reason_codes.append("non_chain_diagnostic_artifact_written")

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
        "adapter_execution_order": list(result.get("adapter_execution_order") or []),
        "did_mutate_production": bool(result.get("did_mutate_production")),
    }


def render_read_only_adapter_chain_report_markdown(result: Dict[str, Any] | None = None) -> str:
    payload = deepcopy(result) if result is not None else run_read_only_adapter_chain()
    validation = dict(payload.get("validation") or validate_read_only_adapter_chain_result(payload))
    summary = dict(payload.get("summary") or {})
    lines = [
        "# Manual Read-Only Adapter Chain",
        "",
        "Manual diagnostic chain only. It does not update queue action, packet generation, tailoring generation, scoring, ranking, application submission, or production artifacts.",
        "",
        f"Chain version: `{_clean_text(payload.get('chain_version'))}`",
        f"Execution mode: `{_clean_text(payload.get('execution_mode'))}`",
        f"Did execute chain: `{bool(payload.get('did_execute_chain'))}`",
        f"Did mutate production: `{bool(payload.get('did_mutate_production'))}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Summary",
        "",
        f"- Input rows: `{int(summary.get('input_row_count') or 0)}`",
        f"- Job prioritization recommendations: `{int(summary.get('job_prioritization_recommendation_count') or 0)}`",
        f"- Tailoring decisions: `{int(summary.get('tailoring_decision_count') or 0)}`",
        f"- Operator review lanes: `{int(summary.get('operator_review_lane_count') or 0)}`",
        f"- Adapters executed: `{int(summary.get('adapters_executed_count') or 0)}`",
        "",
        "## Adapter Order",
        "",
    ]
    for adapter_key in list(payload.get("adapter_execution_order") or []):
        adapter_result = dict(dict(payload.get("adapter_results") or {}).get(adapter_key) or {})
        lines.append(
            f"- `{adapter_key}`: did_execute=`{bool(adapter_result.get('did_execute_agent'))}` "
            f"validation=`{dict(adapter_result.get('validation') or {}).get('validation_status', '')}`"
        )
    if not list(payload.get("adapter_execution_order") or []):
        lines.append("- none")
    return "\n".join(lines).strip() + "\n"


def _collect_adapter_artifacts(adapter_results: Dict[str, Dict[str, Any]]) -> List[str]:
    artifacts: List[str] = []
    for adapter_key in ADAPTER_EXECUTION_ORDER:
        artifacts.extend(
            _clean_text(path)
            for path in list(dict(adapter_results.get(adapter_key) or {}).get("artifacts_written") or [])
            if _clean_text(path)
        )
    return artifacts


def _write_chain_artifacts(*, result: Dict[str, Any], output_dir: str | Path) -> List[str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / RESULT_JSON_NAME
    md_path = root / REPORT_MD_NAME

    serializable = deepcopy(result)
    serializable["artifacts_written"] = []
    json_path.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_read_only_adapter_chain_report_markdown(result), encoding="utf-8")
    return [str(json_path), str(md_path)]


def write_read_only_adapter_chain_artifacts(
    *,
    output_dir: str | Path,
    result: Dict[str, Any] | None = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = deepcopy(result) if result is not None else run_read_only_adapter_chain(output_dir=output_dir, **kwargs)
    if result is not None:
        artifacts = _write_chain_artifacts(result=payload, output_dir=output_dir)
        payload["artifacts_written"] = list(payload.get("artifacts_written") or []) + artifacts
        payload["validation"] = validate_read_only_adapter_chain_result(payload)
    return {
        "json_path": str(Path(output_dir) / RESULT_JSON_NAME),
        "md_path": str(Path(output_dir) / REPORT_MD_NAME),
        "payload": payload,
        "validation_status": payload.get("validation", {}).get("validation_status", ""),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the manual read-only adapter chain.")
    parser.add_argument("--queue-input", default="", help="Explicit application_execution_queue.csv-like input path.")
    parser.add_argument("--output-dir", default="", help="Optional isolated directory for chain diagnostics.")
    parser.add_argument("--pipeline-run-id", default="", help="Optional diagnostic pipeline run id.")
    parser.add_argument("--owner-user-id", default="", help="Optional diagnostic owner user id.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    payload = run_read_only_adapter_chain(
        queue_input_artifact_path=args.queue_input,
        output_dir=args.output_dir,
        pipeline_run_id=args.pipeline_run_id,
        owner_user_id=args.owner_user_id,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        validation = dict(payload.get("validation") or {})
        summary = dict(payload.get("summary") or {})
        print(f"Manual read-only adapter chain: {validation.get('validation_status', '')}")
        print(f"Input rows: {summary.get('input_row_count', 0)}")
        print(f"Adapters executed: {summary.get('adapters_executed_count', 0)}")
    return 0 if payload.get("validation", {}).get("validation_status") in {"passed", "warning"} else 1


if __name__ == "__main__":
    sys.exit(main())
