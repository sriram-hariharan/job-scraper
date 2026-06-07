import json
from pathlib import Path

from src.agents import fixture_validator_cli


FIXTURE_DIR = Path("tests/fixtures/agentic_storage_transaction_failure_modes")
SAFE_FIXTURE_PATH = FIXTURE_DIR / "safe_execution_request_minimal.json"
BLOCKED_DB_WRITE_FIXTURE_PATH = FIXTURE_DIR / "blocked_db_write_request_minimal.json"
BLOCKED_APPLICATION_SUBMISSION_FIXTURE_PATH = (
    FIXTURE_DIR / "blocked_application_submission_request_minimal.json"
)


def _load_safe_fixture():
    return json.loads(SAFE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _write_fixture_copy(tmp_path, payload):
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return fixture_path


def test_valid_safe_fixture_returns_zero_with_json_output(capsys):
    original_fixture_source = SAFE_FIXTURE_PATH.read_text(encoding="utf-8")

    exit_code = fixture_validator_cli.main(
        ["--fixture", str(SAFE_FIXTURE_PATH), "--json"]
    )

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "passed"
    assert result["is_valid"] is True
    assert result["did_execute_fixture"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False
    assert SAFE_FIXTURE_PATH.read_text(encoding="utf-8") == original_fixture_source


def test_invalid_fixture_returns_one_with_reason_code(tmp_path, capsys):
    payload = _load_safe_fixture()
    payload["request"]["allow_db_write"] = True
    invalid_fixture_path = _write_fixture_copy(tmp_path, payload)

    exit_code = fixture_validator_cli.main(
        ["--fixture", str(invalid_fixture_path), "--json"]
    )

    assert exit_code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "failed"
    assert result["is_valid"] is False
    assert "db_write_not_allowed" in result["reason_codes"]
    assert result["did_write_db"] is False


def test_application_submission_fixture_returns_one_with_json_reason(tmp_path, capsys):
    payload = _load_safe_fixture()
    payload["request"]["allow_application_submission"] = True
    invalid_fixture_path = _write_fixture_copy(tmp_path, payload)

    exit_code = fixture_validator_cli.main(
        ["--fixture", str(invalid_fixture_path), "--json"]
    )

    assert exit_code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "failed"
    assert result["is_valid"] is False
    assert "application_submission_not_allowed" in result["reason_codes"]
    assert result["did_execute_fixture"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_blocked_db_write_fixture_returns_one_with_json_reason(capsys):
    exit_code = fixture_validator_cli.main(
        ["--fixture", str(BLOCKED_DB_WRITE_FIXTURE_PATH), "--json"]
    )

    assert exit_code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "failed"
    assert result["is_valid"] is False
    assert "db_write_not_allowed" in result["reason_codes"]
    assert result["did_execute_fixture"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_blocked_application_submission_fixture_returns_one_with_json_reason(capsys):
    exit_code = fixture_validator_cli.main(
        ["--fixture", str(BLOCKED_APPLICATION_SUBMISSION_FIXTURE_PATH), "--json"]
    )

    assert exit_code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "failed"
    assert result["is_valid"] is False
    assert "application_submission_not_allowed" in result["reason_codes"]
    assert result["did_execute_fixture"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_missing_fixture_argument_returns_usage_error(capsys):
    exit_code = fixture_validator_cli.main([])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "missing required --fixture path" in captured.err


def test_directory_fixture_argument_returns_usage_error_without_discovery(capsys):
    exit_code = fixture_validator_cli.main(["--fixture", str(FIXTURE_DIR), "--json"])

    assert exit_code == 2
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "failed"
    assert result["reason_codes"] == ["invalid_cli_input"]


def test_fixture_directory_still_contains_only_marker_and_approved_json():
    current_contents = sorted(path.name for path in FIXTURE_DIR.iterdir())

    assert current_contents == [
        ".gitkeep",
        "blocked_application_submission_request_minimal.json",
        "blocked_db_write_request_minimal.json",
        "safe_execution_request_minimal.json",
    ]


def test_fixture_validator_cli_has_no_runtime_or_side_effect_imports():
    source = Path("src/agents/fixture_validator_cli.py").read_text(encoding="utf-8")

    for forbidden in [
        "subprocess",
        "requests",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "src.app",
        "workflow_runner",
        "run_application_planning",
        "application_execution_queue",
        "orchestrator_adapter_harness",
        "proposal_only_mutation_planner",
        "dry_run_execution_simulator",
        "read_only_chain_artifact_generator",
    ]:
        assert forbidden not in source
