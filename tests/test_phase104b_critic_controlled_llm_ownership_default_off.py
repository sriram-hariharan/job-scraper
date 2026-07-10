from copy import deepcopy
from pathlib import Path
import subprocess

import pytest

from src.agents.critic_agent import (
    CRITIC_CONTROLLED_LLM_GUARDRAIL_ARTIFACT_TYPE,
    build_critic_controlled_llm_guardrail_artifact,
)
from tests.support.phase_guard_registry import assert_no_forbidden_runtime_calls_ast


# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405 d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961 fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0 c0c7a0a229a0cc9a1042c84c37a1728a33707e1035f6d604b6fe6aa74cc4b5e7
ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src/agents/critic_agent.py"


def _critic_input() -> dict:
    return {
        "tailoring_suggestion_payload": {
            "patch_ready_suggestions": [
                {"suggestion_id": "s1", "proposed_text": "Built Python APIs."}
            ]
        },
        "jd_intelligence": {"required_skills": ["Python"]},
        "resume_evidence_rows": [{"text": "Built Python APIs."}],
        "context_id": "ctx-104b",
        "job_id": "job-104b",
    }


def _adapter_result(**overrides) -> dict:
    payload = {
        "critic_status": "approved",
        "decision": "approve",
        "verdict": "safe",
        "risk_level": "low",
        "approved_suggestions": [{"suggestion_id": "s1"}],
        "downgraded_suggestions": [],
        "rejected_suggestions": [],
        "concerns": [],
        "unsupported_claims": [],
        "validation_errors": [],
        "review_notes": "Evidence-backed.",
        "recommendations": ["Proceed with manual review."],
        "normalized_response": {"critic_status": "approved"},
        "provider": "groq",
        "model": "llama-test",
        "prompt_version": "critic-guardrail-shadow-v1",
        "token_usage": {
            "input_tokens": 30,
            "output_tokens": 12,
            "total_tokens": 42,
        },
        "estimated_cost": 0.01,
        "latency_ms": 88,
        "fallback_provider_used": False,
        "schema_validation_passed": True,
        "schema_validation_errors": [],
        "retry_count": 1,
        "cache_hit": True,
        "cache_key": "critic-cache-key",
        "error_message": "",
    }
    payload.update(overrides)
    return payload


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
    assert payload["guardrail_decision_only"] is True


def test_existing_guardrail_result_is_reused_and_avoids_duplicate_llm_call():
    existing = _adapter_result(source="manual_critic_guardrail_dry_run")

    def fail_if_called(_packet):
        raise AssertionError("adapter should not be called")

    payload = build_critic_controlled_llm_guardrail_artifact(
        _critic_input(),
        existing_guardrail_result=existing,
        enabled=True,
        guardrail_adapter=fail_if_called,
    )

    assert payload["artifact_type"] == CRITIC_CONTROLLED_LLM_GUARDRAIL_ARTIFACT_TYPE
    assert payload["status"] == "completed"
    assert payload["source"] == "existing_critic_guardrail_result"
    assert payload["reason"] == "existing_guardrail_result_reused"
    assert payload["existing_guardrail_result_reused"] is True
    assert payload["duplicate_llm_call_avoided"] is True
    assert payload["provider_call_performed"] is False
    assert payload["live_llm_call_performed"] is False
    assert payload["metadata"]["provider"] == "groq"
    _assert_no_production_mutation(payload)


def test_gate_off_does_not_call_adapter_and_returns_fallback():
    def fail_if_called(_packet):
        raise AssertionError("gate-off adapter should not be called")

    payload = build_critic_controlled_llm_guardrail_artifact(
        _critic_input(),
        enabled=False,
        guardrail_adapter=fail_if_called,
    )

    assert payload["status"] == "fallback"
    assert payload["reason"] == "critic_llm_gate_disabled"
    assert payload["gated_off"] is True
    assert payload["fallback_used"] is True
    assert payload["provider_call_performed"] is False
    assert payload["live_llm_call_performed"] is False
    _assert_no_production_mutation(payload)


def test_gate_on_calls_adapter_exactly_once_and_preserves_response():
    calls = []

    def fake_adapter(packet):
        calls.append(deepcopy(packet))
        return _adapter_result()

    payload = build_critic_controlled_llm_guardrail_artifact(
        _critic_input(),
        enabled=True,
        guardrail_adapter=fake_adapter,
    )

    assert len(calls) == 1
    assert calls[0]["job_id"] == "job-104b"
    assert payload["status"] == "completed"
    assert payload["source"] == "controlled_guardrail_adapter"
    assert payload["reason"] == "controlled_critic_guardrail_llm_performed"
    assert payload["provider_call_performed"] is True
    assert payload["live_llm_call_performed"] is True
    assert payload["normalized_guardrail_response"]["decision"] == "approve"
    assert payload["normalized_guardrail_response"]["verdict"] == "safe"
    assert payload["normalized_guardrail_response"]["risk_level"] == "low"
    assert payload["normalized_guardrail_response"]["approved_suggestions"] == [
        {"suggestion_id": "s1"}
    ]
    _assert_no_production_mutation(payload)


