# Phase 18 Operator Decision Capture Contract

## Scope

Phase 18D is docs/tests-only and authorizes no runtime behavior. It adds no API
route, UI behavior, collector behavior, provider call, approval creation,
decision persistence, scoring/ranking mutation, queue mutation, resume
mutation, execution request, application execution, or application submission.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This decision-capture contract follows:

- `phase17-three-core-shadow-readiness-release-v1`
- `phase18a-live-readiness-approval-boundary-v1`
- `phase18b-human-approval-gate-contract-v1`
- `phase18c-approval-preview-readonly-v1`

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

Decision capture must preserve the separation between relevance, intelligence,
final scoring, preview, human decision, provider behavior, mutation, execution,
and submission.

## Operator decision capture purpose

A future decision capture may record or represent a human/operator decision
after a read-only approval preview. The decision capture contract must remain
separate from approval preview, provider execution, scoring/ranking mutation,
queue mutation, resume mutation, execution request creation, application
execution, and application submission.

A captured decision is not an executor.

A captured decision is not a provider call.

A captured decision is not a submission command.

The future representation of a decision may be consumed only by a separate,
later, independently approved executor phase.

## Allowed future decision capture statuses

The complete allowed decision-capture status set is:

1. `not_requested`
2. `decision_pending`
3. `decision_captured`
4. `decision_rejected`
5. `decision_expired`
6. `decision_revoked`
7. `decision_blocked`
8. `failed_closed`

Unknown or missing statuses must be treated as `failed_closed`.

## Required future decision capture fields

Every future decision capture must expose:

1. `decision_id` — decision id
2. `preview_id` — preview id
3. `requested_capability` — requested capability
4. `target_context_summary` — target context summary
5. `operator_or_reviewer_id` — operator/reviewer id
6. `decision_status` — decision status
7. `decision_value` — decision value
8. `decision_reason` — decision reason
9. `evidence_summary` — evidence summary
10. `risk_summary` — risk summary
11. `safety_flag_summary` — safety flag summary
12. `linked_trace_or_readback_id` — linked trace/readback id
13. `expiry_timestamp` — expiry timestamp
14. `created_timestamp` — created timestamp
15. `decision_timestamp` — decision timestamp
16. `rollback_or_disable_reference` — rollback/disable reference
17. `fail_closed_reason` — fail-closed reason

Missing required fields must keep the decision pending, blocked, or failed
closed.

## Allowed decision values

The complete allowed decision-value set is:

1. `approve`
2. `reject`
3. `revoke`
4. `expire`
5. `request_changes`
6. `no_decision`
7. `failed_closed`

An `approve` value remains review metadata and is not authority to execute.

## Capabilities requiring separate decision capture

Each capability below requires its own future decision capture:

1. Live provider execution
2. Provider SDK/network calls
3. Final scoring mutation
4. Ranking mutation
5. Queue mutation
6. Resume mutation
7. Approval creation
8. Execution request creation
9. Application execution
10. Application submission
11. DB writes
12. Secrets access

A decision for one capability does not authorize another capability. A
decision must be single-capability scoped, time-bound, auditable, reversible,
fail-closed, and tied to a read-only preview.

## Hard rules

- No decision capture may directly submit an application.
- No decision capture may call a provider.
- No decision capture may create an execution request.
- No decision capture may mutate scoring, ranking, queue, resume, or
  application state.
- No decision capture may write secrets or log secrets.
- No decision capture may bypass default-off feature flags.
- No decision capture may bypass dry-run/readback evidence.
- No decision capture may combine provider execution with
  scoring/ranking/queue/resume/application submission.
- No decision capture may transform a preview into execution without a
  separate later approved executor phase.

Decision capture, persistence, and execution must remain separately designed
and independently approved scopes.

## Failed-closed decision conditions

A future decision capture must be blocked or `failed_closed` for:

1. Missing preview id
2. Missing operator/reviewer id
3. Missing requested capability
4. Unknown requested capability
5. Mismatched capability
6. Missing evidence summary
7. Missing safety flag summary
8. Unsafe safety flags
9. Expired decision window
10. Revoked decision
11. Rejected decision
12. Missing rollback/disable reference
13. Attempted execution or mutation

No failed-closed condition may produce an implicit approval, provider call,
mutation, execution request, application execution, or submission.

## Minimum future observability

Future decision-capture readback must expose:

1. Decision status
2. Decision value
3. Requested capability
4. Operator/reviewer id
5. Decision reason
6. Target context summary
7. Evidence summary
8. Risk summary
9. Safety flag summary
10. Fail-closed reason
11. Linked trace/readback id

Observability must remain passive and must not trigger the captured decision.

## Not authorized by Phase 18D

- No live provider execution.
- No provider SDK/network call.
- No approval creation runtime.
- No decision persistence runtime.
- No DB writes.
- No secrets access.
- No final scoring mutation.
- No ranking mutation.
- No queue mutation.
- No resume mutation.
- No execution request creation.
- No application execution.
- No application submission.

Phase 18D defines a future decision metadata contract only. It adds no
persistence, provider call, mutation, execution, or submission path.

## Recommended next phase

Phase 18E should be a protected live-provider activation plan, still no
mutation.

