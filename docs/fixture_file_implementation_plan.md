# Fixture File Implementation Plan

Doc path: `docs/fixture_file_implementation_plan.md`

Phase 61A is a fixture file implementation plan only. There is no implementation in this phase. No fixture validator code is added. No fixture files are added. No fixture directory is added. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Implementation-Plan Scope

The fixture directory creation implementation plan exists at `docs/fixture_directory_creation_implementation_plan.md`.

The fixture directory creation implementation plan release checkpoint exists at `docs/fixture_directory_creation_implementation_plan_release_safety_checkpoint.md`.

Future fixture files remain future work. The future fixture directory remains proposed only:

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

## Fixture File Implementation Plan Decision

- Fixture file implementation plan: `PASS`
- Fixture file implementation: `NOT_YET`
- Fixture directory creation: `NOT_YET`
- Fixture validator implementation: `NOT_YET`
- Runtime failure-mode tests: `NO_GO`
- Storage integration tests: `NO_GO`
- Transaction integration tests: `NO_GO`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Future Fixture File Implementation Sequence

Future fixture file implementation should proceed only in separately approved phases:

1. confirm fixture directory creation phase is approved and complete
2. add fixture README before any JSON fixture files
3. add safe synthetic metadata-only fixture files in a separately approved phase
4. add unsafe/forbidden mutation fixture files in a separately approved phase
5. add security/privacy redaction fixture files in a separately approved phase
6. add storage-unavailable and concurrency fixture files in separately approved phases
7. add fixture validator implementation only after fixture file structure is audited
8. add runtime tests only after fixture files and validator are separately approved
9. audit branch before merge

None of these steps happen in this phase.

## Future Fixture File Categories

Future-only fixture categories:

- safe execution request fixtures
- safe execution plan fixtures
- safe mutation proposal fixtures
- forbidden mutation fixtures
- idempotency duplicate fixtures
- idempotency conflict fixtures
- execution lock collision fixtures
- audit ledger missing-entry fixtures
- rollback plan missing fixtures
- stale artifact version fixtures
- storage unavailable fixtures
- concurrency collision fixtures
- security/privacy redaction fixtures

No fixture file is created in this phase.

## Future Fixture File Admission Checklist

Before any fixture file is added, require:

- synthetic-only data
- lowercase snake_case filename
- approved fixture family
- approved reason codes
- no real identifiers
- no production paths
- no live queue paths
- no application submission target
- no raw resume payload
- no full private document
- no secrets or credentials
- expected_result present
- expected_reason_codes present
- expected_blocked present
- expected_did_mutate=false
- expected_did_write_db=false
- expected_no_secret_leakage=true for privacy cases
- fixture_schema_version present
- fixture_id synthetic and deterministic
- payload_hash deterministic or explicitly omitted until validator phase
- artifact_refs_json synthetic only

## Future Fixture File Command Policy

Future policy only:

- fixture file creation must be explicit and reviewable
- no generated fixture files without explicit approval
- no bulk fixture generation
- no production-derived fixture payloads
- no hidden fixture files
- no `.keep` placeholders unless separately approved
- no absolute filesystem paths
- no network paths
- no live queue paths
- no DB write paths
- no application submission paths
- no scripts that auto-populate fixtures
- no runtime test invocation from fixture file creation

## Proposed Future Fixture Filename Examples

Examples only; these files are not created in this phase:

- `safe_execution_request_minimal.json`
- `safe_execution_plan_metadata_only.json`
- `safe_mutation_proposal_operator_note.json`
- `safe_mutation_proposal_artifact_status_marker.json`
- `unsafe_mutation_proposal_application_submission.json`
- `unsafe_mutation_proposal_queue_action_update.json`
- `idempotency_duplicate_same_payload.json`
- `idempotency_duplicate_conflicting_payload.json`
- `execution_lock_collision_same_target.json`
- `audit_ledger_pre_attempt_missing.json`
- `rollback_plan_missing_required.json`
- `stale_artifact_version_proposal.json`
- `storage_unavailable_write_blocked.json`
- `concurrency_collision_retry_blocked.json`
- `secret_leakage_payload_redaction_case.json`
- `raw_resume_payload_redaction_case.json`

## Fixture File Implementation Blockers

- fixture file implementation plan final audit passed
- fixture directory creation implementation plan release checkpoint passed
- fixture directory skeleton release checkpoint passed
- fixture implementation plan release checkpoint passed
- fixture naming and reason-code taxonomy release checkpoint passed
- fixture validator contract release checkpoint passed
- fixture design release checkpoint passed
- privacy/no-secret strategy approved
- no-production-path strategy approved
- fixture file creation phase explicitly approved
- fixture validator implementation phase separately approved
- runtime test scope separately approved before runtime tests

## Forbidden Next-Step Shortcuts

- do not add fixture files next without a separate approved fixture file implementation phase
- do not create fixture directories next without a separate approved directory creation implementation phase
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

- no fixture files in this phase
- no fixture directories in this phase
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

Recommended next phase: 61B fixture file implementation plan final audit and merge gate.

After 61B: 62A fixture file implementation plan release safety checkpoint, docs/tests only.

The 62A release safety checkpoint is tracked in `docs/fixture_file_implementation_plan_release_safety_checkpoint.md`.

The 63A fixture validator implementation plan is tracked in `docs/fixture_validator_implementation_plan.md`.

The first synthetic fixture payload implementation is tracked in `docs/first_synthetic_fixture_payload_implementation.md`.

Do not add fixture files next. Do not create fixture directories next. Do not implement fixture validators next. Do not add runtime tests next. Do not implement migrations, storage APIs, DB writes, mutation, or live execution next.
