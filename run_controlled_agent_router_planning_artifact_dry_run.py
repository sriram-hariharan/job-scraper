"""Read-only dry-run command for planning artifact router handoffs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.controlled_agent_router_planning_artifact_mapper_readonly import (
    build_controlled_agent_router_planning_artifact_mapper_readonly,
)


PHASE = "33E"


class PlanningArtifactLoadError(ValueError):
    """Raised when a planning artifact cannot be loaded deterministically."""


def _ensure_row_list(value: Any, *, source: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise PlanningArtifactLoadError(f"{source} must contain a list of rows")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise PlanningArtifactLoadError(
                f"{source} row {index} must be a JSON object"
            )
        rows.append(dict(item))
    return rows


def _load_json(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PlanningArtifactLoadError(f"invalid JSON: {exc.msg}") from exc

    if isinstance(payload, list):
        return _ensure_row_list(payload, source="json")
    if isinstance(payload, dict):
        for key in ("planning_rows", "rows", "items", "jobs"):
            if key in payload:
                return _ensure_row_list(payload[key], source=f"json.{key}")
    raise PlanningArtifactLoadError(
        "json must be a row list or include planning_rows, rows, items, or jobs"
    )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise PlanningArtifactLoadError(f"unreadable file: {exc}") from exc

    for line_number, line in enumerate(lines, start=1):
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise PlanningArtifactLoadError(
                f"invalid JSONL on line {line_number}: {exc.msg}"
            ) from exc
        if not isinstance(payload, dict):
            raise PlanningArtifactLoadError(
                f"jsonl line {line_number} must be a JSON object"
            )
        rows.append(dict(payload))
    return rows


def _load_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except csv.Error as exc:
        raise PlanningArtifactLoadError(f"invalid CSV: {exc}") from exc


def load_planning_rows_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load planning-like rows from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    try:
        if suffix == ".json":
            return _load_json(artifact_path)
        if suffix == ".jsonl":
            return _load_jsonl(artifact_path)
        if suffix == ".csv":
            return _load_csv(artifact_path)
    except OSError as exc:
        raise PlanningArtifactLoadError(f"unreadable file: {exc}") from exc

    raise PlanningArtifactLoadError(f"unsupported planning artifact extension: {suffix}")


def _dry_run_key(
    *,
    planning_row_count: int,
    next_step_counts: dict[str, int],
) -> str:
    count_pairs = ",".join(
        f"{step}:{count}" for step, count in sorted(next_step_counts.items())
    )
    return "|".join(
        (
            f"phase={PHASE}",
            f"rows={planning_row_count}",
            f"steps={count_pairs}",
        )
    )


def build_dry_run_payload(
    planning_rows: list[dict[str, Any]] | None = None,
    router_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read-only grouped router handoff dry-run payload."""

    rows = planning_rows if isinstance(planning_rows, list) else []
    mapper_result = build_controlled_agent_router_planning_artifact_mapper_readonly(
        planning_rows=rows,
        router_policy=router_policy,
    )
    grouped = deepcopy(mapper_result.get("grouped_by_next_allowed_step", {}))
    counts = deepcopy(mapper_result.get("next_step_counts", {}))
    row_count = len(rows)
    return {
        "phase": PHASE,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "dry_run_command_only": True,
        "planning_artifact_dry_run": True,
        "allowlisted_routing_only": True,
        "requires_manual_user_control": True,
        "planning_row_count": row_count,
        "mapper_result": deepcopy(mapper_result),
        "grouped_by_next_allowed_step": grouped,
        "next_step_counts": counts,
        "dry_run_summary": {
            "planning_row_count": row_count,
            "mapped_item_count": len(mapper_result.get("mapped_items", [])),
            "unmapped_row_count": len(mapper_result.get("unmapped_rows", [])),
            "next_step_counts": counts,
            "stdout_only": True,
            "output_file_written": False,
        },
        "dry_run_key": _dry_run_key(
            planning_row_count=row_count,
            next_step_counts=counts,
        ),
        "no_llm_calls": True,
        "llm_call_performed": False,
        "no_provider_calls": True,
        "provider_call_performed": False,
        "no_network_calls": True,
        "network_call_performed": False,
        "dispatch_performed": False,
        "stage_execution_performed": False,
        "tailoring_runtime_call_performed": False,
        "ai_tailoring_generation_performed": False,
        "real_tailoring_output_created": False,
        "resume_rewrite_performed": False,
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
        "database_write_performed": False,
        "persistence_performed": False,
        "execution_performed": False,
        "submission_performed": False,
        "auto_apply_performed": False,
        "auto_submit_performed": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only dry-run for controlled router planning artifacts."
    )
    parser.add_argument("--input", dest="input_path", help="Planning artifact path.")
    parser.add_argument(
        "--score-threshold",
        dest="score_threshold",
        type=float,
        help="Optional final score threshold for router policy.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the read-only dry-run command."""

    try:
        args = _parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    if not args.input_path:
        print("error: --input is required", file=sys.stderr)
        return 2

    router_policy = None
    if args.score_threshold is not None:
        router_policy = {"final_score_threshold": args.score_threshold}

    try:
        rows = load_planning_rows_from_path(args.input_path)
        payload = build_dry_run_payload(
            planning_rows=rows,
            router_policy=router_policy,
        )
    except PlanningArtifactLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
