CREATE TABLE IF NOT EXISTS bulk_generation_runs (
    run_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    pipeline_run_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'queued', 'running', 'stop_requested', 'stopped', 'completed', 'failed'
    )),
    total_count INTEGER NOT NULL CHECK (total_count > 0 AND total_count <= 500),
    completed_count INTEGER NOT NULL DEFAULT 0 CHECK (completed_count >= 0),
    succeeded_count INTEGER NOT NULL DEFAULT 0 CHECK (succeeded_count >= 0),
    needs_attention_count INTEGER NOT NULL DEFAULT 0 CHECK (needs_attention_count >= 0),
    current_sequence INTEGER,
    current_job_identity TEXT NOT NULL DEFAULT '',
    worker_pid TEXT NOT NULL DEFAULT '',
    worker_identity TEXT NOT NULL DEFAULT '',
    stop_requested BOOLEAN NOT NULL DEFAULT FALSE,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_category TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    UNIQUE (run_id, owner_user_id),
    CHECK (completed_count <= total_count),
    CHECK (succeeded_count + needs_attention_count = completed_count)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_bulk_generation_runs_one_active_owner
ON bulk_generation_runs (owner_user_id)
WHERE status IN ('queued', 'running', 'stop_requested');

CREATE INDEX IF NOT EXISTS idx_bulk_generation_runs_owner_started
ON bulk_generation_runs (owner_user_id, started_at DESC);

CREATE TABLE IF NOT EXISTS bulk_generation_items (
    run_id TEXT NOT NULL,
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL CHECK (sequence > 0),
    job_identity TEXT NOT NULL,
    job_doc_id TEXT NOT NULL DEFAULT '',
    queue_rank TEXT NOT NULL DEFAULT '',
    selected_resume TEXT NOT NULL,
    job_label TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'running', 'succeeded', 'needs_attention'
    )),
    outcome TEXT NOT NULL DEFAULT '',
    error_category TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    PRIMARY KEY (run_id, sequence),
    UNIQUE (run_id, job_identity),
    FOREIGN KEY (run_id, owner_user_id)
        REFERENCES bulk_generation_runs(run_id, owner_user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bulk_generation_items_owner_run_sequence
ON bulk_generation_items (owner_user_id, run_id, sequence);
