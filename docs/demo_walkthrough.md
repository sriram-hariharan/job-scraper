# ApplyLens AI Demo Walkthrough

This is a 4-5 minute primary portfolio demo for showing the implemented system with sanitized/local data only. Do not show private resumes, real application data, real emails, or private company/client details.

## Setup

- Start the local FastAPI app.
- Use a sanitized local account and sanitized pipeline artifacts.
- Keep one eligible Planning row ready for Generate Suggestions.

## Primary Demo Script

0:00 - Run the live pipeline with sanitized data.

"ApplyLens AI is a job-application intelligence workspace. The live pipeline collects and normalizes jobs, matches them against saved resumes, and creates reviewable planning artifacts."

0:35 - Open Planning.

"Planning shows the ranked job, deterministic score, selected resume, packet status, and next human review step. Hybrid scoring combines evidence dimensions with always-on local `semantic_alignment` at weight `0.05`. No provider or LLM calculates the final score."

Open `AI review notes · advisory` when present.

"Planning displays that existing selector readback as optional readback and advisory notes. This display does not call a provider from the UI and cannot override the selected resume, score, ranking, queue, or action."

1:15 - Trigger Generate Suggestions for one eligible row.

"Generate Suggestions runs one existing backend request while the full-page step runner communicates progress. It does not apply to the job or change application status."

1:50 - Show the full-page progress flow, then Tailoring Workspace.

"The workspace opens the selected resume and generated suggestions for human review. The operator accepts, edits, or rejects suggestions before export; source resumes are not overwritten."

2:30 - Open AI Optimize Scan.

"AI Optimize Scan explains match gaps and suggestion coverage. When active TS/Top Secret clearance is required but missing, the clearance warning is diagnostic-only: it does not cap or penalize the score and does not change the selected resume."

3:10 - Open Agentic Review.

"Agentic Review shows the evidence chain, Agent Trace, and workflow verification from existing run artifacts. This is traceability for the workflow layer, not hidden autonomous execution."

Show one collapsed trace detail and the workflow verification summary.

"The agentic layer explains and verifies pipeline decisions without changing what jobs are shown, how the queue is ordered, or which application action a human takes."

4:15 - Close with human-control safety guarantees.

"ApplyLens never auto-applies, submits to an ATS, messages recruiters, or overwrites source resumes. There is no production decision mutation from these diagnostics, and the final application action remains manual and human-controlled."

## Optional Technical Appendix

For a technical reviewer, optionally show the 60-90 second manual read-only adapter-chain smoke demo after the primary product demo. It is not production and not live orchestration; it runs only from an explicit local command against sanitized rows.

```bash
TMP_CHAIN_DIR="$(mktemp -d)"
python -m src.agents.read_only_chain_artifact_generator \
  --queue-input tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv \
  --output-dir "$TMP_CHAIN_DIR" \
  --json
find "$TMP_CHAIN_DIR" -maxdepth 3 -type f -print | sort
```

The generator requires both `--queue-input` and `--output-dir`; it refuses to run without explicit paths. The resulting artifacts remain diagnostic and can be copied manually into a sanitized run artifact set for Agentic Review. The app does not run this chain from UI actions, live planning, the scheduler, or `workflow_runner.py`.

The chain result uses `execution_mode=manual_read_only_adapter_chain` and safety flags including `did_mutate_production=false`, `allow_live_pipeline_wiring=false`, and `allow_application_submission=false`. `src/agents/workflow_runner.py` remains dry-run only.

The offline benchmark is also available as an optional technical check:

```bash
python -m src.evaluation.agentic_benchmark --no-write --print-summary
```

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

- Run live pipeline
- Planning score and selected resume
- AI review notes · advisory
- Generate Suggestions full-page progress
- Tailoring Workspace
- AI Optimize Scan diagnostic-only clearance warning
- Agentic Review evidence chain
- Agent Trace and Workflow Verification
- Optional manual read-only adapter chain smoke fixture: `docs/read_only_chain_smoke.md`
- Optional Agentic Benchmark command
- Safety close: final application action remains manual
