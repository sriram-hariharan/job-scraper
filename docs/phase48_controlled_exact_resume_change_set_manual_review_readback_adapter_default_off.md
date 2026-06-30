# Phase 48A controlled exact resume change-set manual review readback adapter default-off

Phase 48A adds a controlled exact resume change-set manual review readback adapter. It adapts Phase 47 manual review packets into a deterministic UI/API readback payload for later surfaces.

This is a default-off, read-only adapter. It is not a provider call phase. It is not an LLM request phase. It is not a validation phase. It is not a normalization phase. It is not a manual review packet creation phase. It is not a UI route phase. It is not an API route phase. It prepares readback payloads for later UI/API manual review readback.

The adapter reads supplied manual review packets or a supplied Phase 47 review packet result. Explicit `manual_review_packets` take precedence over `review_packet_result`. It can read direct packet lists, nested Phase 47B results, flattened grouped packets, and nested grouped packets.

The adapter creates manual review readback items only. Each readback item preserves manual review and user acceptance requirements, exposes before/after text when policy permits, carries evidence and risk flags when policy permits, maps recommended operator actions to deterministic labels, and groups by change type and operator action when policy permits.

Safety boundaries:

- It does not call LLM.
- It does not call provider.
- It does not call network.
- It does not call tailoring runtime.
- It does not generate real tailoring output.
- It does not create new proposal text.
- It does not create manual review packets.
- It does not validate provider responses.
- It does not normalize provider responses.
- It does not produce a full resume.
- It does not overwrite resumes.
- It does not mutate resumes.
- It does not persist data.
- It does not write to database.
- It does not execute applications.
- It does not submit applications.
- It does not add UI routes.
- It does not add API routes.
- It does not perform UI readback.
- It does not perform API readback.
- It does not perform user acceptance.
- No auto-apply.
- No auto-submit.
- Manual user control remains required.
- Exact worthy changes must be manually accepted by the user.
- Existing UI/manual control remains the acceptance point.
- Resume overwrite is not needed.
- Application execution is not needed.

The readback payload is advisory only and proposal only. Its allowed user actions are non-mutating preview, inspect, and defer. Its blocked user actions include apply, overwrite_resume, mutate_resume, submit_application, auto_apply, and auto_submit.

Provider response validation, provider response normalization, manual review packet building, UI readback, API readback, user acceptance, resume mutation, and final scoring remain separate.

Markers:

- controlled exact resume change-set manual review readback adapter
- manual review readback adapter default-off
- ui api readback payload only
- manual review readback only
- read only
- advisory only
- proposal only
- exact worthy changes only
- manual review required
- requires manual user control
- missing packets block readback payload use
- invalid non-dict packets are counted and excluded
- max_readback_items truncates deterministically
- include_before_after_text policy controls before and after text exposure
- include_risk_flags policy controls risk flag exposure
- include_evidence policy controls evidence exposure
- include_action_labels policy controls action label exposure
- group_by_change_type policy controls type grouping
- group_by_operator_action policy controls operator action grouping
- sort_by_display_order policy controls deterministic display order
- review_risk maps to Review risk before accepting
- review_change maps to Review exact change
- reject_invalid maps to Reject invalid proposal
- inspect_unknown maps to Inspect unknown proposal
- unknown maps to Inspect proposal
- no callbacks
- no mutation commands
- no database write commands
- no network requests
- no submission commands

References:

- `phase47-controlled-exact-resume-change-set-manual-review-packet-builder-release-v1`
- `phase47b-controlled-exact-resume-change-set-manual-review-packet-builder-dry-run-command-default-off-v1`
- `phase47a-controlled-exact-resume-change-set-manual-review-packet-builder-default-off-v1`
- `phase46-controlled-exact-resume-change-set-provider-response-normalization-release-v1`
- `phase45-controlled-exact-resume-change-set-provider-response-validation-release-v1`
- `phase44-controlled-exact-resume-change-set-provider-call-boundary-release-v1`
- `phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1`
- `phase42-exact-resume-change-set-proposal-builder-release-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

## Phase 48A verifier marker alignment

- adapts manual review packets after phase 47
- prepares UI/API-readback-ready payloads
- does not modify UI files
- does not modify API/service files
- produces manual-review readback payload only
- UI/API readback wiring comes in a later phase
