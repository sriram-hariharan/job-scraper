# Second Synthetic Fixture Payload Implementation

Doc path: `docs/second_synthetic_fixture_payload_implementation.md`

Phase 81A is second synthetic fixture payload implementation only. Exactly one new synthetic fixture payload is added. New fixture file: `tests/fixtures/agentic_storage_transaction_failure_modes/blocked_db_write_request_minimal.json`. Existing safe fixture remains: `tests/fixtures/agentic_storage_transaction_failure_modes/safe_execution_request_minimal.json`. `.gitkeep` remains. The fixture directory contains only `.gitkeep`, `blocked_db_write_request_minimal.json`, and `safe_execution_request_minimal.json`. The blocked fixture is inert. The blocked fixture is not executed. The blocked fixture is not wired into runtime. The blocked fixture is not discovered by workflow_runner. The blocked fixture is not used by live planning. The blocked fixture does not trigger generator, simulator, proposal planner, app services, queue, DB, or application submission. The blocked fixture intentionally sets `request.allow_db_write` true. The expected validator result is failed. The expected reason code includes `db_write_not_allowed`. The expected `did_execute_fixture` false. The expected `did_mutate_production` false. The expected `did_write_db` false. No runtime integration is added. No workflow_runner integration is added. No live planning integration is added. No app services integration is added. No queue integration is added. No automatic fixture validation is added. No fixture execution is added. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No runtime DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are added. No application submission is added.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Implementation Scope

- Second synthetic fixture payload implementation: `PASS`
- Blocked DB-write fixture payload: `PASS`
- Additional fixture payload files beyond approved blocked fixture: `NO_GO`
- Runtime integration implementation: `NO_GO`
- Workflow runner integration: `NO_GO`
- Live planning integration: `NO_GO`
- App services integration: `NO_GO`
- Queue integration: `NO_GO`
- Fixture discovery in runtime: `NO_GO`
- Automatic fixture validation: `NO_GO`
- Fixture execution: `NO_GO`
- Runtime failure-mode tests: `NO_GO`
- Storage integration tests: `NO_GO`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Fixture Directory Contents

- `.gitkeep`
- `blocked_db_write_request_minimal.json`
- `safe_execution_request_minimal.json`

## Blocked Fixture Contract

- `fixture_schema_version == fixture_schema_v1`
- `fixture_id == blocked_db_write_request_minimal`
- `fixture_family == blocked_db_write_request`
- `synthetic is true`
- `contains_private_data is false`
- `contains_secret is false`
- `contains_production_path is false`
- `contains_live_queue_path is false`
- `contains_application_submission_target is false`
- `request.execution_mode == dry_run_only`
- `request.allow_agent_execution is false`
- `request.allow_live_execution is false`
- `request.allow_mutation is false`
- `request.allow_db_write is true`
- `request.allow_queue_update is false`
- `request.allow_application_submission is false`
- `expected_validation.validation_status == failed`
- `expected_validation.reason_codes` includes `db_write_not_allowed`
- `expected_validation.did_execute_fixture is false`
- `expected_validation.did_mutate_production is false`
- `expected_validation.did_write_db is false`

## Validator/CLI Coverage

- direct validator coverage confirms the blocked fixture fails safely
- direct validator coverage confirms `db_write_not_allowed`
- direct validator coverage confirms `did_execute_fixture` false
- direct validator coverage confirms `did_mutate_production` false
- direct validator coverage confirms `did_write_db` false
- manual CLI coverage confirms the blocked fixture returns exit code `1`
- manual CLI JSON output includes `db_write_not_allowed`
- manual CLI JSON output confirms `did_execute_fixture` false
- manual CLI JSON output confirms `did_mutate_production` false
- manual CLI JSON output confirms `did_write_db` false

## Runtime Isolation Confirmation

- no runtime path imports/calls the validator or CLI
- `workflow_runner.py` does not import/call fixture_validator or fixture_validator_cli
- `run_application_planning.py` does not import/call fixture_validator or fixture_validator_cli
- `application_execution_queue.py` does not import/call fixture_validator or fixture_validator_cli
- `src/app/services.py` does not import/call fixture_validator or fixture_validator_cli
- orchestrator harness does not import/call fixture_validator or fixture_validator_cli
- proposal planner does not import/call fixture_validator or fixture_validator_cli
- dry-run simulator does not import/call fixture_validator or fixture_validator_cli
- read-only generator does not import/call fixture_validator or fixture_validator_cli

## Forbidden Next-Step Shortcuts

- do not wire validator into workflow_runner next without explicit approval
- do not wire validator into live planning next without explicit approval
- do not auto-discover fixture directories next
- do not validate fixtures automatically during application planning next
- do not add DB writes next
- do not add queue mutation next
- do not add approval APIs next
- do not add mutation APIs next
- do not add application submission automation next
- do not enable workflow_runner live execution next

## Recommended Next Phase

Recommended next phase: 81B second synthetic fixture payload implementation final audit and merge gate.

After 81B: 82A second synthetic fixture payload implementation release safety checkpoint, docs/tests only.
