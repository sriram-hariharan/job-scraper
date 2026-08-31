from __future__ import annotations

import contextlib
from copy import deepcopy
import importlib
import logging
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
    assert result["intelligent_jobs"][0]["intelligence"][
        "skill_extraction"
    ] == {
        "status": "success_nonempty",
        "failure_category": "",
        "failure_stage": "",
    }
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


def test_production_jd_empty_cache_hit_remains_successful_empty(
    monkeypatch,
):
    skill_enricher, job_intelligence = _production_modules(monkeypatch)
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: {
            "required_skills": [],
            "preferred_skills": [],
        },
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("cache hit must not call provider"),
    )
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **_kwargs: pytest.fail("cache hit must not write"),
    )

    intelligent_job = job_intelligence.build_job_intelligence(
        deepcopy(_jobs()[0])
    )

    assert intelligent_job["intelligence"]["skills"] == {
        "required": [],
        "preferred": [],
        "all": [],
    }
    assert intelligent_job["intelligence"]["skill_extraction"] == {
        "status": "success_empty",
        "failure_category": "",
        "failure_stage": "",
    }


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
    assert graph["intelligence"]["skill_extraction"] == {
        "status": "failure",
        "failure_category": "schema_or_parse",
        "failure_stage": "cache",
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
    assert graph["intelligence"]["skill_extraction"] == {
        "status": "failure",
        "failure_category": "unknown",
        "failure_stage": "execution",
    }
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
    assert graph["intelligence"]["skill_extraction"] == {
        "status": "failure",
        "failure_category": "schema_or_parse",
        "failure_stage": "response",
    }


def _skill_job_text() -> str:
    return (
        "Required Qualifications:\n- Python\n- SQL\n"
        "Responsibilities:\n"
        + ("Maintain reliable data quality and reporting workflows. " * 8)
        + "\n"
        "Preferred Qualifications:\n- Airflow"
    )


def _skill_response() -> str:
    return (
        '{"required_skills":["python","sql"],'
        '"preferred_skills":["airflow"]}'
    )


def _adjacent_skill_section_job_text() -> str:
    return (
        "Required Qualifications:\n"
        "- Python\n"
        "- SQL\n"
        "- Apache Spark\n\n"
        "Preferred Qualifications:\n"
        "- Airflow\n"
        "- Databricks"
    )


def test_skill_context_bucket_respects_adjacent_explicit_section_spans(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    job_text = _adjacent_skill_section_job_text()

    assert (
        skill_enricher._context_bucket_for_skill("python", job_text)
        == "required"
    )
    assert (
        skill_enricher._context_bucket_for_skill("sql", job_text)
        == "required"
    )
    assert (
        skill_enricher._context_bucket_for_skill("apache spark", job_text)
        == "required"
    )
    assert (
        skill_enricher._context_bucket_for_skill("airflow", job_text)
        == "preferred"
    )
    assert (
        skill_enricher._context_bucket_for_skill("databricks", job_text)
        == "preferred"
    )


def test_skill_context_reassignment_repairs_all_preferred_model_buckets(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)

    required, preferred = skill_enricher._reassign_skills_by_context(
        [],
        ["python", "sql", "apache spark", "airflow", "databricks"],
        _adjacent_skill_section_job_text(),
    )

    assert required == ["apache spark", "python", "sql"]
    assert preferred == ["airflow", "databricks"]


def test_skill_context_reassignment_prefers_required_for_duplicate_context(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    job_text = (
        "Required Qualifications:\n- Python\n\n"
        "Preferred Qualifications:\n- Python\n- Airflow"
    )

    required, preferred = skill_enricher._reassign_skills_by_context(
        [],
        ["python", "airflow"],
        job_text,
    )

    assert required == ["python"]
    assert preferred == ["airflow"]


@pytest.mark.parametrize(
    ("job_text", "expected"),
    [
        (
            "Required Qualifications:\n- Python\n- SQL\n"
            "Preferred Qualifications:\n- Airflow",
            {"python": "required", "sql": "required", "airflow": "preferred"},
        ),
        (
            "Required Qualifications:\n- Python\n- Kubernetes is a plus",
            {"python": "required", "kubernetes": "preferred"},
        ),
        (
            "Preferred Qualifications:\n- Databricks\n- Airflow",
            {"databricks": "preferred", "airflow": "preferred"},
        ),
        (
            "Required Qualifications:\n- Python\n\n"
            "Preferred Qualifications:\n- Python\n- Airflow",
            {"python": "required", "airflow": "preferred"},
        ),
        (
            "Required Qualifications:\n- Python\n"
            "Preferred Qualifications:\n- Airflow",
            {"python": "required"},
        ),
        (
            "Required Qualifications:\n- Python preferred",
            {"python": "preferred"},
        ),
    ],
)
def test_skill_context_bucket_boundaries_and_inline_preferred_override(
    monkeypatch,
    job_text,
    expected,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)

    assert {
        skill: skill_enricher._context_bucket_for_skill(skill, job_text)
        for skill in expected
    } == expected


def test_full_skill_finalization_repairs_all_preferred_model_buckets(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    provider_calls = []
    stores = []
    monkeypatch.delenv("JOB_STACK_OWNER_USER_ID", raising=False)
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )

    def provider(**kwargs):
        provider_calls.append(kwargs)
        return (
            '{"required_skills":[],"preferred_skills":['
            '"python","sql","apache spark","airflow","databricks"]}'
        )

    monkeypatch.setattr(skill_enricher, "run_chat_completion", provider)
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **kwargs: stores.append(kwargs),
    )

    result = skill_enricher.enrich_skills_with_llm(
        _adjacent_skill_section_job_text()
    )

    assert result == {
        "required_skills": ["apache spark", "python", "sql"],
        "preferred_skills": ["airflow", "databricks"],
        "extraction_status": "success_nonempty",
        "failure_category": "",
        "failure_stage": "",
    }
    assert len(provider_calls) == 1
    assert len(stores) == 1


def test_owner_skill_cache_hit_repairs_buckets_without_provider_or_store(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    cached = {
        "required_skills": [],
        "preferred_skills": [
            "python",
            "sql",
            "apache spark",
            "airflow",
            "databricks",
        ],
    }
    cache_keys = []
    stores = []
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda key: cache_keys.append(key) or cached,
    )
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **kwargs: stores.append(kwargs),
    )
    _forbid_owner_skill_execution(monkeypatch, skill_enricher)

    result = skill_enricher.enrich_skills_with_llm(
        _adjacent_skill_section_job_text(),
        owner_user_id="owner-a",
    )

    assert result is cached
    assert result == {
        "required_skills": ["apache spark", "python", "sql"],
        "preferred_skills": ["airflow", "databricks"],
        "extraction_status": "success_nonempty",
        "failure_category": "",
        "failure_stage": "",
    }
    assert cache_keys == [
        skill_enricher.build_skill_cache_key(
            _adjacent_skill_section_job_text()
        )
    ]
    assert stores == []
    assert skill_enricher.get_skill_cache_metrics() == {
        "cache_hits": 1,
        "cache_misses": 0,
        "cache_stores": 0,
        "cache_only_skips": 0,
        "live_failures": 0,
    }


def _forbid_owner_skill_execution(monkeypatch, skill_enricher):
    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        lambda *_args, **_kwargs: pytest.fail("route must not resolve"),
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("user runtime must not execute"),
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )


