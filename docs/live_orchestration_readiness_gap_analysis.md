# Live Orchestration Readiness Gap Analysis

Doc path: `docs/live_orchestration_readiness_gap_analysis.md`

Phase 33A is a planning/readiness gap analysis only. It does not implement live orchestration, automatic execution, scheduler execution, queue mutation, application submission, database writes, or UI controls that run agents.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `allow_agent_execution=false` and `executable_adapter_count=0`.

## What Exists Today

- Read-only adapter modules exist for Job Prioritization, Tailoring Decision, and Operator Review:
  - `src/agents/read_only_job_prioritization_adapter.py`
  - `src/agents/read_only_tailoring_decision_adapter.py`
  - `src/agents/read_only_operator_review_adapter.py`
- The manual read-only adapter chain exists in `src/agents/read_only_adapter_chain.py`.
- The explicit read-only chain artifact generator exists in `src/agents/read_only_chain_artifact_generator.py`.
- Diagnostic artifacts exist for the manual chain and explicit generator:
  - `read_only_adapter_chain_result.json`
  - `read_only_adapter_chain_report.md`
  - `read_only_chain_artifact_generation_result.json`
  - `read_only_chain_artifact_generation_report.md`
- Verifier checks recognize and validate the manual chain and explicit generator artifacts when they are already present.
- Agentic Review can display existing Manual Read-Only Adapter Chain and Explicit Read-Only Chain Generator diagnostics.
- A sanitized/offline smoke fixture exists at `tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv`.
- The generator-to-viewer roundtrip test covers generator output, artifact validation, verifier integration, service read models, and Agentic Review contract text.
- The operator runbook exists at `docs/read_only_chain_operator_runbook.md`.
- The orchestrator adapter harness is preflight only and keeps `executable_adapter_count=0`.

## What Does Not Exist Yet

- No live orchestration.
- No automatic scheduler execution.
- No UI run button.
- No `workflow_runner.py` execution path.
- No production queue mutation.
- No application submission automation.
- No DB write path for live orchestration.
- No rollback mechanism.
- No operator approval gate for production mutations.
- No idempotent production execution contract.
- No persisted execution lock.
- No live failure recovery policy.
- No audit ledger for production changes.
- No allowlist for mutation-capable agents.
- No dry-run-to-live promotion gate.
- No per-agent production adapter contracts.

## Required Gaps Before Live Orchestration

### Execution Architecture

- Define a production execution contract before any runner can call agents outside dry-run mode.
- Separate dry-run, read-only simulation, and mutation-capable execution modes with explicit type/schema boundaries.
- Define per-agent production adapter contracts for input loading, validation, execution, output validation, diagnostics, mutation proposals, and commit behavior.
- Keep `workflow_runner.py` dry-run only until a separate reviewed phase replaces or wraps it behind a safe execution boundary.

### Safety Gates

- Add a dry-run-to-live promotion gate that fails closed by default.
- Require explicit feature flags for any future controlled execution prototype.
- Require an allowlist for mutation-capable agents before any production mutation can be attempted.
- Add checks that block queue mutation, application submission, scoring/ranking changes, tailoring generation, and packet generation unless a reviewed mutation policy explicitly permits them.

### Mutation Policy

- Define which fields can ever be mutated, by which adapter, under which approval state.
- Define immutable fields and no-touch surfaces for scoring, ranking, filtering, resume selection, packet generation, tailoring generation, scheduler behavior, source behavior, and RAG behavior.
- Require pre-mutation and post-mutation validation that proves no unexpected production fields changed.
- Treat every mutation as a proposed operation until an approval gate and audit ledger exist.

### Approval Workflow

- Add an operator approval gate for production mutations before live execution is considered.
- Define approval states, approver identity, run identity, expiry, and cancellation behavior.
- Require clear separation between advisory diagnostics, proposed actions, approved actions, and committed production changes.
- Prove that no queue mutation or application submission can happen without explicit approval.

### Rollback/Recovery

