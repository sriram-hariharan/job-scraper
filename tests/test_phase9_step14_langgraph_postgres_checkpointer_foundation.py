import ast
from contextlib import contextmanager
from copy import deepcopy
import importlib
import os
from pathlib import Path

import pytest

from src.agents import evidence_chain_langgraph_harness as harness
from src.storage.admin_tools.durable_orchestration import (
    setup_langgraph_checkpointer as setup_tool,
)
from src.storage.durable_orchestration import langgraph_postgres


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/storage/durable_orchestration/langgraph_postgres.py"
)
SETUP_PATH = (
    ROOT
    / "src/storage/admin_tools/durable_orchestration"
    / "setup_langgraph_checkpointer.py"
)
LIVE_GATE = "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_TEST_ENABLED"
LIVE_TARGET = "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_TEST_DATABASE_URL"
RUNTIME_TARGET = "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_DATABASE_URL"
REPOSITORY_TABLES = (
    "orchestration_graph_runs",
    "orchestration_checkpoints",
    "orchestration_interrupt_requests",
    "orchestration_human_decisions",
    "orchestration_resume_authorizations",
    "orchestration_resume_consumptions",
    "orchestration_node_attempts",
    "orchestration_terminal_results",
    "orchestration_lifecycle_events",
)


class _FakeConnection:
    def __init__(self):
        self.closed = False
        self.cursor_calls = 0

    def cursor(self):
        self.cursor_calls += 1
        raise AssertionError("runtime saver construction must not execute SQL")

    def close(self):
        self.closed = True


class _CatalogCursor:
    def __init__(self, responses):
        self._responses = list(responses)
        self.closed = False
        self.executions = []

    def execute(self, statement, parameters=None):
        self.executions.append((statement, parameters))

    def fetchall(self):
        if not self._responses:
            raise AssertionError("unexpected catalog fetch")
        return self._responses.pop(0)

    def close(self):
        self.closed = True


class _CatalogConnection:
    def __init__(self, responses):
        self.cursor_instance = _CatalogCursor(responses)

    def cursor(self):
        return self.cursor_instance


