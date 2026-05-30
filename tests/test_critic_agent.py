from src.agents import critic_agent


def _supported_input(**overrides):
    payload = critic_agent.build_critic_agent_input_payload(
        suggestion_id="suggestion_supported",
        original_resume_evidence=[
            "Built Python APIs and PostgreSQL-backed batch workers for internal operations."
        ],
        jd_required_skills=["Python", "APIs"],
        jd_preferred_skills=["PostgreSQL"],
        proposed_text="Built Python APIs and PostgreSQL-backed batch workers for internal operations.",
        source_bullet="Built Python APIs and PostgreSQL-backed batch workers for internal operations.",
        projected_score_delta=0.12,
        suggestion_type="patch_ready",
    )
    payload.update(overrides)
    return payload


def test_critic_supported_suggestion_is_approved():
    rendered = critic_agent.render_critic_decision(_supported_input())

    assert rendered["output"]["decision"] == "approve"
    assert rendered["output"]["reason_codes"] == []
    assert rendered["validation"]["validation_status"] == "passed"


def test_critic_rejects_unsupported_tool_or_domain():
    rendered = critic_agent.render_critic_decision(
        _supported_input(
            suggestion_id="suggestion_fake_tool",
            proposed_text="Built Kubernetes automation for Python APIs and PostgreSQL workers.",
        )
    )

    assert rendered["output"]["decision"] == "reject"
    assert "fake_tool_or_domain" in rendered["output"]["reason_codes"]


def test_critic_rejects_unsupported_metric():
    rendered = critic_agent.render_critic_decision(
        _supported_input(
            suggestion_id="suggestion_fake_metric",
            proposed_text="Built Python APIs and reduced batch processing latency by 40%.",
        )
    )

    assert rendered["output"]["decision"] == "reject"
    assert "unsupported_claim" in rendered["output"]["reason_codes"]


def test_critic_rejects_weak_score_lift_patch_ready_suggestion():
    rendered = critic_agent.render_critic_decision(
        _supported_input(
            suggestion_id="suggestion_weak_lift",
            projected_score_delta=0,
        )
    )

    assert rendered["output"]["decision"] == "reject"
    assert "weak_score_lift" in rendered["output"]["reason_codes"]


def test_critic_guidance_only_safe_suggestion_is_guidance():
    rendered = critic_agent.render_critic_decision(
        _supported_input(
            suggestion_id="suggestion_guidance",
            suggestion_type="guidance_only",
            proposed_text="Emphasize Python API work when describing the batch-worker project.",
            projected_score_delta=0,
        )
    )

    assert rendered["output"]["decision"] == "downgrade_to_guidance"
    assert "safe_guidance_only" in rendered["output"]["reason_codes"]


def test_critic_output_schema_has_stable_keys():
    rendered = critic_agent.render_critic_decision(_supported_input())

    assert set(rendered["output"]) == {
        "suggestion_id",
        "decision",
        "confidence",
        "reason_codes",
        "evidence_spans",
        "score_delta",
        "notes",
    }
    assert rendered["validation"]["stable_output_keys"] is True


def test_critic_trace_disabled_by_default():
    result = critic_agent.record_critic_agent_trace(
        input_payloads=[_supported_input()],
        env={},
    )

    assert result == {"attempted": False, "reason": "trace_disabled"}


def test_critic_trace_can_be_monkeypatched_without_postgres():
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

    result = critic_agent.record_critic_agent_trace(
        input_payloads=[_supported_input()],
        env={
            "APPLYLENS_AGENT_TRACE_ENABLED": "1",
            "JOB_STACK_OWNER_USER_ID": "user-1",
            "JOB_APP_PIPELINE_RUN_ID": "run-1",
        },
        trace_module=FakeTrace,
    )

    assert result["recorded"] is True
    assert result["summary"]["decision_counts"] == {"approve": 1}
    assert [name for name, _ in calls] == [
        "create_run",
        "record_step",
        "complete_step",
        "complete_run",
    ]
