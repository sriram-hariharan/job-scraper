"""Default-off dry-run command for JD evidence score impact planning annotation."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.jd_evidence_score_impact_planning_artifact_annotator_default_off import (
    build_jd_evidence_score_impact_planning_artifact_annotator_default_off,
)


PHASE = "39B"
PLANNING_ROW_KEYS = (
    "planning_rows",
    "rows",
    "items",
    "jobs",
    "annotated_rows",
    "unannotated_rows",
)
IMPACT_ROW_KEYS = ("impact_rows", "rows", "items")
FALSE_ACTION_KEYS = (
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "scoring_feature_preparation_performed",
    "contribution_preview_performed",
    "score_impact_preview_performed",
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
            rows = [dict(row) for row in reader]
    except csv.Error as exc:
        raise DryRunLoadError(f"invalid CSV: {exc}") from exc
    except OSError as exc:
        raise DryRunLoadError(f"unreadable file: {exc}") from exc
    for index, row in enumerate(rows):
        if None in row:
            raise DryRunLoadError(f"invalid CSV: row {index} has extra columns")
    return rows


def _rows_from_wrapped_json(
    payload: dict[str, Any],
    *,
    keys: tuple[str, ...],
    source: str,
) -> list[dict[str, Any]]:
    for key in keys:
        if key in payload:
            return _ensure_row_list(payload[key], source=f"{source}.{key}")
    raise DryRunLoadError(f"{source} must include one of: {', '.join(keys)}")


def _planning_rows_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="json")
    if isinstance(payload, dict):
        return _rows_from_wrapped_json(
            payload,
            keys=PLANNING_ROW_KEYS,
            source="json",
        )
    raise DryRunLoadError("planning rows json must be a row list or object")


def load_planning_rows_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load planning-like rows from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _planning_rows_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_rows(artifact_path, source="planning rows jsonl")
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported planning rows extension: {suffix}")


def _impact_rows_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="json")
    if isinstance(payload, dict):
        return _rows_from_wrapped_json(
            payload,
            keys=IMPACT_ROW_KEYS,
            source="json",
        )
    raise DryRunLoadError("impact rows json must be a row list or object")


def load_impact_rows_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load explicit score impact rows from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _impact_rows_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_rows(artifact_path, source="impact rows jsonl")
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported impact rows extension: {suffix}")


def _impact_result_from_json(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"impact_rows": _ensure_row_list(payload, source="json")}
    if not isinstance(payload, dict):
        raise DryRunLoadError("impact result json must be an object or impact row list")
    if isinstance(payload.get("impact_result"), dict):
        return deepcopy(payload["impact_result"])
    if isinstance(payload.get("impact_packet"), dict):
        return {"impact_packet": deepcopy(payload["impact_packet"])}
    if "packet_type" in payload and isinstance(payload.get("impact_rows"), list):
        return {"impact_packet": deepcopy(payload)}
    if any(key in payload for key in IMPACT_ROW_KEYS):
        return {"impact_rows": _rows_from_wrapped_json(payload, keys=IMPACT_ROW_KEYS, source="json")}
    if any(key in payload for key in ("annotator_result", "annotated_rows")):
        raise DryRunLoadError("annotator-result input is not a score impact result")
    raise DryRunLoadError(
        "impact result json must include impact_result, impact_packet, "
        "impact_rows, rows, or items"
    )


def load_impact_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load a score impact result-like artifact from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _impact_result_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return {"impact_rows": _load_jsonl_rows(artifact_path, source="impact result jsonl")}
    if suffix == ".csv":
        return {"impact_rows": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported impact result extension: {suffix}")


def _dry_run_key(annotator_result: dict[str, Any]) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"rows={int(annotator_result.get('planning_row_count', 0))}",
            f"annotated={len(annotator_result.get('annotated_rows', []))}",
            f"unannotated={len(annotator_result.get('unannotated_rows', []))}",
            f"available={int(annotator_result.get('score_preview_available_count', 0))}",
            f"blocked={int(annotator_result.get('score_preview_blocked_count', 0))}",
            f"positive={int(annotator_result.get('positive_impact_count', 0))}",
            f"negative={int(annotator_result.get('negative_impact_count', 0))}",
        )
    )


def build_dry_run_payload(
    planning_rows: list[dict[str, Any]] | None = None,
    impact_result: dict[str, Any] | None = None,
    impact_rows: list[dict[str, Any]] | None = None,
    annotation_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 39B planning annotation dry-run payload."""

    rows = deepcopy(planning_rows) if isinstance(planning_rows, list) else None
    result = deepcopy(impact_result) if isinstance(impact_result, dict) else None
    explicit_rows = deepcopy(impact_rows) if isinstance(impact_rows, list) else None
    policy = deepcopy(annotation_policy) if isinstance(annotation_policy, dict) else {}
    annotator_result = build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
        planning_rows=rows,
        impact_result=result,
        impact_rows=explicit_rows,
        annotation_policy=policy,
    )
    annotated_rows = deepcopy(annotator_result.get("annotated_rows", []))
    unannotated_rows = deepcopy(annotator_result.get("unannotated_rows", []))
    annotation_summary = deepcopy(annotator_result.get("annotation_summary", {}))
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_score_impact_planning_artifact_annotator_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "preview_only": True,
        "deterministic_score_impact_annotation": True,
        "requires_manual_user_control": True,
        "planning_row_count": int(annotator_result.get("planning_row_count", 0)),
        "impact_result_present": result not in (None, {}, []),
        "impact_rows_present": explicit_rows not in (None, [], {}) or bool(
            annotator_result.get("impact_rows_present")
        ),
        "annotation_policy": deepcopy(
            annotator_result.get("annotation_policy", policy)
        ),
        "annotator_result": deepcopy(annotator_result),
        "annotated_rows": annotated_rows,
        "unannotated_rows": unannotated_rows,
        "annotation_summary": annotation_summary,
        "score_preview_available_count": int(
            annotator_result.get("score_preview_available_count", 0)
        ),
        "score_preview_blocked_count": int(
            annotator_result.get("score_preview_blocked_count", 0)
        ),
        "positive_impact_count": int(annotator_result.get("positive_impact_count", 0)),
        "negative_impact_count": int(annotator_result.get("negative_impact_count", 0)),
        "neutral_impact_count": int(annotator_result.get("neutral_impact_count", 0)),
        "red_flag_review_count": int(annotator_result.get("red_flag_review_count", 0)),
        "existing_score_fields_detected": deepcopy(
            annotator_result.get("existing_score_fields_detected", [])
        ),
        "existing_scores_preserved": bool(
            annotator_result.get("existing_scores_preserved", False)
        ),
        "dry_run_summary": {
            "planning_rows_present": rows not in (None, [], {}),
            "impact_result_present": result not in (None, {}, []),
            "impact_rows_present": explicit_rows not in (None, [], {}),
            "annotated_row_count": len(annotated_rows),
            "unannotated_row_count": len(unannotated_rows),
            "stdout_only": True,
            "output_file_written": False,
            "hypothetical_score_preview_produced": True,
            "final_score_produced": False,
            "existing_score_changed": False,
        },
        "dry_run_key": _dry_run_key(annotator_result),
        "hypothetical_score_preview_produced": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    if args.positive_delta_threshold is not None:
        policy["positive_delta_threshold"] = float(args.positive_delta_threshold)
    if args.negative_delta_threshold is not None:
        policy["negative_delta_threshold"] = float(args.negative_delta_threshold)
    if args.exclude_full_impact_row:
        policy["include_full_impact_row"] = False
    if args.skip_unmatched_annotations:
        policy["annotate_unmatched_rows"] = False
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Default-off JD evidence score impact planning annotation dry-run."
    )
    parser.add_argument("--input", dest="input_path", help="Planning rows path.")
    parser.add_argument(
        "--impact-result",
        dest="impact_result_path",
        help="Optional score impact result path.",
    )
    parser.add_argument(
        "--impact-rows",
        dest="impact_rows_path",
        help="Optional explicit score impact rows path.",
    )
    parser.add_argument("--positive-delta-threshold", type=float)
    parser.add_argument("--negative-delta-threshold", type=float)
    parser.add_argument("--exclude-full-impact-row", action="store_true")
    parser.add_argument("--skip-unmatched-annotations", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 39B dry-run command."""

    try:
        args = _parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    if not args.input_path:
        print("error: --input is required", file=sys.stderr)
        return 2

    try:
        planning_rows = load_planning_rows_from_path(args.input_path)
        impact_result = (
            load_impact_result_from_path(args.impact_result_path)
            if args.impact_result_path
            else None
        )
        impact_rows = (
            load_impact_rows_from_path(args.impact_rows_path)
            if args.impact_rows_path
            else None
        )
        payload = build_dry_run_payload(
            planning_rows=planning_rows,
            impact_result=impact_result,
            impact_rows=impact_rows,
            annotation_policy=_policy_from_args(args),
        )
    except DryRunLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
