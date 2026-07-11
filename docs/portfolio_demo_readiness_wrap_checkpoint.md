# Portfolio demo readiness wrap checkpoint

This checkpoint marks the **portfolio demo readiness** point for **ApplyLens AI**, the **job scraper app** with an **agentic AI layer**. This is **docs/tests only** and describes the **completed portfolio scope** without adding runtime behavior.

## Portfolio positioning

ApplyLens AI demonstrates a production-style agentic layer added incrementally on top of an existing job scraper app. The system keeps the existing scraping, filtering, ranking, and application logic unchanged while adding observability, traceability, read-only review surfaces, and a deterministic evaluator.

This is positioned as an engineering portfolio project focused on safe agent architecture, traceability, deterministic guardrails, and explicit human-triggered review actions.

## What is implemented

The completed portfolio scope includes:

- Agent State foundation
- trace recorder
- Relevance Prefilter Agent
- Deduplication Agent
- JD Intelligence Agent
- Final Application Scoring Agent
- read-only Agent Trace API endpoint
- read-only Agent Trace UI panel
- trace UI polish
- Critic/Evaluator runtime skeleton
- explicit read-only Critic/Evaluator API action
- deterministic evaluator
- trace-only evaluation inputs
- deterministic local semantic similarity helper
- always-on `semantic_alignment` with weight `0.05` included in `final_score`
- diagnostic-only active TS/Top Secret clearance readback with no cap or penalty
- optional default-off LLM adjudicator readback that cannot override selection or scoring
- Planning UI display of existing adjudicator readback without a provider call

## Demo flow

1. scrape or load jobs using the existing job scraper app flow.
2. existing filtering/ranking remains unchanged.
3. agent trace can be viewed read-only through the read-only Agent Trace UI panel.
4. Critic/Evaluator can be triggered explicitly through the explicit read-only Critic/Evaluator API action.
5. response shows evaluator findings/warnings/recommendations.
6. no auto-apply or submission occurs.
7. no application execution occurs.
8. no application submission occurs.
9. optional adjudicator commentary remains readback-only and cannot change winner, resolved resume, final score, ranking, queue, or action.

## Safety guarantees

The portfolio demo intentionally preserves safety boundaries:

- no live LLM call
- no model provider call
- no storage writes
- no schema migration
- no approval mutation
- no ranking change
- no scoring change
- no application execution
- no application submission
- no pipeline wiring
- no scheduler
- no background task
- no file export
- no auto-apply
- no ATS submission
- no recruiter messaging
- no source-resume overwrite

The implemented scoring system does include deterministic local `semantic_alignment` at weight `0.05`. The “no scoring change” guarantee above means this documentation/readiness wrap makes no scoring change; it does not describe semantic scoring as zero-weight or diagnostic-only. The optional LLM adjudicator is not part of `final_score` and has no decision authority.

## What is intentionally not implemented

The following production features are intentionally not implemented before portfolio publishing:

- persistent trace activation
- feedback capture storage
- LangGraph runtime orchestration
- autonomous application execution
- autonomous application submission
- evaluator pipeline wiring
- scheduler-based evaluator execution
- model-provider critic calls

These remain future production-platform work, not portfolio blockers.

## How to explain this in interviews

Explain that ApplyLens AI is not just a scraper. It is a job automation platform with a safe agentic observability layer. The important design choice is separation of responsibilities: existing filtering/ranking stays unchanged, agents emit trace metadata, the UI shows trace state read-only, and the Critic/Evaluator only reviews trace inputs through an explicit user action.

For scoring, explain that deterministic evidence dimensions and local token-cosine semantic alignment produce the final score. Optional LLM adjudicator output is a separate, default-off readback that helps a human inspect candidates without changing the selected resume or score.

The strongest engineering point is that the agentic layer was added incrementally without rewriting the pipeline or changing application scoring/submission behavior.

## Local demo checklist

- Start the app locally.
- Run or load a job search result.
- Open the agentic review workspace.
- Show the read-only Agent Trace UI panel.
- Trigger the explicit read-only Critic/Evaluator API action.
- Show evaluator_status, evaluator_findings, evaluator_warnings, evaluator_recommendations, requires_human_review, and deterministic_rubric_version.
- Confirm no auto-apply, no application execution, and no application submission.

## GitHub README checklist

The GitHub README should clearly show:

- what the project does
- architecture summary
- agentic AI layer
- demo flow
- safety guarantees
- what is implemented
- what is intentionally not implemented
- how to run tests
- portfolio positioning

## Resume bullet ideas

- Built ApplyLens AI, a production-style job scraper app with an agentic AI layer, read-only trace UI, deterministic evaluator, and explicit human-triggered review actions.
- Added Agent State foundation, trace recorder, and named agent wrappers for relevance prefiltering, deduplication, JD intelligence, and final application scoring without changing core ranking or application behavior.
- Implemented a read-only Agent Trace API/UI and explicit read-only Critic/Evaluator API action with no live LLM call, no storage writes, no approval mutation, and no application submission.

## Rollback plan

Rollback plan: revert this docs/tests only checkpoint commit. Since this checkpoint has no runtime code, no API change, no UI behavior change, no storage writes, no schema migration, no pipeline wiring, no scheduler, no background task, and no file export, rollback is limited to documentation and test files.

## Verification plan

Verification plan:

- Run the focused portfolio demo readiness tests.
- Run tests/test_agentic_docs.py.
- Run the full test suite.
- Confirm only docs/tests files changed.
- Confirm no src/ files changed.
- Confirm no application execution or application submission paths changed.

## Phase 127 demo freeze checkpoint

The Phase 127 portfolio demo freeze is documentation/readiness only. The finalized 4-5 minute primary demo route is:

1. Run live pipeline with sanitized data.
2. Open Planning and show deterministic score, selected resume, and `AI review notes · advisory`.
3. Trigger Generate Suggestions and show its full-page progress flow.
4. Review the result in Tailoring Workspace and AI Optimize Scan.
5. Point out the diagnostic-only TS clearance warning when present.
6. Open Agentic Review and show evidence-chain traceability.
7. Close with the permanent human-control safety boundary.

Freeze readiness confirms:

- hybrid scoring is ready with always-on local `semantic_alignment` at weight `0.05`;
- AI review notes remain default-off, readback-only, and non-mutating;
- Generate Suggestions and Tailoring Workspace are ready for the sanitized demo path;
- AI Optimize Scan diagnostic readback is ready and does not change scoring;
- Agentic Review evidence-chain and trace displays are ready;
- no auto-apply, ATS submission, recruiter messaging, application status mutation, or source-resume overwrite is introduced;
- the final application action remains manual and human-controlled;
- the full test suite is expected green when the configured `DATABASE_URL` is available.

After this checkpoint, feature work is frozen for the portfolio demo. Future changes should use a separate post-freeze branch.

## Stop condition

Stop condition: stop feature work after this checkpoint.

This is enough for portfolio. Future work can continue later as production-platform hardening, but it is not required before publishing the project.

## Exact verifier terms

- local demo checklist
- resume bullet ideas
- rollback plan
- verification plan
