# Phase 23C Tailoring-Agent Opportunity UI Readback

Phase 23C builds on Phase 23B and adds a UI readback surface only. The panel is
default-off, read-only, advisory-only, and manual-review only.

The panel appears only when an existing page/readback payload supplies a
tailoring-agent opportunity result, when the deterministic
`tailoring_agent_opportunity_fixture=1` fixture is explicit, or when the
optional `tailoring_agent_opportunity_api_fetch=1` gate is explicit.

There are no backend behavior changes, no API changes, no services changes, no
agent helper changes, no pipeline changes, no matching changes, and no
tailoring runtime changes.

## Passive readback boundary

This UI only identifies tailoring opportunities. The tailoring agent remains
separate from final scoring, and this UI does not generate AI tailoring.
`Generate AI Tailoring` is only a later user-triggered action; this phase adds
no button or control for it.

Generated tailoring suggestions remain preview/manual-review only unless the
user accepts edits. The panel records no silent resume rewrite, no automatic
resume overwrite, no resume mutation, and no application mutation.

The UI makes no provider calls and no network calls except the optional,
explicitly gated POST to `/api/tailoring-agent-opportunity-contract`. It makes
no database writes, no persistence, no mutation, no execution, and no
submission.

## Permanent product boundary

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control remains required for final job application submission

## Release references

- `phase23b-tailoring-agent-opportunity-api-readback-v1`
- `phase23a-tailoring-agent-opportunity-contract-v1`
- `phase22-core-agent-evidence-materialization-release-v1`
- `phase22f-core-agent-evidence-materialization-release-checkpoint-v1`
- `phase22e-core-agent-evidence-materialization-ui-readback-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

## Exact Phase 23C safety markers

- UI readback only.
- No agent helper changes.
- No tailoring runtime changes.
- Tailoring agent remains separate from final scoring.
- No automatic resume overwrite.
- No submission.
