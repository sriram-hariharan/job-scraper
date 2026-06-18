-- Static pgvector vector-evidence SQL DDL artifact.
-- This schema is never applied automatically by the application.
-- Requirement: the PostgreSQL `vector` extension must already be installed
-- by an explicitly approved administrative change before this file is applied.
-- This file intentionally does not run CREATE EXTENSION or create a migration.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_extension
        WHERE extname = 'vector'
    ) THEN
        RAISE EXCEPTION
            'pgvector extension "vector" must be installed before applying vector evidence schema';
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS vector_evidence_chunks (
    chunk_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    chunk_type TEXT NOT NULL,
    chunk_version INTEGER NOT NULL DEFAULT 1,
    content_hash TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    job_id TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    stage TEXT NOT NULL DEFAULT '',
    agent_name TEXT NOT NULL DEFAULT '',
    trace_id TEXT NOT NULL DEFAULT '',
    run_id TEXT NOT NULL DEFAULT '',
    resume_version TEXT NOT NULL DEFAULT '',
    profile_version TEXT NOT NULL DEFAULT '',
    source_record_id TEXT NOT NULL DEFAULT '',
    source_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT ck_vector_evidence_chunks_version_positive
        CHECK (chunk_version > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_vector_evidence_chunks_owner_type_hash_version
ON vector_evidence_chunks (
    owner_user_id,
    chunk_type,
    content_hash,
    chunk_version
)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vector_evidence_chunks_owner_job_active
ON vector_evidence_chunks (owner_user_id, job_id, chunk_type)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vector_evidence_chunks_owner_source_active
ON vector_evidence_chunks (owner_user_id, source_record_id, chunk_type)
WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS vector_evidence_embeddings (
    chunk_id TEXT NOT NULL REFERENCES vector_evidence_chunks(chunk_id) ON DELETE CASCADE,
    embedding_model_id TEXT NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    embedding VECTOR NOT NULL,
    embedding_content_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    PRIMARY KEY (
        chunk_id,
        embedding_model_id,
        embedding_dimension,
        embedding_content_hash
    ),
    CONSTRAINT ck_vector_evidence_embeddings_dimension_positive
        CHECK (embedding_dimension > 0),
    CONSTRAINT ck_vector_evidence_embeddings_dimension_matches
        CHECK (vector_dims(embedding) = embedding_dimension)
);

CREATE INDEX IF NOT EXISTS idx_vector_evidence_embeddings_model_active
ON vector_evidence_embeddings (
    embedding_model_id,
    embedding_dimension,
    embedding_content_hash
)
WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS vector_evidence_retrieval_events (
    retrieval_event_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    request_id TEXT NOT NULL DEFAULT '',
    query_hash TEXT NOT NULL DEFAULT '',
    query_purpose TEXT NOT NULL DEFAULT '',
    chunk_type TEXT NOT NULL DEFAULT '',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    job_id TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    stage TEXT NOT NULL DEFAULT '',
    agent_name TEXT NOT NULL DEFAULT '',
    trace_id TEXT NOT NULL DEFAULT '',
    run_id TEXT NOT NULL DEFAULT '',
    embedding_model_id TEXT NOT NULL DEFAULT '',
    embedding_dimension INTEGER,
    top_k INTEGER NOT NULL,
    result_count INTEGER NOT NULL DEFAULT 0,
    fallback_reason TEXT NOT NULL DEFAULT '',
    latency_ms INTEGER,
    backend_status TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT ck_vector_evidence_retrieval_top_k_positive
        CHECK (top_k > 0),
    CONSTRAINT ck_vector_evidence_retrieval_result_count_nonnegative
        CHECK (result_count >= 0)
);

CREATE INDEX IF NOT EXISTS idx_vector_evidence_retrieval_owner_created
ON vector_evidence_retrieval_events (owner_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vector_evidence_retrieval_owner_request
ON vector_evidence_retrieval_events (owner_user_id, request_id);

-- No HNSW or IVFFlat index is created in this phase. Index method, operator
-- class, and build parameters require separate measured approval.
-- No INSERT, UPDATE, DELETE, extension installation, or automatic execution hook.

