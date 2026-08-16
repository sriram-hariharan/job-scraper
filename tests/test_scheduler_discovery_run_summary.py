from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from src.app import api, services


ADMIN_USER = {"user_id": "admin-1", "is_admin": True}
NON_ADMIN_USER = {"user_id": "user-1", "is_admin": False}
RUN_ID = "sched_agent_discovery_exact_20260816"


def _client_as(monkeypatch, user):
    def guard(request):
        if user is not None:
            request.state.auth_user = dict(user)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


def _artifact(**overrides):
    payload = {
        "run_id": RUN_ID,
        "job_name": "agent_discovery",
        "status": "succeeded",
        "started_at": "2026-08-16T01:00:00Z",
        "finished_at": "2026-08-16T01:05:30Z",
        "return_code": 0,
        "summary_message": "Discovery scheduler run completed successfully",
        "component_statuses": {
            "company_discovery_agent": "succeeded",
            "discovery_stage": "succeeded",
            "internal_component": "must-not-leak",
        },
        "failure_components": [],
        "component_errors": {"discovery_stage": "RuntimeError('secret')"},
        "company_discovery_summary": {
            "status": "succeeded",
            "queries_attempted": 22,
            "queries_failed": 0,
            "total_candidate_count": 155,
            "candidate_counts_by_ats": {"greenhouse": 70, "lever": 85},
            "raw_options": {"password": "synthetic-secret"},
        },
        "discovery_summary": {
            "run_unique_discovered_by_ats": {
                "greenhouse": 53,
                "lever": 128,
                "ashby": 109,
            },
            "sources": {
                "domain_discovered": {"greenhouse": 20, "lever": 30},
                "github_discovered": {"ashby": 4},
                "internal_source": {"lever": 999},
            },
        },
        "command_text": "psql postgresql://synthetic:secret@example/db",
        "pid": 1234,
        "log_path": "/tmp/private.log",
        "options": {"DATABASE_URL": "postgresql://synthetic:secret@example/db"},
    }
    payload.update(overrides)
    return payload


def _install_artifacts(monkeypatch, artifact=None, trigger="manual_admin"):
    calls = []

    def read(*, run_id, artifact_kind, initialize=True):
        calls.append((run_id, artifact_kind, initialize))
        if artifact_kind == "agent_discovery_summary":
            return _artifact() if artifact is None else artifact
        return {
            "run_id": RUN_ID,
            "job_name": "agent_discovery",
            "trigger_source": trigger,
            "command_text": "must-not-leak",
        }

    monkeypatch.setattr(services, "get_scheduler_artifact_payload", read)
    return calls


def test_summary_endpoint_is_admin_only(monkeypatch):
    assert _client_as(monkeypatch, None).get(
        f"/scheduler/runs/{RUN_ID}/agent-discovery-summary"
    ).status_code == 401
    assert _client_as(monkeypatch, NON_ADMIN_USER).get(
        f"/scheduler/runs/{RUN_ID}/agent-discovery-summary"
    ).status_code == 403


def test_exact_run_artifacts_are_composed_read_only_and_bounded(monkeypatch):
    calls = _install_artifacts(monkeypatch)
    response = _client_as(monkeypatch, ADMIN_USER).get(
        f"/scheduler/runs/{RUN_ID}/agent-discovery-summary"
    )

    assert response.status_code == 200
    payload = response.json()
    assert calls == [
        (RUN_ID, "agent_discovery_summary", False),
        (RUN_ID, "post_run_summary", False),
    ]
    assert payload["run_id"] == RUN_ID
    assert payload["job_name"] == "agent_discovery"
    assert payload["trigger"] == "manual"
    assert payload["company_discovery"] == {
        "status": "succeeded",
        "queries_attempted": 22,
        "queries_failed": 0,
        "total_candidate_count": 155,
        "candidate_counts_by_ats": {"greenhouse": 70, "lever": 85},
    }
    assert payload["discovery"]["run_unique_discovered_by_ats"] == {
        "greenhouse": 53,
        "lever": 128,
        "ashby": 109,
    }
    assert payload["discovery"]["sources"] == {
        "domain_discovered": {"greenhouse": 20, "lever": 30},
        "github_discovered": {"ashby": 4},
    }
    assert payload["components"] == {
        "company_discovery_agent": "succeeded",
        "discovery_stage": "succeeded",
    }
    serialized = json.dumps(payload).lower()
    for forbidden in (
        "database_url",
        "synthetic-secret",
        "command_text",
        "postgresql://",
        "pid",
        "log_path",
        "raw_options",
        "component_errors",
        "internal_component",
        "internal_source",
    ):
        assert forbidden not in serialized


@pytest.mark.parametrize(
    "artifact",
    [
        {},
        _artifact(run_id="another-run"),
        _artifact(job_name="live_pipeline"),
    ],
)
def test_missing_or_mismatched_artifact_fails_closed_without_latest_fallback(
    monkeypatch, artifact
):
    calls = _install_artifacts(monkeypatch, artifact=artifact)
    response = _client_as(monkeypatch, ADMIN_USER).get(
        f"/scheduler/runs/{RUN_ID}/agent-discovery-summary"
    )
    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "ok": False,
            "available": False,
            "run_id": RUN_ID,
            "message": "Discovery summary unavailable",
        }
    }
    assert calls == [(RUN_ID, "agent_discovery_summary", False)]


@pytest.mark.parametrize(
    "trigger,expected",
    [
        ("manual_admin", "manual"),
        ("external_scheduler_wrapper", "scheduled"),
        ("customer_secret_trigger", "unknown"),
    ],
)
def test_trigger_provenance_is_allowlisted(monkeypatch, trigger, expected):
    _install_artifacts(monkeypatch, trigger=trigger)
    payload = services.agent_discovery_run_summary_payload(RUN_ID)
    assert payload["trigger"] == expected
    assert trigger not in json.dumps(payload)


def test_missing_metrics_stay_missing_and_dangerous_summary_text_is_replaced(monkeypatch):
    artifact = _artifact(
        company_discovery_summary={},
        discovery_summary={},
        summary_message="DATABASE_URL=postgresql://synthetic:secret@example/db",
    )
    _install_artifacts(monkeypatch, artifact=artifact)
    payload = services.agent_discovery_run_summary_payload(RUN_ID)
    assert payload["company_discovery"]["queries_attempted"] is None
    assert payload["company_discovery"]["queries_failed"] is None
    assert payload["company_discovery"]["total_candidate_count"] is None
    assert "synthetic" not in json.dumps(payload).lower()
