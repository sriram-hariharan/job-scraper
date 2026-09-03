from __future__ import annotations

import asyncio
import threading

from fastapi import Request
from fastapi.responses import JSONResponse

from src.app import api, services
from src.auth import runtime as auth_runtime
from src.auth.session import auth_cookie_name
from src.storage.notification_state import read_postgres


OWNER = "owner-hot-path"
NOTIFICATION_ID = "scheduled_run_email::run-hot-path::live_pipeline"


def _request(path: str = "/notifications/read-state", method: str = "POST") -> Request:
    cookie = f"{auth_cookie_name()}=test-session-token".encode("latin-1")
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "root_path": "",
            "headers": [(b"cookie", cookie)],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
    )


def _notification() -> dict:
    return {
        "notification_id": NOTIFICATION_ID,
        "notification_kind": "scheduled_run_email_delivery",
        "created_at": "2026-09-03T12:00:00+00:00",
        "title": "Scheduled run succeeded",
        "message": "Bounded notification.",
        "level": "success",
        "is_read": False,
        "job_name": "live_pipeline",
        "run_id": "run-hot-path",
        "run_status": "succeeded",
        "delivery_status": "recorded_outbox_only",
    }


def test_auth_lookup_session_touch_and_bulk_read_run_off_event_loop(monkeypatch):
    event_loop_thread = threading.get_ident()
    observed_threads: dict[str, int] = {}

    def auth_lookup(**_kwargs):
        observed_threads["auth"] = threading.get_ident()
        return {
            "ok": True,
            "user": {"user_id": OWNER, "is_admin": True},
        }

    def bulk_read(*, owner_user_id: str):
        assert owner_user_id == OWNER
        observed_threads["bulk"] = threading.get_ident()
        return {}

    async def downstream(_request):
        observed_threads["downstream"] = threading.get_ident()
        await asyncio.sleep(0)
        return JSONResponse({"ok": True})

    monkeypatch.setattr(
        auth_runtime,
        "get_auth_user_for_session_token_hash_postgres_payload",
        auth_lookup,
    )
    monkeypatch.setattr(
        api.bulk_generation_service,
        "active_bulk_generation_guard_state",
        bulk_read,
    )

    response = asyncio.run(api.require_dashboard_auth(_request(), downstream))

    assert response.status_code == 200
    assert observed_threads["auth"] != event_loop_thread
    assert observed_threads["bulk"] != event_loop_thread
    assert observed_threads["downstream"] == event_loop_thread


def test_blocking_auth_worker_does_not_block_another_async_task(monkeypatch):
    auth_started = threading.Event()
    auth_release = threading.Event()
    event_loop_progressed = False

    def blocking_auth(request):
        auth_started.set()
        assert auth_release.wait(timeout=2)
        request.state.auth_user = {"user_id": OWNER}
        return None

    async def downstream(_request):
        return JSONResponse({"ok": True})

    async def exercise():
        nonlocal event_loop_progressed
        request_task = asyncio.create_task(
            api.require_dashboard_auth(_request(path="/notifications"), downstream)
        )
        await asyncio.sleep(0.05)
        event_loop_progressed = True
        assert auth_started.is_set()
        assert not request_task.done()
        auth_release.set()
        return await request_task

    monkeypatch.setattr(api, "auth_guard_response", blocking_auth)

    response = asyncio.run(exercise())
    assert response.status_code == 200
    assert event_loop_progressed is True


def test_auth_failure_response_and_downstream_short_circuit_are_unchanged(monkeypatch):
    downstream_called = False

    def reject(_request):
        return JSONResponse({"detail": "Not authenticated."}, status_code=401)

    async def downstream(_request):
        nonlocal downstream_called
        downstream_called = True
        return JSONResponse({"ok": True})

    monkeypatch.setattr(api, "auth_guard_response", reject)
    response = asyncio.run(api.require_dashboard_auth(_request(), downstream))

    assert response.status_code == 401
    assert downstream_called is False


