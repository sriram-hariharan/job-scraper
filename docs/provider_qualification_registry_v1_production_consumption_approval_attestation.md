# V1 provider qualification registry production-consumption approval attestation

## Approval record

- Approval date: `2026-09-14`
- Release owner: repository release owner
- Reviewed implementation baseline: `ccbd08b1ee9b0d1e0de017b0b617e7bd0fc5eb67`
- Packaged artifact: `src/evaluation/production_provider_qualification_registry_v1.json`
- Raw and canonical SHA-256: `6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f`
- Source policy pin: `6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f`
- Schema: `controlled-provider-qualification-registry-artifact-v1`
- Contract: `controlled-provider-qualification-registry-v1`
- Scope: `evaluation_qualification_state_only`

The approved immutable snapshot contains 12 workloads and 44 cells: 16
qualified, 22 rejected, and 6 stale.

## Release-owner approval

> I approve production packaging and consumption of the immutable V1 provider qualification registry with SHA-256 `6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f`, schema `controlled-provider-qualification-registry-artifact-v1`, contract `controlled-provider-qualification-registry-v1`, scope `evaluation_qualification_state_only`, and exactly 12 workloads and 44 cells, based on its complete retained evidence and required-review chains; this approval changes no cell or provider/model qualification, authorizes consumption of the existing pinned evaluation snapshot only, preserves the separately tracked Skill Extraction and Job Fit V2 authorities, and does not authorize new evaluation generation, provider calls, requalification, or routing changes.

## Evidence and review closure

- All 44 cell evidence references resolved during the approval audit.
- All 43 unique evidence payloads existed and matched their exact raw hashes.
- All 14 referenced review payloads existed and matched their exact raw hashes.
- No qualified human-review-required cell lacked a review.
- No cell identity, qualification binding, or policy-pin inconsistency remained.

The evidence and review payloads remain retained evaluation outputs. This
attestation does not claim that ignored payloads under `outputs/` are newly
tracked or packaged.

## Exact V1 registry bindings

- Benchmark contract: `817e3620b9ceefce15cf6991617116c1d1ee0a585e4f1dd17a60f614f473fd25`
- Controlled plan: `f2dcf5345442009915819432a9c1fc9342de40561eb6824c1518dcd31e99d3bf`
- Model catalog snapshot: `024cc680a79c0f3b1f108511ca208db0a46b4a9a61abdf9f4d8c360062b03f90`

## Historical authority references

- `73de801e2b96507ca2fcaa434faff4a2e51ce12b` — provider qualification registry foundation.
- `a7baf013917dbda88dfc10b7a21642f197088cf4` — frozen, read-only V1 recommendation policy.
- `340be82cc54ca0ac41e2cf624516a0a6fd75cd10` — exact approved V1 policy pin and reviewed Tailoring generation activation.
- `89855ea92b16a7b1a9315cfcd2f598cf6e5dc88d` — Grounded RAG owner-routing activation.
- `ad172d1e886e93d4b28464499cd33af7e5e4aa2a` — Manual scan owner-routing activation, preserving V1 fail-closed state.
- `f7af8981cbe770c78b7facf071974352372e613a`, `42cb44cdc89fd7b6ff2c065695e83046ae5c8f5b`, and `122b168024ec6291c0e283c4311737990a594338` — Manual provider preview qualification, default-route, and live-boundary chain.

The separately tracked Skill Extraction V2 authority remains
`bcf1286e52c6a35793595ba1eddbcbb39c145522`, activated by
`c3d419c5368d41fcf0ff817ccd69f8b76e575ad2`. The separately tracked Job Fit
V2 authority remains `f7e4b52f270d95eaf642e4af6322d89076d2584f`, with exact
qualification and activation in `1d2f148f0ffb2c7f9639c1d13f2d6a8cb3c3f095`.

## Authority boundary

Packaging preserves every V1 cell, timestamp, status, binding, task
fingerprint, evidence hash, and review hash exactly. It does not newly qualify
or remove any provider/model and does not change any winner. It changes only
production availability of the already-pinned V1 authority.

Evaluation generation remains separate and continues to own
`outputs/provider_benchmark/provider-qualification-registry.json` and the rest
of `outputs/` as runtime/evaluation state. Production routing consumes only the
immutable packaged snapshot under `src/evaluation/`. The persistent production
`/app/outputs` volume cannot replace the packaged authority.

Skill Extraction and Job Fit V2 overlays continue to supersede their
historical V1 base authority. This attestation authorizes no provider calls,
qualification reruns, requalification, or additional routing changes.
