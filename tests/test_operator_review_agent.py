from src.agents import operator_review_agent


def _row(**overrides):
    row = {
        "job_doc_id": "job_1",
        "job_company": "Example Co",
        "job_title": "Backend Software Engineer",
        "source": "greenhouse",
        "existing_action": "APPLY",
        "advisory_priority": "apply_now",
        "tailoring_decision": "no_tailoring_needed",
        "critic_decision": "",
        "deterministic_winner_score": "0.850000",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
        "source_recommendation": "",
        "winner_resume": "backend_resume.pdf",
        "resolved_resume": "backend_resume.pdf",
    }
    row.update(overrides)
    return row


def _lane(row):
    payload = operator_review_agent.render_operator_review(rows=[row])
    return payload["output"]["reviews"][0]["operator_review_lane"]


def test_operator_review_fallback_only_row_becomes_hold_or_skip():
    assert _lane(
        _row(
            deterministic_winner_score="0.000000",
            fallback_only_no_deterministic_match="true",
            packet_generation_allowed="false",
            packet_generation_block_reason="fallback_only_no_deterministic_match",
        )
    ) == "hold_or_skip"


def test_operator_review_critic_reject_row_becomes_hold_or_skip():
    assert _lane(_row(critic_decision="reject")) == "hold_or_skip"


def test_operator_review_zero_score_packet_blocked_row_becomes_hold_or_skip():
    assert _lane(
        _row(
            deterministic_winner_score="0.000000",
            packet_generation_allowed="false",
            packet_generation_block_reason="no_deterministic_winner",
        )
    ) == "hold_or_skip"


def test_operator_review_positive_packet_blocked_row_becomes_review_before_action():
    assert _lane(
        _row(
            deterministic_winner_score="0.550000",
            packet_generation_allowed="false",
            packet_generation_block_reason="deterministic_score_below_credible_threshold",
            tailoring_decision="manual_review_before_tailoring",
        )
    ) == "review_before_action"


def test_operator_review_apply_now_no_tailoring_packet_allowed_becomes_ready_to_apply():
    assert _lane(
        _row(
            advisory_priority="apply_now",
            tailoring_decision="no_tailoring_needed",
            packet_generation_allowed="true",
        )
    ) == "ready_to_apply"


def test_operator_review_tailor_first_becomes_tailor_then_apply():
    assert _lane(
        _row(
            advisory_priority="tailor_first",
            tailoring_decision="tailor_before_apply",
            deterministic_winner_score="0.650000",
        )
    ) == "tailor_then_apply"


def test_operator_review_watch_source_signal_becomes_source_watch():
    assert _lane(
        _row(
            advisory_priority="watch_source",
            source_recommendation="monitor",
            tailoring_decision="light_tailoring",
        )
    ) == "source_watch"


def test_operator_review_validation_catches_fallback_only_ready_to_apply_bug():
    input_payload = operator_review_agent.build_operator_review_agent_input_payload(
        rows=[
            _row(
                deterministic_winner_score="0.000000",
                fallback_only_no_deterministic_match="true",
                packet_generation_allowed="false",
            )
        ]
    )
    output_payload = {
        "total_rows": 1,
        "lane_counts": {"ready_to_apply": 1},
        "reviews": [
            {
                "job_id": "job_1",
                "company": "Example Co",
                "title": "Backend Software Engineer",
                "operator_review_lane": "ready_to_apply",
            }
        ],
    }

    validation = operator_review_agent.build_operator_review_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
    )

    assert validation["validation_status"] == "failed"
    assert "fallback_only_ready_to_apply" in validation["reason_codes"]


def test_operator_review_trace_disabled_by_default():
    result = operator_review_agent.record_operator_review_agent_trace(
        rows=[_row()],
        env={},
    )

    assert result == {"attempted": False, "reason": "trace_disabled"}


def test_operator_review_trace_can_be_monkeypatched_without_postgres():
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

    result = operator_review_agent.record_operator_review_agent_trace(
        rows=[_row()],
        source_artifact_path="tailoring_decision_recommendations.csv",
        env={
            operator_review_agent.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": "user-1",
            "JOB_APP_PIPELINE_RUN_ID": "run-1",
        },
        trace_module=FakeTrace,
    )

    assert result["recorded"] is True
    assert result["summary"]["lane_counts"] == {"ready_to_apply": 1}
    assert [name for name, _ in calls] == [
        "create_run",
        "record_step",
        "complete_step",
        "complete_run",
    ]
    step_record = calls[1][1]
    assert step_record["model_provider"] == "deterministic"
    assert step_record["model_name"] == "operator_review_rules"
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
