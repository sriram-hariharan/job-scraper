from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from src.app import api, services
from src.storage import scheduler_artifacts_store
from src.storage.notification_state.store import (
    notification_state_contract_health_payload,
    notification_state_db_row,
)


ADMIN = {
    "user_id": "admin-1",
    "email": "admin@example.test",
    "is_admin": True,
    "access_level": "admin",
}
NON_ADMIN = {
    "user_id": "user-1",
    "email": "user@example.test",
    "is_admin": False,
    "access_level": "user",
}


def _notification(
    notification_id: str,
    *,
    created_at: str,
    job_name: str = "live_pipeline",
    run_status: str = "succeeded",
    delivery_status: str = "recorded_outbox_only",
    level: str = "success",
) -> dict:
    return {
        "notification_id": notification_id,
        "notification_kind": "scheduled_run_email_delivery",
        "created_at": created_at,
        "title": f"Scheduled run {run_status}",
        "message": "Bounded scheduler notification.",
        "level": level,
        "is_read": False,
        "job_name": job_name,
        "run_id": notification_id.split("::")[1],
        "run_status": run_status,
        "delivery_mode": "outbox_only",
        "delivery_status": delivery_status,
    }


def _artifact(payload: dict, *, artifact_kind: str = "post_run_notification") -> dict:
    return {
        "artifact_id": f"artifact-{payload.get('notification_id', 'other')}",
        "run_id": payload.get("run_id", "run-other"),
        "job_name": payload.get("job_name", "live_pipeline"),
        "artifact_kind": artifact_kind,
        "artifact_name": "notification.json",
        "payload_json": deepcopy(payload),
        "created_at": payload.get("created_at", ""),
        "updated_at": payload.get("created_at", ""),
    }


def _artifact_payload(rows: list[dict]) -> dict:
    return {
        "ok": True,
        "artifact_kind": "post_run_notification",
        "query_limit": 500,
        "rows": deepcopy(rows),
        "count": len(rows),
    }


def _client_as(monkeypatch, user: dict | None) -> TestClient:
    def guard(request):
        if user is None:
            return JSONResponse(status_code=401, content={"detail": "Authentication required."})
        request.state.auth_user = dict(user)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


def test_storage_lists_only_bounded_notification_artifacts_newest_first(monkeypatch):
    captured = {}
    rows = [
        _artifact(_notification("scheduled_run_email::new::live_pipeline", created_at="2026-08-24T08:00:00+00:00")),
        _artifact({"notification_id": "unrelated"}, artifact_kind="post_run_summary"),
    ]

    def fake_query(sql):
        captured["sql"] = sql
        return {"rows": rows}

    monkeypatch.setattr(scheduler_artifacts_store, "_run_psql_json_query", fake_query)
    monkeypatch.setattr(
        scheduler_artifacts_store,
        "init_scheduler_artifacts_store",
        lambda: (_ for _ in ()).throw(AssertionError("read must not initialize/write schema")),
    )

    payload = scheduler_artifacts_store.list_scheduler_artifacts_by_kind(
        artifact_kind="post_run_notification",
        limit=9999,
    )

    assert payload["query_limit"] == 500
    assert payload["count"] == 1
    assert payload["rows"][0]["payload_json"]["notification_id"].endswith("live_pipeline")
    assert "WHERE artifact_kind = 'post_run_notification'" in captured["sql"]
    assert "LIMIT 500" in captured["sql"]
    assert "payload_json->>'created_at'" in captured["sql"]
    assert "artifact_id DESC" in captured["sql"]


