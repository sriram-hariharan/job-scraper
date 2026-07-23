import ast
from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from src.storage.admin_tools.durable_orchestration import apply_schema


ROOT = Path(__file__).resolve().parents[1]
EXECUTOR_PATH = (
    ROOT
    / "src/storage/admin_tools/durable_orchestration/apply_schema.py"
)
SCHEMA_PATH = ROOT / "src/storage/durable_orchestration/schema.sql"
STORE_PATH = ROOT / "src/storage/durable_orchestration/store.py"
REPOSITORY_PATH = ROOT / "src/storage/durable_orchestration/repository.py"
HARNESS_PATH = ROOT / "src/agents/evidence_chain_langgraph_harness.py"
TARGET = "postgresql://schema-user:secret@example.invalid/durable"


class FakeRunner:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((list(command), dict(kwargs)))
        if not self.responses:
            raise AssertionError("unexpected subprocess invocation")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def _process(*, returncode=0, stdout="", stderr=""):
    return SimpleNamespace(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _compatible_rows():
    rows = []
    for name in apply_schema._EXPECTED_TABLES:
        contract = apply_schema._TABLE_CONTRACTS[name]
        rows.append(
            {
                "object_name": name,
                "schema_name": "public",
                "relkind": "r",
                "columns": list(contract["columns"]),
                "column_types": dict(contract["column_types"]),
                "primary_key_columns": list(contract["primary_key"]),
                "constraint_names": list(contract["constraint_names"]),
                "constraint_definitions": list(
                    contract["definition_fragments"]
                ),
                "index_names": list(contract["index_names"]),
            }
        )
    return rows


def _catalog_output(rows):
    return "".join(
        json.dumps(row, sort_keys=True) + "\n"
        for row in rows
    )


def _postgres18_sized_catalog_output():
    rows = _compatible_rows()
    for index, row in enumerate(rows):
        row["constraint_definitions"].append(
            "CHECK (postgres18_catalog_shape_"
            + str(index)
            + "_"
            + ("x" * 3_600)
            + ")"
        )
    output = _catalog_output(rows)
    assert len(output) > apply_schema.MAX_CAPTURED_OUTPUT_CHARS
    assert len(output) <= apply_schema.MAX_CATALOG_OUTPUT_CHARS
    assert all(
        len(line) <= apply_schema.MAX_CATALOG_RECORD_CHARS
        for line in output.splitlines()
    )
    return output


def _executor(runner, *, enabled=True):
    return apply_schema.DurableOrchestrationSchemaExecutor(
        enabled=enabled,
        runner=runner,
    )


def test_module_import_is_side_effect_free_and_has_no_database_dependency():
    source = EXECUTOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert not {
        "psycopg",
        "psycopg2",
        "asyncpg",
        "sqlalchemy",
        "alembic",
        "langgraph",
    } & imported
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {
            "main",
            "DurableOrchestrationSchemaExecutor",
        }
        for node in tree.body
    )
    assert apply_schema.CAPABILITY_NAME == (
        "APPLYLENS_DURABLE_ORCHESTRATION_SCHEMA_EXECUTION_ENABLED"
    )


@pytest.mark.parametrize("operation", ["plan", "check", "apply"])
def test_capability_defaults_off_before_schema_or_subprocess(
    operation,
    monkeypatch,
):
    runner = FakeRunner()
    executor = _executor(runner, enabled=False)

    def prohibited_schema_read(*args, **kwargs):
        raise AssertionError("disabled operation read schema")

    monkeypatch.setattr(
        apply_schema,
        "_load_schema_artifact",
        prohibited_schema_read,
    )
    if operation == "plan":
        result = executor.plan()
    elif operation == "check":
        result = executor.check(database_url=TARGET)
    else:
        result = executor.apply(database_url=TARGET)

    assert result.outcome == "disabled"
    assert result.diagnostic_code == "capability_disabled"
    assert runner.calls == []


