from __future__ import annotations

import ast
import csv
from copy import deepcopy
import importlib
import json
from pathlib import Path
import socket
import sqlite3
import sys

import pytest

import application_execution_queue as queue
from src.agents import job_prioritization_agent as priority
from src.agents import job_prioritization_graph_integration
from src.agents import operator_review_agent


GRAPH_MODULE = "src.agents.job_prioritization_authoritative_graph"
GRAPH_FLAG = queue.AUTHORITATIVE_JOB_PRIORITIZATION_LANGGRAPH_FLAG


def _row(**overrides):
    row = {
        "job_doc_id": "job-1",
        "job_company": "Example Co",
        "job_title": "Backend Engineer",
        "job_location": "Remote",
        "source": "greenhouse",
        "action": "APPLY",
        "winner_resume": "resume.pdf",
        "winner_score": "0.750000",
        "winner_missing_requirements": "",
        "score_gap": "0.100000",
        "deterministic_winner_available": "true",
        "deterministic_winner_score": "0.750000",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
        "requires_manual_review": "false",
        "variant_review_required": "false",
        "selection_signal": "deterministic_winner",
        "resolved_resume_source": "deterministic_winner",
        "resolved_selection_status": "resolved",
    }
    row.update(overrides)
    return row


def _metadata():
    return {
        "pipeline_run_id": "run-13c",
        "owner_user_id": "owner-13c",
        "context_id": "job_priority:run-13c",
        "source_artifact_path": "queue.csv",
    }


def _route(rows, *, env):
    return queue._build_authoritative_priority_shared_result(
        rows=rows,
        env=env,
        **_metadata(),
    )


def _configure_main(monkeypatch, tmp_path, rows, *, graph_enabled):
    output = tmp_path / "application_execution_queue.csv"
    priority_output = tmp_path / "priority.csv"
    tailoring_output = tmp_path / "tailoring.csv"
    operator_output = tmp_path / "operator.csv"
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
            "--priority-output-csv",
            str(priority_output),
            "--tailoring-decision-output-csv",
            str(tailoring_output),
            "--operator-review-output-csv",
            str(operator_output),
        ],
    )
    monkeypatch.setenv(GRAPH_FLAG, "1" if graph_enabled else "0")
    monkeypatch.delenv(
        queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG,
        raising=False,
    )
    monkeypatch.delenv(
        queue.PRODUCTION_SHADOW_JOB_PRIORITY_OWNER_FLAG,
        raising=False,
    )
    monkeypatch.setenv(priority.TRACE_ENABLED_ENV, "0")
    return {
        "queue": output,
        "priority": priority_output,
        "tailoring": tailoring_output,
        "operator": operator_output,
    }


