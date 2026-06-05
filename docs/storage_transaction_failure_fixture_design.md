# Storage Transaction Failure Fixture Design

Doc path: `docs/storage_transaction_failure_fixture_design.md`

Phase 49A is fixture design only. There is no implementation in this phase. No fixture files are added. No runtime failure-mode tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Purpose

This document designs future synthetic fixtures for storage/transaction failure-mode tests before any runtime implementation exists. It defines fixture families, naming, safety constraints, required fields, validation expectations, and review gates so later fixture files can be audited before storage APIs, transaction code, migrations, runtime DB writes, mutation execution, approval actions, or live execution are considered.

This phase is documentation only. It does not add fixture JSON/CSV files, runtime failure-mode tests, storage integration tests, transaction integration tests, DB schemas, migrations, SQL DDL, storage modules, APIs, approval actions, mutation APIs, scheduler execution, queue updates, application submission, or production writes.

## Current Boundary

The current system remains:

- explicit/manual/read-only/non-mutating
- diagnostic/proposal artifacts only
- storage schema proposal is design-only
- no production mutation
- no DB writes
- no schema/migration/storage implementation
- no approval API/storage
- no audit ledger storage
- no idempotency store
- no execution lock store
- no transaction implementation
- no runtime failure-mode tests
- no live orchestration

Current safe tooling is limited to the read-only chain artifact generator, dry-run execution simulator, proposal-only mutation planner, and Agentic Review diagnostic display.

## Fixture Design Decision

- Fixture design: `PASS`
- Fixture file implementation: `NOT_YET`
- Runtime failure-mode tests: `NOT_YET`
- Storage integration tests: `NOT_YET`
- Transaction integration tests: `NOT_YET`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Fixture Families

Future fixture families are proposed as design labels only. They are not files, directories, tables, classes, modules, or tests added in this phase.

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

These are proposed fixture families only, not files added in this phase.

## Naming Convention Proposal

Future fixture names should be lowercase snake_case, include the safety class or failure mode, and end in `.json` unless a later approved phase explicitly requires another format.

Proposed future names:

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

These are future names only and should not be created in this phase.

## Safe Fixture Content Requirements

Future fixtures must:

- use synthetic `owner_user_id`
- use synthetic `pipeline_run_id`
- use synthetic target IDs
- use fake actor IDs
- use fake timestamps
- use hashes/references instead of raw private content
- avoid real company/person identifiers
- avoid real resumes
- avoid full private documents
- avoid secrets, tokens, credentials
- avoid real application URLs
- avoid live queue file paths
- avoid production DB identifiers

## Required Fixture Fields By Family

Future fixture fields must align with `docs/storage_schema_proposal.md`. The field lists below are minimum proposed content expectations, not implemented schemas.

Execution request fields:

- `fixture_schema_version`
- `fixture_family`
- `request_id`
- `request_source`
- `requested_action_type`
- `requested_target_type`
- `requested_target_id`
- `request_payload_hash`
- `request_payload_summary`
- `request_status`
- `idempotency_key`
- `created_by_actor_type`
- `created_by_actor_id`
- `created_at_utc`
- `owner_user_id`
- `pipeline_run_id`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`

Execution plan fields:

- `fixture_schema_version`
- `fixture_family`
- `plan_id`
- `request_id`
- `plan_mode`
- `plan_status`
- `proposed_step_count`
- `requires_approval`
- `requires_audit_ledger`
- `requires_idempotency_key`
- `requires_execution_lock`
- `requires_rollback_plan`
- `plan_payload_hash`
- `plan_summary`
- `created_at_utc`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`

Mutation proposal fields:

- `fixture_schema_version`
- `fixture_family`
- `mutation_id`
- `request_id`
- `plan_id`
- `mutation_type`
- `target_type`
- `target_id`
- `proposed_after_value_hash`
- `proposed_after_value_json`
- `evidence_refs_json`
- `policy_status`
- `proposal_status`
- `can_execute_live`
- `blocked_by_default`
- `requires_approval`
- `requires_rollback_plan`
- `created_at_utc`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`
- `expected_did_mutate`

Approval record fields:

- `fixture_schema_version`
- `fixture_family`
- `approval_id`
- `approval_scope_type`
- `approval_scope_json`
- `approval_status`
- `reviewer_actor_type`
- `reviewer_actor_id`
- `approval_reason`
- `approved_mutation_ids_json`
- `expires_at_utc`
- `consumed_at_utc`
- `revoked_at_utc`
- `evidence_refs_json`
- `created_at_utc`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`

Idempotency record fields:

- `fixture_schema_version`
- `fixture_family`
- `idempotency_key`
- `idempotency_scope`
- `request_payload_hash`
- `target_type`
- `target_id`
- `mutation_type`
- `state`
- `first_seen_at_utc`
- `last_seen_at_utc`
- `expires_at_utc`
- `replay_result_ref_json`
- `conflict_reason`
- `audit_ledger_entry_id`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`

Execution lock fields:

- `fixture_schema_version`
- `fixture_family`
- `execution_lock_key`
- `lock_scope`
- `target_type`
- `target_id`
- `mutation_type`
- `owner_execution_id`
- `owner_actor_id`
- `lock_status`
- `acquired_at_utc`
- `renewed_at_utc`
- `expires_at_utc`
- `released_at_utc`
- `release_reason`
- `audit_ledger_entry_id`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`

Audit ledger entry fields:

