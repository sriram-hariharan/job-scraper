from __future__ import annotations

from copy import deepcopy
import importlib
from pathlib import Path
import sys
import types

import pytest

from src.agents import jd_intelligence_authoritative_graph as graph_owner
from src.pipeline import collector


GRAPH_MODULE = "src.agents.jd_intelligence_authoritative_graph"
GATE = "APPLYLENS_AUTHORITATIVE_JD_INTELLIGENCE_LANGGRAPH_ENABLED"


def _jobs() -> list[dict]:
    return [
        {
            "job_id": "job-1",
            "company": "Example One",
            "title": "Data Engineer",
            "description_text": (
                "Required Qualifications:\n- Python\n- SQL\n"
                "Preferred Qualifications:\n- Airflow"
            ),
            "metadata": {"source_order": 1},
        },
        {
            "job_id": "job-2",
            "company": "Example Two",
            "title": "Machine Learning Engineer",
            "description_text": "Required Python and PyTorch.",
            "metadata": {"source_order": 2},
        },
    ]


def _fake_owner(job: dict) -> dict:
    output = deepcopy(job)
    output["intelligence"] = {
        "skills": {
            "required": ["python"],
            "preferred": ["sql"],
            "all": ["python", "sql"],
        },
        "visa_sponsorship": "unknown",
    }
    output["role_family"] = "data_engineering"
    return output


def _graph(
    jobs: list[dict],
    *,
    owner=_fake_owner,
) -> dict:
    return graph_owner.execute_authoritative_jd_intelligence_graph(
        jobs=jobs,
        build_job_intelligence_func=owner,
        pipeline_run_id="run-phase17a",
        owner_user_id="owner-phase17a",
        context_id="context-phase17a",
    )


def _production_modules(monkeypatch):
    import dotenv

    monkeypatch.setattr(
        dotenv,
        "load_dotenv",
        lambda *_args, **_kwargs: False,
    )
    skill_enricher = importlib.import_module("src.ai.skill_llm_enricher")
    job_intelligence = importlib.import_module(
        "src.intelligence.job_intelligence"
    )
    monkeypatch.setattr(
        job_intelligence,
        "SKILL_EXTRACTION_BACKEND",
        "groq_first",
    )
    monkeypatch.setattr(
        skill_enricher,
        "SKILL_EXTRACTION_MODE",
        "cache_prefer_live",
    )
    skill_enricher.reset_skill_cache_metrics()
    return skill_enricher, job_intelligence


def test_exact_graph_and_state_versions():
    assert (
        graph_owner.AUTHORITATIVE_JD_INTELLIGENCE_GRAPH_VERSION
        == "authoritative-jd-intelligence-graph-v1"
    )
    assert (
        graph_owner.AUTHORITATIVE_JD_INTELLIGENCE_STATE_VERSION
        == "authoritative-jd-intelligence-state-v1"
    )


def test_real_state_graph_has_one_production_node():
    graph = graph_owner.build_authoritative_jd_intelligence_graph(
        build_job_intelligence_func=_fake_owner
    )

    assert type(graph).__name__ == "StateGraph"
    assert set(graph.nodes) == {"jd_intelligence"}
    assert graph_owner.AUTHORITATIVE_JD_INTELLIGENCE_PRODUCTION_NODE_COUNT == 1


def test_graph_order_is_start_jd_intelligence_end():
    graph = graph_owner.build_authoritative_jd_intelligence_graph(
        build_job_intelligence_func=_fake_owner
    )

    assert graph.edges == {
        ("__start__", "jd_intelligence"),
        ("jd_intelligence", "__end__"),
    }


def test_activation_gate_defaults_off():
    for value in (None, "", "0", "false", "no", "off"):
        env = {} if value is None else {GATE: value}
        assert (
            collector._authoritative_jd_intelligence_langgraph_enabled(env)
            is False
        )


def test_activation_gate_uses_existing_truthy_convention():
    for value in ("1", "true", "TRUE", "yes", "on"):
        assert (
            collector._authoritative_jd_intelligence_langgraph_enabled(
                {GATE: value}
            )
            is True
        )


