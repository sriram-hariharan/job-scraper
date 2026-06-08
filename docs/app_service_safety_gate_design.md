# App-Service Safety Gate Design

Doc path: `docs/app_service_safety_gate_design.md`

Phase 97A is app-service safety gate design only. App-service safety gate implementation: NOT_YET.

`src/app/services.py` is not modified in this phase. `workflow_runner.py` is not modified in this phase. No runtime behavior changes in this phase.

Contract phrases: src/app/services.py is not modified in this phase; workflow_runner.py is not modified in this phase; app services must not bypass workflow-runner fixture validation gate; app services must refuse run/execute actions if workflow-runner gate reports blocked_by_fixture_validation_gate true; blocked results must remain non-executing.

The future app-service safety gate must ensure app services eventually call a safety-gated workflow-runner path only. App services must not bypass workflow-runner fixture validation gate.

## A. Current Design Scope

This phase is docs/tests only and design-only. It does not add app services integration, queue integration, live planning integration, fixture execution, automatic execution, DB writes, queue mutation, application submission, approval API/storage, scheduler/background execution, UI run/approve/reject buttons, LangGraph, or an agent framework.

No fixture payload JSON modified. No fixture payload files added.

## B. Existing Workflow-Runner Safety Gate

The existing workflow-runner fixture validation gate is blocking-only. It refuses unsafe fixture-validation states before any future app/UI/API-triggered agentic run can proceed. `workflow_runner.py` remains dry-run only.

The existing gate blocks missing, malformed, unexpected, and mismatched fixture validation. It also blocks unsafe execution signals such as executable_adapter_count greater than 0 and allow_agent_execution true unless a later phase explicitly approves those states.

## C. Proposed Future App-Service Gate Contract

App services must eventually call a safety-gated workflow-runner path only. App services must not bypass workflow-runner fixture validation gate.

App services must preserve dry-run-only behavior until a later approved execution phase. Expected blocked-fixture failures are accepted only when actual failure matches expected_validation. Blocked results must remain non-executing.

## D. App-Service Block Conditions

App services must refuse run/execute actions if workflow-runner gate reports blocked_by_fixture_validation_gate true.

App services must refuse run/execute actions if fixture validation is missing. App services must refuse run/execute actions if fixture validation fails.

App services must refuse run/execute actions if executable_adapter_count is greater than 0 without later explicit approval. App services must refuse run/execute actions if allow_agent_execution is true without later explicit approval.

## E. App-Service Non-Block Conditions

Future app-service entry points may proceed only through a safety-gated workflow-runner dry-run result when fixture validation is present, fixture validation passes, blocked_by_fixture_validation_gate is false, executable_adapter_count is 0, allow_agent_execution is false, and all non-execution safety fields remain safe.

Expected blocked-fixture failures are accepted only when actual failure matches expected_validation.

## F. Runtime Isolation Confirmation

No queue integration. No live planning integration. No DB writes. No mutation. No application submission. No approval API/storage. No scheduler/background execution. No UI run/approve/reject buttons.

`workflow_runner.py` remains dry-run only. Blocked results must remain non-executing.

## G. Forbidden Shortcuts

Do not implement app-service safety gate next unless 97B passes and explicit approval is given. Do not wire queue mutation next. Do not enable execution next. Do not add DB writes, queue mutation, storage APIs, migrations, mutation execution, or live execution next.

## H. Explicit Non-Goals

- no app-service safety gate implementation
- no app services integration
- no queue integration
- no live planning integration
- no fixture execution
- no automatic execution
- no DB writes
- no queue mutation
- no mutation execution
- no application submission
- no approval API/storage
- no scheduler/background execution
- no UI run/approve/reject buttons
- no migrations
- no SQL DDL
- no LangGraph or agent framework
- no fixture payload JSON modified
- no fixture payload files added

## I. Recommended Next Phase

Recommended next phase: 97B app-service safety gate design final audit and merge gate.

After 97B, recommend: 98A app-service safety gate implementation, only if explicitly approved.

## Decisions

- App-service safety gate design: PASS
- App-service safety gate implementation: NOT_YET
- Runtime-facing integration scope: DESIGN_ONLY
- Workflow runner blocking gate reuse: GO
- Fixture validation failure-mode coverage reuse: GO
- App services integration implementation: NO_GO
- Queue integration: NO_GO
- Live planning integration: NO_GO
- Fixture execution: NO_GO
- Automatic execution: NO_GO
- DB writes: NO_GO
- Mutation execution: NO_GO
- Application submission: NO_GO
- Approval API/storage: NO_GO
- Scheduler/background execution: NO_GO
- UI run/approve/reject buttons: NO_GO
