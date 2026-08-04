from __future__ import annotations

from copy import deepcopy
import importlib
from pathlib import Path
import sys
import types

import pytest

from src.agents import (
    deterministic_prefilter_dedupe_authoritative_graph as graph_owner,
)
from src.pipeline import collector, dedupe, job_filter


GRAPH_MODULE = (
    "src.agents.deterministic_prefilter_dedupe_authoritative_graph"
)
GATE = "APPLYLENS_AUTHORITATIVE_PREFILTER_DEDUPE_LANGGRAPH_ENABLED"
FUTURE_POSTED_AT = "2099-01-01T00:00:00Z"


def _job(
    job_id: str,
    *,
    company: str = "Acme",
    title: str = "Data Scientist",
    location: str = "New York, NY",
    source: str = "greenhouse",
    url: str | None = None,
) -> dict:
    return {
        "job_id": job_id,
        "company": company,
        "title": title,
        "location": location,
        "source": source,
        "posted_at": FUTURE_POSTED_AT,
        "url": url or f"https://jobs.example/{job_id}",
        "metadata": {"source_rank": int(job_id) if job_id.isdigit() else 0},
    }


def _jobs() -> list[dict]:
    return [
        _job("1"),
        _job("2"),
        _job("3", company="Beta", title="Machine Learning Engineer"),
        _job("4", company="Gamma", title="Accountant"),
    ]


def _direct(
    jobs: list[dict],
    *,
    selected_role_families: list[str] | None = None,
    excluded_keywords: list[str] | None = None,
    audit_enabled: bool = False,
    target_seniority: list[str] | None = None,
    seniority_strict_match: bool = False,
) -> dict:
    audit_rows = [] if audit_enabled else None
    filtered_jobs, diagnostics = job_filter.filter_jobs(
        deepcopy(jobs),
        selected_role_families=selected_role_families,
        target_seniority=target_seniority,
        seniority_strict_match=seniority_strict_match,
        filter_mode="strict_live",
        return_diagnostics=True,
        role_title_audit_rows=audit_rows,
        excluded_keywords=list(excluded_keywords or []),
    )
    return {
        "filtered_jobs": deepcopy(filtered_jobs),
        "filter_diagnostics": dict(diagnostics),
        "role_title_audit_rows": deepcopy(audit_rows or []),
        "deduplicated_jobs": deepcopy(dedupe.dedupe_jobs(filtered_jobs)),
    }


def _graph(
    jobs: list[dict],
    *,
    selected_role_families: list[str] | None = None,
    excluded_keywords: list[str] | None = None,
    audit_enabled: bool = False,
    target_seniority: list[str] | None = None,
    seniority_strict_match: bool = False,
) -> dict:
    return graph_owner.execute_authoritative_prefilter_dedupe_graph(
        jobs=jobs,
        selected_role_families=selected_role_families,
        target_seniority=target_seniority,
        seniority_strict_match=seniority_strict_match,
        filter_mode="strict_live",
        role_title_audit_rows=[] if audit_enabled else None,
        excluded_keywords=list(excluded_keywords or []),
        pipeline_run_id="run-phase16a",
        owner_user_id="owner-phase16a",
        context_id="context-phase16a",
    )


def test_exact_graph_and_state_versions():
    assert (
        graph_owner.AUTHORITATIVE_PREFILTER_DEDUPE_GRAPH_VERSION
        == "authoritative-prefilter-dedupe-graph-v1"
    )
    assert (
        graph_owner.AUTHORITATIVE_PREFILTER_DEDUPE_STATE_VERSION
        == "authoritative-prefilter-dedupe-state-v1"
    )


def test_real_state_graph_has_exact_two_production_nodes():
    graph = graph_owner.build_authoritative_prefilter_dedupe_graph()

    assert type(graph).__name__ == "StateGraph"
    assert set(graph.nodes) == {"filter_jobs", "dedupe_jobs"}
    assert (
        graph_owner.AUTHORITATIVE_PREFILTER_DEDUPE_PRODUCTION_NODE_COUNT
        == 2
    )


