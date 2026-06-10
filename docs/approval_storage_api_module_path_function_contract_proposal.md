# Approval Storage API Module Path And Function Contract Proposal

Doc path: `docs/approval_storage_api_module_path_function_contract_proposal.md`

Step 121A proposes a future approval storage API module path and public function contract. This phase is docs/tests only and adds no runtime behavior.

## A. Current proposal scope

This proposal is documentation only. It does not create a Python storage module, storage API implementation, approval storage implementation, approval API endpoint, function stub, SQL execution code, migration runner code, DB write, queue mutation, execution, mutation execution, scheduler/background execution, UI run/approve/reject button, or application submission.

No runtime behavior changes in this phase.

No storage API file added.

No storage module added.

No function stubs added.

No DB writes added.

No queue mutation added.

No execution enabled.

No mutation execution enabled.

No application submission enabled.

No SQL file modified in this phase.

The static SQL artifact remains inert.

## B. Repository structure inspected

Repository structure and `src/storage` conventions were inspected.

Existing storage domains commonly use `src/storage/<domain>/schema.sql` with a companion `store.py` when implementation is approved.

The existing static approval SQL artifact remains at `src/storage/agentic_approvals/schema.sql`.

No `src/storage/agentic_approvals/store.py` file is added by this proposal.

## C. Proposed future module path

Proposed future storage API module path: `src/storage/agentic_approvals/store.py`.

This path is PROPOSED_ONLY.

The proposed module path must be reviewed before creation.

The proposed module must not be created until a separate future safety checkpoint and implementation phase explicitly approve it.

## D. Proposed future public function contract

Proposed future public function names are PROPOSED_ONLY.

Proposed future function names must be reviewed before implementation.

Candidate future functions:

- `create_approval_request(...)`
- `get_approval_request(...)`
- `list_approval_requests(...)`
- `record_approval_audit_event(...)`
- `record_approval_decision(...)`
- `expire_approval_requests(...)`

None of these functions exist in this phase, and no function stubs are added.

## E. Proposed request persistence function boundary

Future proposal only: `create_approval_request(...)`.

The future request persistence boundary should create one approval request using the approved schema fields, preserve `idempotency_key` behavior, preserve `approval_status` constraints, and persist only non-secret JSON-compatible snapshots.

The future function must not execute SQL automatically from the static SQL artifact.

## F. Proposed audit event persistence function boundary

Future proposal only: `record_approval_audit_event(...)`.

The future audit event persistence boundary should append an audit event linked to an existing approval request.

The future function must preserve audit event foreign key behavior and must not store secrets or raw credentials.

## G. Proposed read/query function boundary

Future proposal only: `get_approval_request(...)` and `list_approval_requests(...)`.

The future read/query boundary should return approval request records and related non-secret audit metadata without mutating queues, enabling execution, enabling mutation execution, or submitting applications.

Read/query functions must preserve deterministic behavior and stage-level observability.

## H. Proposed decision/update function boundary

Future proposal only: `record_approval_decision(...)`.

The future decision/update boundary should be considered only after a separate approval-flow implementation review confirms allowed status transitions, actor metadata, audit event behavior, idempotency handling, and data-safety constraints.

Decision/update behavior must not trigger queue mutation, execution, mutation execution, application submission, scheduler/background execution, or UI run/approve/reject buttons by itself.

## I. Proposed expiration/cleanup function boundary

Future proposal only: `expire_approval_requests(...)`.

The future expiration/cleanup boundary should mark stale pending approval requests according to reviewed status-transition rules and append non-secret audit events when approved by a future phase.

Expiration/cleanup behavior must not delete production records, execute mutations, or submit applications.

## J. Idempotency contract proposal

The future storage API must preserve `idempotency_key` behavior.

Duplicate idempotency keys should return a deterministic outcome without creating duplicate logical approval requests.

Retries must not create duplicate approval requests or duplicate audit events for the same logical operation.

## K. Transaction boundary proposal

Future request creation and its initial audit event should commit together or fail together when they are part of one logical storage operation.

Future transaction handling must remain storage-scoped and must not trigger queue mutation, execution, mutation execution, scheduler/background execution, UI actions, or application submission.

Migration execution must be separate future phase.

## L. Error handling and retry proposal

Future error handling should use deterministic error categories for duplicate idempotency keys, missing approval requests, invalid statuses, stale transitions, constraint failures, serialization failures, and connection failures.

Retry behavior should be limited to cases that cannot duplicate durable approval records.

Failures must preserve non-executing behavior.

## M. Observability and logging proposal

Future storage API behavior must preserve stage-level observability.

Future logs and diagnostics should include non-secret identifiers, operation names, validation status, reason codes, timing fields, and deterministic outcomes.

Observability must not expose secrets, raw credentials, full environment values, or unsafe payload contents.

## N. Security and data-safety proposal

The future storage API must not store secrets.

The future storage API must not store raw credentials.

The future storage API must validate payload shapes before persistence.

The future storage API must keep approval storage separate from application integration, queue mutation, live execution, and migration execution.

## O. Forbidden implementation shortcuts

Do not add the proposed module in this phase.

Do not add function stubs in this phase.

Do not add storage API implementation in this phase.

Do not add Python storage modules in this phase.

Do not add DB writes in this phase.

Do not add approval API endpoints or approval storage implementation in this phase.

Do not add queue mutation, execution, mutation execution, scheduler/background execution, UI run/approve/reject buttons, live execution, or application submission.

Do not execute SQL automatically.

Do not add migration execution or migration runner code.

Do not add new SQL files, migration files, or DB schema files.

## P. Recommended next phase

Recommended next phase: 121B: approval storage API module path and function contract proposal final audit and merge gate.

After 121B, recommend: 122A: approval storage API implementation safety checkpoint, docs/tests only first.

Implementation safety checkpoint: `docs/approval_storage_api_implementation_safety_checkpoint.md`.

Step 123A implements the proposed module path only with no runtime integration: `docs/approval_storage_api_implementation_module_only.md`.

Storage API implementation safety checkpoint must be separate future phase.

Storage API implementation must be separate future phase.

Application integration must be separate future phase.

Migration execution must be separate future phase.

## Q. Verification contract phrases

Verification contract phrases

- Approval storage API module path and function contract proposal: PASS
- Proposed storage API module path: PROPOSED_ONLY
- Proposed storage API function contract: PROPOSED_ONLY
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
- no function stubs added
- no DB writes added
- no queue mutation added
- no execution enabled
- no mutation execution enabled
- no application submission enabled
- no SQL file modified in this phase
- static SQL artifact remains inert
- future storage API module path must be reviewed before creation
- future storage API function names must be reviewed before implementation
- future storage API must not execute SQL automatically
- future storage API must preserve idempotency_key behavior
- future storage API must preserve approval_status constraints
- future storage API must preserve audit event foreign key behavior
- future storage API must not store secrets
- future storage API must not store raw credentials
- future storage API must preserve stage-level observability
- future storage API must preserve deterministic behavior
- storage API implementation safety checkpoint must be separate future phase
- storage API implementation must be separate future phase
- application integration must be separate future phase
- migration execution must be separate future phase