def test_graph_contract_real_stategraph_one_node_and_canonical_callable():
    graph_owner = importlib.import_module(GRAPH_MODULE)
    graph = graph_owner.build_authoritative_job_prioritization_graph()

    assert type(graph).__name__ == "StateGraph"
    assert type(graph).__module__.startswith("langgraph.")
    assert graph_owner.AUTHORITATIVE_JOB_PRIORITIZATION_GRAPH_VERSION == (
        "authoritative-job-prioritization-graph-v1"
    )
    assert graph_owner.AUTHORITATIVE_JOB_PRIORITIZATION_STATE_VERSION == (
        "authoritative-job-prioritization-state-v1"
    )
    assert graph_owner.AUTHORITATIVE_JOB_PRIORITIZATION_PRODUCTION_NODE_COUNT == 1
    assert set(graph.nodes) == {
        graph_owner.AUTHORITATIVE_JOB_PRIORITIZATION_NODE
    }
    assert graph_owner.AUTHORITATIVE_JOB_PRIORITIZATION_NODE == (
        "build_job_prioritization_shared_result"
    )
    assert set(
        graph_owner.AuthoritativeJobPrioritizationState.__annotations__
    ) == {
        "state_version",
        "execution_mode",
        "pipeline_run_id",
        "owner_user_id",
        "context_id",
        "source_artifact_path",
        "queue_rows",
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
    assert "build_job_prioritization_shared_result" in called_attributes
    assert not {
        "render_job_prioritization_recommendations",
        "render_job_prioritization_recommendation_rows",
    }.intersection(called_attributes)


def test_gate_defaults_off_and_does_not_import_or_construct_graph(monkeypatch):
    sys.modules.pop(GRAPH_MODULE, None)
    calls = []
    real_builder = queue.build_job_prioritization_shared_result

    def counted(**kwargs):
        calls.append(deepcopy(kwargs))
        return real_builder(**kwargs)

    monkeypatch.setattr(
        queue,
        "build_job_prioritization_shared_result",
        counted,
    )
    rows = [_row()]
    before = deepcopy(rows)
    shared, metadata = _route(rows, env={})

    assert calls and len(calls) == 1
    assert GRAPH_MODULE not in sys.modules
    assert metadata["execution_mode"] == "direct"
    assert metadata["production_node_count"] == 0
    assert metadata["invocation_count"] == 1
    assert shared["contract_version"] == (
        priority.JOB_PRIORITIZATION_SHARED_RESULT_VERSION
    )
    assert rows == before


def test_gate_on_constructs_graph_and_invokes_shared_owner_exactly_once(
    monkeypatch,
):
    graph_owner = importlib.import_module(GRAPH_MODULE)
    owner_calls = []
    graph_build_calls = []
    real_owner = priority.build_job_prioritization_shared_result
    real_graph_builder = (
        graph_owner.build_authoritative_job_prioritization_graph
    )

    def counted_owner(**kwargs):
        owner_calls.append(deepcopy(kwargs))
        return real_owner(**kwargs)

    def counted_graph_builder():
        graph_build_calls.append(1)
        return real_graph_builder()

    monkeypatch.setattr(
        priority,
        "build_job_prioritization_shared_result",
        counted_owner,
    )
    monkeypatch.setattr(
        graph_owner,
        "build_authoritative_job_prioritization_graph",
        counted_graph_builder,
    )
    monkeypatch.setattr(
        queue,
        "build_job_prioritization_shared_result",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("direct route also executed")
        ),
    )
    shared, metadata = _route([_row()], env={GRAPH_FLAG: "1"})

    assert len(graph_build_calls) == 1
    assert len(owner_calls) == 1
    assert metadata["execution_mode"] == "langgraph"
    assert metadata["production_node_count"] == 1
    assert metadata["invocation_count"] == 1
    assert shared["contract_version"] == (
        priority.JOB_PRIORITIZATION_SHARED_RESULT_VERSION
    )


@pytest.mark.parametrize(
    ("conflict_flag", "failure_code"),
    [
        (
            queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG,
            "authoritative_priority_conflict_diagnostic_verification",
        ),
        (
            queue.PRODUCTION_SHADOW_JOB_PRIORITY_OWNER_FLAG,
            "authoritative_priority_conflict_production_shadow_owner",
        ),
    ],
)
def test_conflicting_owner_modes_fail_before_any_invocation(
    monkeypatch,
    conflict_flag,
    failure_code,
):
    direct_calls = []
    monkeypatch.setattr(
        queue,
        "build_job_prioritization_shared_result",
        lambda **kwargs: direct_calls.append(kwargs),
    )

    with pytest.raises(
        queue.AuthoritativeJobPrioritizationGateConflictError
    ) as captured:
        _route(
            [_row()],
            env={GRAPH_FLAG: "1", conflict_flag: "true"},
        )

    assert captured.value.failure_code == failure_code
    assert str(captured.value) == failure_code
    assert direct_calls == []


def test_completed_artifact_shadow_parity_gate_remains_compatible():
    shared, metadata = _route(
        [_row()],
        env={
            GRAPH_FLAG: "1",
            "APPLYLENS_ARTIFACT_ONLY_PRODUCTION_SHADOW_ENABLED": "1",
        },
    )
    assert metadata["execution_mode"] == "langgraph"
    assert shared["rendered_rows"][0]["job_id"] == "job-1"


