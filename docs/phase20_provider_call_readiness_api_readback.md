# Phase 20B Provider-Call Readiness API Readback

Phase 20B builds on Phase 20A by adding one default-off, read-only API
endpoint:

- `POST /api/provider-call-readiness-readback`

The endpoint accepts caller-supplied JSON, passes the supported fields to the
Phase 20A helper, and returns that helper payload directly. It remains
preflight/readback only.

This is not live provider invocation. Phase 20B performs no provider SDK call,
provider call, or network call. It reads or writes no database or file state,
persists no approval, decision, or audit record, and mutates no score, ranking,
queue, resume, application, execution, or submission state.

The endpoint remains default-off unless the caller explicitly sets
`enabled=true` and supplies the Phase 20A configuration flag. Caller-supplied
kill-switch configuration remains authoritative.

## Permanent product rule

ApplyLens has no auto-apply feature and no auto-submit feature. It permits no autonomous application execution and no automatic job application submission. This is a permanent product boundary for this and future phases.

## Release lineage

- `phase20a-provider-call-readiness-experiment-v1`
- `phase19-readonly-approval-workflow-release-v1`
- `phase18-safety-wrap-release-v1`

## Recommended next phase

The next phase should add a default-off UI readback panel for provider-call
readiness. It must still perform no live provider call and authorize no
mutation.