def test_cli_never_falls_back_to_generic_database_url(capsys):
    runner = FakeRunner()
    result_code = apply_schema.main(
        ["--check"],
        configuration={
            apply_schema.CAPABILITY_NAME: "true",
            "DATABASE_URL": TARGET,
        },
        runner=runner,
    )

    assert result_code == 1
    assert runner.calls == []
    output = capsys.readouterr().out
    assert "dedicated_target_missing" in output
    assert TARGET not in output


@pytest.mark.parametrize("operation", ["check", "apply"])
def test_missing_dedicated_target_fails_before_psql(operation):
    runner = FakeRunner()
    executor = _executor(runner)

    result = getattr(executor, operation)(database_url="")

    assert result.outcome == "unavailable"
    assert result.diagnostic_code == "dedicated_target_missing"
    assert runner.calls == []


def test_help_reads_no_configuration_and_performs_no_inspection(capsys):
    class ProhibitedConfiguration:
        def get(self, key, default=None):
            raise AssertionError("help inspected configuration")

    runner = FakeRunner()
    with pytest.raises(SystemExit) as captured:
        apply_schema.main(
            ["--help"],
            configuration=ProhibitedConfiguration(),
            runner=runner,
        )

    assert captured.value.code == 0
    assert runner.calls == []
    assert "--plan" in capsys.readouterr().out


def test_cli_requires_one_explicit_operation_without_defaulting_to_apply():
    with pytest.raises(SystemExit) as captured:
        apply_schema.main([], configuration={})

    assert captured.value.code != 0


def test_plan_reads_exact_schema_and_computes_sha256_without_psql():
    runner = FakeRunner()
    result = _executor(runner).plan()

    assert result.outcome == "planned"
    assert result.schema_contract_version == (
        "durable-orchestration-schema-v1"
    )
    assert result.schema_sha256 == sha256(SCHEMA_PATH.read_bytes()).hexdigest()
    assert result.object_count == 9
    assert result.compatibility == "not_inspected"
    assert runner.calls == []
    with pytest.raises(FrozenInstanceError):
        result.outcome = "applied"


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        (b"", "schema_artifact_empty"),
        (b"SELECT 1;\n", "schema_artifact_contract_incomplete"),
        (b"\xff", "schema_artifact_unreadable"),
    ],
)
def test_schema_artifact_rejects_empty_incomplete_or_invalid_encoding(
    tmp_path,
    content,
    reason,
):
    path = tmp_path / "schema.sql"
    path.write_bytes(content)

    with pytest.raises(ValueError, match=reason):
        apply_schema._load_schema_artifact(path)


def test_schema_artifact_rejects_missing_file_and_symlink(tmp_path):
    missing = tmp_path / "missing.sql"
    with pytest.raises(ValueError, match="schema_artifact_missing"):
        apply_schema._load_schema_artifact(missing)

    link = tmp_path / "schema-link.sql"
    link.symlink_to(SCHEMA_PATH)
    with pytest.raises(ValueError, match="schema_artifact_symlink_rejected"):
        apply_schema._load_schema_artifact(link)


def test_check_absent_uses_read_only_catalog_psql_only():
    runner = FakeRunner(_process(stdout=""))
    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "absent"
    assert result.object_count == 0
    assert len(runner.calls) == 1
    command, kwargs = runner.calls[0]
    assert command[1] == TARGET
    assert "-X" in command
    assert "ON_ERROR_STOP=1" in command
    assert "-c" in command
    assert "-f" not in command
    assert "-1" not in command
    assert "CREATE TABLE" not in command[-1]
    assert kwargs == {
        "check": False,
        "capture_output": True,
        "text": True,
        "timeout": apply_schema.PSQL_TIMEOUT_SECONDS,
        "shell": False,
    }


def test_check_all_nine_compatible_objects():
    runner = FakeRunner(
        _process(stdout=_catalog_output(_compatible_rows()))
    )

    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "compatible"
    assert result.compatibility == "compatible"
    assert result.object_count == 9


def test_postgres18_sized_nine_record_catalog_output_is_compatible():
    runner = FakeRunner(
        _process(stdout=_postgres18_sized_catalog_output())
    )

    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "compatible"
    assert result.compatibility == "compatible"
    assert result.object_count == 9


