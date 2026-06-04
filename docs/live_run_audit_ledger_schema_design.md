# Live-Run Audit Ledger Schema Design

Doc path: `docs/live_run_audit_ledger_schema_design.md`

Phase 36A is a design/schema proposal only. No implementation in this phase adds DB tables, migrations, storage APIs, live orchestration, mutation execution, approval API, approval UI, approval storage, scheduler/background execution, autonomous execution, LLM calls, queue mutation, scoring/ranking changes, or application submission.

No DB table or migration is added. No live execution is enabled. No mutation is enabled. No approval API/UI/storage is implemented. `workflow_runner.py` remains dry-run only, and read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Purpose

Define a future immutable audit trail for production-capable agent execution, approvals, mutations, validation, rollback, and blocked attempts before any live orchestration implementation exists.

This proposal names ledger entities, event vocabulary, linkage rules, failure behavior, privacy boundaries, and future gates. It does not create database schema, write ledger rows, wire storage APIs, approve mutations, run agents, mutate queues, submit applications, or change pipeline behavior.

## Current Boundary

The current system remains read-only and diagnostic:

- Read-only adapters exist for advisory job prioritization, tailoring decision, and operator review.
- The manual read-only adapter chain runs only from explicit operator/test invocation with explicit inputs.
- The explicit read-only chain artifact generator requires an explicit queue input and explicit output directory.
- Diagnostic artifacts can be verified and displayed in Agentic Review when already present.
- Current chain/generator artifacts are diagnostic artifacts only.
- No live orchestration.
- No scheduler/background execution.
- No UI run button.
- No `workflow_runner.py` execution path.
- No DB write for live orchestration.
- No queue mutation.
- No application submission.
- No scoring/ranking changes.
- No approval API/UI/storage.
- No production mutation.

## Ledger Design Principles

- Immutable append-only events: ledger entries are appended and never silently rewritten.
- No silent mutation: every future mutable action must have a visible proposal, approval state, execution attempt, validation result, and final event.
- Before/after capture: every mutable target must capture `before_value_json`, `proposed_after_value_json`, and `after_value_json` where applicable.
- Owner/run scoping: every event must scope to `owner_user_id` and relevant `pipeline_run_id`.
- Idempotency: duplicate execution requests, proposals, approvals, and mutation attempts must be detected by stable `idempotency_key` values.
- Lock awareness: mutable targets must include `execution_lock_key` so concurrent mutations are blocked or serialized by a future lock policy.
- Approval linkage: mutation-capable execution attempts must link to bounded approval records.
- Rollback traceability: rollback plans and rollback attempts must link to the original mutation and execution attempt.
- Artifact version references: evidence and generated diagnostics must be referenced by stable artifact refs, versions, hashes, or paths rather than copied wholesale.
- Reason codes: every blocked, denied, approved, applied, failed, and rolled-back event must include machine-readable reason codes.
- Validation status: event payloads must record the validation state before and after any future execution attempt.
- Human-readable summary: operators need a concise summary for review, support, and incident response.
- Machine-readable payload: automation needs normalized JSON payloads for validation, export, and audit review.

## Proposed Tables/Entities

Design only; no table is created in this phase.

- `agentic_execution_requests`: future operator/system requests to evaluate a bounded execution intent.
- `agentic_execution_plans`: validated plans derived from execution requests.
- `agentic_mutation_proposals`: proposed production changes separated from execution and commit.
- `agentic_approval_records`: human review decisions and approval scope.
- `agentic_execution_attempts`: bounded execution attempts after gates, locks, and audit readiness.
- `agentic_audit_ledger_entries`: immutable event ledger for proposals, approvals, attempts, mutations, validation, rollback, and blocked operations.
- `agentic_rollback_plans`: documented recovery paths tied to mutable targets and original mutations.
- `agentic_execution_locks`: persisted lock records for mutable target scopes.

## `agentic_audit_ledger_entries` Fields

Proposed fields:

- `ledger_entry_id`
- `event_type`
- `event_status`
- `created_at_utc`
- `owner_user_id`
- `pipeline_run_id`
- `request_id`
- `plan_id`
- `mutation_id`
- `approval_id`
- `execution_id`
- `rollback_id`
- `agent_key`
- `target_type`
- `target_id`
- `mutation_type`
- `before_value_json`
- `after_value_json`
- `proposed_after_value_json`
- `artifact_refs_json`
- `evidence_refs_json`
- `reason_codes_json`
- `validation_status`
- `risk_level`
- `idempotency_key`
- `execution_lock_key`
- `actor_type`
- `actor_id`
- `summary`
- `payload_json`

## Event Types

Proposed `event_type` values:

- `execution_request_created`
- `execution_plan_created`
- `mutation_proposed`
- `approval_requested`
- `approval_approved`
- `approval_rejected`
- `approval_expired`
- `approval_revoked`
- `execution_attempt_started`
- `execution_attempt_blocked`
- `execution_attempt_succeeded`
- `execution_attempt_failed`
- `mutation_applied`
- `mutation_blocked`
- `rollback_planned`
- `rollback_started`
- `rollback_succeeded`
- `rollback_failed`
- `validation_passed`
- `validation_failed`
- `policy_denied`

## Status Values

Proposed `event_status` values:

- `pending`
- `approved`
- `rejected`
- `blocked`
- `running`
- `succeeded`
- `failed`
- `expired`
- `revoked`
- `rolled_back`
- `rollback_failed`

## Linkage Rules

- Every mutation proposal links to `request_id` and `plan_id`.
- Every approval links to `mutation_ids` or an explicit approval scope.
- Every execution attempt links to `approval_id` when mutation-capable.
- Every `mutation_applied` event links to `before_value_json` and `after_value_json`.
- Every rollback event links to the original `mutation_id` and `rollback_plan`.
- Every event includes `idempotency_key` where applicable.
- Every mutable target includes `execution_lock_key`.
- Every validation event links to the request, plan, execution attempt, and relevant artifact refs.
- Every blocked operation records reason codes and the actor or system component that attempted it.

## Retention And Privacy

- Avoid secrets in ledger payloads.
- Redact tokens, credentials, cookies, API keys, session identifiers, and private auth material.
- Avoid storing full resumes, private documents, full job packets, or generated tailoring text directly in ledger entries.
- Store artifact refs, hashes, versions, row ids, and minimal before/after field snapshots where possible.
- Define retention windows in a later storage design phase.
- Preserve exportability for operator review, incident response, and compliance without exposing unnecessary private content.

## Query Examples

Design-level examples only:

- Events for a `pipeline_run_id`.
- Mutations for a `target_id`.
- Blocked attempts by `event_type=execution_attempt_blocked`, `mutation_blocked`, or `policy_denied`.
- Approvals by reviewer using `actor_type=human_reviewer` and `actor_id`.
- Rollback history for a `mutation_id`.
- Duplicate `idempotency_key` attempts.
- Validation failures by `agent_key`, `mutation_type`, or `risk_level`.

## Failure Behavior

If the ledger is unavailable, future runtime must block mutation if ledger unavailable. It must not fall back to unaudited execution, must not write production state, must not mutate queues, must not submit applications, and must not retry destructive work automatically.

The safe fallback is to emit a diagnostic artifact only, mark the attempt blocked, preserve enough context for operator review, and require a human operator to decide the next step after ledger service recovery.

## Relationship To Current Read-Only Chain

The current read-only chain/generator artifacts may become `artifact_refs_json` or `evidence_refs_json` values in a future ledger, but the current chain and generator must not write ledger rows directly in this phase.

Current diagnostics remain separate from production mutation audit entries. Any future proposal that cites read-only chain/generator artifacts must validate artifact version, owner context, pipeline run context, source queue snapshot, reason-code vocabulary, and schema compatibility before requesting approval.

## Future Gates

Before any live audit ledger implementation or mutation-capable execution exists, later phases must complete:

- Idempotency/locking design.
- DB migration design.
- Storage API design.
- Ledger write transaction design.
- Rollback design.
- Approval storage design.
- Read-only ledger viewer mock.
- Failure-mode tests.
- Operator runbook update.

These gates are prerequisites only. Completing them must not by itself enable live orchestration, mutation execution, approval storage, DB writes, queue mutation, application submission, scheduler/background execution, or autonomous execution.