def test_graph_node_order_is_start_prefilter_dedupe_end():
    graph = graph_owner.build_authoritative_prefilter_dedupe_graph()

    assert graph_owner.AUTHORITATIVE_PREFILTER_DEDUPE_NODE_ORDER == (
        "filter_jobs",
        "dedupe_jobs",
    )
    assert graph.edges == {
        ("__start__", "filter_jobs"),
        ("filter_jobs", "dedupe_jobs"),
        ("dedupe_jobs", "__end__"),
    }


def test_activation_gate_defaults_off():
    for value in (None, "", "0", "false", "no", "off"):
        env = {} if value is None else {GATE: value}
        assert (
            collector._authoritative_prefilter_dedupe_langgraph_enabled(env)
            is False
        )


def test_activation_gate_uses_existing_truthy_convention():
    for value in ("1", "true", "TRUE", "yes", "on"):
        assert (
            collector._authoritative_prefilter_dedupe_langgraph_enabled(
                {GATE: value}
            )
            is True
        )


def test_gate_off_does_not_import_or_construct_graph(monkeypatch):
    monkeypatch.delitem(sys.modules, GRAPH_MODULE, raising=False)

    result = collector._maybe_execute_authoritative_prefilter_dedupe_graph(
        jobs=_jobs(),
        selected_role_families=None,
        filter_mode="strict_live",
        role_title_audit_rows=None,
        excluded_keywords=[],
        env={},
    )

    assert result is None
    assert GRAPH_MODULE not in sys.modules


def test_gate_on_lazily_imports_graph_and_forwards_existing_context(
    monkeypatch,
):
    captured = {}

    def execute(**kwargs):
        captured.update(deepcopy(kwargs))
        return {
            "filtered_jobs": [],
            "filter_diagnostics": {},
            "role_title_audit_rows": [],
            "deduplicated_jobs": [],
            "execution_metadata": {
                "execution_mode": "langgraph",
                "production_node_count": 2,
                "prefilter_invocation_count": 1,
                "dedupe_invocation_count": 1,
                "status": "completed",
            },
        }

    monkeypatch.setitem(
        sys.modules,
        GRAPH_MODULE,
        types.SimpleNamespace(
            execute_authoritative_prefilter_dedupe_graph=execute
        ),
    )
    jobs = _jobs()
    result = collector._maybe_execute_authoritative_prefilter_dedupe_graph(
        jobs=jobs,
        selected_role_families=["data_science"],
        filter_mode="user_pipeline",
        role_title_audit_rows=[],
        excluded_keywords=["intern"],
        env={
            GATE: "1",
            "JOB_APP_PIPELINE_RUN_ID": "run-16a",
            "JOB_STACK_OWNER_USER_ID": "owner-16a",
            "APPLYLENS_AGENT_CONTEXT_ID": "context-16a",
        },
    )

    assert result is not None
    assert captured["jobs"] == jobs
    assert captured["pipeline_run_id"] == "run-16a"
    assert captured["owner_user_id"] == "owner-16a"
    assert captured["context_id"] == "context-16a"
    assert captured["selected_role_families"] == ["data_science"]
    assert captured["target_seniority"] == []
    assert captured["seniority_strict_match"] is False
    assert captured["filter_mode"] == "user_pipeline"
    assert captured["excluded_keywords"] == ["intern"]


def test_production_path_direct_and_graph_outputs_are_identical():
    jobs = _jobs()
    direct = _direct(jobs)
    graph = _graph(jobs)

    assert graph["filtered_jobs"] == direct["filtered_jobs"]
    assert graph["filter_diagnostics"] == direct["filter_diagnostics"]
    assert graph["deduplicated_jobs"] == direct["deduplicated_jobs"]


def test_supplemental_replacement_has_direct_and_graph_parity():
    supplemental = {
        **_job("himalayas", source="himalayas"),
        "provider_attribution_required": True,
        "provider_attribution_label": "Himalayas",
        "provider_attribution_url": "https://himalayas.app",
    }
    direct_job = _job("direct", source="greenhouse")

    direct = _direct([supplemental, direct_job])
    graph = _graph([supplemental, direct_job])

    assert direct["deduplicated_jobs"] == [direct_job]
    assert graph["deduplicated_jobs"] == direct["deduplicated_jobs"]
    assert graph["execution_metadata"]["production_node_count"] == 2
    assert graph["execution_metadata"]["dedupe_invocation_count"] == 1


