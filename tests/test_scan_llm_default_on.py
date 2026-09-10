from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


def _request_payload(scan_id: str = "scan-llm-default-on") -> dict:
    return {
        "scan_id": scan_id,
        "company": "ExampleCo",
        "role": "Senior Analytics Engineer",
        "job_description_text": (
            "Own semantic layer design, Python and dbt delivery, data quality "
            "monitoring, and financial analytics."
        ),
        "job_url": "https://example.test/jobs/analytics-engineer",
        "job_doc_id": "job-llm-default-on",
        "resume_text": (
            "Senior Analytics Engineer. Delivered semantic layer design with Python "
            "and dbt for financial analytics."
        ),
    }


def _valid_content(**overrides) -> dict:
    return {
        "required_skills": ["semantic layer design", "Kubernetes"],
        "preferred_skills": ["Python"],
        "required_tools": ["dbt"],
        "preferred_tools": [],
        "workflows": ["data quality monitoring"],
        "methods": [],
        "business_contexts": ["financial analytics"],
        "stakeholder_contexts": [],
        "ownership_signals": [],
        "seniority_signals": ["Senior"],
        "risk_flags": [],
        "extraction_confidence": 0.91,
        **overrides,
    }


def _configured_client(monkeypatch, provider_result=None, provider_error=None):
    monkeypatch.setenv("DATABASE_URL", "postgresql://unit-test.invalid/applylens")
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-llm-scan")
    monkeypatch.setattr(api, "_auth_owner_email", lambda request: "owner@example.test")

    route_calls = []
    runtime_calls = []
    persisted_rows = []

    def fake_resolve(owner_user_id, workload_id):
        route_calls.append((owner_user_id, workload_id))
        return {
            "workload_id": workload_id,
            "provider": "fake-configured-provider",
            "model": "fake-configured-model",
            "effective_selection_source": "applylens_recommended",
        }

    def fake_runtime(**kwargs):
        runtime_calls.append(deepcopy(kwargs))
        if provider_error is not None:
            raise provider_error
        return deepcopy(
            provider_result
            or {
                "content": _valid_content(),
                "provider": "fake-configured-provider",
                "model": "fake-configured-model",
                "token_usage": {"total_tokens": 51},
                "latency_ms": 9,
                "fallback_used": False,
            }
        )

    def fake_persist(row):
        persisted_rows.append(deepcopy(row))
        return {
            "attempted": True,
            "ok": True,
            "table_name": "saved_scans",
            "scan_id": row["scan_id"],
        }

    monkeypatch.setattr(services, "resolve_effective_user_provider_route", fake_resolve)
    monkeypatch.setattr(services, "run_user_chat_completion_with_metadata", fake_runtime)
    monkeypatch.setattr(services, "_dual_write_saved_scan_postgres", fake_persist)
    return TestClient(api.app), route_calls, runtime_calls, persisted_rows


