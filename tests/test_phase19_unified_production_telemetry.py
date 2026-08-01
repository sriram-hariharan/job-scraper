from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path
import sys
import types

from langgraph.checkpoint.memory import MemorySaver
import pytest

import generate_tailoring_suggestions as tailoring_caller
from src.agents import production_telemetry as telemetry
from src.pipeline import collector
from tests import test_phase18r_generic_production_durable_contract as phase18


FINAL_GRAPH_GATE = (
    "APPLYLENS_AUTHORITATIVE_FINAL_SCORING_LANGGRAPH_ENABLED"
)
TAILORING_GRAPH_GATE = (
    "APPLYLENS_AUTHORITATIVE_TAILORING_GENERATION_LANGGRAPH_ENABLED"
)
PREFILTER_DEDUPE_GRAPH_GATE = (
    "APPLYLENS_AUTHORITATIVE_PREFILTER_DEDUPE_LANGGRAPH_ENABLED"
)
TELEMETRY_GATE = "APPLYLENS_PRODUCTION_AGENT_TELEMETRY_ENABLED"
FINAL_GRAPH_MODULE = "src.agents.final_scoring_authoritative_graph"
PREFILTER_DEDUPE_GRAPH_MODULE = (
    "src.agents.deterministic_prefilter_dedupe_authoritative_graph"
)
NOW = "2026-07-30T12:00:00Z"


def _metadata(**overrides):
    value = {
        "graph_version": "graph-v1",
        "state_version": "state-v1",
        "execution_mode": "langgraph",
        "node_name": "score_jobs",
        "status": "completed",
        "failure_classification": "",
        "invocation_count": 1,
        "node_latency_ms": 7,
        "persistent_mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
    }
    value.update(overrides)
    return value


def _event(**overrides):
    values = {
        "pipeline_run_id": "run-phase19",
        "owner_user_id": "owner-phase19",
        "context_id": "context-phase19",
        "node_key": "score_jobs",
        "workload_classification": "deterministic",
        "execution_metadata": _metadata(),
        "timestamp": NOW,
    }
    values.update(overrides)
    return telemetry.build_production_telemetry_event(**values)


def _final_env(*, telemetry_enabled: bool) -> dict[str, str]:
    return {
        FINAL_GRAPH_GATE: "1",
        TELEMETRY_GATE: "1" if telemetry_enabled else "0",
        "JOB_APP_PIPELINE_RUN_ID": "run-phase19",
        "JOB_STACK_OWNER_USER_ID": "owner-phase19",
        "APPLYLENS_AGENT_CONTEXT_ID": "context-phase19",
    }


def _final_result():
    return {
        "scored_jobs": [{"job_id": "job-phase19", "score": 9}],
        "execution_metadata": _metadata(
            graph_version="authoritative-final-scoring-graph-v1",
            state_version="authoritative-final-scoring-state-v1",
            production_node_count=1,
            input_count=1,
            scored_count=1,
        ),
    }


def _install_final_graph(monkeypatch, execute):
    monkeypatch.setitem(
        sys.modules,
        FINAL_GRAPH_MODULE,
        types.SimpleNamespace(
            execute_authoritative_final_scoring_graph=execute
        ),
    )


def _prefilter_jobs():
    return [
        {
            "job_id": "prefilter-1",
            "company": "Private Example",
            "title": "Data Scientist",
            "location": "New York, NY",
            "source": "greenhouse",
            "posted_at": "2099-01-01T00:00:00Z",
            "url": "https://jobs.example/prefilter-1",
        },
        {
            "job_id": "prefilter-2",
            "company": "Private Example",
            "title": "Data Scientist",
            "location": "New York, NY",
            "source": "greenhouse",
            "posted_at": "2099-01-01T00:00:00Z",
            "url": "https://jobs.example/prefilter-2",
        },
        {
            "job_id": "prefilter-3",
            "company": "Private Example",
            "title": "Accountant",
            "location": "New York, NY",
            "source": "greenhouse",
            "posted_at": "2099-01-01T00:00:00Z",
            "url": "https://jobs.example/prefilter-3",
        },
    ]


