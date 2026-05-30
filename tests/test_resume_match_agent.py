from src.agents import resume_match_agent


def _row(**overrides):
    row = {
        "job_doc_id": "job_1",
        "winner_resume": "SWATIKA_test_1.pdf",
        "winner_score": "0.520000",
        "runner_up_resume": "backup.pdf",
        "resume_variants_considered": "19",
        "resolved_resume": "SWATIKA_test_1.pdf",
        "resolved_resume_source": "deterministic_winner",
        "deterministic_winner_available": "true",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
    }
    row.update(overrides)
    return row


def test_resume_match_agent_output_summary_and_score_buckets():
    rows = [
        _row(winner_score="0.000000", winner_resume="", resolved_resume="fallback.pdf", resolved_resume_source="llm_fallback_generated", deterministic_winner_available="false", fallback_only_no_deterministic_match="true", packet_generation_allowed="false", packet_generation_block_reason="fallback_only_no_deterministic_match"),
        _row(winner_score="0.490000", winner_resume="weak.pdf", packet_generation_allowed="false", packet_generation_block_reason="deterministic_score_below_credible_threshold"),
        _row(winner_score="0.520000", winner_resume="SWATIKA_test_1.pdf"),
        _row(winner_score="0.630000", winner_resume="senior.pdf"),
        _row(winner_score="0.720000", winner_resume="strong.pdf", resolved_resume_source="deterministic_equivalent_variants"),
        _row(winner_score="0.610000", winner_resume="tie.pdf", resolved_resume_source="llm_adjudication_generated"),
    ]

    output = resume_match_agent.build_resume_match_agent_output_payload(rows)

    assert output["total_rows"] == 6
    assert output["deterministic_winner_count"] == 5
    assert output["fallback_only_no_deterministic_match_count"] == 1
    assert output["deterministic_equivalent_variant_count"] == 1
    assert output["llm_adjudication_selected_count"] == 1
    assert output["low_confidence_blocked_count"] == 1
    assert output["packet_generation_allowed_count"] == 4
    assert output["score_buckets"] == {
        "score_zero": 1,
        "score_lt_050": 1,
        "score_050_059": 1,
        "score_060_069": 2,
        "score_070_plus": 1,
    }
    assert output["selected_resume_distribution"]["SWATIKA_test_1.pdf"] == 1


def test_resume_match_agent_validation_passes_for_blocked_fallback_and_swatika_row():
    rows = [
        _row(winner_resume="", winner_score="0.000000", resolved_resume="fallback.pdf", resolved_resume_source="llm_fallback_generated", deterministic_winner_available="false", fallback_only_no_deterministic_match="true", packet_generation_allowed="false", packet_generation_block_reason="fallback_only_no_deterministic_match"),
        _row(winner_resume="SWATIKA_test_1.pdf", winner_score="0.520000", packet_generation_allowed="true"),
    ]
    input_payload = resume_match_agent.build_resume_match_agent_input_payload(
        rows=rows,
        candidate_resume_names=["SWATIKA_test_1.pdf", "fallback.pdf"],
        pipeline_run_id="run_1",
        owner_user_id="user_1",
        source_artifact_path="best_resume_variant_by_job.csv",
    )
    output_payload = resume_match_agent.build_resume_match_agent_output_payload(rows)

    validation = resume_match_agent.build_resume_match_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
        rows=rows,
    )

    assert validation["validation_status"] == "passed"
    assert validation["fallback_only_rows_have_packet_generation_allowed_false"] is True
    assert validation["zero_score_fallback_rows_are_not_packet_allowed"] is True
    assert validation["deterministic_rows_with_score_gte_050_can_be_packet_allowed"] is True
    assert validation["reason_codes"] == []


def test_resume_match_agent_validation_fails_when_fallback_is_packet_allowed():
    rows = [
        _row(winner_resume="", winner_score="0.000000", resolved_resume="fallback.pdf", resolved_resume_source="llm_fallback_generated", deterministic_winner_available="false", fallback_only_no_deterministic_match="true", packet_generation_allowed="true"),
    ]
    input_payload = resume_match_agent.build_resume_match_agent_input_payload(
        rows=rows,
        candidate_resume_names=["fallback.pdf"],
    )
    output_payload = resume_match_agent.build_resume_match_agent_output_payload(rows)

    validation = resume_match_agent.build_resume_match_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
        rows=rows,
    )

    assert validation["validation_status"] == "failed"
    assert "fallback_only_packet_allowed" in validation["reason_codes"]
    assert "zero_score_fallback_packet_allowed" in validation["reason_codes"]


