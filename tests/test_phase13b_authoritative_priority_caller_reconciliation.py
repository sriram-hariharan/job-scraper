from __future__ import annotations

import csv
from copy import deepcopy
import json
from pathlib import Path
import socket
import sqlite3
import sys

import pytest

import application_execution_queue as queue
from src.agents import job_prioritization_agent as priority
from src.agents import job_prioritization_graph_integration as graph_integration
from src.agents import operator_review_agent


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


def _shared(rows=None, **metadata):
    return priority.build_job_prioritization_shared_result(
        rows=deepcopy(rows or [_row()]),
        **metadata,
    )


def _run_queue_main(monkeypatch, tmp_path, rows, *extra_args):
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
    monkeypatch.setenv(priority.TRACE_ENABLED_ENV, "0")
    monkeypatch.delenv(queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG, raising=False)
    queue.main()
    return output


def test_shared_result_contract_version_determinism_and_containment():
    rows = [_row(), _row(job_doc_id="job-2", job_company="Second Co")]
    before = deepcopy(rows)

    first = _shared(
        rows,
        pipeline_run_id="run-1",
        owner_user_id="owner-1",
        source_artifact_path="queue.csv",
    )
    second = _shared(
        rows,
        pipeline_run_id="run-1",
        owner_user_id="owner-1",
        source_artifact_path="queue.csv",
    )

    assert first == second
    assert rows == before
    assert set(first) == {"contract_version", "payload", "rendered_rows"}
    assert (
        first["contract_version"]
        == priority.JOB_PRIORITIZATION_SHARED_RESULT_VERSION
        == "job-prioritization-shared-result-v1"
    )
    assert len(first["rendered_rows"]) == 2
    first["rendered_rows"][0]["advisory_priority"] = "changed"
    first["payload"]["input"]["rows"][0]["company"] = "changed"
    assert second["rendered_rows"][0]["advisory_priority"] == "apply_now"
    assert second["payload"]["input"]["rows"][0]["company"] == "Example Co"
    assert rows == before


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update({"contract_version": "wrong"}),
        lambda value: value["rendered_rows"][0].update(
            {"advisory_priority": "skip_for_now"}
        ),
        lambda value: value["payload"]["validation"].update(
            {"validation_status": "failed"}
        ),
        lambda value: value["payload"]["input"].update({"row_count": 2}),
    ],
)
def test_malformed_or_mismatched_shared_result_fails_closed(mutate):
    rows = [_row()]
    shared = _shared(rows)
    mutate(shared)

    with pytest.raises((TypeError, ValueError)):
        priority.validate_job_prioritization_shared_result(
            shared,
            expected_rows=rows,
        )


def test_writer_reuses_shared_result_without_rerender_and_preserves_bytes(
    monkeypatch,
    tmp_path,
):
    rows = [
        _row(),
        _row(
            job_doc_id="job-2",
            action="MAYBE_TAILOR",
            deterministic_winner_score="0.650000",
            winner_score="0.650000",
        ),
    ]
    metadata = {
        "pipeline_run_id": "run-1",
        "owner_user_id": "owner-1",
        "source_artifact_path": "queue.csv",
    }
    baseline_csv = tmp_path / "baseline.csv"
    baseline_summary = tmp_path / "baseline.json"
    priority.write_job_prioritization_artifacts(
        rows=rows,
        output_csv_path=baseline_csv,
        summary_json_path=baseline_summary,
        **metadata,
    )
    shared = _shared(rows, **metadata)

    def prohibited(*args, **kwargs):
        raise AssertionError("recommendation logic reran")

    monkeypatch.setattr(
        priority,
        "render_job_prioritization_recommendations",
        prohibited,
    )
    monkeypatch.setattr(
        priority,
        "render_job_prioritization_recommendation_rows",
        prohibited,
    )
    actual_csv = tmp_path / "actual.csv"
    actual_summary = tmp_path / "actual.json"
    result = priority.write_job_prioritization_artifacts(
        rows=rows,
        output_csv_path=actual_csv,
        summary_json_path=actual_summary,
        shared_result=shared,
        **metadata,
    )

    assert actual_csv.read_bytes() == baseline_csv.read_bytes()
    assert actual_summary.read_bytes() == baseline_summary.read_bytes()
    assert result["row_count"] == len(shared["rendered_rows"])
    assert result["validation"] == shared["payload"]["validation"]
    assert result["summary"] == shared["payload"]["summary"]
    with actual_csv.open(encoding="utf-8", newline="") as handle:
        assert list(csv.DictReader(handle)) == shared["rendered_rows"]


