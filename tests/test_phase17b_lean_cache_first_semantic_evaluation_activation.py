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


def _invalid_response(case_name: str, batch: list[dict]) -> str:
    payload = json.loads(_response_for(batch))
    results = payload["results"]
    if case_name == "top_level_list":
        return json.dumps(results)
    if case_name == "missing_result":
        payload["results"] = results[:-1]
    elif case_name == "duplicate_id":
        results[-1]["id"] = results[0]["id"]
    elif case_name == "bool_id":
        results[0]["id"] = True
    elif case_name == "non_integer_id":
        results[0]["id"] = "0"
    elif case_name == "out_of_range_id":
        results[0]["id"] = len(batch)
    elif case_name == "missing_required_field":
        results[0].pop("reason")
    elif case_name == "malformed_results_type":
        payload["results"] = {"id": 0}
    elif case_name == "non_object_result":
        results[0] = "not-an-object"
    else:  # pragma: no cover - test data is fixed above.
        raise AssertionError(f"unknown invalid response case: {case_name}")
    return json.dumps(payload)


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


def test_parse_failure_gets_one_corrective_retry_without_backoff(monkeypatch):
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

    assert len(calls) == 2
    assert sleeps == []
    assert result[0]["ai_fit"] == "PARSE_ERROR"
    assert evaluator.get_eval_cache_metrics()["eval_live_failures"] == 1


@pytest.mark.parametrize(
    "case_name",
    (
        "top_level_list",
        "missing_result",
        "duplicate_id",
        "bool_id",
        "non_integer_id",
        "out_of_range_id",
        "missing_required_field",
        "malformed_results_type",
        "non_object_result",
    ),
)
def test_invalid_complete_batch_is_rejected_before_projection_or_cache(
    monkeypatch,
    case_name,
):
    evaluator = _evaluator(monkeypatch)
    jobs = _jobs(2)
    calls = []
    stores = []
    sleeps = []
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: None,
    )
    monkeypatch.setattr(
        evaluator,
        "store_cached_job_evaluation",
        lambda **kwargs: stores.append(kwargs),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: (
            calls.append(1) or _invalid_response(case_name, jobs)
        ),
    )
    monkeypatch.setattr(
        evaluator.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )

    result = evaluator.evaluate_jobs(jobs)

    assert calls == [1, 1]
    assert sleeps == []
    assert stores == []
    assert [job["ai_fit"] for job in result] == ["PARSE_ERROR", "PARSE_ERROR"]
    assert all("ai_fit_score" not in job for job in result)
    assert evaluator.get_eval_cache_metrics()["eval_cache_stores"] == 0
    assert evaluator.get_eval_cache_metrics()["eval_live_failures"] == 1


def test_parse_retry_recovery_projects_and_caches_only_valid_second_response(
    monkeypatch,
):
    evaluator = _evaluator(monkeypatch)
    jobs = _jobs(2)
    route_calls = _install_owner_route(evaluator, monkeypatch)
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: None,
    )
    stores = []
    runtime_calls = []
    responses = iter(("invalid", _response_for(jobs)))
    monkeypatch.setattr(
        evaluator,
        "store_cached_job_evaluation",
        lambda **kwargs: stores.append(kwargs),
    )

    def runtime(**kwargs):
        runtime_calls.append(kwargs)
        return {"content": next(responses)}

    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        runtime,
    )

    result = evaluator.evaluate_jobs(jobs, owner_user_id="owner-parse-recovery")

    assert route_calls == [("owner-parse-recovery", "job_fit_evaluation")]
    assert len(runtime_calls) == 2
    assert {
        (call["provider"], call["model"])
        for call in runtime_calls
    } == {("groq", "openai/gpt-oss-20b")}
    assert [job["ai_fit_score"] for job in result] == [8, 8]
    assert [store["evaluation"] for store in stores] == [
        _evaluation(0),
        _evaluation(1),
    ]
    assert evaluator.get_eval_cache_metrics()["eval_cache_stores"] == 2
    assert evaluator.get_eval_cache_metrics()["eval_live_failures"] == 0


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
    assert sleeps == [10, 20, 40, 80]
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
    assert len(runtime_calls) == 2
    assert {
        (call["provider"], call["model"])
        for call in runtime_calls
    } == {("groq", "openai/gpt-oss-20b")}
    assert sleeps == []
    assert result[0]["ai_fit"] == "PARSE_ERROR"
    assert evaluator.get_eval_cache_metrics()["eval_live_failures"] == 1


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
    assert sleeps == [10, 20, 40, 80]
    assert result[0]["ai_fit"] == "RATE_LIMIT_FAIL"
    assert evaluator.get_eval_cache_metrics()["eval_live_failures"] == 1


