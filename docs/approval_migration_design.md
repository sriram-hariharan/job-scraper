# Approval Migration Design

Doc path: `docs/approval_migration_design.md`

Phase 109A is approval migration design only. This phase is docs/tests only and adds no runtime behavior.

## A. Current Design Scope

This design defines the future migration plan for approval storage after the physical approval storage schema design is complete.

No runtime behavior changes in this phase.

No migration file added.

No SQL file added.

No DB schema file added.

No SQL DDL added.

No storage API added.

No DB writes added.

No queue mutation added.

No execution enabled.

No mutation execution enabled.

No application submission enabled.

`workflow_runner.py` remains dry-run only.

The app-service gate remains blocking-only.

The queue gate remains blocking-only.

Blocked results remain non-executing.

## B. Migration Objective

The future migration must create the physical approval storage tables only after an explicit implementation phase is approved.

The migration objective is to map the documented `agentic_approval_requests` and `agentic_approval_audit_events` table plan into reviewed SQL DDL in a later separate phase, with safety checks before any DB write or runtime integration.

## C. Forward Migration Ordering

Forward migration must create `agentic_approval_requests` before `agentic_approval_audit_events`.

The audit table depends on the request table because audit events reference approval requests.

The future migration must validate idempotency_key uniqueness.

The future migration must validate approval_status constraints.

The future migration must validate audit event foreign key behavior.

## D. Rollback Ordering

Rollback must drop `agentic_approval_audit_events` before `agentic_approval_requests`.

The rollback plan must respect the audit-event foreign key dependency and avoid orphaned schema objects.

Rollback design remains documentation-only in this phase.

## E. Data Safety Checks

The future migration must not store secrets.

The future migration must not store raw credentials.

The future migration must not store raw resume/application-submission payloads.

Application submission remains blocked until a later explicit phase.

Approved requests cannot bypass safety gates.

Approved requests cannot execute if safety gates fail.

## F. Idempotency And Repeat-Run Behavior

The future migration design should be repeat-run safe through explicit table-existence checks or migration tooling metadata in a later implementation phase.

The future migration must validate idempotency_key uniqueness before any approval storage implementation uses the table.

Repeat-run behavior must not create duplicate constraints, duplicate indexes, duplicate audit tables, or inconsistent status constraints.

## G. Pre-Migration Validation

Before any future migration implementation, validation must confirm that no DB schema file, migration file, SQL file, SQL DDL, storage API, DB write path, approval endpoint, queue mutation, execution path, mutation execution, or application submission path is being bundled into the design phase.

Future pre-migration validation should also confirm table names, column names, status constraints, idempotency key uniqueness, audit foreign-key behavior, rollback order, and data minimization.

## H. Post-Migration Validation

After a future migration implementation, validation should confirm both tables exist in the expected order, primary keys and unique keys are present, audit events reference approval requests, approval_status constraints are enforced, rollback removes audit events before requests, and no secrets or raw credentials are stored.

Post-migration validation is not implemented in this phase.

## I. Forbidden Shortcuts

Do not add migration files next unless explicitly approved.

Do not add SQL DDL next unless explicitly approved.

Do not add DB schema files next unless explicitly approved.

Do not add storage APIs next.

Do not add DB writes next.

Do not enable execution next.

Do not add queue mutation next.

Do not add application submission next.

Do not treat this migration design as permission to implement persistence.

## J. Recommended Next Phase

Recommended next phase: 109B approval migration design final audit and merge gate.

After 109B, recommend: 110A approval migration design release safety checkpoint, docs/tests only.

Release safety checkpoint: `docs/approval_migration_design_release_safety_checkpoint.md`.

## K. Verification Contract Phrases

Verification contract phrases

- Approval migration design: PASS
- Migration implementation: NOT_YET
- Migration file implementation: NOT_YET
- SQL DDL implementation: NOT_YET
- Physical DB schema implementation: NOT_YET
- Storage API implementation: NOT_YET
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
- no migration file added
- no SQL file added
- no DB schema file added
- no SQL DDL added
- no storage API added
- no DB writes added
- no queue mutation added
- no execution enabled
- no mutation execution enabled
- no application submission enabled
- workflow_runner.py remains dry-run only
- app-service gate remains blocking-only
- queue gate remains blocking-only
- blocked results remain non-executing
- forward migration must create agentic_approval_requests before agentic_approval_audit_events
- rollback must drop agentic_approval_audit_events before agentic_approval_requests
- migration must validate idempotency_key uniqueness
- migration must validate approval_status constraints
- migration must validate audit event foreign key behavior
- migration must not store secrets
- migration must not store raw credentials
- migration must be separate future phase
- SQL DDL must be separate future phase
