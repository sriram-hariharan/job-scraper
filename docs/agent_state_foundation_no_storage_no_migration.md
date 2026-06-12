# Agent State Foundation, No Storage, No Migration

Step 179A adds a pure deterministic agent state foundation module at `src/agents/agent_state.py`. It introduces a serializable `JobApplicationContext` model and pure trace snapshot helpers without storage, migrations, scheduler work, reporting job execution, file export, emitters, application execution, or application submission.

## Scope

- Pure module path: `src/agents/agent_state.py`
- Focused tests: `tests/test_agent_state_foundation_no_storage_no_migration.py`
- No API route added.
- No UI action added.
- No protected execution, approval storage, scheduler, submission, workflow runner, schema, or migration files modified.

The helpers require caller-supplied timestamps. They do not call current time internally and do not generate random identifiers. Keys are derived deterministically from supplied inputs.

## Verification contract phrases

- Agent state foundation no storage no migration: PASS
- Agent state foundation implementation: PURE_MODULE_ONLY
- Runtime-facing integration scope: PURE_HELPERS_ONLY
- Pure module path: src/agents/agent_state.py
- JobApplicationContext implementation: GO
- Trace helper implementation: GO
- API endpoint implementation: NO_GO
- UI action implementation: NO_GO
- Storage implementation: NO_GO
- Agent runs storage: NO_GO
- Agent steps storage: NO_GO
- DB schema implementation: NO_GO
- SQL DDL implementation: NO_GO
- Migration implementation: NO_GO
- Scheduler/background work: NO_GO
- Reporting job execution: NO_GO
- File export creation: NO_GO
- Metrics emitter: NO_GO
- Logging emitter: NO_GO
- Audit writer: NO_GO
- Application execution: NO_GO
- Application submission: NO_GO
- JobApplicationContext is deterministic
- JobApplicationContext serializes to a plain dict
- JobApplicationContext includes context_id
- JobApplicationContext includes context_key
- JobApplicationContext includes approval_request_id
- JobApplicationContext includes job_id
- JobApplicationContext includes candidate_key
- JobApplicationContext includes role_family
- JobApplicationContext includes run_mode
- JobApplicationContext includes observed_at_utc
- JobApplicationContext includes metadata
- timestamps are supplied by caller
- no current time call
- no random ID generation
- IDs and keys are derived deterministically from inputs
- build_agent_run_snapshot helper exists
- build_agent_step_snapshot helper exists
- append_trace_step helper exists
- append_trace_step returns a new structure
- append_trace_step does not mutate input
- did_persist_state: false
- did_write_agent_run: false
- did_write_agent_step: false
- did_schedule_background_work: false
- did_execute_scheduler: false
- did_execute_reporting_job: false
- did_export_files: false
- did_execute_application: false
- did_submit_application: false
- migration_required: false
- persistence_enabled: false
- no storage module modified in this phase
- no SQL file modified in this phase
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
- no persistent storage writer added
- no file response class added
- no streaming response class added
- no file write helpers added
- no subprocess added
- no background task added
- no Thread or Process added
- agent state preserves existing queue safety gates
- agent state preserves existing execution safety gates
- agent state preserves submission safety gates
- agent state preserves scheduler decision safety gates
- agent state preserves live scheduler decision safety gates
- agent state preserves production observability safety gates
- agent state preserves reporting job safety boundaries
- agent state preserves cache behavior
- agent state preserves retry behavior
- agent state preserves deduplication
- agent state preserves ranking
- agent state preserves metrics behavior
- agent state preserves ATS health behavior
- storage implementation must be separate future phase
- migration implementation must be separate future phase
- API integration must be separate future phase
- scheduler/background implementation must be separate future phase
- reporting job execution must be separate future phase

## Non-goals

- No database tables.
- No `agent_runs` storage.
- No `agent_steps` storage.
- No migration.
- No SQL execution.
- No API endpoint.
- No scheduler or background work.
- No reporting job execution.
- No file export.
- No active emitter.
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

## Idempotency

The agent state foundation is deterministic and preserves idempotency for repeated context and trace snapshot calls with the same inputs.
