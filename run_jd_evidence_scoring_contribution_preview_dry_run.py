"""Default-off dry-run command for JD evidence contribution previews."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.jd_evidence_scoring_contribution_preview_default_off import (
    build_jd_evidence_scoring_contribution_preview_default_off,
)


PHASE = "37B"
ROW_KEYS = ("scoring_feature_rows", "feature_rows", "rows", "items")
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
            return [dict(row) for row in reader]
    except csv.Error as exc:
        raise DryRunLoadError(f"invalid CSV: {exc}") from exc
    except OSError as exc:
        raise DryRunLoadError(f"unreadable file: {exc}") from exc


def _rows_from_wrapped_json(payload: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    for key in ROW_KEYS:
        if key in payload:
            return _ensure_row_list(payload[key], source=f"{source}.{key}")
    raise DryRunLoadError(
        f"{source} must include scoring_feature_rows, feature_rows, rows, or items"
    )


def _feature_packet_from_json(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"scoring_feature_rows": _ensure_row_list(payload, source="json")}
    if not isinstance(payload, dict):
        raise DryRunLoadError("feature packet json must be an object or row list")
    if isinstance(payload.get("feature_packet"), dict):
        return deepcopy(payload["feature_packet"])
    if isinstance(payload.get("preview_result"), dict) and isinstance(
        payload["preview_result"].get("contribution_packet"),
        dict,
    ):
        raise DryRunLoadError("preview-result input is not a scoring feature packet")
    if isinstance(payload.get("adapter_result"), dict) and isinstance(
        payload["adapter_result"].get("feature_packet"),
        dict,
    ):
        return deepcopy(payload["adapter_result"]["feature_packet"])
    if isinstance(payload.get("feature_packet"), list):
        return {"scoring_feature_rows": _ensure_row_list(payload["feature_packet"], source="json.feature_packet")}
    if "packet_type" in payload and isinstance(payload.get("scoring_feature_rows"), list):
        return deepcopy(payload)
    if any(key in payload for key in ROW_KEYS):
        return {"scoring_feature_rows": _rows_from_wrapped_json(payload, source="json")}
    raise DryRunLoadError(
        "feature packet json must include feature_packet, adapter_result.feature_packet, "
        "scoring_feature_rows, feature_rows, rows, or items"
    )


def load_feature_packet_from_path(path: str | Path) -> dict[str, Any]:
    """Load a feature packet-like artifact from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _feature_packet_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return {
            "scoring_feature_rows": _load_jsonl_rows(
                artifact_path,
                source="feature packet jsonl",
            )
        }
    if suffix == ".csv":
        return {"scoring_feature_rows": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported feature packet extension: {suffix}")


def _scoring_rows_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="json")
    if isinstance(payload, dict):
        return _rows_from_wrapped_json(payload, source="json")
    raise DryRunLoadError("scoring feature rows json must be a row list or object")


def load_scoring_feature_rows_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load explicit scoring feature rows from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _scoring_rows_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_rows(artifact_path, source="scoring feature rows jsonl")
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported scoring feature rows extension: {suffix}")


def _dry_run_key(preview_result: dict[str, Any]) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"ready={int(preview_result.get('preview_ready_count', 0))}",
            f"blocked={int(preview_result.get('preview_blocked_count', 0))}",
            f"positive={preview_result.get('positive_contribution_points_total', 0)}",
            f"negative={preview_result.get('negative_contribution_points_total', 0)}",
            f"bounded={preview_result.get('bounded_contribution_points_total', 0)}",
            f"red_review={int(preview_result.get('red_flag_review_count', 0))}",
        )
    )