def test_check_partial_table_set_is_blocking_classification():
    runner = FakeRunner(
        _process(stdout=_catalog_output(_compatible_rows()[:4]))
    )

    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "partial"
    assert result.object_count == 4


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(relkind="v"),
        lambda row: row.update(columns=[]),
        lambda row: row.update(primary_key_columns=[]),
        lambda row: row.update(constraint_names=[]),
        lambda row: row.update(constraint_definitions=[]),
        lambda row: row.update(index_names=[]),
        lambda row: row.update(column_types={}),
    ],
)
def test_check_incompatible_object_structure(mutation):
    rows = _compatible_rows()
    mutation(rows[0])
    runner = FakeRunner(_process(stdout=_catalog_output(rows)))

    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "incompatible"
    assert result.object_count == 9


@pytest.mark.parametrize(
    ("table_index", "remove_prefix"),
    [
        (1, "foreign key"),
        (0, "unique"),
        (0, "run_status"),
    ],
)
def test_foreign_unique_and_check_constraint_drift_remains_incompatible(
    table_index,
    remove_prefix,
):
    rows = _compatible_rows()
    rows[table_index]["constraint_definitions"] = [
        definition
        for definition in rows[table_index]["constraint_definitions"]
        if not definition.lower().startswith(remove_prefix)
    ]
    runner = FakeRunner(_process(stdout=_catalog_output(rows)))

    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "incompatible"
    assert result.object_count == 9


def test_missing_cas_column_remains_incompatible():
    rows = _compatible_rows()
    rows[0]["columns"].remove("lock_version")
    rows[0]["column_types"].pop("lock_version")
    runner = FakeRunner(_process(stdout=_catalog_output(rows)))

    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "incompatible"
    assert result.object_count == 9


@pytest.mark.parametrize(
    "mutate",
    [
        lambda row: row.pop("index_names"),
        lambda row: row.update(unexpected_field=[]),
        lambda row: row.update(columns=None),
        lambda row: row.update(relkind=True),
        lambda row: row.update(columns="not-an-array"),
        lambda row: row.update(column_types=False),
        lambda row: row.update(columns=[True]),
    ],
)
def test_malformed_field_count_null_boolean_or_array_shape_fails_closed(
    mutate,
):
    rows = _compatible_rows()
    mutate(rows[0])
    runner = FakeRunner(_process(stdout=_catalog_output(rows)))

    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "unavailable"
    assert result.diagnostic_code == "catalog_result_invalid"


@pytest.mark.parametrize(
    "stdout",
    [
        _catalog_output(_compatible_rows() + [_compatible_rows()[0]]),
        _catalog_output(_compatible_rows()[:1])
        + "\n"
        + _catalog_output(_compatible_rows()[1:]),
        '{"object_name":"one","object_name":"two"}\n',
    ],
)
def test_excess_blank_or_duplicate_key_records_fail_closed(stdout):
    runner = FakeRunner(_process(stdout=stdout))

    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "unavailable"
    assert result.diagnostic_code == "catalog_result_invalid"


@pytest.mark.parametrize("stderr", ["WARNING: bounded", "NOTICE: bounded"])
def test_catalog_warning_or_notice_on_stderr_fails_closed(stderr):
    runner = FakeRunner(
        _process(
            stdout=_catalog_output(_compatible_rows()),
            stderr=stderr,
        )
    )

    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "unavailable"
    assert result.diagnostic_code == "catalog_stderr_present"


@pytest.mark.parametrize(
    ("rows", "outcome"),
    [
        (_compatible_rows()[:2], "partial"),
        (
            [
                {
                    **row,
                    "relkind": "v",
                }
                if index == 0
                else row
                for index, row in enumerate(_compatible_rows())
            ],
            "incompatible",
        ),
    ],
)
def test_partial_or_incompatible_preflight_blocks_apply(rows, outcome):
    runner = FakeRunner(_process(stdout=_catalog_output(rows)))

    result = _executor(runner).apply(database_url=TARGET)

    assert result.outcome == outcome
    assert len(runner.calls) == 1
    assert "-c" in runner.calls[0][0]
    assert "-f" not in runner.calls[0][0]


