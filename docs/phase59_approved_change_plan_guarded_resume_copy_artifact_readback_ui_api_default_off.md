# Phase 59B approved-change plan guarded resume copy artifact readback UI/API default-off

Phase 59B hardens the existing Phase59A guarded new-copy resume artifact readback through the planning workspace API/UI surface. It is default-off and does not create artifacts unless the explicit Phase59A guarded manual action flag and approved change plan ID or stable plan key are supplied.

The readback exposes artifact creation enabled/requested flags, artifact created status, artifact ID or stable artifact key, artifact kind/output kind, source resume unchanged and source resume overwritten flags, approved change plan ID or stable plan key, applied approved change count, rejected/skipped change counts, validation status, fallback status, and fallback reason/error class when present.

The API readback and UI readback are passive surfaces. They display the guarded artifact state returned by the planning workspace action and do not create an artifact by themselves.

The guarded action creates a new-copy artifact/readback only. It uses approved-change plan input only and excludes unaccepted or unapproved proposal IDs.

Deterministic fallback is preserved for default-off, missing approved change plan ID, missing approved-change plan input, mismatched plan IDs, or invalid artifact requests.

Safety boundaries:

- default-off
- guarded resume copy artifact readback
- approved-change plan input
- planning workspace action
- api readback
- deterministic fallback
- no live llm call
- no provider call
- no source resume overwrite
- no source resume mutation
- no unapproved proposal application
- no application execution
- no application submission
- no auto-apply
- no automatic application behavior
- no scoring formula changes
- no scoring weight changes

Phase59B preserves Phase55 live JD LLM planning scan readback, Phase56 live tailoring suggestion readback, Phase57 exact resume change proposal readback, Phase58 manual acceptance / approved-change plan readback, and Phase59A guarded artifact behavior.

