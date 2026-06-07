"""Read-only validation for explicitly provided synthetic fixture files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


VALIDATOR_VERSION = "minimal_fixture_validator_v1"
EXPECTED_SCHEMA_VERSION = "fixture_schema_v1"
EXPECTED_FIXTURE_ID = "safe_execution_request_minimal"
EXPECTED_FIXTURE_FAMILY = "safe_execution_request"

REASON_INVALID_JSON = "invalid_json"
REASON_MISSING_REQUIRED_FIELD = "missing_required_field"
REASON_INVALID_SCHEMA_VERSION = "invalid_schema_version"
REASON_INVALID_FIXTURE_FAMILY = "invalid_fixture_family"
REASON_PRIVATE_DATA_NOT_ALLOWED = "private_data_not_allowed"
REASON_SECRET_NOT_ALLOWED = "secret_not_allowed"
REASON_PRODUCTION_PATH_NOT_ALLOWED = "production_path_not_allowed"
REASON_LIVE_QUEUE_PATH_NOT_ALLOWED = "live_queue_path_not_allowed"
REASON_APPLICATION_SUBMISSION_TARGET_NOT_ALLOWED = (
    "application_submission_target_not_allowed"
)
REASON_AGENT_EXECUTION_NOT_ALLOWED = "agent_execution_not_allowed"
REASON_LIVE_EXECUTION_NOT_ALLOWED = "live_execution_not_allowed"
REASON_MUTATION_NOT_ALLOWED = "mutation_not_allowed"
REASON_DB_WRITE_NOT_ALLOWED = "db_write_not_allowed"
REASON_QUEUE_UPDATE_NOT_ALLOWED = "queue_update_not_allowed"
REASON_APPLICATION_SUBMISSION_NOT_ALLOWED = "application_submission_not_allowed"
REASON_EXECUTION_FLAG_NOT_FALSE = "execution_flag_not_false"

REQUIRED_TOP_LEVEL_FIELDS = {
    "fixture_schema_version",
    "fixture_id",
    "fixture_family",
    "synthetic",
    "contains_private_data",
    "contains_secret",
    "contains_production_path",
    "contains_live_queue_path",
    "contains_application_submission_target",
    "request",
    "expected_validation",
}
REQUIRED_REQUEST_FIELDS = {
    "execution_mode",
    "allow_agent_execution",
    "allow_live_execution",
    "allow_mutation",
    "allow_db_write",
    "allow_queue_update",
    "allow_application_submission",
}
REQUIRED_EXPECTED_VALIDATION_FIELDS = {
    "did_execute_fixture",
    "did_mutate_production",
    "did_write_db",
}


def _empty_result(reason_codes: List[str] | None = None) -> Dict[str, Any]:
    reason_codes = list(reason_codes or [])
    return {
        "validator_version": VALIDATOR_VERSION,
        "validation_status": "failed" if reason_codes else "passed",
        "fixture_id": "",
        "fixture_family": "",
        "is_valid": not reason_codes,
        "reason_codes": reason_codes,
        "warning_codes": [],
        "did_execute_fixture": False,
        "did_mutate_production": False,
        "did_write_db": False,
    }


def _append_missing_required_codes(
    *,
    payload: Dict[str, Any],
    request: Dict[str, Any],
    expected_validation: Dict[str, Any],
    reason_codes: List[str],
) -> None:
    missing_fields = sorted(REQUIRED_TOP_LEVEL_FIELDS.difference(payload))
    missing_fields.extend(
        f"request.{field}"
        for field in sorted(REQUIRED_REQUEST_FIELDS.difference(request))
    )
    missing_fields.extend(
        f"expected_validation.{field}"
        for field in sorted(
            REQUIRED_EXPECTED_VALIDATION_FIELDS.difference(expected_validation)
        )
    )
    reason_codes.extend([REASON_MISSING_REQUIRED_FIELD] * len(missing_fields))


def _append_boolean_failure(
    *,
    condition: bool,
    reason_code: str,
    reason_codes: List[str],
) -> None:
    if condition:
        reason_codes.append(reason_code)


def validate_fixture_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a parsed fixture payload without executing or mutating anything."""

    request = payload.get("request")
    if not isinstance(request, dict):
        request = {}
    expected_validation = payload.get("expected_validation")
    if not isinstance(expected_validation, dict):
        expected_validation = {}

    reason_codes: List[str] = []
    _append_missing_required_codes(
        payload=payload,
        request=request,
        expected_validation=expected_validation,
        reason_codes=reason_codes,
    )

    if payload.get("fixture_schema_version") != EXPECTED_SCHEMA_VERSION:
        reason_codes.append(REASON_INVALID_SCHEMA_VERSION)
    if payload.get("fixture_id") != EXPECTED_FIXTURE_ID:
        reason_codes.append(REASON_INVALID_FIXTURE_FAMILY)
    if payload.get("fixture_family") != EXPECTED_FIXTURE_FAMILY:
        reason_codes.append(REASON_INVALID_FIXTURE_FAMILY)
    if payload.get("synthetic") is not True:
        reason_codes.append(REASON_PRIVATE_DATA_NOT_ALLOWED)

    _append_boolean_failure(
        condition=payload.get("contains_private_data") is not False,
        reason_code=REASON_PRIVATE_DATA_NOT_ALLOWED,
        reason_codes=reason_codes,
    )
    _append_boolean_failure(
        condition=payload.get("contains_secret") is not False,
        reason_code=REASON_SECRET_NOT_ALLOWED,
        reason_codes=reason_codes,
    )
    _append_boolean_failure(
        condition=payload.get("contains_production_path") is not False,
        reason_code=REASON_PRODUCTION_PATH_NOT_ALLOWED,
        reason_codes=reason_codes,
    )
    _append_boolean_failure(
        condition=payload.get("contains_live_queue_path") is not False,
        reason_code=REASON_LIVE_QUEUE_PATH_NOT_ALLOWED,
        reason_codes=reason_codes,
    )
    _append_boolean_failure(
        condition=payload.get("contains_application_submission_target") is not False,
        reason_code=REASON_APPLICATION_SUBMISSION_TARGET_NOT_ALLOWED,
        reason_codes=reason_codes,
    )

    if request.get("execution_mode") != "dry_run_only":
        reason_codes.append(REASON_EXECUTION_FLAG_NOT_FALSE)
    _append_boolean_failure(
        condition=request.get("allow_agent_execution") is not False,
        reason_code=REASON_AGENT_EXECUTION_NOT_ALLOWED,
        reason_codes=reason_codes,
    )
    _append_boolean_failure(
        condition=request.get("allow_live_execution") is not False,
        reason_code=REASON_LIVE_EXECUTION_NOT_ALLOWED,
        reason_codes=reason_codes,
    )
    _append_boolean_failure(
        condition=request.get("allow_mutation") is not False,
        reason_code=REASON_MUTATION_NOT_ALLOWED,
        reason_codes=reason_codes,
    )
    _append_boolean_failure(
        condition=request.get("allow_db_write") is not False,
        reason_code=REASON_DB_WRITE_NOT_ALLOWED,
        reason_codes=reason_codes,
    )
    _append_boolean_failure(
        condition=request.get("allow_queue_update") is not False,
        reason_code=REASON_QUEUE_UPDATE_NOT_ALLOWED,
        reason_codes=reason_codes,
    )
    _append_boolean_failure(
        condition=request.get("allow_application_submission") is not False,
        reason_code=REASON_APPLICATION_SUBMISSION_NOT_ALLOWED,
        reason_codes=reason_codes,
    )

    for field in REQUIRED_EXPECTED_VALIDATION_FIELDS:
        if expected_validation.get(field) is not False:
            reason_codes.append(REASON_EXECUTION_FLAG_NOT_FALSE)

    return {
        "validator_version": VALIDATOR_VERSION,
        "validation_status": "failed" if reason_codes else "passed",
        "fixture_id": str(payload.get("fixture_id") or ""),
        "fixture_family": str(payload.get("fixture_family") or ""),
        "is_valid": not reason_codes,
        "reason_codes": reason_codes,
        "warning_codes": [],
        "did_execute_fixture": False,
        "did_mutate_production": False,
        "did_write_db": False,
    }


def validate_fixture_file(path: str | Path) -> Dict[str, Any]:
    """Read and validate one explicitly provided local fixture file."""

    fixture_path = Path(path)
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _empty_result([REASON_INVALID_JSON])
    except OSError:
        return _empty_result([REASON_MISSING_REQUIRED_FIELD])

    if not isinstance(payload, dict):
        return _empty_result([REASON_INVALID_JSON])
    return validate_fixture_payload(payload)
