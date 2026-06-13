# Critic/Evaluator runtime skeleton without LLM calls

Step 200A adds an isolated deterministic skeleton in `src/agents/critic_evaluator.py`. It evaluates already-built trace-only evaluation inputs as plain Python data and returns a deterministic evaluator contract without calling models, changing scoring, writing storage, wiring pipeline execution, or changing API/UI behavior.

This phase has no live LLM call, no model provider call, no API behavior change, no UI behavior change, no storage writes, no schema migration, no pipeline wiring, no scheduler, no background task, no file export, no approval mutation, no ranking change, no scoring change, no application execution, and no application submission.

## Runtime skeleton contract

The isolated deterministic skeleton exposes:

- `CRITIC_EVALUATOR_RUBRIC_VERSION`
- `build_empty_evaluator_result`
- `evaluate_agent_trace`

The evaluator output contract contains:

- evaluator_status
- evaluator_findings
- evaluator_warnings
- evaluator_recommendations
- requires_human_review
- deterministic_rubric_version

## Deterministic rubric checks

The trace-only rubric checks:

1. trace completeness
2. agent step ordering
3. safety metadata completeness
4. validation_json consistency
5. separation of prefilter relevance, LLM evaluation, and final application scoring
6. no application execution or submission judgment

The skeleton does not judge whether a candidate should apply, does not change application scoring, does not call LLMs, does not mutate input, and does not write files or database rows.

## Safety boundary

- isolated deterministic skeleton
- no live LLM call
- no model provider call
- no API behavior change
- no UI behavior change
- no storage writes
- no schema migration
- no pipeline wiring
- no scheduler
- no background task
- no file export
- no approval mutation
- no ranking change
- no scoring change
- no application execution
- no application submission
- trace-only evaluation inputs

## Rollback plan

Contract phrase: rollback plan.

Rollback is limited to removing `src/agents/critic_evaluator.py`, removing the focused tests, removing this document, and removing README/orchestrator readiness links. No API, UI, storage, schema, migration, pipeline, scheduler, workflow runner, approval, ranking, scoring, LLM, application execution, or application submission rollback is required.

## Verification plan

Contract phrase: verification plan.

- Focused tests: `tests/test_critic_evaluator_runtime_skeleton_no_llm_no_pipeline.py`.
- Verify the evaluator returns evaluator_status, evaluator_findings, evaluator_warnings, evaluator_recommendations, requires_human_review, and deterministic_rubric_version.
- Verify identical trace inputs produce identical outputs.
- Verify the evaluator does not mutate input.
- Verify empty trace requires human review.
- Verify missing safety metadata creates a warning/finding.
- Verify invalid or missing validation_json creates a warning/finding.
- Verify ordered trace passes the ordering check.
- Verify out-of-order trace creates a warning/finding.
- Verify no provider/network/storage/pipeline/execution markers are introduced in the isolated skeleton.