def test_owner_skill_cache_hit_returns_before_route_or_provider(monkeypatch):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    cached = {
        "required_skills": ["python", "sql"],
        "preferred_skills": ["airflow"],
    }
    cache_keys = []
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda key: cache_keys.append(key) or cached,
    )
    _forbid_owner_skill_execution(monkeypatch, skill_enricher)

    result = skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id="owner-a",
    )

    assert result is cached
    assert result["extraction_status"] == "success_nonempty"
    assert result["failure_category"] == ""
    assert result["failure_stage"] == ""
    assert cache_keys == [
        skill_enricher.build_skill_cache_key(_skill_job_text())
    ]
    assert skill_enricher.get_skill_cache_metrics() == {
        "cache_hits": 1,
        "cache_misses": 0,
        "cache_stores": 0,
        "cache_only_skips": 0,
        "live_failures": 0,
    }


def test_owner_empty_skill_cache_hit_is_successful_empty_without_provider(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    cached = {
        "required_skills": [],
        "preferred_skills": [],
    }
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: cached,
    )
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **_kwargs: pytest.fail("cache hit must not write"),
    )
    _forbid_owner_skill_execution(monkeypatch, skill_enricher)

    result = skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id="owner-a",
    )

    assert result is cached
    assert result == {
        "required_skills": [],
        "preferred_skills": [],
        "extraction_status": "success_empty",
        "failure_category": "",
        "failure_stage": "",
    }
    assert skill_enricher.get_skill_cache_metrics() == {
        "cache_hits": 1,
        "cache_misses": 0,
        "cache_stores": 0,
        "cache_only_skips": 0,
        "live_failures": 0,
    }


def test_owner_skill_cache_only_miss_stops_before_route_or_provider(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    monkeypatch.setattr(skill_enricher, "SKILL_EXTRACTION_MODE", "cache_only")
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )
    _forbid_owner_skill_execution(monkeypatch, skill_enricher)

    result = skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id="owner-a",
    )

    assert result == skill_enricher.get_empty_skill_result(
        failure_category="configuration",
        failure_stage="cache",
    )
    assert skill_enricher.get_skill_cache_metrics() == {
        "cache_hits": 0,
        "cache_misses": 1,
        "cache_stores": 0,
        "cache_only_skips": 1,
        "live_failures": 0,
    }


