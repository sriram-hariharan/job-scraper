from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar_hook
from src.pipeline import collector


GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
JD_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED"
PERSISTENCE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED"
)
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _scored_jobs():
    return [
        {
            "id": "job_1",
            "title": "Data Platform Engineer",
            "company": "ExampleCo",
            "application_priority_score": 0.91,
            "required_skills": ["SQL"],
            "job_description": "Build SQL and Airflow data pipelines.",
        }
    ]


def _hook_payload(**config):
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="run_trace_persistence",
        batch_id="batch_trace_persistence",
        job_id="job_trace_persistence",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=1,
        source_deterministic_decision="scored_jobs_available",
        source_deterministic_reason_codes=["application_priority_completed"],
        sidecar_config=config,
        job_payload=_scored_jobs()[0],
        resume_profile_payload={},
        existing_trace_context={"trace_id": "shadow_trace_persistence"},
        called_by_pipeline=True,
    )


def _assert_persistence_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["trace_persistence_only"] is True
    assert safety["trace_persistence_called_by_hook"] is True
    assert safety["pipeline_hook_called_by_pipeline"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_create_execution_request"] is False
    assert safety["did_create_execution_launch_request"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["auto_apply_enabled"] is False


def test_default_environment_does_not_change_deterministic_pipeline_output(monkeypatch):
    monkeypatch.delenv(GLOBAL_FLAG, raising=False)
    monkeypatch.delenv(JD_FLAG, raising=False)
    monkeypatch.delenv(PERSISTENCE_FLAG, raising=False)
    scored_jobs = _scored_jobs()
    before = deepcopy(scored_jobs)

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(scored_jobs)

    assert payload is None
    assert scored_jobs == before


def test_trace_persistence_flag_disabled_does_not_attempt_persistence():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
    )

    persistence = payload["trace_persistence"]
    assert persistence["trace_persistence_status"] == "trace_persistence_not_enabled"
    assert persistence["persistence_attempted"] is False
    assert persistence["persistence_records"] == {}
    assert payload["trace_capture"]["trace_capture_status"] == "trace_capture_captured"
    _assert_persistence_safety(persistence)


def test_kill_switch_prevents_trace_persistence():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH=True,
    )

    persistence = payload["trace_persistence"]
    assert payload["hook_status"] == "hook_blocked_by_kill_switch"
    assert persistence["trace_persistence_status"] == (
        "trace_persistence_blocked_by_kill_switch"
    )
    assert persistence["persistence_attempted"] is False
    _assert_persistence_safety(persistence)


def test_trace_persistence_enabled_builds_metadata_without_provider_or_live_db():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED=True,
    )

    persistence = payload["trace_persistence"]
    assert persistence["trace_persistence_status"] == (
        "trace_persistence_skipped_no_safe_sink"
    )
    assert persistence["persistence_attempted"] is False
    assert persistence["requires_live_database"] is False
    assert persistence["provider_calls_disabled_in_tests"] is True
    assert persistence["source_trace_context"]["hook_status"] == (
        "hook_completed_with_fallback"
    )
    assert persistence["persistence_records"]["trace_summary"]["summary_type"] == (
        "agent_trace"
    )
    assert persistence["live_provider_backed_automated_agents"] == 0
    assert persistence["mutation_authorized_agents"] == 0
    _assert_persistence_safety(persistence)


def test_persistence_failure_is_non_blocking():
    def writer(_records):
        raise RuntimeError("write boom")

    payload = shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="run_trace_persistence",
        batch_id="batch_trace_persistence",
        job_id="job_trace_persistence",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=1,
        source_deterministic_decision="scored_jobs_available",
        source_deterministic_reason_codes=["application_priority_completed"],
        sidecar_config={
            GLOBAL_FLAG: True,
            JD_FLAG: True,
            PERSISTENCE_FLAG: True,
        },
        job_payload=_scored_jobs()[0],
        called_by_pipeline=True,
        trace_persistence_writer=writer,
    )

    persistence = payload["trace_persistence"]
    assert payload["hook_status"] == "hook_completed_with_fallback"
    assert persistence["trace_persistence_status"] == (
        "trace_persistence_failed_non_blocking"
    )
    assert persistence["persistence_attempted"] is True
    assert persistence["writer_result"]["error_type"] == "RuntimeError"
    _assert_persistence_safety(persistence)


def test_hook_output_includes_trace_capture_and_persistence_when_enabled():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED=True,
    )

    assert payload["trace_capture"]["trace_capture_status"] == "trace_capture_captured"
    assert payload["trace_persistence"]["trace_persistence_status"] == (
        "trace_persistence_skipped_no_safe_sink"
    )
    assert payload["trace_persistence"]["source_trace_context"][
        "source_deterministic_stage"
    ] == "application_priority"


def test_persistence_output_is_not_used_for_mutations_or_deterministic_decisions():
    hook_source = Path("src/agents/shadow_sidecar_hook.py").read_text(encoding="utf-8")
    persistence_source = Path("src/agents/shadow_sidecar_trace_persistence.py").read_text(
        encoding="utf-8"
    )
    combined = hook_source + "\n" + persistence_source
    forbidden = [
        "score_jobs(",
        "rank_jobs(",
        "save_new_job_ids(",
        "create_approval_request(",
        "record_approval_decision(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "src.app.api",
        "src.app.services",
        "agentic_review.js",
        "schema.sql",
    ]
    for marker in forbidden:
        assert marker not in combined

    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    assert "return scored_jobs" in collector_source
    assert "trace_persistence" not in collector_source


def test_storage_schema_files_are_not_changed_by_hook_integration():
    schema_source = Path("src/storage/agent_trace/schema.sql").read_text(
        encoding="utf-8"
    )

    assert "agent_runs" in schema_source
    assert "agent_steps" in schema_source
    assert "shadow_sidecar_trace_persistence" not in schema_source
