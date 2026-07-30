from __future__ import annotations

import ast
import csv
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

import application_execution_queue as queue
from src.agents import job_prioritization_agent as priority
from src.agents import operator_review_agent as operator
from src.agents import tailoring_decision_agent as tailoring


GRAPH_MODULE = "src.agents.operator_review_authoritative_graph"
GRAPH_FLAG = queue.AUTHORITATIVE_OPERATOR_REVIEW_LANGGRAPH_FLAG


def _row(**overrides):
    row = {
        "job_doc_id": "job-1",
        "job_company": "Example Co",
        "job_title": "Backend Engineer",
        "job_location": "Remote",
        "source": "greenhouse",
        "action": "APPLY",
        "advisory_priority": "apply_now",
        "winner_resume": "resume.pdf",
        "resolved_resume": "resume.pdf",
        "winner_score": "0.850000",
        "resolved_score": "0.850000",
        "winner_missing_requirements": "",
        "resolved_missing_requirements": "",
        "score_gap": "0.100000",
        "deterministic_winner_available": "true",
        "deterministic_winner_score": "0.850000",
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


def _tailoring_overlay_rows():
    queue_rows = [_row()]
    priority_shared = priority.build_job_prioritization_shared_result(
        rows=deepcopy(queue_rows),
        pipeline_run_id="run-15c",
        owner_user_id="owner-15c",
        source_artifact_path="queue.csv",
    )
    priority_rows = queue._with_priority_overlay(
        queue_rows,
        shared_result=priority_shared,
    )
    tailoring_shared = tailoring.build_tailoring_decision_shared_result(
        rows=deepcopy(priority_rows),
        pipeline_run_id="run-15c",
        owner_user_id="owner-15c",
        source_artifact_path="queue.csv",
    )
    return queue._with_tailoring_decision_overlay(
        priority_rows,
        shared_result=tailoring_shared,
    )


def _rows():
    return _tailoring_overlay_rows() + [
        {
            **_tailoring_overlay_rows()[0],
            "job_id": "job-2",
            "job_doc_id": "job-2",
            "company": "Second Co",
            "job_company": "Second Co",
            "title": "Platform Engineer",
            "job_title": "Platform Engineer",
            "advisory_priority": "tailor_first",
            "tailoring_decision": "tailor_before_apply",
            "winner_score": "0.650000",
            "resolved_score": "0.650000",
            "deterministic_winner_score": "0.650000",
        }
    ]


def _metadata():
    return {
        "pipeline_run_id": "run-15c",
        "owner_user_id": "owner-15c",
        "context_id": "operator_review:run-15c",
        "source_artifact_path": "queue.csv",
    }


def _route(rows, *, env):
    return queue._build_authoritative_operator_review_shared_result(
        rows=rows,
        env=env,
        **_metadata(),
    )


def _configure_main(
    monkeypatch,
    tmp_path,
    *,
    artifact=False,
    trace=False,
    valid_context=False,
    priority_graph=False,
    tailoring_graph=False,
    operator_graph=False,
    priority_artifact=False,
    tailoring_artifact=False,
):
    output = tmp_path / "application_execution_queue.csv"
    args = [
        "application_execution_queue.py",
        "--input-csv",
        str(tmp_path / "unused.csv"),
        "--output-csv",
        str(output),
        "--top-k-console",
        "0",
    ]
    if priority_artifact:
        args.extend(
            [
                "--priority-output-csv",
                str(tmp_path / "priority.csv"),
                "--priority-summary-json",
                str(tmp_path / "priority.json"),
            ]
        )
    if tailoring_artifact:
        args.extend(
            [
                "--tailoring-decision-output-csv",
                str(tmp_path / "tailoring.csv"),
                "--tailoring-decision-summary-json",
                str(tmp_path / "tailoring.json"),
            ]
        )
    if artifact:
        args.extend(
            [
                "--operator-review-output-csv",
                str(tmp_path / "operator.csv"),
                "--operator-review-summary-json",
                str(tmp_path / "operator.json"),
            ]
        )
    monkeypatch.setattr(queue, "_load_rows", lambda _path: [_row()])
    monkeypatch.setattr(sys, "argv", args)
    monkeypatch.setenv(
        queue.AUTHORITATIVE_JOB_PRIORITIZATION_LANGGRAPH_FLAG,
        "1" if priority_graph else "0",
    )
    monkeypatch.setenv(
        queue.AUTHORITATIVE_TAILORING_DECISION_LANGGRAPH_FLAG,
        "1" if tailoring_graph else "0",
    )
    monkeypatch.setenv(GRAPH_FLAG, "1" if operator_graph else "0")
    monkeypatch.setenv(operator.TRACE_ENABLED_ENV, "1" if trace else "0")
    monkeypatch.delenv(operator.TRACE_STRICT_ENV, raising=False)
    if valid_context:
        monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "owner-15c")
        monkeypatch.setenv("JOB_APP_PIPELINE_RUN_ID", "run-15c")
    else:
        monkeypatch.delenv("JOB_STACK_OWNER_USER_ID", raising=False)
        monkeypatch.delenv("JOB_APP_PIPELINE_RUN_ID", raising=False)
        monkeypatch.delenv("JOB_STACK_USER_PIPELINE_RUN_ID", raising=False)
    monkeypatch.delenv(
        queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG,
        raising=False,
    )
    monkeypatch.delenv(
        queue.PRODUCTION_SHADOW_JOB_PRIORITY_OWNER_FLAG,
        raising=False,
    )
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
    return output


