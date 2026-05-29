CREATE TABLE IF NOT EXISTS agent_runs (
    agent_run_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    pipeline_run_id TEXT NOT NULL DEFAULT '',
    context_id TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_owner_started
ON agent_runs (owner_user_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_pipeline_started
ON agent_runs (pipeline_run_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_context_started
ON agent_runs (context_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_status_started
ON agent_runs (status, started_at DESC);

CREATE TABLE IF NOT EXISTS agent_steps (
    agent_step_id TEXT PRIMARY KEY,
    agent_run_id TEXT NOT NULL REFERENCES agent_runs(agent_run_id) ON DELETE CASCADE,
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    pipeline_run_id TEXT NOT NULL DEFAULT '',
    context_id TEXT NOT NULL DEFAULT '',
    agent_name TEXT NOT NULL,
    agent_version TEXT NOT NULL DEFAULT '',
    input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    latency_ms INTEGER,
    model_provider TEXT NOT NULL DEFAULT '',
    model_name TEXT NOT NULL DEFAULT '',
    token_usage_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    cost_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_agent_steps_run_started
ON agent_steps (agent_run_id, started_at);

CREATE INDEX IF NOT EXISTS idx_agent_steps_owner_started
ON agent_steps (owner_user_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_steps_pipeline_started
ON agent_steps (pipeline_run_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_steps_context_started
ON agent_steps (context_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_steps_status_started
ON agent_steps (status, started_at DESC);
