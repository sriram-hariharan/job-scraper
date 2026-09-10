from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import types

from src.agents import final_scoring_authoritative_graph as graph_owner
from src.pipeline import application_scorer, collector


GRAPH_MODULE = "src.agents.final_scoring_authoritative_graph"
GATE = "APPLYLENS_AUTHORITATIVE_FINAL_SCORING_LANGGRAPH_ENABLED"


def _job(
    job_id: str,
    *,
    company: str,
    title: str,
    ai_relevance: float,
    skill_match: float,
    seniority_match: float,
    learning_opportunity: float,
) -> dict:
    return {
        "job_id": job_id,
        "company": company,
        "title": title,
        "posted_at": "",
        "ai_relevance": ai_relevance,
        "skill_match": skill_match,
        "seniority_match": seniority_match,
        "learning_opportunity": learning_opportunity,
        "metadata": {"source_order": int(job_id)},
    }


def _jobs() -> list[dict]:
    return [
        _job(
            "1",
            company="ColdCo",
            title="Data Scientist",
            ai_relevance=0.4,
            skill_match=0.5,
            seniority_match=0.6,
            learning_opportunity=0.7,
        ),
        _job(
            "2",
            company="HotCo",
            title="Senior Machine Learning Engineer",
            ai_relevance=0.9,
            skill_match=0.8,
            seniority_match=0.9,
            learning_opportunity=0.6,
        ),
        _job(
            "3",
            company="OtherCo",
            title="Staff AI Engineer",
            ai_relevance=0.7,
            skill_match=0.7,
            seniority_match=0.8,
            learning_opportunity=0.5,
        ),
    ]


def _momentum():
    return [("HotCo", 10, 5, 2, 1)]


def _direct(jobs: list[dict]) -> list[dict]:
    return application_scorer.score_jobs(deepcopy(jobs))


def _graph(jobs: list[dict]) -> dict:
    return graph_owner.execute_authoritative_final_scoring_graph(
        jobs=jobs,
        pipeline_run_id="run-phase16b",
        owner_user_id="owner-phase16b",
        context_id="context-phase16b",
    )


def test_exact_graph_and_state_versions():
    assert (
        graph_owner.AUTHORITATIVE_FINAL_SCORING_GRAPH_VERSION
        == "authoritative-final-scoring-graph-v1"
    )
    assert (
        graph_owner.AUTHORITATIVE_FINAL_SCORING_STATE_VERSION
        == "authoritative-final-scoring-state-v1"
    )


def test_real_state_graph_has_one_production_node():
    graph = graph_owner.build_authoritative_final_scoring_graph()

    assert type(graph).__name__ == "StateGraph"
    assert set(graph.nodes) == {"score_jobs"}
    assert graph_owner.AUTHORITATIVE_FINAL_SCORING_PRODUCTION_NODE_COUNT == 1


def test_graph_order_is_start_score_jobs_end():
    graph = graph_owner.build_authoritative_final_scoring_graph()

    assert graph.edges == {
        ("__start__", "score_jobs"),
        ("score_jobs", "__end__"),
    }


def test_activation_gate_defaults_off():
    for value in (None, "", "0", "false", "no", "off"):
        env = {} if value is None else {GATE: value}
        assert (
            collector._authoritative_final_scoring_langgraph_enabled(env)
            is False
        )


def test_activation_gate_uses_existing_truthy_convention():
    for value in ("1", "true", "TRUE", "yes", "on"):
        assert (
            collector._authoritative_final_scoring_langgraph_enabled(
                {GATE: value}
            )
            is True
        )


def test_gate_off_does_not_import_or_construct_graph(monkeypatch):
    monkeypatch.delitem(sys.modules, GRAPH_MODULE, raising=False)

    result = collector._maybe_execute_authoritative_final_scoring_graph(
        jobs=_jobs(),
        env={},
    )

    assert result is None
    assert GRAPH_MODULE not in sys.modules


