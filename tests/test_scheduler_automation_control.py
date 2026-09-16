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
        self.snapshot_read_count = 0
        self.fail_on_insert_number = None
        self.connections = []

    def add_event(self, revision, job_name, paused, actor="admin-history"):
        row = (
            revision,
            "pause" if paused else "resume",
            not paused,
            paused,
            datetime(2026, 9, 15, 12, revision % 60, tzinfo=timezone.utc),
            actor,
            job_name,
        )
        self.events.append(row)
        self.events.sort(key=lambda event: event[0])
        self.next_revision = max(self.next_revision, revision + 1)
        return row

    def connect(self, _database_url):
        connection = FakeConnection(self)
        self.connections.append(connection)
        return connection


class FakeConnection:
    def __init__(self, database):
        self.database = database
        self.event_snapshot = list(database.events)
        self.revision_snapshot = database.next_revision
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
        self.database.events = list(self.event_snapshot)
        self.database.next_revision = self.revision_snapshot
        self.database.lock_held = None

    def close(self):
        self.closed = True
        self.database.lock_held = None


class FakeCursor:
    def __init__(self, database):
        self.database = database
        self.row = None
        self.rows = []
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
        if normalized.startswith("WITH supported_jobs"):
            self.database.snapshot_read_count += 1
            self.rows = []
            for job_name in control_store.SCHEDULER_AUTOMATION_AFFECTED_JOBS:
                matching = [
                    event for event in self.database.events
                    if event[6] is None or event[6] == job_name
                ]
                event = matching[-1] if matching else None
                self.rows.append(
                    (job_name,) + event
                    if event is not None
                    else (job_name, None, None, None, None, None, None, None)
                )
            return
        if normalized.startswith("SELECT revision"):
            job_name = params[0]
            matching = [
                event for event in self.database.events
                if event[6] is None or event[6] == job_name
            ]
            self.row = matching[-1] if matching else None
            return
        if normalized.startswith("INSERT INTO scheduler_automation_control_events"):
            if self.database.fail_on_insert_number == self.database.insert_count + 1:
                raise RuntimeError("simulated insert failure containing secret detail")
            job_name, action, prior_paused, resulting_paused, actor = params
            self.row = (
                self.database.next_revision,
                action,
                prior_paused,
                resulting_paused,
                datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc),
                actor,
                job_name,
            )
            self.database.next_revision += 1
            self.database.insert_count += 1
            self.database.events.append(self.row)
            return
        raise AssertionError(f"Unexpected SQL: {normalized}")

    def fetchone(self):
        return self.row

    def fetchall(self):
        return list(self.rows)

    def close(self):
        self.closed = True


def test_default_state_is_unpaused_and_finite():
    database = FakeDatabase()
    state = control_store.read_scheduler_automation_control(
        database_url="postgresql://test.invalid/db",
        connection_factory=database.connect,
    )

    assert state == {
        "aggregate_state": "running",
        "manual_admin_runs_allowed": True,
        "affected_jobs": ["agent_discovery", "live_pipeline"],
        "jobs": {
            job_name: {
                "job_name": job_name,
                "paused": False,
                "revision": 0,
                "updated_at": None,
                "updated_by_user_id": None,
                "paused_at": None,
                "paused_by_user_id": None,
                "effective_scope": "default",
            }
            for job_name in ("agent_discovery", "live_pipeline")
        },
        "paused": False,
        "revision": 0,
        "updated_at": None,
        "updated_by_user_id": None,
        "paused_at": None,
        "paused_by_user_id": None,
    }
    assert database.snapshot_read_count == 1


@pytest.mark.parametrize("job_name", ["live_pipeline", "agent_discovery"])
def test_per_job_pause_resume_and_duplicates_are_independent(job_name):
    database = FakeDatabase()
    kwargs = {
        "database_url": "postgresql://test.invalid/db",
        "connection_factory": database.connect,
    }

    other_job = "agent_discovery" if job_name == "live_pipeline" else "live_pipeline"
    paused = control_store.set_scheduler_job_automation_paused(
        job_name,
        True,
        changed_by_user_id="admin-1",
        **kwargs,
    )
    duplicate_pause = control_store.set_scheduler_job_automation_paused(
        job_name,
        True,
        changed_by_user_id="admin-2",
        **kwargs,
    )
    resumed = control_store.set_scheduler_job_automation_paused(
        job_name,
        False,
        changed_by_user_id="admin-2",
        **kwargs,
    )
    duplicate_resume = control_store.set_scheduler_job_automation_paused(
        job_name,
        False,
        changed_by_user_id="admin-3",
        **kwargs,
    )

    assert paused["changed"] is True
    assert paused["previous_paused"] is False
    assert paused["job_name"] == job_name
    assert paused["automation_control"]["aggregate_state"] == "partially_paused"
    assert paused["automation_control"]["jobs"][job_name]["revision"] == 1
    assert paused["automation_control"]["jobs"][job_name]["paused_by_user_id"] == "admin-1"
    assert paused["automation_control"]["jobs"][other_job]["paused"] is False
    assert duplicate_pause["changed"] is False
    assert duplicate_pause["automation_control"]["jobs"][job_name]["revision"] == 1
    assert resumed["changed"] is True
    assert resumed["previous_paused"] is True
    assert resumed["automation_control"]["aggregate_state"] == "running"
    assert resumed["automation_control"]["jobs"][job_name]["revision"] == 2
    assert resumed["automation_control"]["jobs"][job_name]["updated_by_user_id"] == "admin-2"
    assert duplicate_resume["changed"] is False
    assert duplicate_resume["automation_control"]["revision"] == 2
    assert database.insert_count == 2
    assert [(row[6], *row[1:4]) for row in database.events] == [
        (job_name, "pause", False, True),
        (job_name, "resume", True, False),
    ]
    assert database.lock_modes == [
        ("exclusive", control_store.SCHEDULER_AUTOMATION_ADMISSION_LOCK_KEYS),
    ] * 4


def test_historical_global_and_named_events_use_newest_matching_revision():
    database = FakeDatabase()
    database.add_event(10, None, True)
    database.add_event(11, "live_pipeline", False)
    database.add_event(12, None, False)
    database.add_event(13, "agent_discovery", True)

    state = control_store.read_scheduler_automation_control(
        database_url="postgresql://test.invalid/db",
        connection_factory=database.connect,
    )

    assert state["aggregate_state"] == "partially_paused"
    assert state["jobs"]["live_pipeline"]["paused"] is False
    assert state["jobs"]["live_pipeline"]["revision"] == 12
    assert state["jobs"]["live_pipeline"]["effective_scope"] == "global"
    assert state["jobs"]["agent_discovery"]["paused"] is True
    assert state["jobs"]["agent_discovery"]["revision"] == 13
    assert state["jobs"]["agent_discovery"]["effective_scope"] == "job"
    assert state["paused"] is False
    assert state["revision"] == 13
    assert state["paused_at"] is None


def test_legacy_global_pause_and_resume_append_named_events_atomically():
    database = FakeDatabase()
    kwargs = {
        "database_url": "postgresql://test.invalid/db",
        "connection_factory": database.connect,
    }

    paused = control_store.set_scheduler_automation_paused(
        True, changed_by_user_id="admin-1", **kwargs,
    )
    duplicate = control_store.set_scheduler_automation_paused(
        True, changed_by_user_id="admin-2", **kwargs,
    )
    resumed = control_store.set_scheduler_automation_paused(
        False, changed_by_user_id="admin-3", **kwargs,
    )

    assert paused["automation_control"]["aggregate_state"] == "paused"
    assert paused["automation_control"]["paused"] is True
    assert duplicate["changed"] is False
    assert resumed["automation_control"]["aggregate_state"] == "running"
    assert [(row[6], row[1]) for row in database.events] == [
        ("agent_discovery", "pause"),
        ("live_pipeline", "pause"),
        ("agent_discovery", "resume"),
        ("live_pipeline", "resume"),
    ]
    assert all(row[6] is not None for row in database.events)


def test_bulk_transition_rolls_back_atomically_and_failure_is_bounded():
    database = FakeDatabase()
    database.fail_on_insert_number = 2

    with pytest.raises(control_store.SchedulerAutomationControlUnavailable) as exc:
        control_store.set_scheduler_automation_paused(
            True,
            changed_by_user_id="admin-1",
            database_url="postgresql://test.invalid/db",
            connection_factory=database.connect,
        )

    assert str(exc.value) == "scheduler_automation_control_unavailable"
    assert database.events == []
    assert database.connections[-1].rollbacks == 1
    assert "secret" not in str(exc.value)
    assert "MAX(revision)" not in control_store._INSERT_EVENT_SQL.upper()


def test_unsupported_job_is_rejected_before_connection_or_mutation():
    called = False

    def connect(_database_url):
        nonlocal called
        called = True
        raise AssertionError("connection must not be opened")

    with pytest.raises(ValueError, match="Unsupported scheduler job name"):
        control_store.set_scheduler_job_automation_paused(
            "unknown",
            True,
            changed_by_user_id="admin-1",
            database_url="postgresql://test.invalid/db",
            connection_factory=connect,
        )
    assert called is False


def test_automatic_admission_uses_shared_lock_until_caller_finishes_spawn():
    database = FakeDatabase()
    with control_store.automatic_scheduler_start_admission(
        job_name="live_pipeline",
        database_url="postgresql://test.invalid/db",
        connection_factory=database.connect,
    ) as state:
        assert state["paused"] is False
        assert database.lock_held == "shared"

    assert database.lock_held is None
    assert database.lock_modes == [
        ("shared", control_store.SCHEDULER_AUTOMATION_ADMISSION_LOCK_KEYS),
    ]


def test_automatic_admission_reads_only_the_selected_job_state():
    database = FakeDatabase()
    control_store.set_scheduler_job_automation_paused(
        "live_pipeline",
        True,
        changed_by_user_id="admin-1",
        database_url="postgresql://test.invalid/db",
        connection_factory=database.connect,
    )

    with control_store.automatic_scheduler_start_admission(
        job_name="live_pipeline",
        database_url="postgresql://test.invalid/db",
        connection_factory=database.connect,
    ) as live_state:
        assert live_state["paused"] is True
    with control_store.automatic_scheduler_start_admission(
        job_name="agent_discovery",
        database_url="postgresql://test.invalid/db",
        connection_factory=database.connect,
    ) as discovery_state:
        assert discovery_state["paused"] is False


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
    def paused_admission(**kwargs):
        assert kwargs["job_name"] == job_name
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
    def admitted(**kwargs):
        assert kwargs["job_name"] == "agent_discovery"
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
