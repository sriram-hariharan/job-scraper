# Failure-Mode Test Plan

Doc path: `docs/failure_mode_test_plan.md`

Phase 46A is a failure-mode test plan only. There is no implementation in this phase. No runtime failure-mode tests are implemented in this phase. No DB schema is added. No migration is added. No storage API is added. No transaction code is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are enabled. No application submission is enabled.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Purpose

This document defines the future test plan for fail-closed behavior before any controlled mutation-capable implementation. It names the test categories and fixtures required before storage implementation, transaction implementation, approval API/storage, mutation API, or live execution can be considered.

This plan is documentation only. It does not add runtime behavior, test DB setup, failure-mode runtime tests, migrations, storage APIs, approval APIs, mutation APIs, live orchestration, or production writes.

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

## Failure-Mode Test Plan Decision

- Failure-mode test plan: `PASS`
- Runtime failure-mode test implementation: `NOT_YET`
- Storage integration tests: `NOT_YET`
- Transaction integration tests: `NOT_YET`
- Mutation execution tests: `NO_GO`
- Approval action tests: `NO_GO`
- Runtime DB writes: `NO_GO`
- DB migrations: `NO_GO`
- Live execution: `NO_GO`

## Test Categories Required Before Implementation

Future implementation requires these test categories before any mutable path is proposed:

- feature flag and environment gate tests
- approval scope/expiry/revocation tests
- idempotency reservation/replay/conflict tests
- execution lock acquire/release/expiry/collision tests
- audit ledger pre-attempt/post-attempt tests
- mutation transaction boundary tests
- post-mutation validation tests
- rollback plan/attempt tests
- operator-visible result publication tests
- no-secret/no-private-document leakage tests
- concurrency and retry tests
- feature flag disabled tests
- storage unavailable tests

## Feature Flag And Environment Gate Failure Tests

Future tests must verify:

- feature flag disabled blocks before storage changes
- wrong environment blocks before storage changes
- missing environment gate blocks before mutation
- no diagnostic-only tool becomes executable by config typo
- all disabled gates emit operator-visible diagnostic reason codes

## Approval Failure Tests

Future tests must verify:

- missing approval blocks mutation
- expired approval blocks mutation
- revoked approval blocks mutation
- approval scope mismatch blocks mutation
- approval store unavailable blocks approval consumption
- approval cannot be reused after consumption
- approval cannot authorize forbidden mutation type
- approval action remains unavailable when approval feature flag disabled

## Idempotency Failure Tests

Future tests must verify:

- idempotency store unavailable blocks mutation
- missing idempotency key blocks mutation
- duplicate key same payload replays prior result safely
- duplicate key different payload blocks mutation
- failed_retryable state does not double-apply
- failed_terminal state blocks unsafe retry
- idempotency finalization failure is visible
- idempotency record links to audit ledger

## Execution Lock Failure Tests

Future tests must verify:

- lock store unavailable blocks mutation
- lock collision blocks mutation
- lock expiry mid-attempt is visible
- stale lock recovery requires audit trail
- lock release failure is visible
- no mutation occurs without execution lock
- no broad/global lock allowed in first prototype

## Audit Ledger Failure Tests

Future tests must verify:

- audit ledger unavailable before mutation blocks mutation
- pre-attempt ledger write failure blocks mutation
- ledger write succeeds but mutation fails records failed attempt
- mutation succeeds but post-attempt ledger write fails creates blocked recovery state
- rollback events are written separately
- failed attempts are never hidden
- no secret/token/raw resume/full private document is stored
- ledger rows link to idempotency key, lock key, approval id, and rollback id where applicable

## Transaction Boundary Failure Tests

Future tests must verify:

- no mutation before preflight validation
- no mutation before proposal validation
- no mutation before approval scope check
- no mutation before idempotency reservation
- no mutation before execution lock acquisition
- no mutation before audit ledger pre-attempt write
- no success result before post-mutation validation
- approval consumption failure after mutation enters blocked recovery state
- lock release failure after mutation is visible
- retry cannot apply same mutation twice

## Rollback Failure Tests

Future tests must verify:

- rollback-required mutation without rollback plan blocks mutation
- rollback plan invalid blocks mutation
- rollback attempt failure is visible
- rollback success writes separate result
- automatic rollback retry loop is disabled unless separately approved
- operator-directed rollback is audited
- rollback cannot submit applications

## Application Submission Tests

Application submission remains out of scope.

- no application submission test should expect live submission
- any future submission automation requires separate submission-specific transaction design, idempotency design, approval policy, rollback/irreversibility policy, and legal/privacy review

## Security And Privacy Tests

Future tests must verify:

- no secrets in ledger/idempotency/lock records
- no credentials/tokens stored
- no raw resumes stored
- no full private documents stored
- sensitive fields are redacted
- artifact refs and hashes are used where possible
- operator identity handling is auditable
- retention/export behavior is reviewed before implementation

## Concurrency And Retry Tests

Future tests must verify:

- concurrent attempts on same target collide safely
- batch proposals do not bypass per-target locks
- retry after network timeout does not double-apply
- retry after post-validation failure does not mark success
- stale artifact version blocks mutation
- multi-target mutation requires separate approved design

## Test Fixture Requirements

Future fixtures should include:

- safe synthetic execution request
- safe synthetic mutation proposal
- safe synthetic approval record
- safe synthetic idempotency record
- safe synthetic lock record
- safe synthetic ledger entry
- safe synthetic rollback plan
- unsafe forbidden mutation proposal
- duplicate idempotency payload pair
- lock collision pair
- expired/revoked approval examples

## Required Test Gates Before Any Implementation Merge

Required gates before implementation merge:

- unit tests for storage contracts
- integration tests using test DB only
- migration rollback rehearsal
- concurrency tests
- fail-closed storage unavailable tests
- feature flag disabled tests
- no-secret leakage tests
- no-production-write tests
- audit trail completeness tests
- operator visibility tests

These gates must pass before storage implementation, transaction implementation, approval API/storage, mutation API, or live execution is merged.

## Recommended Next Phase

Recommended next phase: 47A storage schema proposal docs for audit ledger/idempotency/locks/approvals, still no migration.

Alternative: 47A failure-mode fixture design doc, still no runtime tests.

The storage schema proposal is tracked in `docs/storage_schema_proposal.md`.

Do not implement migrations next unless a separate schema proposal audit passes. Do not implement failure-mode runtime tests against production paths. Do not implement transaction code next. Do not implement approval API/storage next. Do not start live mutation next.
