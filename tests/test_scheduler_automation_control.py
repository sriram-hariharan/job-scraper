from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.pipeline import scheduler
from src.storage.scheduler import control_store


class FakeDatabase:
    def __init__(self):
        self.events = []
        self.next_revision = 1
        self.lock_modes = []
        self.lock_held = None
        self.insert_count = 0

    def connect(self, _database_url):
        return FakeConnection(self)


class FakeConnection:
    def __init__(self, database):
        self.database = database
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return FakeCursor(self.database)

    def commit(self):
        self.commits += 1
        self.database.lock_held = None

    def rollback(self):
        self.rollbacks += 1
        self.database.lock_held = None

    def close(self):
        self.closed = True
        self.database.lock_held = None


class FakeCursor:
    def __init__(self, database):
        self.database = database
        self.row = None
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        self.close()

    def execute(self, sql, params=None):
        normalized = " ".join(str(sql).split())
        if "pg_advisory_xact_lock_shared" in normalized:
            self.database.lock_modes.append(("shared", tuple(params or ())))
            self.database.lock_held = "shared"
            self.row = (None,)
            return
        if "pg_advisory_xact_lock" in normalized:
            self.database.lock_modes.append(("exclusive", tuple(params or ())))
            self.database.lock_held = "exclusive"
            self.row = (None,)
            return
        if normalized.startswith("SELECT revision"):
            self.row = self.database.events[-1] if self.database.events else None
            return
        if normalized.startswith("INSERT INTO scheduler_automation_control_events"):
            action, prior_paused, resulting_paused, actor = params
            self.row = (
                self.database.next_revision,
                action,
                prior_paused,
                resulting_paused,
                datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc),
                actor,
            )
            self.database.next_revision += 1
            self.database.insert_count += 1
            self.database.events.append(self.row)
            return
        raise AssertionError(f"Unexpected SQL: {normalized}")

    def fetchone(self):
        return self.row

    def close(self):
        self.closed = True


def test_default_state_is_unpaused_and_finite():
    database = FakeDatabase()
    state = control_store.read_scheduler_automation_control(
        database_url="postgresql://test.invalid/db",
        connection_factory=database.connect,
    )

    assert state == {
        "paused": False,
        "revision": 0,
        "updated_at": None,
        "updated_by_user_id": None,
        "paused_at": None,
        "paused_by_user_id": None,
        "affected_jobs": ["agent_discovery", "live_pipeline"],
        "manual_admin_runs_allowed": True,
    }


def test_pause_resume_and_duplicate_requests_are_append_only_and_idempotent():
    database = FakeDatabase()
    kwargs = {
        "database_url": "postgresql://test.invalid/db",
        "connection_factory": database.connect,
    }

    paused = control_store.set_scheduler_automation_paused(
        True,
        changed_by_user_id="admin-1",
        **kwargs,
    )
    duplicate_pause = control_store.set_scheduler_automation_paused(
        True,
        changed_by_user_id="admin-2",
        **kwargs,
    )
    resumed = control_store.set_scheduler_automation_paused(
        False,
        changed_by_user_id="admin-2",
        **kwargs,
    )
    duplicate_resume = control_store.set_scheduler_automation_paused(
        False,
        changed_by_user_id="admin-3",
        **kwargs,
    )

    assert paused["changed"] is True
    assert paused["previous_paused"] is False
    assert paused["automation_control"]["revision"] == 1
    assert paused["automation_control"]["paused_by_user_id"] == "admin-1"
    assert paused["automation_control"]["paused_at"] == "2026-09-15T12:00:00+00:00"
    assert duplicate_pause["changed"] is False
    assert duplicate_pause["automation_control"]["revision"] == 1
    assert resumed["changed"] is True
    assert resumed["previous_paused"] is True
    assert resumed["automation_control"]["revision"] == 2
    assert resumed["automation_control"]["updated_by_user_id"] == "admin-2"
    assert resumed["automation_control"]["paused_at"] is None
    assert resumed["automation_control"]["paused_by_user_id"] is None
    assert duplicate_resume["changed"] is False
    assert duplicate_resume["automation_control"]["revision"] == 2
    assert database.insert_count == 2
    assert [row[1:4] for row in database.events] == [
        ("pause", False, True),
        ("resume", True, False),
    ]
    assert database.lock_modes == [
        ("exclusive", control_store.SCHEDULER_AUTOMATION_ADMISSION_LOCK_KEYS),
    ] * 4


def test_automatic_admission_uses_shared_lock_until_caller_finishes_spawn():
    database = FakeDatabase()
    with control_store.automatic_scheduler_start_admission(
        database_url="postgresql://test.invalid/db",
        connection_factory=database.connect,
    ) as state:
        assert state["paused"] is False
        assert database.lock_held == "shared"

    assert database.lock_held is None
    assert database.lock_modes == [
        ("shared", control_store.SCHEDULER_AUTOMATION_ADMISSION_LOCK_KEYS),
    ]


