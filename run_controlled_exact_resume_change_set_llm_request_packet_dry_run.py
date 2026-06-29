"""Default-off dry-run command for controlled exact-change LLM request packets."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.controlled_exact_resume_change_set_llm_request_packet_default_off import (
    build_controlled_exact_resume_change_set_llm_request_packet_default_off,
)


PHASE = "43B"
CHANGE_PROPOSAL_KEYS = ("change_proposals", "rows", "items", "proposals")
PROPOSAL_RESULT_ROW_KEYS = ("change_proposals", "rows", "items")
FALSE_ACTION_KEYS = (
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
    """Raised when Phase 43B dry-run input cannot be loaded."""


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


def _ensure_object_rows(value: Any, *, source: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise DryRunLoadError(f"{source} must contain a list of objects")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise DryRunLoadError(f"{source} row {index} must be a JSON object")
        rows.append(dict(row))
    return rows


def _load_jsonl_rows(path: Path, *, source: str) -> list[dict[str, Any]]:
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


def _rows_from_wrapped_json(
    payload: dict[str, Any],
    *,
    keys: tuple[str, ...],
    source: str,
) -> list[dict[str, Any]]:
    for key in keys:
        if key in payload:
            return _ensure_object_rows(payload[key], source=f"{source}.{key}")
    raise DryRunLoadError(f"{source} must include one of: {', '.join(keys)}")


def _change_proposals_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return _ensure_object_rows(payload, source="json")
    if isinstance(payload, dict):
        return _rows_from_wrapped_json(
            payload,
            keys=CHANGE_PROPOSAL_KEYS,
            source="json",
        )
    raise DryRunLoadError("change proposal json must be a list or object")


def load_change_proposals_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load exact change proposals from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _change_proposals_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_rows(artifact_path, source="change proposal jsonl")
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported change proposal extension: {suffix}")


def _proposal_result_from_json(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"change_proposals": _ensure_object_rows(payload, source="json")}
    if not isinstance(payload, dict):
        raise DryRunLoadError("proposal result json must be an object or list")
    if isinstance(payload.get("proposal_result"), dict):
        return deepcopy(payload)
    if isinstance(payload.get("change_proposals_by_type"), dict):
        return deepcopy(payload)
    if any(key in payload for key in PROPOSAL_RESULT_ROW_KEYS):
        return {
            "change_proposals": _rows_from_wrapped_json(
                payload,
                keys=PROPOSAL_RESULT_ROW_KEYS,
                source="json",
            )
        }
    raise DryRunLoadError(
        "proposal result json must include proposal_result, "
        "change_proposals, change_proposals_by_type, rows, or items"
    )


def load_proposal_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load a Phase 42 proposal-result-like artifact from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _proposal_result_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return {
            "change_proposals": _load_jsonl_rows(
                artifact_path,
                source="proposal result jsonl",
            )
        }
    if suffix == ".csv":
        return {"change_proposals": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported proposal result extension: {suffix}")


def load_context_from_path(path: str | Path) -> dict[str, Any]:
    """Load a context artifact from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        payload = _read_json(artifact_path)
        if not isinstance(payload, dict):
            raise DryRunLoadError("context json must be an object")
        return deepcopy(payload)
    if suffix == ".jsonl":
        return {
            "rows": _load_jsonl_rows(
                artifact_path,
                source="context jsonl",
            )
        }
    if suffix == ".csv":
        return {"rows": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported context extension: {suffix}")


def _dry_run_key(request_result: dict[str, Any]) -> str:
    summary = request_result.get("request_packet_summary", {})
    return "|".join(
        (
            f"phase={PHASE}",
            f"request_phase={request_result.get('phase', '')}",
            f"proposals={int(request_result.get('change_proposal_count', 0))}",
            f"valid={int(request_result.get('valid_change_proposal_count', 0))}",
            f"invalid={int(request_result.get('invalid_change_proposal_count', 0))}",
            f"included={int(summary.get('included_change_proposal_count', 0))}",
            f"blocked={bool(summary.get('request_blocked'))}",
        )
    )


def build_dry_run_payload(
    change_proposals: list[dict[str, Any]] | None = None,
    proposal_result: dict[str, Any] | None = None,
    resume_context: dict[str, Any] | None = None,
    jd_context: dict[str, Any] | None = None,
    tailoring_context: dict[str, Any] | None = None,
    request_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 43B request-packet dry-run payload."""

    proposals = deepcopy(change_proposals) if isinstance(change_proposals, list) else None
    result = deepcopy(proposal_result) if isinstance(proposal_result, dict) else None
    resume = deepcopy(resume_context) if isinstance(resume_context, dict) else None
    jd = deepcopy(jd_context) if isinstance(jd_context, dict) else None
    tailoring = deepcopy(tailoring_context) if isinstance(tailoring_context, dict) else None
    policy = deepcopy(request_policy) if isinstance(request_policy, dict) else {}
    request_result = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        change_proposals=proposals,
        proposal_result=result,
        resume_context=resume,
        jd_context=jd,
        tailoring_context=tailoring,
        request_policy=policy,
    )
    request_packet = deepcopy(request_result.get("request_packet", {}))
    request_messages = deepcopy(request_result.get("request_messages", []))
    request_schema = deepcopy(request_result.get("request_schema", {}))
    request_summary = deepcopy(request_result.get("request_packet_summary", {}))
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_llm_request_packet_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "llm_request_packet_only": True,
        "provider_request_packet_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "manual_trigger_required": True,
        "change_proposals_present": isinstance(change_proposals, list)
        and len(change_proposals) > 0,
        "proposal_result_present": isinstance(proposal_result, dict),
        "resume_context_present": isinstance(resume_context, dict),
        "jd_context_present": isinstance(jd_context, dict),
        "tailoring_context_present": isinstance(tailoring_context, dict),
        "request_policy": deepcopy(request_result.get("request_policy", policy)),
        "request_result": deepcopy(request_result),
        "request_packet": request_packet,
        "request_messages": request_messages,
        "request_schema": request_schema,
        "request_packet_summary": request_summary,
        "dry_run_summary": {
            "request_blocked": bool(request_summary.get("request_blocked")),
            "included_change_proposal_count": int(
                request_summary.get("included_change_proposal_count", 0)
            ),
            "excluded_change_proposal_count": int(
                request_summary.get("excluded_change_proposal_count", 0)
            ),
            "invalid_change_proposal_count": int(
                request_summary.get("invalid_change_proposal_count", 0)
            ),
            "provider_dispatch_prepared_not_executed": True,
            "llm_call_performed": False,
            "provider_call_performed": False,
            "network_call_performed": False,
        },
        "dry_run_key": _dry_run_key(request_result),
        "llm_request_packet_created": True,
        "provider_dispatch_ready": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _request_policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    for key in (
        "max_proposals_per_request",
        "response_format",
        "temperature",
        "max_output_tokens",
    ):
        value = getattr(args, key)
        if value is not None:
            policy[key] = value
    if args.include_full_resume_context:
        policy["include_full_resume_context"] = True
    if args.include_full_jd_context:
        policy["include_full_jd_context"] = True
    if args.exclude_tailoring_context:
        policy["include_tailoring_context"] = False
    policy["require_manual_trigger"] = True
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build default-off exact resume change-set LLM request packets.",
    )
    parser.add_argument("--input", required=True, help="Change proposals input file")
    parser.add_argument("--proposal-result", help="Optional Phase 42 proposal result file")
    parser.add_argument("--resume-context", help="Optional resume context file")
    parser.add_argument("--jd-context", help="Optional JD context file")
    parser.add_argument("--tailoring-context", help="Optional tailoring context file")
    parser.add_argument("--max-proposals-per-request", type=int)
    parser.add_argument("--include-full-resume-context", action="store_true")
    parser.add_argument("--include-full-jd-context", action="store_true")
    parser.add_argument("--exclude-tailoring-context", action="store_true")
    parser.add_argument("--response-format")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--max-output-tokens", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 43B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        change_proposals = load_change_proposals_from_path(args.input)
        proposal_result = (
            load_proposal_result_from_path(args.proposal_result)
            if args.proposal_result
            else None
        )
        resume_context = (
            load_context_from_path(args.resume_context)
            if args.resume_context
            else None
        )
        jd_context = load_context_from_path(args.jd_context) if args.jd_context else None
        tailoring_context = (
            load_context_from_path(args.tailoring_context)
            if args.tailoring_context
            else None
        )
        payload = build_dry_run_payload(
            change_proposals=change_proposals,
            proposal_result=proposal_result,
            resume_context=resume_context,
            jd_context=jd_context,
            tailoring_context=tailoring_context,
            request_policy=_request_policy_from_args(args),
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
