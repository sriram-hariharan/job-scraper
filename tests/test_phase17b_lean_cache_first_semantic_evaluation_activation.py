from __future__ import annotations

from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys
import types

import pytest

from src.agents import semantic_evaluation_authoritative_graph as graph_owner
from src.pipeline import collector


GRAPH_MODULE = "src.agents.semantic_evaluation_authoritative_graph"
GATE = "APPLYLENS_AUTHORITATIVE_SEMANTIC_EVALUATION_LANGGRAPH_ENABLED"


def _jobs(count: int = 2) -> list[dict]:
    return [
        {
            "job_id": f"job-{index}",
            "company": f"Example {index}",
            "title": "Machine Learning Engineer",
            "intelligence": {
                "skills": {
                    "required": ["python"],
                    "preferred": ["pytorch"],
                    "all": ["python", "pytorch"],
                },
                "seniority": "senior",
                "ai_flags": {"machine_learning": True},
            },
            "embedding_score": float(index) / 10,
        }
        for index in range(count)
    ]


def _evaluation(index: int = 0) -> dict:
    return {
        "ai_relevance": 8 + index,
        "skill_match": 7,
        "seniority_match": 8,
        "learning_opportunity": 9,
        "overall_score": 8,
        "visa_sponsorship_signal": "unknown",
        "reason": "Bounded synthetic evaluation",
    }


def _response_for(batch: list[dict]) -> str:
    return json.dumps(
        {
            "results": [
                {
                    "id": index,
                    **_evaluation(index),
                }
                for index, _job in enumerate(batch)
            ]
        }
    )


def _fake_owner(jobs: list[dict]) -> list[dict]:
    for index, job in enumerate(jobs):
        job["ai_fit_score"] = 8 + index
        job["ai_fit"] = f"{8 + index}/10"
    return jobs


def _graph(
    jobs: list[dict],
    *,
    owner=_fake_owner,
) -> dict:
    return graph_owner.execute_authoritative_semantic_evaluation_graph(
        jobs=jobs,
        evaluate_jobs_func=owner,
        pipeline_run_id="run-phase17b",
        owner_user_id="owner-phase17b",
        context_id="context-phase17b",
    )


def _evaluator(monkeypatch):
    import dotenv

    monkeypatch.setattr(
        dotenv,
        "load_dotenv",
        lambda *_args, **_kwargs: False,
    )
    evaluator = importlib.import_module("src.ai.job_fit_evaluator")
    monkeypatch.setattr(evaluator, "EVAL_MODE", "cache_prefer_live")
    monkeypatch.setattr(evaluator, "BATCH_SIZE", 5)
    monkeypatch.setattr(evaluator, "MIN_REQUEST_INTERVAL", 0.0)
    monkeypatch.setattr(evaluator, "last_request_time", 0)
    monkeypatch.setattr(evaluator.random, "shuffle", lambda _items: None)
    evaluator.reset_eval_cache_metrics()
    return evaluator


def test_exact_graph_and_state_versions():
    assert (
        graph_owner.AUTHORITATIVE_SEMANTIC_EVALUATION_GRAPH_VERSION
        == "authoritative-semantic-evaluation-graph-v1"
    )
    assert (
        graph_owner.AUTHORITATIVE_SEMANTIC_EVALUATION_STATE_VERSION
        == "authoritative-semantic-evaluation-state-v1"
    )


def test_real_state_graph_has_exactly_one_production_node():
    graph = graph_owner.build_authoritative_semantic_evaluation_graph(
        evaluate_jobs_func=_fake_owner
    )

    assert type(graph).__name__ == "StateGraph"
    assert set(graph.nodes) == {"semantic_job_fit_evaluation"}
    assert (
        graph_owner.AUTHORITATIVE_SEMANTIC_EVALUATION_PRODUCTION_NODE_COUNT
        == 1
    )


def test_graph_order_is_start_semantic_evaluation_end():
    graph = graph_owner.build_authoritative_semantic_evaluation_graph(
        evaluate_jobs_func=_fake_owner
    )

    assert graph.edges == {
        ("__start__", "semantic_job_fit_evaluation"),
        ("semantic_job_fit_evaluation", "__end__"),
    }


