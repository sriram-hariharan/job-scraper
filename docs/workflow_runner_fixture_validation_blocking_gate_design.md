# Workflow-Runner Fixture Validation Blocking Gate Design

Doc path: `docs/workflow_runner_fixture_validation_blocking_gate_design.md`

Phase 91A is workflow-runner fixture validation blocking gate design only. Workflow-runner blocking gate implementation: `NOT_YET`.

`workflow_runner.py` is not modified in this phase. No runtime behavior changes in this phase. No fixture payload files added. No fixture payload JSON modified.

## A. Current Design Scope

This phase documents how a future workflow-runner fixture validation blocking gate should behave before any later approved non-dry-run or runtime execution path is allowed. It does not implement the gate.

Preflight fixture validation remains the source of safety truth for fixture validation. Benchmark fixture validation remains reporting-only.

## B. Existing Safety Inputs

The future gate should consume the existing preflight fixture validation summary produced by the orchestrator adapter harness. The approved fixture set remains exactly:

- `safe_execution_request_minimal.json`
- `blocked_db_write_request_minimal.json`
- `blocked_application_submission_request_minimal.json`

Current safety fields remain:

- `workflow_runner.py` remains dry-run only
- `executable_adapter_count` remains 0
- `allow_agent_execution` remains false
- `did_execute_count` remains 0
- `did_execute_live` remains false
- `did_mutate_production` remains false
- `did_write_db` remains false

## C. Proposed Future Blocking Gate Contract

Future workflow-runner gate must be blocking-only, not execution.

Future workflow-runner gate must refuse unsafe execution if fixture validation fails. Future workflow-runner gate must refuse unsafe execution if fixture validation is missing. Future workflow-runner gate must refuse unsafe execution if expected fixture count is not 3. Future workflow-runner gate must refuse unsafe execution if unexpected fixture files appear. Future workflow-runner gate must refuse unsafe execution if `fixture_validation_failed_fixture_ids` is non-empty.

Future workflow-runner gate must refuse unsafe execution if `executable_adapter_count` is greater than 0 without explicit later approval. Future workflow-runner gate must refuse unsafe execution if `allow_agent_execution` is true without explicit later approval.

Future workflow-runner gate must preserve dry-run-only behavior until a later approved execution phase.

## D. Expected-Failure Handling

Blocked fixtures are expected failures and should not block if actual failure matches expected_validation.

The blocked DB-write fixture and blocked application-submission fixture should remain non-blocking only when their actual failed validation status and expected reason codes match their fixture `expected_validation` contract. The safe fixture should remain non-blocking only when it validates as passed.

## E. Block Conditions

Malformed, missing, unexpected, or mismatched fixture validation must block.

The future gate must block when any of these conditions are present:

- fixture validation is absent from the preflight payload
- fixture validation status is not `passed`
- fixture validation passed flag is not true
- expected fixture count is not 3
- checked fixture count is not 3
- unexpected fixture files appear
- missing fixture files appear
- `fixture_validation_failed_fixture_ids` is non-empty
- a blocked fixture failure no longer matches `expected_validation`
- a safe fixture no longer validates as passed
- any fixture result reports execution, mutation, or DB writes
- `executable_adapter_count` is greater than 0 without explicit later approval
- `allow_agent_execution` is true without explicit later approval

## F. Non-Block Conditions

Expected blocked fixture failures should not block when actual failure matches expected_validation.

Observed reason codes such as `db_write_not_allowed` and `application_submission_not_allowed` should remain non-blocking when they come from approved blocked fixtures whose actual validation matches their expected validation contract.

## G. Runtime Isolation Confirmation

This design adds no live planning integration. This design adds no app services integration. This design adds no queue integration. This design adds no DB writes. This design adds no mutation. This design adds no application submission. This design adds no approval API/storage. This design adds no scheduler/background execution.

There is no fixture execution and no automatic execution in this phase.

## H. Forbidden Shortcuts

Do not implement workflow_runner blocking next unless 91B passes and explicit approval is given. Do not wire validator into live planning next. Do not auto-discover arbitrary fixture directories next. Do not add DB writes, queue mutation, storage APIs, migrations, mutation execution, or live execution next.

## I. Explicit Non-Goals

- no workflow_runner implementation
- no workflow_runner integration implementation
- no runtime behavior changes
- no fixture payload files
- no fixture payload JSON changes
- no fixture execution
- no automatic execution
- no live planning integration
- no app services integration
- no queue integration
- no DB writes
- no queue mutation
- no mutation execution
- no application submission
- no approval API/storage
- no scheduler/background execution
- no migrations
- no SQL DDL
- no UI run/approve/reject buttons
- no LangGraph or agent framework

## J. Recommended Next Phase

Recommended next phase: 91B workflow-runner fixture validation blocking gate design final audit and merge gate.

After 91B, recommend: 92A workflow-runner fixture validation blocking gate implementation, only if explicitly approved.

## Decisions

- Workflow-runner fixture validation blocking gate design: `PASS`
- Workflow-runner blocking gate implementation: `NOT_YET`
- Runtime-facing integration scope: `DESIGN_ONLY`
- Preflight fixture validation reuse: `GO`
- Benchmark fixture validation reporting: `GO`
- Workflow runner integration implementation: `NO_GO`
- Live planning integration: `NO_GO`
- App services integration: `NO_GO`
- Queue integration: `NO_GO`
- Fixture execution: `NO_GO`
- Automatic execution: `NO_GO`
- DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Application submission: `NO_GO`
- Approval API/storage: `NO_GO`
- Scheduler/background execution: `NO_GO`
