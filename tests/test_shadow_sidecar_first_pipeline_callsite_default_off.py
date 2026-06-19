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
        }
    ]


def _assert_pipeline_hook_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["pipeline_hook_available"] is True
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
    calls = []

    def fail_if_called(**_kwargs):
        calls.append("called")
        raise AssertionError("shadow hook should stay gated off")

    monkeypatch.setattr(
        shadow_sidecar_hook, "run_shadow_sidecar_pipeline_hook", fail_if_called
    )
    scored_jobs = _scored_jobs()
    before = deepcopy(scored_jobs)

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(scored_jobs)

    assert payload is None
    assert calls == []
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
    assert payload["chain_attempted"] is False
    _assert_pipeline_hook_safety(payload)
    assert scored_jobs == before


def test_enabled_call_site_uses_isolated_hook_fallback_without_mutation(monkeypatch):
    for flag_name in ALL_SIDECAR_FLAGS:
        monkeypatch.delenv(flag_name, raising=False)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(JD_FLAG, "true")
    scored_jobs = _scored_jobs()
    before = deepcopy(scored_jobs)

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(scored_jobs)

    assert payload["hook_status"] == "hook_completed_with_fallback"
    assert payload["chain_attempted"] is True
    assert payload["default_off_pipeline_hook_call_sites"] == 1
    assert payload["source_deterministic_stage"] == "application_priority"
    assert payload["source_deterministic_status"] == "completed"
    assert payload["source_deterministic_score"] == 1
    assert payload["source_deterministic_decision"] == "scored_jobs_available"
    assert payload["source_deterministic_reason_codes"] == [
        "application_priority_completed"
    ]
    assert payload["provider_calls_disabled_in_tests"] is True
    assert payload["trace_capture"]["trace_capture_status"] == "trace_capture_captured"
    assert payload["trace_capture"]["persistence_deferred"] is True
    assert payload["live_production_pipeline_connected_agents"] == 0
    assert payload["live_agents_allowed_to_automate_mutations"] == 0
    _assert_pipeline_hook_safety(payload)
    assert scored_jobs == before


def test_sidecar_failure_is_non_blocking_and_preserves_output(monkeypatch):
    for flag_name in ALL_SIDECAR_FLAGS:
        monkeypatch.delenv(flag_name, raising=False)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    scored_jobs = _scored_jobs()
    before = deepcopy(scored_jobs)

    def fail_hook(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(shadow_sidecar_hook, "run_shadow_sidecar_pipeline_hook", fail_hook)

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(scored_jobs)

    assert payload is None
    assert scored_jobs == before


def test_pipeline_hook_call_site_exists_only_at_audited_integration_point():
    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    assert collector_source.count("run_shadow_sidecar_pipeline_hook(") == 1
    assert collector_source.count("_maybe_run_shadow_sidecar_after_application_priority(") == 2

    complete_idx = collector_source.index(
        'complete_stage("application_priority", counts={"scored_jobs": len(scored_jobs)})'
    )
    call_idx = collector_source.index(
        "_maybe_run_shadow_sidecar_after_application_priority(",
        complete_idx,
    )
    source_health_idx = collector_source.index(
        "if role_title_audit_rows is not None:", call_idx
    )
    rag_export_idx = collector_source.index('start_stage("rag_export"', call_idx)

    vector_idx = collector_source.index(
        "_maybe_collect_vector_evidence_after_application_priority(scored_jobs)",
        complete_idx,
    )
    assert complete_idx < vector_idx < call_idx < source_health_idx < rag_export_idx

    pipeline_call_sites = []
    for path in sorted(Path("src/pipeline").glob("*.py")):
        if "run_shadow_sidecar_pipeline_hook(" in path.read_text(encoding="utf-8"):
            pipeline_call_sites.append(path.as_posix())
    assert pipeline_call_sites == ["src/pipeline/collector.py"]


def test_sidecar_output_is_not_used_for_mutations_or_deterministic_decisions():
    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    helper_start = collector_source.index(
        "def _maybe_run_shadow_sidecar_after_application_priority"
    )
    helper_end = collector_source.index("def log_market_insights")
    helper_source = collector_source[helper_start:helper_end]

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
    assert 'payload.get("hook_status"' in helper_source


def test_stage_logging_metrics_retry_cache_dedup_and_health_flow_is_preserved():
    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    required = [
        'start_stage("application_priority"',
        "scored_jobs = score_jobs(ai_jobs)",
        'complete_stage("application_priority", counts={"scored_jobs": len(scored_jobs)})',
        "_maybe_run_shadow_sidecar_after_application_priority(",
        'start_stage("rag_export"',
        "log_stage_metrics(",
        "dedupe_jobs(",
        "filter_new_jobs(",
        "save_new_job_ids(",
        "check_ats_health(",
        "check_pipeline_regression(",
        "get_eval_cache_metrics()",
    ]
    for marker in required:
        assert marker in collector_source


def test_api_ui_service_files_are_not_changed_by_call_site():
    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    assert "src.app.api" not in collector_source
    assert "src.app.services" not in collector_source
    assert "agentic_review.js" not in collector_source
