"""Default-off dry-run command for exact-change provider response validation."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_provider_response_validation_default_off import (
    build_controlled_exact_resume_change_set_provider_response_validation_default_off,
)


PHASE = "45B"
REQUEST_TYPE = "exact_resume_change_set_refinement"
FALSE_ACTION_KEYS = (
    "provider_response_normalization_performed",
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


class DryRunLoadError(ValueError):
    """Raised when Phase 45B dry-run input cannot be loaded."""


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
        rows = _load_jsonl_objects(artifact_path, source="provider response jsonl")
        if len(rows) == 1:
            return deepcopy(rows[0])
        return _provider_response_from_rows(rows)
    if suffix == ".txt":
        return _read_text(artifact_path)
    if suffix == ".csv":
        return _provider_response_from_rows(_load_csv_rows(artifact_path))
    raise DryRunLoadError(f"unsupported provider response extension: {suffix}")


def _provider_call_result_from_wrapper(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DryRunLoadError("provider call result input must be a JSON object")
    if "provider_response" in payload:
        return deepcopy(payload)
    nested = payload.get("provider_call_result")
    if isinstance(nested, dict):
        copied = deepcopy(payload)
        if "provider_response" in nested or "provider_response" in copied:
            return copied
        return {"provider_call_result": deepcopy(nested)}
    raise DryRunLoadError(
        "provider call result input must include provider_response or provider_call_result"
    )


def load_provider_call_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load one provider call result from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _provider_call_result_from_wrapper(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _provider_call_result_from_wrapper(
            _load_one_jsonl_object(artifact_path, source="provider call result jsonl")
        )
    if suffix == ".csv":
        return _provider_call_result_from_wrapper(
            _load_one_csv_row(artifact_path, source="provider call result")
        )
    raise DryRunLoadError(f"unsupported provider call result extension: {suffix}")


def _is_request_packet(value: Any) -> bool:
    return isinstance(value, dict) and value.get("request_type") == REQUEST_TYPE


def _original_request_packet_from_wrapper(payload: Any) -> dict[str, Any]:
    if _is_request_packet(payload):
        return deepcopy(payload)
    if not isinstance(payload, dict):
        raise DryRunLoadError("original request packet input must be a JSON object")
    original = payload.get("original_request_packet")
    if _is_request_packet(original):
        return deepcopy(original)
    direct = payload.get("request_packet")
    if _is_request_packet(direct):
        return deepcopy(direct)
    nested_result = payload.get("request_result")
    if isinstance(nested_result, dict) and _is_request_packet(
        nested_result.get("request_packet")
    ):
        return deepcopy(nested_result["request_packet"])
    raise DryRunLoadError(
        "original request packet input must include request_type exact_resume_change_set_refinement"
    )


def load_original_request_packet_from_path(path: str | Path) -> dict[str, Any]:
    """Load one original Phase 43 request packet from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _original_request_packet_from_wrapper(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _original_request_packet_from_wrapper(
            _load_one_jsonl_object(artifact_path, source="original request packet jsonl")
        )
    if suffix == ".csv":
        return _original_request_packet_from_wrapper(
            _load_one_csv_row(artifact_path, source="original request packet")
        )
    raise DryRunLoadError(f"unsupported original request packet extension: {suffix}")


def _dry_run_key(validation_result: dict[str, Any]) -> str:
    summary = validation_result.get("validation_summary", {})
    return "|".join(
        (
            f"phase={PHASE}",
            f"validation_phase={validation_result.get('phase', '')}",
            f"response={bool(validation_result.get('provider_response_present'))}",
            f"call_result={bool(validation_result.get('provider_call_result_present'))}",
            f"request={bool(validation_result.get('original_request_packet_present'))}",
            f"valid={bool(validation_result.get('provider_response_valid'))}",
            f"errors={summary.get('error_count', 0)}",
        )
    )


def build_dry_run_payload(
    provider_response: Any = None,
    provider_call_result: dict[str, Any] | None = None,
    original_request_packet: dict[str, Any] | None = None,
    validation_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 45B provider-response validation payload."""

    response = deepcopy(provider_response)
    call_result = (
        deepcopy(provider_call_result) if isinstance(provider_call_result, dict) else None
    )
    request_packet = (
        deepcopy(original_request_packet)
        if isinstance(original_request_packet, dict)
        else None
    )
    policy = deepcopy(validation_policy) if isinstance(validation_policy, dict) else {}
    validation_result = (
        build_controlled_exact_resume_change_set_provider_response_validation_default_off(
            provider_response=response,
            provider_call_result=call_result,
            original_request_packet=request_packet,
            validation_policy=policy,
        )
    )
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_provider_response_validation_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "validation_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "provider_response_present": bool(
            validation_result.get("provider_response_present")
        ),
        "provider_call_result_present": bool(
            validation_result.get("provider_call_result_present")
        ),
        "original_request_packet_present": bool(
            validation_result.get("original_request_packet_present")
        ),
        "validation_policy": deepcopy(validation_result.get("validation_policy", {})),
        "validation_result": deepcopy(validation_result),
        "parsed_provider_response": deepcopy(
            validation_result.get("parsed_provider_response")
        ),
        "provider_response_parse_status": validation_result.get(
            "provider_response_parse_status",
            "",
        ),
        "provider_response_valid": bool(
            validation_result.get("provider_response_valid")
        ),
        "validation_errors": list(validation_result.get("validation_errors", [])),
        "validation_warnings": list(validation_result.get("validation_warnings", [])),
        "refined_change_proposals": deepcopy(
            validation_result.get("refined_change_proposals", [])
        ),
        "valid_refined_change_proposal_count": int(
            validation_result.get("valid_refined_change_proposal_count", 0)
        ),
        "invalid_refined_change_proposal_count": int(
            validation_result.get("invalid_refined_change_proposal_count", 0)
        ),
        "known_proposal_ids": list(validation_result.get("known_proposal_ids", [])),
        "unknown_proposal_ids": list(
            validation_result.get("unknown_proposal_ids", [])
        ),
        "missing_required_fields_by_proposal": deepcopy(
            validation_result.get("missing_required_fields_by_proposal", {})
        ),
        "invalid_safety_flags": deepcopy(
            validation_result.get("invalid_safety_flags", {})
        ),
        "validation_summary": deepcopy(
            validation_result.get("validation_summary", {})
        ),
        "dry_run_summary": {
            "validation_phase": validation_result.get("phase"),
            "provider_response_present": bool(
                validation_result.get("provider_response_present")
            ),
            "provider_call_result_present": bool(
                validation_result.get("provider_call_result_present")
            ),
            "original_request_packet_present": bool(
                validation_result.get("original_request_packet_present")
            ),
            "provider_response_valid": bool(
                validation_result.get("provider_response_valid")
            ),
            "provider_response_validation_performed": True,
            "network_call_performed": False,
        },
        "dry_run_key": _dry_run_key(validation_result),
        "provider_response_validation_performed": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _validation_policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    if args.allow_missing_refined_change_proposals:
        policy["require_refined_change_proposals"] = False
    if args.require_known_proposal_ids:
        policy["require_known_proposal_ids"] = True
    if args.disallow_extra_top_level_keys:
        policy["allow_extra_top_level_keys"] = False
    if args.allow_empty_refined_change_proposals:
        policy["allow_empty_refined_change_proposals"] = True
    if args.max_refined_change_proposals is not None:
        policy["max_refined_change_proposals"] = args.max_refined_change_proposals
    if args.max_text_length is not None:
        policy["max_text_length"] = args.max_text_length
    if args.skip_required_boolean_safety_flags:
        policy["required_boolean_safety_flags"] = False
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate exact resume change-set provider responses.",
    )
    parser.add_argument("--input", required=True, help="Provider response input file")
    parser.add_argument(
        "--provider-call-result",
        help="Optional Phase 44 provider call result file",
    )
    parser.add_argument(
        "--original-request-packet",
        help="Optional Phase 43 original request packet file",
    )
    parser.add_argument("--allow-missing-refined-change-proposals", action="store_true")
    parser.add_argument("--require-known-proposal-ids", action="store_true")
    parser.add_argument("--disallow-extra-top-level-keys", action="store_true")
    parser.add_argument("--allow-empty-refined-change-proposals", action="store_true")
    parser.add_argument("--max-refined-change-proposals", type=int)
    parser.add_argument("--max-text-length", type=int)
    parser.add_argument("--skip-required-boolean-safety-flags", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 45B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        provider_response = load_provider_response_from_path(args.input)
        provider_call_result = (
            load_provider_call_result_from_path(args.provider_call_result)
            if args.provider_call_result
            else None
        )
        original_request_packet = (
            load_original_request_packet_from_path(args.original_request_packet)
            if args.original_request_packet
            else None
        )
        payload = build_dry_run_payload(
            provider_response=provider_response,
            provider_call_result=provider_call_result,
            original_request_packet=original_request_packet,
            validation_policy=_validation_policy_from_args(args),
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
