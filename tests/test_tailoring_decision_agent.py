import csv
import json

from src.agents import tailoring_decision_agent


def _row(**overrides):
    row = {
        "job_doc_id": "job_1",
        "job_company": "Example Co",
        "job_title": "Backend Software Engineer",
        "action": "APPLY",
        "advisory_priority": "apply_now",
        "deterministic_winner_available": "true",
        "deterministic_winner_score": "0.750000",
        "winner_score": "0.750000",
        "winner_resume": "backend_resume.pdf",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
        "critic_decision": "",
        "missing_requirement_count": "1",
    }
    row.update(overrides)
    return row


def _decision(row):
    payload = tailoring_decision_agent.render_tailoring_decisions(rows=[row])
    return payload["output"]["decisions"][0]["tailoring_decision"]


def test_tailoring_decision_fallback_only_row_becomes_do_not_tailor():
    assert _decision(
        _row(
            deterministic_winner_available="false",
            deterministic_winner_score="0.000000",
            winner_score="0.000000",
            fallback_only_no_deterministic_match="true",
            packet_generation_allowed="false",
            packet_generation_block_reason="fallback_only_no_deterministic_match",
        )
    ) == "do_not_tailor"


def test_tailoring_decision_critic_reject_row_becomes_do_not_tailor():
    assert _decision(_row(critic_decision="reject")) == "do_not_tailor"


def test_tailoring_decision_borderline_score_manual_review():
    assert _decision(_row(deterministic_winner_score="0.550000", winner_score="0.550000")) == "manual_review_before_tailoring"


def test_tailoring_decision_tailor_first_score_becomes_tailor_before_apply():
    assert _decision(
        _row(advisory_priority="tailor_first", deterministic_winner_score="0.650000", winner_score="0.650000")
    ) == "tailor_before_apply"


def test_tailoring_decision_high_apply_now_becomes_light_tailoring():
    assert _decision(_row(advisory_priority="apply_now", deterministic_winner_score="0.750000", winner_score="0.750000")) == "light_tailoring"


def test_tailoring_decision_very_high_apply_now_no_gaps_needs_no_tailoring():
    assert _decision(
        _row(
            advisory_priority="apply_now",
            deterministic_winner_score="0.850000",
            winner_score="0.850000",
            missing_requirement_count="0",
            winner_missing_requirements="",
            resolved_missing_requirements="",
        )
    ) == "no_tailoring_needed"


def test_tailoring_decision_validation_catches_fallback_only_tailoring_bug():
    input_payload = tailoring_decision_agent.build_tailoring_decision_agent_input_payload(
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
        "decision_counts": {"tailor_before_apply": 1},
        "decisions": [
            {
                "job_id": "job_1",
                "company": "Example Co",
                "title": "Backend Software Engineer",
                "tailoring_decision": "tailor_before_apply",
            }
        ],
    }

    validation = tailoring_decision_agent.build_tailoring_decision_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
    )

    assert validation["validation_status"] == "failed"
    assert "fallback_only_tailoring_allowed" in validation["reason_codes"]


def test_tailoring_decision_trace_disabled_by_default():
    result = tailoring_decision_agent.record_tailoring_decision_agent_trace(
        rows=[_row()],
        env={},
    )

    assert result == {"attempted": False, "reason": "trace_disabled"}


def test_tailoring_decision_artifact_renders_stable_columns_and_preserves_inputs(tmp_path):
    rows = [
        _row(
            job_doc_id="job_fallback",
            deterministic_winner_available="false",
            deterministic_winner_score="0.000000",
            winner_score="0.000000",
            fallback_only_no_deterministic_match="true",
            packet_generation_allowed="false",
            packet_generation_block_reason="fallback_only_no_deterministic_match",
        ),
        _row(job_doc_id="job_critic", critic_decision="reject", critic_reason_codes="unsupported_claim"),
        _row(job_doc_id="job_light", advisory_priority="apply_now", deterministic_winner_score="0.750000"),
    ]
    original_rows = [dict(row) for row in rows]
    output_csv = tmp_path / "tailoring_decision_recommendations.csv"
    summary_json = tmp_path / "tailoring_decision_summary.json"

    result = tailoring_decision_agent.write_tailoring_decision_artifacts(
        rows=rows,
        output_csv_path=output_csv,
        summary_json_path=summary_json,
        pipeline_run_id="run-1",
        owner_user_id="user-1",
        source_artifact_path="application_execution_queue.csv",
    )

    with output_csv.open("r", encoding="utf-8", newline="") as handle:
        rendered = list(csv.DictReader(handle))
    summary = json.loads(summary_json.read_text(encoding="utf-8"))

    assert list(rendered[0]) == tailoring_decision_agent.TAILORING_DECISION_FIELDNAMES
    assert rendered[0]["existing_action"] == "APPLY"
    assert rendered[0]["advisory_priority"] == "apply_now"
    assert rendered[0]["tailoring_decision"] == "do_not_tailor"
    assert rendered[0]["tailoring_reason_codes"] == "fallback_only_no_deterministic_match"
    assert rendered[1]["tailoring_decision"] == "do_not_tailor"
    assert rendered[1]["critic_decision"] == "reject"
    assert rendered[1]["critic_reason_codes"] == "unsupported_claim"
    assert rendered[2]["tailoring_decision"] == "light_tailoring"
    assert rendered[2]["winner_resume"] == "backend_resume.pdf"
    assert result["row_count"] == 3
    assert summary["agent_name"] == "Tailoring Decision Agent"
    assert rows == original_rows


def test_tailoring_decision_trace_can_be_monkeypatched_without_postgres():
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

    result = tailoring_decision_agent.record_tailoring_decision_agent_trace(
        rows=[_row()],
        source_artifact_path="application_execution_queue.csv",
        env={
            tailoring_decision_agent.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": "user-1",
            "JOB_APP_PIPELINE_RUN_ID": "run-1",
        },
        trace_module=FakeTrace,
    )

    assert result["recorded"] is True
    assert result["summary"]["decision_counts"] == {"light_tailoring": 1}
    assert [name for name, _ in calls] == [
        "create_run",
        "record_step",
        "complete_step",
        "complete_run",
    ]
    step_record = calls[1][1]
    assert step_record["model_provider"] == "deterministic"
    assert step_record["model_name"] == "tailoring_decision_rules"
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
