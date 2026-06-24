# Phase 18 Provider Response Validation Contract

## Scope

Phase 18H is docs/tests-only and authorizes no runtime behavior. Phase 18H does
not implement response validation. Phase 18H does not implement a provider
adapter. Phase 18H does not call a provider. Phase 18H does not activate a
provider. It adds no API route, UI behavior, collector behavior, provider SDK
call, network call, secrets access, approval creation, decision persistence,
scoring/ranking mutation, queue mutation, resume mutation, execution request,
application execution, or application submission.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This provider response validation contract follows:

- `phase17-three-core-shadow-readiness-release-v1`
- `phase18a-live-readiness-approval-boundary-v1`
- `phase18b-human-approval-gate-contract-v1`
- `phase18c-approval-preview-readonly-v1`
- `phase18d-operator-decision-capture-contract-v1`
- `phase18e-live-provider-activation-plan-v1`
- `phase18f-provider-runtime-adapter-contract-v1`
- `phase18g-live-provider-dry-run-packet-contract-v1`

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

A future validator must preserve the separate responsibilities of these agents
and must not become provider, scoring, ranking, queueing, resume, execution, or
submission authority.

## Provider response validation purpose

A future validator may validate a provider response after a separately
approved provider call phase. The validator must treat provider output as
advisory evidence. The validator must not own provider invocation.

The validator must not mutate final scoring, ranking, queue, resume, or
application state. The validator must not create approval records, decisions,
execution requests, application executions, or submissions. The validator
must fail closed when response shape, schema, redaction, safety flags, or
linked trace context is invalid.

## Allowed future response validation statuses

The complete allowed future response-validation status set is:

1. `not_available`
2. `validation_not_started`
3. `validation_ready`
4. `validation_passed`
5. `validation_blocked`
6. `validation_failed_closed`

Unknown or missing statuses must be treated as `validation_failed_closed`.

## Required future response validation fields

Every future response validation record or readback must expose:

1. `validation_id` — validation id
2. `validation_status` — validation status
3. `provider_name` — provider name
4. `provider_operation` — provider operation
5. `model_or_endpoint_identifier` — model or endpoint identifier
6. `requested_capability` — requested capability
7. `linked_preview_id` — linked preview id
8. `linked_decision_id` — linked decision id
9. `linked_activation_id` — linked activation id
10. `linked_adapter_id` — linked adapter id
11. `linked_dry_run_packet_id` — linked dry-run packet id
12. `linked_trace_or_readback_id` — linked trace/readback id
13. `response_schema_summary` — response schema summary
14. `response_schema_validation_status` — response schema validation status
15. `response_redaction_summary` — response redaction summary
16. `output_safety_classification` — output safety classification
17. `advisory_output_summary` — advisory output summary
18. `unsafe_content_indicators` — unsafe content indicators
19. `missing_fields` — missing fields
20. `malformed_fields` — malformed fields
21. `safety_flag_summary` — safety flag summary
22. `fail_closed_reason` — fail-closed reason
23. `rollback_or_disable_reference` — rollback/disable reference
24. `created_timestamp` — created timestamp
25. `completed_timestamp` — completed timestamp

Missing required fields must make validation unavailable, blocked, or failed
closed.

## Future validation categories

A future response validator may distinguish:

1. Required field validation
2. Response schema validation
3. Response type validation
4. Response bounds validation
5. Redaction validation
6. Unsafe content validation
7. Safety flag validation
8. Linked trace/readback validation
9. Linked dry-run packet validation
10. Advisory-only classification validation

Phase 18H does not implement any of those validations.

## Required future default-off gates

A future implementation must require all of these independently named,
default-off gates:

1. Global provider runtime flag
2. Provider-specific flag
3. Adapter-specific flag
4. Response-validation flag
5. Operation-specific flag
6. Human decision required flag
7. Mutation-disabled flag

No single gate may imply or replace another gate.

## Response validation safety requirements

- Response validation must be deterministic.
- Response validation must not call providers.
- Response validation must not read secret values.
- Response validation must not create network traffic.
- Response validation must not persist approvals or decisions.
- Response validation must not mutate final score, rank, queue, resume, or
  application state.
- Response validation must not treat provider output as final scoring
  authority.
- Response validation must fail closed when schema validation or redaction
  fails.
- Response validation output must remain advisory and review-only.

## Failed-closed response validation conditions

A future response validation must be blocked or
`validation_failed_closed` for:

1. Missing provider name
2. Missing provider operation
3. Missing requested capability
4. Missing linked preview id
5. Missing linked decision id
6. Missing linked activation id
7. Missing linked adapter id
8. Missing linked dry-run packet id
9. Missing linked trace/readback id
10. Missing response schema summary
11. Missing response schema validation status
12. Malformed response
13. Missing required response fields
14. Unsafe content detected
15. Secret value detected
16. Missing safety flag summary
17. Unsafe safety flags
18. Advisory-only classification missing
19. Attempted provider call
20. Attempted mutation or submission

No failed-closed condition may expand authority, expose a secret, call a
provider, create network traffic, mutate state, execute an application, or
submit an application.

## Minimum future observability

Future response-validation readback must expose:

1. Validation status
2. Provider name
3. Provider operation
4. Requested capability
5. Linked preview id
6. Linked decision id
7. Linked activation id
8. Linked adapter id
9. Linked dry-run packet id
10. Linked trace/readback id
11. Response schema validation status
12. Response redaction summary
13. Output safety classification
14. Advisory output summary
15. Fail-closed reason

Observability must remain passive, omit secret values, and trigger no provider
or mutation behavior.

## Not authorized by Phase 18H

- No response validator implementation.
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

Phase 18H defines a future contract only. It creates no response validator,
packet builder, adapter, provider client, network request, secret lookup,
approval, decision persistence, mutation, execution, or submission path.

## Recommended next phase

Phase 18I should be a docs/tests-only provider readback and audit contract,
still no provider call and still no mutation.
