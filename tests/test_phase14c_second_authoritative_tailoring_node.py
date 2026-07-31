from __future__ import annotations

import ast
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

import application_execution_queue as queue
from src.agents import job_prioritization_agent as priority
from src.agents import operator_review_agent
from src.agents import tailoring_decision_agent as tailoring


GRAPH_MODULE = "src.agents.tailoring_decision_authoritative_graph"
GRAPH_FLAG = queue.AUTHORITATIVE_TAILORING_DECISION_LANGGRAPH_FLAG


def _row(**overrides):
    row = {
        "job_doc_id": "job-1",
        "job_company": "Example Co",
        "job_title": "Backend Engineer",
        "job_location": "Remote",
        "source": "greenhouse",
        "action": "APPLY",
        "winner_resume": "resume.pdf",
        "resolved_resume": "resume.pdf",
        "winner_score": "0.750000",
        "resolved_score": "0.750000",
        "winner_missing_requirements": "distributed systems",
        "resolved_missing_requirements": "distributed systems",
        "score_gap": "0.100000",
        "deterministic_winner_available": "true",
        "deterministic_winner_score": "0.750000",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
        "critic_decision": "",
        "critic_reason_codes": "",
        "requires_manual_review": "false",
        "variant_review_required": "false",
        "selection_signal": "deterministic_winner",
        "resolved_resume_source": "deterministic_winner",
        "resolved_selection_status": "resolved",
    }
    row.update(overrides)
    return row


def _priority_overlay_rows():
    rows = [_row()]
    shared = priority.build_job_prioritization_shared_result(
        rows=deepcopy(rows),
        pipeline_run_id="run-14c",
        owner_user_id="owner-14c",
        source_artifact_path="queue.csv",
    )
    return queue._with_priority_overlay(
        rows,
        shared_result=shared,
    )


def _metadata():
    return {
        "pipeline_run_id": "run-14c",
        "owner_user_id": "owner-14c",
        "context_id": "tailoring_decision:run-14c",
        "source_artifact_path": "queue.csv",
    }


def _route(rows, *, env):
    return queue._build_authoritative_tailoring_shared_result(
        rows=rows,
        env=env,
        **_metadata(),
    )


def _configure_main(
    monkeypatch,
    tmp_path,
    rows,
    *,
    tailoring_graph_enabled,
    priority_graph_enabled=False,
    extra_args=(),
):
    output = tmp_path / "application_execution_queue.csv"
    monkeypatch.setattr(queue, "_load_rows", lambda _path: deepcopy(rows))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "application_execution_queue.py",
            "--input-csv",
            str(tmp_path / "unused.csv"),
            "--output-csv",
            str(output),
            "--top-k-console",
            "0",
            *extra_args,
        ],
    )
    monkeypatch.setenv(
        GRAPH_FLAG,
        "1" if tailoring_graph_enabled else "0",
    )
    monkeypatch.setenv(
        queue.AUTHORITATIVE_JOB_PRIORITIZATION_LANGGRAPH_FLAG,
        "1" if priority_graph_enabled else "0",
    )
    monkeypatch.delenv(
        queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG,
        raising=False,
    )
    monkeypatch.delenv(
        queue.PRODUCTION_SHADOW_JOB_PRIORITY_OWNER_FLAG,
        raising=False,
    )
    monkeypatch.setenv(tailoring.TRACE_ENABLED_ENV, "0")
    monkeypatch.setattr(
        queue,
        "record_job_prioritization_agent_trace",
        lambda **_kwargs: {"attempted": False, "reason": "isolated"},
    )
    monkeypatch.setattr(
        queue,
        "record_tailoring_decision_agent_trace",
        lambda **_kwargs: {"attempted": False, "reason": "isolated"},
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        lambda **_kwargs: {"attempted": False, "reason": "isolated"},
    )
    return output


