# Agent State Storage/Migration Readiness Checkpoint

This checkpoint is docs/tests-only. It does not implement database storage, schema migration, SQL DDL, agent run persistence, agent step persistence, repository writers, API endpoints, UI actions, scheduler jobs, reporting jobs, execution triggers, submission triggers, file exports, metrics emitters, logging emitters, or audit writers.

## Purpose

Step 180A defines the contract for a future storage/migration phase for the pure agent state foundation.

The existing pure helper layer must remain unchanged:

- `JobApplicationContext`
- `build_agent_run_snapshot`
- `build_agent_step_snapshot`
- `append_trace_step`

The future storage phase must not be mixed with scoring, execution, scheduler, reporting job, or submission behavior.

## Required separation

Future `agent_runs` and `agent_steps` persistence must remain separate from:

1. prefilter relevance
2. LLM evaluation
3. final application scoring
4. application execution
5. application submission
6. scheduler/background execution
7. reporting job execution
8. file export behavior
9. UI action behavior
10. metrics/logging/audit emitters

The storage layer must not become a hidden scheduler, hidden reporter, hidden exporter, hidden emitter, hidden scoring layer, or hidden application execution path.

## Future storage/migration contract

A future implementation may add `agent_runs` and `agent_steps` storage only if:

- schema changes are explicit and reviewed
- migration scope is limited to agent state tables only
- storage writes require explicit approved workflow boundaries
- idempotency is defined for repeated run/step write attempts
- storage calls do not mutate caller-owned state unexpectedly
- trace snapshots remain deterministic
- failures are observable and directly testable
- approval, execution, submission, scheduler, cache, retry, deduplication, ranking, ATS health, and metrics flows are preserved
- no application execution or submission is triggered as a side effect

## Explicit non-goals

This checkpoint allows no `agent_runs` table, no `agent_steps` table, no migration, no SQL execution, no storage writer, no API route, no UI action, no reporting job, no scheduler, no background task, no file export, no application execution, and no application submission.

## Protected production boundaries

The following must remain unchanged in this checkpoint:

- pure agent state helper behavior
- application execution queue behavior
- workflow runner behavior
- approval store behavior
- approval storage schema
- existing approval/execution/submission/scheduler gates
- read-only dashboard/export/writer-status endpoints
- explicit reporting job action safety boundaries
- existing cache, retry, ranking, deduplication, ATS health, and metrics flow

## Required implementation-phase checks

The future storage/migration implementation verifier must prove:

- only approved storage/schema/test/doc files changed
- schema changes are isolated to reviewed agent state tables
- no startup/import/page-load execution was introduced
- no read-only GET endpoint mutates state
- no scheduler, submission, execution, export, or reporting job side effect was introduced
- storage write behavior requires explicit approved invocation
- idempotency is directly tested
- existing full test suite passes
