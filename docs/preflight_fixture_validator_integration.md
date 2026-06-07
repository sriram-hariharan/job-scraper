# Preflight Fixture Validator Integration

Doc path: `docs/preflight_fixture_validator_integration.md`

Phase 88A is a preflight-only fixture validator integration implementation. Fixture validation is now wired only into orchestrator preflight JSON reporting from `python -m src.agents.orchestrator_adapter_harness --preflight --json`.

Fixture validation is read-only. Fixture validation validates exactly the approved fixture files:

- `tests/fixtures/agentic_storage_transaction_failure_modes/safe_execution_request_minimal.json`
- `tests/fixtures/agentic_storage_transaction_failure_modes/blocked_db_write_request_minimal.json`
- `tests/fixtures/agentic_storage_transaction_failure_modes/blocked_application_submission_request_minimal.json`

No fixture payload files beyond the approved three are expected. The fixture directory still contains only `.gitkeep`, `blocked_application_submission_request_minimal.json`, `blocked_db_write_request_minimal.json`, and `safe_execution_request_minimal.json`.

The preflight fixture validation summary is additive. Existing preflight JSON fields remain in place, including `allow_agent_execution`, `executable_adapter_count`, `adapter_preflight_results`, `summary`, `context`, and `validation`.

## Preflight JSON Fields

The orchestrator preflight JSON now includes:

- `fixture_validation`
- `fixture_validation_enabled`
- `fixture_validation_status`
- `fixture_validation_passed`
- `fixture_validation_checked_count`
- `fixture_validation_expected_fixture_count`
- `fixture_validation_results`
- `fixture_validation_failed_fixture_ids`
- `fixture_validation_reason_codes`

Blocked fixtures are expected to fail validation and still produce overall preflight pass when their actual failure matches `expected_validation`. The safe fixture is expected to pass validation. The blocked DB-write fixture is expected to fail with `db_write_not_allowed`. The blocked application-submission fixture is expected to fail with `application_submission_not_allowed`.

Preflight fails only on mismatch, missing fixture, unexpected fixture, malformed fixture, or unexpected runtime risk.

## Safety Boundary

Fixture validation does not execute fixtures. Fixture validation does not call workflow_runner. Fixture validation does not call live planning. Fixture validation does not call app services. Fixture validation does not call queue. Fixture validation does not call DB. Fixture validation does not mutate. Fixture validation does not submit applications.

`workflow_runner.py` remains dry-run only. `executable_adapter_count` remains 0. `allow_agent_execution` remains false. `did_execute_count` remains 0. `did_execute_live` remains false. `did_mutate_production` remains false. `did_write_db` remains false.

## Decisions

- Preflight-only fixture validator integration: `PASS`
- Runtime-facing integration scope: `PREFLIGHT_ONLY`
- Workflow runner integration: `NO_GO`
- Live planning integration: `NO_GO`
- App services integration: `NO_GO`
- Queue integration: `NO_GO`
- Fixture execution: `NO_GO`
- Automatic execution: `NO_GO`
- DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Application submission: `NO_GO`
- Approval API/storage: `NO_GO`
- Scheduler/background execution: `NO_GO`

## Explicit Non-Goals

- no fixture payload files
- no fixture payload JSON changes
- no fixture validator behavior changes
- no fixture validator CLI behavior changes
- no workflow_runner integration
- no live planning integration
- no app services integration
- no queue integration
- no fixture execution
- no automatic execution
- no DB writes
- no queue mutation
- no application submission
- no approval API/storage
- no migrations
- no SQL DDL
- no scheduler/background execution
- no UI run/approve/reject buttons
- no LangGraph or agent framework

## Recommended Next Phase

Recommended next phase: 88B preflight-only fixture validator integration final audit and merge gate.

Do not wire validator into workflow_runner next. Do not wire validator into live planning next. Do not auto-discover fixture directories next. Do not execute fixture payloads next. Do not add DB writes, queue mutation, storage APIs, migrations, mutation execution, live execution, approval API/storage, or application submission next.
