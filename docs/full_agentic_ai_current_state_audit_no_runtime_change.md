# Full Agentic AI Current-State Audit

## Purpose

This audit maps the current repository against the full-fledged ApplyLens AI agentic roadmap.

This checkpoint is intentionally docs/tests only.

No runtime behavior is changed.

No API behavior is changed.

No storage schema is changed.

No scheduler behavior is changed.

No pipeline behavior is changed.

## Current branch goal

Branch:

`full-agentic-ai-current-state-audit-no-runtime-change`

Goal:

Identify what already exists before implementing the next agentic AI roadmap phase.

## Core finding

The repository already contains substantial agentic infrastructure.

The next phase should not blindly create new modules or rewrite the pipeline. The correct next move is to inspect the existing agent state, trace, feedback, approval, workflow, API, service, and UI surfaces, then extend them incrementally.

## Existing surfaces found

| Area | Existing files |
|---|---|
| Roadmap | `docs/full_fledged_agentic_ai_app_roadmap.md` |
| Agent state | `src/agents/agent_state.py` (current state owner) |
| Agent trace helpers | `src/agents/trace.py` |
| Stage-style agents | `src/agents/relevance_prefilter.py`, `src/agents/deduplication.py`, `src/agents/jd_intelligence.py`, `src/agents/resume_match_agent.py`, `src/agents/tailoring_decision_agent.py`, `src/agents/final_application_scoring.py` |
| Critic/evaluator | `src/agents/critic_agent.py`, `src/agents/critic_evaluator.py` |
| Workflow orchestration helpers | `src/agents/workflow_registry.py`, `src/agents/workflow_runner.py`, `src/agents/workflow_verifier.py` |
| Agent state storage | `src/storage/agent_state/schema.sql`, `src/storage/agent_state/store.py`, `src/storage/agent_state/migration_runner.py` |
| Agent trace storage | `src/storage/agent_trace/schema.sql`, `src/storage/agent_trace/store.py` |
| Agent feedback storage | `src/storage/agent_feedback/schema.sql`, `src/storage/agent_feedback/store.py` |
| Agentic approvals storage | `src/storage/agentic_approvals/schema.sql`, `src/storage/agentic_approvals/store.py` |
| User pipeline storage | `src/storage/user_pipeline/schema.sql`, `src/storage/user_pipeline/store.py` |
| API/service surfaces | `src/app/api.py`, `src/app/services.py` |
| UI surfaces | `src/app/profile_ui.py`, `src/app/static/agentic_review.js`, `src/app/static/app_redesign.css` |

## Path existence check

| Path | Status |
|---|---|
| `docs/full_fledged_agentic_ai_app_roadmap.md` | present |
| `src/agents/agent_state.py` | present |
| `src/agents/trace.py` | present |
| `src/agents/relevance_prefilter.py` | present |
| `src/agents/deduplication.py` | present |
| `src/agents/jd_intelligence.py` | present |
| `src/agents/resume_match_agent.py` | present |
| `src/agents/tailoring_decision_agent.py` | present |
| `src/agents/final_application_scoring.py` | present |
| `src/agents/critic_agent.py` | present |
| `src/agents/critic_evaluator.py` | present |
| `src/agents/workflow_registry.py` | present |
| `src/agents/workflow_runner.py` | present |
| `src/agents/workflow_verifier.py` | present |
| `src/storage/agent_state/schema.sql` | present |
| `src/storage/agent_state/store.py` | present |
| `src/storage/agent_state/migration_runner.py` | present |
| `src/storage/agent_trace/schema.sql` | present |
| `src/storage/agent_trace/store.py` | present |
| `src/storage/agent_feedback/schema.sql` | present |
| `src/storage/agent_feedback/store.py` | present |
| `src/storage/agentic_approvals/schema.sql` | present |
| `src/storage/agentic_approvals/store.py` | present |
| `src/storage/user_pipeline/schema.sql` | present |
| `src/storage/user_pipeline/store.py` | present |
| `src/app/api.py` | present |
| `src/app/services.py` | present |
| `src/app/profile_ui.py` | present |
| `src/app/static/agentic_review.js` | present |
| `src/app/static/app_redesign.css` | present |

## Roadmap fit

### Phase 2: Persistent Agent State and Trace Foundation

Current status: partially present.

The repository already has agent state and agent trace storage modules. Before adding or changing schema, the next implementation phase must inspect the existing SQL schemas and store contracts.

