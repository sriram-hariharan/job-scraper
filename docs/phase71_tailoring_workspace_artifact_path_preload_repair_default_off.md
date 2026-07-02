# Phase 71A tailoring workspace artifact path/preload repair

Phase 71A repairs Tailoring Workspace and AI Optimize readback for live-pipeline runs that write planning artifacts into a run-scoped output directory.

The artifact path safety guard remains strict: artifact paths must stay inside the planning output directory used for that run. The repair does not make absolute paths broadly trusted and does not remove the “Artifact path must stay inside the planning output directory” protection.

The runtime repair separates two safe resolver paths:

- Planning artifacts, packet artifacts, suggestion sets, and scan preload packet references use the run-scoped planning output directory and safe relative artifact keys such as `job_packets/...`.
- Resume preview/source resume content uses the existing source resume preview resolver/profile-resume materialization path. Source resumes may live in the resume library/upload-safe location and are not validated with the planning artifact resolver.

## What changed

- Planning rows now expose row-level `planning_output_dir` metadata inferred from the generated `job_packets` artifact paths.
- Planning rows expose safe relative artifact keys for packet/suggestion artifacts so browser payloads do not need to trust raw absolute artifact paths.
- Tailoring Workspace links carry that run-scoped planning output directory into the workspace route.
- Tailoring Workspace artifact, draft, preview, save, export, and AI Optimize preload calls pass the run-scoped `output_dir` to the existing guarded API endpoints.
- Tailoring Workspace and AI Optimize readback use stable run packet resume metadata: safe relative packet keys plus a basename-only selected resume variant.
- AI Optimize Scan pages retain the same run-scoped output directory and use it for preload, preview, draft persistence, and export readback.
- The generated `__tailoring.json` suggestion artifact is optional. When the base planning packet exists but the optional tailoring artifact was not generated, the workspace loads the row context and exposes an explicit no-suggestions state instead of returning HTTP 400.
- AI Optimize preload can fall back to the base planning packet/job-resume metadata when the optional tailoring artifact is absent, with AI suggestion counts at `0` and a readable no-suggestions reason.
- Resume preview never uses `__tailoring.json` as the preview source. Browser payloads separate the base planning packet, optional suggestion artifact, and trusted resume preview identity.
- If a resume preview request accidentally receives a `__tailoring.json` path, the server defensively resolves the actual resume variant from the guarded base packet metadata or rejects the request with a safe error.
- The actual Tailoring Workspace resume preview route is covered by route-level tests and does not require `__tailoring.json`.
- The actual AI Optimize preload route is covered by route-level tests and returns base-packet context when `__tailoring.json` is missing.
- Static payload guards include `app.js`, `planning.js`, and `scan_workspace.js` so resume, preview, and preload fields do not use `tailoring_json_path`.

## Safety behavior

- Safe in-run artifacts load from the correct run-scoped planning output directory.
- Out-of-run artifacts are still rejected by the existing path guard.
- Source resume preview is loaded by trusted resume variant/source resolver metadata, not by the planning artifact guard.
- Source resume preview is loaded by resume variant/source identity and must not be validated as a planning suggestion artifact.
- Browser payloads avoid unsafe raw absolute resume paths when a stable resume variant/id is available.
- Browser payloads do not pass optional `__tailoring.json` files as resume preview paths.
- Missing or empty suggestion sets remain readable as a no-suggestions/fallback state rather than a hard failed-load state.
- Missing optional tailoring files are not treated as hard failures when their required base packet exists.
- Missing required base packets still fail safely with a clear artifact-not-found error.
- Scan preload payloads are loaded from the same run-scoped planning metadata as the opened planning row.

## Non-goals

This repair does not call a live LLM/provider in tests, create resume artifacts during readback, overwrite resumes, mutate source resume state, automate ATS actions, submit applications, enqueue apply/submit actions, mark jobs as applied, or add automatic application behavior.


## Verifier markers

- tailoring workspace artifact path repair
- suggestion set loading
- __tailoring.json optional only
- optional tailoring artifact
- resume preview must not use __tailoring.json
- actual workspace resume preview route covered
- actual AI Optimize preload route covered
- static app.js included in payload guard
- separate base packet, suggestion artifact, and resume preview sources
- missing tailoring file must not be HTTP 400
- missing tailoring artifact no-suggestions state
- clean no-suggestions state
- base planning packet fallback
- base packet fallback
- scan preload payload
- AI Optimize preload from base packet
- artifact path must stay inside planning output directory
- run-scoped planning output directory
- safe relative artifact path
- source resume preview resolver
- stable run packet resume metadata
- no raw browser absolute path trust
- no path guard removal
- no live llm call in tests
- no resume artifact creation
- no source resume overwrite
- no ats automation
- no application submission
- no auto-apply


## Runtime resolver marker notes

- separate planning artifact and resume preview path resolvers
- artifact path guard preserved
