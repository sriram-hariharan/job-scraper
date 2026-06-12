# Agent State Migration Runner Readiness Checkpoint

This checkpoint is docs/tests-only. It does not implement a migration runner, migration execution, database connection creation, transaction commit, startup execution, import-time execution, API endpoint, UI action, scheduler job, reporting job execution, file export, metrics emitter, logging emitter, audit writer, application execution, or application submission.

## Purpose

Step 182A defines the contract for a future isolated migration runner that may apply the already-reviewed `src/storage/agent_state/schema.sql` for `agent_runs` and `agent_steps`.

The current implementation state is:

- pure agent state helpers exist
- isolated `agent_runs` and `agent_steps` schema exists
- isolated repository helpers exist
- no migration runner exists in this checkpoint
- no migration execution exists in this checkpoint
- no connection creation exists in this checkpoint
- no commit behavior exists in this checkpoint

## Required separation

A future migration runner must remain separate from:

1. prefilter relevance
2. LLM evaluation
3. final application scoring
4. application execution
5. application submission
6. scheduler/background execution
7. reporting job execution
8. API/UI behavior
9. file export behavior
10. metrics/logging/audit emitters

The migration runner must not become a hidden scheduler, hidden reporter, hidden exporter, hidden emitter, hidden scoring layer, hidden API action, or hidden application execution path.

## Future migration runner contract

A future implementation may add an agent state migration runner only if:

- it is isolated to `src/storage/agent_state/schema.sql`
- it applies only `agent_runs` and `agent_steps`
- it does not modify approval schema or approval store behavior
- execution requires explicit approved invocation
- connection handling is caller-controlled or explicitly injected
- transaction behavior is explicit and directly tested
- idempotency is defined for repeated migration attempts
- failures are observable and directly testable
- no startup/import/page-load execution is introduced
- approval, execution, submission, scheduler, cache, retry, deduplication, ranking, ATS health, and metrics flows are preserved
- no application execution or submission is triggered as a side effect

## Explicit non-goals

This checkpoint allows no migration runner, no migration execution, no DB connection creation, no transaction commit, no API route, no UI action, no reporting job, no scheduler, no background task, no file export, no metrics emitter, no logging emitter, no audit writer, no application execution, and no application submission.

## Protected production boundaries

The following must remain unchanged in this checkpoint:

- pure agent state helper behavior
- isolated agent state schema/repository behavior
- application execution queue behavior
- workflow runner behavior
- approval store behavior
- approval storage schema
- existing approval/execution/submission/scheduler gates
- read-only dashboard/export/writer-status endpoints
- explicit reporting job action safety boundaries
- existing cache, retry, ranking, deduplication, ATS health, and metrics flow

## Required implementation-phase checks

The future migration runner implementation verifier must prove:

- only approved agent-state migration-runner files changed
- no approval schema/store files changed
- no API/UI files changed
- no startup/import/page-load execution was introduced
- no read-only GET endpoint mutates state
- no scheduler, submission, execution, export, or reporting job side effect was introduced
- migration execution requires explicit approved invocation
- idempotency is directly tested
- existing full test suite passes
