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
        CHECK (run_status IN (
            'running', 'awaiting_decision', 'decision_recorded',
            'resume_authorized', 'resume_consumed', 'decision_rejected',
            'resumed', 'completed', 'failed', 'cancelled'
        )),
    CONSTRAINT ck_orchestration_graph_runs_current_checkpoint
        CHECK (
            (run_status = 'running' AND current_checkpoint_id IS NULL)
            OR
            (run_status <> 'running' AND current_checkpoint_id IS NOT NULL)
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
        CHECK (interrupt_status IN (
            'awaiting_decision', 'decision_recorded', 'resume_authorized',
            'resume_consumed', 'decision_rejected', 'cancelled', 'expired'
        )),
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
WHERE interrupt_status = 'awaiting_decision';

CREATE INDEX IF NOT EXISTS idx_orchestration_interrupt_requests_expiry
ON orchestration_interrupt_requests (expires_at)
WHERE expires_at IS NOT NULL AND interrupt_status = 'awaiting_decision';

CREATE TABLE IF NOT EXISTS orchestration_human_decisions (
    decision_id TEXT PRIMARY KEY,
    graph_invocation_id TEXT NOT NULL REFERENCES orchestration_graph_runs (graph_invocation_id),
    checkpoint_id TEXT NOT NULL REFERENCES orchestration_checkpoints (checkpoint_id),
    interrupt_request_id TEXT NOT NULL REFERENCES orchestration_interrupt_requests (interrupt_request_id),
    owner_user_id TEXT NOT NULL,
    pipeline_run_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    job_index INTEGER NOT NULL CHECK (job_index >= 0),
    selected_resume_id TEXT NOT NULL,
    operator_review_artifact_digest TEXT NOT NULL CHECK (operator_review_artifact_digest ~ '^[0-9a-f]{64}$'),
    decision_value TEXT NOT NULL CHECK (decision_value IN ('continue_read_only', 'needs_revision', 'cancel')),
    actor_id TEXT NOT NULL,
    client_idempotency_key TEXT NOT NULL,
    expected_interrupt_status TEXT NOT NULL CHECK (expected_interrupt_status = 'awaiting_decision'),
    expected_interrupt_version INTEGER NOT NULL CHECK (expected_interrupt_version >= 0),
    expected_run_lock_version INTEGER NOT NULL CHECK (expected_run_lock_version >= 0),
    decision_record_status TEXT NOT NULL CHECK (decision_record_status IN ('recorded', 'rejected')),
    reason TEXT NOT NULL DEFAULT '' CHECK (octet_length(reason) <= 4096),
    rejection_code TEXT NOT NULL DEFAULT '',
    application_authorization BOOLEAN NOT NULL DEFAULT FALSE CHECK (application_authorization = FALSE),
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_orchestration_human_decisions_idempotency UNIQUE (interrupt_request_id, client_idempotency_key)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_orchestration_human_decisions_current
ON orchestration_human_decisions (interrupt_request_id)
WHERE decision_record_status = 'recorded';

CREATE TABLE IF NOT EXISTS orchestration_resume_authorizations (
    authorization_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL UNIQUE REFERENCES orchestration_human_decisions (decision_id),
    graph_invocation_id TEXT NOT NULL REFERENCES orchestration_graph_runs (graph_invocation_id),
    checkpoint_id TEXT NOT NULL REFERENCES orchestration_checkpoints (checkpoint_id),
    interrupt_request_id TEXT NOT NULL REFERENCES orchestration_interrupt_requests (interrupt_request_id),
    owner_user_id TEXT NOT NULL,
    pipeline_run_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    job_index INTEGER NOT NULL CHECK (job_index >= 0),
    selected_resume_id TEXT NOT NULL,
    operator_review_artifact_digest TEXT NOT NULL CHECK (operator_review_artifact_digest ~ '^[0-9a-f]{64}$'),
    decision_value TEXT NOT NULL CHECK (decision_value = 'continue_read_only'),
    safe_next_node_key TEXT NOT NULL CHECK (safe_next_node_key = 'finalize'),
    authorization_token_hash TEXT NOT NULL CHECK (authorization_token_hash ~ '^[0-9a-f]{64}$'),
    authorization_status TEXT NOT NULL CHECK (authorization_status IN ('authorized', 'consumed', 'expired', 'revoked')),
    lock_version INTEGER NOT NULL DEFAULT 0 CHECK (lock_version >= 0),
    read_only BOOLEAN NOT NULL DEFAULT TRUE CHECK (read_only = TRUE),
    application_authorization BOOLEAN NOT NULL DEFAULT FALSE CHECK (application_authorization = FALSE),
    resume_text_mutation_authorization BOOLEAN NOT NULL DEFAULT FALSE CHECK (resume_text_mutation_authorization = FALSE),
    queue_mutation_authorization BOOLEAN NOT NULL DEFAULT FALSE CHECK (queue_mutation_authorization = FALSE),
    operator_state_mutation_authorization BOOLEAN NOT NULL DEFAULT FALSE CHECK (operator_state_mutation_authorization = FALSE),
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS orchestration_resume_consumptions (
    consumption_id TEXT PRIMARY KEY,
    authorization_id TEXT NOT NULL UNIQUE REFERENCES orchestration_resume_authorizations (authorization_id),
    decision_id TEXT NOT NULL REFERENCES orchestration_human_decisions (decision_id),
    graph_invocation_id TEXT NOT NULL REFERENCES orchestration_graph_runs (graph_invocation_id),
    checkpoint_id TEXT NOT NULL REFERENCES orchestration_checkpoints (checkpoint_id),
    interrupt_request_id TEXT NOT NULL REFERENCES orchestration_interrupt_requests (interrupt_request_id),
    owner_user_id TEXT NOT NULL,
    pipeline_run_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    job_index INTEGER NOT NULL CHECK (job_index >= 0),
    selected_resume_id TEXT NOT NULL,
    resume_invocation_id TEXT NOT NULL UNIQUE,
    consumer_instance_id TEXT NOT NULL,
    claimed_at TIMESTAMPTZ NOT NULL,
    claim_status TEXT NOT NULL CHECK (claim_status IN ('claimed', 'reconciled', 'failed')),
    expected_authorization_version INTEGER NOT NULL CHECK (expected_authorization_version >= 0),
    application_authorization BOOLEAN NOT NULL DEFAULT FALSE CHECK (application_authorization = FALSE)
);

CREATE INDEX IF NOT EXISTS idx_orchestration_human_decisions_owner_interrupt
ON orchestration_human_decisions (owner_user_id, interrupt_request_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orchestration_resume_authorizations_owner_status
ON orchestration_resume_authorizations (owner_user_id, authorization_status, expires_at);
CREATE INDEX IF NOT EXISTS idx_orchestration_resume_consumptions_owner_authorization
ON orchestration_resume_consumptions (owner_user_id, authorization_id);

CREATE TABLE IF NOT EXISTS orchestration_node_attempts (
    node_attempt_id TEXT PRIMARY KEY,
    graph_invocation_id TEXT NOT NULL REFERENCES orchestration_graph_runs (graph_invocation_id),
    input_checkpoint_id TEXT NOT NULL REFERENCES orchestration_checkpoints (checkpoint_id),
    output_checkpoint_id TEXT REFERENCES orchestration_checkpoints (checkpoint_id),
    owner_user_id TEXT NOT NULL,
    pipeline_run_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    job_index INTEGER NOT NULL CHECK (job_index >= 0),
    selected_resume_id TEXT NOT NULL,
    node_key TEXT NOT NULL,
    attempt_number INTEGER NOT NULL CHECK (attempt_number >= 1),
    resume_invocation_id TEXT,
    attempt_status TEXT NOT NULL CHECK (attempt_status IN ('pending', 'claimed', 'succeeded', 'failed', 'abandoned')),
    lease_owner_id TEXT,
    lease_acquired_at TIMESTAMPTZ,
    lease_expires_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER CHECK (duration_ms IS NULL OR duration_ms >= 0),
    input_digest TEXT NOT NULL CHECK (input_digest ~ '^[0-9a-f]{64}$'),
    output_digest TEXT CHECK (output_digest IS NULL OR output_digest ~ '^[0-9a-f]{64}$'),
    error_code TEXT NOT NULL DEFAULT '' CHECK (octet_length(error_code) <= 256),
    error_detail TEXT NOT NULL DEFAULT '' CHECK (octet_length(error_detail) <= 4096),
    lock_version INTEGER NOT NULL DEFAULT 0 CHECK (lock_version >= 0),
    application_authorization BOOLEAN NOT NULL DEFAULT FALSE CHECK (application_authorization = FALSE),
    mutation_authorization BOOLEAN NOT NULL DEFAULT FALSE CHECK (mutation_authorization = FALSE),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_orchestration_node_attempt_identity
        UNIQUE (graph_invocation_id, input_checkpoint_id, node_key, attempt_number),
    CONSTRAINT ck_orchestration_node_attempt_output
        CHECK (
            (attempt_status = 'succeeded' AND output_checkpoint_id IS NOT NULL AND output_digest IS NOT NULL)
            OR
            (attempt_status <> 'succeeded' AND output_checkpoint_id IS NULL AND output_digest IS NULL)
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_orchestration_node_attempt_success
ON orchestration_node_attempts (graph_invocation_id, input_checkpoint_id, node_key)
WHERE attempt_status = 'succeeded';

CREATE TABLE IF NOT EXISTS orchestration_terminal_results (
    terminal_result_id TEXT PRIMARY KEY,
    graph_invocation_id TEXT NOT NULL UNIQUE REFERENCES orchestration_graph_runs (graph_invocation_id),
    terminal_checkpoint_id TEXT NOT NULL REFERENCES orchestration_checkpoints (checkpoint_id),
    owner_user_id TEXT NOT NULL,
    pipeline_run_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    job_index INTEGER NOT NULL CHECK (job_index >= 0),
    selected_resume_id TEXT NOT NULL,
    graph_state_schema_version TEXT NOT NULL,
    checkpoint_schema_version TEXT NOT NULL,
    terminal_status TEXT NOT NULL CHECK (terminal_status IN ('completed', 'failed', 'cancelled')),
    result_digest TEXT NOT NULL CHECK (result_digest ~ '^[0-9a-f]{64}$'),
    result_metadata_json JSONB NOT NULL CHECK (
        jsonb_typeof(result_metadata_json) = 'object'
        AND octet_length(result_metadata_json::text) <= 262144
    ),
    final_node_order_json JSONB NOT NULL CHECK (jsonb_typeof(final_node_order_json) = 'array'),
    failure_code TEXT NOT NULL DEFAULT '' CHECK (
        octet_length(failure_code) <= 256
        AND (
            (terminal_status = 'failed' AND failure_code <> '')
            OR
            (terminal_status <> 'failed' AND failure_code = '')
        )
    ),
    application_authorization BOOLEAN NOT NULL DEFAULT FALSE CHECK (application_authorization = FALSE),
    completed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS orchestration_lifecycle_events (
    event_id TEXT PRIMARY KEY,
    graph_invocation_id TEXT NOT NULL REFERENCES orchestration_graph_runs (graph_invocation_id),
    checkpoint_id TEXT REFERENCES orchestration_checkpoints (checkpoint_id),
    interrupt_request_id TEXT REFERENCES orchestration_interrupt_requests (interrupt_request_id),
    decision_id TEXT REFERENCES orchestration_human_decisions (decision_id),
    authorization_id TEXT REFERENCES orchestration_resume_authorizations (authorization_id),
    consumption_id TEXT REFERENCES orchestration_resume_consumptions (consumption_id),
    node_attempt_id TEXT REFERENCES orchestration_node_attempts (node_attempt_id),
    terminal_result_id TEXT REFERENCES orchestration_terminal_results (terminal_result_id),
    owner_user_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'graph_run_created', 'checkpoint_committed', 'interrupt_created',
        'decision_recorded', 'decision_rejected', 'authorization_created',
        'authorization_consumed', 'node_attempt_claimed',
        'node_attempt_succeeded', 'node_attempt_failed',
        'terminal_result_recorded', 'recovery_claim_recorded'
    )),
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_sequence INTEGER NOT NULL CHECK (event_sequence >= 0),
    event_payload_json JSONB NOT NULL CHECK (
        jsonb_typeof(event_payload_json) = 'object'
        AND octet_length(event_payload_json::text) <= 262144
    ),
    event_timestamp TIMESTAMPTZ NOT NULL,
    projection_status TEXT NOT NULL DEFAULT 'pending' CHECK (projection_status IN ('pending', 'projected', 'failed')),
    projected_at TIMESTAMPTZ,
    projection_retry_count INTEGER NOT NULL DEFAULT 0 CHECK (projection_retry_count >= 0),
    CONSTRAINT uq_orchestration_lifecycle_event_sequence
        UNIQUE (graph_invocation_id, aggregate_type, aggregate_id, event_sequence)
);

CREATE INDEX IF NOT EXISTS idx_orchestration_node_attempts_owner_recovery
ON orchestration_node_attempts (owner_user_id, graph_invocation_id, attempt_status, lease_expires_at);
CREATE INDEX IF NOT EXISTS idx_orchestration_terminal_results_owner_graph
ON orchestration_terminal_results (owner_user_id, graph_invocation_id);
CREATE INDEX IF NOT EXISTS idx_orchestration_lifecycle_events_owner_projection
ON orchestration_lifecycle_events (owner_user_id, graph_invocation_id, projection_status, event_sequence);
