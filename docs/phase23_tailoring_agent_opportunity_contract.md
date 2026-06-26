# Phase 23A Tailoring-Agent Opportunity Contract

Phase 23A builds on the Phase 22 core-agent evidence materialization release.
It introduces a pure, default-off tailoring-agent opportunity contract.

The tailoring agent is separate from final scoring. This phase only identifies
tailoring opportunities from caller-supplied evidence. It does not generate AI
tailoring.

## Opportunity boundary

The contract may identify opportunities from supplied missing requirements,
supplied core-agent evidence packet gaps, and supplied tailoring context. Its
records are read-only, advisory-only, manual-review only, and deterministic.

Future `Generate AI Tailoring` must be user-triggered. Generated tailoring
suggestions must remain preview/manual-review only unless the user accepts
edits.

Phase 23A authorizes:

- no silent resume rewrite
- no automatic resume overwrite
- no resume mutation
- no application submission
- no provider calls
- no network calls
- no database writes
- no persistence
- no mutation
- no execution
- no submission

The contract does not call scoring, prefilter, matching, tailoring, pipeline,
or LLM runtime functions. It creates no provider interaction and generates no
tailoring text.

## Permanent product boundary

The permanent rule remains:

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control remains required for final job application submission

Any future provider-backed tailoring generation requires a separate phase,
explicit default-off gates, preview-only output, and manual-review control.

## Release references

- `phase22-core-agent-evidence-materialization-release-v1`
- `phase22f-core-agent-evidence-materialization-release-checkpoint-v1`
- `phase22e-core-agent-evidence-materialization-ui-readback-v1`
- `phase22d-core-agent-evidence-materialization-api-readback-v1`
- `phase22c-core-agent-evidence-materialization-preview-v1`
- `phase22b-core-agent-automation-mutation-inventory-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

## Exact Phase 23A scope markers

- This phase only identifies tailoring opportunities.
- This phase does not generate AI tailoring.