def test_provider_failure_category_matches_shared_allowlist_and_safe_sources(
    monkeypatch,
):
    evaluator = _evaluator(monkeypatch)
    from src.ai import llm_client

    class CategorizedFailure(RuntimeError):
        def __init__(self):
            self.error_category = "timeout"
            super().__init__("category=safety")

    assert evaluator._PROVIDER_FAILURE_CATEGORIES == frozenset(
        llm_client._PROVIDER_ERROR_CATEGORIES
    )
    assert evaluator._provider_failure_category(CategorizedFailure()) == "timeout"
    assert evaluator._provider_failure_category(
        RuntimeError("bounded failure (category=connection)")
    ) == "connection"
    assert evaluator._provider_failure_category(
        RuntimeError("private provider detail category=not_allowlisted")
    ) == "unknown"


@pytest.mark.parametrize("category", ("timeout", "connection", "provider_5xx"))
def test_transient_provider_failure_retries_once_then_fails_closed(
    monkeypatch,
    category,
):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    route_calls = _install_owner_route(evaluator, monkeypatch)
    runtime_calls = []
    sleeps = []

    def fail(**kwargs):
        runtime_calls.append(kwargs)
        raise RuntimeError(f"bounded failure (category={category})")

    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        fail,
    )
    monkeypatch.setattr(
        evaluator.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )

    result = evaluator.evaluate_jobs(
        _jobs(1),
        owner_user_id="owner-transient-terminal",
    )

    assert route_calls == [
        ("owner-transient-terminal", "job_fit_evaluation")
    ]
    assert len(runtime_calls) == 2
    assert sleeps == [10]
    assert result[0]["ai_fit"] == "LLM_CALL_FAIL"
    assert evaluator.get_eval_cache_metrics()["eval_live_failures"] == 1
    assert evaluator.get_eval_cache_metrics()["eval_cache_stores"] == 0


@pytest.mark.parametrize("category", ("timeout", "connection", "provider_5xx"))
def test_transient_provider_retry_can_recover_without_terminal_failure(
    monkeypatch,
    category,
):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: None,
    )
    stores = []
    calls = []
    sleeps = []
    monkeypatch.setattr(
        evaluator,
        "store_cached_job_evaluation",
        lambda **kwargs: stores.append(kwargs),
    )

    def recover(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError(f"bounded failure (category={category})")
        return {"content": _response_for(_jobs(1))}

    _install_owner_route(evaluator, monkeypatch)
    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        recover,
    )
    monkeypatch.setattr(
        evaluator.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )

    result = evaluator.evaluate_jobs(
        _jobs(1),
        owner_user_id="owner-transient-recovery",
    )

    assert len(calls) == 2
    assert sleeps == [10]
    assert result[0]["ai_fit_score"] == 8
    assert len(stores) == 1
    assert evaluator.get_eval_cache_metrics()["eval_live_failures"] == 0


@pytest.mark.parametrize(
    "category",
    (
        "authentication",
        "authorization",
        "configuration",
        "invalid_request",
        "provider_model_mismatch",
        "unsupported_provider",
        "schema_or_parse",
        "refusal_or_empty_content",
        "safety",
        "unknown",
    ),
)
def test_non_transient_provider_failure_does_not_retry_or_sleep(
    monkeypatch,
    category,
):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    _install_owner_route(evaluator, monkeypatch)
    calls = []
    sleeps = []

    def fail(**kwargs):
        calls.append(kwargs)
        raise RuntimeError(f"bounded failure (category={category})")

    monkeypatch.setattr(
        evaluator,
        "run_user_chat_completion_with_metadata",
        fail,
    )
    monkeypatch.setattr(
        evaluator.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )

    result = evaluator.evaluate_jobs(
        _jobs(1),
        owner_user_id="owner-non-transient",
    )

    assert len(calls) == 1
    assert sleeps == []
    assert result[0]["ai_fit"] == "LLM_CALL_FAIL"
    assert evaluator.get_eval_cache_metrics()["eval_live_failures"] == 1
    assert evaluator.get_eval_cache_metrics()["eval_cache_stores"] == 0


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


