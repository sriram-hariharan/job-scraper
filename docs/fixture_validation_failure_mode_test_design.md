# Fixture Validation Failure-Mode Test Design

Doc path: `docs/fixture_validation_failure_mode_test_design.md`

Phase 94A is malformed/missing fixture validation failure-mode test design only. Failure-mode test implementation: `NOT_YET`.

`workflow_runner.py` is not modified in this phase. `orchestrator_adapter_harness.py` is not modified in this phase. `agentic_benchmark.py` is not modified in this phase. `fixture_validator.py` is not modified in this phase.

No fixture payload files are added in this phase. No fixture payload JSON files are modified in this phase. No runtime behavior changes in this phase.

`workflow_runner.py` remains dry-run only. Preflight fixture validation remains the fixture-validation source of truth. Benchmark fixture validation remains reporting-only. The workflow-runner gate remains blocking-only, not execution.

## A. Current Design Scope

This phase designs future failure-mode tests for fixture validation and the workflow-runner blocking gate. It does not add malformed fixture payload files, mutate existing fixture payload JSON, or implement failure-mode tests.

The current fixture directory remains limited to:

- `safe_execution_request_minimal.json`
- `blocked_db_write_request_minimal.json`
- `blocked_application_submission_request_minimal.json`
- `.gitkeep`

## B. Existing Safety Gate Behavior

The existing workflow-runner blocking gate accepts healthy fixture validation and blocks unsafe fixture-validation summaries. Current healthy validation accepts expected blocked-fixture failures when actual failure matches expected_validation.

## C. Future Failure-Mode Test Matrix

Future failure-mode tests must cover:

- missing `safe_execution_request_minimal.json` blocks
- missing `blocked_db_write_request_minimal.json` blocks
- missing `blocked_application_submission_request_minimal.json` blocks
- malformed fixture JSON blocks
- unexpected extra fixture file blocks
- wrong `fixture_validation_expected_fixture_count` blocks
- wrong `fixture_validation_checked_count` blocks
- `fixture_validation_failed_fixture_ids` non-empty blocks
- `fixture_validation_status` not passed blocks
- `fixture_validation_passed` false blocks
- blocked DB-write fixture actual/expected mismatch blocks
- blocked application-submission fixture actual/expected mismatch blocks
- safe fixture actual/expected mismatch blocks
- `executable_adapter_count` greater than 0 blocks
- `allow_agent_execution` true blocks
- `did_execute_count` non-zero blocks
- `did_execute_live` true blocks
- `did_mutate_production` true blocks
- `did_write_db` true blocks

## D. Required Block Cases

Missing approved fixtures must block. Malformed fixture JSON must block. Unexpected extra fixture files must block. Wrong expected or checked fixture counts must block. Non-empty `fixture_validation_failed_fixture_ids` must block. Fixture status not passed and fixture passed false must block. Actual/expected fixture validation mismatches must block. Unsafe execution fields must block.

## E. Required Non-Block Cases

Expected blocked-fixture failures do not block when actual failure matches expected_validation.

The blocked DB-write fixture should remain non-blocking when actual validation status is failed and expected validation status is failed. The blocked application-submission fixture should remain non-blocking when actual validation status is failed and expected validation status is failed. The safe fixture should remain non-blocking when actual validation status is passed and expected validation status is passed.

## F. Required Non-Execution Assertions

Future failure-mode tests must confirm blocked results remain non-executing. Future failure-mode tests must confirm blocked results keep `did_execute_count` 0, `did_execute_live` false, `did_mutate_production` false, and `did_write_db` false.

Future failure-mode tests must confirm no app service calls, no queue calls, no DB calls, no application submission calls, and no live planning calls.

## G. Runtime Isolation Confirmation

This design adds no workflow_runner behavior, no live planning integration, no app services integration, no queue integration, no fixture execution, no automatic execution, no DB writes, no mutation execution, and no application submission.

## H. Forbidden Shortcuts

Do not implement failure-mode tests next unless 94B passes and explicit approval is given. Do not add malformed fixture payload files next unless explicitly approved. Do not modify real fixture JSON payloads next. Do not wire validator into live planning next. Do not wire validator into app services next without a design/checkpoint phase. Do not wire validator into queue mutation next without a design/checkpoint phase. Do not enable execution next. Do not add DB writes, queue mutation, storage APIs, migrations, mutation execution, or live execution next.

## I. Explicit Non-Goals

- no failure-mode test implementation
- no malformed fixture payload files
- no fixture payload files
- no fixture payload JSON modifications
- no workflow_runner implementation changes
- no preflight implementation changes
- no benchmark implementation changes
- no fixture validator implementation changes
- no live planning integration
- no app services integration
- no queue integration
- no fixture execution
- no automatic execution
- no DB writes
- no mutation execution
- no application submission
- no approval API/storage
- no scheduler/background execution
- no migrations
- no SQL DDL
- no UI run/approve/reject buttons
- no LangGraph or agent framework

## J. Recommended Next Phase

Recommended next phase: 94B malformed/missing fixture validation failure-mode test design final audit and merge gate.

After 94B, recommend: 95A malformed/missing fixture validation failure-mode test implementation, only if explicitly approved.

## Decisions

- Fixture validation failure-mode test design: `PASS`
- Failure-mode test implementation: `NOT_YET`
- Runtime-facing integration scope: `DESIGN_ONLY`
- Workflow runner blocking gate reuse: `GO`
- Preflight fixture validation reuse: `GO`
- Benchmark fixture validation reporting: `GO`
- Fixture payload mutation: `NO_GO`
- Additional fixture payload files in this phase: `NO_GO`
- Workflow runner implementation changes: `NO_GO`
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
