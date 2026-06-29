"""Default-off dry-run command for JD evidence score impact review queues."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.jd_evidence_score_impact_review_queue_builder_default_off import (
    build_jd_evidence_score_impact_review_queue_builder_default_off,
)


PHASE = "41B"
REVIEW_PACKET_KEYS = ("review_packets", "rows", "items", "review_queue")
BUILDER_RESULT_ROW_KEYS = ("review_packets", "rows", "items")
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
    "review_packet_building_performed",
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
    """Raised when review queue dry-run input cannot be loaded."""


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
        raise DryRunLoadError(f"{source} must contain a list of review packet objects")
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


def _review_packets_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="json")
    if isinstance(payload, dict):
        return _rows_from_wrapped_json(
            payload,
            keys=REVIEW_PACKET_KEYS,
            source="json",
        )
    raise DryRunLoadError("review packets json must be a row list or object")


def load_review_packets_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load review packets from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _review_packets_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_rows(artifact_path, source="review packets jsonl")
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported review packets extension: {suffix}")


def _builder_result_from_json(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"review_packets": _ensure_row_list(payload, source="json")}
    if not isinstance(payload, dict):
        raise DryRunLoadError("builder result json must be an object or row list")
    if isinstance(payload.get("builder_result"), dict):
        return deepcopy(payload)
    if any(key in payload for key in BUILDER_RESULT_ROW_KEYS):
        return {
            "review_packets": _rows_from_wrapped_json(
                payload,
                keys=BUILDER_RESULT_ROW_KEYS,
                source="json",
            )
        }
    raise DryRunLoadError(
        "builder result json must include builder_result, "
        "review_packets, rows, or items"
    )


def load_builder_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load a Phase 40 builder-result-like artifact from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _builder_result_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return {
            "review_packets": _load_jsonl_rows(
                artifact_path,
                source="builder result jsonl",
            )
        }
    if suffix == ".csv":
        return {"review_packets": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported builder result extension: {suffix}")


def _dry_run_key(queue_result: dict[str, Any]) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"packets={int(queue_result.get('review_packet_count', 0))}",
            f"queue={len(queue_result.get('review_queue', []))}",
            f"urgent={int(queue_result.get('urgent_review_count', 0))}",
            f"manual={int(queue_result.get('manual_review_count', 0))}",
            f"positive={int(queue_result.get('positive_review_count', 0))}",
            f"negative={int(queue_result.get('negative_review_count', 0))}",
            f"neutral={int(queue_result.get('neutral_review_count', 0))}",
            f"unmatched={int(queue_result.get('unmatched_count', 0))}",
            f"unknown={int(queue_result.get('unknown_review_count', 0))}",
        )
    )


def build_dry_run_payload(
    review_packets: list[dict[str, Any]] | None = None,
    builder_result: dict[str, Any] | None = None,
    queue_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 41B review queue dry-run payload."""

    packets = deepcopy(review_packets) if isinstance(review_packets, list) else None
    result = deepcopy(builder_result) if isinstance(builder_result, dict) else None
    policy = deepcopy(queue_policy) if isinstance(queue_policy, dict) else {}
    queue_result = build_jd_evidence_score_impact_review_queue_builder_default_off(
        review_packets=packets,
        builder_result=result,
        queue_policy=policy,
    )
    review_queue = deepcopy(queue_result.get("review_queue", []))
    grouped = deepcopy(queue_result.get("review_queue_by_priority", {}))
    summary = deepcopy(queue_result.get("review_queue_summary", {}))
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_score_impact_review_queue_builder_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "preview_only": True,
        "deterministic_review_queue_building": True,
        "manual_review_queue_only": True,
        "requires_manual_user_control": True,
        "review_packets_present": isinstance(review_packets, list)
        and len(review_packets) > 0,
        "builder_result_present": isinstance(builder_result, dict),
        "queue_policy": deepcopy(queue_result.get("queue_policy", policy)),
        "queue_result": deepcopy(queue_result),
        "review_queue": review_queue,
        "review_queue_by_priority": grouped,
        "review_queue_summary": summary,
        "urgent_review_count": int(queue_result.get("urgent_review_count", 0)),
        "manual_review_count": int(queue_result.get("manual_review_count", 0)),
        "positive_review_count": int(queue_result.get("positive_review_count", 0)),
        "negative_review_count": int(queue_result.get("negative_review_count", 0)),
        "neutral_review_count": int(queue_result.get("neutral_review_count", 0)),
        "unmatched_count": int(queue_result.get("unmatched_count", 0)),
        "unknown_review_count": int(queue_result.get("unknown_review_count", 0)),
        "score_preview_available_count": int(
            queue_result.get("score_preview_available_count", 0)
        ),
        "score_preview_blocked_count": int(
            queue_result.get("score_preview_blocked_count", 0)
        ),
        "red_flag_review_count": int(queue_result.get("red_flag_review_count", 0)),
        "existing_score_fields_detected": deepcopy(
            queue_result.get("existing_score_fields_detected", [])
        ),
        "existing_scores_preserved": queue_result.get(
            "existing_scores_preserved"
        )
        is True,
        "dry_run_summary": {
            "review_queue_count": len(review_queue),
            "builder_missing_inputs": list(queue_result.get("missing_inputs", [])),
            "final_score_produced": False,
            "existing_score_changed": False,
        },
        "dry_run_key": _dry_run_key(queue_result),
        "hypothetical_score_preview_produced": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _queue_policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    for key in (
        "urgent_red_flag_priority",
        "blocked_preview_priority",
        "manual_review_priority",
        "negative_review_priority",
        "positive_review_priority",
        "neutral_review_priority",
        "unmatched_priority",
        "unknown_priority",
        "max_queue_items",
    ):
        value = getattr(args, key)
        if value is not None:
            policy[key] = value
    if args.preserve_input_order_within_priority:
        policy["sort_by_absolute_delta_within_priority"] = False
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a default-off JD evidence score impact review queue.",
    )
    parser.add_argument("--input", required=True, help="Review packets input file")
    parser.add_argument(
        "--builder-result",
        help="Optional Phase 40 review packet builder result file",
    )
    parser.add_argument("--urgent-red-flag-priority", type=int)
    parser.add_argument("--blocked-preview-priority", type=int)
    parser.add_argument("--manual-review-priority", type=int)
    parser.add_argument("--negative-review-priority", type=int)
    parser.add_argument("--positive-review-priority", type=int)
    parser.add_argument("--neutral-review-priority", type=int)
    parser.add_argument("--unmatched-priority", type=int)
    parser.add_argument("--unknown-priority", type=int)
    parser.add_argument(
        "--preserve-input-order-within-priority",
        action="store_true",
        help="Disable absolute-delta sorting inside equal priority groups",
    )
    parser.add_argument("--max-queue-items", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 41B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        review_packets = load_review_packets_from_path(args.input)
        builder_result = (
            load_builder_result_from_path(args.builder_result)
            if args.builder_result
            else None
        )
        payload = build_dry_run_payload(
            review_packets=review_packets,
            builder_result=builder_result,
            queue_policy=_queue_policy_from_args(args),
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
