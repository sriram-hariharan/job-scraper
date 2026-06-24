# Phase 18 Mutation Boundary Readiness Contract

## Scope

Phase 18K is docs/tests-only and authorizes no runtime behavior. Phase 18K does
not implement a mutation boundary. Phase 18K does not mutate scoring, ranking,
queue, resume, application state, execution requests, application executions,
or submissions. Phase 18K does not call or activate a provider. Phase 18K does
not access secrets. Phase 18K does not create network traffic.

Phase 18K adds no API route, UI behavior, collector behavior, provider SDK
call, network call, secrets access, approval creation, decision persistence,
audit persistence, scoring/ranking mutation, queue mutation, resume mutation,
execution request, application execution, or application submission.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This mutation boundary readiness contract follows:

- `phase17-three-core-shadow-readiness-release-v1`
- `phase18a-live-readiness-approval-boundary-v1`
- `phase18b-human-approval-gate-contract-v1`
- `phase18c-approval-preview-readonly-v1`
- `phase18d-operator-decision-capture-contract-v1`
- `phase18e-live-provider-activation-plan-v1`
- `phase18f-provider-runtime-adapter-contract-v1`
- `phase18g-live-provider-dry-run-packet-contract-v1`
- `phase18h-provider-response-validation-contract-v1`
- `phase18i-provider-readback-audit-contract-v1`
- `phase18j-provider-call-boundary-readiness-contract-v1`

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

The mutation boundary must keep prefilter relevance, JD intelligence, and final
application scoring separate.

## Mutation boundary readiness purpose

A future mutation boundary may isolate whether advisory evidence can become a
persisted workflow change. The boundary must not combine provider execution
with mutation.

The boundary must not combine scoring mutation, ranking mutation, queue
mutation, resume mutation, execution request creation, application execution,
or application submission into one approval.

Mutation readiness is not mutation execution.

Mutation readiness is not automatic application submission.

## Separately scoped future mutation categories

Each future category requires a separate scope and approval:

1. Final scoring mutation
2. Ranking mutation
3. Queue mutation
4. Resume mutation
5. Execution request creation
6. Application execution
7. Application submission
8. DB write/persistence

Approval or readiness for one category does not imply readiness for another.

## Allowed future mutation boundary statuses

The complete allowed future mutation boundary status set is:

1. `not_available`
2. `mutation_boundary_not_configured`
3. `mutation_boundary_disabled`
4. `mutation_readiness_incomplete`
5. `mutation_ready_for_separate_mutation_phase`
6. `mutation_blocked`
7. `mutation_failed_closed`

Unknown or missing statuses must be treated as `mutation_failed_closed`.

## Required future mutation boundary fields

Every future mutation boundary readiness record must expose:

1. `mutation_boundary_id` — mutation boundary id
2. `mutation_boundary_status` — mutation boundary status
3. `requested_mutation_category` — requested mutation category
4. `requested_capability` — requested capability
5. `target_context_summary` — target context summary
6. `linked_preview_id` — linked preview id
7. `linked_decision_id` — linked decision id
8. `linked_activation_id` — linked activation id
9. `linked_adapter_id` — linked adapter id
10. `linked_dry_run_packet_id` — linked dry-run packet id
11. `linked_response_validation_id` — linked response validation id
12. `linked_readback_id` — linked readback id
13. `linked_audit_id` — linked audit id
14. `linked_provider_call_boundary_id` — linked provider-call boundary id
15. `linked_trace_or_readback_id` — linked trace/readback id
16. `advisory_score_summary` — advisory score summary
17. `advisory_ranking_summary` — advisory ranking summary
18. `advisory_queue_recommendation_summary` — advisory queue recommendation summary
19. `evidence_summary` — evidence summary
20. `safety_flag_summary` — safety flag summary
21. `required_feature_flags` — required feature flags
22. `operator_or_reviewer_id` — operator/reviewer id
23. `mutation_disabled_gate_status` — mutation-disabled gate status
24. `submission_disabled_gate_status` — submission-disabled gate status
25. `rollback_or_disable_reference` — rollback/disable reference
26. `missing_requirements` — missing requirements
27. `fail_closed_reason` — fail-closed reason
28. `created_timestamp` — created timestamp

