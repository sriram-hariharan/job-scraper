from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
import subprocess

from src.app import services
from tests.support.phase_guard_registry import (
    assert_no_forbidden_runtime_calls_ast,
    get_changed_files,
    legacy_guard_allowlist,
)


# phase105b legacy guard marker: changes_only services_hash bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 api_hash d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
ROOT = Path(__file__).resolve().parents[1]
SERVICES_PATH = ROOT / "src/app/services.py"
CRITIC_PATH = ROOT / "src/agents/critic_agent.py"


def _jd() -> dict:
    return {
        "required_skills": ["Python", "SQL"],
        "required_tools": ["Airflow"],
        "workflows": ["production data pipelines"],
    }


def _resume() -> dict:
    return {
        "resume_id": "resume-a",
        "bullets": ["Built Python and SQL pipelines with Airflow."],
        "skills": ["Python", "SQL"],
        "tools": ["Airflow"],
    }


def _tailoring_payload() -> dict:
    evidence = "Built Python and SQL pipelines with Airflow."
    return {
        "patch_ready_suggestions": [
            {
                "suggestion_id": "tailoring-001",
                "source_bullet_id": "bullet-1",
                "original_text": evidence,
                "suggested_text": evidence,
                "reason": "Existing resume evidence directly supports JD signal: Python.",
                "evidence_spans": [evidence],
                "jd_signal_links": [{"field": "required_skills", "signal": "Python"}],
                "patch_ready": True,
                "projected_score_delta": 0.03,
                "risk_flags": [],
            }
        ],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
        "missing_evidence": [],
    }


def _request_payload() -> dict:
    return {
        "tailoring_suggestion_payload": _tailoring_payload(),
        "jd_intelligence": _jd(),
        "resume_evidence_rows": [_resume()],
        "context_id": "ctx-105b",
        "job_id": "job-105b",
    }


def _provider_payload(**overrides) -> dict:
    payload = {
        "critic_status": "approved",
        "approved_suggestions": [
            {
                "suggestion_id": "tailoring-001",
                "decision": "approve",
                "confidence": 0.92,
                "reason_codes": [],
                "evidence_spans": ["Built Python and SQL pipelines with Airflow."],
                "notes": "Evidence-backed.",
                "original_patch_ready": True,
                "final_patch_ready": True,
            }
        ],
        "downgraded_suggestions": [],
        "rejected_suggestions": [],
        "reason_codes": [],
        "unsupported_claim_risks": [],
        "ats_risks": [],
        "readability_risks": [],
        "evidence_gaps": [],
        "confidence": 0.92,
        "rationale": "Provider approved evidence-backed suggestions.",
        "model_provider": "fake-provider",
        "model_name": "fake-model",
        "prompt_version": "critic-prompt-v105b",
        "token_usage": {
            "input_tokens": 30,
            "output_tokens": 12,
            "total_tokens": 42,
        },
        "cost": {"estimated_cost": 0.01, "cost_currency": "USD"},
        "estimated_cost": 0.01,
        "latency_ms": 88,
        "provider_fallback_used": False,
        "schema_validation_passed": True,
        "schema_validation_errors": [],
        "retry_count": 1,
        "cache_hit": True,
        "cache_key": "critic-cache-105b",
        "error_message": "",
    }
    payload.update(overrides)
    return payload


def _artifact(payload: dict | None = None, **overrides) -> dict:
    artifact = {
        "artifact_type": "critic_controlled_llm_guardrail_artifact",
        "status": "completed",
        "reason": "controlled_critic_guardrail_llm_performed",
        "source": "controlled_guardrail_adapter",
        "enabled": True,
        "gated_off": False,
        "fallback_used": False,
        "provider_call_performed": True,
        "live_llm_call_performed": True,
        "existing_guardrail_result_reused": False,
        "duplicate_llm_call_avoided": False,
        "guardrail_result": payload if payload is not None else _provider_payload(),
        "metadata": {},
        "error_message": "",
        "safety_metadata": _false_safety(),
        **_false_safety(),
    }
    artifact.update(overrides)
    return artifact


def _false_safety() -> dict:
    return {
        "database_write_performed": False,
        "trace_persistence_performed": False,
        "collector_output_changed": False,
        "production_output_changed": False,
        "scoring_changed": False,
        "ranking_changed": False,
        "filtering_changed": False,
        "queue_mutation_performed": False,
        "review_queue_mutation_performed": False,
        "scheduler_mutation_performed": False,
        "tailoring_mutation_performed": False,
        "source_resume_mutation_performed": False,
        "generated_resume_mutation_performed": False,
        "application_status_changed": False,
        "auto_apply_performed": False,
        "ats_submission_performed": False,
        "apply_click_performed": False,
        "recruiter_message_sent": False,
        "mark_applied_performed": False,
        "external_action_automation_performed": False,
    }


