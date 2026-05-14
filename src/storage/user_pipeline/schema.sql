CREATE TABLE IF NOT EXISTS user_pipeline_runs (
    run_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    current_stage TEXT NOT NULL DEFAULT '',
    stage_message TEXT NOT NULL DEFAULT '',
    summary_message TEXT NOT NULL DEFAULT '',
    return_code INTEGER,
    started_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_user_pipeline_runs_owner_started
ON user_pipeline_runs (owner_user_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_pipeline_runs_status_started
ON user_pipeline_runs (status, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_pipeline_runs_owner_status_started
ON user_pipeline_runs (owner_user_id, status, started_at DESC);

CREATE TABLE IF NOT EXISTS user_seen_jobs (
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    seen_key TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '',
    job_url TEXT NOT NULL DEFAULT '',
    job_doc_id TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    first_run_id TEXT NOT NULL DEFAULT '',
    last_run_id TEXT NOT NULL DEFAULT '',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (owner_user_id, seen_key)
);

CREATE INDEX IF NOT EXISTS idx_user_seen_jobs_owner_last_seen
ON user_seen_jobs (owner_user_id, last_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_seen_jobs_job_doc_id
ON user_seen_jobs (job_doc_id);

CREATE INDEX IF NOT EXISTS idx_user_seen_jobs_job_url
ON user_seen_jobs (job_url);

CREATE TABLE IF NOT EXISTS user_pipeline_artifacts (
    artifact_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES user_pipeline_runs(run_id) ON DELETE CASCADE,
    artifact_kind TEXT NOT NULL,
    artifact_name TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'application/json',
    content_json JSONB,
    content_text TEXT NOT NULL DEFAULT '',
    content_bytes BYTEA,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_pipeline_artifacts_owner_run
ON user_pipeline_artifacts (owner_user_id, run_id, artifact_kind);

CREATE INDEX IF NOT EXISTS idx_user_pipeline_artifacts_run_kind
ON user_pipeline_artifacts (run_id, artifact_kind);

CREATE INDEX IF NOT EXISTS idx_user_pipeline_artifacts_owner_created
ON user_pipeline_artifacts (owner_user_id, created_at DESC);
