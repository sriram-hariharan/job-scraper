from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from src.agents.source_health_agent import build_source_health_agent_output_payload


SUMMARY_JSON_NAME = "agentic_workflow_summary.json"
SUMMARY_MD_NAME = "agentic_workflow_summary.md"

SUMMARY_ARTIFACT_NAMES = [
    "application_execution_queue.csv",
    "job_prioritization_recommendations.csv",
    "tailoring_decision_recommendations.csv",
    "operator_review_recommendations.csv",
    "source_health_report.csv",
    "best_resume_variant_by_job.csv",
    "job_packet_manifest.csv",
]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _counter(rows: Iterable[Dict[str, Any]], field: str) -> Dict[str, int]:
    counts = Counter(
        _clean_text(row.get(field)) or "<empty>"
        for row in rows
    )
    return dict(sorted(counts.items()))


def _truthy(value: Any) -> bool:
    return _clean_text(value).lower() in {"1", "true", "yes", "y", "on"}


def _first_nonblank(row: Dict[str, Any], *fields: str) -> str:
    for field in fields:
        value = _clean_text(row.get(field))
        if value:
            return value
    return ""


def _job_item(row: Dict[str, Any]) -> Dict[str, str]:
    return {
        "job_id": _first_nonblank(row, "job_id", "job_doc_id"),
        "company": _first_nonblank(row, "company", "job_company"),
        "title": _first_nonblank(row, "title", "job_title"),
        "source": _clean_text(row.get("source")),
        "existing_action": _first_nonblank(row, "existing_action", "action"),
        "advisory_priority": _clean_text(row.get("advisory_priority")),
        "tailoring_decision": _clean_text(row.get("tailoring_decision")),
        "operator_review_lane": _clean_text(row.get("operator_review_lane")),
        "winner_resume": _first_nonblank(row, "winner_resume", "resolved_resume"),
        "deterministic_winner_score": _first_nonblank(
            row,
            "deterministic_winner_score",
            "selector_winner_score",
            "winner_score",
            "resolved_score",
        ),
    }


def _source_recommendation_counts(source_health_rows: List[Dict[str, Any]]) -> Dict[str, int]:
    if not source_health_rows:
        return {}
    output_payload = build_source_health_agent_output_payload(source_health_rows)
    return _counter(output_payload.get("recommendations", []) or [], "recommendation")


def build_agentic_workflow_summary(
    *,
    queue_rows: List[Dict[str, Any]] | None = None,
    job_prioritization_rows: List[Dict[str, Any]] | None = None,
    tailoring_decision_rows: List[Dict[str, Any]] | None = None,
    operator_review_rows: List[Dict[str, Any]] | None = None,
    source_health_rows: List[Dict[str, Any]] | None = None,
    best_resume_rows: List[Dict[str, Any]] | None = None,
    packet_manifest_rows: List[Dict[str, Any]] | None = None,
    missing_artifacts: List[str] | None = None,
    generated_at_utc: str | None = None,
) -> Dict[str, Any]:
    queue_rows = list(queue_rows or [])
    job_prioritization_rows = list(job_prioritization_rows or [])
    tailoring_decision_rows = list(tailoring_decision_rows or [])
    operator_review_rows = list(operator_review_rows or [])
    source_health_rows = list(source_health_rows or [])
    best_resume_rows = list(best_resume_rows or [])
    packet_manifest_rows = list(packet_manifest_rows or [])

    packet_generated_rows = [
        row for row in packet_manifest_rows
        if _clean_text(row.get("packet_status")) == "generated"
    ]
    top_ready = [
        _job_item(row)
        for row in operator_review_rows
        if _clean_text(row.get("operator_review_lane")) == "ready_to_apply"
    ][:10]
    top_hold = [
        _job_item(row)
        for row in operator_review_rows
        if _clean_text(row.get("operator_review_lane")) == "hold_or_skip"
    ][:10]

    fallback_only_count = sum(
        1
        for row in queue_rows or best_resume_rows
        if _truthy(row.get("fallback_only_no_deterministic_match"))
    )
    packet_blocked_count = sum(
        1
        for row in queue_rows or packet_manifest_rows
        if _clean_text(row.get("packet_generation_allowed")).lower() == "false"
        or bool(_clean_text(row.get("packet_generation_block_reason")))
    )
    operator_counts = _counter(operator_review_rows, "operator_review_lane")

    return {
        "total_queue_jobs": len(queue_rows),
        "total_packet_jobs": len(packet_generated_rows),
        "advisory_priority_counts": _counter(job_prioritization_rows, "advisory_priority"),
        "tailoring_decision_counts": _counter(tailoring_decision_rows, "tailoring_decision"),
        "operator_review_lane_counts": operator_counts,
        "fallback_only_count": fallback_only_count,
        "packet_blocked_count": packet_blocked_count,
        "ready_to_apply_count": operator_counts.get("ready_to_apply", 0),
        "tailor_then_apply_count": operator_counts.get("tailor_then_apply", 0),
        "hold_or_skip_count": operator_counts.get("hold_or_skip", 0),
        "source_watch_count": operator_counts.get("source_watch", 0),
        "source_recommendation_counts": _source_recommendation_counts(source_health_rows),
        "top_ready_to_apply_jobs": top_ready,
        "top_hold_or_skip_jobs": top_hold,
        "missing_artifacts": sorted(set(missing_artifacts or [])),
        "generated_at_utc": generated_at_utc or _utc_now_iso(),
    }


