# ApplyLens AI / Job Scraper — Complete Project Context

> Canonical implementation-oriented map for humans and coding agents working in this repository.
>
> Repository: `sriram-hariharan/job-scraper`
> Snapshot discipline: verify the active branch, HEAD, and worktree before relying on commit-specific state.

This is a living architecture and product reference, not a changelog. Current production code is authoritative. Tests describe enforced contracts. Runtime acceptance evidence can confirm UI behavior. `README.md`, `docs/`, and checkpoint artifacts are supporting material and must not override the implementation.

## Table of contents

1. [Scope and classification](#1-scope-and-classification)
2. [Product and invariants](#2-product-and-invariants)
3. [Runtime topology and entry points](#3-runtime-topology-and-entry-points)
4. [Acquisition and discovery](#4-acquisition-and-discovery)
5. [Processing pipeline](#5-processing-pipeline)
6. [Matching, intelligence, and resume selection](#6-matching-intelligence-and-resume-selection)
7. [Application planning and tailoring](#7-application-planning-and-tailoring)
8. [Bulk generation](#8-bulk-generation)
9. [Optimization Review / Scan](#9-optimization-review--scan)
10. [Application decisions and execution boundary](#10-application-decisions-and-execution-boundary)
11. [Web application, identity, and routes](#11-web-application-identity-and-routes)
12. [RAG and assistant retrieval](#12-rag-and-assistant-retrieval)
13. [Provider and model routing](#13-provider-and-model-routing)
14. [Agent, trace, and evaluation infrastructure](#14-agent-trace-and-evaluation-infrastructure)
15. [Scheduler and notifications](#15-scheduler-and-notifications)
16. [Persistence and caching](#16-persistence-and-caching)
17. [Frontend architecture](#17-frontend-architecture)
18. [Observability, concurrency, configuration, and deployment](#18-observability-concurrency-configuration-and-deployment)
19. [Repository inventory](#19-repository-inventory)
20. [Tests, documentation, and archive](#20-tests-documentation-and-archive)
21. [Ownership lookup and maintenance rules](#21-ownership-lookup-and-maintenance-rules)

---

# 1. Scope and classification

The repository mixes active product code with optional integrations, controlled experiments, generated assets, test fixtures, historical readiness records, and archived implementations. Interpret references in this document using these labels:

| Label | Meaning |
|---|---|
| **Production runtime** | Called by a normal CLI, API, worker, page, or scheduled execution path. |
| **Optional/default-off** | Integrated behind an explicit flag or runtime prerequisite and not part of the default path. |
| **Internal infrastructure** | Persistence, contracts, adapters, or orchestration support used by active or guarded flows; not itself a user feature. |
| **Diagnostic/developer** | Read-only previews, dry runs, canaries, benchmarks, analysis scripts, smoke tools, or admin utilities. |
| **Historical/readiness** | Checkpoint and phase evidence retained in `docs/` or tests; not proof that a capability is active. |
| **Archive** | Code under `archive/`; not an authoritative runtime owner unless an active import proves otherwise. |

Do not infer activation from a filename. In particular, many `src/agents/` and `src/evaluation/` modules deliberately contain `readonly`, `dry_run`, `shadow`, `preview`, `default_off`, `canary`, or readiness semantics.

---

# 2. Product and invariants

ApplyLens AI is a job acquisition, ranking, resume-selection, tailoring, planning, and human-review application. It discovers or receives job sources, builds job intelligence, compares resume evidence, produces planning artifacts and grounded rewrite suggestions, and tracks human application decisions.

The product does **not** have an authoritative automatic ATS submission loop. It can construct queues, review packets, approvals, readiness previews, simulations, and human handoff artifacts, but application submission remains outside the active authority boundary.

## 2.1 Separate scoring responsibilities

Keep these conceptually and operationally distinct:

1. **Deterministic eligibility/prefiltering** removes jobs that do not satisfy role, title, location, freshness, exclusion, or early evidence rules.
2. **LLM evaluation** performs bounded interpretation for an explicitly enabled and routable workload.
3. **Final application scoring** produces downstream application-priority information.

An embedding relevance value, LLM fit result, final application score, Scan optimization score, and UI progress percentage are not interchangeable.

## 2.2 Safety invariants

Preserve:

- authenticated owner isolation and run identity;
- source-specific retry and pagination bounds;
- acquisition health and sanitized failure classification;
- deterministic filtering, deduplication, and seen-state filtering;
- bounded batch and subprocess execution;
- evidence-grounded resume and tailoring decisions;
- explicit provider/model qualification and fail-closed behavior;
- human review before resume/application use;
- write verification where a UI reports persistence success;
- stage status, metrics, and inspectable failure states;
- no silent provider fallback or scoring-owner substitution.

---

# 3. Runtime topology and entry points

```text
Standalone discovery (manual or scheduled)
  run_agent_discovery.py
    -> company discovery agent
    -> src.pipeline.discovery_stage
    -> PostgreSQL discovery state (+ Redis read-through cache when configured)

Acquisition / owner projection
  main.py
    -> src.pipeline.collector
    -> scrapers or shared PostgreSQL corpus
    -> deterministic stages
    -> optional guarded AI/agent stages
    -> RAG/seen/metrics persistence
    -> optional run_application_planning.py

Authenticated web application
  run_api.py
    -> src.app.api
    -> src.app.services and page modules
    -> PostgreSQL owner state, run artifacts, workers, and hybrid frontend
```

## `main.py` — production CLI

`main.py` validates CLI mode combinations, initializes runtime status, invokes `collect_all_jobs_async()`, exports/merges planning information, and can launch `run_application_planning.py`. It supports normal scraper-backed processing, owner-neutral `--global-acquisition-only`, authenticated `--shared-postgres-projection`, application-planning-only operation, bounded planning job/packet limits, optional tailoring/LLM/fallback/adjudication flags, and controlled seen-state deletion.

## `run_application_planning.py` — production planning orchestrator

The authoritative planning chain is subprocess-oriented:

```text
batch_select_best_resume_variant.py
  -> optional archive_batch_selector_runtime_fixture.py helper
  -> application_shortlist_from_batch_selector.py
  -> application_execution_queue.py
  -> job packets and optional tailoring artifacts
```

At the end, the orchestrator also attempts to write agentic workflow summary, manifest, execution-plan, dry-run, RAG-evaluation, and verifier artifacts. Those artifacts are best-effort/non-authoritative; the verifier becomes strict only when `APPLYLENS_WORKFLOW_VERIFIER_STRICT` is enabled.

## Other entry points

- `run_api.py` launches the FastAPI/Uvicorn application and supports reload mode.
- `job_app.py` is a compatibility/menu and automation wrapper used by scheduler command construction; it is not the only runtime authority.
- `run_agent_discovery.py` is the standalone discovery entry point. Discovery is **not** an unconditional first stage inside `collector.py`.
- `src/app/bulk_generation_worker.py` is the persisted Bulk worker CLI launched by the web service.
- `src/pipeline/scheduler.py` is the scheduler CLI and macOS launchd integration owner. There is no active `src/scheduler/` package.

---

# 4. Acquisition and discovery

## 4.1 Active acquisition sources

`src/pipeline/collector.py` runs these eleven scraper adapters, concurrently at the outer collector boundary:

| Source | Scraper | Dedicated detail adapter |
|---|---|---|
| Workday | `src/scrapers/workday_scraper.py` | `src/details/workday_details.py` |
| Greenhouse | `src/scrapers/greenhouse_scraper.py` | `src/details/greenhouse_details.py` |
| Lever | `src/scrapers/lever_scraper.py` | `src/details/lever_details.py` |
| Ashby | `src/scrapers/ashby_scraper.py` | `src/details/ashby_details.py` |
| Workable | `src/scrapers/workable_scraper.py` | `src/details/workable_details.py` |
| Jobvite | `src/scrapers/jobvite_scraper.py` | `src/details/jobvite_details.py` |
| Recruitee | `src/scrapers/recruitee_scraper.py` | none |
| SmartRecruiters | `src/scrapers/smartrecruiters_scraper.py` | `src/details/smartrecruiters_details.py` |
| Built In | `src/scrapers/builtin_scraper.py` | `src/details/builtin_details.py` |
| USAJobs | `src/scrapers/usajobs_scraper.py` | none |
| Himalayas | `src/scrapers/himalayas_scraper.py` | none |

Built In is a site adapter, not Python built-in behavior. A scraper’s presence does not imply a separate detail adapter.

## 4.2 Discovery mechanisms

The standalone discovery path uses `src/discovery/` and `src/pipeline/discovery_stage.py`. Implemented mechanisms include domain and career-page ATS detection; curated seeds and learned company/domain state; ATS-neighbor discovery for Greenhouse, Lever, Ashby, Workable, and Jobvite; Greenhouse API and embedded-board discovery; SmartRecruiters discovery; GitHub-assisted discovery; sitemap discovery/fetching; and bounded persisted crawl scheduling, offsets, and detection cache.

`src/config/consts.py::SUPPORTED_ATS` is the six-family discovery/detection set (Greenhouse, Lever, Workday, Ashby, Workable, Jobvite). It is not the complete acquisition-source list: the other sources enter through direct tenant, global-feed, or query-profile adapters.

## 4.3 Transport, pagination, and concurrency

Shared HTTP defaults in `src/utils/http_retry.py` and `src/config/consts.py` are a 10-second request timeout, two total attempts, 0.5-second fallback delay, a 30-second delay cap, and transient status handling for 429/500/502/503/504. Numeric or HTTP-date `Retry-After` values are honored within the cap. Source adapters can implement equivalent bounded async/urllib handling where they do not call the shared `requests` wrapper.

| Source | Explicit bound |
|---|---|
| Workday | 20 rows/page, at most 100 pages |
| Workable | 50 rows/page, at most 100 pages |
| SmartRecruiters | 100 rows/page, at most 10 pages/company |
| USAJobs | at most 4 query profiles, 50 rows/page, 20 pages/profile |
| Himalayas | at most 4 query profiles, 20 rows/page, 10 pages/profile |
| Built In | three fixed category URLs; returned jobs capped at 10,000 |

The outer collector schedules all source functions through `asyncio` executors. Important inner limits include Greenhouse connector 50, Lever connector/semaphore 100, discovery semaphores/connectors 20, detail enrichment `ThreadPoolExecutor(max_workers=20)`, timestamp hydration workers 10, and source-specific `run_parallel` limits. These are independent bounds, not one global concurrency number.

## 4.4 Health and failure semantics

`src/discovery/crawl_scheduler.py` defines `AcquisitionOutcome` statuses `SUCCESS`, `EMPTY`, `PARTIAL`, and `FAILED`. Failure reasons are sanitized to transport, non-200, malformed-payload, parse, pagination-interrupted, pagination-limit, or no-progress categories. Only `SUCCESS` and `EMPTY` advance a target’s successful crawl schedule. Metrics combine transport outcomes with URL/timestamp/description completeness and downstream stage counts.

---

# 5. Processing pipeline

## 5.1 Modes

### Global acquisition only

`global_acquisition_only=True` scrapes all sources, checks source health, deduplicates, persists owner-neutral documents to PostgreSQL RAG storage, enforces shared retention, and persists discovered companies. It does not run owner preferences, details, intelligence, AI evaluation, resume matching, final scoring, or full-pipeline metrics.

### Shared PostgreSQL projection

`input_source="shared_postgres_pool"` requires authenticated user-pipeline mode and an owner. It reads the active shared RAG corpus through a bounded projection with a hard ceiling of 500,000 jobs, then applies that owner’s preferences and downstream stages. It does not scrape or persist global acquisition metrics.

### Normal scraper-backed processing

The CLI/default collector acquires from scrapers and runs the full downstream pipeline. The authenticated web launcher also uses this collector path unless explicitly configured for a planning-only projection.

## 5.2 Full downstream order

```text
scraping or shared_input
  -> location preference policy
  -> deterministic filter
  -> dedupe
  -> rank
  -> seen/cache filter
  -> detail enrichment
  -> JD intelligence + skill persistence/discovery
  -> AI-evaluation eligibility filter
  -> embedding prefilter (ownerless filesystem mode only)
  -> AI job evaluation
  -> embedding resume prior (ownerless filesystem mode only)
  -> final application-priority scoring
  -> optional shadow/trace/vector/evidence hooks
  -> RAG export and retention
  -> seen-state persistence
  -> metrics/finalization
  -> optional application planning in main.py
```

Authenticated user-pipeline runs skip the legacy filesystem embedding prefilter and filesystem resume prior because profile resumes live in PostgreSQL. Resume variant selection still occurs later in application planning.

## 5.3 Filtering

`src/pipeline/job_filter.py` applies selected role-family/title patterns, target seniority and strictness, excluded keywords, U.S./remote location rules, and a 24-hour freshness policy. Owner location preferences are applied before that filter with strict/fallback behavior from onboarding/profile settings. Ashby, Jobvite, and Workday have source-specific timestamp hydration paths. User-pipeline runs write role/title audit and source-health artifacts.

## 5.4 Deduplication, ranking, and seen state

- `src/pipeline/dedupe.py` owns duplicate suppression.
- `src/pipeline/job_ranker.py` ranks deduplicated jobs using role, seniority, location, and preferred-skill information.
- `src/utils/job_cache.py` filters seen identities after ranking and stages/promotes owner-scoped seen records when the PostgreSQL backend is configured.
- The legacy non-PostgreSQL load/save fallback is intentionally a no-op; active code must not be documented as using `job_cache.db`.

## 5.5 Detail and description caching

`src/pipeline/job_details.py` invokes available detail adapters with a 20-worker pool. `src/cache/description_cache.py` uses PostgreSQL table `job_description_cache`; there is no active `description_cache.db` runtime.

## 5.6 Intelligence, AI evaluation, and output

`src/intelligence/job_intelligence.py` builds structured intelligence and decides which jobs are eligible for AI evaluation. Skill and evaluation caches are observed separately. `src/ai/job_fit_evaluator.py` evaluates the bounded candidate set. `src/pipeline/application_scorer.py` then owns final application-priority scoring. The corpus, seen state, market insight logs, and metrics are persisted through their domain stores.

---

# 6. Matching, intelligence, and resume selection

## 6.1 Matching ownership

`src/matching/` contains domain models, the JD intelligence contract, job adapter, relevance prefilter, dimensional scorer, semantic similarity, clearance handling, and signal-family matching. `src/intelligence/` adds role-family classification, job intelligence, market insights, skill discovery, and skill frequency.

The scorer’s semantic-alignment weight is `0.05`; it is a scoring component, not a universal similarity acceptance threshold.

## 6.2 Skill and requirement semantics

`src/ai/hybrid_skill_extractor.py` and `src/ai/skill_llm_enricher.py` combine deterministic/normalized signals with optional LLM enrichment. Structured required, preferred, and all-skill fields remain distinct.

- A presentation string such as `Python, Tableau, Statistical analysis` is not one atomic skill.
- Arbitrary comma text is not blindly split into invented requirements.
- `Python or R` is one disjunctive requirement.
- Either alternative satisfies that group once, both still count once, and neither produces one missing group.
- Generic prose containing “or” is not automatically treated as a disjunction.

## 6.3 Resume ingestion and evidence

`src/resume/` owns document loading/storage abstraction, resume models, evidence construction, and embeddings. Profile resume PDF blobs and role mappings are stored in PostgreSQL. New Scan separately accepts a saved profile resume, uploaded PDF/DOCX/TXT, or pasted resume text.

Resume evidence includes skills, tools, experience entries, quantified bullets, and anchors usable by deterministic matching and tailoring. A filename or title resemblance is not sufficient authority.

## 6.4 Planning selection authority

`batch_select_best_resume_variant.py` compares valid resume variants per job and records deterministic winner, runner-up, scores, gap, prefilter status, credibility, and any explicitly enabled fallback/adjudication metadata. Downstream planning and Bulk validate that selected identities still refer to the current owner, pipeline, planning row, and winner/runner-up set.

---

# 7. Application planning and tailoring

## 7.1 Planning outputs

The planning orchestrator produces `best_resume_variant_by_job.csv`, `application_shortlist_by_job.csv`, `application_execution_queue.csv`, `job_packet_manifest.csv`, per-job packets, deterministic and optional LLM tailoring JSON/Markdown, status summaries, diagnostics, and best-effort agentic artifacts.

Planning can consume a filesystem corpus or bounded PostgreSQL projection. Authenticated web runs materialize run-scoped scratch/output under the canonical owner/run tree and register user-pipeline artifacts in PostgreSQL.

## 7.2 Tailoring stages

`src/tailoring/` owns family matching, packet evidence support, planning, candidate selection, rendering, replacement selection, and score utilities. Live generation in `src/tailoring/llm.py` follows this guarded shape:

```text
packet evidence
  -> bounded rewrite-direction generation
  -> candidate writer/refinement
  -> judge/validation
  -> replacement selector
  -> rendered artifacts and metadata
```

Generated text must remain grounded in supplied evidence. Unsupported tools, methods, metrics, skills, domains, or responsibilities are rejected or left directional rather than silently applied.

## 7.3 Actionability

- Safe positive-lift rewrites use the ready/actionable lane.
- Safe, high-confidence, `export_safe_no_score_lift` rewrites may be `direct_apply_optional`.
- Score-neutral optional rewrites must not be labeled `direct_apply_ready`.
- Regressive, fabricated, unsupported, or unsafe cosmetic changes remain rejected/non-actionable.
- Source resume content is not overwritten by generation.

## 7.4 Failure, cache, and fallback behavior

Tailoring records requested/resolved provider and model, cache hits, parse status, retry counts, raw-response handling, and failure category. Authenticated owner generation resolves the effective qualified `tailoring_generation` route and disables provider fallback. If that route or credential is unavailable, it returns a failed-closed tailoring result without a provider call. Ownerless CLI generation uses explicit environment/default configuration; this is separate from user preference routing.

---

# 8. Bulk generation

Bulk reuses the existing per-job regeneration service; it is not a second tailoring executor.

Owners are `src/app/bulk_generation_service.py`, `src/app/bulk_generation_worker.py`, `src/storage/bulk_generation/`, the Bulk routes in `src/app/api.py`, and the UI in `frontend/executive-kpi/src/PlanningWorklist.tsx` plus `src/app/static/planning.js`.

## 8.1 Admission and persisted state

- Requests contain 1–500 distinct candidates.
- Candidates are checked against the authenticated owner’s current pipeline planning artifacts and current winner/runner-up resume identities.
- A unique partial index permits only one `queued`, `running`, or `stop_requested` run per owner.
- Live Pipeline and Bulk generation block one another for the same owner.
- Run states: `queued`, `running`, `stop_requested`, `stopped`, `completed`, `failed`.
- Item states: `pending`, `running`, `succeeded`, `needs_attention`.
- The worker processes items sequentially and checks stop-after-current between items.
- Dead, mismatched, or missing workers are reconciled to an explicit failed state.

The worker invokes regeneration with live LLM tailoring enabled, refresh disabled, and parse retry limit zero. Item outcomes distinguish generated output, safe/no-rewrite, empty/unusable output, stale candidates, and provider/generation failures.

## 8.2 First run, progress, and stop

A first-time eligible Bulk action opens the settings overlay and then uses `POST /planning/bulk-generation/start`. Active state uses the canonical status poller and progress popover. Stop means stop after the current item; it is not an unsafe process kill.

## 8.3 Results Center and reruns

Terminal history for the current pipeline remains accessible. Results are the latest attempt per job across runs and support search plus All, Generated / Ready, Safe / no rewrite, and Failed / attention filters.

Default rerunnable outcomes are `no_safe_rewrites`, `empty`, `failed`, or blank outcome, provided the item is not running. Generated results remain visible but are not marked rerunnable by the public payload/UI.

Selected reruns and rerun-all-eligible use the exact chosen identities, start immediately through the same endpoint/worker/poller, do not reopen settings, and must not silently apply the first-run default count. The modal closes only after admission succeeds; an error leaves it open.

---

# 9. Optimization Review / Scan

Primary owners are `src/app/planning_ui.py`, `src/app/services.py`, `src/app/static/planning.js`, `src/app/static/scan_workspace.js`, and the Scan CSS files. The main route is `/scan-workspace`; `/tailoring-workspace` is a related but distinct artifact editor.

## 9.1 Entry lanes

1. **Planning artifact lane** — opens a job/resume packet and loads/saves a workspace-draft JSON sibling using authenticated owner plus `pipeline_run_id` validation.
2. **Saved Scan lane** — creates/loads owner-scoped PostgreSQL saved scans, including deterministic New Scan reports built from a saved resume, PDF/DOCX/TXT upload, or pasted resume plus job description.

Optional saved-scan diagnostic/exact-change/handoff stages are exposed as explicit `enable_*` request flags whose defaults are false. They are not normal Save behavior.

## 9.2 Review model

The workspace renders Skills, Formatting, Personal Details, and review/guidance state from a stable issue contract. Matched/Missing/AI presentation must preserve canonical skills, structured groups, alternative requirements, and resume evidence anchors.

## 9.3 Exclude and Re-include

- Exclude retains the stable issue ID and removes the item from active Missing count/penalty.
- Exclusion does not promote the issue to Matched and does not delete it from the review contract.
- Excluded items render once in a dedicated Excluded group with Re-include.
- Re-include removes the ID from the exclusion set and returns the item to its normal Missing group.
- Both transitions make the draft dirty and persist across Save/reload.
- Excluding an issue must not make the score regress merely because it left the active penalty set.

## 9.4 Score resolution and ownership

The client accepts the first valid numeric source in this order:

1. `scan_score.score`
2. `score_preview.projected_score_points`
3. `score_preview.projected_score`
4. `score_preview.original_score_points`
5. `score_preview.original_score`

Null, undefined, blank, or invalid values are not coerced to zero. Scan/exclusion resolution and backend score preview own the Optimization score. Annotation acceptance/progress renderers do not write that score, so it remains stable across reload and tab changes.

## 9.5 Dirty state and Save

The persistence signature contains exactly five user-state classes: selected patch candidate IDs, rewrite review decisions, manual bullet edits, excluded Scan issue IDs, and personal details.

Persisted state is applied before the hydrated signature is established. An unchanged review is clean, Save is disabled, and its tooltip says `No changes made`. A changed review enables Save with `Save changes`; the loading label is `Saving...`.

Save persists without navigating or opening the Continue modal. The helper `continueScanWorkspaceAfterReview()` exists but is not bound to the current toolbar Save action. Failed writes remain dirty/retryable.

## 9.6 Persistence verification and navigation identity

Tailoring-to-Scan and Scan-to-Tailoring navigation carry `pipeline_run_id`. Artifact load/save resolves the run against the authenticated owner; older URLs with `output_dir` but no explicit run ID use recorded owner pipeline runs rather than trusting arbitrary path components.

Saved-scan updates use owner-scoped `UPDATE ... RETURNING`, and the service verifies returned exclusion/draft state before acknowledging success. A failed or unverified write does not advance the saved signature.

## 9.7 Compare and export

Compare is a read-only reconstruction of the export model. PDF and DOCX export use the workspace-draft generation path. Export is blocked while the draft is dirty and instructs the user to Save first. The toolbar uses the custom wrapper-owned tooltip only; it must not also expose a native `title` tooltip or an empty tooltip shell.

---

# 10. Application decisions and execution boundary

## 10.1 User-facing state

- `/decisions-ui` presents recorded decisions, selected resume context, and manual next steps.
- `/applications` reads latest `APPLIED` and `SAVED` jobs and supports search/sort/pagination.
- `POST /application-actions` appends owner-scoped action history.
- Allowed statuses are `OPENED`, `APPLIED`, `SAVED`, `NOT_APPLIED`, and `DISMISSED`.
- `src/storage/operator_decisions/` and `src/storage/application_actions/` are separate persistence domains.

## 10.2 Queue does not mean submission

`application_execution_queue.py` produces queue CSVs, recommendations, review/readiness payloads, guarded request artifacts, simulations, and preflight/observability information. A readiness decision can report that prerequisites passed, but `application_submission_enabled`, live execution, mutation, and the automatic submission loop remain false. It does not submit applications to ATS sites.

The manual guarded APIs under `/api/manual-*` implement previews, request records, transitions, readback, or simulations. Their existence is not live application authority.

---

# 11. Web application, identity, and routes

## 11.1 Backend composition

- `src/app/api.py` creates FastAPI, mounts static assets, registers APIs, defines current API request models, starts background RAG warmup, and applies authentication guards.
- `src/app/services.py` is the shared service layer for pipelines, planning, Scan, artifacts, profile state, RAG, scheduler readbacks, and guarded agent operations.
- `src/app/ui.py` and `src/app/ui_shell.py` own core pages and shell/navigation.
- `auth_ui.py`, `onboarding_ui.py`, `profile_ui.py`, `planning_ui.py`, `decisions_ui.py`, and `application_hub_ui.py` own page-specific HTML/routes.

## 11.2 Page routes

| Route | Surface |
|---|---|
| `/` | Overview/executive dashboard |
| `/planning` | Planning Worklist |
| `/pipeline` | Pipeline dashboard |
| `/scheduler` | Scheduler health/operations |
| `/agentic-operations` | Agentic operations dashboard |
| `/advanced-diagnostics` | Advanced diagnostic dashboard |
| `/scan-workspace` | Optimization Review / New Scan |
| `/tailoring-workspace` | Tailoring workspace |
| `/decisions-ui` | Decision review |
| `/applications` | Application hub |
| `/profile` | Profile/resumes |
| `/profile/preferences` | Preference settings |
| `/profile/ai-settings` | Provider/model settings |
| `/profile/saved-scans` | Saved scans |
| `/guide` | Normal-user ApplyLens App Guide |
| `/profile/pipeline-runs/{run_id}/agentic-review` | Run-scoped agentic review |
| `/onboarding` | Onboarding |
| `/login`, `/register` | Authentication |
| `/admin/registration-requests` | Admin registration approval |

The visible primary shell navigation is narrower: Overview, Planning, Decisions, Applications, and Pipeline. Other surfaces remain reachable through profile/operations flows. Protected browser routes redirect to login; protected JSON APIs return authentication failures.

## 11.3 Important API families

- health/status and pipeline launch;
- scheduler command/config/status/history/storage/summary and manual discovery run-now;
- notification list/summary/read/delete;
- browse/review/workflow/planner/planning-artifact;
- Scan preload/start/saved state/delete;
- resume upload/extraction/preview and resume selection/regeneration;
- Bulk start/status/results/run/stop;
- patch selection and workspace draft load/save/preview/render/export;
- application actions and applied/saved job views;
- RAG search, lightweight job search, assistant query, and grounded answer;
- profile resumes/mappings, onboarding preferences, AI settings/credentials/routes;
- admin user access and agentic overview;
- pipeline run detail, artifacts, traces, review data, and rerun;
- explicit manual/default-off agent, approval, vector-evidence, and canary readbacks.

## 11.4 Auth, onboarding, and profile

`src/auth/` owns password, session, approval-email, and authentication runtime support; `src/storage/auth/` owns users, sessions, and registration requests. Registration is approval-gated through the admin flow.

Onboarding completion requires at least one selected role family and one profile resume. Preferences include role families, seniority rules, locations/fallback, preferred skills, and exclusions. Profile manages PDF resumes, role mappings, pipeline runs/artifacts, saved scans, and AI settings.

Authenticated web pipeline launch requires a profile resume. It reserves an active run in PostgreSQL, optionally takes a Redis admission lock when enabled/configured, validates process identity/liveness, bounds argv/environment size, uses a canonical owner/run scratch tree, persists status/artifact references, and reconciles stale/terminal runs.

---

## 11.1 App Guide ownership

`src/app/guide_ui.py` owns the normal-user `/guide` page and its guide content. `src/app/api.py` registers that router. `src/app/ui_shell.py` owns the single global Guide toolbar control and places it immediately before Notifications. Guide-specific presentation and interaction belong to `src/app/static/app_guide.css` and `src/app/static/app_guide.js`; shared shell-control styling remains owned by `src/app/static/app_redesign.css`.

---

# 12. RAG and assistant retrieval

`src/rag/` provides document construction/export, corpus access, lexical and semantic retrieval, query filters, hybrid ranking, diagnostic filtering, answer grounding, and evaluation support.

## 12.1 Active retrieval behavior

- The lexical corpus is read from PostgreSQL `rag_job_documents` through `src/rag/corpus_store.py`.
- PostgreSQL access has Redis read-through caching when `REDIS_URL` is configured, plus matching in-process cache expiry/invalidation.
- Owner chat/search constrains allowed job IDs before evidence reaches the answerer; an empty allowed set fails closed rather than widening to the shared corpus.
- Query metadata filters are inferred and merged with explicit filters.
- Lexical and any semantic results are filtered, deduplicated, merged, ranked, and passed through a retrieval gate.
- Corpus-overview questions can use a bounded sample of at most 12 real postings when per-document term overlap produces no result.

## 12.2 Semantic lane classification

`src/rag/retriever.py` uses the `BAAI/bge-small-en-v1.5` LlamaIndex filesystem index, but that **legacy** semantic lane is disabled by default behind `JOB_STACK_ENABLE_LEGACY_RAG_INDEX`. API startup performs a background warmup attempt; disabled semantic retrieval is treated as unavailable and the query engine falls back to lexical retrieval. PostgreSQL/Redis RAG storage is active, but it is not a production pgvector semantic index in this path.

---

# 13. Provider and model routing

## 13.1 Separate catalogs, qualification, and transport

- `src/ai/provider_model_catalog.py` lists configurable candidates only. It supports Groq and OpenAI; catalog presence is not qualification.
- `src/evaluation/controlled_provider_qualification_registry.py` and frozen recommendation/renderer-bound registries establish reviewed workload qualification.
- `src/app/provider_model_routing_service.py` bridges a qualified recommendation or qualified owner override to an exact runtime pair. It does not rank models or substitute providers.
- `src/ai/user_provider_runtime.py` reads the exact owner credential, builds a fresh provider client, and calls shared transport with fallback disabled.
- `src/ai/llm_client.py` is the shared provider transport and structured-output compatibility layer.

## 13.2 Workload behavior

The routing policy enumerates skill extraction, job-fit evaluation, JD intelligence, grounded RAG answer, resume fallback ranking, ambiguous resume adjudication, critic evaluation, tailoring generation/refinement/judge, manual Scan phrase, and manual provider preview.

A workload status maps to `qualified_provider_model`, `deterministic` for zero qualified options, or `blocked_non_live`. Owner overrides are accepted only when the exact provider/model remains qualified for that workload; otherwise the qualified ApplyLens recommendation is used. A generic preferred provider does not override the workload route.

## 13.3 Credentials and failure rules

User provider credentials are owner scoped and stored as `fernet-v1` ciphertext with rotation-keyring support. APIs return only bounded hints, never plaintext. Missing settings, credentials, qualification, or malformed route state fails closed. Authenticated tailoring has no provider fallback. Ownerless CLI/provider paths are separately controlled by explicit environment names.

Current tailoring generation/refinement/judge snapshot recommendations use Groq `openai/gpt-oss-120b`, but callers should resolve policy rather than hard-code that snapshot identity.

---

# 14. Agent, trace, and evaluation infrastructure

## 14.1 Classification

`src/agents/` is mixed:

- **Active bounded owners/adapters:** company discovery, workflow artifact writers, trace contracts, source-health/relevance trace wrappers, planning recommendation components, and production human-checkpoint/durable orchestration used by explicit guarded flows.
- **Optional/default-off authoritative wrappers:** LangGraph wrappers for deterministic filter/dedupe, JD intelligence, semantic evaluation, final scoring, prioritization, tailoring decision/generation, and operator review. Enablement preserves existing underlying owners and exactly-once contracts.
- **Shadow/advisory:** production shadow graph/sidecar, three-core shadow flow, vector-evidence hooks, evidence-chain composition/execution, and recommendation overlays.
- **Diagnostic/manual:** preview, dry-run, read-only adapter, readiness, canary, approval, and exact-resume-change modules.

Collector flags for authoritative graphs, controlled JD LLM ownership, production telemetry, Himalayas active retention, shadow chains, vector/evidence hooks, and advisory diagnostics default off unless explicitly configured. Default processing remains the direct functions in section 5.

## 14.2 Human and mutation boundaries

Agent recommendations do not silently mutate ranking, resume content, queue state, application state, or ATS state. Approval records, operator decisions, guarded execution requests, and human checkpoint state are separate artifacts/stores. Persisting a human decision does not enable automatic submission.

## 14.3 State, trace, and evaluation

`src/storage/agent_state/`, `agent_trace/`, `agent_feedback/`, `agentic_approvals/`, and `durable_orchestration/` provide schema/store support. Run-scoped trace and evidence-chain readbacks are exposed in profile/agentic review. Trace persistence is observability, not decision authority.

`src/evaluation/` contains benchmarks, metrics, RAG evaluation, provider compatibility, controlled canary transports, production-parity harnesses, reviewed qualification registries, and recommendation policy. These are controlled evidence/policy inputs, not code that runs on every request.

Root `run_controlled_*_dry_run.py`, evidence-shadow, matching-smoke, benchmark, and `analyze_*` scripts are diagnostic/developer tools unless an explicit operational workflow invokes them.

---

# 15. Scheduler and notifications

## 15.1 Scheduler

`src/pipeline/scheduler.py` defines:

| Job | Default launchd interval | Role |
|---|---:|---|
| `agent_discovery` | 86,400 seconds | runs `run_agent_discovery.py` |
| `live_pipeline` | 21,600 seconds | builds a bounded `main.py` command through `job_app.py` |

The scheduler supports command inspection, wrapper execution, run history, PostgreSQL synchronization, and macOS launchd config/install/status/uninstall. The default scheduled live-pipeline command builder is acquisition-only unless explicit options are selected. Global-acquisition mode rejects planning/tailoring and seen-deletion combinations.

The `/scheduler` page is a health/operations surface. The API exposes manual run-now only for `agent_discovery`; normal authenticated pipeline launch remains `POST /pipeline/run`.

Scheduler persistence lives in `src/storage/scheduler/` and `src/storage/scheduler_artifacts_store.py`, not `src/scheduler/`.

## 15.2 Post-run and Notification Center

After a scheduler wrapper run, it attempts to persist a post-run summary, email outbox record, delivery result, and notification artifact. `JOB_STACK_POST_RUN_EMAIL_MODE` supports `outbox_only`, `dry_run`, and `smtp`; default is `outbox_only`. SMTP requires explicit host/from/to settings.

`src/storage/notification_state/` stores owner read/delete state separately. APIs support list, summary/unread count, read-state changes, individual delete, and delete-all; shell code reconciles mutations.

---

# 16. Persistence and caching

## 16.1 Authoritative stores

| Store/path | Data authority |
|---|---|
| `src/storage/auth/` | users, sessions, registration requests |
| `src/storage/profile_resumes/` | owner resume PDF blobs and role mappings |
| `src/storage/onboarding_preferences/` | owner preferences/onboarding state |
| `src/storage/user_ai_settings/` | provider metadata, encrypted credentials, task-model selections |
| `src/storage/user_pipeline/` | runs, active reservations, seen-state staging/promotion, artifacts |
| `src/storage/application_actions/` | append-only application action history |
| `src/storage/operator_decisions/` | operator decisions |
| `src/storage/patch_selections/` | planning patch selections |
| `src/storage/saved_scans/` | owner saved Scan state |
| `src/storage/bulk_generation/` | Bulk runs/items |
| `src/storage/notification_state/` | notification read/delete state |
| `src/storage/scheduler/`, `src/storage/scheduler_artifacts_store.py` | scheduler definitions/history/artifacts |
| `src/storage/rag_store.py` | shared RAG documents and retention |
| `src/storage/discovery_store.py` | companies, targets, crawl state, offsets, detection cache |
| `src/storage/metrics_store.py` | pipeline, ATS, company, source-health metrics |
| `src/storage/skill_db.py`, `src/storage/skill_corpus_store.py` | discovered/extracted skills and LLM caches |
| `src/storage/agent_state/`, `src/storage/agent_trace/`, `src/storage/agent_feedback/` | agent state and observability |
| `src/storage/agentic_approvals/`, `src/storage/durable_orchestration/` | approvals and durable checkpoints |
| `src/storage/vector_evidence/` | guarded pgvector evidence support |

`src/storage/admin_tools/` contains explicit schema/smoke/admin utilities; it is not a normal request-path store.

## 16.2 Cache authority

- `src/cache/description_cache.py` uses PostgreSQL `job_description_cache`.
- `src/utils/job_cache.py` uses `user_pipeline` PostgreSQL seen state when `JOB_STACK_SEEN_JOBS_BACKEND=postgres` and an owner is present; its legacy fallback does not persist.
- `src/storage/rag_store.py` and `src/storage/discovery_store.py` use PostgreSQL as authority with Redis read-through caching/invalidation when configured.
- `src/storage/redis_locks.py` provides optional distributed locking, including user-pipeline admission when enabled.
- Shared RAG documents have a 15-day active retention window.

Redis is optional acceleration/coordination; PostgreSQL remains authoritative. Active runtime does not use historical `job_cache.db` or `description_cache.db` SQLite caches.

## 16.3 Filesystem artifacts

CLI/planning runs can produce CSV, JSON, Markdown, PDF, DOCX, logs, and status files under configured roots. Authenticated runs constrain them to the registered owner/run root and persist artifact references. Workspace drafts are validated JSON siblings of authorized planning artifacts; a path alone is not an identity credential.

---

# 17. Frontend architecture

The UI is hybrid: server-rendered FastAPI HTML, classic JavaScript, and a React 18/TypeScript/Vite bundle. Generated React JS/CSS is committed under `src/app/static/build/executive-kpi/` and must be rebuilt when source changes.

## 17.1 Classic static runtime

- `app.js`, `styles.css`, `app_redesign.css` — base behavior/styles;
- `shell.js` — navigation and Notification Center;
- `planning.js`, `planning_dashboard.css` — Planning bridge/state;
- `scan_workspace.js` and Scan CSS — Scan review/persistence/export;
- `application_views.js`, `decisions.js` — application/decision surfaces;
- `agentic_review.js` and CSS — run-scoped agent review;
- `floating_intelligence_chat.js` — assistant UI;
- onboarding/preference JS/CSS and location selector;
- profile and AI-settings JS/CSS;
- tailoring CSS, media, provider logos, and vendored PDF.js.

`planning.js` spans Planning, Bulk bridging, Tailoring navigation, and Scan support; it is a shared high-risk owner.

## 17.2 React source

`frontend/executive-kpi/src/` contains Analytics Dashboard, Executive Queue, Operational Dashboards, Planning Worklist, Source Yield, Agentic Operations, Advanced Diagnostics, Pipeline, Scheduler Health, filters, table primitives, models, styles, bootstrap, and colocated tests.

Dashboard metrics remain consumers of backend status/metrics contracts; component counters are not backend authority.

---

# 18. Observability, concurrency, configuration, and deployment

## 18.1 Observability

The application records pipeline stage status/counts, acquisition HTTP/outcome/source-health metrics, role/title and source audits, persistent pipeline/ATS/company metrics, provider/cache/parse/retry summaries, Bulk progress/failures, scheduler/delivery/notification records, agent traces/feedback/approvals, and frontend dirty/progress/terminal states.

Do not replace a specific degraded/failure classification with fabricated success or a generic error.

## 18.2 Bounded execution

The project combines `asyncio`, connector/semaphore bounds, thread pools, sequential persisted workers, pagination/profile caps, timeouts, subprocess liveness checks, and job/packet/item ceilings. New concurrency must preserve rate limiting, deterministic identity, admission, and owner/run isolation.

## 18.3 Configuration and deployment

`src/config/` owns constants, settings, role taxonomy/scoring, seniority policy, and source query profiles. Environment variables control database/Redis, owner/run context, providers, timeouts/limits, scheduler delivery, and optional agent features. Names may be documented; secret values must not be.

- `Dockerfile` builds React with Node 22 and runs Python 3.12 with PostgreSQL client/build support.
- `docker-compose.prod.yml` defines PostgreSQL 18, Redis 7 Alpine, and web on loopback port 8000.
- `deploy/env.production.example` is a variable template, not runtime authority or credentials.
- `.dockerignore` and `.gitignore` constrain build/version-control context.

---

# 19. Repository inventory

## 19.1 Runtime source directories

| Path | Classification and contents |
|---|---|
| `models/` | Production job/description models. |
| `src/ai/` | Embeddings, extraction, evaluation, provider transport/catalog, resume matching. |
| `src/app/` | FastAPI, services, pages, Bulk, provider settings, static runtime. |
| `src/auth/` | Authentication runtime. |
| `src/cache/` | PostgreSQL description cache. |
| `src/config/` | Settings, constants, role/seniority policy, query profiles. |
| `src/details/` | Job detail adapters. |
| `src/discovery/` | ATS/domain/career/GitHub/sitemap discovery and crawl logic. |
| `src/intelligence/` | Job/market intelligence, role families, skills. |
| `src/matching/` | Evidence models, prefilter, scorer, semantic/family matching. |
| `src/pipeline/` | Collector, stages, scheduler, retention, post-run, projection, shadow hooks. |
| `src/rag/` | Corpus, retrieval, filtering/ranking, answer/index diagnostics. |
| `src/resume/` | Loading, models, evidence, embeddings. |
| `src/scrapers/` | Eleven active adapters. |
| `src/storage/` | PostgreSQL schemas/repositories and Redis adapters. |
| `src/tailoring/` | Planner, LLM, grounding, selection, rendering, scoring. |
| `src/utils/` | Retry, health, metrics, logging, parallelism, locking, seen/timestamp tools. |

`src/agents/` and `src/evaluation/` are mixed active/internal/default-off/diagnostic packages as classified in section 14.

## 19.2 Root production/operational scripts

| File | Classification |
|---|---|
| `main.py` | Production pipeline CLI. |
| `run_api.py` | Web launcher. |
| `run_application_planning.py` | Planning orchestrator. |
| `run_agent_discovery.py` | Discovery launcher. |
| `job_app.py` | Compatibility/menu/scheduler wrapper. |
| `batch_select_best_resume_variant.py` | Planning resume-selection stage. |
| `application_shortlist_from_batch_selector.py` | Planning shortlist stage. |
| `application_execution_queue.py` | Queue/artifact/readiness stage; no submission. |
| `archive_batch_selector_runtime_fixture.py` | Optional fixture archival helper. |
| `generate_tailoring_suggestions.py` | Tailoring utility. |
| `select_best_resume_variant.py` | Single-selection utility. |
| `manage_himalayas_retention.py` | Retention utility. |

## 19.3 Root developer/analysis utilities

The `analyze_*` scripts, `benchmark_skill_extractors.py`, skill seed generators/merger, `jd_resume_diff_helper.py`, `run_matching_smoke.py`, `run_evidence_chain_shadow.py`, all root controlled/default-off dry-run launchers, and `skill_eval.txt` support analysis, seeds, smoke tests, shadow evidence, or controlled dry runs. They are not web features or default collector stages.

## 19.4 Other top-level families

| Path | Classification |
|---|---|
| `frontend/executive-kpi/` | React runtime source, build config, and tests. |
| `tests/` | Backend/unit/integration/contract/regression tests and fixtures. |
| `docs/` | Architecture, readiness, phase/checkpoint, runbook, and evidence docs. |
| `deploy/` | Deployment example configuration. |
| `archive/` | Deprecated/historical implementations. |
| Docker/Compose/requirements | Runtime/deployment manifests. |
| README/CLAUDE/context | User guidance, agent rules, and this system map. |

Generated caches, virtual environments, local `.env`, `.DS_Store`, build caches, and runtime outputs can exist locally but are not tracked architecture.

---

# 20. Tests, documentation, and archive

The backend suite covers source health, pipeline stages, matching/scoring, selection, tailoring, provider policy, isolation, persistence, Scan, Bulk, scheduler/notifications, agent/read-only contracts, and static integrity. React/Vitest tests live beside components.

Phase-numbered/hash-guard tests can preserve historical compatibility or readiness constraints. Read their assertions and active call sites before treating a phase name as a feature. Do not put transient pass counts or stale expected-hash incidents here.

`README.md` is the user/developer entry point; `CLAUDE.md` contains working rules; `docs/architecture_summary.md` is supporting context. Other `docs/` phase/checkpoint/readiness files are evidence/history, not runtime owners.

`archive/job_intelligence_improved.py` and `archive/skill_llm_enricher_regex.py` are deprecated/historical. Current code uses active `src/intelligence/` and `src/ai/` owners.

---

# 21. Ownership lookup and maintenance rules

| Change area | Inspect first |
|---|---|
| Acquisition | `src/scrapers/`, `src/details/`, `src/pipeline/collector.py` |
| Discovery | `run_agent_discovery.py`, `src/discovery/`, discovery stage/store |
| Filter/dedupe/rank | `job_filter.py`, `dedupe.py`, `job_ranker.py`, preferences |
| Seen/description cache | `src/utils/job_cache.py`, `src/cache/description_cache.py`, `src/storage/user_pipeline/` |
| JD intelligence | intelligence owner, JD contract, extraction modules |
| Resume evidence/selection | `src/resume/`, selector scripts, credibility module |
| Final score | `src/pipeline/application_scorer.py` |
| Planning | orchestrator plus selector/shortlist/queue stages |
| Tailoring | `src/tailoring/`, tailoring generator utility |
| Bulk | Bulk service/worker/store/API and Planning frontend |
| Scan | planning UI/services/static and saved-scan/workspace stores |
| Applications | application/decision UI and action/decision stores |
| Auth/profile/onboarding | auth/app modules and relevant stores |
| Provider routing | catalog, qualification registries/policy, routing service, user runtime/store |
| RAG | `src/rag/`, `src/storage/rag_store.py`, RAG APIs/services |
| Scheduler/notifications | pipeline scheduler/post-run modules and stores/shell |
| Agents/traces | `src/agents/`, actual call site, stores, evaluation policy |
| Frontend dashboards | React source and generated static build |
| Deployment | Docker/Compose, `deploy/`, settings, requirements |

Before changing behavior, identify the active call site, authoritative state owner, enablement/default, identity boundary, and existing tests. Extend the existing path rather than creating a parallel executor, store, score, or provider route.

After a material change:

1. update the affected section here;
2. remove obsolete statements instead of appending contradictory history;
3. keep default-off, diagnostic, and archived code visibly classified;
4. update the audited branch/commit only when intentionally resynchronizing the whole document;
5. never describe a planned or checkpoint-only feature as active;
6. never include credentials or secret configuration values.
