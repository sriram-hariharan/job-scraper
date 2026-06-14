from copy import deepcopy
from pathlib import Path

from src.agents.agent_state import JobApplicationContext, build_agent_run_snapshot
from src.agents import (
    deduplication,
    final_application_scoring,
    jd_intelligence,
    relevance_prefilter,
    trace,
)


EXPECTED_STAGE_ORDER = [
    "relevance_prefilter_trace_wrapper",
    "deduplication_trace_wrapper",
    "jd_intelligence_trace_wrapper",
    "final_application_scoring_trace_wrapper",
]


def _context() -> JobApplicationContext:
    return JobApplicationContext(
        approval_request_id="approval_stage_bundle",
        job_id="job_stage_bundle",
        candidate_key="candidate_stage_bundle",
        role_family="software_engineering",
        run_mode="dry_run",
        observed_at_utc="2026-06-12T18:00:00Z",
        metadata={"source": "stage_trace_bundle_test"},
    )


def _run_snapshot() -> dict:
    snapshot = build_agent_run_snapshot(
        context=_context(),
        agent_name="stage_trace_bundle_agent",
        observed_at_utc="2026-06-12T18:01:00Z",
        run_status="ready",
        metadata={"source": "stage_trace_bundle_test"},
    )
    snapshot.update(
        {
            "owner_user_id": "user_stage_bundle",
            "pipeline_run_id": "pipeline_stage_bundle",
            "status": snapshot["run_status"],
            "started_at": snapshot["observed_at_utc"],
        }
    )
    return snapshot


def _prefilter_summary() -> dict:
    return {
        "input_count": 5,
        "kept_count": 3,
        "dropped_count": 2,
        "reason_counts": {"title_match": 3, "location_reject": 2},
        "role_family": "software_engineering",
        "seniority": "senior",
        "location_policy": "us_remote_or_hybrid",
    }


def _deduplication_summary() -> dict:
    return {
        "input_count": 8,
        "filtered_count": 8,
        "unique_count": 5,
        "seen_count": 2,
        "new_count": 3,
        "same_run_duplicate_count": 3,
        "cross_run_duplicate_count": 2,
        "reason_counts": {
            "new_job": 3,
            "seen_job": 2,
            "same_run_duplicate": 3,
        },
    }


def _jd_intelligence_summary() -> dict:
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["Airflow"],
        "required_tools": ["PostgreSQL"],
        "preferred_tools": ["dbt"],
        "methods": ["experimentation", "causal inference"],
        "workflows": ["batch pipelines", "metric reviews"],
        "business_contexts": ["marketplace growth"],
        "stakeholder_contexts": ["product managers", "data science"],
        "ownership_signals": ["owns data quality"],
        "seniority_indicators": ["technical leadership"],
    }


def _final_scoring_summary() -> dict:
    return {
        "input_count": 6,
        "scored_count": 5,
        "qualified_count": 3,
        "disqualified_count": 2,
        "score_summary": {
            "score_band_high": 2,
            "score_band_medium": 1,
            "score_band_low": 2,
        },
        "threshold_summary": {
            "qualification_threshold": 0.72,
            "disqualification_threshold": 0.45,
        },
        "decision_counts": {"qualified": 3, "disqualified": 2},
        "top_score": 0.94,
        "bottom_score": 0.31,
        "average_score": 0.68,
    }


def _stage_snapshots(run_id: str) -> list[dict]:
    context = _context()
    steps = [
        relevance_prefilter.build_relevance_prefilter_step_snapshot(
            context=context,
            prefilter_summary=_prefilter_summary(),
            observed_at_utc="2026-06-12T18:02:00Z",
            agent_run_id=run_id,
            step_index=1,
        ),
        deduplication.build_deduplication_step_snapshot(
            context=context,
            deduplication_summary=_deduplication_summary(),
            observed_at_utc="2026-06-12T18:03:00Z",
            agent_run_id=run_id,
            step_index=2,
        ),
        jd_intelligence.build_jd_intelligence_step_snapshot(
            context=context,
            jd_intelligence_summary=_jd_intelligence_summary(),
            observed_at_utc="2026-06-12T18:04:00Z",
            agent_run_id=run_id,
            step_index=3,
        ),
        final_application_scoring.build_final_application_scoring_step_snapshot(
            context=context,
            scoring_summary=_final_scoring_summary(),
            observed_at_utc="2026-06-12T18:05:00Z",
            agent_run_id=run_id,
            step_index=4,
        ),
    ]
    for step in steps:
        step.update(
            {
                "owner_user_id": "user_stage_bundle",
                "pipeline_run_id": "pipeline_stage_bundle",
                "status": step["step_status"],
                "started_at": step["observed_at_utc"],
            }
        )
    return steps


