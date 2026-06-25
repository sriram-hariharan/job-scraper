# Phase 20D No Auto-Apply Safety Checkpoint

Phase 20D records the permanent product boundary against auto-apply. This
checkpoint is documentation and tests only and changes no runtime behavior.

This is not a temporary default-off feature. ApplyLens permits:

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission

The app may assist, preview, rank, prepare, explain, and guide. Final
application submission must remain under manual user control outside any
autonomous execution path.

Provider-call readiness is preflight/readback only. Phase 20A through Phase
20C performed no provider calls, no network calls, no database writes, no
persistence, no mutation, no execution, and no submission.

## Release lineage

- `phase20a-provider-call-readiness-experiment-v1`
- `phase20b-provider-call-readiness-api-readback-v1`
- `phase20c-provider-call-readiness-ui-readback-v1`
- `phase19-readonly-approval-workflow-release-v1`
- `phase18-safety-wrap-release-v1`

The permanent policy is defined in
`docs/no_auto_apply_safety_policy.md`. Future phases may improve assistance
and readback, but they may not introduce automatic application execution or
submission.