def test_owner_skill_live_miss_executes_exact_route_once_and_stores_model(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "environment-owner")
    cache_keys = []
    resolver_calls = []
    runtime_calls = []
    stores = []
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda key: cache_keys.append(key) or None,
    )
    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        lambda owner, workload: resolver_calls.append(
            (owner, workload)
        ) or {
            "provider": "openai",
            "model": "gpt-5-mini",
            "effective_selection_source": "user_override",
        },
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: runtime_calls.append(kwargs) or {
            "content": _skill_response(),
            "provider": "openai",
            "model": "gpt-5-mini",
            "fallback_used": False,
        },
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **kwargs: stores.append(kwargs),
    )
    expected_cache_key = skill_enricher.build_skill_cache_key(
        _skill_job_text()
    )

    result = skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id=" owner-a ",
    )

    assert resolver_calls == [("owner-a", "skill_extraction")]
    assert cache_keys == [expected_cache_key]
    assert len(runtime_calls) == 1
    call = runtime_calls[0]
    assert call["owner_user_id"] == "owner-a"
    assert call["provider"] == "openai"
    assert call["model"] == "gpt-5-mini"
    assert call["temperature"] == (
        skill_enricher.SKILL_EXTRACTION_TEMPERATURE
    )
    assert call["max_tokens"] == skill_enricher.SKILL_EXTRACTION_MAX_TOKENS
    assert "fallback_enabled" not in call
    assert result == {
        "required_skills": ["python", "sql"],
        "preferred_skills": ["airflow"],
        "extraction_status": "success_nonempty",
        "failure_category": "",
        "failure_stage": "",
    }
    assert stores == [
        {
            "cache_key": expected_cache_key,
            "model": "gpt-5-mini",
            "required_skills": ["python", "sql"],
            "preferred_skills": ["airflow"],
        }
    ]
    assert skill_enricher.get_skill_cache_metrics()["cache_stores"] == 1


def test_owner_skill_parse_retry_reuses_one_frozen_route(monkeypatch):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )
    resolver_calls = []
    runtime_calls = []
    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        lambda owner, workload: resolver_calls.append(
            (owner, workload)
        ) or {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
        },
    )

    def user_runtime(**kwargs):
        runtime_calls.append(kwargs)
        return {
            "content": (
                "not structured output"
                if len(runtime_calls) == 1
                else _skill_response()
            )
        }

    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        user_runtime,
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )
    stores = []
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **kwargs: stores.append(kwargs),
    )

    result = skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id="owner-a",
    )

    assert resolver_calls == [("owner-a", "skill_extraction")]
    assert len(runtime_calls) == 2
    assert {
        (call["owner_user_id"], call["provider"], call["model"])
        for call in runtime_calls
    } == {("owner-a", "groq", "openai/gpt-oss-20b")}
    assert runtime_calls[0]["messages"][1]["content"] != (
        runtime_calls[1]["messages"][1]["content"]
    )
    assert result["required_skills"] == ["python", "sql"]
    assert stores[0]["model"] == "openai/gpt-oss-20b"


def test_owner_skill_route_failure_is_bounded_and_increments_live_failure(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )
    resolver_calls = []

    def fail_route(owner, workload):
        resolver_calls.append((owner, workload))
        raise RuntimeError("secret registry and database detail")

    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        fail_route,
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("user runtime must not execute"),
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )

    result = skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id="owner-a",
    )

    assert resolver_calls == [("owner-a", "skill_extraction")]
    assert result == skill_enricher.get_empty_skill_result(
        failure_category="unknown",
        failure_stage="route",
    )
    assert skill_enricher.get_skill_cache_metrics()["live_failures"] == 1


def test_owner_skill_provider_failure_has_no_legacy_fallback(monkeypatch):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )
    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        lambda owner, workload: {
            "provider": "openai",
            "model": "gpt-5-mini",
        },
    )
    user_calls = []

    def fail_user_runtime(**kwargs):
        user_calls.append(kwargs)
        raise RuntimeError("provider secret detail")

    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        fail_user_runtime,
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("legacy fallback must not execute"),
    )

    result = skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id="owner-a",
    )

    assert len(user_calls) == 1
    assert result == skill_enricher.get_empty_skill_result(
        failure_category="unknown",
        failure_stage="execution",
    )
    assert skill_enricher.get_skill_cache_metrics()["live_failures"] == 1


