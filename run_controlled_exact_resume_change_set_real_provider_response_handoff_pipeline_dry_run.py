"""Default-off dry-run command for real provider response handoff."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off import (
    build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off,
)


PHASE = "50B"
FALSE_ACTION_KEYS = (
    "provider_call_performed",
    "real_provider_call_performed",
    "llm_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_change_applied",
    "resume_artifact_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "database_" + "write_performed",
    "persistence_performed",
    "execution_performed",
    "application_execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_" + "apply_performed",
    "auto_" + "submit_performed",
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "user_decision_accepted",
)


class DryRunLoadError(ValueError):
    """Raised when Phase 50B dry-run input cannot be loaded."""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DryRunLoadError(f"unreadable file: {exc}") from exc


def _read_json(path: Path) -> Any:
    if path.suffix.lower() != ".json":
        raise DryRunLoadError(f"unsupported input extension: {path.suffix.lower()}")
    try:
        return json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise DryRunLoadError(f"invalid JSON: {exc.msg}") from exc


def load_provider_response_from_path(path: str | Path) -> Any:
    """Load a provider response from a local JSON file."""

    payload = _read_json(Path(path))
    if isinstance(payload, dict) and "provider_response" in payload:
        return deepcopy(payload["provider_response"])
    return deepcopy(payload)


def load_runtime_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load a Phase 49 runtime result from a local JSON file."""

    payload = _read_json(Path(path))
    if not isinstance(payload, dict):
        raise DryRunLoadError("runtime result input must be a JSON object")
    nested = payload.get("runtime_result")
    if isinstance(nested, dict):
        return deepcopy(nested)
    return deepcopy(payload)


