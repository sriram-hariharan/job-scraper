from __future__ import annotations

from copy import deepcopy
import csv
import json
from pathlib import Path

import pytest

from src.agents.evidence_chain_shadow_adapter import (
    adapt_completed_planning_artifacts,
)


def _artifacts():
    corpus = [
        {"doc_id": "job-0", "title": "Other", "company": "Elsewhere"},
        {
            "doc_id": "job-1",
            "title": "ML Engineer",
            "company": "Acme",
            "description": "Bounded fixture description",
            "ai_fit_score": 0.8,
        },
    ]
    best = [{"job_doc_id": "job-1", "winner_resume": "resume-a"}]
    queue = [
        {
            "job_doc_id": "job-1",
            "winner_resume": "resume-a",
            "resolved_resume": "resume-b",
            "action": "TAILOR_THEN_APPLY",
        }
    ]
    manifest = [
        {
            "job_doc_id": "job-1",
            "winner_resume": "resume-a",
            "packet_resume": "resume-b",
            "packet_resume_source": "llm_adjudication_generated",
        }
    ]
    evidence = {
        "resume-b": [
            {
                "resume_id": "resume-b",
                "skills": ["python"],
                "bullets": ["Built systems"],
            }
        ]
    }
    return corpus, best, queue, manifest, evidence


def _adapt(**overrides):
    corpus, best, queue, manifest, evidence = _artifacts()
    kwargs = {
        "owner_id": "owner-1",
        "pipeline_run_id": "run-1",
        "context_id": "planning-1",
        "job_id": "job-1",
        "resume_evidence_by_id": evidence,
        "include_trace_payload": False,
        "job_corpus_rows": corpus,
        "best_resume_rows": best,
        "execution_queue_rows": queue,
        "packet_manifest_rows": manifest,
    }
    kwargs.update(overrides)
    return adapt_completed_planning_artifacts(**kwargs)


def test_valid_mapping_is_deterministic_and_does_not_mutate_inputs():
    corpus, best, queue, manifest, evidence = _artifacts()
    inputs = deepcopy((corpus, best, queue, manifest, evidence))
    kwargs = {
        "owner_id": "owner-1",
        "pipeline_run_id": "run-1",
        "context_id": "planning-1",
        "job_id": "job-1",
        "resume_evidence_by_id": evidence,
        "include_trace_payload": True,
        "job_corpus_rows": corpus,
        "best_resume_rows": best,
        "execution_queue_rows": queue,
        "packet_manifest_rows": manifest,
    }

    first = adapt_completed_planning_artifacts(**kwargs)
    second = adapt_completed_planning_artifacts(**kwargs)

    assert first == second
    assert first["status"] == "success"
    graph_input = first["graph_input"]
    assert graph_input["job_id"] == "job-1"
    assert graph_input["job_index"] == 1
    assert graph_input["selected_resume_id"] == "resume-b"
    assert graph_input["graph_invocation_id"].startswith(
        "langgraph-evidence-chain-invocation:"
    )
    state = graph_input["initial_state"]
    assert state["owner_user_id"] == "owner-1"
    assert state["pipeline_run_id"] == "run-1"
    assert state["context_id"] == "planning-1"
    assert state["artifacts"] == {}
    assert state["ordered_node_keys"] == []
    assert state["node_statuses"] == []
    assert state["warnings"] == []
    assert (corpus, best, queue, manifest, evidence) == inputs


@pytest.mark.parametrize(
    ("override", "value", "failure"),
    [
        ("owner_id", "", "owner_identity_missing"),
        ("pipeline_run_id", "", "pipeline_identity_missing"),
        ("context_id", "", "context_identity_missing"),
        ("job_id", "", "job_not_found"),
        ("job_id", "absent", "job_not_found"),
    ],
)
def test_identity_rejections(override, value, failure):
    assert _adapt(**{override: value})["failure_code"] == failure


def test_duplicate_corpus_identity_is_rejected():
    corpus, *_ = _artifacts()
    assert _adapt(job_corpus_rows=[*corpus, deepcopy(corpus[-1])])[
        "failure_code"
    ] == "duplicate_job_identity"