def test_overlay_reuses_shared_rows_and_contains_consumer_mutation(monkeypatch):
    rows = [_row()]
    before = deepcopy(rows)
    shared = _shared(rows)
    shared_before = deepcopy(shared)

    monkeypatch.setattr(
        queue,
        "render_job_prioritization_recommendation_rows",
        lambda _rows: (_ for _ in ()).throw(
            AssertionError("row renderer reran")
        ),
    )
    overlay = queue._with_priority_overlay(
        rows,
        env={},
        shared_result=shared,
    )
    overlay[0]["advisory_priority"] = "changed"

    assert rows == before
    assert shared == shared_before


def test_downstream_tailoring_and_operator_inputs_remain_equivalent():
    rows = [_row()]
    direct_overlay = queue._with_priority_overlay(rows, env={})
    shared_overlay = queue._with_priority_overlay(
        rows,
        env={},
        shared_result=_shared(rows),
    )
    assert shared_overlay == direct_overlay

    direct_tailoring = queue._with_tailoring_decision_overlay(direct_overlay)
    shared_tailoring = queue._with_tailoring_decision_overlay(shared_overlay)
    assert shared_tailoring == direct_tailoring
    assert operator_review_agent.render_operator_review_rows(
        shared_tailoring
    ) == operator_review_agent.render_operator_review_rows(direct_tailoring)


def test_default_authoritative_queue_path_computes_recommendations_once(
    monkeypatch,
    tmp_path,
):
    calls = []
    real_builder = priority.build_job_prioritization_agent_output_payload

    def counted(*args, **kwargs):
        calls.append(1)
        return real_builder(*args, **kwargs)

    monkeypatch.setattr(
        priority,
        "build_job_prioritization_agent_output_payload",
        counted,
    )
    rows = [_row()]
    before = deepcopy(rows)
    output = _run_queue_main(monkeypatch, tmp_path, rows)

    assert calls == [1]
    assert rows == before
    assert output.is_file()


def test_renderer_failure_propagates_before_priority_writer_boundary(
    monkeypatch,
    tmp_path,
):
    writer_calls = []

    def render_failure(**kwargs):
        raise RuntimeError("render_failed")

    monkeypatch.setattr(
        queue,
        "build_job_prioritization_shared_result",
        render_failure,
    )
    monkeypatch.setattr(
        queue,
        "write_job_prioritization_artifacts",
        lambda **kwargs: writer_calls.append(kwargs),
    )

    with pytest.raises(RuntimeError, match="render_failed"):
        _run_queue_main(
            monkeypatch,
            tmp_path,
            [_row()],
            "--priority-output-csv",
            str(tmp_path / "priority.csv"),
        )
    assert writer_calls == []


def test_priority_file_write_failure_is_advisory_and_does_not_rerender(
    monkeypatch,
    tmp_path,
    capsys,
):
    calls = []
    real_builder = priority.build_job_prioritization_agent_output_payload

    def counted(*args, **kwargs):
        calls.append(1)
        return real_builder(*args, **kwargs)

    monkeypatch.setattr(
        priority,
        "build_job_prioritization_agent_output_payload",
        counted,
    )
    monkeypatch.setattr(
        queue,
        "write_job_prioritization_artifacts",
        lambda **kwargs: (_ for _ in ()).throw(OSError("write_failed")),
    )
    _run_queue_main(
        monkeypatch,
        tmp_path,
        [_row()],
        "--priority-output-csv",
        str(tmp_path / "priority.csv"),
    )

    assert calls == [1]
    assert "Job prioritization advisory artifact skipped: write_failed" in (
        capsys.readouterr().out
    )


