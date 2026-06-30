"""Default-off dry-run command for approved change plan packets."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_approved_change_plan_packet_default_off import (
    build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off,
)


PHASE = "53B"
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
    """Raised when Phase 53B dry-run input cannot be loaded."""


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


def load_manual_decision_readback_from_path(path: str | Path) -> dict[str, Any]:
    """Load a Phase 52 manual decision readback payload from local JSON."""

    payload = _read_json(Path(path))
    if not isinstance(payload, dict):
        raise DryRunLoadError("manual decision readback input must be a JSON object")
    return deepcopy(payload)


def _dry_run_key(plan_result: dict[str, Any]) -> str:
    key_payload = {
        "phase": PHASE,
        "plan_phase": plan_result.get("phase"),
        "status": plan_result.get("status"),
        "blocked_reason": plan_result.get("blocked_reason", ""),
        "approved_change_plan_packet_key": plan_result.get(
            "approved_change_plan_packet_key",
            "",
        ),
        "stage_sequence": plan_result.get("stage_sequence", []),
    }
    encoded = json.dumps(key_payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase53b-approved-change-plan-packet-dry-run-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_dry_run_payload(
    manual_decision_readback: dict[str, Any] | None = None,
    enable_approved_change_plan_packet: bool = False,
    allow_approved_change_plan_packet: bool = False,
) -> dict[str, Any]:
    """Build the Phase 53B dry-run payload by calling Phase 53A once."""

    plan_policy = {
        "allow_approved_change_plan_packet": bool(allow_approved_change_plan_packet)
    }
    plan_result = (
        build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
            manual_decision_readback_result=deepcopy(manual_decision_readback)
            if isinstance(manual_decision_readback, dict)
            else None,
            enabled=bool(enable_approved_change_plan_packet),
            plan_policy=plan_policy,
        )
    )
    dry_run_summary = {
        "plan_phase": plan_result.get("phase"),
        "plan_status": plan_result.get("status"),
        "plan_blocked_reason": plan_result.get("blocked_reason", ""),
        "approved_change_plan_packet_created": plan_result.get(
            "approved_change_plan_packet_created",
            False,
        ),
        "approved_change_plan_packet_key": plan_result.get(
            "approved_change_plan_packet_key",
            "",
        ),
        "stage_sequence": list(plan_result.get("stage_sequence", [])),
        "stage_summary_keys": sorted(plan_result.get("stage_summaries", {}).keys())
        if isinstance(plan_result.get("stage_summaries"), dict)
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
        "controlled_exact_resume_change_set_approved_change_plan_packet_dry_run": True,
        "dry_run_command_only": True,
        "approved_change_plan_packet_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enable_approved_change_plan_packet": bool(
            enable_approved_change_plan_packet
        ),
        "allow_approved_change_plan_packet": bool(
            allow_approved_change_plan_packet
        ),
        "manual_decision_readback_present": isinstance(
            manual_decision_readback,
            dict,
        ),
        "status": plan_result.get("status"),
        "blocked_reason": plan_result.get("blocked_reason", ""),
        "plan_result": deepcopy(plan_result),
        "stage_summaries": deepcopy(plan_result.get("stage_summaries", {})),
        "stage_results": deepcopy(plan_result.get("stage_results", {})),
        "approved_change_plan_packet": deepcopy(
            plan_result.get("approved_change_plan_packet")
        ),
        "approved_change_plan_packet_created": plan_result.get(
            "approved_change_plan_packet_created",
            False,
        ),
        "dry_run_summary": dry_run_summary,
        "dry_run_key": _dry_run_key(plan_result),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run exact resume change-set approved change plan packet.",
    )
    parser.add_argument(
        "--manual-decision-readback",
        help="Optional local JSON Phase 52 manual decision readback file",
    )
    parser.add_argument("--enable-approved-change-plan-packet", action="store_true")
    parser.add_argument("--allow-approved-change-plan-packet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 53B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        manual_decision_readback = (
            load_manual_decision_readback_from_path(args.manual_decision_readback)
            if args.manual_decision_readback
            else None
        )
        payload = build_dry_run_payload(
            manual_decision_readback=manual_decision_readback,
            enable_approved_change_plan_packet=(
                args.enable_approved_change_plan_packet
            ),
            allow_approved_change_plan_packet=args.allow_approved_change_plan_packet,
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
