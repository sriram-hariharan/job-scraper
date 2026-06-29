"""Default-off dry-run command for JD evidence scoring feature packets."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.jd_evidence_final_scoring_feature_adapter_default_off import (
    build_jd_evidence_final_scoring_feature_adapter_default_off,
)


PHASE = "36B"
PLANNING_LIST_KEYS = ("planning_rows", "rows", "items", "jobs", "feature_rows")
EVIDENCE_RESULT_KEYS = (
    "evidence_results",
    "results",
    "items",
    "rows",
    "feature_rows",
    "scoring_feature_rows",
)
FALSE_ACTION_KEYS = (
    "final_score_produced",
    "existing_score_changed",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "final_scoring_performed",
    "matching_scoring_module_called",
    "tailoring_opportunity_check_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
)


class DryRunLoadError(ValueError):
    """Raised when dry-run input cannot be loaded deterministically."""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DryRunLoadError(f"unreadable file: {exc}") from exc


def _read_json(path: Path) -> Any:
    try:
        return json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise DryRunLoadError(f"invalid JSON: {exc.msg}") from exc


def _ensure_row_list(value: Any, *, source: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise DryRunLoadError(f"{source} must contain a list of row objects")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise DryRunLoadError(f"{source} row {index} must be a JSON object")
        rows.append(dict(item))
    return rows


def _load_planning_json(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="json")
    if isinstance(payload, dict):
        for key in PLANNING_LIST_KEYS:
            if key in payload:
                return _ensure_row_list(payload[key], source=f"json.{key}")
    raise DryRunLoadError(
        "json must be a row list or include planning_rows, rows, items, jobs, or feature_rows"
    )


def _load_jsonl_rows(path: Path, *, source: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(_read_text(path).splitlines(), start=1):
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


def _extract_evidence_results_json(payload: Any) -> list[Any] | dict[str, Any]:
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, dict):
        for key in EVIDENCE_RESULT_KEYS:
            if key in payload:
                value = payload[key]
                if isinstance(value, (list, dict)):
                    return deepcopy(value)
                raise DryRunLoadError(
                    f"json.{key} must contain a list or keyed dictionary"
                )
        return deepcopy(payload)
    raise DryRunLoadError(
        "evidence results json must be a list, keyed dictionary, or supported wrapper"
    )


def load_evidence_results_from_path(path: str | Path) -> list[Any] | dict[str, Any]:
    """Load evidence results from JSON, JSONL, or CSV."""

    evidence_path = Path(path)
    suffix = evidence_path.suffix.lower()
    if suffix == ".json":
        return _extract_evidence_results_json(_read_json(evidence_path))
    if suffix == ".jsonl":
        return _load_jsonl_rows(evidence_path, source="evidence results jsonl")
    if suffix == ".csv":
        return _load_csv_rows(evidence_path)
    raise DryRunLoadError(f"unsupported evidence results extension: {suffix}")


def _policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "high_required_skill_coverage_threshold": float(
            args.high_required_skill_coverage_threshold
        ),
        "low_required_skill_coverage_threshold": float(
            args.low_required_skill_coverage_threshold
        ),
        "high_tool_coverage_threshold": float(args.high_tool_coverage_threshold),
        "red_flag_review_threshold": int(args.red_flag_review_threshold),
    }


def _dry_run_key(
    *,
    row_count: int,
    ready_count: int,
    missing_count: int,
    high_count: int,
    low_count: int,
    red_review_count: int,
) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"rows={row_count}",
            f"ready={ready_count}",
            f"missing={missing_count}",
            f"high={high_count}",
            f"low={low_count}",
            f"red_review={red_review_count}",
        )
    )


def build_dry_run_payload(
    planning_rows: list[dict[str, Any]] | None = None,
    evidence_results: Any = None,
    feature_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 36B scoring feature dry-run payload."""

    rows = planning_rows if isinstance(planning_rows, list) else []
    policy = deepcopy(feature_policy) if isinstance(feature_policy, dict) else {}
    adapter_result = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=rows,
        evidence_results=evidence_results,
        feature_policy=policy,
    )
    ready_count = int(adapter_result.get("evidence_ready_count", 0))
    missing_count = int(adapter_result.get("evidence_missing_count", 0))
    high_count = int(adapter_result.get("high_coverage_count", 0))
    low_count = int(adapter_result.get("low_coverage_count", 0))
    red_review_count = int(adapter_result.get("red_flag_review_count", 0))
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_final_scoring_feature_adapter_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "deterministic_scoring_feature_preparation": True,
        "requires_manual_user_control": True,
        "planning_row_count": len(rows),
        "evidence_results_present": evidence_results not in (None, "", [], {}),
        "feature_policy": policy,
        "adapter_result": deepcopy(adapter_result),
        "feature_packet": deepcopy(adapter_result.get("feature_packet", {})),
        "scoring_feature_rows": deepcopy(
            adapter_result.get("scoring_feature_rows", [])
        ),
        "scoring_feature_summary": deepcopy(
            adapter_result.get("scoring_feature_summary", {})
        ),
        "existing_score_fields_detected": deepcopy(
            adapter_result.get("existing_score_fields_detected", [])
        ),
        "existing_scores_preserved": bool(
            adapter_result.get("existing_scores_preserved", False)
        ),
        "evidence_ready_count": ready_count,
        "evidence_missing_count": missing_count,
        "high_coverage_count": high_count,
        "low_coverage_count": low_count,
        "red_flag_review_count": red_review_count,
        "dry_run_summary": {
            "planning_row_count": len(rows),
            "evidence_results_present": evidence_results not in (None, "", [], {}),
            "feature_row_count": len(adapter_result.get("feature_rows", [])),
            "evidence_ready_count": ready_count,
            "evidence_missing_count": missing_count,
            "high_coverage_count": high_count,
            "low_coverage_count": low_count,
            "red_flag_review_count": red_review_count,
            "stdout_only": True,
            "output_file_written": False,
            "final_score_produced": False,
            "existing_score_changed": False,
        },
        "dry_run_key": _dry_run_key(
            row_count=len(rows),
            ready_count=ready_count,
            missing_count=missing_count,
            high_count=high_count,
            low_count=low_count,
            red_review_count=red_review_count,
        ),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Default-off JD evidence final-scoring feature dry-run."
    )
    parser.add_argument("--input", dest="input_path", help="Planning artifact path.")
    parser.add_argument(
        "--evidence-results",
        dest="evidence_results_path",
        help="Optional evidence results path.",
    )
    parser.add_argument(
        "--high-required-skill-coverage-threshold",
        dest="high_required_skill_coverage_threshold",
        type=float,
        default=0.8,
    )
    parser.add_argument(
        "--low-required-skill-coverage-threshold",
        dest="low_required_skill_coverage_threshold",
        type=float,
        default=0.5,
    )
    parser.add_argument(
        "--high-tool-coverage-threshold",
        dest="high_tool_coverage_threshold",
        type=float,
        default=0.8,
    )
    parser.add_argument(
        "--red-flag-review-threshold",
        dest="red_flag_review_threshold",
        type=int,
        default=1,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 36B dry-run command."""

    try:
        args = _parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    if not args.input_path:
        print("error: --input is required", file=sys.stderr)
        return 2

    try:
        rows = load_planning_rows_from_path(args.input_path)
        evidence = (
            load_evidence_results_from_path(args.evidence_results_path)
            if args.evidence_results_path
            else None
        )
        payload = build_dry_run_payload(
            planning_rows=rows,
            evidence_results=evidence,
            feature_policy=_policy_from_args(args),
        )
    except DryRunLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
