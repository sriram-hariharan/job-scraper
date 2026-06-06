# Fixture Directory Creation Implementation

Doc path: `docs/fixture_directory_creation_implementation.md`

Phase 71A is fixture directory creation implementation only. The fixture directory now exists intentionally. No fixture payload files are added. Only the `.gitkeep` marker is added. No fixture validator code is added. No fixture validator module is added. No fixture validator CLI is added. No fixture validator tests are added. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Implementation Scope

- Fixture directory creation implementation: `PASS`
- Directory created: `tests/fixtures/agentic_storage_transaction_failure_modes/`
- Marker file added: `tests/fixtures/agentic_storage_transaction_failure_modes/.gitkeep`
- Fixture payload files: `NOT_YET`
- Fixture validator implementation: `NOT_YET`
- Fixture validator tests: `NOT_YET`
- Runtime failure-mode tests: `NO_GO`
- Storage integration tests: `NO_GO`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Safe Directory Boundary

- directory exists only as a future fixture location
- `.gitkeep` is not a fixture payload
- no test should execute from this directory yet
- no runtime should read from this directory yet
- no generator should write to this directory
- no validator should run against this directory yet
- no fixture file discovery should be wired into runtime
- no workflow_runner execution path should reference this directory
- no live planning path should reference this directory

## Allowed Current Contents

Only this path is allowed in the directory during this phase:

- `tests/fixtures/agentic_storage_transaction_failure_modes/.gitkeep`

## Forbidden Current Contents

These contents are forbidden in this phase:

- JSON fixture files
- CSV fixture files
- YAML fixture files
- TXT fixture files
- Markdown fixture payload files
- generated fixture files
- production-derived fixture files
- private documents
- raw resumes
- secrets or credentials
- runtime test files
- validator test files

## Future Fixture File Entry Criteria

Fixture files may only be added after:

- fixture directory creation implementation final audit passed
- fixture directory creation implementation release safety checkpoint passed
- fixture file implementation plan final audit passed
- fixture file implementation plan release checkpoint passed
- fixture file implementation phase separately approved
- privacy/no-secret strategy approved
- no-production-path strategy approved
- exact fixture file allowlist approved
- fixture payload schema approved
- fixture validator implementation separately approved or explicitly deferred with user approval

## Forbidden Next-Step Shortcuts

- do not add fixture payload files next without explicit fixture file implementation approval
- do not implement fixture validators next without explicit validator implementation approval
- do not add fixture validator tests next
- do not add runtime failure-mode tests next
- do not add storage integration tests next
- do not add DB schema files next
- do not add migrations next
- do not add SQL DDL next
- do not add storage APIs next
- do not add approval APIs next
- do not add mutation APIs next
- do not add DB writes next
- do not add live queue updates next
- do not start application submission automation next
- do not enable workflow_runner live execution next

## Explicit Non-Goals

- no fixture payloads
- no validator implementation
- no validator tests
- no runtime tests
- no storage integration tests
- no DB schema/migration
- no SQL DDL
- no storage module
- no API routes
- no approval actions
- no mutation execution
- no live queue updates
- no application submission

## Recommended Next Phase

Recommended next phase: 71B fixture directory creation implementation final audit and merge gate.

After 71B: 72A fixture directory creation implementation release safety checkpoint, docs/tests only.

The 72A release safety checkpoint is tracked in `docs/fixture_directory_creation_implementation_release_safety_checkpoint.md`.

Do not add fixture payload files next. Do not implement fixture validators next. Do not add validator tests next. Do not add runtime tests next.
