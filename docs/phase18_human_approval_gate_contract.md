# Phase 18 Human Approval Gate Contract

## Scope

Phase 18B is docs/tests-only and authorizes no runtime behavior. It adds no API
route, UI behavior, collector behavior, provider call, scoring/ranking
mutation, queue mutation, resume mutation, execution request, application
execution, or application submission.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This contract follows:

- `phase17-three-core-shadow-readiness-release-v1`
- `phase18a-live-readiness-approval-boundary-v1`

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

An approval gate must not merge these agents' responsibilities or grant one
agent authority over provider execution, scoring, ranking, queueing, resume
mutation, execution, or submission.

## Human approval gate purpose

A future gate must capture a human/operator decision before any proposed live
behavior can proceed. The gate itself must not execute the action. It must
produce reviewable decision metadata that can be audited, expired, revoked,
and evaluated independently from any later executor.

An `approved` decision is evidence of a narrowly scoped human decision, not an
execution command.

## Allowed future decision states

The complete allowed future decision-state set is:

1. `not_requested`
2. `requested`
3. `approved`
4. `rejected`
5. `expired`
6. `revoked`
7. `failed_closed`

Unknown or missing states must be treated as `failed_closed`.

## Required future approval request fields

Every future approval request must carry:

1. `request_id` — request id
2. `requested_capability` — requested capability
3. `requester_source` — requester/source
4. `target_context` — target job/application/run context
5. `evidence_summary` — evidence summary
6. `proposed_action_summary` — proposed action summary
7. `risk_summary` — risk summary
8. `safety_flags` — safety flags
9. `expiry_timestamp` — expiry timestamp
10. `created_timestamp` — created timestamp
11. `operator_or_reviewer_id` — operator id or reviewer id
12. `decision_timestamp` — decision timestamp
13. `decision_reason` — decision reason
14. `rollback_or_disable_reference` — rollback/disable reference

Missing required fields must prevent approval from authorizing later work.

## Capabilities requiring separate approval

Each capability below requires its own future approval:

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

Approval for one capability does not imply approval for another. Approval must
be single-capability scoped, time-bound, auditable, reversible, and
fail-closed.

## Hard rules

- No approval may directly submit an application.
- No approval may combine provider execution with
  scoring/ranking/queue/resume/application submission.
- No approval may bypass default-off feature flags.
- No approval may bypass dry-run/readback evidence.
- No approval may bypass tests proving no submit/apply path is reachable unless
  submission itself is the separately approved capability in a later phase.

The approval decision and any later executor must remain separate components
with independently reviewed scopes.

## Fail-closed conditions

A future gate must return or remain `failed_closed` for:

1. Missing approval
2. Expired approval
3. Revoked approval
4. Rejected approval
5. Mismatched capability
6. Missing evidence
7. Missing feature flag
8. Unsafe safety flags
9. Unknown target context
10. Provider/runtime error

No fail-closed condition may be converted into an implicit approval, retry, or
execution request.

## Minimum future observability

Future approval readback must expose:

1. Decision state
2. Requested capability
3. Operator/reviewer id
4. Decision timestamp
5. Evidence summary
6. Safety flag summary
7. Fail-closed reason
8. Linked trace/readback id

Observability must remain reviewable without triggering the approved
capability.

## Not authorized by Phase 18B

- No live provider execution.
- No provider SDK/network call.
- No DB writes.
- No secrets access.
- No final scoring mutation.
- No ranking mutation.
- No queue mutation.
- No resume mutation.
- No approval creation runtime.
- No execution request creation.
- No application execution.
- No application submission.

Phase 18B defines a future contract only. It does not create approval records,
persist decisions, call providers, or enable any action path.

## Recommended next phase

Phase 18C should be a read-only approval preview, still no execution.