def test_service_merges_latest_state_deduplicates_orders_and_filters(monkeypatch):
    newest = _notification(
        "scheduled_run_email::run-new::live_pipeline",
        created_at="2026-08-24T08:00:00+00:00",
    )
    duplicate_older = {**newest, "created_at": "2026-08-23T08:00:00+00:00", "title": "stale"}
    failed = _notification(
        "scheduled_run_email::run-failed::agent_discovery",
        created_at="2026-08-24T07:00:00+00:00",
        job_name="agent_discovery",
        run_status="failed",
        level="error",
    )
    smtp_failure = _notification(
        "scheduled_run_email::run-smtp::live_pipeline",
        created_at="2026-08-24T06:00:00+00:00",
        delivery_status="failed_smtp",
        level="error",
    )
    unrelated = {**newest, "notification_id": "other", "notification_kind": "other_kind"}
    artifacts = [_artifact(failed), _artifact(duplicate_older), _artifact(smtp_failure), _artifact(newest), _artifact(unrelated)]
    monkeypatch.setattr(
        services,
        "list_scheduler_artifacts_by_kind",
        lambda **kwargs: _artifact_payload(artifacts),
    )
    monkeypatch.setattr(
        services,
        "_load_latest_notification_state_overlay",
        lambda: {newest["notification_id"]: {"is_read": True, "state_timestamp": "2026-08-24T09:00:00+00:00"}},
    )

    payload = services.notifications_payload(
        limit=20,
        scheduler_notifications_visible=True,
    )
    assert [row["notification_id"] for row in payload["rows"]] == [
        newest["notification_id"],
        failed["notification_id"],
        smtp_failure["notification_id"],
    ]
    assert payload["rows"][0]["title"] != "stale"
    assert payload["rows"][0]["is_read"] is True
    assert payload["rows"][1]["is_read"] is False
    assert payload["rows"][1]["run_status"] == "failed"
    assert payload["rows"][2]["delivery_status"] == "failed_smtp"
    assert payload["notification_source"] == "scheduler_artifacts"

    filtered = services.notifications_payload(
        job_name="agent_discovery",
        level="error",
        delivery_status="recorded_outbox_only",
        is_read="false",
        limit=10,
        scheduler_notifications_visible=True,
    )
    assert [row["notification_id"] for row in filtered["rows"]] == [failed["notification_id"]]

    unread = services.notifications_unread_count_payload(
        scheduler_notifications_visible=True,
    )
    assert unread == {"ok": True, "total_rows": 3, "read_count": 1, "unread_count": 2}


def test_later_unread_transition_reopens_notification(monkeypatch):
    row = _notification(
        "scheduled_run_email::run-toggle::live_pipeline",
        created_at="2026-08-24T08:00:00+00:00",
    )
    monkeypatch.setattr(
        services,
        "list_scheduler_artifacts_by_kind",
        lambda **kwargs: _artifact_payload([_artifact(row)]),
    )
    monkeypatch.setattr(
        services,
        "_load_latest_notification_state_overlay",
        lambda: {row["notification_id"]: {"is_read": False, "state_timestamp": "2026-08-24T10:00:00+00:00"}},
    )
    payload = services.notifications_payload(
        scheduler_notifications_visible=True,
    )
    assert payload["rows"][0]["is_read"] is False
    assert payload["rows"][0]["read_state_timestamp"] == "2026-08-24T10:00:00+00:00"


def test_missing_state_transition_defaults_to_unread(monkeypatch):
    row = {
        **_notification(
            "scheduled_run_email::run-no-state::live_pipeline",
            created_at="2026-08-24T08:00:00+00:00",
        ),
        "is_read": True,
    }
    monkeypatch.setattr(
        services,
        "list_scheduler_artifacts_by_kind",
        lambda **kwargs: _artifact_payload([_artifact(row)]),
    )
    monkeypatch.setattr(
        services,
        "_load_latest_notification_state_overlay",
        lambda **_kwargs: {},
    )

    payload = services.notifications_payload(
        scheduler_notifications_visible=True,
    )

    assert payload["rows"][0]["is_read"] is False


def test_admin_api_reads_summarizes_counts_and_updates_shared_state(monkeypatch):
    row = _notification(
        "scheduled_run_email::run-admin::live_pipeline",
        created_at="2026-08-24T08:00:00+00:00",
    )
    storage_calls = []
    writes = []
    monkeypatch.setattr(
        services,
        "list_scheduler_artifacts_by_kind",
        lambda **kwargs: storage_calls.append(kwargs) or _artifact_payload([_artifact(row)]),
    )
    monkeypatch.setattr(
        services,
        "get_scheduler_artifact_payload",
        lambda **kwargs: storage_calls.append(kwargs) or deepcopy(row),
    )
    monkeypatch.setattr(
        services,
        "_load_latest_notification_state_overlay",
        lambda **_kwargs: {},
    )
    monkeypatch.setattr(
        services,
        "_dual_write_notification_state_postgres",
        lambda state_row: writes.append(deepcopy(state_row)) or {"attempted": True, "ok": True},
    )
    client = _client_as(monkeypatch, ADMIN)

    listed = client.get("/notifications?limit=10&notification_dir=/tmp/not-authoritative")
    assert listed.status_code == 200
    assert [item["notification_id"] for item in listed.json()["rows"]] == [row["notification_id"]]
    assert listed.json()["notification_source"] == "scheduler_artifacts"

    summary = client.get("/notifications/summary?limit=10")
    assert summary.status_code == 200
    assert summary.json()["total_rows"] == 1
    assert summary.json()["unread_count"] == 1

    unread = client.get("/notifications/unread-count")
    assert unread.status_code == 200
    assert unread.json()["unread_count"] == 1

    updated = client.post(
        "/notifications/read-state?notification_dir=/tmp/not-authoritative",
        json={"notification_id": row["notification_id"], "is_read": True},
    )
    assert updated.status_code == 200
    assert updated.json()["notification"]["is_read"] is True
    assert len(writes) == 1
    assert writes[0]["notification_id"] == row["notification_id"]
    assert writes[0]["owner_user_id"] == ADMIN["user_id"]
    assert all(call["artifact_kind"] == "post_run_notification" for call in storage_calls)