def test_graph_contract_real_stategraph_one_node_and_canonical_callable():
    graph_owner = importlib.import_module(GRAPH_MODULE)
    graph = graph_owner.build_authoritative_tailoring_decision_graph()

    assert type(graph).__name__ == "StateGraph"
    assert type(graph).__module__.startswith("langgraph.")
    assert graph_owner.AUTHORITATIVE_TAILORING_DECISION_GRAPH_VERSION == (
        "authoritative-tailoring-decision-graph-v1"
    )
    assert graph_owner.AUTHORITATIVE_TAILORING_DECISION_STATE_VERSION == (
        "authoritative-tailoring-decision-state-v1"
    )
    assert (
        graph_owner.AUTHORITATIVE_TAILORING_DECISION_PRODUCTION_NODE_COUNT
        == 1
    )
    assert set(graph.nodes) == {
        graph_owner.AUTHORITATIVE_TAILORING_DECISION_NODE
    }
    assert graph_owner.AUTHORITATIVE_TAILORING_DECISION_NODE == (
        "build_tailoring_decision_shared_result"
    )
    assert set(
        graph_owner.AuthoritativeTailoringDecisionState.__annotations__
    ) == {
        "state_version",
        "graph_version",
        "execution_mode",
        "pipeline_run_id",
        "owner_user_id",
        "context_id",
        "priority_overlay_rows",
        "shared_result",
        "current_node",
        "completed_nodes",
        "pending_node",
        "status",
        "failure_classification",
        "invocation_count",
        "node_latency_ms",
        "deterministic",
        "read_only",
        "provider_calls_allowed",
        "mutation_authority",
        "application_authority",
        "ats_authority",
    }
    source = Path(graph_owner.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
    }
    assert "build_tailoring_decision_shared_result" in called_attributes
    assert not {
        "render_tailoring_decisions",
        "render_tailoring_decision_rows",
        "recommend_tailoring_decision",
    }.intersection(called_attributes)


def test_gate_defaults_off_without_graph_import_or_construction(monkeypatch):
    sys.modules.pop(GRAPH_MODULE, None)
    calls = []
    real_builder = queue.build_tailoring_decision_shared_result

    def counted(**kwargs):
        calls.append(deepcopy(kwargs))
        return real_builder(**kwargs)

    monkeypatch.setattr(
        queue,
        "build_tailoring_decision_shared_result",
        counted,
    )
    rows = _priority_overlay_rows()
    before = deepcopy(rows)
    shared, metadata = _route(rows, env={})

    assert len(calls) == 1
    assert GRAPH_MODULE not in sys.modules
    assert metadata["execution_mode"] == "direct"
    assert metadata["production_node_count"] == 0
    assert metadata["invocation_count"] == 1
    assert shared["contract_version"] == (
        tailoring.TAILORING_DECISION_SHARED_RESULT_VERSION
    )
    assert rows == before


def test_gate_on_constructs_graph_and_invokes_owner_exactly_once(
    monkeypatch,
):
    graph_owner = importlib.import_module(GRAPH_MODULE)
    owner_calls = []
    graph_build_calls = []
    real_owner = tailoring.build_tailoring_decision_shared_result
    real_graph_builder = (
        graph_owner.build_authoritative_tailoring_decision_graph
    )

    def counted_owner(**kwargs):
        owner_calls.append(deepcopy(kwargs))
        return real_owner(**kwargs)

    def counted_graph_builder(**kwargs):
        graph_build_calls.append(deepcopy(kwargs))
        return real_graph_builder(**kwargs)

    monkeypatch.setattr(
        tailoring,
        "build_tailoring_decision_shared_result",
        counted_owner,
    )
    monkeypatch.setattr(
        graph_owner,
        "build_authoritative_tailoring_decision_graph",
        counted_graph_builder,
    )
    monkeypatch.setattr(
        queue,
        "build_tailoring_decision_shared_result",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("direct tailoring route also executed")
        ),
    )
    shared, metadata = _route(
        _priority_overlay_rows(),
        env={GRAPH_FLAG: "1"},
    )

    assert len(graph_build_calls) == 1
    assert len(owner_calls) == 1
    assert metadata["execution_mode"] == "langgraph"
    assert metadata["production_node_count"] == 1
    assert metadata["invocation_count"] == 1
    assert shared["contract_version"] == (
        tailoring.TAILORING_DECISION_SHARED_RESULT_VERSION
    )


def test_priority_and_tailoring_authoritative_nodes_execute_once_in_order(
    monkeypatch,
    tmp_path,
):
    order = []
    real_priority = priority.build_job_prioritization_shared_result
    real_tailoring = tailoring.build_tailoring_decision_shared_result

    def counted_priority(**kwargs):
        order.append("priority")
        return real_priority(**kwargs)

    def counted_tailoring(**kwargs):
        order.append("tailoring")
        return real_tailoring(**kwargs)

    monkeypatch.setattr(
        priority,
        "build_job_prioritization_shared_result",
        counted_priority,
    )
    monkeypatch.setattr(
        tailoring,
        "build_tailoring_decision_shared_result",
        counted_tailoring,
    )
    _configure_main(
        monkeypatch,
        tmp_path,
        [_row()],
        tailoring_graph_enabled=True,
        priority_graph_enabled=True,
    )

    queue.main()

    assert order == ["priority", "tailoring"]


