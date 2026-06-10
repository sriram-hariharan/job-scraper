# Approval Storage API Application Integration Call-Site Wiring Only

Doc path: `docs/approval_storage_api_application_integration_call_site_wiring_only.md`

Step 128A implements approved application integration call-site wiring only. This phase uses the existing approval storage API module from the approved app-service boundary and does not enable execution, queue mutation, mutation execution, application submission, approval endpoints, UI actions, scheduler/background execution, SQL execution, migration execution, SQL files, migration files, DB schema files, or dependencies.

## A. Current implementation scope

The implementation scope is limited to an explicit app-service helper in `src/app/services.py`. The helper is not invoked by existing pipeline, queue, workflow runner, route, UI, scheduler, or background paths.

The helper requires caller-provided safety-gated payloads and an injected DB-API compatible connection. It remains deterministic and unit-testable with fakes or mocks.

## B. Implemented call-site path

Implemented call-site path: `src/app/services.py`.

This is the approved call-site boundary from `docs/approval_storage_api_application_integration_path_call_site_proposal.md`: app services may translate already safety-gated dry-run artifacts into approval request payloads.

No other proposed call-site is implemented. `application_execution_queue.py`, `src/app/static/agentic_review.js`, and `src/agents/workflow_runner.py` are not wired to approval storage in this phase.

## C. Storage API import boundary

The storage API module remains at `src/storage/agentic_approvals/store.py`.

The app-service helper imports the storage module only inside the explicit helper when no fake or injected storage module is provided. The storage API module does not execute SQL at import time and does not open DB connections at import time.

Tests use fake storage modules and do not require a live database.

## D. Request persistence wiring behavior

The app-service helper can call `create_approval_request(...)` only when the supplied app-service safety gate passed, no app-service block is present, required identifiers are present, and optional queue safety gate evidence is not blocking.

The caller must provide `approval_request_id`, `dry_run_artifact_id`, `owner_id`, `idempotency_key`, and `expires_at`. This preserves `idempotency_key` behavior and keeps connection ownership outside the storage module.

Storage failures return deterministic failed status payloads and do not enable execution.

## E. Audit event persistence wiring behavior

The app-service helper can call `record_approval_audit_event(...)` only when an explicit `audit_event_id` is supplied after request persistence succeeds.

The audit payload is bounded, deterministic, and tied to the approval request id, dry-run artifact id, idempotency key, and approved storage call-site.

## F. No execution enablement confirmation

Execution enablement remains NO_GO.

No execution behavior changes in this phase. Blocked or failed storage results remain non-executing with `did_execute_count` `0`, `did_execute_live` `false`, `did_mutate_production` `false`, and `did_write_db` `false`.

## G. No mutation execution confirmation

Mutation execution remains NO_GO.

No mutation execution is enabled. No mutation execution path is added.

## H. No application submission confirmation

Application submission remains NO_GO.

No application submission path is added or enabled.

## I. No approval endpoint confirmation

Approval API endpoints remain NO_GO.

No approval API endpoint is added. The helper is not exposed as a route.

## J. No UI action confirmation

UI run/approve/reject buttons remain NO_GO.

No UI action is added. `src/app/static/agentic_review.js` is not wired to approval storage in this phase.

## K. Queue safety gate preservation

Queue mutation remains NO_GO.

The app-service helper preserves existing queue safety gates by refusing persistence when provided queue safety gate evidence is blocked, failed, or not passed. It does not mutate queue state.

## L. Execution safety gate preservation

The helper preserves existing execution safety gates by requiring an already-passed app-service safety gate payload and by refusing blocked app-service gate output.

`workflow_runner.py` remains dry-run only and is not wired to approval storage in this phase.

## M. Observability and deterministic behavior

The helper returns deterministic fields for call-site name, storage status, reason codes, request persistence, audit event persistence, and non-execution safety flags.

Application integration preserves stage-level observability.

Application integration preserves deterministic behavior.

## N. Security and data-safety behavior

The helper stores only bounded approval metadata and safety gate snapshots passed by the caller. It does not store secrets, raw credentials, database URLs, authorization headers, tokens, API keys, private keys, or unbounded raw payloads.

Static SQL artifact remains inert.

## O. Tests added

Direct call-site wiring tests live in `tests/test_approval_storage_api_application_integration_call_site.py`.

The tests use fakes or mocks only, do not require a live database, confirm storage calls stay behind the app-service boundary, confirm blocked safety gates do not call storage, confirm queue safety gates remain intact, and confirm non-execution safety fields remain disabled.

## P. Recommended next phase

Recommended next phase: 128B: approval storage API application integration call-site wiring final audit and merge gate.

After 128B, recommend: 129A: approval storage API application integration release safety checkpoint, docs/tests only.

Execution enablement must be separate future phase.

Approval endpoint implementation must be separate future phase.

UI action implementation must be separate future phase.

Migration execution must be separate future phase.

## Q. Verification contract phrases

Verification contract phrases

- Approval storage API application integration call-site wiring only: PASS
- Application integration implementation: CALL_SITE_WIRING_ONLY
- Storage API implementation: EXISTING_MODULE_USED
- Storage module path: src/storage/agentic_approvals/store.py
- Runtime-facing integration scope: APPROVED_CALL_SITE_ONLY
- DB write capability: APPROVED_CALL_SITE_STORAGE_ONLY
- Queue mutation: NO_GO
- Execution enablement: NO_GO
- Mutation execution: NO_GO
- Application submission: NO_GO
- Scheduler/background execution: NO_GO
- UI run/approve/reject buttons: NO_GO
- Approval API endpoints: NO_GO
- Live execution: NO_GO
- no execution behavior changes in this phase
- no queue mutation added
- no execution enabled
- no mutation execution enabled
- no application submission enabled
- no approval API endpoint added
- no UI action added
- no scheduler/background execution added
- no SQL file modified in this phase
- static SQL artifact remains inert
- storage API module remains at proposed path
- storage API module does not execute SQL at import time
- storage API module does not open DB connections at import time
- application integration preserves existing queue safety gates
- application integration preserves existing execution safety gates
- application integration preserves idempotency_key behavior
- application integration preserves approval_status constraints
- application integration preserves stage-level observability
- application integration preserves deterministic behavior
- application integration tests use fakes or mocks only
- application integration tests do not require live database
- execution enablement must be separate future phase
- approval endpoint implementation must be separate future phase
- UI action implementation must be separate future phase
- migration execution must be separate future phase

## Step 129A release safety checkpoint

See `docs/approval_storage_api_application_integration_release_safety_checkpoint.md` for the release safety checkpoint confirming that application integration remains approved call-site wiring only, with no execution enablement, queue mutation, application submission, approval endpoint, UI action, scheduler/background execution, SQL change, or migration execution.
