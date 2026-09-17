"""Step 18D25B role storage, Admin boundary and profile presentation contracts.

All database execution is intercepted; these tests never connect to PostgreSQL.
"""
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from src.app import api, auth_ui, services
from src.app.profile_ui import profile_page
from src.storage.auth import read_postgres as storage
from src.storage.auth.store import auth_user_db_row

ROOT = Path(__file__).resolve().parents[1]


def client_as(monkeypatch, role="user", is_admin=False):
    def guard(request):
        request.state.auth_user = {"user_id": "actor", "access_level": role, "is_admin": is_admin}
    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


@pytest.mark.parametrize("role,expected", [(None, "user"), ("user", "user"), ("super_user", "super_user"), (" SUPER_USER ", "super_user"), ("admin", "admin"), ("executive", "executive"), ("unknown", "user")])
def test_role_normalization_and_public_serialization(role, expected):
    row = auth_user_db_row({"email": "person@example.test", "password_hash": "test-only", "access_level": role})
    assert row["access_level"] == expected
    for serialize in (auth_ui._public_user_payload, services._public_admin_user_row):
        public = serialize(row)
        assert public["access_level"] == expected
        assert public["is_admin"] is False
        assert "password_hash" not in public


@pytest.mark.parametrize("role,admin", [("admin", False), (" ADMIN ", False), ("user", True), ("super_user", True)])
def test_effective_admin_can_change_role(monkeypatch, role, admin):
    operation = Mock(return_value={"ok": True, "updated": True, "user": {"access_level": "super_user"}})
    monkeypatch.setattr(services, "admin_profile_update_user_role_payload", operation)
    response = client_as(monkeypatch, role, admin).patch("/profile/admin/users/target/role", json={"access_level": "super_user"})
    assert response.status_code == 200
    operation.assert_called_once_with(user_id="target", access_level="super_user")


@pytest.mark.parametrize("role", ["user", "super_user", "executive"])
def test_non_admin_cannot_list_or_mutate_accounts(monkeypatch, role):
    operation = Mock(side_effect=AssertionError("Unauthorized storage access"))
    for name in ("admin_profile_users_payload", "admin_profile_update_user_role_payload", "admin_profile_update_user_access_payload", "admin_profile_delete_user_payload"):
        monkeypatch.setattr(services, name, operation)
    client = client_as(monkeypatch, role)
    for response in (
        client.get("/profile/admin/users"),
        client.patch("/profile/admin/users/target/role", json={"access_level": "super_user"}),
        client.patch("/profile/admin/users/target/role", json={"access_level": "user"}),
        client.patch("/profile/admin/users/target/access", json={"is_active": False}),
        client.delete("/profile/admin/users/target"),
    ):
        assert response.status_code == 403
    operation.assert_not_called()


@pytest.mark.parametrize("role", [None, "admin", "executive", "SUPER_USER", "", True, [], {}])
def test_invalid_role_rejected_before_database(monkeypatch, role):
    query = Mock(side_effect=AssertionError("Invalid role reached SQL"))
    monkeypatch.setattr(storage, "_run_psql_json_query", query)
    response = client_as(monkeypatch, "admin").patch("/profile/admin/users/target/role", json={"access_level": role})
    assert response.status_code == 400
    query.assert_not_called()


@pytest.mark.parametrize(
    "role,current_role,active",
    [("super_user", "user", True), ("user", "super_user", True), ("user", "super_user", False)],
)
def test_eligible_role_update_only_changes_role_and_timestamp(monkeypatch, role, current_role, active):
    row = {"user_id": "target", "access_level": role, "is_active": active, "is_admin": False, "display_name": "Preserved", "email": "preserved@example.test", "password_hash": "private"}
    query = Mock(return_value={"data": {"updated": True, "user": row}})
    monkeypatch.setattr(storage, "_run_psql_json_query", query)
    response = client_as(monkeypatch, "admin").patch("/profile/admin/users/target/role", json={"access_level": role, "is_active": not active, "is_admin": True})
    assert response.status_code == 200
    public = response.json()["user"]
    assert public["access_level"] == role and public["is_active"] == active
    assert public["display_name"] == "Preserved" and public["is_admin"] is False
    assert "password_hash" not in public
    sql = query.call_args.kwargs["sql"].split("WITH updated_user AS", 1)[1]
    assert f"SET access_level = '{role}', updated_at = now()" in sql
    assert "AND is_admin = FALSE" in sql
    assert f"LOWER(BTRIM(COALESCE(access_level, 'user'))) = '{current_role}'" in sql
    assert ("AND is_active = TRUE" in sql) is (role == "super_user")
    assert "auth_sessions" not in sql and "DELETE" not in sql
    assert "SET is_active" not in sql and "SET is_admin" not in sql


