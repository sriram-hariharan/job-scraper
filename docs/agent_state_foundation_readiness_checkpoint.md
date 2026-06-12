# Agent State Foundation Readiness Checkpoint

This checkpoint is docs/tests-only. It does not implement `JobApplicationContext`, `agent_runs`, `agent_steps`, trace helpers, database storage, schema migration, SQL DDL, scheduler jobs, reporting jobs, execution triggers, submission triggers, file exports, metrics emitters, logging emitters, or audit writers.

## Purpose

The next implementation phase may add an agent state foundation only after this checkpoint defines the production-safe contract.

The current production-safe surfaces must remain unchanged:

- read-only production scheduler observability dashboard
- read-only export preview
- read-only writer status endpoint
- explicitly invoked reporting job action with no side effects
- no state persistence in this checkpoint
- no migration in this checkpoint
- no scheduler/background execution in this checkpoint
- no execution or submission trigger in this checkpoint

## Required separation

Agent state must remain separate from:

1. prefilter relevance
2. LLM evaluation
3. final application scoring
4. application execution
5. application submission
6. scheduler/background execution
7. file export behavior
8. reporting job behavior
9. storage migration review

The agent state foundation must not become a hidden scheduler, hidden reporting job, hidden exporter, hidden emitter, hidden scoring layer, or hidden application execution path.

## Future agent state contract

A future implementation may add agent state primitives only if:

- `JobApplicationContext` is deterministic and serializable
- `agent_runs` and `agent_steps` schemas are explicitly reviewed before migration
- trace helpers are pure or clearly bounded by explicit persistence calls
- state writes require explicit approved workflow boundaries
- idempotency is defined for repeated trace/state calls
- failures are observable and directly testable
- existing stage-level logging and observability remain intact
- approval, execution, submission, scheduler, cache, retry, deduplication, ranking, ATS health, and metrics flows are preserved
- no application execution or submission is triggered as a side effect

## Explicit non-goals

This checkpoint allows no `JobApplicationContext` implementation, no `agent_runs` table, no `agent_steps` table, no trace helper implementation, no migration, no SQL execution, no state persistence, no reporting job, no scheduler, no background task, no file export, no application execution, and no application submission.

## Protected production boundaries

The following must remain unchanged in this checkpoint:

- application execution queue behavior
- workflow runner behavior
- approval store behavior
- approval storage schema
- existing approval/execution/submission/scheduler gates
- read-only dashboard/export/writer-status endpoints
- explicit reporting job action safety boundaries
- existing cache, retry, ranking, deduplication, ATS health, and metrics flow

## Required implementation-phase checks

The future agent state implementation verifier must prove:

- only approved files changed
- no migration or schema changes occur unless explicitly allowed
- no startup/import/page-load execution was introduced
- no read-only GET endpoint mutates state
- no scheduler, submission, execution, export, migration, or reporting job side effect was introduced
- state/context/trace output is deterministic and directly tested
- existing full test suite passes
