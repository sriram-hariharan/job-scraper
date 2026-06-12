-- Static agent state SQL DDL artifact only.
-- This file is intentionally inert: it is not executed automatically by this phase.
-- Rollback guidance: remove agent_steps before agent_runs in a separately reviewed migration phase.

CREATE TABLE IF NOT EXISTS agent_runs (
    agent_run_id TEXT PRIMARY KEY,
    agent_run_key TEXT NOT NULL,
    context_key TEXT NOT NULL,
    approval_request_id TEXT NOT NULL DEFAULT '',
    job_id TEXT NOT NULL DEFAULT '',
    candidate_key TEXT NOT NULL DEFAULT '',
    agent_name TEXT NOT NULL,
    run_status TEXT NOT NULL,
    observed_at_utc TIMESTAMPTZ NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    safety_flags_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_agent_runs_agent_run_key UNIQUE (agent_run_key)
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_context_observed
ON agent_runs (context_key, observed_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_approval_observed
ON agent_runs (approval_request_id, observed_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_job_observed
ON agent_runs (job_id, observed_at_utc DESC);

CREATE TABLE IF NOT EXISTS agent_steps (
    agent_step_id TEXT PRIMARY KEY,
    agent_step_key TEXT NOT NULL,
    agent_run_id TEXT NOT NULL,
    context_key TEXT NOT NULL,
    approval_request_id TEXT NOT NULL DEFAULT '',
    job_id TEXT NOT NULL DEFAULT '',
    candidate_key TEXT NOT NULL DEFAULT '',
    agent_name TEXT NOT NULL,
    step_name TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    step_status TEXT NOT NULL,
    observed_at_utc TIMESTAMPTZ NOT NULL,
    input_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    reason_codes_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    safety_flags_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_agent_steps_agent_step_key UNIQUE (agent_step_key),
    CONSTRAINT fk_agent_steps_agent_run
        FOREIGN KEY (agent_run_id)
        REFERENCES agent_runs (agent_run_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_steps_run_observed
ON agent_steps (agent_run_id, observed_at_utc);

CREATE INDEX IF NOT EXISTS idx_agent_steps_context_observed
ON agent_steps (context_key, observed_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_agent_steps_approval_observed
ON agent_steps (approval_request_id, observed_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_agent_steps_job_observed
ON agent_steps (job_id, observed_at_utc DESC);

-- Verification contract phrases
-- Agent state schema file implementation: PASS
-- SQL file implementation: STATIC_ARTIFACT_ONLY
-- SQL execution: NOT_INCLUDED
-- Migration runner: NOT_INCLUDED
-- Runtime-facing integration scope: ISOLATED_STORAGE_ARTIFACT_ONLY
-- Schema contains agent_runs
-- Schema contains agent_steps
-- Schema has no approval schema modification
-- Schema has no approval table modification
-- no INSERT statements
-- no UPDATE statements
-- no DELETE statements
-- no automatic execution hook
-- no migration runner added
