-- Static PostgreSQL contract only. This artifact is not executed on import.

CREATE TABLE IF NOT EXISTS orchestration_graph_runs (
    graph_invocation_id TEXT PRIMARY KEY,
    graph_engine TEXT NOT NULL,
    graph_state_schema_version TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
    pipeline_run_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    job_index INTEGER NOT NULL,
    selected_resume_id TEXT NOT NULL,
    run_status TEXT NOT NULL,
    current_checkpoint_id TEXT,
    lock_version INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    terminal_at TIMESTAMPTZ,
    purge_after TIMESTAMPTZ,
    CONSTRAINT ck_orchestration_graph_runs_job_index
        CHECK (job_index >= 0),
    CONSTRAINT ck_orchestration_graph_runs_lock_version
        CHECK (lock_version >= 0),
    CONSTRAINT ck_orchestration_graph_runs_status
        CHECK (run_status IN ('running', 'awaiting_decision')),
    CONSTRAINT ck_orchestration_graph_runs_current_checkpoint
        CHECK (
            (run_status = 'running' AND current_checkpoint_id IS NULL)
            OR
            (run_status = 'awaiting_decision' AND current_checkpoint_id IS NOT NULL)
        ),
    CONSTRAINT uq_orchestration_graph_runs_logical_identity
        UNIQUE (
            graph_engine,
            graph_state_schema_version,
            owner_user_id,
            pipeline_run_id,
            context_id,
            job_id,
            job_index,
            selected_resume_id
        ),
    CONSTRAINT uq_orchestration_graph_runs_bound_identity
        UNIQUE (
            graph_invocation_id,
            owner_user_id,
            pipeline_run_id,
            context_id,
            job_id,
            job_index,
            selected_resume_id
        )
);

