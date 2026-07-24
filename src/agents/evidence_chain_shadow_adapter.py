"""Deterministic read-only adaptation of completed planning artifacts.

This module deliberately owns no runtime configuration, persistence, graph
execution, resume loading, or production-stage recomputation.
"""

from __future__ import annotations

import csv
from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, TypedDict


SHADOW_INPUT_ADAPTER_VERSION = "evidence-chain-shadow-input-adapter-v1"
_ARTIFACT_NAMES = (
    "job_corpus",
    "best_resume",
    "execution_queue",
    "packet_manifest",
)


class ShadowGraphInputRecord(TypedDict):
    adapter_version: str
    job_id: str
    job_index: int
    selected_resume_id: str
    graph_invocation_id: str
    initial_state: Dict[str, Any]


class ShadowAdapterResult(TypedDict, total=False):
    status: str
    adapter_version: str
    failure_code: str
    job_id: str
    graph_input: ShadowGraphInputRecord


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _failure(code: str, *, job_id: str = "") -> ShadowAdapterResult:
    result: ShadowAdapterResult = {
        "status": "failed",
        "adapter_version": SHADOW_INPUT_ADAPTER_VERSION,
        "failure_code": code,
    }
    if _clean_text(job_id):
        result["job_id"] = _clean_text(job_id)
    return result


def _identity(row: Mapping[str, Any]) -> str:
    return _clean_text(
        row.get("doc_id") or row.get("job_doc_id") or row.get("job_id")
    )


def _resume_identity(row: Mapping[str, Any]) -> str:
    return _clean_text(row.get("resume_id") or row.get("resume_name"))


def _load_jsonl(path: Path) -> tuple[List[Dict[str, Any]] | None, str]:
    if not path.is_file():
        return None, "artifact_missing"
    rows: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    return None, "artifact_malformed"
                rows.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "artifact_malformed"
    return (rows, "") if rows else (None, "artifact_malformed")


def _load_csv(path: Path) -> tuple[List[Dict[str, Any]] | None, str]:
    if not path.is_file():
        return None, "artifact_missing"
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return None, "artifact_malformed"
            rows = [dict(row) for row in reader]
    except (OSError, UnicodeError, csv.Error):
        return None, "artifact_malformed"
    return (rows, "") if rows else (None, "artifact_malformed")


def _artifact_rows(
    *,
    name: str,
    supplied_rows: Sequence[Mapping[str, Any]] | None,
    path: str | Path | None,
) -> tuple[List[Dict[str, Any]] | None, str]:
    if supplied_rows is not None:
        if not supplied_rows or any(not isinstance(row, Mapping) for row in supplied_rows):
            return None, "artifact_malformed"
        return deepcopy([dict(row) for row in supplied_rows]), ""
    if path is None or not _clean_text(path):
        return None, "artifact_missing"
    resolved = Path(path)
    return _load_jsonl(resolved) if name == "job_corpus" else _load_csv(resolved)


def _rows_for_job(
    rows: Sequence[Mapping[str, Any]], job_id: str
) -> List[Dict[str, Any]]:
    return [dict(row) for row in rows if _identity(row) == job_id]


