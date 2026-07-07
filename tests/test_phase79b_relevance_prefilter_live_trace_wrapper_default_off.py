import pytest

from src.agents import workflow_runner
from src.pipeline import collector


class FakeTraceModule:
    def __init__(self, *, fail_on_create=False):
        self.fail_on_create = fail_on_create
        self.calls = []

    def create_agent_run(self, *, record):
        self.calls.append(("create_agent_run", record))
        if self.fail_on_create:
            raise RuntimeError("trace unavailable")
        return {"run": {"agent_run_id": "agent_run_phase79b"}}

    def record_agent_step(self, *, record):
        self.calls.append(("record_agent_step", record))
        return {"step": {"agent_step_id": "agent_step_phase79b"}}

    def complete_agent_step(self, **kwargs):
        self.calls.append(("complete_agent_step", kwargs))
        return {"updated": True}

    def complete_agent_run(self, **kwargs):
        self.calls.append(("complete_agent_run", kwargs))
        return {"updated": True}


def _env(**overrides):
    base = {
        "APPLYLENS_AGENT_TRACE_ENABLED": "",
        "APPLYLENS_AGENT_TRACE_STRICT": "",
        "JOB_APP_PIPELINE_RUN_ID": "pipeline_phase79b",
        "JOB_STACK_OWNER_USER_ID": "owner_phase79b",
    }
    base.update(overrides)
    return base


def _summary(input_count=3, kept_count=2):
    dropped_count = input_count - kept_count
    return {
        "input_count": input_count,
        "kept_count": kept_count,
        "dropped_count": dropped_count,
        "reason_counts": {
            "embedding_prefilter_kept": kept_count,
            "embedding_prefilter_dropped": max(dropped_count, 0),
        },
        "role_family": "software_engineering",
        "seniority": "senior",
        "location_policy": "us_remote",
        "source_stage": "embedding_prefilter",
    }


def test_default_off_relevance_prefilter_live_trace_does_not_touch_trace_storage():
    trace_module = FakeTraceModule()
    jobs = [{"id": "job_1"}, {"id": "job_2"}]
    original_jobs = [dict(job) for job in jobs]

    result = collector._record_relevance_prefilter_agent_trace(
        prefilter_summary=_summary(input_count=len(jobs), kept_count=len(jobs)),
        env=_env(APPLYLENS_AGENT_TRACE_ENABLED=""),
        trace_module=trace_module,
    )

    assert result == {"attempted": False, "reason": "trace_disabled"}
    assert jobs == original_jobs
    assert trace_module.calls == []


def test_enabled_relevance_prefilter_live_trace_records_metadata_without_output_change():
    trace_module = FakeTraceModule()
    jobs = [{"id": "job_1"}, {"id": "job_2"}, {"id": "job_3"}]
    output_jobs = jobs[:2]
    original_output_jobs = [dict(job) for job in output_jobs]

    result = collector._record_relevance_prefilter_agent_trace(
        prefilter_summary=_summary(input_count=len(jobs), kept_count=len(output_jobs)),
        env=_env(APPLYLENS_AGENT_TRACE_ENABLED="1"),
        trace_module=trace_module,
    )

    assert output_jobs == original_output_jobs
    assert result["attempted"] is True
    assert result["recorded"] is True
    assert result["summary"]["input_count"] == 3
    assert result["summary"]["kept_count"] == 2
    assert result["summary"]["dropped_count"] == 1
    assert result["summary"]["source_stage"] == "embedding_prefilter"
    assert result["summary"]["preserves_stage_output"] is True
    assert [call[0] for call in trace_module.calls] == [
        "create_agent_run",
        "record_agent_step",
        "complete_agent_step",
        "complete_agent_run",
    ]
    step_record = trace_module.calls[1][1]
    assert step_record["agent_name"] == "relevance_prefilter_agent"
    assert step_record["model_provider"] == "deterministic"
    assert step_record["model_name"] == "relevance_prefilter_trace_wrapper"
    assert trace_module.calls[2][1]["validation_json"] == {
        "is_valid": True,
        "errors": [],
        "preserves_prefilter_relevance": True,
        "did_call_live_filter": False,
        "did_call_llm_evaluation": False,
        "did_call_final_application_scoring": False,
    }


def test_relevance_prefilter_trace_failure_is_non_blocking_when_strict_off():
    result = collector._record_relevance_prefilter_agent_trace(
        prefilter_summary=_summary(),
        env=_env(APPLYLENS_AGENT_TRACE_ENABLED="1", APPLYLENS_AGENT_TRACE_STRICT=""),
        trace_module=FakeTraceModule(fail_on_create=True),
    )

    assert result["attempted"] is True
    assert result["recorded"] is False
    assert "trace unavailable" in result["warning"]


def test_relevance_prefilter_trace_failure_raises_when_strict_on():
    with pytest.raises(RuntimeError, match="trace unavailable"):
        collector._record_relevance_prefilter_agent_trace(
            prefilter_summary=_summary(),
            env=_env(
                APPLYLENS_AGENT_TRACE_ENABLED="1",
                APPLYLENS_AGENT_TRACE_STRICT="1",
            ),
            trace_module=FakeTraceModule(fail_on_create=True),
        )


def test_relevance_prefilter_trace_bridge_requires_existing_trace_context():
    trace_module = FakeTraceModule()

    result = collector._record_relevance_prefilter_agent_trace(
        prefilter_summary=_summary(),
        env={
            "APPLYLENS_AGENT_TRACE_ENABLED": "1",
            "APPLYLENS_AGENT_TRACE_STRICT": "",
        },
        trace_module=trace_module,
    )

    assert result["attempted"] is False
    assert result["reason"] == "missing_trace_context"
    assert trace_module.calls == []


def test_workflow_runner_remains_dry_run_only_after_phase79b_trace_bridge():
    payload = workflow_runner.run_agentic_workflow_dry_run()

    assert payload["execution_mode"] == "dry_run"
    assert payload["executed_step_count"] == 0
    assert payload["summary"]["did_execute_any_step"] is False
    assert all(step["did_execute"] is False for step in payload["ordered_step_results"])