class _TraceCapture:
    calls = []
    fail_at = ""

    @classmethod
    def reset(cls, *, fail_at=""):
        cls.calls = []
        cls.fail_at = fail_at

    @classmethod
    def _record(cls, name, payload):
        cls.calls.append((name, deepcopy(payload)))
        if cls.fail_at == name:
            raise RuntimeError(f"{name}_failed")

    @classmethod
    def create_agent_run(cls, *, record):
        cls._record("create_run", record)
        return {"run": {"agent_run_id": "agent-run-15c"}}

    @classmethod
    def record_agent_step(cls, *, record):
        cls._record("record_step", record)
        return {"step": {"agent_step_id": "agent-step-15c"}}

    @classmethod
    def complete_agent_step(cls, **kwargs):
        cls._record("complete_step", kwargs)
        return {}

    @classmethod
    def complete_agent_run(cls, **kwargs):
        cls._record("complete_run", kwargs)
        return {}


def _trace_payloads(rows, shared):
    _TraceCapture.reset()
    result = operator.record_operator_review_agent_trace(
        rows=rows,
        source_artifact_path=_metadata()["source_artifact_path"],
        env={
            operator.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": _metadata()["owner_user_id"],
            "JOB_APP_PIPELINE_RUN_ID": _metadata()["pipeline_run_id"],
        },
        trace_module=_TraceCapture,
        shared_result=shared,
    )
    return result, deepcopy(_TraceCapture.calls)


