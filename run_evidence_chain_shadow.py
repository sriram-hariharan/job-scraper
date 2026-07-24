"""Explicit command for process-local read-only evidence-chain shadow execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Dict, Mapping


MAX_INPUT_BYTES = 1_000_000
MAX_RESUMES = 50
MAX_EVIDENCE_ROWS_PER_RESUME = 20
_IDENTITY = re.compile(r"[A-Za-z0-9_.:@/-]{1,200}")


class CommandInputError(ValueError):
    pass


def _identity(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not _IDENTITY.fullmatch(text):
        raise CommandInputError(f"{field}_invalid")
    return text


def _load_json(path: str, label: str) -> Any:
    resolved = Path(path)
    if not resolved.is_file():
        raise CommandInputError(f"{label}_missing")
    try:
        if resolved.stat().st_size > MAX_INPUT_BYTES:
            raise CommandInputError(f"{label}_too_large")
        return json.loads(resolved.read_text(encoding="utf-8"))
    except CommandInputError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CommandInputError(f"{label}_malformed") from exc


def _resume_evidence(value: Any) -> Dict[str, list[Dict[str, Any]]]:
    if not isinstance(value, Mapping) or not isinstance(value.get("resumes"), list):
        raise CommandInputError("resume_evidence_malformed")
    entries = value["resumes"]
    if not entries or len(entries) > MAX_RESUMES:
        raise CommandInputError("resume_evidence_count_invalid")
    result: Dict[str, list[Dict[str, Any]]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise CommandInputError("resume_evidence_malformed")
        resume_id = _identity(entry.get("resume_id"), "resume_identity")
        if resume_id in result:
            raise CommandInputError("resume_identity_duplicate")
        rows = entry.get("evidence_rows")
        if (
            not isinstance(rows, list)
            or not rows
            or len(rows) > MAX_EVIDENCE_ROWS_PER_RESUME
            or any(not isinstance(row, Mapping) for row in rows)
        ):
            raise CommandInputError("resume_evidence_malformed")
        normalized = [dict(row) for row in rows]
        if any(
            str(row.get("resume_id") or row.get("resume_name") or "").strip()
            != resume_id
            for row in normalized
        ):
            raise CommandInputError("resume_evidence_identity_mismatch")
        result[resume_id] = normalized
    return result


def _authoritative_facts(value: Any) -> tuple[list[str], Dict[str, list[Dict[str, Any]]]]:
    if not isinstance(value, Mapping) or not isinstance(value.get("jobs"), list):
        raise CommandInputError("authoritative_facts_malformed")
    job_ids: list[str] = []
    comparisons: Dict[str, list[Dict[str, Any]]] = {}
    for entry in value["jobs"]:
        if not isinstance(entry, Mapping):
            raise CommandInputError("authoritative_facts_malformed")
        job_id = _identity(entry.get("job_id"), "job_identity")
        if job_id in comparisons:
            raise CommandInputError("job_identity_duplicate")
        fields = entry.get("comparisons", [])
        if not isinstance(fields, list) or any(
            not isinstance(field, Mapping) for field in fields
        ):
            raise CommandInputError("authoritative_comparisons_malformed")
        job_ids.append(job_id)
        comparisons[job_id] = [dict(field) for field in fields]
    if not job_ids:
        raise CommandInputError("authoritative_jobs_missing")
    return job_ids, comparisons


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run explicit read-only evidence shadow.")
    parser.add_argument("--execute-shadow", action="store_true")
    parser.add_argument("--job-corpus")
    parser.add_argument("--best-resume")
    parser.add_argument("--execution-queue")
    parser.add_argument("--packet-manifest")
    parser.add_argument("--resume-evidence")
    parser.add_argument("--authoritative-facts")
    parser.add_argument("--owner-id")
    parser.add_argument("--pipeline-run-id")
    parser.add_argument("--context-id")
    parser.add_argument("--include-trace-payload", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.execute_shadow:
        raise CommandInputError("execute_shadow_acknowledgement_required")
    required = (
        ("job_corpus", args.job_corpus),
        ("best_resume", args.best_resume),
        ("execution_queue", args.execution_queue),
        ("packet_manifest", args.packet_manifest),
        ("resume_evidence", args.resume_evidence),
        ("authoritative_facts", args.authoritative_facts),
        ("owner_identity", args.owner_id),
        ("pipeline_identity", args.pipeline_run_id),
        ("context_identity", args.context_id),
    )
    for label, value in required:
        if not str(value or "").strip():
            raise CommandInputError(f"{label}_missing")
    owner_id = _identity(args.owner_id, "owner_identity")
    pipeline_run_id = _identity(args.pipeline_run_id, "pipeline_identity")
    context_id = _identity(args.context_id, "context_identity")
    evidence = _resume_evidence(_load_json(args.resume_evidence, "resume_evidence"))
    job_ids, comparisons = _authoritative_facts(
        _load_json(args.authoritative_facts, "authoritative_facts")
    )

    from src.agents.evidence_chain_shadow_execution import execute_readonly_shadow

    result = execute_readonly_shadow(
        job_ids=job_ids,
        owner_id=owner_id,
        pipeline_run_id=pipeline_run_id,
        context_id=context_id,
        resume_evidence_by_id=evidence,
        authoritative_comparisons_by_job=comparisons,
        include_trace_payload=bool(args.include_trace_payload),
        job_corpus_path=args.job_corpus,
        best_resume_path=args.best_resume,
        execution_queue_path=args.execution_queue,
        packet_manifest_path=args.packet_manifest,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CommandInputError as exc:
        print(
            json.dumps(
                {"status": "command_input_rejected", "failure_code": str(exc)},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=__import__("sys").stderr,
        )
        raise SystemExit(2)
