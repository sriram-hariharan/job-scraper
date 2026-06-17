# Phase 6F Human-reviewed Influence Preview Readiness Audit

No runtime behavior changed in this phase.

No influence preview builder was added in this phase.

No UI, API, service, pipeline, storage, scoring, ranking, queue, approval, resume, execution request, execution launch request, application execution, or application submission behavior changed in this phase.

No live provider calls were added.

## Inspected Files

Exact inspected files for this readiness audit:

- `src/agents/shadow_sidecar_score_comparison.py`
- `src/agents/final_application_scoring.py`
- `src/pipeline/collector.py`
- `src/app/services.py`
- `src/app/api.py`
- `src/app/static/agentic_review.js`
- `src/agents/shadow_sidecar.py`
- `docs/phase5_shadow_sidecar_end_to_end_readiness_audit.md`
- `docs/phase6_shadow_score_comparison_ui_readiness_audit.md`
- `tests/test_shadow_sidecar_score_comparison_readonly.py`
- `tests/test_shadow_sidecar_score_comparison_service_helper_no_api_ui.py`
- `tests/test_shadow_sidecar_score_comparison_api_default_off_no_ui.py`
- `tests/test_shadow_sidecar_score_comparison_ui_default_off.py`
- `tests/test_phase6_shadow_score_comparison_ui_readiness_audit.py`
- `tests/test_portfolio_demo_readiness_wrap_checkpoint.py`

Protected pipeline runtime, API route, service, UI/static, scoring, ranking, queue, approval, execution, and storage schema files were inspected only. They were not modified for this audit.

## Current Implemented Phase 6A-6E Shadow Score Comparison Flow

Current implemented Phase 6A-6E shadow score comparison flow:

- Phase 6A added isolated score comparison helper: `src/agents/shadow_sidecar_score_comparison.py`.
- Phase 6B added read-only service helper: `shadow_sidecar_score_comparison_service_payload`.
- Phase 6C added default-off API route: `POST /api/shadow-sidecar/score-comparison`.
- Phase 6D added UI readiness audit: `docs/phase6_shadow_score_comparison_ui_readiness_audit.md`.
- Phase 6E added read-only UI panel: `renderShadowSidecarScoreComparisonSection`.

The score comparison flow compares deterministic final scoring context against shadow sidecar evidence. It remains read-only, default-off, operator-triggered, and advisory only.

Shadow score comparison remains advisory only.

## Current Safety Status

Current safety status:

- Live provider-backed automated agents remain zero.
- live provider-backed automated agents: 0
- Mutation-authorized agents remain zero.
- mutation-authorized agents: 0
- scoring/ranking mutation: 0
- queue/approval/resume/execution/submission mutation: 0
- live agents connected to production pipeline for automated mutation: 0

The existing Phase 6 comparison path is not allowed to mutate deterministic decisions, final scores, rankings, queues, approvals, resumes, execution requests, execution launch requests, applications, or submissions.

## Existing Boundaries

Existing boundaries that must remain intact before any influence preview work:

- Prefilter relevance remains separate.
- LLM evaluation remains separate.
- Final application scoring remains separate.
- Shadow score comparison remains advisory only.
- Influence preview remains separate from deterministic final application scoring.
- No LLM ranking override is allowed.
- No score override is allowed.
- No downstream queue or approval mutation is allowed.

The future influence preview may explain a possible human-reviewed effect, but it must not become the scoring formula, ranking logic, or queue handoff logic.

## Future Influence Preview Object

Proposed future influence preview object fields:

- `preview_status`
- `preview_type`
- `deterministic_score_context`
- `shadow_comparison_context`
- `proposed_influence_summary`
- `proposed_score_adjustment_preview`
- `proposed_ranking_effect_preview`
- `required_human_review`
- `approval_gate_required`
- `no_mutation_safety_metadata`

The object should be built from deep-copied deterministic score context and shadow comparison context. It should preview what a reviewer could consider, not apply that influence.

## Required Feature Flag And Kill Switch

Required future feature flag:

- `APPLYLENS_AGENTIC_PIPELINE_HUMAN_REVIEWED_INFLUENCE_PREVIEW_ENABLED`

The feature flag must default off.

The kill switch must block influence preview construction and any future influence request path:

- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH`

Kill switch behavior must win over all enablement flags. If the kill switch is on, the preview must return a safe blocked status and must not call providers, mutate state, or create downstream records.

## Required Preview Constraints

Required preview constraints:

- read-only
- advisory only
- no score mutation
- no ranking mutation
- no queue mutation
- no approval mutation
- no resume mutation
- no execution request mutation
- no execution launch request mutation
- no application execution/submission
- no application execution
- no application submission

Explicit human review is required before any influence.

Approval gate is required before any influence.

No future influence preview may be applied automatically. It must remain a preview until a later approval-gated request path exists and is explicitly reviewed.

## Observability Requirements

Required observability before future implementation:

- Preserve existing stage-level logging and metrics flow.
- Existing stage-level logging and metrics flow must be preserved.
- Existing retry, rate-limit, cache, deduplication, and ATS health checks must not be removed.
- Trace bundle context must remain available.
- Evidence pack context must remain available.
- Readiness status must remain visible.
- Health status must remain visible.
- Provider calls must not run in tests.
- Tests must use deterministic inputs or fake adapters only.

The future preview should report both deterministic score context and shadow comparison context, including any missing evidence or blockers, without changing pipeline outcomes.

## Proposed Next Implementation Sequence

Proposed next implementation sequence:

1. add isolated influence preview builder
2. add service helper
3. add default-off API readback
4. add UI preview panel
5. add approval-gated influence request
6. only later allow approved influence to affect downstream ranking/scoring
7. only much later guarded automation

Each step must preserve default-off behavior and no mutation unless a later phase explicitly introduces a human-approved, guarded mutation path.

## Explicit Non-goals

Explicit non-goals for Phase 6F:

- no runtime behavior in this audit
- no influence builder yet
- no UI/API/service changes
- no score/ranking mutation
- no approval-gated mutation yet
- no application execution/submission
- no provider calls
- no pipeline wiring
- no storage schema change
- no migration
- no queue mutation
- no approval mutation
- no resume overwrite

Phase 6F is a readiness audit only. It documents the safe path toward a future human-reviewed influence preview while preserving the current zero-mutation, advisory-only shadow score comparison boundary.