def test_revoked_ordinary_user_cannot_be_promoted_or_implicitly_authorized(monkeypatch):
    stored = {"user_id": "target", "access_level": "user", "is_active": False, "is_admin": False}
    query = Mock(return_value={"data": {"updated": False, "user": {}}})
    monkeypatch.setattr(storage, "_run_psql_json_query", query)
    response = client_as(monkeypatch, "admin").patch(
        "/profile/admin/users/target/role", json={"access_level": "super_user", "is_active": True},
    )
    assert response.status_code == 400
    assert stored == {"user_id": "target", "access_level": "user", "is_active": False, "is_admin": False}
    sql = query.call_args.kwargs["sql"].split("WITH updated_user AS", 1)[1]
    assert "LOWER(BTRIM(COALESCE(access_level, 'user'))) = 'user'" in sql
    assert "AND is_active = TRUE" in sql
    assert "SET is_active" not in sql
    assert "SET access_level = 'super_user', updated_at = now()" in sql
    assert "AND is_admin = FALSE" in sql


def test_protected_or_missing_target_is_not_success(monkeypatch):
    monkeypatch.setattr(storage, "_run_psql_json_query", Mock(return_value={"data": {"updated": False, "user": {}}}))
    response = client_as(monkeypatch, "admin").patch("/profile/admin/users/protected/role", json={"access_level": "super_user"})
    assert response.status_code == 400
    assert "protected" in response.json()["detail"]


def test_unauthenticated_role_change_is_rejected(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    operation = Mock(side_effect=AssertionError("Unauthenticated storage access"))
    monkeypatch.setattr(services, "admin_profile_update_user_role_payload", operation)
    response = TestClient(api.app).patch("/profile/admin/users/target/role", json={"access_level": "super_user"})
    assert response.status_code == 401
    operation.assert_not_called()


def test_list_includes_protected_admins_without_changing_default_storage_filter(monkeypatch):
    query = Mock(return_value={"users": [{"user_id": "a", "access_level": "admin", "is_admin": False}], "total_count": 1})
    monkeypatch.setattr(services, "get_non_admin_auth_users_postgres_payload", query)
    assert services.admin_profile_users_payload()["users"][0]["access_level"] == "admin"
    assert query.call_args.kwargs["include_admin"] is True
    assert "is_admin = FALSE" in storage._build_non_admin_users_sql(100, ensure_schema=False)
    assert "is_admin = FALSE" not in storage._build_non_admin_users_sql(100, ensure_schema=False, include_admin=True)


def test_sessions_read_current_role_and_deauthorization_still_revokes_sessions():
    sql = storage._build_active_session_user_sql("test-token", idle_timeout_seconds=60, ensure_schema=False)
    assert "FROM auth_users u" in sql and "u.access_level" in sql and "u.is_admin" in sql
    assert "WHERE u.is_active = TRUE" in sql
    revoke = storage._build_update_non_admin_user_access_sql("target", False, ensure_schema=False)
    assert "UPDATE auth_sessions" in revoke and "SET revoked_at = now()" in revoke
    assert "is_admin = FALSE" in revoke and "<> 'admin'" in revoke
    authorize = storage._build_update_non_admin_user_access_sql("target", True, ensure_schema=False)
    assert "SET\n        is_active = TRUE" in authorize
    assert "UPDATE auth_sessions" not in authorize
    assert "is_admin = FALSE" in authorize and "<> 'admin'" in authorize
    deletion = storage._build_delete_non_admin_user_sql("target", ensure_schema=False)
    assert "is_admin = FALSE" in deletion and "<> 'admin'" in deletion


@pytest.mark.parametrize("path", ["/scheduler", "/agentic-operations", "/advanced-diagnostics", "/profile/pipeline-runs/test-run/agentic-review"])
def test_super_user_operational_pages_are_enabled(monkeypatch, path):
    monkeypatch.setattr(services, "profile_saved_scans_payload", lambda **_kwargs: {"saved_scans": []})
    response = client_as(monkeypatch, "super_user").get(path, follow_redirects=False)
    assert response.status_code == 200


def test_admin_only_profile_controls_and_semantic_modal():
    request = Request({"type": "http", "method": "GET", "path": "/profile", "headers": [], "query_string": b""})
    request.state.auth_user = {"user_id": "admin", "access_level": "admin"}
    html = profile_page(request)
    assert 'id="adminUsersList" role="list"' in html
    assert 'id="refreshAdminUsersBtn"' in html
    refresh_button = html.split('id="refreshAdminUsersBtn"', 1)[1].split("</button>", 1)[0]
    assert 'class="user-access-refresh-icon"' in refresh_button
    assert 'd="M20 11.5a8 8 0 1 0-.6 3.6"' in refresh_button
    assert 'stroke-width="1.8"' in refresh_button
    assert "Refresh" in refresh_button
    assert "adminUsersTableBody" not in html
    assert 'aria-labelledby="adminUserRoleTitle"' in html and 'aria-modal="true"' in html
    assert "Gets access to" in html
    assert "Not enabled yet" not in html
    assert "additional operational visibility and read-only access" in html
    assert 'id="adminUserDeleteModal"' in html
    request.state.auth_user = {"user_id": "super", "access_level": "super_user", "is_admin": False}
    html = profile_page(request)
    assert 'id="adminUsersList"' not in html and 'id="adminUserRoleModal"' not in html
    # The shared shell ships hidden Admin links for every role; its existing JS
    # owns visibility. Super User must receive the same shell as an ordinary user.
    request.state.auth_user = {"user_id": "normal", "access_level": "user", "is_admin": False}
    assert html == profile_page(request)