@pytest.mark.parametrize("preflight_rows", [[], _compatible_rows()])
def test_apply_uses_exact_atomic_psql_contract_and_requires_postflight(
    preflight_rows,
):
    runner = FakeRunner(
        _process(stdout=_catalog_output(preflight_rows)),
        _process(stdout="application output"),
        _process(stdout=_catalog_output(_compatible_rows())),
    )

    result = _executor(runner).apply(database_url=TARGET)

    assert result.outcome == "applied"
    assert result.compatibility == "compatible"
    assert result.object_count == 9
    assert result.subprocess_succeeded is True
    assert len(runner.calls) == 3
    command, kwargs = runner.calls[1]
    assert command == [
        "psql",
        TARGET,
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-1",
        "-f",
        str(SCHEMA_PATH.resolve()),
    ]
    assert isinstance(command, list)
    assert kwargs["shell"] is False
    assert kwargs["timeout"] == apply_schema.PSQL_TIMEOUT_SECONDS
    assert "-c" in runner.calls[0][0]
    assert "-c" in runner.calls[2][0]


def test_nonzero_apply_fails_closed_with_bounded_redacted_result():
    runner = FakeRunner(
        _process(stdout=""),
        _process(
            returncode=2,
            stdout=f"target={TARGET}",
            stderr=f"password secret at {TARGET}",
        ),
    )

    result = _executor(runner).apply(database_url=TARGET)

    assert result.outcome == "execution_failed"
    assert result.subprocess_succeeded is False
    assert result.diagnostic_code == "psql_nonzero_exit"
    assert TARGET not in repr(result)
    assert "secret" not in repr(result)
    assert len(runner.calls) == 2


def test_apply_timeout_is_bounded_chained_and_not_retried():
    runner = FakeRunner(
        _process(stdout=""),
        subprocess.TimeoutExpired(
            cmd=["psql", TARGET],
            timeout=apply_schema.PSQL_TIMEOUT_SECONDS,
        ),
    )

    with pytest.raises(apply_schema.SchemaExecutorProcessError) as captured:
        _executor(runner).apply(database_url=TARGET)

    error = captured.value
    assert error.result.outcome == "execution_failed"
    assert error.result.diagnostic_code == "psql_timeout"
    assert TARGET not in str(error)
    assert error.__cause__ is not None
    assert len(runner.calls) == 2


@pytest.mark.parametrize(
    ("postflight", "compatibility"),
    [
        ([], "absent"),
        (_compatible_rows()[:3], "partial"),
    ],
)
def test_successful_subprocess_without_compatible_postflight_is_not_applied(
    postflight,
    compatibility,
):
    runner = FakeRunner(
        _process(stdout=""),
        _process(returncode=0, stdout=f"do not expose {TARGET}"),
        _process(stdout=_catalog_output(postflight)),
    )

    result = _executor(runner).apply(database_url=TARGET)

    assert result.outcome == "verification_failed"
    assert result.compatibility == compatibility
    assert result.subprocess_succeeded is True
    assert TARGET not in repr(result)
    assert len(runner.calls) == 3


def test_catalog_timeout_malformed_or_nonzero_is_unavailable_without_retry():
    runners = (
        FakeRunner(
            subprocess.TimeoutExpired(cmd=["psql"], timeout=60)
        ),
        FakeRunner(_process(stdout="not-json\n")),
        FakeRunner(_process(returncode=1, stderr="could not connect")),
    )

    results = [
        _executor(runner).check(database_url=TARGET)
        for runner in runners
    ]

    assert [result.outcome for result in results] == [
        "unavailable",
        "unavailable",
        "unavailable",
    ]
    assert [len(runner.calls) for runner in runners] == [1, 1, 1]
    assert all(TARGET not in repr(result) for result in results)


