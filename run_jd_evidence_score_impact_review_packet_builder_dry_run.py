"""Default-off dry-run command for JD evidence score impact review packets."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.jd_evidence_score_impact_review_packet_builder_default_off import (
    build_jd_evidence_score_impact_review_packet_builder_default_off,
)


PHASE = "40B"
ANNOTATED_ROW_KEYS = (
    "annotated_rows",
    "rows",
    "items",
    "review_packets",
    "planning_rows",
)
ANNOTATOR_RESULT_ROW_KEYS = ("annotated_rows", "rows", "items")
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
    "planning_annotation_performed",
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
    """Raised when review packet dry-run input cannot be loaded."""


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


def _annotated_rows_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="json")
    if isinstance(payload, dict):
        return _rows_from_wrapped_json(
            payload,
            keys=ANNOTATED_ROW_KEYS,
            source="json",
        )
    raise DryRunLoadError("annotated rows json must be a row list or object")


def load_annotated_rows_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load annotated planning rows from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _annotated_rows_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_rows(artifact_path, source="annotated rows jsonl")
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported annotated rows extension: {suffix}")


def _annotator_result_from_json(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"annotated_rows": _ensure_row_list(payload, source="json")}
    if not isinstance(payload, dict):
        raise DryRunLoadError("annotator result json must be an object or row list")
    if isinstance(payload.get("annotator_result"), dict):
        return deepcopy(payload)
    if any(key in payload for key in ANNOTATOR_RESULT_ROW_KEYS):
        return {
            "annotated_rows": _rows_from_wrapped_json(
                payload,
                keys=ANNOTATOR_RESULT_ROW_KEYS,
                source="json",
            )
        }
    raise DryRunLoadError(
        "annotator result json must include annotator_result, "
        "annotated_rows, rows, or items"
    )


def load_annotator_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load a Phase 39 annotator-result-like artifact from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _annotator_result_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return {
            "annotated_rows": _load_jsonl_rows(
                artifact_path,
                source="annotator result jsonl",
            )
        }
    if suffix == ".csv":
        return {"annotated_rows": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported annotator result extension: {suffix}")


def _dry_run_key(builder_result: dict[str, Any]) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"rows={int(builder_result.get('annotated_row_count', 0))}",
            f"packets={len(builder_result.get('review_packets', []))}",
            f"manual={int(builder_result.get('manual_review_count', 0))}",
            f"positive={int(builder_result.get('positive_review_count', 0))}",
            f"negative={int(builder_result.get('negative_review_count', 0))}",
            f"neutral={int(builder_result.get('neutral_review_count', 0))}",
            f"unmatched={int(builder_result.get('unmatched_count', 0))}",
            f"unknown={int(builder_result.get('unknown_review_count', 0))}",
        )
    )


def build_dry_run_payload(
    annotated_rows: list[dict[str, Any]] | None = None,
    annotator_result: dict[str, Any] | None = None,
    review_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 40B review packet dry-run payload."""

    rows = deepcopy(annotated_rows) if isinstance(annotated_rows, list) else None
    result = deepcopy(annotator_result) if isinstance(annotator_result, dict) else None
    policy = deepcopy(review_policy) if isinstance(review_policy, dict) else {}
    builder_result = build_jd_evidence_score_impact_review_packet_builder_default_off(
        annotated_rows=rows,
        annotator_result=result,
        review_policy=policy,
    )
    review_packets = deepcopy(builder_result.get("review_packets", []))
    grouped = deepcopy(builder_result.get("review_packets_by_recommendation", {}))
    summary = deepcopy(builder_result.get("review_packet_summary", {}))
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_score_impact_review_packet_builder_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "preview_only": True,
        "deterministic_review_packet_building": True,
        "manual_review_packet_only": True,
        "requires_manual_user_control": True,
        "annotated_rows_present": isinstance(annotated_rows, list)
        and len(annotated_rows) > 0,
        "annotator_result_present": isinstance(annotator_result, dict),
        "review_policy": deepcopy(builder_result.get("review_policy", policy)),
        "builder_result": deepcopy(builder_result),
        "review_packets": review_packets,
        "review_packets_by_recommendation": grouped,
        "review_packet_summary": summary,
        "manual_review_count": int(builder_result.get("manual_review_count", 0)),
        "positive_review_count": int(builder_result.get("positive_review_count", 0)),
        "negative_review_count": int(builder_result.get("negative_review_count", 0)),
        "neutral_review_count": int(builder_result.get("neutral_review_count", 0)),
        "unmatched_count": int(builder_result.get("unmatched_count", 0)),
        "unknown_review_count": int(builder_result.get("unknown_review_count", 0)),
        "score_preview_available_count": int(
            builder_result.get("score_preview_available_count", 0)
        ),
        "score_preview_blocked_count": int(
            builder_result.get("score_preview_blocked_count", 0)
        ),
        "red_flag_review_count": int(builder_result.get("red_flag_review_count", 0)),
        "existing_score_fields_detected": deepcopy(
            builder_result.get("existing_score_fields_detected", [])
        ),
        "existing_scores_preserved": builder_result.get(
            "existing_scores_preserved"
        )
        is True,
        "dry_run_summary": {
            "review_packet_count": len(review_packets),
            "builder_missing_inputs": list(builder_result.get("missing_inputs", [])),
            "final_score_produced": False,
            "existing_score_changed": False,
        },
        "dry_run_key": _dry_run_key(builder_result),
        "hypothetical_score_preview_produced": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _review_policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy = {
        "include_full_annotated_row": bool(args.include_full_annotated_row),
        "include_score_impact_preview_result": not bool(
            args.exclude_score_impact_preview_result
        ),
    }
    if args.max_missing_reason_items is not None:
        policy["max_missing_reason_items"] = args.max_missing_reason_items
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build default-off JD evidence score impact review packets.",
    )
    parser.add_argument("--input", required=True, help="Annotated rows input file")
    parser.add_argument(
        "--annotator-result",
        help="Optional Phase 39 annotator result file",
    )
    parser.add_argument(
        "--include-full-annotated-row",
        action="store_true",
        help="Include copied full annotated rows in each review packet",
    )
    parser.add_argument(
        "--exclude-score-impact-preview-result",
        action="store_true",
        help="Exclude copied score impact preview result details",
    )
    parser.add_argument(
        "--max-missing-reason-items",
        type=int,
        help="Maximum invalid/missing reason items to include",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 40B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        annotated_rows = load_annotated_rows_from_path(args.input)
        annotator_result = (
            load_annotator_result_from_path(args.annotator_result)
            if args.annotator_result
            else None
        )
        payload = build_dry_run_payload(
            annotated_rows=annotated_rows,
            annotator_result=annotator_result,
            review_policy=_review_policy_from_args(args),
        )
    except (DryRunLoadError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except SystemExit as exc:
        return int(exc.code or 0)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