def _bundle() -> tuple[dict, list[dict], dict]:
    run = _run_snapshot()
    steps = _stage_snapshots(run["agent_run_id"])
    return run, steps, trace.build_stage_trace_bundle_payload(
        run_snapshot=run,
        step_snapshots=steps,
    )


def test_stage_trace_bundle_contains_all_four_steps_in_order():
    run, steps, bundle = _bundle()

    assert bundle["operation"] == "build_stage_trace_bundle_payload"
    assert bundle["bundle_type"] == "stage_trace_bundle"
    assert bundle["run_snapshot"] == run
    assert bundle["step_snapshots"] == steps
    assert bundle["step_count"] == 4
    assert bundle["stage_names"] == EXPECTED_STAGE_ORDER
    assert bundle["stage_order_validation"] == {
        "is_valid": True,
        "expected_stage_order": EXPECTED_STAGE_ORDER,
        "observed_stage_order": EXPECTED_STAGE_ORDER,
        "missing_expected_stages": [],
        "unexpected_stages": [],
        "duplicate_stages": [],
    }


def test_stage_trace_bundle_trace_summary_counts_all_steps():
    _, _, bundle = _bundle()

    assert bundle["trace_summary"]["summary_type"] == "agent_trace"
    assert bundle["trace_summary"]["run_count"] == 1
    assert bundle["trace_summary"]["step_count"] == 4
    assert bundle["trace_summary"]["agent_counts"] == {
        "deduplication_agent": 1,
        "final_application_scoring_agent": 1,
        "jd_intelligence_agent": 1,
        "relevance_prefilter_agent": 1,
    }


def test_stage_trace_bundle_detects_missing_stage():
    run = _run_snapshot()
    steps = _stage_snapshots(run["agent_run_id"])[:-1]

    bundle = trace.build_stage_trace_bundle_payload(
        run_snapshot=run,
        step_snapshots=steps,
    )

    assert bundle["stage_order_validation"]["is_valid"] is False
    assert bundle["missing_expected_stages"] == [
        "final_application_scoring_trace_wrapper",
    ]
    assert bundle["unexpected_stages"] == []
    assert bundle["duplicate_stages"] == []


def test_stage_trace_bundle_detects_duplicate_stage():
    run = _run_snapshot()
    steps = _stage_snapshots(run["agent_run_id"])
    steps.append(deepcopy(steps[0]))

    bundle = trace.build_stage_trace_bundle_payload(
        run_snapshot=run,
        step_snapshots=steps,
    )

    assert bundle["stage_order_validation"]["is_valid"] is False
    assert bundle["duplicate_stages"] == [
        {"stage_name": "relevance_prefilter_trace_wrapper", "count": 2},
    ]


def test_stage_trace_bundle_detects_unexpected_stage():
    run = _run_snapshot()
    steps = _stage_snapshots(run["agent_run_id"])
    steps[1]["step_name"] = "unexpected_trace_wrapper"
    steps[1]["agent_name"] = "unexpected_agent"

    bundle = trace.build_stage_trace_bundle_payload(
        run_snapshot=run,
        step_snapshots=steps,
    )

    assert bundle["stage_order_validation"]["is_valid"] is False
    assert bundle["missing_expected_stages"] == ["deduplication_trace_wrapper"]
    assert bundle["unexpected_stages"] == ["unexpected_trace_wrapper"]
    assert bundle["trace_summary"]["agent_counts"]["unexpected_agent"] == 1


def test_stage_trace_bundle_is_deterministic_and_does_not_mutate_inputs():
    run = _run_snapshot()
    steps = _stage_snapshots(run["agent_run_id"])
    original_run = deepcopy(run)
    original_steps = deepcopy(steps)

    first = trace.build_stage_trace_bundle_payload(
        run_snapshot=run,
        step_snapshots=steps,
    )
    second = trace.build_stage_trace_bundle_payload(
        run_snapshot=run,
        step_snapshots=steps,
    )

    assert run == original_run
    assert steps == original_steps
    assert first == second
    assert first["run_snapshot"] is not run
    assert first["step_snapshots"] is not steps


def test_stage_trace_bundle_safety_metadata_is_read_only():
    _, _, bundle = _bundle()

    assert bundle["safety_metadata"] == {
        "did_read_database": False,
        "did_write_database": False,
        "did_create_agent_run": False,
        "did_create_agent_step": False,
        "did_update_agent_run": False,
        "did_update_agent_step": False,
        "did_prepare_statement": False,
        "did_call_live_stage": False,
        "did_call_prefilter_relevance": False,
        "did_call_deduplication": False,
        "did_call_jd_intelligence": False,
        "did_call_final_application_scoring": False,
        "did_call_llm": False,
        "did_change_pipeline": False,
        "did_change_scoring": False,
        "did_change_ranking": False,
        "did_change_approval": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }
    assert bundle["trace_summary"]["safety_metadata"]["did_write_database"] is False
    assert bundle["trace_summary"]["safety_metadata"]["did_call_llm"] is False
    assert bundle["trace_summary"]["safety_metadata"]["did_execute_application"] is False
    assert bundle["trace_summary"]["safety_metadata"]["did_submit_application"] is False


