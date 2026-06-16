# Phase 5L Shadow Sidecar Pipeline Integration Point Audit

This checkpoint is documentation/test only.

No runtime behavior change is introduced.

No production pipeline behavior is changed.

No scheduler behavior is changed.

No storage schema is changed.

No migration is added.

No pipeline wiring was added.

Live agents connected to production pipeline remain zero.

Live agents allowed to automate mutations remain zero.

## Exact Inspected Files

Repository structure and pipeline-adjacent files inspected for this audit:

- `src/pipeline/collector.py`
- `src/pipeline/runtime_status.py`
- `src/pipeline/job_filter.py`
- `src/pipeline/dedupe.py`
- `src/pipeline/job_ranker.py`
- `src/pipeline/application_scorer.py`
- `src/pipeline/embedding_prefilter.py`
- `src/intelligence/job_intelligence.py`
- `src/ai/job_fit_evaluator.py`
- `src/utils/pipeline_metrics.py`
- `src/utils/log_sections.py`
- `src/utils/job_cache.py`
- `src/utils/http_retry.py`
- `src/utils/ats_health.py`
- `src/evaluation/metrics.py`
- `src/storage/metrics_store.py`
- `src/agents/relevance_prefilter.py`
- `src/agents/deduplication.py`
- `src/agents/final_application_scoring.py`
- `src/agents/trace.py`
- `src/storage/agent_trace/store.py`
- `src/agents/shadow_sidecar.py`
- `docs/phase5_shadow_agentic_pipeline_sidecar_readiness_audit.md`
- `docs/phase5_shadow_sidecar_config_contract_no_runtime_change.md`
- `docs/phase5_shadow_sidecar_trace_schema_contract_no_runtime_change.md`
- `docs/phase5_shadow_sidecar_adapter_interface_contract_no_runtime_change.md`

Protected runtime files were inspected only. They were not modified.

## Existing Pipeline Stages Discovered

`src/pipeline/runtime_status.py` defines this `STAGE_ORDER`:

1. `startup`
2. `scraping`
3. `filtering`
4. `dedupe`
5. `ranking`
6. `cache_filter`
7. `details`
8. `intelligence`
9. `ai_evaluation_filter`
10. `embedding_prefilter`
11. `ai_evaluation`
12. `resume_matching`
13. `application_priority`
14. `rag_export`
15. `planning`
16. `finalization`

`src/pipeline/collector.py` is the main observed orchestration file. It calls the stage status helpers from `src/pipeline/runtime_status.py`, uses `section(...)` from `src/utils/log_sections.py`, and uses `log_stage_metrics(...)` from `src/utils/pipeline_metrics.py`.

The collector sequence observed in code is:

- Scraping via ATS scraper functions.
- Filtering via `src/pipeline/job_filter.py`.
- Deduplication via `src/pipeline/dedupe.py`.
- Ranking via `src/pipeline/job_ranker.py`.
- Cache filtering via `src/utils/job_cache.py`.
- Job details enrichment via `src/pipeline/job_details.py`.
- Job intelligence via `src/intelligence/job_intelligence.py`.
- AI evaluation selection via `filter_jobs_for_ai_evaluation(...)`.
- Embedding prefilter via `src/pipeline/embedding_prefilter.py`.
- AI evaluation via `src/ai/job_fit_evaluator.py`.
- Resume matching via `src.ai.resume_matcher.match_resumes(...)`.
- Final application priority scoring via `src/pipeline/application_scorer.py`.
- RAG export and post-run persistence after scoring.

## Existing Adjacent Files By Concern

Prefilter relevance:

- Runtime-adjacent filtering is in `src/pipeline/job_filter.py`.
- Embedding prefiltering is in `src/pipeline/embedding_prefilter.py`.
- Read-only relevance trace wrapper is in `src/agents/relevance_prefilter.py`.

LLM evaluation:

- Job intelligence skill extraction is in `src/intelligence/job_intelligence.py`.
- Job fit evaluation is in `src/ai/job_fit_evaluator.py`.
- LLM operations metadata helpers are in `src/agents/llmops.py`.

Deduplication:

- Runtime deduplication is in `src/pipeline/dedupe.py`.
- Read-only deduplication trace wrapper is in `src/agents/deduplication.py`.

Final application scoring:

- Runtime final application priority scoring is in `src/pipeline/application_scorer.py`.
- Ranking before cache filtering is in `src/pipeline/job_ranker.py`.
- Read-only final application scoring trace wrapper is in `src/agents/final_application_scoring.py`.

Metrics and stage logging:

- Stage order and status writes are in `src/pipeline/runtime_status.py`.
- Stage metrics logging is in `src/utils/pipeline_metrics.py`.
- Section logging is in `src/utils/log_sections.py`.
- Historical metrics storage is in `src/storage/metrics_store.py`.
- Small evaluation metric helpers are in `src/evaluation/metrics.py`.

