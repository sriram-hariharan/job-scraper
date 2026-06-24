# Phase 18 Live-Provider Dry-Run Packet Contract

## Scope

Phase 18G is docs/tests-only and authorizes no runtime behavior. Phase 18G does
not implement a dry-run packet builder. Phase 18G does not implement an
adapter. Phase 18G does not activate a provider. It adds no API route, UI
behavior, collector behavior, provider SDK call, network call, secrets access,
approval creation, decision persistence, scoring/ranking mutation, queue
mutation, resume mutation, execution request, application execution, or
application submission.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This live-provider dry-run packet contract follows:

- `phase17-three-core-shadow-readiness-release-v1`
- `phase18a-live-readiness-approval-boundary-v1`
- `phase18b-human-approval-gate-contract-v1`
- `phase18c-approval-preview-readonly-v1`
- `phase18d-operator-decision-capture-contract-v1`
- `phase18e-live-provider-activation-plan-v1`
- `phase18f-provider-runtime-adapter-contract-v1`

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

A future packet must preserve the separate responsibilities of these agents
and must not become provider, scoring, ranking, queueing, resume, execution, or
submission authority.

## Live-provider dry-run packet purpose

A future dry-run packet may assemble the exact reviewable inputs that would be
sent to a provider. The packet must be redacted, schema-described, and
reviewable before any provider call.

The packet must not call the provider. The packet must not read secret values.
The packet must not create network traffic. The packet must not mutate scoring,
ranking, queue, resume, or application state. The packet must not execute or
submit anything.

## Allowed future dry-run packet statuses

The complete allowed future dry-run packet-status set is:

1. `not_available`
2. `packet_incomplete`
3. `packet_ready_for_review`
4. `packet_blocked`
5. `packet_failed_closed`

Unknown or missing statuses must be treated as `packet_failed_closed`.

## Required future dry-run packet fields

Every future dry-run packet must expose:

1. `packet_id` — packet id
2. `packet_status` — packet status
3. `provider_name` — provider name
4. `provider_operation` — provider operation
5. `model_or_endpoint_identifier` — model or endpoint identifier
6. `requested_capability` — requested capability
7. `target_context_summary` — target context summary
8. `linked_preview_id` — linked preview id
9. `linked_decision_id` — linked decision id
10. `linked_activation_id` — linked activation id
11. `linked_adapter_id` — linked adapter id
12. `linked_trace_or_readback_id` — linked trace/readback id
13. `redacted_request_preview` — redacted request preview
14. `request_schema_summary` — request schema summary
15. `response_schema_summary` — response schema summary
16. `input_redaction_summary` — input redaction summary
17. `output_redaction_summary` — output redaction summary
18. `safety_flag_summary` — safety flag summary
19. `required_feature_flags` — required feature flags
20. `timeout_policy` — timeout policy
21. `retry_policy` — retry policy
22. `rate_limit_policy` — rate limit policy
23. `cost_limit_policy` — cost limit policy
24. `network_policy_summary` — network policy summary
25. `secrets_reference_name_only` — secrets reference name only
26. `missing_requirements` — missing requirements
27. `fail_closed_reason` — fail-closed reason
28. `rollback_or_disable_reference` — rollback/disable reference
29. `created_timestamp` — created timestamp

Missing required fields must make the future packet incomplete, blocked, or
failed closed.

## Required redaction guarantees

A future dry-run packet must guarantee:

1. No secret value in packet
2. No raw API key
3. No provider token
4. No password
5. No unredacted environment variable value
6. No personally sensitive data beyond the approved target context summary
7. Secrets reference name only is allowed

Redaction failure must never be converted into a partial or review-ready
packet.

## Future packet validation categories

A future packet contract may distinguish:

1. Required field validation
2. Schema summary validation
3. Redaction validation
4. Safety flag validation
5. Feature flag validation
6. Linked preview validation
7. Linked decision validation
8. Linked activation validation
9. Linked adapter validation
10. Network policy validation
11. Retry/rate-limit/cost policy validation

Phase 18G does not implement any of those validations.

## Required future default-off gates

A future implementation must require all of these independently named,
default-off gates:

1. Global provider runtime flag
2. Provider-specific flag
3. Adapter-specific flag
4. Dry-run packet flag
5. Operation-specific flag
6. Human decision required flag
7. Mutation-disabled flag

No single gate may imply or replace another gate.

## Packet safety requirements

- Packet construction must be deterministic.
- Packet construction must not call providers.
- Packet construction must not read secret values.
- Packet construction must not create network traffic.
- Packet construction must not persist approvals or decisions.
- Packet construction must not mutate final score, rank, queue, resume, or
  application state.
- Packet construction must fail closed when redaction or required links are
  missing.
- Packet output must remain advisory and review-only.

## Failed-closed packet conditions

A future packet must be blocked or `packet_failed_closed` for:

1. Missing provider name
2. Missing provider operation
3. Missing requested capability
4. Missing linked preview id
5. Missing linked decision id
6. Missing linked activation id
7. Missing linked adapter id
8. Missing target context summary
9. Missing redacted request preview
10. Missing request schema summary
11. Missing response schema summary
12. Missing redaction summary
13. Missing feature flag
14. Unsafe safety flags
15. Secret value detected
16. Network policy missing
17. Timeout policy missing
18. Retry policy missing
19. Rate limit policy missing
20. Cost limit policy missing
21. Attempted provider call
22. Attempted mutation or submission

No failed-closed condition may expand authority, expose a secret, call a
provider, create network traffic, mutate state, execute an application, or
submit an application.

## Minimum future observability

Future packet readback must expose:

1. Packet status
2. Provider name
3. Provider operation
4. Requested capability
5. Linked preview id
6. Linked decision id
7. Linked activation id
8. Linked adapter id
9. Linked trace/readback id
10. Redaction validation summary
11. Safety flag summary
12. Missing requirements
13. Fail-closed reason

Observability must remain passive, omit secret values, and trigger no provider
or mutation behavior.

## Not authorized by Phase 18G

- No dry-run packet builder implementation.
- No adapter implementation.
- No live provider execution.
- No provider SDK/network call.
- No secrets access.
- No approval creation runtime.
- No decision persistence runtime.
- No DB writes.
- No final scoring mutation.
- No ranking mutation.
- No queue mutation.
- No resume mutation.
- No execution request creation.
- No application execution.
- No application submission.

Phase 18G defines a future contract only. It creates no packet builder,
adapter, provider client, network request, secret lookup, approval, decision
persistence, mutation, execution, or submission path.

## Recommended next phase

Phase 18H should be a docs/tests-only provider response validation contract,
still no provider call and still no mutation.
