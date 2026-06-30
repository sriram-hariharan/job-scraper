"""Default-off dry-run command for exact-change manual review packets."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_manual_review_packet_builder_default_off import (
    build_controlled_exact_resume_change_set_manual_review_packet_builder_default_off,
)


PHASE = "47B"
PROPOSAL_CONTAINER_KEYS = (
    "normalized_refined_change_proposals",
    "manual_review_packets",
    "rows",
    "items",
    "proposals",
)
NORMALIZATION_RESULT_KEYS = (
    "normalization_result",
    "normalized_refined_change_proposals",
    "normalized_change_proposals_by_type",
    "rows",
    "items",
)
FALSE_ACTION_KEYS = (
    "ui_readback_performed",
    "user_acceptance_performed",
    "resume_change_applied",
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
    """Raised when Phase 47B dry-run input cannot be loaded."""


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
            raise DryRunLoadError(
                f"{source} line {line_number} must be a JSON object"
            )
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
        raise DryRunLoadError(f"{source} must contain a list of proposal objects")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise DryRunLoadError(f"{source} row {index} must be a JSON object")
        rows.append(dict(row))
    return rows


def _proposal_rows_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="normalized change proposals json")
    if isinstance(payload, dict):
        for key in PROPOSAL_CONTAINER_KEYS:
            if key in payload:
                return _ensure_row_list(
                    payload[key],
                    source=f"normalized change proposals json.{key}",
                )
    raise DryRunLoadError(
        "normalized change proposals json must be a list or include "
        "normalized_refined_change_proposals, manual_review_packets, rows, items, or proposals"
    )


def load_normalized_change_proposals_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load normalized Phase 46 change proposals from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _proposal_rows_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_objects(
            artifact_path,
            source="normalized change proposals jsonl",
        )
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported normalized change proposals extension: {suffix}")


def _normalization_result_from_json(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"normalized_refined_change_proposals": _ensure_row_list(payload, source="normalization result json")}
    if not isinstance(payload, dict):
        raise DryRunLoadError("normalization result input must be a JSON object or list")
    if isinstance(payload.get("normalization_result"), dict):
        return deepcopy(payload)
    for key in NORMALIZATION_RESULT_KEYS:
        if key in payload:
            return deepcopy(payload)
    raise DryRunLoadError(
        "normalization result input must include normalization_result, "
        "normalized_refined_change_proposals, normalized_change_proposals_by_type, rows, or items"
    )


def load_normalization_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load one Phase 46 normalization result from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _normalization_result_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _normalization_result_from_json(
            _load_one_jsonl_object(artifact_path, source="normalization result jsonl")
        )
    if suffix == ".csv":
        return _normalization_result_from_json(
            _load_one_csv_row(artifact_path, source="normalization result")
        )
    raise DryRunLoadError(f"unsupported normalization result extension: {suffix}")


def load_review_context_from_path(path: str | Path) -> dict[str, Any]:
    """Load review context from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        payload = _read_json(artifact_path)
        if not isinstance(payload, dict):
            raise DryRunLoadError("review context json must be a JSON object")
        return deepcopy(payload)
    if suffix == ".jsonl":
        return {
            "rows": _load_jsonl_objects(artifact_path, source="review context jsonl")
        }
    if suffix == ".csv":
        return {"rows": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported review context extension: {suffix}")


def _dry_run_key(
    *,
    review_packet_result: dict[str, Any],
    normalized_change_proposals_present: bool,
    normalization_result_present: bool,
    review_context_present: bool,
) -> str:
    summary = review_packet_result.get("manual_review_packet_summary", {})
    payload = {
        "phase": PHASE,
        "review_packet_key": review_packet_result.get("review_packet_key", ""),
        "normalized_change_proposals_present": normalized_change_proposals_present,
        "normalization_result_present": normalization_result_present,
        "review_context_present": review_context_present,
        "packet_count": summary.get("manual_review_packet_count", 0),
        "missing_inputs": review_packet_result.get("missing_inputs", []),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase47b-manual-review-packet-dry-run-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_dry_run_payload(
    normalized_change_proposals: list[dict[str, Any]] | None = None,
    normalization_result: dict[str, Any] | None = None,
    review_context: dict[str, Any] | None = None,
    review_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 47B manual review packet payload."""

    proposals = (
        deepcopy(normalized_change_proposals)
        if isinstance(normalized_change_proposals, list)
        else None
    )
    normalization = (
        deepcopy(normalization_result) if isinstance(normalization_result, dict) else None
    )
    context = deepcopy(review_context) if isinstance(review_context, dict) else None
    policy = deepcopy(review_policy) if isinstance(review_policy, dict) else {}
    review_packet_result = (
        build_controlled_exact_resume_change_set_manual_review_packet_builder_default_off(
            normalized_change_proposals=proposals,
            normalization_result=normalization,
            review_context=context,
            review_policy=policy,
        )
    )
    proposals_present = isinstance(proposals, list)
    normalization_present = isinstance(normalization, dict)
    context_present = isinstance(context, dict)
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_manual_review_packet_builder_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_packet_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "normalized_change_proposals_present": proposals_present,
        "normalization_result_present": normalization_present,
        "review_context_present": context_present,
        "review_policy": deepcopy(review_packet_result.get("review_policy", {})),
        "review_packet_result": deepcopy(review_packet_result),
        "manual_review_packets": deepcopy(
            review_packet_result.get("manual_review_packets", [])
        ),
        "manual_review_packets_by_type": deepcopy(
            review_packet_result.get("manual_review_packets_by_type", {})
        ),
        "manual_review_packet_summary": deepcopy(
            review_packet_result.get("manual_review_packet_summary", {})
        ),
        "review_packet_findings": deepcopy(
            review_packet_result.get("review_packet_findings", [])
        ),
        "dry_run_summary": {
            "review_packet_phase": review_packet_result.get("phase"),
            "normalized_change_proposals_present": proposals_present,
            "normalization_result_present": normalization_present,
            "review_context_present": context_present,
            "manual_review_packet_count": len(
                review_packet_result.get("manual_review_packets", [])
            ),
            "missing_input_count": len(review_packet_result.get("missing_inputs", [])),
            "manual_review_packets_created": True,
            "ui_readback_performed": False,
            "user_acceptance_performed": False,
            "resume_change_applied": False,
        },
        "dry_run_key": _dry_run_key(
            review_packet_result=review_packet_result,
            normalized_change_proposals_present=proposals_present,
            normalization_result_present=normalization_present,
            review_context_present=context_present,
        ),
        "manual_review_packets_created": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _review_policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    if args.max_review_packets is not None:
        policy["max_review_packets"] = args.max_review_packets
    if args.exclude_before_after_text:
        policy["include_before_after_text"] = False
    if args.exclude_risk_flags:
        policy["include_risk_flags"] = False
    if args.exclude_evidence:
        policy["include_evidence"] = False
    if args.manual_review_required_false:
        policy["require_manual_review"] = False
    if args.requires_user_acceptance_false:
        policy["require_user_acceptance"] = False
    if args.disable_group_by_change_type:
        policy["group_by_change_type"] = False
    if args.sort_by_change_type:
        policy["sort_by_change_type"] = True
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build exact resume change-set manual review packets.",
    )
    parser.add_argument("--input", required=True, help="Normalized proposal input file")
    parser.add_argument(
        "--normalization-result",
        help="Optional Phase 46 normalization result file",
    )
    parser.add_argument("--review-context", help="Optional review context file")
    parser.add_argument("--max-review-packets", type=int)
    parser.add_argument("--exclude-before-after-text", action="store_true")
    parser.add_argument("--exclude-risk-flags", action="store_true")
    parser.add_argument("--exclude-evidence", action="store_true")
    parser.add_argument("--manual-review-required-false", action="store_true")
    parser.add_argument("--requires-user-acceptance-false", action="store_true")
    parser.add_argument("--disable-group-by-change-type", action="store_true")
    parser.add_argument("--sort-by-change-type", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 47B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        normalized_change_proposals = load_normalized_change_proposals_from_path(
            args.input
        )
        normalization_result = (
            load_normalization_result_from_path(args.normalization_result)
            if args.normalization_result
            else None
        )
        review_context = (
            load_review_context_from_path(args.review_context)
            if args.review_context
            else None
        )
        payload = build_dry_run_payload(
            normalized_change_proposals=normalized_change_proposals,
            normalization_result=normalization_result,
            review_context=review_context,
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
