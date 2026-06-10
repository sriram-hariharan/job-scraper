# Approval Storage API Design

Doc path: `docs/approval_storage_api_design.md`

Step 118A designs a future approval storage API for the static SQL artifact at `src/storage/agentic_approvals/schema.sql`. This phase is docs/tests only and adds no runtime behavior.

## A. Current design scope

This document is design only. It does not add a Python storage module, storage API implementation, approval storage implementation, approval API endpoint, SQL execution code, migration runner code, DB write, queue mutation, execution, mutation execution, scheduler/background execution, UI run/approve/reject button, or application submission.

No runtime behavior changes in this phase.

No storage API file added.

No storage module added.

No DB writes added.

No queue mutation added.

No execution enabled.

No mutation execution enabled.

No application submission enabled.

No SQL file modified in this phase.

The static SQL artifact remains inert.

## B. Storage API objective

The future storage API should provide explicit, deterministic persistence boundaries for approval requests and approval audit events after a separate implementation phase approves it.

The API should use the schema shape from `src/storage/agentic_approvals/schema.sql` without executing the SQL artifact automatically.

The API should keep approval persistence separate from queue mutation, mutation execution, live execution, scheduler/background execution, UI action handling, and application submission.

## C. Proposed future module location

Proposed future module location: `src/storage/agentic_approvals/store.py`.

That location is proposed only. Storage API implementation must be separate future phase.

The future module should be small, explicit, and limited to approval request and approval audit event persistence helpers.

## D. Proposed public function boundaries

Future public function candidates:

- `create_approval_request(...)` for inserting a pending approval request with an idempotency key.
- `get_approval_request(...)` for reading a request by approval request id or idempotency key.
- `record_approval_audit_event(...)` for appending an audit event tied to an approval request.
- `mark_approval_decision(...)` for recording a reviewed decision only after a separate approval-flow implementation phase approves that boundary.

These are design candidates only and do not add implementation.

## E. Approval request persistence design

The future storage API should persist approval request records using the approved request table fields, including `approval_request_id`, `dry_run_artifact_id`, `owner_id`, `idempotency_key`, `approval_status`, non-secret JSON-compatible safety snapshots, review metadata, and lifecycle timestamps.

The future API must preserve `idempotency_key` behavior and must not create duplicate logical approval requests for the same idempotency key.

The future API must preserve `approval_status` constraints and should validate status names before attempting persistence.

## F. Approval audit event persistence design

The future storage API should append audit events to `agentic_approval_audit_events` with a stable `audit_event_id`, linked `approval_request_id`, event type, actor reference, JSON-compatible event payload, and timestamp.

The future API must preserve audit event foreign key behavior and must not create audit events without an existing approval request.

Audit events should describe approval lifecycle changes without storing secrets or raw credentials.

## G. Idempotency and duplicate protection design

The future storage API should treat `idempotency_key` as the primary duplicate-protection boundary for approval request creation.

On duplicate idempotency keys, the future API should return the existing approval request or raise a deterministic duplicate-result error, depending on the separately approved implementation contract.

Retry behavior must be deterministic and must not create additional approval requests or audit events for the same logical operation.

## H. Transaction boundary design

The future storage API should use explicit transaction boundaries for request creation plus its initial audit event when both are written in one operation.

Approval request writes and audit event writes should either commit together or fail together when they are part of one logical persistence operation.

Transaction code is not implemented in this phase.

## I. Error handling and retry behavior design

The future storage API should classify constraint violations, duplicate idempotency, missing approval requests, stale status transitions, serialization failures, and connection failures into deterministic error categories.

Retryable failures should be limited to infrastructure or serialization cases that cannot duplicate durable approval records.

Non-retryable failures should preserve stage-level observability without falling through to execution, queue mutation, DB writes outside the approved API boundary, or application submission.

## J. Observability and logging design

The future storage API must preserve stage-level observability.

Logs and diagnostic payloads should include non-secret identifiers, operation names, validation statuses, reason codes, and timing fields.

Observability should not include secrets, raw credentials, full environment values, or unredacted payloads that could expose sensitive data.

## K. Security and data-safety design

The future storage API must not store secrets.

The future storage API must not store raw credentials.

The API should persist only non-secret approval metadata, non-secret safety snapshots, and JSON-compatible event payloads.

Future implementation must validate payload shape and reject unsafe fields before persistence.

## L. Forbidden implementation shortcuts

Do not add storage API implementation next without a separate implementation phase.

Do not add Python storage modules in this phase.

Do not execute SQL automatically.

Do not add DB writes in this phase.

Do not add approval endpoints or approval storage implementation in this phase.

Do not add queue mutation, execution, mutation execution, scheduler/background execution, UI run/approve/reject buttons, live execution, or application submission.

Do not treat this design as permission to run migrations or touch a database.

## M. Recommended next phase

Recommended next phase: 118B: approval storage API design final audit and merge gate.

After 118B, recommend: 119A: approval storage API design release safety checkpoint, docs/tests only.

Release safety checkpoint: `docs/approval_storage_api_design_release_safety_checkpoint.md`.

Implementation readiness review: `docs/approval_storage_api_implementation_readiness_review.md`.

Module path and function contract proposal: `docs/approval_storage_api_module_path_function_contract_proposal.md`.

Storage API implementation must be separate future phase.

Application integration must be separate future phase.

Migration execution must be separate future phase.

## N. Verification contract phrases

Verification contract phrases

- Approval storage API design: PASS
- Storage API implementation: NOT_YET
- Storage module implementation: NOT_YET
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
- no storage API file added
- no storage module added
- no DB writes added
- no queue mutation added
- no execution enabled
- no mutation execution enabled
- no application submission enabled
- no SQL file modified in this phase
- static SQL artifact remains inert
- storage API must use explicit future approval before implementation
- storage API must not execute SQL automatically
- storage API must preserve idempotency_key behavior
- storage API must preserve approval_status constraints
- storage API must preserve audit event foreign key behavior
- storage API must not store secrets
- storage API must not store raw credentials
- storage API must preserve stage-level observability
- storage API must preserve deterministic behavior
- storage API implementation must be separate future phase
- application integration must be separate future phase
- migration execution must be separate future phase
