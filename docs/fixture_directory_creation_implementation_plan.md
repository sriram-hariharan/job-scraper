# Fixture Directory Creation Implementation Plan

Doc path: `docs/fixture_directory_creation_implementation_plan.md`

Phase 59A is a fixture directory creation implementation plan only. There is no implementation in this phase. No fixture validator code is added. No fixture files are added. No fixture directory is added. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Implementation-Plan Scope

The fixture directory skeleton design exists at `docs/fixture_directory_skeleton_design.md`.

The fixture directory skeleton release checkpoint exists at `docs/fixture_directory_skeleton_release_safety_checkpoint.md`.

Future directory creation remains future work. The future fixture directory remains proposed only:

- `tests/fixtures/agentic_storage_transaction_failure_modes/`

No fixture directories are created. No fixture files are created. No fixture validator implementation exists. Current runtime tooling remains explicit/manual/read-only/non-mutating:

- read-only chain artifact generator
- dry-run execution simulator
- proposal-only mutation planner
- Agentic Review diagnostic display

## Confirmed Safe Boundaries

Confirmed boundaries for this implementation plan:

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

## Fixture Directory Creation Implementation Plan Decision

- Fixture directory creation implementation plan: `PASS`
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

## Future Directory Creation Sequence

Future directory creation should proceed only in a separately approved implementation phase:

1. create parent fixture directory in separately approved implementation phase
2. create fixture README in separately approved implementation phase
3. create approved fixture family subdirectories in separately approved implementation phase
4. add no fixture JSON files until a later separately approved phase
5. run docs/tests validation after directory creation
6. run no runtime fixture tests until validator and fixture files are separately approved
7. audit branch before merge

None of these steps happen in this phase.

## Future Directory Creation Command Policy

Future policy only:

- directory creation must be explicit and reviewable
- no generated fixture files during directory creation
- no placeholder JSON files
- no `.keep` files unless separately approved
- no hidden files
- no production paths
- no live queue paths
- no DB write paths
- no application submission paths
- no scripts that auto-populate fixtures
- no runtime test invocation from directory creation

## Approved Future Directory List

Future-only directories:

- `tests/fixtures/agentic_storage_transaction_failure_modes/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/execution_request_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/mutation_proposal_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/idempotency_record_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/execution_lock_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/audit_ledger_entry_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/rollback_plan_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/forbidden_mutation_fixtures/`
- `tests/fixtures/agentic_storage_transaction_failure_modes/security_privacy_redaction_fixtures/`

These directories are not created in this phase.

## Future Fixture README Content Plan

The future README should include:

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
- directory ownership rules
- review requirements before adding fixture files

## Directory Creation Blockers

- fixture directory creation implementation plan final audit passed
- fixture directory skeleton release checkpoint passed
- fixture implementation plan release checkpoint passed
- fixture naming and reason-code taxonomy release checkpoint passed
- fixture validator contract release checkpoint passed
- fixture design release checkpoint passed
- privacy/no-secret strategy approved
- no-production-path strategy approved
- directory creation phase explicitly approved
- fixture file phase separately approved
- runtime test scope separately approved before runtime tests

## Forbidden Next-Step Shortcuts

- do not create fixture directories next without a separate approved directory creation implementation phase
- do not add fixture files next without a fixture file implementation phase
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

Recommended next phase: 59B fixture directory creation implementation plan final audit and merge gate.

After 59B: 60A fixture directory creation implementation plan release safety checkpoint, docs/tests only.

Do not create fixture directories next. Do not add fixture files next. Do not implement fixture validators next. Do not add runtime tests next. Do not implement migrations, storage APIs, DB writes, mutation, or live execution next.
