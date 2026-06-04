# Mutation Policy And Approval Gate Design

Doc path: `docs/mutation_policy_approval_gate_design.md`

Phase 35A is design only. No implementation in this phase adds live orchestration, mutation execution, approval API, approval UI, approval storage, database schema, scheduler/background execution, autonomous execution, LLM calls, queue mutation, scoring/ranking changes, or application submission.

No live execution is enabled. No mutation is enabled. No approval API/UI/storage is implemented. `workflow_runner.py` remains dry-run only, and read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Purpose

Define the future approval and mutation boundary for any production-capable agent execution. This policy defines what future live execution may propose, what must remain blocked, and what human approval must prove before any mutation could be attempted in a later implementation phase.

This document is planning-only. It does not add mutation APIs, approval storage, execution code, database writes, application submission, queue updates, scheduler behavior, UI controls, or runtime integration.

The future live-run audit ledger schema proposal is detailed in `docs/live_run_audit_ledger_schema_design.md`. That document is design/schema proposal-only and does not enable persistence, ledger writes, live execution, or mutation execution.

## Current State

The current system remains read-only and diagnostic:

- Read-only adapters exist for advisory job prioritization, tailoring decision, and operator review.
- The manual read-only adapter chain runs only from explicit operator/test invocation with explicit inputs.
- The explicit read-only chain artifact generator requires an explicit queue input and explicit output directory.
- Diagnostic artifacts can be verified and displayed in Agentic Review when already present.
- No DB write is added for live orchestration.
- No queue mutation is enabled.
- No application submission is enabled.
- No live orchestration is enabled.

Current artifacts and read-only chain/generator outputs may inform future proposals, but they are not approvals and cannot directly mutate production state.

## Mutation Classification

Future policy evaluation must classify every requested action into exactly one mutation class:

- `forbidden_mutation`: an action that must be blocked before approval and before execution.
- `approval_required_mutation`: a narrowly allowed future proposal that cannot execute unless human approval, audit, idempotency, locking, rollback, feature flag, and environment gates pass.
- `diagnostic_artifact_write`: a diagnostic/read-only artifact write that does not mutate production decisions.
- `read_only_observation`: a read-only inspection of owner-scoped artifacts, metadata, or diagnostics.
- `operator_note`: an operator-authored note proposal that is separate from queue action, scoring, ranking, tailoring, packet, source, RAG, or submission behavior.
- `future_deferred_mutation`: a possible future mutation type that is explicitly outside the first live prototype and must remain blocked until a separate policy phase approves it.

Unclassified actions must fail closed as `forbidden_mutation`.

## Allowed First-Phase Mutation Proposals

The first future mutation-capable prototype, if separately approved later, may only propose these actions. This section allows proposals only, not execution:

- Queue diagnostic status marker proposal.
- Operator-reviewed queue action update proposal.
- Artifact status marker proposal.
- Operator note proposal.

These proposal types still require before/after capture, evidence, policy evaluation, human approval, idempotency key, execution lock, audit ledger entry, rollback handling when possible, and final validation before any later live execution can attempt them.

## Explicitly Forbidden Mutations

The following mutation types must remain blocked for the first live prototype:

- Application submission.
- Resume rewriting.
- Tailoring generation.
- Packet generation.
- Scoring formula changes.
- Ranking changes.
- Scraper/source mutation.
- RAG corpus mutation.
- Deletion of production records.
- Credential/token mutation.
- User profile mutation.
- Hidden scheduler/background execution.
- Mutation without before/after capture.
- Mutation without approval.
- Mutation without audit ledger entry.
- Mutation without idempotency key.
- Mutation without execution lock.
- Mutation without rollback plan where rollback is possible.

No application submission is allowed by this policy.

## Approval Gate Contract

A future `approval_record` is a gate, not execution. It proves bounded human review for specific mutation proposals and must not be treated as broad permission.

Proposed fields:

- `approval_id`
- `mutation_ids`
- `requested_by`
- `approved_by`
- `approval_status`
- `approval_scope`
- `created_at_utc`
- `approved_at_utc`
- `expires_at_utc`
- `review_notes`
- `rejection_reason`
- `risk_level`
- `required_evidence_refs`
- `approved_mutation_types`
- `blocked_mutation_types`
- `idempotency_key`
- `audit_ledger_ref`

Approval records must bind to exact mutation ids, target ids, expected before values, mutation types, owner context, pipeline run context, environment, evidence refs, and expiration.

## Approval States

