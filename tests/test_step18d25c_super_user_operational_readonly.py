"""Step 18D25C Super User operational visibility and Admin control boundary.

All service calls are intercepted. These tests do not connect to PostgreSQL or
invoke providers.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.app import api, auth_ui, services


USER = {"user_id": "user-owner", "access_level": "user", "is_admin": False}
SUPER_USER = {"user_id": "super-owner", "access_level": "super_user", "is_admin": False}
ADMIN = {"user_id": "admin-owner", "access_level": "admin", "is_admin": False}
ROOT = Path(__file__).resolve().parents[1]


def client_as(monkeypatch: pytest.MonkeyPatch, user: dict | None) -> TestClient:
    def guard(request):
        if user is not None:
            request.state.auth_user = dict(user)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    monkeypatch.setattr(
        auth_ui,
        "current_user_from_request",
        lambda request: dict(getattr(request.state, "auth_user", {}) or {}),
    )
    return TestClient(api.app)


@pytest.fixture(autouse=True)
def isolated_readbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        services,
        "profile_saved_scans_payload",
        lambda **_kwargs: {"ok": True, "saved_scans": []},
    )


@pytest.mark.parametrize(
    "path",
    (
        "/scheduler",
        "/agentic-operations",
        "/advanced-diagnostics",
        "/profile/pipeline-runs/run-18d25c/agentic-review",
    ),
)
def test_operational_page_role_matrix(monkeypatch, path: str) -> None:
    assert client_as(monkeypatch, None).get(path).status_code == 401
    assert client_as(monkeypatch, USER).get(path).status_code == 403
    assert client_as(monkeypatch, SUPER_USER).get(path).status_code == 200
    assert client_as(monkeypatch, ADMIN).get(path).status_code == 200


@pytest.mark.parametrize(
    ("path", "service_name", "run_key"),
    (
        ("/profile/admin/agentic-operations/overview", "agentic_operations_overview_payload", None),
        ("/profile/pipeline-runs/run-18d25c/agentic-review-data", "profile_pipeline_run_agentic_review_payload", "run_id"),
        ("/profile/pipeline-runs/run-18d25c/agent-trace", "agent_trace_payload", "pipeline_run_id"),
        ("/profile/pipeline-runs/run-18d25c/evidence-chain-trace", "get_evidence_chain_trace_readback_payload", "pipeline_run_id"),
    ),
)
def test_owner_scoped_operational_read_api_role_matrix(
    monkeypatch,
    path: str,
    service_name: str,
    run_key: str | None,
) -> None:
    calls: list[dict] = []

    def readback(**kwargs):
        calls.append(kwargs)
        return {"ok": True, "owner_user_id": kwargs["owner_user_id"]}

    monkeypatch.setattr(services, service_name, readback)
    assert client_as(monkeypatch, USER).get(path).status_code == 403

    for actor in (SUPER_USER, ADMIN):
        response = client_as(monkeypatch, actor).get(f"{path}?owner_user_id=attacker")
        assert response.status_code == 200
        assert response.json()["owner_user_id"] == actor["user_id"]
        assert calls[-1]["owner_user_id"] == actor["user_id"]
        assert "attacker" not in calls[-1].values()
        if run_key:
            assert calls[-1][run_key] == "run-18d25c"


def test_scheduler_read_api_role_matrix(monkeypatch) -> None:
    monkeypatch.setattr(services, "scheduler_operator_summary_payload", lambda **_kwargs: {"ok": True})
    monkeypatch.setattr(services, "agent_discovery_run_summary_payload", lambda _run_id: {"ok": True})

    for path in ("/scheduler/summary", "/scheduler/runs/run-18d25c/agent-discovery-summary"):
        assert client_as(monkeypatch, USER).get(path).status_code == 403
        assert client_as(monkeypatch, SUPER_USER).get(path).status_code == 200
        assert client_as(monkeypatch, ADMIN).get(path).status_code == 200


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    (
        ("put", "/scheduler/automation-control", {"paused": True}),
        ("put", "/scheduler/jobs/live_pipeline/automation-control", {"paused": True}),
        ("put", "/scheduler/jobs/agent_discovery/automation-control", {"paused": True}),
        ("post", "/scheduler/jobs/agent_discovery/run-now", None),
    ),
)
def test_scheduler_mutations_reject_user_and_super_user_before_service(
    monkeypatch,
    method: str,
    path: str,
    json_body: dict | None,
) -> None:
    forbidden = Mock(side_effect=AssertionError("Unauthorized scheduler mutation reached service"))
    monkeypatch.setattr(services, "set_scheduler_automation_paused_payload", forbidden)
    monkeypatch.setattr(services, "set_scheduler_job_automation_paused_payload", forbidden)
    monkeypatch.setattr(services, "start_manual_agent_discovery_payload", forbidden)

    for actor in (USER, SUPER_USER):
        response = getattr(client_as(monkeypatch, actor), method)(path, json=json_body)
        assert response.status_code == 403
    forbidden.assert_not_called()


def test_super_user_cannot_manage_user_access(monkeypatch) -> None:
    forbidden = Mock(side_effect=AssertionError("Unauthorized User Access request reached service"))
    for name in (
        "admin_profile_users_payload",
        "admin_profile_update_user_access_payload",
        "admin_profile_update_user_role_payload",
        "admin_profile_delete_user_payload",
    ):
        monkeypatch.setattr(services, name, forbidden)

    client = client_as(monkeypatch, SUPER_USER)
    responses = (
        client.get("/profile/admin/users"),
        client.patch("/profile/admin/users/target/access", json={"is_active": False}),
        client.patch("/profile/admin/users/target/role", json={"access_level": "super_user"}),
        client.patch("/profile/admin/users/target/role", json={"access_level": "user"}),
        client.delete("/profile/admin/users/target"),
    )
    assert {response.status_code for response in responses} == {403}
    forbidden.assert_not_called()


def test_super_user_cannot_administer_registration_requests(monkeypatch) -> None:
    forbidden = Mock(side_effect=AssertionError("Unauthorized registration request reached storage"))
    monkeypatch.setattr(auth_ui, "get_pending_auth_registration_requests_postgres_payload", forbidden)
    monkeypatch.setattr(auth_ui, "approve_auth_registration_request_postgres_payload", forbidden)
    monkeypatch.setattr(auth_ui, "reject_auth_registration_request_postgres_payload", forbidden)

    client = client_as(monkeypatch, SUPER_USER)
    assert client.get("/admin/registration-requests", follow_redirects=False).status_code == 403
    assert client.get("/admin/registration-requests/data").status_code == 403
    assert client.post("/admin/registration-requests/request-1/approve", json={}).status_code == 403
    assert client.post("/admin/registration-requests/request-1/reject", json={}).status_code == 403
    forbidden.assert_not_called()


@pytest.mark.parametrize("actor", (USER, SUPER_USER))
def test_existing_owner_scoped_diagnostics_mutation_remains_a_normal_user_capability(
    monkeypatch,
    actor: dict,
) -> None:
    reset = Mock(return_value={"ok": True, "diagnostics_reset": True, "diagnostic_state": {}})
    monkeypatch.setattr(services, "reset_saved_scan_diagnostics_payload", reset)

    response = client_as(monkeypatch, actor).post(
        "/planning/saved-scan/scan-1/state",
        json={"diagnostics_reset": True},
    )

    assert response.status_code == 200
    reset.assert_called_once_with(scan_id="scan-1", owner_user_id=actor["user_id"])


def test_agentic_review_super_user_branch_uses_only_owner_scoped_get_readbacks() -> None:
    source = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
    branch = source.split("async function initAgenticReviewReadOnlyPage()", 1)[1].split(
        "initAgenticReviewReadOnlyPage();", 1
    )[0]

    assert "renderAgenticReviewData" in branch
    assert "removeAgenticReviewOperationalControls();" in branch
    assert "agentic-review-data" in branch
    assert "agent-trace" in branch
    assert "evidence-chain-trace" not in branch  # delegated to the bounded GET helper
    assert "MANUAL_PROVIDER_PREVIEW_ENDPOINT" not in branch
    assert 'method: "POST"' not in branch
    assert "loadManualProviderPreviewReadiness" not in branch


def test_agentic_review_read_only_cleanup_removes_manual_controls() -> None:
    source = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
    cleanup = source.split("function removeAgenticReviewOperationalControls()", 1)[1].split(
        "async function initAgenticReviewReadOnlyPage()", 1
    )[0]

    assert ".agentic-feedback-actions" in cleanup
    assert ".manual-provider-preview-action-cell" in cleanup
    assert "#agenticReviewTracePanel input" in cleanup
    assert ".forEach((element) => element.remove())" in cleanup


def test_admin_guard_remains_distinct_from_operations_viewer() -> None:
    assert api._require_admin_user is not api._require_operations_viewer
    assert auth_ui._require_admin_user is not api._require_operations_viewer
