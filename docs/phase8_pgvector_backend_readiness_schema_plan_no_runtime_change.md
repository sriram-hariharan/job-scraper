# Phase 8I pgvector backend readiness and schema plan — no runtime change

## Phase boundary

Phase 8I is a docs/tests-only pgvector readiness and schema proposal. It makes **no runtime change**, **no dependency change**, and applies **no schema or migration**. No SQL artifact, migration, storage adapter, database connection, extension installation, embedding, provider call, pipeline wiring, API/service/UI change, score change, ranking change, queue change, approval change, resume change, execution request, application execution, or submission is included.

Postgres + pgvector is a recommendation only. This document is not authorization to install the extension, add a Python package, create tables, connect to Postgres, backfill data, or switch the existing Phase 8B–8G in-memory vector evidence flow.

## Files and directories inspected

- `src/storage/`
- all existing `src/storage/**/schema.sql` files
- `src/storage/scheduler/init.sql`
- `src/storage/scheduler/seed.sql`
- `src/storage/admin_tools/README.md`
- `src/storage/admin_tools/agent_trace/apply_schema.py`
- `src/storage/agent_state/migration_runner.py`
- `src/storage/rag_store.py`
- `src/storage/agent_trace/store.py`
- `src/storage/profile_resumes/store.py`
- migration/Alembic filename and directory search results
- dependency manifests: `requirements.txt`, plus checks for `pyproject.toml`, `Pipfile`, lock files, setup files, environment files, and `uv.lock`
- `src/agents/vector_evidence_contract.py`
- `src/agents/vector_evidence_indexing_dry_run.py`
- `src/agents/vector_evidence_retrieval_dry_run.py`
- the Phase 8E helper in `src/app/services.py`
- the Phase 8F route in `src/app/api.py`
- `docs/phase8_vector_db_readiness_audit_no_runtime_change.md`
- existing Phase 8 tests through the Phase 8G UI checkpoint
- `tests/test_portfolio_demo_readiness_wrap_checkpoint.py`
- existing logging, cache, retry, deduplication, ranking, metrics, and ATS-health call sites in `src/pipeline/collector.py`, `src/storage/rag_store.py`, and `src/utils/`

## Current storage, schema, migration, and dependency findings

The repository already has Postgres-oriented storage boundaries, so this plan maps to existing conventions rather than inventing a second storage architecture:

- Storage is organized by domain under `src/storage/<domain>/`, commonly with `store.py`, `read_postgres.py`, `schema.sql`, and `__init__.py`.
- Existing schemas use Postgres types and features including `JSONB`, `TIMESTAMPTZ`, `BYTEA`, foreign keys, partial indexes, and owner-scoped keys.
- `auth_users.user_id` is the established authenticated owner identity. `profile_resumes`, `agent_trace`, `agent_feedback`, `user_pipeline`, and related stores use `owner_user_id`.
- `src/storage/rag_store.py` is the closest job-evidence source. It stores stable merge keys, job identifiers, company/title/source, retrieval text, payload/metadata JSONB, timestamps, deterministic upserts, bounded batches, write locking, and Redis cache invalidation.
- `src/storage/profile_resumes/` is the authoritative resume storage boundary. Vector rows must remain derived projections and must not duplicate raw resume binaries.
- `src/storage/agent_trace/` is the authoritative trace boundary and already carries owner, pipeline/context/run identifiers, agent information, timestamps, validation, and provider metadata.
- Static `schema.sql` artifacts and explicit admin tools exist. `src/storage/admin_tools/*/apply_schema.py` uses `psql`, `DATABASE_URL`, `ON_ERROR_STOP`, a transaction, print-only support, URL redaction, and contract-health checks.
- One explicit `src/storage/agent_state/migration_runner.py` exists. It is inert on import and requires caller-supplied SQL plus an injected cursor. There is no Alembic directory or general migration framework.
- Some current stores use the `psql` executable; some can optionally use `psycopg`/`psycopg2` if available. Neither pgvector nor a Postgres Python driver is declared in `requirements.txt`.
- The only discovered dependency manifest is `requirements.txt`. It contains no `pgvector`, `psycopg`, `psycopg2`, Pinecone, Chroma, or FAISS dependency.
- Current Phase 8 vector evidence is deterministic, in-memory, read-only, provider-free, and database-free. It has stable chunk IDs, bounded metadata, lexical retrieval, metadata filters, deterministic tie-breaking, no-result fallbacks, a service helper, one API route, and a manually triggered read-only UI.