def test_activation_gate_defaults_off():
    for value in (None, "", "0", "false", "no", "off"):
        env = {} if value is None else {GATE: value}
        assert (
            collector._authoritative_semantic_evaluation_langgraph_enabled(
                env
            )
            is False
        )


def test_activation_gate_uses_existing_truthy_convention():
    for value in ("1", "true", "TRUE", "yes", "on"):
        assert (
            collector._authoritative_semantic_evaluation_langgraph_enabled(
                {GATE: value}
            )
            is True
        )


def test_gate_off_uses_direct_owner_once_without_graph_import(monkeypatch):
    monkeypatch.delitem(sys.modules, GRAPH_MODULE, raising=False)
    calls = []

    def owner(jobs):
        calls.append(1)
        return jobs

    jobs = _jobs()
    graph_result = (
        collector._maybe_execute_authoritative_semantic_evaluation_graph(
            jobs=jobs,
            evaluate_jobs_func=owner,
            env={},
        )
    )
    output = owner(jobs) if graph_result is None else graph_result[
        "evaluated_jobs"
    ]

    assert output == jobs
    assert calls == [1]
    assert GRAPH_MODULE not in sys.modules


def test_gate_on_lazily_invokes_graph_and_owner_once(monkeypatch):
    graph_calls = []
    owner_calls = []

    def execute(**kwargs):
        graph_calls.append(1)
        evaluated = kwargs["evaluate_jobs_func"](kwargs["jobs"])
        return {
            "evaluated_jobs": evaluated,
            "execution_metadata": {
                "execution_mode": "langgraph",
                "production_node_count": 1,
                "invocation_count": 1,
                "status": "completed",
            },
        }

    def owner(jobs):
        owner_calls.append(1)
        return jobs

    monkeypatch.setitem(
        sys.modules,
        GRAPH_MODULE,
        types.SimpleNamespace(
            execute_authoritative_semantic_evaluation_graph=execute
        ),
    )
    result = collector._maybe_execute_authoritative_semantic_evaluation_graph(
        jobs=_jobs(),
        evaluate_jobs_func=owner,
        env={
            GATE: "1",
            "JOB_APP_PIPELINE_RUN_ID": "run-17b",
            "JOB_STACK_OWNER_USER_ID": "owner-17b",
            "APPLYLENS_AGENT_CONTEXT_ID": "context-17b",
        },
    )

    assert result is not None
    assert graph_calls == [1]
    assert owner_calls == [1]


def test_direct_and_graph_outputs_are_identical():
    direct_input = _jobs()
    graph_input = deepcopy(direct_input)

    direct = _fake_owner(direct_input)
    graph = _graph(graph_input)["evaluated_jobs"]

    assert graph == direct


def test_direct_and_graph_mutation_contracts_are_identical():
    direct_input = _jobs()
    graph_input = deepcopy(direct_input)

    _fake_owner(direct_input)
    _graph(graph_input)

    assert graph_input == direct_input
    assert all("ai_fit_score" in job for job in graph_input)


def test_production_owner_invocation_count_is_exactly_one():
    calls = []

    def owner(jobs):
        calls.append(1)
        return jobs

    result = _graph(_jobs(), owner=owner)

    assert calls == [1]
    assert result["execution_metadata"]["invocation_count"] == 1


def test_graph_failure_propagates_without_direct_fallback():
    calls = []

    def owner(_jobs):
        calls.append(1)
        raise RuntimeError("semantic_evaluation_failed")

    with pytest.raises(RuntimeError, match="semantic_evaluation_failed"):
        _graph(_jobs(), owner=owner)

    assert calls == [1]


def test_malformed_owner_output_fails_closed():
    with pytest.raises(
        TypeError,
        match="authoritative_semantic_evaluated_jobs_must_be_list",
    ):
        _graph(_jobs(), owner=lambda _jobs: "invalid")


