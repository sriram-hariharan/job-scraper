# Phase 22C Core-Agent Evidence Materialization Preview

Phase 22C builds on the Phase 22B core-agent automation and mutation
inventory. It adds one pure, default-off helper that wraps existing
deterministic outputs supplied by a caller into a read-only manual-review
evidence packet.

The helper only materializes caller-supplied dictionaries. It does not read
artifacts itself and does not call scoring, prefilter, or tailoring runtime
functions. It adds no API, UI, services, pipeline, or collector connection.
It performs no provider calls, no network calls, no database writes, and no
persistence.

## Core-agent sequence and boundaries

The packet preserves the ordered core-agent sequence:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

`relevance_prefilter` owns early relevance gating. `jd_intelligence` owns JD
signal extraction and interpretation. `final_application_scoring` owns final
advisory score synthesis.

The tailoring agent remains separate from final scoring. Tailoring opportunity
detection may be included as evidence, but AI tailoring generation does not
happen in this phase. `Generate AI Tailoring` is a later user-triggered action
only. Generated tailoring suggestions must remain preview/manual-review only
unless the user accepts edits.

## Current safe boundary

Phase 22C is:

- default-off
- read-only
- advisory-only
- manual-review only
- read-only/advisory/manual-review evidence

It authorizes:

- no provider calls
- no network calls
- no database writes
- no persistence
- no mutation
- no scoring mutation
- no ranking mutation
- no queue mutation
- no resume mutation
- no application mutation
- no approval mutation
- no decision mutation
- no audit mutation
- no execution
- no submission

The helper deep-copies its inputs, does not mutate caller data, and does not
create new scoring, ranking, tailoring, or application decisions. It only
summarizes whether supplied evidence is complete enough for manual review.

## Permanent product boundary

The permanent rule remains:

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control over final job application submission

Phase 22C does not authorize automatic application execution or submission.

## Release references

- `phase22b-core-agent-automation-mutation-inventory-v1`
- `phase22a-manual-review-ux-hardening-v1`
- `phase21-manual-review-workflow-release-v1`
- `phase20-provider-readiness-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`
- `phase19-readonly-approval-workflow-release-v1`
- `phase18-safety-wrap-release-v1`
- `phase17-three-core-shadow-readiness-release-v1`