def test_skill_owner_falls_back_to_existing_pipeline_environment(monkeypatch):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", " pipeline-owner ")
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )
    resolver_calls = []
    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        lambda owner, workload: resolver_calls.append(
            (owner, workload)
        ) or {
            "provider": "openai",
            "model": "gpt-5-mini",
        },
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: {"content": _skill_response()},
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **_kwargs: None,
    )

    result = skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id="   ",
    )

    assert resolver_calls == [("pipeline-owner", "skill_extraction")]
    assert result["required_skills"] == ["python", "sql"]


def test_blank_owner_skill_cache_miss_preserves_legacy_model_execution(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    monkeypatch.delenv("JOB_STACK_OWNER_USER_ID", raising=False)
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )
    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        lambda *_args, **_kwargs: pytest.fail("resolver must not execute"),
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("user runtime must not execute"),
    )
    legacy_calls = []
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **kwargs: legacy_calls.append(kwargs) or _skill_response(),
    )
    stores = []
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **kwargs: stores.append(kwargs),
    )

    result = skill_enricher.enrich_skills_with_llm(_skill_job_text())

    assert len(legacy_calls) == 1
    assert legacy_calls[0]["model"] == skill_enricher.MODEL
    assert result["required_skills"] == ["python", "sql"]
    assert stores[0]["model"] == skill_enricher.MODEL


def test_owner_skill_live_only_bypasses_cache_and_store(monkeypatch):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    monkeypatch.setattr(skill_enricher, "SKILL_EXTRACTION_MODE", "live_only")
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: pytest.fail("live_only must bypass cache read"),
    )
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **_kwargs: pytest.fail("live_only must bypass cache store"),
    )
    resolver_calls = []
    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        lambda owner, workload: resolver_calls.append(
            (owner, workload)
        ) or {
            "provider": "openai",
            "model": "gpt-5-mini",
        },
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: {"content": _skill_response()},
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )

    result = skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id="owner-a",
    )

    assert resolver_calls == [("owner-a", "skill_extraction")]
    assert result["preferred_skills"] == ["airflow"]
    assert skill_enricher.get_skill_cache_metrics() == {
        "cache_hits": 0,
        "cache_misses": 0,
        "cache_stores": 0,
        "cache_only_skips": 0,
        "live_failures": 0,
    }


def test_owner_skill_section_parser_remains_before_json_retry(monkeypatch):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )
    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        lambda owner, workload: {
            "provider": "openai",
            "model": "gpt-5-mini",
        },
    )
    calls = []
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: calls.append(kwargs) or {
            "content": (
                "REQUIRED SKILLS:\n- python\n- sql\n\n"
                "PREFERRED SKILLS:\n- airflow"
            )
        },
    )

    result = skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id="owner-a",
    )

    assert len(calls) == 1
    assert result == {
        "required_skills": ["python", "sql"],
        "preferred_skills": ["airflow"],
        "extraction_status": "success_nonempty",
        "failure_category": "",
        "failure_stage": "",
    }


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
    semantic = source.index(
        "evaluate_jobs_with_progress = _wrap_ai_evaluator_with_runtime_progress(",
        eligibility,
    )
    semantic_graph = source.index(
        "_maybe_execute_authoritative_semantic_evaluation_graph(",
        semantic,
    )
    evaluated_jobs_available = source.index(
        'logger.info(f"AI evaluated {len(ai_jobs)} jobs")',
        semantic_graph,
    )
    final_scoring = source.index(
        "_maybe_execute_authoritative_final_scoring_graph(jobs=ai_jobs)",
        evaluated_jobs_available,
    )

    assert (
        details
        < graph_call
        < eligibility
        < semantic
        < semantic_graph
        < evaluated_jobs_available
        < final_scoring
    )


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

    assert "from src.ai.job_fit_evaluator import evaluate_jobs" in source
    assert (
        "evaluate_jobs_with_progress = _wrap_ai_evaluator_with_runtime_progress("
        in source
    )
    assert "jobs=evaluable_jobs" in source
    assert "evaluate_jobs_func=evaluate_jobs_with_progress" in source
    assert source.count(
        "ai_jobs = evaluate_jobs_with_progress(evaluable_jobs)"
    ) == 1
    assert (
        'ai_jobs = semantic_evaluation_graph_result["evaluated_jobs"]'
        in source
    )
    assert "evaluate_jobs" not in graph_source
    assert "job_fit_evaluator" not in graph_source


def test_run006_remains_absent():
    assert not any(
        path.name.lower().replace("_", "-").startswith("run-006")
        for path in Path(".").rglob("*")
    )


# ---------------------------------------------------------------------------
# Bounded live skill-extraction failure diagnostics (observability only).
# ---------------------------------------------------------------------------


class _BoundedLogCapture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


