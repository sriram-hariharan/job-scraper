# Critic/Evaluator explicit read-only API action readiness checkpoint

Step 202A is docs/tests only. This checkpoint records Critic/Evaluator explicit read-only API action readiness for a future explicit read-only API action that can call the isolated Critic/Evaluator runtime skeleton later. It has no API implementation, no endpoint implementation, and no API route change.

The future explicit read-only API action is a planning surface only. Step 202A does not modify `src/app/api.py`, does not wire evaluator behavior into API/runtime, and does not change the existing read-only Agent Trace API endpoint.

## Endpoint contract proposal

Contract phrase: endpoint contract proposal.

Future route shape, not implemented in this checkpoint:

POST /api/agentic-approvals/{approval_request_id}/critic-evaluator-readonly

The future route must be explicit user action only, read-only, deterministic, no storage writes, no LLM calls, no approval mutation, no scoring change, no pipeline wiring, and no application execution/submission. It may call the Critic/Evaluator runtime skeleton in `src/agents/critic_evaluator.py`, including evaluate_agent_trace and build_empty_evaluator_result, against trace-only evaluation inputs from the read-only Agent Trace API endpoint.

## Request contract

Contract phrase: request contract.

Future request contract fields:

- approval_request_id
- trace payload source
- optional evaluator_rubric_version
- no mutation fields

The request contract must not include approval mutation fields, ranking fields, scoring mutation fields, application execution fields, application submission fields, storage write directives, LLM provider directives, or pipeline wiring directives.

## Response contract

Contract phrase: response contract.

Future response contract fields:

- evaluator_status
- evaluator_findings
- evaluator_warnings
- evaluator_recommendations
- requires_human_review
- deterministic_rubric_version
- did_write_storage
- did_call_llm
- did_mutate_approval
- did_change_score
- did_execute_application
- did_submit_application

The future response should keep did_write_storage, did_call_llm, did_mutate_approval, did_change_score, did_execute_application, and did_submit_application false for this read-only evaluation action.

## Error handling contract

Contract phrase: error handling contract.

- Missing trace payload source should return a deterministic read-only error.
- Missing approval_request_id should return a deterministic read-only error.
- Unsupported evaluator_rubric_version should return a deterministic read-only error.
- Empty traces may safely return the evaluator_status and requires_human_review result from the Critic/Evaluator runtime skeleton.
- Errors must not write storage, call LLMs, mutate approvals, change scores, wire the pipeline, execute applications, or submit applications.

## Safety boundary

- docs/tests only
- future explicit read-only API action
- Critic/Evaluator explicit read-only API action readiness
- Critic/Evaluator runtime skeleton
- src/agents/critic_evaluator.py
- evaluate_agent_trace
- build_empty_evaluator_result
- evaluator_status
- evaluator_findings
- evaluator_warnings
- evaluator_recommendations
- requires_human_review
- deterministic_rubric_version
- read-only evaluation
- trace-only evaluation inputs
- explicit user action
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

## Implementation guardrails

Contract phrase: implementation guardrails.

- Do not implement the API route.
- Do not modify `src/app/api.py`.
- Do not wire evaluator into API/runtime.
- Do not add endpoint implementation.
- Do not add API route change.
- Do not add UI behavior.
- Do not add storage writes.
- Do not add schema migration.
- Do not add pipeline wiring.
- Do not add scheduler/background work.
- Do not add file export.
- Do not add live LLM call or model provider call.
- Do not add approval mutation.
- Do not add ranking change or scoring change.
- Do not add application execution or application submission.

## Non-goals

Contract phrase: non-goals.

- No API implementation.
- No endpoint implementation.
- No API route change.
- No `src/app/api.py` changes.
- No frontend JS changes.
- No storage/schema/migration changes.
- No pipeline, scheduler, workflow runner, approvals, ranking, scoring, application execution, application submission, or LLM flow changes.

## Rollback plan

Contract phrase: rollback plan.

Rollback for Step 202A is documentation-only: remove this document, remove the focused test file, and remove the README and orchestrator readiness links. Because this checkpoint adds no API behavior, no UI behavior, no runtime behavior, no storage writes, no schema migration, no LLM calls, no model provider calls, no approval mutation, no ranking change, no scoring change, no application execution, and no application submission, rollback has no production data or behavior impact.

## Verification plan

Contract phrase: verification plan.

- Focused tests: `tests/test_critic_evaluator_readonly_api_action_readiness_checkpoint.py`.
- Verify this document exists.
- Verify README links to this document.
- Verify `docs/orchestrator_readiness.md` links to this document.
- Verify required Critic/Evaluator explicit read-only API action readiness terms are present.
- Verify the endpoint contract proposal names `POST /api/agentic-approvals/{approval_request_id}/critic-evaluator-readonly` as a future route shape only.
- Verify request contract, response contract, and error handling contract terms are present.
- Verify Step 202A remains docs/tests only and does not modify runtime code, `src/`, API, frontend JS, storage/schema/migrations, pipeline, scheduler, workflow runner, approvals behavior, application execution, application submission, ranking, scoring, or LLM calls.