def _assert_artifact_safety(artifact: dict) -> None:
    for key, expected in _false_safety().items():
        assert artifact[key] is expected
        assert artifact["safety_metadata"][key] is expected


def _function_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"{name} missing from {path}")


def test_gate_off_preserves_existing_manual_behavior_and_does_not_call_adapter():
    calls = []

    def fail_if_called(_payload):
        calls.append(_payload)
        raise AssertionError("gate-off adapter must not be called")

    payload = services.build_manual_critic_guardrail_dry_run_payload(
        **_request_payload(),
        adapter=fail_if_called,
        feature_enabled=False,
    )

    assert calls == []
    assert payload["service_surface"] == "manual_critic_guardrail_dry_run"
    assert payload["critic_status"] == "approved"
    assert payload["validation_status"] == "disabled"
    assert payload["fallback_used"] is True
    assert payload["safety_metadata"]["did_call_llm"] is False
    artifact = payload["critic_controlled_llm_guardrail_artifact"]
    assert artifact["gated_off"] is True
    assert artifact["reason"] == "critic_llm_gate_disabled"
    assert artifact["provider_call_performed"] is False
    _assert_artifact_safety(artifact)


def test_gate_on_routes_through_critic_helper_and_injects_service_provider(monkeypatch):
    calls = []

    def fake_live_adapter(_payload):
        raise AssertionError("service must not call the live adapter outside helper")

    def fake_helper(critic_input, **kwargs):
        calls.append({"critic_input": deepcopy(critic_input), **kwargs})
        assert kwargs["enabled"] is True
        assert kwargs["guardrail_adapter"] is fake_live_adapter
        return _artifact()

    monkeypatch.setattr(services, "_live_critic_guardrail_provider_adapter", fake_live_adapter)
    monkeypatch.setattr(
        services.critic_agent,
        "build_critic_controlled_llm_guardrail_artifact",
        fake_helper,
    )

    payload = services.build_manual_critic_guardrail_dry_run_payload(
        **_request_payload(),
        feature_enabled=True,
    )

    assert len(calls) == 1
    assert calls[0]["critic_input"]["job_id"] == "job-105b"
    assert payload["critic_controlled_llm_guardrail_artifact"]["source"] == (
        "controlled_guardrail_adapter"
    )
    assert payload["validation_status"] == "valid"


def test_gate_on_calls_injected_adapter_exactly_once_through_real_helper():
    calls = []

    def fake_adapter(packet):
        calls.append(deepcopy(packet))
        return _provider_payload()

    payload = services.build_manual_critic_guardrail_dry_run_payload(
        **_request_payload(),
        adapter=fake_adapter,
        feature_enabled=True,
    )

    assert len(calls) == 1
    assert calls[0]["job_id"] == "job-105b"
    artifact = payload["critic_controlled_llm_guardrail_artifact"]
    assert artifact["provider_call_performed"] is True
    assert artifact["live_llm_call_performed"] is True
    assert payload["validation_status"] == "valid"
    assert payload["fallback_used"] is False
    _assert_artifact_safety(artifact)


def test_no_pre_helper_direct_adapter_call_is_present():
    snippet = _function_source(SERVICES_PATH, "build_manual_critic_guardrail_dry_run_payload")

    assert "provider_payload = effective_adapter(" not in snippet
    assert "build_critic_controlled_llm_guardrail_artifact" in snippet
    assert "guardrail_adapter=effective_adapter" in snippet


