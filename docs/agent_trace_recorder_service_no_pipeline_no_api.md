# Agent Trace Recorder Service, No Pipeline, No API

Step 184A adds lightweight deterministic trace recorder helpers in `src/agents/trace.py` for caller-supplied agent run and agent step snapshots. The helpers build recording payloads through the isolated `src/storage/agent_state/store.py` SQL preparation helpers and can execute only when a caller explicitly injects a cursor or execution callback.

This phase does not wire the trace recorder into the live pipeline. It adds no API endpoint, UI action, scheduler/background work, reporting job execution, file export, metrics/logging/audit emitters, application execution, application submission, database connection creation, transaction commit, current time call, random ID generation, schema change, migration runner change, approval store change, or approval schema change.

## Scope

- Trace recorder helper path: `src/agents/trace.py`
- Agent state snapshot source remains: `src/agents/agent_state.py`
- Agent state storage helper source remains: `src/storage/agent_state/store.py`
- Schema source remains: `src/storage/agent_state/schema.sql`
- Migration runner source remains: `src/storage/agent_state/migration_runner.py`
- Focused tests: `tests/test_agent_trace_recorder_service_no_pipeline_no_api.py`

## Verification contract phrases

- Agent trace recorder service no pipeline no API: PASS
- Agent trace recorder implementation: LIGHTWEIGHT_HELPERS_ONLY
- Runtime-facing integration scope: TRACE_RECORDER_HELPERS_ONLY
- Trace recorder helper path: src/agents/trace.py
- Agent state snapshot source: src/agents/agent_state.py
- Agent state storage helper source: src/storage/agent_state/store.py
- build_agent_run_record_payload helper exists
- build_agent_step_record_payload helper exists
- build_agent_trace_recording_payload helper exists
- build_fake_smoke_trace_payload helper exists
- execute_agent_trace_recording helper exists
- caller-supplied run snapshot required
- caller-supplied step snapshots required
- fake smoke trace has exactly one agent run
- fake smoke trace has exactly one agent step
- trace payload creation is deterministic
- repeated trace payload calls produce identical output
- trace recorder does not mutate caller-owned snapshots
- trace recorder does not mutate caller-owned lists
- trace recorder uses agent_state storage preparation helpers
- execution requires injected cursor or injected execution callback
- fake cursor receives expected operations only when explicitly invoked
- trace recorder does not create database connections
- trace recorder does not commit transactions
- trace recorder does not run migrations
- trace recorder does not call current time
- trace recorder does not generate random IDs
- import has no side effects
- did_create_connection: false
- did_commit_transaction: false
- did_run_migration: false
- did_schedule_background_work: false
- did_execute_scheduler: false
- did_execute_reporting_job: false
- did_export_files: false
- did_execute_application: false
- did_submit_application: false
- api_route_added: false
- ui_action_added: false
- pipeline_wiring_added: false
- no live pipeline integration added
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
- no schema SQL modified
- no migration runner modified
- no approval store modified
- no approval schema modified
- no workflow runner modified
- no application execution queue modified
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
- pipeline integration must be separate future phase
- API integration must be separate future phase
- UI integration must be separate future phase
- scheduler/background implementation must be separate future phase
- reporting job execution must be separate future phase

## Safety contract

The trace recorder is a deterministic preparation and explicit-recording helper only. It is not a pipeline hook, API route, UI action, scheduler, reporter, exporter, emitter, execution path, or submission path.

## Trace recorder safety contract

The trace recorder prepares records for agent_runs and agent_steps using JobApplicationContext-derived snapshots.

It has no pipeline wiring, no background task, no connection creation, no commit behavior, and requires explicit caller invocation with caller-supplied snapshots and caller-supplied execution objects.

The helper remains deterministic and does not execute API, UI, scheduler, reporting job, file export, application execution, or application submission behavior.
