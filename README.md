# ApplyLens AI

<p align="center">
  <strong>AI-powered job discovery, application planning, resume scanning, and tailoring workspace.</strong>
</p>

<p align="center">
  Scrape jobs from modern ATS platforms, rank opportunities against saved resumes, review AI optimization guidance, generate tailored drafts, and track the full application workflow from one local operator app.
</p>

---

## Table of Contents

- [What This App Does](#what-this-app-does)
- [Core Workflows](#core-workflows)
- [Dashboard Pages](#dashboard-pages)
- [Pipeline Capabilities](#pipeline-capabilities)
- [AI Optimize Scan](#ai-optimize-scan)
- [Resume Tailoring Workspace](#resume-tailoring-workspace)
- [Scheduler Operations](#scheduler-operations)
- [Storage and Persistence](#storage-and-persistence)
- [Supported ATS Sources](#supported-ats-sources)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
- [Running the App](#running-the-app)
- [Running Pipelines from the CLI](#running-pipelines-from-the-cli)
- [Environment Variables](#environment-variables)
- [Testing and Validation](#testing-and-validation)
- [Portfolio and Demo Docs](#portfolio-and-demo-docs)
- [Deployment Notes](#deployment-notes)
- [Roadmap Ideas](#roadmap-ideas)

---

## What This App Does

ApplyLens AI is a job-search operating system for serious application workflows. It combines job scraping, resume intelligence, AI-assisted review, and decision tracking into a single FastAPI web application.

The app is designed around a practical application loop:

1. Discover and scrape jobs from multiple ATS platforms.
2. Filter, deduplicate, and rank jobs against your saved resume corpus.
3. Review recommended opportunities in dashboards.
4. Run an AI Optimize Scan for any target role.
5. Compare resume content against job requirements.
6. Accept, reject, or manually edit AI suggestions.
7. Export polished resume drafts.
8. Track application decisions, pipeline runs, and saved scans.

The project can run locally for development, or as a Dockerized web service with PostgreSQL and Redis.

---

## Core Workflows

### 1. Job Discovery and Collection

The pipeline discovers companies and job boards, then scrapes jobs from supported ATS providers. It handles common ATS-specific differences through dedicated scraper modules.

High-level flow:

```text
Company discovery
  -> ATS-specific scraping
  -> job normalization
  -> location/title/freshness filtering
  -> deduplication
  -> seen-job filtering
  -> job corpus export
  -> application planning
```

### 2. Application Planning

Application planning takes the current job corpus and creates operator-friendly outputs:

- Ranked application shortlist.
- Best resume variant per job.
- Runner-up and close-call review queues.
- Direct-apply, maybe-tailor, and skip decisions.
- Planning artifacts for dashboards.
- Optional LLM-powered tailoring suggestions.

### 3. AI Optimize Scan

The scan workspace lets you paste a job description, choose a saved resume, and generate a structured review:

- Personal details review.
- Skill match analysis.
- Searchability checks.
- ATS formatting checks.
- Recruiter-review suggestions.
- Resume preview with clickable AI annotations.
- Accept, reject, manual edit, compare, export, and continue flows.

### 4. Tailoring and Export

The tailoring workspace turns scan guidance into editable resume drafts. You can inspect AI suggestions, generate phrase alternatives, save decisions, and export the final draft as PDF or DOCX.

---

## Dashboard Pages

The web app uses a shared navigation shell with these main pages:

| Page | Route | Purpose |
| --- | --- | --- |
| Executive | `/` | High-level operator dashboard for live pipeline runs and current opportunities. |
| Planning | `/planning` | Application planning table, shortlist, resume selection, and tailoring entry points. |
| Decisions | `/decisions-ui` | Review and manage operator decisions for jobs and resume variants. |
| Intelligence | `/intelligence` | Job and skill intelligence surfaces backed by local artifacts and RAG tools. |
| Applications | `/applications` | Application/action tracking workspace. |
| Scheduler | `/scheduler` | Scheduler health, command previews, launchd configuration, and run history. |
| Profile | `/profile` | Saved resumes, pipeline runs, saved scans, and account/admin tools. |
| Saved Scans | `/profile/saved-scans` | Review previously generated AI Optimize Scan records. |
| Login/Register | `/login`, `/register` | Local authentication and optional registration approval workflow. |

---

## Pipeline Capabilities

### Job Scraping

The main scraping pipeline is driven by `main.py` and the modules under `src/pipeline` and `src/scrapers`.

It supports:

- ATS-specific scraping.
- Parallel collection where supported.
- Job normalization into consistent records.
- Location and title filtering.
- Freshness checks.
- Deduplication.
- Seen-job state to avoid reprocessing old listings.
- Export of current-run job corpus artifacts.

### Application Planning

Application planning is driven by `run_application_planning.py` and helper modules under `src/tailoring`, `src/ai`, `src/rag`, and `src/storage`.

It supports:

- Resume-to-job matching.
- Skill extraction and enrichment.
- Best-resume selection.
- Application priority scoring.
- Manual review queues.
- Patch candidate generation.
- Tailoring packet generation.
- LLM fallback/adjudication modes where configured.

### Local RAG

The app includes a local retrieval layer for job search and question answering:

- Job corpus indexing.
- Lexical and semantic retrieval.
- Compact or full answer modes.
- Optional legacy RAG index support.

CLI access is available through:

```bash
python job_app.py rag "show data scientist roles with strong Python requirements"
```

---

## AI Optimize Scan

The AI Optimize Scan workspace is one of the central product surfaces.

### New Scan Flow

From `/scan-workspace`, the user can:

- Select a saved profile resume.
- Enter company, role, posting URL, and job description.
- Start a scan.
- Review a generated optimization report.
- Save the scan record.
- Re-scan the same saved scan after editing the inputs.

### Review Flow

The generated review includes:

- Score summary.
- Matched count.
- Missing count.
- AI-generated suggestions count.
- Resume preview.
- Job description preview.
- Accepted/rejected/manual-edit comparison.
- Export controls.

### Suggestion Handling

Resume annotations can be opened directly from the preview. The suggestion popover supports:

- Inspecting matched or missing signals.
- Editing the draft bullet.
- Generating LLM phrase options.
- Choosing a phrase alternative.
- Reverting edits.
- Saving edits for rescoring.

### Re-Scan

Saved New Scan reviews include a `Re-scan` action. It reopens the New Scan form with the previous scan inputs prefilled, then updates the same saved scan record when submitted.

This is useful when:

- The job description changed.
- The role title needs correction.
- A different saved resume should be tested.
- You want to regenerate guidance without creating a duplicate scan.

---

## Resume Tailoring Workspace

The tailoring workspace is available from planning rows and scan review flows.

It provides:

- Split-pane resume and guidance review.
- Personal details editing.
- Skill and searchability review tabs.
- Formatting checks.
- Recruiter tips.
- Accept/reject/manual edit decisions.
- Live draft rendering.
- PDF and DOCX export.
- Saved workspace drafts.

The workspace is designed to preserve the source resume structure while applying targeted, reviewable changes.

---

## Scheduler Operations

The scheduler wrapper lives in `src/pipeline/scheduler.py`.

Currently supported scheduled jobs:

| Job | What it runs |
| --- | --- |
| `agent_discovery` | `python -u run_agent_discovery.py` |
| `live_pipeline` | `python -u main.py --run-application-planning ...` |

The scheduler layer supports:

- Command generation.
- Launchd plist generation for macOS.
- Launchd install/uninstall/status helpers.
- JSONL run history.
- Optional Postgres run-history sync.
- Post-run summary artifacts.
- Post-run email outbox artifacts.
- Notification records.

Useful endpoints:

```text
GET /scheduler/jobs
GET /scheduler/command
GET /scheduler/launchd-config
GET /scheduler/launchd-agent-status
GET /scheduler/history
GET /scheduler/summary
```

Example command preview:

```bash
python -m src.pipeline.scheduler --job live_pipeline --print-only
```

---

## Storage and Persistence

The app can operate with local files and also includes Postgres-backed stores for production-style persistence.

Major storage areas:

| Area | Purpose |
| --- | --- |
| `outputs/application_planning` | Active planning artifacts and generated outputs. |
| `outputs/_archive` | Archived planning outputs. |
| `data/scheduler_run_history.jsonl` | Scheduler run audit trail. |
| `data/*_companies.txt` | Discovered ATS company lists. |
| `tmp/pipeline_runs` | Pipeline scratch/run workspace. |
| PostgreSQL | Users, sessions, profile resumes, saved scans, decisions, actions, scheduler artifacts, notification state. |
| Redis | Optional cache and admission/lock support. |

Postgres schemas live under `src/storage/**/schema.sql`.

---

## Supported ATS Sources

The scraper layer includes dedicated modules for:

| ATS | Scraper |
| --- | --- |
| Greenhouse | `src/scrapers/greenhouse_scraper.py` |
| Lever | `src/scrapers/lever_scraper.py` |
| Workday | `src/scrapers/workday_scraper.py` |
| Ashby | `src/scrapers/ashby_scraper.py` |
| Workable | `src/scrapers/workable_scraper.py` |
| Jobvite | `src/scrapers/jobvite_scraper.py` |
| SmartRecruiters | `src/scrapers/smartrecruiters_scraper.py` |

Discovery helpers live under `src/discovery` and include ATS detection, sitemap discovery, GitHub discovery, learned company expansion, and SmartRecruiters/Greenhouse-specific discovery paths.

---

## Project Structure

```text
.
├── main.py                         # Main scraping pipeline entry point
├── job_app.py                      # Operator CLI for pipeline/planning/RAG workflows
├── run_api.py                      # FastAPI/uvicorn launcher
├── run_application_planning.py     # Application planning pipeline
├── run_agent_discovery.py          # Standalone company discovery agent
├── src/
│   ├── app/                        # FastAPI routes, page templates, services, static UI
│   ├── ai/                         # LLM clients, skill extraction, job-fit evaluation
│   ├── auth/                       # Auth, sessions, registration approval
│   ├── discovery/                  # Company and ATS discovery
│   ├── details/                    # ATS job detail fetchers
│   ├── pipeline/                   # Collector, scheduler, scoring, post-run artifacts
│   ├── rag/                        # Retrieval and job corpus question answering
│   ├── resume/                     # Resume loading, embeddings, evidence helpers
│   ├── scrapers/                   # ATS-specific scrapers
│   ├── storage/                    # Local/Postgres stores and schemas
│   ├── tailoring/                  # Tailoring planner, rendering, selection logic
│   └── utils/                      # Shared utilities
├── tests/                          # Regression and smoke tests
├── deploy/                         # Production environment examples
├── Dockerfile
├── docker-compose.prod.yml
└── requirements.txt
```

---

## Local Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Create environment configuration

Create a `.env` file in the repo root. At minimum, configure the LLM provider keys you plan to use.

Common options:

```bash
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=...

# Optional alternatives/fallbacks
OPENAI_API_KEY=...
GEMINI_API_KEY=...
LLM_FALLBACK_ENABLED=false
LLM_FALLBACK_PROVIDER=gemini
LLM_FALLBACK_MODEL=gemini-2.5-flash

# Optional production persistence
DATABASE_URL=postgresql://user:password@localhost:5432/job_scraper_ops
REDIS_URL=redis://localhost:6379/0
```

### 4. Start the web app

```bash
python run_api.py --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

---

## Running the App

### Web UI

```bash
python run_api.py --reload
```

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

### Main Pipeline

```bash
python main.py --run-application-planning
```

### Planning-Only Run

Use this when you already have a job corpus and want to regenerate planning outputs without scraping again.

```bash
python main.py \
  --application-planning-only \
  --run-application-planning \
  --application-planning-output-dir outputs/application_planning
```

---

## Running Pipelines from the CLI

`job_app.py` provides a compact operator CLI.

### Run scrape + planning

```bash
python job_app.py run --run-application-planning
```

### Run planning only

```bash
python job_app.py plan --job-limit 50
```

### Check output status

```bash
python job_app.py status
```

### Browse planning rows

```bash
python job_app.py browse --limit 20
```

### Review close calls

```bash
python job_app.py review --undecided-only true
```

### Record a resume decision

```bash
python job_app.py decide \
  --queue-rank 1 \
  --selected-resume "My Resume.pdf" \
  --note "Best match for senior ML role"
```

### Ask the local RAG layer

```bash
python job_app.py rag "Which roles mention Kubernetes and ML infrastructure?"
```

---

## Environment Variables

The project supports many optional settings. The most commonly useful ones are below.

### LLM and AI

| Variable | Purpose |
| --- | --- |
| `LLM_PROVIDER` | Default provider for general LLM calls. |
| `LLM_MODEL` | Default model for general LLM calls. |
| `GROQ_API_KEY` | Groq API key. |
| `OPENAI_API_KEY` | OpenAI API key. |
| `GEMINI_API_KEY` | Gemini API key. |
| `LLM_FALLBACK_ENABLED` | Enables provider fallback. |
| `SKILL_EXTRACTION_BACKEND` | Skill extraction backend selection. |
| `EVAL_MODE` | Job-fit evaluation mode. |
| `LLM_TAILOR_PROVIDER` | Provider for tailoring generation. |
| `LLM_TAILOR_MODEL` | Model for tailoring generation. |
| `SCAN_PHRASE_PROVIDER` | Provider for scan phrase generation. |
| `SCAN_PHRASE_MODEL` | Model for scan phrase generation. |

### Persistence

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Enables Postgres-backed stores. |
| `REDIS_URL` | Enables Redis cache/locks where supported. |
| `JOB_STACK_SEEN_JOBS_BACKEND` | Set to `postgres` for Postgres-backed seen-job state. |
| `JOB_STACK_OWNER_USER_ID` | Owner/user scope for user-specific pipeline data. |
| `JOB_STACK_USER_PIPELINE_MODE` | Enables user-scoped pipeline behavior. |

### Auth

| Variable | Purpose |
| --- | --- |
| `JOB_STACK_AUTH_ENABLED` | Enable or disable auth guard. |
| `JOB_STACK_AUTH_COOKIE_SECURE` | Secure cookie setting. |
| `JOB_STACK_AUTH_COOKIE_SAMESITE` | SameSite cookie setting. |
| `JOB_STACK_AUTH_REGISTRATION_ENABLED` | Enable registration page flow. |
| `JOB_STACK_AUTH_REGISTRATION_APPROVAL_REQUIRED` | Require admin approval for new registrations. |
| `JOB_STACK_AUTH_FIRST_USER_ADMIN_ENABLED` | Make the first user an admin. |

### Scheduler and Notifications

| Variable | Purpose |
| --- | --- |
| `JOB_STACK_POST_RUN_EMAIL_MODE` | Email delivery mode, usually `outbox_only` or SMTP-backed. |
| `JOB_STACK_POST_RUN_EMAIL_SMTP_HOST` | SMTP host. |
| `JOB_STACK_POST_RUN_EMAIL_SMTP_PORT` | SMTP port. |
| `JOB_STACK_POST_RUN_EMAIL_SMTP_USERNAME` | SMTP username. |
| `JOB_STACK_POST_RUN_EMAIL_SMTP_PASSWORD` | SMTP password. |
| `JOB_STACK_POST_RUN_EMAIL_FROM` | From address for post-run email. |
| `JOB_STACK_POST_RUN_EMAIL_TO` | Recipient list. |

See `deploy/env.production.example` for a production-oriented starter file.

---

## Testing and Validation

Useful checks:

```bash
python3 -m py_compile src/app/services.py src/app/planning_ui.py src/app/api.py
node --check src/app/static/planning.js
node --check src/app/static/scan_workspace.js
```

Run the available Python tests:

```bash
pytest
```

Run matching smoke tests:

```bash
python run_matching_smoke.py
```

---

## Portfolio and Demo Docs

For a recruiter- or hiring-manager-friendly view of the agentic system:

- [Portfolio overview](docs/portfolio_overview.md)
- [Architecture summary](docs/architecture_summary.md)
- [Demo walkthrough](docs/demo_walkthrough.md)
- [Manual read-only chain smoke demo](docs/read_only_chain_smoke.md)
- [Read-only chain operator runbook](docs/read_only_chain_operator_runbook.md)
- [Live orchestration readiness gap analysis](docs/live_orchestration_readiness_gap_analysis.md)
- [Production execution contract design](docs/production_execution_contract_design.md)
- [Mutation policy and approval gate design](docs/mutation_policy_approval_gate_design.md)
- [Live-run audit ledger schema design](docs/live_run_audit_ledger_schema_design.md)
- [Idempotency and locking design](docs/idempotency_locking_design.md)
- [Dry-run execution simulator](docs/dry_run_execution_simulator.md)
- [Controlled execution decision gate](docs/controlled_execution_decision_gate.md)
- [Proposal-only mutation planner](docs/proposal_only_mutation_planner.md)
- [Proposal planner release safety checkpoint](docs/proposal_planner_release_safety_checkpoint.md)
- [Storage design review for audit ledger, idempotency, and locks](docs/storage_design_review_audit_idempotency_locks.md)
- [Transaction boundary design](docs/transaction_boundary_design.md)
- [Failure-mode test plan](docs/failure_mode_test_plan.md)
- [Storage schema proposal](docs/storage_schema_proposal.md)
- [Storage schema release safety checkpoint](docs/storage_schema_release_safety_checkpoint.md)
- [Storage transaction failure fixture design](docs/storage_transaction_failure_fixture_design.md)
- [Storage transaction fixture release safety checkpoint](docs/storage_transaction_fixture_release_safety_checkpoint.md)
- [Fixture validator contract design](docs/fixture_validator_contract_design.md)
- [Fixture validator contract release safety checkpoint](docs/fixture_validator_contract_release_safety_checkpoint.md)
- [Fixture naming and reason-code taxonomy checkpoint](docs/fixture_naming_reason_code_taxonomy_checkpoint.md)
- [Fixture naming and reason-code taxonomy release safety checkpoint](docs/fixture_naming_reason_code_taxonomy_release_safety_checkpoint.md)
- [Fixture implementation plan](docs/fixture_implementation_plan.md)
- [Fixture implementation plan release safety checkpoint](docs/fixture_implementation_plan_release_safety_checkpoint.md)
- [Fixture directory skeleton design](docs/fixture_directory_skeleton_design.md)
- [Fixture directory skeleton release safety checkpoint](docs/fixture_directory_skeleton_release_safety_checkpoint.md)
- [Fixture directory creation implementation plan](docs/fixture_directory_creation_implementation_plan.md)
- [Fixture directory creation implementation plan release safety checkpoint](docs/fixture_directory_creation_implementation_plan_release_safety_checkpoint.md)
- [Fixture directory creation implementation](docs/fixture_directory_creation_implementation.md)
- [Fixture directory creation implementation release safety checkpoint](docs/fixture_directory_creation_implementation_release_safety_checkpoint.md)
- [Fixture file implementation plan](docs/fixture_file_implementation_plan.md)
- [Fixture file implementation plan release safety checkpoint](docs/fixture_file_implementation_plan_release_safety_checkpoint.md)
- [First synthetic fixture payload implementation](docs/first_synthetic_fixture_payload_implementation.md)
- [First synthetic fixture payload implementation release safety checkpoint](docs/first_synthetic_fixture_payload_implementation_release_safety_checkpoint.md)
- [Minimal fixture validator module implementation](docs/minimal_fixture_validator_module_implementation.md)
- [Minimal fixture validator module implementation release safety checkpoint](docs/minimal_fixture_validator_module_implementation_release_safety_checkpoint.md)
- [Minimal fixture validator CLI implementation](docs/minimal_fixture_validator_cli_implementation.md)
- [Minimal fixture validator CLI implementation release safety checkpoint](docs/minimal_fixture_validator_cli_implementation_release_safety_checkpoint.md)
- [Runtime fixture validator integration design](docs/runtime_fixture_validator_integration_design.md)
- [Runtime fixture validator integration design release safety checkpoint](docs/runtime_fixture_validator_integration_design_release_safety_checkpoint.md)
- [Second synthetic fixture payload implementation](docs/second_synthetic_fixture_payload_implementation.md)
- [Second synthetic fixture payload implementation release safety checkpoint](docs/second_synthetic_fixture_payload_implementation_release_safety_checkpoint.md)
- [Third synthetic fixture payload implementation plan](docs/third_synthetic_fixture_payload_implementation_plan.md)
- [Third synthetic fixture payload implementation plan release safety checkpoint](docs/third_synthetic_fixture_payload_implementation_plan_release_safety_checkpoint.md)
- [Blocked application-submission fixture readiness check](docs/blocked_application_submission_fixture_readiness_check.md)
- [Blocked application-submission fixture implementation](docs/blocked_application_submission_fixture_implementation.md)
- [Blocked application-submission fixture implementation release safety checkpoint](docs/blocked_application_submission_fixture_implementation_release_safety_checkpoint.md)
- [Preflight fixture validator integration](docs/preflight_fixture_validator_integration.md)
- [Benchmark fixture validator integration](docs/benchmark_fixture_validator_integration.md)
- [Benchmark fixture validator integration release safety checkpoint](docs/benchmark_fixture_validator_integration_release_safety_checkpoint.md)
- [Workflow-runner fixture validation blocking gate design](docs/workflow_runner_fixture_validation_blocking_gate_design.md)
- [Workflow-runner fixture validation blocking gate implementation](docs/workflow_runner_fixture_validation_blocking_gate_implementation.md)
- [Workflow-runner fixture validation blocking gate release safety checkpoint](docs/workflow_runner_fixture_validation_blocking_gate_release_safety_checkpoint.md)
- [Fixture validation failure-mode test design](docs/fixture_validation_failure_mode_test_design.md)
- [Fixture validation failure-mode test implementation](docs/fixture_validation_failure_mode_test_implementation.md)
- [Fixture validation failure-mode tests release safety checkpoint](docs/fixture_validation_failure_mode_tests_release_safety_checkpoint.md)
- [App-service safety gate design](docs/app_service_safety_gate_design.md)
- [App-service safety gate implementation](docs/app_service_safety_gate_implementation.md)
- [App-service safety gate release safety checkpoint](docs/app_service_safety_gate_release_safety_checkpoint.md)
- [Queue safety gate design](docs/queue_safety_gate_design.md)
- [Queue safety gate implementation](docs/queue_safety_gate_implementation.md)
- [Queue safety gate release safety checkpoint](docs/queue_safety_gate_release_safety_checkpoint.md)
- [Runtime safety roadmap review](docs/runtime_safety_roadmap_review.md)
- [Approval API/storage design](docs/approval_api_storage_design.md)
- [Approval storage schema design](docs/approval_storage_schema_design.md)
- [Approval storage schema release safety checkpoint](docs/approval_storage_schema_release_safety_checkpoint.md)
- [Physical approval storage schema design](docs/physical_approval_storage_schema_design.md)
- [Physical approval storage schema release safety checkpoint](docs/physical_approval_storage_schema_release_safety_checkpoint.md)
- [Approval migration design](docs/approval_migration_design.md)
- [Approval migration design release safety checkpoint](docs/approval_migration_design_release_safety_checkpoint.md)
- [Approval SQL DDL design](docs/approval_sql_ddl_design.md)
- [Approval SQL DDL design release safety checkpoint](docs/approval_sql_ddl_design_release_safety_checkpoint.md)
- [Approval SQL DDL implementation readiness review](docs/approval_sql_ddl_implementation_readiness_review.md)
- [Approval SQL DDL file path and content proposal](docs/approval_sql_ddl_file_path_content_proposal.md)
- [Approval SQL DDL file implementation safety checkpoint](docs/approval_sql_ddl_file_implementation_safety_checkpoint.md)
- [Approval SQL DDL static artifact](src/storage/agentic_approvals/schema.sql)
- [Approval SQL DDL file implementation final release checkpoint](docs/approval_sql_ddl_file_implementation_final_release_checkpoint.md)
- [Approval storage API design](docs/approval_storage_api_design.md)
- [Approval storage API design release safety checkpoint](docs/approval_storage_api_design_release_safety_checkpoint.md)
- [Approval storage API implementation readiness review](docs/approval_storage_api_implementation_readiness_review.md)
- [Approval storage API module path and function contract proposal](docs/approval_storage_api_module_path_function_contract_proposal.md)
- [Approval storage API implementation safety checkpoint](docs/approval_storage_api_implementation_safety_checkpoint.md)
- [Approval storage API implementation module only](docs/approval_storage_api_implementation_module_only.md)
- [Approval storage API implementation release safety checkpoint](docs/approval_storage_api_implementation_release_safety_checkpoint.md)
- [Approval storage API application integration readiness review](docs/approval_storage_api_application_integration_readiness_review.md)
- [Fixture validator implementation plan](docs/fixture_validator_implementation_plan.md)
- [Fixture validator implementation plan release safety checkpoint](docs/fixture_validator_implementation_plan_release_safety_checkpoint.md)
- [Fixture validator implementation design refinement](docs/fixture_validator_implementation_design_refinement.md)
- [Fixture validator implementation design refinement release safety checkpoint](docs/fixture_validator_implementation_design_refinement_release_safety_checkpoint.md)
- [Fixture validator implementation approval gate design](docs/fixture_validator_implementation_approval_gate_design.md)
- [Fixture validator implementation approval gate design release safety checkpoint](docs/fixture_validator_implementation_approval_gate_design_release_safety_checkpoint.md)
- [Fixture validator implementation readiness matrix](docs/fixture_validator_implementation_readiness_matrix.md)
- [Fixture validator implementation readiness matrix release safety checkpoint](docs/fixture_validator_implementation_readiness_matrix_release_safety_checkpoint.md)
- [Agentic platform runbook](docs/agentic_platform.md)

These docs distinguish implemented features from future roadmap items and document the dry-run, diagnostic, and no production decision mutation guarantees.

Agentic Review can display dry-run execution simulation artifacts and an Operator Approval Mock as read-only diagnostics only; the mock does not approve, reject, store approval, mutate queues, write to the database, submit applications, or execute anything.

---

## Deployment Notes

The repo includes a production-style Docker setup:

```bash
cp deploy/env.production.example .env.production
docker compose -f docker-compose.prod.yml up --build
```

The compose file starts:

- PostgreSQL
- Redis
- FastAPI web app

The web service is exposed on:

```text
127.0.0.1:8000
```

For a real deployment, set strong credentials, secure cookie settings, and the public base URL in `.env.production`.

---

## Roadmap Ideas

Potential next improvements:

- More ATS adapters and richer job detail extraction.
- In-app scheduler installation controls.
- More detailed pipeline observability.
- Better scan-to-application workflow automation.
- More granular resume version history.
- Team/shared workspace support.
- Expanded test coverage for UI state transitions and scan regeneration.

---

## Notes

This repository is built as an operator-first system: deterministic pipelines where possible, LLM assistance where useful, and reviewable user decisions before important resume/application changes are committed.