def test_gate_off_does_not_import_or_construct_graph(monkeypatch):
    monkeypatch.delitem(sys.modules, GRAPH_MODULE, raising=False)

    result = collector._maybe_execute_authoritative_jd_intelligence_graph(
        jobs=_jobs(),
        build_job_intelligence_func=_fake_owner,
        env={},
    )

    assert result is None
    assert GRAPH_MODULE not in sys.modules


def test_gate_on_lazily_imports_and_forwards_owner_and_context(monkeypatch):
    captured = {}

    def execute(**kwargs):
        captured.update(kwargs)
        return {
            "intelligent_jobs": [],
            "execution_metadata": {
                "execution_mode": "langgraph",
                "production_node_count": 1,
                "node_invocation_count": 1,
                "jd_owner_invocation_count": len(kwargs["jobs"]),
                "status": "completed",
            },
        }

    monkeypatch.setitem(
        sys.modules,
        GRAPH_MODULE,
        types.SimpleNamespace(
            execute_authoritative_jd_intelligence_graph=execute
        ),
    )
    result = collector._maybe_execute_authoritative_jd_intelligence_graph(
        jobs=_jobs(),
        build_job_intelligence_func=_fake_owner,
        env={
            GATE: "1",
            "JOB_APP_PIPELINE_RUN_ID": "run-17a",
            "JOB_STACK_OWNER_USER_ID": "owner-17a",
            "APPLYLENS_AGENT_CONTEXT_ID": "context-17a",
        },
    )

    assert result is not None
    assert captured["build_job_intelligence_func"] is _fake_owner
    assert captured["pipeline_run_id"] == "run-17a"
    assert captured["owner_user_id"] == "owner-17a"
    assert captured["context_id"] == "context-17a"


def test_direct_and_graph_outputs_are_identical():
    jobs = _jobs()
    direct = [_fake_owner(deepcopy(job)) for job in jobs]

    assert _graph(jobs)["intelligent_jobs"] == direct


def test_output_order_is_unchanged():
    result = _graph(_jobs())["intelligent_jobs"]

    assert [job["job_id"] for job in result] == ["job-1", "job-2"]


def test_structured_output_fields_are_unchanged():
    direct = [_fake_owner(job) for job in _jobs()]
    graph = _graph(_jobs())["intelligent_jobs"]

    assert [set(job) for job in graph] == [set(job) for job in direct]
    assert [job["intelligence"] for job in graph] == [
        job["intelligence"] for job in direct
    ]


def test_owner_executes_exactly_once_per_job():
    calls = []

    def counted_owner(job):
        calls.append(job["job_id"])
        return _fake_owner(job)

    result = _graph(_jobs(), owner=counted_owner)

    assert calls == ["job-1", "job-2"]
    assert result["execution_metadata"]["jd_owner_invocation_count"] == 2


def test_caller_jobs_remain_unchanged():
    jobs = _jobs()
    before = deepcopy(jobs)

    _graph(jobs)

    assert jobs == before


def test_deep_copy_contains_existing_owner_mutation():
    jobs = _jobs()
    before = deepcopy(jobs)

    def mutating_owner(job):
        job["metadata"]["owner_mutated_copy"] = True
        return job

    result = _graph(jobs, owner=mutating_owner)

    assert jobs == before
    assert result["intelligent_jobs"][0]["metadata"][
        "owner_mutated_copy"
    ] is True


def test_empty_input_calls_owner_zero_times():
    calls = []

    result = _graph([], owner=lambda job: calls.append(job))

    assert result["intelligent_jobs"] == []
    assert result["execution_metadata"]["jd_owner_invocation_count"] == 0
    assert calls == []


def test_owner_failure_propagates_without_direct_fallback():
    calls = []

    def failing_owner(_job):
        calls.append(1)
        raise RuntimeError("jd_owner_failed")

    with pytest.raises(RuntimeError, match="jd_owner_failed"):
        _graph(_jobs(), owner=failing_owner)

    assert calls == [1]


