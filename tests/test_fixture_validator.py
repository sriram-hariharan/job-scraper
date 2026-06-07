import json
from pathlib import Path

from src.agents.fixture_validator import validate_fixture_file


FIXTURE_DIR = Path("tests/fixtures/agentic_storage_transaction_failure_modes")
SAFE_FIXTURE_PATH = FIXTURE_DIR / "safe_execution_request_minimal.json"


def _load_safe_fixture():
    return json.loads(SAFE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _write_fixture_copy(tmp_path, payload):
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return fixture_path


def test_safe_execution_request_minimal_fixture_passes_validation():
    result = validate_fixture_file(SAFE_FIXTURE_PATH)

    assert result["validation_status"] == "passed"
    assert result["fixture_id"] == "safe_execution_request_minimal"
    assert result["fixture_family"] == "safe_execution_request"
    assert result["is_valid"] is True
    assert result["reason_codes"] == []
    assert result["warning_codes"] == []
    assert result["did_execute_fixture"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_allow_db_write_true_fails_with_db_write_reason(tmp_path):
    payload = _load_safe_fixture()
    payload["request"]["allow_db_write"] = True

    result = validate_fixture_file(_write_fixture_copy(tmp_path, payload))

    assert result["validation_status"] == "failed"
    assert result["is_valid"] is False
    assert "db_write_not_allowed" in result["reason_codes"]
    assert result["did_write_db"] is False


def test_contains_secret_true_fails_with_secret_reason(tmp_path):
    payload = _load_safe_fixture()
    payload["contains_secret"] = True

    result = validate_fixture_file(_write_fixture_copy(tmp_path, payload))

    assert result["validation_status"] == "failed"
    assert "secret_not_allowed" in result["reason_codes"]
    assert result["did_execute_fixture"] is False


def test_application_submission_true_fails_with_submission_reason(tmp_path):
    payload = _load_safe_fixture()
    payload["request"]["allow_application_submission"] = True

    result = validate_fixture_file(_write_fixture_copy(tmp_path, payload))

    assert result["validation_status"] == "failed"
    assert "application_submission_not_allowed" in result["reason_codes"]
    assert result["did_mutate_production"] is False


def test_missing_required_field_fails_with_missing_required_field(tmp_path):
    payload = _load_safe_fixture()
    payload.pop("fixture_schema_version")

    result = validate_fixture_file(_write_fixture_copy(tmp_path, payload))

    assert result["validation_status"] == "failed"
    assert "missing_required_field" in result["reason_codes"]
    assert result["did_execute_fixture"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_validator_module_has_no_runtime_or_side_effect_imports():
    source = Path("src/agents/fixture_validator.py").read_text(encoding="utf-8")

    for forbidden in [
        "argparse",
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


def test_fixture_directory_contains_only_marker_and_approved_json():
    current_contents = sorted(path.name for path in FIXTURE_DIR.iterdir())

    assert current_contents == [".gitkeep", "safe_execution_request_minimal.json"]