def test_verification_gate_receives_same_shared_rows_and_off_is_inert(
    monkeypatch,
    capsys,
):
    rows = [_row()]
    shared = _shared(rows)
    calls = []

    def diagnostic(**kwargs):
        calls.append(deepcopy(kwargs["direct_rendered_rows"]))
        return {
            "classification": "matched",
            "direct_output_authoritative": True,
            "graph_output_applied": False,
        }

    monkeypatch.setattr(
        graph_integration,
        "verify_direct_job_prioritization_rows",
        diagnostic,
    )
    queue._with_priority_overlay(rows, env={}, shared_result=shared)
    assert calls == []
    assert capsys.readouterr().out == ""

    queue._with_priority_overlay(
        rows,
        env={queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG: "1"},
        shared_result=shared,
    )
    assert calls == [shared["rendered_rows"]]
    rendered = capsys.readouterr().out
    assert "Job prioritization graph verification:" in rendered
    assert '"graph_output_applied":false' in rendered


def test_trace_disabled_is_inert_and_enabled_reuses_shared_payload(
    monkeypatch,
):
    rows = [_row()]
    metadata = {
        "pipeline_run_id": "run-1",
        "owner_user_id": "owner-1",
        "source_artifact_path": "queue.csv",
    }
    shared = _shared(rows, **metadata)

    monkeypatch.setattr(
        priority,
        "render_job_prioritization_recommendations",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("trace recomputed recommendations")
        ),
    )
    assert priority.record_job_prioritization_agent_trace(
        rows=rows,
        env={},
        shared_result={"invalid": True},
    ) == {"attempted": False, "reason": "trace_disabled"}

    calls = []

    class FakeTrace:
        @staticmethod
        def create_agent_run(*, record):
            calls.append(("create", record))
            return {"run": {"agent_run_id": "run-record-1"}}

        @staticmethod
        def record_agent_step(*, record):
            calls.append(("step", record))
            return {"step": {"agent_step_id": "step-record-1"}}

        @staticmethod
        def complete_agent_step(**kwargs):
            calls.append(("complete_step", kwargs))
            return {}

        @staticmethod
        def complete_agent_run(**kwargs):
            calls.append(("complete_run", kwargs))
            return {}

    result = priority.record_job_prioritization_agent_trace(
        rows=rows,
        source_artifact_path=metadata["source_artifact_path"],
        env={
            priority.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": metadata["owner_user_id"],
            "JOB_APP_PIPELINE_RUN_ID": metadata["pipeline_run_id"],
        },
        trace_module=FakeTrace,
        shared_result=shared,
    )
    assert result["recorded"] is True
    assert result["summary"] == shared["payload"]["summary"]
    assert [name for name, _payload in calls] == [
        "create",
        "step",
        "complete_step",
        "complete_run",
    ]


def test_shared_path_introduces_no_network_or_database_activity(
    monkeypatch,
    tmp_path,
):
    prohibited = []

    def blocked(*args, **kwargs):
        prohibited.append((args, kwargs))
        raise AssertionError("external activity")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(sqlite3, "connect", blocked)
    rows = [_row()]
    shared = _shared(rows)
    priority.write_job_prioritization_artifacts(
        rows=rows,
        output_csv_path=tmp_path / "priority.csv",
        shared_result=shared,
    )

    assert prohibited == []
    assert not any(
        marker in json.dumps(shared, sort_keys=True).lower()
        for marker in ("credential", "provider_response", "ats_authorized")
    )
