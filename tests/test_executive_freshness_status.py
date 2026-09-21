from datetime import datetime, timedelta, timezone

from src.app import services
from src.storage.scheduler import read_postgres


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)


def _shared_run(hours_ago: int = 1):
    return {"run": {"run_id": "global-run", "finished_at": (NOW - timedelta(hours=hours_ago)).isoformat()}}


def test_scheduler_freshness_query_is_bounded_to_successful_scheduled_global_live_pipeline():
    sql = read_postgres._build_latest_successful_global_live_pipeline_sql()
    assert "job_name = 'live_pipeline'" in sql
    assert "status = 'succeeded'" in sql
    assert "trigger_source = 'external_scheduler_wrapper'" in sql
    assert "ORDER BY finished_at DESC" in sql
    for private_field in ("command_text", "options_json", "error_text", "host"):
        assert private_field not in sql


def test_freshness_boundaries_are_timezone_aware_and_deterministic():
    shared_fresh = services._executive_freshness_fact(
        NOW - timedelta(hours=12), now=NOW, fresh_for=timedelta(hours=12), missing_status="unavailable"
    )
    shared_stale = services._executive_freshness_fact(
        NOW - timedelta(hours=12, seconds=1), now=NOW, fresh_for=timedelta(hours=12), missing_status="unavailable"
    )
    personal_fresh = services._executive_freshness_fact(
        NOW - timedelta(hours=24), now=NOW, fresh_for=timedelta(hours=24), aging_for=timedelta(days=7), missing_status="not_generated"
    )
    personal_aging = services._executive_freshness_fact(
        NOW - timedelta(days=7), now=NOW, fresh_for=timedelta(hours=24), aging_for=timedelta(days=7), missing_status="not_generated"
    )
    personal_stale = services._executive_freshness_fact(
        NOW - timedelta(days=7, seconds=1), now=NOW, fresh_for=timedelta(hours=24), aging_for=timedelta(days=7), missing_status="not_generated"
    )

    assert shared_fresh["status"] == "fresh"
    assert shared_stale["status"] == "stale"
    assert personal_fresh["status"] == "fresh"
    assert personal_aging["status"] == "aging"
    assert personal_stale["status"] == "stale"
    assert personal_stale["completed_at"].endswith("Z")


def test_personalized_freshness_is_owner_scoped_and_ignores_newer_failed_runs(monkeypatch):
    calls = []

    monkeypatch.setattr(services, "get_latest_successful_global_live_pipeline_postgres_payload", lambda **_: _shared_run())

    def get_runs(**kwargs):
        calls.append(kwargs)
        owner = kwargs["owner_user_id"]
        if owner == "owner-a":
            # This represents the older successful snapshot; a newer failed run
            # is excluded by the required status filter.
            return {"rows": [{"run_id": "owner-a-success", "status": "succeeded", "completed_at": (NOW - timedelta(days=2)).isoformat()}]}
        return {"rows": []}

    monkeypatch.setattr(services, "get_user_pipeline_runs_postgres_payload", get_runs)
    owner_a = services.executive_freshness_payload(owner_user_id="owner-a", now=NOW)
    owner_b = services.executive_freshness_payload(owner_user_id="owner-b", now=NOW)

    assert owner_a["personalized"] == {
        "completed_at": "2026-09-16T12:00:00Z",
        "age_seconds": 172800,
        "status": "aging",
        "run_id": "owner-a-success",
    }
    assert owner_b["personalized"] == {
        "completed_at": None,
        "age_seconds": None,
        "status": "not_generated",
        "run_id": None,
    }
    assert [call["owner_user_id"] for call in calls] == ["owner-a", "owner-b"]
    assert all(call["status"] == "succeeded" and call["limit"] == 1 for call in calls)


def test_freshness_read_failures_degrade_without_raising(monkeypatch):
    def fail(**_kwargs):
        raise SystemExit("database unavailable")

    monkeypatch.setattr(services, "get_latest_successful_global_live_pipeline_postgres_payload", fail)
    monkeypatch.setattr(services, "get_user_pipeline_runs_postgres_payload", fail)

    payload = services.executive_freshness_payload(owner_user_id="owner-a", now=NOW)
    assert payload["shared_jobs"] == {"updated_at": None, "age_seconds": None, "status": "unavailable"}
    assert payload["personalized"] == {
        "completed_at": None,
        "age_seconds": None,
        "status": "not_generated",
        "run_id": None,
    }


def test_artifact_snapshot_is_the_personalized_freshness_authority(monkeypatch):
    monkeypatch.setattr(services, "get_latest_successful_global_live_pipeline_postgres_payload", lambda **_: _shared_run(13))
    monkeypatch.setattr(
        services,
        "get_user_pipeline_runs_postgres_payload",
        lambda **_: (_ for _ in ()).throw(AssertionError("artifact-backed status must not select another run")),
    )
    artifact_context = {
        "run": {
            "run_id": "snapshot-run",
            "status": "succeeded",
            "completed_at": (NOW - timedelta(hours=4)).isoformat(),
        }
    }
    payload = services.executive_freshness_payload(
        owner_user_id="owner-a", artifact_context=artifact_context, now=NOW
    )
    assert payload["shared_jobs"]["status"] == "stale"
    assert payload["personalized"]["status"] == "fresh"
    assert payload["personalized"]["run_id"] == "snapshot-run"
