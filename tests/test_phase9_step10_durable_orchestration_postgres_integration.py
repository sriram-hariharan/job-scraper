"""Environment-gated real PostgreSQL verification for the Step 9 executor.

The configured target must be an operator-provisioned, disposable database.
This test never creates or drops a database, schema, table, or unrelated
object. Provisioning and disposal remain external operator responsibilities.
"""

from hashlib import sha256
import os
from pathlib import Path
import shutil
from typing import Any, Mapping

import pytest

from src.storage.admin_tools.durable_orchestration import apply_schema


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "src/storage/durable_orchestration/schema.sql"
BOUNDED_SKIP_DISABLED = "dedicated_test_schema_execution_not_enabled"
BOUNDED_SKIP_TARGET = "dedicated_test_database_target_missing"
BOUNDED_ALIAS_FAILURE = "dedicated_test_database_target_alias_rejected"


def _dedicated_target_or_skip(
    configuration: Mapping[str, Any],
) -> str:
    if not apply_schema._truthy(
        configuration.get(apply_schema.TEST_EXECUTION_CAPABILITY_NAME)
    ):
        pytest.skip(BOUNDED_SKIP_DISABLED)
    target = str(
        configuration.get(apply_schema.TEST_DATABASE_URL_NAME, "") or ""
    ).strip()
    if not target:
        pytest.skip(BOUNDED_SKIP_TARGET)
    non_test_targets = (
        str(
            configuration.get(apply_schema.DATABASE_URL_NAME, "") or ""
        ).strip(),
        str(configuration.get("DATABASE_URL", "") or "").strip(),
    )
    if any(value and value == target for value in non_test_targets):
        pytest.fail(BOUNDED_ALIAS_FAILURE)
    return target


def _assert_safe_preflight(result: apply_schema.SchemaExecutionResult) -> None:
    assert result.outcome in {
        "absent",
        "compatible",
    }, "dedicated_test_preflight_not_safe"
    if result.outcome == "absent":
        assert result.object_count == 0, "absent_object_count_invalid"
    else:
        assert result.object_count == 9, "compatible_object_count_invalid"
        assert result.compatibility == "compatible"


def _assert_applied(result: apply_schema.SchemaExecutionResult) -> None:
    assert result.outcome == "applied", "schema_application_not_applied"
    assert result.compatibility == "compatible"
    assert result.object_count == 9
    assert result.subprocess_succeeded is True


def _assert_compatible(result: apply_schema.SchemaExecutionResult) -> None:
    assert result.outcome == "compatible", "catalog_not_compatible"
    assert result.compatibility == "compatible"
    assert result.object_count == 9


def test_real_durable_orchestration_schema_executor_postgres_integration():
    """Run only with a separately enabled and dedicated PostgreSQL target."""
    target = _dedicated_target_or_skip(os.environ)
    assert shutil.which("psql") is not None, "psql_executable_unavailable"

    executor = apply_schema.DurableOrchestrationSchemaExecutor(enabled=True)

    plan = executor.plan()
    assert plan.outcome == "planned", "schema_plan_failed"
    assert plan.schema_sha256 == sha256(SCHEMA_PATH.read_bytes()).hexdigest()
    assert plan.object_count == 9

    preflight = executor.check(database_url=target)
    _assert_safe_preflight(preflight)

    first_application = executor.apply(database_url=target)
    _assert_applied(first_application)

    first_postflight = executor.check(database_url=target)
    _assert_compatible(first_postflight)

    second_application = executor.apply(database_url=target)
    _assert_applied(second_application)

    second_postflight = executor.check(database_url=target)
    _assert_compatible(second_postflight)

    for result in (
        plan,
        preflight,
        first_application,
        first_postflight,
        second_application,
        second_postflight,
    ):
        result_text = repr(result)
        assert target not in result_text, "target_exposed_in_result"


def test_missing_enablement_skips_before_subprocess_use(monkeypatch):
    def prohibited_subprocess(*args, **kwargs):
        raise AssertionError("subprocess_called_before_enablement")

    monkeypatch.setattr(apply_schema.subprocess, "run", prohibited_subprocess)
    with pytest.raises(pytest.skip.Exception) as captured:
        _dedicated_target_or_skip(
            {
                apply_schema.TEST_DATABASE_URL_NAME: (
                    "postgresql://test-user:test-secret@test.invalid/test"
                ),
            }
        )

    assert str(captured.value) == BOUNDED_SKIP_DISABLED
    assert "test-secret" not in str(captured.value)


