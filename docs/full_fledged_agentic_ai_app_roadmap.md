# ApplyLens AI Full-Fledged Agentic AI App Roadmap

## Target Product

ApplyLens AI will become a production-style agentic AI platform for job discovery, job intelligence extraction, resume-job matching, evidence-backed tailoring, critic validation, human-in-the-loop approval, evaluation, RAG observability, and LLMOps.

The target is not a chatbot. The target is not fake agents talking to each other. The target is a traceable AI workflow system where each agent has clear responsibility, structured input/output, validation, observability, traceability, and human approval.

## Current Honest Position

The system now has bounded production orchestration without replacing its
existing owners. Deterministic production responsibilities cover prefiltering,
deduplication, final scoring, job prioritization, tailoring decision, and
conditional operator review. Cache-first LLM responsibilities cover JD
intelligence, semantic job-fit evaluation, and tailoring generation. The critic
remains deterministic.

All authoritative graph routes remain default-off. Tailoring generation is the
representative durable node, with committed replay/restart support. Unified
production telemetry is also default-off and currently covers representative
authoritative paired prefilter/dedup graph, final-scoring, tailoring, and
durable execution routes—not every agent. Prefilter/dedup telemetry requires
both its graph gate and the telemetry gate; the direct route remains
uninstrumented. Its events are sanitized and non-authoritative. Discovery, JD
intelligence, semantic evaluation, critic, and strategy are not newly covered.
Tailoring can pause for durable human review, and one authenticated action can
record `continue_read_only`, `needs_revision`, or `cancel`. Human-reviewed state
does not authorize application submission, ATS activity, source-resume
replacement, or any automatic application.

Evidence-backed resume matching still includes deterministic dimensions and
always-on local semantic alignment at weight `0.05`. The default-off LLM
adjudicator remains read-only and cannot override the winner, final score,
ranking, queue, or action.

## Product Principle

Do not rewrite the existing pipeline.

Use this pattern:

Existing pipeline stage -> agent wrapper -> structured output -> validation -> trace log -> next stage

Avoid this pattern:

Agent A chats with Agent B -> Agent C guesses what happened -> no structured state -> no reproducible evaluation

## Safety Principle

Keep these separate:

1. Prefilter relevance
2. LLM evaluation
3. Final application scoring

No LLM-backed agent should directly overwrite final scoring, queue state, approval state, application execution, or submission.

## Phase 1: Roadmap Freeze and Current-State Audit

Deliverables:

- full roadmap document
- current-state audit of existing agent modules, trace modules, storage modules, API routes, UI surfaces, and tests
- gap list between current system and target full-fledged app
- no runtime behavior change
- no storage change
- no API change
- no pipeline change

## Phase 2: Persistent Agent State and Trace Foundation

Deliverables:

- canonical JobApplicationContext
- durable agent_runs
- durable agent_steps
- trace writer helpers
- read-only trace reader helpers
- tests for user isolation and no cross-user trace leakage

Safety boundaries:

- no application execution
- no application submission
- no approval mutation
- no scoring change
- no ranking change
- no scraper behavior change
- no scheduler behavior change
- no automatic LLM calls

## Phase 3: Wrap Existing Pipeline Stages as Trace-Recording Agents

Agents:

1. Discovery Agent
2. Relevance Prefilter Agent
3. Deduplication Agent
4. JD Intelligence Agent
5. Resume Match Agent
6. Tailoring Suggestion Agent
7. Critic / Guardrail Agent
8. Strategy Agent

Initial goal is trace recording without behavior change.

## Phase 4: Full Agent Trace UI

Views:

- run-level trace
- job-level trace
- scan-level trace

Each step should show status, reason codes, counts, latency, model metadata, validation status, compact summary, and expandable JSON/evidence.

## Phase 5: LLM-Backed JD Intelligence Agent

First real LLM-backed agent.

Outputs:

- required skills
- preferred skills
- required tools
- preferred tools
- workflows
- methods
- business contexts
- stakeholder contexts
- ownership signals
- seniority signals
- risk flags

Requirements:

- structured JSON output
- schema validation
- prompt versioning
- model versioning
- retry on invalid JSON
- deterministic fallback
- trace logging
- no final scoring mutation

