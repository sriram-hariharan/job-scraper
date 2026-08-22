from __future__ import annotations

from dataclasses import asdict, replace
import inspect
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.agents import canonical_registry
from src.app import api, services
from src.storage.user_pipeline import store as user_pipeline_store


ADMIN_USER = {
    "user_id": "admin-owner",
    "email": "admin@example.test",
    "is_admin": True,
    "access_level": "user",
}
ACCESS_LEVEL_ADMIN_USER = {
    "user_id": "access-admin-owner",
    "email": "access-admin@example.test",
    "is_admin": False,
    "access_level": "admin",
}
NON_ADMIN_USER = {
    "user_id": "non-admin-owner",
    "email": "user@example.test",
    "is_admin": False,
    "access_level": "user",
}
OVERVIEW_PATH = "/profile/admin/agentic-operations/overview"


def _client_as(monkeypatch: pytest.MonkeyPatch, user: dict | None) -> TestClient:
    def guard(request):
        if user is not None:
            request.state.auth_user = dict(user)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


@pytest.mark.parametrize("admin_user", [ADMIN_USER, ACCESS_LEVEL_ADMIN_USER])
def test_admin_can_read_owner_scoped_overview(monkeypatch, admin_user) -> None:
    captured: dict = {}

    def overview(**kwargs):
        captured.update(kwargs)
        return {"ok": True, "owner_user_id": kwargs["owner_user_id"]}

    monkeypatch.setattr(services, "agentic_operations_overview_payload", overview)
    response = _client_as(monkeypatch, admin_user).get(OVERVIEW_PATH)

    assert response.status_code == 200
    assert response.json()["owner_user_id"] == admin_user["user_id"]
    assert captured == {"owner_user_id": admin_user["user_id"]}


def test_non_admin_is_forbidden_before_overview_invocation(monkeypatch) -> None:
    called = False

    def forbidden_overview(**_kwargs):
        nonlocal called
        called = True
        raise AssertionError("Non-admin request must not reach overview composition.")

    monkeypatch.setattr(
        services,
        "agentic_operations_overview_payload",
        forbidden_overview,
    )
    response = _client_as(monkeypatch, NON_ADMIN_USER).get(OVERVIEW_PATH)

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required."}
    assert called is False


def test_unauthenticated_request_keeps_existing_middleware_401(monkeypatch) -> None:
    monkeypatch.setenv("JOB_STACK_AUTH_ENABLED", "true")

    response = TestClient(api.app).get(OVERVIEW_PATH)

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_query_parameters_cannot_override_authenticated_admin_owner(monkeypatch) -> None:
    captured: dict = {}

    def overview(**kwargs):
        captured.update(kwargs)
        return {"ok": True, "owner_user_id": kwargs["owner_user_id"]}

    monkeypatch.setattr(services, "agentic_operations_overview_payload", overview)
    response = _client_as(monkeypatch, ADMIN_USER).get(
        f"{OVERVIEW_PATH}?owner_user_id=other-owner&user_id=other-user"
    )

    assert response.status_code == 200
    assert captured == {"owner_user_id": ADMIN_USER["user_id"]}
    assert "other-owner" not in captured.values()
    assert "other-user" not in captured.values()


def test_current_pipeline_valid_status_is_projected_without_writes(
    monkeypatch,
    tmp_path,
) -> None:
    status_path = tmp_path / "live_pipeline_status.json"
    status_payload = {
        "run_id": "run-61c",
        "status": "running",
        "current_stage": "ai_evaluation",
        "completed_stages": ["startup", "scraping"],
        "stage_order": ["startup", "scraping", "ai_evaluation"],
        "stage_started_at": "2026-08-22T12:00:00+00:00",
        "stage_message": "Evaluating jobs",
        "counts": {"jobs": 4},
        "config": {"job_limit": 10},
        "final_job_count": None,
        "updated_at_utc": "2026-08-22T12:01:00+00:00",
        "unapproved_internal_field": "must-not-leak",
    }
    status_path.write_text(json.dumps(status_payload), encoding="utf-8")

    def fail_write(*_args, **_kwargs):
        raise AssertionError("Pure current-status readback must not write files.")

    monkeypatch.setattr(Path, "write_text", fail_write)
    monkeypatch.setattr(Path, "replace", fail_write)
    payload = services.agentic_operations_current_pipeline_payload(status_path)

    assert payload["available"] is True
    assert payload["state"] == "available"
    assert payload["run_id"] == "run-61c"
    assert payload["counts"] == {"jobs": 4}
    assert payload["config"] == {"job_limit": 10}
    assert "unapproved_internal_field" not in payload


