from __future__ import annotations

import csv
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

import application_execution_queue as queue
from src.agents import operator_review_agent as operator


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
        "tailoring_decision": "no_tailoring_needed",
    }
    row.update(overrides)
    return row


def _rows():
    return [
        _row(),
        _row(
            job_doc_id="job-2",
            job_company="Second Co",
            job_title="Platform Engineer",
            advisory_priority="tailor_first",
            tailoring_decision="tailor_before_apply",
            winner_score="0.700000",
            resolved_score="0.700000",
            deterministic_winner_score="0.700000",
        ),
    ]


def _metadata():
    return {
        "pipeline_run_id": "run-15b",
        "owner_user_id": "owner-15b",
        "source_artifact_path": "application_execution_queue.csv",
    }


def _shared(rows=None, **metadata):
    return operator.build_operator_review_shared_result(
        rows=deepcopy(rows or _rows()),
        **metadata,
    )


class _FakeTrace:
    calls = []
    fail_at = ""
    mutate_inputs = False

    @classmethod
    def reset(cls, *, fail_at="", mutate_inputs=False):
        cls.calls = []
        cls.fail_at = fail_at
        cls.mutate_inputs = mutate_inputs

    @classmethod
    def _record(cls, name, payload):
        cls.calls.append((name, deepcopy(payload)))
        if cls.mutate_inputs and isinstance(payload, dict):
            payload["mutated_by_trace"] = True
        if cls.fail_at == name:
            raise RuntimeError(f"{name}_failed")

    @classmethod
    def create_agent_run(cls, *, record):
        cls._record("create_run", record)
        return {"run": {"agent_run_id": "agent-run-15b"}}

    @classmethod
    def record_agent_step(cls, *, record):
        cls._record("record_step", record)
        return {"step": {"agent_step_id": "agent-step-15b"}}

    @classmethod
    def complete_agent_step(cls, **kwargs):
        cls._record("complete_step", kwargs)
        return {"step": {"agent_step_id": kwargs["agent_step_id"]}}

    @classmethod
    def complete_agent_run(cls, **kwargs):
        cls._record("complete_run", kwargs)
        return {"run": {"agent_run_id": kwargs["agent_run_id"]}}


def _trace_env(*, strict=False):
    return {
        operator.TRACE_ENABLED_ENV: "1",
        operator.TRACE_STRICT_ENV: "1" if strict else "0",
        "JOB_STACK_OWNER_USER_ID": "owner-15b",
        "JOB_APP_PIPELINE_RUN_ID": "run-15b",
    }


