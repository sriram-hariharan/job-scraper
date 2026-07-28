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
from src.agents import operator_review_agent
from src.agents import tailoring_decision_agent as tailoring


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


def _metadata():
    return {
        "pipeline_run_id": "run-14b",
        "owner_user_id": "owner-14b",
        "source_artifact_path": "application_execution_queue.csv",
    }


def _shared(rows=None, **metadata):
    return tailoring.build_tailoring_decision_shared_result(
        rows=deepcopy(rows or [_row()]),
        **metadata,
    )


def _run_queue_main(
    monkeypatch,
    tmp_path,
    rows,
    *extra_args,
    trace_enabled=False,
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
        tailoring.TRACE_ENABLED_ENV,
        "1" if trace_enabled else "0",
    )
    monkeypatch.delenv(
        queue.AUTHORITATIVE_JOB_PRIORITIZATION_LANGGRAPH_FLAG,
        raising=False,
    )
    monkeypatch.delenv(
        queue.JOB_PRIORITIZATION_GRAPH_VERIFY_FLAG,
        raising=False,
    )
    monkeypatch.delenv(
        queue.PRODUCTION_SHADOW_JOB_PRIORITY_OWNER_FLAG,
        raising=False,
    )
    queue.main()
    return output


def test_shared_result_contract_version_sections_determinism_and_containment():
    rows = [
        _row(),
        _row(
            job_doc_id="job-2",
            job_company="Second Co",
            job_title="Platform Engineer",
            deterministic_winner_score="0.850000",
            winner_score="0.850000",
            missing_requirement_count="0",
            winner_missing_requirements="",
            resolved_missing_requirements="",
        ),
    ]
    before = deepcopy(rows)
    metadata = _metadata()

    first = _shared(rows, **metadata)
    second = _shared(rows, **metadata)

    assert first == second
    assert rows == before
    assert set(first) == {"contract_version", "payload", "rendered_rows"}
    assert set(first["payload"]) == {
        "input",
        "output",
        "validation",
        "summary",
    }
    assert (
        first["contract_version"]
        == tailoring.TAILORING_DECISION_SHARED_RESULT_VERSION
        == "tailoring-decision-shared-result-v1"
    )
    assert list(first["rendered_rows"][0]) == (
        tailoring.TAILORING_DECISION_FIELDNAMES
    )
    assert [row["job_id"] for row in first["rendered_rows"]] == [
        "job-1",
        "job-2",
    ]

    first["payload"]["input"]["rows"][0]["company"] = "mutated"
    first["payload"]["output"]["decisions"][0][
        "tailoring_reason_codes"
    ].append("mutated")
    first["rendered_rows"][0]["tailoring_decision"] = "do_not_tailor"
    assert second["payload"]["input"]["rows"][0]["company"] == "Example Co"
    assert second["payload"]["output"]["decisions"][0][
        "tailoring_reason_codes"
    ] == ["high_score_light_touch"]
    assert second["rendered_rows"][0]["tailoring_decision"] == (
        "light_tailoring"
    )
    assert rows == before


def test_shared_result_invokes_canonical_decision_logic_exactly_once(
    monkeypatch,
):
    calls = []
    real = tailoring.build_tailoring_decision_agent_output_payload

    def counted(*args, **kwargs):
        calls.append(deepcopy(kwargs["input_payload"]))
        return real(*args, **kwargs)

    monkeypatch.setattr(
        tailoring,
        "build_tailoring_decision_agent_output_payload",
        counted,
    )
    shared = _shared([_row()])

    assert len(calls) == 1
    assert shared["rendered_rows"][0]["tailoring_decision"] == (
        shared["payload"]["output"]["decisions"][0]["tailoring_decision"]
    )
    assert shared["rendered_rows"][0]["tailoring_reason_codes"] == "|".join(
        shared["payload"]["output"]["decisions"][0][
            "tailoring_reason_codes"
        ]
    )


def _wrong_version(value):
    value["contract_version"] = "wrong"


def _missing_section(value):
    value["payload"].pop("summary")


def _row_count_mismatch(value):
    value["payload"]["input"]["row_count"] = 99


def _identity_mismatch(value):
    value["payload"]["output"]["decisions"][0]["job_id"] = "other-job"


def _ordering_mismatch(value):
    value["payload"]["output"]["decisions"].reverse()


def _invalid_decision(value):
    value["payload"]["output"]["decisions"][0][
        "tailoring_decision"
    ] = "invalid"


