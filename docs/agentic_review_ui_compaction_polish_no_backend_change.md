# Agentic Review UI compaction polish

Step 206A implements Agentic Review UI compaction polish as a UI-only presentation update for portfolio demo readability.

This step makes no backend change, no API change, no storage change, no pipeline change, and no scheduler change.

## Scope

Agent Trace remains read-only Agent Trace and GET only. Debug details collapsed by default keeps technical booleans available without exposing them as primary page content.

Optional diagnostics not recorded collapsed by default keeps missing optional diagnostic cards available while showing the compact helper copy first.

Markdown summary collapsed by default keeps the generated Markdown text available without making overview and diagnostic sections visually heavy.

Floating chat safe spacing is increased with CSS so the floating chat control does not cover lower-right Agentic Review cards.

## Non-goals

This step adds no application execution, no application submission, no approval mutation, no scoring change, no ranking change, no live LLM call, and no model provider call.

It does not add routes, storage writes, migrations, scheduler work, workflow runner behavior, application execution behavior, application submission behavior, ranking behavior, scoring behavior, evaluator behavior, approval mutation behavior, or hidden provider calls.

## Verification Plan

This section is the verification plan.

- Confirm `src/app/api.py` is unchanged.
- Confirm protected storage, pipeline, scheduler, workflow runner, ranking, scoring, and application execution files are unchanged.
- Confirm no frontend auto-call is added for critic-evaluator-readonly.
- Confirm Agent Trace remains GET only and read-only.
- Confirm Debug details collapsed by default.
- Confirm Optional diagnostics not recorded collapsed by default.
- Confirm Markdown summary collapsed by default.
- Confirm floating chat safe spacing exists in CSS.

## Rollback Plan

This section is the rollback plan.

Revert only the Step 206A UI, CSS, test, and documentation files:

- `src/app/static/agentic_review.js`
- `src/app/static/app_redesign.css`
- `tests/test_agentic_review_ui_compaction_polish_no_backend_change.py`
- `docs/agentic_review_ui_compaction_polish_no_backend_change.md`
- the link in `docs/orchestrator_readiness.md`

No backend, API, storage, pipeline, scheduler, application execution, application submission, approval mutation, scoring, ranking, live LLM, or model provider state needs rollback because this step does not change those surfaces.