def test_genuine_priority_owner_conflict_fails_before_tailoring_invocation(
    monkeypatch,
):
    tailoring_calls = []
    monkeypatch.setattr(
        queue,
        "build_tailoring_decision_shared_result",
        lambda **kwargs: tailoring_calls.append(kwargs),
    )

    with pytest.raises(
        queue.AuthoritativeJobPrioritizationGateConflictError
    ) as captured:
        queue._build_authoritative_priority_shared_result(
            rows=[_row()],
            pipeline_run_id="run-14c",
            owner_user_id="owner-14c",
            context_id="job_priority:run-14c",
            source_artifact_path="queue.csv",
            env={
                queue.AUTHORITATIVE_JOB_PRIORITIZATION_LANGGRAPH_FLAG: "1",
                queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG: "1",
                GRAPH_FLAG: "1",
            },
        )

    assert captured.value.failure_code == (
        "authoritative_priority_conflict_diagnostic_verification"
    )
    assert tailoring_calls == []


@pytest.mark.parametrize(
    "compatible_flag",
    [
        "APPLYLENS_ARTIFACT_ONLY_PRODUCTION_SHADOW_ENABLED",
        queue.PRODUCTION_SHADOW_JOB_PRIORITY_OWNER_FLAG,
        tailoring.TAILORING_DECISION_PRIORITY_EVIDENCE_GATE,
        tailoring.TRACE_ENABLED_ENV,
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED",
        "APPLYLENS_LIVE_TAILORING_SUGGESTION_DRY_RUN_ENABLED",
    ],
)
def test_independent_shadow_evidence_and_trace_gates_remain_compatible(
    compatible_flag,
):
    shared, metadata = _route(
        _priority_overlay_rows(),
        env={GRAPH_FLAG: "1", compatible_flag: "1"},
    )

    assert metadata["execution_mode"] == "langgraph"
    assert metadata["invocation_count"] == 1
    assert shared["rendered_rows"][0]["job_id"] == "job-1"


def test_graph_failure_propagates_without_direct_fallback(monkeypatch):
    importlib.import_module(GRAPH_MODULE)
    direct_calls = []

    monkeypatch.setattr(
        tailoring,
        "build_tailoring_decision_shared_result",
        lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("authoritative_tailoring_owner_failed")
        ),
    )
    monkeypatch.setattr(
        queue,
        "build_tailoring_decision_shared_result",
        lambda **kwargs: direct_calls.append(kwargs),
    )

    with pytest.raises(
        RuntimeError,
        match="authoritative_tailoring_owner_failed",
    ):
        _route(
            _priority_overlay_rows(),
            env={GRAPH_FLAG: "1"},
        )

    assert direct_calls == []


def test_graph_failure_creates_no_tailoring_or_operator_outputs(
    monkeypatch,
    tmp_path,
):
    calls = []
    output = _configure_main(
        monkeypatch,
        tmp_path,
        [_row()],
        tailoring_graph_enabled=True,
        extra_args=(
            "--tailoring-decision-output-csv",
            str(tmp_path / "tailoring.csv"),
            "--operator-review-output-csv",
            str(tmp_path / "operator.csv"),
        ),
    )
    monkeypatch.setattr(
        tailoring,
        "build_tailoring_decision_shared_result",
        lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("authoritative_tailoring_owner_failed")
        ),
    )
    monkeypatch.setattr(
        queue,
        "write_tailoring_decision_artifacts",
        lambda **kwargs: calls.append(("tailoring", kwargs)),
    )
    monkeypatch.setattr(
        queue,
        "write_operator_review_artifacts",
        lambda **kwargs: calls.append(("operator", kwargs)),
    )

    with pytest.raises(
        RuntimeError,
        match="authoritative_tailoring_owner_failed",
    ):
        queue.main()

    assert output.is_file()
    assert calls == []
    assert not (tmp_path / "tailoring.csv").exists()
    assert not (tmp_path / "operator.csv").exists()