def adapt_completed_planning_artifacts(
    *,
    owner_id: str,
    pipeline_run_id: str,
    context_id: str,
    job_id: str,
    resume_evidence_by_id: Mapping[str, Sequence[Mapping[str, Any]]],
    include_trace_payload: bool,
    job_corpus_rows: Sequence[Mapping[str, Any]] | None = None,
    best_resume_rows: Sequence[Mapping[str, Any]] | None = None,
    execution_queue_rows: Sequence[Mapping[str, Any]] | None = None,
    packet_manifest_rows: Sequence[Mapping[str, Any]] | None = None,
    job_corpus_path: str | Path | None = None,
    best_resume_path: str | Path | None = None,
    execution_queue_path: str | Path | None = None,
    packet_manifest_path: str | Path | None = None,
    expected_artifact_schema_versions: Mapping[str, str] | None = None,
) -> ShadowAdapterResult:
    """Build one validated initial graph input without executing the graph."""

    normalized_job_id = _clean_text(job_id)
    for value, code in (
        (owner_id, "owner_identity_missing"),
        (pipeline_run_id, "pipeline_identity_missing"),
        (context_id, "context_identity_missing"),
    ):
        if not _clean_text(value):
            return _failure(code, job_id=normalized_job_id)
    if not normalized_job_id:
        return _failure("job_not_found")

    supplied = {
        "job_corpus": (job_corpus_rows, job_corpus_path),
        "best_resume": (best_resume_rows, best_resume_path),
        "execution_queue": (execution_queue_rows, execution_queue_path),
        "packet_manifest": (packet_manifest_rows, packet_manifest_path),
    }
    artifacts: Dict[str, List[Dict[str, Any]]] = {}
    for name in _ARTIFACT_NAMES:
        rows, failure_code = _artifact_rows(
            name=name,
            supplied_rows=supplied[name][0],
            path=supplied[name][1],
        )
        if failure_code:
            return _failure(failure_code, job_id=normalized_job_id)
        artifacts[name] = rows or []
        expected_version = _clean_text(
            (expected_artifact_schema_versions or {}).get(name)
        )
        observed_versions = {
            _clean_text(row.get("schema_version"))
            for row in artifacts[name]
            if _clean_text(row.get("schema_version"))
        }
        if (
            len(observed_versions) > 1
            or (expected_version and observed_versions != {expected_version})
        ):
            return _failure("artifact_malformed", job_id=normalized_job_id)

    corpus_identities = [_identity(row) for row in artifacts["job_corpus"]]
    if any(not identity for identity in corpus_identities):
        return _failure("artifact_malformed", job_id=normalized_job_id)
    if len(corpus_identities) != len(set(corpus_identities)):
        return _failure("duplicate_job_identity", job_id=normalized_job_id)
    if normalized_job_id not in corpus_identities:
        return _failure("job_not_found", job_id=normalized_job_id)
    job_index = corpus_identities.index(normalized_job_id)
    if job_index < 0:
        return _failure("job_index_unresolved", job_id=normalized_job_id)
    job = artifacts["job_corpus"][job_index]

    matching: Dict[str, List[Dict[str, Any]]] = {}
    for name in ("best_resume", "execution_queue", "packet_manifest"):
        matching[name] = _rows_for_job(artifacts[name], normalized_job_id)
        if not matching[name]:
            return _failure("job_not_found", job_id=normalized_job_id)
        if name != "packet_manifest" and len(matching[name]) != 1:
            return _failure("duplicate_job_identity", job_id=normalized_job_id)

    selected = {
        _clean_text(row.get("packet_resume"))
        for row in matching["packet_manifest"]
        if _clean_text(row.get("packet_resume"))
    }
    if len(selected) > 1:
        return _failure("selected_resume_conflict", job_id=normalized_job_id)
    if not selected:
        return _failure("selected_resume_missing", job_id=normalized_job_id)
    if len(matching["packet_manifest"]) > 1:
        return _failure("duplicate_job_identity", job_id=normalized_job_id)
    selected_resume_id = next(iter(selected))

    raw_evidence = resume_evidence_by_id.get(selected_resume_id)
    if not raw_evidence:
        return _failure("resume_evidence_missing", job_id=normalized_job_id)
    resume_rows = deepcopy(
        [dict(row) for row in raw_evidence if isinstance(row, Mapping)]
    )
    if len(resume_rows) != len(raw_evidence) or any(
        _resume_identity(row) != selected_resume_id for row in resume_rows
    ):
        return _failure("resume_evidence_missing", job_id=normalized_job_id)

    title = _clean_text(job.get("title") or job.get("job_title"))
    company = _clean_text(job.get("company") or job.get("job_company"))
    if not title or not company:
        return _failure("graph_input_invalid", job_id=normalized_job_id)

    from src.agents.evidence_chain_langgraph_harness import (
        _build_checkpoint_identity,
        _build_initial_graph_state,
    )

    initial_state = _build_initial_graph_state(
        job=job,
        job_index=job_index,
        job_identity={
            "job_id": normalized_job_id,
            "title": title,
            "company": company,
        },
        resume_rows=resume_rows,
        selected_resume_id=selected_resume_id,
        pipeline_run_id=_clean_text(pipeline_run_id),
        owner_user_id=_clean_text(owner_id),
        context_id=_clean_text(context_id),
        include_trace_payload=bool(include_trace_payload),
    )
    try:
        graph_identity = _build_checkpoint_identity(initial_state)
    except (TypeError, ValueError):
        return _failure("graph_input_invalid", job_id=normalized_job_id)

    return {
        "status": "success",
        "adapter_version": SHADOW_INPUT_ADAPTER_VERSION,
        "job_id": normalized_job_id,
        "graph_input": {
            "adapter_version": SHADOW_INPUT_ADAPTER_VERSION,
            "job_id": normalized_job_id,
            "job_index": job_index,
            "selected_resume_id": selected_resume_id,
            "graph_invocation_id": graph_identity.graph_invocation_id,
            "initial_state": initial_state,
        },
    }
