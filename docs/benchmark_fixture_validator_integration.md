# Benchmark Fixture Validator Integration

Doc path: `docs/benchmark_fixture_validator_integration.md`

Phase 89A is an agentic benchmark fixture validator integration implementation. The benchmark now surfaces fixture validation summary fields in `python -m src.evaluation.agentic_benchmark --no-write --print-summary`.

Release safety checkpoint: `docs/benchmark_fixture_validator_integration_release_safety_checkpoint.md`.

The benchmark integration is read-only. The benchmark integration reuses preflight fixture-validation semantics from the orchestrator adapter harness. The benchmark does not execute fixtures. The benchmark does not call workflow_runner. The benchmark does not call live planning. The benchmark does not call app services. The benchmark does not call queue. The benchmark does not call DB. The benchmark does not mutate. The benchmark does not submit applications.

Blocked fixtures are expected to fail validation and still produce overall benchmark pass when actual failure matches `expected_validation`.

The benchmark reports fixture validation observability for exactly the approved fixtures:

- `tests/fixtures/agentic_storage_transaction_failure_modes/safe_execution_request_minimal.json`
- `tests/fixtures/agentic_storage_transaction_failure_modes/blocked_db_write_request_minimal.json`
- `tests/fixtures/agentic_storage_transaction_failure_modes/blocked_application_submission_request_minimal.json`

The safe fixture is expected to pass validation. The blocked DB-write fixture is expected to fail with `db_write_not_allowed`. The blocked application-submission fixture is expected to fail with `application_submission_not_allowed`.

## Benchmark Summary Fields

The benchmark summary metrics now include:

- `fixture_validation_passed`
- `fixture_validation_status`
- `fixture_validation_checked_count`
- `fixture_validation_expected_fixture_count`
- `fixture_validation_failed_fixture_ids`
- `fixture_validation_reason_codes`
- `executable_adapter_count`
- `allow_agent_execution`
- `did_execute_count`
- `did_execute_live`
- `did_mutate_production`
- `did_write_db`

Existing benchmark fields are preserved, including `failed_case_ids`, `validation_pass_rate`, and `workflow_registry_validation_passed`.

## Safety Boundary

`workflow_runner.py` remains dry-run only. `executable_adapter_count` remains 0. `allow_agent_execution` remains false. `did_execute_count` remains 0. `did_execute_live` remains false. `did_mutate_production` remains false. `did_write_db` remains false.

## Decisions

- Benchmark fixture validator integration: `PASS`
- Runtime-facing integration scope: `BENCHMARK_REPORTING_ONLY`
- Preflight fixture validation reuse: `GO`
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

Recommended next phase: 89B agentic benchmark fixture validator integration final audit and merge gate.

Do not wire validator into workflow_runner next. Do not wire validator into live planning next. Do not execute fixture payloads next. Do not add DB writes, queue mutation, storage APIs, migrations, mutation execution, live execution, approval API/storage, or application submission next.