- `fixture_schema_version`
- `fixture_family`
- `ledger_entry_id`
- `event_type`
- `event_status`
- `created_at_utc`
- `owner_user_id`
- `pipeline_run_id`
- `request_id`
- `plan_id`
- `mutation_id`
- `approval_id`
- `execution_id`
- `rollback_id`
- `agent_key`
- `target_type`
- `target_id`
- `mutation_type`
- `artifact_refs_json`
- `evidence_refs_json`
- `reason_codes_json`
- `validation_status`
- `risk_level`
- `idempotency_key`
- `execution_lock_key`
- `actor_type`
- `actor_id`
- `summary`
- `payload_hash`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`

Rollback plan fields:

- `fixture_schema_version`
- `fixture_family`
- `rollback_id`
- `mutation_id`
- `request_id`
- `plan_id`
- `rollback_strategy`
- `rollback_status`
- `rollback_payload_hash`
- `rollback_payload_summary`
- `before_value_ref_json`
- `expected_restore_value_hash`
- `requires_operator_approval`
- `created_at_utc`
- `validated_at_utc`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`

Execution attempt fields:

- `fixture_schema_version`
- `fixture_family`
- `execution_id`
- `request_id`
- `plan_id`
- `mutation_id`
- `approval_id`
- `idempotency_key`
- `execution_lock_key`
- `attempt_status`
- `started_at_utc`
- `completed_at_utc`
- `failure_type`
- `failure_reason`
- `retryable`
- `rollback_required`
- `rollback_id`
- `audit_ledger_entry_ids_json`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`

Validation result fields:

- `fixture_schema_version`
- `fixture_family`
- `validation_id`
- `execution_id`
- `mutation_id`
- `validation_stage`
- `validation_status`
- `validator_key`
- `validation_reason_codes_json`
- `validation_payload_hash`
- `created_at_utc`
- `expected_result`
- `expected_reason_codes`
- `expected_blocked`

## Allowed Safe Mutation Proposal Fixtures

Only these future mutation proposal fixture types are allowed for the first fixture implementation proposal:

- `queue_diagnostic_status_marker`
- `operator_note`
- `artifact_status_marker`

These fixtures must still be non-executable and blocked by default until future approved phases explicitly add and audit fixture files, validators, storage contracts, approval gates, transaction boundaries, and feature flags.

## Forbidden Mutation Fixtures

Future forbidden fixtures must cover:

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

These fixtures must validate as blocked/rejected and must never execute.

## Idempotency Fixture Cases

Future idempotency fixtures should cover:

- missing idempotency key blocks mutation
- same key same payload replays safely
- same key different payload blocks mutation
- failed_retryable does not double-apply
- failed_terminal blocks unsafe retry
- expired idempotency record blocks or requires new key
- idempotency record links to audit ledger

## Execution Lock Fixture Cases

Future execution lock fixtures should cover:

- missing lock blocks mutation
- lock collision same target blocks mutation
- stale lock requires audited recovery
- expired lock is visible
- release failure is visible
- no broad/global lock in first prototype

## Approval Fixture Cases

Future approval fixtures should cover:

- missing approval blocks mutation
- expired approval blocks mutation
- revoked approval blocks mutation
- scope mismatch blocks mutation
- consumed approval cannot be reused
- forbidden mutation type cannot be approved
- approval store unavailable blocks consumption

## Audit Ledger Fixture Cases

Future audit ledger fixtures should cover:

- pre-attempt ledger entry missing blocks mutation
- ledger unavailable before mutation blocks mutation
- mutation failure writes failed attempt
- post-attempt ledger failure enters blocked recovery state
- rollback events are separate entries
- failed attempts are never hidden
- ledger references idempotency, lock, approval, rollback where applicable

## Rollback Fixture Cases

Future rollback fixtures should cover:

- rollback-required mutation without rollback plan blocks mutation
- invalid rollback plan blocks mutation
- rollback attempt failure is visible
- rollback success is separate result
- no automatic rollback retry loop without approval
- rollback cannot submit applications

## Concurrency/Retry Fixture Cases

Future concurrency/retry fixtures should cover:

- concurrent same-target attempts collide safely
- batch proposals do not bypass per-target locks
- retry after timeout does not double-apply
- retry after post-validation failure does not mark success
- stale artifact version blocks mutation
- multi-target mutation remains out of scope

## Security/Privacy Fixture Cases

Future security/privacy fixtures should cover:

- secret value is redacted
- credential/token fields are rejected or redacted
- raw resume payload is rejected
- full private document payload is rejected
- sensitive payload field is hashed
- artifact reference is allowed
- payload hash is allowed
- retention metadata is present

## Fixture Validation Expectations

Future fixture validation should verify:

- schema version present
- fixture family present
- expected_result present
- expected_reason_codes present
- expected_blocked boolean present
- expected_did_mutate=false for unsafe cases
- expected_did_write_db=false for unavailable storage cases
- expected_no_secret_leakage=true for privacy cases
- no real identifiers
- deterministic ordering
- no production paths

## Future Fixture Directory Proposal

Design only. A future approved implementation phase may propose:

- `tests/fixtures/agentic_storage_transaction_failure_modes/`
- subdirectories by family
- `README.md` inside fixture directory
- no files created in this phase

This phase must not create that directory or any fixture file.

## Required Review Before Fixture Implementation

Before adding fixtures:

- fixture design audit passed
- schema proposal release checkpoint passed
- failure-mode test plan approved
- transaction boundary design approved
- storage design review approved
- privacy review completed
- fixture naming approved
- fixture validator contract approved

## Explicit Non-Goals

- no fixture files in this phase
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

Recommended next phase: 50A fixture design final audit/release checkpoint, docs/tests only.

Alternative: 50A fixture validator contract design doc, docs/tests only.

The storage/transaction fixture release safety checkpoint is tracked in `docs/storage_transaction_fixture_release_safety_checkpoint.md`.

Do not add fixture files next unless fixture design passes final audit. Do not add runtime tests next unless a separate fixture implementation phase is approved. Do not implement migrations, storage APIs, DB writes, mutation, or live execution next.
