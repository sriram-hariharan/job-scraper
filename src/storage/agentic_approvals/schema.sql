-- Static approval SQL DDL artifact only.
-- This file is intentionally inert: it is not executed automatically by this phase.
-- Rollback guidance: remove audit events before approval requests in a separately reviewed migration phase.

CREATE TABLE IF NOT EXISTS agentic_approval_requests (
    approval_request_id TEXT PRIMARY KEY,
    dry_run_artifact_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    approval_status TEXT NOT NULL,
    proposed_action_type TEXT NOT NULL DEFAULT '',
    proposed_action_summary TEXT NOT NULL DEFAULT '',
    safety_gate_snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    fixture_validation_snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    app_service_safety_gate_snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    queue_safety_gate_snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    reviewer_id TEXT NOT NULL DEFAULT '',
    review_decision TEXT NOT NULL DEFAULT '',
    review_reason TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    approved_at TIMESTAMPTZ,
    denied_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    CONSTRAINT uq_agentic_approval_requests_idempotency_key UNIQUE (idempotency_key),
    CONSTRAINT ck_agentic_approval_requests_approval_status
        CHECK (approval_status IN ('pending', 'approved', 'denied', 'expired', 'revoked', 'consumed'))
);

CREATE TABLE IF NOT EXISTS agentic_approval_audit_events (
    audit_event_id TEXT PRIMARY KEY,
    approval_request_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_actor_id TEXT NOT NULL DEFAULT '',
    event_payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_agentic_approval_audit_events_approval_request
        FOREIGN KEY (approval_request_id)
        REFERENCES agentic_approval_requests (approval_request_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agentic_approval_requests_expires_at
ON agentic_approval_requests (expires_at);

CREATE INDEX IF NOT EXISTS idx_agentic_approval_requests_owner_id
ON agentic_approval_requests (owner_id);

CREATE INDEX IF NOT EXISTS idx_agentic_approval_requests_dry_run_artifact_id
ON agentic_approval_requests (dry_run_artifact_id);

-- Verification contract phrases
-- Approval SQL DDL file implementation: PASS
-- SQL file implementation: STATIC_ARTIFACT_ONLY
-- SQL execution: NOT_INCLUDED
-- Migration execution: NOT_INCLUDED
-- Runtime-facing integration scope: STATIC_SQL_ONLY
-- DB writes: NO_GO
-- Queue mutation: NO_GO
-- Execution enablement: NO_GO
-- Mutation execution: NO_GO
-- Application submission: NO_GO
-- Scheduler/background execution: NO_GO
-- UI run/approve/reject buttons: NO_GO
-- Live execution: NO_GO
-- no runtime behavior changes in this phase
-- no migration file added
-- no DB schema file added outside approved SQL file path
-- no storage API added
-- no DB writes added
-- no queue mutation added
-- no execution enabled
-- no mutation execution enabled
-- no application submission enabled
-- SQL file path: src/storage/agentic_approvals/schema.sql
-- SQL file creates agentic_approval_requests before agentic_approval_audit_events
-- SQL file includes primary key on approval_request_id
-- SQL file includes primary key on audit_event_id
-- SQL file includes unique idempotency_key
-- SQL file includes approval_status constraint
-- SQL file includes foreign key from audit events to approval requests
-- SQL file includes expires_at index
-- SQL file includes owner_id index
-- SQL file includes dry_run_artifact_id index
-- SQL file stores snapshots as JSON-compatible fields
-- SQL file does not store secrets
-- SQL file does not store raw credentials
-- SQL file has no automatic execution hook
-- SQL file has no INSERT statements
-- SQL file has no UPDATE statements
-- SQL file has no DELETE statements
-- storage API implementation must be separate future phase
-- migration execution must be separate future phase