def build_dry_run_payload(
    feature_packet: dict[str, Any] | None = None,
    scoring_feature_rows: list[dict[str, Any]] | None = None,
    contribution_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 37B contribution preview dry-run payload."""

    packet = deepcopy(feature_packet) if isinstance(feature_packet, dict) else None
    rows = deepcopy(scoring_feature_rows) if isinstance(scoring_feature_rows, list) else None
    policy = deepcopy(contribution_policy) if isinstance(contribution_policy, dict) else {}
    preview_result = build_jd_evidence_scoring_contribution_preview_default_off(
        feature_packet=packet,
        scoring_feature_rows=rows,
        contribution_policy=policy,
    )
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_scoring_contribution_preview_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "deterministic_contribution_preview": True,
        "requires_manual_user_control": True,
        "feature_packet_present": packet not in (None, {}, []),
        "scoring_feature_rows_present": rows not in (None, [], {}),
        "contribution_policy": policy,
        "preview_result": deepcopy(preview_result),
        "contribution_packet": deepcopy(preview_result.get("contribution_packet", {})),
        "contribution_rows": deepcopy(preview_result.get("contribution_rows", [])),
        "contribution_summary": deepcopy(preview_result.get("contribution_summary", {})),
        "positive_contribution_points_total": preview_result.get(
            "positive_contribution_points_total",
            0,
        ),
        "negative_contribution_points_total": preview_result.get(
            "negative_contribution_points_total",
            0,
        ),
        "bounded_contribution_points_total": preview_result.get(
            "bounded_contribution_points_total",
            0,
        ),
        "high_positive_contribution_count": int(
            preview_result.get("high_positive_contribution_count", 0)
        ),
        "negative_contribution_count": int(
            preview_result.get("negative_contribution_count", 0)
        ),
        "red_flag_review_count": int(preview_result.get("red_flag_review_count", 0)),
        "existing_score_fields_detected": deepcopy(
            preview_result.get("existing_score_fields_detected", [])
        ),
        "existing_scores_preserved": bool(
            preview_result.get("existing_scores_preserved", False)
        ),
        "preview_ready_count": int(preview_result.get("preview_ready_count", 0)),
        "preview_blocked_count": int(preview_result.get("preview_blocked_count", 0)),
        "dry_run_summary": {
            "feature_packet_present": packet not in (None, {}, []),
            "scoring_feature_rows_present": rows not in (None, [], {}),
            "contribution_row_count": len(preview_result.get("contribution_rows", [])),
            "preview_ready_count": int(preview_result.get("preview_ready_count", 0)),
            "preview_blocked_count": int(preview_result.get("preview_blocked_count", 0)),
            "stdout_only": True,
            "output_file_written": False,
            "final_score_produced": False,
            "existing_score_changed": False,
        },
        "dry_run_key": _dry_run_key(preview_result),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "max_positive_contribution_points": float(
            args.max_positive_contribution_points
        ),
        "max_negative_contribution_points": float(
            args.max_negative_contribution_points
        ),
        "required_skill_weight": float(args.required_skill_weight),
        "preferred_skill_weight": float(args.preferred_skill_weight),
        "tool_weight": float(args.tool_weight),
        "responsibility_weight": float(args.responsibility_weight),
        "missing_required_skill_penalty": float(args.missing_required_skill_penalty),
        "missing_tool_penalty": float(args.missing_tool_penalty),
        "red_flag_penalty": float(args.red_flag_penalty),
        "red_flag_review_threshold": int(args.red_flag_review_threshold),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Default-off JD evidence contribution preview dry-run."
    )
    parser.add_argument("--input", dest="input_path", help="Feature packet path.")
    parser.add_argument(
        "--scoring-feature-rows",
        dest="scoring_feature_rows_path",
        help="Optional explicit scoring feature rows path.",
    )
    parser.add_argument("--max-positive-contribution-points", type=float, default=12)
    parser.add_argument("--max-negative-contribution-points", type=float, default=-12)
    parser.add_argument("--required-skill-weight", type=float, default=6)
    parser.add_argument("--preferred-skill-weight", type=float, default=2)
    parser.add_argument("--tool-weight", type=float, default=2)
    parser.add_argument("--responsibility-weight", type=float, default=2)
    parser.add_argument("--missing-required-skill-penalty", type=float, default=-1)
    parser.add_argument("--missing-tool-penalty", type=float, default=-0.5)
    parser.add_argument("--red-flag-penalty", type=float, default=-3)
    parser.add_argument("--red-flag-review-threshold", type=int, default=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 37B dry-run command."""

    try:
        args = _parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    if not args.input_path:
        print("error: --input is required", file=sys.stderr)
        return 2

    try:
        packet = load_feature_packet_from_path(args.input_path)
        rows = (
            load_scoring_feature_rows_from_path(args.scoring_feature_rows_path)
            if args.scoring_feature_rows_path
            else None
        )
        payload = build_dry_run_payload(
            feature_packet=packet,
            scoring_feature_rows=rows,
            contribution_policy=_policy_from_args(args),
        )
    except DryRunLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