def _rendered_row_mismatch(value):
    value["rendered_rows"][0]["tailoring_reason_codes"] = "wrong"


def _duplicate_identity(value):
    value["payload"]["input"]["rows"][1]["job_id"] = "job-1"


def _missing_identity(value):
    value["payload"]["input"]["rows"][0]["job_id"] = ""


@pytest.mark.parametrize(
    "mutate",
    [
        _wrong_version,
        _missing_section,
        _row_count_mismatch,
        _identity_mismatch,
        _ordering_mismatch,
        _invalid_decision,
        _rendered_row_mismatch,
        _duplicate_identity,
        _missing_identity,
    ],
)
def test_malformed_shared_result_fails_closed(mutate):
    rows = [
        _row(),
        _row(
            job_doc_id="job-2",
            job_company="Second Co",
            job_title="Platform Engineer",
        ),
    ]
    shared = _shared(rows)
    mutate(shared)

    with pytest.raises((TypeError, ValueError)):
        tailoring.validate_tailoring_decision_shared_result(
            shared,
            expected_rows=rows,
        )


def test_shared_result_metadata_and_expected_rows_fail_closed():
    rows = [_row()]
    metadata = _metadata()
    shared = _shared(rows, **metadata)

    with pytest.raises(ValueError, match="metadata_mismatch"):
        tailoring.validate_tailoring_decision_shared_result(
            shared,
            expected_rows=rows,
            pipeline_run_id="other-run",
        )
    with pytest.raises(ValueError, match="input_mismatch"):
        tailoring.validate_tailoring_decision_shared_result(
            shared,
            expected_rows=[_row(job_company="Changed Co")],
        )


def test_writer_shared_handoff_preserves_csv_summary_and_validation(
    monkeypatch,
    tmp_path,
):
    rows = [
        _row(),
        _row(
            job_doc_id="job-2",
            job_company="Second Co",
            job_title="Platform Engineer",
            advisory_priority="tailor_first",
            deterministic_winner_score="0.650000",
            winner_score="0.650000",
        ),
    ]
    metadata = _metadata()
    baseline_csv = tmp_path / "baseline.csv"
    baseline_summary = tmp_path / "baseline.json"
    tailoring.write_tailoring_decision_artifacts(
        rows=rows,
        output_csv_path=baseline_csv,
        summary_json_path=baseline_summary,
        **metadata,
    )
    shared = _shared(rows, **metadata)

    def prohibited(*args, **kwargs):
        raise AssertionError("tailoring decisions rerendered")

    monkeypatch.setattr(tailoring, "render_tailoring_decisions", prohibited)
    monkeypatch.setattr(
        tailoring,
        "render_tailoring_decision_rows",
        prohibited,
    )
    actual_csv = tmp_path / "actual.csv"
    actual_summary = tmp_path / "actual.json"
    result = tailoring.write_tailoring_decision_artifacts(
        rows=rows,
        output_csv_path=actual_csv,
        summary_json_path=actual_summary,
        shared_result=shared,
        **metadata,
    )

    assert actual_csv.read_bytes() == baseline_csv.read_bytes()
    assert actual_summary.read_bytes() == baseline_summary.read_bytes()
    assert result["summary"] == shared["payload"]["summary"]
    assert result["validation"] == shared["payload"]["validation"]
    assert result["row_count"] == 2
    with actual_csv.open(encoding="utf-8", newline="") as handle:
        assert list(csv.DictReader(handle)) == shared["rendered_rows"]


def test_overlay_shared_handoff_preserves_order_and_operator_input(
    monkeypatch,
):
    rows = [
        _row(),
        _row(
            job_doc_id="job-2",
            job_company="Second Co",
            job_title="Platform Engineer",
            advisory_priority="tailor_first",
            deterministic_winner_score="0.650000",
            winner_score="0.650000",
        ),
    ]
    shared = _shared(rows)
    expected = queue._with_tailoring_decision_overlay(rows)

    monkeypatch.setattr(
        queue,
        "render_tailoring_decision_rows",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("tailoring row renderer reran")
        ),
    )
    actual = queue._with_tailoring_decision_overlay(
        rows,
        shared_result=shared,
    )

    assert actual == expected
    assert [row["job_doc_id"] for row in actual] == ["job-1", "job-2"]
    assert operator_review_agent.render_operator_review_rows(
        actual
    ) == operator_review_agent.render_operator_review_rows(expected)


