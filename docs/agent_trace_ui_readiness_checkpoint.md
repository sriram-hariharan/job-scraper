# Agent Trace UI readiness checkpoint

Step 189A is a docs/tests only readiness checkpoint for a future read-only Agent Trace UI. It maps the intended API and UI implementation path onto the existing repository structure without changing runtime behavior.

This checkpoint adds no behavior change, no API behavior change, no UI behavior change, no pipeline wiring, no scheduler, no background task, no storage writes, no schema migration, no file export, no application execution, and no application submission. The plan is read-only and deterministic.

## Current foundation inventory

- JobApplicationContext exists in `src/agents/agent_state.py` as the deterministic job/application context payload helper.
- agent_runs exists as the planned agent-run storage table in `src/storage/agent_state/schema.sql`.
- agent_steps exists as the planned ordered step storage table in `src/storage/agent_state/schema.sql`.
- migration runner exists in `src/storage/agent_state/migration_runner.py` and remains explicitly invoked only.
- trace recorder exists in `src/agents/trace.py` and prepares caller-supplied trace payloads without opening connections internally.
- Relevance Prefilter Agent wrapper exists in `src/agents/relevance_prefilter.py`.
- Deduplication Agent wrapper exists in `src/agents/deduplication.py`.
- JD Intelligence Agent wrapper exists in `src/agents/jd_intelligence.py`.
- Final Application Scoring Agent wrapper exists in `src/agents/final_application_scoring.py`.
- Focused readiness tests: `tests/test_agent_trace_ui_readiness_checkpoint.py`.

## Proposed next implementation path

1. Add a read-only backend trace retrieval endpoint in a future phase.
2. Add a read-only frontend trace panel in a future phase.
3. Make no edits to workflow runner in first UI step.
4. Add no live pipeline wiring in first UI step.

The future backend should be limited to retrieval and presentation of existing trace data. The future frontend should only render the retrieved trace data and empty states.

## Intended API contract for next implementation step

- The future endpoint is a read-only endpoint.
- The future endpoint accepts a caller-supplied run or approval identifier.
- The future endpoint returns agent run metadata and ordered agent steps.
- The future endpoint supports empty trace safely.
- The future endpoint does not create agent runs.
- The future endpoint does not create agent steps.
- The future endpoint does not mutate approvals.
- The future endpoint does not execute pipeline.
- The future endpoint must not create DB connections internally unless a separate implementation checkpoint explicitly approves that boundary.
- The future endpoint must not commit transactions internally.
- The future endpoint must not perform scraping, filtering, deduplication, JD extraction, ranking, LLM evaluation, final application scoring, application execution, or application submission.

## Intended UI contract for next implementation step

- The future UI adds a read-only trace panel.
- The future UI shows ordered agent steps.
- The future UI shows agent name, status, started/completed timestamps if supplied, input/output summary, validation_json, and safety metadata.
- The future UI shows an empty-state message when no trace exists.
- The future UI adds no approve/apply/submit/run/retry/export action.
- The future UI must not trigger trace creation.
- The future UI must not trigger pipeline execution.
- The future UI must not mutate approvals.

## Safety contract terms

- no behavior change
- no API behavior change
- no UI behavior change
- no pipeline wiring
- no scheduler
- no background task
- no storage writes
- no schema migration
- no file export
- no application execution
- no application submission
- read-only
- deterministic

## Explicit separation

- prefilter relevance remains separate and is not called by this checkpoint.
- deduplication remains separate and is not called by this checkpoint.
- JD intelligence remains separate and is not called by this checkpoint.
- final application scoring remains separate and is not called by this checkpoint.
- LLM evaluation remains separate and is not called by this checkpoint.
- application execution remains separate and is not called by this checkpoint.
- application submission remains separate and is not called by this checkpoint.

## Rollback plan

Because this checkpoint is docs/tests only, rollback is limited to removing this document, removing the focused readiness tests, and removing the README/orchestrator readiness links. No runtime API, UI, storage, scheduler, pipeline, execution, or submission rollback is required.

## Verification plan for future implementation

- Verify the read-only endpoint is registered only for safe retrieval.
- Verify the endpoint accepts a caller-supplied run or approval identifier.
- Verify the endpoint returns agent run metadata and ordered agent steps.
- Verify empty trace responses are stable and safe.
- Verify no agent runs are created.
- Verify no agent steps are created.
- Verify approvals are not mutated.
- Verify pipeline execution is not triggered.
- Verify the read-only trace panel renders ordered agent steps.
- Verify the trace panel renders agent name, status, timestamps when supplied, input/output summary, validation_json, and safety metadata.
- Verify no approve/apply/submit/run/retry/export action is present.
- Verify no workflow runner edits are required in the first UI step.
- Verify no live pipeline wiring is added in the first UI step.

## UI no-action safety contract

The future read-only trace panel must expose no approve action, no apply action, no submit action, no run action, no retry action, and no export action.

Exact prohibited UI action phrases:
- no approve
- no apply
- no submit
- no run
- no retry
- no export
