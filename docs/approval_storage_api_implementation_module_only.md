# Approval Storage API Implementation Module Only

Doc path: `docs/approval_storage_api_implementation_module_only.md`

Step 123A implements the approval storage API module at the proposed path only. This phase adds direct storage helpers and direct unit tests, but it does not wire the module into runtime behavior.

## A. Current implementation scope

This implementation is storage module only. It adds no runtime integration, app service integration, approval API endpoint, queue integration, scheduler/background integration, UI integration, automatic SQL execution, migration execution, mutation execution, live execution, or application submission.

The static SQL artifact remains `src/storage/agentic_approvals/schema.sql` and is not modified in this phase.

## B. Implemented module path

Implemented module path: `src/storage/agentic_approvals/store.py`.

The storage API file is added only at the proposed path from `docs/approval_storage_api_module_path_function_contract_proposal.md`.

## C. Implemented public function contract

Implemented public functions:

- `create_approval_request(...)`
- `get_approval_request(...)`
- `list_approval_requests(...)`
- `record_approval_audit_event(...)`
- `record_approval_decision(...)`
- `expire_approval_requests(...)`

These functions require an injected DB-API compatible connection. The module does not open a database connection at import time.

## D. No runtime integration confirmation

Runtime-facing integration scope: NOT_INCLUDED.

No runtime behavior changes in this phase.

No app service, route, scheduler, background worker, queue processor, UI action, mutation execution path, or application submission path imports or invokes this module in this phase.

## E. DB write capability boundary

DB write capability: STORAGE_MODULE_ONLY_NOT_INVOKED_BY_PIPELINE.

The storage module contains explicit persistence helpers that execute only when a caller injects a connection and calls a function.

The pipeline does not invoke these helpers in this phase.

## F. SQL execution boundary

The storage API module does not execute SQL at import time.

The storage API module does not open DB connections at import time.

The static SQL artifact remains inert and is not executed automatically.

Migration execution must be separate future phase.

## G. Idempotency behavior

`create_approval_request(...)` preserves `idempotency_key` behavior with an `ON CONFLICT (idempotency_key) DO NOTHING` boundary and a deterministic existing-row lookup.

Repeated calls for the same idempotency key do not create duplicate logical approval requests.

## H. Approval status behavior

The storage module preserves `approval_status` constraints by validating status values before query execution.

Decision recording is limited to reviewed terminal decision statuses.

## I. Audit event behavior

`record_approval_audit_event(...)` appends audit events linked by `approval_request_id`.

The implementation preserves audit event foreign key expectations by keeping audit events tied to approval request identifiers and relying on the schema foreign key for database enforcement.

## J. Transaction boundary behavior

Transaction control remains with the injected connection owner.

The module does not commit, rollback, open a connection, run migrations, mutate queues, enable execution, enable mutation execution, submit applications, or trigger scheduler/background work.

## K. Observability behavior

The storage module preserves stage-level observability with deterministic operation names and reason codes in `ApprovalStorageError`.

Error messages do not include database URLs, credentials, secrets, or raw payload values.

## L. Security and data-safety behavior

The storage API module does not store secrets.

The storage API module does not store raw credentials.

JSON-compatible payload helpers reject sensitive field names before persistence.

## M. Forbidden shortcuts avoided

No runtime integration added.

No queue mutation added.

No execution enabled.

No mutation execution enabled.

No application submission enabled.

No scheduler/background execution added.

No UI run/approve/reject buttons added.

No SQL file modified in this phase.

No automatic SQL execution added.

No migration execution added.

## N. Recommended next phase

Recommended next phase: 123B: approval storage API implementation module-only final audit and merge gate.

After 123B, recommend: 124A: approval storage API implementation release safety checkpoint, docs/tests only.

Release safety checkpoint: `docs/approval_storage_api_implementation_release_safety_checkpoint.md`.

Application integration must be separate future phase.

Migration execution must be separate future phase.

## O. Verification contract phrases

Verification contract phrases

- Approval storage API implementation module only: PASS
- Storage API implementation: STORAGE_MODULE_ONLY
- Storage module implementation: ADDED
- Runtime-facing integration scope: NOT_INCLUDED
- DB write capability: STORAGE_MODULE_ONLY_NOT_INVOKED_BY_PIPELINE
- Queue mutation: NO_GO
- Execution enablement: NO_GO
- Mutation execution: NO_GO
- Application submission: NO_GO
- Scheduler/background execution: NO_GO
- UI run/approve/reject buttons: NO_GO
- Live execution: NO_GO
- no runtime behavior changes in this phase
- storage API file added only at proposed path
- storage module added only at proposed path
- no runtime integration added
- no queue mutation added
- no execution enabled
- no mutation execution enabled
- no application submission enabled
- no SQL file modified in this phase
- static SQL artifact remains inert
- storage API module does not execute SQL at import time
- storage API module does not open DB connections at import time
- storage API module preserves idempotency_key behavior
- storage API module preserves approval_status constraints
- storage API module preserves audit event foreign key behavior
- storage API module does not store secrets
- storage API module does not store raw credentials
- storage API module preserves stage-level observability
- storage API module preserves deterministic behavior
- application integration must be separate future phase
- migration execution must be separate future phase