def test_gate_on_lazily_imports_graph_and_forwards_context(monkeypatch):
    captured = {}

    def execute(**kwargs):
        captured.update(deepcopy(kwargs))
        return {
            "scored_jobs": [],
            "execution_metadata": {
                "execution_mode": "langgraph",
                "production_node_count": 1,
                "invocation_count": 1,
                "status": "completed",
            },
        }

    monkeypatch.setitem(
        sys.modules,
        GRAPH_MODULE,
        types.SimpleNamespace(
            execute_authoritative_final_scoring_graph=execute
        ),
    )
    jobs = _jobs()
    result = collector._maybe_execute_authoritative_final_scoring_graph(
        jobs=jobs,
        env={
            GATE: "1",
            "JOB_APP_PIPELINE_RUN_ID": "run-16b",
            "JOB_STACK_OWNER_USER_ID": "owner-16b",
            "APPLYLENS_AGENT_CONTEXT_ID": "context-16b",
        },
    )

    assert result is not None
    assert captured["jobs"] == jobs
    assert captured["pipeline_run_id"] == "run-16b"
    assert captured["owner_user_id"] == "owner-16b"
    assert captured["context_id"] == "context-16b"


def test_production_direct_and_graph_outputs_are_identical(monkeypatch):
    monkeypatch.setattr(
        application_scorer,
        "get_hiring_momentum",
        _momentum,
    )
    jobs = _jobs()

    direct = _direct(jobs)
    graph = _graph(jobs)

    assert graph["scored_jobs"] == direct


def test_direct_and_graph_output_order_is_identical(monkeypatch):
    monkeypatch.setattr(
        application_scorer,
        "get_hiring_momentum",
        _momentum,
    )

    direct = _direct(_jobs())
    graph = _graph(_jobs())["scored_jobs"]

    assert [row["job_id"] for row in graph] == [
        row["job_id"] for row in direct
    ]
    assert [row["priority_score"] for row in graph] == sorted(
        [row["priority_score"] for row in graph],
        reverse=True,
    )


def test_score_fields_and_schema_are_identical(monkeypatch):
    monkeypatch.setattr(
        application_scorer,
        "get_hiring_momentum",
        _momentum,
    )
    direct = _direct(_jobs())
    graph = _graph(_jobs())["scored_jobs"]

    assert [set(row) for row in graph] == [set(row) for row in direct]
    assert [row["ai_signal_score"] for row in graph] == [
        row["ai_signal_score"] for row in direct
    ]
    assert [row["priority_score"] for row in graph] == [
        row["priority_score"] for row in direct
    ]


def test_production_owner_executes_exactly_once(monkeypatch):
    calls = []
    real_owner = application_scorer.score_jobs
    monkeypatch.setattr(
        application_scorer,
        "get_hiring_momentum",
        _momentum,
    )

    def counted_owner(jobs):
        calls.append("score_jobs")
        return real_owner(jobs)

    monkeypatch.setattr(application_scorer, "score_jobs", counted_owner)

    result = _graph(_jobs())

    assert calls == ["score_jobs"]
    assert result["execution_metadata"]["invocation_count"] == 1


def test_momentum_lookup_count_is_not_duplicated(monkeypatch):
    calls = []

    def counted_momentum():
        calls.append(1)
        return _momentum()

    monkeypatch.setattr(
        application_scorer,
        "get_hiring_momentum",
        counted_momentum,
    )

    _graph(_jobs())

    assert calls == [1, 1, 1]


def test_caller_jobs_remain_unchanged(monkeypatch):
    monkeypatch.setattr(
        application_scorer,
        "get_hiring_momentum",
        _momentum,
    )
    jobs = _jobs()
    before = deepcopy(jobs)

    _graph(jobs)

    assert jobs == before


def test_deep_copy_contains_owner_mutation(monkeypatch):
    jobs = _jobs()
    before = deepcopy(jobs)

    def mutating_owner(rows):
        rows[0]["metadata"]["owner_mutation"] = True
        return rows

    monkeypatch.setattr(
        application_scorer,
        "score_jobs",
        mutating_owner,
    )

    result = _graph(jobs)

    assert jobs == before
    assert result["scored_jobs"][0]["metadata"]["owner_mutation"] is True


def test_empty_input_preserves_empty_contract(monkeypatch):
    calls = []

    def unexpected_momentum():
        calls.append(1)
        return []

    monkeypatch.setattr(
        application_scorer,
        "get_hiring_momentum",
        unexpected_momentum,
    )

    result = _graph([])

    assert result["scored_jobs"] == []
    assert result["execution_metadata"]["input_count"] == 0
    assert result["execution_metadata"]["scored_count"] == 0
    assert calls == []


