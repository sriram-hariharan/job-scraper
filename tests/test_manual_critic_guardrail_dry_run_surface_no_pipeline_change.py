from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-critic-guardrail-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _jd() -> dict:
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": [],
        "required_tools": ["Airflow"],
        "preferred_tools": [],
        "workflows": ["production data pipelines"],
        "business_contexts": ["finance partners"],
    }


def _resume() -> dict:
    return {
        "resume_id": "resume-a",
        "bullets": [
            "Built Python and SQL production data pipelines with Airflow for finance partners."
        ],
        "skills": ["Python", "SQL"],
        "tools": ["Airflow"],
        "business_contexts": ["finance partners"],
    }


def _tailoring_payload() -> dict:
    evidence = "Built Python and SQL production data pipelines with Airflow for finance partners."
    return {
        "suggestion_status": "patch_ready_available",
        "selected_resume_id": "resume-a",
        "patch_ready_suggestions": [
            {
                "suggestion_id": "tailoring_dry_run_001",
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
        "unsupported_claim_risks": [],
        "projected_score_delta": 0.03,
    }


def _request_payload() -> dict:
    return {
        "tailoring_suggestion_payload": _tailoring_payload(),
        "jd_intelligence": _jd(),
        "resume_evidence_rows": [_resume()],
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _assert_readonly_safety(payload: dict, *, did_call_llm: bool = False) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
    assert safety["feature_flag_required"] is True
    assert safety["deterministic_only"] is True
    assert safety["did_call_llm"] is did_call_llm
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["advisory_only"] is True


def _valid_provider_payload() -> dict:
    evidence = "Built Python and SQL production data pipelines with Airflow for finance partners."
    return {
        "critic_status": "approved",
        "approved_suggestions": [
            {
                "suggestion_id": "tailoring_dry_run_001",
                "decision": "approve",
                "confidence": 0.91,
                "reason_codes": [],
                "evidence_spans": [evidence],
                "notes": "Evidence-backed suggestion.",
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
        "confidence": 0.91,
        "rationale": "Provider approved evidence-backed tailoring suggestions.",
        "model_provider": "fake-provider",
        "model_name": "fake-model",
        "prompt_version": "fake-prompt-v1",
        "token_usage": {"total_token_count": 42},
        "cost": {"estimated_cost": 0.01, "cost_currency": "USD"},
        "latency_ms": 88,
    }


def test_service_returns_manual_critic_guardrail_dry_run_payload():
    source = _request_payload()
    original = deepcopy(source)

    first = services.build_manual_critic_guardrail_dry_run_payload(**source)
    second = services.build_manual_critic_guardrail_dry_run_payload(**source)

    assert first == second
    assert source == original
    assert first["service_surface"] == "manual_critic_guardrail_dry_run"
    assert first["critic_status"] == "approved"
    assert first["validation_status"] == "disabled"
    assert first["fallback_used"] is True
    assert first["approved_suggestions"]
    _assert_readonly_safety(first)


def test_service_default_flag_off_does_not_call_critic_provider():
    calls = []

    def fake_adapter(payload):
        calls.append(payload)
        return _valid_provider_payload()

    payload = services.build_manual_critic_guardrail_dry_run_payload(
        **_request_payload(),
        adapter=fake_adapter,
    )

    assert calls == []
    assert payload["validation_status"] == "disabled"
    assert payload["fallback_used"] is True
    assert payload["env_feature_flag_enabled"] is False
    _assert_readonly_safety(payload, did_call_llm=False)


def test_service_enabled_fake_critic_provider_returns_validated_output():
    calls = []

    def fake_adapter(payload):
        calls.append(payload)
        return _valid_provider_payload()

    payload = services.build_manual_critic_guardrail_dry_run_payload(
        **_request_payload(),
        adapter=fake_adapter,
        feature_enabled=True,
    )

    assert calls
    assert payload["validation_status"] == "valid"
    assert payload["fallback_used"] is False
    assert payload["critic_status"] == "approved"
    assert payload["approved_suggestions"][0]["confidence"] == 0.91
    assert payload["model_provider"] == "fake-provider"
    assert payload["model_name"] == "fake-model"
    assert payload["prompt_version"] == "fake-prompt-v1"
    assert payload["token_usage"] == {"total_token_count": 42}
    assert payload["cost"] == {"estimated_cost": 0.01, "cost_currency": "USD"}
    assert payload["latency_ms"] == 88
    _assert_readonly_safety(payload, did_call_llm=True)


def test_service_enabled_critic_provider_invalid_json_falls_back_safely():
    payload = services.build_manual_critic_guardrail_dry_run_payload(
        **_request_payload(),
        adapter=lambda _payload: {"raw_response": "{bad json", "model_provider": "fake-provider"},
        feature_enabled=True,
    )

    assert payload["validation_status"] == "fallback"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["invalid_json_response"]
    assert payload["critic_status"] == "approved"
    _assert_readonly_safety(payload, did_call_llm=True)


def test_service_enabled_critic_provider_exception_falls_back_safely():
    def fake_adapter(_payload):
        raise RuntimeError("provider unavailable")

    payload = services.build_manual_critic_guardrail_dry_run_payload(
        **_request_payload(),
        adapter=fake_adapter,
        feature_enabled=True,
    )

    assert payload["validation_status"] == "fallback"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["adapter_error:RuntimeError"]
    assert payload["critic_status"] == "approved"
    _assert_readonly_safety(payload, did_call_llm=True)


def test_live_critic_provider_adapter_reuses_existing_llm_client_with_schema(monkeypatch):
    captured = {}

    def fake_run_chat_completion_with_metadata(**kwargs):
        captured.update(kwargs)
        return {
            "content": _valid_provider_payload(),
            "provider": "fake-provider",
            "model": "fake-model",
            "fallback_used": False,
            "token_usage": {"total_token_count": 55},
            "cost": {"estimated_cost": 0.03, "cost_currency": "USD"},
            "latency_ms": 99,
        }

    import src.ai.llm_client as llm_client

    monkeypatch.setattr(
        llm_client,
        "run_chat_completion_with_metadata",
        fake_run_chat_completion_with_metadata,
    )

    result = services._live_critic_guardrail_provider_adapter(_request_payload())

    assert captured["response_mime_type"] == "application/json"
    assert captured["response_schema"] == services.LIVE_CRITIC_GUARDRAIL_DRY_RUN_RESPONSE_SCHEMA
    assert captured["return_parsed"] is True
    assert captured["temperature"] == 0
    assert "manual dry-run" in captured["messages"][0]["content"]
    assert result["critic_status"] == "approved"
    assert result["approved_suggestions"][0]["suggestion_id"] == "tailoring_dry_run_001"
    assert result["model_provider"] == "fake-provider"
    assert result["model_name"] == "fake-model"
    assert result["prompt_version"] == services.LIVE_CRITIC_GUARDRAIL_DRY_RUN_PROMPT_VERSION
    assert result["token_usage"] == {"total_token_count": 55}
    assert result["cost"] == {"estimated_cost": 0.03, "cost_currency": "USD"}
    assert result["latency_ms"] == 99


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_critic_guardrail_payload(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json=_request_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_critic_guardrail_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["critic_status"] == "approved"
    assert payload["approved_suggestions"]
    _assert_readonly_safety(payload)


def test_api_route_handles_missing_output_normally(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"tailoring_suggestion_payload": {}, "jd_intelligence": {}, "resume_evidence_rows": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["critic_status"] == "insufficient_evidence"
    assert "tailoring_payload_missing" in payload["reason_codes"]
    assert payload["approved_suggestions"] == []
    assert payload["downgraded_suggestions"] == []
    assert payload["rejected_suggestions"] == []
    _assert_readonly_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_approval_execution_or_llm_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualCriticGuardrailDryRunRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-critic-guardrail-dry-run")')
    route_end = source.index(
        '@app.post(\n    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-reporting-job"'
    )
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "FileResponse(",
        "StreamingResponse(",
        "open(",
        ".write(",
        "write_text",
        "write_bytes",
        "send_file",
        "subprocess",
        "background_tasks.add_task",
        "Thread(",
        "Process(",
        "get_agentic_approval_store",
        "_agentic_approval_storage_connection",
        "cursor.execute",
        ".commit(",
        "src.storage",
        "schema.sql",
        "migration_runner",
        "application_execution_queue",
        "submit_application(",
        "execute_application(",
        "score_resume_job_match",
        "ranking",
        "run_chat_completion",
        "openai",
        "anthropic",
        "llm_client",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_service_helper_slice_has_no_storage_scoring_queue_or_llm_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_manual_critic_guardrail_dry_run_payload")
    end = source.index("def _artifact_row_by_name")
    snippet = source[start:end]

    forbidden_markers = [
        "insert_",
        "get_rag_job_documents",
        "cursor.execute",
        ".commit(",
        "subprocess",
        "requests.",
        "httpx.",
        "run_chat_completion",
        "score_resume_job_match",
        "mutate_ranking",
        "update_ranking",
        "execute_application(",
        "submit_application(",
        "workflow_runner",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_ui_manual_critic_guardrail_section_uses_existing_escaped_rendering():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualCriticGuardrailDryRunSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Critic Guardrail Dry-run" in snippet
    assert "data-manual-critic-guardrail-dry-run" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Approved suggestions\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Downgraded suggestions\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Rejected suggestions\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Unsupported claim risks\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Evidence gaps\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet
    assert "does not mutate resume content" in snippet


def test_ui_manual_critic_click_posts_endpoint_and_existing_dry_runs_still_exist():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-critic-guardrail-dry-run") == 1
    assert source.count("data-manual-critic-guardrail-dry-run") == 4
    assert "manual_critic_guardrail_dry_run_result" in source
    assert "renderManualCriticGuardrailDryRunSection(tracePayload)" in source
    assert source.count("/api/manual-jd-intelligence-dry-run") == 1
    assert source.count("/api/manual-resume-match-dry-run") == 1
    assert source.count("/api/manual-tailoring-suggestion-dry-run") == 1
    assert "renderManualJdIntelligenceDryRunSection(tracePayload)" in source
    assert "renderManualResumeMatchDryRunSection(tracePayload)" in source
    assert "renderManualTailoringSuggestionDryRunSection(tracePayload)" in source