def test_execution_metadata_is_bounded_and_contains_no_jobs():
    metadata = _graph(_jobs())["execution_metadata"]

    assert metadata["node_name"] == "semantic_job_fit_evaluation"
    assert 0 <= metadata["node_latency_ms"] <= 300_000
    assert metadata["provider_calls_allowed"] is True
    assert (
        metadata["mutation_contract"]
        == "production_evaluator_mutates_input_jobs"
    )
    assert metadata["mutation_authority"] is False
    assert metadata["application_authority"] is False
    assert metadata["ats_authority"] is False
    assert "jobs" not in metadata
    assert "resume" not in metadata


def test_graph_does_not_recompute_upstream_or_downstream_stages():
    source = Path(
        "src/agents/semantic_evaluation_authoritative_graph.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "build_job_intelligence",
        "filter_jobs_for_ai_evaluation",
        "prefilter_jobs_by_embedding",
        "score_jobs",
        "critic",
        "tailoring",
        "submit_application",
        "ats_submission",
        "run_chat_completion",
        "get_cached_job_evaluation",
        "store_cached_job_evaluation",
        "dotenv",
        "api_key",
    )

    for token in forbidden:
        assert token not in source


def test_all_cache_hits_make_zero_provider_calls_and_preserve_parity(
    monkeypatch,
):
    evaluator = _evaluator(monkeypatch)
    lookups = []
    provider_calls = []
    stores = []
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda key: (lookups.append(key) or _evaluation()),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **kwargs: provider_calls.append(kwargs),
    )
    monkeypatch.setattr(
        evaluator,
        "store_cached_job_evaluation",
        lambda **kwargs: stores.append(kwargs),
    )
    direct_input = _jobs()
    graph_input = deepcopy(direct_input)
    direct = evaluator.evaluate_jobs(direct_input)
    lookups.clear()

    graph = _graph(
        graph_input,
        owner=evaluator.evaluate_jobs,
    )["evaluated_jobs"]

    assert graph == direct
    assert len(lookups) == len(graph_input)
    assert provider_calls == []
    assert stores == []


def test_cache_only_miss_preserves_skip_marker(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(evaluator, "EVAL_MODE", "cache_only")
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: None,
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("cache_only must not call provider"),
    )

    result = _graph(
        _jobs(1),
        owner=evaluator.evaluate_jobs,
    )["evaluated_jobs"]

    assert result[0]["ai_fit"] == "EVAL_SKIPPED_CACHE_ONLY"
    assert evaluator.get_eval_cache_metrics()["eval_cache_only_skips"] == 1


def test_cache_prefer_live_miss_uses_one_batch_call_and_owner_cache_writes(
    monkeypatch,
):
    evaluator = _evaluator(monkeypatch)
    lookups = []
    provider_calls = []
    stores = []
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda key: (lookups.append(key) or None),
    )

    def provider(**kwargs):
        provider_calls.append(kwargs)
        return _response_for(_jobs())

    monkeypatch.setattr(evaluator, "run_chat_completion", provider)
    monkeypatch.setattr(
        evaluator,
        "store_cached_job_evaluation",
        lambda **kwargs: stores.append(kwargs),
    )
    jobs = _jobs()

    result = _graph(
        jobs,
        owner=evaluator.evaluate_jobs,
    )["evaluated_jobs"]

    assert len(lookups) == 2
    assert len(provider_calls) == 1
    assert len(stores) == 2
    assert [job["job_id"] for job in result] == ["job-0", "job-1"]
    assert all(not any(key.startswith("_eval_") for key in job) for job in result)


def test_live_only_mode_bypasses_cache_lookup_and_write(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(evaluator, "EVAL_MODE", "live_only")
    provider_calls = []
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: pytest.fail("live_only must not read cache"),
    )
    monkeypatch.setattr(
        evaluator,
        "store_cached_job_evaluation",
        lambda **_kwargs: pytest.fail("live_only must not write cache"),
    )

    def provider(**kwargs):
        provider_calls.append(kwargs)
        return _response_for(_jobs())

    monkeypatch.setattr(evaluator, "run_chat_completion", provider)

    result = _graph(
        _jobs(),
        owner=evaluator.evaluate_jobs,
    )["evaluated_jobs"]

    assert len(provider_calls) == 1
    assert len(result) == 2