def test_graph_failure_propagates_without_direct_fallback(monkeypatch):
    graph_owner = importlib.import_module(GRAPH_MODULE)
    direct_calls = []

    def graph_failure(**_kwargs):
        raise RuntimeError("authoritative_owner_failed")

    monkeypatch.setattr(
        priority,
        "build_job_prioritization_shared_result",
        graph_failure,
    )
    monkeypatch.setattr(
        queue,
        "build_job_prioritization_shared_result",
        lambda **kwargs: direct_calls.append(kwargs),
    )

    with pytest.raises(RuntimeError, match="authoritative_owner_failed"):
        _route([_row()], env={GRAPH_FLAG: "1"})

    assert graph_owner is sys.modules[GRAPH_MODULE]
    assert direct_calls == []


def test_graph_failure_causes_no_downstream_artifact_writes(
    monkeypatch,
    tmp_path,
):
    paths = _configure_main(
        monkeypatch,
        tmp_path,
        [_row()],
        graph_enabled=True,
    )
    write_calls = []

    def graph_failure(**_kwargs):
        raise RuntimeError("authoritative_owner_failed")

    monkeypatch.setattr(
        priority,
        "build_job_prioritization_shared_result",
        graph_failure,
    )
    monkeypatch.setattr(
        queue,
        "write_job_prioritization_artifacts",
        lambda **kwargs: write_calls.append(("priority", kwargs)),
    )
    monkeypatch.setattr(
        queue,
        "write_tailoring_decision_artifacts",
        lambda **kwargs: write_calls.append(("tailoring", kwargs)),
    )
    monkeypatch.setattr(
        queue,
        "write_operator_review_artifacts",
        lambda **kwargs: write_calls.append(("operator", kwargs)),
    )

    with pytest.raises(RuntimeError, match="authoritative_owner_failed"):
        queue.main()

    assert write_calls == []
    assert paths["queue"].is_file()
    assert not paths["priority"].exists()
    assert not paths["tailoring"].exists()
    assert not paths["operator"].exists()


def test_direct_and_graph_results_order_and_deep_copy_are_identical():
    rows = [
        _row(),
        _row(
            job_doc_id="job-2",
            job_company="Second Co",
            action="MAYBE_TAILOR",
            winner_score="0.650000",
            deterministic_winner_score="0.650000",
        ),
    ]
    before = deepcopy(rows)
    direct, direct_metadata = _route(rows, env={})
    graphed, graph_metadata = _route(rows, env={GRAPH_FLAG: "1"})

    assert graphed == direct
    assert [
        row["job_id"] for row in graphed["rendered_rows"]
    ] == ["job-1", "job-2"]
    assert direct_metadata["execution_mode"] == "direct"
    assert graph_metadata["execution_mode"] == "langgraph"
    assert rows == before
    graphed["rendered_rows"][0]["advisory_priority"] = "changed"
    graphed["payload"]["input"]["rows"][0]["company"] = "changed"
    assert direct["rendered_rows"][0]["advisory_priority"] == "apply_now"
    assert direct["payload"]["input"]["rows"][0]["company"] == "Example Co"
    assert rows == before


def test_direct_and_graph_artifacts_and_downstream_rows_are_identical(
    tmp_path,
):
    rows = [_row(), _row(job_doc_id="job-2", job_company="Second Co")]
    metadata = _metadata()
    direct, _ = _route(rows, env={})
    graphed, _ = _route(rows, env={GRAPH_FLAG: "1"})
    direct_csv = tmp_path / "direct.csv"
    direct_summary = tmp_path / "direct.json"
    graph_csv = tmp_path / "graph.csv"
    graph_summary = tmp_path / "graph.json"

    priority.write_job_prioritization_artifacts(
        rows=rows,
        output_csv_path=direct_csv,
        summary_json_path=direct_summary,
        shared_result=direct,
        pipeline_run_id=metadata["pipeline_run_id"],
        owner_user_id=metadata["owner_user_id"],
        source_artifact_path=metadata["source_artifact_path"],
    )
    priority.write_job_prioritization_artifacts(
        rows=rows,
        output_csv_path=graph_csv,
        summary_json_path=graph_summary,
        shared_result=graphed,
        pipeline_run_id=metadata["pipeline_run_id"],
        owner_user_id=metadata["owner_user_id"],
        source_artifact_path=metadata["source_artifact_path"],
    )

    assert graph_csv.read_bytes() == direct_csv.read_bytes()
    assert graph_summary.read_bytes() == direct_summary.read_bytes()
    with graph_csv.open(encoding="utf-8", newline="") as handle:
        assert list(csv.DictReader(handle)) == graphed["rendered_rows"]
    direct_overlay = queue._with_priority_overlay(
        rows,
        env={},
        shared_result=direct,
    )
    graph_overlay = queue._with_priority_overlay(
        rows,
        env={},
        shared_result=graphed,
    )
    assert graph_overlay == direct_overlay
    direct_tailoring = queue._with_tailoring_decision_overlay(direct_overlay)
    graph_tailoring = queue._with_tailoring_decision_overlay(graph_overlay)
    assert graph_tailoring == direct_tailoring
    assert operator_review_agent.render_operator_review_rows(
        graph_tailoring
    ) == operator_review_agent.render_operator_review_rows(
        direct_tailoring
    )


