# Phase 22B Core-Agent Automation and Mutation Inventory Checkpoint

Phase 22B documents existing deterministic automation and maps its safe future
relationship to core agents. This is a docs/tests-only checkpoint and changes
no runtime behavior.

## Deterministic capability inventory

The application already has the following foundations:

- deterministic job discovery/filtering through the current collection and
  corpus workflow;
- deterministic role/title/location/freshness filtering in
  `src/pipeline/job_filter.py`;
- deterministic resume/job prefiltering in `src/matching/prefilter.py`;
- deterministic JD/resume evidence extraction used by matching and planning;
- deterministic final resume-job scoring in `src/matching/scorer.py`;
- deterministic best resume variant selection in
  `batch_select_best_resume_variant.py`;
- deterministic shortlist/action classification in
  `application_shortlist_from_batch_selector.py`;
- deterministic review evidence generation through
  `run_application_planning.py` outputs;
- deterministic tailoring packet generation through planning and
  `generate_tailoring_suggestions.py`;
- optional LLM fallback/adjudication in the existing batch selector when
  explicitly configured; and
- optional LLM tailoring through `generate_tailoring_suggestions.py` and
  `src/tailoring/llm.py` when explicitly requested.

The existing deterministic files in scope are:

- `src/pipeline/job_filter.py`
- `src/matching/prefilter.py`
- `src/matching/scorer.py`
- `batch_select_best_resume_variant.py`
- `application_shortlist_from_batch_selector.py`
- `run_application_planning.py`
- `generate_tailoring_suggestions.py`
- `src/tailoring/llm.py`

## Core-agent automation direction

The ordered core-agent sequence is:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

`relevance_prefilter` should own early relevance gating.
`jd_intelligence` should own JD signal extraction and evidence interpretation.
`final_application_scoring` should own final advisory score synthesis.

Agents should first wrap and materialize the existing deterministic outputs.
Agents may interact through explicit read-only payloads before any durable
mutation is considered. Live-provider agent automation should follow only
after read-only materialization, API readback, UI readback,
provider-readiness checks, and safety gates.

Prefilter relevance, JD intelligence, final application scoring, and
tailoring suggestions must remain separate:

- final application scoring may advise manual review but must not directly
  mutate queue, ranking, or application state;
- relevance prefilter may reduce review load but must not submit or execute
  applications;
- JD intelligence may produce evidence but must not become final scoring or
  mutation authority; and
- tailoring suggestions may guide resume edits but must not silently rewrite,
  overwrite, apply, or submit.

The tailoring agent should remain separate from final scoring and should
identify tailoring opportunities automatically as evidence. AI tailoring
generation must later be user-triggered through a `Generate AI Tailoring`
button. Generated suggestions remain preview/manual-review only unless the
user accepts edits.

## Current automation status

- automatic job analysis is partly present through deterministic planning and
  evidence artifacts;
- automatic relevance prefiltering is present deterministically;
- automatic scoring is present deterministically;
- automatic review evidence generation is present through planning outputs;
- automatic tailoring opportunity detection is partly present through
  shortlist actions, missing requirements, JD/resume packets, and tailoring
  packet generation;
- agent evidence generation and readback exist as staged/default-off wrappers;
  and
- read-only/advisory/manual-review evidence is the current safe automation
  boundary.

## Mutation inventory

Phase 22B authorizes:

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

## Permanent safety boundary

The permanent product boundary remains:

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control over final job application submission

No automatic application or submission path is introduced or authorized.

## Phase 22C recommendation

Phase 22C should implement a default-off, read-only core-agent evidence
materialization preview. It should combine existing deterministic evidence
into one manual-review packet containing:

- relevance prefilter result;
- JD signals;
- final advisory score;
- review rationale;
- missing requirements; and
- tailoring opportunities.

Any future durable scoring/ranking/queue mutation must require a separate
mutation-boundary phase, explicit tests, and approval gates. Any future
provider-backed tailoring generation must be user-triggered by
`Generate AI Tailoring`, default-off/gated, preview-only, and
manual-review controlled.

## Release references

- `phase22a-manual-review-ux-hardening-v1`
- `phase21-manual-review-workflow-release-v1`
- `phase21e-manual-review-workflow-release-checkpoint-v1`
- `phase21d-manual-review-readiness-ui-readback-v1`
- `phase20-provider-readiness-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`
- `phase19-readonly-approval-workflow-release-v1`
- `phase18-safety-wrap-release-v1`
- `phase17-three-core-shadow-readiness-release-v1`