def _prefilter_env(
    *,
    graph_enabled: bool,
    telemetry_enabled: bool,
    include_identity: bool = True,
) -> dict[str, str]:
    values = {
        PREFILTER_DEDUPE_GRAPH_GATE: "1" if graph_enabled else "0",
        TELEMETRY_GATE: "1" if telemetry_enabled else "0",
    }
    if include_identity:
        values.update(
            {
                "JOB_APP_PIPELINE_RUN_ID": "run-phase22p-a",
                "JOB_STACK_OWNER_USER_ID": "owner-phase22p-a",
                "APPLYLENS_AGENT_CONTEXT_ID": "context-phase22p-a",
            }
        )
    return values


def _prefilter_result():
    jobs = _prefilter_jobs()
    return {
        "filtered_jobs": deepcopy(jobs[:2]),
        "filter_diagnostics": {
            "title_pass": 2,
            "location_pass": 2,
            "title_mismatch": 1,
        },
        "role_title_audit_rows": [],
        "deduplicated_jobs": deepcopy(jobs[:1]),
        "execution_metadata": {
            "graph_version": "authoritative-prefilter-dedupe-graph-v1",
            "state_version": "authoritative-prefilter-dedupe-state-v1",
            "execution_mode": "langgraph",
            "node_order": ["filter_jobs", "dedupe_jobs"],
            "production_node_count": 2,
            "prefilter_invocation_count": 1,
            "dedupe_invocation_count": 1,
            "input_count": 3,
            "prefilter_output_count": 2,
            "dedupe_output_count": 1,
            "prefilter_latency_ms": 11,
            "dedupe_latency_ms": 7,
            "status": "completed",
            "failure_classification": "",
            "deterministic": True,
            "read_only": True,
            "provider_calls_allowed": False,
            "mutation_authority": False,
            "application_authority": False,
            "ats_authority": False,
        },
    }


def _install_prefilter_graph(monkeypatch, execute):
    monkeypatch.setitem(
        sys.modules,
        PREFILTER_DEDUPE_GRAPH_MODULE,
        types.SimpleNamespace(
            execute_authoritative_prefilter_dedupe_graph=execute
        ),
    )


def _invoke_prefilter(
    *,
    env,
    telemetry_sink=None,
    jobs=None,
    on_prefilter_completed=None,
    on_dedupe_completed=None,
):
    return collector._maybe_execute_authoritative_prefilter_dedupe_graph(
        jobs=_prefilter_jobs() if jobs is None else jobs,
        selected_role_families=None,
        filter_mode="strict_live",
        role_title_audit_rows=None,
        excluded_keywords=[],
        on_prefilter_completed=on_prefilter_completed,
        on_dedupe_completed=on_dedupe_completed,
        env=env,
        telemetry_sink=telemetry_sink,
    )


def _tailoring_result(*, cache_hit=False, failure=""):
    return {
        "parse_ok": not bool(failure),
        "parse_error": failure,
        "retry_used": False,
        "cache_hit": cache_hit,
        "requested_provider": "groq",
        "requested_model": "requested-model",
        "resolved_provider": "groq",
        "resolved_model": "resolved-model",
        "fallback_used": False,
        "prompt_version": "tailoring-live-v1",
        "raw_response": "must never enter telemetry",
        "parsed": {"generated_tailoring_text": "private"},
        "concrete_replacement_candidates_requested": False,
    }


def _tailoring_env(
    *,
    telemetry_enabled: bool,
    durable: bool = False,
) -> dict[str, str]:
    return {
        TAILORING_GRAPH_GATE: "1",
        TELEMETRY_GATE: "1" if telemetry_enabled else "0",
        phase18.GATE: "1" if durable else "0",
        "JOB_APP_PIPELINE_RUN_ID": "run-phase18r",
        "JOB_STACK_OWNER_USER_ID": "owner-phase18r",
        "APPLYLENS_AGENT_CONTEXT_ID": "context-phase18r",
    }


