# Agent Trace read-only UI panel

Step 191A adds a read-only frontend Agent Trace panel that consumes the existing Step 190A endpoint. This phase adds no API changes, no storage changes, no storage writes, no schema migration, no pipeline wiring, no scheduler, no background task, no file export, no application execution, no application submission, no live LLM call, and no approval mutation.

The panel is deterministic. It displays existing trace retrieval responses only and does not create agent runs, create agent steps, persist trace rows, update approvals, submit applications, trigger execution, or write files.

## UI contract

- Frontend file: `src/app/static/agentic_review.js`.
- The Agent Trace panel is read-only.
- The panel fetches existing trace data with GET only.
- The panel displays ordered agent steps when they are returned.
- The panel displays empty trace state when a run exists but has no ordered agent steps.
- The panel displays not found trace state when no trace exists for the approval request.
- The panel displays safety metadata.
- The panel displays `validation_json`.
- The panel displays agent run metadata without editing it.
- The panel displays input and output summaries without editing them.
- The panel has no approve action.
- The panel has no apply action.
- The panel has no submit action.
- The panel has no run action.
- The panel has no retry action.
- The panel has no export action.
- The panel adds no buttons for trace mutation.

## Endpoint dependency

- Endpoint dependency: `GET /api/agentic-approvals/{approval_request_id}/agent-trace`.
- The UI uses the existing read-only endpoint from Step 190A.
- This phase adds no API changes.
- This phase adds no backend route.
- This phase adds no storage helper.
- This phase adds no migration.
- Existing fallback profile trace display remains GET-only for run-based pages without an approval request id.

## Safety contract

- no API changes
- no storage changes
- no storage writes
- no schema migration
- no pipeline wiring
- no scheduler
- no background task
- no file export
- no application execution
- no application submission
- no live LLM call
- no approval mutation
- no approval storage mutation
- no queue mutation
- no database writes
- no reporting job
- no live emitter
- deterministic

The panel is a display-only surface. It must not contain approve, apply, submit, run, retry, or export controls. Fetch failure handling remains read-only and preserves the page.

## Rollback plan

Rollback is limited to removing the read-only frontend panel wiring, removing this doc, removing the focused UI tests, and removing README/orchestrator readiness links. No API rollback, storage rollback, schema rollback, migration rollback, scheduler rollback, pipeline rollback, execution rollback, submission rollback, or approval-storage rollback is required.

## Verification plan

- Focused tests: `tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py`.
- Verify the panel renders the Agent Trace read-only UI surface.
- Verify the panel uses GET-only trace retrieval.
- Verify the panel depends on `GET /api/agentic-approvals/{approval_request_id}/agent-trace`.
- Verify empty trace and not found trace states are visible.
- Verify ordered agent steps, safety metadata, and `validation_json` are visible.
- Verify no approve, apply, submit, run, retry, or export controls are added.
- Verify protected API, storage, schema, workflow, pipeline, scheduler, execution, and submission files are unchanged.
- Verify documentation links and doc tests cover the Step 191A contract.

## endpoint dependency

The endpoint dependency is the existing read-only Agent Trace backend API endpoint from Step 190. This UI panel only reads from that endpoint and does not add backend API changes.

## safety contract

The safety contract is read-only: no approve, no apply, no submit, no run, no retry, no export, no approval mutation, no storage writes, no schema migration, no pipeline wiring, no scheduler, no background task, no file export, no live LLM call, no application execution, and no application submission.

## rollback plan

The rollback plan is to remove the read-only UI panel, this documentation, and focused tests while leaving the existing read-only backend endpoint, storage, schema, workflow runner, scheduler, pipeline, approvals, and application execution behavior unchanged.

## verification plan

The verification plan is to run the focused read-only UI tests, documentation tests, and full test suite while confirming no API changes, no storage changes, no storage writes, no schema migration, no pipeline wiring, no scheduler, no background task, no file export, no application execution, and no application submission.
