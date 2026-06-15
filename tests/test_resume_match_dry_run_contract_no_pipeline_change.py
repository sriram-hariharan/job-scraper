from copy import deepcopy
from pathlib import Path

from src.agents import resume_match_agent


def _jd_signals() -> dict:
    return {
        "required_skills": ["Python", "SQL", "RAG"],
        "preferred_skills": ["machine learning"],
        "required_tools": ["Airflow", "dbt"],
        "preferred_tools": ["Snowflake"],
        "workflows": ["production data pipelines", "LLMOps evaluation"],
        "methods": ["stakeholder reporting"],
        "business_contexts": ["analytics platform"],
        "stakeholder_contexts": ["finance partners"],
        "ownership_signals": ["owned production workflows"],
        "seniority_signals": ["senior IC scope"],
    }


def _strong_resume(resume_id: str = "strong_resume") -> dict:
    return {
        "resume_id": resume_id,
        "skills": ["Python", "SQL", "RAG", "machine learning"],
        "tools": ["Airflow", "dbt", "Snowflake"],
        "workflows": ["production data pipelines", "LLMOps evaluation"],
        "methods": ["stakeholder reporting"],
        "business_contexts": ["analytics platform"],
        "stakeholder_contexts": ["finance partners"],
        "ownership_signals": ["owned production workflows"],
        "seniority_signals": ["senior IC scope"],
        "raw_text": (
            "Senior IC scope owning production data pipelines in Python, SQL, Airflow, dbt, "
            "Snowflake, RAG, machine learning, LLMOps evaluation, analytics platform work, "
            "stakeholder reporting with finance partners."
        ),
    }


def _weak_resume() -> dict:
    return {
        "resume_id": "weak_resume",
        "skills": ["Excel"],
        "tools": ["Tableau"],
        "raw_text": "Built dashboards and basic reporting.",
    }


def _assert_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert safety["dry_run_only"] is True
    assert safety["deterministic_only"] is True
    assert safety["did_call_llm"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False


def test_strong_evidence_produces_strong_match_signals():
    payload = resume_match_agent.build_resume_match_dry_run_payload(
        jd_intelligence=_jd_signals(),
        resume_variants=[_strong_resume()],
        context_id="ctx-1",
        job_id="job-1",
    )

    assert payload["match_status"] == "strong_match"
    assert payload["recommendation_label"] == "strong_match"
    assert payload["selected_resume_id"] == "strong_resume"
    assert payload["confidence"] >= 0.70
    assert payload["dimension_scores"]["hard_skills"] == 1.0
    assert payload["dimension_scores"]["tools"] == 1.0
    assert payload["dimension_scores"]["ai_ml_rag_llmops"] == 1.0
    assert any(row["signal"] == "Python" for row in payload["matched_evidence"])
    assert "required_skills" in payload["source_fields_used"]
    assert payload["context_id"] == "ctx-1"
    assert payload["job_id"] == "job-1"
    _assert_safety(payload)


def test_missing_jd_signals_returns_safe_low_information_payload():
    payload = resume_match_agent.build_resume_match_dry_run_payload(
        jd_intelligence={},
        resume_variants=[_strong_resume()],
    )

    assert payload["match_status"] == "insufficient_jd_signals"
    assert payload["recommendation_label"] == "manual_review"
    assert payload["confidence"] == 0.0
    assert "jd_signals_missing" in payload["missing_evidence"]
    assert "low_information_jd" in payload["risk_flags"]
    assert payload["matched_evidence"] == []
    _assert_safety(payload)


def test_missing_resume_evidence_returns_missing_evidence_without_crashing():
    payload = resume_match_agent.build_resume_match_dry_run_payload(
        jd_intelligence=_jd_signals(),
        resume_variants=[],
    )

    assert payload["match_status"] == "insufficient_evidence"
    assert payload["selected_resume_id"] == ""
    assert payload["candidate_resume_scores"] == []
    assert "resume_evidence_missing" in payload["missing_evidence"]
    assert "resume_evidence_unavailable" in payload["risk_flags"]
    assert payload["recommendation_label"] == "manual_review"
    _assert_safety(payload)


def test_multiple_resume_variants_are_ranked_only_inside_returned_payload():
    payload = resume_match_agent.build_resume_match_dry_run_payload(
        jd_intelligence=_jd_signals(),
        resume_variants=[_weak_resume(), _strong_resume("best_resume")],
    )

    assert [row["resume_id"] for row in payload["candidate_resume_scores"]] == [
        "best_resume",
        "weak_resume",
    ]
    assert payload["selected_resume_id"] == "best_resume"
    assert payload["candidate_resume_scores"][0]["score"] > payload["candidate_resume_scores"][1]["score"]
    _assert_safety(payload)


def test_selected_resume_id_can_focus_returned_dry_run_without_mutating_rank():
    payload = resume_match_agent.build_resume_match_dry_run_payload(
        jd_intelligence=_jd_signals(),
        resume_variants=[_weak_resume(), _strong_resume("best_resume")],
        selected_resume_id="weak_resume",
    )

    assert payload["selected_resume_id"] == "weak_resume"
    assert [row["resume_id"] for row in payload["candidate_resume_scores"]] == [
        "best_resume",
        "weak_resume",
    ]
    assert payload["match_status"] in {"weak_match", "partial_match"}
    _assert_safety(payload)


def test_resume_match_dry_run_does_not_mutate_inputs():
    jd = _jd_signals()
    resumes = [_weak_resume(), _strong_resume()]
    original_jd = deepcopy(jd)
    original_resumes = deepcopy(resumes)

    first = resume_match_agent.build_resume_match_dry_run_payload(
        jd_intelligence=jd,
        resume_variants=resumes,
    )
    second = resume_match_agent.build_resume_match_dry_run_payload(
        jd_intelligence=jd,
        resume_variants=resumes,
    )

    assert first == second
    assert jd == original_jd
    assert resumes == original_resumes
    _assert_safety(first)


def test_resume_match_dry_run_source_has_no_runtime_side_effect_markers():
    source = Path("src/agents/resume_match_agent.py").read_text()
    start = source.index("RESUME_MATCH_DRY_RUN_DIMENSIONS")
    snippet = source[start:]

    forbidden_markers = [
        "run_chat_completion",
        "src.ai.llm_client",
        "build_resume_evidence(",
        "score_resume_job_match",
        "create_agent_run(",
        "record_agent_step(",
        "complete_agent_run(",
        "cursor.execute",
        ".commit(",
        "subprocess",
        "application_execution_queue",
        "execute_application(",
        "submit_application(",
        "approval_store",
        "workflow_runner",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet
