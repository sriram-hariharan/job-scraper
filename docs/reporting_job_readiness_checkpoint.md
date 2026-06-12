# Reporting Job Readiness Checkpoint

This checkpoint is docs/tests-only. It does not implement a reporting job, scheduler job, background job, persistent reporting storage, SQL migration, file export, execution trigger, submission trigger, metrics emitter, logging emitter, or audit writer.

## Purpose

The next implementation phase may add a reporting job only after this checkpoint defines the production-safe contract.

The current production-safe surfaces must remain unchanged:

- read-only production scheduler observability dashboard
- read-only export preview
- read-only writer status endpoint
- persistent reporting storage/migration remains unimplemented unless explicitly approved
- no reporting job in this checkpoint
- no scheduler or background execution in this checkpoint
- no file export in this checkpoint
- no execution or submission trigger in this checkpoint

## Required separation

A future reporting job must remain separate from:

1. prefilter relevance
2. LLM evaluation
3. final application scoring
4. application execution
5. application submission
6. scheduler/background execution
7. file export behavior
8. persistent storage migration review

The reporting job must not become a hidden scheduler, hidden exporter, hidden emitter, or hidden application execution path.

## Future reporting job contract

A future implementation may add reporting job behavior only if:

- the job is explicitly invoked from an approved route or approved workflow boundary
- the job does not run automatically from import, startup, page load, read-only GET preview, dashboard view, or writer-status view
- inputs are validated before job execution
- output is deterministic and structured
- persistence boundaries are explicit
- idempotency is defined
- failures are observable and directly testable
- rate limiting, retry behavior, caching, deduplication, ranking, ATS health checks, and existing metrics flow are preserved
- no application execution or submission is triggered as a side effect

## Explicit non-goals

This checkpoint allows no reporting job, no scheduler, no background task, no migration, no persistent storage writer, no file export, no SQL execution, no application execution, and no application submission.

## Protected production boundaries

The following must remain unchanged in this checkpoint:

- application execution queue behavior
- workflow runner behavior
- approval store behavior
- approval storage schema
- existing approval/execution/submission/scheduler gates
- read-only dashboard/export/writer-status endpoints
- existing cache, retry, ranking, deduplication, ATS health, and metrics flow

## Required implementation-phase checks

The future reporting job implementation verifier must prove:

- only approved files changed
- no startup/import/page-load execution was introduced
- no read-only GET endpoint triggers job execution
- no scheduler, submission, execution, export, or migration side effect was introduced
- reporting job execution requires explicit approved invocation
- reporting job result is deterministic and directly tested
- existing full test suite passes
