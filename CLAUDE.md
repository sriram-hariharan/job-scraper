# CLAUDE.md

Guidance for Claude Code when working in this repository.

# Project
- Project name: Job Scraper App / ApplyLens AI.
- Treat this as a production-grade system that will grow into a larger autonomous agent platform.
- It is a Python (FastAPI) job-discovery and application-planning pipeline with a scoped
  TypeScript/React frontend and classic-script browser bridges. Human review is mandatory;
  there is no auto-apply.

# Repository-first workflow
- Always inspect the repository structure before proposing or implementing changes.
- Never hallucinate files, modules, functions, APIs, storage tables, routes, or pipeline stages.
- Map every requested change onto existing files that already handle adjacent logic.
- Assume existing code works unless a bug is demonstrated.
- Prefer incremental extensions over rewrites.
- Never simplify the project into toy examples.
- Treat source code, tests, configuration, and current Git history as more authoritative than
  README or stale documentation. (README.md and docs/ are large and may be outdated.)
- Verify documentation claims against the current implementation before relying on them.

# Repository map (high-level, verified ownership boundaries)
- `main.py` — pipeline CLI entrypoint.
- `run_api.py` — launches the API via `uvicorn src.app.api:app`.
- `src/app/` — FastAPI application: `api.py` (app instance, `/static` mount, UI routers, and
  `/api/*` routes), `services.py`, `schemas.py`, per-page `*_ui.py` routers, and classic-script
  browser bridges under `src/app/static/`.
- `src/pipeline/` — pipeline stages and runtime orchestration.
- `src/agents/` — agent, evidence-chain, and LLMops modules (many are default-off / dry-run /
  read-only by design; do not enable them implicitly).
- `src/storage/` — persistence layer (Postgres-backed and Redis-backed stores, plus per-domain
  stores).
- `src/auth/` — authentication, sessions, and owner scoping support.
- `src/config/` — settings, constants, and role/ATS configuration.
- Other `src/` subsystems (matching, evaluation, intelligence, tailoring, resume, rag,
  discovery, details, scrapers) support the pipeline; inspect the relevant module before
  changing it rather than relying on this list.
- `tests/` — pytest suite plus fixtures and support helpers.
- `frontend/executive-kpi/` — Vite + React + TypeScript dashboard workspace.
- `data/` — local caches/DBs and seeds (gitignored). `outputs/` — generated artifacts.
- Top-level `analyze_*.py`, `run_*.py`, and similar files are operational/analysis scripts.

# Architecture safety
- Never rewrite existing modules unless explicitly requested.
- Never change pipeline architecture without explicit approval.
- Before changing pipeline stages, inspect the current orchestrator, entrypoint, configuration,
  and tests. Never assume a documented stage order is current without verifying it against the
  implementation.
- Integrate new code into the current module structure.
- Avoid new dependencies unless absolutely necessary; prefer what is already in requirements.txt
  and frontend/executive-kpi/package.json.
- Preserve existing logging, configuration, retries, caching, deduplication, ranking, metrics,
  rate limiting, ATS health checks, and safety mechanisms.
- Keep prefilter relevance, LLM evaluation, and final application scoring clearly separated.
- Preserve stage-level observability.
- Keep behavior deterministic wherever possible.

# Application safety
- Never introduce auto-apply behavior.
- Preserve human review and manual application boundaries (default-off / dry-run / read-only
  agent modules exist on purpose — keep them off by default).
- Preserve authenticated owner scoping (owner-user-id auth helpers in src/app/api.py, threaded
  through services and stores).
- Never expose or reassign unowned records without explicit approval.
- Do not change ATS behavior, scoring, ranking, matching, storage schemas, decision values,
  application statuses, or API contracts unless explicitly approved.

# Editing rules
- Make only the exact required changes.
- Do not modify unrelated files.
- Do not reset, restore, stash, clean, commit, push, merge, tag, or delete files unless
  explicitly instructed.
