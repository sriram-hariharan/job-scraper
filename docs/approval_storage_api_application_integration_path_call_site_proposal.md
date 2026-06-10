# Approval Storage API Application Integration Path And Call-Site Proposal

Doc path: `docs/approval_storage_api_application_integration_path_call_site_proposal.md`

Step 126A is an application integration path and call-site proposal only. This phase is docs/tests only and adds no runtime behavior.

## A. Current proposal scope

This proposal identifies future application integration paths and future call-sites for the existing approval storage API module at `src/storage/agentic_approvals/store.py`.

Every integration path and call-site in this document is proposed only. No proposed call-site invokes the storage module in this phase. No runtime file, storage module, SQL file, queue path, workflow runner path, app service path, scheduler/background path, UI action, execution path, mutation execution path, or application submission path is modified.

## B. Runtime files inspected

The proposal inspected these files without modifying them:

- `application_execution_queue.py`
- `src/app/services.py`
- `src/app/static/agentic_review.js`
- `src/agents/workflow_runner.py`
- `src/storage/agentic_approvals/schema.sql`
- `src/storage/agentic_approvals/store.py`
- `tests/test_agentic_approval_storage_api.py`

The static SQL artifact remains inert. The storage API module remains module-only and is not invoked by the pipeline.

## C. Proposed future integration path

Future application integration should be split into separate reviewed phases:

1. A safety checkpoint confirming exact call boundaries and non-execution behavior.
2. A proposed app-service call-site implementation that remains blocked by existing workflow-runner and queue safety gates.
3. A separately reviewed approval API endpoint proposal, if endpoints are still required.
4. A separately reviewed migration execution phase before any production database use.

The future path must preserve existing queue safety gates, existing execution safety gates, `idempotency_key` behavior, `approval_status` constraints, stage-level observability, and deterministic behavior.

## D. Proposed future call-sites

Future call-sites are proposal-only:

- `src/app/services.py` could own application-service boundaries that translate already safety-gated dry-run artifacts into approval request payloads.
- `application_execution_queue.py` could remain a downstream consumer of app-service safety-gated results and must not create approval requests directly unless a separate queue integration phase approves it.
- `src/app/static/agentic_review.js` could display read-only approval readiness state after backend endpoints are separately designed and implemented.
- `src/agents/workflow_runner.py` should remain dry-run only and should not call approval storage directly.

These call-sites are not modified in this phase and do not invoke `src/storage/agentic_approvals/store.py`.

## E. Proposed request persistence call boundary

Future approval request persistence should call `create_approval_request(...)` only after:

- workflow-runner fixture validation gate passes,
- app-service safety gate passes,
- queue safety gate passes when queue context is involved,
- an explicit dry-run artifact id is available,
- an idempotency key is available,
- a non-secret safety gate snapshot is assembled,
- migration execution has been separately approved and completed.

The caller should inject a DB-API compatible connection. The storage module should not own connection creation.

## F. Proposed audit event persistence call boundary

Future audit event persistence should call `record_approval_audit_event(...)` only for deterministic state observations or human review events tied to an existing approval request id.

Audit event payloads must remain JSON-compatible, bounded, non-secret, and free of raw credentials.

## G. Proposed decision/update call boundary

Future approval decisions should call `record_approval_decision(...)` only after a separate approval API/storage implementation phase defines human reviewer identity, transition rules, error handling, and audit event behavior.

Approval decisions must not enable execution when safety gates are failing.

## H. Proposed read/query call boundary

Future read/query use should call `get_approval_request(...)` and `list_approval_requests(...)` only for read-only display, diagnostics, or explicit operator review surfaces.

Read/query call-sites must not mutate queues, enable execution, submit applications, or bypass safety gates.

## I. Queue safety gate preservation

Future application integration must preserve existing queue safety gates.

Queue mutation remains NO_GO in this phase. Future queue processing must not create approval records or consume approvals unless a separate implementation safety checkpoint approves the exact queue call boundary.

## J. Execution safety gate preservation

Future application integration must preserve existing execution safety gates.

Execution enablement remains NO_GO in this phase. Mutation execution, application submission, scheduler/background execution, UI run/approve/reject buttons, and live execution remain NO_GO.

## K. Idempotency and approval status preservation

Future integration must preserve `idempotency_key` behavior by deriving stable idempotency keys from deterministic dry-run artifact and proposed action identity.

Future integration must preserve `approval_status` constraints and must not invent status values outside the approved storage contract.

## L. Observability and stage logging proposal

Future integration should emit deterministic operation names, stage names, non-secret identifiers, reason codes, and safety gate snapshot references.

Future integration must preserve stage-level observability and deterministic behavior so tests can prove the storage call boundary remains explicit and non-executing.

## M. Security and data-safety proposal

Future integration must not store secrets, raw credentials, database URLs, authorization headers, tokens, API keys, private keys, or full unbounded payloads.

Future snapshots must be non-secret, JSON-compatible, bounded, and limited to approval metadata, dry-run artifact references, and safety gate evidence.

## N. Forbidden implementation shortcuts

Do not implement application integration in this phase.

Do not add imports from `src/storage/agentic_approvals/store.py` into runtime files in this phase.

Do not add function stubs in this phase.

Do not add app service integration, workflow runner integration, queue integration, approval API endpoints, UI actions, scheduler/background execution, execution, mutation execution, application submission, SQL execution code, migration runner code, SQL files, migration files, DB schema files, or dependencies in this phase.

## O. Recommended next phase

Recommended next phase: 126B: approval storage API application integration path and call-site proposal final audit and merge gate.

After 126B, recommend: 127A: approval storage API application integration implementation safety checkpoint, docs/tests only first.

Application integration implementation safety checkpoint must be separate future phase.

Application integration implementation must be separate future phase.

Migration execution must be separate future phase.

## P. Verification contract phrases

Verification contract phrases

- Approval storage API application integration path and call-site proposal: PASS
- Application integration path proposal: PROPOSED_ONLY
- Application call-site proposal: PROPOSED_ONLY
- Storage API implementation: EXISTING_MODULE_ONLY
- Storage module path: src/storage/agentic_approvals/store.py
- Runtime-facing integration scope: DESIGN_ONLY
- DB write capability: STORAGE_MODULE_ONLY_NOT_INVOKED_BY_PIPELINE
- Queue mutation: NO_GO
- Execution enablement: NO_GO
- Mutation execution: NO_GO
- Application submission: NO_GO
- Scheduler/background execution: NO_GO
- UI run/approve/reject buttons: NO_GO
- Approval API endpoints: NO_GO
- Live execution: NO_GO
- no runtime behavior changes in this phase
- no app service integration added
- no workflow runner integration added
- no queue integration added
- no approval API endpoint added
- no UI action added
- no scheduler/background execution added
- no execution enabled
- no mutation execution enabled
- no application submission enabled
- no storage API file modified in this phase
- no storage module modified in this phase
- no SQL file modified in this phase
- static SQL artifact remains inert
- storage API module remains module-only
- storage API module remains not invoked by pipeline
- future application integration path proposed only
- future application call-sites proposed only
- future application integration must preserve existing queue safety gates
- future application integration must preserve existing execution safety gates
- future application integration must preserve idempotency_key behavior
- future application integration must preserve approval_status constraints
- future application integration must preserve stage-level observability
- future application integration must preserve deterministic behavior
- application integration implementation safety checkpoint must be separate future phase
- application integration implementation must be separate future phase
- migration execution must be separate future phase
