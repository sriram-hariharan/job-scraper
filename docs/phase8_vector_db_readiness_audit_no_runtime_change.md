# Phase 8A vector database readiness audit — no runtime change

## Phase boundary

Phase 8A is a docs/test-only readiness audit. It makes no runtime change, adds no dependencies, and makes no schema change. It does not add a vector database, vector extension, embedding runtime, provider call, pipeline integration, API route, service behavior, UI, scoring behavior, ranking behavior, queue behavior, execution behavior, or submission behavior.

This phase does not add pgvector, Pinecone, Chroma, FAISS, LangChain, or LangGraph. It does not modify `src/`, `requirements.txt`, SQL, migrations, or dependency manifests. Every backend, flag, chunk, metadata field, and migration step below is a future design proposal rather than an active implementation.

## Files and directories inspected

The readiness audit inspected these existing repository areas:

- `src/pipeline/collector.py`
- `src/pipeline/embedding_prefilter.py`
- `src/pipeline/application_scorer.py`
- `src/pipeline/job_ranker.py`
- `src/agents/`
- `src/agents/relevance_prefilter.py`
- `src/agents/jd_intelligence.py`
- `src/agents/resume_match_agent.py`
- `src/agents/tailoring_decision_agent.py`
- `src/agents/critic_agent.py`
- `src/agents/final_application_scoring.py`
- `src/agents/trace.py`
- `src/agents/shadow_sidecar_trace_persistence.py`
- `src/agents/shadow_sidecar_trace_readback.py`
- `src/agents/agent_recommendation_overlay.py`
- `src/agents/agent_recommendation_overlay_readback.py`
- `src/agents/pipeline_agent_review_packet.py`
- `src/storage/`
- `src/storage/rag_store.py`
- `src/storage/agent_trace/store.py`
- `src/storage/agent_trace/schema.sql`
- `src/storage/profile_resumes/store.py`
- `src/storage/profile_resumes/schema.sql`
- `requirements.txt`
- existing Phase 7 overlay/readback/review packet tests, including `tests/test_agent_recommendation_overlay_readonly.py`, `tests/test_pipeline_generated_agent_recommendation_overlay_readback_readonly.py`, `tests/test_pipeline_agent_review_packet_readonly.py`, and `tests/test_review_packet_preview_dry_run_no_pipeline_change.py`
- `tests/test_portfolio_demo_readiness_wrap_checkpoint.py`

## Existing evidence sources that could become vector chunks

The repository already contains evidence-bearing structures that could be copied into a future, separately approved vector index:

- Job corpus documents in `src/storage/rag_store.py`, with stable merge keys, `doc_id`, company, title, source, job URL, retrieval text, JSON payload, metadata, and timestamps.
- Job descriptions and normalized job fields passing through `src/pipeline/collector.py`, JD enrichment, filtering, and existing RAG export/storage paths.
- Resume files and role mappings in `src/storage/profile_resumes/`, plus resume evidence consumed by the Resume Match Agent and Critic Agent.
- JD intelligence output such as required/preferred skills, tools, methods, workflows, business context, stakeholder context, ownership signals, and seniority indicators.
- Resume match and tailoring evidence such as selected resume context, source bullets, proposed text, match reasons, gaps, and projected score delta.
- Trace runs and steps in `src/storage/agent_trace/`, including run/context identifiers, agent name/version, input/output/validation JSON, status, timestamps, provider/model metadata, token usage, cost, and errors.
- Trace evidence packs, stage bundles, health/readiness decisions, and shadow sidecar trace readback payloads in `src/agents/trace.py` and `src/agents/shadow_sidecar_trace_readback.py`.
- Read-only recommendation overlays and operator review packets in `src/agents/agent_recommendation_overlay_readback.py` and `src/agents/pipeline_agent_review_packet.py`.
- Future human decisions and application outcomes, when a later phase defines an approved, privacy-safe source contract.

The source records remain authoritative. A future vector index must be a derived, rebuildable evidence projection, never the system of record.

## Candidate chunk types

### Job description chunks

Candidate content includes responsibility paragraphs, qualification groups, skills/tools, business context, seniority signals, location constraints, and normalized JD intelligence. Chunks should retain a stable source reference and job freshness timestamp so stale or replaced descriptions can be rejected.

### Resume/profile chunks