def test_non_admin_cannot_see_or_mutate_global_scheduler_notifications(monkeypatch):
    storage_calls = []
    writes = []
    monkeypatch.setattr(
        services,
        "list_scheduler_artifacts_by_kind",
        lambda **kwargs: storage_calls.append(kwargs) or _artifact_payload([]),
    )
    monkeypatch.setattr(
        services,
        "_dual_write_notification_state_postgres",
        lambda row: writes.append(row) or {"attempted": True, "ok": True},
    )
    client = _client_as(monkeypatch, NON_ADMIN)

    listed = client.get("/notifications")
    assert listed.status_code == 200
    assert listed.json()["rows"] == []
    assert client.get("/notifications/summary").json()["total_rows"] == 0
    assert client.get("/notifications/unread-count").json()["unread_count"] == 0
    blocked = client.post(
        "/notifications/read-state",
        json={
            "notification_id": "scheduled_run_email::real-run::live_pipeline",
            "is_read": True,
        },
    )
    assert blocked.status_code == 400
    assert storage_calls == []
    assert writes == []


def test_unauthenticated_behavior_and_safe_storage_failure_are_preserved(monkeypatch):
    unauthenticated = _client_as(monkeypatch, None)
    assert unauthenticated.get("/notifications").status_code == 401

    client = _client_as(monkeypatch, ADMIN)
    monkeypatch.setattr(
        services,
        "list_scheduler_artifacts_by_kind",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("postgresql://secret")),
    )
    failed = client.get("/notifications")
    assert failed.status_code == 503
    assert failed.json() == {
        "detail": {"ok": False, "error_category": "notification_storage_unavailable"}
    }
    assert "secret" not in failed.text


def test_read_state_does_not_mutate_scheduler_artifacts(monkeypatch):
    row = _notification(
        "scheduled_run_email::run-state::live_pipeline",
        created_at="2026-08-24T08:00:00+00:00",
    )
    monkeypatch.setattr(
        services,
        "list_scheduler_artifacts_by_kind",
        lambda **kwargs: _artifact_payload([_artifact(row)]),
    )
    monkeypatch.setattr(
        services,
        "get_scheduler_artifact_payload",
        lambda **_kwargs: deepcopy(row),
    )
    monkeypatch.setattr(services, "_load_latest_notification_state_overlay", lambda: {})
    writes = []
    monkeypatch.setattr(
        services,
        "_dual_write_notification_state_postgres",
        lambda state_row: writes.append(deepcopy(state_row)) or {"attempted": True, "ok": True},
    )

    result = services.record_notification_read_state_payload(
        notification_id=row["notification_id"],
        is_read=True,
        scheduler_notifications_visible=True,
    )
    assert result["notification"]["is_read"] is True
    assert writes and writes[0]["notification_id"] == row["notification_id"]
    assert "upsert_scheduler_artifact" not in services.record_notification_read_state_payload.__code__.co_names


def test_notification_state_contract_supports_owner_scoped_tombstones():
    row = notification_state_db_row(
        {
            "state_timestamp": "2026-09-02T12:00:00+00:00",
            "owner_user_id": "owner-a",
            "notification_id": "notification-1",
            "is_read": False,
            "is_deleted": True,
        }
    )

    assert row["owner_user_id"] == "owner-a"
    assert row["is_deleted"] is True
    assert notification_state_contract_health_payload()["all_checks_pass"] is True