## Phase 6: Evidence-Backed Resume Match Agent

Current status: deterministic scoring plus local semantic alignment is live, and optional LLM adjudicator readback is live behind a default-off gate. The adjudicator does not calculate `final_score`, choose the winner, or mutate ranking, queue, or action. Any future LLM decision authority remains intentionally unimplemented.

Outputs:

- selected resume
- ranked resume variants
- match dimensions
- missing evidence
- strong evidence
- weak evidence
- confidence
- rationale

This agent does not rewrite resumes.

## Phase 7: LLM-Backed Tailoring Suggestion Agent

Outputs:

- patch-ready suggestions
- guidance-only suggestions
- rationale
- evidence references
- projected score impact

Safety:

- no invented tools
- no invented metrics
- no invented domains
- no inflated ownership
- no unsupported claims
- no direct resume overwrite
- human approval required

## Phase 8: Critic / Guardrail Agent

Checks:

1. Resume support
2. Tool/domain safety
3. Scope exaggeration
4. ATS safety
5. Human readability
6. Score impact
7. Patch safety

Output decision:

approve, reject, or downgrade_to_guidance.

## Phase 9: Evaluation Benchmark

Dataset:

- 20 to 30 sanitized job descriptions
- 5 to 10 resume variants
- expected skill extraction
- expected best resume
- expected missing evidence
- expected apply/tailor/skip decision
- expected unsafe suggestions to reject

Metrics:

- JD extraction precision/recall
- resume selection accuracy
- suggestion validity
- unsupported claim rate
- critic rejection accuracy
- RAG top-k hit rate
- latency
- cost
- fallback rate

## Phase 10: LLMOps and AI Observability

Track per agent call:

- agent name
- agent version
- prompt version
- model provider
- model name
- input tokens
- output tokens
- estimated cost
- latency
- retry count
- fallback used
- schema validation status
- error type

## Phase 11: Human Feedback Loop

Events:

- suggestion accepted
- suggestion rejected
- suggestion edited
- job applied
- job skipped
- job saved
- resume manually selected
- scan rerun

Uses:

- ranking calibration
- suggestion style tuning
- critic evaluation
- resume variant selection
- apply/tailor/skip calibration
- benchmark dataset creation

## Phase 12: RAG Evaluation Dashboard

Show per scan/job:

- query text
- retrieved chunks
- retrieval scores
- evidence used in final decision
- missing evidence warnings
- latency

Metrics:

- top-k hit rate
- average retrieval score
- retrieval latency
- required skill coverage
- unsupported claims prevented by evidence checks

## Phase 13: Optional Graph Orchestration — Implemented, Default Off

Separate authoritative `StateGraph` routes now wrap proven owners for bounded
deterministic and cache-first LLM responsibilities. Direct and graph routes are
mutually exclusive at each caller boundary, and direct owners remain the
business authority.

Production durability, representative unified telemetry, and the durable
human-review checkpoint/action are implemented behind additional default-off
gates. The review continuation is read-only; it is not general human approval
and never authorizes application or ATS actions.

## Phase 14: Demo Mode and Portfolio Packaging

Demo dataset:

- sample resumes
- sample job descriptions
- sample pipeline run
- sample scan
- sample agent trace
- sample benchmark result
- no private personal data

Demo flow:

1. dashboard and pipeline run
2. run-level trace
3. job-level trace
4. JD signals
5. resume match
6. tailoring suggestion
7. critic rejection
8. final recommendation
9. evaluation and LLMOps metrics

## What Not To Build

Do not build these early:

- generic chatbot over the app
- fake multi-agent conversation logs
- autonomous auto-apply bot
- new scraper sources before evaluation exists
- LangGraph rewrite before contracts are stable
- large UI redesign before trace/evaluation exists
- hidden LLM calls without trace and cost metadata
- LLM scoring that directly mutates application decisions

## Final Target Story

ApplyLens AI is an agentic AI workflow platform for job intelligence and resume optimization. It combines production pipeline engineering, deterministic safety gates, structured agent contracts, persisted traces, RAG-backed evidence, LLM-based extraction and suggestion generation, critic validation, human approval, benchmark evaluation, feedback learning, and LLMOps observability.
