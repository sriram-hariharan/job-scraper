# Third Synthetic Fixture Payload Implementation Plan

Doc path: `docs/third_synthetic_fixture_payload_implementation_plan.md`

Phase 83A is a third synthetic fixture payload implementation plan only. Third fixture payload file implementation: `NOT_YET`. No fixture payload file is added in this phase.

The proposed future fixture file is `tests/fixtures/agentic_storage_transaction_failure_modes/blocked_application_submission_request_minimal.json`. The proposed fixture family is `blocked_application_submission_request`. The proposed reason code is `application_submission_not_allowed`. Reason code support must be verified before future implementation.

Existing fixtures remain unchanged: `.gitkeep`, `blocked_db_write_request_minimal.json`, and `safe_execution_request_minimal.json`. The fixture directory still contains only `.gitkeep`, `blocked_db_write_request_minimal.json`, and `safe_execution_request_minimal.json`.

No runtime integration is added. No workflow_runner integration is added. No live planning integration is added. No app services integration is added. No queue integration is added. No fixture discovery in runtime is added. No automatic fixture validation is added. No fixture execution is added. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are added. No application submission is added.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Plan Scope

- Third synthetic fixture payload implementation plan: `PASS`
- Third fixture payload file implementation: `NOT_YET`
- Proposed blocked application-submission fixture: `READY_FOR_REVIEW`
- Proposed `application_submission_not_allowed` reason code: `NEEDS_VERIFICATION`
- Existing fixture payload files: `GO`
- Additional fixture payload files in this phase: `NO_GO`
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

## Existing Fixture Inventory

The current fixture directory is `tests/fixtures/agentic_storage_transaction_failure_modes/`.

It must still contain exactly:

- `.gitkeep`
- `blocked_db_write_request_minimal.json`
- `safe_execution_request_minimal.json`

No `blocked_application_submission_request_minimal.json` fixture file exists yet. No existing fixture payload JSON file is modified in this phase.

## Proposed Future Fixture Contract

The future fixture payload, if explicitly approved after this plan, should use this contract:

- `fixture_schema_version`: `fixture_schema_v1`
- `fixture_id`: `blocked_application_submission_request_minimal`
- `fixture_family`: `blocked_application_submission_request`
- `synthetic`: `true`
- `contains_private_data`: `false`
- `contains_secret`: `false`
- `contains_production_path`: `false`
- `contains_live_queue_path`: `false`
- `contains_application_submission_target`: `false`
- `request.execution_mode`: `dry_run_only`
- `request.allow_agent_execution`: `false`
- `request.allow_live_execution`: `false`
- `request.allow_mutation`: `false`
- `request.allow_db_write`: `false`
- `request.allow_queue_update`: `false`
- `request.allow_application_submission`: `true`
- `expected_validation.validation_status`: `failed`
- `expected_validation.reason_codes` includes `application_submission_not_allowed`
- `expected_validation.did_execute_fixture`: `false`
- `expected_validation.did_mutate_production`: `false`
- `expected_validation.did_write_db`: `false`

## Reason-Code Readiness Check

Future implementation cannot assume `application_submission_not_allowed` exists.

Future implementation must inspect `src/agents/fixture_validator.py` and tests before adding the fixture. If the reason code exists, add only the fixture/tests/docs. If the reason code does not exist, add the smallest validator-only reason-code support and tests, with no runtime integration.

If reason code support is missing, a future phase must either add the reason code through a minimal validator-only change, or choose a blocked field already supported by the validator.

## Future Implementation Constraints

- Do not add `blocked_application_submission_request_minimal.json` next unless 83B passes and explicit approval is given.
- Future implementation must keep fixture data synthetic and inert.
- Future implementation must not execute fixture payloads.
- Future implementation must keep expected execution and mutation flags false.
- Future implementation must keep the validator explicit-file-path-only.
- Future implementation must keep the CLI manual-only.
- Future implementation must avoid runtime failure-mode tests unless explicitly approved.

## Runtime Isolation Confirmation

- no runtime integration added
- no workflow_runner integration added
- no live planning integration added
- no app services integration added
- no queue integration added
- no fixture discovery in runtime added
- no automatic fixture validation added
- no fixture execution added
- no runtime failure-mode tests added
- no storage integration tests added
- no DB schema file added
- no migration added
- no SQL DDL added
- no DB writes added
- no live execution enabled
- no mutation enabled
- no approval API/storage enabled
- no queue updates added
- no application submission added
- `workflow_runner.py` remains dry-run only
- preflight `executable_adapter_count` remains 0

## Forbidden Next-Step Shortcuts

- Do not add `blocked_application_submission_request_minimal.json` next unless 83B passes and explicit approval is given.
- Do not wire validator into workflow_runner next.
- Do not wire validator into live planning next.
- Do not auto-discover fixture directories next.
- Do not add DB writes, queue mutation, storage APIs, migrations, mutation execution, or live execution next.
- Do not add approval APIs or approval storage next.
- Do not add application submission next.
- Do not add automatic fixture validation next.
- Do not add fixture execution next.

## Explicit Non-Goals

- no fixture payload file implementation in this phase
- no fixture payload JSON changes in this phase
- no validator code changes in this phase
- no CLI code changes in this phase
- no fixture validator tests in this phase beyond docs assertions
- no CLI tests in this phase
- no runtime implementation in this phase
- no workflow_runner integration in this phase
- no live planning integration in this phase
- no app services integration in this phase
- no queue integration in this phase
- no fixture discovery in runtime
- no automatic fixture validation
- no fixture execution
- no runtime failure-mode tests
- no storage integration tests
- no DB schema/migration
- no SQL DDL
- no storage API
- no runtime DB writes
- no queue mutation
- no mutation execution
- no live execution
- no approval API/storage
- no application submission

## Recommended Next Phase

Recommended next phase: 83B third synthetic fixture payload implementation plan final audit and merge gate.

After 83B: 84A third synthetic fixture payload implementation plan release safety checkpoint, docs/tests only.

Do not add `blocked_application_submission_request_minimal.json` next unless 83B passes and explicit approval is given. Do not wire validator into workflow_runner next. Do not wire validator into live planning next. Do not auto-discover fixture directories next. Do not add DB writes, queue mutation, storage APIs, migrations, mutation execution, or live execution next.
