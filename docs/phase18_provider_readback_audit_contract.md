# Phase 18 Provider Readback and Audit Contract

## Scope

Phase 18I is docs/tests-only and authorizes no runtime behavior. Phase 18I does
not implement provider readback. Phase 18I does not implement audit
persistence. Phase 18I does not implement response validation. Phase 18I does
not call or activate a provider. It adds no API route, UI behavior, collector
behavior, provider SDK call, network call, secrets access, approval creation,
decision persistence, audit persistence, scoring/ranking mutation, queue
mutation, resume mutation, execution request, application execution, or
application submission.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This provider readback and audit contract follows:

- `phase17-three-core-shadow-readiness-release-v1`
- `phase18a-live-readiness-approval-boundary-v1`
- `phase18b-human-approval-gate-contract-v1`
- `phase18c-approval-preview-readonly-v1`
- `phase18d-operator-decision-capture-contract-v1`
- `phase18e-live-provider-activation-plan-v1`
- `phase18f-provider-runtime-adapter-contract-v1`
- `phase18g-live-provider-dry-run-packet-contract-v1`
- `phase18h-provider-response-validation-contract-v1`

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

Future readback and audit behavior must preserve these agents' separate
responsibilities and must not become provider, scoring, ranking, queueing,
resume, execution, or submission authority.

## Provider readback and audit purpose

A future readback may summarize provider interaction evidence after a
separately approved provider call and separately approved response validation.
A future audit record may preserve review metadata only after a separately
approved persistence phase.

Readback must remain passive. Audit must not become execution authority.
Readback and audit must not own provider invocation. Readback and audit must
not mutate final scoring, ranking, queue, resume, or application state.
Readback and audit must not create approval records, decisions, execution
requests, application executions, or submissions.

## Allowed future readback statuses

The complete allowed future readback-status set is:

1. `not_available`
2. `readback_not_started`
3. `readback_ready`
4. `readback_complete`
5. `readback_blocked`
6. `readback_failed_closed`

Unknown or missing readback statuses must be treated as
`readback_failed_closed`.

## Allowed future audit statuses

The complete allowed future audit-status set is:

1. `audit_not_available`
2. `audit_not_started`
3. `audit_ready`
4. `audit_recorded`
5. `audit_blocked`
6. `audit_failed_closed`

Unknown or missing audit statuses must be treated as `audit_failed_closed`.

## Required future readback fields

Every future readback must expose:

1. `readback_id` — readback id
2. `readback_status` — readback status
3. `provider_name` — provider name
4. `provider_operation` — provider operation
5. `requested_capability` — requested capability
6. `linked_preview_id` — linked preview id
7. `linked_decision_id` — linked decision id
8. `linked_activation_id` — linked activation id
9. `linked_adapter_id` — linked adapter id
10. `linked_dry_run_packet_id` — linked dry-run packet id
11. `linked_response_validation_id` — linked response validation id
12. `linked_trace_or_readback_id` — linked trace/readback id
13. `advisory_output_summary` — advisory output summary
14. `validation_status_summary` — validation status summary
15. `redaction_summary` — redaction summary
16. `safety_flag_summary` — safety flag summary
17. `missing_requirements` — missing requirements
18. `fail_closed_reason` — fail-closed reason
19. `created_timestamp` — created timestamp
20. `completed_timestamp` — completed timestamp

Missing required fields must keep readback unavailable, blocked, or failed
closed.

## Required future audit fields

Every future audit record must expose:

1. `audit_id` — audit id
2. `audit_status` — audit status
3. `audit_scope` — audit scope
4. `provider_name` — provider name
5. `provider_operation` — provider operation
6. `requested_capability` — requested capability
7. `linked_readback_id` — linked readback id
8. `linked_preview_id` — linked preview id
9. `linked_decision_id` — linked decision id
10. `linked_activation_id` — linked activation id
11. `linked_adapter_id` — linked adapter id
12. `linked_dry_run_packet_id` — linked dry-run packet id
13. `linked_response_validation_id` — linked response validation id
14. `linked_trace_or_readback_id` — linked trace/readback id
15. `operator_or_reviewer_id` — operator/reviewer id
16. `decision_reason` — decision reason
17. `safety_flag_summary` — safety flag summary
18. `redaction_summary` — redaction summary
19. `fail_closed_reason` — fail-closed reason
20. `retention_policy_summary` — retention policy summary
21. `rollback_or_disable_reference` — rollback/disable reference
22. `created_timestamp` — created timestamp

