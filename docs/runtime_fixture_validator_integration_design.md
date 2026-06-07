# Runtime Fixture Validator Integration Design

Doc path: `docs/runtime_fixture_validator_integration_design.md`

Phase 79A is runtime-facing fixture validator integration design only. No runtime integration is implemented. No workflow_runner integration is implemented. No live planning integration is implemented. No app services integration is implemented. No queue integration is implemented. No fixture discovery in runtime is implemented. No automatic fixture validation is implemented. No fixture execution is implemented. No additional fixture payload files are added. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are added. No application submission is added.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Design Scope

- Runtime-facing fixture validator integration design: `PASS`
- Runtime integration implementation: `NOT_YET`
- Workflow runner integration: `NOT_YET`
- Live planning integration: `NOT_YET`
- App services integration: `NOT_YET`
- Queue integration: `NOT_YET`
- Fixture discovery in runtime: `NOT_YET`
- Automatic fixture validation: `NOT_YET`
- Fixture execution: `NO_GO`
- Runtime failure-mode tests: `NO_GO`
- Storage integration tests: `NO_GO`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Existing Safe Validator Assets

- `src/agents/fixture_validator.py` exists and is read-only
- `src/agents/fixture_validator_cli.py` exists and is manual-only
- `tests/test_fixture_validator.py` exists
- `tests/test_fixture_validator_cli.py` exists
- safe fixture exists: `tests/fixtures/agentic_storage_transaction_failure_modes/safe_execution_request_minimal.json`
- fixture directory contains only `.gitkeep` and `safe_execution_request_minimal.json`

## Future Integration Boundary

This is design only. A future integration must:

- be explicitly approved in a later phase
- use explicit allowlisted fixture paths
- remain read-only
- not execute fixture payloads
- not mutate queue items
- not write to DB
- not submit applications
- not call external systems
- not run automatically during live planning
- not enable workflow_runner live execution
- not change scoring/ranking/filtering/resume/tailoring behavior
- preserve stage-level logging and observability if later implemented

## Proposed Future Integration Points

- preflight-only fixture validator check
  - implementation status: `NOT_YET`
  - mutation allowed: false
  - DB writes allowed: false
  - live execution allowed: false
  - application submission allowed: false
- CI-only fixture validator check
  - implementation status: `NOT_YET`
  - mutation allowed: false
  - DB writes allowed: false
  - live execution allowed: false
  - application submission allowed: false
- manual CLI validation before release
  - implementation status: `NOT_YET`
  - mutation allowed: false
  - DB writes allowed: false
  - live execution allowed: false
  - application submission allowed: false
- optional dry-run-only workflow validation gate
  - implementation status: `NOT_YET`
  - mutation allowed: false
  - DB writes allowed: false
  - live execution allowed: false
  - application submission allowed: false
- documentation/test-only contract checks
  - implementation status: `NOT_YET`
  - mutation allowed: false
  - DB writes allowed: false
  - live execution allowed: false
  - application submission allowed: false

## Required Future Approval Gates

Future runtime integration requires:

- explicit runtime integration approval
- exact file allowlist
- exact function allowlist
- exact call-site allowlist
- explicit no-DB-write confirmation
- explicit no-queue-mutation confirmation
- explicit no-application-submission confirmation
- explicit workflow_runner dry-run-only preservation plan
- rollback plan
- observability/logging plan
- focused tests approved before implementation
- release safety checkpoint after implementation

## Forbidden Runtime Shortcuts

- do not import validator into workflow_runner next
- do not import validator into live planning next
- do not import validator into app services next
- do not import validator into queue processing next
- do not auto-discover fixture directories next
- do not validate fixtures automatically during application planning next
- do not add DB writes next
- do not add queue mutation next
- do not add approval APIs next
- do not add mutation APIs next
- do not add application submission automation next
- do not enable workflow_runner live execution next

## Non-Goals

- no runtime implementation in this phase
- no workflow_runner integration in this phase
- no live planning integration in this phase
- no app service integration in this phase
- no queue integration in this phase
- no new fixture payload files in this phase
- no runtime tests in this phase
- no storage integration tests in this phase
- no DB schema/migration
- no SQL DDL
- no storage module
- no API routes
- no approval actions
- no mutation execution
- no live queue updates
- no application submission

## Recommended Next Phase

Recommended next phase: 79B runtime-facing fixture validator integration design final audit and merge gate.

After 79B: 80A runtime-facing fixture validator integration design release safety checkpoint, docs/tests only.

Do not implement runtime integration next. Do not wire validator into workflow_runner next. Do not wire validator into live planning next. Do not add runtime tests next. Do not implement migrations, storage APIs, DB writes, mutation, or live execution next.
