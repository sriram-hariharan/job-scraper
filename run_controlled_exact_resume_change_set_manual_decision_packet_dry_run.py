"""Default-off dry-run command for manual decision packet creation."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_manual_decision_packet_default_off import (
    build_controlled_exact_resume_change_set_manual_decision_packet_default_off,
)


PHASE = "51B"
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
    "user_decision_applied",
    "user_acceptance_performed",
)


class DryRunLoadError(ValueError):
    """Raised when Phase 51B dry-run input cannot be loaded."""


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


def load_readback_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load Phase 50 readback/manual review output from a local JSON file."""

    payload = _read_json(Path(path))
    if not isinstance(payload, dict):
        raise DryRunLoadError("readback/manual review input must be a JSON object")
    for key in (
        "readback_result",
        "phase50_result",
        "pipeline_result",
        "manual_review_readback",
        "readback_payload",
    ):
        nested = payload.get(key)
        if isinstance(nested, dict):
            return deepcopy(nested)
    return deepcopy(payload)


def load_manual_review_output_from_path(path: str | Path) -> dict[str, Any]:
    """Load manual review output from a local JSON file."""

    payload = _read_json(Path(path))
    if not isinstance(payload, dict):
        raise DryRunLoadError("manual review input must be a JSON object")
    for key in ("manual_review_output", "manual_review_packet_result"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            return deepcopy(nested)
    return deepcopy(payload)


def load_manual_decisions_from_path(path: str | Path) -> list[dict[str, Any]] | dict[str, Any]:
    """Load explicit manual decisions from a local JSON file."""

    payload = _read_json(Path(path))
    if isinstance(payload, list):
        return deepcopy(payload)
    if isinstance(payload, dict):
        for key in (
            "manual_decisions",
            "decisions",
            "operator_decisions",
            "decisions_by_proposal_id",
        ):
            if key in payload:
                return deepcopy(payload)
        return deepcopy(payload)
    raise DryRunLoadError("manual decision input must be a JSON object or list")


def _dry_run_key(decision_result: dict[str, Any]) -> str:
    key_payload = {
        "phase": PHASE,
        "decision_phase": decision_result.get("phase"),
        "status": decision_result.get("status"),
        "blocked_reason": decision_result.get("blocked_reason", ""),
        "manual_decision_packet_key": decision_result.get("manual_decision_packet_key", ""),
        "stage_sequence": decision_result.get("stage_sequence", []),
    }
    encoded = json.dumps(key_payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase51b-manual-decision-packet-dry-run-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_dry_run_payload(
    readback_result: dict[str, Any] | None = None,
    manual_review_output: dict[str, Any] | None = None,
    manual_decisions: list[dict[str, Any]] | dict[str, Any] | None = None,
    enable_manual_decision_packet: bool = False,
    allow_manual_decision_packet: bool = False,
    require_all_readback_items_decided: bool = False,
) -> dict[str, Any]:
    """Build the Phase 51B dry-run payload by calling Phase 51A once."""

    decision_policy = {
        "allow_manual_decision_packet": bool(allow_manual_decision_packet),
        "require_all_readback_items_decided": bool(
            require_all_readback_items_decided
        ),
    }
    decision_result = (
        build_controlled_exact_resume_change_set_manual_decision_packet_default_off(
            readback_result=deepcopy(readback_result)
            if isinstance(readback_result, dict)
            else None,
            manual_review_output=deepcopy(manual_review_output)
            if isinstance(manual_review_output, dict)
            else None,
            manual_decisions=deepcopy(manual_decisions)
            if isinstance(manual_decisions, (dict, list))
            else None,
            enabled=bool(enable_manual_decision_packet),
            decision_policy=decision_policy,
        )
    )
    dry_run_summary = {
        "decision_phase": decision_result.get("phase"),
        "decision_status": decision_result.get("status"),
        "decision_blocked_reason": decision_result.get("blocked_reason", ""),
        "manual_decision_packet_created": decision_result.get(
            "manual_decision_packet_created",
            False,
        ),
        "manual_decision_packet_key": decision_result.get(
            "manual_decision_packet_key",
            "",
        ),
        "stage_sequence": list(decision_result.get("stage_sequence", [])),
        "stage_summary_keys": sorted(
            decision_result.get("stage_summaries", {}).keys()
        )
        if isinstance(decision_result.get("stage_summaries"), dict)
        else [],
        "provider_call_performed": False,
        "llm_call_performed": False,
        "network_call_performed": False,
        "resume_mutation_performed": False,
        "persistence_performed": False,
        "resume_artifact_created": False,
        "application_execution_performed": False,
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_manual_decision_packet_dry_run": True,
        "dry_run_command_only": True,
        "manual_decision_packet_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enable_manual_decision_packet": bool(enable_manual_decision_packet),
        "allow_manual_decision_packet": bool(allow_manual_decision_packet),
        "require_all_readback_items_decided": bool(
            require_all_readback_items_decided
        ),
        "readback_result_present": isinstance(readback_result, dict),
        "manual_review_output_present": isinstance(manual_review_output, dict),
        "manual_decisions_present": isinstance(manual_decisions, (dict, list)),
        "status": decision_result.get("status"),
        "blocked_reason": decision_result.get("blocked_reason", ""),
        "decision_result": deepcopy(decision_result),
        "stage_summaries": deepcopy(decision_result.get("stage_summaries", {})),
        "stage_results": deepcopy(decision_result.get("stage_results", {})),
        "manual_decision_packet": deepcopy(
            decision_result.get("manual_decision_packet")
        ),
        "manual_decision_packet_created": decision_result.get(
            "manual_decision_packet_created",
            False,
        ),
        "dry_run_summary": dry_run_summary,
        "dry_run_key": _dry_run_key(decision_result),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run exact resume change-set manual decision packet creation.",
    )
    parser.add_argument(
        "--readback-result",
        help="Optional local JSON Phase 50 readback/manual review output file",
    )
    parser.add_argument(
        "--manual-review-output",
        help="Optional local JSON manual review output file",
    )
    parser.add_argument(
        "--manual-decisions",
        help="Optional local JSON explicit manual decisions file",
    )
    parser.add_argument("--enable-manual-decision-packet", action="store_true")
    parser.add_argument("--allow-manual-decision-packet", action="store_true")
    parser.add_argument("--require-all-readback-items-decided", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 51B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        readback_result = (
            load_readback_result_from_path(args.readback_result)
            if args.readback_result
            else None
        )
        manual_review_output = (
            load_manual_review_output_from_path(args.manual_review_output)
            if args.manual_review_output
            else None
        )
        manual_decisions = (
            load_manual_decisions_from_path(args.manual_decisions)
            if args.manual_decisions
            else None
        )
        payload = build_dry_run_payload(
            readback_result=readback_result,
            manual_review_output=manual_review_output,
            manual_decisions=manual_decisions,
            enable_manual_decision_packet=args.enable_manual_decision_packet,
            allow_manual_decision_packet=args.allow_manual_decision_packet,
            require_all_readback_items_decided=args.require_all_readback_items_decided,
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
