CREATE TABLE IF NOT EXISTS profile_resumes (
    owner_user_id TEXT NOT NULL,
    resume_name TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    sha256 TEXT NOT NULL,
    file_bytes BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (owner_user_id, resume_name)
);

CREATE INDEX IF NOT EXISTS idx_profile_resumes_owner_updated
ON profile_resumes (owner_user_id, updated_at DESC);
