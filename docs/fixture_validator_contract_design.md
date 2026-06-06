# Fixture Validator Contract Design

Doc path: `docs/fixture_validator_contract_design.md`

Phase 51A is fixture validator contract design only. There is no implementation in this phase. No fixture validator code is added. No fixture files are added. No fixture directory is added. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Contract Scope

The storage/transaction failure fixture design doc exists at `docs/storage_transaction_failure_fixture_design.md`.

The fixture release safety checkpoint exists at `docs/storage_transaction_fixture_release_safety_checkpoint.md`.

The fixture naming and reason-code taxonomy checkpoint is tracked in `docs/fixture_naming_reason_code_taxonomy_checkpoint.md`.

Fixture families are proposed only. The future fixture directory is proposed only:

- `tests/fixtures/agentic_storage_transaction_failure_modes/`

No fixture validator implementation exists. No fixture files are created. No fixture directories are created. Current runtime tooling remains explicit/manual/read-only/non-mutating:

- read-only chain artifact generator
- dry-run execution simulator
- proposal-only mutation planner
- Agentic Review diagnostic display

## Confirmed Safe Boundaries

Confirmed boundaries for this contract design:

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

## Fixture Validator Contract Design Decision

- Fixture validator contract design: `PASS`
- Fixture validator implementation: `NOT_YET`
- Fixture files: `NO_GO`
- Fixture directory creation: `NO_GO`
- Runtime failure-mode tests: `NO_GO`
- Storage integration tests: `NO_GO`
- Transaction integration tests: `NO_GO`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Contract Goals

The future fixture validator contract should:

- validate future fixture structure before runtime tests exist
- fail closed on missing required fields
- produce deterministic reason codes
- validate safety expectations without executing fixtures
- reject real identifiers, production paths, secrets, credentials, raw resumes, and full private documents
- validate expected non-mutating behavior
- keep validator output diagnostic-only
- avoid DB writes and runtime side effects
- keep future implementation explicit/manual only unless separately approved

## Proposed Validator Input Contract

Future validator input should accept an explicit fixture object or future fixture file path only. It must not discover production paths, live queue paths, real application URLs, raw private documents, raw resumes, secrets, or credentials.

Proposed input fields:

- `fixture_schema_version`
- `fixture_family`
- `fixture_id`
- `fixture_name`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`
- `expected_did_mutate`
- `expected_did_write_db`
- `expected_no_secret_leakage`
- `expected_validator_reason_codes`
- `synthetic_context_metadata`
- `source_fixture_ref`
- `artifact_refs_json`
- `payload_hash`

Input safety expectations:

- explicit fixture object or future fixture file path only
- no production paths
- no live queue paths
- no real application URLs
- no raw private documents
- no raw resumes
- no secrets or credentials

## Proposed Validator Output Contract

Future validator output should be diagnostic-only and non-mutating.

Proposed output fields:

- `validator_version`
- `validation_status`
- `fixture_family`
- `fixture_id`
- `fixture_name`
- `checked_at_utc`
- `reason_codes`
- `warning_codes`
- `missing_required_fields`
- `forbidden_field_hits`
- `privacy_redaction_findings`
- `deterministic_ordering_status`
- `production_path_status`
- `mutation_expectation_status`
- `db_write_expectation_status`
- `fixture_execution_status`
- `summary`
- `did_execute_fixture=false`
- `did_mutate_production=false`
- `did_write_db=false`

## Required Validator Checks

Future validator checks should include:

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
- fixture names are lowercase snake_case when applicable
- forbidden mutation fixtures are expected blocked
- allowed mutation proposal fixture types are still non-executable and blocked by default

## Proposed Validator Reason Code Groups

Future validator reason code groups should include:

- `missing_required_field`
- `unknown_fixture_family`
- `invalid_fixture_schema_version`
- `unsafe_expected_mutation`
- `unsafe_expected_db_write`
- `forbidden_mutation_type`
- `real_identifier_detected`
- `production_path_detected`
- `live_queue_path_detected`
- `application_submission_target_detected`
- `secret_like_value_detected`
- `credential_field_detected`
- `raw_private_document_detected`
- `raw_resume_payload_detected`
- `nondeterministic_ordering`
- `missing_expected_reason_codes`
- `invalid_expected_blocked_flag`
- `fixture_execution_forbidden`
- `storage_write_forbidden`

## Fixture Family Coverage

This is design-only coverage. No fixture files are implemented.

- `execution_request_fixtures`
- `execution_plan_fixtures`
- `mutation_proposal_fixtures`
- `approval_record_fixtures`
- `idempotency_record_fixtures`
- `execution_lock_fixtures`
- `audit_ledger_entry_fixtures`
- `rollback_plan_fixtures`
- `execution_attempt_fixtures`
- `validation_result_fixtures`
- `forbidden_mutation_fixtures`
- `concurrency_collision_fixtures`
- `stale_artifact_version_fixtures`
- `storage_unavailable_fixtures`
- `security_privacy_redaction_fixtures`

## Allowed Safe Mutation Proposal Fixture Types

Allowed safe mutation proposal fixture types remain:

- `queue_diagnostic_status_marker`
- `operator_note`
- `artifact_status_marker`

They are still non-executable and blocked by default until a separately approved implementation phase.

## Forbidden Mutation Fixture Coverage

Forbidden mutation fixture coverage must include:

- `application_submission`
- `queue_action_update`
- `tailoring_generation`
- `packet_generation`
- `scoring_update`
- `ranking_update`
- `resume_rewrite`
- `scraper_source_mutation`
- `rag_corpus_mutation`
- `production_record_delete`

These must validate as blocked/rejected and must never execute.

## Required Blockers Before Validator Implementation

Required blockers before validator implementation:

- fixture validator contract design final audit passed
- fixture design release checkpoint passed
- storage schema proposal release checkpoint passed
- failure-mode test plan approved
- transaction boundary design approved
- storage design review approved
- privacy/no-secret strategy approved
- no-production-path strategy approved
- fixture naming approved
- reason code taxonomy approved
- implementation phase explicitly approved
- runtime test scope separately approved before runtime tests

## Forbidden Next-Step Shortcuts

- do not implement fixture validators next without a separate implementation phase
- do not add fixture files next
- do not create fixture directories next
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

Recommended next phase: 51B fixture validator contract design final audit and merge gate.

After 51B: 52A fixture validator contract release safety checkpoint, docs/tests only.

The fixture validator contract release safety checkpoint is tracked in `docs/fixture_validator_contract_release_safety_checkpoint.md`.

The future fixture validator implementation plan is tracked in `docs/fixture_validator_implementation_plan.md`.

The fixture validator implementation plan release safety checkpoint is tracked in `docs/fixture_validator_implementation_plan_release_safety_checkpoint.md`.

The fixture validator implementation design refinement is tracked in `docs/fixture_validator_implementation_design_refinement.md`.

Do not add fixture files next. Do not add runtime tests next. Do not implement fixture validators next without a separate approved phase. Do not implement migrations, storage APIs, DB writes, mutation, or live execution next.
