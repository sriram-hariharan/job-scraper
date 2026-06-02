from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.agents import job_prioritization_agent


ADAPTER_VERSION = "job_prioritization_read_only_adapter_v1"
AGENT_KEY = "job_prioritization"
EXECUTION_MODE = "read_only_adapter"
RESULT_JSON_NAME = "job_prioritization_read_only_adapter_result.json"
REPORT_MD_NAME = "job_prioritization_read_only_adapter_report.md"
RECOMMENDATIONS_CSV_NAME = "job_prioritization_read_only_adapter_recommendations.csv"

PRODUCTION_ACTION_FIELDS = {
    "action",
    "queue_action",
    "application_action",
    "packet_status",
    "tailoring_status",
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_key(row: Dict[str, Any]) -> str:
    return "||".join(
        [
            _clean_text(row.get("job_id") or row.get("job_doc_id") or row.get("doc_id")),
            _clean_text(row.get("company") or row.get("job_company")),
            _clean_text(row.get("title") or row.get("job_title")),
        ]
    ).lower()


def _action_snapshot(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [
        {
            "job_key": _job_key(row),
            "job_id": _clean_text(row.get("job_id") or row.get("job_doc_id") or row.get("doc_id")),
            "company": _clean_text(row.get("company") or row.get("job_company")),
            "title": _clean_text(row.get("title") or row.get("job_title")),
            "action": _clean_text(row.get("action")),
        }
        for row in rows
    ]


def build_job_prioritization_adapter_context(
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    input_artifact_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    created_at_utc: str = "",
) -> Dict[str, Any]:
    return {
        "adapter_version": ADAPTER_VERSION,
        "agent_key": AGENT_KEY,
        "execution_mode": EXECUTION_MODE,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "input_artifact_path": _clean_text(input_artifact_path),
        "output_dir": _clean_text(output_dir),
        "created_at_utc": _clean_text(created_at_utc) or _utc_now_iso(),
        "allow_production_mutation": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_update": False,
    }


def load_job_prioritization_adapter_inputs(
    *,
    rows: List[Dict[str, Any]] | None = None,
    input_artifact_path: str | Path | None = None,
) -> Dict[str, Any]:
    if rows is not None:
        safe_rows = [dict(row) for row in deepcopy(rows)]
        return {
            "load_status": "loaded",
            "input_source": "rows",
            "input_artifact_path": "",
            "rows": safe_rows,
            "row_count": len(safe_rows),
            "reason_codes": [],
        }

    path_text = _clean_text(input_artifact_path)
    if path_text:
        path = Path(path_text)
        if not path.exists() or not path.is_file():
            return {
                "load_status": "warning",
                "input_source": "input_artifact_path",
                "input_artifact_path": path_text,
                "rows": [],
                "row_count": 0,
                "reason_codes": ["input_artifact_not_found"],
            }
        with path.open("r", encoding="utf-8", newline="") as handle:
            loaded_rows = [dict(row) for row in csv.DictReader(handle)]
        return {
            "load_status": "loaded",
            "input_source": "input_artifact_path",
            "input_artifact_path": path_text,
            "rows": loaded_rows,
            "row_count": len(loaded_rows),
            "reason_codes": [],
        }

    return {
        "load_status": "warning",
        "input_source": "none",
        "input_artifact_path": "",
        "rows": [],
        "row_count": 0,
        "reason_codes": ["no_input_rows_or_path"],
    }


def _base_result(
    *,
    context: Dict[str, Any],
    loaded_rows: List[Dict[str, Any]],
    reason_codes: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "adapter_version": ADAPTER_VERSION,
        "agent_key": AGENT_KEY,
        "agent_name": job_prioritization_agent.AGENT_NAME,
        "execution_mode": EXECUTION_MODE,
        "pipeline_run_id": _clean_text(context.get("pipeline_run_id")),
        "owner_user_id": _clean_text(context.get("owner_user_id")),
        "context": dict(context),
        "did_execute_agent": False,
        "did_mutate_production": False,
        "allow_production_mutation": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_update": False,
        "row_count": len(loaded_rows),
        "recommendation_count": 0,
        "recommendations": [],
        "input_action_snapshot": _action_snapshot(loaded_rows),
        "summary": {
            "agent_name": job_prioritization_agent.AGENT_NAME,
            "agent_version": job_prioritization_agent.AGENT_VERSION,
            "row_count": len(loaded_rows),
            "priority_counts": {},
            "validation_status": "warning",
            "reason_codes": list(reason_codes or []),
        },
        "artifacts_written": [],
        "reason_codes": list(reason_codes or []),
    }


def run_job_prioritization_read_only_adapter(
    *,
    rows: List[Dict[str, Any]] | None = None,
    input_artifact_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
) -> Dict[str, Any]:
    context = build_job_prioritization_adapter_context(
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        input_artifact_path=input_artifact_path,
        output_dir=output_dir,
    )
    loaded = load_job_prioritization_adapter_inputs(
        rows=rows,
        input_artifact_path=input_artifact_path,
    )
    loaded_rows = [dict(row) for row in list(loaded.get("rows") or [])]
    reason_codes = list(loaded.get("reason_codes") or [])

    if not loaded_rows:
        result = _base_result(
            context=context,
            loaded_rows=loaded_rows,
            reason_codes=reason_codes or ["no_input_rows"],
        )
        result["validation"] = validate_job_prioritization_adapter_result(result)
        if output_dir:
            result["artifacts_written"] = _write_adapter_artifacts(result=result, output_dir=output_dir)
        return result

    payload = job_prioritization_agent.render_job_prioritization_recommendations(
        rows=loaded_rows,
        pipeline_run_id=_clean_text(context.get("pipeline_run_id")),
        owner_user_id=_clean_text(context.get("owner_user_id")),
        source_artifact_path=_clean_text(loaded.get("input_artifact_path")),
    )
    recommendations = list(dict(payload.get("output") or {}).get("recommendations") or [])
    summary = dict(payload.get("summary") or {})
    result = _base_result(context=context, loaded_rows=loaded_rows, reason_codes=reason_codes)
    result.update(
        {
            "did_execute_agent": True,
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "summary": summary,
        }
    )
    result["validation"] = validate_job_prioritization_adapter_result(result)
    if output_dir:
        result["artifacts_written"] = _write_adapter_artifacts(result=result, output_dir=output_dir)
    return result


def validate_job_prioritization_adapter_result(result: Dict[str, Any]) -> Dict[str, Any]:
    reason_codes: List[str] = []
    warning_codes: List[str] = []

    if _clean_text(result.get("execution_mode")) != EXECUTION_MODE:
        reason_codes.append("execution_mode_not_read_only_adapter")
    if bool(result.get("did_mutate_production")):
        reason_codes.append("did_mutate_production")
    for flag in [
        "allow_production_mutation",
        "allow_queue_action_update",
        "allow_packet_update",
        "allow_tailoring_update",
    ]:
        if bool(result.get(flag)):
            reason_codes.append(f"{flag}_true")

    snapshots = {
        _clean_text(item.get("job_key")): dict(item)
        for item in list(result.get("input_action_snapshot") or [])
        if _clean_text(item.get("job_key"))
    }
    recommendations = list(result.get("recommendations") or [])
    for recommendation in recommendations:
        rec_key = _job_key(recommendation)
        snapshot = snapshots.get(rec_key, {})
        expected_action = _clean_text(snapshot.get("action"))
        existing_action = _clean_text(recommendation.get("existing_action"))
        original_action = _clean_text(recommendation.get("original_action"))
        if expected_action and existing_action != expected_action:
            reason_codes.append("existing_action_changed")
        if expected_action and original_action != expected_action:
            reason_codes.append("original_action_changed")
        changed_fields = [
            field
            for field in PRODUCTION_ACTION_FIELDS
            if field in recommendation and _clean_text(recommendation.get(field)) != expected_action
        ]
        if changed_fields:
            reason_codes.append("production_action_field_written")

    if int(result.get("row_count") or 0) == 0:
        warning_codes.append("no_input_rows")
    if bool(result.get("did_execute_agent")) and int(result.get("recommendation_count") or 0) == 0:
        reason_codes.append("executed_without_recommendations")

    bad_artifacts = [
        artifact
        for artifact in list(result.get("artifacts_written") or [])
        if Path(_clean_text(artifact)).name
        not in {RESULT_JSON_NAME, REPORT_MD_NAME, RECOMMENDATIONS_CSV_NAME}
    ]
    if bad_artifacts:
        reason_codes.append("non_adapter_artifact_written")

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
        "did_mutate_production": bool(result.get("did_mutate_production")),
        "recommendation_count": int(result.get("recommendation_count") or 0),
    }


def render_job_prioritization_adapter_report_markdown(result: Dict[str, Any] | None = None) -> str:
    payload = deepcopy(result) if result is not None else run_job_prioritization_read_only_adapter()
    validation = dict(payload.get("validation") or validate_job_prioritization_adapter_result(payload))
    summary = dict(payload.get("summary") or {})
    lines = [
        "# Job Prioritization Read-Only Adapter",
        "",
        "Manual read-only adapter prototype. It does not update queue action, packet generation, tailoring, scoring, or ranking.",
        "",
        f"Adapter version: `{_clean_text(payload.get('adapter_version'))}`",
        f"Execution mode: `{_clean_text(payload.get('execution_mode'))}`",
        f"Did execute agent: `{bool(payload.get('did_execute_agent'))}`",
        f"Did mutate production: `{bool(payload.get('did_mutate_production'))}`",
        f"Rows: `{int(payload.get('row_count') or 0)}`",
        f"Recommendations: `{int(payload.get('recommendation_count') or 0)}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Priority Counts",
        "",
    ]
    counts = dict(summary.get("priority_counts") or {})
    if counts:
        for key, value in sorted(counts.items()):
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- none")
    lines.extend(["", "## Recommendations", ""])
    for item in list(payload.get("recommendations") or []):
        lines.append(
            f"- `{_clean_text(item.get('job_id')) or '-'}` "
            f"{_clean_text(item.get('company'))} / {_clean_text(item.get('title'))}: "
            f"`{_clean_text(item.get('advisory_priority'))}`"
        )
    if not list(payload.get("recommendations") or []):
        lines.append("- none")
    return "\n".join(lines).strip() + "\n"


def _write_adapter_artifacts(*, result: Dict[str, Any], output_dir: str | Path) -> List[str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / RESULT_JSON_NAME
    md_path = root / REPORT_MD_NAME
    csv_path = root / RECOMMENDATIONS_CSV_NAME

    serializable = deepcopy(result)
    serializable["artifacts_written"] = []
    json_path.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_job_prioritization_adapter_report_markdown(result), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=job_prioritization_agent.RECOMMENDATION_FIELDNAMES)
        writer.writeheader()
        for item in list(result.get("recommendations") or []):
            row = {
                "job_id": _clean_text(item.get("job_id")),
                "company": _clean_text(item.get("company")),
                "title": _clean_text(item.get("title")),
                "source": _clean_text(item.get("source")),
                "existing_action": _clean_text(item.get("existing_action")),
                "advisory_priority": _clean_text(item.get("advisory_priority")),
                "advisory_reason_codes": "|".join(
                    _clean_text(code)
                    for code in list(item.get("advisory_reason_codes") or [])
                    if _clean_text(code)
                ),
                "deterministic_winner_score": _clean_text(item.get("deterministic_winner_score")),
                "fallback_only_no_deterministic_match": _clean_text(item.get("fallback_only_no_deterministic_match")),
                "packet_generation_allowed": _clean_text(item.get("packet_generation_allowed")),
                "packet_generation_block_reason": _clean_text(item.get("packet_generation_block_reason")),
                "source_recommendation": _clean_text(item.get("source_recommendation")),
                "critic_decision": _clean_text(item.get("critic_decision")),
            }
            writer.writerow({field: row.get(field, "") for field in job_prioritization_agent.RECOMMENDATION_FIELDNAMES})
    return [str(json_path), str(md_path), str(csv_path)]


def write_job_prioritization_adapter_artifacts(
    *,
    output_dir: str | Path,
    result: Dict[str, Any] | None = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = deepcopy(result) if result is not None else run_job_prioritization_read_only_adapter(**kwargs)
    artifacts = _write_adapter_artifacts(result=payload, output_dir=output_dir)
    payload["artifacts_written"] = artifacts
    payload["validation"] = validate_job_prioritization_adapter_result(payload)
    return {
        "json_path": str(Path(output_dir) / RESULT_JSON_NAME),
        "md_path": str(Path(output_dir) / REPORT_MD_NAME),
        "csv_path": str(Path(output_dir) / RECOMMENDATIONS_CSV_NAME),
        "payload": payload,
        "validation_status": payload.get("validation", {}).get("validation_status", ""),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Job Prioritization read-only adapter prototype.")
    parser.add_argument("--input", default="", help="Explicit application_execution_queue.csv-like input path.")
    parser.add_argument("--output-dir", default="", help="Optional isolated directory for adapter-specific diagnostics.")
    parser.add_argument("--pipeline-run-id", default="", help="Optional diagnostic pipeline run id.")
    parser.add_argument("--owner-user-id", default="", help="Optional diagnostic owner user id.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    payload = run_job_prioritization_read_only_adapter(
        input_artifact_path=args.input,
        output_dir=args.output_dir,
        pipeline_run_id=args.pipeline_run_id,
        owner_user_id=args.owner_user_id,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        validation = dict(payload.get("validation") or {})
        print(f"Job Prioritization read-only adapter: {validation.get('validation_status', '')}")
        print(f"Rows: {payload.get('row_count', 0)}")
        print(f"Recommendations: {payload.get('recommendation_count', 0)}")
    return 0 if payload.get("validation", {}).get("validation_status") in {"passed", "warning"} else 1


if __name__ == "__main__":
    sys.exit(main())
