# Core-Agent Automation and Mutation Capability Inventory

This is the current Phase 21 release-candidate inventory. It records the eight
intended specialized agents, their actual production reachability, and the
remaining safety boundaries. Graph wrappers, repositories, telemetry adapters,
durable adapters, test harnesses, evidence artifacts, and compatibility shims
are infrastructure or contracts; they are not additional agents.

## Canonical eight-agent release inventory

1. **Discovery Agent**
   - Responsibility: discover configured companies and ATS job boards.
   - Execution: deterministic.
   - Production owner: `src/pipeline/discovery_stage.py` and the existing
     scraper owners.
   - Production caller: the collection pipeline started by `main.py`.
   - Graph participation: none; the direct production stage remains
     authoritative.
   - Default gate: normal collection configuration; no high-risk graph or LLM
     capability is enabled by this stage.
   - Cache behavior: existing scraper/source caches only.
   - Durability: pipeline-run persistence, not the production graph checkpoint
     contract.
   - Telemetry: existing pipeline-stage status/logging; not unified
     production-node telemetry.
   - Human-review relationship: produces candidate jobs for later review.
   - Authority: no resume mutation, application authority, or ATS submission
     authority.

2. **Relevance Prefilter Agent**
   - Responsibility: deterministic title, location, freshness, and relevance
     gating.
   - Execution: deterministic.
   - Production owner: `src/pipeline/job_filter.py`.
   - Production caller: `src/pipeline/collector.py`.
   - Graph participation: the same owner can run through the default-off
     `APPLYLENS_AUTHORITATIVE_PREFILTER_DEDUPE_LANGGRAPH_ENABLED` route.
   - Default gate:
     `APPLYLENS_AUTHORITATIVE_PREFILTER_DEDUPE_LANGGRAPH_ENABLED` is off.
   - Cache behavior: no LLM cache.
   - Durability: no production durable-node integration.
   - Telemetry: the default-off paired graph emits one sanitized unified
     production event only when both the graph and telemetry gates are on;
     the direct route is not instrumented.
   - Human-review relationship: reduces the candidate set before manual
     planning.
   - Authority: no resume mutation, application authority, or ATS authority.

3. **Deduplication Agent**
   - Responsibility: collapse duplicate job rows without changing the
     authoritative filtering rules.
   - Execution: deterministic.
   - Production owner: `src/pipeline/dedupe.py`.
   - Production caller: `src/pipeline/collector.py`.
   - Graph participation: paired with relevance prefilter in the same
     default-off authoritative two-node `StateGraph`.
   - Default gate:
     `APPLYLENS_AUTHORITATIVE_PREFILTER_DEDUPE_LANGGRAPH_ENABLED` is off.
   - Cache behavior: no LLM cache.
   - Durability: no production durable-node integration.
   - Telemetry: the default-off paired graph emits one sanitized unified
     production event after the prefilter event only when both gates are on;
     the direct route is not instrumented.
   - Human-review relationship: prevents duplicate review work.
   - Authority: no resume mutation, application authority, or ATS authority.

4. **JD Intelligence Agent**
   - Responsibility: extract structured job requirements and skills.
   - Execution: cache-first LLM with the existing deterministic/fail-closed
     behavior.
   - Production owner: `src/ai/skill_llm_enricher.py`.
   - Production caller: `src/pipeline/collector.py`.
   - Graph participation: one default-off authoritative node under
     `APPLYLENS_AUTHORITATIVE_JD_INTELLIGENCE_LANGGRAPH_ENABLED`.
   - Default gate: the authoritative graph and live LLM modes are off.
   - Cache behavior: the production owner retains cache lookup, write, failure,
     and cache-only semantics.
   - Durability: no production durable-node integration.
   - Telemetry: existing cache/provider metrics; not one of the two integrated
     unified production-telemetry representatives.
   - Human-review relationship: supplies bounded evidence, never a final
     application decision.
   - Authority: no scoring mutation, resume mutation, application authority, or
     ATS authority.

5. **Resume Match Agent**
   - Responsibility: evaluate semantic job fit, compute deterministic final
     application scores, and select a resume using the existing owners.
   - Execution: cache-first LLM semantic evaluation plus deterministic final
     scoring; optional adjudicator output remains default-off and read-only.
   - Production owners: `src/ai/job_fit_evaluator.py`,
     `src/pipeline/application_scorer.py`, and the existing resume selector.
   - Production caller: `src/pipeline/collector.py` and application planning.
   - Graph participation: separate default-off semantic-evaluation and
     final-scoring authoritative nodes.
   - Default gate: both authoritative graph routes and optional LLM
     adjudication are off.
   - Cache behavior: semantic-evaluation cache remains owner-managed; final
     scoring performs no provider or LLM cache operation.
   - Durability: no production durable-node integration.
   - Telemetry: final scoring is the deterministic representative for unified
     production telemetry; semantic evaluation retains its existing metrics.
   - Human-review relationship: emits ranked evidence and resume identity for
     planning review.
   - Authority: no resume-text mutation, application authority, or ATS
     authority.

