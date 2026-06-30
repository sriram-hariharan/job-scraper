"""Default-off dry-run command for manual review readback adaptation."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_manual_review_readback_adapter_default_off import (
    build_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off,
)


PHASE = "48B"
PACKET_CONTAINER_KEYS = (
    "manual_review_packets",
    "readback_items",
    "rows",
    "items",
    "packets",
)
REVIEW_RESULT_KEYS = (
    "review_packet_result",
    "manual_review_packets",
    "manual_review_packets_by_type",
    "rows",
    "items",
)
FALSE_ACTION_KEYS = (
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "resume_change_applied",
    "manual_review_packets_created",
    "resume_change_proposals_created",
    "provider_response_validation_performed",
    "provider_response_normalization_performed",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
)


class DryRunLoadError(ValueError):
    """Raised when Phase 48B dry-run input cannot be loaded."""


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


def _load_jsonl_objects(path: Path, *, source: str) -> list[dict[str, Any]]:
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
            raise DryRunLoadError(f"{source} line {line_number} must be a JSON object")
        rows.append(dict(payload))
    if not rows:
        raise DryRunLoadError(f"{source} must contain at least one JSON object row")
    return rows


def _load_one_jsonl_object(path: Path, *, source: str) -> dict[str, Any]:
    rows = _load_jsonl_objects(path, source=source)
    if len(rows) != 1:
        raise DryRunLoadError(f"{source} must contain exactly one JSON object row")
    return rows[0]


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
    if not rows:
        raise DryRunLoadError("invalid CSV: missing rows")
    return rows


def _load_one_csv_row(path: Path, *, source: str) -> dict[str, Any]:
    rows = _load_csv_rows(path)
    if len(rows) != 1:
        raise DryRunLoadError(f"{source} csv must contain exactly one row")
    return rows[0]


def _ensure_row_list(value: Any, *, source: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise DryRunLoadError(f"{source} must contain a list of manual review packet objects")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise DryRunLoadError(f"{source} row {index} must be a JSON object")
        rows.append(dict(row))
    return rows


def _manual_review_packets_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="manual review packets json")
    if isinstance(payload, dict):
        for key in PACKET_CONTAINER_KEYS:
            if key in payload:
                return _ensure_row_list(
                    payload[key],
                    source=f"manual review packets json.{key}",
                )
    raise DryRunLoadError(
        "manual review packets json must be a list or include "
        "manual_review_packets, readback_items, rows, items, or packets"
    )


def load_manual_review_packets_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load Phase 47 manual review packets from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _manual_review_packets_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_objects(artifact_path, source="manual review packets jsonl")
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported manual review packets extension: {suffix}")


def _review_packet_result_from_json(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {
            "manual_review_packets": _ensure_row_list(
                payload,
                source="review packet result json",
            )
        }
    if not isinstance(payload, dict):
        raise DryRunLoadError("review packet result input must be a JSON object or list")
    if "review_packet_result" in payload:
        return deepcopy(payload)
    if "manual_review_packets" in payload:
        return deepcopy(payload)
    if "manual_review_packets_by_type" in payload:
        return deepcopy(payload)
    for key in ("rows", "items"):
        if key in payload:
            return {
                "manual_review_packets": _ensure_row_list(
                    payload[key],
                    source=f"review packet result json.{key}",
                )
            }
    raise DryRunLoadError(
        "review packet result input must include review_packet_result, "
        "manual_review_packets, manual_review_packets_by_type, rows, or items"
    )


def load_review_packet_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load one Phase 47 review packet result from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _review_packet_result_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _review_packet_result_from_json(
            _load_one_jsonl_object(artifact_path, source="review packet result jsonl")
        )
    if suffix == ".csv":
        return {"manual_review_packets": [_load_one_csv_row(artifact_path, source="review packet result")]}
    raise DryRunLoadError(f"unsupported review packet result extension: {suffix}")


def load_readback_context_from_path(path: str | Path) -> dict[str, Any]:
    """Load readback context from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        payload = _read_json(artifact_path)
        if not isinstance(payload, dict):
            raise DryRunLoadError("readback context json must be a JSON object")
        return deepcopy(payload)
    if suffix == ".jsonl":
        return {
            "source_format": "jsonl",
            "rows": _load_jsonl_objects(artifact_path, source="readback context jsonl"),
        }
    if suffix == ".csv":
        return {"source_format": "csv", "rows": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported readback context extension: {suffix}")


def _dry_run_key(
    *,
    readback_result: dict[str, Any],
    manual_review_packets_present: bool,
    review_packet_result_present: bool,
    readback_context_present: bool,
) -> str:
    summary = readback_result.get("readback_summary", {})
    payload = {
        "phase": PHASE,
        "readback_key": readback_result.get("readback_key", ""),
        "manual_review_packets_present": manual_review_packets_present,
        "review_packet_result_present": review_packet_result_present,
        "readback_context_present": readback_context_present,
        "readback_item_count": summary.get("readback_item_count", 0),
        "missing_inputs": readback_result.get("missing_inputs", []),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase48b-manual-review-readback-dry-run-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_dry_run_payload(
    manual_review_packets: list[dict[str, Any]] | None = None,
    review_packet_result: dict[str, Any] | None = None,
    readback_context: dict[str, Any] | None = None,
    readback_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 48B manual review readback payload."""

    packets = deepcopy(manual_review_packets) if isinstance(manual_review_packets, list) else None
    review_result = deepcopy(review_packet_result) if isinstance(review_packet_result, dict) else None
    context = deepcopy(readback_context) if isinstance(readback_context, dict) else None
    policy = deepcopy(readback_policy) if isinstance(readback_policy, dict) else {}
    readback_result = (
        build_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off(
            manual_review_packets=packets,
            review_packet_result=review_result,
            readback_context=context,
            readback_policy=policy,
        )
    )
    packets_present = isinstance(packets, list) and bool(packets)
    review_result_present = isinstance(review_result, dict)
    context_present = isinstance(context, dict) and bool(context)
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_readback_only": True,
        "ui_api_readback_payload_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "manual_review_packets_present": packets_present,
        "review_packet_result_present": review_result_present,
        "readback_context_present": context_present,
        "readback_policy": deepcopy(readback_result.get("readback_policy", {})),
        "readback_result": deepcopy(readback_result),
        "readback_items": deepcopy(readback_result.get("readback_items", [])),
        "readback_items_by_type": deepcopy(readback_result.get("readback_items_by_type", {})),
        "readback_items_by_action": deepcopy(readback_result.get("readback_items_by_action", {})),
        "readback_payload": deepcopy(readback_result.get("readback_payload", {})),
        "readback_summary": deepcopy(readback_result.get("readback_summary", {})),
        "readback_findings": deepcopy(readback_result.get("readback_findings", {})),
        "dry_run_summary": {
            "readback_adapter_phase": readback_result.get("phase"),
            "manual_review_packets_present": packets_present,
            "review_packet_result_present": review_result_present,
            "readback_context_present": context_present,
            "readback_item_count": len(readback_result.get("readback_items", [])),
            "missing_input_count": len(readback_result.get("missing_inputs", [])),
            "manual_review_readback_payload_created": True,
            "ui_route_added": False,
            "api_route_added": False,
            "ui_readback_performed": False,
            "api_readback_performed": False,
            "user_acceptance_performed": False,
            "resume_change_applied": False,
        },
        "dry_run_key": _dry_run_key(
            readback_result=readback_result,
            manual_review_packets_present=packets_present,
            review_packet_result_present=review_result_present,
            readback_context_present=context_present,
        ),
        "manual_review_readback_payload_created": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _readback_policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    if args.max_readback_items is not None:
        policy["max_readback_items"] = args.max_readback_items
    if args.exclude_before_after_text:
        policy["include_before_after_text"] = False
    if args.exclude_risk_flags:
        policy["include_risk_flags"] = False
    if args.exclude_evidence:
        policy["include_evidence"] = False
    if args.exclude_action_labels:
        policy["include_action_labels"] = False
    if args.disable_group_by_change_type:
        policy["group_by_change_type"] = False
    if args.disable_group_by_operator_action:
        policy["group_by_operator_action"] = False
    if args.disable_sort_by_display_order:
        policy["sort_by_display_order"] = False
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build exact resume change-set manual review readback payloads.",
    )
    parser.add_argument("--input", required=True, help="Manual review packets input file")
    parser.add_argument(
        "--review-packet-result",
        help="Optional Phase 47 review packet result file",
    )
    parser.add_argument("--readback-context", help="Optional readback context file")
    parser.add_argument("--max-readback-items", type=int)
    parser.add_argument("--exclude-before-after-text", action="store_true")
    parser.add_argument("--exclude-risk-flags", action="store_true")
    parser.add_argument("--exclude-evidence", action="store_true")
    parser.add_argument("--exclude-action-labels", action="store_true")
    parser.add_argument("--disable-group-by-change-type", action="store_true")
    parser.add_argument("--disable-group-by-operator-action", action="store_true")
    parser.add_argument("--disable-sort-by-display-order", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 48B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        manual_review_packets = load_manual_review_packets_from_path(args.input)
        review_packet_result = (
            load_review_packet_result_from_path(args.review_packet_result)
            if args.review_packet_result
            else None
        )
        readback_context = (
            load_readback_context_from_path(args.readback_context)
            if args.readback_context
            else None
        )
        payload = build_dry_run_payload(
            manual_review_packets=manual_review_packets,
            review_packet_result=review_packet_result,
            readback_context=readback_context,
            readback_policy=_readback_policy_from_args(args),
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
