# Physical Approval Storage Schema Design

Doc path: `docs/physical_approval_storage_schema_design.md`

Phase 107A is physical approval storage schema design only. This phase is docs/tests only and adds no runtime behavior.

Physical DB schema implementation: NOT_YET.

Migration implementation: NOT_YET.

SQL DDL implementation: NOT_YET.

Storage API implementation: NOT_YET.

Runtime-facing integration scope: DESIGN_ONLY.

## A. Current Design Scope

This design maps the conceptual approval storage model into a future physical schema plan for table names, columns, data types, constraints, indexes, migration ordering, rollback, and tests.

No runtime behavior changes in this phase.

No DB schema file added.

No migration added.

No SQL DDL added.

No storage API added.

No DB writes added.

No queue mutation added.

No execution enabled.

No mutation execution enabled.

No application submission enabled.

No scheduler/background execution enabled.

No UI run/approve/reject buttons enabled.

`workflow_runner.py` remains dry-run only.

The app-service gate remains blocking-only.

The queue gate remains blocking-only.

Blocked results remain non-executing.

## B. Physical Table Plan

The future physical schema plan includes these tables:

- table `agentic_approval_requests`
- table `agentic_approval_audit_events`

This phase does not create either table. The names are design targets only and require later explicit schema and migration phases before implementation.

## C. Approval Requests Table Plan

The future `agentic_approval_requests` table should contain:

- `agentic_approval_requests.approval_request_id`
- `agentic_approval_requests.dry_run_artifact_id`
- `agentic_approval_requests.owner_id`
- `agentic_approval_requests.proposed_action_type`
- `agentic_approval_requests.proposed_action_summary`
- `agentic_approval_requests.safety_gate_snapshot_json`
- `agentic_approval_requests.fixture_validation_snapshot_json`
- `agentic_approval_requests.app_service_safety_gate_snapshot_json`
- `agentic_approval_requests.queue_safety_gate_snapshot_json`
- `agentic_approval_requests.idempotency_key`
- `agentic_approval_requests.approval_status`
- `agentic_approval_requests.reviewer_id`
- `agentic_approval_requests.review_decision`
- `agentic_approval_requests.review_reason`
- `agentic_approval_requests.expires_at`
- `agentic_approval_requests.created_at`
- `agentic_approval_requests.updated_at`
- `agentic_approval_requests.approved_at`
- `agentic_approval_requests.denied_at`
- `agentic_approval_requests.revoked_at`

Approval request rows must bind a dry-run artifact, owner, proposed action, safety snapshots, idempotency key, status, expiry, and review metadata without storing secrets or raw credentials.

## D. Approval Audit Events Table Plan

The future `agentic_approval_audit_events` table should contain:

- `agentic_approval_audit_events.audit_event_id`
- `agentic_approval_audit_events.approval_request_id`
- `agentic_approval_audit_events.event_type`
- `agentic_approval_audit_events.event_actor_id`
- `agentic_approval_audit_events.event_payload_json`
- `agentic_approval_audit_events.created_at`

Audit event rows must be append-only and must reference approval requests without enabling execution, queue mutation, DB writes in this phase, or application submission.

## E. Type Strategy

Identifiers use text or UUID consistently.

Status fields use constrained text/enums conceptually.

Snapshot fields use JSON-compatible storage.

Timestamps are timezone-aware.

Large raw credentials are forbidden.

Secrets are forbidden.

Raw resume/application submission payloads are out of scope.

## F. Constraint And Index Strategy

The future physical schema should include these constraints and indexes:

- primary key on approval_request_id
- primary key on audit_event_id
- unique idempotency_key
- foreign key from audit events to approval requests
- index on dry_run_artifact_id
- index on owner_id
- index on approval_status
- index on expires_at
- index on created_at
- constrained status values
- constrained status transitions handled by storage/service layer in future phase
- audit events are append-only
- snapshots are immutable after request creation

These are physical schema design requirements only. No DB schema file, migration, SQL DDL, storage API, or DB write is added in this phase.

## G. Migration Ordering And Rollback Plan

Migration ordering must create approval_requests before approval_audit_events.

Rollback must drop audit table before request table.

migration ordering must create approval_requests before approval_audit_events

rollback must drop audit table before request table

Migration must be separate future phase.

SQL DDL must be separate future phase.

No migration file added in this phase.

No SQL file added in this phase.

no migration file added in this phase

no SQL file added in this phase

The future migration test plan should verify table creation order, foreign-key dependencies, unique idempotency key behavior, rollback order, timestamp defaults, constrained status values, and immutable audit event behavior before any implementation can be considered.

## H. Security And Data Minimization

Approval request and audit event rows should store only approval metadata, non-secret safety snapshots, stable artifact references, idempotency data, status, review metadata, and audit event metadata.

Large raw credentials are forbidden.

Secrets are forbidden.

secrets are forbidden

Raw resume/application submission payloads are out of scope.

Application submission remains blocked until later explicit phase.

Approved requests cannot bypass safety gates.

Approved requests cannot execute if safety gates fail.

## I. Forbidden Shortcuts

Do not add DB schema files next unless explicitly approved.

Do not add migrations next unless explicitly approved.

Do not add SQL DDL next unless explicitly approved.

Do not add storage APIs next.

Do not add DB writes next.

Do not enable execution next.

Do not add queue mutation next.

Do not add application submission next.

Do not treat this physical schema design as permission to implement persistence.

## J. Recommended Next Phase

Recommended next phase: 107B physical approval storage schema design final audit and merge gate.

After 107B, recommend: 108A physical approval storage schema design release safety checkpoint, docs/tests only.

Only after that, consider migration design, not implementation.

## Decisions

- Physical approval storage schema design: PASS
- Physical DB schema implementation: NOT_YET
- Migration implementation: NOT_YET
- SQL DDL implementation: NOT_YET
- Storage API implementation: NOT_YET
- Runtime-facing integration scope: DESIGN_ONLY
- DB writes: NO_GO
- Queue mutation: NO_GO
- Execution enablement: NO_GO
- Mutation execution: NO_GO
- Application submission: NO_GO
- Scheduler/background execution: NO_GO
- UI run/approve/reject buttons: NO_GO
- Live execution: NO_GO
