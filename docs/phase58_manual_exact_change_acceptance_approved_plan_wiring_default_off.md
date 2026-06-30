# Phase 58A manual exact change acceptance approved plan wiring default-off

Phase 58A wires manual exact change acceptance into the real planning workspace action path. It is default-off and only runs when the planning workspace request explicitly enables manual exact change acceptance and supplies accepted exact resume change proposal IDs.

This phase reuses the existing manual decision and approved-change plan packet logic:

1. Phase51 manual decision packet
2. Phase52 manual decision readback
3. Phase53 approved-change plan packet

Only explicitly user-accepted proposal IDs can enter the approved-change plan packet. Unaccepted proposals are represented as rejected/skipped and are not included in approved changes.

The response/readback includes manual acceptance enabled/performed flags, accepted proposal count and IDs, skipped/rejected counts, approved-change plan creation status, stable plan key, validation status, fallback status, and fallback reason/error class when present.

Deterministic fallback is used for default-off, missing accepted proposal IDs, missing Phase57 proposal readback, or invalid/unknown proposal IDs.

Safety boundaries:

- default-off
- manual exact change acceptance only
- approved-change plan wiring only
- planning workspace action
- no live llm call
- no provider call
- no network call
- no resume mutation
- no resume overwrite
- no resume artifact creation
- no suggestion application
- no application execution
- no application submission
- no auto-apply
- no auto-submit
- no scoring formula changes
- no scoring weight changes

Phase58A preserves Phase55 live JD LLM planning scan readback, Phase56 live tailoring suggestion readback, and Phase57 exact resume change proposal readback.

## Phase 58A required markers

- default-off
- manual exact change acceptance
- approved-change plan wiring
- planning workspace action
- deterministic fallback
- no live llm call
- no resume mutation
- no artifact creation
- no application execution
- no auto-apply

