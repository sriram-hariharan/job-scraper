# Approval Storage Schema Release Safety Checkpoint

Doc path: `docs/approval_storage_schema_release_safety_checkpoint.md`

Phase 106A is a release safety checkpoint only. This phase is docs/tests only and adds no runtime behavior.

Approval storage schema design is complete.

DB schema implementation: NOT_YET.

Migration implementation: NOT_YET.

SQL DDL implementation: NOT_YET.

Storage API implementation: NOT_YET.

Runtime-facing integration scope: DESIGN_ONLY.

## A. Current Checkpoint Scope

This release checkpoint confirms the approval storage schema design is complete while still adding no physical DB schema, migration, SQL DDL, storage API, DB writes, approval endpoints, queue mutation, execution, mutation execution, or application submission.

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

## B. Release Decision

Release checkpoint: PASS.

Approval storage schema design: GO.

The schema contract is ready for final audit and merge-gate review as a design artifact only. It is not an implementation approval for DB schema files, migrations, SQL DDL, storage APIs, DB writes, approval API endpoints, queue mutation, execution, mutation execution, scheduler execution, UI execution actions, or application submission.

## C. Approved Conceptual Schema Contract

The approved conceptual schema includes:

- approval_requests conceptual table
- approval_audit_events conceptual table
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

request payload must not contain secrets

request payload must not store raw credentials

Approval status must be append-audited.

Approval state transitions must be constrained.

Approved requests cannot bypass safety gates.

Approved requests cannot execute if safety gates fail.

approved requests cannot bypass safety gates

approved requests cannot execute if safety gates fail

Application submission remains blocked until later explicit phase.

## D. Status Model Confirmation

The approved status model includes:

- pending
- approved
- denied
- expired
- revoked
- consumed

Approved status alone does not execute work. Consumed approvals must not be reused for duplicate execution, and expired, revoked, or denied approvals must not return to executable states.

## E. Constraint And Index Confirmation

The approved conceptual constraints and indexes include:

- primary key on approval_request_id
- unique idempotency_key
- index on dry_run_artifact_id
- index on user_id or owner_id
- index on approval_status
- index on expires_at
- created_at and updated_at timestamps
- constrained status transitions
- immutable audit events

These remain conceptual constraints only. They do not add DB schema files, migrations, SQL DDL, storage APIs, DB writes, queue mutation, or execution.

## F. Security And Data Minimization Confirmation

Approval request and audit payloads must store only enough data to bind approval to a dry-run artifact, owner, proposed action, safety snapshots, status, idempotency, expiry, and audit trail.

Secrets, raw credentials, bearer tokens, cookies, private keys, source credentials, and application-submission credentials must remain outside approval storage.

Safety gate snapshots should be structured summaries or immutable artifact references, not unbounded raw payload dumps.

## G. Runtime Isolation Confirmation

`workflow_runner.py` remains dry-run only.

The app-service gate remains blocking-only.

The queue gate remains blocking-only.

Blocked results remain non-executing.

No approval API endpoints added.

No approval storage implementation added.

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

## H. Forbidden Next-Step Shortcuts

Do not add DB schema files next unless explicitly approved.

Do not add migrations next unless explicitly approved.

Do not add SQL DDL next unless explicitly approved.

Do not add storage APIs next.

Do not add DB writes next.

Do not enable execution next.

Do not add queue mutation next.

Do not add application submission next.

Do not treat this release checkpoint as permission to implement physical persistence.

## I. Explicit Non-Goals

This checkpoint does not add DB schema files.

This checkpoint does not add migrations.

This checkpoint does not add SQL DDL.

This checkpoint does not add storage APIs.

This checkpoint does not add DB writes.

This checkpoint does not add approval endpoints.

This checkpoint does not add queue mutation.

This checkpoint does not add execution.

This checkpoint does not add mutation execution.

This checkpoint does not add application submission.

This checkpoint does not add scheduler/background execution.

This checkpoint does not add UI run/approve/reject buttons.

This checkpoint does not add LangGraph or an agent framework.

## J. Recommended Next Phase

Recommended next phase: 106B approval storage schema release safety checkpoint final audit and merge gate.

After 106B, recommend: 107A physical approval storage schema design, docs/tests only first.

Only after that, consider migration design, not implementation.

Follow-up physical schema design: `docs/physical_approval_storage_schema_design.md`.

## Decisions

- Release checkpoint: PASS
- Approval storage schema design: GO
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