@pytest.mark.parametrize("graph_enabled", [False, True])
def test_main_invokes_each_requested_consumer_once(
    monkeypatch,
    tmp_path,
    graph_enabled,
):
    paths = _configure_main(
        monkeypatch,
        tmp_path,
        [_row()],
        graph_enabled=graph_enabled,
    )
    calls = {
        "direct_owner": 0,
        "graph_owner": 0,
        "priority_writer": 0,
        "priority_overlay": 0,
        "tailoring_writer": 0,
        "tailoring_overlay": 0,
        "operator_writer": 0,
        "priority_trace": 0,
    }
    real_direct_owner = queue.build_job_prioritization_shared_result
    real_graph_owner = priority.build_job_prioritization_shared_result
    real_priority_writer = queue.write_job_prioritization_artifacts
    real_priority_overlay = queue._with_priority_overlay
    real_tailoring_writer = queue.write_tailoring_decision_artifacts
    real_tailoring_overlay = queue._with_tailoring_decision_overlay
    real_operator_writer = queue.write_operator_review_artifacts

    def direct_owner(**kwargs):
        calls["direct_owner"] += 1
        return real_direct_owner(**kwargs)

    def graph_owner(**kwargs):
        calls["graph_owner"] += 1
        return real_graph_owner(**kwargs)

    def counted(name, callback):
        def wrapper(*args, **kwargs):
            calls[name] += 1
            return callback(*args, **kwargs)

        return wrapper

    monkeypatch.setattr(
        queue,
        "build_job_prioritization_shared_result",
        direct_owner,
    )
    monkeypatch.setattr(
        priority,
        "build_job_prioritization_shared_result",
        graph_owner,
    )
    monkeypatch.setattr(
        queue,
        "write_job_prioritization_artifacts",
        counted("priority_writer", real_priority_writer),
    )
    monkeypatch.setattr(
        queue,
        "_with_priority_overlay",
        counted("priority_overlay", real_priority_overlay),
    )
    monkeypatch.setattr(
        queue,
        "write_tailoring_decision_artifacts",
        counted("tailoring_writer", real_tailoring_writer),
    )
    monkeypatch.setattr(
        queue,
        "_with_tailoring_decision_overlay",
        counted("tailoring_overlay", real_tailoring_overlay),
    )
    monkeypatch.setattr(
        queue,
        "write_operator_review_artifacts",
        counted("operator_writer", real_operator_writer),
    )
    monkeypatch.setattr(
        queue,
        "record_job_prioritization_agent_trace",
        lambda **_kwargs: (
            calls.__setitem__(
                "priority_trace",
                calls["priority_trace"] + 1,
            )
            or {"attempted": False}
        ),
    )

    queue.main()

    assert calls == {
        "direct_owner": 0 if graph_enabled else 1,
        "graph_owner": 1 if graph_enabled else 0,
        "priority_writer": 1,
        "priority_overlay": 1,
        "tailoring_writer": 1,
        "tailoring_overlay": 1,
        "operator_writer": 1,
        "priority_trace": 1,
    }
    assert all(path.is_file() for path in paths.values())