def test_owner_failure_propagates_once_without_direct_fallback(monkeypatch):
    calls = []

    def fail_owner(rows):
        calls.append(1)
        raise RuntimeError("final_scoring_failed")

    monkeypatch.setattr(application_scorer, "score_jobs", fail_owner)

    try:
        _graph(_jobs())
    except RuntimeError as exc:
        assert str(exc) == "final_scoring_failed"
    else:
        raise AssertionError("expected final scoring failure")

    assert calls == [1]


def test_malformed_owner_output_fails_closed(monkeypatch):
    monkeypatch.setattr(
        application_scorer,
        "score_jobs",
        lambda rows: "invalid",
    )

    try:
        _graph(_jobs())
    except TypeError as exc:
        assert "authoritative_final_scoring_scored_jobs_must_be_list" in str(
            exc
        )
    else:
        raise AssertionError("expected malformed output failure")


def test_owner_output_count_mismatch_fails_closed(monkeypatch):
    monkeypatch.setattr(
        application_scorer,
        "score_jobs",
        lambda rows: rows[:-1],
    )

    try:
        _graph(_jobs())
    except RuntimeError as exc:
        assert str(exc) == "authoritative_final_scoring_output_count_mismatch"
    else:
        raise AssertionError("expected output count failure")


def test_execution_metadata_is_bounded_and_contains_no_rows(monkeypatch):
    monkeypatch.setattr(
        application_scorer,
        "get_hiring_momentum",
        _momentum,
    )

    metadata = _graph(_jobs())["execution_metadata"]

    assert metadata["node_name"] == "score_jobs"
    assert metadata["production_node_count"] == 1
    assert 0 <= metadata["node_latency_ms"] <= 300_000
    assert metadata["deterministic"] is True
    assert metadata["caller_input_immutable"] is True
    assert metadata["provider_calls_allowed"] is False
    assert metadata["persistent_mutation_authority"] is False
    assert metadata["application_authority"] is False
    assert metadata["ats_authority"] is False
    assert "jobs" not in metadata
    assert "rows" not in metadata


def test_graph_owner_has_no_llm_provider_persistence_or_action_authority():
    source = Path(
        "src/agents/final_scoring_authoritative_graph.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "job_fit_evaluator",
        "evaluate_jobs",
        "llm_client",
        "run_chat_completion",
        "provider_client",
        "dotenv",
        "api_key",
        "connect(",
        ".commit(",
        "checkpointer",
        "submit_application",
        "mark_applied",
        "ats_submission",
        "write_text(",
        "write_bytes(",
    )

    for token in forbidden:
        assert token not in source


def test_collector_preserves_llm_then_final_scoring_order():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")

    evaluation_stage = source.index('section("AI JOB EVALUATION", logger)')
    evaluation = source.index(
        "evaluate_jobs_with_progress = _wrap_ai_evaluator_with_runtime_progress(",
        evaluation_stage,
    )
    semantic_graph = source.index(
        "_maybe_execute_authoritative_semantic_evaluation_graph(",
        evaluation,
    )
    direct_fallback = source.index(
        "ai_jobs = evaluate_jobs_with_progress(evaluable_jobs)",
        semantic_graph,
    )
    evaluated_jobs_available = source.index(
        'logger.info(f"AI evaluated {len(ai_jobs)} jobs")',
        direct_fallback,
    )
    scoring_boundary = source.index(
        "_maybe_execute_authoritative_final_scoring_graph(jobs=ai_jobs)",
        evaluated_jobs_available,
    )
    shadow = source.index(
        "_maybe_run_shadow_sidecar_after_application_priority(",
        scoring_boundary,
    )

    assert (
        evaluation
        < semantic_graph
        < direct_fallback
        < evaluated_jobs_available
        < scoring_boundary
        < shadow
    )
    assert "evaluate_jobs_func=evaluate_jobs_with_progress" in source[
        semantic_graph:direct_fallback
    ]
    assert source.count(
        "ai_jobs = evaluate_jobs_with_progress(evaluable_jobs)"
    ) == 1