6. **Tailoring Suggestion Agent**
   - Responsibility: generate bounded, evidence-backed tailoring suggestions
     without overwriting the source resume.
   - Execution: cache-first LLM.
   - Production owner: `src/tailoring/llm.py` through
     `generate_tailoring_suggestions.py`.
   - Production caller: the explicit tailoring-generation workflow.
   - Graph participation: one default-off authoritative tailoring-generation
     node.
   - Default gate: authoritative tailoring generation, durability, telemetry,
     and human checkpoint/action are all off.
   - Cache behavior: existing tailoring cache, retry, provider, and fallback
     owners remain unchanged.
   - Durability: representative production durable node; committed replay and
     restart are supported and avoid duplicate owner/provider/cache work.
   - Telemetry: the cache-first LLM and durable first-execution/replay
     representative for unified production telemetry.
   - Human-review relationship: Phase 20 creates a durable pause; Phase 21
     accepts only an authenticated `continue_read_only`, `needs_revision`, or
     `cancel` action. Continuation is read-only and human-controlled.
   - Authority: no source-resume replacement, application authority, or ATS
     authority.

7. **Critic / Guardrail Agent**
   - Responsibility: deterministically identify unsupported claims,
     contradictions, and review risk.
   - Execution: deterministic; controlled LLM guardrail experiments remain
     evidence-only/default-off compatibility components.
   - Production owner: `src/agents/critic_agent.py`.
   - Production caller: current callers are manual diagnostic/service,
     benchmark, and historical evidence-chain paths; it is not an
     authoritative production graph node.
   - Graph participation: evidence-chain compatibility only, not the current
     production graph route.
   - Default gate: controlled LLM/evidence-chain experiments are off.
   - Cache behavior: no production LLM cache in the deterministic critic.
   - Durability: no production durable-node integration.
   - Telemetry: legacy agent trace/diagnostic coverage only.
   - Human-review relationship: provides advisory risk evidence.
   - Authority: no scoring, ranking, resume, application, or ATS mutation
     authority.

8. **Strategy Agent**
   - Responsibility: synthesize advisory job priority, tailoring decision, and
     conditional operator-review lane.
   - Execution: deterministic.
   - Production owners: `src/agents/job_prioritization_agent.py`,
     `src/agents/tailoring_decision_agent.py`, and
     `src/agents/operator_review_agent.py`.
   - Production caller: `application_execution_queue.py`.
   - Graph participation: three separate default-off authoritative nodes;
     operator review preserves its conditional execution boundary.
   - Default gate: priority, tailoring-decision, and operator-review graph
     routes are off.
   - Cache behavior: no LLM cache.
   - Durability: no production durable-node integration.
   - Telemetry: existing agent traces and execution metadata; not integrated
     into the unified production-telemetry representative set.
   - Human-review relationship: recommends a review lane; it does not capture
     the authenticated Phase 21 decision and does not approve an application.
   - Authority: no queue mutation beyond existing authoritative artifact
     creation, no resume mutation, no application authority, and no ATS
     authority.

## Infrastructure and compatibility classification

- Implemented in production workflow: discovery, relevance prefilter,
  deduplication, JD intelligence, resume match, tailoring suggestion, and the
  strategy responsibilities.
- Default-off production capabilities: every authoritative LangGraph route,
  cache-first live LLM mode, production durability, unified production
  telemetry, and durable human checkpoint/action.
- Evidence-only/test-only component: controlled provider canaries, benchmarks,
  and controlled critic experiments.
- Historical compatibility contract: the evidence-chain graph, shadow
  contracts, and the Phase 22 inventory checkpoint remain retained but are not
  counted as production agents.

Unified telemetry coverage is intentionally representative, not all-agent:
authoritative paired prefilter/dedup graph execution, deterministic final
scoring, cache-first tailoring generation, and durable tailoring first
execution/replay use the shared adapter. Prefilter/dedup events are sanitized,
non-authoritative, and require both default-off gates; the direct route is not
instrumented. Discovery, JD intelligence, semantic evaluation, critic, and
strategy are not newly covered. No claim of complete all-node telemetry is
made, and no autonomous application, ATS, or resume-mutation authority was
added.

## Phase 22 historical inventory

The remainder of this document preserves the older Phase 22 three-core
inventory vocabulary for compatibility guards. Its future-tense
recommendations are historical and are superseded by the Phase 21
release-candidate inventory above.

## Existing deterministic foundations

The current application already provides:

- deterministic job discovery/filtering through the collection pipeline and
  normalized job corpus;
