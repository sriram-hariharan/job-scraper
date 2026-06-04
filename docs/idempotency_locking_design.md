# Idempotency And Locking Design

Doc path: `docs/idempotency_locking_design.md`

Phase 37A is design only. No implementation in this phase adds lock tables, migrations, idempotency stores, storage APIs, runtime lock checks, idempotency enforcement, live orchestration, mutation execution, approval storage, audit ledger storage, scheduler/background execution, autonomous execution, LLM calls, queue mutation, scoring/ranking changes, or application submission.

No lock table or migration is added. No idempotency store is added. No runtime lock checks are added. No live execution is enabled. No mutation is enabled. `workflow_runner.py` remains dry-run only, and read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Purpose

Define future duplicate-prevention and concurrency-control rules for production-capable agent execution before any live orchestration implementation exists.

This document names future idempotency keys, lock scopes, lifecycle states, collision behavior, safety invariants, and implementation gates. It does not create storage, write database rows, enforce locks, consume approvals, run adapters, mutate queues, submit applications, or change pipeline behavior.

## Current Boundary

The current system remains read-only and diagnostic:

- Current read-only adapters exist for advisory job prioritization, tailoring decision, and operator review.
- The manual read-only chain exists only for explicit operator/test invocation with explicit inputs.
- The explicit generator requires an explicit queue input and explicit output directory.
- Current chain/generator artifacts are diagnostic artifacts only.
- No DB write.
- No queue mutation.
- No application submission.
- No live orchestration.
- No scheduler/background execution.
- No UI run button.
- No scoring/ranking changes.
- No idempotency enforcement.
- No execution locking.
- `workflow_runner.py` remains dry-run only.
- Read-only adapter preflight keeps `executable_adapter_count=0`.

## Idempotency Principles

- Every future execution request must have a stable idempotency key.
- Retries must return the prior result or block duplicate mutation.
- Same key plus same payload must be safe.
- Same key plus different payload must be rejected.
- Mutation idempotency must be scoped to target and mutation type.
- Idempotency records must link to audit ledger entries.
- Idempotency must be checked before approval consumption and before mutation attempt.
- No application submission can be retried without separate submission-specific idempotency policy.

## Locking Principles

- Every mutable target requires an execution lock.
- Locks must be scoped narrowly to the smallest mutable target that protects correctness.
- Every lock must include owner/run identity.
- Every lock must include TTL/expiry.
- Stale locks require safe recovery.
- Lock acquisition must occur before mutation execution.
- Lock release must be audited.
- Lock collision must block mutation and produce diagnostic output.
- No global broad lock for the first prototype unless explicitly approved.

## Proposed Idempotency Key Structure

Future keys should be deterministic, stable, and based on already validated context. The exact hash function and canonical serialization are future implementation details.

- `execution_request`: `execution_request:{owner_user_id}:{pipeline_run_id}:{artifact_version_hash}:{request_payload_hash}`
- `execution_plan`: `execution_plan:{owner_user_id}:{pipeline_run_id}:{execution_request_id}:{artifact_version_hash}`
- `mutation_proposal`: `mutation_proposal:{owner_user_id}:{pipeline_run_id}:{target_type}:{target_id}:{mutation_type}:{source_agent_key}:{proposed_after_value_hash}`
- `approval_consumption`: `approval_consumption:{owner_user_id}:{pipeline_run_id}:{approval_id}:{target_type}:{target_id}:{mutation_type}`
- `mutation_attempt`: `mutation_attempt:{owner_user_id}:{pipeline_run_id}:{approval_id}:{target_type}:{target_id}:{mutation_type}:{proposed_after_value_hash}`
- `rollback_attempt`: `rollback_attempt:{owner_user_id}:{pipeline_run_id}:{target_type}:{target_id}:{mutation_type}:{approval_id}:{artifact_version_hash}`

Stable fields may include:

- `owner_user_id`
- `pipeline_run_id`
- `target_type`
- `target_id`
- `mutation_type`
- `source_agent_key`
- `artifact_version_hash`
- `proposed_after_value_hash`
- `approval_id` where applicable

## Proposed Lock Scopes

- `pipeline_run_lock`: protects one future live execution run from duplicate run-level transitions.
- `job_target_lock`: protects one future mutable job target from concurrent mutation.
- `queue_row_lock`: protects one future mutable application queue row.
- `artifact_status_lock`: protects one future artifact status marker or version pointer.
- `approval_consumption_lock`: protects one approval from double consumption.
- `rollback_lock`: protects one rollback target from concurrent rollback attempts.

