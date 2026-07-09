from copy import deepcopy
from pathlib import Path

import pytest

from src.agents.jd_intelligence import (
    CONTROLLED_LLM_ARTIFACT_TYPE,
    CONTROLLED_LLM_GATE_NAME,
    build_jd_intelligence_controlled_llm_artifact,
)
from tests.support.phase_guard_registry import assert_no_forbidden_runtime_calls_ast


# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405 d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 cc2de35be2ccdf50640b5933651f0d8ef596a400d4c38436ea8aebd8320a9d6c 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b c0c7a0a229a0cc9a1042c84c37a1728a33707e1035f6d604b6fe6aa74cc4b5e7
ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src/agents/jd_intelligence.py"


def _job_with_intelligence() -> dict:
    return {
        "job_id": "job-102b-existing",
        "title": "Data Platform Engineer",
        "company": "Example Systems",
        "description": "Build Python data platforms.",
        "intelligence": {
            "skills": {
                "required": ["Python", "SQL"],
                "preferred": ["Airflow"],
                "all": ["Python", "SQL", "Airflow"],
            },
            "visa_sponsorship": "unknown",
        },
    }


def _job_without_intelligence() -> dict:
    return {
        "job_id": "job-102b-missing",
        "title": "Analytics Engineer",
        "company": "Example Data",
        "job_description": "Own dbt models and metrics pipelines.",
    }


def _assert_no_production_mutation(payload: dict) -> None:
    safety = payload["safety_metadata"]
    for key in (
        "database_write_performed",
        "trace_persistence_performed",
        "collector_output_changed",
        "production_output_changed",
        "scoring_changed",
        "ranking_changed",
        "filtering_changed",
        "queue_mutation_performed",
        "review_queue_mutation_performed",
        "scheduler_mutation_performed",
        "tailoring_mutation_performed",
        "source_resume_mutation_performed",
        "generated_resume_mutation_performed",
        "application_status_changed",
        "auto_apply_performed",
        "ats_submission_performed",
        "apply_click_performed",
        "recruiter_message_sent",
        "mark_applied_performed",
        "external_action_automation_performed",
    ):
        assert payload[key] is False
        assert safety[key] is False
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True


def test_existing_intelligence_is_reused_and_avoids_duplicate_llm_call():
    job = _job_with_intelligence()
    original = deepcopy(job)

    def fail_if_called(_packet):
        raise AssertionError("extraction helper should not be called")

    payload = build_jd_intelligence_controlled_llm_artifact(
        job,
        enabled=True,
        extraction_helper=fail_if_called,
    )

    assert job == original
    assert payload["artifact_type"] == CONTROLLED_LLM_ARTIFACT_TYPE
    assert payload["status"] == "completed"
    assert payload["source"] == "existing_job_intelligence"
    assert payload["reason"] == "existing_intelligence_reused"
    assert payload["used_existing_intelligence"] is True
    assert payload["existing_intelligence_reused"] is True
    assert payload["duplicate_call_avoided"] is True
    assert payload["provider_call_performed"] is False
    assert payload["live_llm_call_performed"] is False
    assert payload["required_skills"] == ["Python", "SQL"]
    assert payload["preferred_skills"] == ["Airflow"]
    assert payload["all_skills"] == ["Python", "SQL", "Airflow"]
    _assert_no_production_mutation(payload)


def test_gate_off_missing_intelligence_returns_deterministic_fallback_without_call():
    job = _job_without_intelligence()

    def fail_if_called(_packet):
        raise AssertionError("gate-off helper should not be called")

    payload = build_jd_intelligence_controlled_llm_artifact(
        job,
        enabled=False,
        extraction_helper=fail_if_called,
    )

    assert payload["status"] == "fallback"
    assert payload["source"] == "deterministic_fallback"
    assert payload["reason"] == "llm_gate_disabled"
    assert payload["gated_off"] is True
    assert payload["fallback_used"] is True
    assert payload["provider_call_performed"] is False
    assert payload["safety_metadata"]["deterministic_fallback_used"] is True
    _assert_no_production_mutation(payload)


def test_gate_on_missing_intelligence_calls_injected_helper_once_and_preserves_metadata():
    calls = []

    def fake_extraction(packet):
        calls.append(deepcopy(packet))
        return {
            "jd_signals": {
                "required_skills": ["dbt", "SQL"],
                "preferred_skills": ["Looker"],
                "responsibilities": ["Own metrics layer"],
                "tools": ["BigQuery"],
            },
            "extraction_ready": True,
            "extraction_source": "existing_skill_signal_helper",
            "provider": "groq",
            "model": "llama-test",
            "prompt_version": "jd-skill-signals-v1",
            "cache_hit": True,
            "cache_key": "skill-cache-key",
            "retry_count": 1,
            "schema_validation_passed": True,
            "parse_retry_performed": True,
            "input_tokens": 100,
            "output_tokens": 30,
            "total_tokens": 130,
            "estimated_cost": 0.004,
            "latency_ms": 250,
            "fallback_provider_used": False,
        }

    payload = build_jd_intelligence_controlled_llm_artifact(
        _job_without_intelligence(),
        enabled=True,
        extraction_helper=fake_extraction,
    )

    assert len(calls) == 1
    assert calls[0]["gate_name"] == CONTROLLED_LLM_GATE_NAME
    assert calls[0]["default_off"] is True
    assert calls[0]["read_only"] is True
    assert payload["status"] == "completed"
    assert payload["source"] == "controlled_extraction_helper"
    assert payload["reason"] == "controlled_llm_extraction_performed"
    assert payload["provider_call_performed"] is True
    assert payload["live_llm_call_performed"] is True
    assert payload["required_skills"] == ["dbt", "SQL"]
    assert payload["preferred_skills"] == ["Looker"]
    assert payload["responsibilities"] == ["Own metrics layer"]
    assert payload["tools"] == ["BigQuery"]
    metadata = payload["metadata"]
    assert metadata["provider"] == "groq"
    assert metadata["model"] == "llama-test"
    assert metadata["prompt_version"] == "jd-skill-signals-v1"
    assert metadata["cache_hit"] is True
    assert metadata["cache_key"] == "skill-cache-key"
    assert metadata["retry_count"] == 1
    assert metadata["schema_validation_passed"] is True
    assert metadata["parse_retry_performed"] is True
    assert metadata["token_usage"] == {
        "input_tokens": 100,
        "output_tokens": 30,
        "total_tokens": 130,
    }
    assert metadata["cost"] == {"estimated_cost": 0.004}
    assert metadata["latency_ms"] == 250
    assert payload["safety_metadata"]["token_metrics_available"] is True
    assert payload["safety_metadata"]["cost_metrics_available"] is True
    assert payload["safety_metadata"]["latency_metrics_available"] is True
    _assert_no_production_mutation(payload)