@contextlib.contextmanager
def _captured_enricher_logs(skill_enricher):
    handler = _BoundedLogCapture()
    enricher_logger = skill_enricher.logger
    previous_level = enricher_logger.level
    enricher_logger.addHandler(handler)
    enricher_logger.setLevel(logging.DEBUG)
    try:
        yield handler.messages
    finally:
        enricher_logger.removeHandler(handler)
        enricher_logger.setLevel(previous_level)


_SANITIZED_TRANSPORT_FAILURE = (
    "LLM provider invocation failed "
    "(stage=primary, category=rate_limit, "
    "provider=groq, model=openai/gpt-oss-20b)"
)

_SECRET_MARKER = "VERY_SECRET_DIAGNOSTIC_VALUE"


class _InjectedConfigurationError(RuntimeError):
    """Mirrors UserProviderRuntimeConfigurationError's bounded .category."""

    def __init__(self, category: str, message: str) -> None:
        self.category = category
        super().__init__(message)


def _qualified_owner_route(monkeypatch, skill_enricher):
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )
    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        lambda _owner, _workload: {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
        },
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )


def _forbid_store(monkeypatch, skill_enricher):
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **_kwargs: pytest.fail("failed output must not be cached"),
    )


def _run_owner_failure(monkeypatch, skill_enricher, exc):
    calls = []

    def fail_user_runtime(**kwargs):
        calls.append(kwargs)
        raise exc

    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        fail_user_runtime,
    )
    with _captured_enricher_logs(skill_enricher) as messages:
        result = skill_enricher.enrich_skills_with_llm(
            _skill_job_text(),
            owner_user_id="owner-a",
        )
    return calls, result, messages


@pytest.mark.parametrize(
    "category",
    ["timeout", "rate_limit", "provider_5xx"],
)
def test_owner_execution_failure_preserves_bounded_outcome_metadata(
    monkeypatch,
    category,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    _qualified_owner_route(monkeypatch, skill_enricher)
    _forbid_store(monkeypatch, skill_enricher)

    calls, result, messages = _run_owner_failure(
        monkeypatch,
        skill_enricher,
        RuntimeError(
            "LLM provider invocation failed "
            f"(stage=primary, category={category}, "
            "provider=groq, model=openai/gpt-oss-20b)"
        ),
    )

    assert len(calls) == 1
    assert result["required_skills"] == []
    assert result["preferred_skills"] == []
    assert result["extraction_status"] == "failure"
    assert result["failure_category"] == category
    assert result["failure_stage"] == "execution"
    failure = next(
        message
        for message in messages
        if "LLM skill extraction owner execution failed" in message
    )
    assert f"category={category}" in failure


def test_skill_extraction_outcome_survives_intelligence_collector_and_corpus(
    monkeypatch,
):
    skill_enricher, job_intelligence = _production_modules(monkeypatch)
    from src.rag.job_document_builder import build_job_document

    monkeypatch.setattr(
        job_intelligence,
        "enrich_skills_with_llm",
        lambda _description: {
            "required_skills": [],
            "preferred_skills": [],
            "extraction_status": "failure",
            "failure_category": "timeout",
            "failure_stage": "execution",
        },
    )

    intelligent_job = job_intelligence.build_job_intelligence(
        deepcopy(_jobs()[0])
    )
    assert intelligent_job["intelligence"]["skills"] == {
        "required": [],
        "preferred": [],
        "all": [],
    }
    assert intelligent_job["intelligence"]["skill_extraction"] == {
        "status": "failure",
        "failure_category": "timeout",
        "failure_stage": "execution",
    }

    signals = collector._job_intelligence_skill_signals(intelligent_job)
    assert signals["skill_extraction_status"] == "failure"
    assert signals["skill_extraction_failure_category"] == "timeout"
    assert signals["skill_extraction_failure_stage"] == "execution"

    document = build_job_document(intelligent_job)
    assert document["required_skills"] == []
    assert document["preferred_skills"] == []
    assert document["all_skills"] == []
    assert document["skill_extraction_status"] == "failure"
    assert document["skill_extraction_failure_category"] == "timeout"
    assert document["skill_extraction_failure_stage"] == "execution"


def test_provider_secret_is_absent_from_intelligence_and_corpus_metadata(
    monkeypatch,
):
    skill_enricher, job_intelligence = _production_modules(monkeypatch)
    from src.rag.job_document_builder import build_job_document

    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "owner-a")
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )
    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        lambda _owner, _workload: {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
        },
    )

    def fail_with_secret(**_kwargs):
        raise RuntimeError(f"provider body {_SECRET_MARKER}")

    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        fail_with_secret,
    )
    _forbid_store(monkeypatch, skill_enricher)

    intelligent_job = job_intelligence.build_job_intelligence(
        deepcopy(_jobs()[0])
    )
    document = build_job_document(intelligent_job)

    assert intelligent_job["intelligence"]["skill_extraction"] == {
        "status": "failure",
        "failure_category": "unknown",
        "failure_stage": "execution",
    }
    assert _SECRET_MARKER not in str(intelligent_job["intelligence"])
    assert _SECRET_MARKER not in str(document)


