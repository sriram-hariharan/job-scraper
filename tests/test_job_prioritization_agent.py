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