- Design a rollback mechanism for every production mutation.
- Define recovery behavior for partial failure, validation failure, timeout, duplicate run, and operator cancellation.
- Store enough before/after state to undo approved changes or mark them as non-reversible before execution.
- Define a failed-live-run policy that does not retry destructive work automatically.

### Observability/Audit Logging

- Add a live-run audit ledger schema proposal before implementation.
- Record run id, owner id, adapter id, artifact versions, approval id, mutation proposal, before/after field values, validation status, and rollback status.
- Keep diagnostic traces distinct from production mutation audit entries.
- Include reason codes for blocked, skipped, approved, committed, failed, and rolled-back operations.

### Idempotency and Locking

- Define an idempotency key for each future live run and mutation operation.
- Add a persisted execution lock before any live runner can mutate production state.
- Define duplicate submission behavior for repeated operator clicks, retried jobs, interrupted runs, and concurrent scheduler/manual invocations.
- Require tests proving repeated execution cannot duplicate queue changes, DB writes, or application submissions.

### Artifact/Version Compatibility

- Version every live execution input, output, approval, and mutation artifact.
- Define compatibility checks between dry-run artifacts, read-only chain artifacts, generator artifacts, and future live execution artifacts.
- Fail closed when artifacts are missing, stale, generated by an incompatible version, or tied to a different owner/run context.
- Keep existing read-only artifact names separate from production artifact names.

### UI/Operator Controls

- Do not add a UI run button until approval, locking, idempotency, audit ledger, rollback, and feature flag strategy are designed and tested.
- Any future UI must show dry-run results, proposed changes, approval status, rollback availability, and live-run warnings before enabling action.
- Operator controls must never trigger hidden background execution.
- Agentic Review remains a diagnostics viewer until a later explicitly approved phase.

### Test Strategy

- Preserve current tests proving `workflow_runner.py` remains dry-run only and preflight `executable_adapter_count=0`.
- Add contract tests for production adapter interfaces before adding any implementation.
- Add mutation-policy tests that prove no queue mutation and no application submission can occur without approval.
- Add rollback, idempotency, locking, audit-ledger, feature-flag, and failure-recovery tests before any controlled execution prototype.
- Keep smoke fixtures sanitized/offline and avoid real/private job, resume, user, or company data.

### Deployment/Feature Flag Strategy

- Design explicit opt-in feature flags for each future stage of live readiness.
- Keep defaults off for any execution or mutation capability.
- Add environment validation that prevents live execution in development or production unless all required flags, approval gates, and lock stores are configured.
- Document rollout, rollback, monitoring, and emergency disable procedures before implementation.

## Proposed Future Milestones

- 34A: production execution contract design doc only.
- 35A: mutation policy and approval gate design doc only.
- 36A: live-run audit ledger schema proposal only.
- 37A: idempotency/locking design doc only.
- 38A: dry-run execution simulator, still no mutation.
- 39A: operator approval UI mock/read-only only.
- 40A+: only then consider controlled execution prototype, still behind explicit feature flags.

## Hard Blockers

- `workflow_runner.py` is dry-run only and has no execution adapter boundary.
- Preflight intentionally reports `executable_adapter_count=0`.
- No per-agent production adapter contracts exist.
- No operator approval gate exists for production mutations.
- No mutation policy exists for queue action, submission, DB writes, tailoring generation, packet generation, scoring, or ranking.
- No rollback mechanism exists.
- No persisted execution lock exists.
- No idempotency contract exists for live runs or production mutations.
- No live failure recovery policy exists.
- No live-run audit ledger exists.
- No allowlist exists for mutation-capable agents.
- No dry-run-to-live promotion gate exists.
- No feature-flag rollout strategy exists for controlled execution.

## Non-Goals

- No live execution in this phase.
- No scheduler.
- No UI run button.
- No application submission.
- No queue mutation.
- No scoring/ranking changes.
- No filtering, scraping/source, resume selection, tailoring generation, packet generation, RAG, DB write, or application workflow behavior changes.
- No LangGraph or agent framework.
- No new dependencies.