def test_strict_seniority_direct_and_graph_outputs_are_identical():
    jobs = [
        _job("senior", title="Senior Data Scientist"),
        _job("staff", title="Staff Data Scientist"),
        _job("unknown", title="Data Scientist"),
    ]
    kwargs = {
        "selected_role_families": ["data_science"],
        "target_seniority": ["senior"],
        "seniority_strict_match": True,
        "audit_enabled": True,
    }
    direct = _direct(jobs, **kwargs)
    graph = _graph(jobs, **kwargs)
    assert [job["job_id"] for job in direct["filtered_jobs"]] == ["senior"]
    assert graph["filtered_jobs"] == direct["filtered_jobs"]
    assert graph["role_title_audit_rows"] == direct["role_title_audit_rows"]


def test_direct_and_graph_audit_rows_are_identical():
    jobs = _jobs()
    direct = _direct(jobs, audit_enabled=True)
    graph = _graph(jobs, audit_enabled=True)

    assert graph["role_title_audit_rows"] == direct[
        "role_title_audit_rows"
    ]


def test_selected_role_and_excluded_keyword_behavior_is_preserved():
    jobs = [
        _job("1", title="Backend Engineer"),
        _job("2", title="Backend Engineer Intern"),
        _job("3", title="Data Scientist"),
    ]
    direct = _direct(
        jobs,
        selected_role_families=["backend_engineering"],
        excluded_keywords=["intern"],
    )
    graph = _graph(
        jobs,
        selected_role_families=["backend_engineering"],
        excluded_keywords=["intern"],
    )

    assert graph["filtered_jobs"] == direct["filtered_jobs"]
    assert [row["job_id"] for row in graph["filtered_jobs"]] == ["1"]
    assert graph["filter_diagnostics"]["excluded_keyword"] == 1
    assert graph["filter_diagnostics"]["title_mismatch"] == 1


def test_empty_input_preserves_empty_contract():
    result = _graph([])

    assert result["filtered_jobs"] == []
    assert result["deduplicated_jobs"] == []
    assert result["filter_diagnostics"] == {
        "title_pass": 0,
        "location_pass": 0,
    }
    assert result["execution_metadata"]["input_count"] == 0


@pytest.mark.parametrize(
    "jobs,expected_ids",
    [
        (
            [_job("same"), _job("same", company="Beta")],
            ["same"],
        ),
        (
            [
                _job("1", url="https://jobs.example/shared"),
                {
                    **_job("", company="Beta"),
                    "job_id": "",
                    "url": "https://jobs.example/shared",
                },
            ],
            [""],
        ),
        (
            [_job("1"), _job("2")],
            ["1"],
        ),
    ],
)
def test_existing_dedupe_identity_and_stable_order_are_preserved(
    jobs,
    expected_ids,
):
    if jobs[0].get("url") == "https://jobs.example/shared":
        jobs[0]["job_id"] = ""

    result = _graph(jobs)

    assert [
        row.get("job_id", "") for row in result["deduplicated_jobs"]
    ] == expected_ids


def test_each_production_owner_executes_exactly_once(monkeypatch):
    calls = []
    real_filter = job_filter.filter_jobs
    real_dedupe = dedupe.dedupe_jobs

    def counted_filter(*args, **kwargs):
        calls.append("filter_jobs")
        return real_filter(*args, **kwargs)

    def counted_dedupe(*args, **kwargs):
        calls.append("dedupe_jobs")
        return real_dedupe(*args, **kwargs)

    monkeypatch.setattr(job_filter, "filter_jobs", counted_filter)
    monkeypatch.setattr(dedupe, "dedupe_jobs", counted_dedupe)

    result = _graph(_jobs())

    assert calls == ["filter_jobs", "dedupe_jobs"]
    assert result["execution_metadata"]["prefilter_invocation_count"] == 1
    assert result["execution_metadata"]["dedupe_invocation_count"] == 1


