# Fixture Validator Implementation Plan

Doc path: `docs/fixture_validator_implementation_plan.md`

Phase 63A is a fixture validator implementation plan only. There is no implementation in this phase. No fixture validator code is added. No fixture validator module is added. No fixture validator CLI is added. No fixture validator tests are added. No fixture files are added. No fixture directory is added. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Implementation-Plan Scope

The fixture validator contract design exists at `docs/fixture_validator_contract_design.md`.

The fixture validator contract release safety checkpoint exists at `docs/fixture_validator_contract_release_safety_checkpoint.md`.

The fixture file implementation plan exists at `docs/fixture_file_implementation_plan.md`.

The fixture file implementation plan release safety checkpoint exists at `docs/fixture_file_implementation_plan_release_safety_checkpoint.md`.

Future fixture validator remains future work. Future fixture files remain proposed only. The future fixture directory remains proposed only:

- `tests/fixtures/agentic_storage_transaction_failure_modes/`

No fixture validator implementation exists. No fixture validator module exists. No fixture validator CLI exists. No fixture validator tests exist. No fixture directories are created. No fixture files are created.

Current runtime tooling remains explicit/manual/read-only/non-mutating:

- read-only chain artifact generator
- dry-run execution simulator
- proposal-only mutation planner
- Agentic Review diagnostic display

## Confirmed Safe Boundaries

Confirmed boundaries for this implementation plan:

- no fixture validator code
- no fixture validator module
- no fixture validator CLI
- no fixture validator tests
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

## Fixture Validator Implementation Plan Decision

- Fixture validator implementation plan: `PASS`
- Fixture validator implementation: `NOT_YET`
- Fixture validator module: `NOT_YET`
- Fixture validator CLI: `NOT_YET`
- Fixture validator tests: `NOT_YET`
- Fixture file implementation: `NOT_YET`
- Fixture directory creation: `NOT_YET`
- Runtime failure-mode tests: `NO_GO`
- Storage integration tests: `NO_GO`
- Transaction integration tests: `NO_GO`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Future Validator Implementation Sequence

Future validator implementation should proceed only in separately approved phases:

1. confirm fixture file implementation plan release checkpoint passed
2. confirm fixture directory creation and fixture file phases are separately approved and complete
3. add validator module in a separately approved implementation phase
4. add validator CLI only if separately approved
5. validate synthetic fixture metadata only
6. validate fixture schema version, fixture family, expected result, expected reason codes, and safety flags
7. reject production paths, live queue paths, application submission targets, secrets, credentials, raw resumes, and private documents
8. keep validator non-mutating and local-only
9. add validator tests only after validator implementation is separately approved
10. add runtime failure-mode tests only after fixture files and validator are separately audited
11. audit branch before merge

None of these steps happen in this phase.

## Future Validator Module Boundary

Future module boundaries only:

- validator must not execute fixture payloads
- validator must not call workflow_runner
- validator must not call proposal planner
- validator must not call dry-run simulator
- validator must not call read-only chain generator
- validator must not call storage APIs
- validator must not write DB
- validator must not mutate queue state
- validator must not submit applications
- validator must not make network calls
- validator must not require external services
- validator must not infer missing safety fields as safe
- validator must fail closed on unknown fixture families
- validator must fail closed on unknown reason codes
- validator must produce deterministic sorted reason codes

## Future Validator Input Contract Enforcement

Future validator will enforce:

- fixture_schema_version
- fixture_family
- fixture_id
- fixture_name
- expected_result
- expected_reason_codes
- expected_blocked
- expected_did_mutate
- expected_did_write_db
- expected_no_secret_leakage
- expected_validator_reason_codes
- synthetic_context_metadata
- source_fixture_ref
- artifact_refs_json
- payload_hash

## Future Validator Output Contract Enforcement

Future validator output will include:

- validator_version
- validation_status
- fixture_family
- fixture_id
- fixture_name
- checked_at_utc
- reason_codes
- warning_codes
- missing_required_fields
- forbidden_field_hits
- privacy_redaction_findings
- deterministic_ordering_status
- production_path_status
- mutation_expectation_status
- db_write_expectation_status
- fixture_execution_status
- summary
- did_execute_fixture=false
- did_mutate_production=false
- did_write_db=false

## Future Validator Safety Checks

Future validator safety checks:

- schema version present
- fixture family present
- fixture family allowed
- expected_result present
- expected_reason_codes present
- expected_blocked boolean present
- expected_did_mutate=false for unsafe cases
- expected_did_write_db=false for unavailable storage cases
- expected_no_secret_leakage=true for privacy cases
- no real identifiers
- no production paths
- no live queue paths
- no application submission targets
- no secret/token/credential fields
- no raw resume payloads
- no full private document payloads
- deterministic ordering
- reason codes are stable and sorted
- fixture names are lowercase snake_case
- forbidden mutation fixtures are expected blocked
- allowed mutation proposal fixture types are still non-executable and blocked by default

## Future Validator Command Policy

Future policy only:

- validator execution must be explicit and reviewable
- no automatic validator invocation from runtime planning
- no background validator execution
- no validator execution during application planning
- no validator execution from workflow_runner live path
- no generated fixtures
- no production-derived fixture payloads
- no network calls
- no DB writes
- no queue mutation
- no application submission
- no approval/mutation side effects
- validator output must be local and deterministic

## Fixture Validator Implementation Blockers

- fixture validator implementation plan final audit passed
- fixture file implementation plan release checkpoint passed
- fixture directory creation implementation plan release checkpoint passed
- fixture directory skeleton release checkpoint passed
- fixture implementation plan release checkpoint passed
- fixture naming and reason-code taxonomy release checkpoint passed
- fixture validator contract release checkpoint passed
- fixture design release checkpoint passed
- privacy/no-secret strategy approved
- no-production-path strategy approved
- fixture file creation phase explicitly approved and complete
- fixture validator implementation phase separately approved
- runtime test scope separately approved before runtime tests

## Forbidden Next-Step Shortcuts

- do not implement fixture validators next without a separate approved validator implementation phase
- do not add fixture validator tests next without validator implementation approval
- do not add fixture files next without a separate approved fixture file implementation phase
- do not create fixture directories next without a separate approved directory creation implementation phase
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

- no validator implementation in this phase
- no validator module in this phase
- no validator CLI in this phase
- no validator tests in this phase
- no fixture files in this phase
- no fixture directories in this phase
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

Recommended next phase: 63B fixture validator implementation plan final audit and merge gate.

After 63B: 64A fixture validator implementation plan release safety checkpoint, docs/tests only.

Do not implement fixture validators next. Do not add fixture validator tests next. Do not add fixture files next. Do not create fixture directories next. Do not add runtime tests next. Do not implement migrations, storage APIs, DB writes, mutation, or live execution next.
