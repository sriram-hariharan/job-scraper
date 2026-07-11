# ApplyLens AI Demo Walkthrough

This is a 2-3 minute portfolio script for showing the implemented system with sanitized/local data only. Do not show private resumes, real application data, real emails, or private company/client details.

## Setup

- Start the local FastAPI app.
- Use a sanitized local account and sanitized pipeline artifacts.
- Keep the Agentic Benchmark command ready:

```bash
python -m src.evaluation.agentic_benchmark --no-write --print-summary
```

## Script

0:00 - Open the dashboard or profile pipeline runs.

"ApplyLens AI is a job-application intelligence workspace. The core pipeline scrapes and normalizes jobs, matches them against saved resumes, and creates reviewable planning artifacts."

0:20 - Open one pipeline run.

"Each run is owner-scoped and artifact-backed. The app keeps run status, counts, generated planning outputs, and diagnostic metadata available from the UI."

0:40 - Open Agentic Review.

"This is the recruiter-friendly view of the agentic layer. It shows what the advisory system saw and validated without changing what jobs are shown or how the queue is ordered."

0:48 - Optional: open a Planning row with `LLM adjudicator readback`.

"Hybrid scoring combines deterministic evidence dimensions with local semantic alignment at a small fixed weight. When optional adjudicator output was generated, Planning displays that existing selector readback here. Opening this detail does not call a provider, and the commentary cannot override the selected resume or score."

0:55 - Show Agent Trace.

"Agent Trace records aggregate run and step diagnostics when tracing is enabled. It is traceability for the workflow layer, not hidden autonomous execution."

1:10 - Show Workflow Verification.

"The verifier checks whether expected agentic artifacts are present and internally consistent. Missing optional data is a warning in non-strict mode, which keeps the operator page usable."

1:25 - Show Manifest, Execution Plan, and Dry Run.

"The workflow registry defines the implemented advisory agents and safety guarantees. The execution plan is diagnostic. The runner is dry-run only: `src/agents/workflow_runner.py` reports skipped steps and does not execute agents or mutate production decisions."

1:50 - Show Human Feedback.

"The Human Feedback section lets the user explicitly mark the Agentic Review as useful or not useful. Feedback is append-only and read-only for evaluation; it does not tune ranking, scoring, queue action, tailoring, or packet generation."

2:05 - Show RAG Evaluation.

"RAG Evaluation summarizes retrieval diagnostics such as average retrieval score, top-k hit rate, and missing evidence warnings. It does not alter retrieval behavior, embeddings, ranking, or production decisions."

2:20 - Show benchmark command.

"The project includes an offline deterministic benchmark using sanitized/offline fixtures. This validates advisory-agent behavior, workflow registry contracts, agent feedback export shape, and RAG Evaluation schema shape without live scraping or LLM calls."

2:40 - Optional 60-90 second manual chain smoke demo.

"There is also a manual read-only adapter chain smoke fixture for technical reviewers. It is not production and not live orchestration; it runs only from an explicit local command against sanitized rows."

```bash
TMP_CHAIN_DIR="$(mktemp -d)"
python -m src.agents.read_only_chain_artifact_generator \
  --queue-input tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv \
  --output-dir "$TMP_CHAIN_DIR" \
  --json
find "$TMP_CHAIN_DIR" -maxdepth 3 -type f -print | sort
```

"The generator requires both `--queue-input` and `--output-dir`; it refuses to run without explicit paths. The root output includes `read_only_adapter_chain_result.json`, `read_only_adapter_chain_report.md`, and generator-specific report files; adapter-specific CSV/JSON/Markdown files stay inside adapter subdirectories. The chain result uses `execution_mode=manual_read_only_adapter_chain` and safety flags such as `did_mutate_production=false`, `allow_live_pipeline_wiring=false`, and `allow_application_submission=false`."

"For viewer testing, those two root chain artifacts can be copied into a sanitized run artifact set so Agentic Review can display them. That copy is manual; the app does not run the chain from UI actions, live planning, the scheduler, or `workflow_runner.py`."

3:50 - End with safety guarantees.

"The important engineering choice is separation: the production pipeline creates the real application-planning outputs, while the agentic layer explains, verifies, traces, and evaluates them. No production decision mutation happens from these diagnostics."

## What Not To Claim

- Do not claim real autonomous agent execution; the runner is dry-run only.
- Do not claim the manual read-only adapter chain is live orchestration.
- Do not claim feedback tunes ranking, scoring, queue action, resume selection, tailoring generation, or packet generation.
- Do not claim RAG Evaluation changes retrieval, embeddings, ranking, scoring, or queue behavior.
- Do not claim Groq or an LLM calculates `final_score`, chooses the winner, or changes the queue action.
- Do not claim active TS clearance diagnostics cap or penalize scores.
- Do not claim the Planning readback UI triggers adjudication or a provider call.
- Do not claim auto-apply, ATS submission, recruiter messaging, or source-resume overwrite.
- Do not claim benchmark results from a live production run unless you are showing a real sanitized run and clearly label it.
- Do not show private user data, real resumes, real applications, real emails, or confidential company details.

## Quick Feature Checklist

- Dashboard/profile pipeline runs
- Pipeline run details
- Agentic Review
- Agent Trace
- Workflow Verification
- Manifest / Execution Plan / Dry Run
- Human Feedback
- RAG Evaluation
- Manual read-only adapter chain smoke fixture: `docs/read_only_chain_smoke.md`
- Operator runbook for the explicit generator: `docs/read_only_chain_operator_runbook.md`
- Agentic Benchmark command
- Safety close: no production decision mutation
