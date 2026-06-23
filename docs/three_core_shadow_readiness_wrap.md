# Three-Core Shadow Readiness Wrap

## Checkpoint scope

This Phase 17K checkpoint is docs/tests only. It summarizes the Phase 17A
through Phase 17J three-core shadow automation already present in ApplyLens AI;
it does not add or authorize new runtime behavior.

The completed surface remains:

- default-off
- read-only
- shadow-only
- advisory-only

## Ordered three-core agents

The near-term three-core sequence is:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

These responsibilities remain separate: prefilter relevance does not become JD
intelligence, JD intelligence does not become final scoring, and the shadow
path does not mutate final scoring or ranking.

## Phase 17 inventory

| Phase | Pushed tag | Purpose |
| --- | --- | --- |
| 17A | `phase17a-three-core-agent-shadow-pipeline-hook-v1` | Added the default-off three-core shadow pipeline hook contract. |
| 17B | `phase17b-three-core-agent-shadow-sidecar-bridge-v1` | Bridged the three-core shadow hook into the existing shadow sidecar boundary. |
| 17C | `phase17c-three-core-agent-collector-shadow-wiring-v1` | Added collector wiring guarded by default-off shadow flags. |
| 17D | `phase17d-three-core-agent-collector-connection-plan-v1` | Connected the collector to the explicit three-core shadow connection plan. |
| 17E | `phase17e-three-core-agent-shadow-callable-adapters-v1` | Added callable adapters for the three ordered core agents. |
| 17F | `phase17f-three-core-agent-collector-callable-wiring-v1` | Supplied the callable adapters to the guarded collector shadow path. |
| 17G | `phase17g-three-core-agent-shadow-runtime-readback-v1` | Added deterministic read-only runtime acceptance readback. |
| 17H | `phase17h-three-core-agent-shadow-operator-canary-v1` | Added the default-off operator canary over an injected shadow payload provider. |
| 17I | `phase17i-three-core-agent-shadow-api-ui-readback-v1` | Added protected service, API, and passive UI readback surfaces. |
| 17J | `phase17j-three-core-shadow-local-fixture-ui-visibility-v1` | Added an explicit default-off local UI fixture for panel visibility. |

## Known operator surfaces and gates

- Read-only API endpoint:
  `/api/three-core-shadow-operator-canary-readback`
- Local UI fixture query flag:
  `?three_core_canary_fixture=1`
- Three-core collector flag:
  `APPLYLENS_AGENTIC_PIPELINE_THREE_CORE_SHADOW_PIPELINE_HOOK_ENABLED`
- Existing global shadow sidecar flag:
  `APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED`

The local fixture flag only supplies deterministic browser-side display data
when no real canary readback result exists. It does not call the API, collector,
pipeline, provider runtime, database, filesystem, execution, or submission
paths, and it does not overwrite a real payload.

## Safety matrix

| Capability or side effect | Phase 17K readiness state |
| --- | --- |
| Mutation authorization | Not authorized |
| Final scoring mutation | Not authorized |
| Ranking mutation | Not authorized |
| Queue mutation | Not authorized |
| Resume mutation | Not authorized |
| Provider SDK call | Not used |
| Network call | Not used |
| Database read/write | Not used |
| File IO | Not used |
| Application execution | Not authorized and not performed |
| Application submission | Not authorized and not performed |

This wrap does not grant mutation authority. It does not change the default-off
collector gates, call providers, read secrets, create network traffic, read or
write the database, perform runtime file IO, or change application state.

## Manual verification

1. Run the full tests:
   `PYTHONPATH="$PWD" python -m pytest tests -q`
2. Run the app normally using the repository's local setup.
3. Open the agentic review page normally and confirm its behavior is unchanged.
4. Open the same page with `?three_core_canary_fixture=1`.
5. Confirm the **Three-Core Shadow Operator Canary** panel is visible only when
   the fixture flag is present or a real
   `three_core_shadow_operator_canary_readback_result` payload exists.
6. Confirm the panel shows the completed canary/readback state, the three
   ordered agents, shadow result count `3`, and read-only safety metadata.
7. Confirm no apply, submit, execute, or approval control appears in the
   three-core fixture/readback panel.

## Not yet authorized

- Live provider execution is not authorized by this wrap.
- Final scoring mutation is not authorized.
- Ranking mutation is not authorized.
- Queue mutation is not authorized.
- Resume mutation is not authorized.
- Application execution is not authorized.
- Application submission is not authorized.

Any future live-provider or mutation phase requires a separate protected plan,
explicit review, new safety tests, and independently approved runtime scope.

## Next safe decision options

1. Keep the completed Phase 17 surface shadow-only.
2. Promote these readiness docs to the main release.
3. Design a separate protected approval plan before any live provider or
   mutation work.