Candidate content includes bounded resume sections, experience bullets, skills, projects, and profile preferences. These chunks require strict owner scoping, explicit consent, redaction policy, and a `resume_version` or `profile_version`. Raw resume binaries should not be embedded directly.

### Trace evidence chunks

Candidate content includes bounded summaries from agent step input/output/validation JSON, reason codes, evidence spans, safety metadata, and trace readiness findings. Secrets, unbounded payloads, and raw provider prompts must be excluded.

### Operator review packet chunks

Candidate content includes review focus, overlay findings, recommended operator action, deterministic source decision, advisory shadow findings, and safety metadata from read-only review packets. These chunks support operator recall and comparison; they do not authorize mutation.

### Future application outcome feedback chunks

Candidate content could include operator-approved dispositions and later outcomes such as reviewed, applied, rejected, interviewed, or offered. This source does not yet define a vector contract. A future phase must specify consent, retention, provenance, label quality, and protection against outcome leakage before indexing it.

## Candidate metadata fields

Each future chunk should use bounded, filterable metadata where available:

- `job_id`
- `company`
- `title`
- `source`
- `stage`
- `agent_name`
- `trace_id` and/or `run_id` when available
- `resume_version` and/or `profile_version` when available
- `created_at`
- `safety_flags`
- `read_only`

Additional useful provenance fields may include `chunk_id`, `chunk_type`, `source_record_id`, `source_updated_at`, `owner_user_id` or a non-reversible tenant scope, `content_hash`, `chunk_version`, `embedding_model_id`, `embedding_dimension`, and `deleted_at`. Privacy-sensitive identifiers must not be exposed across owners or tenants.

## Retrieval mapped to existing pipeline, agents, and storage

Vector retrieval is a future evidence-support layer mapped to existing areas, not a replacement for them:

| Future retrieval flow | Existing source areas | Permitted future output |
| --- | --- | --- |
| JD intelligence evidence retrieval | `src/pipeline/collector.py`, job corpus storage, `src/agents/jd_intelligence.py` | Relevant JD passages with provenance for advisory extraction/review |
| Resume match evidence retrieval | profile resume storage, `src/agents/resume_match_agent.py` | Owner-scoped resume passages and match evidence |
| Tailoring suggestion evidence retrieval | JD evidence, resume evidence, `src/agents/tailoring_decision_agent.py` | Grounding passages for suggestions, never direct resume mutation |
| Critic/guardrail evidence retrieval | trace evidence, source bullets, `src/agents/critic_agent.py` | Evidence spans supporting or rejecting advisory claims |
| Operator review packet evidence retrieval | trace readback, overlay readback, `src/agents/pipeline_agent_review_packet.py` | Read-only provenance and comparable prior evidence for human review |

`src/storage/rag_store.py`, `src/storage/agent_trace/`, and `src/storage/profile_resumes/` demonstrate current storage boundaries. Any future vector repository must be a separate adapter with explicit owner filters and must not silently alter these existing stores.

## Evaluation-boundary separation

The following four concerns must stay separate:

1. **Prefilter relevance** is the existing deterministic or legacy embedding-assisted candidate reduction boundary represented by `src/pipeline/embedding_prefilter.py` and the Relevance Prefilter Agent wrapper. It must not be silently replaced by vector retrieval.
2. **LLM/shadow evaluation** is optional, feature-flagged, advisory evaluation represented by shadow sidecar and dry-run agent surfaces. Provider-backed behavior must remain disabled by default and independently observable.
3. **Final application scoring** is the authoritative deterministic scoring boundary represented by `src/pipeline/application_scorer.py` and the Final Application Scoring Agent wrapper. Retrieval must not write, lift, suppress, or otherwise influence this score without a separately approved phase and explicit policy.
4. **Retrieval/evidence support** may return relevant passages, provenance, confidence, and no-evidence fallbacks. It is advisory evidence only and has no authority over prefiltering, LLM/shadow decisions, final application scoring, ranking, queues, approvals, execution, or submission.

## Backend options and tradeoffs

### Postgres + pgvector

Advantages:

- Aligns with the repository's existing Postgres storage patterns.
- Keeps transactional source metadata and vector references near existing job, profile, and trace records.
- Supports metadata filtering, ownership boundaries, operational backups, and one local deployment surface.
- Avoids introducing a separate managed service during the first implementation.