def test_current_pipeline_missing_and_malformed_states_are_safe(tmp_path) -> None:
    missing = services.agentic_operations_current_pipeline_payload(
        tmp_path / "missing.json"
    )
    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_text("{not-json", encoding="utf-8")
    malformed = services.agentic_operations_current_pipeline_payload(malformed_path)

    assert missing == {
        "available": False,
        "state": "not_found",
        "source_path": str(tmp_path / "missing.json"),
    }
    assert malformed == {
        "available": False,
        "state": "malformed",
        "source_path": str(malformed_path),
    }


def test_recent_runs_reader_is_owner_scoped_bounded_and_schema_free(monkeypatch) -> None:
    captured: dict = {}
    rows = [
        {
            "run_id": f"run-{index}",
            "owner_user_id": ADMIN_USER["user_id"],
            "status": "succeeded",
            "started_at": f"2026-08-{index + 1:02d}T00:00:00+00:00",
            "status_json": {"counts": {"jobs": index}},
        }
        for index in range(15)
    ]

    def get_runs(**kwargs):
        captured.update(kwargs)
        return {"ok": True, "runs": rows, "total_row_count": len(rows)}

    monkeypatch.setattr(services, "get_user_pipeline_runs_postgres_payload", get_runs)
    payload = services.agentic_operations_recent_runs_payload(
        owner_user_id=ADMIN_USER["user_id"],
        limit=999,
    )

    assert captured["owner_user_id"] == ADMIN_USER["user_id"]
    assert captured["limit"] == services.AGENTIC_OPERATIONS_RECENT_RUN_LIMIT
    assert captured["offset"] == 0
    assert captured["ensure_schema"] is False
    assert captured["print_only"] is False
    assert payload["count"] == services.AGENTIC_OPERATIONS_RECENT_RUN_LIMIT
    assert len(payload["runs"]) == services.AGENTIC_OPERATIONS_RECENT_RUN_LIMIT
    assert all("owner_user_id" not in row for row in payload["runs"])


def test_overview_resolves_current_status_from_owner_scoped_recent_run(
    monkeypatch,
    tmp_path,
) -> None:
    status_path = tmp_path / "owner-status.json"
    status_path.write_text(
        json.dumps({"run_id": "owner-run", "status": "running"}),
        encoding="utf-8",
    )
    captured: dict = {}

    def get_runs(**kwargs):
        captured.update(kwargs)
        return {
            "runs": [
                {
                    "run_id": "owner-run",
                    "owner_user_id": ADMIN_USER["user_id"],
                    "status": "running",
                    "config_json": {"status_path": str(status_path)},
                }
            ]
        }

    monkeypatch.setattr(services, "get_user_pipeline_runs_postgres_payload", get_runs)
    payload = services.agentic_operations_overview_payload(
        owner_user_id=ADMIN_USER["user_id"]
    )

    assert captured["owner_user_id"] == ADMIN_USER["user_id"]
    assert payload["current_pipeline"]["run_id"] == "owner-run"
    assert payload["current_pipeline"]["state"] == "available"
    assert "_current_status_path" not in payload["recent_runs_state"]


def test_underlying_recent_runs_query_is_select_only_without_schema(monkeypatch) -> None:
    captured: dict = {}

    def query(**kwargs):
        captured.update(kwargs)
        return {"data": {"rows": [], "total_row_count": 0}}

    monkeypatch.setattr(user_pipeline_store, "_run_psql_json_stdin_query", query)
    user_pipeline_store.get_user_pipeline_runs_postgres_payload(
        owner_user_id=ADMIN_USER["user_id"],
        limit=10,
        ensure_schema=False,
    )

    sql = captured["sql"].upper()
    assert "SELECT" in sql
    for forbidden in ("INSERT ", "UPDATE ", "DELETE ", "CREATE ", "ALTER "):
        assert forbidden not in sql