def test_stage_completion_callbacks_preserve_production_order(monkeypatch):
    events = []
    real_filter = job_filter.filter_jobs
    real_dedupe = dedupe.dedupe_jobs

    def ordered_filter(*args, **kwargs):
        events.append("filter_owner")
        return real_filter(*args, **kwargs)

    def ordered_dedupe(*args, **kwargs):
        events.append("dedupe_owner")
        return real_dedupe(*args, **kwargs)

    monkeypatch.setattr(job_filter, "filter_jobs", ordered_filter)
    monkeypatch.setattr(dedupe, "dedupe_jobs", ordered_dedupe)

    graph_owner.execute_authoritative_prefilter_dedupe_graph(
        jobs=_jobs(),
        on_prefilter_completed=lambda *args: events.append(
            "filter_completed"
        ),
        on_dedupe_completed=lambda *args: events.append("dedupe_completed"),
    )

    assert events == [
        "filter_owner",
        "filter_completed",
        "dedupe_owner",
        "dedupe_completed",
    ]


def test_caller_jobs_and_audit_arguments_remain_unchanged():
    jobs = _jobs()
    audit_rows = [{"existing": "row"}]
    jobs_before = deepcopy(jobs)
    audit_before = deepcopy(audit_rows)

    graph_owner.execute_authoritative_prefilter_dedupe_graph(
        jobs=jobs,
        role_title_audit_rows=audit_rows,
        excluded_keywords=[],
    )

    assert jobs == jobs_before
    assert audit_rows == audit_before


def test_deep_copy_contains_owner_mutation(monkeypatch):
    jobs = [_job("1")]
    before = deepcopy(jobs)

    def mutating_filter(rows, **kwargs):
        rows[0]["metadata"]["mutated_inside_owner"] = True
        return rows, {"title_pass": 1, "location_pass": 1}

    monkeypatch.setattr(job_filter, "filter_jobs", mutating_filter)

    result = _graph(jobs)

    assert jobs == before
    assert result["filtered_jobs"][0]["metadata"][
        "mutated_inside_owner"
    ] is True


def test_prefilter_failure_propagates_without_dedupe_or_fallback(monkeypatch):
    dedupe_calls = []

    def fail_filter(*args, **kwargs):
        raise RuntimeError("prefilter_failed")

    def count_dedupe(*args, **kwargs):
        dedupe_calls.append(1)
        return []

    monkeypatch.setattr(job_filter, "filter_jobs", fail_filter)
    monkeypatch.setattr(dedupe, "dedupe_jobs", count_dedupe)

    with pytest.raises(RuntimeError, match="prefilter_failed"):
        _graph(_jobs())

    assert dedupe_calls == []


def test_dedupe_failure_propagates_once_without_retry(monkeypatch):
    calls = []

    def fail_dedupe(*args, **kwargs):
        calls.append(1)
        raise RuntimeError("dedupe_failed")

    monkeypatch.setattr(dedupe, "dedupe_jobs", fail_dedupe)

    with pytest.raises(RuntimeError, match="dedupe_failed"):
        _graph(_jobs())

    assert calls == [1]


def test_malformed_prefilter_contract_fails_closed(monkeypatch):
    monkeypatch.setattr(job_filter, "filter_jobs", lambda *a, **k: [])

    with pytest.raises(
        RuntimeError,
        match="authoritative_prefilter_result_invalid",
    ):
        _graph(_jobs())


def test_malformed_prefilter_diagnostics_fail_closed(monkeypatch):
    monkeypatch.setattr(
        job_filter,
        "filter_jobs",
        lambda rows, **kwargs: (rows, {"bad": True}),
    )

    with pytest.raises(
        RuntimeError,
        match="authoritative_prefilter_diagnostics_invalid",
    ):
        _graph(_jobs())


