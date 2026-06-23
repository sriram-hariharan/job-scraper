# Phase 18 Read-Only Approval Preview

## Scope

Phase 18C is docs/tests-only and authorizes no runtime behavior. It adds no API
route, UI behavior, collector behavior, provider call, approval creation,
scoring/ranking mutation, queue mutation, resume mutation, execution request,
application execution, or application submission.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This preview contract follows:

- `phase17-three-core-shadow-readiness-release-v1`
- `phase18a-live-readiness-approval-boundary-v1`
- `phase18b-human-approval-gate-contract-v1`

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

The preview must preserve the separation between relevance, intelligence, final
scoring, provider behavior, approval decisions, and every mutation or
application path.

## Read-only approval preview purpose

A future preview may assemble reviewable approval-request metadata before any
human decision. The preview must not create an approval. The preview must not
persist an approval record. The preview must not execute or submit anything.
The preview must not call providers or SDK/network runtime. The preview must
not mutate scoring, ranking, queue, resume, or application state.

A preview is a review artifact only. It is neither an approval request record
nor evidence that a human decision has occurred.

## Allowed preview statuses

The complete allowed preview-status set is:

1. `not_available`
2. `preview_ready`
3. `preview_incomplete`
4. `preview_blocked`
5. `failed_closed`

Unknown or missing statuses must be treated as `failed_closed`.

## Required future preview fields

Every future preview must expose:

1. `preview_id` — preview id
2. `preview_status` — preview status
3. `requested_capability` — requested capability
4. `target_context_summary` — target context summary
5. `requester_source` — requester/source
6. `evidence_summary` — evidence summary
7. `proposed_action_summary` — proposed action summary
8. `risk_summary` — risk summary
9. `safety_flag_summary` — safety flag summary
10. `required_feature_flags` — required feature flags
11. `missing_requirements` — missing requirements
12. `fail_closed_reasons` — fail-closed reasons
13. `expiry_recommendation` — expiry recommendation
14. `rollback_or_disable_reference` — rollback/disable reference
15. `linked_trace_or_readback_id` — linked trace/readback id
16. `created_timestamp` — created timestamp

Missing required fields must make the preview incomplete or failed closed.

## Preview-only capability categories

The future preview may describe one of these categories without authorizing it:

1. Live provider execution preview
2. Provider SDK/network call preview
3. Final scoring mutation preview
4. Ranking mutation preview
5. Queue mutation preview
6. Resume mutation preview
7. Approval creation preview
8. Execution request creation preview
9. Application execution preview
10. Application submission preview
11. DB write preview
12. Secrets access preview

Previewing a capability does not authorize the capability.

Previewing a capability does not create approval records.

Previewing a capability does not imply human approval.

Previewing one capability does not imply approval or preview readiness for another.

## Hard rules

- No preview may directly submit an application.
- No preview may create an approval record.
- No preview may create an execution request.
- No preview may call a provider.
- No preview may read secrets.
- No preview may write to the database.
- No preview may mutate final scoring, ranking, queue, resume, or application
  state.
- No preview may combine provider execution with
  scoring/ranking/queue/resume/application submission.
- No preview may bypass default-off feature flags.
- No preview may bypass dry-run/readback evidence.

Preview construction and any future approval decision or executor must remain
separate, independently reviewed scopes.

## Failed-closed preview conditions

A future preview must be blocked, incomplete, or `failed_closed` for:

1. Missing target context
2. Missing requested capability
3. Unknown requested capability
4. Missing evidence summary
5. Missing feature flag
6. Unsafe safety flags
7. Expired preview window
8. Mismatched trace/readback id
9. Missing rollback/disable reference
10. Attempted execution or mutation

No failed-closed condition may create a record, approval, execution request, or
retry with expanded authority.

## Minimum future observability

Future preview readback must expose:

1. Preview status
2. Requested capability
3. Target context summary
4. Evidence summary
5. Proposed action summary
6. Risk summary
7. Safety flag summary
8. Missing requirements
9. Fail-closed reasons
10. Linked trace/readback id

Observability remains passive and must not trigger the previewed capability.

## Not authorized by Phase 18C

- No live provider execution.
- No provider SDK/network call.
- No approval creation runtime.
- No DB writes.
- No secrets access.
- No final scoring mutation.
- No ranking mutation.
- No queue mutation.
- No resume mutation.
- No execution request creation.
- No application execution.
- No application submission.

Phase 18C defines a future read-only contract only. It creates no approval,
decision, persistence, provider call, mutation, execution, or submission path.

## Recommended next phase

Phase 18D should be operator decision capture contract, still no execution.