class _FakeTrace:
    calls = []
    mutate_records = False
    fail_create = False

    @classmethod
    def reset(cls):
        cls.calls = []
        cls.mutate_records = False
        cls.fail_create = False

    @classmethod
    def create_agent_run(cls, *, record):
        cls.calls.append(("create", deepcopy(record)))
        if cls.mutate_records:
            record["summary_json"]["decision_counts"] = {"mutated": 1}
        if cls.fail_create:
            raise RuntimeError("trace_write_failed")
        return {"run": {"agent_run_id": "trace-run-1"}}

    @classmethod
    def record_agent_step(cls, *, record):
        cls.calls.append(("step", deepcopy(record)))
        if cls.mutate_records:
            record["input_json"]["rows"][0]["company"] = "mutated"
        return {"step": {"agent_step_id": "trace-step-1"}}

    @classmethod
    def complete_agent_step(cls, **kwargs):
        cls.calls.append(("complete_step", deepcopy(kwargs)))
        if cls.mutate_records:
            kwargs["output_json"]["decisions"][0][
                "tailoring_decision"
            ] = "do_not_tailor"
        return {}

    @classmethod
    def complete_agent_run(cls, **kwargs):
        cls.calls.append(("complete_run", deepcopy(kwargs)))
        return {}


def test_trace_disabled_returns_before_shared_validation_or_render(
    monkeypatch,
):
    monkeypatch.setattr(
        tailoring,
        "render_tailoring_decisions",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("disabled trace rendered")
        ),
    )
    assert tailoring.record_tailoring_decision_agent_trace(
        rows=[_row()],
        env={},
        shared_result={"malformed": True},
    ) == {"attempted": False, "reason": "trace_disabled"}


def test_trace_reuses_shared_payload_without_rerender(monkeypatch):
    rows = [_row()]
    metadata = _metadata()
    shared = _shared(rows, **metadata)
    _FakeTrace.reset()
    monkeypatch.setattr(
        tailoring,
        "render_tailoring_decisions",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("trace rerendered")
        ),
    )

    result = tailoring.record_tailoring_decision_agent_trace(
        rows=rows,
        source_artifact_path=metadata["source_artifact_path"],
        env={
            tailoring.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": metadata["owner_user_id"],
            "JOB_APP_PIPELINE_RUN_ID": metadata["pipeline_run_id"],
        },
        trace_module=_FakeTrace,
        shared_result=shared,
    )

    assert result["recorded"] is True
    assert result["summary"] == shared["payload"]["summary"]
    assert result["validation"] == shared["payload"]["validation"]
    assert [name for name, _payload in _FakeTrace.calls] == [
        "create",
        "step",
        "complete_step",
        "complete_run",
    ]
    assert _FakeTrace.calls[0][1]["summary_json"] == (
        shared["payload"]["summary"]
    )
    assert _FakeTrace.calls[1][1]["input_json"] == (
        shared["payload"]["input"]
    )
    assert _FakeTrace.calls[2][1]["output_json"] == (
        shared["payload"]["output"]
    )
    assert _FakeTrace.calls[2][1]["validation_json"] == (
        shared["payload"]["validation"]
    )


@pytest.mark.parametrize("strict", [False, True])
def test_trace_failure_preserves_strictness_without_rerender(
    monkeypatch,
    strict,
):
    rows = [_row()]
    metadata = _metadata()
    shared = _shared(rows, **metadata)
    _FakeTrace.reset()
    _FakeTrace.fail_create = True
    monkeypatch.setattr(
        tailoring,
        "render_tailoring_decisions",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("trace failure rerendered")
        ),
    )
    env = {
        tailoring.TRACE_ENABLED_ENV: "1",
        tailoring.TRACE_STRICT_ENV: "1" if strict else "0",
        "JOB_STACK_OWNER_USER_ID": metadata["owner_user_id"],
        "JOB_APP_PIPELINE_RUN_ID": metadata["pipeline_run_id"],
    }
    kwargs = {
        "rows": rows,
        "source_artifact_path": metadata["source_artifact_path"],
        "env": env,
        "trace_module": _FakeTrace,
        "shared_result": shared,
    }

    if strict:
        with pytest.raises(RuntimeError, match="trace_write_failed"):
            tailoring.record_tailoring_decision_agent_trace(**kwargs)
    else:
        result = tailoring.record_tailoring_decision_agent_trace(**kwargs)
        assert result == {
            "attempted": True,
            "recorded": False,
            "warning": "trace_write_failed",
        }


