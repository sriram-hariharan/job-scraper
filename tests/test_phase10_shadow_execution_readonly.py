from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from langgraph.checkpoint.memory import InMemorySaver

from src.agents.evidence_chain_shadow_execution import execute_readonly_shadow


EXPECTED_NODES = [
    "jd_intelligence",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]


def _inputs():
    corpus = [
        {
            "doc_id": "job-shadow-1",
            "title": "AI Platform Engineer",
            "company": "Synthetic Co",
            "intelligence": {
                "skills": {
                    "required": ["Python", "SQL"],
                    "preferred": ["RAG"],
                    "all": ["Python", "SQL", "RAG"],
                },
                "visa_sponsorship": "unknown",
            },
            "ai_fit_score": 8,
            "priority_score": 12.5,
        }
    ]
    best = [{"job_doc_id": "job-shadow-1", "winner_resume": "resume-shadow"}]
    queue = [
        {
            "job_doc_id": "job-shadow-1",
            "winner_resume": "resume-shadow",
            "resolved_resume": "resume-shadow",
            "action": "TAILOR_THEN_APPLY",
        }
    ]
    manifest = [
        {
            "job_doc_id": "job-shadow-1",
            "packet_resume": "resume-shadow",
            "packet_resume_source": "deterministic_winner",
        }
    ]
    evidence = {
        "resume-shadow": [
            {
                "resume_id": "resume-shadow",
                "skills": ["Python", "SQL", "RAG"],
                "raw_text": "Synthetic evidence only.",
            }
        ]
    }
    comparisons = {
        "job-shadow-1": [
            {"field": "pipeline_run_id", "mode": "exact",
             "authoritative_value": "run-shadow"},
            {"field": "job_id", "mode": "exact",
             "authoritative_value": "job-shadow-1"},
            {"field": "selected_resume_id", "mode": "exact",
             "authoritative_value": "resume-shadow"},
            {"field": "completed_node_order", "mode": "ordered",
             "authoritative_value": EXPECTED_NODES},
            {"field": "pending_node", "mode": "exact",
             "authoritative_value": "finalize"},
        ]
    }
    return corpus, best, queue, manifest, evidence, comparisons


def _execute(**overrides):
    corpus, best, queue, manifest, evidence, comparisons = _inputs()
    kwargs = {
        "job_ids": ["job-shadow-1"],
        "owner_id": "owner-shadow",
        "pipeline_run_id": "run-shadow",
        "context_id": "context-shadow",
        "resume_evidence_by_id": evidence,
        "authoritative_comparisons_by_job": comparisons,
        "include_trace_payload": True,
        "job_corpus_rows": corpus,
        "best_resume_rows": best,
        "execution_queue_rows": queue,
        "packet_manifest_rows": manifest,
    }
    kwargs.update(overrides)
    return execute_readonly_shadow(**kwargs)


def test_real_graph_stops_after_six_nodes_with_inmemory_saver_only(monkeypatch):
    from src.agents import evidence_chain_shadow_execution as execution

    original = execution._start_readonly_pause
    observed = {}

    def inspect(initial_state):
        session, result = original(initial_state)
        observed["saver"] = session._checkpointer
        observed["graph"] = session._compiled_graph
        return session, result

    monkeypatch.setattr(execution, "_start_readonly_pause", inspect)
    payload = _execute()
    result = payload["results"][0]
    facts = result["shadow_facts"]

    assert isinstance(observed["saver"], InMemorySaver)
    assert result["status"] == "parity_completed"
    assert result["execution_status"] == "completed_at_operator_review"
    assert facts["completed_node_order"] == EXPECTED_NODES
    assert list(facts["node_statuses"]) == EXPECTED_NODES
    assert all(status == "completed" for status in facts["node_statuses"].values())
    assert facts["pending_node"] == "finalize"
    assert facts["finalization_executed"] is False
    assert facts["final_bundle_present"] is False
    assert facts["final_trace_present"] is False
    assert result["parity"]["overall_classification"] == "match"
    incomparable = [
        row for row in result["parity"]["field_results"]
        if row["field"] == "human_finalization_outcome"
    ]
    assert incomparable[0]["status"] == "intentionally_incomparable"