def _truthy(value):
    return str(value or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


def _live_target_or_skip():
    if not _truthy(os.environ.get(LIVE_GATE)):
        pytest.skip("dedicated LangGraph PostgreSQL checkpointer gate disabled")
    target = str(os.environ.get(LIVE_TARGET) or "").strip()
    if not target:
        pytest.skip("dedicated LangGraph PostgreSQL checkpointer target missing")
    assert target != str(os.environ.get("DATABASE_URL") or "").strip()
    assert target != str(os.environ.get(RUNTIME_TARGET) or "").strip()
    return target


def _catalog_fixture(*, public_tables=(), dedicated_tables=None, migrations=None):
    dedicated = set(
        setup_tool.EXPECTED_PACKAGE_TABLES
        if dedicated_tables is None
        else dedicated_tables
    )
    columns = {}
    primary_keys = {}
    for table_name in dedicated:
        key = (setup_tool.SUPPORTED_SCHEMA, table_name)
        columns[key] = setup_tool.EXPECTED_COLUMNS[table_name]
        primary_keys[key] = setup_tool.EXPECTED_PRIMARY_KEYS[table_name]
    for table_name in public_tables:
        key = ("public", table_name)
        columns[key] = setup_tool.EXPECTED_COLUMNS[table_name]
        primary_keys[key] = setup_tool.EXPECTED_PRIMARY_KEYS[table_name]
    return {
        "schema_exists": bool(dedicated),
        "public_tables": set(public_tables),
        "dedicated_tables": dedicated,
        "columns": columns,
        "primary_keys": primary_keys,
        "migrations": tuple(
            range(len(setup_tool.PostgresSaver.MIGRATIONS))
            if migrations is None
            else migrations
        ),
    }


def _compatible_catalog_responses():
    schema = setup_tool.SUPPORTED_SCHEMA
    column_rows = []
    primary_key_rows = []
    for table_name in setup_tool.EXPECTED_PACKAGE_TABLES:
        for ordinal, column_name in enumerate(
            setup_tool.EXPECTED_COLUMNS[table_name],
            start=1,
        ):
            column_rows.append(
                {
                    "table_schema": schema,
                    "table_name": table_name,
                    "column_name": column_name,
                    "ordinal_position": ordinal,
                }
            )
        primary_key_rows.append(
            {
                "table_schema": schema,
                "table_name": table_name,
                "primary_key_columns": list(
                    setup_tool.EXPECTED_PRIMARY_KEYS[table_name]
                ),
            }
        )
    migration_rows = [
        {"v": version}
        for version in range(len(setup_tool.PostgresSaver.MIGRATIONS))
    ]
    return [
        [{"schema_name": schema}],
        column_rows,
        primary_key_rows,
        migration_rows,
    ]


def test_saver_owner_defaults_off_and_rejects_blank_target_before_connect(
    monkeypatch,
):
    calls = []
    monkeypatch.setattr(
        langgraph_postgres.psycopg,
        "connect",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(
        langgraph_postgres.LangGraphPostgresSaverError,
        match="capability_disabled",
    ):
        with langgraph_postgres.open_langgraph_postgres_saver():
            pass
    with pytest.raises(
        langgraph_postgres.LangGraphPostgresSaverError,
        match="database_url_missing",
    ):
        with langgraph_postgres.open_langgraph_postgres_saver(enabled=True):
            pass

    assert calls == []


def test_saver_owner_has_no_environment_or_database_url_fallback(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://ignored:ignored@example.invalid/ignored",
    )
    monkeypatch.setenv(
        LIVE_TARGET,
        "postgresql://ignored:ignored@example.invalid/ignored",
    )
    monkeypatch.setattr(
        langgraph_postgres.psycopg,
        "connect",
        lambda *args, **kwargs: pytest.fail("connection attempted"),
    )

    with pytest.raises(
        langgraph_postgres.LangGraphPostgresSaverError,
        match="database_url_missing",
    ):
        with langgraph_postgres.open_langgraph_postgres_connection(enabled=True):
            pass


@pytest.mark.parametrize(
    "schema",
    ["public", "src", "applylens_langgraph_checkpoint_extra", ""],
)
def test_saver_owner_accepts_only_the_fixed_dedicated_schema(
    schema,
    monkeypatch,
):
    monkeypatch.setattr(
        langgraph_postgres.psycopg,
        "connect",
        lambda *args, **kwargs: pytest.fail("connection attempted"),
    )

    with pytest.raises(
        langgraph_postgres.LangGraphPostgresSaverError,
        match="schema_unsupported",
    ):
        with langgraph_postgres.open_langgraph_postgres_connection(
            enabled=True,
            database_url="postgresql://user:secret@localhost/applylens",
            schema=schema,
        ):
            pass


@pytest.mark.parametrize(
    ("keyword", "value", "diagnostic"),
    [
        ("connect_timeout_seconds", 0, "connect_timeout_invalid"),
        ("connect_timeout_seconds", 31, "connect_timeout_invalid"),
        ("statement_timeout_ms", 0, "statement_timeout_invalid"),
        ("statement_timeout_ms", 60_001, "statement_timeout_invalid"),
        ("application_name", "", "application_name_invalid"),
        ("application_name", "x" * 64, "application_name_invalid"),
    ],
)
def test_saver_owner_bounds_timeouts_and_application_name(
    keyword,
    value,
    diagnostic,
    monkeypatch,
):
    monkeypatch.setattr(
        langgraph_postgres.psycopg,
        "connect",
        lambda *args, **kwargs: pytest.fail("connection attempted"),
    )

    with pytest.raises(
        langgraph_postgres.LangGraphPostgresSaverError,
        match=diagnostic,
    ):
        with langgraph_postgres.open_langgraph_postgres_connection(
            enabled=True,
            database_url="postgresql://user:secret@localhost/applylens",
            **{keyword: value},
        ):
            pass


def test_connection_contract_is_saver_compatible_and_ssl_is_explicit_only(
    monkeypatch,
):
    calls = []

    def fake_connect(target, **options):
        connection = _FakeConnection()
        calls.append((target, options, connection))
        return connection

    monkeypatch.setattr(langgraph_postgres.psycopg, "connect", fake_connect)
    target = "postgresql://user:secret@localhost/applylens"
    with langgraph_postgres.open_langgraph_postgres_connection(
        enabled=True,
        database_url=target,
    ):
        pass
    with langgraph_postgres.open_langgraph_postgres_connection(
        enabled=True,
        database_url=target,
        ssl_mode="require",
    ):
        pass

    assert len(calls) == 2
    first_options = calls[0][1]
    assert first_options["autocommit"] is True
    assert first_options["prepare_threshold"] == 0
    assert first_options["connect_timeout"] == 5
    assert "statement_timeout=5000" in first_options["options"]
    assert (
        "search_path=applylens_langgraph_checkpoint"
        in first_options["options"]
    )
    assert "sslmode" not in first_options
    assert calls[1][1]["sslmode"] == "require"
    assert all(connection.closed for _, _, connection in calls)


def test_import_opens_no_connection_and_module_has_no_global_pool_or_saver(
    monkeypatch,
):
    monkeypatch.setattr(
        langgraph_postgres.psycopg,
        "connect",
        lambda *args, **kwargs: pytest.fail("connection attempted during import"),
    )
    importlib.reload(langgraph_postgres)
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))

    assignments = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    assert not any(
        isinstance(value, ast.Call)
        and (
            getattr(value.func, "id", "") in {"PostgresSaver", "ConnectionPool"}
            or getattr(value.func, "attr", "") in {"connect", "from_conn_string"}
        )
        for assignment in assignments
        for value in [
            assignment.value
            if isinstance(assignment, (ast.Assign, ast.AnnAssign))
            else None
        ]
        if value is not None
    )


