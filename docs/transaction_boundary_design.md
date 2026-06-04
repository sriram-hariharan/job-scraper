# Transaction Boundary Design

Doc path: `docs/transaction_boundary_design.md`

Phase 45A is a transaction boundary design only. There is no implementation in this phase. No DB schema is added. No migration is added. No storage API is added. No transaction code is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Purpose

This document defines future transaction sequencing for a controlled mutation-capable system before any implementation exists. It describes the ordering and failure semantics for audit ledger writes, idempotency reservation, execution locks, approval consumption, mutation attempts, validation, and rollback.

The goal is to make the future boundary reviewable before DB schemas, migrations, storage APIs, transaction code, runtime writes, or mutation-capable execution are proposed.

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

## Transaction Boundary Decision

- Transaction implementation: `NOT_YET`
- Runtime DB writes: `NO_GO`
- DB migrations: `NO_GO`
- Mutation execution: `NO_GO`
- Approval consumption: `NO_GO`
- Queue mutation: `NO_GO`
- Application submission: `NO_GO`
- Transaction boundary design: `PASS`

## Proposed Future Transaction Participants

These are conceptual participants, not implemented tables/classes in this phase:

- `execution_request`
- `execution_plan`
- `mutation_proposal`
- `approval_record`
- `idempotency_record`
- `execution_lock`
- `audit_ledger_entry`
- `mutation_attempt`
- `validation_result`
- `rollback_plan`
- `rollback_attempt`

No package, module, class, table, migration, storage API, transaction helper, route, background job, or runtime hook is added by this design.

## Proposed Transaction Phases

A future controlled mutation transaction should be designed around these phases:

1. `preflight_validation`
2. `feature_flag_environment_gate_check`
3. `proposal_validation`
4. `approval_scope_check`
5. `idempotency_reservation`
6. `execution_lock_acquisition`
7. `audit_ledger_pre_attempt_write`
8. `mutation_attempt`
9. `post_mutation_validation`
10. `audit_ledger_post_attempt_write`
11. `approval_consumption`
12. `idempotency_finalization`
13. `execution_lock_release`
14. `rollback_if_required`
15. `operator_visible_result_publication`

These phases are sequencing requirements for later design and tests only. They do not enable execution.

## Required Ordering Invariants

Future implementation must preserve these invariants:

- no mutation before feature flag/environment gate passes
- no mutation before proposal validation passes
- no mutation before approval scope check passes
- no approval consumption before idempotency reservation
- no mutation before idempotency reservation
- no mutation before execution lock acquisition
- no mutation before audit ledger pre-attempt write
- no lock release before post-attempt ledger write unless emergency recovery path is used
- no approval consumption reuse
- no success result before post-mutation validation
- no retry can apply the same mutation twice
- no application submission without separate submission transaction design

## Failure Matrix

Future behavior must be defined for each failure case:

| Failure case | Future behavior |
| --- | --- |
| feature flag disabled | Block before storage changes and emit diagnostic artifact only. |
| approval missing | Block before idempotency reservation, lock acquisition, ledger write, or mutation. |
| approval expired | Block before mutation and report expired approval. |
| approval scope mismatch | Block before mutation and require a new bounded approval. |
| idempotency store unavailable | Idempotency store unavailable blocks mutation. |
| duplicate idempotency key same payload | Replay the prior terminal result or return the prior in-progress state without double-apply. |
| duplicate idempotency key different payload | Block mutation as an idempotency conflict. |
| lock unavailable | Lock store unavailable blocks mutation. |
| lock expires mid-attempt | Stop further mutation, write/require recovery ledger event, and require operator recovery. |
| audit ledger unavailable before mutation | Audit ledger unavailable before mutation blocks mutation. |
| audit ledger write succeeds but mutation fails | Write failed attempt state, preserve before/after evidence, and avoid automatic retry unless policy allows. |
| mutation succeeds but post-validation fails | Mark unsafe/failed validation, require rollback path, and keep operator-visible status. |
| post-attempt audit ledger write fails | Treat as critical recovery state; do not publish success until recovery ledger state is resolved. |
| approval consumption fails after mutation | Mark recovery-required state and prevent approval reuse until reconciled. |
| idempotency finalization fails | Keep retry from double-applying; reconcile idempotency before any follow-up mutation. |
| lock release fails | Keep failure visible and require stale-lock recovery with audit trail. |
| rollback plan missing | Block rollback-required mutation before attempt. |
| rollback attempt fails | Record rollback failure and block follow-up automation. |
| operator result publication fails | Preserve ledger/idempotency state and allow manual diagnostic retrieval without reapplying mutation. |

