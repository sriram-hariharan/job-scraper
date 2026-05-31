import csv
import json
from pathlib import Path

from src.agents import job_prioritization_agent


def _row(**overrides):
    row = {
        "job_doc_id": "job_1",
        "job_company": "Example Co",
        "job_title": "Backend Software Engineer",
        "source": "greenhouse",
        "action": "APPLY",
        "deterministic_winner_available": "true",
        "deterministic_winner_score": "0.750000",
        "winner_score": "0.750000",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
    }
    row.update(overrides)
    return row


def _priority(row):
    payload = job_prioritization_agent.render_job_prioritization_recommendations(rows=[row])
    return payload["output"]["recommendations"][0]["advisory_priority"]


def test_job_prioritization_fallback_only_row_becomes_skip_for_now():
    priority = _priority(
        _row(
            deterministic_winner_available="false",
            deterministic_winner_score="0.000000",
            winner_score="0.000000",
            fallback_only_no_deterministic_match="true",
            packet_generation_allowed="false",
            packet_generation_block_reason="fallback_only_no_deterministic_match",
        )
    )

    assert priority == "skip_for_now"


def test_job_prioritization_zero_score_packet_blocked_is_not_apply_now():
    priority = _priority(
        _row(
            deterministic_winner_available="false",
            deterministic_winner_score="0.000000",
            winner_score="0.000000",
            packet_generation_allowed="false",
            packet_generation_block_reason="no_deterministic_winner",
        )
    )

    assert priority == "skip_for_now"


def test_job_prioritization_borderline_deterministic_row_becomes_manual_review():
    assert _priority(_row(deterministic_winner_score="0.550000", winner_score="0.550000")) == "manual_review"


def test_job_prioritization_good_tailoring_signal_becomes_tailor_first():
    assert _priority(_row(action="MAYBE_TAILOR", deterministic_winner_score="0.650000", winner_score="0.650000")) == "tailor_first"


def test_job_prioritization_high_score_packet_allowed_becomes_apply_now():
    assert _priority(_row(deterministic_winner_score="0.750000", winner_score="0.750000")) == "apply_now"


def test_job_prioritization_source_signal_can_be_watch_source_without_mutating_action():
    payload = job_prioritization_agent.render_job_prioritization_recommendations(
        rows=[
            _row(
                action="APPLY",
                source_recommendation="demote",
                deterministic_winner_score="0.780000",
                winner_score="0.780000",
            )
        ]
    )

    recommendation = payload["output"]["recommendations"][0]
    assert recommendation["advisory_priority"] == "watch_source"
    assert recommendation["original_action"] == "APPLY"


def test_job_prioritization_validation_catches_fallback_only_apply_now_bug():
    input_payload = job_prioritization_agent.build_job_prioritization_agent_input_payload(
        rows=[
            _row(
                deterministic_winner_available="false",
                deterministic_winner_score="0.000000",
                winner_score="0.000000",
                fallback_only_no_deterministic_match="true",
                packet_generation_allowed="false",
            )
        ]
    )
    output_payload = {
        "total_rows": 1,
        "priority_counts": {"apply_now": 1},
        "recommendations": [
            {
                "job_id": "job_1",
                "company": "Example Co",
                "title": "Backend Software Engineer",
                "original_action": "APPLY",
                "advisory_priority": "apply_now",
                "priority_reason": "bad fixture",
            }
        ],
    }

    validation = job_prioritization_agent.build_job_prioritization_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
    )

    assert validation["validation_status"] == "failed"
    assert "fallback_only_apply_now" in validation["reason_codes"]
    assert "packet_blocked_apply_now" in validation["reason_codes"]


def test_job_prioritization_trace_disabled_by_default():
    result = job_prioritization_agent.record_job_prioritization_agent_trace(
        rows=[_row()],
        env={},
    )

    assert result == {"attempted": False, "reason": "trace_disabled"}


def test_job_prioritization_trace_can_be_monkeypatched_without_postgres():
    calls = []

    class FakeTrace:
        @staticmethod
        def create_agent_run(*, record):
            calls.append(("create_run", record))
            return {"run": {"agent_run_id": "agent-run-1"}}

        @staticmethod
        def record_agent_step(*, record):
            calls.append(("record_step", record))
            return {"step": {"agent_step_id": "agent-step-1"}}

        @staticmethod
        def complete_agent_step(**kwargs):
            calls.append(("complete_step", kwargs))
            return {"step": {"agent_step_id": kwargs["agent_step_id"]}}

        @staticmethod
        def complete_agent_run(**kwargs):
            calls.append(("complete_run", kwargs))
            return {"run": {"agent_run_id": kwargs["agent_run_id"]}}

    result = job_prioritization_agent.record_job_prioritization_agent_trace(
        rows=[_row()],
        source_artifact_path="application_execution_queue.csv",
        env={
            job_prioritization_agent.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": "user-1",
            "JOB_APP_PIPELINE_RUN_ID": "run-1",
        },
        trace_module=FakeTrace,
    )

    assert result["recorded"] is True
    assert result["summary"]["priority_counts"] == {"apply_now": 1}
    assert [name for name, _ in calls] == [
        "create_run",
        "record_step",
        "complete_step",
        "complete_run",
    ]
    step_record = calls[1][1]
    assert step_record["model_provider"] == "deterministic"
    assert step_record["model_name"] == "job_prioritization_rules"
    assert step_record["token_usage_json"] == {
        "metadata_version": "llmops_metadata_v1",
        "input_token_count": 0,
        "output_token_count": 0,
        "total_token_count": 0,
    }
    assert step_record["cost_json"] == {
        "metadata_version": "llmops_metadata_v1",
        "estimated_cost": 0.0,
        "cost_currency": "",
        "cost_reason": "no_rate_table_configured",
    }


def test_job_prioritization_artifact_helper_renders_stable_csv_columns(tmp_path):
    rows = [
        _row(
            job_doc_id="skip_job",
            job_company="Fallback Co",
            job_title="Software Engineer",
            deterministic_winner_available="false",
            deterministic_winner_score="0.000000",
            winner_score="0.000000",
            fallback_only_no_deterministic_match="true",
            packet_generation_allowed="false",
            packet_generation_block_reason="fallback_only_no_deterministic_match",
        ),
        _row(
            job_doc_id="apply_job",
            job_company="Apply Co",
            job_title="Backend Software Engineer",
            deterministic_winner_score="0.750000",
            winner_score="0.750000",
            packet_generation_allowed="true",
        ),
    ]
    original_rows = [dict(row) for row in rows]
    csv_path = tmp_path / "job_prioritization_recommendations.csv"
    summary_path = tmp_path / "job_prioritization_summary.json"

    result = job_prioritization_agent.write_job_prioritization_artifacts(
        rows=rows,
        output_csv_path=csv_path,
        summary_json_path=summary_path,
        pipeline_run_id="run_1",
        owner_user_id="user_1",
        source_artifact_path="application_execution_queue.csv",
    )

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rendered = list(csv.DictReader(handle))

    assert rows == original_rows
    assert result["row_count"] == 2
    assert list(rendered[0].keys()) == job_prioritization_agent.RECOMMENDATION_FIELDNAMES
    assert rendered[0]["existing_action"] == "APPLY"
    assert rendered[0]["advisory_priority"] == "skip_for_now"
    assert rendered[0]["advisory_reason_codes"] == "fallback_only_no_deterministic_match"
    assert rendered[1]["advisory_priority"] == "apply_now"
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    assert summary["agent_name"] == job_prioritization_agent.AGENT_NAME
    assert summary["priority_counts"] == {"apply_now": 1, "skip_for_now": 1}
