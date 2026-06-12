# Agent State Storage Schema Repository, No Runner, No API

Step 181A adds an isolated agent state storage schema artifact and deterministic repository preparation helpers for `agent_runs` and `agent_steps`. The storage package prepares SQL statements and parameter tuples for an explicit future caller. It does not create database connections, commit transactions, run migrations, execute SQL, add API routes, add UI actions, schedule work, execute reporting jobs, export files, emit metrics/logs/audits, execute applications, or submit applications.

## Scope

- Schema path: `src/storage/agent_state/schema.sql`
- Repository helper path: `src/storage/agent_state/store.py`
- Package path: `src/storage/agent_state/__init__.py`
- Focused tests: `tests/test_agent_state_storage_schema_repository_no_runner_no_api.py`
- No API route added.
- No UI action added.
- No migration runner added.
- No migration executed.
- No protected execution, approval storage, scheduler, submission, workflow runner, API, UI, approval schema, or migration files modified.

The repository helpers are deterministic and non-executing. They accept caller-owned agent state snapshots, deep-copy them into response payloads, and return SQL/params only. Timestamps and IDs must be supplied by caller or derived by the pure agent state layer before these helpers are called.

## Verification contract phrases

- Agent state storage schema repository no runner no API: PASS
- Agent state storage implementation: ISOLATED_SQL_AND_PREPARE_ONLY
- Runtime-facing integration scope: STORAGE_PREPARATION_ONLY
- Schema path: src/storage/agent_state/schema.sql
- Repository helper path: src/storage/agent_state/store.py
- Package path: src/storage/agent_state/__init__.py
- agent_runs schema: GO
- agent_steps schema: GO
- repository SQL preparation helpers: GO
- migration runner implementation: NO_GO
- migration execution: NO_GO
- API endpoint implementation: NO_GO
- UI action implementation: NO_GO
- scheduler/background work: NO_GO
- reporting job execution: NO_GO
- file export creation: NO_GO
- metrics emitter: NO_GO
- logging emitter: NO_GO
- audit writer: NO_GO
- application execution: NO_GO
- application submission: NO_GO
- approval store modification: NO_GO
- approval schema modification: NO_GO
- schema contains agent_runs only and agent_steps only
- schema uses CREATE TABLE IF NOT EXISTS
- schema has no approval schema modification
- schema has no approval table modification
- schema has no INSERT statements
- schema has no UPDATE statements
- schema has no DELETE statements
- repository helpers do not create connections
- repository helpers do not commit transactions
- repository helpers do not call current time
- repository helpers do not generate random IDs
- repository helpers preserve caller snapshots
- repository helpers do not mutate input snapshots
- repository output is deterministic
- prepare_agent_run_upsert helper exists
- prepare_agent_step_upsert helper exists
- did_create_connection: false
- did_commit_transaction: false
- did_run_migration: false
- did_schedule_background_work: false
- did_execute_scheduler: false
- did_execute_reporting_job: false
- did_export_files: false
- did_execute_application: false
- did_submit_application: false
- migration_runner_added: false
- no storage connection management added
- no transaction commit added
- no migration file added
- no migration runner added
- no migration execution enabled
- no API route added
- no UI action added
- no scheduler execution added
- no reporting job execution added
- no application execution added
- no application submission added
- no metrics emitter added
- no logging emitter added
- no audit writer added
- no file export writer added
- no FileResponse added
- no StreamingResponse added
- no file write helpers added
- no subprocess added
- no background task added
- no Thread or Process added
- agent state storage preserves existing queue safety gates
- agent state storage preserves existing execution safety gates
- agent state storage preserves submission safety gates
- agent state storage preserves scheduler decision safety gates
- agent state storage preserves live scheduler decision safety gates
- agent state storage preserves production observability safety gates
- agent state storage preserves reporting job safety boundaries
- agent state storage preserves cache behavior
- agent state storage preserves retry behavior
- agent state storage preserves deduplication
- agent state storage preserves ranking
- agent state storage preserves metrics behavior
- agent state storage preserves ATS health behavior
- migration runner must be separate future phase
- API integration must be separate future phase
- UI integration must be separate future phase
- scheduler/background implementation must be separate future phase
- reporting job execution must be separate future phase

## Non-goals

- No API endpoint.
- No UI action.
- No scheduler or background work.
- No reporting job execution.
- No file export.
- No active emitters.
- No application execution.
- No application submission.
- No scoring changes.
- No prefilter relevance changes.
- No LLM evaluation changes.
- No execution changes.
- No submission changes.
- No scheduler changes.
- No cache changes.
- No retry changes.
- No deduplication changes.
- No ranking changes.
- No metrics behavior changes.
- No ATS health behavior changes.
- No approval store changes.
- No approval schema changes.
- No automatic DB connection management.
- No transaction commit.
- No migration runner.

## Storage safety contract

The agent state storage repository has no commit behavior, no connection creation, and preserves idempotency for repeated schema/repository preparation calls with the same inputs.