def test_owner_scoped_latest_state_query_is_single_bounded_indexed_lookup():
    payload = read_postgres.get_latest_notification_states_postgres_payload(
        notification_ids=[NOTIFICATION_ID, services._NOTIFICATION_DELETE_ALL_STATE_ID],
        owner_user_id=OWNER,
        database_url="postgresql://example.invalid/test",
        print_only=True,
    )
    sql = payload["command"][-1]

    assert payload["query_count"] == 2
    assert "WITH requested(notification_id) AS" in sql
    assert "INNER JOIN requested USING (notification_id)" in sql
    assert "events.owner_user_id IN ('owner-hot-path', '')" in sql
    assert "SELECT COUNT(*)" not in sql
    assert NOTIFICATION_ID in sql
    assert services._NOTIFICATION_DELETE_ALL_STATE_ID in sql


def test_read_state_uses_one_keyed_source_read_one_state_read_and_one_write(monkeypatch):
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        services,
        "get_scheduler_artifact_payload",
        lambda **kwargs: calls.append(("source", kwargs)) or _notification(),
    )
    monkeypatch.setattr(
        services,
        "get_latest_notification_states_postgres_payload",
        lambda **kwargs: calls.append(("state", kwargs)) or {
            "postgres": {"latest_rows": []}
        },
    )
    monkeypatch.setattr(
        services,
        "get_notification_state_postgres_status_payload",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("mutation must not run metadata/count status query")
        ),
    )
    monkeypatch.setattr(
        services,
        "list_scheduler_artifacts_by_kind",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("mutation must not scan the scheduler artifact window")
        ),
    )
    monkeypatch.setattr(
        services,
        "_dual_write_notification_state_postgres",
        lambda row: calls.append(("write", dict(row))) or {"ok": True},
    )

    result = services.record_notification_read_state_payload(
        notification_id=NOTIFICATION_ID,
        is_read=True,
        scheduler_notifications_visible=True,
        owner_user_id=OWNER,
    )

    assert result["notification"]["is_read"] is True
    assert [name for name, _payload in calls] == ["source", "state", "write"]
    state_call = dict(calls[1][1])
    assert state_call["owner_user_id"] == OWNER
    assert state_call["notification_ids"] == [
        NOTIFICATION_ID,
        services._NOTIFICATION_DELETE_ALL_STATE_ID,
    ]


def test_delete_reuses_one_keyed_source_read_and_preserves_tombstone(monkeypatch):
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        services,
        "get_scheduler_artifact_payload",
        lambda **kwargs: calls.append(("source", kwargs)) or _notification(),
    )
    monkeypatch.setattr(
        services,
        "get_latest_notification_states_postgres_payload",
        lambda **kwargs: calls.append(("state", kwargs)) or {
            "postgres": {
                "latest_rows": [
                    {
                        "notification_id": NOTIFICATION_ID,
                        "owner_user_id": OWNER,
                        "is_read": True,
                        "is_deleted": False,
                        "state_timestamp": "2026-09-03T12:01:00+00:00",
                    }
                ]
            }
        },
    )
    monkeypatch.setattr(
        services,
        "_load_scheduler_notification_source_rows",
        lambda: (_ for _ in ()).throw(
            AssertionError("delete must not scan or fetch the source twice")
        ),
    )
    monkeypatch.setattr(
        services,
        "_dual_write_notification_state_postgres",
        lambda row: calls.append(("write", dict(row))) or {"ok": True},
    )

    result = services.delete_notification_payload(
        notification_id=NOTIFICATION_ID,
        scheduler_notifications_visible=True,
        owner_user_id=OWNER,
    )

    assert result["already_deleted"] is False
    assert result["state_row"]["is_read"] is True
    assert result["state_row"]["is_deleted"] is True
    assert [name for name, _payload in calls] == ["source", "state", "write"]


def test_delete_distinguishes_missing_source_from_owner_tombstone(monkeypatch):
    monkeypatch.setattr(services, "get_scheduler_artifact_payload", lambda **_kwargs: {})
    try:
        services.delete_notification_payload(
            notification_id=NOTIFICATION_ID,
            scheduler_notifications_visible=True,
            owner_user_id=OWNER,
        )
    except ValueError as exc:
        assert str(exc) == f"Notification not found: {NOTIFICATION_ID}"
    else:
        raise AssertionError("missing source must retain the not-found failure")

