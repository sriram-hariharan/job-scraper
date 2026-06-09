# Approval Storage Schema Design

Doc path: `docs/approval_storage_schema_design.md`

Phase 105A is approval storage schema design only. This phase is docs/tests only and adds no runtime behavior.

DB schema implementation: NOT_YET.

Migration implementation: NOT_YET.

SQL DDL implementation: NOT_YET.

Storage API implementation: NOT_YET.

Runtime-facing integration scope: DESIGN_ONLY.

## A. Current Design Scope

This design defines the conceptual approval storage schema contract required before any future approval storage implementation, DB schema file, migration, storage API, DB writes, queue mutation, dry-run-to-execute promotion, mutation execution, or application submission can be considered.

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

## B. Conceptual Storage Model

The future storage model should contain two conceptual tables:

- approval_requests conceptual table
- approval_audit_events conceptual table

These are conceptual schema requirements only. They are not DB schema files, migrations, SQL DDL, storage APIs, or runtime integrations.

## C. approval_requests Contract

The approval_requests conceptual table must define approval request records with these required fields and constraints:

- approval_request_id stable identifier
- dry_run_artifact_id required
- user_id or owner_id required
- proposed_action_type required
- proposed_action_summary required
- safety_gate_snapshot required
- fixture_validation_snapshot required
- app_service_safety_gate_snapshot required
- queue_safety_gate_snapshot required
- idempotency_key required and unique
- approval_status required
- reviewer_id nullable until reviewed
- review_decision nullable until reviewed
- review_reason nullable until reviewed
- expires_at required
- created_at required
- updated_at required
- approved_at nullable
- denied_at nullable
- revoked_at nullable
- audit_event_id references

The request payload must not contain secrets.

The request payload must not store raw credentials.

Approved requests cannot bypass safety gates.

Approved requests cannot execute if safety gates fail.

approved requests cannot bypass safety gates

approved requests cannot execute if safety gates fail

Application submission remains blocked until later explicit phase.

## D. approval_audit_events Contract

The approval_audit_events conceptual table must append-audit approval lifecycle changes without permitting silent overwrite of historical decisions.

Approval status must be append-audited.

Audit event records should include an audit_event_id, approval_request_id reference, previous status, next status, actor identity, reviewer identity when applicable, decision reason when applicable, timestamp, dry_run_artifact_id, idempotency_key, and non-secret safety snapshot references.

Immutable audit events are required.

Audit payloads must not contain secrets or raw credentials.

## E. Status Model and Transitions

Required status model:

- pending
- approved
- denied
- expired
- revoked
- consumed

Approval state transitions must be constrained.

Constrained status transitions should permit pending to approved, denied, expired, or revoked; approved to consumed, expired, or revoked; and should reject transitions from denied, expired, revoked, or consumed back into executable states.

Consumed approvals must not be reused for duplicate execution.

## F. Index and Constraint Strategy

Required indexes/constraints conceptually:

- primary key on approval_request_id
- unique idempotency_key
- index on dry_run_artifact_id
- index on user_id or owner_id
- index on approval_status
- index on expires_at
- created_at and updated_at timestamps
- constrained status transitions
- immutable audit events

These index and constraint requirements are conceptual only and do not add SQL DDL, migrations, DB schema files, storage APIs, DB writes, or runtime behavior in this phase.

## G. Security and Data Minimization

Request and audit payloads must store only enough data to bind approval to a dry-run artifact, owner, proposed action, safety snapshots, status, idempotency, expiry, and audit trail.

Request payload must not contain secrets.

Request payload must not store raw credentials.

Secrets, raw credentials, bearer tokens, cookies, private keys, and source credentials must remain outside approval storage.

Safety gate snapshots should be structured summaries or immutable artifact references, not unbounded raw payload dumps.

## H. Execution Blocking Rules

DB writes: NO_GO.

Queue mutation: NO_GO.

Execution enablement: NO_GO.

Mutation execution: NO_GO.

Application submission: NO_GO.

Scheduler/background execution: NO_GO.

UI run/approve/reject buttons: NO_GO.

Live execution: NO_GO.

Approved requests cannot bypass safety gates.

Approved requests cannot execute if safety gates fail.

Approval storage schema design does not enable dry-run-to-execute promotion.

## I. Forbidden Shortcuts

Do not add DB schema files next unless explicitly approved.

Do not add migrations next unless explicitly approved.

Do not add SQL DDL next unless explicitly approved.

Do not add storage APIs next.

Do not add DB writes next.

Do not enable execution next.

Do not add queue mutation next.

Do not add application submission next.

Do not treat conceptual tables as implemented persistence.

## J. Recommended Next Phase

Recommended next phase: 105B approval storage schema design final audit and merge gate.

After 105B, recommend: 106A approval storage schema release safety checkpoint, docs/tests only.

Only after that, consider physical schema or migration design, not implementation.

Release safety checkpoint: `docs/approval_storage_schema_release_safety_checkpoint.md`.

## Decisions

- Approval storage schema design: PASS
- DB schema implementation: NOT_YET
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