def test_missing_dedicated_url_skips_before_subprocess_use(monkeypatch):
    def prohibited_subprocess(*args, **kwargs):
        raise AssertionError("subprocess_called_without_dedicated_target")

    monkeypatch.setattr(apply_schema.subprocess, "run", prohibited_subprocess)
    with pytest.raises(pytest.skip.Exception) as captured:
        _dedicated_target_or_skip(
            {
                apply_schema.TEST_EXECUTION_CAPABILITY_NAME: "true",
            }
        )

    assert str(captured.value) == BOUNDED_SKIP_TARGET


@pytest.mark.parametrize(
    "non_test_configuration",
    [
        {
            apply_schema.DATABASE_URL_NAME: (
                "postgresql://runtime-user:runtime-secret@runtime.invalid/db"
            ),
        },
        {
            "DATABASE_URL": (
                "postgresql://generic-user:generic-secret@generic.invalid/db"
            ),
        },
        {
            apply_schema.DATABASE_URL_NAME: (
                "postgresql://runtime-user:runtime-secret@runtime.invalid/db"
            ),
            "DATABASE_URL": (
                "postgresql://generic-user:generic-secret@generic.invalid/db"
            ),
        },
    ],
)
def test_no_runtime_or_generic_database_fallback(
    non_test_configuration,
    monkeypatch,
):
    def prohibited_subprocess(*args, **kwargs):
        raise AssertionError("subprocess_used_non_test_database_target")

    monkeypatch.setattr(apply_schema.subprocess, "run", prohibited_subprocess)
    configuration = {
        apply_schema.TEST_EXECUTION_CAPABILITY_NAME: "true",
        **non_test_configuration,
    }

    with pytest.raises(pytest.skip.Exception) as captured:
        _dedicated_target_or_skip(configuration)

    reason = str(captured.value)
    assert reason == BOUNDED_SKIP_TARGET
    for value in non_test_configuration.values():
        assert value not in reason


@pytest.mark.parametrize(
    "alias_name",
    [
        apply_schema.DATABASE_URL_NAME,
        "DATABASE_URL",
    ],
)
def test_equal_test_and_non_test_target_fails_before_subprocess(
    alias_name,
    monkeypatch,
):
    target = "postgresql://alias-user:alias-secret@alias.invalid/db"

    def prohibited_subprocess(*args, **kwargs):
        raise AssertionError("subprocess_called_with_aliased_target")

    monkeypatch.setattr(apply_schema.subprocess, "run", prohibited_subprocess)
    with pytest.raises(pytest.fail.Exception) as captured:
        _dedicated_target_or_skip(
            {
                apply_schema.TEST_EXECUTION_CAPABILITY_NAME: "true",
                apply_schema.TEST_DATABASE_URL_NAME: target,
                alias_name: target,
            }
        )

    assert str(captured.value) == BOUNDED_ALIAS_FAILURE
    assert target not in str(captured.value)
    assert "alias-secret" not in str(captured.value)


@pytest.mark.parametrize(
    ("value", "accepted"),
    [
        ("true", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("enabled", True),
        ("false", False),
        ("0", False),
        ("", False),
        ("unexpected", False),
    ],
)
def test_enablement_uses_only_step9_supported_explicit_values(
    value,
    accepted,
):
    configuration = {
        apply_schema.TEST_EXECUTION_CAPABILITY_NAME: value,
        apply_schema.TEST_DATABASE_URL_NAME: (
            "postgresql://test-user:test-secret@test.invalid/test"
        ),
    }

    if accepted:
        assert _dedicated_target_or_skip(configuration)
    else:
        with pytest.raises(pytest.skip.Exception) as captured:
            _dedicated_target_or_skip(configuration)
        assert str(captured.value) == BOUNDED_SKIP_DISABLED


def test_boundary_messages_and_types_expose_no_target_details():
    target = "postgresql://private-user:private-secret@private.invalid:5544/db"
    configurations = (
        {},
        {
            apply_schema.TEST_EXECUTION_CAPABILITY_NAME: "true",
        },
    )

    for configuration in configurations:
        with pytest.raises(pytest.skip.Exception) as captured:
            _dedicated_target_or_skip(configuration)
        message = str(captured.value)
        for sensitive in (
            target,
            "private-user",
            "private-secret",
            "private.invalid",
            "5544",
        ):
            assert sensitive not in message
