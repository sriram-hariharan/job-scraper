# Phase 50B — controlled exact resume change-set real provider response handoff pipeline dry-run command, default-off

Phase 50B exposes a deterministic CLI dry-run command for the Phase 50A provider response handoff pipeline.

The command reads local JSON files only. It does not call a provider, call an LLM, call network, mutate resumes, persist data, score applications, execute application workflow, create UI routes, create API routes, accept user decisions, or create resume artifacts.

## Default-off behavior

The command is default-off. The Phase 50A pipeline is only enabled when both flags are supplied:

- `--enable-handoff`
- `--allow-real-provider-response-handoff`

Without those flags, the command still prints structured JSON and returns success for the expected safe blocked result.

## Local JSON inputs

The command accepts:

- `--provider-response` for a local JSON provider response payload.
- `--runtime-result` for a local JSON Phase 49 runtime result payload.
- `--original-request-packet` for the local JSON Phase 43 request packet.
- Optional `--original-change-proposals`, `--review-context`, and `--readback-context` local JSON files.

Invalid JSON or unreadable files are command/input errors and return non-zero.

## Handoff sequence

Phase 50B calls Phase 50A only. Phase 50A preserves the exact sequence:

`validation -> normalization -> manual review -> readback`

The dry-run output includes the Phase 50A pipeline result, stage summaries, final readback payload when all stages pass, and false safety flags for provider call, LLM call, network call, mutation, persistence, scoring, artifact creation, application execution, UI/API routes, and user decision acceptance.