## Lock Lifecycle

- `requested`: a future run has requested a lock but has not acquired it.
- `acquired`: the lock is held by one owner/run identity.
- `renewed`: the lock TTL was extended by the same owner/run identity.
- `released`: the lock was intentionally released after success, failure, or cancellation.
- `expired`: the lock passed its TTL without renewal.
- `force_released`: an operator or recovery process released a stale lock under an audited procedure.
- `blocked`: acquisition failed because another valid lock exists or the lock store is unavailable.

## Idempotency Record Lifecycle

- `reserved`: the key and payload hash are reserved before work begins.
- `running`: the future operation is actively using the reservation.
- `succeeded`: the future operation completed and the result may be replayed for exact duplicates.
- `failed_retryable`: the future operation failed before mutation or at a safe retry boundary.
- `failed_terminal`: the future operation failed in a way that must not be retried automatically.
- `duplicate_replayed`: the same key plus same payload returned the prior result.
- `duplicate_conflict`: the same key plus different payload was rejected.
- `expired`: the reservation passed its retention window and cannot authorize mutation.

## Collision And Duplicate Behavior

- Duplicate request same payload: return the previous terminal result or current running status; do not apply mutation twice.
- Duplicate request different payload: reject as `duplicate_conflict` and write future diagnostic/audit evidence.
- Concurrent mutation on same queue row: lock collision blocks mutation and returns diagnostic output.
- Concurrent rollback for same mutation: `rollback_lock` allows only one rollback attempt for the same target and mutation.
- Stale approval consumption: reject when approval is already consumed, expired, revoked, or scoped to different evidence.
- Stale artifact version: reject when `artifact_version_hash` does not match the approved proposal.
- Lock unavailable: block mutation; do not fall back to unlocked execution.
- Lock expired mid-run: stop before mutation if possible, mark the attempt for recovery, and require audited resolution before retry.
- Idempotency store unavailable: block live execution; do not fall back to non-idempotent execution.

## Safety Invariants

- No mutation without idempotency key.
- No mutation without execution lock.
- No approval consumption without idempotency record.
- No retry can apply same mutation twice.
- No application submission without separate submission idempotency design.
- No live execution if lock store unavailable.
- No live execution if idempotency store unavailable.
- No lock bypass in production.
- All lock/idempotency decisions must link to audit ledger entries.

## Relationship To Audit Ledger

The live-run audit ledger schema proposal is detailed in `docs/live_run_audit_ledger_schema_design.md`.

Future idempotency reservations should write ledger events. Future lock acquire/release decisions should write ledger events. Future duplicate replay/conflict outcomes should write ledger events.

Potential future events include `idempotency_reserved`, `idempotency_duplicate_replayed`, `idempotency_duplicate_conflict`, `lock_acquired`, `lock_released`, `lock_blocked`, `lock_expired`, and `lock_force_released`.

The current phase does not write ledger rows, create audit storage, enforce idempotency, acquire locks, or run live execution.

## Relationship To Approval Gate

The mutation policy and approval gate design is detailed in `docs/mutation_policy_approval_gate_design.md`.

- Approval consumption must be idempotent.
- Consumed approvals cannot be reused.
- Approval scope mismatch blocks lock acquisition.
- Expired or revoked approval blocks idempotency reservation.
- Approval consumption must occur only after the idempotency key and payload are validated.
- Approval consumption must occur only after required lock scopes are known.

## Relationship To Current Read-Only Chain

- The chain/generator remains diagnostic only.
- The smoke fixture and roundtrip tests do not require locks.
- Future proposal artifacts may include calculated keys, but not enforce in this phase.
- `workflow_runner.py` does not invoke the chain, generator, adapters, lock store, idempotency store, or audit ledger.
- Current diagnostics do not mutate production state and do not consume approvals.

## Future Implementation Gates

- DB schema/migration design for idempotency records and locks.
- Storage API design.
- Transaction boundary design.
- Lock TTL/recovery design.
- Audit ledger integration design.
- Dry-run simulator.
- Failure-mode tests.
- Operator runbook update.

These gates do not themselves enable live orchestration, mutation execution, lock storage, idempotency storage, DB writes, queue mutation, application submission, approval storage, or scheduler/background execution.
