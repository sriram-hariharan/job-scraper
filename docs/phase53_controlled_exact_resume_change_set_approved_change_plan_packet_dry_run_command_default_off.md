# Phase 53B — controlled exact resume change-set approved change plan packet dry-run command, default-off

Phase 53B exposes a deterministic local dry-run command for the Phase 53A approved-change plan packet helper.

The command is default-off. Without `--enable-approved-change-plan-packet` and `--allow-approved-change-plan-packet`, it returns structured blocked JSON and does not produce an approved-change plan packet.

## Local input only

The command accepts Phase 52 manual decision readback output from a local JSON file through `--manual-decision-readback`.

It calls Phase 53A only and preserves Phase 53A stage observability in the dry-run JSON output. Raw Phase 51 manual decision packets, raw Phase 50 readback/manual review input, missing input, invalid JSON, and incomplete readback are surfaced safely.

## Plan packet only

The dry run produces an approved-change plan packet only when explicitly enabled and allowed and when the Phase 52 readback input is valid.

The command does not apply decisions to resumes and does not create resume artifacts. The plan packet remains a review/planning artifact for later steps.

## Safety boundary

Phase 53B does not call a provider, does not call an LLM, and does not call network.

It performs no mutation, no resume overwrite, no persistence, no scoring, no artifact creation, no application execution, no application submission, no UI route, and no API route.

Provider execution, validation, normalization, manual review/readback, manual decision capture, readback, approved-change planning, artifact creation, scoring, and application execution remain separate.

## Safety markers

- no provider call
- no llm
- no network
- no mutation
- no persistence
- no scoring
- no artifact creation
- no application execution
- plan packet only