def test_exact_contract_version_and_gate_convention():
    assert (
        telemetry.PRODUCTION_TELEMETRY_CONTRACT_VERSION
        == "production-agent-telemetry-v1"
    )
    for value in (None, "", "0", "false", "no", "off"):
        assert telemetry.telemetry_enabled(value) is False
    for value in ("1", "true", "TRUE", "yes", "on"):
        assert telemetry.telemetry_enabled(value) is True


def test_deterministic_event_has_exact_identity_and_counts():
    event = _event(input_count=3, output_count=2)
    assert event["pipeline_run_id"] == "run-phase19"
    assert event["owner_user_id"] == "owner-phase19"
    assert event["context_id"] == "context-phase19"
    assert event["node_key"] == "score_jobs"
    assert event["workload_classification"] == "deterministic"
    assert event["input_count"] == 3
    assert event["output_count"] == 2
    assert event["invocation_count"] == 1


def test_deterministic_event_reports_no_provider_activity():
    event = _event(
        source_metadata={
            "requested_provider": "groq",
            "requested_model": "model",
        }
    )
    assert "requested_provider" not in event
    assert "requested_model" not in event
    assert "cache_status" not in event


def test_direct_and_graph_routes_are_distinct():
    direct = _event(
        execution_metadata=_metadata(execution_mode="direct")
    )
    graph = _event()
    assert direct["execution_route"] == "direct"
    assert graph["execution_route"] == "graph"


def test_durable_first_and_replay_routes_are_distinct():
    first = _event(
        workload_classification="llm",
        node_key="tailoring_generation",
        execution_metadata=_metadata(
            durable_status="completed",
            node_invocation_count=1,
        ),
    )
    replay = _event(
        workload_classification="llm",
        node_key="tailoring_generation",
        execution_metadata=_metadata(
            durable_status="completed_replay",
            invocation_count=0,
            graph_invocation_count=0,
            tailoring_owner_invocation_count=0,
            provider_call_count=0,
            cache_write_count=0,
        ),
    )
    assert first["execution_route"] == "durable_first_execution"
    assert replay["execution_route"] == "durable_replay"
    assert replay["durable_classification"] == "completed_replay"
    assert replay["graph_invocation_count"] == 0
    assert replay["owner_invocation_count"] == 0
    assert replay["provider_invocation_count"] == 0
    assert replay["cache_write_count"] == 0


def test_cache_hit_metadata_is_preserved():
    event = _event(
        workload_classification="llm",
        source_metadata={"cache_hit": True},
    )
    assert event["cache_status"] == "hit"


def test_cache_miss_metadata_is_preserved():
    event = _event(
        workload_classification="llm",
        source_metadata={"cache_hit": False},
    )
    assert event["cache_status"] == "miss"


def test_requested_and_resolved_provider_model_are_preserved():
    event = _event(
        workload_classification="llm",
        source_metadata={
            "requested_provider": "groq",
            "requested_model": "requested",
            "resolved_provider": "openai",
            "resolved_model": "resolved",
        },
    )
    assert event["requested_provider"] == "groq"
    assert event["requested_model"] == "requested"
    assert event["resolved_provider"] == "openai"
    assert event["resolved_model"] == "resolved"


def test_retry_and_fallback_metadata_are_preserved():
    event = _event(
        workload_classification="llm",
        source_metadata={
            "retry_used": True,
            "fallback_used": True,
        },
    )
    assert event["retry_used"] is True
    assert event["fallback_used"] is True


