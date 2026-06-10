# Approval UI action only no execution

## A. Current implementation scope

This phase adds a UI action only for approval decision recording from Agentic Review.

The UI action is implemented in `src/app/static/agentic_review.js`.

The UI action targets the existing endpoint route path `POST /api/agentic-approvals/{approval_request_id}/decision`.

Runtime route file: `src/app/api.py`.

Storage module path: `src/storage/agentic_approvals/store.py`.

## B. UI action behavior

The UI renders an approval decision panel in the existing operator approval mock area.

The panel supports the backend-supported decision values `approved`, `denied`, and `revoked`.

The UI action sends only `reviewer_id`, `review_decision`, optional `review_reason`, and optional `decided_at` to the existing approval decision endpoint.

The UI action calls approval decision endpoint only.

## C. Safe blocked identity behavior

No safe reviewer identity is exposed directly by the Agentic Review page DOM or payload in this phase.

The implementation checks existing UI state for a real current-user `user_id`. When no safe reviewer identity is available, the approval action remains disabled and displays a deterministic blocked message.

The implementation also requires an existing approval request id. When no approval request id is available, the approval action remains disabled and displays a deterministic blocked message.

## D. Runtime isolation confirmation

This phase does not modify API routes, storage modules, SQL files, migrations, migration runners, storage schema, or dependencies.

This phase does not add queue mutation, execution enablement, mutation execution, application submission, scheduler/background execution, or live execution.

The UI action preserves existing queue safety gates.

The UI action preserves existing execution safety gates.

The UI action preserves `idempotency_key` behavior by not changing approval request creation or idempotency logic.

The UI action preserves `approval_status` constraints by using only the existing backend-supported decision values.

The UI action preserves stage-level observability and deterministic behavior through deterministic disabled states, status messages, and endpoint-only request construction.

## E. Future phase boundaries

Execution enablement must be separate future phase.

Migration execution must be separate future phase.

## F. Verification contract phrases

- Approval UI action only no execution: PASS
- UI action implementation: UI_ACTION_ONLY
- Endpoint route path: /api/agentic-approvals/{approval_request_id}/decision
- Runtime route file: src/app/api.py
- UI asset path: src/app/static/agentic_review.js
- Storage module path: src/storage/agentic_approvals/store.py
- Queue mutation: NO_GO
- Execution enablement: NO_GO
- Mutation execution: NO_GO
- Application submission: NO_GO
- Scheduler/background execution: NO_GO
- Live execution: NO_GO
- no API route modified in this phase unless blocked and explicitly documented
- no storage module modified in this phase
- no SQL file modified in this phase
- no queue mutation added
- no execution enabled
- no mutation execution enabled
- no application submission enabled
- UI action calls approval decision endpoint only
- UI action preserves existing queue safety gates
- UI action preserves existing execution safety gates
- UI action preserves idempotency_key behavior
- UI action preserves approval_status constraints
- UI action preserves stage-level observability
- UI action preserves deterministic behavior
- execution enablement must be separate future phase
- migration execution must be separate future phase

## Step 137A approval UI action only release safety checkpoint

See `docs/approval_ui_action_only_release_safety_checkpoint.md`.

This release checkpoint is docs/tests only. It does not modify UI files, runtime API files, storage module files, SQL files, queue mutation, execution, mutation execution, application submission, scheduler/background execution, or migration execution.
