# Persistent Reporting Storage/Migration Readiness Checkpoint

This checkpoint is docs/tests-only. It does not implement persistent reporting storage, schema migrations, SQL DDL, reporting jobs, scheduler jobs, background jobs, execution triggers, submission behavior, file exports, metrics emitters, logging emitters, or audit writers.

## Purpose

The next implementation phase may introduce persistent reporting storage only after this checkpoint defines the storage and migration contract. This checkpoint preserves the current production-safe behavior:

- read-only production scheduler observability dashboard
- read-only export preview
- read-only writer status endpoint
- no file creation
- no reporting job
- no scheduler/background work
- no execution/submission trigger
- no database migration in this checkpoint

## Required separation

Persistent reporting storage must remain separate from:

1. prefilter relevance
2. LLM evaluation
3. final application scoring
4. application execution
5. application submission
6. scheduler/background execution
7. file export/reporting job behavior

The future storage layer must not blur read-only preview/status surfaces with approved persistence boundaries.

## Future storage contract

A future implementation may add persistent reporting storage only if:

- migration files are explicit and reviewed
- schema changes are deterministic
- storage functions validate payloads before persistence
- write operations require explicit approved workflow boundaries
- idempotency is defined for repeated calls
- failures are observable and testable
- no scheduler, submission, execution, export, or reporting job is triggered as a side effect

## Explicit non-goals

This checkpoint allows no migration, no storage writer, no reporting job, no scheduler, no background task, no file export, no SQL execution, no application execution, and no application submission.

## Protected production boundaries

The following must remain unchanged in this checkpoint:

- application execution queue behavior
- workflow runner behavior
- approval store behavior
- approval storage schema
- existing approval/execution/submission/scheduler gates
- existing cache, retry, ranking, deduplication, ATS health, and metrics flow

## Required implementation-phase checks

The future persistent storage implementation verifier must prove:

- only approved files changed
- schema/migration changes are explicit when allowed
- no scheduler, execution, submission, export, or reporting job behavior was introduced
- storage writes are deterministic, idempotent, and directly tested
- read-only dashboard/export/writer-status endpoints stay GET-only
- existing full test suite passes
