"""Default-off dry-run command for exact-change real provider runtime."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off import (
    build_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off,
)


PHASE = "49B"
REQUEST_PACKET_KEYS = ("request_packet", "llm_request_packet", "request_payload")
REQUEST_RESULT_KEYS = (
    "request_result",
    "request_packet",
    "llm_request_packet",
    "request_payload",
)
FALSE_ACTION_KEYS = (
    "provider_response_validation_performed",
    "provider_response_normalization_performed",
    "manual_review_packets_created",
    "manual_review_readback_payload_created",
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_change_applied",
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
    """Raised when Phase 49B dry-run input cannot be loaded."""


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


def _load_jsonl_object(path: Path, *, source: str) -> dict[str, Any]:
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
    if len(rows) != 1:
        raise DryRunLoadError(f"{source} must contain exactly one JSON object row")
    return rows[0]


def _load_csv_object(path: Path, *, source: str) -> dict[str, Any]:
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
    if len(rows) != 1:
        raise DryRunLoadError(f"{source} csv must contain exactly one row")
    return rows[0]


def _looks_like_request_packet(value: Any) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    return any(key in value for key in ("request_type", "request_id", "messages", "prompt"))


def _request_packet_from_json(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DryRunLoadError("request packet input must be a JSON object")
    for key in REQUEST_PACKET_KEYS:
        nested = payload.get(key)
        if isinstance(nested, dict):
            if not _looks_like_request_packet(nested):
                raise DryRunLoadError(f"request packet json.{key} has invalid shape")
            return deepcopy(nested)
    if _looks_like_request_packet(payload):
        return deepcopy(payload)
    raise DryRunLoadError(
        "request packet json must be a request packet or include request_packet, "
        "llm_request_packet, or request_payload"
    )


def load_request_packet_from_path(path: str | Path) -> dict[str, Any]:
    """Load one Phase 43 request packet from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _request_packet_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _request_packet_from_json(
            _load_jsonl_object(artifact_path, source="request packet jsonl")
        )
    if suffix == ".csv":
        return _request_packet_from_json(
            _load_csv_object(artifact_path, source="request packet")
        )
    raise DryRunLoadError(f"unsupported request packet extension: {suffix}")


