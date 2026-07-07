from copy import deepcopy
from pathlib import Path

from src.agents.jd_intelligence import (
    build_existing_job_intelligence_trace_payload,
    describe_existing_job_intelligence_result,
)
from tests.support.phase_guard_registry import assert_no_forbidden_runtime_calls_ast


ROOT = Path(__file__).resolve().parents[1]


def _already_intelligent_job(index: int = 1) -> dict:
    return {
        "job_id": f"job-86b-{index}",
        "title": f"Data Platform Engineer {index}",
        "company": "Example Systems",
        "source": "greenhouse",
        "url": f"https://example.test/jobs/86b-{index}",
        "role_family": "data_engineering",
        "intelligence": {
            "skills": {
                "required": ["python", "sql", f"skill-{index}"],
                "preferred": ["airflow"],
                "all": ["python", "sql", "airflow", f"skill-{index}"],
            },
            "visa_sponsorship": "unknown",
        },
    }


def _assert_trace_payload_safety(payload: dict) -> None:
    assert payload["reused_existing_pipeline_output"] is True
    assert payload["provider_call_performed"] is False
    assert payload["duplicate_llm_call_performed"] is False
    assert payload["trace_persistence_requested"] is False
    assert payload["trace_persistence_performed"] is False
    assert payload["production_output_changed"] is False
    for key in (
        "auto_apply_performed",
        "auto_submit_performed",
        "ats_submission_performed",
        "apply_click_performed",
        "recruiter_message_sent",
        "mark_applied_performed",
        "provider_call_performed",
        "duplicate_llm_call_performed",
        "build_job_intelligence_called",
        "skill_extraction_called",
        "run_chat_completion_called",
        "evaluate_jobs_called",
        "database_write_performed",
        "trace_persistence_performed",
        "production_output_changed",
        "scoring_changed",
        "ranking_changed",
        "filtering_changed",
        "queue_changed",
        "scheduler_changed",
        "tailoring_changed",
        "source_resume_changed",
        "workflow_runner_live_execution_performed",
    ):
        assert payload[key] is False
        assert payload["safety_metadata"][key] is False
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["safety_metadata"]["read_only"] is True
    assert payload["safety_metadata"]["advisory_only"] is True


def test_trace_payload_aggregates_existing_job_intelligence_without_mutation():
    jobs = [_already_intelligent_job(1), _already_intelligent_job(2)]
    original = deepcopy(jobs)

    payload = build_existing_job_intelligence_trace_payload(jobs)

    assert jobs == original
    assert payload["stage_name"] == "jd_intelligence_existing_output"
    assert payload["source_stage"] == "intelligence"
    assert payload["wrapper_version"] == "jd-intelligence-existing-output-trace-payload-v1"
    assert payload["sample_limit"] == 10
    assert payload["job_count_seen"] == 2
    assert payload["job_count_sampled"] == 2
    assert payload["omitted_job_count"] == 0
    assert [job["job_id"] for job in payload["jobs"]] == ["job-86b-1", "job-86b-2"]
    assert payload["jobs"][0] == describe_existing_job_intelligence_result(jobs[0])
    assert payload["validation_summary"] == {
        "total_jobs_seen": 2,
        "sampled_jobs": 2,
        "valid_wrapper_outputs": 2,
        "invalid_wrapper_outputs": 0,
        "missing_intelligence_count": 0,
        "missing_skills_count": 0,
        "malformed_intelligence_count": 0,
        "malformed_skills_count": 0,
        "provider_call_performed": False,
        "duplicate_llm_call_performed": False,
        "production_output_changed": False,
    }
    _assert_trace_payload_safety(payload)


def test_trace_payload_uses_deterministic_first_n_sampling_and_omitted_count():
    jobs = [_already_intelligent_job(index) for index in range(1, 8)]

    payload = build_existing_job_intelligence_trace_payload(jobs, sample_limit=3)

    assert payload["job_count_seen"] == 7
    assert payload["job_count_sampled"] == 3
    assert payload["omitted_job_count"] == 4
    assert [job["job_id"] for job in payload["jobs"]] == [
        "job-86b-1",
        "job-86b-2",
        "job-86b-3",
    ]