def test_prompt_version_is_preserved_only_when_supplied():
    with_prompt = _event(
        workload_classification="llm",
        source_metadata={"prompt_version": "prompt-v7"},
    )
    without_prompt = _event(workload_classification="llm")
    assert with_prompt["prompt_version"] == "prompt-v7"
    assert "prompt_version" not in without_prompt


def test_source_proven_token_counts_are_preserved():
    event = _event(
        workload_classification="llm",
        source_metadata={
            "input_token_count": 10,
            "output_token_count": 4,
            "total_token_count": 14,
        },
    )
    assert event["input_token_count"] == 10
    assert event["output_token_count"] == 4
    assert event["total_token_count"] == 14


def test_unknown_token_and_cost_fields_are_not_fabricated():
    event = _event(workload_classification="llm")
    for field in (
        "input_token_count",
        "output_token_count",
        "total_token_count",
        "exact_cost",
        "cost_currency",
    ):
        assert field not in event


def test_exact_source_cost_is_preserved_without_repricing():
    event = _event(
        workload_classification="llm",
        source_metadata={
            "exact_cost": "0.001250",
            "cost_currency": "USD",
        },
    )
    assert event["exact_cost"] == "0.001250"
    assert event["cost_currency"] == "USD"


def test_latency_is_nonnegative_and_bounded():
    negative = _event(
        execution_metadata=_metadata(node_latency_ms=-100)
    )
    excessive = _event(
        execution_metadata=_metadata(node_latency_ms=999_999_999)
    )
    assert negative["latency_ms"] == 0
    assert excessive["latency_ms"] == telemetry.MAX_TELEMETRY_LATENCY_MS


def test_failure_classification_is_preserved():
    event = _event(
        execution_metadata=_metadata(
            status="failed",
            failure_classification="structured_validation_failure",
        )
    )
    assert event["status"] == "failed"
    assert (
        event["failure_classification"]
        == "structured_validation_failure"
    )


def test_owner_scoped_identity_is_required():
    for field in ("pipeline_run_id", "owner_user_id", "context_id"):
        kwargs = {field: ""}
        with pytest.raises(
            telemetry.ProductionTelemetryContractError,
            match=f"telemetry_{field}_required",
        ):
            _event(**kwargs)


def test_raw_business_and_provider_fields_are_rejected():
    for field in (
        "raw_prompt",
        "raw_response",
        "resume_text",
        "job_description",
        "generated_content",
        "provider_response",
    ):
        with pytest.raises(
            telemetry.ProductionTelemetryContractError,
            match="telemetry_source_prohibited_field",
        ):
            _event(
                workload_classification="llm",
                source_metadata={field: "private"},
            )


def test_credentials_and_database_urls_are_rejected():
    for unsafe in (
        "postgresql://user:secret@host/database",
        "authorization: bearer secret",
        "api_key=secret",
    ):
        with pytest.raises(
            telemetry.ProductionTelemetryContractError,
            match="unsafe",
        ):
            _event(
                workload_classification="llm",
                source_metadata={"requested_model": unsafe},
            )


def test_mutation_application_and_ats_authority_must_remain_false():
    for field in (
        "persistent_mutation_authority",
        "application_authority",
        "ats_authority",
    ):
        metadata = _metadata()
        metadata[field] = True
        with pytest.raises(
            telemetry.ProductionTelemetryContractError,
            match="telemetry_authority_must_be_false",
        ):
            _event(execution_metadata=metadata)


def test_injected_sink_receives_one_fresh_event():
    events = []
    result = telemetry.emit_production_telemetry(
        pipeline_run_id="run-phase19",
        owner_user_id="owner-phase19",
        context_id="context-phase19",
        node_key="score_jobs",
        workload_classification="deterministic",
        execution_metadata=_metadata(),
        timestamp=NOW,
        sink=events.append,
    )
    assert result["emitted"] is True
    assert len(events) == 1
    events[0]["status"] = "changed-by-sink-consumer"
    assert result["event"]["status"] == "completed"