def test_repeated_execution_has_deterministic_facts_and_parity():
    first, second = _execute(), _execute()
    first_result, second_result = first["results"][0], second["results"][0]
    first_facts = deepcopy(first_result["shadow_facts"])
    second_facts = deepcopy(second_result["shadow_facts"])
    first_facts.pop("graph_latency_ms")
    second_facts.pop("graph_latency_ms")
    assert first_facts == second_facts
    assert first_result["parity"] == second_result["parity"]
    assert first_result["graph_invocation_id"] == second_result["graph_invocation_id"]


def test_parity_owner_receives_only_bounded_facts(monkeypatch):
    from src.agents import evidence_chain_shadow_execution as execution

    captured = {}
    original = execution.compare_shadow_parity

    def inspect(**kwargs):
        captured.update(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(execution, "compare_shadow_parity", inspect)
    payload = _execute()
    assert payload["results"][0]["status"] == "parity_completed"
    rendered = repr(captured).lower()
    assert "synthetic evidence only" not in rendered
    assert "raw_text" not in rendered
    assert "checkpoint" not in rendered
    result_fields = payload["results"][0]["parity"]["field_results"]
    assert [field["field"] for field in result_fields] == sorted(
        field["field"] for field in result_fields
    )


def test_one_input_failure_is_isolated_from_completed_job():
    corpus, best, queue, manifest, evidence, comparisons = _inputs()
    payload = _execute(
        job_ids=["job-shadow-1", "job-missing"],
        authoritative_comparisons_by_job={**comparisons, "job-missing": []},
    )
    assert payload["results"][0]["status"] == "parity_completed"
    assert payload["results"][1] == {
        "job_id": "job-missing",
        "status": "input_rejected",
        "failure_code": "job_not_found",
    }


def test_malformed_state_and_unexpected_pending_node_fail_closed():
    def malformed(_initial_state):
        return SimpleNamespace(_paused_state={}), {
            "completed_node_keys": EXPECTED_NODES,
            "safe_next_node": "finalize",
        }

    def unexpected(_initial_state):
        state = {
            "ordered_node_keys": EXPECTED_NODES,
            "artifacts": {},
            "node_statuses": [],
        }
        return SimpleNamespace(_paused_state=state), {
            "completed_node_keys": EXPECTED_NODES,
            "safe_next_node": "resume_match",
        }

    assert _execute(_session_starter=malformed)["results"][0]["status"] == (
        "graph_output_malformed"
    )
    assert _execute(_session_starter=unexpected)["results"][0]["status"] == (
        "graph_output_malformed"
    )


def test_artifact_files_are_digest_checked_and_unchanged(tmp_path):
    import csv
    import json

    corpus, best, queue, manifest, evidence, comparisons = _inputs()
    corpus_path = tmp_path / "corpus.jsonl"
    corpus_path.write_text(json.dumps(corpus[0]) + "\n", encoding="utf-8")
    paths = {}
    for name, rows in (("best", best), ("queue", queue), ("manifest", manifest)):
        path = tmp_path / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        paths[name] = path
    before = {path: path.read_bytes() for path in tmp_path.iterdir()}
    payload = execute_readonly_shadow(
        job_ids=["job-shadow-1"],
        owner_id="owner-shadow",
        pipeline_run_id="run-shadow",
        context_id="context-shadow",
        resume_evidence_by_id=evidence,
        authoritative_comparisons_by_job=comparisons,
        include_trace_payload=False,
        job_corpus_path=corpus_path,
        best_resume_path=paths["best"],
        execution_queue_path=paths["queue"],
        packet_manifest_path=paths["manifest"],
    )
    assert payload["artifacts_unchanged"] is True
    assert {path: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_execution_module_has_no_production_or_durable_imports():
    source = (
        Path(__file__).resolve().parents[1]
        / "src/agents/evidence_chain_shadow_execution.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "durable_evidence_chain_resume_coordinator",
        "src.storage.durable_orchestration",
        "PostgresSaver",
        "DATABASE_URL",
        "runtime_status",
        "application_actions",
        "notification",
        "invoke(None",
        "Command(resume=",
    ):
        assert forbidden not in source
