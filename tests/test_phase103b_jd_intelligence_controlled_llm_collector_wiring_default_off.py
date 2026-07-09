from copy import deepcopy
from pathlib import Path
import ast

from src.pipeline import collector
from tests.support.phase_guard_registry import assert_no_forbidden_runtime_calls_ast


# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405 d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961 fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0 c0c7a0a229a0cc9a1042c84c37a1728a33707e1035f6d604b6fe6aa74cc4b5e7
ROOT = Path(__file__).resolve().parents[1]
GATE = "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_CONTROLLED_LLM_ENABLED"


def _missing_job(job_id: str = "job-103b-missing") -> dict:
    return {
        "job_id": job_id,
        "title": "Analytics Engineer",
        "company": "Example Data",
        "description_text": "Build Python and SQL analytics systems.",
    }


def _intelligent_job(job_id: str = "job-103b-existing") -> dict:
    return {
        "job_id": job_id,
        "title": "Data Platform Engineer",
        "company": "Example Systems",
        "description_text": "Own Python data platforms.",
        "intelligence": {
            "skills": {
                "required": ["Python", "SQL"],
                "preferred": ["Airflow"],
                "all": ["Python", "SQL", "Airflow"],
            },
            "visa_sponsorship": "unknown",
        },
    }


def _fake_builder(job: dict) -> dict:
    output = deepcopy(job)
    output["intelligence"] = {
        "skills": {
            "required": ["Python"],
            "preferred": ["SQL"],
            "all": ["Python", "SQL"],
        },
        "visa_sponsorship": "unknown",
    }
    output["role_family"] = "data_engineering"
    return output


def _call_helper(jobs, *, enabled, build_func, artifact_builder=None, strict=True):
    return collector._build_intelligent_jobs_with_controlled_jd_agent_ownership(
        deepcopy(jobs),
        build_job_intelligence_func=build_func,
        artifact_builder=artifact_builder,
        enabled=enabled,
        env={GATE: "1" if enabled else ""},
        strict=strict,
    )


def _collector_source() -> str:
    return (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")


def _helper_source() -> str:
    source = _collector_source()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "_build_intelligent_jobs_with_controlled_jd_agent_ownership"
        ):
            return ast.get_source_segment(source, node) or ""
    raise AssertionError("Phase 103B collector helper missing")


def test_gate_off_preserves_legacy_path_and_does_not_call_phase102_helper():
    jobs = [_missing_job("legacy-1"), _missing_job("legacy-2")]
    calls = []

    def build(job):
        calls.append(job["job_id"])
        return {**job, "legacy_built": True}

    def fail_artifact_builder(*_args, **_kwargs):
        raise AssertionError("Phase 102 helper must not run when gate is off")

    result = _call_helper(
        jobs,
        enabled=False,
        build_func=build,
        artifact_builder=fail_artifact_builder,
    )

    assert calls == ["legacy-1", "legacy-2"]
    assert result["enabled"] is False
    assert result["jd_intelligence_controlled_llm_runtime_summary"] is None
    assert [job["legacy_built"] for job in result["intelligent_jobs"]] == [True, True]


def test_gate_on_missing_intelligence_uses_agent_owned_adapter_once():
    calls = []
    jobs = [_missing_job("owned-1")]

    def build(job):
        calls.append(job["job_id"])
        return _fake_builder(job)

    result = _call_helper(jobs, enabled=True, build_func=build)
    summary = result["jd_intelligence_controlled_llm_runtime_summary"]

    assert calls == ["owned-1"]
    assert result["intelligent_jobs"][0]["intelligence"]["skills"]["required"] == [
        "Python"
    ]
    assert result["intelligent_jobs"][0]["role_family"] == "data_engineering"
    assert summary["enabled"] is True
    assert summary["artifacts_built"] == 1
    assert summary["extraction_helper_called_count"] == 1
    assert summary["provider_call_performed_count"] == 1
    assert summary["duplicate_call_avoided_count"] == 0


def test_gate_on_existing_intelligence_reuses_and_avoids_duplicate_call():
    job = _intelligent_job()

    def fail_build(_job):
        raise AssertionError("existing intelligence should avoid build call")

    result = _call_helper([job], enabled=True, build_func=fail_build)
    artifact = result["jd_intelligence_controlled_llm_runtime_summary"]["artifacts"][0]

    assert result["intelligent_jobs"][0] == job
    assert artifact["existing_intelligence_reused"] is True
    assert artifact["duplicate_call_avoided"] is True
    assert artifact["provider_call_performed"] is False
    assert result["jd_intelligence_controlled_llm_runtime_summary"][
        "extraction_helper_called_count"
    ] == 0


def test_gate_on_mixed_jobs_calls_existing_build_only_for_missing_jobs():
    jobs = [_intelligent_job("existing"), _missing_job("missing")]
    calls = []

    def build(job):
        calls.append(job["job_id"])
        return _fake_builder(job)

    result = _call_helper(jobs, enabled=True, build_func=build)
    summary = result["jd_intelligence_controlled_llm_runtime_summary"]

    assert calls == ["missing"]
    assert len(summary["artifacts"]) == 2
    assert summary["existing_intelligence_reused_count"] == 1
    assert summary["duplicate_call_avoided_count"] == 1
    assert summary["extraction_helper_called_count"] == 1
    assert [job["job_id"] for job in result["intelligent_jobs"]] == [
        "existing",
        "missing",
    ]


