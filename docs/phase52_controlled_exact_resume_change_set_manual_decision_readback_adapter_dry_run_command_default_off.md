# Phase 52B — controlled exact resume change-set manual decision readback adapter dry-run command, default-off

Phase 52B exposes a deterministic CLI dry-run wrapper for the Phase 52A manual decision readback adapter.

It is default-off. Without `--enable-manual-decision-readback` and `--allow-manual-decision-readback`, the command prints a structured blocked JSON result.

## Local JSON input only

The command accepts a Phase 51 manual decision packet or Phase 51 result from local JSON input only:

- `--manual-decision-packet`

The command calls Phase 52A only and preserves Phase 52A stage-level observability in the printed JSON.

## Readback only

Phase 52B produces readback only. It does not apply decisions to resumes and does not create artifacts.

Raw Phase 50 readback/manual review input, invalid JSON, missing packet input, and invalid or incomplete decision packets are surfaced safely through the structured result or clean command errors.

## Safety boundary

Phase 52B does not call a provider, does not call an LLM, and does not call network.

It performs no mutation, no resume overwrite, no persistence, no scoring, no artifact creation, no application execution, no application submission, no UI route, and no API route.

Provider execution, validation, normalization, manual review/readback, manual decision capture, readback, artifact creation, scoring, and application execution remain separate.

## Safety markers

- no provider call
- no llm
- no network
- no mutation
- no persistence
- no scoring
- no artifact creation
- no application execution
- readback only
