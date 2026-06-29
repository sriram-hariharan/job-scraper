"""Default-off dry-run command for exact resume change-set proposals."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.exact_resume_change_set_proposal_builder_default_off import (
    build_exact_resume_change_set_proposal_builder_default_off,
)


PHASE = "42B"
REVIEW_QUEUE_KEYS = ("review_queue", "rows", "items", "queue_items")
QUEUE_RESULT_ROW_KEYS = ("review_queue", "rows", "items")
FALSE_ACTION_KEYS = (
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
    """Raised when exact proposal dry-run input cannot be loaded."""


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


def _ensure_row_list(value: Any, *, source: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise DryRunLoadError(f"{source} must contain a list of queue item objects")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise DryRunLoadError(f"{source} row {index} must be a JSON object")
        rows.append(dict(item))
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
            return _ensure_row_list(payload[key], source=f"{source}.{key}")
    raise DryRunLoadError(f"{source} must include one of: {', '.join(keys)}")


def _review_queue_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return _ensure_row_list(payload, source="json")
    if isinstance(payload, dict):
        return _rows_from_wrapped_json(
            payload,
            keys=REVIEW_QUEUE_KEYS,
            source="json",
        )
    raise DryRunLoadError("review queue json must be a row list or object")


def load_review_queue_from_path(path: str | Path) -> list[dict[str, Any]]:
    """Load review queue items from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _review_queue_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return _load_jsonl_rows(artifact_path, source="review queue jsonl")
    if suffix == ".csv":
        return _load_csv_rows(artifact_path)
    raise DryRunLoadError(f"unsupported review queue extension: {suffix}")


def _queue_result_from_json(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"review_queue": _ensure_row_list(payload, source="json")}
    if not isinstance(payload, dict):
        raise DryRunLoadError("queue result json must be an object or row list")
    if isinstance(payload.get("queue_result"), dict):
        return deepcopy(payload)
    if isinstance(payload.get("review_queue_by_priority"), dict):
        return deepcopy(payload)
    if any(key in payload for key in QUEUE_RESULT_ROW_KEYS):
        return {
            "review_queue": _rows_from_wrapped_json(
                payload,
                keys=QUEUE_RESULT_ROW_KEYS,
                source="json",
            )
        }
    raise DryRunLoadError(
        "queue result json must include queue_result, "
        "review_queue, review_queue_by_priority, rows, or items"
    )