Missing required fields must keep the boundary unavailable, incomplete,
blocked, or failed closed.

## Mutation readiness prerequisites

A future mutation readiness evaluation must require:

1. Linked approval preview exists
2. Linked operator decision exists
3. Linked readback/audit contract exists
4. Linked provider-call boundary exists when provider evidence is used
5. Advisory evidence exists
6. Requested mutation category is single-scope
7. Operator/reviewer id exists
8. Required feature flags are default-off and explicitly named
9. Mutation-disabled gate is present
10. Submission-disabled gate is present
11. Rollback/disable reference is defined
12. Tests prove no submit/apply path is reachable

Satisfying these prerequisites establishes readiness for separate review only.
It does not authorize mutation.

## Required future default-off gates

A future implementation must require all of these independently named,
default-off gates:

1. Global mutation runtime flag
2. Mutation-boundary flag
3. Requested-mutation-category flag
4. Human decision required flag
5. Advisory-evidence required flag
6. Provider-evidence isolated flag
7. Mutation-disabled flag
8. Submission-disabled flag
9. Rollback-required flag

No single gate may imply or replace another gate.

## Mutation boundary safety requirements

- Mutation readiness evaluation must be deterministic.
- Mutation readiness evaluation must not call providers.
- Mutation readiness evaluation must not read secret values.
- Mutation readiness evaluation must not create network traffic.
- Mutation readiness evaluation must not mutate final score, rank, queue,
  resume, application state, execution request, application execution, or
  submission.
- Mutation readiness evaluation must fail closed when any prerequisite is
  missing.
- Mutation readiness output must remain advisory and review-only.
- Provider-call readiness and mutation readiness must remain separate.
- Each mutation category must require a separate later implementation phase.
- Application submission must remain separately blocked.

## Failed-closed mutation boundary conditions

A future boundary must be blocked or `mutation_failed_closed` for:

1. Missing requested mutation category
2. Unknown requested mutation category
3. Mixed mutation categories
4. Missing target context summary
5. Missing linked preview id
6. Missing linked decision id
7. Missing linked readback id
8. Missing linked audit id
9. Missing provider-call boundary id when provider evidence is used
10. Missing linked trace/readback id
11. Missing advisory evidence
12. Missing operator/reviewer id
13. Missing required feature flag
14. Missing mutation-disabled gate
15. Missing submission-disabled gate
16. Missing rollback/disable reference
17. Unsafe safety flags
18. Attempted provider call
19. Attempted scoring mutation
20. Attempted ranking mutation
21. Attempted queue mutation
22. Attempted resume mutation
23. Attempted execution request creation
24. Attempted application execution
25. Attempted application submission

No failed-closed condition may expand authority, call a provider, mutate state,
create execution work, execute an application, or submit an application.

## Minimum future observability

Future mutation boundary readiness observability must expose:

1. Mutation boundary status
2. Requested mutation category
3. Requested capability
4. Target context summary
5. Linked preview id
6. Linked decision id
7. Linked readback id
8. Linked audit id
9. Linked provider-call boundary id
10. Linked trace/readback id
11. Advisory evidence summary
12. Safety flag summary
13. Missing requirements
14. Fail-closed reason

Observability must remain passive and trigger no provider, persistence,
mutation, execution, or submission behavior.

## Not authorized by Phase 18K

- No mutation boundary implementation.
- No live provider execution.
- No provider SDK/network call.
- No secrets access.
- No approval creation runtime.
- No decision persistence runtime.
- No audit persistence runtime.
- No DB writes.
- No final scoring mutation.
- No ranking mutation.
- No queue mutation.
- No resume mutation.
- No execution request creation.
- No application execution.
- No application submission.

Phase 18K defines readiness criteria only. It creates no mutation boundary,
provider call, persistence, scoring/ranking change, queue/resume change,
execution request, application execution, or submission path.

## Recommended next phase

Phase 18L should be a Phase 18 safety wrap and release checkpoint before Phase
19 read-only runtime implementation.
