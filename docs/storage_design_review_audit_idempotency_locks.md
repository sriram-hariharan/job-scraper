# Storage Design Review: Audit Ledger, Idempotency, And Locks

Doc path: `docs/storage_design_review_audit_idempotency_locks.md`

Phase 44A is a storage design review only. There is no implementation in this phase. No DB schema is added. No migration is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Purpose

This document reviews the future storage boundary for:

- audit ledger entries
- idempotency records
- execution locks
- approval records linkage
- rollback linkage

The review defines gates and risks that must be resolved before any later schema, migration, storage API, or runtime write implementation can be considered.

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
- no live orchestration

## Storage Design Review Decision

- Audit ledger storage implementation: `NOT_YET`
- Idempotency store implementation: `NOT_YET`
- Execution lock store implementation: `NOT_YET`
- Approval storage implementation: `NOT_YET`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Proposal-only artifact diagnostics: `GO`
- Storage design review: `PASS`

## Proposed Future Storage Components

These are proposed future components, not implemented modules:

- `agentic_audit_ledger_store`
- `agentic_idempotency_store`
- `agentic_execution_lock_store`
- `agentic_approval_record_store`
- `agentic_rollback_plan_store`

No package, module, table, migration, API route, background job, or runtime hook is added by this design review.

## Audit Ledger Storage Review

Future audit ledger storage must support:

- append-only writes
- immutable event history
- before/after capture
- actor identity
- reason codes
- artifact references
- target identity
- validation status
- rollback linkage
- idempotency key linkage
- execution lock linkage
- no secret/token storage
- no full resume/private document storage
- transaction boundary with mutation attempt

The ledger must fail closed: if a required ledger entry cannot be recorded, mutation remains blocked.

## Idempotency Storage Review

Future idempotency storage must support:

- stable idempotency key
- request payload hash
- state lifecycle
- duplicate replay
- duplicate conflict
- expiry/retention
- link to audit ledger entry
- no mutation attempt before reservation
- no approval consumption before idempotency reservation
- no application submission policy yet

Idempotency records must protect against duplicate operator clicks, retried jobs, interrupted runs, and replayed requests with changed payloads.

## Execution Lock Storage Review

Future execution lock storage must support:

- narrow lock scope
- owner/run identity
- target identity
- TTL/expiry
- renewal
- safe stale-lock recovery
- lock collision behavior
- audited acquire/release
- no mutation before lock acquisition
- no broad/global lock without separate approval

Locking must prevent concurrent mutation attempts for the same target without blocking unrelated diagnostic viewing.

## Approval Record Storage Review

Future approval record storage must support:

- approval state
- approval scope
- reviewer identity
- approval expiry
- evidence references
- consumed approval handling
- revocation handling
- linkage to mutation proposal
- linkage to audit ledger
- no approval action implementation in this phase

This review does not add approval APIs, approval storage, approval UI actions, or approval consumption.

## Rollback Storage Review

Future rollback storage must support:

- rollback plan reference
- original mutation linkage
- rollback eligibility
- rollback attempt history
- rollback failure state
- before/after restoration metadata
- operator-visible rollback summary
- no rollback implementation in this phase

Rollback metadata must be designed before any rollback-required mutation can become executable.

## Transaction Boundary Design Questions

Open questions before implementation:

- single transaction versus staged append-only event flow
- ledger write before/after mutation attempt
- idempotency reservation timing
- lock acquisition timing
- approval consumption timing
- rollback plan validation timing
- failure handling when ledger write succeeds but mutation fails
- failure handling when mutation succeeds but post-validation fails
- retry behavior
- eventual consistency tolerance

These questions must be answered before DB migrations, storage APIs, or mutation-capable runtime code are proposed.

## Failure-Mode Requirements Before Implementation

Required fail-closed behavior:

- ledger unavailable blocks mutation
- idempotency store unavailable blocks mutation
- lock store unavailable blocks mutation
- approval store unavailable blocks approval consumption
- duplicate key with different payload blocks mutation
- lock collision blocks mutation
- expired approval blocks mutation
- stale artifact version blocks mutation
- rollback plan missing blocks rollback-required mutation
- storage write timeout produces diagnostic artifact only

No failure mode may silently fall through to queue mutation, application submission, approval consumption, or production DB writes.

## Security And Privacy Requirements

Future storage design must require:

- no secrets
- no credentials
- no tokens
- no raw resumes
- no full private documents
- redact sensitive payload fields
- store references/hashes where possible
- operator identity handling
- retention policy required before implementation

Security review is required before any migration or storage API implementation.

## Required Tests Before Implementation

Future implementation must have tests for:

- append-only ledger behavior
- idempotency duplicate replay/conflict
- lock acquisition/release/expiry
- approval consumption
- rollback linkage
- unavailable storage fail-closed
- concurrent attempt collision
- migration rollback rehearsal
- no secret leakage
- feature flag disabled blocks writes

These tests must exist before any storage write path or mutation-capable execution path is enabled.

## Required Feature Flags And Environment Gates

Future conceptual flags:

- `AGENTIC_AUDIT_LEDGER_STORAGE_ENABLED`
- `AGENTIC_IDEMPOTENCY_STORAGE_ENABLED`
- `AGENTIC_EXECUTION_LOCK_STORAGE_ENABLED`
- `AGENTIC_APPROVAL_STORAGE_ENABLED`
- `AGENTIC_MUTATION_EXECUTION_ENABLED`

These flags are conceptual only and must not be added to runtime config in this phase.

## Recommended Next Phase

Recommended next phase: 45A storage schema proposal docs for audit ledger/idempotency/locks, still no migration.

Alternative: 45A transaction boundary design doc, still no implementation.

The transaction boundary design is tracked in `docs/transaction_boundary_design.md`.

Do not implement migrations next unless a separate schema proposal audit passes. Do not implement approval API/storage next. Do not start live mutation next.