def test_sink_failure_is_bounded_and_does_not_raise():
    def failed_sink(_event):
        raise RuntimeError("secret sink detail")

    result = telemetry.emit_production_telemetry(
        pipeline_run_id="run-phase19",
        owner_user_id="owner-phase19",
        context_id="context-phase19",
        node_key="score_jobs",
        workload_classification="deterministic",
        execution_metadata=_metadata(),
        timestamp=NOW,
        sink=failed_sink,
    )
    assert result == {
        "emitted": False,
        "failure_classification": "sink_failure",
        "reason_code": "telemetry_sink_failed",
    }


@pytest.mark.parametrize("telemetry_enabled", [False, True])
def test_prefilter_graph_off_imports_nothing_and_returns_direct_sentinel(
    monkeypatch,
    telemetry_enabled,
):
    events = []
    monkeypatch.delitem(
        sys.modules,
        PREFILTER_DEDUPE_GRAPH_MODULE,
        raising=False,
    )
    monkeypatch.delitem(
        sys.modules,
        "src.agents.production_telemetry",
        raising=False,
    )

    result = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=False,
            telemetry_enabled=telemetry_enabled,
        ),
        telemetry_sink=events.append,
    )

    assert result is None
    assert events == []
    assert PREFILTER_DEDUPE_GRAPH_MODULE not in sys.modules
    assert "src.agents.production_telemetry" not in sys.modules


def test_prefilter_graph_on_telemetry_off_executes_once_without_import(
    monkeypatch,
):
    calls, events = [], []

    def execute(**_kwargs):
        calls.append("graph")
        return deepcopy(_prefilter_result())

    _install_prefilter_graph(monkeypatch, execute)
    monkeypatch.delitem(
        sys.modules,
        "src.agents.production_telemetry",
        raising=False,
    )

    result = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=False,
        ),
        telemetry_sink=events.append,
    )

    assert result == _prefilter_result()
    assert calls == ["graph"]
    assert events == []
    assert "src.agents.production_telemetry" not in sys.modules


def test_prefilter_both_gates_on_emit_two_exact_ordered_node_events(
    monkeypatch,
):
    calls, events = [], []

    def execute(**_kwargs):
        calls.append("graph")
        return deepcopy(_prefilter_result())

    _install_prefilter_graph(monkeypatch, execute)
    result = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=True,
        ),
        telemetry_sink=events.append,
    )

    assert result == _prefilter_result()
    assert calls == ["graph"]
    assert [event["node_key"] for event in events] == [
        "filter_jobs",
        "dedupe_jobs",
    ]
    assert [
        (event["input_count"], event["output_count"])
        for event in events
    ] == [(3, 2), (2, 1)]
    assert [event["latency_ms"] for event in events] == [11, 7]
    for event in events:
        assert event["workload_classification"] == "deterministic"
        assert event["execution_route"] == "graph"
        assert event["status"] == "completed"
        assert event["invocation_count"] == 1
        assert event["mutation_authority"] is False
        assert event["application_authority"] is False
        assert event["ats_authority"] is False


def test_prefilter_telemetry_on_off_output_parity_and_order(monkeypatch):
    calls = []

    def execute(**_kwargs):
        calls.append("graph")
        return deepcopy(_prefilter_result())

    _install_prefilter_graph(monkeypatch, execute)
    without_telemetry = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=False,
        )
    )
    events = []
    with_telemetry = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=True,
        ),
        telemetry_sink=events.append,
    )

    assert with_telemetry == without_telemetry
    assert [
        row["job_id"] for row in with_telemetry["filtered_jobs"]
    ] == ["prefilter-1", "prefilter-2"]
    assert [
        row["job_id"] for row in with_telemetry["deduplicated_jobs"]
    ] == ["prefilter-1"]
    assert calls == ["graph", "graph"]
    assert len(events) == 2


