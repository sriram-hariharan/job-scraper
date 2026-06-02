CREATE TABLE IF NOT EXISTS agent_feedback_events (
    event_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    pipeline_run_id TEXT,
    context_id TEXT,
    agent_run_id TEXT,
    agent_step_id TEXT,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    source TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_feedback_events_owner_created
ON agent_feedback_events (owner_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_feedback_events_owner_event_type_created
ON agent_feedback_events (owner_user_id, event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_feedback_events_owner_target_created
ON agent_feedback_events (owner_user_id, target_type, target_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_feedback_events_pipeline_created
ON agent_feedback_events (pipeline_run_id, created_at DESC);
