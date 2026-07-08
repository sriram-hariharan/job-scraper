import ast
from copy import deepcopy
from pathlib import Path

from src.agents import resume_match_agent


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "jd_extraction_performed",
    "trace_persistence_performed",
    "collector_output_changed",
    "production_output_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "workflow_runner_executed",
    "auto_apply_performed",
    "ats_submission_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
]


def _jd_wrapper_output() -> dict:
    return {
        "status": "completed",
        "job_id": "job-89b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "required_skills": ["Python", "SQL", "RAG"],
        "preferred_skills": ["Airflow", "Snowflake"],
        "all_skills": ["Python", "SQL", "RAG", "Airflow", "Snowflake"],
        "extraction_source": "existing_pipeline_job_intelligence",
        "validation_json": {
            "is_valid_for_existing_output_wrapper": True,
            "missing_or_invalid_fields": [],
        },
        "safety_metadata": {
            "provider_call_performed": False,
            "duplicate_llm_call_performed": False,
        },
    }


def _resume_evidence(resume_id: str = "resume-main") -> dict:
    return {
        "resume_id": resume_id,
        "skills": ["Python", "RAG", "Airflow"],
        "raw_text": (
            "Built production RAG platforms in Python with Airflow orchestration "
            "and stakeholder-facing AI evaluation workflows."
        ),
    }


def _assert_safety(payload: dict) -> None:
    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["diagnostic_only"] is True
    safety = payload["safety_metadata"]
    for flag in REQUIRED_FALSE_SAFETY_FLAGS:
        assert payload[flag] is False
        assert safety[flag] is False


def test_jd_wrapper_output_builds_deterministic_resume_match_evidence_artifact():
    payload = resume_match_agent.build_resume_match_jd_evidence_artifact(
        jd_intelligence=_jd_wrapper_output(),
        resume_variants=[_resume_evidence()],
    )

    assert payload["artifact_type"] == "resume_match_jd_evidence"
    assert payload["source_agent"] == "resume_match"
    assert payload["upstream_agent"] == "jd_intelligence"
    assert payload["upstream_evidence_source"] == "existing_pipeline_job_intelligence"
    assert payload["job_id"] == "job-89b"
    assert payload["title"] == "AI Platform Engineer"
    assert payload["company"] == "Example AI"
    assert payload["jd_required_skills"] == ["Python", "SQL", "RAG"]
    assert payload["jd_preferred_skills"] == ["Airflow", "Snowflake"]
    assert payload["jd_all_skills"] == ["Python", "SQL", "RAG", "Airflow", "Snowflake"]
    assert payload["matched_required_skills"] == ["Python", "RAG"]
    assert payload["missing_required_skills"] == ["SQL"]
    assert payload["matched_preferred_skills"] == ["Airflow"]
    assert payload["missing_preferred_skills"] == ["Snowflake"]
    assert payload["selected_resume_id"] == "resume-main"
    assert "skills" in payload["resume_evidence_fields_used"]
    assert "raw_text" in payload["resume_evidence_fields_used"]
    assert payload["match_status"] in {"partial_match", "strong_match", "weak_match"}
    assert payload["recommendation_label"] == payload["match_status"]
    assert payload["critic_input_summary"]["job_id"] == "job-89b"
    assert payload["critic_input_summary"]["missing_required_skill_count"] == 1
    assert payload["validation_summary"]["validation_status"] == "passed"
    assert payload["reason_codes"] == []
    _assert_safety(payload)


def test_missing_jd_intelligence_returns_degraded_artifact_without_crashing():
    payload = resume_match_agent.build_resume_match_jd_evidence_artifact(
        jd_intelligence=None,
        resume_variants=[_resume_evidence()],
        job_id="job-missing",
        title="Unknown Role",
        company="Unknown Co",
    )

    assert payload["artifact_type"] == "resume_match_jd_evidence"
    assert payload["job_id"] == "job-missing"
    assert payload["match_status"] == "insufficient_jd_signals"
    assert "jd_intelligence_missing" in payload["reason_codes"]
    assert "jd_required_skills_missing" in payload["reason_codes"]
    assert payload["matched_required_skills"] == []
    assert payload["missing_required_skills"] == []
    assert payload["validation_summary"]["validation_status"] == "degraded"
    _assert_safety(payload)