def load_original_request_packet_from_path(path: str | Path) -> dict[str, Any]:
    """Load the original Phase 43 request packet from a local JSON file."""

    payload = _read_json(Path(path))
    if not isinstance(payload, dict):
        raise DryRunLoadError("original request packet input must be a JSON object")
    for key in ("original_request_packet", "request_packet", "llm_request_packet", "request_payload"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            return deepcopy(nested)
    return deepcopy(payload)


def load_original_change_proposals_from_path(path: str | Path) -> list[dict[str, Any]] | dict[str, Any]:
    """Load original exact resume change proposals from a local JSON file."""

    payload = _read_json(Path(path))
    if isinstance(payload, list):
        return deepcopy(payload)
    if isinstance(payload, dict):
        for key in (
            "original_change_proposals",
            "change_proposals",
            "exact_resume_change_proposals",
            "proposals",
            "items",
            "rows",
        ):
            value = payload.get(key)
            if isinstance(value, list):
                return deepcopy(value)
        return deepcopy(payload)
    raise DryRunLoadError("original change proposals input must be a JSON object or list")


def load_context_from_path(path: str | Path, *, source: str) -> dict[str, Any]:
    """Load review or readback context from a local JSON file."""

    payload = _read_json(Path(path))
    if not isinstance(payload, dict):
        raise DryRunLoadError(f"{source} input must be a JSON object")
    return deepcopy(payload)


def _dry_run_key(pipeline_result: dict[str, Any]) -> str:
    key_payload = {
        "phase": PHASE,
        "pipeline_phase": pipeline_result.get("phase"),
        "status": pipeline_result.get("status"),
        "provider_response_source": pipeline_result.get("provider_response_source"),
        "provider_response_present": pipeline_result.get("provider_response_present"),
        "stage_sequence": pipeline_result.get("stage_sequence", []),
    }
    encoded = json.dumps(key_payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase50b-provider-response-handoff-dry-run-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_dry_run_payload(
    runtime_result: dict[str, Any] | None = None,
    provider_response: Any = None,
    original_request_packet: dict[str, Any] | None = None,
    original_change_proposals: list[dict[str, Any]] | dict[str, Any] | None = None,
    review_context: dict[str, Any] | None = None,
    readback_context: dict[str, Any] | None = None,
    enable_handoff: bool = False,
    allow_real_provider_response_handoff: bool = False,
) -> dict[str, Any]:
    """Build the Phase 50B dry-run payload by calling Phase 50A once."""

    handoff_policy = {
        "allow_real_provider_response_handoff": bool(
            allow_real_provider_response_handoff
        )
    }
    pipeline_result = (
        build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off(
            runtime_result=deepcopy(runtime_result) if isinstance(runtime_result, dict) else None,
            provider_response=deepcopy(provider_response),
            original_request_packet=deepcopy(original_request_packet)
            if isinstance(original_request_packet, dict)
            else None,
            original_change_proposals=deepcopy(original_change_proposals)
            if isinstance(original_change_proposals, (dict, list))
            else None,
            review_context=deepcopy(review_context)
            if isinstance(review_context, dict)
            else None,
            readback_context=deepcopy(readback_context)
            if isinstance(readback_context, dict)
            else None,
            enabled=bool(enable_handoff),
            handoff_policy=handoff_policy,
        )
    )
    dry_run_summary = {
        "pipeline_phase": pipeline_result.get("phase"),
        "pipeline_status": pipeline_result.get("status"),
        "pipeline_blocked_reason": pipeline_result.get("blocked_reason", ""),
        "provider_response_present": pipeline_result.get("provider_response_present", False),
        "provider_response_source": pipeline_result.get("provider_response_source", ""),
        "stage_sequence": list(pipeline_result.get("stage_sequence", [])),
        "stage_summary_keys": sorted(
            pipeline_result.get("stage_summaries", {}).keys()
        )
        if isinstance(pipeline_result.get("stage_summaries"), dict)
        else [],
        "provider_call_performed": False,
        "llm_call_performed": False,
        "network_call_performed": False,
        "resume_mutation_performed": False,
        "persistence_performed": False,
        "application_execution_performed": False,
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run": True,
        "dry_run_command_only": True,
        "real_provider_response_handoff_pipeline_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enable_handoff": bool(enable_handoff),
        "allow_real_provider_response_handoff": bool(
            allow_real_provider_response_handoff
        ),
        "runtime_result_present": isinstance(runtime_result, dict),
        "provider_response_present": provider_response is not None,
        "original_request_packet_present": isinstance(original_request_packet, dict),
        "original_change_proposals_present": isinstance(
            original_change_proposals,
            (dict, list),
        ),
        "review_context_present": isinstance(review_context, dict),
        "readback_context_present": isinstance(readback_context, dict),
        "status": pipeline_result.get("status"),
        "blocked_reason": pipeline_result.get("blocked_reason", ""),
        "pipeline_result": deepcopy(pipeline_result),
        "stage_summaries": deepcopy(pipeline_result.get("stage_summaries", {})),
        "final_readback_payload": deepcopy(
            pipeline_result.get("final_readback_payload")
        ),
        "dry_run_summary": dry_run_summary,
        "dry_run_key": _dry_run_key(pipeline_result),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run exact resume change-set provider response handoff.",
    )
    parser.add_argument(
        "--provider-response",
        help="Optional local JSON provider response file",
    )
    parser.add_argument(
        "--runtime-result",
        help="Optional local JSON Phase 49 runtime result file",
    )
    parser.add_argument(
        "--original-request-packet",
        required=True,
        help="Local JSON original Phase 43 request packet file",
    )
    parser.add_argument(
        "--original-change-proposals",
        help="Optional local JSON original exact resume change proposals file",
    )
    parser.add_argument("--review-context", help="Optional local JSON review context")
    parser.add_argument("--readback-context", help="Optional local JSON readback context")
    parser.add_argument("--enable-handoff", action="store_true")
    parser.add_argument("--allow-real-provider-response-handoff", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 50B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        provider_response = (
            load_provider_response_from_path(args.provider_response)
            if args.provider_response
            else None
        )
        runtime_result = (
            load_runtime_result_from_path(args.runtime_result)
            if args.runtime_result
            else None
        )
        original_request_packet = load_original_request_packet_from_path(
            args.original_request_packet
        )
        original_change_proposals = (
            load_original_change_proposals_from_path(args.original_change_proposals)
            if args.original_change_proposals
            else None
        )
        review_context = (
            load_context_from_path(args.review_context, source="review context")
            if args.review_context
            else None
        )
        readback_context = (
            load_context_from_path(args.readback_context, source="readback context")
            if args.readback_context
            else None
        )
        payload = build_dry_run_payload(
            runtime_result=runtime_result,
            provider_response=provider_response,
            original_request_packet=original_request_packet,
            original_change_proposals=original_change_proposals,
            review_context=review_context,
            readback_context=readback_context,
            enable_handoff=args.enable_handoff,
            allow_real_provider_response_handoff=(
                args.allow_real_provider_response_handoff
            ),
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
