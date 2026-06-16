# Phase 5A Shadow Agentic Pipeline Sidecar Readiness Audit

This checkpoint is documentation/test only.

No runtime behavior change is introduced.

No production pipeline behavior is changed.

No scheduler behavior is changed.

No storage schema is changed.

No migration is added.

No API, UI, service, agent, storage, scoring, ranking, queue, approval, execution, launch, application, or submission runtime file is changed.

## Current Live-Agent Count

| Count | Value |
|---|---:|
| live LLM-capable agents coded | 3 |
| live agents available in manual/shadow workflow | 3 |
| live agents connected to production pipeline | 0 |
| live agents allowed to automate mutations | 0 |

The three coded live LLM-capable agents are:

- JD Intelligence Agent
- Tailoring Suggestion Agent
- Critic / Guardrail Agent

These agents currently exist in manual/shadow workflow only. They are not connected to the production pipeline, and they are not allowed to automate mutation of scoring, ranking, queue state, approval state, resume content, execution requests, launch requests, applications, or submissions.

## Workflow Definitions

Manual/shadow workflow means an operator-triggered or service-callable diagnostic path that can build dry-run or shadow payloads without changing production decisions. Manual/shadow workflow outputs are advisory, read-only, and safe to discard.

Production pipeline shadow sidecar means a future read-only companion stage attached alongside the existing deterministic production pipeline after existing deterministic job filtering/evaluation signals are available. A sidecar may observe inputs, call a default-off shadow agent when explicitly enabled, and emit trace/evidence records, but it must not change the deterministic pipeline result.

Automated workflow means any production path that can run without a human manually triggering the specific action. Automated workflow includes scheduler-triggered work, background tasks, automatic queue handoff, approval mutation, execution request creation, launch request creation, application execution, or application submission. Phase 5A does not enable automated workflow.

## Recommended First Pipeline Connection

The safest first real-pipeline connection is a read-only shadow sidecar after existing deterministic job filtering/evaluation signals are available.

Required boundaries for that first connection:

- First integration is read-only shadow sidecar.
- Trace/evidence storage only.
- No scoring override.
- No ranking override.
- No scoring/ranking override.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No application execution.
- No application submission.
- No execution request mutation.
- No launch request mutation.
- No automatic pipeline wiring in this phase.

The sidecar must emit observability only. It must not replace relevance prefiltering, deterministic deduplication, deterministic ranking, final application scoring, approval handling, queue handling, execution request handling, launch request handling, application execution, or application submission.

## Candidate Sidecar Stages

1. JD Intelligence shadow extraction
2. Tailoring Suggestion shadow advice
3. Critic/Guardrail shadow risk review

Each candidate stage should remain advisory. If any stage fails validation or its feature flag is disabled, the sidecar must use deterministic fallback and preserve the existing production pipeline result.

## Required Safety Gates Before Runtime Wiring

Before any future runtime wiring, all of these gates must be satisfied:

- Feature flag default-off requirement.
- Provider-backed sidecar runs remain disabled unless explicitly enabled.
- Trace bundle emitted.
- Evidence pack emitted.
- Status/health/readiness checks emitted.
- Trace/evidence/readiness observability requirements documented and tested.
- Deterministic fallback for disabled flags, missing adapters, invalid provider output, and provider exceptions.
- Provider calls must not run in tests.
- No provider call in tests.
- No mutation.
- No scoring mutation.
- No ranking mutation.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No execution mutation.
- No submission mutation.
- No application execution.
- No application submission.
- Batch-level observability.
- Kill switch.

These gates are prerequisites, not implementation in this phase.

## Explicit Non-Goals

- No auto-apply.
- No auto-submit.
- No LLM ranking override.
- No resume overwrite.
- No queue mutation.
- No approval mutation.
- No execution launch.
- No application execution.
- No application submission.
- No production pipeline connection in this phase.
- No runtime behavior change.

## Proposed Phase 5 Implementation Sequence

1. Documentation/readiness audit.
2. Shadow sidecar config contract.
3. Sidecar trace schema contract.
4. Pipeline-sidecar adapter default-off.
5. Local deterministic test doubles only.
6. Provider-backed shadow run default-off.
7. Dashboard/readback.
8. Human-approved influence path.
9. Guarded automation only after validation.

## Readiness Decision

Phase 5A is not a runtime implementation phase.

The current readiness decision is:

- Keep live agents in manual/shadow workflow.
- Keep live agents connected to production pipeline at 0.
- Keep live agents allowed to automate mutations at 0.
- Document the sidecar boundary before adding any adapter.
- Add tests that prove the readiness document preserves no runtime behavior change.

