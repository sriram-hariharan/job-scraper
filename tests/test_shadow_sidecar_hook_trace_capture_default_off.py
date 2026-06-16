from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar_hook
from src.pipeline import collector


GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
JD_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED"
TAILORING_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED"
CRITIC_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED"
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"
ALL_SIDECAR_FLAGS = (GLOBAL_FLAG, JD_FLAG, TAILORING_FLAG, CRITIC_FLAG, KILL_SWITCH)


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
        run_id="run_trace_capture",
        batch_id="batch_trace_capture",
        job_id="job_trace_capture",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=1,
        source_deterministic_decision="scored_jobs_available",
        source_deterministic_reason_codes=["application_priority_completed"],
        sidecar_config=config,
        job_payload=_scored_jobs()[0],
        resume_profile_payload={},
        existing_trace_context={"trace_id": "shadow_trace_capture"},
        called_by_pipeline=True,
    )


def _assert_trace_capture_safety(trace_capture):
    safety = trace_capture["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["trace_capture_only"] is True
    assert safety["pipeline_hook_called_by_pipeline"] is True
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
    assert safety["did_read_database"] is False
    assert safety["did_write_database"] is False


def test_default_environment_does_not_change_deterministic_pipeline_output(monkeypatch):
    for flag_name in ALL_SIDECAR_FLAGS:
        monkeypatch.delenv(flag_name, raising=False)
    scored_jobs = _scored_jobs()
    before = deepcopy(scored_jobs)

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(scored_jobs)

    assert payload is None
    assert scored_jobs == before


def test_global_flag_disabled_does_not_change_deterministic_pipeline_output(monkeypatch):
    for flag_name in ALL_SIDECAR_FLAGS:
        monkeypatch.delenv(flag_name, raising=False)
    monkeypatch.setenv(GLOBAL_FLAG, "false")
    monkeypatch.setenv(JD_FLAG, "true")
    scored_jobs = _scored_jobs()
    before = deepcopy(scored_jobs)

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(scored_jobs)

    assert payload is None
    assert scored_jobs == before


def test_kill_switch_enabled_does_not_change_deterministic_pipeline_output(monkeypatch):
    for flag_name in ALL_SIDECAR_FLAGS:
        monkeypatch.delenv(flag_name, raising=False)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(JD_FLAG, "true")
    monkeypatch.setenv(KILL_SWITCH, "true")
    scored_jobs = _scored_jobs()
    before = deepcopy(scored_jobs)

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(scored_jobs)

    assert payload["hook_status"] == "hook_blocked_by_kill_switch"
    assert payload["trace_capture"]["trace_capture_status"] == "trace_capture_skipped"
    _assert_trace_capture_safety(payload["trace_capture"])
    assert scored_jobs == before


def test_hook_enabled_builds_shadow_trace_capture_without_provider_calls():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
    )

    trace_capture = payload["trace_capture"]
    assert trace_capture["trace_capture_status"] == "trace_capture_captured"
    assert trace_capture["trace_capture_only"] is True
    assert trace_capture["persistence_deferred"] is True
    assert trace_capture["hook_status"] == "hook_completed_with_fallback"
    assert trace_capture["chain_attempted"] is True
    assert trace_capture["provider_calls_disabled_in_tests"] is True
    assert trace_capture["live_provider_backed_automated_agents"] == 0
    assert trace_capture["mutation_authorized_agents"] == 0
    _assert_trace_capture_safety(trace_capture)


def test_trace_capture_includes_hook_chain_source_summary_and_safety_metadata():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
    )
    trace_capture = payload["trace_capture"]

    assert trace_capture["hook_status"] == payload["hook_status"]
    assert trace_capture["chain_summary"]["chain_status"] == "completed_with_fallback"
    assert trace_capture["chain_summary"]["stage_order"] == ["jd_intelligence"]
    assert trace_capture["source_deterministic_stage"] == "application_priority"
    assert trace_capture["source_deterministic_status"] == "completed"
    assert trace_capture["source_deterministic_score"] == 1
    assert trace_capture["source_deterministic_decision"] == "scored_jobs_available"
    assert trace_capture["source_deterministic_reason_codes"] == [
        "application_priority_completed"
    ]
    assert trace_capture["trace_bundle"]["bundle_type"] == (
        "shadow_sidecar_chain_trace_bundle"
    )
    assert trace_capture["evidence_pack"]["evidence_pack_type"] == (
        "shadow_sidecar_chain_evidence_pack"
    )
    assert trace_capture["trace_summary"]["summary_type"] == "agent_trace"
    assert trace_capture["trace_summary"]["step_count"] == 1
    _assert_trace_capture_safety(trace_capture)


def test_trace_capture_failure_is_non_blocking(monkeypatch):
    for flag_name in ALL_SIDECAR_FLAGS:
        monkeypatch.delenv(flag_name, raising=False)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(JD_FLAG, "true")
    scored_jobs = _scored_jobs()
    before = deepcopy(scored_jobs)

    def fail_capture(_payload):
        raise RuntimeError("capture boom")

    monkeypatch.setattr(
        shadow_sidecar_hook,
        "build_shadow_sidecar_hook_trace_capture_payload",
        fail_capture,
    )

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(scored_jobs)

    assert payload["hook_status"] == "hook_completed_with_fallback"
    assert payload["trace_capture"]["trace_capture_status"] == (
        "trace_capture_failed_non_blocking"
    )
    assert payload["trace_capture"]["error_type"] == "RuntimeError"
    _assert_trace_capture_safety(payload["trace_capture"])
    assert scored_jobs == before


def test_sidecar_trace_output_is_not_used_for_mutations_or_decisions():
    hook_source = Path("src/agents/shadow_sidecar_hook.py").read_text(encoding="utf-8")
    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    helper_start = hook_source.index("def build_shadow_sidecar_hook_trace_capture_payload")
    helper_end = hook_source.index("def _safe_shadow_sidecar_hook_trace_capture_payload")
    helper_source = hook_source[helper_start:helper_end]

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
        "upsert_",
        "record_agent_step",
        "create_agent_run",
        "complete_agent_run",
    ]
    for marker in forbidden:
        assert marker not in helper_source

    assert "return scored_jobs" in collector_source
    assert "trace_capture" not in collector_source


def test_api_ui_service_files_are_not_changed_by_trace_capture():
    hook_source = Path("src/agents/shadow_sidecar_hook.py").read_text(encoding="utf-8")
    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    combined = hook_source + "\n" + collector_source

    assert "src.app.api" not in combined
    assert "src.app.services" not in combined
    assert "agentic_review.js" not in combined


def test_retry_rate_limit_cache_dedup_ats_health_and_counts_remain_visible():
    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    required = [
        "get_eval_cache_metrics()",
        "dedupe_jobs(",
        "filter_new_jobs(",
        "save_new_job_ids(",
        "check_ats_health(",
        "check_pipeline_regression(",
        "complete_stage(",
        "log_stage_metrics(",
    ]
    for marker in required:
        assert marker in collector_source