def _configure_queue(
    monkeypatch,
    tmp_path,
    *,
    artifact=False,
    trace=False,
    valid_context=False,
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
    monkeypatch.setenv(operator.TRACE_ENABLED_ENV, "1" if trace else "0")
    monkeypatch.delenv(operator.TRACE_STRICT_ENV, raising=False)
    if valid_context:
        monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "owner-15b")
        monkeypatch.setenv("JOB_APP_PIPELINE_RUN_ID", "run-15b")
    else:
        monkeypatch.delenv("JOB_STACK_OWNER_USER_ID", raising=False)
        monkeypatch.delenv("JOB_APP_PIPELINE_RUN_ID", raising=False)
        monkeypatch.delenv("JOB_STACK_USER_PIPELINE_RUN_ID", raising=False)
    monkeypatch.delenv(
        queue.AUTHORITATIVE_JOB_PRIORITIZATION_LANGGRAPH_FLAG,
        raising=False,
    )
    monkeypatch.delenv(
        queue.AUTHORITATIVE_TAILORING_DECISION_LANGGRAPH_FLAG,
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


def test_shared_result_contract_determinism_order_and_containment():
    rows = _rows()
    before = deepcopy(rows)
    first = _shared(rows, **_metadata())
    second = _shared(rows, **_metadata())

    assert first == second
    assert rows == before
    assert first["contract_version"] == (
        operator.OPERATOR_REVIEW_SHARED_RESULT_VERSION
    ) == "operator-review-shared-result-v1"
    assert set(first) == {"contract_version", "payload", "rendered_rows"}
    assert set(first["payload"]) == {
        "input",
        "output",
        "validation",
        "summary",
    }
    assert list(first["rendered_rows"][0]) == (
        operator.OPERATOR_REVIEW_FIELDNAMES
    )
    assert [row["job_id"] for row in first["rendered_rows"]] == [
        "job-1",
        "job-2",
    ]

    first["payload"]["input"]["rows"][0]["company"] = "mutated"
    first["payload"]["output"]["reviews"][0][
        "operator_reason_codes"
    ].append("mutated")
    first["rendered_rows"][0]["operator_review_lane"] = "hold_or_skip"
    assert second["payload"]["input"]["rows"][0]["company"] == "Example Co"
    assert second["payload"]["output"]["reviews"][0][
        "operator_reason_codes"
    ] == ["apply_ready_signals_aligned"]
    assert second["rendered_rows"][0]["operator_review_lane"] == (
        "ready_to_apply"
    )
    assert rows == before


def test_builder_calls_canonical_render_once_and_lane_owner_once_per_row(
    monkeypatch,
):
    render_calls = []
    lane_calls = []
    real_render = operator.render_operator_review
    real_lane = operator.recommend_operator_lane

    def counted_render(**kwargs):
        render_calls.append(deepcopy(kwargs))
        return real_render(**kwargs)

    def counted_lane(row):
        lane_calls.append(deepcopy(row))
        return real_lane(row)

    monkeypatch.setattr(operator, "render_operator_review", counted_render)
    monkeypatch.setattr(operator, "recommend_operator_lane", counted_lane)

    result = _shared(_rows(), **_metadata())

    assert len(render_calls) == 1
    assert len(lane_calls) == len(_rows())
    assert result["rendered_rows"] == (
        operator._render_operator_review_rows_from_payload(result["payload"])
    )


def test_validator_returns_a_contained_copy():
    shared = _shared(**_metadata())
    validated = operator.validate_operator_review_shared_result(
        shared,
        expected_rows=_rows(),
        **_metadata(),
    )
    validated["payload"]["input"]["rows"][0]["company"] = "changed"
    validated["rendered_rows"][0]["operator_review_lane"] = "hold_or_skip"

    assert shared["payload"]["input"]["rows"][0]["company"] == "Example Co"
    assert shared["rendered_rows"][0]["operator_review_lane"] == (
        "ready_to_apply"
    )


def test_writer_shared_path_never_rerenders_and_preserves_exact_bytes(
    monkeypatch,
    tmp_path,
):
    rows = _rows()
    metadata = _metadata()
    expected = _shared(rows, **metadata)
    expected_csv = tmp_path / "expected.csv"
    expected_json = tmp_path / "expected.json"
    actual_csv = tmp_path / "actual.csv"
    actual_json = tmp_path / "actual.json"

    with expected_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=operator.OPERATOR_REVIEW_FIELDNAMES,
        )
        writer.writeheader()
        writer.writerows(expected["rendered_rows"])
    expected_json.write_text(
        json.dumps(
            expected["payload"]["summary"],
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        operator,
        "render_operator_review",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("unexpected rerender")
        ),
    )
    monkeypatch.setattr(
        operator,
        "render_operator_review_rows",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("unexpected row rerender")
        ),
    )

    result = operator.write_operator_review_artifacts(
        rows=rows,
        output_csv_path=actual_csv,
        summary_json_path=actual_json,
        shared_result=expected,
        **metadata,
    )

    assert actual_csv.read_bytes() == expected_csv.read_bytes()
    assert actual_json.read_bytes() == expected_json.read_bytes()
    assert result["summary"] == expected["payload"]["summary"]
    assert result["validation"] == expected["payload"]["validation"]


def test_standalone_writer_and_public_row_renderer_remain_compatible(tmp_path):
    rows = _rows()
    before = deepcopy(rows)
    csv_path = tmp_path / "operator.csv"
    summary_path = tmp_path / "operator.json"

    rendered = operator.render_operator_review_rows(rows)
    result = operator.write_operator_review_artifacts(
        rows=rows,
        output_csv_path=csv_path,
        summary_json_path=summary_path,
        **_metadata(),
    )
    with csv_path.open(encoding="utf-8", newline="") as handle:
        written = list(csv.DictReader(handle))

    assert written == rendered
    assert result["row_count"] == len(rows)
    assert result["validation"]["validation_status"] == "passed"
    assert rows == before


def test_trace_shared_path_never_rerenders_and_is_deep_copy_contained(
    monkeypatch,
):
    rows = _rows()
    before = deepcopy(rows)
    shared = _shared(rows, **_metadata())
    shared_before = deepcopy(shared)
    _FakeTrace.reset(mutate_inputs=True)
    monkeypatch.setattr(
        operator,
        "render_operator_review",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("unexpected rerender")
        ),
    )

    result = operator.record_operator_review_agent_trace(
        rows=rows,
        source_artifact_path=_metadata()["source_artifact_path"],
        env=_trace_env(),
        trace_module=_FakeTrace,
        shared_result=shared,
    )

    assert result["recorded"] is True
    assert [name for name, _payload in _FakeTrace.calls] == [
        "create_run",
        "record_step",
        "complete_step",
        "complete_run",
    ]
    assert shared == shared_before
    assert rows == before