def _without_timestamps(value):
    if isinstance(value, dict):
        return {
            key: _without_timestamps(item)
            for key, item in value.items()
            if key not in {"started_at", "completed_at"}
        }
    if isinstance(value, list):
        return [_without_timestamps(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_without_timestamps(item) for item in value)
    return value


def test_graph_contract_real_stategraph_one_node_and_canonical_callable():
    graph_owner = importlib.import_module(GRAPH_MODULE)
    graph = graph_owner.build_authoritative_operator_review_graph()

    assert type(graph).__name__ == "StateGraph"
    assert type(graph).__module__.startswith("langgraph.")
    assert graph_owner.AUTHORITATIVE_OPERATOR_REVIEW_GRAPH_VERSION == (
        "authoritative-operator-review-graph-v1"
    )
    assert graph_owner.AUTHORITATIVE_OPERATOR_REVIEW_STATE_VERSION == (
        "authoritative-operator-review-state-v1"
    )
    assert graph_owner.AUTHORITATIVE_OPERATOR_REVIEW_PRODUCTION_NODE_COUNT == 1
    assert set(graph.nodes) == {
        graph_owner.AUTHORITATIVE_OPERATOR_REVIEW_NODE
    }
    assert graph_owner.AUTHORITATIVE_OPERATOR_REVIEW_NODE == (
        "build_operator_review_shared_result"
    )
    assert set(
        graph_owner.AuthoritativeOperatorReviewState.__annotations__
    ) == {
        "graph_version",
        "state_version",
        "execution_mode",
        "pipeline_run_id",
        "owner_user_id",
        "context_id",
        "tailoring_overlay_rows",
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
    assert "build_operator_review_shared_result" in called_attributes
    assert "validate_operator_review_shared_result" in called_attributes
    assert not {
        "render_operator_review",
        "render_operator_review_rows",
        "recommend_operator_lane",
    }.intersection(called_attributes)


@pytest.mark.parametrize("gate_enabled", [False, True])
def test_no_consumer_never_imports_graph_or_computes(
    monkeypatch,
    tmp_path,
    gate_enabled,
):
    sys.modules.pop(GRAPH_MODULE, None)
    _configure_main(
        monkeypatch,
        tmp_path,
        operator_graph=gate_enabled,
    )
    calls = []
    monkeypatch.setattr(
        queue,
        "build_operator_review_shared_result",
        lambda **kwargs: calls.append(kwargs),
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        lambda **_kwargs: {"attempted": False, "reason": "trace_disabled"},
    )

    queue.main()

    assert calls == []
    assert GRAPH_MODULE not in sys.modules
    assert not (tmp_path / "operator.csv").exists()


def test_gate_defaults_off_uses_direct_owner_without_graph_import():
    sys.modules.pop(GRAPH_MODULE, None)
    rows = _rows()
    before = deepcopy(rows)
    shared, metadata = _route(rows, env={})

    assert GRAPH_MODULE not in sys.modules
    assert metadata["execution_mode"] == "direct"
    assert metadata["production_node_count"] == 0
    assert metadata["invocation_count"] == 1
    assert shared["contract_version"] == (
        operator.OPERATOR_REVIEW_SHARED_RESULT_VERSION
    )
    assert rows == before


def test_gate_on_constructs_graph_and_invokes_owner_exactly_once(monkeypatch):
    graph_owner = importlib.import_module(GRAPH_MODULE)
    owner_calls = []
    graph_build_calls = []
    real_owner = operator.build_operator_review_shared_result
    real_graph_builder = (
        graph_owner.build_authoritative_operator_review_graph
    )

    def counted_owner(**kwargs):
        owner_calls.append(deepcopy(kwargs))
        return real_owner(**kwargs)

    def counted_graph_builder(**kwargs):
        graph_build_calls.append(deepcopy(kwargs))
        return real_graph_builder(**kwargs)

    monkeypatch.setattr(
        operator,
        "build_operator_review_shared_result",
        counted_owner,
    )
    monkeypatch.setattr(
        graph_owner,
        "build_authoritative_operator_review_graph",
        counted_graph_builder,
    )
    monkeypatch.setattr(
        queue,
        "build_operator_review_shared_result",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("direct operator route also executed")
        ),
    )

    shared, metadata = _route(_rows(), env={GRAPH_FLAG: "1"})

    assert len(graph_build_calls) == 1
    assert len(owner_calls) == 1
    assert metadata["execution_mode"] == "langgraph"
    assert metadata["production_node_count"] == 1
    assert metadata["invocation_count"] == 1
    assert shared["contract_version"] == (
        operator.OPERATOR_REVIEW_SHARED_RESULT_VERSION
    )


@pytest.mark.parametrize(
    (
        "artifact",
        "trace",
        "valid_context",
        "operator_graph",
        "expected_direct",
        "expected_graph",
    ),
    [
        (True, False, False, False, 1, 0),
        (True, False, False, True, 0, 1),
        (False, True, True, False, 1, 0),
        (False, True, True, True, 0, 1),
        (True, True, True, True, 0, 1),
        (False, True, False, True, 0, 0),
    ],
)
def test_conditional_exactly_once_matrix(
    monkeypatch,
    tmp_path,
    artifact,
    trace,
    valid_context,
    operator_graph,
    expected_direct,
    expected_graph,
):
    _configure_main(
        monkeypatch,
        tmp_path,
        artifact=artifact,
        trace=trace,
        valid_context=valid_context,
        operator_graph=operator_graph,
    )
    graph_owner = importlib.import_module(GRAPH_MODULE)
    direct_calls = []
    graph_calls = []
    owner_calls = []
    real_direct = queue.build_operator_review_shared_result
    real_owner = operator.build_operator_review_shared_result
    real_graph = graph_owner.execute_authoritative_operator_review_graph

    def counted_direct(**kwargs):
        direct_calls.append(deepcopy(kwargs))
        return real_direct(**kwargs)

    def counted_owner(**kwargs):
        owner_calls.append(deepcopy(kwargs))
        return real_owner(**kwargs)

    def counted_graph(**kwargs):
        graph_calls.append(deepcopy(kwargs))
        return real_graph(**kwargs)

    monkeypatch.setattr(
        queue,
        "build_operator_review_shared_result",
        counted_direct,
    )
    monkeypatch.setattr(
        operator,
        "build_operator_review_shared_result",
        counted_owner,
    )
    monkeypatch.setattr(
        graph_owner,
        "execute_authoritative_operator_review_graph",
        counted_graph,
    )
    monkeypatch.setattr(
        queue,
        "write_operator_review_artifacts",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        lambda **_kwargs: {"attempted": False, "reason": "isolated"},
    )

    queue.main()

    assert len(direct_calls) == expected_direct
    assert len(graph_calls) == expected_graph
    assert len(owner_calls) == expected_graph
    assert len(direct_calls) + len(owner_calls) in {0, 1}


def test_artifact_and_trace_graph_mode_share_one_result_without_rerender(
    monkeypatch,
    tmp_path,
):
    _configure_main(
        monkeypatch,
        tmp_path,
        artifact=True,
        trace=True,
        valid_context=True,
        operator_graph=True,
    )
    render_calls = []
    real_render = operator.render_operator_review

    def counted_render(**kwargs):
        render_calls.append(deepcopy(kwargs))
        return real_render(**kwargs)

    def isolated_trace(**kwargs):
        return operator.record_operator_review_agent_trace(
            **kwargs,
            env={
                operator.TRACE_ENABLED_ENV: "1",
                "JOB_STACK_OWNER_USER_ID": "owner-15c",
                "JOB_APP_PIPELINE_RUN_ID": "run-15c",
            },
            trace_module=_TraceCapture,
        )

    _TraceCapture.reset()
    monkeypatch.setattr(operator, "render_operator_review", counted_render)
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        isolated_trace,
    )

    queue.main()

    assert len(render_calls) == 1
    assert (tmp_path / "operator.csv").is_file()
    assert [name for name, _payload in _TraceCapture.calls] == [
        "create_run",
        "record_step",
        "complete_step",
        "complete_run",
    ]


