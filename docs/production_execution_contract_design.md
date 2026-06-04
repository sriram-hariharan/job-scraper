# Production Execution Contract Design

Doc path: `docs/production_execution_contract_design.md`

Phase 34A is design only. No implementation in this phase adds live orchestration, automatic execution, scheduler/background execution, UI run controls, database writes, queue mutation, scoring/ranking changes, or application submission.

No live execution is enabled. `workflow_runner.py` remains dry-run only, and read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Purpose

Define the future production execution contract before any live orchestration prototype exists. This document names the data entities, required fields, safety invariants, allowed and forbidden mutation surfaces, rollback expectations, and implementation gates that must be satisfied before any later phase can consider controlled execution.

This document is planning-only. It does not add runtime behavior, adapters, scheduler behavior, UI behavior, database schema, LLM calls, or application submission behavior.

The future mutation policy and approval gate boundary is detailed in `docs/mutation_policy_approval_gate_design.md`. That document is design-only and does not enable mutation execution.

The future live-run audit ledger schema proposal is detailed in `docs/live_run_audit_ledger_schema_design.md`. That document is design/schema proposal-only and does not enable persistence, ledger writes, live execution, or mutation execution.

## Current Boundary

- `workflow_runner.py` emits skipped dry-run steps only and must not invoke adapters, chains, generators, LLM calls, database writes, queue mutation, or application submission.
- `orchestrator_adapter_harness.py` is preflight/read-only only and must keep `allow_agent_execution=false` and `executable_adapter_count=0`.
- The manual read-only adapter chain and explicit read-only chain artifact generator can write isolated diagnostics only when manually invoked with explicit input and output locations.
- Existing diagnostic artifacts can be evidence for future proposals, but they are not approvals and cannot commit production changes.
- No live orchestration, no scheduler/background execution, no hidden automatic execution, no UI run button, no DB write, no queue mutation, no application submission, and no scoring/ranking changes are enabled.

## Future Execution Contract Entities

Future live readiness depends on separate, versioned entities. These names are contract vocabulary only in this phase:

- `execution_request`: an operator or system request to evaluate a bounded execution intent.
- `execution_plan`: the validated plan derived from an execution request.
- `mutation_proposal`: a proposed production change, separated from execution and commit.
- `approval_record`: the human approval or rejection record for one or more mutation proposals.
- `execution_attempt`: a single bounded attempt to execute an approved plan after gates, locks, and audit writes are satisfied.
- `execution_result`: the final status and validation summary for an attempted execution.
- `rollback_plan`: the documented recovery path for each mutable field or approved non-reversible action.
- `audit_ledger_entry`: an immutable audit record for every proposal, approval, execution attempt, validation, rollback, and blocked operation.
- `idempotency_key`: the stable duplicate-protection key for a request, plan, proposal, or mutation.
- `execution_lock`: the persisted lock that prevents concurrent mutation of the same target scope.

## Execution Request Contract

An `execution_request` describes intent only. It must not mutate data.

Required fields:

- `request_id`
- `pipeline_run_id`
- `owner_user_id`
- `requested_by`
- `requested_at_utc`
- `execution_mode`
- `dry_run_required`
- `requested_agent_keys`
- `input_artifact_refs`
- `output_artifact_dir`
- `feature_flags_snapshot`
- `environment`
- `reason_for_run`

Validation rules:

- `dry_run_required` defaults to true until a future approved live phase exists.
- `execution_mode` must fail closed unless it is an explicitly allowed mode for the current environment.
- `feature_flags_snapshot` must prove that live execution and every mutation class are separately enabled before a future live run can proceed.
- `requested_agent_keys` must match an allowlist defined in a later approved mutation policy.

## Execution Plan Contract

An `execution_plan` describes what could happen after validation. It must remain non-mutating until approvals, locks, and audit ledger writes exist.

Required fields:

- `plan_id`
- `request_id`
- `ordered_steps`
- `allowed_mutation_types`
- `blocked_mutation_types`
- `required_approvals`
- `required_locks`
- `expected_artifacts`
- `validation_policy`
- `rollback_required`
- `can_execute_live`

Validation rules:

- `can_execute_live` must be a boolean and must default to false.
- `allowed_mutation_types` must be empty unless a future approved policy explicitly allows each mutation class.
- `blocked_mutation_types` must include application submission, resume rewriting, tailoring generation, packet generation, scoring formula changes, ranking changes, scraper/source mutation, RAG corpus mutation, and deletion of production records for the first live prototype.
- `rollback_required` must be true for any mutable production field unless the policy explicitly marks the action non-reversible and blocks automatic retry.
- A `rollback_plan` must be present before `can_execute_live` can be true.

## Mutation Proposal Contract

A `mutation_proposal` is separate from execution. It describes a possible change and cannot commit that change.

Required fields:

