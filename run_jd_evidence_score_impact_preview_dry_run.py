"""Default-off dry-run command for JD evidence score impact previews."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.jd_evidence_score_impact_preview_default_off import (
    build_jd_evidence_score_impact_preview_default_off,
)


PHASE = "38B"
ROW_KEYS = ("contribution_rows", "rows", "items")
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
        raise DryRunLoadError(f"{source} must contain a list of contribution row objects")
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


def _rows_from_wrapped_json(payload: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    for key in ROW_KEYS:
        if key in payload:
            return _ensure_row_list(payload[key], source=f"{source}.{key}")
    raise DryRunLoadError(
        f"{source} must include contribution_rows, rows, or items"
    )


def _contribution_packet_from_json(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"contribution_rows": _ensure_row_list(payload, source="json")}
    if not isinstance(payload, dict):
        raise DryRunLoadError(
            "contribution packet json must be an object or contribution row list"
        )
    if isinstance(payload.get("contribution_packet"), dict):
        return deepcopy(payload["contribution_packet"])
    preview_result = payload.get("preview_result")
    if isinstance(preview_result, dict) and isinstance(
        preview_result.get("contribution_packet"),
        dict,
    ):
        return deepcopy(preview_result["contribution_packet"])
    if "packet_type" in payload and isinstance(payload.get("contribution_rows"), list):
        return deepcopy(payload)
    if any(key in payload for key in ROW_KEYS):
        return {"contribution_rows": _rows_from_wrapped_json(payload, source="json")}
    raise DryRunLoadError(
        "contribution packet json must include contribution_packet, "
        "preview_result.contribution_packet, contribution_rows, rows, or items"
    )


def load_contribution_packet_from_path(path: str | Path) -> dict[str, Any]:
    """Load a contribution packet-like artifact from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _contribution_packet_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return {
            "contribution_rows": _load_jsonl_rows(
                artifact_path,
                source="contribution packet jsonl",
            )
        }
    if suffix == ".csv":
        return {"contribution_rows": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported contribution packet extension: {suffix}")


def _contribution_rows_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="json")
    if isinstance(payload, dict):
        return _rows_from_wrapped_json(payload, source="json")
    raise DryRunLoadError(
        "contribution rows json must be a contribution row list or object"
    )


def load_contribution_rows_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load explicit contribution rows from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _contribution_rows_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_rows(artifact_path, source="contribution rows jsonl")
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported contribution rows extension: {suffix}")


def _dry_run_key(impact_result: dict[str, Any]) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"available={int(impact_result.get('preview_score_available_count', 0))}",
            f"blocked={int(impact_result.get('preview_score_blocked_count', 0))}",
            f"positive={int(impact_result.get('positive_impact_count', 0))}",
            f"negative={int(impact_result.get('negative_impact_count', 0))}",
            f"neutral={int(impact_result.get('neutral_impact_count', 0))}",
            f"red_review={int(impact_result.get('red_flag_review_count', 0))}",
        )
    )


def build_dry_run_payload(
    contribution_packet: dict[str, Any] | None = None,
    contribution_rows: list[dict[str, Any]] | None = None,
    impact_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 38B score impact preview dry-run payload."""

    packet = deepcopy(contribution_packet) if isinstance(contribution_packet, dict) else None
    rows = deepcopy(contribution_rows) if isinstance(contribution_rows, list) else None
    policy = deepcopy(impact_policy) if isinstance(impact_policy, dict) else {}
    impact_result = build_jd_evidence_score_impact_preview_default_off(
        contribution_packet=packet,
        contribution_rows=rows,
        impact_policy=policy,
    )
    impact_packet = deepcopy(impact_result.get("impact_packet", {}))
    impact_rows = deepcopy(impact_result.get("impact_rows", []))
    impact_summary = deepcopy(impact_result.get("impact_summary", {}))
    preview_score_available_count = int(
        impact_result.get("preview_score_available_count", 0)
    )
    preview_score_blocked_count = int(
        impact_result.get("preview_score_blocked_count", 0)
    )
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_score_impact_preview_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "preview_only": True,
        "deterministic_score_impact_preview": True,
        "requires_manual_user_control": True,
        "contribution_packet_present": packet not in (None, {}, []),
        "contribution_rows_present": rows not in (None, [], {}),
        "impact_policy": deepcopy(impact_result.get("impact_policy", policy)),
        "impact_result": deepcopy(impact_result),
        "impact_packet": impact_packet,
        "impact_rows": impact_rows,
        "impact_summary": impact_summary,
        "preview_score_available_count": preview_score_available_count,
        "preview_score_blocked_count": preview_score_blocked_count,
        "positive_impact_count": int(impact_result.get("positive_impact_count", 0)),
        "negative_impact_count": int(impact_result.get("negative_impact_count", 0)),
        "neutral_impact_count": int(impact_result.get("neutral_impact_count", 0)),
        "red_flag_review_count": int(impact_result.get("red_flag_review_count", 0)),
        "existing_score_fields_detected": deepcopy(
            impact_result.get("existing_score_fields_detected", [])
        ),
        "existing_scores_preserved": bool(
            impact_result.get("existing_scores_preserved", False)
        ),
        "score_preview_values": deepcopy(
            impact_result.get("score_preview_values", [])
        ),
        "dry_run_summary": {
            "contribution_packet_present": packet not in (None, {}, []),
            "contribution_rows_present": rows not in (None, [], {}),
            "impact_row_count": len(impact_rows),
            "preview_score_available_count": preview_score_available_count,
            "preview_score_blocked_count": preview_score_blocked_count,
            "stdout_only": True,
            "output_file_written": False,
            "hypothetical_score_preview_produced": True,
            "final_score_produced": False,
            "existing_score_changed": False,
        },
        "dry_run_key": _dry_run_key(impact_result),
        "hypothetical_score_preview_produced": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    if args.score_floor is not None:
        policy["score_floor"] = float(args.score_floor)
    if args.score_ceiling is not None:
        policy["score_ceiling"] = float(args.score_ceiling)
    if args.default_base_score is not None:
        policy["default_base_score"] = float(args.default_base_score)
    if args.require_existing_score_for_preview:
        policy["require_existing_score_for_preview"] = True
    if args.allow_red_flag_score_preview:
        policy["red_flag_review_blocks_preview_score"] = False
    if args.round_digits is not None:
        policy["round_digits"] = int(args.round_digits)
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Default-off JD evidence score impact preview dry-run."
    )
    parser.add_argument("--input", dest="input_path", help="Contribution packet path.")
    parser.add_argument(
        "--contribution-rows",
        dest="contribution_rows_path",
        help="Optional explicit contribution rows path.",
    )
    parser.add_argument("--score-floor", type=float)
    parser.add_argument("--score-ceiling", type=float)
    parser.add_argument("--default-base-score", type=float)
    parser.add_argument("--require-existing-score-for-preview", action="store_true")
    parser.add_argument("--allow-red-flag-score-preview", action="store_true")
    parser.add_argument("--round-digits", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 38B dry-run command."""

    try:
        args = _parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    if not args.input_path:
        print("error: --input is required", file=sys.stderr)
        return 2

    try:
        packet = load_contribution_packet_from_path(args.input_path)
        rows = (
            load_contribution_rows_from_path(args.contribution_rows_path)
            if args.contribution_rows_path
            else None
        )
        payload = build_dry_run_payload(
            contribution_packet=packet,
            contribution_rows=rows,
            impact_policy=_policy_from_args(args),
        )
    except DryRunLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