def test_adapter_metadata_normalization_preserves_known_fields_and_missing_is_safe():
    full = build_critic_controlled_llm_guardrail_artifact(
        _critic_input(),
        enabled=True,
        guardrail_adapter=lambda _packet: _adapter_result(
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
            cost={"estimated_cost": 0.02, "cost_currency": "USD"},
            schema_validation_errors=["minor_warning"],
        ),
    )

    metadata = full["metadata"]
    assert metadata["provider"] == "groq"
    assert metadata["model"] == "llama-test"
    assert metadata["prompt_version"] == "critic-guardrail-shadow-v1"
    assert metadata["input_tokens"] == 10
    assert metadata["output_tokens"] == 5
    assert metadata["total_tokens"] == 15
    assert metadata["estimated_cost"] == 0.01
    assert metadata["cost"] == {"estimated_cost": 0.02, "cost_currency": "USD"}
    assert metadata["latency_ms"] == 88
    assert metadata["schema_validation_passed"] is True
    assert metadata["schema_validation_errors"] == ["minor_warning"]
    assert metadata["retry_count"] == 1
    assert metadata["cache_hit"] is True
    assert metadata["cache_key"] == "critic-cache-key"
    assert full["safety_metadata"]["token_metrics_available"] is True
    assert full["safety_metadata"]["cost_metrics_available"] is True
    assert full["safety_metadata"]["latency_metrics_available"] is True

    minimal = build_critic_controlled_llm_guardrail_artifact(
        _critic_input(),
        enabled=True,
        guardrail_adapter=lambda _packet: {"critic_status": "needs_guidance"},
    )

    assert minimal["metadata"]["provider"] == ""
    assert minimal["metadata"]["input_tokens"] is None
    assert minimal["metadata"]["estimated_cost"] is None
    assert minimal["metadata"]["latency_ms"] is None
    assert minimal["safety_metadata"]["token_metrics_available"] is False
    assert minimal["safety_metadata"]["cost_metrics_available"] is False
    assert minimal["safety_metadata"]["latency_metrics_available"] is False
    _assert_no_production_mutation(minimal)


def test_adapter_failure_strict_false_returns_fallback_artifact():
    def failing_adapter(_packet):
        raise RuntimeError("provider unavailable")

    payload = build_critic_controlled_llm_guardrail_artifact(
        _critic_input(),
        enabled=True,
        guardrail_adapter=failing_adapter,
        strict=False,
    )

    assert payload["status"] == "fallback"
    assert payload["reason"] == "critic_llm_guardrail_failed"
    assert payload["fallback_used"] is True
    assert payload["provider_call_performed"] is True
    assert payload["live_llm_call_performed"] is True
    assert "RuntimeError" in payload["error_message"]
    _assert_no_production_mutation(payload)


def test_adapter_failure_strict_true_reraises_after_adapter_attempt():
    calls = []

    def failing_adapter(packet):
        calls.append(deepcopy(packet))
        raise RuntimeError("strict failure")

    with pytest.raises(RuntimeError, match="strict failure"):
        build_critic_controlled_llm_guardrail_artifact(
            _critic_input(),
            enabled=True,
            guardrail_adapter=failing_adapter,
            strict=True,
        )

    assert len(calls) == 1


def test_inputs_are_not_mutated():
    critic_input = _critic_input()
    existing = _adapter_result()
    original_input = deepcopy(critic_input)
    original_existing = deepcopy(existing)

    build_critic_controlled_llm_guardrail_artifact(
        critic_input,
        existing_guardrail_result=existing,
        enabled=True,
        guardrail_adapter=lambda _packet: _adapter_result(),
    )

    assert critic_input == original_input
    assert existing == original_existing


def test_source_has_no_job_fit_evaluator_or_raw_provider_calls():
    assert_no_forbidden_runtime_calls_ast(
        [HELPER_PATH],
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


def test_phase104b_does_not_wire_collector_api_or_static_runtime():
    for relative_path in (
        "src/pipeline/collector.py",
        "src/app/api.py",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "build_critic_controlled_llm_guardrail_artifact" not in text

    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    changed.update(
        subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    unexpected_static = {
        path
        for path in changed
        if path.startswith("src/app/static/")
        and path != "src/app/static/agentic_review.js"
        and path != "src/app/static/app.js"
        and path != "src/app/static/planning.js"
    }
    assert not unexpected_static


def test_safety_flags_remain_false_for_apply_ats_mutation_and_review_queue():
    payload = build_critic_controlled_llm_guardrail_artifact(
        _critic_input(),
        enabled=True,
        guardrail_adapter=lambda _packet: _adapter_result(),
    )

    _assert_no_production_mutation(payload)
    assert payload["safety_metadata"]["review_queue_mutation_performed"] is False
    assert payload["safety_metadata"]["source_resume_mutation_performed"] is False
    assert payload["safety_metadata"]["generated_resume_mutation_performed"] is False
