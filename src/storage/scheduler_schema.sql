CREATE TABLE IF NOT EXISTS scheduler_job_definitions (
    job_name TEXT PRIMARY KEY,
    job_description TEXT NOT NULL,
    default_options_json JSONB NOT NULL,
    supports_planning_only BOOLEAN NOT NULL,
    supports_application_planning BOOLEAN NOT NULL,
    trigger_source TEXT NOT NULL,
    is_active BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scheduler_job_definitions_active
    ON scheduler_job_definitions (is_active);

CREATE TABLE IF NOT EXISTS scheduler_run_history (
    run_id TEXT PRIMARY KEY,
    job_name TEXT NOT NULL REFERENCES scheduler_job_definitions (job_name),
    job_description TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('succeeded', 'failed')),
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ NOT NULL,
    return_code INTEGER NOT NULL,
    command_text TEXT NOT NULL,
    command_json JSONB NOT NULL,
    options_json JSONB NOT NULL,
    trigger_source TEXT NOT NULL,
    error_text TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scheduler_run_history_job_started
    ON scheduler_run_history (job_name, started_at);

CREATE INDEX IF NOT EXISTS idx_scheduler_run_history_status_started
    ON scheduler_run_history (status, started_at);

INSERT INTO scheduler_job_definitions (
    job_name,
    job_description,
    default_options_json,
    supports_planning_only,
    supports_application_planning,
    trigger_source,
    is_active
)
VALUES
    (
        'agent_discovery',
        'Run standalone company discovery agent.',
        '{}'::jsonb,
        FALSE,
        FALSE,
        'external_scheduler_wrapper',
        TRUE
    ),
    (
        'live_pipeline',
        'Run main pipeline and optionally downstream application planning.',
        '{"delete_seen_data":"no","generate_llm_fallback":false,"generate_llm_tailoring":false,"generate_tailoring":false,"job_limit":50,"job_packet_limit":0,"llm_actions":"APPLY,APPLY_REVIEW_VARIANTS","output_dir":"outputs/application_planning","planning_only":false,"refresh_llm_tailoring":false,"run_application_planning":true}'::jsonb,
        TRUE,
        TRUE,
        'external_scheduler_wrapper',
        TRUE
    )
ON CONFLICT (job_name) DO UPDATE
SET
    job_description = EXCLUDED.job_description,
    default_options_json = EXCLUDED.default_options_json,
    supports_planning_only = EXCLUDED.supports_planning_only,
    supports_application_planning = EXCLUDED.supports_application_planning,
    trigger_source = EXCLUDED.trigger_source,
    is_active = EXCLUDED.is_active;