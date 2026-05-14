CREATE TABLE IF NOT EXISTS patch_selections (
    selection_id TEXT PRIMARY KEY,
    selection_timestamp TIMESTAMPTZ NOT NULL,
    owner_user_id TEXT NOT NULL DEFAULT '',
    job_doc_id TEXT NOT NULL,
    queue_rank TEXT NOT NULL,
    job_company TEXT NOT NULL,
    job_title TEXT NOT NULL,
    selected_resume TEXT NOT NULL,
    tailoring_json_path TEXT NOT NULL,
    artifact_signature TEXT NOT NULL,
    selected_candidate_ids_json JSONB NOT NULL,
    note TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_patch_selections_path_timestamp
ON patch_selections (tailoring_json_path, selection_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_patch_selections_job_doc_id
ON patch_selections (job_doc_id);

CREATE INDEX IF NOT EXISTS idx_patch_selections_queue_rank
ON patch_selections (queue_rank);

ALTER TABLE patch_selections
ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_patch_selections_owner_timestamp
ON patch_selections (owner_user_id, selection_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_patch_selections_owner_job_doc_id
ON patch_selections (owner_user_id, job_doc_id);