CREATE TABLE IF NOT EXISTS orchestration_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    graph_invocation_id TEXT NOT NULL,
    checkpoint_sequence INTEGER NOT NULL,
    checkpoint_schema_version TEXT NOT NULL,
    graph_state_schema_version TEXT NOT NULL,
    checkpoint_status TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
    pipeline_run_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    job_index INTEGER NOT NULL,
    selected_resume_id TEXT NOT NULL,
    checkpoint_envelope_json JSONB NOT NULL,
    checkpoint_envelope_digest TEXT NOT NULL,
    completed_node_keys_json JSONB NOT NULL,
    next_node_key TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL,
    purge_after TIMESTAMPTZ,
    CONSTRAINT ck_orchestration_checkpoints_sequence
        CHECK (checkpoint_sequence >= 0),
    CONSTRAINT ck_orchestration_checkpoints_job_index
        CHECK (job_index >= 0),
    CONSTRAINT ck_orchestration_checkpoints_status
        CHECK (checkpoint_status = 'diagnostic_snapshot'),
    CONSTRAINT ck_orchestration_checkpoints_envelope_object
        CHECK (jsonb_typeof(checkpoint_envelope_json) = 'object'),
    CONSTRAINT ck_orchestration_checkpoints_envelope_size
        CHECK (octet_length(checkpoint_envelope_json::text) <= 1048576),
    CONSTRAINT ck_orchestration_checkpoints_digest
        CHECK (checkpoint_envelope_digest ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_orchestration_checkpoints_completed_nodes
        CHECK (jsonb_typeof(completed_node_keys_json) = 'array'),
    CONSTRAINT uq_orchestration_checkpoints_run_sequence
        UNIQUE (graph_invocation_id, checkpoint_sequence),
    CONSTRAINT uq_orchestration_checkpoints_run_checkpoint
        UNIQUE (checkpoint_id, graph_invocation_id),
    CONSTRAINT uq_orchestration_checkpoints_bound_identity
        UNIQUE (
            checkpoint_id,
            graph_invocation_id,
            owner_user_id,
            pipeline_run_id,
            context_id,
            job_id,
            job_index,
            selected_resume_id
        ),
    CONSTRAINT fk_orchestration_checkpoints_graph_run
        FOREIGN KEY (
            graph_invocation_id,
            owner_user_id,
            pipeline_run_id,
            context_id,
            job_id,
            job_index,
            selected_resume_id
        )
        REFERENCES orchestration_graph_runs (
            graph_invocation_id,
            owner_user_id,
            pipeline_run_id,
            context_id,
            job_id,
            job_index,
            selected_resume_id
        )
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orchestration_interrupt_requests (
    interrupt_request_id TEXT PRIMARY KEY,
    graph_invocation_id TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    interrupt_request_schema_version TEXT NOT NULL,
    checkpoint_schema_version TEXT NOT NULL,
    graph_state_schema_version TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
    pipeline_run_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    job_index INTEGER NOT NULL,
    selected_resume_id TEXT NOT NULL,
    node_key TEXT NOT NULL,
    safe_next_node_key TEXT NOT NULL,
    operator_review_artifact_type TEXT NOT NULL,
    operator_review_artifact_version TEXT NOT NULL,
    operator_review_artifact_digest TEXT NOT NULL,
    allowed_decision_values_json JSONB NOT NULL,
    interrupt_request_json JSONB NOT NULL,
    interrupt_status TEXT NOT NULL,
    lock_version INTEGER NOT NULL DEFAULT 0,
    read_only BOOLEAN NOT NULL,
    diagnostic_only BOOLEAN NOT NULL,
    application_authorization BOOLEAN NOT NULL,
    resume_authorization BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    CONSTRAINT ck_orchestration_interrupt_requests_job_index
        CHECK (job_index >= 0),
    CONSTRAINT ck_orchestration_interrupt_requests_lock_version
        CHECK (lock_version >= 0),
    CONSTRAINT ck_orchestration_interrupt_requests_status
        CHECK (interrupt_status = 'pending'),
    CONSTRAINT ck_orchestration_interrupt_requests_unresolved
        CHECK (resolved_at IS NULL),
    CONSTRAINT ck_orchestration_interrupt_requests_boundary
        CHECK (node_key = 'operator_review' AND safe_next_node_key = 'finalize'),
    CONSTRAINT ck_orchestration_interrupt_requests_artifact_digest
        CHECK (operator_review_artifact_digest ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_orchestration_interrupt_requests_allowed_decisions
        CHECK (
            allowed_decision_values_json
            = '["continue_read_only","needs_revision","cancel"]'::jsonb
        ),
    CONSTRAINT ck_orchestration_interrupt_requests_payload_object
        CHECK (jsonb_typeof(interrupt_request_json) = 'object'),
    CONSTRAINT ck_orchestration_interrupt_requests_payload_size
        CHECK (octet_length(interrupt_request_json::text) <= 262144),
    CONSTRAINT ck_orchestration_interrupt_requests_safety
        CHECK (
            read_only = TRUE
            AND diagnostic_only = TRUE
            AND application_authorization = FALSE
            AND resume_authorization = FALSE
        ),
    CONSTRAINT uq_orchestration_interrupt_requests_checkpoint_node
        UNIQUE (checkpoint_id, node_key),
    CONSTRAINT fk_orchestration_interrupt_requests_graph_run
        FOREIGN KEY (graph_invocation_id)
        REFERENCES orchestration_graph_runs (graph_invocation_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_orchestration_interrupt_requests_checkpoint
        FOREIGN KEY (checkpoint_id)
        REFERENCES orchestration_checkpoints (checkpoint_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_orchestration_interrupt_requests_bound_checkpoint
        FOREIGN KEY (
            checkpoint_id,
            graph_invocation_id,
            owner_user_id,
            pipeline_run_id,
            context_id,
            job_id,
            job_index,
            selected_resume_id
        )
        REFERENCES orchestration_checkpoints (
            checkpoint_id,
            graph_invocation_id,
            owner_user_id,
            pipeline_run_id,
            context_id,
            job_id,
            job_index,
            selected_resume_id
        )
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_orchestration_graph_runs_owner_updated
ON orchestration_graph_runs (owner_user_id, updated_at DESC, graph_invocation_id);

CREATE INDEX IF NOT EXISTS idx_orchestration_graph_runs_pipeline_context
ON orchestration_graph_runs (
    owner_user_id,
    pipeline_run_id,
    context_id,
    job_index
);

CREATE INDEX IF NOT EXISTS idx_orchestration_graph_runs_current_checkpoint
ON orchestration_graph_runs (owner_user_id, current_checkpoint_id)
WHERE current_checkpoint_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_orchestration_graph_runs_purge
ON orchestration_graph_runs (purge_after)
WHERE purge_after IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_orchestration_checkpoints_owner_run_sequence
ON orchestration_checkpoints (
    owner_user_id,
    graph_invocation_id,
    checkpoint_sequence DESC
);

CREATE INDEX IF NOT EXISTS idx_orchestration_checkpoints_purge
ON orchestration_checkpoints (purge_after)
WHERE purge_after IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_orchestration_interrupt_requests_pending_owner
ON orchestration_interrupt_requests (
    owner_user_id,
    created_at,
    interrupt_request_id
)
WHERE interrupt_status = 'pending';

CREATE INDEX IF NOT EXISTS idx_orchestration_interrupt_requests_expiry
ON orchestration_interrupt_requests (expires_at)
WHERE expires_at IS NOT NULL AND interrupt_status = 'pending';
