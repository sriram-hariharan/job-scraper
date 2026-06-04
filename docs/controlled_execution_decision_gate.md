# Controlled Execution Decision Gate

Doc path: `docs/controlled_execution_decision_gate.md`

Phase 40A is a decision gate only. There is no implementation in this phase, no live execution enabled, no mutation enabled, no approval API/storage enabled, and no DB writes.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current State

The current system has useful diagnostic foundations, but it is still not mutation-capable:

- Read-only adapters exist for Job Prioritization, Tailoring Decision, and Operator Review.
- The manual read-only adapter chain exists and is explicit/manual only.
- The explicit read-only chain artifact generator exists and requires explicit input and output paths.
- The dry-run execution simulator exists and consumes already-produced read-only artifacts only.
- Agentic Review diagnostics can display read-only chain, generator, simulator, and verifier artifacts after they already exist.
- The Operator Approval Mock exists as a read-only, non-actionable diagnostic display.
- Design docs exist for production execution contract, mutation policy and approval gate, live-run audit ledger schema, and idempotency/locking.

These pieces are evidence and planning scaffolding. They are not live orchestration, approval, mutation, or execution.

## Current Hard Safety Boundary

- No live execution.
- No queue mutation.
- No application submission.
- No DB write.
- No approval storage/API.
- No audit ledger storage.
- No lock/idempotency store.
- No scheduler.
- No UI execution/approval action.
- No UI run/approve/reject buttons.
- No runtime or pipeline behavior change.

## Decision

Decision vocabulary:

- `GO`: ready to implement the capability.
- `LIMITED_GO`: ready only for explicitly bounded safety scaffolding.
- `NO_GO`: not ready and must remain blocked.

Current decision:

- Live mutation: `NO_GO`.
- Application submission automation: `NO_GO`.
- Queue mutation: `NO_GO`.
- Approval UI/action: `NO_GO`.
- DB-backed audit ledger implementation: `NOT YET`.
- Proposal-only mutation planner: `LIMITED_GO`, if explicit/manual/read-only/non-mutating.

The project is not ready for live mutation. Allowed next work should be safety scaffolding only. The earliest reasonable next step is a proposal-only mutation planner that writes diagnostic artifacts only, or more design around approval, audit, idempotency, and locking implementation.

Do not recommend live queue mutation yet.

## Decision Matrix

| Capability | Readiness | Decision | Blockers | Allowed next step |
| --- | --- | --- | --- | --- |
| Live pipeline execution | Not ready | `NO_GO` | No implemented approval, audit, idempotency, lock, rollback, feature flag, or mutation transaction boundary. | Keep `workflow_runner.py` dry-run only; design proposal-only scaffolding first. |
| Queue action mutation | Not ready | `NO_GO` | Approval storage/API missing, audit ledger storage missing, idempotency store missing, execution lock store missing, rollback implementation missing. | Proposal-only mutation planner may describe candidate queue changes as non-executable diagnostics. |
| Application submission | Not ready | `NO_GO` | Submission-specific approval, idempotency, rollback/recovery, audit, and operator policy are missing. | Keep application submission automation blocked. |
| DB-backed audit ledger | Design only | `NOT YET` | Implemented audit ledger storage missing; migration and storage API review missing. | 41A audit ledger storage implementation design review, no migration yet. |
| Approval API/storage | Design only | `NO_GO` | Implemented approval storage/API missing; approval scope, expiry, and consumption behavior not implemented. | 43A approval API/storage design review, no implementation yet. |
| Lock/idempotency store | Design only | `NO_GO` | Implemented idempotency store missing; implemented execution lock store missing; collision and recovery behavior not implemented. | 42A idempotency/lock storage implementation design review, no migration yet. |
| Proposal-only mutation planner | Partially ready for diagnostics | `LIMITED_GO` | Must not mutate, approve, execute, write DB rows, update queues, or submit applications. | 40B proposal-only mutation planner design or utility, explicit/manual/read-only/non-mutating. |
| Read-only approval review UI | Mock only | `LIMITED_GO` | Real approval API/storage and mutation execution remain missing. | 44A read-only approval review UI mock v2, no actions. |
| Dry-run simulator enhancement | Ready for diagnostics | `LIMITED_GO` | Must remain explicit/manual and diagnostic-only; no live promotion. | Add stricter validation or richer diagnostic artifacts only. |

## Blockers Before Live Mutation

- Implemented audit ledger storage missing.
- Implemented approval storage/API missing.
- Implemented idempotency store missing.
- Implemented execution lock store missing.
- Rollback implementation missing.
- Mutation transaction boundary missing.
- Feature flag/environment gate implementation missing.
- Operator approval workflow missing.
- Failure recovery tests missing.
- Production dry-run-to-live promotion policy missing.
- No reviewed mutation API contract implemented.

Until these blockers are closed in reviewed phases, live mutation remains `NO_GO`.

## Allowed Next Phases

- 40B: proposal-only mutation planner design or utility, no mutation.
- 41A: audit ledger storage implementation design review, no migration yet.
- 42A: idempotency/lock storage implementation design review, no migration yet.
- 43A: approval API/storage design review, no implementation yet.
- 44A: read-only approval review UI mock v2, no actions.
- 45A+: only after approved storage designs, consider migrations behind feature flags.

## Explicit Non-Goals

- No live execution in this phase.
- No mutation.
- No queue updates.
- No application submission.
- No approval/reject buttons.
- No DB writes.
- No scheduler.
- No agent framework integration.
- No approval API/storage implementation.
- No audit ledger storage implementation.
- No lock/idempotency implementation.
- No runtime/pipeline/app behavior changes.

## Recommended Next Step

Do not start live execution.

Build a proposal-only mutation planner next, or finish storage design reviews first. If choosing code, code must stay explicit/manual and write diagnostic artifacts only.

Phase 41A proposal-only mutation planner details live in `docs/proposal_only_mutation_planner.md`. That planner is explicit/manual/read-only/non-mutating and does not enable live execution.