def test_metadata_is_preserved_without_inventing_missing_values():
    payload = services.build_manual_critic_guardrail_dry_run_payload(
        **_request_payload(),
        adapter=lambda _packet: _provider_payload(),
        feature_enabled=True,
    )
    artifact = payload["critic_controlled_llm_guardrail_artifact"]

    assert payload["model_provider"] == "fake-provider"
    assert payload["model_name"] == "fake-model"
    assert payload["prompt_version"] == "critic-prompt-v105b"
    assert payload["token_usage"] == {
        "input_tokens": 30,
        "output_tokens": 12,
        "total_tokens": 42,
    }
    assert payload["cost"] == {"estimated_cost": 0.01, "cost_currency": "USD"}
    assert payload["latency_ms"] == 88
    assert artifact["metadata"]["provider"] == "fake-provider"
    assert artifact["metadata"]["model"] == "fake-model"
    assert artifact["metadata"]["input_tokens"] == 30
    assert artifact["metadata"]["output_tokens"] == 12
    assert artifact["metadata"]["total_tokens"] == 42
    assert artifact["metadata"]["estimated_cost"] == 0.01
    assert artifact["metadata"]["latency_ms"] == 88
    assert artifact["metadata"]["fallback_provider_used"] is False
    assert artifact["metadata"]["schema_validation_passed"] is True
    assert artifact["metadata"]["schema_validation_errors"] == []
    assert artifact["metadata"]["retry_count"] == 1
    assert artifact["metadata"]["cache_hit"] is True
    assert artifact["metadata"]["cache_key"] == "critic-cache-105b"

    minimal = services.build_manual_critic_guardrail_dry_run_payload(
        **_request_payload(),
        adapter=lambda _packet: _provider_payload(
            model_provider="",
            model_name="",
            token_usage={},
            cost={},
            estimated_cost=None,
            latency_ms=None,
            retry_count=None,
            cache_hit=False,
            cache_key="",
        ),
        feature_enabled=True,
    )
    minimal_artifact = minimal["critic_controlled_llm_guardrail_artifact"]
    assert minimal_artifact["metadata"]["provider"] == ""
    assert minimal_artifact["metadata"]["input_tokens"] is None
    assert minimal_artifact["metadata"]["estimated_cost"] is None
    assert minimal_artifact["metadata"]["latency_ms"] is None


def test_adapter_failure_uses_existing_service_fallback_and_artifact_reason():
    def failing_adapter(_packet):
        raise RuntimeError("provider unavailable")

    payload = services.build_manual_critic_guardrail_dry_run_payload(
        **_request_payload(),
        adapter=failing_adapter,
        feature_enabled=True,
    )

    artifact = payload["critic_controlled_llm_guardrail_artifact"]
    assert payload["critic_status"] == "approved"
    assert payload["validation_status"] == "fallback"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["adapter_error:RuntimeError"]
    assert artifact["reason"] == "critic_llm_guardrail_failed"
    assert artifact["fallback_used"] is True
    assert "RuntimeError" in artifact["error_message"]
    _assert_artifact_safety(artifact)


def test_no_job_fit_duplication_or_raw_provider_calls_from_critic_agent():
    assert_no_forbidden_runtime_calls_ast(
        [CRITIC_PATH],
        forbidden_calls=(
            "run_chat_completion",
            "run_chat_completion_with_metadata",
            "score_jobs",
            "rank_jobs",
            "execute_application",
            "submit_application",
            "job_fit_evaluator",
        ),
        forbidden_imports=(
            "src.ai.job_fit_evaluator",
            "src.app.services",
            "openai",
            "groq",
            "google.generativeai",
            "google.genai",
        ),
    )


def test_service_manual_critic_slice_does_not_add_job_fit_or_raw_provider_calls():
    snippet = _function_source(SERVICES_PATH, "build_manual_critic_guardrail_dry_run_payload")
    forbidden = [
        "job_fit_evaluator",
        "score_resume_job_match",
        "run_chat_completion(",
        "run_chat_completion_with_metadata(",
        "openai",
        "groq",
        "google.generativeai",
        "submit_application(",
        "execute_application(",
        "mark_as_applied",
    ]
    for marker in forbidden:
        assert marker not in snippet


def test_no_collector_api_ui_or_static_changes_for_phase105b():
    changed = get_changed_files(ROOT)
    phase129_surface = (
        legacy_guard_allowlist("phase129b_auth_loader_ui")
        | legacy_guard_allowlist(
            "phase129c_workflow_overlay_and_run_scoped_corpus"
        )
    )

    phase108a_collector_surface = {
        "src/pipeline/collector.py",
        "tests/test_phase108a_collector_langgraph_evidence_chain_execution_default_off.py",
    }
    unexpected_collector_change = {
        path for path in changed if path == "src/pipeline/collector.py"
    } - phase108a_collector_surface
    assert not unexpected_collector_change
    if "src/pipeline/collector.py" in changed:
        assert phase108a_collector_surface <= changed
    unexpected_api_change = {
        path for path in changed if path == "src/app/api.py"
    } - phase129_surface
    assert not unexpected_api_change
    for relative_path in ("src/pipeline/collector.py", "src/app/api.py"):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "build_critic_controlled_llm_guardrail_artifact" not in text

    historical_static_surface = {
        "src/app/static/agentic_review.js",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.js",
        "src/app/static/scan_workspace_review.css",
        "src/app/static/styles.css",
    }
    unexpected_static = {
        path
        for path in changed
        if path.startswith("src/app/static/")
        and path not in historical_static_surface
        and path not in phase129_surface
    }
    assert not unexpected_static
    assert not any(path.startswith("src/app/templates/") for path in changed)
