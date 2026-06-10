# Approval SQL DDL File Path And Content Proposal

Doc path: `docs/approval_sql_ddl_file_path_content_proposal.md`

Phase 114A is a file path and content proposal only. This phase is docs/tests only and adds no runtime behavior.

## A. Current proposal scope

This proposal names a future SQL DDL file path and documents the expected content outline for approval storage. It does not create the SQL file, migration file, schema file, SQL DDL implementation, storage API, DB write, approval endpoint, queue mutation, execution, mutation execution, scheduler/background execution, UI run/approve/reject button, or application submission.

No runtime behavior changes in this phase.

No SQL file added.

No migration file added.

No DB schema file added.

No SQL DDL added.

No storage API added.

No DB writes added.

No queue mutation added.

No execution enabled.

No mutation execution enabled.

No application submission enabled.

## B. Proposed future SQL DDL file path

Proposed future SQL DDL file path: `src/storage/agentic_approvals/schema.sql`.

This path follows the existing repository convention of keeping storage schema files under `src/storage/<domain>/schema.sql`.

The future SQL DDL file path remains proposed only.

The future SQL DDL content remains proposed only.

The proposed SQL DDL file path must follow existing repository conventions.

The proposed path must not be created until a separate future SQL DDL file implementation phase explicitly approves it.

## C. Proposed content outline

The proposed SQL DDL content outline must be documented.

The future file should contain only reviewed DDL for the approval persistence tables, related constraints, related indexes, and rollback notes or comments if the future implementation phase approves comments.

The future file must not contain SQL execution wrappers, migration runners, seed data, storage API code, application code, approval endpoints, queue mutation code, or scheduler/background execution hooks.

The future SQL DDL must not store secrets.

The future SQL DDL must not store raw credentials.

## D. Proposed table creation order

The proposed SQL DDL must create `agentic_approval_requests` before `agentic_approval_audit_events`.

The request table should contain the stable approval request identifier, dry-run artifact reference, owner/account boundary, idempotency key, approval status, proposed action summary fields, non-secret safety snapshots, review metadata, and lifecycle timestamps.

The audit event table should contain the stable audit event identifier, approval request reference, event type, actor reference, JSON-compatible event payload, and event timestamp.

## E. Proposed rollback order

The proposed rollback must drop `agentic_approval_audit_events` before `agentic_approval_requests`.

The rollback order must preserve the dependency boundary from audit events to approval requests.

Migration execution must be separate future phase.

## F. Proposed constraints

The proposed SQL DDL must include unique idempotency_key.

The proposed SQL DDL must include approval_status constraint.

The proposed SQL DDL must include audit event foreign key behavior.

The proposed SQL DDL should include primary key behavior for `approval_request_id` and `audit_event_id`.

The proposed SQL DDL should keep status-transition enforcement reserved for a future storage/service implementation phase.

## G. Proposed indexes

The proposed SQL DDL should include indexes for `expires_at`, `owner_id`, and `dry_run_artifact_id`.

The proposed SQL DDL may identify approval status, created timestamp, and audit event approval request lookup indexes as review candidates.

Any additional index tuning must be reviewed before implementation.

## H. Proposed validation checks

Future validation should confirm the approved file path matches `src/storage/agentic_approvals/schema.sql` or records an explicitly approved replacement path.

Future validation should confirm the proposed SQL DDL creates `agentic_approval_requests` before `agentic_approval_audit_events`.

Future validation should confirm rollback drops `agentic_approval_audit_events` before `agentic_approval_requests`.

Future validation should confirm unique `idempotency_key`, approval status constraints, audit event foreign key behavior, required indexes, JSON-compatible snapshot fields, and data-safety boundaries.

Future validation should confirm no automatic SQL execution is wired from docs, tests, app services, workflow runner, benchmark, preflight, queue processing, scheduler/background work, or UI actions.

## I. Forbidden implementation shortcuts

Do not add SQL files next unless explicitly approved.

Do not add migration files next unless explicitly approved.

Do not add DB schema files next unless explicitly approved.

Do not add storage APIs next.

Do not add DB writes next.

Do not execute SQL next.

Do not enable execution next.

Do not add queue mutation next.

Do not add application submission next.

Do not treat this proposal as permission to implement or execute SQL DDL.

## J. Recommended next phase

Recommended next phase: 114B approval SQL DDL file path and content proposal final audit and merge gate.

After 114B, recommend: 115A approval SQL DDL file implementation safety checkpoint, docs/tests only first.

File implementation safety checkpoint: `docs/approval_sql_ddl_file_implementation_safety_checkpoint.md`.

SQL DDL file implementation must be separate future phase.

Migration execution must be separate future phase.

## K. Verification contract phrases

Verification contract phrases

- Approval SQL DDL file path and content proposal: PASS
- SQL DDL file path proposal: GO_FOR_REVIEW_ONLY
- SQL DDL content proposal: GO_FOR_REVIEW_ONLY
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
- future SQL DDL file path remains proposed only
- future SQL DDL content remains proposed only
- proposed SQL DDL file path must follow existing repository conventions
- proposed SQL DDL content outline must be documented
- proposed SQL DDL must create agentic_approval_requests before agentic_approval_audit_events
- proposed rollback must drop agentic_approval_audit_events before agentic_approval_requests
- proposed SQL DDL must include unique idempotency_key
- proposed SQL DDL must include approval_status constraint
- proposed SQL DDL must include audit event foreign key behavior
- proposed SQL DDL must not store secrets
- proposed SQL DDL must not store raw credentials
- SQL DDL file implementation must be separate future phase
- migration execution must be separate future phase
