from copy import deepcopy

import pytest

from src.agents.agent_state import JobApplicationContext
from src.agents import (
    deduplication,
    final_application_scoring,
    jd_intelligence,
    relevance_prefilter,
)


def _context(label: str) -> JobApplicationContext:
    return JobApplicationContext(
        approval_request_id=f"approval_{label}",
        job_id=f"job_{label}",
        candidate_key=f"candidate_{label}",
        role_family="software_engineering",
        run_mode="dry_run",
        observed_at_utc="2026-06-12T17:00:00Z",
        metadata={"source": "aggregate_trace_summary_test"},
    )


def _prefilter_summary() -> dict:
    return {
        "input_count": 5,
        "kept_count": 3,
        "dropped_count": 2,
        "reason_counts": {
            "title_match": 3,
            "location_reject": 1,
            "freshness_reject": 1,
        },
        "embedding_similarity_summary": {"min": 0.11, "max": 0.91, "mean": 0.52},
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
        "decision_counts": {
            "qualified": 3,
            "disqualified": 2,
        },
        "top_score": 0.94,
        "bottom_score": 0.31,
        "average_score": 0.68,
    }


STAGE_CASES = (
    {
        "label": "relevance_prefilter",
        "agent_name": "relevance_prefilter_agent",
        "describe": relevance_prefilter.describe_relevance_prefilter_result,
        "snapshot": relevance_prefilter.build_relevance_prefilter_step_snapshot,
        "summary_kw": "prefilter_summary",
        "valid_summary": _prefilter_summary,
        "invalid_summary": lambda: {
            **_prefilter_summary(),
            "kept_count": 4,
        },
        "expected_errors": ["kept_dropped_count_mismatch"],
        "stage_flags": (
            "did_call_live_filter",
            "did_call_llm_evaluation",
            "did_call_final_application_scoring",
        ),
    },
    {
        "label": "deduplication",
        "agent_name": "deduplication_agent",
        "describe": deduplication.describe_deduplication_result,
        "snapshot": deduplication.build_deduplication_step_snapshot,
        "summary_kw": "deduplication_summary",
        "valid_summary": _deduplication_summary,
        "invalid_summary": lambda: {
            **_deduplication_summary(),
            "new_count": 4,
        },
        "expected_errors": ["seen_new_unique_count_mismatch"],
        "stage_flags": (
            "did_call_live_deduplication",
            "did_call_prefilter_relevance",
            "did_call_llm_evaluation",
            "did_call_final_application_scoring",
        ),
    },
    {
        "label": "jd_intelligence",
        "agent_name": "jd_intelligence_agent",
        "describe": jd_intelligence.describe_jd_intelligence_result,
        "snapshot": jd_intelligence.build_jd_intelligence_step_snapshot,
        "summary_kw": "jd_intelligence_summary",
        "valid_summary": _jd_intelligence_summary,
        "invalid_summary": lambda: {
            **_jd_intelligence_summary(),
            "required_skills": "Python",
        },
        "expected_errors": ["required_skills_not_list"],
        "stage_flags": (
            "did_call_live_jd_extraction",
            "did_call_llm_provider",
            "did_call_prefilter_relevance",
            "did_call_deduplication",
            "did_call_final_application_scoring",
        ),
    },
    {
        "label": "final_application_scoring",
        "agent_name": "final_application_scoring_agent",
        "describe": final_application_scoring.describe_final_application_scoring_result,
        "snapshot": final_application_scoring.build_final_application_scoring_step_snapshot,
        "summary_kw": "scoring_summary",
        "valid_summary": _final_scoring_summary,
        "invalid_summary": lambda: {
            **_final_scoring_summary(),
            "qualified_count": 4,
        },
        "expected_errors": ["qualified_disqualified_scored_count_mismatch"],
        "stage_flags": (
            "did_call_live_final_application_scoring",
            "did_call_prefilter_relevance",
            "did_call_deduplication",
            "did_call_jd_intelligence",
            "did_call_llm_provider",
        ),
    },
)


def _ids(case: dict) -> str:
    return case["label"]


def _assert_trace_summary_is_read_only(trace_summary: dict) -> None:
    assert trace_summary["summary_type"] == "agent_trace"
    assert trace_summary["safety_metadata"]["did_write_database"] is False
    assert trace_summary["safety_metadata"]["did_call_llm"] is False
    assert trace_summary["safety_metadata"]["did_change_pipeline"] is False
    assert trace_summary["safety_metadata"].get("did_change_ranking", False) is False
    assert trace_summary["safety_metadata"].get("did_change_approval", False) is False
    assert trace_summary["safety_metadata"]["did_execute_application"] is False
    assert trace_summary["safety_metadata"]["did_submit_application"] is False


@pytest.mark.parametrize("case", STAGE_CASES, ids=_ids)
def test_stage_wrapper_describe_trace_summary_is_consistent_and_opt_in(case):
    summary = case["valid_summary"]()
    original = deepcopy(summary)

    default_payload = case["describe"](summary)
    first = case["describe"](summary, include_trace_summary=True)
    second = case["describe"](summary, include_trace_summary=True)

    assert summary == original
    assert first == second
    assert "trace_summary" not in default_payload
    assert "trace_summary" not in default_payload["output_json"]
    assert "trace_summary" in first
    assert "trace_summary" not in first["output_json"]
    assert first["trace_summary"]["agent_counts"] == {case["agent_name"]: 1}
    assert first["trace_summary"]["step_count"] == 1
    _assert_trace_summary_is_read_only(first["trace_summary"])


@pytest.mark.parametrize("case", STAGE_CASES, ids=_ids)
def test_stage_wrapper_snapshot_trace_summary_is_consistent_and_opt_in(case):
    summary = case["valid_summary"]()
    original = deepcopy(summary)
    kwargs = {
        "context": _context(case["label"]),
        case["summary_kw"]: summary,
        "observed_at_utc": "2026-06-12T17:01:00Z",
        "agent_run_id": f"agent_run_{case['label']}",
    }

    default_step = case["snapshot"](**kwargs)
    opt_in_step = case["snapshot"](**kwargs, include_trace_summary=True)

    assert summary == original
    assert "trace_summary" not in default_step["metadata"]
    assert "trace_summary" not in default_step["output_summary"]
    assert "trace_summary" in opt_in_step["metadata"]
    assert "trace_summary" not in opt_in_step["output_summary"]
    _assert_trace_summary_is_read_only(opt_in_step["metadata"]["trace_summary"])


@pytest.mark.parametrize("case", STAGE_CASES, ids=_ids)
def test_invalid_stage_wrapper_summaries_preserve_errors_without_other_stage_calls(case):
    summary = case["invalid_summary"]()
    original = deepcopy(summary)

    payload = case["describe"](summary, include_trace_summary=True)

    assert summary == original
    assert payload["status"] == "invalid"
    assert payload["validation_json"]["is_valid"] is False
    assert payload["validation_json"]["errors"] == case["expected_errors"]
    for flag in case["stage_flags"]:
        assert payload[flag] is False
        if flag in payload["validation_json"]:
            assert payload["validation_json"][flag] is False
    assert payload.get("did_execute_application", False) is False
    assert payload.get("did_submit_application", False) is False
    assert payload["trace_summary"]["step_status_counts"] == {"invalid": 1}
    _assert_trace_summary_is_read_only(payload["trace_summary"])
