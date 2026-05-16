from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.storage.scheduler_artifacts_store import upsert_scheduler_artifact


DEFAULT_POST_RUN_EMAIL_OUTBOX_DIR = Path("postgres_artifacts/scheduler/post_run_email_outbox")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_job_name(value: Any) -> str:
    text = _clean_text(value).lower()
    return text.replace("-", "_").replace(" ", "_")


def _dict_or_empty(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _status_token(value: Any) -> str:
    normalized = _clean_text(value).lower()
    if normalized == "succeeded":
        return "SUCCEEDED"
    if normalized == "failed":
        return "FAILED"
    return "UNKNOWN"


def _mapping_lines(mapping: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    for key in sorted(mapping):
        lines.append(f"- {key}: {mapping[key]}")
    return lines


def _nested_mapping_lines(mapping: Dict[str, Any]) -> List[str]:
    lines: List[str] = []

    for outer_key in sorted(mapping):
        inner = _dict_or_empty(mapping.get(outer_key))
        if not inner:
            lines.append(f"- {outer_key}: <empty>")
            continue

        inner_text = ", ".join(
            f"{inner_key}={inner[inner_key]}"
            for inner_key in sorted(inner)
        )
        lines.append(f"- {outer_key}: {inner_text}")

    return lines


def _render_agent_discovery_subject(summary: Dict[str, Any]) -> str:
    status_token = _status_token(summary.get("status"))
    rollup_counts = _dict_or_empty(summary.get("rollup_counts"))
    total_discovered = sum(_safe_int(value, 0) for value in rollup_counts.values())

    if status_token == "FAILED":
        failure_components = _list_or_empty(summary.get("failure_components"))
        failure_suffix = ",".join(str(item) for item in failure_components) or "error"
        return f"Scheduled job {status_token} | agent_discovery | {failure_suffix}"

    return f"Scheduled job {status_token} | agent_discovery | discovered={total_discovered}"


def _render_live_pipeline_subject(summary: Dict[str, Any]) -> str:
    status_token = _status_token(summary.get("status"))
    final_job_count = summary.get("final_job_count")

    if final_job_count is None:
        final_job_count = _dict_or_empty(summary.get("counts")).get("final_jobs")

    if status_token == "FAILED":
        stage = _clean_text(summary.get("current_stage")) or "error"
        return f"Scheduled job {status_token} | live_pipeline | stage={stage}"

    return f"Scheduled job {status_token} | live_pipeline | final_jobs={final_job_count}"


def _render_agent_discovery_body(
    summary: Dict[str, Any],
    *,
    post_run_summary_path: str,
) -> str:
    lines = [
        "Scheduled Job Summary",
        f"Job: {summary.get('job_name', '')}",
        f"Run ID: {summary.get('run_id', '')}",
        f"Status: {summary.get('status', '')}",
        f"Started At: {summary.get('started_at', '')}",
        f"Finished At: {summary.get('finished_at', '')}",
        f"Summary: {summary.get('summary_message', '')}",
        f"Normalized Summary Path: {post_run_summary_path}",
        f"Source Artifact Type: {summary.get('artifact_type', '')}",
        f"Source Artifact Path: {summary.get('artifact_path', '')}",
    ]

    error = _clean_text(summary.get("error"))
    if error:
        lines.append(f"Error: {error}")

    component_statuses = _dict_or_empty(summary.get("component_statuses"))
    if component_statuses:
        lines.append("")
        lines.append("Component Statuses:")
        lines.extend(_mapping_lines(component_statuses))

    failure_components = _list_or_empty(summary.get("failure_components"))
    if failure_components:
        lines.append("")
        lines.append("Failure Components:")
        lines.extend(f"- {item}" for item in failure_components)

    component_errors = _dict_or_empty(summary.get("component_errors"))
    if component_errors:
        lines.append("")
        lines.append("Component Errors:")
        lines.extend(_mapping_lines(component_errors))

    rollup_counts = _dict_or_empty(summary.get("rollup_counts"))
    if rollup_counts:
        lines.append("")
        lines.append("Run Unique Discovered By ATS:")
        lines.extend(_mapping_lines(rollup_counts))

    source_counts = _dict_or_empty(summary.get("source_counts"))
    if source_counts:
        lines.append("")
        lines.append("Source Counts:")
        lines.extend(_nested_mapping_lines(source_counts))

    return "\n".join(lines).strip()


def _render_live_pipeline_body(
    summary: Dict[str, Any],
    *,
    post_run_summary_path: str,
) -> str:
    lines = [
        "Scheduled Job Summary",
        f"Job: {summary.get('job_name', '')}",
        f"Run ID: {summary.get('run_id', '')}",
        f"Status: {summary.get('status', '')}",
        f"Started At: {summary.get('started_at', '')}",
        f"Finished At: {summary.get('finished_at', '')}",
        f"Summary: {summary.get('summary_message', '')}",
        f"Final Job Count: {summary.get('final_job_count', '')}",
        f"Normalized Summary Path: {post_run_summary_path}",
        f"Source Artifact Type: {summary.get('artifact_type', '')}",
        f"Source Artifact Path: {summary.get('artifact_path', '')}",
        f"Log Path: {summary.get('log_path', '')}",
        f"Status Path: {summary.get('status_path', '')}",
    ]

    current_stage = _clean_text(summary.get("current_stage"))
    if current_stage:
        lines.append(f"Current Stage: {current_stage}")

    error = _clean_text(summary.get("error"))
    if error:
        lines.append(f"Error: {error}")

    completed_stages = _list_or_empty(summary.get("completed_stages"))
    if completed_stages:
        lines.append("")
        lines.append("Completed Stages:")
        lines.extend(f"- {item}" for item in completed_stages)

    counts = _dict_or_empty(summary.get("counts"))
    if counts:
        lines.append("")
        lines.append("Counts:")
        lines.extend(_mapping_lines(counts))

    config = _dict_or_empty(summary.get("config"))
    if config:
        lines.append("")
        lines.append("Config:")
        lines.extend(_mapping_lines(config))

    return "\n".join(lines).strip()


def build_post_run_email_payload(
    summary: Dict[str, Any],
    *,
    post_run_summary_path: str = "",
) -> Dict[str, Any]:
    normalized_summary = dict(summary)
    job_name = _normalize_job_name(normalized_summary.get("job_name"))

    if job_name == "agent_discovery":
        subject = _render_agent_discovery_subject(normalized_summary)
        body_text = _render_agent_discovery_body(
            normalized_summary,
            post_run_summary_path=post_run_summary_path,
        )
    elif job_name == "live_pipeline":
        subject = _render_live_pipeline_subject(normalized_summary)
        body_text = _render_live_pipeline_body(
            normalized_summary,
            post_run_summary_path=post_run_summary_path,
        )
    else:
        subject = (
            f"Scheduled job {_status_token(normalized_summary.get('status'))} | "
            f"{job_name or 'unknown_job'}"
        )
        body_text = "\n".join(
            [
                "Scheduled Job Summary",
                f"Job: {normalized_summary.get('job_name', '')}",
                f"Run ID: {normalized_summary.get('run_id', '')}",
                f"Status: {normalized_summary.get('status', '')}",
                f"Summary: {normalized_summary.get('summary_message', '')}",
                f"Normalized Summary Path: {post_run_summary_path}",
            ]
        ).strip()

    return {
        "message_kind": "scheduled_run_summary_email",
        "rendered_at": _utc_now(),
        "delivery_status": "rendered_outbox_only",
        "delivery_provider": "",
        "delivery_error": "",
        "job_name": job_name,
        "run_id": _clean_text(normalized_summary.get("run_id")),
        "status": _clean_text(normalized_summary.get("status")),
        "subject": subject,
        "body_text": body_text,
        "post_run_summary_path": _clean_text(post_run_summary_path),
        "source_artifact_type": _clean_text(normalized_summary.get("artifact_type")),
        "source_artifact_path": _clean_text(normalized_summary.get("artifact_path")),
    }


def _post_run_email_output_path(
    summary: Dict[str, Any],
    *,
    output_dir: Any = DEFAULT_POST_RUN_EMAIL_OUTBOX_DIR,
) -> Path:
    job_name = _normalize_job_name(summary.get("job_name")) or "scheduled_job"
    run_id = _clean_text(summary.get("run_id")) or "unknown_run"

    return Path(str(output_dir)).expanduser() / f"{run_id}__{job_name}__email_outbox.json"


def write_post_run_email_outbox_artifact(
    summary: Dict[str, Any],
    *,
    post_run_summary_path: str = "",
    output_dir: Any = DEFAULT_POST_RUN_EMAIL_OUTBOX_DIR,
) -> Dict[str, Any]:
    payload = build_post_run_email_payload(
        summary,
        post_run_summary_path=post_run_summary_path,
    )

    output_path = _post_run_email_output_path(
        summary,
        output_dir=output_dir,
    )

    artifact = upsert_scheduler_artifact(
        run_id=_clean_text(payload.get("run_id")),
        job_name=_clean_text(payload.get("job_name")),
        artifact_kind="post_run_email_outbox",
        artifact_name=output_path.name,
        payload_json=payload,
    )

    payload["outbox_path"] = artifact["artifact_ref"]

    return {
        "path": artifact["artifact_ref"],
        "payload": payload,
        "artifact_id": artifact["artifact_id"],
        "storage_backend": "postgres",
    }
