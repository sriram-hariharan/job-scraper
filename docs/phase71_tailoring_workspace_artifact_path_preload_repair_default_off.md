# Phase 71A tailoring workspace artifact path/preload repair

Phase 71A repairs Tailoring Workspace and AI Optimize readback for live-pipeline runs that write planning artifacts into a run-scoped output directory.

The artifact path safety guard remains strict: artifact paths must stay inside the planning output directory used for that run. The repair does not make absolute paths broadly trusted and does not remove the “Artifact path must stay inside the planning output directory” protection.

## What changed

- Planning rows now expose row-level `planning_output_dir` metadata inferred from the generated `job_packets` artifact paths.
- Tailoring Workspace links carry that run-scoped planning output directory into the workspace route.
- Tailoring Workspace artifact, draft, preview, save, export, and AI Optimize preload calls pass the run-scoped `output_dir` to the existing guarded API endpoints.
- AI Optimize Scan pages retain the same run-scoped output directory and use it for preload, preview, draft persistence, and export readback.

## Safety behavior

- Safe in-run artifacts load from the correct run-scoped planning output directory.
- Out-of-run artifacts are still rejected by the existing path guard.
- Missing or empty suggestion sets remain readable as a no-suggestions/fallback state rather than a hard failed-load state.
- Scan preload payloads are loaded from the same run-scoped planning metadata as the opened planning row.

## Non-goals

This repair does not call a live LLM/provider in tests, create resume artifacts during readback, overwrite resumes, mutate source resume state, automate ATS actions, submit applications, enqueue apply/submit actions, mark jobs as applied, or add automatic application behavior.


## Verifier markers

- tailoring workspace artifact path repair
- suggestion set loading
- artifact path must stay inside planning output directory
- safe relative artifact path
- no path guard removal
- no live llm call in tests
- no resume artifact creation
- no source resume overwrite
- no ats automation
- no application submission
- no auto-apply
