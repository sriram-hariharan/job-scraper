CREATE TABLE IF NOT EXISTS application_actions (
    action_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL DEFAULT '',
    action_key TEXT NOT NULL,
    action_timestamp TIMESTAMPTZ NOT NULL,
    job_doc_id TEXT NOT NULL,
    job_url TEXT NOT NULL,
    job_company TEXT NOT NULL,
    job_title TEXT NOT NULL,
    application_status TEXT NOT NULL,
    source_view TEXT NOT NULL,
    note TEXT NOT NULL
);

ALTER TABLE application_actions
ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_application_actions_action_key_timestamp
ON application_actions (action_key, action_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_application_actions_status_timestamp
ON application_actions (application_status, action_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_application_actions_company_title
ON application_actions (job_company, job_title);

CREATE INDEX IF NOT EXISTS idx_application_actions_owner_key_timestamp
ON application_actions (owner_user_id, action_key, action_timestamp DESC);
