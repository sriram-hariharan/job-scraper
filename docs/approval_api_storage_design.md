# Approval API/Storage Design

Doc path: `docs/approval_api_storage_design.md`

Phase 104A is approval API/storage design only. This phase is docs/tests only and adds no runtime behavior.

Approval API implementation: NOT_YET.

Approval storage implementation: NOT_YET.

Runtime-facing integration scope: DESIGN_ONLY.

Exact verifier phrases: explicit human approval required before execution; approval cannot bypass safety gates; approval cannot enable execution if gates are failing.

## A. Current Design Scope

This design defines the approval API and approval storage model required before any future dry-run-to-execute promotion, queue mutation, DB writes, mutation execution, or application submission can be considered.

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

## B. Existing Safety Gates

`workflow_runner.py` remains dry-run only.

The app-service gate remains blocking-only.

The queue gate remains blocking-only.

Blocked results remain non-executing.

Approval cannot bypass safety gates.

Approval cannot enable execution if gates are failing.

Approval cannot enable application submission without later explicit phase.

## C. Approval Object Contract

Explicit human approval required before execution.

An approval request must be tied to a dry-run artifact id.

An approval request must be tied to user ownership.

An approval request must include proposed action summary.

An approval request must include safety gate snapshot.

An approval request must include fixture validation snapshot.

An approval request must include app-service safety gate snapshot.

An approval request must include queue safety gate snapshot.

An approval request must include idempotency key.

An approval request must include expiry timestamp.

An approval request must include approval status.

An approval request must include reviewer identity.

An approval request must include created_at and updated_at.

An approval request must include audit log references.

An approval request must not contain secrets.

An approval request must not store raw credentials.

## D. Approval Status Model

The approval status model must distinguish pending, approved, denied, expired, superseded, and consumed states before any implementation phase.

Approval approval/denial must be auditable.

Approved status alone must not execute work. A later execution phase must re-check safety gates, user ownership, idempotency, expiry, and mutation allowlists.

## E. Approval Audit Model

Approval audit records must capture requester identity, reviewer identity, dry-run artifact id, proposed action summary, safety gate snapshot identifiers, status transitions, timestamps, denial reasons, expiry, and idempotency key.

Audit references must not contain secrets or raw credentials.

## F. Storage Design Constraints

DB schema: NOT_YET.

Migration: NOT_YET.

SQL DDL: NOT_YET.

Storage API: NOT_YET.

No DB schema file added. No migration added. No SQL DDL added. No storage API added. No DB writes added.

Persistent approval storage requires a later schema design and release checkpoint before implementation.

## G. API Design Constraints

Approval API implementation: NOT_YET.

The future API contract must require explicit human approval, user ownership, dry-run artifact binding, safety gate snapshots, fixture validation snapshots, app-service safety gate snapshots, queue safety gate snapshots, idempotency keys, expiry timestamps, audit references, and reviewer identity.

The future API must reject requests that would bypass safety gates, execute with failing gates, store secrets, store raw credentials, or enable application submission without a later explicit phase.

## H. Execution Blocking Rules

DB writes: NO_GO.

Queue mutation: NO_GO.

Execution enablement: NO_GO.

Mutation execution: NO_GO.

Application submission: NO_GO.

Scheduler/background execution: NO_GO.

UI run/approve/reject buttons: NO_GO.

Live execution: NO_GO.

## I. Forbidden Shortcuts

Do not add approval storage next unless 104B passes and explicit approval is given.

Do not add DB writes next.

Do not add queue mutation next.

Do not enable execution next.

Do not add application submission next.

Do not add UI run/approve/reject buttons next without a design/checkpoint phase.

## J. Recommended Next Phase

Recommended next phase: 104B approval API/storage design final audit and merge gate.

After 104B, recommend: 105A approval storage schema design, docs/tests only first.

## Decisions

- Approval API/storage design: PASS
- Approval API implementation: NOT_YET
- Approval storage implementation: NOT_YET
- Runtime-facing integration scope: DESIGN_ONLY
- DB schema: NOT_YET
- Migration: NOT_YET
- SQL DDL: NOT_YET
- Storage API: NOT_YET
- DB writes: NO_GO
- Queue mutation: NO_GO
- Execution enablement: NO_GO
- Mutation execution: NO_GO
- Application submission: NO_GO
- Scheduler/background execution: NO_GO
- UI run/approve/reject buttons: NO_GO
- Live execution: NO_GO