def test_trace_payload_hard_caps_sample_limit_and_handles_invalid_limits():
    jobs = [_already_intelligent_job(index) for index in range(1, 31)]

    capped = build_existing_job_intelligence_trace_payload(jobs, sample_limit=99)
    fallback = build_existing_job_intelligence_trace_payload(jobs, sample_limit="not-int")
    empty = build_existing_job_intelligence_trace_payload(jobs, sample_limit=-4)

    assert capped["sample_limit"] == 25
    assert capped["job_count_sampled"] == 25
    assert capped["omitted_job_count"] == 5
    assert fallback["sample_limit"] == 10
    assert fallback["job_count_sampled"] == 10
    assert empty["sample_limit"] == 0
    assert empty["job_count_sampled"] == 0
    assert empty["omitted_job_count"] == 30


def test_trace_payload_counts_malformed_and_missing_intelligence_without_raising():
    jobs = [
        _already_intelligent_job(1),
        {"job_id": "missing-intelligence", "title": "Missing"},
        {"job_id": "malformed-intelligence", "intelligence": "bad"},
        {"job_id": "missing-skills", "intelligence": {}},
        {"job_id": "malformed-skills", "intelligence": {"skills": []}},
        {
            "job_id": "bad-skill-lists",
            "intelligence": {
                "skills": {
                    "required": "python",
                    "preferred": [],
                    "all": [],
                }
            },
        },
    ]

    payload = build_existing_job_intelligence_trace_payload(jobs)

    assert payload["job_count_seen"] == 6
    assert payload["job_count_sampled"] == 6
    summary = payload["validation_summary"]
    assert summary["valid_wrapper_outputs"] == 1
    assert summary["invalid_wrapper_outputs"] == 5
    assert summary["missing_intelligence_count"] == 1
    assert summary["malformed_intelligence_count"] == 1
    assert summary["missing_skills_count"] == 1
    assert summary["malformed_skills_count"] == 2
    invalid = [job for job in payload["jobs"] if job["status"] == "invalid"]
    assert len(invalid) == 5
    assert all(job["provider_call_performed"] is False for job in payload["jobs"])


def test_trace_payload_accepts_generators_and_mapping_singletons():
    generator_payload = build_existing_job_intelligence_trace_payload(
        _already_intelligent_job(index) for index in range(1, 4)
    )
    singleton_payload = build_existing_job_intelligence_trace_payload(
        _already_intelligent_job(9)
    )

    assert generator_payload["job_count_seen"] == 3
    assert generator_payload["job_count_sampled"] == 3
    assert singleton_payload["job_count_seen"] == 1
    assert singleton_payload["jobs"][0]["job_id"] == "job-86b-9"


def test_trace_payload_source_has_no_provider_extraction_collector_or_persistence_calls():
    path = ROOT / "src/agents/jd_intelligence.py"
    source = path.read_text(encoding="utf-8")
    forbidden_tokens = [
        "from src.ai.llm_client import",
        "from src.intelligence.job_intelligence import",
        "from src.pipeline.collector import",
        "from src.app.services import",
        "from src.app.api import",
        "run_chat_completion(",
        "run_chat_completion_with_metadata(",
        "enrich_skills_with_llm(",
        "build_job_intelligence(",
        "evaluate_jobs(",
        "record_agent_step_postgres_payload(",
        "create_agent_run_postgres_payload(",
        "agent_trace_payload(",
        "cursor.execute(",
        "commit(",
        "workflow_runner",
    ]
    for token in forbidden_tokens:
        assert token not in source
    assert_no_forbidden_runtime_calls_ast(
        [path],
        forbidden_calls=(
            "run_chat_completion",
            "run_chat_completion_with_metadata",
            "enrich_skills_with_llm",
            "build_job_intelligence",
            "evaluate_jobs",
            "record_agent_step_postgres_payload",
            "create_agent_run_postgres_payload",
            "agent_trace_payload",
            "submit_application",
            "execute_application",
            "click_apply",
            "mark_as_applied",
            "send_recruiter_message",
        ),
        forbidden_imports=(
            "src.ai.llm_client",
            "src.intelligence.job_intelligence",
            "src.pipeline.collector",
            "src.app.services",
            "src.app.api",
            "src.agents.workflow_runner",
        ),
    )