@pytest.mark.parametrize(
    "mode",
    ["artifact_disabled", "artifact_enabled", "operator_enabled"],
)
def test_queue_authoritative_path_computes_tailoring_once(
    monkeypatch,
    tmp_path,
    mode,
):
    calls = []
    real = tailoring.build_tailoring_decision_agent_output_payload

    def counted(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(
        tailoring,
        "build_tailoring_decision_agent_output_payload",
        counted,
    )
    args = []
    if mode == "artifact_enabled":
        args = [
            "--tailoring-decision-output-csv",
            str(tmp_path / "tailoring.csv"),
            "--tailoring-decision-summary-json",
            str(tmp_path / "tailoring.json"),
        ]
    elif mode == "operator_enabled":
        args = [
            "--operator-review-output-csv",
            str(tmp_path / "operator.csv"),
            "--operator-review-summary-json",
            str(tmp_path / "operator.json"),
        ]

    output = _run_queue_main(
        monkeypatch,
        tmp_path,
        [_row()],
        *args,
    )

    assert calls == [1]
    assert output.is_file()
    if mode == "artifact_enabled":
        assert (tmp_path / "tailoring.csv").is_file()
    if mode == "operator_enabled":
        assert (tmp_path / "operator.csv").is_file()


def test_queue_trace_enabled_path_computes_tailoring_once(
    monkeypatch,
    tmp_path,
):
    calls = []
    real_output_builder = (
        tailoring.build_tailoring_decision_agent_output_payload
    )

    def counted(*args, **kwargs):
        calls.append(1)
        return real_output_builder(*args, **kwargs)

    monkeypatch.setattr(
        tailoring,
        "build_tailoring_decision_agent_output_payload",
        counted,
    )
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "owner-14b")
    monkeypatch.setenv("JOB_APP_PIPELINE_RUN_ID", "run-14b")
    monkeypatch.setattr(
        queue,
        "record_job_prioritization_agent_trace",
        lambda **_kwargs: {"attempted": False, "reason": "isolated"},
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        lambda **_kwargs: {"attempted": False, "reason": "isolated"},
    )
    real_trace = tailoring.record_tailoring_decision_agent_trace
    _FakeTrace.reset()

    def isolated_trace(**kwargs):
        return real_trace(
            **kwargs,
            env={
                tailoring.TRACE_ENABLED_ENV: "1",
                "JOB_STACK_OWNER_USER_ID": "owner-14b",
                "JOB_APP_PIPELINE_RUN_ID": "run-14b",
            },
            trace_module=_FakeTrace,
        )

    monkeypatch.setattr(
        queue,
        "record_tailoring_decision_agent_trace",
        isolated_trace,
    )

    _run_queue_main(
        monkeypatch,
        tmp_path,
        [_row()],
        trace_enabled=True,
    )

    assert calls == [1]
    assert [name for name, _payload in _FakeTrace.calls] == [
        "create",
        "step",
        "complete_step",
        "complete_run",
    ]


def test_shared_result_failure_precedes_tailoring_and_operator_consumers(
    monkeypatch,
    tmp_path,
):
    calls = []
    monkeypatch.setattr(
        queue,
        "build_tailoring_decision_shared_result",
        lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("decision_failed")
        ),
    )
    monkeypatch.setattr(
        queue,
        "write_tailoring_decision_artifacts",
        lambda **_kwargs: calls.append("tailoring_writer"),
    )
    monkeypatch.setattr(
        queue,
        "write_operator_review_artifacts",
        lambda **_kwargs: calls.append("operator_writer"),
    )
    monkeypatch.setattr(
        queue,
        "record_tailoring_decision_agent_trace",
        lambda **_kwargs: calls.append("tailoring_trace"),
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        lambda **_kwargs: calls.append("operator_trace"),
    )

    with pytest.raises(RuntimeError, match="decision_failed"):
        _run_queue_main(
            monkeypatch,
            tmp_path,
            [_row()],
            "--tailoring-decision-output-csv",
            str(tmp_path / "tailoring.csv"),
            "--operator-review-output-csv",
            str(tmp_path / "operator.csv"),
        )

    assert calls == []
    assert not (tmp_path / "tailoring.csv").exists()
    assert not (tmp_path / "operator.csv").exists()