- `mutation_id`
- `target_type`
- `target_id`
- `field_name`
- `before_value`
- `proposed_after_value`
- `reason_codes`
- `evidence_refs`
- `source_agent_key`
- `confidence`
- `requires_approval`
- `rollback_strategy`
- `idempotency_key`

Validation rules:

- `before_value` must be captured before approval and before mutation.
- `proposed_after_value` must be validated against the future mutation policy.
- `evidence_refs` can include current read-only chain/generator artifacts, but those artifacts must not execute mutations directly.
- `requires_approval` must be true for every production mutation.

## Approval Contract

An `approval_record` records human review. Approval is not execution; it only unlocks a bounded proposal for a bounded time and scope.

Required fields:

- `approval_id`
- `mutation_ids`
- `approved_by`
- `approved_at_utc`
- `approval_scope`
- `expiration_utc`
- `rejection_reason`
- `approval_status`
- `human_review_notes`

Validation rules:

- `approval_status` must distinguish pending, approved, rejected, expired, cancelled, and consumed.
- `approval_scope` must bind approval to exact mutation ids, target ids, expected before values, environment, and owner context.
- Expired, rejected, cancelled, or already consumed approvals cannot permit execution.

## Execution Result Contract

An `execution_attempt` records one bounded try to execute an approved plan. An `execution_result` records the outcome of that attempted plan. Both must be paired with audit ledger entries.

Required fields:

- `execution_id`
- `request_id`
- `plan_id`
- `status`
- `started_at_utc`
- `completed_at_utc`
- `steps_attempted`
- `mutations_attempted`
- `mutations_succeeded`
- `mutations_failed`
- `rollback_status`
- `artifacts_written`
- `validation_status`
- `reason_codes`

Validation rules:

- `status` must distinguish blocked, skipped, dry_run, pending_approval, running, succeeded, failed, rolled_back, rollback_failed, and cancelled.
- `mutations_attempted` must be zero unless approval, feature flag, environment gate, idempotency key, execution lock, audit ledger write, and rollback plan checks all pass.
- `validation_status` must fail closed if expected artifacts, before values, approval scope, lock ownership, or feature flag snapshots do not match.

## Safety Invariants

- No mutation without an approved mutation proposal.
- No application submission without explicit separate approval.
- No queue mutation without before/after capture.
- No scoring/ranking changes without separate approved policy.
- No live execution without feature flag and environment gate.
- No execution without idempotency key.
- No execution without lock.
- No execution without audit ledger write.
- No execution without rollback plan for mutable fields.
- No hidden automatic execution.
- No scheduler execution until separately approved.

## Allowed Future Mutation Types

These mutation types may be considered for a first controlled prototype only after the future gates are complete:

- Queue diagnostic status update.
- Operator-approved queue action update.
- Artifact status marker.

Do NOT allow application submission yet.

## Forbidden Mutation Types for First Live Prototype

- Application submission.
- Resume rewriting.
- Tailoring generation.
- Packet generation.
- Scoring formula changes.
- Ranking changes.
- Scraper/source mutation.
- RAG corpus mutation.
- Deletion of production records.

## Failure Modes and Rollback Requirements

- Partial mutation: capture exact before/after state, stop further mutations, validate affected records, and run the approved rollback plan when reversible.
- Duplicate execution: reject or return the prior result by `idempotency_key`; never apply the same mutation twice.
- Stale artifact versions: block execution when input artifact refs, schema versions, owner context, or pipeline run ids do not match.
- Missing approval: block before acquiring mutation capability.
- Expired approval: block and require fresh human review.
- Lock collision: block or wait according to a future explicit lock policy; never run concurrently on the same mutable scope.
- Validation failure: block before mutation or roll back after mutation according to the affected field policy.
- Artifact write failure: block execution if required audit or result artifacts cannot be written.
- Rollback failure: record `rollback_failed`, alert the operator, block automatic retry, and preserve evidence for manual recovery.

## Compatibility With Current Read-Only Chain

The current manual read-only adapter chain and explicit read-only chain artifact generator remain diagnostic. Their artifacts can become input evidence to future `mutation_proposal` records, but they must not execute mutations directly.

Future compatibility checks must validate artifact schema version, artifact path, owner context, pipeline run id, source queue snapshot, generator version, and expected reason-code vocabulary before any proposal uses the artifacts as evidence.

## Future Implementation Gates

The following gates must be completed in later planning-first phases before live execution can be considered:

- Mutation policy design.
- Approval gate design.
- Audit ledger schema.
- Idempotency/locking design.
- Dry-run simulator.
- Read-only approval UI mock.
- Feature flag policy.
- Operator runbook update.

These gates are prerequisites only. Completing one gate must not imply live orchestration, automatic execution, DB writes, queue mutation, application submission, or scheduler/background execution.