def test_normal_api_scan_defaults_to_configured_llm_and_persists_same_review(monkeypatch):
    client, route_calls, runtime_calls, persisted_rows = _configured_client(monkeypatch)

    response = client.post("/planning/start-scan", json=_request_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["scan_status"] == "ready"
    assert payload["llm_analysis_status"] == "succeeded"
    assert route_calls == [("owner-llm-scan", "jd_intelligence")]
    assert len(runtime_calls) == 1
    runtime = runtime_calls[0]
    assert runtime["owner_user_id"] == "owner-llm-scan"
    assert runtime["provider"] == "fake-configured-provider"
    assert runtime["model"] == "fake-configured-model"
    assert runtime["workload_id"] == "jd_intelligence"
    assert runtime["return_parsed"] is True
    assert runtime["response_schema"] == services.LIVE_JD_INTELLIGENCE_DRY_RUN_RESPONSE_SCHEMA

    review = payload["scan_review_payload"]
    metadata = review["jd_llm_extraction"]
    assert metadata["response_schema_validation_status"] == "valid"
    assert metadata["grounding_status"] == "valid"
    assert metadata["validated_signals_applied_to_scoring"] is True
    assert metadata["structured_jd_signals"]["required_skills"] == [
        "semantic layer design"
    ]
    assert metadata["grounding_rejections"]["required_skills"] == ["Kubernetes"]
    assert "semantic layer design" in review["selected_jd_record"]["required_skills"]
    assert "Kubernetes" not in review["selected_jd_record"]["all_skills"]
    assert "semantic layer design" in str(review["scan_issue_contract"]).lower()

    assert len(persisted_rows) == 1
    stored = persisted_rows[0]
    assert stored["match_rate"] == review["scan_score"]["score"]
    assert stored["payload_json"]["scan_review_payload"] == review
    assert stored["payload_json"]["llm_analysis_status"] == "succeeded"

    monkeypatch.setattr(
        services,
        "get_saved_scan_postgres_payload",
        lambda scan_id, owner_user_id="": {"scan": deepcopy(stored)},
    )
    readback = services.saved_scan_report_payload(
        stored["scan_id"], owner_user_id="owner-llm-scan"
    )
    assert readback["scan"]["match_rate"] == review["scan_score"]["score"]
    assert readback["llm_analysis_status"] == "succeeded"
    assert readback["scan_review_payload"]["scan_score"] == review["scan_score"]
    assert readback["jd_llm_extraction_readback"]["structured_jd_signals"] == (
        metadata["structured_jd_signals"]
    )


def test_explicit_internal_disable_is_off_while_unspecified_request_is_on(monkeypatch):
    client, route_calls, runtime_calls, _persisted_rows = _configured_client(monkeypatch)

    normal = client.post("/planning/start-scan", json=_request_payload("scan-normal"))
    disabled = client.post(
        "/planning/start-scan",
        json={
            **_request_payload("scan-disabled"),
            "enable_jd_llm_extraction": False,
        },
    )

    assert normal.json()["llm_analysis_status"] == "succeeded"
    assert disabled.json()["llm_analysis_status"] == "disabled"
    assert disabled.json()["jd_llm_extraction_readback"]["llm_call_attempted"] is False
    assert route_calls == [("owner-llm-scan", "jd_intelligence")]
    assert len(runtime_calls) == 1


def test_provider_failure_returns_truthful_persisted_deterministic_fallback(monkeypatch):
    client, route_calls, runtime_calls, persisted_rows = _configured_client(
        monkeypatch,
        provider_error=RuntimeError("mock provider unavailable"),
    )

    response = client.post("/planning/start-scan", json=_request_payload("scan-fallback"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["scan_status"] == "ready"
    assert payload["llm_analysis_status"] == "fallback"
    assert payload["scan"]["note"] == (
        "Scan report generated with deterministic fallback after AI analysis was unavailable."
    )
    readback = payload["jd_llm_extraction_readback"]
    assert readback["llm_enabled"] is True
    assert readback["llm_call_attempted"] is True
    assert readback["llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert "provider_callable_error:RuntimeError" in readback["validation_errors"]
    assert route_calls == [("owner-llm-scan", "jd_intelligence")]
    assert len(runtime_calls) == 1
    assert persisted_rows[0]["payload_json"]["llm_analysis_status"] == "fallback"


def test_malformed_json_and_schema_invalid_score_are_rejected(monkeypatch):
    malformed_client, _routes, _runtime, _rows = _configured_client(
        monkeypatch,
        provider_result={
            "content": "{not-json",
            "provider": "fake-configured-provider",
            "model": "fake-configured-model",
        },
    )
    malformed = malformed_client.post(
        "/planning/start-scan", json=_request_payload("scan-malformed")
    ).json()
    assert malformed["llm_analysis_status"] == "fallback"
    assert malformed["jd_llm_extraction_readback"][
        "response_schema_validation_status"
    ] == "invalid"
    assert "invalid_json_response" in malformed["jd_llm_extraction_readback"][
        "validation_errors"
    ]

    invalid_client, _routes, _runtime, _rows = _configured_client(
        monkeypatch,
        provider_result={
            "content": {**_valid_content(), "match_score": 1},
            "provider": "fake-configured-provider",
            "model": "fake-configured-model",
        },
    )
    invalid = invalid_client.post(
        "/planning/start-scan", json=_request_payload("scan-invalid-score")
    ).json()
    disabled = invalid_client.post(
        "/planning/start-scan",
        json={
            **_request_payload("scan-invalid-score-disabled"),
            "enable_jd_llm_extraction": False,
        },
    ).json()
    assert invalid["llm_analysis_status"] == "fallback"
    assert "unexpected_fields:match_score" in invalid["jd_llm_extraction_readback"][
        "validation_errors"
    ]
    assert invalid["scan_review_payload"]["scan_score"] == disabled[
        "scan_review_payload"
    ]["scan_score"]


def test_llm_success_does_not_override_persistence_failure_truthfulness(monkeypatch):
    client, _route_calls, _runtime_calls, _persisted_rows = _configured_client(monkeypatch)
    monkeypatch.setattr(
        services,
        "_dual_write_saved_scan_postgres",
        lambda row: {
            "attempted": True,
            "ok": False,
            "table_name": "saved_scans",
            "error": "mock write failure",
        },
    )

    payload = client.post(
        "/planning/start-scan", json=_request_payload("scan-persist-failure")
    ).json()

    assert payload["llm_analysis_status"] == "succeeded"
    assert payload["ok"] is False
    assert payload["scan_status"] == "failed"
    assert payload["scan"]["scan_status"] == "failed"


def test_scan_ui_describes_real_ai_stage_without_fake_progress_timing():
    script = (
        Path(__file__).resolve().parents[1]
        / "src/app/static/scan_workspace.js"
    ).read_text(encoding="utf-8")
    stage_block = script.split("const SCAN_WORKSPACE_PROCESSING_STAGES = [", 1)[1].split(
        "];", 1
    )[0]
    request_block = script.split("async function beginScanWorkspaceProcessing()", 1)[1].split(
        "function buildSavedScanRescanDraft", 1
    )[0]

    for label in (
        "Prepare request",
        "Load resume",
        "Analyze job with AI",
        "Validate and score match",
        "Build review payload",
        "Save report",
    ):
        assert label in stage_block
    assert "setTimeout" not in request_block
    assert 'currentStageKey = "prepare"' in request_block
    assert 'currentStageKey = "persist"' in request_block
    assert "AI analysis was unavailable" in request_block
