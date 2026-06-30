# Phase 59A approved-change plan guarded resume copy artifact wiring default-off

Phase 59A wires an explicit guarded planning workspace action that creates a new-copy resume artifact packet from an approved-change plan. It is default-off and requires both the manual artifact creation flag and the approved change plan ID or stable plan key.

The action consumes the existing Phase58 manual exact change acceptance approved-change plan readback. Only approved changes from that approved-change plan can enter the guarded resume copy artifact. Rejected, skipped, unaccepted, and unapproved proposal IDs are excluded.

The response/readback includes artifact creation enabled/requested flags, artifact created status, stable artifact key, artifact kind/output kind, source resume unchanged and source resume overwritten flags, approved change plan ID, applied approved change count, skipped/rejected counts, validation status, fallback status, and fallback reason/error class when present.

Deterministic fallback is used for default-off, missing approved change plan ID, missing approved-change plan input, mismatched plan IDs, or approved plans with no approved changes.

Safety boundaries:

- default-off
- guarded resume copy artifact wiring
- approved-change plan input
- planning workspace action
- deterministic fallback
- no live llm call
- no provider call
- no network call
- no source resume overwrite
- no source resume mutation
- no unapproved proposal application
- no application execution
- no application submission
- no auto-apply
- no automatic application behavior
- no scoring formula changes
- no scoring weight changes

Phase59A preserves Phase55 live JD LLM planning scan readback, Phase56 live tailoring suggestion readback, Phase57 exact resume change proposal readback, and Phase58 manual acceptance / approved-change plan readback.