def test_progress_prepared_and_batch_counts_are_exact(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(evaluator, "BATCH_SIZE", 2)
    cached_values = iter([_evaluation(), None, None, None, None, None])
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: next(cached_values),
    )
    monkeypatch.setattr(
        evaluator,
        "store_cached_job_evaluation",
        lambda **_kwargs: None,
    )
    responses = iter(
        (
            _response_for(_jobs(2)),
            _response_for(_jobs(2)),
            _response_for(_jobs(1)),
        )
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: next(responses),
    )
    events = []

    result = evaluator.evaluate_jobs(_jobs(6), progress_callback=events.append)

    prepared = events[0]
    assert prepared == {
        "event": "prepared",
        "total_jobs": 6,
        "cache_hits": 1,
        "cache_misses": 5,
        "cache_only_skips": 0,
        "uncached_jobs": 5,
        "total_batches": 3,
        "completed_batches": 0,
        "failed_batches": 0,
        "processed_live_jobs": 0,
        "failed_live_jobs": 0,
    }
    batch_events = [
        event for event in events if event["event"] == "batch_completed"
    ]
    assert [event["completed_batches"] for event in batch_events] == [1, 2, 3]
    processed_counts = [event["processed_live_jobs"] for event in batch_events]
    assert processed_counts == sorted(processed_counts)
    assert sorted(
        current - previous
        for previous, current in zip([0, *processed_counts], processed_counts)
    ) == [1, 2, 2]
    assert processed_counts[-1] == 5
    assert [event["failed_batches"] for event in batch_events] == [0, 0, 0]
    assert events[-1] == {**batch_events[-1], "event": "completed"}
    assert len(result) == 6


def test_progress_all_cache_hits_has_zero_live_batches(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(
        evaluator,
        "get_cached_job_evaluation",
        lambda _key: _evaluation(),
    )
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("cache hits must not call provider"),
    )
    events = []

    result = evaluator.evaluate_jobs(_jobs(3), progress_callback=events.append)

    assert [event["event"] for event in events] == ["prepared", "completed"]
    assert events[0]["cache_hits"] == 3
    assert events[0]["cache_misses"] == 0
    assert events[0]["uncached_jobs"] == 0
    assert events[0]["total_batches"] == 0
    assert events[-1]["completed_batches"] == 0
    assert events[-1]["processed_live_jobs"] == 0
    assert len(result) == 3


def test_progress_cache_only_misses_are_terminal_without_live_batches(monkeypatch):
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
    events = []

    result = evaluator.evaluate_jobs(_jobs(2), progress_callback=events.append)

    assert [event["event"] for event in events] == ["prepared", "completed"]
    assert events[0]["cache_hits"] == 0
    assert events[0]["cache_misses"] == 2
    assert events[0]["cache_only_skips"] == 2
    assert events[0]["uncached_jobs"] == 0
    assert events[0]["total_batches"] == 0
    assert events[-1]["completed_batches"] == 0
    assert events[-1]["failed_live_jobs"] == 0
    assert [job["ai_fit"] for job in result] == [
        "EVAL_SKIPPED_CACHE_ONLY",
        "EVAL_SKIPPED_CACHE_ONLY",
    ]


