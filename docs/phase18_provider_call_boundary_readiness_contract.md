# Phase 18 Provider-Call Boundary Readiness Contract

## Scope

Phase 18J is docs/tests-only and authorizes no runtime behavior. Phase 18J does
not implement a provider-call boundary. Phase 18J does not call or activate a
provider. Phase 18J does not access secrets. Phase 18J does not create network
traffic. It adds no API route, UI behavior, collector behavior, provider SDK
call, network call, secrets access, approval creation, decision persistence,
audit persistence, scoring/ranking mutation, queue mutation, resume mutation,
execution request, application execution, or application submission.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This provider-call boundary readiness contract follows:

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

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

A future boundary must preserve these agents' separate responsibilities and
must not become scoring, ranking, queueing, resume, execution, or submission
authority.

## Provider-call boundary readiness purpose

A future provider-call boundary may isolate the exact moment where a provider
SDK/network call would be allowed. The boundary must require separately
approved preview, decision, activation, adapter, dry-run packet, response
validation, readback, and audit contracts before any call.

The boundary must not own scoring, ranking, queueing, resume mutation, approval
creation, decision persistence, audit persistence, execution request creation,
application execution, or application submission. Provider output must remain
advisory until a separate mutation phase is approved.

Provider-call readiness is not provider execution.

## Allowed future provider-call boundary statuses

The complete allowed future provider-call boundary status set is:

1. `not_available`
2. `boundary_not_configured`
3. `boundary_disabled`
4. `boundary_readiness_incomplete`
5. `boundary_ready_for_separate_call_phase`
6. `boundary_blocked`
7. `boundary_failed_closed`

Unknown or missing statuses must be treated as `boundary_failed_closed`.

## Required future provider-call boundary fields

Every future provider-call boundary readiness record must expose:

1. `boundary_id` — boundary id
2. `boundary_status` — boundary status
3. `provider_name` — provider name
4. `provider_operation` — provider operation
5. `model_or_endpoint_identifier` — model or endpoint identifier
6. `requested_capability` — requested capability
7. `linked_preview_id` — linked preview id
8. `linked_decision_id` — linked decision id
9. `linked_activation_id` — linked activation id
10. `linked_adapter_id` — linked adapter id
11. `linked_dry_run_packet_id` — linked dry-run packet id
12. `linked_response_validation_id` — linked response validation id
13. `linked_readback_id` — linked readback id
14. `linked_audit_id` — linked audit id
15. `linked_trace_or_readback_id` — linked trace/readback id
16. `required_feature_flags` — required feature flags
17. `operator_or_reviewer_id` — operator/reviewer id
18. `dry_run_packet_status` — dry-run packet status
19. `response_validation_status` — response validation status
20. `readback_status` — readback status
21. `audit_status` — audit status
22. `secrets_reference_name_only` — secrets reference name only
23. `network_policy_summary` — network policy summary
24. `timeout_policy` — timeout policy
25. `retry_policy` — retry policy
26. `rate_limit_policy` — rate limit policy
27. `cost_limit_policy` — cost limit policy
28. `output_schema_summary` — output schema summary
29. `safety_flag_summary` — safety flag summary
30. `missing_requirements` — missing requirements
31. `fail_closed_reason` — fail-closed reason
32. `rollback_or_disable_reference` — rollback/disable reference
33. `created_timestamp` — created timestamp

Missing required fields must keep the boundary unavailable, incomplete,
blocked, or failed closed.

## Readiness prerequisites

A future readiness evaluation must require:

1. Linked approval preview exists
2. Linked operator decision exists
3. Linked activation plan exists
4. Linked adapter contract exists
5. Linked dry-run packet exists
6. Linked response validation contract exists
7. Linked readback/audit contract exists
8. Required feature flags are default-off and explicitly named
9. Secrets reference name only is available
10. Network policy is defined
11. Timeout policy is defined
12. Retry policy is defined
13. Rate limit policy is defined
14. Cost limit policy is defined
15. Rollback/disable reference is defined
16. Mutation-disabled gate is present

Satisfying these prerequisites establishes readiness for separate review only.
It does not authorize a provider call.

## Required future default-off gates

A future implementation must require all of these independently named,
default-off gates:

1. Global provider runtime flag
2. Provider-specific flag
3. Provider-call-boundary flag
4. Operation-specific flag
5. Human decision required flag
6. Dry-run packet required flag
7. Response-validation required flag
8. Readback/audit required flag
9. Mutation-disabled flag
10. Submission-disabled flag

No single gate may imply or replace another gate.

## Boundary safety requirements

- Boundary readiness evaluation must be deterministic.
- Boundary readiness evaluation must not call providers.
- Boundary readiness evaluation must not read secret values.
- Boundary readiness evaluation must not create network traffic.
- Boundary readiness evaluation must not persist approvals, decisions, or
  audit records.
- Boundary readiness evaluation must not mutate final score, rank, queue,
  resume, or application state.
- Boundary readiness evaluation must fail closed when any prerequisite is
  missing.
- Boundary readiness output must remain advisory and review-only.
- Provider-call readiness must require a separate later provider-call phase.

## Failed-closed boundary conditions

A future boundary must be blocked or `boundary_failed_closed` for:

1. Missing provider name
2. Missing provider operation
3. Missing requested capability
4. Missing linked preview id
5. Missing linked decision id
6. Missing linked activation id
7. Missing linked adapter id
8. Missing linked dry-run packet id
9. Missing linked response validation id
10. Missing linked readback id
11. Missing linked audit id
12. Missing linked trace/readback id
13. Missing required feature flag
14. Missing operator/reviewer id
15. Missing secrets reference name only
16. Missing network policy
17. Missing timeout policy
18. Missing retry policy
19. Missing rate limit policy
20. Missing cost limit policy
21. Unsafe safety flags
22. Secret value detected
23. Attempted provider call
24. Attempted mutation or submission

No failed-closed condition may expand authority, expose a secret, call a
provider, create network traffic, persist state, mutate state, execute an
application, or submit an application.

## Minimum future observability

Future boundary readiness observability must expose:

1. Boundary status
2. Provider name
3. Provider operation
4. Requested capability
5. Linked preview id
6. Linked decision id
7. Linked activation id
8. Linked adapter id
9. Linked dry-run packet id
10. Linked response validation id
11. Linked readback id
12. Linked audit id
13. Linked trace/readback id
14. Readiness prerequisite summary
15. Safety flag summary
16. Missing requirements
17. Fail-closed reason

Observability must remain passive, omit secret values, and trigger no provider,
persistence, or mutation behavior.

## Not authorized by Phase 18J

- No provider-call boundary implementation.
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

Phase 18J defines readiness criteria only. It creates no provider-call
boundary, provider client, network request, secret lookup, approval, decision
persistence, audit persistence, mutation, execution, or submission path.

## Recommended next phase

Phase 18K should be a docs/tests-only mutation boundary readiness contract,
still no provider call and still no mutation.
