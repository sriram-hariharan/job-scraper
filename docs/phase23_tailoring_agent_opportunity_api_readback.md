# Phase 23B Tailoring-Agent Opportunity API Readback

Phase 23B builds on Phase 23A and adds default-off API readback only.

The endpoint is `POST /api/tailoring-agent-opportunity-contract`. It accepts
caller JSON and returns the Phase 23A helper payload directly. Enablement is
accepted only from the caller's `enabled` field; absent, false, or non-boolean
values keep the contract off.

This API only identifies tailoring opportunities from caller-supplied
evidence. The tailoring agent remains separate from final scoring, and this
API does not generate AI tailoring. `Generate AI Tailoring` is only a later
user-triggered action.

## Readback boundary

Phase 23B makes:

- no UI changes
- no services changes
- no agent helper changes
- no pipeline changes
- no matching changes
- no tailoring runtime changes

The route makes no provider calls, no network calls, no database writes, no
persistence, no mutation, no execution, and no submission. It creates no
approval records, persists no decisions or audits, and performs no silent
resume rewrite or automatic resume overwrite.

## Permanent product boundary

The permanent product rules remain:

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control remains required for final job application submission

## Release references

- `phase23a-tailoring-agent-opportunity-contract-v1`
- `phase22-core-agent-evidence-materialization-release-v1`
- `phase22f-core-agent-evidence-materialization-release-checkpoint-v1`
- `phase22e-core-agent-evidence-materialization-ui-readback-v1`
- `phase22d-core-agent-evidence-materialization-api-readback-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

## Exact Phase 23B safety markers

- No silent resume rewrite.
- No automatic resume overwrite.
- No persistence.
