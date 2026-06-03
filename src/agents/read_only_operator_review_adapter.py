from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.agents import operator_review_agent


ADAPTER_VERSION = "operator_review_read_only_adapter_v1"
AGENT_KEY = "operator_review"
EXECUTION_MODE = "read_only_adapter"
RESULT_JSON_NAME = "operator_review_read_only_adapter_result.json"
REPORT_MD_NAME = "operator_review_read_only_adapter_report.md"
REVIEWS_CSV_NAME = "operator_review_read_only_adapter_reviews.csv"

PRODUCTION_ACTION_FIELDS = {
    "action",
    "queue_action",
    "application_action",
    "packet_status",
    "tailoring_status",
    "tailoring_generation_status",
    "score",
    "rank",
    "application_submitted",
    "application_submission_status",
    "submitted_at",
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


def _production_snapshot(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [
        {
            "job_key": _job_key(row),
            "job_id": _clean_text(row.get("job_id") or row.get("job_doc_id") or row.get("doc_id")),
            "company": _clean_text(row.get("company") or row.get("job_company")),
            "title": _clean_text(row.get("title") or row.get("job_title")),
            "action": _clean_text(row.get("action") or row.get("existing_action")),
            "queue_action": _clean_text(row.get("queue_action")),
            "application_action": _clean_text(row.get("application_action")),
            "packet_status": _clean_text(row.get("packet_status")),
            "tailoring_status": _clean_text(row.get("tailoring_status")),
            "tailoring_generation_status": _clean_text(row.get("tailoring_generation_status")),
            "score": _clean_text(row.get("score")),
            "rank": _clean_text(row.get("rank")),
            "application_submitted": _clean_text(row.get("application_submitted")),
            "application_submission_status": _clean_text(row.get("application_submission_status")),
            "submitted_at": _clean_text(row.get("submitted_at")),
        }
        for row in rows
    ]


def build_operator_review_adapter_context(
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    queue_input_artifact_path: str | Path | None = None,
    prioritization_input_artifact_path: str | Path | None = None,
    tailoring_input_artifact_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    created_at_utc: str = "",
) -> Dict[str, Any]:
    return {
        "adapter_version": ADAPTER_VERSION,
        "agent_key": AGENT_KEY,
        "execution_mode": EXECUTION_MODE,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "queue_input_artifact_path": _clean_text(queue_input_artifact_path),
        "prioritization_input_artifact_path": _clean_text(prioritization_input_artifact_path),
        "tailoring_input_artifact_path": _clean_text(tailoring_input_artifact_path),
        "output_dir": _clean_text(output_dir),
        "created_at_utc": _clean_text(created_at_utc) or _utc_now_iso(),
        "allow_production_mutation": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_generation_update": False,
        "allow_scoring_update": False,
        "allow_ranking_update": False,
        "allow_application_submission": False,
    }


def _load_csv_rows(path_text: str) -> Dict[str, Any]:
    path = Path(path_text)
    if not path.exists() or not path.is_file():
        return {
            "load_status": "warning",
            "rows": [],
            "row_count": 0,
            "reason_codes": ["input_artifact_not_found"],
        }
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    return {
        "load_status": "loaded",
        "rows": rows,
        "row_count": len(rows),
        "reason_codes": [],
    }


def _load_explicit_rows_or_path(
    *,
    rows: List[Dict[str, Any]] | None,
    path: str | Path | None,
    missing_reason_code: str,
    row_source: str,
    path_source: str,
) -> Dict[str, Any]:
    if rows is not None:
        safe_rows = [dict(row) for row in deepcopy(rows)]
        return {
            "load_status": "loaded",
            "input_source": row_source,
            "input_artifact_path": "",
            "rows": safe_rows,
            "row_count": len(safe_rows),
            "reason_codes": [],
        }

    path_text = _clean_text(path)
    if path_text:
        loaded = _load_csv_rows(path_text)
        return {
            "input_source": path_source,
            "input_artifact_path": path_text,
            **loaded,
        }

    return {
        "load_status": "warning",
        "input_source": "none",
        "input_artifact_path": "",
        "rows": [],
        "row_count": 0,
        "reason_codes": [missing_reason_code],
    }


def _overlay_rows(
    *,
    queue_rows: List[Dict[str, Any]],
    prioritization_rows: List[Dict[str, Any]],
    tailoring_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    prioritization_by_key = {
        _job_key(row): dict(row)
        for row in prioritization_rows
        if _job_key(row)
    }
    tailoring_by_key = {
        _job_key(row): dict(row)
        for row in tailoring_rows
        if _job_key(row)
    }
    prioritization_fields = {
        "advisory_priority",
        "deterministic_winner_score",
        "fallback_only_no_deterministic_match",
        "packet_generation_allowed",
        "packet_generation_block_reason",
        "critic_decision",
        "source_recommendation",
    }
    tailoring_fields = {
        "tailoring_decision",
        "critic_decision",
        "packet_generation_allowed",
        "packet_generation_block_reason",
        "winner_resume",
        "resolved_resume",
    }
    merged_rows: List[Dict[str, Any]] = []
    for row in queue_rows:
        merged = dict(row)
        prioritization_row = prioritization_by_key.get(_job_key(row), {})
        tailoring_row = tailoring_by_key.get(_job_key(row), {})
        for field in prioritization_fields:
            if _clean_text(prioritization_row.get(field)) and not _clean_text(merged.get(field)):
                merged[field] = prioritization_row.get(field)
        for field in tailoring_fields:
            if _clean_text(tailoring_row.get(field)) and not _clean_text(merged.get(field)):
                merged[field] = tailoring_row.get(field)
        merged_rows.append(merged)
    return merged_rows


def load_operator_review_adapter_inputs(
    *,
    queue_rows: List[Dict[str, Any]] | None = None,
    queue_input_artifact_path: str | Path | None = None,
    prioritization_rows: List[Dict[str, Any]] | None = None,
    prioritization_input_artifact_path: str | Path | None = None,
    tailoring_rows: List[Dict[str, Any]] | None = None,
    tailoring_input_artifact_path: str | Path | None = None,
) -> Dict[str, Any]:
    queue = _load_explicit_rows_or_path(
        rows=queue_rows,
        path=queue_input_artifact_path,
        missing_reason_code="no_queue_rows_or_path",
        row_source="queue_rows",
        path_source="queue_input_artifact_path",
    )
    prioritization = _load_explicit_rows_or_path(
        rows=prioritization_rows,
        path=prioritization_input_artifact_path,
        missing_reason_code="no_prioritization_rows_or_path",
        row_source="prioritization_rows",
        path_source="prioritization_input_artifact_path",
    )
    tailoring = _load_explicit_rows_or_path(
        rows=tailoring_rows,
        path=tailoring_input_artifact_path,
        missing_reason_code="no_tailoring_rows_or_path",
        row_source="tailoring_rows",
        path_source="tailoring_input_artifact_path",
    )
    loaded_queue_rows = [dict(row) for row in list(queue.get("rows") or [])]
    loaded_prioritization_rows = [dict(row) for row in list(prioritization.get("rows") or [])]
    loaded_tailoring_rows = [dict(row) for row in list(tailoring.get("rows") or [])]
    rows = _overlay_rows(
        queue_rows=loaded_queue_rows,
        prioritization_rows=loaded_prioritization_rows,
        tailoring_rows=loaded_tailoring_rows,
    )
    reason_codes = list(queue.get("reason_codes") or [])
    for source in [prioritization, tailoring]:
        reason_codes.extend(
            code
            for code in list(source.get("reason_codes") or [])
            if code not in {"no_prioritization_rows_or_path", "no_tailoring_rows_or_path"}
        )
    return {
        "load_status": "loaded" if loaded_queue_rows else "warning",
        "queue": queue,
        "prioritization": prioritization,
        "tailoring": tailoring,
        "rows": rows,
        "row_count": len(rows),
        "reason_codes": reason_codes,
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
        "agent_name": operator_review_agent.AGENT_NAME,
        "execution_mode": EXECUTION_MODE,
        "pipeline_run_id": _clean_text(context.get("pipeline_run_id")),
        "owner_user_id": _clean_text(context.get("owner_user_id")),
        "context": dict(context),
        "did_execute_agent": False,
        "did_mutate_production": False,
        "allow_production_mutation": False,
        "allow_queue_action_update": False,
        "allow_packet_update": False,
        "allow_tailoring_generation_update": False,
        "allow_scoring_update": False,
        "allow_ranking_update": False,
        "allow_application_submission": False,
        "row_count": len(loaded_rows),
        "lane_count": 0,
        "reviews": [],
        "input_production_snapshot": _production_snapshot(loaded_rows),
        "summary": {
            "agent_name": operator_review_agent.AGENT_NAME,
            "agent_version": operator_review_agent.AGENT_VERSION,
            "row_count": len(loaded_rows),
            "lane_counts": {},
            "validation_status": "warning",
            "reason_codes": list(reason_codes or []),
        },
        "artifacts_written": [],
        "reason_codes": list(reason_codes or []),
    }


def run_operator_review_read_only_adapter(
    *,
    queue_rows: List[Dict[str, Any]] | None = None,
    queue_input_artifact_path: str | Path | None = None,
    prioritization_rows: List[Dict[str, Any]] | None = None,
    prioritization_input_artifact_path: str | Path | None = None,
    tailoring_rows: List[Dict[str, Any]] | None = None,
    tailoring_input_artifact_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
) -> Dict[str, Any]:
    context = build_operator_review_adapter_context(
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        queue_input_artifact_path=queue_input_artifact_path,
        prioritization_input_artifact_path=prioritization_input_artifact_path,
        tailoring_input_artifact_path=tailoring_input_artifact_path,
        output_dir=output_dir,
    )
    loaded = load_operator_review_adapter_inputs(
        queue_rows=queue_rows,
        queue_input_artifact_path=queue_input_artifact_path,
        prioritization_rows=prioritization_rows,
        prioritization_input_artifact_path=prioritization_input_artifact_path,
        tailoring_rows=tailoring_rows,
        tailoring_input_artifact_path=tailoring_input_artifact_path,
    )
    loaded_rows = [dict(row) for row in list(loaded.get("rows") or [])]
    reason_codes = list(loaded.get("reason_codes") or [])

    if not loaded_rows:
        result = _base_result(
            context=context,
            loaded_rows=loaded_rows,
            reason_codes=reason_codes or ["no_queue_rows"],
        )
        result["validation"] = validate_operator_review_adapter_result(result)
        if output_dir:
            result["artifacts_written"] = _write_adapter_artifacts(result=result, output_dir=output_dir)
        return result

    payload = operator_review_agent.render_operator_review(
        rows=loaded_rows,
        pipeline_run_id=_clean_text(context.get("pipeline_run_id")),
        owner_user_id=_clean_text(context.get("owner_user_id")),
        source_artifact_path=_clean_text(loaded.get("queue", {}).get("input_artifact_path")),
    )
    reviews = list(dict(payload.get("output") or {}).get("reviews") or [])
    summary = dict(payload.get("summary") or {})
    result = _base_result(context=context, loaded_rows=loaded_rows, reason_codes=reason_codes)
    result.update(
        {
            "did_execute_agent": True,
            "lane_count": len(reviews),
            "reviews": reviews,
            "summary": summary,
        }
    )
    result["validation"] = validate_operator_review_adapter_result(result)
    if output_dir:
        result["artifacts_written"] = _write_adapter_artifacts(result=result, output_dir=output_dir)
    return result


def validate_operator_review_adapter_result(result: Dict[str, Any]) -> Dict[str, Any]:
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
        "allow_tailoring_generation_update",
        "allow_scoring_update",
        "allow_ranking_update",
        "allow_application_submission",
    ]:
        if bool(result.get(flag)):
            reason_codes.append(f"{flag}_true")

    snapshots = {
        _clean_text(item.get("job_key")): dict(item)
        for item in list(result.get("input_production_snapshot") or [])
        if _clean_text(item.get("job_key"))
    }
    for review in list(result.get("reviews") or []):
        snapshot = snapshots.get(_job_key(review), {})
        expected_action = _clean_text(snapshot.get("action"))
        existing_action = _clean_text(review.get("existing_action"))
        if expected_action and existing_action != expected_action:
            reason_codes.append("existing_action_changed")
        for field in PRODUCTION_ACTION_FIELDS:
            if field in review:
                expected = expected_action if field in {"action", "queue_action", "application_action"} else _clean_text(snapshot.get(field))
                if _clean_text(review.get(field)) != expected:
                    reason_codes.append("production_action_field_written")

    if int(result.get("row_count") or 0) == 0:
        warning_codes.append("no_queue_rows")
    if bool(result.get("did_execute_agent")) and int(result.get("lane_count") or 0) == 0:
        reason_codes.append("executed_without_reviews")

    bad_artifacts = [
        artifact
        for artifact in list(result.get("artifacts_written") or [])
        if Path(_clean_text(artifact)).name
        not in {RESULT_JSON_NAME, REPORT_MD_NAME, REVIEWS_CSV_NAME}
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
        "lane_count": int(result.get("lane_count") or 0),
    }


def render_operator_review_adapter_report_markdown(result: Dict[str, Any] | None = None) -> str:
    payload = deepcopy(result) if result is not None else run_operator_review_read_only_adapter()
    validation = dict(payload.get("validation") or validate_operator_review_adapter_result(payload))
    summary = dict(payload.get("summary") or {})
    lines = [
        "# Operator Review Read-Only Adapter",
        "",
        "Manual read-only adapter prototype. It does not update queue action, packet generation, tailoring generation, scoring, ranking, or application submission.",
        "",
        f"Adapter version: `{_clean_text(payload.get('adapter_version'))}`",
        f"Execution mode: `{_clean_text(payload.get('execution_mode'))}`",
        f"Did execute agent: `{bool(payload.get('did_execute_agent'))}`",
        f"Did mutate production: `{bool(payload.get('did_mutate_production'))}`",
        f"Rows: `{int(payload.get('row_count') or 0)}`",
        f"Reviews: `{int(payload.get('lane_count') or 0)}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Lane Counts",
        "",
    ]
    counts = dict(summary.get("lane_counts") or {})
    if counts:
        for key, value in sorted(counts.items()):
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- none")
    lines.extend(["", "## Reviews", ""])
    for item in list(payload.get("reviews") or []):
        lines.append(
            f"- `{_clean_text(item.get('job_id')) or '-'}` "
            f"{_clean_text(item.get('company'))} / {_clean_text(item.get('title'))}: "
            f"`{_clean_text(item.get('operator_review_lane'))}`"
        )
    if not list(payload.get("reviews") or []):
        lines.append("- none")
    return "\n".join(lines).strip() + "\n"


def _write_adapter_artifacts(*, result: Dict[str, Any], output_dir: str | Path) -> List[str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / RESULT_JSON_NAME
    md_path = root / REPORT_MD_NAME
    csv_path = root / REVIEWS_CSV_NAME

    serializable = deepcopy(result)
    serializable["artifacts_written"] = []
    json_path.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_operator_review_adapter_report_markdown(result), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=operator_review_agent.OPERATOR_REVIEW_FIELDNAMES)
        writer.writeheader()
        for item in list(result.get("reviews") or []):
            row = {
                "job_id": _clean_text(item.get("job_id")),
                "company": _clean_text(item.get("company")),
                "title": _clean_text(item.get("title")),
                "source": _clean_text(item.get("source")),
                "existing_action": _clean_text(item.get("existing_action")),
                "advisory_priority": _clean_text(item.get("advisory_priority")),
                "tailoring_decision": _clean_text(item.get("tailoring_decision")),
                "operator_review_lane": _clean_text(item.get("operator_review_lane")),
                "operator_review_reason_codes": "|".join(
                    _clean_text(code)
                    for code in list(item.get("operator_reason_codes") or [])
                    if _clean_text(code)
                ),
                "deterministic_winner_score": _clean_text(item.get("deterministic_winner_score")),
                "fallback_only_no_deterministic_match": _clean_text(item.get("fallback_only_no_deterministic_match")),
                "packet_generation_allowed": _clean_text(item.get("packet_generation_allowed")),
                "packet_generation_block_reason": _clean_text(item.get("packet_generation_block_reason")),
                "critic_decision": _clean_text(item.get("critic_decision")),
                "source_recommendation": _clean_text(item.get("source_recommendation")),
                "winner_resume": _clean_text(item.get("winner_resume")),
                "resolved_resume": _clean_text(item.get("resolved_resume")),
            }
            writer.writerow({field: row.get(field, "") for field in operator_review_agent.OPERATOR_REVIEW_FIELDNAMES})
    return [str(json_path), str(md_path), str(csv_path)]


def write_operator_review_adapter_artifacts(
    *,
    output_dir: str | Path,
    result: Dict[str, Any] | None = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = deepcopy(result) if result is not None else run_operator_review_read_only_adapter(**kwargs)
    artifacts = _write_adapter_artifacts(result=payload, output_dir=output_dir)
    payload["artifacts_written"] = artifacts
    payload["validation"] = validate_operator_review_adapter_result(payload)
    return {
        "json_path": str(Path(output_dir) / RESULT_JSON_NAME),
        "md_path": str(Path(output_dir) / REPORT_MD_NAME),
        "csv_path": str(Path(output_dir) / REVIEWS_CSV_NAME),
        "payload": payload,
        "validation_status": payload.get("validation", {}).get("validation_status", ""),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Operator Review read-only adapter prototype.")
    parser.add_argument("--queue-input", default="", help="Explicit application_execution_queue.csv-like input path.")
    parser.add_argument("--prioritization-input", default="", help="Optional explicit job_prioritization_recommendations.csv-like input path.")
    parser.add_argument("--tailoring-input", default="", help="Optional explicit tailoring_decision_recommendations.csv-like input path.")
    parser.add_argument("--output-dir", default="", help="Optional isolated directory for adapter-specific diagnostics.")
    parser.add_argument("--pipeline-run-id", default="", help="Optional diagnostic pipeline run id.")
    parser.add_argument("--owner-user-id", default="", help="Optional diagnostic owner user id.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    payload = run_operator_review_read_only_adapter(
        queue_input_artifact_path=args.queue_input,
        prioritization_input_artifact_path=args.prioritization_input,
        tailoring_input_artifact_path=args.tailoring_input,
        output_dir=args.output_dir,
        pipeline_run_id=args.pipeline_run_id,
        owner_user_id=args.owner_user_id,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        validation = dict(payload.get("validation") or {})
        print(f"Operator Review read-only adapter: {validation.get('validation_status', '')}")
        print(f"Rows: {payload.get('row_count', 0)}")
        print(f"Reviews: {payload.get('lane_count', 0)}")
    return 0 if payload.get("validation", {}).get("validation_status") in {"passed", "warning"} else 1


if __name__ == "__main__":
    sys.exit(main())