def test_canonical_agents_and_zero_mutation_counts_come_from_registry() -> None:
    payload = services.agentic_operations_canonical_agents_payload()
    definitions = canonical_registry.list_canonical_agent_definitions()

    assert payload["agents"] == [asdict(definition) for definition in definitions]
    assert [agent["key"] for agent in payload["agents"]] == list(
        canonical_registry.CANONICAL_AGENT_KEYS
    )
    assert payload["safety_summary"]["canonical_agent_count"] == len(definitions)
    for field_name, value in payload["safety_summary"].items():
        if field_name != "canonical_agent_count":
            assert value == 0


def test_mutation_counts_are_derived_from_registry_definitions(monkeypatch) -> None:
    definitions = canonical_registry.list_canonical_agent_definitions()
    changed_critic = replace(
        definitions[0],
        score_mutation=True,
        queue_mutation=True,
    )
    monkeypatch.setattr(
        services,
        "list_canonical_agent_definitions",
        lambda: (changed_critic, *definitions[1:]),
    )

    summary = services.agentic_operations_canonical_agents_payload()["safety_summary"]

    assert summary["score_mutation_capable_count"] == 1
    assert summary["queue_mutation_capable_count"] == 1
    assert summary["application_action_capable_count"] == 0


def test_overview_response_reports_truthful_no_mutation_metadata(
    monkeypatch,
    tmp_path,
) -> None:
    def fail_side_effect(*_args, **_kwargs):
        raise AssertionError("Read-only overview must not invoke side-effect helpers.")

    for helper_name in (
        "_persist_user_pipeline_status_snapshot",
        "_ingest_pipeline_run_artifacts_to_postgres",
        "_finalize_seen_jobs_staging_payload",
        "_release_user_pipeline_active_run",
        "_write_runtime_status_file",
        "run_user_chat_completion_with_metadata",
        "run_effective_user_chat_completion_with_metadata",
    ):
        monkeypatch.setattr(services, helper_name, fail_side_effect)
    monkeypatch.setattr(
        services,
        "get_user_pipeline_runs_postgres_payload",
        lambda **_kwargs: {"ok": True, "runs": []},
    )
    payload = services.agentic_operations_overview_payload(
        owner_user_id=ADMIN_USER["user_id"],
        status_path=tmp_path / "missing.json",
    )

    assert payload["read_only"] is True
    assert payload["admin_only"] is True
    assert payload["owner_user_id"] == ADMIN_USER["user_id"]
    assert payload["recent_runs"] == []
    assert len(payload["canonical_agents"]) == len(
        canonical_registry.CANONICAL_AGENT_DEFINITIONS
    )
    assert payload["safety_metadata"] == {
        "read_only": True,
        "admin_only": True,
        "cross_user_access": False,
        "database_write_performed": False,
        "schema_write_performed": False,
        "provider_call_performed": False,
        "pipeline_execution_performed": False,
        "scheduler_mutation_performed": False,
        "scoring_changed": False,
        "ranking_changed": False,
        "queue_mutation_performed": False,
        "resume_mutation_performed": False,
        "application_execution_performed": False,
        "ats_submission_performed": False,
    }


def test_overview_source_excludes_write_reconciliation_provider_and_control_helpers() -> None:
    service_source = "\n".join(
        inspect.getsource(function)
        for function in (
            services.agentic_operations_current_pipeline_payload,
            services.agentic_operations_recent_runs_payload,
            services.agentic_operations_canonical_agents_payload,
            services.agentic_operations_overview_payload,
        )
    )
    route_source = inspect.getsource(api.profile_admin_agentic_operations_overview)

    for forbidden in (
        "_persist_user_pipeline_status_snapshot(",
        "_ingest_pipeline_run_artifacts_to_postgres(",
        "_finalize_seen_jobs_staging_payload(",
        "_release_user_pipeline_active_run(",
        "_write_runtime_status_file(",
        ".write_text(",
        ".replace(",
        "owner_pipeline_status_payload(",
        "pipeline_status_payload(",
        "ensure_schema=True",
        "run_user_chat_completion_with_metadata(",
        "run_effective_user_chat_completion_with_metadata(",
        "run_pipeline(",
        "scheduler_run_now(",
        "submit_application(",
        "execute_application(",
    ):
        assert forbidden not in service_source
    assert "_require_admin_user(http_request)" in route_source
    assert "_require_auth_owner_user_id(http_request)" in route_source
    assert "Body(" not in route_source
