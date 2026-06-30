# Phase 58B manual exact change acceptance approved plan readback UI/API default-off

Phase 58B hardens the existing Phase 58A planning workspace readback for manual exact change acceptance. It is default-off and does not create an approved-change plan unless the explicit Phase 58A manual acceptance flag and accepted proposal IDs are supplied through the planning workspace action.

The API readback and passive UI readback expose:

- manual acceptance enabled and performed flags
- accepted proposal count and accepted proposal IDs or stable accepted proposal keys
- rejected and skipped proposal counts
- approved-change plan created status
- approved-change plan ID or stable plan key
- validation status
- fallback status, fallback reason, and fallback error class

The readback preserves the Phase55 live JD LLM planning scan readback, Phase56 live tailoring suggestion readback, and Phase57 exact resume change proposal readback. UI rendering uses existing response data and does not create plans by itself.

Deterministic fallback is preserved for default-off requests, missing accepted proposal IDs, missing Phase57 proposal readback, and invalid accepted proposal IDs.

Safety boundaries:

- default-off
- manual exact change acceptance readback
- approved-change plan readback
- planning workspace action
- api readback
- deterministic fallback
- no live llm call
- no provider call
- no resume mutation
- no resume overwrite
- no resume artifact creation
- no suggestion application
- no application execution
- no application submission
- no auto-apply
- no automatic application behavior
- no scoring formula changes
- no scoring weight changes

Phase 58B is readback hardening only; it does not apply suggestions to a resume, create resume artifacts, execute applications, submit applications, or alter scoring.

## Phase 58B required markers

- default-off
- manual exact change acceptance readback
- approved-change plan readback
- planning workspace action
- api readback
- deterministic fallback
- no live llm call
- no resume mutation
- no artifact creation
- no application execution
- no auto-apply

