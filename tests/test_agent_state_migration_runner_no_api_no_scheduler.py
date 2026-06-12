from copy import deepcopy
import importlib
from pathlib import Path

from src.storage.agent_state import migration_runner


SCHEMA_PATH = Path("src/storage/agent_state/schema.sql")


class FakeCursor:
    def __init__(self):
        self.statements = []
        self.commit_calls = 0

    def execute(self, statement):
        self.statements.append(statement)

    def commit(self):
        self.commit_calls += 1


def _schema_sql():
    return SCHEMA_PATH.read_text()


def _assert_safety_flags_false(payload):
    assert payload["did_create_connection"] is False
    assert payload["did_commit_transaction"] is False
    assert payload["did_schedule_background_work"] is False
    assert payload["did_execute_scheduler"] is False
    assert payload["did_execute_reporting_job"] is False
    assert payload["did_export_files"] is False
    assert payload["did_execute_application"] is False
    assert payload["did_submit_application"] is False
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False


def test_schema_scope_validation_passes_for_current_agent_state_schema():
    plan = migration_runner.build_agent_state_migration_plan(_schema_sql())

    assert plan["migration_scope"] == "agent_state"
    assert plan["target_tables"] == ["agent_runs", "agent_steps"]
    assert plan["statement_count"] == len(plan["statements"])
    assert plan["statement_count"] == 9
    assert plan["did_run_migration"] is False
    assert plan["statements"][0].startswith("CREATE TABLE IF NOT EXISTS agent_runs")
    assert "CREATE TABLE IF NOT EXISTS agent_steps" in plan["statements"][4]
    _assert_safety_flags_false(plan)


def test_forbidden_scope_terms_are_rejected():
    schema = _schema_sql()

    for forbidden in [
        "approval_requests",
        "agentic_approvals",
        "application_execution",
        "application_submissions",
    ]:
        unsafe_schema = schema + f"\nCREATE TABLE IF NOT EXISTS {forbidden} (id TEXT);"
        try:
            migration_runner.build_agent_state_migration_plan(unsafe_schema)
        except ValueError as exc:
            assert forbidden in str(exc)
        else:
            raise AssertionError(f"{forbidden} should be rejected")


def test_migration_plan_is_deterministic_and_preserves_input_text():
    schema = _schema_sql()
    original = deepcopy(schema)

    first = migration_runner.build_agent_state_migration_plan(schema)
    second = migration_runner.build_agent_state_migration_plan(schema)

    assert schema == original
    assert first == second
    assert first["operation"] == "build_agent_state_migration_plan"
    assert first["did_run_migration"] is False
    _assert_safety_flags_false(first)


def test_run_agent_state_migration_executes_only_expected_statements_on_injected_cursor():
    cursor = FakeCursor()
    schema = _schema_sql()
    plan = migration_runner.build_agent_state_migration_plan(schema)

    result = migration_runner.run_agent_state_migration(cursor, schema)

    assert cursor.statements == plan["statements"]
    assert cursor.commit_calls == 0
    assert result["operation"] == "run_agent_state_migration"
    assert result["migration_scope"] == "agent_state"
    assert result["target_tables"] == ["agent_runs", "agent_steps"]
    assert result["did_run_migration"] is True
    assert result["executed_statement_count"] == plan["statement_count"]
    assert result["statement_count"] == plan["statement_count"]
    _assert_safety_flags_false(result)


def test_import_has_no_side_effects_and_no_connection_or_commit_markers():
    reloaded = importlib.reload(migration_runner)
    plan = reloaded.build_agent_state_migration_plan(_schema_sql())
    source = Path("src/storage/agent_state/migration_runner.py").read_text()

    assert plan["did_create_connection"] is False
    assert plan["did_commit_transaction"] is False
    forbidden_tokens = [
        "connect(",
        ".commit(",
        "commit_transaction(",
        "Path(",
        ".read_text(",
        "FileResponse",
        "StreamingResponse",
        "open(",
        "write_text",
        "write_bytes",
        "send_file",
        "subprocess",
        "background_tasks.add_task",
        "Thread",
        "Process",
        "scheduler_execution(",
        "reporting_job_execution(",
        "application_execution(",
        "application_submission(",
        "export_writer",
        "metrics_emitter",
        "logging_emitter",
        "audit_writer",
        "datetime.",
        "utcnow",
        "now(",
        "uuid",
        "random",
        "src.app.api",
        "agentic_review.js",
        "workflow_runner",
        "application_execution_queue",
    ]
    for token in forbidden_tokens:
        assert token not in source