Tradeoffs:

- Requires a future extension/dependency/schema review and migration, none of which is authorized in Phase 8A.
- Requires index tuning, dimension/model governance, re-embedding strategy, and query-performance monitoring.
- Database growth and vector workloads could contend with transactional workloads without resource controls.

### External managed vector DB

Examples for later evaluation include a managed vector service such as Pinecone or another approved provider.

Advantages:

- Managed scaling, indexing, availability, and vector-native operational features.
- Can isolate retrieval workloads from the primary application database.

Tradeoffs:

- Adds network, vendor, credential, privacy, cost, rate-limit, data-residency, and synchronization concerns.
- Requires robust deletion propagation and source/vector consistency.
- Increases test and local-development complexity.

No managed vector dependency or provider integration is added in this phase.

### Local dev-only store

A later spike could use an isolated, replaceable local store solely for developer evaluation.

Advantages:

- Fast experimentation and disposable fixtures.
- No production data or managed-service requirement.

Tradeoffs:

- Risks environment drift and accidental reliance on behavior unavailable in production.
- Weak fit for multi-user privacy, durability, observability, and operational parity.
- Must never become an implicit production fallback.

This phase does not add Chroma, FAISS, or any other local vector dependency.

## Recommended first backend — recommendation only

**Recommendation only: use Postgres + pgvector as the first production-oriented backend in a future Phase 8B+ implementation.**

The recommendation is based on the existing Postgres-backed job document, profile resume, and agent trace boundaries. It is not approval to install pgvector, modify schema, add dependencies, create embeddings, or wire retrieval into runtime. A later phase must validate extension availability, privacy isolation, operational capacity, migration/rollback behavior, and deterministic tests before implementation.

## Required feature flags

Future work should default all retrieval and provider behavior off. Proposed names are:

- `APPLYLENS_VECTOR_RETRIEVAL_ENABLED`
- `APPLYLENS_VECTOR_INDEX_WRITES_ENABLED`
- `APPLYLENS_VECTOR_JOB_CHUNKS_ENABLED`
- `APPLYLENS_VECTOR_RESUME_CHUNKS_ENABLED`
- `APPLYLENS_VECTOR_TRACE_CHUNKS_ENABLED`
- `APPLYLENS_VECTOR_REVIEW_PACKET_CHUNKS_ENABLED`
- `APPLYLENS_VECTOR_OUTCOME_FEEDBACK_CHUNKS_ENABLED`
- `APPLYLENS_VECTOR_PROVIDER_EMBEDDINGS_ENABLED`
- `APPLYLENS_VECTOR_RETRIEVAL_SHADOW_ONLY`
- `APPLYLENS_VECTOR_KILL_SWITCH`

Safe defaults are: kill switch respected, all capabilities disabled, retrieval shadow-only, index writes disabled, provider embeddings disabled, and outcome feedback disabled. Read and write flags must be separate. Resume/profile retrieval must additionally require authenticated owner scope and an explicit privacy/consent gate.

## No-runtime-change migration plan

Phase 8A performs only design and contract documentation:

1. Inventory source contracts and establish chunk, metadata, provenance, deletion, privacy, and freshness requirements.
2. Define deterministic synthetic fixtures and expected retrieval results without importing a vector library.
3. Define a backend-neutral vector repository interface in documentation before runtime code exists.
4. Define feature flags, kill switch behavior, read/write separation, shadow-only behavior, and no-evidence fallback.
5. Require a future schema/dependency approval checkpoint before any extension, table, index, migration, package, or provider is introduced.
6. Require a future offline indexing/backfill plan that is idempotent, content-hash deduplicated, owner-scoped, resumable, observable, and reversible.
7. Require dual-read or shadow-read evaluation before any user-facing retrieval surface.
8. Keep retrieval disconnected from scoring, ranking, queue, approval, execution, and submission throughout migration.
9. Roll back by disabling flags and deleting only derived vector data; source job, resume, trace, and review records remain authoritative.

No migration is executed, no schema artifact is created or changed, and no runtime adapter is added in Phase 8A.

## Future Phase 8B+ plan

