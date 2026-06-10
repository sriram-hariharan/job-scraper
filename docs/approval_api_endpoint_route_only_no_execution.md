# Approval API endpoint route only no execution

## A. Current implementation scope

This phase adds the smallest safe approval decision endpoint route only.

The endpoint route path is `POST /api/agentic-approvals/{approval_request_id}/decision`.

The runtime route file is `src/app/api.py`.

The endpoint uses the existing storage module path `src/storage/agentic_approvals/store.py` only through an injected connection boundary. The default connection provider returns no live connection, so the endpoint returns a safe blocked 503 response unless a test or later approved runtime phase injects a connection.

No database connection is opened at import time. No SQL is executed at import time.

## B. Endpoint behavior

The endpoint accepts a JSON body with `reviewer_id`, `review_decision`, optional `review_reason`, and optional `decided_at`.

The endpoint validates `review_decision` against the existing storage contract and does not invent unsupported status values.

When a safe connection is injected, the endpoint calls the existing approval decision storage function for decision recording only.

When no safe connection is available, the endpoint returns a deterministic blocked response with execution, queue mutation, application submission, and scheduler/background execution disabled.

## C. Runtime isolation confirmation

This phase does not add UI actions, queue mutation, execution enablement, mutation execution, application submission, scheduler/background execution, SQL changes, migration execution, or storage module changes.

Existing queue safety gates remain preserved.

Existing execution safety gates remain preserved.

The endpoint implementation preserves `idempotency_key` behavior by leaving creation/idempotency logic in the existing storage module and not altering that contract.

The endpoint implementation preserves `approval_status` constraints by validating decisions against the existing storage module decision status set.

## D. Testing boundary

Endpoint route tests use fakes or mocks only.

Endpoint route tests do not require live database access.

The tests monkeypatch the internal connection provider and storage decision boundary.

## E. Future phase boundaries

UI action implementation must be separate future phase.

Execution enablement must be separate future phase.

Migration execution must be separate future phase.

## F. Verification contract phrases

- Approval API endpoint route only no execution: PASS
- Endpoint implementation: ENDPOINT_ROUTE_ONLY
- Endpoint route path: /api/agentic-approvals/{approval_request_id}/decision
- Runtime route file: src/app/api.py
- Storage module path: src/storage/agentic_approvals/store.py
- UI run/approve/reject buttons: NO_GO
- Queue mutation: NO_GO
- Execution enablement: NO_GO
- Mutation execution: NO_GO
- Application submission: NO_GO
- Scheduler/background execution: NO_GO
- Live execution: NO_GO
- no UI action added
- no queue mutation added
- no execution enabled
- no mutation execution enabled
- no application submission enabled
- no SQL file modified in this phase
- no storage module modified in this phase
- endpoint route tests use fakes or mocks only
- endpoint route tests do not require live database
- endpoint implementation preserves existing queue safety gates
- endpoint implementation preserves existing execution safety gates
- endpoint implementation preserves idempotency_key behavior
- endpoint implementation preserves approval_status constraints
- UI action implementation must be separate future phase
- execution enablement must be separate future phase
- migration execution must be separate future phase

## Step 133A approval API endpoint route only release safety checkpoint

See `docs/approval_api_endpoint_route_only_release_safety_checkpoint.md`.

This release checkpoint is docs/tests only. It does not modify runtime files, storage module files, SQL files, queue mutation, execution, mutation execution, application submission, UI actions, scheduler/background execution, or migration execution.