def _request_result_from_json(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DryRunLoadError("request result input must be a JSON object")
    if isinstance(payload.get("request_result"), dict):
        return deepcopy(payload)
    for key in ("request_packet", "llm_request_packet", "request_payload"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            if not _looks_like_request_packet(nested):
                raise DryRunLoadError(f"request result json.{key} has invalid shape")
            return deepcopy(payload)
    if _looks_like_request_packet(payload):
        return {"request_packet": deepcopy(payload)}
    raise DryRunLoadError(
        "request result json must include request_result, request_packet, "
        "llm_request_packet, or request_payload"
    )


def load_request_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load one Phase 43 request result from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _request_result_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _request_result_from_json(
            _load_jsonl_object(artifact_path, source="request result jsonl")
        )
    if suffix == ".csv":
        return _request_result_from_json(
            _load_csv_object(artifact_path, source="request result")
        )
    raise DryRunLoadError(f"unsupported request result extension: {suffix}")


def _dry_run_key(runtime_result: dict[str, Any]) -> str:
    key_payload = {
        "phase": PHASE,
        "runtime_phase": runtime_result.get("phase", ""),
        "provider_runtime_key": runtime_result.get("provider_runtime_key", ""),
        "real_provider_call_attempted": runtime_result.get("real_provider_call_attempted", False),
        "real_provider_call_performed": runtime_result.get("real_provider_call_performed", False),
        "provider_runtime_error": runtime_result.get("provider_runtime_error", ""),
    }
    encoded = json.dumps(key_payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase49b-real-provider-runtime-dry-run-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_dry_run_payload(
    request_packet: dict[str, Any] | None = None,
    request_result: dict[str, Any] | None = None,
    enable_real_provider_call: bool = False,
    manual_trigger_confirmed: bool = False,
    provider_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the Phase 49B real-provider runtime dry-run payload."""

    packet = deepcopy(request_packet) if isinstance(request_packet, dict) else None
    result = deepcopy(request_result) if isinstance(request_result, dict) else None
    policy = deepcopy(provider_policy) if isinstance(provider_policy, dict) else {}
    runtime_result = build_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off(
        request_packet=packet,
        request_result=result,
        provider_callable=None,
        enable_real_provider_call=bool(enable_real_provider_call),
        manual_trigger_confirmed=bool(manual_trigger_confirmed),
        provider_policy=policy,
    )
    dry_run_summary = {
        "runtime_adapter_phase": runtime_result.get("phase"),
        "request_packet_present": runtime_result.get("request_packet_present", False),
        "request_result_present": runtime_result.get("request_result_present", False),
        "provider_callable_path_supplied": runtime_result.get(
            "provider_callable_path_supplied",
            False,
        ),
        "provider_callable_path_allowed": runtime_result.get(
            "provider_callable_path_allowed",
            False,
        ),
        "real_provider_call_attempted": runtime_result.get(
            "real_provider_call_attempted",
            False,
        ),
        "real_provider_call_performed": runtime_result.get(
            "real_provider_call_performed",
            False,
        ),
        "provider_runtime_error_present": bool(runtime_result.get("provider_runtime_error", "")),
        "provider_response_validation_performed": False,
        "provider_response_normalization_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run": True,
        "dry_run_command_only": True,
        "real_provider_runtime_adapter_only": True,
        "read_only": True,
        "advisory_only": True,
        "provider_execution_boundary_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "request_packet_present": runtime_result.get("request_packet_present", False),
        "request_result_present": runtime_result.get("request_result_present", False),
        "provider_policy": deepcopy(runtime_result.get("provider_policy", {})),
        "runtime_result": deepcopy(runtime_result),
        "provider_callable_path_supplied": runtime_result.get(
            "provider_callable_path_supplied",
            False,
        ),
        "provider_callable_path_allowed": runtime_result.get(
            "provider_callable_path_allowed",
            False,
        ),
        "real_provider_call_allowed": runtime_result.get("real_provider_call_allowed", False),
        "real_provider_call_blocked_reason": runtime_result.get(
            "real_provider_call_blocked_reason",
            "",
        ),
        "real_provider_call_attempted": runtime_result.get(
            "real_provider_call_attempted",
            False,
        ),
        "real_provider_call_performed": runtime_result.get(
            "real_provider_call_performed",
            False,
        ),
        "llm_call_performed": runtime_result.get("llm_call_performed", False),
        "provider_response": deepcopy(runtime_result.get("provider_response")),
        "provider_response_summary": deepcopy(
            runtime_result.get("provider_response_summary", {})
        ),
        "provider_runtime_error": runtime_result.get("provider_runtime_error", ""),
        "dry_run_summary": dry_run_summary,
        "dry_run_key": _dry_run_key(runtime_result),
        "manual_trigger_confirmed": bool(manual_trigger_confirmed),
        "enable_real_provider_call": bool(enable_real_provider_call),
        "tailoring_runtime_call_performed": runtime_result.get(
            "tailoring_runtime_call_performed",
            False,
        ),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _number_or_none(value: str | None) -> int | float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise DryRunLoadError(f"invalid numeric value: {value}") from exc
    if parsed.is_integer():
        return int(parsed)
    return parsed


def _provider_policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    policy["allow_real_provider_call"] = bool(args.allow_real_provider_call)
    if args.provider_callable_path:
        policy["provider_callable_path"] = args.provider_callable_path
    if args.allowed_provider_module_prefix:
        policy["allowed_provider_module_prefixes"] = list(args.allowed_provider_module_prefix)
    if args.provider_name:
        policy["provider_name"] = args.provider_name
    if args.model_name:
        policy["model_name"] = args.model_name
    if args.temperature is not None:
        policy["temperature"] = _number_or_none(args.temperature)
    if args.max_output_tokens is not None:
        policy["max_output_tokens"] = _number_or_none(args.max_output_tokens)
    if args.request_timeout_seconds is not None:
        policy["request_timeout_seconds"] = _number_or_none(args.request_timeout_seconds)
    if args.max_response_chars is not None:
        policy["max_response_chars"] = args.max_response_chars
    if args.no_capture_raw_response:
        policy["capture_raw_response"] = False
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run exact resume change-set real provider runtime adapter.",
    )
    parser.add_argument("--input", required=True, help="Phase 43 request packet file")
    parser.add_argument("--request-result", help="Optional Phase 43 request result file")
    parser.add_argument("--enable-real-provider-call", action="store_true")
    parser.add_argument("--manual-trigger-confirmed", action="store_true")
    parser.add_argument("--allow-real-provider-call", action="store_true")
    parser.add_argument("--provider-callable-path")
    parser.add_argument("--allowed-provider-module-prefix", action="append")
    parser.add_argument("--provider-name")
    parser.add_argument("--model-name")
    parser.add_argument("--temperature")
    parser.add_argument("--max-output-tokens")
    parser.add_argument("--request-timeout-seconds")
    parser.add_argument("--max-response-chars", type=int)
    parser.add_argument("--no-capture-raw-response", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 49B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        request_packet = load_request_packet_from_path(args.input)
        request_result = (
            load_request_result_from_path(args.request_result)
            if args.request_result
            else None
        )
        payload = build_dry_run_payload(
            request_packet=request_packet,
            request_result=request_result,
            enable_real_provider_call=args.enable_real_provider_call,
            manual_trigger_confirmed=args.manual_trigger_confirmed,
            provider_policy=_provider_policy_from_args(args),
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