def render_agentic_workflow_summary_markdown(summary: Dict[str, Any]) -> str:
    def count_line(label: str, counts: Dict[str, int]) -> str:
        if not counts:
            return f"- {label}: none"
        rendered = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        return f"- {label}: {rendered}"

    def job_lines(rows: List[Dict[str, Any]]) -> List[str]:
        if not rows:
            return ["- None"]
        lines = []
        for row in rows:
            company = _clean_text(row.get("company")) or "-"
            title = _clean_text(row.get("title")) or "-"
            score = _clean_text(row.get("deterministic_winner_score"))
            suffix = f" (score {score})" if score else ""
            lines.append(f"- {company} - {title}{suffix}")
        return lines

    lines = [
        "# Agentic Workflow Summary",
        "",
        "## Overview",
        f"- Generated at UTC: {_clean_text(summary.get('generated_at_utc'))}",
        f"- Total queue jobs: {int(summary.get('total_queue_jobs') or 0)}",
        f"- Total packet jobs: {int(summary.get('total_packet_jobs') or 0)}",
        "",
        "## Resume Match Safety",
        f"- Fallback-only rows: {int(summary.get('fallback_only_count') or 0)}",
        f"- Packet-blocked rows: {int(summary.get('packet_blocked_count') or 0)}",
        "",
        "## Source Health",
        count_line("Source recommendations", dict(summary.get("source_recommendation_counts") or {})),
        "",
        "## Job Prioritization",
        count_line("Advisory priorities", dict(summary.get("advisory_priority_counts") or {})),
        "",
        "## Tailoring Decision",
        count_line("Tailoring decisions", dict(summary.get("tailoring_decision_counts") or {})),
        "",
        "## Operator Review",
        count_line("Operator lanes", dict(summary.get("operator_review_lane_counts") or {})),
        "",
        "## Top Ready Jobs",
        *job_lines(list(summary.get("top_ready_to_apply_jobs") or [])),
        "",
        "## Hold / Skip Jobs",
        *job_lines(list(summary.get("top_hold_or_skip_jobs") or [])),
        "",
        "## Missing Artifacts",
    ]
    missing = list(summary.get("missing_artifacts") or [])
    lines.extend([f"- {name}" for name in missing] if missing else ["- None"])
    lines.append("")
    return "\n".join(lines)


def build_agentic_workflow_summary_from_dir(
    output_dir: str | Path,
    *,
    generated_at_utc: str | None = None,
) -> Dict[str, Any]:
    root = Path(output_dir)
    rows_by_name = {
        name: _read_csv_rows(root / name)
        for name in SUMMARY_ARTIFACT_NAMES
    }
    missing = [
        name for name in SUMMARY_ARTIFACT_NAMES
        if not (root / name).exists()
    ]
    return build_agentic_workflow_summary(
        queue_rows=rows_by_name["application_execution_queue.csv"],
        job_prioritization_rows=rows_by_name["job_prioritization_recommendations.csv"],
        tailoring_decision_rows=rows_by_name["tailoring_decision_recommendations.csv"],
        operator_review_rows=rows_by_name["operator_review_recommendations.csv"],
        source_health_rows=rows_by_name["source_health_report.csv"],
        best_resume_rows=rows_by_name["best_resume_variant_by_job.csv"],
        packet_manifest_rows=rows_by_name["job_packet_manifest.csv"],
        missing_artifacts=missing,
        generated_at_utc=generated_at_utc,
    )


def write_agentic_workflow_summary_artifacts(
    *,
    output_dir: str | Path,
    summary_json_path: str | Path | None = None,
    summary_md_path: str | Path | None = None,
    generated_at_utc: str | None = None,
) -> Dict[str, Any]:
    root = Path(output_dir)
    summary = build_agentic_workflow_summary_from_dir(
        root,
        generated_at_utc=generated_at_utc,
    )
    json_path = Path(summary_json_path) if summary_json_path else root / SUMMARY_JSON_NAME
    md_path = Path(summary_md_path) if summary_md_path else root / SUMMARY_MD_NAME
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_agentic_workflow_summary_markdown(summary), encoding="utf-8")
    return {
        "summary": summary,
        "summary_json_path": str(json_path),
        "summary_md_path": str(md_path),
    }