def test_runtime_saver_construction_performs_no_ddl(monkeypatch):
    connection = _FakeConnection()
    monkeypatch.setattr(
        langgraph_postgres.psycopg,
        "connect",
        lambda *args, **kwargs: connection,
    )

    with langgraph_postgres.open_langgraph_postgres_saver(
        enabled=True,
        database_url="postgresql://user:secret@localhost/applylens",
    ) as saver:
        assert isinstance(saver, langgraph_postgres.PostgresSaver)
        assert saver.conn is connection

    assert connection.cursor_calls == 0
    assert connection.closed is True


def test_setup_plan_performs_no_connection(monkeypatch):
    monkeypatch.setattr(
        langgraph_postgres,
        "open_langgraph_postgres_connection",
        lambda **kwargs: pytest.fail("plan attempted a connection"),
    )

    result = setup_tool.LangGraphCheckpointerSetup().plan()

    assert result.operation == "plan"
    assert result.outcome == "planned"
    assert result.schema == setup_tool.SUPPORTED_SCHEMA


def test_setup_apply_requires_its_separate_gate(monkeypatch):
    monkeypatch.setattr(
        setup_tool.LangGraphCheckpointerSetup,
        "check",
        lambda self: pytest.fail("disabled apply performed a preflight"),
    )

    result = setup_tool.LangGraphCheckpointerSetup(
        enabled=False,
        database_url="postgresql://user:secret@localhost/applylens",
    ).apply()

    assert result.operation == "apply"
    assert result.outcome == "disabled"


def test_setup_cli_never_prints_target_or_credentials(capsys):
    target = "postgresql://private_user:private_password@private.invalid/db"

    return_code = setup_tool.main(
        [
            "--apply",
            "--database-url-env",
            LIVE_TARGET,
            "--schema",
            setup_tool.SUPPORTED_SCHEMA,
        ],
        configuration={
            LIVE_TARGET: target,
            setup_tool.SETUP_CAPABILITY_NAME: "0",
        },
    )
    output = capsys.readouterr().out

    assert return_code == 1
    assert target not in output
    assert "private_user" not in output
    assert "private_password" not in output


@pytest.mark.parametrize(
    ("catalog", "outcome", "diagnostic"),
    [
        (
            _catalog_fixture(
                dedicated_tables={"checkpoints", "checkpoint_blobs"}
            ),
            "partial",
            "partial_package_schema",
        ),
        (
            _catalog_fixture(migrations=(0,)),
            "incompatible",
            "package_migration_state_invalid",
        ),
        (
            _catalog_fixture(public_tables={"checkpoints"}),
            "incompatible",
            "package_table_in_public",
        ),
    ],
)
def test_setup_fails_closed_for_partial_unexpected_or_public_package_schema(
    catalog,
    outcome,
    diagnostic,
):
    result = setup_tool._classify_catalog(catalog)

    assert result.outcome == outcome
    assert result.diagnostic_code == diagnostic


