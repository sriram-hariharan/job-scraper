# Phase 18 Provider Runtime Adapter Contract

## Scope

Phase 18F is docs/tests-only and authorizes no runtime behavior. Phase 18F does
not implement an adapter. Phase 18F does not activate a provider. It adds no API
route, UI behavior, collector behavior, provider SDK call, network call,
secrets access, approval creation, decision persistence, scoring/ranking
mutation, queue mutation, resume mutation, execution request, application
execution, or application submission.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This provider runtime adapter contract follows:

- `phase17-three-core-shadow-readiness-release-v1`
- `phase18a-live-readiness-approval-boundary-v1`
- `phase18b-human-approval-gate-contract-v1`
- `phase18c-approval-preview-readonly-v1`
- `phase18d-operator-decision-capture-contract-v1`
- `phase18e-live-provider-activation-plan-v1`

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

A future adapter must preserve the separate responsibilities of these agents
and must not become scoring, ranking, queueing, resume, approval, execution, or
submission authority.

## Provider runtime adapter purpose

A future adapter may isolate provider-specific request and response handling.
The adapter contract must separate configuration validation, request
preparation, provider invocation, response validation, readback, and downstream
mutation.

The adapter must not own scoring, ranking, queueing, resume mutation, approval
creation, execution request creation, application execution, or application
submission. The adapter must not log secrets. The adapter must not treat
provider output as final scoring authority.

## Allowed future adapter statuses

The complete allowed future adapter-status set is:

1. `not_configured`
2. `disabled`
3. `adapter_unavailable`
4. `adapter_config_validated`
5. `adapter_ready_for_dry_run`
6. `adapter_ready_for_provider_call`
7. `adapter_blocked`
8. `adapter_failed_closed`

Unknown or missing statuses must be treated as `adapter_failed_closed`.

## Required future adapter fields

Every future adapter record or readback must expose:

1. `adapter_id` — adapter id
2. `provider_name` — provider name
3. `provider_operation` — provider operation
4. `model_or_endpoint_identifier` — model or endpoint identifier
5. `requested_capability` — requested capability
6. `request_schema_summary` — request schema summary
7. `response_schema_summary` — response schema summary
8. `input_redaction_summary` — input redaction summary
9. `output_redaction_summary` — output redaction summary
10. `secrets_reference_name_only` — secrets reference name only
11. `required_feature_flags` — required feature flags
12. `timeout_policy` — timeout policy
13. `retry_policy` — retry policy
14. `rate_limit_policy` — rate limit policy
15. `cost_limit_policy` — cost limit policy
16. `network_policy_summary` — network policy summary
17. `dry_run_mode` — dry-run mode
18. `linked_preview_id` — linked preview id
19. `linked_decision_id` — linked decision id
20. `linked_activation_id` — linked activation id
21. `linked_trace_or_readback_id` — linked trace/readback id
22. `safety_flag_summary` — safety flag summary
23. `fail_closed_reason` — fail-closed reason
24. `rollback_or_disable_reference` — rollback/disable reference
25. `created_timestamp` — created timestamp
26. `completed_timestamp` — completed timestamp

No field may contain a secret value. Missing required fields must block future
adapter activity.

## Future adapter operation categories

A future adapter contract may distinguish these operation categories:

1. Configuration validation
2. Redacted request preview construction
3. Request schema validation
4. Response schema validation
5. Provider call boundary
6. Passive readback summary
7. Fail-closed result construction

Phase 18F does not implement any of these operations.

## Required future default-off feature flags

A future implementation must require all of these independently named,
default-off gates:

1. Global provider runtime flag
2. Provider-specific flag
3. Adapter-specific flag
4. Operation-specific flag
5. Dry-run-only flag
6. Human decision required flag
7. Mutation-disabled flag

No single flag may imply or replace another flag.

## Adapter safety requirements

- Provider SDK invocation must be isolated behind explicit default-off flags.
- External network calls must be blocked unless a later provider-call phase is
  separately approved.
- Secret values must never be logged or returned in readback.
- Request and response schemas must be explicit.
- Provider responses must be schema-validated before readback or downstream
  use.
- Provider outputs must remain advisory until a separate mutation phase is
  approved.
- Provider outputs must not mutate final score, rank, queue, resume, or
  application state.
- Timeout, retry, rate limit, and cost policies must be explicit.
- Adapter failures must fail closed.

## Prohibited adapter responsibilities

A future adapter must not own or perform:

1. Final scoring mutation
2. Ranking mutation
3. Queue mutation
4. Resume mutation
5. Approval creation
6. Decision persistence
7. Execution request creation
8. Application execution
9. Application submission
10. DB writes outside a separately approved persistence phase
11. Secrets retrieval without a separately approved secrets boundary

Adapter construction, persistence, mutation, execution, and submission must
remain separately designed and independently approved scopes.

## Failed-closed adapter conditions

A future adapter must be blocked or `adapter_failed_closed` for:

1. Missing global provider runtime flag
2. Missing provider-specific flag
3. Missing adapter-specific flag
4. Missing operation-specific flag
5. Missing linked preview id
6. Missing linked decision id
7. Missing linked activation id
8. Missing provider name
9. Missing provider operation
10. Missing model or endpoint identifier
11. Missing request schema
12. Missing response schema
13. Missing redaction policy
14. Missing timeout policy
15. Missing retry policy
16. Missing rate limit policy
17. Missing cost limit policy
18. Missing network policy
19. Unsafe safety flags
20. Secret value present in output
21. Attempted mutation or submission

No failed-closed condition may expand authority, expose a secret, create an
implicit retry, mutate state, execute an application, or submit an application.

## Minimum future observability

Future adapter readback must expose:

1. Adapter status
2. Provider name
3. Provider operation
4. Requested capability
5. Linked preview id
6. Linked decision id
7. Linked activation id
8. Linked trace/readback id
9. Request schema validation status
10. Response schema validation status
11. Redaction summary
12. Safety flag summary
13. Timeout/retry/rate-limit/cost policy summary
14. Fail-closed reason

Observability must remain passive, omit secret values, and trigger no provider
or mutation behavior.

## Not authorized by Phase 18F

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

Phase 18F defines a future contract only. It creates no adapter, provider
client, network request, secret lookup, approval, decision persistence,
mutation, execution, or submission path.

## Recommended next phase

Phase 18G should be a docs/tests-only live-provider dry-run packet contract,
still no provider call and still no mutation.