def test_priority_tailoring_operator_execute_once_in_order_when_eligible(
    monkeypatch,
    tmp_path,
):
    _configure_main(
        monkeypatch,
        tmp_path,
        artifact=True,
        priority_graph=True,
        tailoring_graph=True,
        operator_graph=True,
    )
    order = []
    real_priority = priority.build_job_prioritization_shared_result
    real_tailoring = tailoring.build_tailoring_decision_shared_result
    real_operator = operator.build_operator_review_shared_result

    def counted_priority(**kwargs):
        order.append("priority")
        return real_priority(**kwargs)

    def counted_tailoring(**kwargs):
        order.append("tailoring")
        return real_tailoring(**kwargs)

    def counted_operator(**kwargs):
        order.append("operator")
        return real_operator(**kwargs)

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
    monkeypatch.setattr(
        operator,
        "build_operator_review_shared_result",
        counted_operator,
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        lambda **_kwargs: {"attempted": False, "reason": "isolated"},
    )

    queue.main()

    assert order == ["priority", "tailoring", "operator"]


def test_all_three_gates_keep_ineligible_operator_absent(
    monkeypatch,
    tmp_path,
):
    sys.modules.pop(GRAPH_MODULE, None)
    _configure_main(
        monkeypatch,
        tmp_path,
        priority_graph=True,
        tailoring_graph=True,
        operator_graph=True,
    )
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
    monkeypatch.setattr(
        queue,
        "build_operator_review_shared_result",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("ineligible operator invoked")
        ),
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        lambda **_kwargs: {"attempted": False, "reason": "trace_disabled"},
    )

    queue.main()

    assert order == ["priority", "tailoring"]
    assert GRAPH_MODULE not in sys.modules


