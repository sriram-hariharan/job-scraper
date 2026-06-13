# Agent Trace persistence activation readiness checkpoint

Step 195A is docs/tests only. This checkpoint prepares a safe future Trace persistence activation and migration execution plan for persistent Agent Trace storage without executing migrations, creating database connections, changing storage code, changing schema.sql, or modifying runtime behavior.

The existing storage foundation includes persistent Agent Trace storage concepts for `agent_runs` and `agent_steps`, a static `schema.sql`, an explicit migration runner, a read-only Agent Trace API endpoint, and a read-only Agent Trace UI panel. This checkpoint is planning only.

## Activation prerequisites

Contract phrase: activation prerequisites.

Future activation must require:

1. explicit operator approval
2. database backup requirement
3. migration dry-run checklist
4. idempotency check
5. rollback plan
6. verification plan
7. production safety checks

Do not implement migration execution in this checkpoint.

## Migration dry-run checklist

Contract phrase: migration dry-run checklist.

- Confirm `schema.sql` targets only `agent_runs` and `agent_steps`.
- Confirm the migration runner remains explicitly invoked only.
- Confirm no database connection is created by documentation or tests.
- Confirm no storage writes occur.
- Confirm idempotency check coverage before any future migration execution.
- Confirm read-only API compatibility before and after any future migration dry run.
- Confirm UI empty trace compatibility before and after any future migration dry run.
- Confirm rollback plan and database backup requirement are approved before production use.

## Production safety checks

Contract phrase: production safety checks.

- no behavior change
- no API behavior change
- no UI behavior change
- no storage code change
- no schema change
- no schema migration
- no migration execution
- no database connection
- no storage writes
- no pipeline wiring
- no scheduler
- no background task
- no file export
- no live LLM call
- no approval mutation
- no application execution
- no application submission
- deterministic
- observability requirements must be reviewed before future activation

## Compatibility requirements

- read-only API compatibility
- UI empty trace compatibility
- persistent Agent Trace storage must remain compatible with read-only retrieval.
- Future persistence activation must not alter the read-only Agent Trace API endpoint contract.
- Future persistence activation must not alter the read-only Agent Trace UI panel contract.

## Non-goals

Contract phrase: non-goals.

- No migration execution.
- No database connection.
- No storage writes.
- No schema change.
- No storage code change.
- No API behavior change.
- No UI behavior change.
- No pipeline wiring.
- No scheduler/background task.
- No file export.
- No live LLM call.
- No approval mutation.
- No application execution.
- No application submission.

## Rollback plan

Contract phrase: rollback plan.

Future activation must include a reviewed rollback plan before any migration execution. The future rollback plan must account for `agent_steps` before `agent_runs`, preserve read-only API compatibility, preserve UI empty trace compatibility, and require a database backup requirement before production use. Step 195A itself rolls back by removing this document, removing the focused tests, and removing README/orchestrator readiness links.

## Verification plan

Contract phrase: verification plan.

- Focused tests: `tests/test_agent_trace_persistence_activation_readiness_checkpoint.py`.
- Verify this document exists.
- Verify README links to this document.
- Verify `docs/orchestrator_readiness.md` links to this document.
- Verify this document contains all activation prerequisites.
- Verify this document contains migration dry-run checklist, idempotency check, production safety checks, database backup requirement, read-only API compatibility, UI empty trace compatibility, observability requirements, non-goals, rollback plan, and verification plan.
- Verify Step 195A remains docs/tests only.
- Verify no runtime code, API, frontend JS, storage code, schema.sql, migration_runner.py, pipeline, scheduler, workflow runner, approval behavior, LLM call, application execution, or application submission file is modified by this checkpoint.