def test_process_output_is_never_returned_even_when_bounded_for_classification():
    sensitive = TARGET + " " + ("x" * 20_000)
    runner = FakeRunner(
        _process(
            returncode=1,
            stdout=sensitive,
            stderr="permission denied",
        )
    )

    result = _executor(runner).check(database_url=TARGET)

    assert result.outcome == "unavailable"
    assert result.diagnostic_code == "psql_permission_denied"
    assert sensitive not in repr(result)
    assert TARGET not in repr(result)


def test_dedicated_integration_target_has_separate_opt_in_and_no_fallback():
    assert apply_schema.dedicated_test_database_target({}) is None
    assert apply_schema.dedicated_test_database_target(
        {
            apply_schema.TEST_EXECUTION_CAPABILITY_NAME: "true",
            apply_schema.DATABASE_URL_NAME: TARGET,
            "DATABASE_URL": TARGET,
        }
    ) is None
    assert apply_schema.dedicated_test_database_target(
        {
            apply_schema.TEST_EXECUTION_CAPABILITY_NAME: "true",
            apply_schema.TEST_DATABASE_URL_NAME: TARGET,
        }
    ) == TARGET
    assert apply_schema.TEST_DATABASE_URL_NAME == (
        "APPLYLENS_DURABLE_ORCHESTRATION_TEST_DATABASE_URL"
    )


@pytest.mark.parametrize(
    ("operation", "responses", "expected_code"),
    [
        ("--plan", (), 0),
        ("--check", (_process(stdout=_catalog_output(_compatible_rows())),), 0),
        (
            "--apply",
            (
                _process(stdout=""),
                _process(),
                _process(stdout=_catalog_output(_compatible_rows())),
            ),
            0,
        ),
    ],
)
def test_cli_success_is_concise_and_redacted(
    operation,
    responses,
    expected_code,
    capsys,
):
    runner = FakeRunner(*responses)
    code = apply_schema.main(
        [operation],
        configuration={
            apply_schema.CAPABILITY_NAME: "true",
            apply_schema.DATABASE_URL_NAME: TARGET,
        },
        runner=runner,
    )

    assert code == expected_code
    output = capsys.readouterr().out
    assert TARGET not in output
    assert "secret" not in output
    assert "outcome=" in output


def test_schema_executor_cannot_create_or_drop_databases_or_tables():
    catalog_sql = apply_schema._CATALOG_SQL.upper()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8").upper()
    apply_command = apply_schema._apply_command(
        psql_bin="psql",
        database_url=TARGET,
        schema_path=SCHEMA_PATH,
    )

    for prohibited in ("CREATE ", "ALTER ", "DROP ", "INSERT ", "UPDATE "):
        assert prohibited not in catalog_sql
    for prohibited in ("CREATE DATABASE", "DROP DATABASE", "DROP TABLE"):
        assert prohibited not in schema_sql
    assert "-c" not in apply_command
    assert apply_command[-2:] == ["-f", str(SCHEMA_PATH)]


def test_no_startup_runtime_or_agent_integration_and_existing_owners_unchanged():
    executor_source = EXECUTOR_PATH.read_text(encoding="utf-8")
    store_source = STORE_PATH.read_text(encoding="utf-8")
    repository_source = REPOSITORY_PATH.read_text(encoding="utf-8")
    harness_source = HARNESS_PATH.read_text(encoding="utf-8")

    for fragment in (
        "src.app",
        "src.pipeline",
        "collector",
        "scheduler",
        "langgraph",
        "checkpointer",
    ):
        assert fragment not in executor_source.lower()
    assert ".execute(" not in store_source
    assert "admin_tools.durable_orchestration" not in repository_source
    assert "admin_tools.durable_orchestration" not in harness_source
    assert SCHEMA_PATH.read_text(encoding="utf-8").count(
        "CREATE TABLE IF NOT EXISTS"
    ) == 9


def test_only_fake_subprocess_contract_is_used_in_this_suite():
    assert apply_schema._invoke.__defaults__ is None
    assert FakeRunner.__call__ is not subprocess.run
