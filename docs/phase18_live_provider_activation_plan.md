# Phase 18 Protected Live-Provider Activation Plan

## Scope

Phase 18E is docs/tests-only and authorizes no runtime behavior. Phase 18E does
not activate a provider. It adds no API route, UI behavior, collector behavior,
provider SDK call, network call, secrets access, approval creation, decision
persistence, scoring/ranking mutation, queue mutation, resume mutation,
execution request, application execution, or application submission.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This protected plan follows:

- `phase17-three-core-shadow-readiness-release-v1`
- `phase18a-live-readiness-approval-boundary-v1`
- `phase18b-human-approval-gate-contract-v1`
- `phase18c-approval-preview-readonly-v1`
- `phase18d-operator-decision-capture-contract-v1`

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

Provider activation must remain separate from each agent's deterministic
responsibility and from all scoring, ranking, queue, resume, execution, and
submission authority.

## Live-provider activation purpose

A future live-provider phase may make one isolated provider call only after
separate approval. Provider activation must remain isolated from scoring
mutation, ranking mutation, queue mutation, resume mutation, approval creation,
execution request creation, application execution, and application submission.

Provider output must remain advisory until a separate mutation phase is
approved. Provider execution must not imply scoring/ranking/queue/resume/
application authority.

## Allowed future provider activation statuses

The complete allowed activation-status set is:

1. `not_configured`
2. `disabled`
3. `approval_required`
4. `ready_for_dry_run`
5. `ready_for_live_provider_call`
6. `provider_call_completed`
7. `provider_call_blocked`
8. `provider_call_failed_closed`

Unknown or missing statuses must be treated as
`provider_call_failed_closed`.

## Required future provider activation fields

Every future activation record or readback must expose:

1. `activation_id` — activation id
2. `requested_capability` — requested capability
3. `provider_name` — provider name
4. `provider_operation` — provider operation
5. `model_or_endpoint_identifier` — model or endpoint identifier
6. `target_context_summary` — target context summary
7. `linked_preview_id` — linked preview id
8. `linked_decision_id` — linked decision id
9. `linked_trace_or_readback_id` — linked trace/readback id
10. `required_feature_flags` — required feature flags
11. `approval_status` — approval status
12. `decision_status` — decision status
13. `dry_run_evidence_summary` — dry-run evidence summary
14. `safety_flag_summary` — safety flag summary
15. `secrets_reference_name_only` — secrets reference name only
16. `network_policy_summary` — network policy summary
17. `timeout_policy` — timeout policy
18. `retry_policy` — retry policy
19. `rate_limit_policy` — rate limit policy
20. `cost_limit_policy` — cost limit policy
21. `redaction_policy` — redaction policy
22. `output_schema_summary` — output schema summary
23. `fail_closed_reason` — fail-closed reason
24. `rollback_or_disable_reference` — rollback/disable reference
25. `created_timestamp` — created timestamp
26. `completed_timestamp` — completed timestamp

No field may contain a secret value. Missing required fields must block the
future provider call.

## Required default-off future feature flags

A future implementation must require all of these independently named,
default-off gates:

1. Global provider runtime flag
2. Provider-specific flag
3. Capability-specific flag
4. Operator decision required flag
5. Dry-run evidence required flag

No single flag may imply or replace another flag.

## Provider safety requirements

- No secret values may be logged.
- Network/provider SDK calls must be behind explicit default-off flags.
- Provider failures must fail closed.
- Provider responses must be schema-validated before use.
- Provider outputs must be treated as advisory evidence only.
- Provider timeout, retry, rate limit, and cost controls must be explicit.
- Provider output must be traceable through readback.
- Provider output must not mutate final score, rank, queue, resume, or
  application state.

Provider activation and any later mutation or executor must remain separate,
independently approved phases.

## Failed-closed provider conditions

A future activation must be blocked or
`provider_call_failed_closed` for:

1. Missing provider flag
2. Missing provider-specific flag
3. Missing capability-specific flag
4. Missing operator decision
5. Missing dry-run evidence
6. Missing linked preview id
7. Missing linked decision id
8. Missing target context
9. Missing safe secrets reference
10. Unsafe safety flags
11. Network policy missing
12. Timeout policy missing
13. Retry policy missing
14. Rate limit policy missing
15. Cost limit policy missing
16. Output schema validation missing
17. Provider error
18. Provider timeout
19. Attempted mutation or submission

No failed-closed condition may expand authority, retry without policy, mutate
state, create execution work, execute an application, or submit an application.

## Minimum future observability

Future activation readback must expose:

1. Activation status
2. Requested capability
3. Provider name
4. Provider operation
5. Linked preview id
6. Linked decision id
7. Linked trace/readback id
8. Dry-run evidence summary
9. Safety flag summary
10. Network policy summary
11. Timeout/retry/rate-limit/cost policy summary
12. Output schema validation status
13. Fail-closed reason

Observability must not expose secret values or trigger another provider call.

## Not authorized by Phase 18E

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

Phase 18E is a plan only. It creates no provider client, network request,
secret lookup, approval, decision persistence, mutation, execution, or
submission path.

## Recommended next phase

Phase 18F should be a docs/tests-only provider runtime adapter contract, still
no provider call and still no mutation.

