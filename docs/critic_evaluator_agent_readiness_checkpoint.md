# Critic/Evaluator agent readiness checkpoint

Step 196A is docs/tests only. This checkpoint records Critic/Evaluator agent readiness for a future Critic/Evaluator agent that may review trace outputs and scoring quality later, without adding runtime evaluator code, model calls, pipeline wiring, or scoring changes now.

The checkpoint is deterministic and has no behavior change, no API behavior change, no UI behavior change, no storage writes, no schema migration, no pipeline wiring, no scheduler, no background task, no file export, no live LLM call, no model provider call, no approval mutation, no application execution, no application submission, and no scoring change.

## Trace-only evaluation inputs

Contract phrase: trace-only evaluation inputs.

The future Critic/Evaluator agent must use agent trace review over existing read-only trace artifacts only. The intended input surface is the read-only Agent Trace API endpoint and the read-only Agent Trace UI panel, including safety metadata review and validation_json review.

The future review scope may reference prefilter relevance, deduplication, JD intelligence, final application scoring, LLM evaluation, application execution, and application submission only as trace-visible concepts. It must not call live model providers, execute applications, submit applications, alter scores, or mutate approval state.

## Quality rubric

Contract phrase: quality rubric.

Future quality rubric:

1. trace completeness
2. agent step ordering
3. safety metadata completeness
4. validation_json consistency
5. separation of prefilter relevance, LLM evaluation, and final application scoring
6. no application execution or submission judgment

## Evaluator output contract

Contract phrase: evaluator output contract.

Future evaluator output contract fields:

- evaluator_status
- evaluator_findings
- evaluator_warnings
- evaluator_recommendations
- requires_human_review
- deterministic_rubric_version

These fields are a design contract only. Step 196A does not implement the agent, does not add storage for evaluator outputs, and does not add API or UI behavior.

## Implementation guardrails

Contract phrase: implementation guardrails.

- docs/tests only
- future Critic/Evaluator agent remains future work.
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
- no application execution
- no application submission
- no scoring change
- deterministic

## Non-goals

Contract phrase: non-goals.

- Do not implement the agent.
- Do not add runtime evaluator code.
- Do not call LLMs.
- Do not change scoring.
- Do not add pipeline wiring.
- Do not add API behavior.
- Do not add UI behavior.
- Do not add storage writes or schema migration.
- Do not add application execution or application submission.

## Rollback plan

Contract phrase: rollback plan.

Rollback for Step 196A is documentation-only: remove this document, remove the focused test file, and remove the README and orchestrator readiness links. Because this checkpoint adds no runtime behavior, no API behavior, no UI behavior, no storage writes, no schema migration, no LLM calls, no scoring change, no application execution, and no application submission, rollback has no production data or behavior impact.

## Verification plan

Contract phrase: verification plan.

- Focused tests: `tests/test_critic_evaluator_agent_readiness_checkpoint.py`.
- Verify this document exists.
- Verify README links to this document.
- Verify `docs/orchestrator_readiness.md` links to this document.
- Verify required Critic/Evaluator agent readiness terms are present.
- Verify the future quality rubric includes trace completeness, agent step ordering, safety metadata completeness, validation_json consistency, separation of prefilter relevance, LLM evaluation, and final application scoring, and no application execution or submission judgment.
- Verify the future evaluator output contract includes evaluator_status, evaluator_findings, evaluator_warnings, evaluator_recommendations, requires_human_review, and deterministic_rubric_version.
- Verify Step 196A remains docs/tests only and does not modify runtime code, `src/`, API, frontend JS, storage/schema/migrations, pipeline, scheduler, workflow runner, approvals behavior, application execution, application submission, LLM calls, model/provider client calls, or scoring.