def test_malformed_owner_output_fails_closed():
    with pytest.raises(
        TypeError,
        match="authoritative_jd_intelligence_owner_output_0_must_be_mapping",
    ):
        _graph(_jobs(), owner=lambda _job: "invalid")


def test_malformed_input_fails_closed():
    with pytest.raises(
        TypeError,
        match="authoritative_jd_intelligence_detailed_jobs_0_must_be_mapping",
    ):
        graph_owner.execute_authoritative_jd_intelligence_graph(
            jobs=["invalid"],
            build_job_intelligence_func=_fake_owner,
        )


def test_execution_metadata_is_bounded_and_contains_no_job_rows():
    metadata = _graph(_jobs())["execution_metadata"]

    assert metadata["node_order"] == ["jd_intelligence"]
    assert 0 <= metadata["node_latency_ms"] <= 300_000
    assert metadata["owner_managed_cache_first"] is True
    assert metadata["provider_calls_conditionally_allowed"] is True
    assert metadata["graph_persistence_authority"] is False
    assert metadata["mutation_authority"] is False
    assert metadata["application_authority"] is False
    assert metadata["ats_authority"] is False
    assert "jobs" not in metadata
    assert "description" not in metadata


def test_graph_owner_adds_no_provider_cache_dotenv_or_action_boundary():
    source = Path(
        "src/agents/jd_intelligence_authoritative_graph.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "llm_client",
        "run_chat_completion",
        "skill_corpus_store",
        "get_cached_llm_skills",
        "store_cached_llm_skills",
        "dotenv",
        "api_key",
        "connect(",
        "subprocess",
        "submit_application",
        "mark_applied",
        "ats_submission",
    )

    for token in forbidden:
        assert token not in source


def test_production_jd_cache_hit_makes_zero_provider_and_cache_write_calls(
    monkeypatch,
):
    skill_enricher, job_intelligence = _production_modules(monkeypatch)
    provider_calls = []
    stores = []
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: {
            "required_skills": ["python", "sql"],
            "preferred_skills": ["airflow"],
        },
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **kwargs: provider_calls.append(kwargs),
    )
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **kwargs: stores.append(kwargs),
    )

    result = _graph(
        [_jobs()[0]],
        owner=job_intelligence.build_job_intelligence,
    )

    assert set(
        result["intelligent_jobs"][0]["intelligence"]["skills"]["all"]
    ) == {"python", "sql", "airflow"}
    assert provider_calls == []
    assert stores == []
    assert skill_enricher.get_skill_cache_metrics()["cache_hits"] == 1


def test_production_jd_cache_miss_uses_one_injected_provider_and_one_store(
    monkeypatch,
):
    skill_enricher, job_intelligence = _production_modules(monkeypatch)
    provider_calls = []
    stores = []
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )

    def provider(**kwargs):
        provider_calls.append(kwargs)
        return (
            '{"required_skills":["python","sql"],'
            '"preferred_skills":["airflow"]}'
        )

    monkeypatch.setattr(skill_enricher, "run_chat_completion", provider)
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **kwargs: stores.append(kwargs),
    )

    result = _graph(
        [_jobs()[0]],
        owner=job_intelligence.build_job_intelligence,
    )

    assert set(
        result["intelligent_jobs"][0]["intelligence"]["skills"]["all"]
    ) == {"python", "sql", "airflow"}
    assert len(provider_calls) == 1
    assert len(stores) == 1
    metrics = skill_enricher.get_skill_cache_metrics()
    assert metrics["cache_misses"] == 1
    assert metrics["cache_stores"] == 1


def test_production_malformed_cached_shape_preserves_existing_empty_recovery(
    monkeypatch,
):
    skill_enricher, job_intelligence = _production_modules(monkeypatch)
    provider_calls = []
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: {"unexpected": "bounded malformed cache value"},
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **kwargs: provider_calls.append(kwargs),
    )

    direct_input = deepcopy(_jobs()[0])
    direct = job_intelligence.build_job_intelligence(direct_input)
    graph = _graph(
        [_jobs()[0]],
        owner=job_intelligence.build_job_intelligence,
    )["intelligent_jobs"][0]

    assert graph == direct
    assert graph["intelligence"]["skills"] == {
        "required": [],
        "preferred": [],
        "all": [],
    }
    assert provider_calls == []


