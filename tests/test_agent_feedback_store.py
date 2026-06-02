import inspect

import pytest

from src.storage.agent_feedback import store
from src.storage.agent_feedback.store import (
    agent_feedback_contract_health_payload,
    agent_feedback_event_db_row,
    agent_feedback_schema_sql_text,
    list_agent_feedback_events,
    record_agent_feedback_event,
    summarize_agent_feedback_events,
)


def _valid_record(**overrides):
    record = {
        "owner_user_id": "user_1",
        "pipeline_run_id": "run_1",
        "context_id": "ctx_1",
        "agent_run_id": "agent_run_1",
        "agent_step_id": "agent_step_1",
        "target_type": "operator_review_lane",
        "target_id": "job_1",
        "event_type": "operator_lane_overridden",
        "payload_json": {"from": "review_before_action", "to": "direct_apply"},
        "source": "api",
        "created_at": "2026-06-02T12:00:00+00:00",
    }
    record.update(overrides)
    return record


def test_agent_feedback_schema_contains_required_table_and_columns():
    sql = agent_feedback_schema_sql_text()

    assert "CREATE TABLE IF NOT EXISTS agent_feedback_events" in sql
    for column in [
        "event_id",
        "owner_user_id",
        "pipeline_run_id",
        "context_id",
        "agent_run_id",
        "agent_step_id",
        "target_type",
        "target_id",
        "event_type",
        "payload_json",
        "source",
        "created_at",
    ]:
        assert column in sql

    health = agent_feedback_contract_health_payload()
    assert health["all_checks_pass"] is True
    assert "suggestion_accepted" in health["event_types"]
    assert "operator_review_lane" in health["target_types"]


def test_valid_feedback_event_can_be_recorded_print_only():
    payload = record_agent_feedback_event(
        record=_valid_record(),
        print_only=True,
        ensure_schema=False,
    )

    assert payload["ok"] is True
    assert payload["recorded"] is True
    assert payload["table_name"] == "agent_feedback_events"
    assert payload["event"]["owner_user_id"] == "user_1"
    assert payload["event"]["event_id"].startswith("agent_feedback_")
    assert "INSERT INTO agent_feedback_events" in payload["sql"]
    assert "'{\"from\":\"review_before_action\",\"to\":\"direct_apply\"}'::jsonb" in payload["sql"]


def test_invalid_event_type_rejected():
    with pytest.raises(ValueError, match="Unsupported agent feedback event_type"):
        agent_feedback_event_db_row(_valid_record(event_type="score_adjusted"))


def test_invalid_target_type_rejected():
    with pytest.raises(ValueError, match="Unsupported agent feedback target_type"):
        agent_feedback_event_db_row(_valid_record(target_type="ranking_weight"))


def test_payload_json_must_be_object():
    with pytest.raises(ValueError, match="payload_json must be a JSON object"):
        agent_feedback_event_db_row(_valid_record(payload_json=["not", "an", "object"]))


def test_listing_is_scoped_by_owner_user_id_print_only():
    payload = list_agent_feedback_events(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        print_only=True,
        ensure_schema=False,
    )

    assert payload["ok"] is True
    assert "WHERE owner_user_id = 'user_1'" in payload["sql"]
    assert "pipeline_run_id = 'run_1'" in payload["sql"]
    assert "owner_user_id = 'user_2'" not in payload["sql"]


def test_listing_supports_feedback_filters_and_bounds_limit_print_only():
    payload = list_agent_feedback_events(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        context_id="ctx_1",
        target_type="pipeline_run_job",
        event_type="job_saved",
        limit=5000,
        print_only=True,
        ensure_schema=False,
    )

    assert "pipeline_run_id = 'run_1'" in payload["sql"]
    assert "context_id = 'ctx_1'" in payload["sql"]
    assert "target_type = 'pipeline_run_job'" in payload["sql"]
    assert "event_type = 'job_saved'" in payload["sql"]
    assert "LIMIT 1000" in payload["sql"]


def test_summary_counts_event_types_correctly(monkeypatch):
    def fake_list_agent_feedback_events(**kwargs):
        return {
            "ok": True,
            "events": [
                {
                    "owner_user_id": "user_1",
                    "event_type": "suggestion_accepted",
                    "target_type": "tailoring_suggestion",
                    "created_at": "2026-06-02T12:00:00+00:00",
                },
                {
                    "owner_user_id": "user_1",
                    "event_type": "suggestion_accepted",
                    "target_type": "tailoring_suggestion",
                    "created_at": "2026-06-02T12:01:00+00:00",
                },
                {
                    "owner_user_id": "user_1",
                    "event_type": "job_saved",
                    "target_type": "pipeline_run_job",
                    "created_at": "2026-06-02T12:02:00+00:00",
                },
            ],
        }

    monkeypatch.setattr(store, "list_agent_feedback_events", fake_list_agent_feedback_events)

    payload = summarize_agent_feedback_events(owner_user_id="user_1")

    assert payload["summary"] == {
        "total_events": 3,
        "event_type_counts": {"job_saved": 1, "suggestion_accepted": 2},
        "target_type_counts": {"pipeline_run_job": 1, "tailoring_suggestion": 2},
        "latest_event_at": "2026-06-02T12:02:00+00:00",
    }


def test_feedback_store_uses_dbapi_and_psql_fallback():
    source = inspect.getsource(store._run_postgres_json_query)

    assert "cursor.execute(sql)" in source
    assert "subprocess.run" in source
    assert "driver_name = \"psycopg\"" in source


def test_feedback_not_imported_into_scoring_queue_or_tailoring_decision_modules():
    for module in [
        "src.pipeline.job_ranker",
        "src.pipeline.application_scorer",
        "src.tailoring.selection",
        "src.tailoring.planner",
        "src.agents.tailoring_decision_agent",
        "src.agents.job_prioritization_agent",
    ]:
        source = inspect.getsource(__import__(module, fromlist=["*"]))
        assert "agent_feedback" not in source
