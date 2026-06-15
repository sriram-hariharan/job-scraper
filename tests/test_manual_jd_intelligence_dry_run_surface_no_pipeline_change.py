from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-jd-intelligence-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _request_payload() -> dict:
    return {
        "job_title": "Senior Analytics Engineer",
        "company": "ExampleCo",
        "location": "Remote",
        "job_description": "Own dbt models, Airflow jobs, Python analysis, and stakeholder reporting.",
        "source_metadata": {"source": "test", "nested": {"url": "https://example.test/job"}},
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _valid_adapter_payload() -> dict:
    return {
        "required_skills": ["SQL", "Python"],
        "preferred_skills": ["analytics engineering"],
        "required_tools": ["dbt"],
        "preferred_tools": ["Airflow"],
        "workflows": ["warehouse modeling"],
        "methods": ["stakeholder reporting"],
        "business_contexts": ["self-serve analytics"],
        "stakeholder_contexts": ["finance partners"],
        "ownership_signals": ["owns data marts"],
        "seniority_signals": ["senior scope"],
        "risk_flags": [],
        "extraction_confidence": 0.9,
        "model_provider": "fake-provider",
        "model_name": "fake-model",
        "prompt_version": "fake-prompt-v1",
    }


def _assert_readonly_safety(payload: dict, *, did_call_llm: bool) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
    assert safety["feature_flag_required"] is True
    assert safety["did_call_llm"] is did_call_llm
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False


def test_service_default_flag_off_returns_disabled_fallback_without_calling_adapter():
    calls = []

    def adapter(payload):
        calls.append(payload)
        return _valid_adapter_payload()

    source = _request_payload()
    original = deepcopy(source)
    payload = services.build_manual_jd_intelligence_dry_run_payload(
        **source,
        adapter=adapter,
    )

    assert source == original
    assert calls == []
    assert payload["validation_status"] == "disabled"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["feature_flag_disabled"]
    assert payload["default_feature_flag_enabled"] is False
    assert payload["service_surface"] == "manual_jd_intelligence_dry_run"
    _assert_readonly_safety(payload, did_call_llm=False)


def test_service_enabled_fake_adapter_returns_validated_jd_intelligence():
    payload = services.build_manual_jd_intelligence_dry_run_payload(
        **_request_payload(),
        adapter=lambda _payload: _valid_adapter_payload(),
        feature_enabled=True,
    )

    assert payload["validation_status"] == "valid"
    assert payload["fallback_used"] is False
    assert payload["required_skills"] == ["SQL", "Python"]
    assert payload["required_tools"] == ["dbt"]
    assert payload["model_provider"] == "fake-provider"
    assert payload["model_name"] == "fake-model"
    _assert_readonly_safety(payload, did_call_llm=True)


def test_service_env_flag_off_does_not_call_live_provider(monkeypatch):
    calls = []

    monkeypatch.setattr(services, "LIVE_JD_INTELLIGENCE_DRY_RUN_ENABLED", False)
    monkeypatch.setattr(
        services,
        "_live_jd_intelligence_provider_adapter",
        lambda payload: calls.append(payload) or _valid_adapter_payload(),
    )

    payload = services.build_manual_jd_intelligence_dry_run_payload(**_request_payload())

    assert calls == []
    assert payload["validation_status"] == "disabled"
    assert payload["fallback_used"] is True
    assert payload["env_feature_flag_enabled"] is False
    _assert_readonly_safety(payload, did_call_llm=False)


def test_service_env_flag_enabled_uses_fake_live_provider(monkeypatch):
    calls = []

    def fake_provider(payload):
        calls.append(payload)
        return {
            **_valid_adapter_payload(),
            "model_provider": "env-provider",
            "model_name": "env-model",
            "token_usage": {"total_token_count": 44},
            "cost": {"estimated_cost": 0.02, "cost_currency": "USD"},
            "latency_ms": 77,
        }

    monkeypatch.setattr(services, "LIVE_JD_INTELLIGENCE_DRY_RUN_ENABLED", True)
    monkeypatch.setattr(services, "_live_jd_intelligence_provider_adapter", fake_provider)

    payload = services.build_manual_jd_intelligence_dry_run_payload(**_request_payload())

    assert calls
    assert calls[0]["job_title"] == "Senior Analytics Engineer"
    assert payload["validation_status"] == "valid"
    assert payload["model_provider"] == "env-provider"
    assert payload["model_name"] == "env-model"
    assert payload["token_usage"] == {"total_token_count": 44}
    assert payload["cost"] == {"estimated_cost": 0.02, "cost_currency": "USD"}
    assert payload["latency_ms"] == 77
    assert payload["env_feature_flag_enabled"] is True
    _assert_readonly_safety(payload, did_call_llm=True)


def test_service_enabled_live_provider_invalid_json_falls_back(monkeypatch):
    monkeypatch.setattr(services, "LIVE_JD_INTELLIGENCE_DRY_RUN_ENABLED", True)
    monkeypatch.setattr(
        services,
        "_live_jd_intelligence_provider_adapter",
        lambda _payload: {"raw_response": "{bad json", "model_provider": "fake"},
    )

    payload = services.build_manual_jd_intelligence_dry_run_payload(**_request_payload())

    assert payload["validation_status"] == "fallback"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["invalid_json_response"]
    _assert_readonly_safety(payload, did_call_llm=True)


def test_service_enabled_live_provider_exception_falls_back(monkeypatch):
    def fake_provider(_payload):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(services, "LIVE_JD_INTELLIGENCE_DRY_RUN_ENABLED", True)
    monkeypatch.setattr(services, "_live_jd_intelligence_provider_adapter", fake_provider)

    payload = services.build_manual_jd_intelligence_dry_run_payload(**_request_payload())

    assert payload["validation_status"] == "fallback"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["adapter_error:RuntimeError"]
    _assert_readonly_safety(payload, did_call_llm=True)


def test_live_provider_adapter_uses_existing_llm_client_with_schema(monkeypatch):
    captured = {}

    def fake_run_chat_completion_with_metadata(**kwargs):
        captured.update(kwargs)
        return {
            "content": _valid_adapter_payload(),
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

    result = services._live_jd_intelligence_provider_adapter(_request_payload())

    assert captured["response_mime_type"] == "application/json"
    assert captured["response_schema"] == services.LIVE_JD_INTELLIGENCE_DRY_RUN_RESPONSE_SCHEMA
    assert captured["return_parsed"] is True
    assert captured["temperature"] == 0
    assert "manual dry-run" in captured["messages"][0]["content"]
    assert result["required_skills"] == ["SQL", "Python"]
    assert result["model_provider"] == "fake-provider"
    assert result["model_name"] == "fake-model"
    assert result["prompt_version"] == services.LIVE_JD_INTELLIGENCE_DRY_RUN_PROMPT_VERSION
    assert result["token_usage"] == {"total_token_count": 55}
    assert result["cost"] == {"estimated_cost": 0.03, "cost_currency": "USD"}
    assert result["latency_ms"] == 99


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_default_disabled_dry_run_payload(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json=_request_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_jd_intelligence_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["validation_status"] == "disabled"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["feature_flag_disabled"]
    _assert_readonly_safety(payload, did_call_llm=False)


def test_api_route_explicit_enabled_can_use_injected_fake_provider(monkeypatch):
    calls = []

    def fake_provider(payload):
        calls.append(payload)
        return _valid_adapter_payload()

    monkeypatch.setattr(services, "LIVE_JD_INTELLIGENCE_DRY_RUN_ENABLED", False)
    monkeypatch.setattr(services, "_live_jd_intelligence_provider_adapter", fake_provider)

    response = _client(monkeypatch).post(
        ENDPOINT,
        json={**_request_payload(), "feature_enabled": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert calls
    assert payload["validation_status"] == "valid"
    assert payload["fallback_used"] is False
    _assert_readonly_safety(payload, did_call_llm=True)


def test_api_route_preserves_service_payload_without_storage_or_provider(monkeypatch):
    captured = {}

    def fake_service(**kwargs):
        captured.update(kwargs)
        return {
            **_valid_adapter_payload(),
            "validation_status": "valid",
            "validation_errors": [],
            "fallback_used": False,
            "manual_surface": True,
            "read_only": True,
            "default_feature_flag_enabled": False,
            "service_surface": "manual_jd_intelligence_dry_run",
            "safety_metadata": {
                "dry_run_only": True,
                "feature_flag_required": True,
                "did_call_llm": True,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_mutate_approval": False,
                "did_execute_application": False,
                "did_submit_application": False,
                "pipeline_wiring_added": False,
            },
        }

    monkeypatch.setattr(services, "build_manual_jd_intelligence_dry_run_payload", fake_service)
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={**_request_payload(), "feature_enabled": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured["job_title"] == "Senior Analytics Engineer"
    assert captured["feature_enabled"] is True
    assert "adapter" not in captured
    assert payload["validation_status"] == "valid"
    assert payload["explicit_user_action"] is True
    _assert_readonly_safety(payload, did_call_llm=True)


def test_api_route_slice_has_no_storage_mutation_queue_scoring_execution_or_provider_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualJdIntelligenceDryRunRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-jd-intelligence-dry-run")')
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


def test_service_helper_slice_has_no_runtime_storage_or_network_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_manual_jd_intelligence_dry_run_payload")
    end = source.index("def _jsonl_row_count_from_text")
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
        "ranking",
        "execute_application",
        "submit_application",
        "workflow_runner",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_live_provider_adapter_slice_reuses_existing_llm_client_without_storage_or_pipeline():
    source = Path("src/app/services.py").read_text()
    start = source.index("def _live_jd_intelligence_provider_adapter")
    end = source.index("def build_manual_jd_intelligence_dry_run_payload")
    snippet = source[start:end]

    assert "from src.ai.llm_client import run_chat_completion_with_metadata" in snippet
    assert "response_mime_type=\"application/json\"" in snippet
    assert "response_schema=_live_jd_intelligence_structured_output_contract()[\"schema\"]" in snippet

    forbidden_markers = [
        "insert_",
        "cursor.execute",
        ".commit(",
        "subprocess",
        "requests.",
        "httpx.",
        "score_resume_job_match",
        "ranking",
        "execute_application",
        "submit_application",
        "workflow_runner",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_ui_manual_jd_dry_run_section_uses_existing_escaped_rendering():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualJdIntelligenceDryRunSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual JD Intelligence Dry-run" in snippet
    assert "data-manual-jd-intelligence-dry-run" in snippet
    assert "escapeHtml(jobTitle)" in snippet
    assert "escapeHtml(company)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Required skills\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet
    assert "feature flag is off by default" in snippet.lower()
    assert "does not write storage" in snippet


def test_ui_manual_jd_dry_run_click_posts_readonly_endpoint_once():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-jd-intelligence-dry-run") == 1
    assert source.count("data-manual-jd-intelligence-dry-run") == 4
    assert "manual_jd_intelligence_dry_run_result" in source
    assert "renderManualJdIntelligenceDryRunSection(tracePayload)" in source
