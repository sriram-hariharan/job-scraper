"""Default-off dry-run command for exact-change provider response normalization."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_provider_response_normalization_default_off import (
    build_controlled_exact_resume_change_set_provider_response_normalization_default_off,
)


PHASE = "46B"
FALSE_ACTION_KEYS = (
    "provider_response_validation_performed",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
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
PROPOSAL_CONTAINER_KEYS = (
    "change_proposals",
    "rows",
    "items",
    "proposals",
)


class DryRunLoadError(ValueError):
    """Raised when Phase 46B dry-run input cannot be loaded."""


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


def _ensure_validation_result_shape(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DryRunLoadError("validation result input must be a JSON object")
    if isinstance(payload.get("validation_result"), dict):
        return deepcopy(payload)
    if isinstance(payload.get("refined_change_proposals"), list):
        return deepcopy(payload)
    if "provider_response_valid" in payload or "parsed_provider_response" in payload:
        return deepcopy(payload)
    raise DryRunLoadError(
        "validation result input must include validation_result, "
        "refined_change_proposals, provider_response_valid, or parsed_provider_response"
    )


def load_validation_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load one Phase 45 validation result from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _ensure_validation_result_shape(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _ensure_validation_result_shape(
            _load_one_jsonl_object(artifact_path, source="validation result jsonl")
        )
    if suffix == ".csv":
        return _ensure_validation_result_shape(
            _load_one_csv_row(artifact_path, source="validation result")
        )
    raise DryRunLoadError(f"unsupported validation result extension: {suffix}")


def _provider_response_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "refined_change_proposals": deepcopy(rows),
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
    }


def load_provider_response_from_path(path: str | Path) -> Any:
    """Load a provider response candidate from JSON, JSONL, TXT, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return deepcopy(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _provider_response_from_rows(
            _load_jsonl_objects(artifact_path, source="provider response jsonl")
        )
    if suffix == ".txt":
        return _read_text(artifact_path)
    if suffix == ".csv":
        return _provider_response_from_rows(_load_csv_rows(artifact_path))
    raise DryRunLoadError(f"unsupported provider response extension: {suffix}")


def _ensure_proposal_rows(value: Any, *, source: str) -> list[dict[str, Any]]:
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
        return _ensure_proposal_rows(payload, source="original change proposals json")
    if isinstance(payload, dict):
        for key in PROPOSAL_CONTAINER_KEYS:
            if key in payload:
                return _ensure_proposal_rows(
                    payload[key],
                    source=f"original change proposals json.{key}",
                )
    raise DryRunLoadError(
        "original change proposals json must be a list or include "
        "change_proposals, rows, items, or proposals"
    )


def load_original_change_proposals_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load original Phase 42 change proposals from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _proposal_rows_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_objects(
            artifact_path,
            source="original change proposals jsonl",
        )
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported original change proposals extension: {suffix}")


def _dry_run_key(
    *,
    normalization_result: dict[str, Any],
    validation_result_present: bool,
    provider_response_present: bool,
    original_change_proposals_present: bool,
) -> str:
    summary = normalization_result.get("normalized_change_set_summary", {})
    payload = {
        "phase": PHASE,
        "normalization_key": normalization_result.get("normalization_key", ""),
        "validation_result_present": validation_result_present,
        "provider_response_present": provider_response_present,
        "original_change_proposals_present": original_change_proposals_present,
        "provider_response_valid": bool(
            normalization_result.get("provider_response_valid")
        ),
        "normalized_count": summary.get("normalized_refined_change_proposal_count", 0),
        "error_count": len(normalization_result.get("normalization_errors", [])),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase46b-provider-response-normalization-dry-run-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_dry_run_payload(
    validation_result: dict[str, Any] | None = None,
    provider_response: Any = None,
    original_change_proposals: list[dict[str, Any]] | None = None,
    normalization_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 46B provider-response normalization payload."""

    validation = deepcopy(validation_result) if isinstance(validation_result, dict) else None
    response = deepcopy(provider_response)
    proposals = (
        deepcopy(original_change_proposals)
        if isinstance(original_change_proposals, list)
        else None
    )
    policy = deepcopy(normalization_policy) if isinstance(normalization_policy, dict) else {}
    normalization_result = (
        build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
            validation_result=validation,
            provider_response=response,
            original_change_proposals=proposals,
            normalization_policy=policy,
        )
    )
    validation_present = isinstance(validation, dict)
    provider_present = response is not None or bool(
        normalization_result.get("provider_response_present")
    )
    proposals_present = isinstance(proposals, list)
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_provider_response_normalization_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "normalization_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "validation_result_present": validation_present,
        "provider_response_present": provider_present,
        "original_change_proposals_present": proposals_present,
        "normalization_policy": deepcopy(
            normalization_result.get("normalization_policy", {})
        ),
        "normalization_result": deepcopy(normalization_result),
        "provider_response_valid": bool(
            normalization_result.get("provider_response_valid")
        ),
        "normalized_refined_change_proposals": deepcopy(
            normalization_result.get("normalized_refined_change_proposals", [])
        ),
        "normalized_change_proposals_by_type": deepcopy(
            normalization_result.get("normalized_change_proposals_by_type", {})
        ),
        "normalized_change_set_summary": deepcopy(
            normalization_result.get("normalized_change_set_summary", {})
        ),
        "normalization_errors": list(
            normalization_result.get("normalization_errors", [])
        ),
        "normalization_warnings": list(
            normalization_result.get("normalization_warnings", [])
        ),
        "normalization_findings": deepcopy(
            normalization_result.get("normalization_findings", [])
        ),
        "dry_run_summary": {
            "normalization_phase": normalization_result.get("phase"),
            "validation_result_present": validation_present,
            "provider_response_present": provider_present,
            "original_change_proposals_present": proposals_present,
            "provider_response_valid": bool(
                normalization_result.get("provider_response_valid")
            ),
            "normalized_refined_change_proposal_count": len(
                normalization_result.get("normalized_refined_change_proposals", [])
            ),
            "normalization_error_count": len(
                normalization_result.get("normalization_errors", [])
            ),
            "provider_response_validation_performed": False,
            "provider_response_normalization_performed": True,
            "network_call_performed": False,
        },
        "dry_run_key": _dry_run_key(
            normalization_result=normalization_result,
            validation_result_present=validation_present,
            provider_response_present=provider_present,
            original_change_proposals_present=proposals_present,
        ),
        "provider_response_normalization_performed": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _normalization_policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    if args.allow_unvalidated_provider_response:
        policy["require_valid_provider_response"] = False
    if args.include_invalid_proposals:
        policy["include_invalid_proposals"] = True
    if args.max_normalized_change_proposals is not None:
        policy["max_normalized_change_proposals"] = args.max_normalized_change_proposals
    if args.no_trim_text:
        policy["trim_text"] = False
    if args.max_text_length is not None:
        policy["max_text_length"] = args.max_text_length
    if args.drop_before_after_text:
        policy["preserve_before_after_text"] = False
    if args.drop_risk_flags:
        policy["preserve_risk_flags"] = False
    if args.default_manual_review_required_false:
        policy["default_manual_review_required"] = False
    if args.default_requires_user_acceptance_false:
        policy["default_requires_user_acceptance"] = False
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize exact resume change-set provider responses.",
    )
    parser.add_argument("--input", required=True, help="Phase 45 validation result file")
    parser.add_argument("--provider-response", help="Optional provider response file")
    parser.add_argument(
        "--original-change-proposals",
        help="Optional Phase 42 original change proposals file",
    )
    parser.add_argument("--allow-unvalidated-provider-response", action="store_true")
    parser.add_argument("--include-invalid-proposals", action="store_true")
    parser.add_argument("--max-normalized-change-proposals", type=int)
    parser.add_argument("--no-trim-text", action="store_true")
    parser.add_argument("--max-text-length", type=int)
    parser.add_argument("--drop-before-after-text", action="store_true")
    parser.add_argument("--drop-risk-flags", action="store_true")
    parser.add_argument("--default-manual-review-required-false", action="store_true")
    parser.add_argument("--default-requires-user-acceptance-false", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 46B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        validation_result = load_validation_result_from_path(args.input)
        provider_response = (
            load_provider_response_from_path(args.provider_response)
            if args.provider_response
            else None
        )
        original_change_proposals = (
            load_original_change_proposals_from_path(args.original_change_proposals)
            if args.original_change_proposals
            else None
        )
        payload = build_dry_run_payload(
            validation_result=validation_result,
            provider_response=provider_response,
            original_change_proposals=original_change_proposals,
            normalization_policy=_normalization_policy_from_args(args),
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