def test_execution_metadata_is_bounded_and_contains_no_raw_rows():
    result = _graph(_jobs())
    metadata = result["execution_metadata"]

    assert metadata["production_node_count"] == 2
    assert metadata["node_order"] == ["filter_jobs", "dedupe_jobs"]
    assert 0 <= metadata["prefilter_latency_ms"] <= 300_000
    assert 0 <= metadata["dedupe_latency_ms"] <= 300_000
    assert metadata["deterministic"] is True
    assert metadata["read_only"] is True
    assert metadata["provider_calls_allowed"] is False
    assert metadata["mutation_authority"] is False
    assert metadata["application_authority"] is False
    assert metadata["ats_authority"] is False
    assert "jobs" not in metadata
    assert "rows" not in metadata
    assert "credentials" not in metadata


def test_synthetic_graph_execution_performs_no_network_or_database_activity(
    monkeypatch,
):
    calls = {"ashby": 0, "workday": 0}

    def unexpected_ashby(*args, **kwargs):
        calls["ashby"] += 1
        raise AssertionError("unexpected network call")

    def unexpected_workday(*args, **kwargs):
        calls["workday"] += 1
        raise AssertionError("unexpected network call")

    monkeypatch.setattr(
        job_filter,
        "fetch_ashby_timestamp_result",
        unexpected_ashby,
    )
    monkeypatch.setattr(
        job_filter,
        "fetch_workday_timestamp",
        unexpected_workday,
    )

    _graph(_jobs())

    assert calls == {"ashby": 0, "workday": 0}


def test_graph_owner_has_no_llm_provider_persistence_or_action_authority():
    source = Path(
        "src/agents/deterministic_prefilter_dedupe_authoritative_graph.py"
    ).read_text(encoding="utf-8")
    forbidden = (
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


def test_collector_gate_off_keeps_existing_direct_owner_calls():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    prefilter_completion_owner = source.index(
        "def complete_prefilter_stage("
    )
    dedupe_stage_start = source.index(
        'section("DEDUPLICATION"',
        prefilter_completion_owner,
    )
    gate_call = source.index(
        "_maybe_execute_authoritative_prefilter_dedupe_graph("
        "\n            jobs=all_jobs,"
    )
    direct_branch = source.index(
        "if prefilter_dedupe_graph_result is None:",
        gate_call,
    )
    direct_filter = source.index("filter_result = filter_jobs(", direct_branch)
    filter_completion_call = source.index(
        "complete_prefilter_stage(\n            filtered_jobs,",
        direct_filter,
    )
    direct_dedupe = source.index(
        "deduped_jobs = dedupe_jobs(filtered_jobs)",
        filter_completion_call,
    )
    dedupe_completion_call = source.index(
        "complete_dedupe_stage(deduped_jobs)",
        direct_dedupe,
    )

    assert prefilter_completion_owner < dedupe_stage_start < gate_call
    assert gate_call < direct_branch < direct_filter
    assert direct_filter < filter_completion_call < direct_dedupe
    assert direct_dedupe < dedupe_completion_call


def test_graph_module_is_not_imported_at_collector_module_import_boundary():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    import_line = (
        "from src.agents."
        "deterministic_prefilter_dedupe_authoritative_graph import"
    )
    helper_start = source.index(
        "def _maybe_execute_authoritative_prefilter_dedupe_graph("
    )

    assert import_line not in source[:helper_start]
    assert import_line in source[helper_start:]


def test_existing_three_authoritative_graph_owners_remain_separate():
    unchanged_owners = (
        "src/agents/job_prioritization_authoritative_graph.py",
        "src/agents/tailoring_decision_authoritative_graph.py",
        "src/agents/operator_review_authoritative_graph.py",
    )

    for path in unchanged_owners:
        assert Path(path).is_file()
        assert "add_node(" in Path(path).read_text(encoding="utf-8")


def test_run006_remains_absent():
    root = Path(".")

    assert not any(
        path.name.lower().replace("_", "-").startswith("run-006")
        for path in root.rglob("*")
    )


def test_public_modules_reload_without_runtime_execution():
    reloaded_collector = importlib.reload(collector)

    assert (
        reloaded_collector.AUTHORITATIVE_PREFILTER_DEDUPE_LANGGRAPH_FLAG
        == GATE
    )
