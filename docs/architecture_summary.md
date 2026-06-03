# ApplyLens AI Architecture Summary

ApplyLens AI is organized as a local operator application with deterministic pipeline artifacts, authenticated web surfaces, advisory agent diagnostics, and offline evaluation tools. The architecture is intentionally conservative: diagnostics can explain and verify decisions, but they do not change production ranking, queue action, tailoring generation, packet generation, or job ordering.

## Application Layer

- FastAPI app: `src/app/api.py`, `src/app/services.py`, page routes, templates, and static JavaScript/CSS power the dashboard, planning, profile pipeline runs, scan workspace, tailoring workspace, scheduler, and Agentic Review pages.
- Auth/session isolation: authenticated routes use the server-side session owner; clients do not provide `owner_user_id` for scoped feedback or run diagnostics.
- PostgreSQL-backed persistence: users, sessions, profile resumes, saved scans, decisions, actions, scheduler artifacts, notification state, pipeline runs, and pipeline artifacts are stored through schemas under `src/storage/**/schema.sql`.
- Redis support: `src/storage/redis_locks.py` and service helpers provide optional cache/lock support, including user-pipeline admission locks when configured.

## Pipeline And Artifact Flow

The core workflow remains the existing deterministic job pipeline:

```text
company discovery
  -> ATS scraping
  -> job normalization
  -> filtering and deduplication
  -> resume matching
  -> application planning
  -> queue and packet artifacts
  -> reviewable dashboard outputs
```

Application planning writes artifacts such as source health, best resume by job, application shortlist, execution queue, tailoring decision summaries, operator review summaries, job packets, workflow summaries, verification payloads, dry-run outputs, and RAG Evaluation reports when those diagnostic hooks are present.

## Agentic Layer

- `src/agents/workflow_registry.py` declares the ApplyLens Agentic Workflow manifest, ordered agents, expected artifacts, required flags, safety guarantees, and benchmark metric keys.
- `src/agents/workflow_planner.py` builds a dry-run execution plan with steps marked planned and disabled.
- `src/agents/workflow_runner.py` is dry-run only; it emits skipped dry-run step results and never executes agents.
- `src/agents/workflow_verifier.py` validates artifacts and reports warnings/failures according to existing strict-mode behavior.
- Advisory agents read existing rows and emit separate advisory fields. They do not overwrite production `action`, queue ordering, packet generation, resume text, or tailoring behavior.

## Read-Only Adapter Prototypes

The read-only adapter prototypes wrap deterministic advisory helpers behind explicit/manual inputs. The manual chain in `src/agents/read_only_adapter_chain.py` composes only the read-only job prioritization, tailoring decision, and operator review adapters in a fixed order. It writes diagnostic artifacts only when an isolated `output_dir` is provided.

This chain sits on a diagnostic artifact boundary:

- Input is explicit rows or an explicit queue CSV path, including the sanitized fixture documented in `docs/read_only_chain_smoke.md`.
- Output is chain-specific JSON/Markdown plus adapter-specific files inside adapter subdirectories.
- Verifier/read-model/UI support can validate and display already-present chain artifacts in Agentic Review.
- `src/agents/workflow_runner.py` remains a separate dry-run runner and does not invoke the chain.

The chain is not production data flow, not live orchestration, and not an application-submission path. Safety flags such as `did_mutate_production=false`, `allow_live_pipeline_wiring=false`, and `allow_application_submission=false` document that boundary in the result payload.

## Agent Trace And Agentic Review

Aggregate Agent Trace storage records run/step diagnostics when tracing is enabled. The Agentic Review UI in `src/app/static/agentic_review.js` renders:

- pipeline run status
- advisory workflow summary
- Agent Trace
- workflow verification
- workflow manifest
- execution plan
- dry-run result
- manual read-only adapter chain diagnostics when artifacts are present
- Human Feedback
- RAG Evaluation

The UI uses compact diagnostic cards and safe empty states when optional artifacts are missing.

## Human Feedback Loop

Human feedback events live in `src/storage/agent_feedback/store.py` and the `agent_feedback_events` table. Feedback is append-only and diagnostic. The implemented read/export foundation includes:

- event recording API
- summary and list read APIs
- Agentic Review helpful/not helpful controls
- agent feedback export payloads
- normalized evaluation rows
- deterministic feedback labels and values

The agent feedback export does not tune or mutate production decisions.

## RAG Evaluation

`src/evaluation/rag_evaluation.py` provides deterministic helpers to build RAG evaluation rows, summarize metrics, validate payloads, render markdown, and write `rag_evaluation_summary.json` plus `rag_evaluation_report.md`.

RAG Evaluation reports average retrieval score, top-k hit rate, missing evidence warnings, validation status, and reason codes. It is diagnostic/read-only and does not alter retrieval, embeddings, corpus generation, scoring, ranking, queue action, tailoring, or packet behavior.

## Benchmark And Evaluation

`src/evaluation/agentic_benchmark.py` runs an offline deterministic benchmark over sanitized fixtures. It checks advisory-agent behavior, workflow registry validity, feedback export schema validity, and RAG Evaluation schema validity.

Useful command:

```bash
python -m src.evaluation.agentic_benchmark --no-write --print-summary
```

The benchmark is designed for repeatable portfolio demos and regression checks; it does not require real database rows, private data, scraping, or LLM calls.

## Safety Guarantees

- No production decision mutation from Agentic Review, feedback export, RAG Evaluation, workflow verification, or dry-run runner diagnostics.
- No advisory diagnostics change scoring, ranking, filtering, queue action, job ordering, resume selection, tailoring generation, packet generation, RAG retrieval, scheduler behavior, source behavior, or pipeline execution.
- Missing diagnostic artifacts are warnings or empty states unless existing strict verifier behavior is explicitly enabled.