def test_direct_and_graph_shared_results_order_and_containment_are_identical():
    rows = _priority_overlay_rows() + [
        {
            **_priority_overlay_rows()[0],
            "job_id": "job-2",
            "job_doc_id": "job-2",
            "company": "Second Co",
            "job_company": "Second Co",
            "title": "Platform Engineer",
            "job_title": "Platform Engineer",
            "advisory_priority": "tailor_first",
            "deterministic_winner_score": "0.650000",
            "winner_score": "0.650000",
        }
    ]
    before = deepcopy(rows)
    direct, direct_metadata = _route(rows, env={})
    graphed, graph_metadata = _route(rows, env={GRAPH_FLAG: "1"})

    assert graphed == direct
    assert graphed["payload"]["input"] == direct["payload"]["input"]
    assert graphed["payload"]["output"] == direct["payload"]["output"]
    assert graphed["payload"]["validation"] == (
        direct["payload"]["validation"]
    )
    assert graphed["payload"]["summary"] == direct["payload"]["summary"]
    assert [row["job_id"] for row in graphed["rendered_rows"]] == [
        "job-1",
        "job-2",
    ]
    assert direct_metadata["execution_mode"] == "direct"
    assert graph_metadata["execution_mode"] == "langgraph"
    assert rows == before

    graphed["payload"]["input"]["rows"][0]["company"] = "mutated"
    graphed["payload"]["output"]["decisions"][0][
        "tailoring_reason_codes"
    ].append("mutated")
    graphed["rendered_rows"][0]["tailoring_decision"] = "do_not_tailor"
    assert direct["payload"]["input"]["rows"][0]["company"] == "Example Co"
    assert "mutated" not in direct["payload"]["output"]["decisions"][0][
        "tailoring_reason_codes"
    ]
    assert direct["rendered_rows"][0]["tailoring_decision"] != (
        "do_not_tailor"
    )
    assert rows == before


class _TraceCapture:
    calls = []

    @classmethod
    def reset(cls):
        cls.calls = []

    @classmethod
    def create_agent_run(cls, *, record):
        cls.calls.append(("create", deepcopy(record)))
        return {"run": {"agent_run_id": "trace-run-14c"}}

    @classmethod
    def record_agent_step(cls, *, record):
        cls.calls.append(("step", deepcopy(record)))
        return {"step": {"agent_step_id": "trace-step-14c"}}

    @classmethod
    def complete_agent_step(cls, **kwargs):
        cls.calls.append(("complete_step", deepcopy(kwargs)))
        return {}

    @classmethod
    def complete_agent_run(cls, **kwargs):
        cls.calls.append(("complete_run", deepcopy(kwargs)))
        return {}


def _trace_payloads(rows, shared):
    _TraceCapture.reset()
    result = tailoring.record_tailoring_decision_agent_trace(
        rows=rows,
        source_artifact_path=_metadata()["source_artifact_path"],
        env={
            tailoring.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": _metadata()["owner_user_id"],
            "JOB_APP_PIPELINE_RUN_ID": _metadata()["pipeline_run_id"],
        },
        trace_module=_TraceCapture,
        shared_result=shared,
    )
    return result, deepcopy(_TraceCapture.calls)


