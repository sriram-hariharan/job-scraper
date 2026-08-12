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

    monkeypatch.delenv("JOB_STACK_OWNER_USER_ID", raising=False)
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


def _install_owner_route(
    evaluator,
    monkeypatch,
    *,
    provider="groq",
    model="openai/gpt-oss-20b",
    route_calls=None,
):
    calls = [] if route_calls is None else route_calls

    def resolve(owner_user_id, workload_id):
        calls.append((owner_user_id, workload_id))
        return {
            "workload_id": workload_id,
            "provider": provider,
            "model": model,
            "effective_selection_source": "applylens_recommended",
        }

    monkeypatch.setattr(
        evaluator,
        "resolve_effective_user_provider_route",
        resolve,
    )
    return calls


def _install_cache_miss(evaluator, monkeypatch):
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


def test_no_owner_preserves_exact_legacy_live_runtime(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    legacy_calls = []
    monkeypatch.setattr(
        evaluator,
        "resolve_effective_user_provider_route",
        lambda *_args: pytest.fail("legacy mode must not resolve owner route"),
    )
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("legacy mode must not use user runtime"),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **kwargs: (
            legacy_calls.append(kwargs) or _response_for(_jobs(1))
        ),
    )

    result = evaluator.evaluate_jobs(_jobs(1))

    assert result[0]["ai_fit_score"] == 8
    assert len(legacy_calls) == 1
    assert legacy_calls[0]["model"] == evaluator.MODEL
    assert legacy_calls[0]["temperature"] == evaluator.JOB_FIT_TEMPERATURE
    assert legacy_calls[0]["max_tokens"] == evaluator.JOB_FIT_MAX_TOKENS


@pytest.mark.parametrize(
    ("explicit_owner", "environment_owner", "expected_owner"),
    (
        ("explicit-owner", "environment-owner", "explicit-owner"),
        (" ", "environment-owner", "environment-owner"),
    ),
)
def test_owner_resolution_precedence_is_explicit_then_environment(
    monkeypatch,
    explicit_owner,
    environment_owner,
    expected_owner,
):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", environment_owner)
    route_calls = _install_owner_route(evaluator, monkeypatch)
    runtime_calls = []
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: (
            runtime_calls.append(kwargs)
            or {"content": _response_for(_jobs(1))}
        ),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("owner mode must not use legacy runtime"),
    )

    evaluator.evaluate_jobs(_jobs(1), owner_user_id=explicit_owner)

    assert route_calls == [(expected_owner, "job_fit_evaluation")]
    assert runtime_calls[0]["owner_user_id"] == expected_owner


def test_owner_all_cache_hits_do_not_resolve_or_execute(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "owner-cache-hit")
    lookups = []
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda key: (lookups.append(key) or _evaluation()),
    )
    monkeypatch.setattr(
        evaluator,
        "resolve_effective_user_provider_route",
        lambda *_args: pytest.fail("cache hits must not resolve owner route"),
    )
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("cache hits must not use user runtime"),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("cache hits must not use legacy runtime"),
    )

    result = evaluator.evaluate_jobs(_jobs(2))

    assert len(lookups) == 2
    assert [job["ai_fit_score"] for job in result] == [8, 8]


def test_owner_cache_only_miss_does_not_resolve_or_execute(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(evaluator, "EVAL_MODE", "cache_only")
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "owner-cache-only")
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: None,
    )
    monkeypatch.setattr(
        evaluator,
        "resolve_effective_user_provider_route",
        lambda *_args: pytest.fail("cache_only must not resolve owner route"),
    )
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("cache_only must not use user runtime"),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("cache_only must not use legacy runtime"),
    )

    result = evaluator.evaluate_jobs(_jobs(1))

    assert result[0]["ai_fit"] == "EVAL_SKIPPED_CACHE_ONLY"
    assert evaluator.get_eval_cache_metrics()["eval_cache_only_skips"] == 1