def test_malformed_jd_intelligence_is_reported_without_extraction_fallback():
    malformed = {
        "job_id": "job-bad",
        "required_skills": "Python",
        "preferred_skills": {"not": "a-list"},
        "validation_json": {
            "is_valid_for_existing_output_wrapper": False,
            "missing_or_invalid_fields": [
                "required_skills_not_list",
                "preferred_skills_not_list",
            ],
        },
    }

    payload = resume_match_agent.build_resume_match_jd_evidence_artifact(
        jd_intelligence=malformed,
        resume_variants=[_resume_evidence()],
    )

    assert payload["job_id"] == "job-bad"
    assert "jd_intelligence_malformed" in payload["reason_codes"]
    assert "required_skills_not_list" in payload["reason_codes"]
    assert "preferred_skills_not_list" in payload["reason_codes"]
    assert payload["validation_summary"]["jd_intelligence_valid"] is False
    assert payload["jd_extraction_performed"] is False
    assert payload["provider_call_performed"] is False
    _assert_safety(payload)


def test_helper_reuses_existing_resume_match_dry_run_logic(monkeypatch):
    original = resume_match_agent.build_resume_match_dry_run_payload
    calls = []

    def wrapped(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(resume_match_agent, "build_resume_match_dry_run_payload", wrapped)

    payload = resume_match_agent.build_resume_match_jd_evidence_artifact(
        jd_intelligence=_jd_wrapper_output(),
        resume_variants=[_resume_evidence()],
        selected_resume_id="resume-main",
    )

    assert len(calls) == 1
    assert calls[0]["jd_intelligence"]["required_skills"] == ["Python", "SQL", "RAG"]
    assert calls[0]["selected_resume_id"] == "resume-main"
    assert payload["selected_resume_id"] == "resume-main"


def test_helper_is_deterministic_and_does_not_mutate_inputs():
    jd = _jd_wrapper_output()
    resumes = [_resume_evidence()]
    original_jd = deepcopy(jd)
    original_resumes = deepcopy(resumes)

    first = resume_match_agent.build_resume_match_jd_evidence_artifact(
        jd_intelligence=jd,
        resume_variants=resumes,
    )
    second = resume_match_agent.build_resume_match_jd_evidence_artifact(
        jd_intelligence=jd,
        resume_variants=resumes,
    )

    assert first == second
    assert jd == original_jd
    assert resumes == original_resumes
    _assert_safety(first)


def test_helper_source_does_not_call_extraction_provider_trace_or_runtime_paths():
    source = (ROOT / "src/agents/resume_match_agent.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_resume_match_jd_evidence_artifact"
    )
    called_names = {
        node.func.id
        for node in ast.walk(helper)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attrs = {
        node.func.attr
        for node in ast.walk(helper)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    forbidden_calls = {
        "build_job_intelligence",
        "describe_existing_job_intelligence_result",
        "build_existing_job_intelligence_trace_payload",
        "persist_existing_job_intelligence_trace_payload",
        "enrich_skills_with_llm",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "evaluate_jobs",
        "score_jobs",
        "create_agent_run",
        "record_agent_step",
        "complete_agent_run",
        "execute_application",
        "submit_application",
    }

    assert forbidden_calls.isdisjoint(called_names)
    assert forbidden_calls.isdisjoint(called_attrs)
    assert "build_resume_match_dry_run_payload" in called_names

    helper_source = ast.get_source_segment(source, helper)
    forbidden_markers = [
        "src.pipeline.collector",
        "src.app.api",
        "src.app.services",
        "workflow_runner",
        "OpenAI",
        "Groq",
        "genai",
        "cursor.execute",
        ".commit(",
        "application_execution_queue",
    ]
    for marker in forbidden_markers:
        assert marker not in helper_source