def test_partial_existing_intelligence_is_sufficient_and_prevents_duplicate_call():
    job = _job_without_intelligence()
    existing_intelligence = {"skills": {"required": ["Python"]}}

    def fail_if_called(_packet):
        raise AssertionError("partial existing intelligence should be sufficient")

    payload = build_jd_intelligence_controlled_llm_artifact(
        job,
        existing_intelligence=existing_intelligence,
        enabled=True,
        extraction_helper=fail_if_called,
    )

    assert payload["status"] == "completed"
    assert payload["source"] == "existing_job_intelligence"
    assert payload["required_skills"] == ["Python"]
    assert payload["preferred_skills"] == []
    assert payload["duplicate_call_avoided"] is True
    assert payload["provider_call_performed"] is False


def test_incomplete_intelligence_with_gate_on_invokes_helper_without_mutating_job():
    job = _job_without_intelligence()
    job["intelligence"] = {"skills": {"required": {"bad": "shape"}}}
    original = deepcopy(job)
    calls = []

    def fake_extraction(packet):
        calls.append(packet)
        return {
            "required_skills": ["Python"],
            "preferred_skills": [],
            "extraction_ready": True,
        }

    payload = build_jd_intelligence_controlled_llm_artifact(
        job,
        enabled=True,
        extraction_helper=fake_extraction,
    )

    assert job == original
    assert len(calls) == 1
    assert payload["status"] == "completed"
    assert payload["required_skills"] == ["Python"]
    assert payload["provider_call_performed"] is True


def test_helper_failure_strict_false_returns_fallback_after_attempt():
    def failing_helper(_packet):
        raise RuntimeError("provider unavailable")

    payload = build_jd_intelligence_controlled_llm_artifact(
        _job_without_intelligence(),
        enabled=True,
        extraction_helper=failing_helper,
        strict=False,
    )

    assert payload["status"] == "fallback"
    assert payload["reason"] == "jd_intelligence_llm_extraction_failed"
    assert payload["provider_call_performed"] is True
    assert payload["fallback_used"] is True
    assert payload["error_message"] == "provider unavailable"
    _assert_no_production_mutation(payload)


def test_helper_failure_strict_true_reraises_only_after_attempt():
    calls = []

    def failing_helper(_packet):
        calls.append(True)
        raise RuntimeError("bad response")

    with pytest.raises(RuntimeError, match="bad response"):
        build_jd_intelligence_controlled_llm_artifact(
            _job_without_intelligence(),
            enabled=True,
            extraction_helper=failing_helper,
            strict=True,
        )

    assert calls == [True]


def test_missing_metadata_does_not_crash_and_uses_safe_defaults():
    payload = build_jd_intelligence_controlled_llm_artifact(
        _job_without_intelligence(),
        enabled=True,
        extraction_helper=lambda _packet: {
            "required_skills": ["Python"],
            "extraction_ready": True,
        },
    )

    assert payload["status"] == "completed"
    assert payload["metadata"]["provider"] == ""
    assert payload["metadata"]["model"] == ""
    assert payload["metadata"]["prompt_version"] == ""
    assert payload["metadata"]["cache_hit"] is False
    assert payload["metadata"]["token_usage"] == {}
    assert payload["metadata"]["cost"] == {}
    assert payload["safety_metadata"]["token_metrics_available"] is False
    assert payload["safety_metadata"]["cost_metrics_available"] is False
    assert payload["safety_metadata"]["latency_metrics_available"] is False


def test_source_safety_has_no_raw_provider_or_runtime_mutation_imports():
    source = HELPER_PATH.read_text(encoding="utf-8")
    forbidden_tokens = [
        "from src.ai.llm_client import",
        "run_chat_completion(",
        "run_chat_completion_with_metadata(",
        "from src.pipeline.collector import",
        "from src.app.services import",
        "from src.app.api import",
        "from groq import Groq",
        "from openai import OpenAI",
        "from google import genai",
        "from src.apply",
        "from src.ats",
        "from src.recruiter",
    ]
    for token in forbidden_tokens:
        assert token not in source
    assert_no_forbidden_runtime_calls_ast(
        [HELPER_PATH],
        forbidden_calls=(
            "run_chat_completion",
            "run_chat_completion_with_metadata",
            "submit_application",
            "mark_applied",
            "score_jobs",
            "rank_jobs",
        ),
        forbidden_imports=(
            "src.ai.llm_client",
            "src.pipeline.collector",
            "src.app.api",
            "src.app.services",
            "src.scoring",
            "src.ranking",
            "src.scheduler",
        ),
    )