Do not create a second parallel trace schema unless the current schema is proven insufficient.

### Phase 3: Wrap Existing Pipeline Stages as Trace-Recording Agents

Current status: partially present.

The repository already has named modules for relevance prefilter, deduplication, JD intelligence, resume match, tailoring decision, final application scoring, critic, and workflow helpers.

The next step should verify which of these modules already record traces, which are deterministic only, and which are connected to the production pipeline.

### Phase 4: Full Agent Trace UI

Current status: partially present.

The repository already has an Agentic Review page, Agent Trace UI assets, profile UI route surfaces, app service payload builders, and API trace-related code.

The next step should map run-level trace, job-level trace, and scan-level trace separately.

### Phase 5: LLM-Backed JD Intelligence Agent

Current status: not ready for implementation yet.

There is an existing JD intelligence module. Before adding LLM behavior, inspect its current contract, output format, tests, and usage sites.

The first LLM-backed stage should remain isolated, structured, schema-validated, traced, and fallback-safe.

### Phase 6: Evidence-Backed Resume Match Agent

Current status: partially present.

There is an existing resume match agent module. The next step should audit current score dimensions, evidence handling, and separation from final scoring.

### Phase 7: Tailoring Suggestion Agent

Current status: partially present.

There is an existing tailoring decision agent module and UI/workspace integration. The next step should map patch-ready suggestions, guidance-only suggestions, critic labels, and human approval flow.

### Phase 8: Critic / Guardrail Agent

Current status: partially present.

Critic agent and readonly critic evaluator surfaces already exist. The next step should audit whether critic output remains advisory and whether it avoids score, approval, execution, or submission mutation.

### Phase 9: Evaluation Benchmark

Current status: gap.

A benchmark harness for JD extraction, resume selection, tailoring suggestion quality, critic rejection accuracy, RAG quality, latency, and cost still needs to be designed.

### Phase 10: LLMOps and AI Observability

Current status: partially present.

There is an LLMOps module. The next step should inspect what metadata is currently recorded and whether it includes model name, prompt version, token usage, cost, latency, retry count, fallback status, schema validation, and error type.

### Phase 11: Human Feedback Loop

Current status: partially present.

Agent feedback storage exists. The next step should map feedback events to agent steps, scans, jobs, and user actions.

### Phase 12: RAG Evaluation Dashboard

Current status: gap or partial foundation.

RAG storage exists elsewhere in the project, but this audit does not yet confirm a RAG evaluation dashboard contract. The next step should inspect RAG stores, exports, retrieval traces, and dashboard surfaces separately.

### Phase 13: Optional Graph Orchestration

Current status: not next.

Graph orchestration should not be added until trace persistence, stage contracts, benchmark evaluation, and human approval interrupts are stable.

## Immediate gaps before implementation

1. Confirm exact existing agent state schema.
2. Confirm exact existing agent trace schema.
3. Confirm exact existing trace write/read helper contracts.
4. Confirm whether agent state and agent trace are already connected to pipeline run IDs and owner user IDs.
5. Confirm whether job-level trace exists or only run-level trace exists.
6. Confirm whether scan-level trace exists.
7. Confirm whether critic/evaluator is read-only across all paths.
8. Confirm whether existing LLMOps module records cost, latency, token usage, prompt version, and fallback.
9. Confirm feedback event schema and whether it links to agent steps.
10. Confirm RAG evidence trace and retrieval-quality surfaces.
11. Confirm tests that protect no execution, no submission, no scoring mutation, and no approval mutation.

## Recommended next implementation checkpoint

Next checkpoint should be:

`full-agentic-ai-schema-contract-audit-no-runtime-change`

Purpose:

Inspect and document the existing schemas and store contracts for:

- `src/storage/agent_state/schema.sql`
- `src/storage/agent_state/store.py`
- `src/storage/agent_trace/schema.sql`
- `src/storage/agent_trace/store.py`
- `src/storage/agent_feedback/schema.sql`
- `src/storage/agent_feedback/store.py`
- `src/storage/agentic_approvals/schema.sql`
- `src/storage/agentic_approvals/store.py`

Expected output:

- schema contract audit doc
- store function inventory
- current field map
- gap map
- no runtime behavior change
- no schema migration
- no API change
- no pipeline change

## Decision

Do not add new runtime behavior yet.

The repository already has enough agentic infrastructure that the next safe move is contract auditing, not implementation.