def _trace_payload(shared):
    calls = []

    class FakeTrace:
        @staticmethod
        def create_agent_run(*, record):
            calls.append(("create", deepcopy(record)))
            return {"run": {"agent_run_id": "run-record-1"}}

        @staticmethod
        def record_agent_step(*, record):
            calls.append(("step", deepcopy(record)))
            return {"step": {"agent_step_id": "step-record-1"}}

        @staticmethod
        def complete_agent_step(**kwargs):
            calls.append(("complete_step", deepcopy(kwargs)))
            return {}

        @staticmethod
        def complete_agent_run(**kwargs):
            calls.append(("complete_run", deepcopy(kwargs)))
            return {}

    metadata = _metadata()
    result = priority.record_job_prioritization_agent_trace(
        rows=[_row()],
        source_artifact_path=metadata["source_artifact_path"],
        env={
            priority.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": metadata["owner_user_id"],
            "JOB_APP_PIPELINE_RUN_ID": metadata["pipeline_run_id"],
        },
        trace_module=FakeTrace,
        shared_result=shared,
    )
    return result, calls


def test_trace_payloads_are_equivalent():
    direct, _ = _route([_row()], env={})
    graphed, _ = _route([_row()], env={GRAPH_FLAG: "1"})
    direct_result, direct_calls = _trace_payload(direct)
    graph_result, graph_calls = _trace_payload(graphed)

    assert direct_result["summary"] == graph_result["summary"]
    assert direct_result["validation"] == graph_result["validation"]
    assert direct_calls[0][1]["summary_json"] == graph_calls[0][1][
        "summary_json"
    ]
    assert direct_calls[1][1]["input_json"] == graph_calls[1][1][
        "input_json"
    ]
    assert direct_calls[2][1]["output_json"] == graph_calls[2][1][
        "output_json"
    ]
    assert direct_calls[2][1]["validation_json"] == graph_calls[2][1][
        "validation_json"
    ]


def test_diagnostic_verification_receives_shared_rows_only_when_allowed(
    monkeypatch,
    capsys,
):
    rows = [_row()]
    shared, metadata = _route(
        rows,
        env={queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG: "1"},
    )
    diagnostic_calls = []

    def diagnostic(**kwargs):
        diagnostic_calls.append(deepcopy(kwargs["direct_rendered_rows"]))
        return {
            "classification": "matched",
            "direct_output_authoritative": True,
            "graph_output_applied": False,
        }

    monkeypatch.setattr(
        job_prioritization_graph_integration,
        "verify_direct_job_prioritization_rows",
        diagnostic,
    )
    queue._with_priority_overlay(
        rows,
        env={queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG: "1"},
        shared_result=shared,
    )

    assert metadata["execution_mode"] == "direct"
    assert diagnostic_calls == [shared["rendered_rows"]]
    assert '"graph_output_applied":false' in capsys.readouterr().out


def test_execution_metadata_is_bounded_and_contains_no_raw_rows():
    rows = [_row(job_company="Private Company", winner_resume="private.pdf")]
    _shared, metadata = _route(rows, env={GRAPH_FLAG: "1"})
    encoded = json.dumps(metadata, sort_keys=True)

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
    assert "Private Company" not in encoded
    assert "private.pdf" not in encoded
    assert "job-1" not in encoded
    assert "rows" not in metadata


def test_graph_route_has_zero_external_activity_or_credential_reads(
    monkeypatch,
):
    external_calls = []
    env_reads = []

    class TrackingEnv(dict):
        def get(self, key, default=None):
            env_reads.append(key)
            return super().get(key, default)

    def blocked(*args, **kwargs):
        external_calls.append((args, kwargs))
        raise AssertionError("external activity")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(sqlite3, "connect", blocked)
    shared, metadata = _route(
        [_row()],
        env=TrackingEnv({GRAPH_FLAG: "1"}),
    )

    assert external_calls == []
    assert all(
        marker not in key.upper()
        for key in env_reads
        for marker in ("CREDENTIAL", "API_KEY", "DATABASE", "DOTENV")
    )
    assert metadata["read_only"] is True
    assert shared["rendered_rows"][0]["job_id"] == "job-1"


def test_authoritative_graph_imports_no_provider_persistence_or_credentials():
    graph_owner = importlib.import_module(GRAPH_MODULE)
    source = Path(graph_owner.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    import_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not {
        "dotenv",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "subprocess",
    }.intersection(import_roots)
    lowered = source.lower()
    assert "checkpointer" not in lowered
    assert "provider_client" not in lowered
    assert "application_submission" not in lowered
    assert "ats_submission" not in lowered
