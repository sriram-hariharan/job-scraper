"""Default-off dry-run command for manual decision readback."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off import (
    build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off,
)


PHASE = "52B"
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
    """Raised when Phase 52B dry-run input cannot be loaded."""


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


def load_manual_decision_packet_from_path(path: str | Path) -> dict[str, Any]:
    """Load a Phase 51 manual decision packet payload from local JSON."""

    payload = _read_json(Path(path))
    if not isinstance(payload, dict):
        raise DryRunLoadError("manual decision packet input must be a JSON object")
    return deepcopy(payload)


def _dry_run_key(readback_result: dict[str, Any]) -> str:
    key_payload = {
        "phase": PHASE,
        "readback_phase": readback_result.get("phase"),
        "status": readback_result.get("status"),
        "blocked_reason": readback_result.get("blocked_reason", ""),
        "readback_payload_key": readback_result.get("readback_payload_key", ""),
        "stage_sequence": readback_result.get("stage_sequence", []),
    }
    encoded = json.dumps(key_payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase52b-manual-decision-readback-dry-run-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_dry_run_payload(
    manual_decision_packet: dict[str, Any] | None = None,
    enable_manual_decision_readback: bool = False,
    allow_manual_decision_readback: bool = False,
) -> dict[str, Any]:
    """Build the Phase 52B dry-run payload by calling Phase 52A once."""

    readback_policy = {
        "allow_manual_decision_readback": bool(allow_manual_decision_readback)
    }
    readback_result = (
        build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off(
            manual_decision_packet_result=deepcopy(manual_decision_packet)
            if isinstance(manual_decision_packet, dict)
            else None,
            enabled=bool(enable_manual_decision_readback),
            readback_policy=readback_policy,
        )
    )
    dry_run_summary = {
        "readback_phase": readback_result.get("phase"),
        "readback_status": readback_result.get("status"),
        "readback_blocked_reason": readback_result.get("blocked_reason", ""),
        "readback_payload_created": readback_result.get(
            "readback_payload_created",
            False,
        ),
        "readback_payload_key": readback_result.get("readback_payload_key", ""),
        "stage_sequence": list(readback_result.get("stage_sequence", [])),
        "stage_summary_keys": sorted(
            readback_result.get("stage_summaries", {}).keys()
        )
        if isinstance(readback_result.get("stage_summaries"), dict)
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
        "controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run": True,
        "dry_run_command_only": True,
        "manual_decision_readback_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enable_manual_decision_readback": bool(enable_manual_decision_readback),
        "allow_manual_decision_readback": bool(allow_manual_decision_readback),
        "manual_decision_packet_present": isinstance(manual_decision_packet, dict),
        "status": readback_result.get("status"),
        "blocked_reason": readback_result.get("blocked_reason", ""),
        "readback_result": deepcopy(readback_result),
        "stage_summaries": deepcopy(readback_result.get("stage_summaries", {})),
        "stage_results": deepcopy(readback_result.get("stage_results", {})),
        "readback_payload": deepcopy(readback_result.get("readback_payload")),
        "readback_payload_created": readback_result.get(
            "readback_payload_created",
            False,
        ),
        "dry_run_summary": dry_run_summary,
        "dry_run_key": _dry_run_key(readback_result),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run exact resume change-set manual decision readback.",
    )
    parser.add_argument(
        "--manual-decision-packet",
        help="Optional local JSON Phase 51 manual decision packet file",
    )
    parser.add_argument("--enable-manual-decision-readback", action="store_true")
    parser.add_argument("--allow-manual-decision-readback", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 52B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        manual_decision_packet = (
            load_manual_decision_packet_from_path(args.manual_decision_packet)
            if args.manual_decision_packet
            else None
        )
        payload = build_dry_run_payload(
            manual_decision_packet=manual_decision_packet,
            enable_manual_decision_readback=args.enable_manual_decision_readback,
            allow_manual_decision_readback=args.allow_manual_decision_readback,
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
