"""Default-off dry-run command for JD signal evidence enrichment."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.jd_signal_planning_artifact_evidence_enricher_default_off import (
    build_jd_signal_planning_artifact_evidence_enricher_default_off,
)


PHASE = "35C"
PLANNING_LIST_KEYS = ("planning_rows", "rows", "items", "jobs")
EVIDENCE_KEYS = (
    "resume_evidence",
    "profile_evidence",
    "candidate_profile",
    "evidence",
    "rows",
    "items",
)
FALSE_ACTION_KEYS = (
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "final_scoring_performed",
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
        "json must be a row list or include planning_rows, rows, items, or jobs"
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


def _extract_resume_json_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, dict):
        for key in EVIDENCE_KEYS:
            if key in payload:
                return deepcopy(payload[key])
        return deepcopy(payload)
    raise DryRunLoadError(
        "resume evidence json must be a string, dictionary, list, or supported wrapper"
    )


def load_resume_evidence_from_path(path: str | Path) -> Any:
    """Load resume/profile evidence from JSON, JSONL, CSV, TXT, or MD."""

    evidence_path = Path(path)
    suffix = evidence_path.suffix.lower()
    if suffix == ".json":
        return _extract_resume_json_payload(_read_json(evidence_path))
    if suffix == ".jsonl":
        return _load_jsonl_rows(evidence_path, source="resume evidence jsonl")
    if suffix == ".csv":
        return _load_csv_rows(evidence_path)
    if suffix in (".txt", ".md"):
        return _read_text(evidence_path)
    raise DryRunLoadError(f"unsupported resume evidence extension: {suffix}")


def _policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "case_sensitive": bool(args.case_sensitive),
        "minimum_token_length": int(args.minimum_token_length),
        "include_partial_matches": args.no_partial_matches is not True,
    }


def _dry_run_key(
    *,
    row_count: int,
    ready_count: int,
    blocked_count: int,
    required_ratio: float,
    preferred_ratio: float,
) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"rows={row_count}",
            f"ready={ready_count}",
            f"blocked={blocked_count}",
            f"required={required_ratio:.6f}",
            f"preferred={preferred_ratio:.6f}",
        )
    )


def build_dry_run_payload(
    planning_rows: list[dict[str, Any]] | None = None,
    resume_evidence: Any = None,
    evidence_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 35C evidence enrichment dry-run payload."""

    rows = planning_rows if isinstance(planning_rows, list) else []
    policy = deepcopy(evidence_policy) if isinstance(evidence_policy, dict) else {}
    enricher_result = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=rows,
        resume_evidence=resume_evidence,
        evidence_policy=policy,
    )
    ready_count = int(enricher_result.get("evidence_ready_count", 0))
    blocked_count = int(enricher_result.get("evidence_blocked_count", 0))
    required_ratio = float(
        enricher_result.get("average_required_skill_coverage_ratio", 0.0)
    )
    preferred_ratio = float(
        enricher_result.get("average_preferred_skill_coverage_ratio", 0.0)
    )
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_signal_planning_artifact_evidence_enrichment_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "deterministic_evidence_matching": True,
        "requires_manual_user_control": True,
        "planning_row_count": len(rows),
        "resume_evidence_present": resume_evidence not in (None, "", [], {}),
        "evidence_policy": policy,
        "enricher_result": deepcopy(enricher_result),
        "evidence_ready_count": ready_count,
        "evidence_blocked_count": blocked_count,
        "coverage_summary": deepcopy(enricher_result.get("coverage_summary", {})),
        "average_required_skill_coverage_ratio": required_ratio,
        "average_preferred_skill_coverage_ratio": preferred_ratio,
        "average_tool_coverage_ratio": float(
            enricher_result.get("average_tool_coverage_ratio", 0.0)
        ),
        "average_responsibility_coverage_ratio": float(
            enricher_result.get("average_responsibility_coverage_ratio", 0.0)
        ),
        "missing_required_skills_by_row": deepcopy(
            enricher_result.get("missing_required_skills_by_row", {})
        ),
        "missing_tools_by_row": deepcopy(
            enricher_result.get("missing_tools_by_row", {})
        ),
        "red_flag_findings_by_row": deepcopy(
            enricher_result.get("red_flag_findings_by_row", {})
        ),
        "dry_run_summary": {
            "planning_row_count": len(rows),
            "resume_evidence_present": resume_evidence not in (None, "", [], {}),
            "evidence_ready_count": ready_count,
            "evidence_blocked_count": blocked_count,
            "stdout_only": True,
            "output_file_written": False,
            "final_application_score_created": False,
            "existing_score_changed": False,
        },
        "dry_run_key": _dry_run_key(
            row_count=len(rows),
            ready_count=ready_count,
            blocked_count=blocked_count,
            required_ratio=required_ratio,
            preferred_ratio=preferred_ratio,
        ),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Default-off JD signal evidence enrichment dry-run."
    )
    parser.add_argument("--input", dest="input_path", help="Planning artifact path.")
    parser.add_argument(
        "--resume-evidence",
        dest="resume_evidence_path",
        help="Optional resume/profile evidence path.",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Use case-sensitive evidence matching.",
    )
    parser.add_argument(
        "--minimum-token-length",
        dest="minimum_token_length",
        type=int,
        default=2,
        help="Minimum token length for partial evidence matches.",
    )
    parser.add_argument(
        "--no-partial-matches",
        action="store_true",
        help="Disable partial token evidence matches.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 35C dry-run command."""

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
            load_resume_evidence_from_path(args.resume_evidence_path)
            if args.resume_evidence_path
            else None
        )
        payload = build_dry_run_payload(
            planning_rows=rows,
            resume_evidence=evidence,
            evidence_policy=_policy_from_args(args),
        )
    except DryRunLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