## Fail-Closed Rules

Future transaction code must fail closed:

- if feature flag/environment gate fails, block before storage changes
- if idempotency store unavailable, block mutation
- if lock store unavailable, block mutation
- if audit ledger unavailable before mutation, block mutation
- if approval store unavailable, block approval consumption
- approval store unavailable blocks approval consumption
- if rollback-required mutation lacks rollback plan, block mutation
- if validation fails before mutation, block mutation
- if any required safety store is unavailable, emit diagnostic artifact only

No failure mode may silently fall through to queue mutation, application submission, approval consumption, production DB writes, or live execution.

## Ledger Write Timing

Future ledger timing should favor auditable intent before mutability:

- write request/plan/proposal event before execution attempt
- write pre-attempt event before mutation
- write post-attempt event after mutation or failure
- write rollback events separately
- never hide failed attempts
- never mutate without auditable intent

The core tradeoff is whether a future system uses a single database transaction for ledger and mutation state, or append-only staged events around a mutation boundary. Either approach must make failed attempts visible, must preserve recovery context, and must fail closed if the pre-attempt ledger entry cannot be written.

## Idempotency Timing

Future idempotency handling should:

- reserve before lock acquisition or after proposal validation
- bind key to payload hash
- replay same payload safely
- reject different payload with same key
- finalize after validation/ledger write
- mark retryable versus terminal failures
- avoid double-apply

The reservation must exist before mutation capability is acquired. Finalization must happen only after post-mutation validation and required ledger write outcomes are known.

## Lock Timing

Future lock handling should:

- acquire after idempotency reservation
- scope lock to target and mutation type
- renew long-running locks
- release only after ledger post-attempt write
- stale lock recovery requires audit trail
- lock collision blocks mutation

Lock scope must be narrow enough to avoid blocking unrelated diagnostics, while still preventing concurrent mutation attempts for the same target and mutation type.

## Approval Timing

Future approval handling should:

- validate approval before idempotency reservation
- consume approval only after successful mutation and validation, or define staged consumption if safer
- consumed approval cannot be reused
- approval expiry checked immediately before mutation attempt
- approval revocation blocks mutation

Approval records must bind to the exact proposal, target, owner/run context, environment, before state, allowed mutation type, and expiry window. Approval store unavailable blocks approval consumption.

## Rollback Timing

Future rollback handling should:

- rollback plan validated before mutation
- rollback attempt starts only after failed/unsafe post-validation or operator-directed recovery
- rollback events are separate ledger entries
- rollback failure must be visible and blocking for follow-up automation
- no automatic retry loop without approval

Rollback must not become hidden automatic execution. The first controlled prototype should prefer operator-directed recovery unless a later reviewed phase explicitly approves narrow automatic rollback behavior.

## Transaction Boundary Open Questions

Open questions before implementation:

- single database transaction versus append-only staged events
- whether approval consumption should happen before or after mutation
- how to handle ledger post-write failure after mutation success
- how to safely recover stale locks
- how to reconcile diagnostics artifacts with future DB records
- how to version artifacts used as evidence
- how much payload to hash versus store
- how to handle multi-target mutations
- how to handle batch proposals
- whether rollback should be operator-triggered only in first prototype

These questions must be answered before DB migrations, storage APIs, transaction code, or mutation-capable runtime paths are proposed.

## Required Tests Before Implementation

Future implementation must have tests for:

- gate failure blocks before mutation
- missing approval blocks
- expired approval blocks
- idempotency duplicate replay/conflict
- lock collision blocks
- pre-attempt ledger unavailable blocks
- mutation failure writes failed attempt
- post-validation failure triggers rollback-required state
- approval consumption cannot be reused
- lock release failure is visible
- rollback failure is visible
- no double-apply on retry
- no secret leakage in ledger/idempotency payloads

These tests must exist before any transaction implementation, storage write path, or mutation-capable execution path is enabled.

## Recommended Next Phase

Recommended next phase: 46A storage schema proposal docs for audit ledger/idempotency/locks/approvals, still no migration.

Alternative: 46A failure-mode test plan doc, still no implementation.

Do not implement migrations next unless a separate schema proposal audit passes. Do not implement transaction code next. Do not implement approval API/storage next. Do not start live mutation next.
