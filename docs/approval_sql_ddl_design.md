# Approval SQL DDL Design

Doc path: `docs/approval_sql_ddl_design.md`

Phase 111A is approval SQL DDL design only. This phase is docs/tests only and adds no runtime behavior.

## A. Current Design Scope

This design translates the approved approval storage schema and migration design into a future SQL DDL plan.

It does not add SQL files, migration files, DB schema files, SQL DDL implementation, storage APIs, DB writes, approval API endpoints, approval storage implementation, queue mutation, execution, mutation execution, application submission, scheduler/background execution, or UI run/approve/reject buttons.

`workflow_runner.py` remains dry-run only.

The app-service gate remains blocking-only.

The queue gate remains blocking-only.

Blocked results remain non-executing.

## B. DDL Objective

The DDL objective is to define the future table, column, constraint, index, check constraint, and JSON snapshot storage plan for approval persistence before any implementation phase.

The future SQL DDL must preserve the migration ordering from the approval migration design: create `agentic_approval_requests` before `agentic_approval_audit_events`, and rollback by dropping `agentic_approval_audit_events` before `agentic_approval_requests`.

## C. approval requests table DDL plan

The future SQL DDL plan includes `agentic_approval_requests`.

The future request table should include:

- `approval_request_id` as the stable primary key.
- `dry_run_artifact_id` as the required dry-run artifact reference.
- `owner_id` as the owner/account boundary.
- `idempotency_key` as a required unique request dedupe key.
- `approval_status` as a constrained status value.
- `proposed_action_type` and `proposed_action_summary` for review context.
- `safety_gate_snapshot_json`, `fixture_validation_snapshot_json`, `app_service_safety_gate_snapshot_json`, and `queue_safety_gate_snapshot_json` as JSON-compatible safety snapshots.
- `reviewer_id`, `review_decision`, and `review_reason` for human review metadata.
- `created_at`, `updated_at`, `expires_at`, `approved_at`, `denied_at`, and `revoked_at` for lifecycle tracking.

The table plan forbids secrets and raw credentials. It stores references and safety snapshots, not raw private documents or application-submission credentials.

## D. approval audit events table DDL plan

The future SQL DDL plan includes `agentic_approval_audit_events`.

The future audit table should include:

- `audit_event_id` as the stable primary key.
- `approval_request_id` as the foreign key back to `agentic_approval_requests`.
- `event_type` as a constrained event category.
- `event_actor_id` as the human or system actor reference.
- `event_payload_json` as a JSON-compatible event payload.
- `created_at` as the event timestamp.

Audit events are append-only in concept. Future implementation must avoid updates that rewrite the audit trail.

## E. Constraint Plan

The future DDL plan includes primary key on `approval_request_id`.

The future DDL plan includes primary key on `audit_event_id`.

The future DDL plan includes unique `idempotency_key`.

The future DDL plan includes foreign key from audit events to approval requests.

The future DDL plan includes approval_status constraint.

The future DDL plan should also keep approval request timestamps and status fields internally consistent, with detailed status-transition enforcement reserved for a separate storage/service design and implementation phase.

## F. Index Plan

The future DDL plan includes expires_at index.

The future DDL plan includes owner_id index.

The future DDL plan includes dry_run_artifact_id index.

Additional future index candidates include approval status, created timestamp, and audit event approval request references. Any implementation-specific index tuning must remain a later explicit SQL DDL or migration phase.

## G. Check Constraint And Enum Strategy

The future DDL should use constrained text or database enum strategy for `approval_status`, with values aligned to the approved schema design: pending, approved, denied, expired, revoked, and consumed.

Check constraints are preferred for the first DDL implementation unless a future migration phase explicitly approves enum lifecycle management.

Status transitions must remain constrained by future storage/service logic; this design does not add that logic.

## H. JSON Snapshot Storage Strategy

The DDL plan stores snapshots as JSON-compatible fields.

Safety gate snapshots must be non-secret, bounded, and reviewable.

The DDL plan forbids secrets.

The DDL plan forbids raw credentials.

Raw application-submission credentials, tokens, and private document bodies are out of scope.

## I. Forbidden Shortcuts

Do not add SQL files next unless explicitly approved.

Do not add migration files next unless explicitly approved.

Do not add DB schema files next unless explicitly approved.

Do not add storage APIs next.

Do not add DB writes next.

Do not enable execution next.

Do not add queue mutation next.

Do not add application submission next.

Do not treat this DDL design as permission to implement SQL DDL.

## J. Recommended Next Phase

Recommended next phase: 111B approval SQL DDL design final audit and merge gate.

After 111B, recommend: 112A approval SQL DDL design release safety checkpoint, docs/tests only.

SQL DDL must be separate future phase.

Migration implementation must be separate future phase.

## K. Verification Contract Phrases

Verification contract phrases

- Approval SQL DDL design: PASS
- SQL DDL implementation: NOT_YET
- SQL file implementation: NOT_YET
- Migration implementation: NOT_YET
- Migration file implementation: NOT_YET
- Physical DB schema implementation: NOT_YET
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
- no runtime behavior changes in this phase
- no SQL file added
- no migration file added
- no DB schema file added
- no SQL DDL added
- no storage API added
- no DB writes added
- no queue mutation added
- no execution enabled
- no mutation execution enabled
- no application submission enabled
- workflow_runner.py remains dry-run only
- app-service gate remains blocking-only
- queue gate remains blocking-only
- blocked results remain non-executing
- DDL plan includes agentic_approval_requests
- DDL plan includes agentic_approval_audit_events
- DDL plan includes primary key on approval_request_id
- DDL plan includes primary key on audit_event_id
- DDL plan includes unique idempotency_key
- DDL plan includes foreign key from audit events to approval requests
- DDL plan includes approval_status constraint
- DDL plan includes expires_at index
- DDL plan includes owner_id index
- DDL plan includes dry_run_artifact_id index
- DDL plan stores snapshots as JSON-compatible fields
- DDL plan forbids secrets
- DDL plan forbids raw credentials
- SQL DDL must be separate future phase
- migration implementation must be separate future phase
