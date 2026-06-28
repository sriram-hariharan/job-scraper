"""Default-off dry-run command for JD-enriched planning artifact routing."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.jd_intelligence_planning_artifact_enricher_default_off import (
    build_jd_intelligence_planning_artifact_enricher_default_off,
)


PHASE = "34C"


class DryRunLoadError(ValueError):
    """Raised when an input artifact cannot be loaded."""


def _ensure_row_list(value: Any, *, source: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise DryRunLoadError(f"{source} must contain a list of row objects")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise DryRunLoadError(f"{source} row {index} must be a JSON object")
        rows.append(dict(item))
    return rows


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DryRunLoadError(f"invalid JSON: {exc.msg}") from exc
    except OSError as exc:
        raise DryRunLoadError(f"unreadable file: {exc}") from exc


def _load_planning_json(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="json")
    if isinstance(payload, dict):
        for key in ("planning_rows", "rows", "items", "jobs"):
            if key in payload:
                return _ensure_row_list(payload[key], source=f"json.{key}")
    raise DryRunLoadError(
        "json must be a row list or include planning_rows, rows, items, or jobs"
    )


def _load_jsonl_rows(path: Path, *, source: str) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DryRunLoadError(f"unreadable file: {exc}") from exc

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DryRunLoadError(
                f"invalid JSONL on line {line_number}: {exc.msg}"
            ) from exc
        if not isinstance(payload, dict):
            raise DryRunLoadError(
                f"{source} line {line_number} must be a JSON object"
            )
        rows.append(dict(payload))
    return rows


def _load_csv_rows(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise DryRunLoadError("invalid CSV: missing header")
            return [dict(row) for row in reader]
    except csv.Error as exc:
        raise DryRunLoadError(f"invalid CSV: {exc}") from exc
    except OSError as exc:
        raise DryRunLoadError(f"unreadable file: {exc}") from exc


def load_planning_rows_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load planning-like rows from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _load_planning_json(artifact_path)
    if suffix == ".jsonl":
        return _load_jsonl_rows(artifact_path, source="jsonl")
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported planning artifact extension: {suffix}")


def load_provider_responses_from_path(path: str | Path) -> list[Any] | dict[str, Any]:
    """Load supplied provider responses from JSON or JSONL."""

    response_path = Path(path)
    suffix = response_path.suffix.lower()
    if suffix == ".jsonl":
        return _load_jsonl_rows(response_path, source="provider jsonl")
    if suffix != ".json":
        raise DryRunLoadError(f"unsupported provider responses extension: {suffix}")

    payload = _read_json(response_path)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, dict):
        for key in ("provider_responses", "responses", "items", "rows"):
            if key in payload:
                value = payload[key]
                if isinstance(value, (list, dict)):
                    return deepcopy(value)
                raise DryRunLoadError(
                    f"json.{key} must contain a list or keyed dictionary"
                )
        return deepcopy(payload)
    raise DryRunLoadError(
        "provider responses json must be a list, keyed dictionary, or include "
        "provider_responses, responses, items, or rows"
    )


def _dry_run_key(
    *,
    row_count: int,
    llm_enabled: bool,
    ready_count: int,
    blocked_count: int,
    next_step_counts: dict[str, int],
) -> str:
    steps = ",".join(
        f"{step}:{count}" for step, count in sorted(next_step_counts.items())
    )
    return "|".join(
        (
            f"phase={PHASE}",
            f"rows={row_count}",
            f"llm_enabled={llm_enabled}",
            f"ready={ready_count}",
            f"blocked={blocked_count}",
            f"steps={steps}",
        )
    )


def build_dry_run_payload(
    planning_rows: list[dict[str, Any]] | None = None,
    enable_llm: bool = False,
    provider_responses: list[Any] | dict[str, Any] | None = None,
    extraction_policy: dict[str, Any] | None = None,
    router_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only JD enrichment dry-run payload."""

    rows = planning_rows if isinstance(planning_rows, list) else []
    llm_enabled = enable_llm is True
    enricher_result = build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=rows,
        enable_llm=llm_enabled,
        provider_responses=provider_responses,
        extraction_policy=extraction_policy,
        router_policy=router_policy,
    )
    grouped = deepcopy(enricher_result.get("grouped_by_next_allowed_step", {}))
    counts = deepcopy(enricher_result.get("next_step_counts", {}))
    ready = int(enricher_result.get("extraction_ready_count", 0))
    blocked = int(enricher_result.get("extraction_blocked_count", 0))
    row_count = len(rows)
    return {
        "phase": PHASE,
        "default_off": True,
        "jd_intelligence_planning_artifact_enrichment_dry_run": True,
        "dry_run_command_only": True,
        "llm_capable": True,
        "llm_enabled": llm_enabled,
        "read_only": True,
        "advisory_only": True,
        "requires_manual_user_control": True,
        "planning_row_count": row_count,
        "provider_responses_present": provider_responses is not None,
        "enricher_result": deepcopy(enricher_result),
        "grouped_by_next_allowed_step": grouped,
        "next_step_counts": counts,
        "extraction_ready_count": ready,
        "extraction_blocked_count": blocked,
        "dry_run_summary": {
            "planning_row_count": row_count,
            "provider_responses_present": provider_responses is not None,
            "extraction_ready_count": ready,
            "extraction_blocked_count": blocked,
            "next_step_counts": counts,
            "stdout_only": True,
            "output_file_written": False,
            "provider_callable_accepted": False,
        },
        "dry_run_key": _dry_run_key(
            row_count=row_count,
            llm_enabled=llm_enabled,
            ready_count=ready,
            blocked_count=blocked,
            next_step_counts=counts,
        ),
        "stage_execution_performed": False,
        "relevance_prefilter_performed": False,
        "final_scoring_performed": False,
        "tailoring_opportunity_check_performed": False,
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
        description="Default-off JD enrichment dry-run for planning artifacts."
    )
    parser.add_argument("--input", dest="input_path", help="Planning artifact path.")
    parser.add_argument(
        "--enable-llm",
        action="store_true",
        help="Enable Phase 34B parsing of supplied provider responses.",
    )
    parser.add_argument(
        "--provider-responses",
        dest="provider_responses_path",
        help="Optional JSON or JSONL provider response artifact.",
    )
    parser.add_argument(
        "--score-threshold",
        dest="score_threshold",
        type=float,
        help="Optional final score threshold for router policy.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the JD enrichment dry-run command."""

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
        responses = (
            load_provider_responses_from_path(args.provider_responses_path)
            if args.provider_responses_path
            else None
        )
        payload = build_dry_run_payload(
            planning_rows=rows,
            enable_llm=args.enable_llm,
            provider_responses=responses,
            router_policy=router_policy,
        )
    except DryRunLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