def test_tailoring_artifact_failure_is_advisory_without_rerender(
    monkeypatch,
    tmp_path,
    capsys,
):
    calls = []
    real = tailoring.build_tailoring_decision_agent_output_payload

    def counted(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(
        tailoring,
        "build_tailoring_decision_agent_output_payload",
        counted,
    )
    monkeypatch.setattr(
        queue,
        "write_tailoring_decision_artifacts",
        lambda **_kwargs: (_ for _ in ()).throw(OSError("write_failed")),
    )

    _run_queue_main(
        monkeypatch,
        tmp_path,
        [_row()],
        "--tailoring-decision-output-csv",
        str(tmp_path / "tailoring.csv"),
        "--operator-review-output-csv",
        str(tmp_path / "operator.csv"),
    )

    assert calls == [1]
    assert "Tailoring decision advisory artifact skipped: write_failed" in (
        capsys.readouterr().out
    )
    assert (tmp_path / "operator.csv").is_file()


def test_deep_copy_containment_across_all_shared_consumers(
    monkeypatch,
    tmp_path,
):
    rows = [_row()]
    before = deepcopy(rows)
    metadata = _metadata()
    shared = _shared(rows, **metadata)
    shared_before = deepcopy(shared)

    validated = tailoring.validate_tailoring_decision_shared_result(
        shared,
        expected_rows=rows,
        **metadata,
    )
    validated["rendered_rows"][0]["company"] = "validator mutation"
    assert shared == shared_before

    tailoring.write_tailoring_decision_artifacts(
        rows=rows,
        output_csv_path=tmp_path / "tailoring.csv",
        shared_result=shared,
        **metadata,
    )
    assert shared == shared_before

    overlay = queue._with_tailoring_decision_overlay(
        rows,
        shared_result=shared,
    )
    overlay[0]["tailoring_decision"] = "overlay mutation"
    assert shared == shared_before

    _FakeTrace.reset()
    _FakeTrace.mutate_records = True
    tailoring.record_tailoring_decision_agent_trace(
        rows=rows,
        source_artifact_path=metadata["source_artifact_path"],
        env={
            tailoring.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": metadata["owner_user_id"],
            "JOB_APP_PIPELINE_RUN_ID": metadata["pipeline_run_id"],
        },
        trace_module=_FakeTrace,
        shared_result=shared,
    )

    assert shared == shared_before
    assert rows == before
    clean_operator_rows = queue._with_tailoring_decision_overlay(
        rows,
        shared_result=shared,
    )
    assert clean_operator_rows[0]["tailoring_decision"] == "light_tailoring"


def test_existing_public_functions_remain_standalone_compatible(tmp_path):
    rows = [_row()]
    payload = tailoring.render_tailoring_decisions(rows=rows)
    rendered = tailoring.render_tailoring_decision_rows(rows)
    artifact = tailoring.write_tailoring_decision_artifacts(
        rows=rows,
        output_csv_path=tmp_path / "tailoring.csv",
    )
    trace = tailoring.record_tailoring_decision_agent_trace(
        rows=rows,
        env={},
    )

    assert rendered[0]["tailoring_decision"] == (
        payload["output"]["decisions"][0]["tailoring_decision"]
    )
    assert artifact["summary"] == payload["summary"]
    assert artifact["validation"] == payload["validation"]
    assert trace == {"attempted": False, "reason": "trace_disabled"}


def test_shared_path_has_no_provider_network_database_or_authority(
    monkeypatch,
):
    prohibited = []

    def blocked(*args, **kwargs):
        prohibited.append((args, kwargs))
        raise AssertionError("external activity")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(sqlite3, "connect", blocked)
    rows = [_row()]
    shared = _shared(rows)
    serialized = json.dumps(shared, sort_keys=True).lower()

    assert prohibited == []
    assert "provider_response" not in serialized
    assert "credential" not in serialized
    assert "application_authority" not in serialized
    assert "ats_authority" not in serialized
    assert rows == [_row()]


def test_phase14b_scope_has_no_run006_or_authoritative_graph(tmp_path):
    repository = Path(__file__).resolve().parents[1]
    changed_source = {
        "application_execution_queue.py",
        "src/agents/tailoring_decision_agent.py",
    }
    assert "src/agents/job_prioritization_authoritative_graph.py" not in (
        changed_source
    )
    assert not any(
        "run_006" in path.name.lower() or "run-006" in path.name.lower()
        for path in repository.rglob("*")
        if ".git" not in path.parts and "__pycache__" not in path.parts
    )