def test_progress_counts_terminally_failed_batch_without_reprojection(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    monkeypatch.setattr(evaluator, "BATCH_SIZE", 2)
    _install_cache_miss(evaluator, monkeypatch)
    calls = []

    def provider(**_kwargs):
        calls.append(1)
        if len(calls) == 1:
            return _response_for(_jobs(2))
        raise RuntimeError("bounded non-transient failure")

    monkeypatch.setattr(evaluator, "run_chat_completion", provider)
    events = []

    result = evaluator.evaluate_jobs(_jobs(4), progress_callback=events.append)

    batch_events = [
        event for event in events if event["event"] == "batch_completed"
    ]
    assert [event["completed_batches"] for event in batch_events] == [1, 2]
    assert batch_events[-1]["processed_live_jobs"] == 2
    assert batch_events[-1]["failed_batches"] == 1
    assert batch_events[-1]["failed_live_jobs"] == 2
    assert events[-1]["event"] == "completed"
    assert events[-1]["completed_batches"] == events[-1]["total_batches"] == 2
    assert [job.get("ai_fit") for job in result[2:]] == [
        "LLM_CALL_FAIL",
        "LLM_CALL_FAIL",
    ]


def test_malformed_corrective_retry_emits_bounded_event(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: "private malformed response text",
    )
    events = []

    evaluator.evaluate_jobs(_jobs(1), progress_callback=events.append)

    retries = [event for event in events if event["event"] == "retry"]
    assert retries == [
        {
            "event": "retry",
            "category": "malformed_response",
            "attempt": 2,
            "maximum_attempts": 2,
            "delay_seconds": 0,
            "batch_ordinal": 1,
            "total_batches": 1,
        }
    ]
    assert "private malformed response text" not in json.dumps(retries)


def test_rate_limit_progress_preserves_attempts_wait_and_heartbeats(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    calls = []
    sleeps = []

    def rate_limited(**_kwargs):
        calls.append(1)
        raise RuntimeError("429 private-token-never-emit")

    monkeypatch.setattr(evaluator, "run_chat_completion", rate_limited)
    monkeypatch.setattr(
        evaluator.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )
    events = []

    result = evaluator.evaluate_jobs(_jobs(1), progress_callback=events.append)

    retries = [event for event in events if event["event"] == "retry"]
    initial_retries = [event for event in retries if not event.get("heartbeat")]
    assert [event["category"] for event in initial_retries] == [
        "rate_limit",
        "rate_limit",
        "rate_limit",
        "rate_limit",
    ]
    assert [event["attempt"] for event in initial_retries] == [2, 3, 4, 5]
    assert [event["delay_seconds"] for event in initial_retries] == [10, 20, 40, 80]
    assert sum(sleeps) == 150
    assert max(sleeps) == evaluator._PROGRESS_HEARTBEAT_INTERVAL_SECONDS
    assert len([event for event in retries if event.get("heartbeat")]) == 4
    assert len(calls) == 5
    assert result[0]["ai_fit"] == "RATE_LIMIT_FAIL"
    assert "private-token-never-emit" not in json.dumps(retries)


def test_transient_retry_progress_uses_safe_category(monkeypatch):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    calls = []
    sleeps = []

    def recover(**_kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("private detail category=timeout")
        return _response_for(_jobs(1))

    monkeypatch.setattr(evaluator, "run_chat_completion", recover)
    monkeypatch.setattr(
        evaluator.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )
    events = []

    result = evaluator.evaluate_jobs(_jobs(1), progress_callback=events.append)

    retry = next(event for event in events if event["event"] == "retry")
    assert retry["category"] == "timeout"
    assert retry["attempt"] == retry["maximum_attempts"] == 2
    assert retry["delay_seconds"] == 10
    assert sleeps == [10]
    assert len(calls) == 2
    assert result[0]["ai_fit_score"] == 8
    assert "private detail" not in json.dumps(events)


def test_progress_callback_failure_and_payload_mutation_cannot_change_output(
    monkeypatch,
):
    evaluator = _evaluator(monkeypatch)
    _install_cache_miss(evaluator, monkeypatch)
    monkeypatch.setattr(
        evaluator,
        "run_chat_completion",
        lambda **_kwargs: _response_for(_jobs(1)),
    )
    callback_calls = []

    def broken_callback(payload):
        callback_calls.append(dict(payload))
        payload["total_jobs"] = 999999
        raise RuntimeError("status persistence unavailable")

    with_callback = evaluator.evaluate_jobs(
        _jobs(1),
        progress_callback=broken_callback,
    )
    without_callback = evaluator.evaluate_jobs(_jobs(1))

    assert callback_calls
    assert with_callback == without_callback
    assert with_callback[0]["job_id"] == "job-0"
    assert with_callback[0]["ai_fit_score"] == 8


def test_collector_progress_adapter_emits_only_safe_message_and_counts():
    updates = []
    progress = {
        "event": "batch_completed",
        "total_jobs": 6,
        "cache_hits": 1,
        "cache_misses": 5,
        "cache_only_skips": 0,
        "uncached_jobs": 5,
        "total_batches": 3,
        "completed_batches": 2,
        "failed_batches": 1,
        "processed_live_jobs": 3,
        "failed_live_jobs": 1,
        "owner_user_id": "owner-secret",
        "provider": "provider-secret",
        "api_key": "credential-secret",
        "raw_exception": "raw-secret",
    }

    collector._update_ai_evaluation_runtime_progress(
        progress,
        status_updater=lambda message, counts=None: updates.append(
            (message, counts)
        ),
    )

    message, counts = updates[0]
    assert message == (
        "AI Evaluation: 2/3 live batches complete | 1 cached | "
        "3/5 live jobs processed | 1 failed"
    )
    assert counts == {
        "ai_evaluation_total_jobs": 6,
        "ai_evaluation_cache_hits": 1,
        "ai_evaluation_cache_misses": 5,
        "ai_evaluation_cache_only_skips": 0,
        "ai_evaluation_uncached_jobs": 5,
        "ai_evaluation_total_batches": 3,
        "ai_evaluation_completed_batches": 2,
        "ai_evaluation_failed_batches": 1,
        "ai_evaluation_processed_live_jobs": 3,
        "ai_evaluation_failed_live_jobs": 1,
    }
    serialized = json.dumps(updates)
    for secret in ("owner-secret", "provider-secret", "credential-secret", "raw-secret"):
        assert secret not in serialized


def test_collector_progress_adapter_persists_message_counts_and_updated_at(
    monkeypatch,
    tmp_path,
):
    from src.pipeline import runtime_status

    status_path = tmp_path / "status.json"
    monkeypatch.setenv(runtime_status.ENV_STATUS_PATH, str(status_path))
    monkeypatch.setenv(runtime_status.ENV_RUN_ID, "run-lr2c")
    timestamps = iter(
        [
            "2026-08-21T10:00:00+00:00",
            "2026-08-21T10:00:01+00:00",
            "2026-08-21T10:00:02+00:00",
            "2026-08-21T10:00:20+00:00",
        ]
    )
    monkeypatch.setattr(runtime_status, "_utc_now", lambda: next(timestamps))
    runtime_status.initialize_run(
        output_dir=str(tmp_path),
        log_path=str(tmp_path / "run.log"),
        status_path=str(status_path),
        planning_only=False,
        job_limit=10,
        job_packet_limit=0,
        llm_actions=[],
        generate_tailoring=False,
        generate_llm_tailoring=False,
        refresh_llm_tailoring=False,
        generate_llm_fallback=False,
        generate_llm_adjudication=False,
        delete_seen_data="no",
    )

    collector._update_ai_evaluation_runtime_progress(
        {
            "event": "completed",
            "total_jobs": 2,
            "cache_hits": 1,
            "cache_misses": 1,
            "cache_only_skips": 0,
            "uncached_jobs": 1,
            "total_batches": 1,
            "completed_batches": 1,
            "failed_batches": 0,
            "processed_live_jobs": 1,
            "failed_live_jobs": 0,
        },
        status_updater=runtime_status.update_stage_message,
    )

    payload = json.loads(status_path.read_text(encoding="utf-8"))
    assert payload["status"] == "running"
    assert payload["stage_message"] == (
        "AI Evaluation: 1/1 live batches complete | 1 cached | "
        "1/1 live jobs processed"
    )
    assert payload["counts"]["ai_evaluation_completed_batches"] == 1
    assert payload["updated_at_utc"] == "2026-08-21T10:00:20+00:00"


def test_wrapped_evaluator_has_direct_and_graph_invocation_parity():
    callback_events = []
    invocations = []

    def owner(jobs, progress_callback=None):
        invocations.append(progress_callback)
        progress_callback({"event": "prepared", "total_jobs": len(jobs)})
        return _fake_owner(jobs)

    wrapped = collector._wrap_ai_evaluator_with_runtime_progress(
        owner,
        progress_callback=callback_events.append,
    )
    direct = wrapped(_jobs())
    graph_result = _graph(_jobs(), owner=wrapped)

    assert graph_result["execution_metadata"]["invocation_count"] == 1
    assert graph_result["evaluated_jobs"] == direct
    assert invocations == [callback_events.append, callback_events.append]
    assert callback_events == [
        {"event": "prepared", "total_jobs": 2},
        {"event": "prepared", "total_jobs": 2},
    ]


def test_wrapped_legacy_evaluator_is_invoked_once_without_typeerror_fallback():
    invocations = []

    def legacy_owner(jobs):
        invocations.append(list(jobs))
        return _fake_owner(jobs)

    wrapped = collector._wrap_ai_evaluator_with_runtime_progress(legacy_owner)
    result = wrapped(_jobs(1))

    assert len(invocations) == 1
    assert result[0]["ai_fit_score"] == 8


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
        "ai_jobs = evaluate_jobs_with_progress(evaluable_jobs)",
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
    assert "evaluate_jobs_func=evaluate_jobs_with_progress" in source[
        graph_call:direct
    ]
    assert "update_stage_message" in source
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
