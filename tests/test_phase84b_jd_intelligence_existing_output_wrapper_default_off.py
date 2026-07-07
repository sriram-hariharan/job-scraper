from copy import deepcopy
from pathlib import Path

from src.agents.jd_intelligence import describe_existing_job_intelligence_result


ROOT = Path(__file__).resolve().parents[1]


def _already_intelligent_job():
    return {
        "job_id": "job-84b",
        "id": "fallback-id",
        "title": "Machine Learning Engineer",
        "company": "Example AI",
        "source": "greenhouse",
        "url": "https://example.test/jobs/84b",
        "role_family": "ml_ai_engineering",
        "intelligence": {
            "skills": {
                "required": ["python", "sql"],
                "preferred": ["airflow"],
                "all": ["python", "sql", "airflow"],
            },
            "visa_sponsorship": "possible",
        },
    }


def _assert_existing_output_safety(payload):
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["reused_existing_pipeline_output"] is True
    assert payload["provider_call_performed"] is False
    assert payload["duplicate_llm_call_performed"] is False
    assert payload["build_job_intelligence_called"] is False
    assert payload["skill_extraction_called"] is False
    assert payload["run_chat_completion_called"] is False
    assert payload["production_output_changed"] is False
    assert payload["database_write_performed"] is False
    assert payload["persistence_performed"] is False
    assert payload["auto_apply_performed"] is False
    assert payload["auto_submit_performed"] is False
    assert payload["ats_submission_performed"] is False
    assert payload["recruiter_message_sent"] is False
    assert payload["mark_applied_performed"] is False
    assert all(value is False for value in payload["safety_metadata"].values() if value is not True)


def test_already_intelligent_job_maps_existing_pipeline_output_without_mutation():
    job = _already_intelligent_job()
    original = deepcopy(job)

    payload = describe_existing_job_intelligence_result(job)

    assert job == original
    assert payload["status"] == "completed"
    assert payload["job_id"] == "job-84b"
    assert payload["title"] == "Machine Learning Engineer"
    assert payload["company"] == "Example AI"
    assert payload["source"] == "greenhouse"
    assert payload["url"] == "https://example.test/jobs/84b"
    assert payload["required_skills"] == ["python", "sql"]
    assert payload["preferred_skills"] == ["airflow"]
    assert payload["all_skills"] == ["python", "sql", "airflow"]
    assert payload["role_family"] == "ml_ai_engineering"
    assert payload["visa_sponsorship"] == "possible"
    assert payload["extraction_source"] == "existing_pipeline_job_intelligence"
    assert payload["validation_json"]["is_valid_for_existing_output_wrapper"] is True
    assert payload["validation_json"]["missing_or_invalid_fields"] == []
    assert payload["metadata"]["wrapper_version"] == "jd-intelligence-existing-output-wrapper-v1"
    _assert_existing_output_safety(payload)


def test_job_without_description_shape_remains_empty_and_read_only():
    job = {
        "id": "job-empty-description",
        "title": "Data Analyst",
        "company": "Example Data",
        "job_source": "lever",
        "job_url": "https://example.test/jobs/empty",
        "intelligence": {
            "skills": {
                "required": [],
                "preferred": [],
                "all": [],
            },
            "visa_sponsorship": None,
        },
    }

    payload = describe_existing_job_intelligence_result(job)

    assert payload["status"] == "completed"
    assert payload["job_id"] == "job-empty-description"
    assert payload["source"] == "lever"
    assert payload["url"] == "https://example.test/jobs/empty"
    assert payload["required_skills"] == []
    assert payload["preferred_skills"] == []
    assert payload["all_skills"] == []
    assert payload["role_family"] == ""
    assert payload["visa_sponsorship"] is None
    assert payload["validation_json"]["is_valid_for_existing_output_wrapper"] is True
    _assert_existing_output_safety(payload)


def test_missing_fields_are_empty_unknown_and_not_hallucinated():
    payload = describe_existing_job_intelligence_result(_already_intelligent_job())

    assert payload["seniority_signals"] == []
    assert payload["domain_signals"] == []
    assert payload["responsibilities"] == []
    assert payload["tools"] == []
    assert payload["location_constraints"] == []
    assert payload["red_flags"] == []
    assert payload["confidence"] is None


def test_malformed_nested_intelligence_returns_validation_warnings_without_extraction():
    job = {
        "job_id": "bad-shape",
        "title": "Backend Engineer",
        "company": "Example Cloud",
        "platform": "ashby",
        "posting_url": "https://example.test/jobs/bad",
        "role_family": "backend_engineering",
        "intelligence": {
            "skills": {
                "required": "python",
                "preferred": {"not": "a-list"},
                "all": None,
            },
            "visa_sponsorship": "unknown",
        },
    }

    payload = describe_existing_job_intelligence_result(job)

    assert payload["status"] == "invalid"
    assert payload["required_skills"] == []
    assert payload["preferred_skills"] == []
    assert payload["all_skills"] == []
    assert payload["validation_json"]["has_intelligence_object"] is True
    assert payload["validation_json"]["has_skills_object"] is True
    assert payload["validation_json"]["required_skills_valid_list"] is False
    assert payload["validation_json"]["preferred_skills_valid_list"] is False
    assert payload["validation_json"]["all_skills_valid_list"] is False
    assert payload["validation_json"]["missing_or_invalid_fields"] == [
        "required_skills_not_list",
        "preferred_skills_not_list",
        "all_skills_not_list",
    ]
    assert payload["validation_json"]["did_trigger_extraction"] is False
    _assert_existing_output_safety(payload)


def test_missing_intelligence_object_does_not_raise_or_extract():
    payload = describe_existing_job_intelligence_result(
        {
            "id": "missing-intelligence",
            "title": "Software Engineer",
            "company": "Example Apps",
        }
    )

    assert payload["status"] == "invalid"
    assert payload["required_skills"] == []
    assert payload["preferred_skills"] == []
    assert payload["all_skills"] == []
    assert payload["validation_json"]["has_intelligence_object"] is False
    assert payload["validation_json"]["has_skills_object"] is False
    assert "intelligence_not_object" in payload["validation_json"]["missing_or_invalid_fields"]
    assert "required_skills_not_list" in payload["validation_json"]["missing_or_invalid_fields"]
    assert payload["validation_json"]["did_trigger_extraction"] is False
    _assert_existing_output_safety(payload)


def test_helper_source_has_no_duplicate_call_or_provider_path():
    source = (ROOT / "src/agents/jd_intelligence.py").read_text(encoding="utf-8")
    forbidden_tokens = [
        "from src.ai.llm_client import",
        "run_chat_completion(",
        "run_chat_completion_with_metadata(",
        "enrich_skills_with_llm",
        "from src.intelligence.job_intelligence import",
        "from groq import Groq",
        "from openai import OpenAI",
        "from google import genai",
        "src.pipeline.collector",
        "workflow_runner",
    ]
    for token in forbidden_tokens:
        assert token not in source