def test_owner_execution_failure_preserves_calls_result_cache_and_metrics(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    _qualified_owner_route(monkeypatch, skill_enricher)
    _forbid_store(monkeypatch, skill_enricher)

    calls, result, _messages = _run_owner_failure(
        monkeypatch,
        skill_enricher,
        RuntimeError(_SANITIZED_TRANSPORT_FAILURE),
    )

    assert len(calls) == 1
    assert result == skill_enricher.get_empty_skill_result(
        failure_category="rate_limit",
        failure_stage="execution",
    )
    assert skill_enricher.get_skill_cache_metrics() == {
        "cache_hits": 0,
        "cache_misses": 1,
        "cache_stores": 0,
        "cache_only_skips": 0,
        "live_failures": 1,
    }


def test_owner_execution_failure_logs_bounded_transport_diagnostic(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    _qualified_owner_route(monkeypatch, skill_enricher)
    _forbid_store(monkeypatch, skill_enricher)

    _calls, _result, messages = _run_owner_failure(
        monkeypatch,
        skill_enricher,
        RuntimeError(_SANITIZED_TRANSPORT_FAILURE),
    )

    failures = [
        message
        for message in messages
        if "LLM skill extraction owner execution failed" in message
    ]
    assert len(failures) == 1
    failure = failures[0]
    assert "provider=groq" in failure
    assert "model=openai/gpt-oss-20b" in failure
    assert "category=rate_limit" in failure
    assert "stage=primary" in failure
    assert "error_type=RuntimeError" in failure


def test_owner_execution_failure_log_never_leaks_exception_message(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    _qualified_owner_route(monkeypatch, skill_enricher)
    _forbid_store(monkeypatch, skill_enricher)

    _calls, _result, messages = _run_owner_failure(
        monkeypatch,
        skill_enricher,
        RuntimeError(
            f"connection reset while calling provider: {_SECRET_MARKER}"
        ),
    )

    assert messages
    for message in messages:
        assert _SECRET_MARKER not in message
    failure = next(
        message
        for message in messages
        if "LLM skill extraction owner execution failed" in message
    )
    assert "category=unknown" in failure
    assert "stage=unknown" in failure
    assert "error_type=RuntimeError" in failure


def test_owner_execution_failure_reports_runtime_configuration_category(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    _qualified_owner_route(monkeypatch, skill_enricher)
    _forbid_store(monkeypatch, skill_enricher)

    _calls, result, messages = _run_owner_failure(
        monkeypatch,
        skill_enricher,
        _InjectedConfigurationError(
            "credential_not_configured",
            f"arbitrary runtime detail {_SECRET_MARKER}",
        ),
    )

    assert result == skill_enricher.get_empty_skill_result(
        failure_category="credential_not_configured",
        failure_stage="execution",
    )
    assert _SECRET_MARKER not in str(result)
    failure = next(
        message
        for message in messages
        if "LLM skill extraction owner execution failed" in message
    )
    assert "category=credential_not_configured" in failure
    assert "error_type=_InjectedConfigurationError" in failure
    for message in messages:
        assert _SECRET_MARKER not in message


def test_owner_route_failure_keeps_stable_prefix_and_bounded_fields(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    monkeypatch.setattr(
        skill_enricher,
        "get_cached_llm_skills",
        lambda _key: None,
    )

    def fail_route(_owner, _workload):
        raise _InjectedConfigurationError(
            "settings_unavailable",
            f"route detail {_SECRET_MARKER}",
        )

    monkeypatch.setattr(
        skill_enricher,
        "resolve_effective_user_provider_route",
        fail_route,
    )
    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("user runtime must not execute"),
    )
    _forbid_store(monkeypatch, skill_enricher)

    with _captured_enricher_logs(skill_enricher) as messages:
        result = skill_enricher.enrich_skills_with_llm(
            _skill_job_text(),
            owner_user_id="owner-a",
        )

    assert result == skill_enricher.get_empty_skill_result(
        failure_category="settings_unavailable",
        failure_stage="route",
    )
    assert result["failure_stage"] == "route"
    assert skill_enricher.get_skill_cache_metrics()["live_failures"] == 1
    route_message = next(
        message
        for message in messages
        if message.startswith("LLM skill extraction owner route unavailable")
    )
    assert "error_type=_InjectedConfigurationError" in route_message
    assert "category=settings_unavailable" in route_message
    for message in messages:
        assert _SECRET_MARKER not in message


def test_bounded_diagnostic_rejects_unknown_category_tokens(monkeypatch):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)

    diagnostic = skill_enricher._bounded_live_failure_diagnostic(
        RuntimeError("failed (stage=primary, category=totally_made_up)")
    )

    assert diagnostic == {
        "error_type": "RuntimeError",
        "category": "unknown",
        "stage": "primary",
    }


def _postfilter_job_text() -> str:
    return (
        "Required Qualifications:\n- Python\n"
        "Responsibilities:\n"
        + ("Maintain reliable reporting workflows in Python. " * 6)
    )


def _run_owner_success(monkeypatch, skill_enricher, job_text, content):
    stores = []
    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: {
            "content": content,
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "fallback_used": False,
        },
    )
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **kwargs: stores.append(kwargs),
    )
    with _captured_enricher_logs(skill_enricher) as messages:
        result = skill_enricher.enrich_skills_with_llm(
            job_text,
            owner_user_id="owner-a",
        )
    return result, stores, messages


def test_model_empty_extraction_logs_source_model_and_stays_cacheable(
    monkeypatch,
):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    _qualified_owner_route(monkeypatch, skill_enricher)

    result, stores, messages = _run_owner_success(
        monkeypatch,
        skill_enricher,
        _skill_job_text(),
        '{"required_skills":[],"preferred_skills":[]}',
    )

    assert result == {
        "required_skills": [],
        "preferred_skills": [],
        "extraction_status": "success_empty",
        "failure_category": "",
        "failure_stage": "",
    }
    assert stores == [
        {
            "cache_key": skill_enricher.build_skill_cache_key(
                _skill_job_text()
            ),
            "model": "openai/gpt-oss-20b",
            "required_skills": [],
            "preferred_skills": [],
        }
    ]
    assert skill_enricher.get_skill_cache_metrics()["cache_stores"] == 1
    assert (
        "LLM skill extraction finalized empty | source=model" in messages
    )
    assert (
        "LLM skill extraction finalized empty | source=postfilter"
        not in messages
    )


def test_postfilter_empty_extraction_logs_source_postfilter(monkeypatch):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    _qualified_owner_route(monkeypatch, skill_enricher)

    result, stores, messages = _run_owner_success(
        monkeypatch,
        skill_enricher,
        _postfilter_job_text(),
        '{"required_skills":["kubernetes"],"preferred_skills":[]}',
    )

    assert result == {
        "required_skills": [],
        "preferred_skills": [],
        "extraction_status": "success_empty",
        "failure_category": "",
        "failure_stage": "",
    }
    assert len(stores) == 1
    assert stores[0]["required_skills"] == []
    assert stores[0]["preferred_skills"] == []
    assert (
        "LLM skill extraction finalized empty | source=postfilter" in messages
    )
    assert (
        "LLM skill extraction finalized empty | source=model" not in messages
    )


def test_nonempty_extraction_logs_finalized_nonempty(monkeypatch):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    _qualified_owner_route(monkeypatch, skill_enricher)

    result, stores, messages = _run_owner_success(
        monkeypatch,
        skill_enricher,
        _skill_job_text(),
        _skill_response(),
    )

    assert result == {
        "required_skills": ["python", "sql"],
        "preferred_skills": ["airflow"],
        "extraction_status": "success_nonempty",
        "failure_category": "",
        "failure_stage": "",
    }
    assert stores == [
        {
            "cache_key": skill_enricher.build_skill_cache_key(
                _skill_job_text()
            ),
            "model": "openai/gpt-oss-20b",
            "required_skills": ["python", "sql"],
            "preferred_skills": ["airflow"],
        }
    ]
    assert "LLM skill extraction finalized nonempty" in messages
    assert not [
        message for message in messages if "finalized empty" in message
    ]


# ---------------------------------------------------------------------------
# Candidate low-reasoning skill_extraction task contract (offline only).
# ---------------------------------------------------------------------------


def test_candidate_skill_extraction_sends_zero_thinking_budget(monkeypatch):
    skill_enricher, _job_intelligence = _production_modules(monkeypatch)
    _qualified_owner_route(monkeypatch, skill_enricher)
    runtime_calls = []

    monkeypatch.setattr(
        skill_enricher,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: runtime_calls.append(kwargs) or {
            "content": _skill_response(),
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "fallback_used": False,
        },
    )
    monkeypatch.setattr(
        skill_enricher,
        "store_cached_llm_skills",
        lambda **_kwargs: None,
    )

    skill_enricher.enrich_skills_with_llm(
        _skill_job_text(),
        owner_user_id="owner-a",
    )

    assert len(runtime_calls) == 1
    call = runtime_calls[0]
    assert call["thinking_budget"] == 0
    assert call["thinking_budget"] == (
        skill_enricher.SKILL_EXTRACTION_THINKING_BUDGET
    )
    # Unchanged inference surface.
    assert call["max_tokens"] == 500
    assert call["temperature"] == 0
    assert call["provider"] == "groq"
    assert call["model"] == "openai/gpt-oss-20b"
    assert "fallback_enabled" not in call
    assert "reasoning_effort" not in call
    assert "response_mime_type" not in call


def test_existing_transport_maps_zero_budget_to_low_reasoning_effort():
    """The mapping stays owned by llm_client; the enricher must not duplicate it."""

    from src.ai import llm_client
    from src.ai import skill_llm_enricher

    captured = {}

    class _Client:
        def __init__(self):
            outer = self

            class _Completions:
                def create(self, **kwargs):
                    captured.update(kwargs)
                    raise _StopRequest()

            class _Chat:
                completions = _Completions()

            self.chat = _Chat()

    class _StopRequest(Exception):
        pass

    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    try:
        llm_client._run_groq_chat_completion(
            messages=messages,
            model="openai/gpt-oss-20b",
            temperature=skill_llm_enricher.SKILL_EXTRACTION_TEMPERATURE,
            max_tokens=skill_llm_enricher.SKILL_EXTRACTION_MAX_TOKENS,
            thinking_budget=skill_llm_enricher.SKILL_EXTRACTION_THINKING_BUDGET,
            provider_client=_Client(),
        )
    except _StopRequest:
        pass

    assert captured["reasoning_effort"] == "low"
    assert captured["include_reasoning"] is False
    assert captured["max_completion_tokens"] == 500
    assert captured["temperature"] == 0
    assert captured["model"] == "openai/gpt-oss-20b"
    assert "response_format" not in captured

    # The enricher may *document* the mapping, but must never construct the
    # provider SDK reasoning/token fields itself. Compare code only.
    enricher_code = "\n".join(
        line
        for line in Path(skill_llm_enricher.__file__)
        .read_text(encoding="utf-8")
        .splitlines()
        if not line.lstrip().startswith("#")
    )
    for provider_sdk_field in (
        "reasoning_effort",
        "include_reasoning",
        "max_completion_tokens",
    ):
        assert provider_sdk_field not in enricher_code


def test_candidate_contract_fingerprints_reasoning_and_context_versions():
    from src.evaluation import production_task_contract_fingerprints as fingerprints
    from src.ai import skill_llm_enricher

    material = (
        skill_llm_enricher
        .build_skill_extraction_production_task_contract_material()
    )
    assert material["task_parameters"] == {
        "temperature": 0,
        "max_tokens": 500,
        "thinking_budget": 0,
    }
    assert material["deterministic_transformation_contract"][
        "context_reassignment"
    ] == "section-bounded-context-v2"
    assert material["task_contract_version"] == "v6_postfilter_cleanup"

    candidate = fingerprints.production_task_contract_sha256("skill_extraction")
    frozen_tested = (
        "c7b9f541743b6967924583029036952b639c1f8117d00b68e152c24ac8405bb4"
    )
    assert candidate != frozen_tested


def test_candidate_contract_preserves_prompt_parser_and_retry_ordering():
    from src.ai import skill_llm_enricher

    source = Path(skill_llm_enricher.__file__).read_text(encoding="utf-8")
    assert "response = _call_live_llm(prompt)" in source
    assert "retry_response = _call_live_llm(retry_prompt)" in source
    assert "prompt = _build_skill_extraction_user_prompt(extraction_text)" in source
    assert "retry_prompt = _build_skill_extraction_retry_prompt(prompt)" in source
    assert source.index("extract_json_from_response(response)") < source.index(
        "_parse_sectioned_skill_response(response)"
    )
    assert source.index("_parse_sectioned_skill_response(response)") < source.index(
        "retry_response = _call_live_llm(retry_prompt)"
    )

    material = (
        skill_llm_enricher
        .build_skill_extraction_production_task_contract_material()
    )
    assert material["output_contract"]["parsers"] == [
        "json_object_extraction",
        "sectioned_skill_lists",
        "json_retry",
    ]


def test_frozen_qualification_authority_is_unchanged_by_candidate_contract():
    from src.evaluation import provider_model_recommendation_policy as policy

    frozen = policy._FROZEN_RECOMMENDATIONS["skill_extraction"]
    assert frozen["provider"] == "groq"
    assert frozen["model"] == "openai/gpt-oss-20b"
    assert frozen["task_contract_sha256"] == (
        "c7b9f541743b6967924583029036952b639c1f8117d00b68e152c24ac8405bb4"
    )
    assert frozen["evidence_sha256"] == (
        "09019474b9f0ae6cf383ae0fb638d489eda1303d4b5185aa9f5a6e850b570432"
    )
    assert frozen["review_sha256"] is None