@pytest.mark.parametrize(
    ("artifact", "trace", "valid_context", "expected_computations"),
    [
        (False, False, False, 0),
        (False, True, False, 0),
        (True, False, False, 1),
        (False, True, True, 1),
        (True, True, True, 1),
    ],
)
def test_queue_computes_once_only_for_an_existing_eligible_consumer(
    monkeypatch,
    tmp_path,
    artifact,
    trace,
    valid_context,
    expected_computations,
):
    _configure_queue(
        monkeypatch,
        tmp_path,
        artifact=artifact,
        trace=trace,
        valid_context=valid_context,
    )
    calls = []
    consumer_shared_results = []
    real_builder = queue.build_operator_review_shared_result

    def counted_builder(**kwargs):
        calls.append(deepcopy(kwargs))
        return real_builder(**kwargs)

    def artifact_writer(**kwargs):
        consumer_shared_results.append(
            ("artifact", kwargs.get("shared_result"))
        )
        return None

    def trace_recorder(**kwargs):
        consumer_shared_results.append(
            ("trace", kwargs.get("shared_result"))
        )
        return {"attempted": False, "reason": "isolated"}

    monkeypatch.setattr(
        queue,
        "build_operator_review_shared_result",
        counted_builder,
    )
    monkeypatch.setattr(queue, "write_operator_review_artifacts", artifact_writer)
    monkeypatch.setattr(queue, "record_operator_review_agent_trace", trace_recorder)

    queue.main()

    assert len(calls) == expected_computations
    for _consumer, shared in consumer_shared_results:
        assert (shared is not None) is bool(expected_computations)


def test_standard_planning_supplies_operator_artifact_paths():
    source = Path("run_application_planning.py").read_text(encoding="utf-8")
    start = source.index('        "application_execution_queue.py",')
    end = source.index("    _run_cmd(execution_queue_cmd)", start)
    execution_queue_command = source[start:end]

    assert '"--operator-review-output-csv",' in execution_queue_command
    assert "str(operator_review_csv)," in execution_queue_command
    assert '"--operator-review-summary-json",' in execution_queue_command
    assert "str(operator_review_summary_json)," in execution_queue_command


def test_shared_result_failure_precedes_operator_artifact_and_trace(
    monkeypatch,
    tmp_path,
):
    _configure_queue(monkeypatch, tmp_path, artifact=True)
    calls = []
    monkeypatch.setattr(
        queue,
        "build_operator_review_shared_result",
        lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("operator_shared_failed")
        ),
    )
    monkeypatch.setattr(
        queue,
        "write_operator_review_artifacts",
        lambda **_kwargs: calls.append("artifact"),
    )
    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        lambda **_kwargs: calls.append("trace"),
    )

    with pytest.raises(RuntimeError, match="operator_shared_failed"):
        queue.main()

    assert calls == []
    assert not (tmp_path / "operator.csv").exists()


def test_artifact_failure_is_advisory_and_valid_trace_reuses_shared_result(
    monkeypatch,
    tmp_path,
    capsys,
):
    _configure_queue(
        monkeypatch,
        tmp_path,
        artifact=True,
        trace=True,
        valid_context=True,
    )
    build_calls = []
    real_builder = queue.build_operator_review_shared_result

    def counted_builder(**kwargs):
        build_calls.append(1)
        return real_builder(**kwargs)

    monkeypatch.setattr(
        queue,
        "build_operator_review_shared_result",
        counted_builder,
    )
    monkeypatch.setattr(
        queue,
        "write_operator_review_artifacts",
        lambda **_kwargs: (_ for _ in ()).throw(OSError("write_failed")),
    )
    _FakeTrace.reset()

    def isolated_trace(**kwargs):
        return operator.record_operator_review_agent_trace(
            **kwargs,
            env=_trace_env(),
            trace_module=_FakeTrace,
        )

    monkeypatch.setattr(
        queue,
        "record_operator_review_agent_trace",
        isolated_trace,
    )

    queue.main()

    assert build_calls == [1]
    assert "Operator review advisory artifact skipped: write_failed" in (
        capsys.readouterr().out
    )
    assert [name for name, _payload in _FakeTrace.calls] == [
        "create_run",
        "record_step",
        "complete_step",
        "complete_run",
    ]


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, {"attempted": False, "reason": "trace_disabled"}),
        (
            {operator.TRACE_ENABLED_ENV: "1"},
            {
                "attempted": False,
                "reason": "missing_trace_context",
                "pipeline_run_id": "",
                "owner_user_id": "",
                "context_id": "",
            },
        ),
    ],
)
def test_ineligible_trace_returns_before_shared_result_validation(env, expected):
    result = operator.record_operator_review_agent_trace(
        rows=_rows(),
        env=env,
        shared_result={"malformed": True},
    )
    assert result == expected