def test_no_duplicate_jd_extraction_count_equals_missing_or_incomplete_jobs_only():
    jobs = [
        _intelligent_job("existing-1"),
        _missing_job("missing-1"),
        _intelligent_job("existing-2"),
        _missing_job("missing-2"),
    ]
    calls = []

    def build(job):
        calls.append(job["job_id"])
        return _fake_builder(job)

    result = _call_helper(jobs, enabled=True, build_func=build)

    assert calls == ["missing-1", "missing-2"]
    assert result["jd_intelligence_controlled_llm_runtime_summary"][
        "extraction_helper_called_count"
    ] == 2


def test_metadata_preservation_where_available_and_safe_defaults_when_absent():
    def build_with_metadata(job):
        output = _fake_builder(job)
        output["_jd_intelligence_llm_metadata"] = {
            "provider": "groq",
            "model": "llama-test",
            "prompt_version": "skill-extraction-v1",
            "cache_hit": True,
            "cache_key": "cache-key",
            "retry_count": 1,
            "schema_validation_passed": True,
            "parse_retry_performed": True,
            "token_usage": {
                "input_tokens": 10,
                "output_tokens": 4,
                "total_tokens": 14,
            },
            "cost": {"estimated_cost": 0.002},
            "latency_ms": 12,
            "fallback_provider_used": False,
        }
        return output

    with_metadata = _call_helper(
        [_missing_job("with-metadata")],
        enabled=True,
        build_func=build_with_metadata,
    )
    without_metadata = _call_helper(
        [_missing_job("without-metadata")],
        enabled=True,
        build_func=_fake_builder,
    )

    artifact = with_metadata["jd_intelligence_controlled_llm_runtime_summary"][
        "artifacts"
    ][0]
    assert artifact["metadata"]["provider"] == "groq"
    assert artifact["metadata"]["model"] == "llama-test"
    assert artifact["metadata"]["cache_hit"] is True
    assert artifact["metadata"]["token_usage"]["total_tokens"] == 14
    assert artifact["metadata"]["cost"]["estimated_cost"] == 0.002
    assert artifact["metadata"]["latency_ms"] == 12
    assert with_metadata["jd_intelligence_controlled_llm_runtime_summary"][
        "token_metrics_available_count"
    ] == 1
    safe_artifact = without_metadata["jd_intelligence_controlled_llm_runtime_summary"][
        "artifacts"
    ][0]
    assert safe_artifact["metadata"]["provider"] == ""
    assert safe_artifact["metadata"]["token_usage"] == {}
    assert without_metadata["jd_intelligence_controlled_llm_runtime_summary"][
        "token_metrics_available_count"
    ] == 0


def test_strict_false_returns_safe_fallback_without_production_mutation():
    def failing_build(_job):
        raise RuntimeError("jd extraction failed")

    result = _call_helper(
        [_missing_job("failure")],
        enabled=True,
        build_func=failing_build,
        strict=False,
    )
    summary = result["jd_intelligence_controlled_llm_runtime_summary"]
    artifact = summary["artifacts"][0]

    assert result["intelligent_jobs"][0]["job_id"] == "failure"
    assert artifact["reason"] == "jd_intelligence_llm_extraction_failed"
    assert artifact["fallback_used"] is True
    assert summary["error_count"] == 1
    for key in collector.JD_INTELLIGENCE_CONTROLLED_LLM_FALSE_FLAGS:
        assert summary[key] is False
        assert summary["safety_metadata"][key] is False


def test_source_and_ast_safety_for_collector_and_jd_agent():
    collector_source = _collector_source()
    helper_source = _helper_source()
    jd_path = ROOT / "src/agents/jd_intelligence.py"
    for source in (collector_source, jd_path.read_text(encoding="utf-8")):
        for token in (
            "from groq import Groq",
            "from openai import OpenAI",
            "from google import genai",
            "run_chat_completion(",
            "run_chat_completion_with_metadata(",
            "from src.app.api import",
            "from src.app.services import",
            "from src.apply",
            "from src.ats",
            "from src.recruiter",
        ):
            assert token not in source
    assert "score_jobs(" not in helper_source
    assert "rank_jobs(" not in helper_source
    assert "filter_jobs(" not in helper_source
    assert_no_forbidden_runtime_calls_ast(
        [ROOT / "src/pipeline/collector.py", jd_path],
        forbidden_calls=(
            "run_chat_completion",
            "run_chat_completion_with_metadata",
            "submit_application",
            "mark_applied",
        ),
        forbidden_imports=(
            "groq",
            "openai",
            "google.genai",
            "src.app.api",
            "src.app.services",
            "src.apply",
            "src.ats",
            "src.recruiter",
        ),
    )