def test_genuine_upstream_duplicate_owner_conflict_precedes_operator(
    monkeypatch,
    tmp_path,
):
    _configure_main(
        monkeypatch,
        tmp_path,
        artifact=True,
        priority_graph=True,
        tailoring_graph=True,
        operator_graph=True,
    )
    monkeypatch.setenv(queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG, "1")
    operator_calls = []
    monkeypatch.setattr(
        operator,
        "build_operator_review_shared_result",
        lambda **kwargs: operator_calls.append(kwargs),
    )

    with pytest.raises(
        queue.AuthoritativeJobPrioritizationGateConflictError
    ):
        queue.main()

    assert operator_calls == []


@pytest.mark.parametrize(
    "compatible_flag",
    [
        "APPLYLENS_ARTIFACT_ONLY_PRODUCTION_SHADOW_ENABLED",
        queue.PRODUCTION_SHADOW_JOB_PRIORITY_OWNER_FLAG,
        tailoring.TAILORING_DECISION_PRIORITY_EVIDENCE_GATE,
        operator.OPERATOR_REVIEW_TAILORING_EVIDENCE_GATE,
        operator.TRACE_ENABLED_ENV,
        "APPLYLENS_LANGGRAPH_OPERATOR_REVIEW_PAUSE_RESUME_ENABLED",
        "APPLYLENS_AGENTIC_APPROVALS_ENABLED",
    ],
)
def test_shadow_evidence_trace_pause_and_decision_flags_are_compatible(
    compatible_flag,
):
    shared, metadata = _route(
        _rows(),
        env={GRAPH_FLAG: "1", compatible_flag: "1"},
    )

    assert metadata["execution_mode"] == "langgraph"
    assert metadata["invocation_count"] == 1
    assert shared["rendered_rows"][0]["job_id"] == "job-1"


def test_graph_failure_propagates_without_direct_fallback(monkeypatch):
    importlib.import_module(GRAPH_MODULE)
    direct_calls = []
    monkeypatch.setattr(
        operator,
        "build_operator_review_shared_result",
        lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("authoritative_operator_owner_failed")
        ),
    )
    monkeypatch.setattr(
        queue,
        "build_operator_review_shared_result",
        lambda **kwargs: direct_calls.append(kwargs),
    )

    with pytest.raises(
        RuntimeError,
        match="authoritative_operator_owner_failed",
    ):
        _route(_rows(), env={GRAPH_FLAG: "1"})

    assert direct_calls == []


def test_graph_failure_writes_no_operator_artifact_or_trace(
    monkeypatch,
    tmp_path,
):
    _configure_main(
        monkeypatch,
        tmp_path,
        artifact=True,
        priority_graph=True,
        tailoring_graph=True,
        operator_graph=True,
        priority_artifact=True,
        tailoring_artifact=True,
    )
    consumer_calls = []
    monkeypatch.setattr(
        operator,
        "build_operator_review_shared_result",
        lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("authoritative_operator_owner_failed")
        ),
    )
    monkeypatch.setattr(
        queue,
        "write_operator_review_artifacts",
        lambda **kwargs: consumer_calls.append(("artifact", kwargs)),
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        lambda **kwargs: consumer_calls.append(("trace", kwargs)),
    )

    with pytest.raises(
        RuntimeError,
        match="authoritative_operator_owner_failed",
    ):
        queue.main()

    assert consumer_calls == []
    assert (tmp_path / "priority.csv").is_file()
    assert (tmp_path / "tailoring.csv").is_file()
    assert not (tmp_path / "operator.csv").exists()