@pytest.mark.parametrize("strict", [False, True])
def test_trace_failure_preserves_strictness_and_never_rerenders(
    monkeypatch,
    strict,
):
    shared = _shared(**_metadata())
    _FakeTrace.reset(fail_at="record_step")
    monkeypatch.setattr(
        operator,
        "render_operator_review",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("unexpected rerender")
        ),
    )
    kwargs = {
        "rows": _rows(),
        "source_artifact_path": _metadata()["source_artifact_path"],
        "env": _trace_env(strict=strict),
        "trace_module": _FakeTrace,
        "shared_result": shared,
    }
    if strict:
        with pytest.raises(RuntimeError, match="record_step_failed"):
            operator.record_operator_review_agent_trace(**kwargs)
    else:
        result = operator.record_operator_review_agent_trace(**kwargs)
        assert result["attempted"] is True
        assert result["recorded"] is False
        assert result["warning"] == "record_step_failed"


@pytest.mark.parametrize(
    "corruption",
    [
        "version",
        "agent_identity",
        "missing_section",
        "malformed_payload",
        "malformed_rendered_row",
        "count",
        "identity",
        "order",
        "missing_identity",
        "duplicate_identity",
        "invalid_lane",
        "reason_codes",
        "validation",
        "summary",
    ],
)
def test_shared_result_validator_fails_closed(corruption):
    rows = _rows()
    shared = _shared(rows, **_metadata())
    if corruption == "version":
        shared["contract_version"] = "wrong"
    elif corruption == "agent_identity":
        shared["payload"]["input"]["agent_name"] = "wrong"
    elif corruption == "missing_section":
        shared["payload"].pop("summary")
    elif corruption == "malformed_payload":
        shared["payload"]["output"] = []
    elif corruption == "malformed_rendered_row":
        shared["rendered_rows"][0]["unexpected"] = "value"
    elif corruption == "count":
        shared["payload"]["input"]["row_count"] = 999
    elif corruption == "identity":
        shared["payload"]["output"]["reviews"][0]["job_id"] = "wrong"
        shared["rendered_rows"][0]["job_id"] = "wrong"
    elif corruption == "order":
        shared["payload"]["output"]["reviews"].reverse()
        shared["rendered_rows"].reverse()
    elif corruption == "missing_identity":
        shared["payload"]["input"]["rows"][0]["job_id"] = ""
        shared["payload"]["output"]["reviews"][0]["job_id"] = ""
        shared["rendered_rows"][0]["job_id"] = ""
    elif corruption == "duplicate_identity":
        shared["payload"]["input"]["rows"][1]["job_id"] = "job-1"
        shared["payload"]["output"]["reviews"][1]["job_id"] = "job-1"
        shared["rendered_rows"][1]["job_id"] = "job-1"
    elif corruption == "invalid_lane":
        shared["payload"]["output"]["reviews"][0][
            "operator_review_lane"
        ] = "invalid"
        shared["rendered_rows"][0]["operator_review_lane"] = "invalid"
        shared["payload"]["output"]["lane_counts"] = {
            "invalid": 1,
            "tailor_then_apply": 1,
        }
    elif corruption == "reason_codes":
        shared["payload"]["output"]["reviews"][0][
            "operator_reason_codes"
        ].append("changed")
    elif corruption == "validation":
        shared["payload"]["validation"]["validation_status"] = "failed"
    elif corruption == "summary":
        shared["payload"]["summary"]["row_count"] = 999

    with pytest.raises(ValueError):
        operator.validate_operator_review_shared_result(shared)


def test_shared_result_metadata_mismatch_fails_closed():
    shared = _shared(**_metadata())
    with pytest.raises(
        ValueError,
        match="operator_review_shared_result_metadata_mismatch",
    ):
        operator.validate_operator_review_shared_result(
            shared,
            expected_rows=_rows(),
            pipeline_run_id="wrong-run",
            owner_user_id=_metadata()["owner_user_id"],
            source_artifact_path=_metadata()["source_artifact_path"],
        )


def test_operator_review_path_has_no_decision_store_or_provider_authority():
    root = Path(__file__).resolve().parents[1]
    operator_text = (root / "src/agents/operator_review_agent.py").read_text(
        encoding="utf-8"
    )
    queue_text = (root / "application_execution_queue.py").read_text(
        encoding="utf-8"
    )

    assert "src.storage.operator_decisions" not in operator_text
    assert "src.storage.agentic_approvals" not in operator_text
    assert "requests." not in operator_text
    assert "TavilyClient" not in operator_text
    assert "AUTHORITATIVE_OPERATOR_REVIEW" not in queue_text
    assert not any(
        path.name.lower().replace("_", "-").startswith("run-006")
        for path in root.rglob("*")
        if ".git" not in path.parts
    )
