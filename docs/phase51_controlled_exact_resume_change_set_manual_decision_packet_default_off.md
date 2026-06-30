# Phase 51A — controlled exact resume change-set manual decision packet, default-off

Phase 51A creates a deterministic manual decision packet from Phase 50 readback/manual review output and explicit operator decisions.

It is default-off and returns a structured blocked result unless explicitly enabled with `enabled=True` and `decision_policy.allow_manual_decision_packet=True`.

## Decision packet only

The helper accepts explicit decisions using these values:

- `approve`
- `reject`
- `needs_revision`

Every decision must reference an existing proposal/change identifier from the Phase 50 readback or manual review output. Unknown identifiers, missing decisions, invalid decision values, missing readback/manual review input, and duplicate decisions block safely.

## Safety boundary

Phase 51A produces a manual decision packet only. It does not apply decisions to resumes and does not create artifacts.

It performs no provider call, no llm call, no network call, no mutation, no resume overwrite, no persistence, no scoring, no artifact creation, no application execution, no application submission, no UI route, and no API route.

Provider execution, validation, normalization, manual review/readback, manual decision capture, artifact creation, scoring, and application execution remain separate.