@pytest.mark.parametrize(
    ("provider", "model"),
    (
        ("groq", "openai/gpt-oss-20b"),
        ("openai", "gpt-5-mini"),
    ),
)
def test_owner_cache_miss_executes_exact_effective_route(
    monkeypatch,
    provider,
    model,
):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    route_calls = _install_owner_route(
        evaluator,
        monkeypatch,
        provider=provider,
        model=model,
    )
    runtime_calls = []
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: (
            runtime_calls.append(kwargs)
            or {"content": _response_for(_jobs(1))}
        ),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("owner mode must not use legacy runtime"),
    )

    result = evaluator.evaluate_jobs(_jobs(1), owner_user_id="owner-live")

    assert route_calls == [("owner-live", "job_fit_evaluation")]
    assert len(runtime_calls) == 1
    assert {
        key: runtime_calls[0][key]
        for key in ("owner_user_id", "provider", "model")
    } == {
        "owner_user_id": "owner-live",
        "provider": provider,
        "model": model,
    }
    assert runtime_calls[0]["temperature"] == evaluator.JOB_FIT_TEMPERATURE
    assert runtime_calls[0]["max_tokens"] == evaluator.JOB_FIT_MAX_TOKENS
    assert result[0]["ai_fit_score"] == 8


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


def test_owner_route_is_frozen_once_across_multiple_batches(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(evaluator, "BATCH_SIZE", 2)
    _install_cache_miss(evaluator, monkeypatch)
    route_calls = _install_owner_route(
        evaluator,
        monkeypatch,
        provider="openai",
        model="gpt-5-mini",
    )
    runtime_calls = []
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: (
            runtime_calls.append(kwargs)
            or {"content": _response_for(_jobs(2))}
        ),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("owner mode must not use legacy runtime"),
    )

    result = evaluator.evaluate_jobs(_jobs(6), owner_user_id="owner-batches")

    assert route_calls == [("owner-batches", "job_fit_evaluation")]
    assert len(runtime_calls) == 3
    assert {
        (call["owner_user_id"], call["provider"], call["model"])
        for call in runtime_calls
    } == {("owner-batches", "openai", "gpt-5-mini")}
    assert [job["job_id"] for job in result] == [
        f"job-{index}" for index in range(6)
    ]


def test_owner_route_is_frozen_across_parse_retries(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    route_calls = _install_owner_route(evaluator, monkeypatch)
    runtime_calls = []
    sleeps = []
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: (
            runtime_calls.append(kwargs) or {"content": "invalid"}
        ),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("owner retries must not use legacy runtime"),
    )
    monkeypatch.setattr(
        evaluator.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )

    result = evaluator.evaluate_jobs(_jobs(1), owner_user_id="owner-parse")

    assert route_calls == [("owner-parse", "job_fit_evaluation")]
    assert len(runtime_calls) == 5
    assert {
        (call["provider"], call["model"])
        for call in runtime_calls
    } == {("groq", "openai/gpt-oss-20b")}
    assert sleeps == [10, 20, 40, 80]
    assert result[0]["ai_fit"] == "PARSE_ERROR"


def test_owner_bounded_rate_limit_preserves_retries_and_frozen_route(
    monkeypatch,
):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    route_calls = _install_owner_route(
        evaluator,
        monkeypatch,
        provider="openai",
        model="gpt-5-mini",
    )
    runtime_calls = []
    sleeps = []

    def rate_limited(**kwargs):
        runtime_calls.append(kwargs)
        raise RuntimeError("provider_execution_failed:category=rate_limit")

    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        rate_limited,
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("owner retries must not use legacy runtime"),
    )
    monkeypatch.setattr(
        evaluator.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )

    result = evaluator.evaluate_jobs(_jobs(1), owner_user_id="owner-rate")

    assert route_calls == [("owner-rate", "job_fit_evaluation")]
    assert len(runtime_calls) == 5
    assert {
        (call["provider"], call["model"])
        for call in runtime_calls
    } == {("openai", "gpt-5-mini")}
    assert sleeps == [10, 20, 40, 80, 160]
    assert result[0]["ai_fit"] == "RATE_LIMIT_FAIL"
    assert evaluator.get_eval_cache_metrics()["eval_live_failures"] == 1


