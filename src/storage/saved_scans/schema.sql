CREATE TABLE IF NOT EXISTS saved_scans (
    scan_id TEXT PRIMARY KEY,
    scan_timestamp TIMESTAMPTZ NOT NULL,
    scan_source TEXT NOT NULL,
    scan_status TEXT NOT NULL,
    resume_source TEXT NOT NULL,
    resume_name TEXT NOT NULL,
    resume_filename TEXT NOT NULL,
    resume_file_path TEXT NOT NULL,
    resume_file_mime_type TEXT NOT NULL,
    resume_size_bytes BIGINT NOT NULL,
    resume_text TEXT NOT NULL,
    job_doc_id TEXT NOT NULL,
    job_url TEXT NOT NULL,
    job_company TEXT NOT NULL,
    job_title TEXT NOT NULL,
    job_description_text TEXT NOT NULL,
    match_rate NUMERIC,
    tailoring_json_path TEXT NOT NULL,
    note TEXT NOT NULL,
    payload_json JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_saved_scans_timestamp
ON saved_scans (scan_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_saved_scans_company_title
ON saved_scans (job_company, job_title);

CREATE INDEX IF NOT EXISTS idx_saved_scans_resume_name
ON saved_scans (resume_name);
