# No Auto-Apply Safety Policy

ApplyLens is an assistive job-search product. It may assist, preview, rank,
prepare, explain, and guide, but it must preserve manual user control over the
final application process.

## Permanent product boundary

This policy is not a temporary default-off feature. It is a permanent product
boundary:

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission

Final application submission must remain under manual user control outside
any autonomous execution path. No feature flag, provider integration, agent,
API, UI control, pipeline stage, or later phase may convert preparation or
readiness into autonomous application execution or submission.

Provider-call readiness is preflight/readback only. It may describe whether
caller-supplied metadata is reviewable, but it must never authorize a provider
call, application execution, or submission.

## Phase 20 evidence

Phases 20A through 20C performed no provider calls, no network calls, no
database writes, no persistence, no mutation, no application execution, and
no submission:

- `phase20a-provider-call-readiness-experiment-v1`
- `phase20b-provider-call-readiness-api-readback-v1`
- `phase20c-provider-call-readiness-ui-readback-v1`

This policy continues the safety boundaries established by:

- `phase19-readonly-approval-workflow-release-v1`
- `phase18-safety-wrap-release-v1`
