# ApplyLens AI Portfolio Overview

ApplyLens AI is a safety-first job-application intelligence platform that turns job discovery, resume matching, planning artifacts, advisory agent diagnostics, feedback events, and offline evaluations into one reviewable operator workspace.

## Problem

Serious job searches create a high-volume operations problem: many scraped roles, inconsistent ATS data, multiple resume variants, unclear fit signals, manual application decisions, and hard-to-audit AI suggestions. A useful system needs to help prioritize work without hiding why a job, resume, packet, or suggestion was recommended.

## Solution

ApplyLens AI combines a FastAPI web app, PostgreSQL-backed user/session/run storage, optional Redis admission locks, deterministic application-planning artifacts, local RAG tools, and an Agentic Review page. The agentic layer reads existing pipeline outputs and turns them into advisory summaries, trace records, workflow verification, human feedback read models, and RAG evaluation diagnostics.

## What Makes It Agentic

- A deterministic workflow registry in `src/agents/workflow_registry.py` defines the implemented advisory agents, artifact contracts, feature flags, safety guarantees, and benchmark metrics.
- Advisory agents summarize source health, resume-match credibility, critic checks, job prioritization, tailoring decisions, and operator-review lanes.
- `src/agents/workflow_runner.py` is dry-run only. It simulates the ordered workflow plan and reports skipped steps; it does not execute agents or mutate production state.
- Agent Trace and Agentic Review expose aggregate run/step diagnostics, workflow verification, manifest, execution plan, dry-run result, Human Feedback, and RAG Evaluation sections.
- Human feedback export and RAG Evaluation are read-only diagnostic foundations for future evaluation and calibration.

## Implemented Components

- FastAPI dashboard, profile, pipeline-run, planning, scan, tailoring, scheduler, and RAG surfaces.
- PostgreSQL-backed users, sessions, saved scans, decisions, actions, pipeline runs, artifacts, notification state, and owner-scoped data access.
- Optional Redis cache and user-pipeline admission lock support.
- Scrape-to-planning pipeline with job normalization, filtering, deduplication, resume matching, application queue artifacts, and tailoring packet outputs.
- Agentic workflow registry, planner, dry-run runner, verifier, manifest artifacts, and Agentic Review UI.
- Aggregate Agent Trace storage and UI display.
- Append-only Human Feedback events, summary/list read models, explicit Agentic Review helpful/not helpful actions, and agent feedback export evaluation rows.
- Diagnostic RAG Evaluation artifacts, validation helpers, compact Agentic Review display, and offline benchmark metric.
- Deterministic benchmark command: `python -m src.evaluation.agentic_benchmark --no-write --print-summary`.

## Manual Read-Only Adapter Chain

The manual read-only adapter chain is a portfolio-safe demonstration of how advisory agent adapters can be composed without becoming live orchestration. It runs only when explicitly invoked against caller-provided rows or the sanitized smoke fixture documented in `docs/read_only_chain_smoke.md`.

What it proves:

- Read-only adapters can be chained in a fixed order: `job_prioritization`, `tailoring_decision`, then `operator_review`.
- Decisions remain advisory through separate fields such as `advisory_priority`, `tailoring_decision`, and `operator_review_lane`.
- Production mutations are blocked with explicit guards including `did_mutate_production=false`, `allow_live_pipeline_wiring=false`, and `allow_application_submission=false`.
- The resulting diagnostic artifacts are inspectable in Agentic Review when manually copied into a sanitized run artifact set.

What it does not do:

- No live orchestration.
- No automatic application submission.
- No queue, tailoring, packet, scoring, ranking, scheduler, RAG, or production pipeline mutation.
- No change to `src/agents/workflow_runner.py`, which remains dry-run only.

## Production Engineering Strengths

- Owner/user isolation is preserved across authenticated APIs, pipeline artifacts, feedback events, and run diagnostics.
- Advisory outputs keep production fields separate from recommendations such as `advisory_priority`, `tailoring_decision`, and `operator_review_lane`.
- Workflow verification and benchmark fixtures make the agentic layer testable without scraping, private data, or live LLM calls.
- Diagnostic missing-data paths are safe: absent optional artifacts render empty states or warnings rather than breaking the operator workspace.
- Feedback remains append-only/read-only for evaluation, and RAG Evaluation remains diagnostic/read-only.

## Portfolio Resume Bullets

AI Engineer:

- Built ApplyLens AI, a FastAPI/PostgreSQL job-application intelligence platform with deterministic advisory agents, traceable Agentic Review diagnostics, offline benchmarks, and safety gates that separate recommendations from production actions.
- Built a manual read-only agent adapter chain that composes job prioritization, tailoring decision, and operator review diagnostics while preserving `did_mutate_production=false` and avoiding live autonomous execution.

Applied AI Engineer:

- Designed an applied AI workflow for resume/job decision support with advisory prioritization, tailoring-decision metadata, human feedback capture, RAG Evaluation diagnostics, and dry-run orchestration artifacts.
- Added verifier, artifact, and Agentic Review visibility for manually produced adapter-chain diagnostics without changing queue action, tailoring, packet generation, scoring, or ranking.

Data Scientist:

- Built offline evaluation and read-model layers for agentic workflow quality, RAG retrieval diagnostics, feedback label export, and benchmark metrics using sanitized/offline fixtures.
- Created a sanitized offline smoke fixture for manual read-only chain demos so advisory behavior can be reviewed without real resume data, real job data, or fake benchmark results.

ML Platform:

- Implemented artifact-backed observability for agent runs, workflow manifests, dry-run plans, verifier status, human feedback, and RAG Evaluation while preserving owner isolation and production decision immutability.
- Preserved production safety with explicit mutation guards, diagnostic-only artifacts, and a preflight harness where `executable_adapter_count=0`.

## Not Yet Implemented / Roadmap

- Autonomous agent execution beyond the current dry-run only runner.
- Using human feedback to tune scoring, ranking, queue action, resume selection, tailoring, or packet generation.
- Using RAG Evaluation metrics to change retrieval, ranking, scoring, queue action, tailoring, or packet decisions.
- Per-job agent trace rows; current trace support is aggregate-only.
- Team/shared workspace workflows beyond the current local operator and owner-scoped storage model.

## Safety And Accuracy

- Agents are advisory/diagnostic unless explicitly wired by the existing pipeline.
- The dry-run runner does not execute agents.
- Human feedback is append-only/read-only for evaluation.
- RAG Evaluation does not alter retrieval or ranking.
- The benchmark uses sanitized/offline fixtures and does not use private resume data, real application data, live scraping, or LLM calls.
- The portfolio docs describe implemented features separately from future roadmap items.