### Existing pattern to follow later

A future implementation should introduce a separate `src/storage/vector_evidence/` domain only after explicit approval. That future domain should follow the existing store/schema/contract-health/admin-tool pattern. It should use the existing `DATABASE_URL`, redacted command reporting, explicit invocation, owner scoping, deterministic payloads, and contract drift checks. Phase 8I creates none of those files.

It must not place vector writes in `src/storage/rag_store.py`, `src/storage/profile_resumes/store.py`, `src/storage/agent_trace/store.py`, the collector, an import hook, startup, page load, scheduler, or background task. Source stores remain authoritative; vector storage is derived and rebuildable.

## Why Postgres + pgvector is the recommended first backend

**Recommendation only: Postgres + pgvector is the preferred first backend for a later implementation phase.**

It fits the repository because Postgres, `DATABASE_URL`, `psql` admin workflows, JSONB metadata, timestamps, owner scoping, contract-health checks, and explicit schema artifacts already exist. It allows transactional chunk provenance and owner filters to live beside—without replacing—the existing source domains. It also avoids adding a separate credentialed network service, synchronization process, deletion protocol, local/production parity gap, and vendor-specific operational surface for the first backend.

This recommendation does not imply that vector workload belongs in existing transactional tables. The proposed tables form a separate derived evidence domain. Capacity testing must determine whether the same Postgres cluster is appropriate or whether a separate Postgres database is needed. Existing logging, configuration, retry behavior, Redis caching, job deduplication, ranking, metrics, and ATS health checks remain unchanged.

## Required extension and environment checks

The first future executable phase must be an extension probe, not a migration. It should be explicit, read-only where possible, and support print-only output. Required checks:

1. Confirm the target is an approved Postgres environment and redact credentials in all output.
2. Query `pg_available_extensions` for `vector`, then query `pg_extension` to determine whether it is installed.
3. Record the Postgres server version and available/installed pgvector extension version.
4. Verify whether the deployment role may run `CREATE EXTENSION vector`; do not grant broader privileges automatically.
5. After separately approved installation, verify the `vector` type, distance operators, and supported operator classes.
6. Verify supported vector dimensions against the proposed embedding model before table creation.
7. Verify whether HNSW and/or IVFFlat index methods and the intended cosine/L2/inner-product operator class are supported by the installed version.
8. Check migration transaction behavior, lock impact, disk capacity, backup coverage, replica compatibility, restore behavior, statement timeout, and maintenance settings.
9. Confirm owner/tenant predicates are mandatory before resume/profile or trace retrieval can execute.
10. Fail closed when the extension, dimension, index capability, owner scope, flags, or backend health is missing.

No extension probe is executed in Phase 8I.

## Proposed storage model — proposal only

The model separates canonical chunk text, model-specific embeddings, and retrieval telemetry. This avoids duplicating normalized text for every embedding model and permits controlled re-embedding.

### Proposed table: `vector_evidence_chunks`

Purpose: derived, owner-scoped evidence text and provenance. Proposed columns:

- `chunk_id TEXT PRIMARY KEY`
- `chunk_type TEXT NOT NULL`
- `chunk_version INTEGER NOT NULL DEFAULT 1`
- `content_hash TEXT NOT NULL`
- `normalized_text TEXT NOT NULL`
- `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
- `job_id TEXT NOT NULL DEFAULT ''`
- `company TEXT NOT NULL DEFAULT ''`
- `title TEXT NOT NULL DEFAULT ''`
- `source TEXT NOT NULL DEFAULT ''`
- `stage TEXT NOT NULL DEFAULT ''`
- `agent_name TEXT NOT NULL DEFAULT ''`
- `trace_id TEXT NOT NULL DEFAULT ''`
- `run_id TEXT NOT NULL DEFAULT ''`
- `resume_version TEXT NOT NULL DEFAULT ''`
- `profile_version TEXT NOT NULL DEFAULT ''`
- `owner_user_id TEXT NOT NULL` or an equivalently enforced tenant-scope column
- `source_record_id TEXT NOT NULL DEFAULT ''`
- `source_updated_at TIMESTAMPTZ`
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `deleted_at TIMESTAMPTZ`

`owner_user_id` should reference the existing auth owner boundary when all source types are owner-scoped. If a future design permits shared job evidence, the migration design must define a non-ambiguous tenant/public scope and must never use an empty owner value to mean both public and private.

### Proposed table: `vector_evidence_embeddings`

Purpose: model-specific vectors for canonical chunks. Proposed columns:

- `chunk_id TEXT NOT NULL` referencing `vector_evidence_chunks(chunk_id)` with reviewed delete behavior
- `embedding_model_id TEXT NOT NULL`
- `embedding_dimension INTEGER NOT NULL`
- `embedding VECTOR(<approved_dimension>) NOT NULL` — vector column proposal only
- `embedding_content_hash TEXT NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `deleted_at TIMESTAMPTZ`