Trace/evidence helpers:

- Stage trace bundle, readiness, health, and evidence helpers are in `src/agents/trace.py`.
- Agent trace storage payload helpers are in `src/storage/agent_trace/store.py`.
- Isolated shadow sidecar helpers are in `src/agents/shadow_sidecar.py`.

Retry, rate-limit, cache, dedup, and ATS health checks:

- HTTP retry helpers are in `src/utils/http_retry.py`.
- Evaluation rate-limit/concurrency behavior is in `src/ai/job_fit_evaluator.py`.
- Seen-job cache behavior is in `src/utils/job_cache.py`.
- Runtime deduplication is in `src/pipeline/dedupe.py`.
- ATS health and regression checks are in `src/utils/ats_health.py`.

## Recommended First Hook Point

The recommended first future hook point is a read-only shadow sidecar after deterministic filtering/evaluation/scoring context is available and before any queue mutation, approval mutation, execution request creation, execution launch request creation, application execution, or submission.

The safest concrete repo point is after `application_priority` completes in `src/pipeline/collector.py`, immediately after:

- `scored_jobs = score_jobs(ai_jobs)`
- `complete_stage("application_priority", counts={"scored_jobs": len(scored_jobs)})`

and before later post-scoring persistence/export/readback work such as source-health trace recording, RAG export, saving seen-job IDs, queue handoff, approval mutation, execution request creation, execution launch request creation, application execution, or submission.

This future placement has access to deterministic filter/rank/cache/detail/intelligence/AI-evaluation/resume-matching/application-priority context while preserving the existing deterministic production decision as authoritative.

## Candidate Future Hook Stage Labels

Phase 5K defined adapter labels:

- `post_filter_evaluation`
- `post_final_scoring`
- `pre_human_review`

Repo-specific mapping:

- `post_filter_evaluation` maps cleanly only as an adapter label after `filtering`, `dedupe`, `ranking`, `ai_evaluation_filter`, or `embedding_prefilter` depending on the future payload shape. The current repo does not have a literal `post_filter_evaluation` runtime stage.
- `post_final_scoring` maps most cleanly to the point immediately after the `application_priority` stage in `src/pipeline/collector.py`.
- `pre_human_review` is an adapter label only. The current collector stage order does not include a literal human-review stage; it should mean after scoring/readiness context is available and before any future queue, approval, execution request, execution launch request, application execution, or submission mutation.

For the first future runtime hook, prefer the `post_final_scoring` adapter label mapped to the existing `application_priority` stage boundary.

## Required Integration Constraints

Any future implementation must preserve all of these constraints:

- Default-off global flag required.
- Default-off per-agent flags required.
- Kill switch required.
- Provider calls are disabled in tests.
- Provider calls must not run in tests.
- Deterministic fallback is required.
- Sidecar failure must not fail deterministic pipeline by default.
- No scoring override.
- No ranking override.
- No scoring/ranking override.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No execution request mutation.
- No execution launch request mutation.
- No application execution.
- No application submission.
- No application execution/submission.
- Stage-level logging must be preserved.
- Existing metrics flow must be preserved.
- Existing retry/rate-limit/cache/dedup/ATS health checks must not be removed.
- Existing `start_stage(...)`, `complete_stage(...)`, `update_counts(...)`, and `log_stage_metrics(...)` behavior must be preserved.
- Existing seen-job cache behavior in `src/utils/job_cache.py` must be preserved.
- Existing ATS health checks in `src/utils/ats_health.py` must be preserved.
- Existing HTTP retry helpers in `src/utils/http_retry.py` must be preserved.
- Existing LLM evaluation cache, rate-limit, and concurrency behavior in `src/ai/job_fit_evaluator.py` must be preserved.

## Proposed Next Implementation Sequence

1. Add default-off pipeline hook module/function, not called.
2. Add tests proving no pipeline wiring.
3. Add one explicit opt-in call site behind feature flag.
4. Add shadow trace storage/readback.
5. Add dashboard/readback.
6. Only later allow human-approved influence.
7. Only much later guarded automation.

## Explicit Non-Goals

- No runtime behavior change.
- No pipeline wiring.
- No provider calls.
- No automated decisions.
- No mutation.
- No scoring mutation.
- No ranking mutation.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No execution request mutation.
- No execution launch request mutation.
- No application execution.
- No application submission.
- No application execution/submission.

## Audit Decision

Phase 5L identifies a repo-specific future integration point only.

No production pipeline hook was added.

No runtime module was changed.

Live production pipeline connected agents remain zero.

Live agents allowed to automate mutations remain zero.