def test_storage_failure_is_bounded_and_does_not_leak_credentials():
    secret_url = "postgresql://admin:very-secret@example.test/app"

    def fail(_database_url):
        raise RuntimeError(f"could not connect to {secret_url}")

    with pytest.raises(control_store.SchedulerAutomationControlUnavailable) as exc:
        control_store.read_scheduler_automation_control(
            database_url=secret_url,
            connection_factory=fail,
        )

    assert str(exc.value) == "scheduler_automation_control_unavailable"
    assert "very-secret" not in str(exc.value)


def _patch_scheduler_post_run(monkeypatch, records):
    monkeypatch.setattr(scheduler, "write_post_run_summary_artifact", lambda _record: {})
    monkeypatch.setattr(scheduler, "write_post_run_email_outbox_artifact", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(scheduler, "deliver_post_run_email_outbox", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(scheduler, "write_notification_record_artifact", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        scheduler,
        "append_scheduler_run_record",
        lambda record, **_kwargs: records.append(record),
    )


@pytest.mark.parametrize("job_name", ["live_pipeline", "agent_discovery"])
def test_paused_automatic_jobs_exit_zero_before_run_or_child(monkeypatch, capsys, job_name):
    @contextmanager
    def paused_admission(**_kwargs):
        yield {"paused": True, "revision": 7}

    monkeypatch.setattr(scheduler, "automatic_scheduler_start_admission", paused_admission)
    monkeypatch.setattr(
        scheduler,
        "_new_scheduler_run_id",
        lambda _job: (_ for _ in ()).throw(AssertionError("run id must not be created")),
    )
    monkeypatch.setattr(
        scheduler.subprocess,
        "Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("child must not start")),
    )
    for owner in (
        "write_post_run_summary_artifact",
        "write_post_run_email_outbox_artifact",
        "deliver_post_run_email_outbox",
        "write_notification_record_artifact",
        "append_scheduler_run_record",
    ):
        monkeypatch.setattr(
            scheduler,
            owner,
            lambda *_args, _owner=owner, **_kwargs: (_ for _ in ()).throw(
                AssertionError(f"{_owner} must not run")
            ),
        )
    monkeypatch.setattr(sys, "argv", ["scheduler", "--job", job_name])

    assert scheduler.main() == 0
    output = capsys.readouterr().out
    assert f"job_name={job_name}" in output
    assert "trigger_source=external_scheduler_wrapper" in output
    assert "revision=7" in output
    assert "skipped_reason=automation_paused" in output


def test_automatic_verification_failure_exits_nonzero_before_child(monkeypatch, capsys):
    @contextmanager
    def unavailable_admission(**_kwargs):
        raise control_store.SchedulerAutomationControlUnavailable(
            "scheduler_automation_control_unavailable"
        )
        yield

    monkeypatch.setattr(scheduler, "automatic_scheduler_start_admission", unavailable_admission)
    monkeypatch.setattr(
        scheduler.subprocess,
        "Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("child must not start")),
    )
    monkeypatch.setattr(sys, "argv", ["scheduler", "--job", "agent_discovery"])

    assert scheduler.main() == 2
    error = capsys.readouterr().err
    assert "scheduler_automation_control_unavailable" in error
    assert "DATABASE_URL" not in error


def test_unpaused_automatic_spawn_occurs_under_lock_then_waits_outside(monkeypatch):
    lock_held = {"value": False}
    records = []
    process_events = []

    @contextmanager
    def admitted(**_kwargs):
        lock_held["value"] = True
        try:
            yield {"paused": False, "revision": 2}
        finally:
            lock_held["value"] = False

    class Process:
        def __init__(self, cmd, **kwargs):
            assert lock_held["value"] is True
            assert kwargs["shell"] is False
            assert kwargs["env"]["JOB_STACK_SCHEDULER_JOB_NAME"] == "agent_discovery"
            process_events.append(("spawn", list(cmd)))

        def wait(self):
            assert lock_held["value"] is False
            process_events.append(("wait", None))
            return 0

    monkeypatch.setattr(scheduler, "automatic_scheduler_start_admission", admitted)
    monkeypatch.setattr(scheduler.subprocess, "Popen", Process)
    _patch_scheduler_post_run(monkeypatch, records)
    monkeypatch.setattr(sys, "argv", ["scheduler", "--job", "agent_discovery"])

    assert scheduler.main() == 0
    assert [event[0] for event in process_events] == ["spawn", "wait"]
    assert len(records) == 1
    assert records[0]["status"] == "succeeded"
    assert records[0]["trigger_source"] == "external_scheduler_wrapper"


def test_manual_admin_bypasses_automatic_pause_admission(monkeypatch):
    records = []
    monkeypatch.setattr(
        scheduler,
        "automatic_scheduler_start_admission",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("manual must bypass gate")),
    )
    monkeypatch.setattr(
        scheduler.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
    )
    _patch_scheduler_post_run(monkeypatch, records)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scheduler",
            "--job",
            "agent_discovery",
            "--trigger-source",
            "manual_admin",
        ],
    )

    assert scheduler.main() == 0
    assert records[0]["trigger_source"] == "manual_admin"