def test_individual_delete_is_owner_scoped_idempotent_and_preserves_source(monkeypatch):
    row = _notification(
        "scheduled_run_email::run-delete::agent_discovery",
        created_at="2026-08-24T08:00:00+00:00",
        job_name="agent_discovery",
    )
    artifacts = [_artifact(row)]
    state_by_owner = {}
    writes = []

    monkeypatch.setattr(
        services,
        "list_scheduler_artifacts_by_kind",
        lambda **_kwargs: _artifact_payload(artifacts),
    )
    monkeypatch.setattr(
        services,
        "get_scheduler_artifact_payload",
        lambda **_kwargs: deepcopy(row),
    )
    monkeypatch.setattr(
        services,
        "_load_latest_notification_state_overlay",
        lambda **kwargs: deepcopy(state_by_owner.get(kwargs.get("owner_user_id", ""), {})),
    )

    def write_state(state_row):
        writes.append(deepcopy(state_row))
        state_by_owner.setdefault(state_row["owner_user_id"], {})[
            state_row["notification_id"]
        ] = {
            **deepcopy(state_row),
            "is_read": bool(state_row["is_read"]),
            "is_deleted": bool(state_row["is_deleted"]),
        }
        return {"attempted": True, "ok": True}

    monkeypatch.setattr(services, "_dual_write_notification_state_postgres", write_state)

    first = services.delete_notification_payload(
        notification_id=row["notification_id"],
        scheduler_notifications_visible=True,
        owner_user_id="owner-a",
    )
    second = services.delete_notification_payload(
        notification_id=row["notification_id"],
        scheduler_notifications_visible=True,
        owner_user_id="owner-a",
    )

    assert first["already_deleted"] is False
    assert second["already_deleted"] is True
    assert len(writes) == 1
    assert writes[0]["owner_user_id"] == "owner-a"
    assert writes[0]["is_deleted"] is True
    assert services.notifications_payload(
        scheduler_notifications_visible=True,
        owner_user_id="owner-a",
    )["rows"] == []
    assert len(services.notifications_payload(
        scheduler_notifications_visible=True,
        owner_user_id="owner-b",
    )["rows"]) == 1
    assert len(artifacts) == 1


def test_delete_all_tombstone_covers_full_owner_inbox_not_client_window(monkeypatch):
    rows = [
        _notification(
            f"scheduled_run_email::run-{index:03d}::live_pipeline",
            created_at=f"2026-08-{1 + (index // 24):02d}T{index % 24:02d}:00:00+00:00",
        )
        for index in range(120)
    ]
    artifacts = [_artifact(row) for row in rows]
    state_by_owner = {}
    writes = []
    monkeypatch.setattr(
        services,
        "list_scheduler_artifacts_by_kind",
        lambda **_kwargs: _artifact_payload(artifacts),
    )
    monkeypatch.setattr(
        services,
        "_load_latest_notification_state_overlay",
        lambda **kwargs: deepcopy(state_by_owner.get(kwargs.get("owner_user_id", ""), {})),
    )

    def write_state(state_row):
        writes.append(deepcopy(state_row))
        state_by_owner.setdefault(state_row["owner_user_id"], {})[
            state_row["notification_id"]
        ] = deepcopy(state_row)
        return {"attempted": True, "ok": True}

    monkeypatch.setattr(services, "_dual_write_notification_state_postgres", write_state)

    first = services.delete_all_notifications_payload(
        scheduler_notifications_visible=True,
        owner_user_id="owner-a",
    )
    second = services.delete_all_notifications_payload(
        scheduler_notifications_visible=True,
        owner_user_id="owner-a",
    )

    assert first["already_deleted"] is False
    assert second["already_deleted"] is True
    assert len(writes) == 1
    assert writes[0]["notification_id"] == services._NOTIFICATION_DELETE_ALL_STATE_ID
    assert services.notifications_payload(
        limit=50,
        scheduler_notifications_visible=True,
        owner_user_id="owner-a",
    )["total_matching_rows"] == 0
    assert services.notifications_unread_count_payload(
        scheduler_notifications_visible=True,
        owner_user_id="owner-a",
    )["unread_count"] == 0
    assert services.notifications_payload(
        limit=50,
        scheduler_notifications_visible=True,
        owner_user_id="owner-b",
    )["total_matching_rows"] == 120
    assert len(artifacts) == 120


def test_delete_api_binds_authenticated_owner(monkeypatch):
    calls = []
    monkeypatch.setattr(
        services,
        "delete_notification_payload",
        lambda **kwargs: calls.append(("one", deepcopy(kwargs))) or {"ok": True},
    )
    monkeypatch.setattr(
        services,
        "delete_all_notifications_payload",
        lambda **kwargs: calls.append(("all", deepcopy(kwargs))) or {"ok": True},
    )
    client = _client_as(monkeypatch, ADMIN)

    assert client.post(
        "/notifications/delete",
        json={"notification_id": "notification-1"},
    ).status_code == 200
    assert client.post("/notifications/delete-all").status_code == 200
    assert calls == [
        (
            "one",
            {
                "notification_id": "notification-1",
                "scheduler_notifications_visible": True,
                "owner_user_id": ADMIN["user_id"],
            },
        ),
        (
            "all",
            {
                "scheduler_notifications_visible": True,
                "owner_user_id": ADMIN["user_id"],
            },
        ),
    ]
