from src.agents import critic_agent
from src.app.services import _build_tailoring_scan_issue_contract


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


def test_critic_advisory_disabled_keeps_scan_issue_payload_unchanged():
    row = {
        "replacement_candidate_id": "supported",
        "source_bullet_id": "bullet_1",
        "final_replacement_text": "Built Python APIs for internal operations.",
        "original_text": "Built Python APIs for internal operations.",
        "supported_jd_signals": ["Python"],
        "projected_overall_delta": 0.05,
        "replacement_source": "live_llm",
    }
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[row],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        tailoring_summary={"missing_required": ["Python"]},
        env={},
    )

    issue = next(item for item in contract["issues"] if item.get("candidate_id") == "supported")
    assert "critic_advisory" not in contract
    assert "critic_decision" not in issue
    assert "critic_advisory_only" not in issue


def test_critic_advisory_enabled_adds_supported_metadata_to_scan_issue():
    row = {
        "replacement_candidate_id": "supported",
        "source_bullet_id": "bullet_1",
        "final_replacement_text": "Built Python APIs for internal operations.",
        "original_text": "Built Python APIs for internal operations.",
        "supported_jd_signals": ["Python"],
        "projected_overall_delta": 0.05,
        "replacement_source": "live_llm",
    }
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[row],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        tailoring_summary={"missing_required": ["Python"]},
        env={"APPLYLENS_CRITIC_ADVISORY_ENABLED": "1"},
    )

    issue = next(item for item in contract["issues"] if item.get("candidate_id") == "supported")
    assert contract["critic_advisory"]["enabled"] is True
    assert issue["critic_advisory_only"] is True
    assert issue["critic_decision"] == "approve"
    assert issue["critic_reason_codes"] == []


def test_critic_advisory_enabled_rejects_unsupported_tool_metadata():
    row = {
        "replacement_candidate_id": "unsupported_tool",
        "source_bullet_id": "bullet_1",
        "final_replacement_text": "Built Kubernetes automation for Python APIs.",
        "original_text": "Built Python APIs for internal operations.",
        "supported_jd_signals": ["Python"],
        "projected_overall_delta": 0.05,
        "replacement_source": "live_llm",
    }
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[row],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        tailoring_summary={"missing_required": ["Python"]},
        env={"APPLYLENS_CRITIC_ADVISORY_ENABLED": "1"},
    )

    issue = next(item for item in contract["issues"] if item.get("candidate_id") == "unsupported_tool")
    assert issue["critic_decision"] == "reject"
    assert "fake_tool_or_domain" in issue["critic_reason_codes"]
    assert issue["can_accept"] is True


def test_critic_advisory_enabled_guidance_only_metadata():
    row = {
        "replacement_candidate_id": "guidance",
        "source_bullet_id": "bullet_1",
        "rewrite_direction": "Emphasize API testing work when tailoring this resume.",
        "original_text": "Created API tests for synthetic workflows.",
        "supported_jd_signals": ["API Testing"],
        "projected_overall_delta": 0.0,
    }
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[row],
        tailoring_summary={"missing_required": ["API Testing"]},
        env={"APPLYLENS_CRITIC_ADVISORY_ENABLED": "1"},
    )

    issue = next(item for item in contract["issues"] if item.get("candidate_id") == "guidance")
    assert issue["critic_decision"] == "downgrade_to_guidance"
    assert "safe_guidance_only" in issue["critic_reason_codes"]
    assert issue["can_accept"] is False


def test_critic_advisory_trace_enabled_can_be_monkeypatched_without_postgres():
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

    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[
            {
                "replacement_candidate_id": "supported",
                "source_bullet_id": "bullet_1",
                "final_replacement_text": "Built Python APIs for internal operations.",
                "original_text": "Built Python APIs for internal operations.",
                "supported_jd_signals": ["Python"],
                "projected_overall_delta": 0.05,
                "replacement_source": "live_llm",
            }
        ],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        tailoring_summary={"missing_required": ["Python"]},
        env={
            "APPLYLENS_CRITIC_ADVISORY_ENABLED": "1",
            "APPLYLENS_AGENT_TRACE_ENABLED": "1",
            "JOB_STACK_OWNER_USER_ID": "user-1",
            "JOB_APP_PIPELINE_RUN_ID": "run-1",
        },
        critic_trace_module=FakeTrace,
    )

    assert contract["critic_advisory"]["trace"]["recorded"] is True
    assert [name for name, _ in calls] == [
        "create_run",
        "record_step",
        "complete_step",
        "complete_run",
    ]