def _without_trace_timestamps(value):
    if isinstance(value, dict):
        return {
            key: _without_trace_timestamps(item)
            for key, item in value.items()
            if key not in {"started_at", "completed_at"}
        }
    if isinstance(value, list):
        return [_without_trace_timestamps(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_without_trace_timestamps(item) for item in value)
    return value


def test_direct_and_graph_artifacts_overlays_operator_and_trace_are_identical(
    tmp_path,
):
    rows = _priority_overlay_rows()
    direct, _ = _route(rows, env={})
    graphed, _ = _route(rows, env={GRAPH_FLAG: "1"})
    metadata = {
        key: value
        for key, value in _metadata().items()
        if key != "context_id"
    }
    direct_csv = tmp_path / "direct.csv"
    direct_summary = tmp_path / "direct.json"
    graph_csv = tmp_path / "graph.csv"
    graph_summary = tmp_path / "graph.json"

    direct_artifact = tailoring.write_tailoring_decision_artifacts(
        rows=rows,
        output_csv_path=direct_csv,
        summary_json_path=direct_summary,
        shared_result=direct,
        **metadata,
    )
    graph_artifact = tailoring.write_tailoring_decision_artifacts(
        rows=rows,
        output_csv_path=graph_csv,
        summary_json_path=graph_summary,
        shared_result=graphed,
        **metadata,
    )
    direct_overlay = queue._with_tailoring_decision_overlay(
        rows,
        shared_result=direct,
    )
    graph_overlay = queue._with_tailoring_decision_overlay(
        rows,
        shared_result=graphed,
    )
    direct_trace, direct_trace_calls = _trace_payloads(rows, direct)
    graph_trace, graph_trace_calls = _trace_payloads(rows, graphed)

    assert graph_csv.read_bytes() == direct_csv.read_bytes()
    assert graph_summary.read_bytes() == direct_summary.read_bytes()
    assert graph_artifact["validation"] == direct_artifact["validation"]
    assert graph_artifact["summary"] == direct_artifact["summary"]
    assert graph_overlay == direct_overlay
    assert operator_review_agent.render_operator_review_rows(
        graph_overlay
    ) == operator_review_agent.render_operator_review_rows(direct_overlay)
    assert graph_trace == direct_trace
    assert _without_trace_timestamps(graph_trace_calls) == (
        _without_trace_timestamps(direct_trace_calls)
    )


def test_execution_metadata_is_bounded_and_contains_no_rows(capsys):
    rows = _priority_overlay_rows()
    shared, metadata = _route(rows, env={GRAPH_FLAG: "1"})

    assert set(metadata) == {
        "graph_version",
        "state_version",
        "execution_mode",
        "node_name",
        "production_node_count",
        "invocation_count",
        "node_latency_ms",
        "status",
        "failure_classification",
        "deterministic",
        "read_only",
        "provider_calls_allowed",
        "mutation_authority",
        "application_authority",
        "ats_authority",
    }
    assert 0 <= metadata["node_latency_ms"] <= 300_000
    assert metadata["provider_calls_allowed"] is False
    assert metadata["mutation_authority"] is False
    assert metadata["application_authority"] is False
    assert metadata["ats_authority"] is False
    serialized = json.dumps(metadata, sort_keys=True)
    assert "Example Co" not in serialized
    assert "resume.pdf" not in serialized
    assert "priority_overlay_rows" not in serialized
    assert capsys.readouterr().out == ""
    assert shared["rendered_rows"][0]["job_id"] == "job-1"


def test_graph_has_no_provider_credential_network_database_or_persistence_path():
    graph_owner = importlib.import_module(GRAPH_MODULE)
    source = Path(graph_owner.__file__).read_text(encoding="utf-8").lower()
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        str(node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )

    assert not {
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "dotenv",
        "psycopg",
        "sqlalchemy",
    }.intersection(imported_roots)
    assert "checkpointer" not in source
    assert "database_url" not in source
    assert "api_key" not in source
    assert "provider_output" not in source
    assert "generated_resume" not in source
    assert "auto_apply" not in source
    assert "ats_submission" not in source


def test_existing_public_apis_and_manual_review_boundaries_remain_compatible(
    tmp_path,
):
    rows = _priority_overlay_rows()
    payload = tailoring.render_tailoring_decisions(rows=rows)
    rendered = tailoring.render_tailoring_decision_rows(rows)
    artifact = tailoring.write_tailoring_decision_artifacts(
        rows=rows,
        output_csv_path=tmp_path / "tailoring.csv",
    )
    review_rows = operator_review_agent.render_operator_review_rows(
        queue._with_tailoring_decision_overlay(rows)
    )

    assert rendered[0]["tailoring_decision"] == (
        payload["output"]["decisions"][0]["tailoring_decision"]
    )
    assert artifact["summary"] == payload["summary"]
    assert artifact["validation"] == payload["validation"]
    assert review_rows[0]["operator_review_lane"] in (
        operator_review_agent.OPERATOR_REVIEW_LANES
    )
    assert queue.APPLICATION_SUBMISSION_GATE_ENABLED is True
    assert queue.APPROVAL_GATED_EXECUTION_ENABLED is True


def test_run006_remains_absent():
    repository = Path(__file__).resolve().parents[1]
    assert not any(
        "run_006" in path.name.lower() or "run-006" in path.name.lower()
        for path in repository.rglob("*")
        if ".git" not in path.parts and "__pycache__" not in path.parts
    )