def test_gate_off_collector_path_keeps_direct_owner_call():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    graph_call = source.index(
        "_maybe_execute_authoritative_final_scoring_graph(jobs=ai_jobs)"
    )
    direct_branch = source.index(
        "if final_scoring_graph_result is None:",
        graph_call,
    )
    direct_owner = source.index("scored_jobs = score_jobs(ai_jobs)", graph_call)

    assert graph_call < direct_branch < direct_owner


def test_source_health_remains_internal_log_and_report_ownership():
    collector_source = Path("src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )
    health_source = Path("src/utils/ats_health.py").read_text(
        encoding="utf-8"
    )

    assert "check_ats_health(all_jobs)" in collector_source
    assert "build_source_health_report_rows(" in collector_source
    assert "write_source_health_report_csv(" in collector_source
    assert "def check_ats_health(jobs):" in health_source
    assert "return " not in health_source.split(
        "def check_ats_health(jobs):",
        1,
    )[1].split("def check_pipeline_regression", 1)[0]


def test_discovery_collection_remains_network_and_persistence_owned():
    source = Path("src/pipeline/discovery_stage.py").read_text(
        encoding="utf-8"
    )

    assert "aiohttp.ClientSession" in source
    assert "asyncio.Semaphore(20)" in source
    assert "persist_discovered_companies()" in source
    assert "run_sitemap_discovery()" in source


def test_cache_routing_and_persistence_remain_inside_job_cache_owner():
    source = Path("src/utils/job_cache.py").read_text(encoding="utf-8")

    assert "def filter_new_jobs(jobs, seen_ids):" in source
    assert "def _postgres_load_seen_job_ids(" in source
    assert "def _postgres_save_new_job_ids(" in source
    assert "upsert_user_seen_job_postgres_payload(" in source
    assert "upsert_user_seen_job_staging_postgres_payload(" in source


def test_application_safety_remains_manual_and_non_executing():
    queue_source = Path("application_execution_queue.py").read_text(
        encoding="utf-8"
    )
    operator_source = Path("src/agents/operator_review_agent.py").read_text(
        encoding="utf-8"
    )
    operator_graph_source = Path(
        "src/agents/operator_review_authoritative_graph.py"
    ).read_text(encoding="utf-8")

    assert '"ready_to_apply"' in operator_source
    assert '"application_authority": False' in operator_graph_source
    assert '"ats_authority": False' in operator_graph_source
    assert '"did_submit_application": False' in queue_source
    assert '"automatic_submission_loop_enabled": False' in queue_source


def test_llm_responsibilities_remain_deferred_outside_graph():
    collector_source = Path("src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )
    graph_source = Path(
        "src/agents/final_scoring_authoritative_graph.py"
    ).read_text(encoding="utf-8")

    assert "from src.ai.job_fit_evaluator import evaluate_jobs" in collector_source
    assert (
        "evaluate_jobs_with_progress = _wrap_ai_evaluator_with_runtime_progress("
        in collector_source
    )
    assert "evaluate_jobs_func=evaluate_jobs_with_progress" in collector_source
    assert (
        collector_source.count(
            "ai_jobs = evaluate_jobs_with_progress(evaluable_jobs)"
        )
        == 1
    )
    assert (
        'ai_jobs = semantic_evaluation_graph_result["evaluated_jobs"]'
        in collector_source
    )
    assert "build_job_intelligence" in collector_source
    assert "evaluate_jobs" not in graph_source
    assert "build_job_intelligence" not in graph_source


def test_existing_activated_nodes_remain_unchanged_and_separate():
    graph_paths = (
        "src/agents/deterministic_prefilter_dedupe_authoritative_graph.py",
        "src/agents/job_prioritization_authoritative_graph.py",
        "src/agents/tailoring_decision_authoritative_graph.py",
        "src/agents/operator_review_authoritative_graph.py",
    )
    node_count = 0

    for path in graph_paths:
        node_count += Path(path).read_text(encoding="utf-8").count(
            "graph.add_node("
        )

    assert node_count == 5
    assert graph_owner.AUTHORITATIVE_FINAL_SCORING_PRODUCTION_NODE_COUNT == 1


def test_run006_remains_absent():
    root = Path(".")

    assert not any(
        path.name.lower().replace("_", "-").startswith("run-006")
        for path in root.rglob("*")
    )