def test_owner_route_failure_preserves_hits_and_fails_misses_closed(
    monkeypatch,
):
    evaluator = _evaluator(monkeypatch)
    cached = iter((_evaluation(), None))
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: next(cached),
    )
    route_calls = []

    def fail_route(owner_user_id, workload_id):
        route_calls.append((owner_user_id, workload_id))
        raise ValueError("private routing detail")

    monkeypatch.setattr(
        evaluator,
        "resolve_effective_user_provider_route",
        fail_route,
    )
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("failed route must not execute owner runtime"),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("failed route must not use legacy runtime"),
    )

    result = evaluator.evaluate_jobs(_jobs(2), owner_user_id="owner-route-fail")

    assert route_calls == [("owner-route-fail", "job_fit_evaluation")]
    assert result[0]["ai_fit_score"] == 8
    assert result[1]["ai_fit"] == "LLM_CALL_FAIL"
    assert evaluator.get_eval_cache_metrics() == {
        "eval_cache_hits": 1,
        "eval_cache_misses": 1,
        "eval_cache_stores": 0,
        "eval_cache_only_skips": 0,
        "eval_live_failures": 1,
    }
    assert all(
        not any(key.startswith("_eval_") for key in job)
        for job in result
    )


def test_owner_runtime_failure_has_no_legacy_or_provider_fallback(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    _install_owner_route(evaluator, monkeypatch)
    runtime_calls = []

    def fail(**kwargs):
        runtime_calls.append(kwargs)
        raise RuntimeError("bounded owner runtime failure")

    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        fail,
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("owner failure must not use legacy runtime"),
    )

    result = evaluator.evaluate_jobs(_jobs(1), owner_user_id="owner-fail")

    assert len(runtime_calls) == 1
    assert result[0]["ai_fit"] == "LLM_CALL_FAIL"
    assert evaluator.get_eval_cache_metrics()["eval_live_failures"] == 1


def test_owner_success_stores_frozen_routed_model(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(evaluator, "MODEL", "legacy-default-model")
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: None,
    )
    stores = []
    monkeypatch.setattr(
        evaluator,
        "store_cached_job_evaluation",
        lambda **kwargs: stores.append(kwargs),
    )
    _install_owner_route(
        evaluator,
        monkeypatch,
        provider="openai",
        model="gpt-5-mini",
    )
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: {"content": _response_for(_jobs(1))},
    )

    evaluator.evaluate_jobs(_jobs(1), owner_user_id="owner-store")

    assert len(stores) == 1
    assert stores[0]["model"] == "gpt-5-mini"
    assert stores[0]["model"] != evaluator.MODEL


def test_live_only_owner_bypasses_cache_and_resolves_once(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(evaluator, "EVAL_MODE", "live_only")
    route_calls = _install_owner_route(evaluator, monkeypatch)
    runtime_calls = []
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
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: (
            runtime_calls.append(kwargs)
            or {"content": _response_for(_jobs(1))}
        ),
    )

    result = evaluator.evaluate_jobs(_jobs(1), owner_user_id="owner-live-only")

    assert route_calls == [("owner-live-only", "job_fit_evaluation")]
    assert len(runtime_calls) == 1
    assert result[0]["ai_fit_score"] == 8


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


def test_job_fit_task_contract_fingerprint_is_unchanged():
    from src.evaluation.production_task_contract_fingerprints import (
        production_task_contract_sha256,
    )

    assert production_task_contract_sha256("job_fit_evaluation") == (
        "e9568a48240886579814a557b414461510f86485e3bb7a50efc3e7ab8e319480"
    )


def test_job_fit_owner_routing_has_no_direct_sdk_or_credential_boundary():
    source = Path("src/ai/job_fit_evaluator.py").read_text(encoding="utf-8")

    for forbidden in (
        "from groq import Groq",
        "from openai import OpenAI",
        "Groq(",
        "OpenAI(",
        "api_key",
        "get_user_provider_credential",
        "decrypt_user_provider",
    ):
        assert forbidden not in source

    assert "src.ai.user_provider_runtime" in source
    assert "resolve_effective_user_provider_route" in source
    assert "run_chat_completion(" in source


def test_run006_remains_absent():
    assert not any(
        path.name.lower().replace("_", "-").startswith("run-006")
        for path in Path(".").rglob("*")
    )