Missing required fields must keep audit unavailable, blocked, or failed
closed.

## Future readback categories

A future readback may distinguish:

1. Advisory provider output summary
2. Response validation summary
3. Redaction and safety summary
4. Linked decision summary
5. Linked packet summary
6. Linked activation summary
7. Fail-closed summary
8. Passive trace summary

## Future audit categories

A future audit contract may distinguish:

1. Approval/decision audit metadata
2. Provider-call evidence audit metadata
3. Response-validation audit metadata
4. Redaction audit metadata
5. Safety-flag audit metadata
6. Rollback/disable audit metadata
7. Retention-policy audit metadata

Phase 18I does not implement any readback or audit operation.

## Required future default-off gates

A future implementation must require all of these independently named,
default-off gates:

1. Global provider runtime flag
2. Provider-specific flag
3. Readback flag
4. Audit flag
5. Response-validation flag
6. Human decision required flag
7. Mutation-disabled flag
8. Persistence-disabled flag

No single gate may imply or replace another gate.

## Readback and audit safety requirements

- Readback construction must be deterministic.
- Readback construction must not call providers.
- Readback construction must not read secret values.
- Readback construction must not create network traffic.
- Readback construction must not mutate final score, rank, queue, resume, or
  application state.
- Audit construction must not persist unless a separate persistence phase is
  approved.
- Audit construction must not expose secret values.
- Audit construction must not become approval, execution, or submission
  authority.
- Readback and audit output must remain advisory and review-only.
- Failures must fail closed.

## Failed-closed readback conditions

A future readback must be blocked or `readback_failed_closed` for:

1. Missing provider name
2. Missing provider operation
3. Missing requested capability
4. Missing linked preview id
5. Missing linked decision id
6. Missing linked activation id
7. Missing linked adapter id
8. Missing linked dry-run packet id
9. Missing linked response validation id
10. Missing advisory output summary
11. Missing validation status summary
12. Missing redaction summary
13. Unsafe safety flags
14. Secret value detected
15. Attempted provider call
16. Attempted mutation or submission

## Failed-closed audit conditions

A future audit must be blocked or `audit_failed_closed` for:

1. Missing audit scope
2. Missing linked readback id
3. Missing linked decision id
4. Missing linked response validation id
5. Missing operator/reviewer id
6. Missing retention policy summary
7. Missing rollback/disable reference
8. Unsafe safety flags
9. Secret value detected
10. Attempted persistence without approval
11. Attempted provider call
12. Attempted mutation or submission

No failed-closed condition may expand authority, expose a secret, call a
provider, persist without approval, mutate state, execute an application, or
submit an application.

## Minimum future observability

Future readback and audit observability must expose:

1. Readback status
2. Audit status
3. Provider name
4. Provider operation
5. Requested capability
6. Linked readback id
7. Linked preview id
8. Linked decision id
9. Linked activation id
10. Linked adapter id
11. Linked dry-run packet id
12. Linked response validation id
13. Linked trace/readback id
14. Advisory output summary
15. Validation status summary
16. Redaction summary
17. Safety flag summary
18. Fail-closed reason

Observability must remain passive, omit secret values, and trigger no provider,
persistence, or mutation behavior.

## Not authorized by Phase 18I

- No provider readback implementation.
- No audit persistence implementation.
- No response validator implementation.
- No dry-run packet builder implementation.
- No adapter implementation.
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

Phase 18I defines a future contract only. It creates no provider readback,
audit persistence, response validator, packet builder, adapter, provider
client, network request, secret lookup, approval, decision persistence,
mutation, execution, or submission path.

## Recommended next phase

Phase 18J should be a docs/tests-only provider-call boundary readiness
contract, still no provider call and still no mutation.
