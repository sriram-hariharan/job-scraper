# Storage Schema Proposal

Doc path: `docs/storage_schema_proposal.md`

Phase 47A is a storage schema proposal only. There is no implementation in this phase. No DB schema file is added. No migration is added. No SQL DDL is added. No SQL DDL file is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Purpose

This document proposes future logical storage schemas for controlled agentic execution safety components before any migration or implementation exists. It covers future audit ledger, idempotency, execution lock, approval, rollback, execution attempt, and validation storage concepts so later work can be reviewed before any mutable path is proposed.

This proposal is documentation only. It does not create schema files, migrations, SQL DDL, tables, storage modules, storage APIs, runtime writes, approval APIs, mutation APIs, live orchestration, or production mutation.

## Current Boundary

The current system remains:

- explicit/manual/read-only/non-mutating
- diagnostic/proposal-only artifacts only
- no production mutation
- no DB writes
- no storage implementation
- no approval API/storage
- no audit ledger storage
- no idempotency store
- no execution lock store
- no transaction implementation
- no live orchestration

## Schema Proposal Decision

- Storage schema proposal: `PASS`
- DB schema implementation: `NOT_YET`
- DB migrations: `NO_GO`
- SQL DDL files: `NO_GO`
- Storage API implementation: `NOT_YET`
- Runtime DB writes: `NO_GO`
- Approval API/storage: `NOT_YET`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Proposed Logical Tables/Entities

Design only; these are proposed logical entities only, not implemented tables:

- `agentic_execution_requests`
- `agentic_execution_plans`
- `agentic_mutation_proposals`
- `agentic_approval_records`
- `agentic_idempotency_records`
- `agentic_execution_locks`
- `agentic_audit_ledger_entries`
- `agentic_rollback_plans`
- `agentic_execution_attempts`
- `agentic_validation_results`

No table, migration, storage class, storage module, repository object, API route, background worker, or runtime hook is added by this proposal.

## Common Fields

Most future entities should include these logical fields where relevant:

- `created_at_utc`
- `updated_at_utc`
- `owner_user_id`
- `pipeline_run_id`
- `request_id`
- `plan_id`
- `actor_type`
- `actor_id`
- `source_artifact_refs_json`
- `evidence_refs_json`
- `reason_codes_json`
- `validation_status`
- `risk_level`
- `metadata_json`

## `agentic_execution_requests` Proposal

Logical fields:

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

## `agentic_execution_plans` Proposal

Logical fields:

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

## `agentic_mutation_proposals` Proposal

Logical fields:

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

Allowed mutation types for first schema proposal:

- `queue_diagnostic_status_marker`
- `operator_note`
- `artifact_status_marker`

Forbidden mutation types must remain blocked:

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

## `agentic_approval_records` Proposal

Logical fields:

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

No approval action/storage is implemented in this phase.

## `agentic_idempotency_records` Proposal

Logical fields:

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

Lifecycle states:

- `reserved`
- `running`
- `succeeded`
- `failed_retryable`
- `failed_terminal`
- `duplicate_replayed`
- `duplicate_conflict`
- `expired`

## `agentic_execution_locks` Proposal

Logical fields:

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

Lifecycle states:

- `requested`
- `acquired`
- `renewed`
- `released`
- `expired`
- `force_released`
- `blocked`

## `agentic_audit_ledger_entries` Proposal

Logical fields:

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
- `before_value_json`
- `after_value_json`
- `proposed_after_value_json`
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
- `payload_json`

Future ledger entries should be append-only and immutable. This phase does not create audit ledger storage, write ledger rows, or define SQL constraints.

## `agentic_rollback_plans` Proposal

Logical fields:

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

## `agentic_execution_attempts` Proposal

Logical fields:

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

## `agentic_validation_results` Proposal

Logical fields:

- `validation_id`
- `execution_id`
- `mutation_id`
- `validation_stage`
- `validation_status`
- `validator_key`
- `validation_reason_codes_json`
- `validation_payload_hash`
- `created_at_utc`

## Relationships And Constraints

Design only:

- mutation proposals link to `request_id` and `plan_id`
- approvals link to mutation scope or approved mutation IDs
- execution attempts link to approval when mutation-capable
- idempotency records link to request payload hash and audit ledger entry
- locks link to execution attempts and audit ledger entry
- audit ledger entries link to all relevant IDs
- rollback plans link to original mutation IDs
- validation results link to execution attempts and mutation IDs
- no mutation without idempotency key
- no mutation without execution lock
- no mutation without pre-attempt audit ledger entry
- no approval reuse after consumption

These are future constraints to review before implementation. They do not create code or runtime enforcement in this phase.

## Index And Uniqueness Proposal

Design only:

- unique `idempotency_key`
- unique active `execution_lock_key`
- index on `pipeline_run_id`
- index on `owner_user_id`
- index on `target_type` and `target_id`
- index on `mutation_id`
- index on `approval_id`
- index on `event_type` and `event_status`
- index on `created_at_utc`
- append-only ledger integrity constraint concept

This section intentionally does not use SQL syntax and does not write SQL DDL.

## Privacy And Retention Proposal

Future storage design must require:

- no secrets
- no credentials
- no tokens
- no raw resumes
- no full private documents
- store hashes/references where possible
- redact sensitive payload fields
- define retention policy before implementation
- exportability for audit review
- deletion/anonymization policy requires separate design

Sensitive payload handling must be reviewed before any schema, migration, storage API, or runtime write path is implemented.

## Migration Readiness Checklist

Before any migration:

- schema proposal audit passed
- failure-mode test plan approved
- transaction boundary approved
- storage design review approved
- test DB migration rehearsal plan created
- rollback migration plan created
- no-secret leakage test plan created
- feature flag strategy approved
- production write block verified
- operator runbook updated

Passing this checklist would only permit a later migration proposal. It would not enable live execution or mutation by itself.

## Explicit Non-Goals

- no SQL DDL in this phase
- no Alembic/migration files
- no table creation
- no storage module
- no API routes
- no approval actions
- no mutation execution
- no live queue updates
- no application submission

## Recommended Next Phase

Recommended next phase: 48A storage schema proposal final audit.

Alternative: 48A test-fixture design doc for future storage/transaction failure modes.

Do not implement migrations next unless this schema proposal has passed a separate final audit. Do not implement storage APIs next. Do not start live mutation next.