- Never delete untracked files without first identifying and reporting them.
- Detect macOS Finder/iCloud numbered duplicate assets such as "file 2.js" or "file 3.css";
  report any that are found; never delete or stage them without explicit approval.
- Preserve current page ownership boundaries, including single request owners and
  React/legacy (classic-script) bridges under src/app/static/.

# Testing
- Test frameworks: pytest (Python) and vitest (frontend, colocated `*.test.ts(x)`).
- Inspect the current pytest configuration before selecting backend test commands.
- Inspect existing focused tests before implementation.
- Add focused regression tests for demonstrated bugs.
- Run focused tests first, e.g.:
  - Backend: `python -m pytest tests/<specific_test_file>.py`
  - Frontend: `cd frontend/executive-kpi && npm test`
- Do not run the full test suite unless explicitly requested (the backend suite is large).
- Run appropriate syntax, compilation, typecheck, build, safety, compatibility, and git diff
  checks:
  - Frontend typecheck: `cd frontend/executive-kpi && npm run typecheck`
  - Frontend build: `cd frontend/executive-kpi && npm run build`
- Never claim tests passed unless actually run successfully.
- Never claim visual approval.
- Do not launch a browser or take screenshots unless explicitly requested.
- Bound commands when a hang is possible (use timeouts for anything that may not terminate).

# Browser / runtime debugging
- For browser or runtime bugs, inspect the served assets, browser console errors, network
  responses, and bridge state before patching code.
- Never treat manually re-executing JavaScript in the browser console as the production fix.
- Preserve IIFE isolation for classic scripts unless inspection proves it is unnecessary.

# Environment notes
- The local Python interpreter and analysis paths are configured in .vscode/settings.json.
- Postgres-backed storage requires the DATABASE_URL environment variable and the psql client
  on PATH.
- Secrets (.env, service-account JSON) are gitignored; never commit them.
- The frontend workspace requires a modern Node version (see
  frontend/executive-kpi/package.json engines); its node_modules is gitignored.

# Git workflow
- Confirm branch and worktree state before editing.
- Current branch: item4-planning-tailoring-options-review.
- Current approved checkpoint: ddf02cb2af56f061087d9ff56c17de9541fd98fd.
- Do not commit or push unless explicitly requested.
- Before commit, verify there are no numbered duplicate generated assets.
- Stage only exact approved files.
- Report commit SHA and push result truthfully.

# Reporting
- Return concise bullet reports instead of full diffs unless explicitly asked.
- Use:
  - Inspected
  - Changed
  - What changed
  - Focused tests
  - Safety
  - Edited files
- For Edited files, show insertion/deletion summaries only.
- Never invent outputs, logs, test counts, or runtime behavior.
- Clearly state anything unverified.

# Current checkpoint
- The following facts were manually verified and approved by the user:
  - Item 4 Planning & Tailoring Options Review is complete.
  - Approved feature checkpoint commit: ddf02cb2af56f061087d9ff56c17de9541fd98fd.
  - Planning patch-selection writes now persist the authenticated owner and fail closed on blank ownership.
  - Draft save/load and patch preview resolve planning artifacts from authenticated owner + pipeline-run identity rather than caller-controlled output roots.
  - `/planning-artifact` uses authenticated owner-root containment, permits same-owner historical-run reads, and rejects cross-owner artifact access.
  - Request `output_dir` values no longer provide authorization authority on the hardened planning routes.
  - `generate_llm_tailoring=false` remains the passive deterministic default; LLM tailoring is triggered only by explicit user actions.
  - `review_decision`, `draft_status`, and derived tailoring readiness remain intentionally separate state concepts.
  - Item 4 focused, compatibility, governance, and closure verification is complete; repository-wide full-suite testing remains deferred until all planned items are complete.
- Application safety remains preserved: no auto-apply, ATS submission, recruiter messaging, or automatic mark-applied behavior was introduced.
- Operational classic-script isolation and existing page request ownership boundaries remain preserved.
- Next planned checkpoint: Item 5 — Deployment.
- Update this Current checkpoint section after every approved checkpoint commit.
