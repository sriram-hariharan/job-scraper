# Fixture Directory Skeleton Design

Doc path: `docs/fixture_directory_skeleton_design.md`

Phase 57A is a fixture directory skeleton design only. There is no implementation in this phase. No fixture validator code is added. No fixture files are added. No fixture directory is added. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Skeleton-Design Scope

The fixture implementation plan exists at `docs/fixture_implementation_plan.md`.

The fixture implementation plan release checkpoint exists at `docs/fixture_implementation_plan_release_safety_checkpoint.md`.

The fixture directory skeleton remains future work. The future fixture directory remains proposed only:

- `tests/fixtures/agentic_storage_transaction_failure_modes/`

No fixture validator implementation exists. No fixture files are created. No fixture directories are created. Current runtime tooling remains explicit/manual/read-only/non-mutating:

- read-only chain artifact generator
- dry-run execution simulator
- proposal-only mutation planner
- Agentic Review diagnostic display

## Confirmed Safe Boundaries

Confirmed boundaries for this skeleton design:

- no fixture validator code
- no fixture files
- no fixture directory creation
- no runtime failure-mode tests
- no storage integration tests
- no DB schema files
- no migrations
- no SQL DDL
- no storage modules
- no storage API
- no DB writes
- no approval API/storage
- no mutation API/storage
- no audit ledger storage
- no idempotency store
- no execution lock store
- no transaction implementation
- no scheduler/background execution
- no workflow_runner execution
- no live planning hooks
- no application submission

## Fixture Directory Skeleton Design Decision

- Fixture directory skeleton design: `PASS`
- Fixture directory creation: `NOT_YET`
- Fixture file implementation: `NOT_YET`
- Fixture validator implementation: `NOT_YET`
- Runtime failure-mode tests: `NO_GO`
- Storage integration tests: `NO_GO`
- Transaction integration tests: `NO_GO`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Proposed Future Directory Skeleton

Future layout only:

- `tests/fixtures/agentic_storage_transaction_failure_modes/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/README.md`
- `tests/fixtures/agentic_storage_transaction_failure_modes/execution_request_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/mutation_proposal_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/idempotency_record_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/execution_lock_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/audit_ledger_entry_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/rollback_plan_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/forbidden_mutation_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/security_privacy_redaction_fixtures/`

No directory or file is created in this phase.

## Directory Ownership And Naming Rules

- directory names must be lowercase snake_case
- directory names must match approved fixture families
- directory names must not include timestamps
- directory names must not include production identifiers
- directory names must not include company names or person names
- directory names must not imply live execution
- directory names must not imply DB writes
- new fixture family directories require docs/tests update before creation

## Future Fixture README Requirements

The future fixture README should document:

- synthetic-only rule
- no production data
- no secrets or credentials
- no raw resumes
- no full private documents
- no live queue paths
- no application submission targets
- allowed fixture families
- approved reason-code taxonomy
- admission checklist
- validator expectations
- non-execution guarantee

## Skeleton Creation Blockers

- fixture directory skeleton design final audit passed
- fixture implementation plan release checkpoint passed
- fixture naming and reason-code taxonomy release checkpoint passed
- fixture validator contract release checkpoint passed
- fixture design release checkpoint passed
- privacy/no-secret strategy approved
- no-production-path strategy approved
- implementation phase explicitly approved
- runtime test scope separately approved before runtime tests

## Forbidden Next-Step Shortcuts

- do not create fixture directories next without a separate implementation phase
- do not add fixture files next without a fixture implementation phase
- do not implement fixture validators next without a separate implementation phase
- do not add runtime failure-mode tests next
- do not add storage integration tests next
- do not add DB schema files next
- do not add Alembic/migration files next
- do not add SQL DDL next
- do not add storage modules next
- do not add approval APIs next
- do not add mutation APIs next
- do not add DB writes next
- do not add live queue updates next
- do not start application submission automation next
- do not enable workflow_runner live execution next

## Explicit Non-Goals

- no fixture directories in this phase
- no fixture files in this phase
- no validator implementation in this phase
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

Recommended next phase: 57B fixture directory skeleton design final audit and merge gate.

After 57B: 58A fixture directory skeleton design release safety checkpoint, docs/tests only.

Do not create fixture directories next. Do not add fixture files next. Do not implement fixture validators next. Do not add runtime tests next. Do not implement migrations, storage APIs, DB writes, mutation, or live execution next.
