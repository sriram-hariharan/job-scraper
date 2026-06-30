# Phase 60B guarded artifact verification readback UI/API, default-off

Phase 60B hardens the existing Phase 60A guarded artifact verification readback through the planning workspace API/UI surface.

This phase is readback only. It reuses the Phase 60A verification wiring and keeps verification default-off unless the explicit manual verification flag/path and an existing artifact id or stable artifact key are provided.

The hardened API/UI readback clearly exposes:

- artifact verification enabled/requested/performed/passed
- artifact id or stable artifact key
- approved-change plan id or stable plan key
- artifact readable
- source resume unchanged / source resume overwritten
- applied approved change count
- mismatch count
- validation status
- deterministic fallback metadata, including fallback reason and error class
- Phase 60B readback hardening metadata

Safety boundaries:

- default-off
- guarded artifact verification readback only
- artifact readback verification only
- planning workspace action only
- api readback
- ui readback
- no live llm call
- no provider call
- no network call
- no artifact creation by verification
- no source resume overwrite
- no source resume mutation
- no unaccepted or unapproved proposal application
- no application execution
- no application submission
- no auto-apply
- no scoring formula or scoring weight changes

Phase 60B preserves Phase 58 approved-change plan readback, Phase 59 guarded artifact readback, and Phase 60A focused verification behavior.
