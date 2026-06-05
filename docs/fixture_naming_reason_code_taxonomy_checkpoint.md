# Fixture Naming And Reason-Code Taxonomy Checkpoint

Doc path: `docs/fixture_naming_reason_code_taxonomy_checkpoint.md`

Phase 53A is a naming and reason-code taxonomy checkpoint only. There is no implementation in this phase. No fixture validator code is added. No fixture files are added. No fixture directory is added. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Checkpoint Scope

The fixture validator contract design exists at `docs/fixture_validator_contract_design.md`.

The fixture validator contract release checkpoint exists at `docs/fixture_validator_contract_release_safety_checkpoint.md`.

Fixture naming is proposed only. Reason-code taxonomy is proposed only. Fixture families remain proposed only. The future fixture directory remains proposed only:

- `tests/fixtures/agentic_storage_transaction_failure_modes/`

No fixture validator implementation exists. No fixture files are created. No fixture directories are created. Current runtime tooling remains explicit/manual/read-only/non-mutating:

- read-only chain artifact generator
- dry-run execution simulator
- proposal-only mutation planner
- Agentic Review diagnostic display

## Confirmed Safe Boundaries

Confirmed boundaries for this checkpoint:

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

## Naming And Reason-Code Taxonomy Decision

- Taxonomy checkpoint: `PASS`
- Fixture naming convention: `GO`
- Validator reason-code taxonomy: `GO`
- Fixture validator implementation: `NO_GO`
- Fixture files: `NO_GO`
- Fixture directory creation: `NO_GO`
- Runtime failure-mode tests: `NO_GO`
- Storage integration tests: `NO_GO`
- Transaction integration tests: `NO_GO`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Fixture Naming Convention

Future fixture naming rules:

- lowercase snake_case
- no spaces
- no uppercase letters
- no timestamps in fixture names unless explicitly approved
- no real company names
- no real person names
- no production IDs
- no live queue IDs
- names must include fixture family or failure mode
- names must end in `.json` unless separately approved
- forbidden mutation cases must start with `unsafe_`
- safe proposal cases must start with `safe_`
- collision cases should include `collision`
- expired/revoked/stale cases should include the failure state
- privacy/security cases should include `redaction`, `secret`, `credential`, `private_document`, or `raw_resume` as applicable

## Proposed Fixture Filename Examples

These examples are not created in this phase:

- `safe_execution_request_minimal.json`
- `safe_mutation_proposal_operator_note.json`
- `safe_mutation_proposal_artifact_status_marker.json`
- `unsafe_mutation_proposal_application_submission.json`
- `unsafe_mutation_proposal_queue_action_update.json`
- `idempotency_duplicate_same_payload.json`
- `idempotency_duplicate_conflicting_payload.json`
- `execution_lock_collision_same_target.json`
- `approval_expired_record.json`
- `approval_revoked_record.json`
- `approval_scope_mismatch_record.json`
- `audit_ledger_pre_attempt_missing.json`
- `audit_ledger_post_attempt_failure.json`
- `rollback_plan_missing_required.json`
- `rollback_attempt_failed.json`
- `stale_artifact_version_proposal.json`
- `secret_leakage_payload_redaction_case.json`

## Reason-Code Taxonomy Groups

Stable future reason-code groups:

- `required_field`
- `schema_version`
- `fixture_family`
- `safety_expectation`
- `mutation_policy`
- `privacy_security`
- `production_path`
- `deterministic_ordering`
- `fixture_execution`
- `storage_write`
- `approval_scope`
- `idempotency`
- `execution_lock`
- `audit_ledger`
- `rollback`
- `stale_artifact`
- `concurrency_retry`

## Required Reason Codes

Required future validator reason codes:

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
- `approval_scope_mismatch`
- `approval_expired`
- `approval_revoked`
- `approval_reuse_forbidden`
- `missing_idempotency_key`
- `idempotency_payload_conflict`
- `execution_lock_missing`
- `execution_lock_collision`
- `audit_ledger_pre_attempt_missing`
- `rollback_plan_missing`
- `stale_artifact_version_detected`
- `retry_double_apply_risk`

## Reason-Code Stability Rules

- reason codes must be lowercase snake_case
- reason codes must be deterministic
- reason codes must be sorted in validator output
- reason codes must not include timestamps
- reason codes must not include raw IDs
- reason codes must not include secrets or private text
- reason codes must not include file-system-specific absolute paths
- new reason codes require docs/test update
- unknown reason codes fail closed in future validator implementation

## Fixture Family Mapping

Future fixture families map to expected reason-code groups as follows:

| Fixture family | Expected reason-code groups |
| --- | --- |
| `execution_request_fixtures` | `required_field`, `schema_version`, `safety_expectation` |
| `execution_plan_fixtures` | `required_field`, `deterministic_ordering`, `safety_expectation` |
| `mutation_proposal_fixtures` | `mutation_policy`, `safety_expectation`, `production_path` |
| `approval_record_fixtures` | `approval_scope`, `required_field`, `safety_expectation` |
| `idempotency_record_fixtures` | `idempotency`, `required_field`, `concurrency_retry` |
| `execution_lock_fixtures` | `execution_lock`, `concurrency_retry`, `required_field` |
| `audit_ledger_entry_fixtures` | `audit_ledger`, `required_field`, `storage_write` |
| `rollback_plan_fixtures` | `rollback`, `required_field`, `mutation_policy` |
| `execution_attempt_fixtures` | `fixture_execution`, `safety_expectation`, `storage_write` |
| `validation_result_fixtures` | `deterministic_ordering`, `required_field`, `fixture_family` |
| `forbidden_mutation_fixtures` | `mutation_policy`, `production_path`, `safety_expectation` |
| `concurrency_collision_fixtures` | `concurrency_retry`, `execution_lock`, `idempotency` |
| `stale_artifact_version_fixtures` | `stale_artifact`, `safety_expectation`, `mutation_policy` |
| `storage_unavailable_fixtures` | `storage_write`, `audit_ledger`, `idempotency` |
| `security_privacy_redaction_fixtures` | `privacy_security`, `production_path`, `safety_expectation` |

## Required Blockers Before Fixture Files

- fixture naming and reason-code taxonomy checkpoint passed
- fixture validator contract release checkpoint passed
- fixture design release checkpoint passed
- storage schema proposal release checkpoint passed
- failure-mode test plan approved
- transaction boundary design approved
- storage design review approved
- privacy/no-secret strategy approved
- no-production-path strategy approved
- implementation phase explicitly approved
- runtime test scope separately approved before runtime tests

## Forbidden Next-Step Shortcuts

- do not implement fixture validators next without a separate implementation phase
- do not add fixture files next without a fixture implementation phase
- do not create fixture directories next without a fixture implementation phase
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

Recommended next phase: 53B fixture naming and reason-code taxonomy final audit and merge gate.

After 53B: 54A fixture naming and reason-code taxonomy release safety checkpoint, docs/tests only.

Do not implement fixture validators next. Do not add fixture files next. Do not add runtime tests next. Do not implement migrations, storage APIs, DB writes, mutation, or live execution next.