def test_production_provider_failure_preserves_existing_empty_fallback(
    monkeypatch,
):
    skill_enricher, job_intelligence = _production_modules(monkeypatch)
    calls = []
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )

    def fail_provider(**_kwargs):
        calls.append(1)
        raise RuntimeError("bounded injected provider failure")

    monkeypatch.setattr(skill_enricher, "run_chat_completion", fail_provider)
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **_kwargs: pytest.fail("failed output must not be cached"),
    )

    graph = _graph(
        [_jobs()[0]],
        owner=job_intelligence.build_job_intelligence,
    )["intelligent_jobs"][0]

    assert calls == [1]
    assert graph["intelligence"]["skills"]["all"] == []
    assert skill_enricher.get_skill_cache_metrics()["live_failures"] == 1


def test_production_structured_validation_failure_uses_existing_parse_retry(
    monkeypatch,
):
    skill_enricher, job_intelligence = _production_modules(monkeypatch)
    calls = []
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )

    def malformed_provider(**_kwargs):
        calls.append(1)
        return "not structured output"

    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        malformed_provider,
    )
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **_kwargs: pytest.fail("invalid output must not be cached"),
    )

    graph = _graph(
        [_jobs()[0]],
        owner=job_intelligence.build_job_intelligence,
    )["intelligent_jobs"][0]

    assert calls == [1, 1]
    assert graph["intelligence"]["skills"]["all"] == []


def test_collector_preserves_details_jd_filter_semantic_and_scoring_order():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    details = source.index("detailed_jobs = enrich_job_details(new_jobs)")
    graph_call = source.index(
        "_maybe_execute_authoritative_jd_intelligence_graph(",
        source.index('section("JOB INTELLIGENCE", logger)'),
    )
    eligibility = source.index(
        "evaluable_jobs = filter_jobs_for_ai_evaluation(intelligent_jobs)"
    )
    semantic = source.index("ai_jobs = evaluate_jobs(evaluable_jobs)")
    final_scoring = source.index(
        "_maybe_execute_authoritative_final_scoring_graph(jobs=ai_jobs)"
    )

    assert details < graph_call < eligibility < semantic < final_scoring


def test_gate_off_collector_path_keeps_direct_jd_owner_call():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    graph_call = source.index(
        "_maybe_execute_authoritative_jd_intelligence_graph(",
        source.index('section("JOB INTELLIGENCE", logger)'),
    )
    direct_branch = source.index(
        "if jd_intelligence_graph_result is None:",
        graph_call,
    )
    direct_owner = source.index(
        "build_job_intelligence(job) for job in detailed_jobs",
        direct_branch,
    )

    assert graph_call < direct_branch < direct_owner


def test_existing_controlled_jd_gate_retains_precedence():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    stage = source.index('section("JOB INTELLIGENCE", logger)')
    controlled = source.index(
        "if _truthy_env_value(os.environ.get(JD_INTELLIGENCE_CONTROLLED_LLM_FLAG)):",
        stage,
    )
    graph_call = source.index(
        "_maybe_execute_authoritative_jd_intelligence_graph(",
        controlled,
    )

    assert controlled < graph_call


def test_semantic_evaluation_remains_at_existing_filtered_caller():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    graph_source = Path(
        "src/agents/jd_intelligence_authoritative_graph.py"
    ).read_text(encoding="utf-8")

    assert "ai_jobs = evaluate_jobs(evaluable_jobs)" in source
    assert "evaluate_jobs" not in graph_source
    assert "job_fit_evaluator" not in graph_source


def test_run006_remains_absent():
    assert not any(
        path.name.lower().replace("_", "-").startswith("run-006")
        for path in Path(".").rglob("*")
    )
