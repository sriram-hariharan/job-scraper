"""Default-off dry-run command for exact-change provider-call boundaries."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_provider_call_boundary_default_off import (
    build_controlled_exact_resume_change_set_provider_call_boundary_default_off,
)


PHASE = "44B"
REQUEST_TYPE = "exact_resume_change_set_refinement"
FALSE_ACTION_KEYS = (
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
    """Raised when Phase 44B dry-run input cannot be loaded."""


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
    return rows


def _load_one_csv_row(path: Path, *, source: str) -> dict[str, Any]:
    rows = _load_csv_rows(path)
    if len(rows) != 1:
        raise DryRunLoadError(f"{source} csv must contain exactly one row")
    return rows[0]


def _is_request_packet(value: Any) -> bool:
    return isinstance(value, dict) and value.get("request_type") == REQUEST_TYPE


def _request_packet_from_wrapper(payload: Any) -> dict[str, Any]:
    if _is_request_packet(payload):
        return deepcopy(payload)
    if not isinstance(payload, dict):
        raise DryRunLoadError("request packet input must be a JSON object")
    direct = payload.get("request_packet")
    if _is_request_packet(direct):
        return deepcopy(direct)
    nested_result = payload.get("request_result")
    if isinstance(nested_result, dict) and _is_request_packet(
        nested_result.get("request_packet")
    ):
        return deepcopy(nested_result["request_packet"])
    raise DryRunLoadError(
        "request packet input must include request_type exact_resume_change_set_refinement"
    )


def load_request_packet_from_path(path: str | Path) -> dict[str, Any]:
    """Load one Phase 43 request packet from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _request_packet_from_wrapper(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _request_packet_from_wrapper(
            _load_one_jsonl_object(artifact_path, source="request packet jsonl")
        )
    if suffix == ".csv":
        return _request_packet_from_wrapper(
            _load_one_csv_row(artifact_path, source="request packet")
        )
    raise DryRunLoadError(f"unsupported request packet extension: {suffix}")


def _request_result_from_wrapper(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DryRunLoadError("request result input must be a JSON object")
    nested_result = payload.get("request_result")
    if isinstance(nested_result, dict):
        return deepcopy(nested_result)
    if isinstance(payload.get("request_packet"), dict):
        return deepcopy(payload)
    if _is_request_packet(payload):
        return {"request_packet": deepcopy(payload)}
    raise DryRunLoadError("request result input must include request_result or request_packet")


def load_request_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load one Phase 43 request result from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _request_result_from_wrapper(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _request_result_from_wrapper(
            _load_one_jsonl_object(artifact_path, source="request result jsonl")
        )
    if suffix == ".csv":
        return _request_result_from_wrapper(
            _load_one_csv_row(artifact_path, source="request result")
        )
    raise DryRunLoadError(f"unsupported request result extension: {suffix}")


def load_provider_response_fixture_from_path(path: str | Path) -> Any:
    """Load a local simulated provider response fixture."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return deepcopy(_read_json(artifact_path))
    if suffix == ".jsonl":
        return {"fixture_rows": _load_jsonl_objects(artifact_path, source="fixture jsonl")}
    if suffix == ".csv":
        return {"fixture_rows": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported provider response fixture extension: {suffix}")


def _make_simulated_provider(fixture: Any):
    copied_fixture = deepcopy(fixture)

    def simulated_provider(_request_packet: dict[str, Any]) -> Any:
        return deepcopy(copied_fixture)

    return simulated_provider


def _dry_run_key(boundary_result: dict[str, Any]) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"boundary_phase={boundary_result.get('phase', '')}",
            f"packet={bool(boundary_result.get('request_packet_present'))}",
            f"valid={bool(boundary_result.get('request_packet_valid'))}",
            f"attempted={bool(boundary_result.get('provider_call_attempted'))}",
            f"performed={bool(boundary_result.get('provider_call_performed'))}",
        )
    )


def build_dry_run_payload(
    request_packet: dict[str, Any] | None = None,
    request_result: dict[str, Any] | None = None,
    provider_response_fixture: Any = None,
    enable_provider_call: bool = False,
    manual_trigger_confirmed: bool = False,
    provider_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 44B provider-boundary dry-run payload."""

    packet = deepcopy(request_packet) if isinstance(request_packet, dict) else None
    result = deepcopy(request_result) if isinstance(request_result, dict) else None
    fixture_present = provider_response_fixture is not None
    fixture = deepcopy(provider_response_fixture)
    policy = deepcopy(provider_policy) if isinstance(provider_policy, dict) else {}
    simulated_provider = _make_simulated_provider(fixture) if fixture_present else None
    boundary_result = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=packet,
        request_result=result,
        provider_callable=simulated_provider,
        enable_provider_call=bool(enable_provider_call),
        manual_trigger_confirmed=bool(manual_trigger_confirmed),
        provider_policy=policy,
    )
    provider_call_result = deepcopy(boundary_result.get("provider_call_result", {}))
    provider_response = deepcopy(boundary_result.get("provider_response"))
    provider_response_summary = deepcopy(
        boundary_result.get("provider_response_summary", {})
    )
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_provider_call_boundary_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "provider_call_boundary_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "manual_trigger_required": True,
        "manual_trigger_confirmed": bool(manual_trigger_confirmed),
        "request_packet_present": isinstance(request_packet, dict),
        "request_result_present": isinstance(request_result, dict),
        "provider_response_fixture_present": fixture_present,
        "simulated_provider_callable_available": fixture_present,
        "enable_provider_call": bool(enable_provider_call),
        "provider_policy": deepcopy(boundary_result.get("provider_policy", policy)),
        "provider_call_result": provider_call_result,
        "provider_response": provider_response,
        "provider_response_present": bool(
            boundary_result.get("provider_response_present")
        ),
        "provider_response_type": boundary_result.get("provider_response_type", "none"),
        "provider_response_summary": provider_response_summary,
        "provider_call_blocked_reason": boundary_result.get(
            "provider_call_blocked_reason",
            "",
        ),
        "dry_run_summary": {
            "boundary_phase": boundary_result.get("phase"),
            "request_packet_valid": bool(boundary_result.get("request_packet_valid")),
            "provider_call_allowed": bool(boundary_result.get("provider_call_allowed")),
            "provider_call_attempted": bool(
                boundary_result.get("provider_call_attempted")
            ),
            "provider_call_performed": bool(
                boundary_result.get("provider_call_performed")
            ),
            "simulated_fixture_used": fixture_present
            and bool(boundary_result.get("provider_call_performed")),
            "network_call_performed": False,
        },
        "dry_run_key": _dry_run_key(boundary_result),
        "provider_call_attempted": bool(boundary_result.get("provider_call_attempted")),
        "provider_call_performed": bool(boundary_result.get("provider_call_performed")),
        "llm_call_performed": bool(boundary_result.get("llm_call_performed")),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _provider_policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    policy["allow_provider_call"] = bool(args.allow_provider_call)
    policy["require_manual_trigger"] = True
    if args.allow_missing_provider_callable:
        policy["require_provider_callable"] = False
    if args.no_capture_raw_response:
        policy["capture_raw_response"] = False
    if args.max_response_chars is not None:
        policy["max_response_chars"] = args.max_response_chars
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build default-off exact resume change-set provider-call boundaries.",
    )
    parser.add_argument("--input", required=True, help="Request packet input file")
    parser.add_argument("--request-result", help="Optional Phase 43 request result file")
    parser.add_argument(
        "--provider-response-fixture",
        help="Optional local simulated provider response fixture",
    )
    parser.add_argument("--enable-provider-call", action="store_true")
    parser.add_argument("--manual-trigger-confirmed", action="store_true")
    parser.add_argument("--allow-provider-call", action="store_true")
    parser.add_argument("--allow-missing-provider-callable", action="store_true")
    parser.add_argument("--no-capture-raw-response", action="store_true")
    parser.add_argument("--max-response-chars", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 44B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        request_packet = load_request_packet_from_path(args.input)
        request_result = (
            load_request_result_from_path(args.request_result)
            if args.request_result
            else None
        )
        fixture = (
            load_provider_response_fixture_from_path(args.provider_response_fixture)
            if args.provider_response_fixture
            else None
        )
        payload = build_dry_run_payload(
            request_packet=request_packet,
            request_result=request_result,
            provider_response_fixture=fixture,
            enable_provider_call=args.enable_provider_call,
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