def test_setup_is_idempotent_when_package_catalog_is_compatible(monkeypatch):
    connections = []

    @contextmanager
    def fake_open_connection(**kwargs):
        connection = _CatalogConnection(_compatible_catalog_responses())
        connections.append(connection)
        yield connection

    monkeypatch.setattr(
        langgraph_postgres,
        "open_langgraph_postgres_connection",
        fake_open_connection,
    )
    monkeypatch.setattr(
        langgraph_postgres,
        "open_langgraph_postgres_saver",
        lambda **kwargs: pytest.fail("compatible setup reran package DDL"),
    )
    setup = setup_tool.LangGraphCheckpointerSetup(
        enabled=True,
        database_url="postgresql://user:secret@localhost/applylens",
    )

    first = setup.apply()
    second = setup.apply()

    assert first.outcome == second.outcome == "compatible"
    assert len(connections) == 2
    assert all(connection.cursor_instance.closed for connection in connections)


def test_foundation_introduces_no_repository_schema_or_application_integration():
    combined = (
        OWNER_PATH.read_text(encoding="utf-8")
        + SETUP_PATH.read_text(encoding="utf-8")
    )

    assert "src.app" not in combined
    assert "src.storage.durable_orchestration.repository" not in combined
    for table_name in REPOSITORY_TABLES:
        assert table_name not in combined
    assert "PostgresSaver.setup()" not in OWNER_PATH.read_text(encoding="utf-8")


def test_live_package_schema_catalog_is_compatible():
    target = _live_target_or_skip()

    with langgraph_postgres.open_langgraph_postgres_connection(
        enabled=True,
        database_url=target,
        application_name="applylens-step14-live-catalog",
    ) as connection:
        catalog = setup_tool._read_catalog(
            connection,
            schema=setup_tool.SUPPORTED_SCHEMA,
        )
    result = setup_tool._classify_catalog(catalog)

    assert result.outcome == "compatible"
    assert catalog["public_tables"] == set()


def _initial_live_graph_state():
    job = {
        "job_id": "phase9-step14-durable-pause",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "url": "https://example.test/jobs/phase9-step14",
        "intelligence": {
            "skills": {
                "required": ["Python", "SQL"],
                "preferred": ["RAG"],
                "all": ["Python", "SQL", "RAG"],
            },
            "visa_sponsorship": "unknown",
        },
        "ai_fit_score": 8,
        "priority_score": 12.5,
    }
    resume_rows = [
        {
            "resume_id": "resume-phase9-step14",
            "skills": ["Python", "SQL", "RAG"],
            "raw_text": "Built Python, SQL, and RAG systems.",
        }
    ]
    return harness._build_initial_graph_state(
        job=job,
        job_index=0,
        job_identity=harness._job_identity(job, 0),
        resume_rows=resume_rows,
        selected_resume_id="resume-phase9-step14",
        pipeline_run_id="run-phase9-step14",
        owner_user_id="owner-phase9-step14",
        context_id="context-phase9-step14",
        include_trace_payload=True,
    )


def _bounded_snapshot_config(snapshot):
    configurable = dict(snapshot.config.get("configurable") or {})
    assert set(configurable) >= {"thread_id", "checkpoint_ns", "checkpoint_id"}
    return {
        "configurable": {
            "thread_id": configurable["thread_id"],
            "checkpoint_ns": configurable["checkpoint_ns"],
            "checkpoint_id": configurable["checkpoint_id"],
        }
    }


def _package_thread_counts(connection, *, excluded_thread_id):
    counts = {}
    with connection.cursor() as cursor:
        for table_name in (
            "checkpoints",
            "checkpoint_blobs",
            "checkpoint_writes",
        ):
            cursor.execute(
                "SELECT count(*) AS row_count "
                f"FROM {table_name} WHERE thread_id <> %s",
                (excluded_thread_id,),
            )
            counts[table_name] = cursor.fetchone()["row_count"]
    return counts


def _exact_package_thread_counts(connection, *, thread_id):
    counts = {}
    with connection.cursor() as cursor:
        for table_name in (
            "checkpoints",
            "checkpoint_blobs",
            "checkpoint_writes",
        ):
            cursor.execute(
                "SELECT count(*) AS row_count "
                f"FROM {table_name} WHERE thread_id = %s",
                (thread_id,),
            )
            counts[table_name] = cursor.fetchone()["row_count"]
    return counts


