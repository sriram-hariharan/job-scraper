# Phase 51B — controlled exact resume change-set manual decision packet dry-run command, default-off

Phase 51B exposes a deterministic CLI dry-run wrapper for the Phase 51A manual decision packet helper.

It is default-off. Without `--enable-manual-decision-packet` and `--allow-manual-decision-packet`, the command prints a structured blocked JSON result.

## Local JSON inputs only

The command accepts Phase 50 readback/manual review output from local JSON input only:

- `--readback-result`
- `--manual-review-output`

It accepts explicit operator decisions from local JSON input only:

- `--manual-decisions`

The command calls Phase 51A only and preserves Phase 51A stage-level observability in the printed JSON.

## Decision packet only

Phase 51B produces a manual decision packet only. It does not apply decisions to resumes and does not create artifacts.

Invalid decision values, unknown proposal/change identifiers, missing readback/manual review input, and missing decision input are surfaced safely through the Phase 51A structured result.

## Safety boundary

Phase 51B does not call a provider, does not call an LLM, and does not call network.

It performs no mutation, no resume overwrite, no persistence, no scoring, no artifact creation, no application execution, no application submission, no UI route, and no API route.

Provider execution, validation, normalization, manual review/readback, manual decision capture, artifact creation, scoring, and application execution remain separate.

## Safety markers

- no provider call
- no llm
- no network
- no mutation
- no persistence
- no scoring
- no artifact creation
- no application execution
- decision packet only