Future approval storage, if implemented in a later phase, must distinguish these states:

- `draft`: proposal is being assembled and cannot execute.
- `pending_review`: proposal is ready for human review and cannot execute yet.
- `approved`: reviewer approved the bounded proposal within scope.
- `rejected`: reviewer rejected the proposal.
- `expired`: approval window ended before execution.
- `revoked`: approval was withdrawn before execution.
- `consumed`: approval was already used by an execution attempt.
- `blocked_by_policy`: policy denied the proposal before or during review.

Only `approved` can ever proceed to later execution checks, and even then it must still pass scope, expiry, evidence, lock, idempotency, audit, rollback, feature flag, environment, and validation gates.

## Approval Scope

Future approvals must be narrow:

- `single_mutation`
- `single_pipeline_run`
- `single_job`
- `bounded_batch`
- `diagnostic_only`

Broad/global approval is disallowed for the first prototype. Approval cannot cover unknown future mutations, new target ids, unrelated pipeline runs, different owners, or hidden scheduler/background execution.

## Evidence Required Before Approval

Human approval cannot be requested until the proposal includes:

- `before_value`
- `proposed_after_value`
- `source_agent_key`
- `reason_codes`
- `evidence_refs`
- `validation_status`
- `rollback_strategy`
- `artifact_version_refs`
- Operator-visible summary.
- Risk classification.

Evidence must be stable, owner-scoped, and tied to the same pipeline run or artifact snapshot that the mutation proposal references.

## Human Review Checklist

Before approval, the reviewer must confirm:

- Target is correct.
- Before/after is correct.
- Evidence supports the change.
- Mutation type is allowed.
- No application submission is included.
- Rollback path exists or non-rollback status is explicitly accepted.
- Idempotency key is present.
- Execution lock scope is clear.
- Audit ledger entry will be written.
- Feature flag/environment gate is enabled.

If any checklist item fails, the approval must be rejected or marked `blocked_by_policy`.

## Policy Evaluation Order

A future implementation must evaluate gates in this order:

1. Feature flag and environment gate.
2. Mutation type allow/deny list.
3. Required evidence presence.
4. Idempotency key presence.
5. Lock availability.
6. Approval state/scope/expiry.
7. Rollback requirement.
8. Audit ledger write readiness.
9. Final pre-execution validation.

Every step must fail closed. No mutation without approval can pass this order.

## Failure And Denial Behavior

- Missing approval: block with `missing_approval`.
- Expired approval: block with `approval_expired`.
- Rejected approval: block with `approval_rejected`.
- Approval scope mismatch: block with `approval_scope_mismatch`.
- Missing evidence: block with `missing_required_evidence`.
- Forbidden mutation type: block with `forbidden_mutation_type`.
- Stale artifact version: block with `stale_artifact_version`.
- Missing rollback plan: block with `missing_rollback_plan` when rollback is possible.
- Lock collision: block or wait according to a later explicit lock policy; never mutate concurrently.
- Audit ledger unavailable: block with `audit_ledger_unavailable`.
- Validation failure: block before mutation, or roll back according to the approved rollback strategy if mutation already began in a later implementation.

Denied proposals must not retry automatically and must not be converted into another mutation type without fresh policy evaluation.

## Audit And Trace Requirements

Future implementation must record immutable audit ledger entries for:

- Proposal creation.
- Approval decision.
- Policy evaluation result.
- Execution attempt.
- Blocked attempt.
- Rollback attempt.
- Reviewer identity.
- Timestamps.
- Reason codes.
- Before/after values where applicable.

Diagnostic traces must remain distinct from production mutation audit entries. Audit ledger writes must be ready before any future mutable execution attempt.

## Relationship To Current Read-Only Chain

The current read-only chain and explicit generator remain diagnostic only. Their artifacts can become evidence for future mutation proposals, but cannot directly mutate anything.

Future proposals that cite read-only chain/generator artifacts must validate artifact versions, owner context, pipeline run context, source queue snapshot, reason-code vocabulary, and schema compatibility before requesting approval.

## Future Implementation Gates

Before coding mutation execution, later phases must complete:

- Audit ledger schema design.
- Idempotency/locking design.
- Dry-run mutation simulator.
- Read-only approval UI mock.
- Feature flag and environment gate policy.
- Rollback design.
- Approval API/storage design.
- Operator runbook update.

These gates do not themselves enable live orchestration, mutation execution, approval storage, DB writes, queue mutation, application submission, or scheduler/background execution.
