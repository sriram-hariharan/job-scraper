# Phase 20A Provider-Call Readiness Experiment

Phase 20A builds on the Phase 19 read-only approval workflow release. It adds
one standalone, deterministic provider-call readiness helper for
caller-supplied inputs.

This is not live provider invocation. The experiment is default-off,
read-only, shadow-only, and advisory-only. It performs no provider calls and
no network calls. It reads no environment configuration, secrets, files, or
database state and writes no files or database records.

The helper validates only:

- explicit enablement and the Phase 20A caller-supplied configuration flag
- caller-supplied kill-switch state
- a caller-supplied requested provider capability
- a caller-supplied request packet summary

Provider name and requested model are optional caller-supplied readback
metadata. A ready result means only that the supplied preflight metadata is
reviewable. It does not authorize or attempt a provider call.

Phase 20A does not mutate score, ranking, queue, resume, approval, decision,
audit, execution, submission, or application state. It adds no API, UI,
service, pipeline, or collector wiring.

## Release lineage

- `phase19-readonly-approval-workflow-release-v1`
- `phase19j-readonly-approval-workflow-release-checkpoint-v1`
- `phase19g-operator-decision-capture-readback-contract-v1`
- `phase18-safety-wrap-release-v1`

## Recommended next phase

The next phase should add a default-off provider-call API readback/preflight
endpoint. It must still perform no live provider invocation and authorize no
mutation.