def test_stage_trace_health_valid_bundle_is_healthy():
    _, _, bundle = _bundle()

    health = trace.evaluate_stage_trace_bundle_health(bundle)

    assert health["ok"] is True
    assert health["health_status"] == "healthy"
    assert health["findings"] == []
    assert health["warnings"] == []
    assert health["stage_order_valid"] is True
    assert health["missing_expected_stages"] == []
    assert health["unexpected_stages"] == []
    assert health["duplicate_stages"] == []
    assert health["all_required_fields_present"] is True


def test_stage_trace_health_missing_stage_returns_warning_and_finding():
    run = _run_snapshot()
    bundle = trace.build_stage_trace_bundle_payload(
        run_snapshot=run,
        step_snapshots=_stage_snapshots(run["agent_run_id"])[:-1],
    )

    health = trace.evaluate_stage_trace_bundle_health(bundle)

    assert health["ok"] is False
    assert health["health_status"] == "warning"
    assert "stage_order_invalid" in health["findings"]
    assert "missing_expected_stages" in health["findings"]
    assert "one_or_more_expected_stages_missing" in health["warnings"]
    assert health["missing_expected_stages"] == [
        "final_application_scoring_trace_wrapper",
    ]


def test_stage_trace_health_duplicate_and_unexpected_stage_returns_warning_and_finding():
    run = _run_snapshot()
    steps = _stage_snapshots(run["agent_run_id"])
    steps.append(deepcopy(steps[0]))
    steps[1]["step_name"] = "unexpected_trace_wrapper"
    bundle = trace.build_stage_trace_bundle_payload(
        run_snapshot=run,
        step_snapshots=steps,
    )

    health = trace.evaluate_stage_trace_bundle_health(bundle)

    assert health["ok"] is False
    assert health["health_status"] == "warning"
    assert "duplicate_stages" in health["findings"]
    assert "unexpected_stages" in health["findings"]
    assert "one_or_more_stage_names_duplicated" in health["warnings"]
    assert "one_or_more_unexpected_stages_present" in health["warnings"]
    assert health["unexpected_stages"] == ["unexpected_trace_wrapper"]
    assert health["duplicate_stages"] == [
        {"stage_name": "relevance_prefilter_trace_wrapper", "count": 2},
    ]


def test_stage_trace_health_is_deterministic_and_does_not_mutate_input():
    _, _, bundle = _bundle()
    original = deepcopy(bundle)

    first = trace.evaluate_stage_trace_bundle_health(bundle)
    second = trace.evaluate_stage_trace_bundle_health(bundle)

    assert bundle == original
    assert first == second


def test_stage_trace_health_safety_metadata_is_read_only():
    _, _, bundle = _bundle()
    health = trace.evaluate_stage_trace_bundle_health(bundle)

    assert health["safety_metadata"]["did_write_database"] is False
    assert health["safety_metadata"]["did_call_llm"] is False
    assert health["safety_metadata"]["did_change_ranking"] is False
    assert health["safety_metadata"]["did_change_scoring"] is False
    assert health["safety_metadata"]["did_change_approval"] is False
    assert health["safety_metadata"]["did_execute_application"] is False
    assert health["safety_metadata"]["did_submit_application"] is False


def test_stage_trace_bundle_helper_source_has_no_runtime_or_storage_execution_calls():
    source = Path("src/agents/trace.py").read_text()
    start = source.index("def stage_trace_bundle_safety_metadata")
    end = source.index("def build_agent_run_record_payload")
    helper_source = source[start:end]

    forbidden_tokens = [
        "prepare_agent_run_upsert",
        "prepare_agent_step_upsert",
        "execute_agent_trace_recording(",
        "create_agent_run(",
        "record_agent_step(",
        "complete_agent_run(",
        "connect(",
        ".commit(",
        "run_migration(",
        "run_llm",
        "model_client",
        "scheduler_execution(",
        "background_tasks.add_task",
        "src.pipeline",
        "rank_jobs",
        "score_jobs",
        "approval_mutation(",
        "approve_application(",
        "application_execution(",
        "application_submission(",
    ]
    for token in forbidden_tokens:
        assert token not in helper_source
