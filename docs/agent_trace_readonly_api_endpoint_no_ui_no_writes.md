# Agent Trace read-only API endpoint

Step 190A adds a read-only backend API endpoint for Agent Trace retrieval. It exposes existing trace-shaped data for a future UI, but it adds no UI changes, no storage writes, no schema migration, no pipeline wiring, no scheduler, no background task, no file export, no application execution, no application submission, no live LLM call, and no approval mutation.

The endpoint is deterministic and does not create agent_runs or create agent_steps. It only prepares read-only trace responses from caller-supplied identifiers and existing read helpers.

## Endpoint contract

- Endpoint: `GET /api/agentic-approvals/{approval_request_id}/agent-trace`
- Query parameter: `agent_run_id`, optional.
- The endpoint is read-only.
- The endpoint uses caller-supplied approval or run identifiers.
- The endpoint returns a not found trace safely when no trace storage connection is available.
- The endpoint returns an empty trace safely when a run exists with zero ordered agent steps.
- The endpoint returns ordered agent steps when trace data exists.
- The endpoint does not mutate approvals.
- The endpoint does not create agent_runs.
- The endpoint does not create agent_steps.
- The endpoint does not execute pipeline.
- The endpoint does not wire trace creation into workflow runner.

## Response contract

The response contains:

- `found`
- `agent_run`
- `agent_steps`
- `step_count`
- `empty_trace`
- `safety_metadata`

Trace exists responses set `found` to true when an agent run is present. Run exists with zero steps responses set `found` to true, `step_count` to 0, and `empty_trace` to true. Not found trace responses set `found` to false, `agent_run` to `{}`, `agent_steps` to `[]`, `step_count` to 0, and `empty_trace` to true.

Ordered agent steps are sorted deterministically by step index, observed timestamp, agent step id, and agent step key. The endpoint supports empty trace and not found trace without raising write-side behavior.

## Storage read helper contract

`src/storage/agent_state/store.py` adds read-only SELECT helper payloads only:

- `prepare_agent_run_select`
- `prepare_agent_steps_select_for_run`
- Focused tests: `tests/test_agent_trace_readonly_api_endpoint_no_ui_no_writes.py`

The helpers do not add INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, UPSERT, commit, connection creation, migration, scheduler, export, execution, submission, or LLM behavior.

## Safety metadata contract

The endpoint returns safety metadata with:

- `read_only: true`
- `did_create_agent_run: false`
- `did_create_agent_step: false`
- `did_mutate_approval: false`
- `did_execute_pipeline: false`
- `did_schedule_background_work: false`
- `did_execute_scheduler: false`
- `did_export_files: false`
- `did_execute_application: false`
- `did_submit_application: false`
- `did_call_llm_provider: false`
- `did_create_connection: false`
- `did_commit_transaction: false`
- `did_run_migration: false`
- `ui_action_added: false`
- `pipeline_wiring_added: false`

## Non-goals

- No frontend trace panel yet.
- No UI action.
- No frontend/static file changes.
- No trace creation.
- No workflow runner changes.
- No live pipeline wiring.
- No storage writes.
- No schema migration.
- No migration execution.
- No scheduler/background task.
- No file export.
- No application execution.
- No application submission.
- No live LLM call.
- No approval mutation.

## Rollback plan

Rollback is limited to removing the read-only API helper/route, removing the read-only SELECT preparation helpers if unused, removing the focused tests, and removing the README/orchestrator readiness links. No UI, schema, migration, scheduler, pipeline, execution, submission, or approval-storage rollback is required.

## Verification plan

- Verify the endpoint exists and is GET-only.
- Verify response shape is stable.
- Verify trace exists responses include agent run metadata and ordered agent steps.
- Verify run exists with zero steps is handled as empty trace.
- Verify not found trace is handled safely.
- Verify safety metadata is present and safe.
- Verify no frontend/static file is changed.
- Verify no schema SQL or migration file is changed.
- Verify no INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, commit, connection creation, scheduler, export, application execution, application submission, pipeline execution, or LLM call is introduced.

## endpoint contract

The endpoint contract is read-only and returns agent trace data without creating agent_runs, creating agent_steps, mutating approvals, executing the pipeline, exporting files, or submitting applications.

## response contract

The response contract includes found, agent_run, agent_steps, step_count, empty_trace, ordered agent steps, and safety metadata.

## rollback plan

The rollback plan is to remove the read-only endpoint/doc/test changes and keep the existing trace recorder, storage schema, wrappers, pipeline, scheduler, API approval behavior, and UI behavior unchanged.

## verification plan

The verification plan is to run the focused read-only API tests, documentation tests, and full test suite while confirming no UI changes, no storage writes, no schema migration, no pipeline wiring, no scheduler, no background task, no file export, no live LLM call, no application execution, and no application submission.
