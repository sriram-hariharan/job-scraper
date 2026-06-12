# Agent State Migration Runner, No API, No Scheduler

Step 183A adds an isolated agent state migration runner helper for the already-reviewed `agent_runs` and `agent_steps` schema. The runner is explicit only: callers must pass schema SQL text and a cursor-like object. It does not read schema files internally, create database connections, commit transactions, run at import time, add an API route, add a UI action, schedule background work, execute reporting jobs, export files, emit metrics/logs/audits, execute applications, or submit applications.

## Scope

- Migration runner path: `src/storage/agent_state/migration_runner.py`
- Schema source remains: `src/storage/agent_state/schema.sql`
- Repository helper source remains: `src/storage/agent_state/store.py`
- Focused tests: `tests/test_agent_state_migration_runner_no_api_no_scheduler.py`
- No API route added.
- No UI action added.
- No scheduler or background task added.
- No reporting job execution added.
- No file export added.
- No application execution added.
- No application submission added.
- No approval store or approval schema files modified.

## Verification contract phrases

- Agent state migration runner no API no scheduler: PASS
- Agent state migration runner implementation: EXPLICIT_CALLER_SUPPLIED_CURSOR_ONLY
- Runtime-facing integration scope: ISOLATED_MIGRATION_RUNNER_ONLY
- Migration runner path: src/storage/agent_state/migration_runner.py
- Schema path: src/storage/agent_state/schema.sql
- Repository helper path: src/storage/agent_state/store.py
- build_agent_state_migration_plan helper exists
- run_agent_state_migration helper exists
- caller-supplied schema SQL text required
- caller-supplied cursor required
- runner does not read files internally
- runner does not create database connections
- runner does not commit transactions
- runner does not call current time
- runner does not generate random IDs
- runner does not mutate caller-owned schema text
- runner validates agent state schema scope before execution
- runner requires agent_runs
- runner requires agent_steps
- runner rejects approval_requests
- runner rejects agentic_approvals
- runner rejects application_execution
- runner rejects application_submissions
- runner splits SQL deterministically
- migration plan output is deterministic
- repeated migration plan calls produce identical metadata
- run helper executes only prepared statements on injected cursor
- import has no side effects
- did_create_connection: false
- did_commit_transaction: false
- did_schedule_background_work: false
- did_execute_scheduler: false
- did_execute_reporting_job: false
- did_export_files: false
- did_execute_application: false
- did_submit_application: false
- api_route_added: false
- ui_action_added: false
- no API endpoint added
- no UI action added
- no scheduler/background work added
- no reporting job execution added
- no file export creation added
- no metrics emitter added
- no logging emitter added
- no audit writer added
- no application execution added
- no application submission added
- no startup execution added
- no import-time execution added
- no page-load execution added
- no approval store modification
- no approval schema modification
- no workflow runner modification
- no application execution queue modification
- no protected execution behavior modified
- no scoring behavior modified
- no prefilter relevance behavior modified
- no LLM evaluation behavior modified
- no scheduler behavior modified
- no cache behavior modified
- no retry behavior modified
- no deduplication behavior modified
- no ranking behavior modified
- no metrics behavior modified
- no ATS health behavior modified
- API integration must be separate future phase
- UI integration must be separate future phase
- scheduler/background implementation must be separate future phase
- reporting job execution must be separate future phase

## Safety contract

The migration runner is not an application startup hook, page-load hook, scheduler, reporter, exporter, emitter, execution path, or submission path. Migration execution can only occur when a caller explicitly invokes `run_agent_state_migration(cursor, schema_sql)` with both a schema string and a cursor-like object.

## Migration runner safety contract

The isolated agent state migration runner has no background task, no connection creation, no commit behavior, and preserves idempotency for repeated migration plan preparation with the same schema input.

Migration execution happens only through explicit caller invocation with a caller-supplied cursor and caller-supplied schema SQL.