- deterministic role/title/location/freshness filtering in
  `src/pipeline/job_filter.py`;
- deterministic resume/job prefiltering in `src/matching/prefilter.py`;
- deterministic JD/resume evidence extraction through the existing job and
  resume evidence builders consumed by matching and planning;
- deterministic final resume-job scoring in `src/matching/scorer.py`;
- deterministic best resume variant selection in
  `batch_select_best_resume_variant.py`;
- deterministic shortlist/action classification in
  `application_shortlist_from_batch_selector.py`;
- deterministic review evidence generation through selector, shortlist, and
  planning outputs produced by `run_application_planning.py`;
- deterministic tailoring packet generation through planning packets and
  `generate_tailoring_suggestions.py`;
- optional LLM fallback/adjudication in
  `batch_select_best_resume_variant.py` where explicitly configured; and
- optional LLM tailoring in `generate_tailoring_suggestions.py` and
  `src/tailoring/llm.py` where explicitly requested.

These foundations are implemented by existing files, not by a newly invented
agent pipeline:

- `src/pipeline/job_filter.py`
- `src/matching/prefilter.py`
- `src/matching/scorer.py`
- `batch_select_best_resume_variant.py`
- `application_shortlist_from_batch_selector.py`
- `run_application_planning.py`
- `generate_tailoring_suggestions.py`
- `src/tailoring/llm.py`

## Core-agent sequence and ownership

The staged core-agent sequence is:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

`relevance_prefilter` should own early relevance gating by wrapping and
materializing the existing deterministic prefilter evidence.
`jd_intelligence` should own JD signal extraction and evidence interpretation,
without becoming the final scoring or mutation authority.
`final_application_scoring` should own final advisory score synthesis by
materializing existing deterministic score evidence for manual review.

Prefilter relevance, JD intelligence, final application scoring, and
tailoring suggestions must stay separate. Final application scoring may
advise manual review, but must not directly mutate queue, ranking, or
application state. Relevance prefilter may reduce review load, but must not
submit or execute applications. JD intelligence may produce evidence, but
must not become final scoring or mutation authority.

The tailoring agent should remain separate from final scoring. It should
identify tailoring opportunities automatically as evidence. Any later AI
tailoring generation must be user-triggered through a `Generate AI Tailoring`
button. Generated tailoring suggestions must remain preview/manual-review
only unless the user accepts edits. Tailoring suggestions may guide resume
edits, but must not silently rewrite, overwrite, apply, or submit.

## Current automation status

- automatic job analysis is partly present through deterministic planning and
  evidence artifacts;
- automatic relevance prefiltering is already present deterministically;
- automatic scoring is already present deterministically;
- automatic review evidence generation is already present through planning
  outputs;
- automatic tailoring opportunity detection is partly present through
  shortlist actions, missing requirements, JD/resume packets, and tailoring
  packet generation;
- agent evidence generation and readback exist as staged/default-off wrappers;
  and
- read-only/advisory/manual-review evidence is the current safe automation
  boundary.

Agents should first wrap and materialize existing deterministic outputs. They
may interact through explicit read-only payloads before any durable mutation
is considered. Live-provider agent automation should be introduced only after
read-only materialization, API readback, UI readback, provider-readiness
checks, and safety gates.

## Current mutation status

This checkpoint authorizes:

- no scoring mutation
- no ranking mutation
- no queue mutation
- no resume mutation
- no application mutation
- no approval mutation
- no decision mutation
- no audit mutation
- no provider-call mutation
- no database write mutation
- no execution mutation
- no submission mutation

## Permanent no-autonomous-application boundary

The permanent product rule is:

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control over final job application submission

There is no auto-apply feature, auto-submit feature, autonomous application
execution, or automatic job application submission. Final submission remains
under manual user control.

## Recommended next technical direction

Phase 22C should implement a default-off, read-only core-agent evidence
materialization preview. The preview should assemble existing deterministic
outputs into one manual-review evidence packet containing the relevance
prefilter result, JD signals, final advisory score, review rationale, missing
requirements, and tailoring opportunities.

Any future durable scoring, ranking, or queue mutation requires a separate
mutation-boundary phase, explicit tests, and approval gates. Any future
provider-backed tailoring generation must be user-triggered by
`Generate AI Tailoring`, default-off/gated, preview-only, and controlled by
manual review.

## Release lineage

- `phase22a-manual-review-ux-hardening-v1`
- `phase21-manual-review-workflow-release-v1`
- `phase21e-manual-review-workflow-release-checkpoint-v1`
- `phase21d-manual-review-readiness-ui-readback-v1`
- `phase20-provider-readiness-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`
- `phase19-readonly-approval-workflow-release-v1`
- `phase18-safety-wrap-release-v1`
- `phase17-three-core-shadow-readiness-release-v1`