def test_prefilter_real_collector_boundary_has_telemetry_output_parity():
    without_telemetry = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=False,
        )
    )
    events = []
    with_telemetry = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=True,
        ),
        telemetry_sink=events.append,
    )

    for field in (
        "filtered_jobs",
        "filter_diagnostics",
        "role_title_audit_rows",
        "deduplicated_jobs",
    ):
        assert with_telemetry[field] == without_telemetry[field]
    with_metadata = dict(with_telemetry["execution_metadata"])
    without_metadata = dict(without_telemetry["execution_metadata"])
    for latency_field in ("prefilter_latency_ms", "dedupe_latency_ms"):
        with_metadata.pop(latency_field)
        without_metadata.pop(latency_field)
    assert with_metadata == without_metadata
    assert [event["node_key"] for event in events] == [
        "filter_jobs",
        "dedupe_jobs",
    ]


def test_prefilter_real_boundary_owners_callbacks_and_telemetry_order(
    monkeypatch,
):
    from src.pipeline import dedupe, job_filter

    order, events = [], []
    real_filter = job_filter.filter_jobs
    real_dedupe = dedupe.dedupe_jobs

    def counted_filter(*args, **kwargs):
        order.append("filter_owner")
        return real_filter(*args, **kwargs)

    def counted_dedupe(*args, **kwargs):
        order.append("dedupe_owner")
        return real_dedupe(*args, **kwargs)

    def sink(event):
        order.append(f"telemetry:{event['node_key']}")
        events.append(event)

    monkeypatch.setattr(job_filter, "filter_jobs", counted_filter)
    monkeypatch.setattr(dedupe, "dedupe_jobs", counted_dedupe)
    result = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=True,
        ),
        telemetry_sink=sink,
        on_prefilter_completed=lambda *_args: order.append(
            "filter_completed"
        ),
        on_dedupe_completed=lambda *_args: order.append(
            "dedupe_completed"
        ),
    )

    assert result is not None
    assert order == [
        "filter_owner",
        "filter_completed",
        "dedupe_owner",
        "dedupe_completed",
        "telemetry:filter_jobs",
        "telemetry:dedupe_jobs",
    ]
    assert len(events) == 2


def test_prefilter_empty_input_emits_two_truthful_zero_count_events():
    events = []
    result = _invoke_prefilter(
        jobs=[],
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=True,
        ),
        telemetry_sink=events.append,
    )

    assert result["filtered_jobs"] == []
    assert result["deduplicated_jobs"] == []
    assert len(events) == 2
    assert [
        (event["input_count"], event["output_count"])
        for event in events
    ] == [(0, 0), (0, 0)]
    assert all(0 <= event["latency_ms"] <= 300_000 for event in events)


def test_prefilter_sink_failure_preserves_output_without_graph_rerun(
    monkeypatch,
):
    calls, sink_calls = [], []

    def execute(**_kwargs):
        calls.append("graph")
        return deepcopy(_prefilter_result())

    def failed_sink(event):
        sink_calls.append(event["node_key"])
        raise RuntimeError("sink unavailable")

    _install_prefilter_graph(monkeypatch, execute)
    result = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=True,
        ),
        telemetry_sink=failed_sink,
    )

    assert result == _prefilter_result()
    assert calls == ["graph"]
    assert sink_calls == ["filter_jobs", "dedupe_jobs"]


def test_prefilter_contract_rejection_preserves_output_without_retry(
    monkeypatch,
):
    calls, events = [], []

    def execute(**_kwargs):
        calls.append("graph")
        return deepcopy(_prefilter_result())

    _install_prefilter_graph(monkeypatch, execute)
    result = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=True,
            include_identity=False,
        ),
        telemetry_sink=events.append,
    )

    assert result == _prefilter_result()
    assert calls == ["graph"]
    assert events == []


