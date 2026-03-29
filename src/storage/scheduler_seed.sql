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