def _repository_graph_counts(connection, *, graph_invocation_id):
    counts = {}
    with connection.cursor() as cursor:
        for table_name in REPOSITORY_TABLES:
            cursor.execute(
                "SELECT count(*) AS row_count "
                f"FROM public.{table_name} WHERE graph_invocation_id = %s",
                (graph_invocation_id,),
            )
            counts[table_name] = cursor.fetchone()["row_count"]
    return counts


def _assert_paused_snapshot(snapshot):
    assert tuple(snapshot.next) == ("finalize",)
    values = dict(snapshot.values)
    artifacts = dict(values["artifacts"])
    assert list(values["ordered_node_keys"]) == list(harness.ORDERED_AGENT_KEYS)
    for artifact_key in harness.ARTIFACT_KEYS_BY_AGENT.values():
        assert artifact_key in artifacts
    assert "evidence_chain_bundle" not in values
    assert "trace_payload" not in values
    assert "agent_evidence_chain_bundle" not in artifacts
    assert "agent_evidence_chain_trace_payload" not in artifacts


def test_live_durable_operator_review_pause_reopens_without_node_rerun(
    monkeypatch,
):
    target = _live_target_or_skip()
    initial_state = _initial_live_graph_state()
    graph_identity = harness._build_checkpoint_identity(initial_state)
    thread_id = graph_identity.graph_invocation_id
    base_config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "",
            "applylens_checkpoint_namespace": (
                harness.LANGGRAPH_OPERATOR_REVIEW_PAUSE_RESUME_CHECKPOINT_NAMESPACE
            ),
        }
    }
    node_names = (
        "_jd_intelligence_node",
        "_resume_match_node",
        "_critic_node",
        "_job_prioritization_node",
        "_tailoring_decision_node",
        "_operator_review_node",
        "_finalize_node",
    )
    calls = {name: 0 for name in node_names}
    for name in node_names:
        original = getattr(harness, name)

        def counted(state, *, _name=name, _original=original):
            calls[_name] += 1
            return _original(state)

        monkeypatch.setattr(harness, name, counted)

    saved_config = None
    unrelated_before = None
    repository_before = None
    try:
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=target,
            application_name="applylens-step14-live-initial",
        ) as saver:
            saver.delete_thread(thread_id)
            unrelated_before = _package_thread_counts(
                saver.conn,
                excluded_thread_id=thread_id,
            )
            repository_before = _repository_graph_counts(
                saver.conn,
                graph_invocation_id=thread_id,
            )
            graph = harness._compile_operator_review_pause_resume_graph(saver)
            graph.invoke(deepcopy(initial_state), deepcopy(base_config))
            snapshot = graph.get_state(deepcopy(base_config))
            _assert_paused_snapshot(snapshot)
            saved_config = _bounded_snapshot_config(snapshot)
            first_connection = saver.conn
        assert first_connection.closed
        del snapshot, graph, saver

        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=target,
            application_name="applylens-step14-live-reopen",
        ) as reopened_saver:
            reopened_graph = harness._compile_operator_review_pause_resume_graph(
                reopened_saver
            )
            reopened_snapshot = reopened_graph.get_state(
                deepcopy(saved_config)
            )
            _assert_paused_snapshot(reopened_snapshot)
            assert _package_thread_counts(
                reopened_saver.conn,
                excluded_thread_id=thread_id,
            ) == unrelated_before
            assert _repository_graph_counts(
                reopened_saver.conn,
                graph_invocation_id=thread_id,
            ) == repository_before
            reopened_connection = reopened_saver.conn
        assert reopened_connection.closed
        del reopened_snapshot, reopened_graph, reopened_saver

        for name in node_names[:-1]:
            assert calls[name] == 1
        assert calls["_finalize_node"] == 0
    finally:
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=target,
            application_name="applylens-step14-live-cleanup",
        ) as cleanup_saver:
            cleanup_saver.delete_thread(thread_id)
            assert _exact_package_thread_counts(
                cleanup_saver.conn,
                thread_id=thread_id,
            ) == {
                "checkpoints": 0,
                "checkpoint_blobs": 0,
                "checkpoint_writes": 0,
            }
            if unrelated_before is not None:
                assert _package_thread_counts(
                    cleanup_saver.conn,
                    excluded_thread_id=thread_id,
                ) == unrelated_before
            if repository_before is not None:
                assert _repository_graph_counts(
                    cleanup_saver.conn,
                    graph_invocation_id=thread_id,
                ) == repository_before