- **Phase 8B — contracts and deterministic fixtures:** approve chunk schemas, metadata validation, privacy scoping, content hashing, deletion semantics, fixture corpus, retrieval metrics, and backend-neutral interfaces. Remain provider-free and runtime-disconnected unless separately authorized.
- **Phase 8C — backend spike behind flags:** validate the recommended Postgres + pgvector backend in an isolated, default-off environment. Add any dependency, extension, and schema only through a separately reviewed migration checkpoint.
- **Phase 8D — offline indexing:** build an explicit, idempotent backfill for approved job-description chunks first. Do not index resumes or traces until their privacy review passes.
- **Phase 8E — shadow retrieval:** retrieve advisory evidence for JD intelligence and operator review with no scoring/ranking/queue/application influence. Compare retrieval against deterministic fixtures and lexical/no-evidence fallbacks.
- **Phase 8F — owner-scoped resume and trace evidence:** add separately approved privacy controls, retention/deletion propagation, and access tests before indexing resume/profile or trace content.
- **Later phase — reviewed influence proposal:** only after measured quality, safety review, and explicit human approval should the team consider whether retrieved evidence may inform a proposal. Direct automatic score or application influence remains out of scope unless separately authorized.

## Risks and required mitigations

- **Embedding drift:** model or dimension changes can make old and new vectors incomparable. Record model/version/dimension and require versioned re-indexing.
- **Stale job descriptions:** replaced or closed jobs can produce misleading evidence. Track source update time, expiry/closed state, and deletion propagation.
- **Duplicate chunks:** repeated exports or overlapping chunk windows can bias retrieval. Use stable chunk IDs, source IDs, content hashes, and deterministic deduplication.
- **Privacy/resume leakage:** resume/profile and trace content can expose personal information. Enforce owner/tenant filters before query execution, minimize text, redact secrets, audit access, and support deletion.
- **Retrieval influencing score without approval:** evidence could accidentally become an implicit scoring feature. Keep retrieval output advisory, typed separately, and prohibited from scoring/ranking inputs.
- **Provider cost/rate limits:** provider-backed embeddings can be expensive or unavailable. Keep provider calls disabled by default, meter usage, batch safely, cache by content hash, and provide a no-provider fallback.
- **Test determinism:** approximate nearest-neighbor results and remote providers can make tests flaky. Use fixed synthetic vectors or deterministic fake adapters, exact expected fixtures, stable tie-breaking, and no network calls in contract tests.

## Safety boundaries

- Retrieval must not mutate scoring, ranking, queue state, approvals, application execution, or application submission.
- Retrieval output must be advisory evidence with explicit provenance and confidence.
- Retrieval must not replace prefilter relevance or final application scoring.
- No automatic submission is permitted.
- No provider-backed automation is permitted without explicit default-off flags, a kill switch, budgets, and observability.
- No retrieved passage may authorize a resume edit, approval, execution request, launch request, or application action.
- Missing, stale, private, unauthorized, or low-confidence evidence must fail closed to a clear no-evidence result.
- Existing source records remain authoritative; vector records are derived and rebuildable.

## Observability requirements

Every future retrieval attempt should emit or return:

- retrieval trace entries with operation, stage, query purpose, filters, backend, feature-flag state, latency, result count, and fallback status
- chunk provenance with chunk ID, source record ID, chunk type/version, content hash, source timestamp, and embedding model/version
- retrieval confidence or distance with backend-specific values normalized only when the normalization contract is documented
- a deterministic fallback when no evidence is found, retrieval is disabled, evidence is stale, access is denied, or the backend is unavailable
- deterministic test fixtures with synthetic content, stable vectors or fake similarity results, stable ordering/tie-breaking, and no provider/network requirement

Sensitive query text, raw resume content, credentials, and unbounded trace payloads must not be written to logs. Observability must distinguish retrieval success from evidence sufficiency; a technically successful query may still return insufficient evidence.

## Audit conclusion

The repository is structurally ready for a later vector-readiness contract phase because it already separates job corpus storage, profile resume storage, trace storage/readback, deterministic prefilter relevance, optional LLM/shadow evaluation, final application scoring, and read-only operator review packets.

It is not yet approved for vector runtime implementation. Phase 8A adds documentation and a focused contract test only: no runtime change, no dependencies added, no schema change, no vector database dependencies, no embeddings runtime, no provider calls, no pipeline runtime modification, no API routes, and no UI.
