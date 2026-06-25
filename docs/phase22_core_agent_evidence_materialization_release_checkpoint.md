# Phase 22F Core-Agent Evidence Materialization Release Checkpoint

Phase 22F closes the Phase 22B through Phase 22E core-agent evidence
materialization sequence. This checkpoint is documentation and tests only and
changes no runtime behavior.

## Phase 22 release summary

### Phase 22B: automation and mutation inventory

Phase 22B created the core-agent automation and mutation capability inventory.
It documented the existing deterministic foundations already present in the
application. Deterministic prefilter, scoring, shortlist, and tailoring packet
foundations remain intact. Future live-provider agent automation was deferred
behind later provider-readiness and safety gates.

### Phase 22C: evidence materialization preview

Phase 22C created the default-off core-agent evidence materialization preview
helper. The helper materializes only caller-supplied dictionaries. It is pure,
deterministic, read-only, advisory-only, and manual-review only.

The helper performs no provider calls, no network calls, no database reads or
writes, and no persistence. It does not call scoring runtime, prefilter
runtime, tailoring runtime, pipeline runtime, execution, or submission.

### Phase 22D: API readback

Phase 22D added API readback for the Phase 22C helper:

- endpoint: `/api/core-agent-evidence-materialization-preview`
- method: `POST`

The API accepts caller JSON and returns the helper payload directly. It does
not create approvals, persist decisions, persist audits, generate AI
tailoring, execute, submit, or mutate state.

### Phase 22E: UI readback

Phase 22E added a passive UI readback surface. The UI is default-off,
read-only, advisory-only, and manual-review only. It can surface the
manual-review evidence packet fields and tailoring opportunity evidence.

The UI adds no application buttons, submit controls, approval controls,
provider controls, execution controls, or autonomous controls.
`Generate AI Tailoring` remains only a later user-triggered action.

## Core-agent sequence

The ordered core-agent sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

These agents remain advisory evidence boundaries. They are not durable
mutation or application-execution authorities.

## Tailoring boundary

The tailoring agent remains separate from final scoring. Tailoring opportunity
detection may be represented as evidence, but AI tailoring generation is not
implemented in Phase 22.

Any future `Generate AI Tailoring` action must be user-triggered,
default-off/gated, preview-only, and manual-review controlled. Generated
tailoring suggestions must not silently rewrite, overwrite, apply, or submit.

## Safe automation meaning after Phase 22

Within the existing deterministic and read-only evidence boundaries, safe
automation can:

- automatically analyze jobs
- automatically prefilter relevance
- automatically extract JD signals
- automatically score fit
- automatically prepare review evidence
- automatically surface review panels
- automatically explain why a job is worth reviewing
- automatically identify tailoring opportunities
- do not automatically apply
- do not automatically submit

This is read-only/advisory/manual-review evidence, not autonomous application
execution.

## Current release boundary

- Phase 22 is not live provider automation.
- Phase 22 is not live provider interaction between agents.
- Phase 22 is not durable mutation.
- Phase 22 is not live tailoring generation.
- Phase 22 is not auto-apply or auto-submit.

Live providers and inter-agent provider-backed automation are deferred to
later phases with separate safety gates.

## Safety checkpoint

Phase 22 evidence materialization remains:

- default-off
- read-only
- advisory-only
- manual-review only
- read-only/advisory/manual-review evidence
- no provider calls
- no network calls
- no database writes
- no persistence
- no mutation
- no scoring mutation
- no ranking mutation
- no queue mutation
- no resume mutation
- no application mutation
- no approval mutation
- no decision mutation
- no audit mutation
- no execution
- no submission
- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control over final job application submission

The permanent product rule is unchanged: final job application submission
must remain under manual user control.

## Release tags

- `phase22a-manual-review-ux-hardening-v1`
- `phase22b-core-agent-automation-mutation-inventory-v1`
- `phase22c-core-agent-evidence-materialization-preview-v1`
- `phase22d-core-agent-evidence-materialization-api-readback-v1`
- `phase22e-core-agent-evidence-materialization-ui-readback-v1`

## Recommended next phase

Phase 23A should introduce a tailoring-agent opportunity contract. It should
remain default-off, read-only, advisory-only, and manual-review only. It should
identify tailoring opportunities from existing evidence without generating AI
tailoring.

Phase 23A should prepare for a later user-triggered
`Generate AI Tailoring` button. Any provider-backed tailoring generation must
be implemented in a separate phase with its own safety gates.