def test_artifact_failure_remains_advisory_and_trace_reuses_graph_result(
    monkeypatch,
    tmp_path,
    capsys,
):
    _configure_main(
        monkeypatch,
        tmp_path,
        artifact=True,
        trace=True,
        valid_context=True,
        operator_graph=True,
    )
    owner_calls = []
    real_owner = operator.build_operator_review_shared_result

    def counted_owner(**kwargs):
        owner_calls.append(deepcopy(kwargs))
        return real_owner(**kwargs)

    def isolated_trace(**kwargs):
        return operator.record_operator_review_agent_trace(
            **kwargs,
            env={
                operator.TRACE_ENABLED_ENV: "1",
                "JOB_STACK_OWNER_USER_ID": "owner-15c",
                "JOB_APP_PIPELINE_RUN_ID": "run-15c",
            },
            trace_module=_TraceCapture,
        )

    _TraceCapture.reset()
    monkeypatch.setattr(
        operator,
        "build_operator_review_shared_result",
        counted_owner,
    )
    monkeypatch.setattr(
        queue,
        "write_operator_review_artifacts",
        lambda **_kwargs: (_ for _ in ()).throw(OSError("write_failed")),
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        isolated_trace,
    )

    queue.main()

    assert len(owner_calls) == 1
    assert "Operator review advisory artifact skipped: write_failed" in (
        capsys.readouterr().out
    )
    assert [name for name, _payload in _TraceCapture.calls] == [
        "create_run",
        "record_step",
        "complete_step",
        "complete_run",
    ]


def test_direct_and_graph_results_artifacts_and_traces_are_identical(
    tmp_path,
):
    rows = _rows()
    before = deepcopy(rows)
    direct, direct_metadata = _route(rows, env={})
    graphed, graph_metadata = _route(rows, env={GRAPH_FLAG: "1"})
    metadata = {
        key: value
        for key, value in _metadata().items()
        if key != "context_id"
    }
    direct_csv = tmp_path / "direct.csv"
    direct_json = tmp_path / "direct.json"
    graph_csv = tmp_path / "graph.csv"
    graph_json = tmp_path / "graph.json"

    direct_artifact = operator.write_operator_review_artifacts(
        rows=rows,
        output_csv_path=direct_csv,
        summary_json_path=direct_json,
        shared_result=direct,
        **metadata,
    )
    graph_artifact = operator.write_operator_review_artifacts(
        rows=rows,
        output_csv_path=graph_csv,
        summary_json_path=graph_json,
        shared_result=graphed,
        **metadata,
    )
    direct_trace, direct_trace_calls = _trace_payloads(rows, direct)
    graph_trace, graph_trace_calls = _trace_payloads(rows, graphed)

    assert graphed == direct
    assert graphed["payload"]["input"] == direct["payload"]["input"]
    assert graphed["payload"]["output"] == direct["payload"]["output"]
    assert graphed["payload"]["validation"] == (
        direct["payload"]["validation"]
    )
    assert graphed["payload"]["summary"] == direct["payload"]["summary"]
    assert graphed["rendered_rows"] == direct["rendered_rows"]
    assert [
        row["operator_review_lane"] for row in graphed["rendered_rows"]
    ] == [
        row["operator_review_lane"] for row in direct["rendered_rows"]
    ]
    assert [
        row["operator_review_reason_codes"]
        for row in graphed["rendered_rows"]
    ] == [
        row["operator_review_reason_codes"]
        for row in direct["rendered_rows"]
    ]
    assert [row["job_id"] for row in graphed["rendered_rows"]] == [
        "job-1",
        "job-2",
    ]
    assert graph_csv.read_bytes() == direct_csv.read_bytes()
    assert graph_json.read_bytes() == direct_json.read_bytes()
    assert graph_artifact["validation"] == direct_artifact["validation"]
    assert graph_artifact["summary"] == direct_artifact["summary"]
    assert graph_trace == direct_trace
    assert _without_timestamps(graph_trace_calls) == (
        _without_timestamps(direct_trace_calls)
    )
    assert direct_metadata["execution_mode"] == "direct"
    assert graph_metadata["execution_mode"] == "langgraph"
    assert rows == before

    graphed["payload"]["input"]["rows"][0]["company"] = "mutated"
    graphed["payload"]["output"]["reviews"][0][
        "operator_reason_codes"
    ].append("mutated")
    graphed["rendered_rows"][0]["operator_review_lane"] = "hold_or_skip"
    assert direct["payload"]["input"]["rows"][0]["company"] == "Example Co"
    assert "mutated" not in direct["payload"]["output"]["reviews"][0][
        "operator_reason_codes"
    ]
    assert direct["rendered_rows"][0]["operator_review_lane"] != (
        "hold_or_skip"
    )
    assert rows == before