def load_queue_result_from_path(path: str | Path) -> dict[str, Any]:
    """Load a Phase 41 queue-result-like artifact from JSON, JSONL, or CSV."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if suffix == ".json":
        return _queue_result_from_json(_read_json(artifact_path))
    if suffix == ".jsonl":
        return {
            "review_queue": _load_jsonl_rows(
                artifact_path,
                source="queue result jsonl",
            )
        }
    if suffix == ".csv":
        return {"review_queue": _load_csv_rows(artifact_path)}
    raise DryRunLoadError(f"unsupported queue result extension: {suffix}")


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


def _dry_run_key(proposal_result: dict[str, Any]) -> str:
    proposals = proposal_result.get("change_proposals", [])
    summary = proposal_result.get("change_set_summary", {})
    return "|".join(
        (
            f"phase={PHASE}",
            f"queue={int(proposal_result.get('review_queue_count', 0))}",
            f"valid={int(proposal_result.get('valid_review_queue_item_count', 0))}",
            f"invalid={int(proposal_result.get('invalid_review_queue_item_count', 0))}",
            f"proposals={len(proposals) if isinstance(proposals, list) else 0}",
            f"blocked={bool(summary.get('proposal_blocked'))}",
        )
    )


def build_dry_run_payload(
    review_queue: list[dict[str, Any]] | None = None,
    queue_result: dict[str, Any] | None = None,
    resume_context: dict[str, Any] | None = None,
    jd_context: dict[str, Any] | None = None,
    tailoring_context: dict[str, Any] | None = None,
    proposal_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the read-only Phase 42B exact proposal dry-run payload."""

    queue = deepcopy(review_queue) if isinstance(review_queue, list) else None
    result = deepcopy(queue_result) if isinstance(queue_result, dict) else None
    resume = deepcopy(resume_context) if isinstance(resume_context, dict) else None
    jd = deepcopy(jd_context) if isinstance(jd_context, dict) else None
    tailoring = deepcopy(tailoring_context) if isinstance(tailoring_context, dict) else None
    policy = deepcopy(proposal_policy) if isinstance(proposal_policy, dict) else {}
    proposal_result = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=queue,
        queue_result=result,
        resume_context=resume,
        jd_context=jd,
        tailoring_context=tailoring,
        proposal_policy=policy,
    )
    change_proposals = deepcopy(proposal_result.get("change_proposals", []))
    grouped = deepcopy(proposal_result.get("change_proposals_by_type", {}))
    summary = deepcopy(proposal_result.get("change_set_summary", {}))
    payload = {
        "phase": PHASE,
        "default_off": True,
        "exact_resume_change_set_proposal_builder_dry_run": True,
        "dry_run_command_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "review_queue_present": isinstance(review_queue, list) and len(review_queue) > 0,
        "queue_result_present": isinstance(queue_result, dict),
        "resume_context_present": isinstance(resume_context, dict),
        "jd_context_present": isinstance(jd_context, dict),
        "tailoring_context_present": isinstance(tailoring_context, dict),
        "proposal_policy": deepcopy(proposal_result.get("proposal_policy", policy)),
        "proposal_result": deepcopy(proposal_result),
        "change_proposals": change_proposals,
        "change_proposals_by_type": grouped,
        "change_set_summary": summary,
        "dry_run_summary": {
            "change_proposal_count": len(change_proposals),
            "proposal_missing_inputs": list(proposal_result.get("missing_inputs", [])),
            "full_resume_produced": False,
            "real_tailoring_output_created": False,
        },
        "dry_run_key": _dry_run_key(proposal_result),
        "resume_change_proposals_created": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def _proposal_policy_from_args(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    for key in (
        "max_change_proposals",
        "max_changes_per_queue_item",
        "minimum_evidence_terms",
    ):
        value = getattr(args, key)
        if value is not None:
            policy[key] = value
    if args.disable_summary_changes:
        policy["allow_summary_changes"] = False
    if args.disable_skill_changes:
        policy["allow_skill_changes"] = False
    if args.disable_bullet_changes:
        policy["allow_bullet_changes"] = False
    if args.disable_project_changes:
        policy["allow_project_changes"] = False
    if args.allow_without_source_evidence:
        policy["require_source_evidence"] = False
    if args.exclude_before_after_text:
        policy["include_before_after_text"] = False
    return policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build default-off exact resume change-set proposals.",
    )
    parser.add_argument("--input", required=True, help="Review queue input file")
    parser.add_argument("--queue-result", help="Optional Phase 41 queue result file")
    parser.add_argument("--resume-context", help="Optional resume context file")
    parser.add_argument("--jd-context", help="Optional JD context file")
    parser.add_argument("--tailoring-context", help="Optional tailoring context file")
    parser.add_argument("--max-change-proposals", type=int)
    parser.add_argument("--max-changes-per-queue-item", type=int)
    parser.add_argument("--minimum-evidence-terms", type=int)
    parser.add_argument("--disable-summary-changes", action="store_true")
    parser.add_argument("--disable-skill-changes", action="store_true")
    parser.add_argument("--disable-bullet-changes", action="store_true")
    parser.add_argument("--disable-project-changes", action="store_true")
    parser.add_argument("--allow-without-source-evidence", action="store_true")
    parser.add_argument("--exclude-before-after-text", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 42B dry-run command."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
        review_queue = load_review_queue_from_path(args.input)
        queue_result = (
            load_queue_result_from_path(args.queue_result)
            if args.queue_result
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
            review_queue=review_queue,
            queue_result=queue_result,
            resume_context=resume_context,
            jd_context=jd_context,
            tailoring_context=tailoring_context,
            proposal_policy=_proposal_policy_from_args(args),
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