def test_provider_exception_preserves_existing_failure_marker(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    calls = []
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: None,
    )

    def fail(**_kwargs):
        calls.append(1)
        raise RuntimeError("bounded provider failure")

    monkeypatch.setattr(evaluator, "run_chat_completion", fail)

    result = _graph(
        _jobs(1),
        owner=evaluator.evaluate_jobs,
    )["evaluated_jobs"]

    assert calls == [1]
    assert result[0]["ai_fit"] == "LLM_CALL_FAIL"


def test_parse_failure_preserves_existing_retry_and_marker(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    calls = []
    sleeps = []
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: None,
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: (calls.append(1) or "invalid"),
    )
    monkeypatch.setattr(
        evaluator.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )

    result = _graph(
        _jobs(1),
        owner=evaluator.evaluate_jobs,
    )["evaluated_jobs"]

    assert len(calls) == 5
    assert len(sleeps) == 4
    assert result[0]["ai_fit"] == "PARSE_ERROR"


def test_rate_limit_failure_preserves_existing_retry_and_marker(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    calls = []
    sleeps = []
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: None,
    )

    def rate_limited(**_kwargs):
        calls.append(1)
        raise RuntimeError("429 bounded rate limit")

    monkeypatch.setattr(evaluator, "run_chat_completion", rate_limited)
    monkeypatch.setattr(
        evaluator.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )

    result = _graph(
        _jobs(1),
        owner=evaluator.evaluate_jobs,
    )["evaluated_jobs"]

    assert len(calls) == 5
    assert len(sleeps) == 5
    assert result[0]["ai_fit"] == "RATE_LIMIT_FAIL"


def test_output_order_restored_after_existing_batch_shuffle(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(evaluator, "BATCH_SIZE", 1)
    monkeypatch.setattr(
        evaluator.random,
        "shuffle",
        lambda batches: batches.reverse(),
    )
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: None,
    )
    monkeypatch.setattr(
        evaluator,
        "store_cached_job_evaluation",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: _response_for(_jobs(1)),
    )
    jobs = _jobs(7)

    result = _graph(
        jobs,
        owner=evaluator.evaluate_jobs,
    )["evaluated_jobs"]

    assert [job["job_id"] for job in result] == [
        f"job-{index}" for index in range(7)
    ]
    assert all(not any(key.startswith("_eval_") for key in job) for job in result)


def test_collector_seam_preserves_upstream_and_downstream_order():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    eligibility = source.index(
        "evaluable_jobs = filter_jobs_for_ai_evaluation(intelligent_jobs)"
    )
    embedding = source.index(
        "evaluable_jobs = prefilter_jobs_by_embedding(",
        eligibility,
    )
    trace = source.index(
        "_record_relevance_prefilter_agent_trace(",
        embedding,
    )
    graph_call = source.index(
        "_maybe_execute_authoritative_semantic_evaluation_graph(",
        trace,
    )
    direct = source.index(
        "ai_jobs = evaluate_jobs(evaluable_jobs)",
        graph_call,
    )
    final_scoring = source.index(
        "_maybe_execute_authoritative_final_scoring_graph(jobs=ai_jobs)",
        direct,
    )

    assert eligibility < embedding < trace < graph_call < direct < final_scoring
    assert "if semantic_evaluation_graph_result is None:" in source[
        graph_call:direct
    ]
    assert 'start_stage("ai_evaluation"' in source
    assert 'complete_stage("ai_evaluation"' in source
    assert "get_provider_metrics()" in source
    assert "get_eval_cache_metrics()" in source


def test_final_scoring_receives_identical_direct_and_graph_outputs():
    direct_input = _jobs()
    graph_input = deepcopy(direct_input)
    direct_output = _fake_owner(direct_input)
    graph_output = _graph(graph_input)["evaluated_jobs"]

    def scoring_input_signature(jobs):
        return [
            (job["job_id"], job["ai_fit_score"], job["embedding_score"])
            for job in jobs
        ]

    assert scoring_input_signature(graph_output) == scoring_input_signature(
        direct_output
    )


def test_run006_remains_absent():
    assert not any(
        path.name.lower().replace("_", "-").startswith("run-006")
        for path in Path(".").rglob("*")
    )
