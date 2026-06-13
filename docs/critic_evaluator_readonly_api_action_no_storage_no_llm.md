# Critic/Evaluator explicit read-only API action

Step 203A adds an explicit read-only API action for the existing Critic/Evaluator runtime skeleton. The route is:

`POST /api/agentic-approvals/{approval_request_id}/critic-evaluator-readonly`

This endpoint is an explicit read-only API action and an explicit user action. It performs read-only evaluation over trace-only evaluation inputs by calling `evaluate_agent_trace`; it does not persist, execute, submit, score, rank, or wire anything into the pipeline.

## Current scope

- Critic/Evaluator runtime skeleton
- evaluate_agent_trace
- read-only evaluation
- trace-only evaluation inputs
- deterministic
- no storage writes
- no schema migration
- no live LLM call
- no model provider call
- no approval mutation
- no ranking change
- no scoring change
- no pipeline wiring
- no scheduler
- no background task
- no file export
- no application execution
- no application submission

## Response contract

The response includes the deterministic evaluator fields:

- evaluator_status
- evaluator_findings
- evaluator_warnings
- evaluator_recommendations
- requires_human_review
- deterministic_rubric_version

The response also includes disabled safety flags:

- did_write_storage
- did_call_llm
- did_mutate_approval
- did_change_score
- did_execute_application
- did_submit_application

All safety flags remain false for this read-only action.

## rollback plan

Rollback is removal of the single API route, the request model, the Step 203A tests, and this documentation link. No storage, schema, migration, pipeline, scheduler, approval, ranking, scoring, execution, submission, UI, or LLM state is introduced by this step.

## verification plan

Verify the route accepts plain trace payload data, returns the evaluator contract, keeps all disabled safety flags false, leaves empty traces requiring human review, and introduces no storage write, schema migration, live LLM call, model provider call, approval mutation, ranking change, scoring change, pipeline wiring, scheduler, background task, file export, application execution, or application submission behavior.

Focused coverage lives in `tests/test_critic_evaluator_readonly_api_action_no_storage_no_llm.py`.
