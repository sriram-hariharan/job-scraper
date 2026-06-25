# Core-Agent Automation and Mutation Capability Inventory

This inventory records the automation foundations that already exist in
ApplyLens AI and the boundary for evolving them into agent-backed automation.
It is documentation only: it adds no runtime behavior, provider call,
pipeline stage, persistence, mutation, execution, or submission path.

## Existing deterministic foundations

The current application already provides:

- deterministic job discovery/filtering through the collection pipeline and
  normalized job corpus;
- deterministic role/title/location/freshness filtering in
  `src/pipeline/job_filter.py`;
- deterministic resume/job prefiltering in `src/matching/prefilter.py`;
- deterministic JD/resume evidence extraction through the existing job and
  resume evidence builders consumed by matching and planning;
- deterministic final resume-job scoring in `src/matching/scorer.py`;
- deterministic best resume variant selection in
  `batch_select_best_resume_variant.py`;
- deterministic shortlist/action classification in
  `application_shortlist_from_batch_selector.py`;
- deterministic review evidence generation through selector, shortlist, and
  planning outputs produced by `run_application_planning.py`;
- deterministic tailoring packet generation through planning packets and
  `generate_tailoring_suggestions.py`;
- optional LLM fallback/adjudication in
  `batch_select_best_resume_variant.py` where explicitly configured; and
- optional LLM tailoring in `generate_tailoring_suggestions.py` and
  `src/tailoring/llm.py` where explicitly requested.

These foundations are implemented by existing files, not by a newly invented
agent pipeline:

- `src/pipeline/job_filter.py`
- `src/matching/prefilter.py`
- `src/matching/scorer.py`
- `batch_select_best_resume_variant.py`
- `application_shortlist_from_batch_selector.py`
- `run_application_planning.py`
- `generate_tailoring_suggestions.py`
- `src/tailoring/llm.py`

## Core-agent sequence and ownership

The staged core-agent sequence is:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

`relevance_prefilter` should own early relevance gating by wrapping and
materializing the existing deterministic prefilter evidence.
`jd_intelligence` should own JD signal extraction and evidence interpretation,
without becoming the final scoring or mutation authority.
`final_application_scoring` should own final advisory score synthesis by
materializing existing deterministic score evidence for manual review.

Prefilter relevance, JD intelligence, final application scoring, and
tailoring suggestions must stay separate. Final application scoring may
advise manual review, but must not directly mutate queue, ranking, or
application state. Relevance prefilter may reduce review load, but must not
submit or execute applications. JD intelligence may produce evidence, but
must not become final scoring or mutation authority.

The tailoring agent should remain separate from final scoring. It should
identify tailoring opportunities automatically as evidence. Any later AI
tailoring generation must be user-triggered through a `Generate AI Tailoring`
button. Generated tailoring suggestions must remain preview/manual-review
only unless the user accepts edits. Tailoring suggestions may guide resume
edits, but must not silently rewrite, overwrite, apply, or submit.

## Current automation status

- automatic job analysis is partly present through deterministic planning and
  evidence artifacts;
- automatic relevance prefiltering is already present deterministically;
- automatic scoring is already present deterministically;
- automatic review evidence generation is already present through planning
  outputs;
- automatic tailoring opportunity detection is partly present through
  shortlist actions, missing requirements, JD/resume packets, and tailoring
  packet generation;
- agent evidence generation and readback exist as staged/default-off wrappers;
  and
- read-only/advisory/manual-review evidence is the current safe automation
  boundary.

Agents should first wrap and materialize existing deterministic outputs. They
may interact through explicit read-only payloads before any durable mutation
is considered. Live-provider agent automation should be introduced only after
read-only materialization, API readback, UI readback, provider-readiness
checks, and safety gates.

## Current mutation status

This checkpoint authorizes:

- no scoring mutation
- no ranking mutation
- no queue mutation
- no resume mutation
- no application mutation
- no approval mutation
- no decision mutation
- no audit mutation
- no provider-call mutation
- no database write mutation
- no execution mutation
- no submission mutation

## Permanent no-autonomous-application boundary

The permanent product rule is:

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control over final job application submission

There is no auto-apply feature, auto-submit feature, autonomous application
execution, or automatic job application submission. Final submission remains
under manual user control.

## Recommended next technical direction

Phase 22C should implement a default-off, read-only core-agent evidence
materialization preview. The preview should assemble existing deterministic
outputs into one manual-review evidence packet containing the relevance
prefilter result, JD signals, final advisory score, review rationale, missing
requirements, and tailoring opportunities.

Any future durable scoring, ranking, or queue mutation requires a separate
mutation-boundary phase, explicit tests, and approval gates. Any future
provider-backed tailoring generation must be user-triggered by
`Generate AI Tailoring`, default-off/gated, preview-only, and controlled by
manual review.

## Release lineage

- `phase22a-manual-review-ux-hardening-v1`
- `phase21-manual-review-workflow-release-v1`
- `phase21e-manual-review-workflow-release-checkpoint-v1`
- `phase21d-manual-review-readiness-ui-readback-v1`
- `phase20-provider-readiness-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`
- `phase19-readonly-approval-workflow-release-v1`
- `phase18-safety-wrap-release-v1`
- `phase17-three-core-shadow-readiness-release-v1`