def test_execution_metadata_and_stdout_are_bounded(capsys):
    shared, metadata = _route(_rows(), env={GRAPH_FLAG: "1"})

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
    assert "tailoring_overlay_rows" not in serialized
    assert capsys.readouterr().out == ""
    assert shared["rendered_rows"][0]["job_id"] == "job-1"


def test_queue_prints_metadata_only_for_actual_graph_execution(
    monkeypatch,
    tmp_path,
    capsys,
):
    _configure_main(
        monkeypatch,
        tmp_path,
        artifact=True,
        operator_graph=True,
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        lambda **_kwargs: {"attempted": False, "reason": "isolated"},
    )

    queue.main()

    output = capsys.readouterr().out
    metadata_lines = [
        line
        for line in output.splitlines()
        if line.startswith("Authoritative operator review execution: ")
    ]
    assert len(metadata_lines) == 1
    metadata = json.loads(metadata_lines[0].split(": ", 1)[1])
    assert metadata["execution_mode"] == "langgraph"
    assert metadata["production_node_count"] == 1
    assert "Example Co" not in metadata_lines[0]
    assert "resume.pdf" not in metadata_lines[0]


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
    assert "provider_response" not in source
    assert "generated_resume" not in source
    assert "operator_decision" not in source
    assert "agentic_approval" not in source
    assert "auto_apply" not in source
    assert "ats_submission" not in source


def test_existing_public_apis_and_manual_review_boundaries_remain_compatible(
    tmp_path,
):
    rows = _rows()
    payload = operator.render_operator_review(rows=rows)
    rendered = operator.render_operator_review_rows(rows)
    artifact = operator.write_operator_review_artifacts(
        rows=rows,
        output_csv_path=tmp_path / "operator.csv",
    )
    with (tmp_path / "operator.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        written = list(csv.DictReader(handle))

    assert rendered == written
    assert artifact["summary"] == payload["summary"]
    assert artifact["validation"] == payload["validation"]
    assert set(row["operator_review_lane"] for row in rendered) <= (
        operator.OPERATOR_REVIEW_LANES
    )
    assert queue.APPLICATION_SUBMISSION_GATE_ENABLED is True
    assert queue.APPROVAL_GATED_EXECUTION_ENABLED is True


def test_three_authoritative_graphs_are_isolated_single_node_owners():
    graph_modules = [
        importlib.import_module(
            "src.agents.job_prioritization_authoritative_graph"
        ),
        importlib.import_module(
            "src.agents.tailoring_decision_authoritative_graph"
        ),
        importlib.import_module(GRAPH_MODULE),
    ]
    builders = [
        graph_modules[0].build_authoritative_job_prioritization_graph(),
        graph_modules[1].build_authoritative_tailoring_decision_graph(),
        graph_modules[2].build_authoritative_operator_review_graph(),
    ]

    assert [len(graph.nodes) for graph in builders] == [1, 1, 1]
    assert sum(len(graph.nodes) for graph in builders) == 3


def test_run006_remains_absent():
    repository = Path(__file__).resolve().parents[1]
    assert not any(
        "run_006" in path.name.lower() or "run-006" in path.name.lower()
        for path in repository.rglob("*")
        if ".git" not in path.parts and "__pycache__" not in path.parts
    )