def test_selected_resume_missing_and_conflict_are_rejected():
    assert _adapt(packet_manifest_rows=[{"job_doc_id": "job-1"}])[
        "failure_code"
    ] == "selected_resume_missing"
    assert _adapt(
        packet_manifest_rows=[
            {"job_doc_id": "job-1", "packet_resume": "resume-a"},
            {"job_doc_id": "job-1", "packet_resume": "resume-b"},
        ]
    )["failure_code"] == "selected_resume_conflict"


def test_missing_or_wrong_resume_evidence_is_rejected():
    assert _adapt(resume_evidence_by_id={})["failure_code"] == "resume_evidence_missing"
    assert _adapt(
        resume_evidence_by_id={"resume-b": [{"resume_id": "resume-a"}]}
    )["failure_code"] == "resume_evidence_missing"


def test_inconsistent_artifact_identity_is_rejected():
    assert _adapt(execution_queue_rows=[{"job_doc_id": "other"}])[
        "failure_code"
    ] == "job_not_found"


def test_malformed_loaded_rows_are_rejected():
    assert _adapt(best_resume_rows=[])["failure_code"] == "artifact_malformed"
    corpus, best, queue, manifest, evidence = _artifacts()
    assert adapt_completed_planning_artifacts(
        owner_id="owner",
        pipeline_run_id="run",
        context_id="context",
        job_id="job-1",
        resume_evidence_by_id=evidence,
        include_trace_payload=False,
        job_corpus_rows=corpus,
        best_resume_rows=best,
        execution_queue_rows=queue,
        packet_manifest_rows=None,
    )["failure_code"] == "artifact_missing"


def test_unsupported_or_inconsistent_artifact_schema_version_is_rejected():
    corpus, *_ = _artifacts()
    corpus = [{**row, "schema_version": "corpus-v0"} for row in corpus]
    assert _adapt(
        job_corpus_rows=corpus,
        expected_artifact_schema_versions={"job_corpus": "corpus-v1"},
    )["failure_code"] == "artifact_malformed"


def _write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_read_only_path_loading_and_malformed_jsonl(tmp_path):
    corpus, best, queue, manifest, evidence = _artifacts()
    corpus_path = tmp_path / "corpus.jsonl"
    corpus_path.write_text(
        "".join(json.dumps(row) + "\n" for row in corpus), encoding="utf-8"
    )
    paths = {}
    for name, rows in (("best", best), ("queue", queue), ("manifest", manifest)):
        paths[name] = tmp_path / f"{name}.csv"
        _write_csv(paths[name], rows)
    before = {path: path.read_bytes() for path in tmp_path.iterdir()}
    result = adapt_completed_planning_artifacts(
        owner_id="owner-1",
        pipeline_run_id="run-1",
        context_id="planning-1",
        job_id="job-1",
        resume_evidence_by_id=evidence,
        include_trace_payload=False,
        job_corpus_path=corpus_path,
        best_resume_path=paths["best"],
        execution_queue_path=paths["queue"],
        packet_manifest_path=paths["manifest"],
    )
    assert result["status"] == "success"
    assert {path: path.read_bytes() for path in tmp_path.iterdir()} == before

    corpus_path.write_text("{not-json}\n", encoding="utf-8")
    assert adapt_completed_planning_artifacts(
        owner_id="owner-1",
        pipeline_run_id="run-1",
        context_id="planning-1",
        job_id="job-1",
        resume_evidence_by_id=evidence,
        include_trace_payload=False,
        job_corpus_path=corpus_path,
        best_resume_path=paths["best"],
        execution_queue_path=paths["queue"],
        packet_manifest_path=paths["manifest"],
    )["failure_code"] == "artifact_malformed"


def test_graph_input_invalid_is_bounded():
    corpus, *_ = _artifacts()
    corpus[-1]["title"] = ""
    result = _adapt(job_corpus_rows=corpus)
    assert result == {
        "status": "failed",
        "adapter_version": "evidence-chain-shadow-input-adapter-v1",
        "failure_code": "graph_input_invalid",
        "job_id": "job-1",
    }
