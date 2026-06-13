# LangGraph orchestration spike readiness checkpoint

Step 198A is docs/tests only. This checkpoint records LangGraph orchestration spike readiness for a future LangGraph orchestration spike using the existing agents, JobApplicationContext, trace recorder, and wrapped agents without dependency installation, graph runtime code, pipeline wiring, or behavior changes now.

The checkpoint is deterministic and has no dependency installation, no LangGraph dependency, no graph runtime code, no behavior change, no API behavior change, no UI behavior change, no storage writes, no schema migration, no pipeline wiring, no scheduler, no background task, no file export, no live LLM call, no model provider call, no approval mutation, no ranking change, no scoring change, no application execution, and no application submission.

## State graph proposal

Contract phrase: state graph proposal.

The future state graph proposal is conceptual only. It may map existing agents onto deterministic trace-shaped steps, including Relevance Prefilter Agent, Deduplication Agent, JD Intelligence Agent, Final Application Scoring Agent, Critic/Evaluator agent readiness, and Feedback learning loop readiness. It must preserve the read-only Agent Trace API endpoint and read-only Agent Trace UI panel as display and retrieval surfaces only.

The future spike may reference prefilter relevance, deduplication, JD intelligence, final application scoring, LLM evaluation, application execution, and application submission only as separated trace-visible concepts. It must not add LangGraph dependency, graph runtime code, model provider calls, live LLM calls, ranking changes, scoring changes, approval mutation, storage writes, scheduler work, background task work, file export behavior, application execution, or application submission.

## Node inventory

Contract phrase: node inventory.

Future node inventory:

- agent_state_initialization
- relevance_prefilter
- deduplication
- jd_intelligence
- final_application_scoring
- critic_evaluator
- feedback_learning_loop

## Edge inventory

Contract phrase: edge inventory.

Future deterministic edge inventory:

agent_state_initialization -> relevance_prefilter -> deduplication -> jd_intelligence -> final_application_scoring -> critic_evaluator -> feedback_learning_loop

## Routing constraints

Contract phrase: routing constraints.

- Routing must remain deterministic.
- Routing must preserve separation between prefilter relevance, deduplication, JD intelligence, final application scoring, LLM evaluation, application execution, and application submission.
- Routing must preserve JobApplicationContext as the future trace state input shape.
- Routing must not wire the graph into live pipeline execution.
- Routing must not add scheduler, background task, API, UI, storage, schema, migration, ranking, scoring, approval, execution, submission, or model provider behavior.

## Side-effect boundaries

Contract phrase: side-effect boundaries.

Future graph nodes cannot perform:

- application execution
- application submission
- approval mutation
- storage writes
- scheduler/background work
- file export
- live LLM call

## Implementation guardrails

Contract phrase: implementation guardrails.

- docs/tests only
- future LangGraph orchestration spike remains future work.
- no dependency installation
- no LangGraph dependency
- no graph runtime code
- no behavior change
- no API behavior change
- no UI behavior change
- no storage writes
- no schema migration
- no pipeline wiring
- no scheduler
- no background task
- no file export
- no live LLM call
- no model provider call
- no approval mutation
- no ranking change
- no scoring change
- no application execution
- no application submission
- deterministic

## Non-goals

Contract phrase: non-goals.

- Do not implement LangGraph.
- Do not add dependencies.
- Do not add runtime graph code.
- Do not change pipeline wiring.
- Do not call LLMs.
- Do not call model providers.
- Do not change scoring or ranking.
- Do not add API behavior.
- Do not add UI behavior.
- Do not add storage writes or schema migration.
- Do not add application execution or application submission.

## Rollback plan

Contract phrase: rollback plan.

Rollback for Step 198A is documentation-only: remove this document, remove the focused test file, and remove the README and orchestrator readiness links. Because this checkpoint adds no runtime behavior, no API behavior, no UI behavior, no storage writes, no schema migration, no dependency installation, no LangGraph dependency, no graph runtime code, no LLM calls, no model provider calls, no ranking change, no scoring change, no application execution, and no application submission, rollback has no production data or behavior impact.

## Verification plan

Contract phrase: verification plan.

- Focused tests: `tests/test_langgraph_orchestration_spike_readiness_checkpoint.py`.
- Verify this document exists.
- Verify README links to this document.
- Verify `docs/orchestrator_readiness.md` links to this document.
- Verify required LangGraph orchestration spike readiness terms are present.
- Verify the node inventory includes agent_state_initialization, relevance_prefilter, deduplication, jd_intelligence, final_application_scoring, critic_evaluator, and feedback_learning_loop.
- Verify the edge inventory describes the future deterministic order from agent_state_initialization through feedback_learning_loop.
- Verify side-effect boundaries say future graph nodes cannot perform application execution, application submission, approval mutation, storage writes, scheduler/background work, file export, or live LLM call.
- Verify Step 198A remains docs/tests only and does not modify runtime code, `src/`, API, frontend JS, storage/schema/migrations, pipeline, scheduler, workflow runner, approvals behavior, application execution, application submission, ranking, scoring, LLM calls, model/provider client calls, LangGraph dependency, or graph runtime code.