def test_prefilter_invalid_graph_result_emits_nothing(monkeypatch):
    calls, events = [], []
    invalid = _prefilter_result()
    invalid["execution_metadata"]["status"] = "failed"

    def execute(**_kwargs):
        calls.append("graph")
        return deepcopy(invalid)

    _install_prefilter_graph(monkeypatch, execute)
    with pytest.raises(
        RuntimeError,
        match="authoritative_prefilter_dedupe_execution_metadata_invalid",
    ):
        _invoke_prefilter(
            env=_prefilter_env(
                graph_enabled=True,
                telemetry_enabled=True,
            ),
            telemetry_sink=events.append,
        )

    assert calls == ["graph"]
    assert events == []


def test_prefilter_events_exclude_business_provider_and_credential_payloads(
    monkeypatch,
):
    events = []
    private_result = _prefilter_result()
    private_result["filtered_jobs"][0]["description_text"] = (
        "private job description"
    )
    private_result["filtered_jobs"][0]["resume_text"] = "private resume"

    _install_prefilter_graph(
        monkeypatch,
        lambda **_kwargs: deepcopy(private_result),
    )
    result = _invoke_prefilter(
        env=_prefilter_env(
            graph_enabled=True,
            telemetry_enabled=True,
        ),
        telemetry_sink=events.append,
    )

    assert result == private_result
    assert len(events) == 2
    prohibited = {
        "jobs",
        "rows",
        "company",
        "title",
        "location",
        "description",
        "description_text",
        "resume",
        "resume_text",
        "provider_request",
        "provider_response",
        "cache",
        "api_key",
        "authorization",
        "token",
        "environment",
    }
    for event in events:
        assert prohibited.isdisjoint(event)
        assert (
            len(
                json.dumps(
                    event,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            <= telemetry.MAX_TELEMETRY_PAYLOAD_BYTES
        )
        assert "Private Example" not in repr(event)
        assert "private job description" not in repr(event)
        assert "private resume" not in repr(event)


def test_final_scoring_gate_off_emits_nothing_and_does_not_import(monkeypatch):
    calls, events = [], []

    def execute(**_kwargs):
        calls.append("owner")
        return deepcopy(_final_result())

    _install_final_graph(monkeypatch, execute)
    monkeypatch.delitem(
        sys.modules,
        "src.agents.production_telemetry",
        raising=False,
    )
    result = collector._maybe_execute_authoritative_final_scoring_graph(
        jobs=[{"job_id": "job-phase19"}],
        env=_final_env(telemetry_enabled=False),
        telemetry_sink=events.append,
    )
    assert result == _final_result()
    assert calls == ["owner"]
    assert events == []
    assert "src.agents.production_telemetry" not in sys.modules


def test_final_scoring_gate_on_emits_once_after_unchanged_output(monkeypatch):
    order, events = [], []

    def execute(**_kwargs):
        order.append("owner")
        return deepcopy(_final_result())

    def sink(event):
        order.append("telemetry")
        events.append(event)

    _install_final_graph(monkeypatch, execute)
    expected = _final_result()
    result = collector._maybe_execute_authoritative_final_scoring_graph(
        jobs=[{"job_id": "job-phase19"}],
        env=_final_env(telemetry_enabled=True),
        telemetry_sink=sink,
    )
    assert result == expected
    assert order == ["owner", "telemetry"]
    assert len(events) == 1
    assert events[0]["workload_classification"] == "deterministic"
    assert events[0]["execution_route"] == "graph"


def test_final_scoring_sink_failure_never_reruns_owner(monkeypatch):
    calls = []

    def execute(**_kwargs):
        calls.append("owner")
        return deepcopy(_final_result())

    def failed_sink(_event):
        raise RuntimeError("sink unavailable")

    _install_final_graph(monkeypatch, execute)
    result = collector._maybe_execute_authoritative_final_scoring_graph(
        jobs=[{"job_id": "job-phase19"}],
        env=_final_env(telemetry_enabled=True),
        telemetry_sink=failed_sink,
    )
    assert result == _final_result()
    assert calls == ["owner"]


def test_tailoring_gate_off_preserves_output_and_emits_nothing():
    calls, events = [], []
    owner_result = _tailoring_result(cache_hit=True)

    def owner(**_kwargs):
        calls.append("owner")
        return deepcopy(owner_result)

    result = (
        tailoring_caller
        ._maybe_execute_authoritative_tailoring_generation_graph(
            packet=phase18._packet(),
            payload=phase18._payload(),
            run_tailoring_func=owner,
            env=_tailoring_env(telemetry_enabled=False),
            telemetry_sink=events.append,
        )
    )
    assert result["tailoring_result"] == owner_result
    assert calls == ["owner"]
    assert events == []


def test_tailoring_cache_hit_and_miss_each_emit_one_parity_event():
    for cache_hit, expected_cache_status in (
        (True, "hit"),
        (False, "miss"),
    ):
        calls, events = [], []
        owner_result = _tailoring_result(cache_hit=cache_hit)

        def owner(**_kwargs):
            calls.append("owner")
            return deepcopy(owner_result)

        result = (
            tailoring_caller
            ._maybe_execute_authoritative_tailoring_generation_graph(
                packet=phase18._packet(),
                payload=phase18._payload(),
                run_tailoring_func=owner,
                env=_tailoring_env(telemetry_enabled=True),
                telemetry_sink=events.append,
            )
        )
        assert result["tailoring_result"] == owner_result
        assert calls == ["owner"]
        assert len(events) == 1
        event = events[0]
        assert event["cache_status"] == expected_cache_status
        assert event["requested_provider"] == "groq"
        assert event["resolved_model"] == "resolved-model"
        assert event["prompt_version"] == "tailoring-live-v1"
        assert "raw_response" not in event
        assert "parsed" not in event


def test_durable_first_and_replay_emit_without_duplicate_owner_or_provider():
    repository = phase18._Repository()
    saver = MemorySaver()
    calls, events = [], []
    owner_result = phase18._owner_result()

    def owner(**_kwargs):
        calls.append("owner")
        return deepcopy(owner_result)

    kwargs = {
        "packet": phase18._packet(),
        "payload": phase18._payload(),
        "run_tailoring_func": owner,
        "env": _tailoring_env(
            telemetry_enabled=True,
            durable=True,
        ),
        "job_index": 7,
        "durable_repository": repository,
        "durable_saver": saver,
        "telemetry_sink": events.append,
    }
    first = (
        tailoring_caller
        ._maybe_execute_authoritative_tailoring_generation_graph(**kwargs)
    )
    replay = (
        tailoring_caller
        ._maybe_execute_authoritative_tailoring_generation_graph(**kwargs)
    )
    assert first["tailoring_result"] == replay["tailoring_result"]
    assert calls == ["owner"]
    assert len(events) == 2
    assert events[0]["execution_route"] == "durable_first_execution"
    assert events[1]["execution_route"] == "durable_replay"
    assert events[1]["graph_invocation_count"] == 0
    assert events[1]["owner_invocation_count"] == 0
    assert events[1]["provider_invocation_count"] == 0
    assert events[1]["cache_write_count"] == 0
    assert events[0]["application_authority"] is False
    assert events[1]["ats_authority"] is False


def test_telemetry_module_has_no_persistence_provider_or_cache_ownership():
    source = Path(telemetry.__file__).read_text(encoding="utf-8")
    for prohibited in (
        "run_chat_completion",
        "get_provider_metrics",
        "get_eval_cache_metrics",
        "get_skill_cache_metrics",
        "DurableOrchestrationRepository",
        "open_langgraph_postgres_saver",
        "DATABASE_URL",
        "CREATE TABLE",
    ):
        assert prohibited not in source
    assert "raw_response" in source
    assert "_reject_prohibited_source" in inspect.getsource(
        telemetry.build_production_telemetry_event
    )