Proposed primary or unique identity: `(chunk_id, embedding_model_id, embedding_dimension, embedding_content_hash)`. A model/dimension change creates a new versioned embedding population; it must not reinterpret old vectors.

### Proposed table: `vector_evidence_retrieval_events`

Purpose: privacy-minimized retrieval event trace and operational metrics, not raw query logging. Proposed columns:

- `retrieval_event_id TEXT PRIMARY KEY`
- `owner_user_id TEXT NOT NULL` or the same enforced tenant scope as the query
- `request_id TEXT NOT NULL DEFAULT ''`
- `query_hash TEXT NOT NULL DEFAULT ''`
- `query_purpose TEXT NOT NULL DEFAULT ''`
- `chunk_type TEXT NOT NULL DEFAULT ''`
- `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
- `job_id TEXT NOT NULL DEFAULT ''`
- `company TEXT NOT NULL DEFAULT ''`
- `stage TEXT NOT NULL DEFAULT ''`
- `agent_name TEXT NOT NULL DEFAULT ''`
- `trace_id TEXT NOT NULL DEFAULT ''`
- `run_id TEXT NOT NULL DEFAULT ''`
- `embedding_model_id TEXT NOT NULL DEFAULT ''`
- `embedding_dimension INTEGER`
- `top_k INTEGER NOT NULL`
- `result_count INTEGER NOT NULL DEFAULT 0`
- `fallback_reason TEXT NOT NULL DEFAULT ''`
- `latency_ms INTEGER`
- `backend_status TEXT NOT NULL DEFAULT ''`
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `deleted_at TIMESTAMPTZ`

Raw resume/profile query text, raw evidence text, credentials, prompts, and unbounded trace payloads must not be placed in retrieval events.

## Proposed indexes — proposal only

No index is created in this phase.

- Unique chunk-version dedup index on `(owner_user_id or tenant scope, chunk_type, content_hash, chunk_version)`.
- Source identity index on `(owner_user_id or tenant scope, source_record_id, chunk_type, chunk_version)`.
- Active-record indexes using `deleted_at IS NULL`.
- B-tree metadata lookup indexes for owner/tenant plus `job_id`, `company`, `stage`, `agent_name`, `trace_id`, `run_id`, `resume_version`, and `profile_version` according to measured query patterns.
- A bounded GIN index on `metadata` only if measured filters require it; promoted typed columns remain preferred for common filters.
- Embedding identity index on `(embedding_model_id, embedding_dimension, embedding_content_hash)`.
- Retrieval-event indexes on owner/tenant plus `created_at`, `request_id`, `job_id`, `stage`, `fallback_reason`, and backend status.
- A pgvector HNSW or IVFFlat vector index is proposal only. The exact method, operator class, build parameters, maintenance policy, and partial predicate must be selected from measured corpus size, recall, latency, write volume, installed pgvector version, and rollback cost. Exact scan remains the deterministic small-fixture baseline.

## Migration and rollback plan

No schema/migration is applied in Phase 8I. A future migration must be a separately reviewed phase:

1. Capture extension probe, database version, privileges, capacity, backup, and restore evidence.
2. Approve an inert `src/storage/vector_evidence/schema.sql` artifact and table contract before execution tooling.
3. Apply `CREATE EXTENSION vector` only through an explicitly approved administrative change; do not hide it in application startup.
4. Create `vector_evidence_chunks`, then `vector_evidence_embeddings`, then `vector_evidence_retrieval_events`.
5. Add non-vector uniqueness and lookup indexes first.
6. Validate owner isolation, constraints, idempotent repeat runs, and exact-scan fixture queries.
7. Build the vector index separately with measured lock/disk impact and a clear abort plan.
8. Keep all reads and writes disabled while schema validation runs.
9. Enable job-description shadow writes first; resume/profile and trace indexing require separate privacy approval.
10. Backfill in bounded, resumable, content-hash-deduplicated batches with progress and failure telemetry.

Rollback order:

1. Set the kill switch and disable retrieval and index writes.
2. Return service/API/UI to the existing deterministic dry-run path.
3. Stop backfill and drain in-flight adapter work.
4. Drop or disable the vector index first if it causes operational pressure.
5. Delete only derived embedding rows and retrieval events; preserve authoritative source records.
6. Drop `vector_evidence_retrieval_events`, then `vector_evidence_embeddings`, then `vector_evidence_chunks` only after retention/export review.
7. Drop the `vector` extension only if no other approved schema depends on it and restore testing confirms safety.

Rollback must never delete source jobs, profile resumes, agent traces, approvals, queue records, or application history.

## Feature flags and safe defaults

Proposed flags:

- `APPLYLENS_PGVECTOR_EXTENSION_PROBE_ENABLED=false`
- `APPLYLENS_VECTOR_BACKEND=memory_dry_run`
- `APPLYLENS_VECTOR_RETRIEVAL_ENABLED=false`
- `APPLYLENS_VECTOR_INDEX_WRITES_ENABLED=false`
- `APPLYLENS_VECTOR_JOB_CHUNKS_ENABLED=false`
- `APPLYLENS_VECTOR_RESUME_CHUNKS_ENABLED=false`
- `APPLYLENS_VECTOR_TRACE_CHUNKS_ENABLED=false`
- `APPLYLENS_VECTOR_REVIEW_PACKET_CHUNKS_ENABLED=false`
- `APPLYLENS_VECTOR_PROVIDER_EMBEDDINGS_ENABLED=false`
- `APPLYLENS_VECTOR_LOCAL_EMBEDDING_STUB_ENABLED=false`
- `APPLYLENS_VECTOR_RETRIEVAL_SHADOW_ONLY=true`
- `APPLYLENS_VECTOR_KILL_SWITCH=true`

Reads, writes, source types, backend choice, and provider behavior must have separate flags. The kill switch wins over every other flag. A backend error or disabled flag must preserve the current no-result/dry-run fallback.

## Privacy controls for resume/profile and trace data

- Require authenticated `owner_user_id`/tenant scope before indexing and before query planning, not only after results are returned.
- Include owner scope in unique keys, lookup predicates, vector queries, cache keys, telemetry aggregation, and deletion jobs.
- Never index raw resume binaries. Normalize and minimize approved text sections only.
- Exclude credentials, contact details unless explicitly required, provider prompts, secrets, tokens, and unbounded trace payloads.
- Define consent, purpose, retention, export, deletion, and re-indexing behavior before enabling resume/profile chunks.
- Propagate profile resume deletion/version replacement to soft-deleted chunks and embeddings, then hard-delete after the approved retention window.
- Do not log raw query or evidence text. Use request IDs, hashes, bounded reason codes, counts, and redacted provenance.
- Test cross-owner access denial before any private corpus is enabled.
- Keep public/shared job evidence distinguishable from private owner-scoped evidence.

## Deduplication and stale chunk cleanup

The existing Phase 8 contract stable chunk IDs and indexing dry-run deduplication should remain the normalization authority until a separately approved contract version changes them.

- Normalize text deterministically before hashing.
- Use `content_hash` plus owner/tenant, chunk type, source identity, and chunk version for idempotent upserts.
- Reuse an embedding only when normalized content hash, model ID, dimension, and embedding contract version all match.
- Do not let duplicate overlapping chunks inflate retrieval ranking.
- Mark replaced source versions with `deleted_at`; queries must filter inactive rows.
- Compare `source_updated_at`, resume/profile versions, trace/run identifiers, and source existence during reconciliation.
- Run stale cleanup only as an explicit, separately approved job—never on import, startup, API read, or UI load.
- Cleanup must be bounded, owner-scoped, observable, retry-safe, and reversible during the retention window.

## Deterministic test strategy

- Keep current contract, indexing dry-run, lexical retrieval dry-run, service, API, and UI tests as the no-DB baseline.
- Use synthetic owner-scoped fixtures and fixed local vectors; do not call providers or require network access.
- Test exact vector scan first with stable ordering by distance, chunk type, and chunk ID.
- Use explicit tolerance for floating-point distance while requiring deterministic tie-breaking.
- Test model/dimension mismatch, extension unavailable, backend disabled, kill switch, no chunks, no results, stale/deleted chunks, metadata filters, and cross-owner denial.
- Test idempotent content-hash upsert and rebuild behavior with fake/injected adapters before Postgres integration tests.
- Put real pgvector integration tests behind an explicit environment marker and disposable database; they must never run implicitly.
- Compare backend results with deterministic fixtures and the current lexical fallback, without changing score or rank assertions.

## Observability requirements

### Chunk provenance

Every result must retain chunk ID/type/version, content hash, source record, source timestamp, owner/tenant scope, job/resume/trace identifiers, model ID, dimension, and deletion/freshness state. User-facing output must expose only safe provenance.

### Retrieval event trace

Record request ID, purpose, stage, bounded metadata filters, backend/flag state, owner scope, model/dimension, top-k, result count, fallback reason, latency, and error category. Do not record raw private text.

### No-result fallback

Disabled, unavailable, unauthorized, stale, empty, dimension-mismatched, and zero-match paths must return the existing advisory no-result shape and continue without retrieval influence.

### Latency and volume metrics

Measure extension/backend availability, chunk and embedding counts by safe scope/type/model, indexing throughput, stale/deleted volume, query latency percentiles, result counts, no-result rate, error rate, vector index size, database load, and cache hit/miss behavior. Use existing logging/metrics conventions rather than adding a parallel emitter in the migration.

Existing collector logging, config, HTTP retry, Redis caching, job deduplication, deterministic ranking, pipeline metrics, and ATS health checks must be preserved unchanged. Vector retries must be bounded and must not retry authorization, validation, or dimension errors.

## Evaluation and safety boundaries

These concerns remain explicitly separate:

1. **Prefilter relevance** remains the existing candidate-reduction boundary and is not replaced by pgvector retrieval.
2. **LLM/shadow evaluation** remains optional, independently flagged, provider-governed, and advisory.
3. **Final application scoring** remains authoritative and deterministic.
4. **Retrieval/evidence support** returns passages, provenance, distance/confidence, and fallbacks only.

Required safety boundaries:

- no scoring mutation
- no ranking mutation
- no queue or application mutation
- no approval or resume mutation
- no execution-request or launch-request creation
- no application execution
- no submission automation
- no provider-backed automation without explicit default-off flags, kill switch, budgets, and observability
- no retrieved evidence may authorize or trigger an action
- source records remain authoritative; vector rows are derived and rebuildable

## Future implementation phases

1. **Extension probe:** read-only/print-only capability and privilege report; no extension installation.
2. **Schema proposal:** approve exact DDL, constraints, ownership policy, vector dimension, index method, backup, and rollback artifacts; still no application runtime change.
3. **Schema migration:** separately approved extension/table/index migration with validation and rollback evidence; runtime flags remain off.
4. **Local no-provider embedding stub:** deterministic local fixture vectors only, injected behind flags, with no production data and no provider call.
5. **Provider-backed embedding integration behind flags:** separate approval for provider, privacy, cost, rate limits, model/dimension versioning, caching, and deletion propagation.
6. **Retrieval backend adapter:** backend-neutral interface mapped to a future `src/storage/vector_evidence/` domain, owner-filtered and default-off.
7. **Service/API/UI switch from dry-run to backend under flags:** shadow comparison first; retain dry-run/no-result fallback and do not alter scoring, ranking, queue, approval, resume, execution, or submission behavior.

## Phase 8I conclusion

The repository is ready for a separately approved pgvector extension probe and exact schema proposal because its existing Postgres storage, owner-scoping, schema artifacts, admin tools, contract-health checks, and Phase 8 evidence contracts provide concrete integration boundaries.

It is not ready or authorized for runtime activation in this phase. Phase 8I adds only this plan and its focused test/checkpoint allowlist: no runtime change, no dependency change, no schema/migration applied, no Postgres connection, no pgvector installation, no embeddings, no providers, and no behavior change.