def test_resume_match_agent_trace_disabled_by_default_does_not_record(monkeypatch):
    class TraceModule:
        def create_agent_run(self, **kwargs):
            raise AssertionError("trace should not be called when disabled")

    monkeypatch.delenv(resume_match_agent.TRACE_ENABLED_ENV, raising=False)

    result = resume_match_agent.record_resume_match_agent_trace(
        rows=[_row()],
        candidate_resume_names=["SWATIKA_test_1.pdf"],
        source_artifact_path="best_resume_variant_by_job.csv",
        trace_module=TraceModule(),
    )

    assert result == {"attempted": False, "reason": "trace_disabled"}


def test_resume_match_agent_optional_trace_recording_can_be_monkeypatched():
    calls = []

    class TraceModule:
        def create_agent_run(self, **kwargs):
            calls.append(("create_agent_run", kwargs))
            return {"run": {"agent_run_id": "agent_run_1"}}

        def record_agent_step(self, **kwargs):
            calls.append(("record_agent_step", kwargs))
            return {"step": {"agent_step_id": "agent_step_1"}}

        def complete_agent_step(self, **kwargs):
            calls.append(("complete_agent_step", kwargs))
            return {"ok": True}

        def complete_agent_run(self, **kwargs):
            calls.append(("complete_agent_run", kwargs))
            return {"ok": True}

    result = resume_match_agent.record_resume_match_agent_trace(
        rows=[_row()],
        candidate_resume_names=["SWATIKA_test_1.pdf"],
        source_artifact_path="best_resume_variant_by_job.csv",
        env={
            resume_match_agent.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": "user_1",
            "JOB_APP_PIPELINE_RUN_ID": "run_1",
        },
        trace_module=TraceModule(),
    )

    assert result["recorded"] is True
    assert result["agent_run_id"] == "agent_run_1"
    assert result["agent_step_id"] == "agent_step_1"
    assert [name for name, _payload in calls] == [
        "create_agent_run",
        "record_agent_step",
        "complete_agent_step",
        "complete_agent_run",
    ]
    step_record = calls[1][1]["record"]
    assert step_record["agent_name"] == resume_match_agent.AGENT_NAME
    assert step_record["input_json"]["job_count"] == 1
    assert step_record["owner_user_id"] == "user_1"
    assert step_record["pipeline_run_id"] == "run_1"


def test_resume_match_agent_trace_failure_returns_warning_when_not_strict():
    class TraceModule:
        def create_agent_run(self, **kwargs):
            raise RuntimeError("trace db unavailable")

    result = resume_match_agent.record_resume_match_agent_trace(
        rows=[_row()],
        candidate_resume_names=["SWATIKA_test_1.pdf"],
        source_artifact_path="best_resume_variant_by_job.csv",
        env={
            resume_match_agent.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": "user_1",
            "JOB_APP_PIPELINE_RUN_ID": "run_1",
        },
        trace_module=TraceModule(),
    )

    assert result["attempted"] is True
    assert result["recorded"] is False
    assert "trace db unavailable" in result["warning"]


def test_resume_match_agent_trace_strict_reraises_failure():
    class TraceModule:
        def create_agent_run(self, **kwargs):
            raise RuntimeError("strict trace failure")

    try:
        resume_match_agent.record_resume_match_agent_trace(
            rows=[_row()],
            candidate_resume_names=["SWATIKA_test_1.pdf"],
            source_artifact_path="best_resume_variant_by_job.csv",
            env={
                resume_match_agent.TRACE_ENABLED_ENV: "1",
                resume_match_agent.TRACE_STRICT_ENV: "1",
                "JOB_STACK_OWNER_USER_ID": "user_1",
                "JOB_APP_PIPELINE_RUN_ID": "run_1",
            },
            trace_module=TraceModule(),
        )
    except RuntimeError as exc:
        assert "strict trace failure" in str(exc)
    else:
        raise AssertionError("Expected strict trace failure to be raised.")
