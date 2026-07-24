# Controlled Shadow Observation Runbook

## Scope and permanent boundaries

This runbook governs explicit, default-off post-planning shadow observation. It
is not canary routing and does not make shadow orchestration authoritative.
Authoritative application planning remains the only production authority.

The shadow path uses no live LLM, durable execution, `finalize`, application
action, or submission. It retains only the bounded
`applylens-shadow-observation-v1` operational record. It must not retain job,
resume, owner, run, context, graph, content, path, stdout, stderr,
recommendation, artifact-digest, credential, or authorization data.

## Approval and ownership

Before the first controlled run, record approval from Engineering, Operations,
Security/privacy, and Product. Assign a named Shadow Observation Operator and a
different named Shadow Rollback Owner. A parity result cannot promote or change
production automatically.

## Eligible initial cohort

The initial cohort is limited to user-owned, planning-only, direct
operator-selected executions with explicit owner, pipeline-run, and context
identities. Scheduler-wide and service-wide activation are prohibited.

Operational coverage targets are:

- the first 10 runs have no more than 10 jobs each;
- at least 50 runs over seven days;
- at least 500 total jobs;
- at least five 25-job batches.

These are coverage targets, not statistically proven thresholds.

## Preflight

The Shadow Observation Operator must:

1. Verify the deployed commit and release provenance.
2. Verify the production shadow flag defaults to false.
3. Confirm that flag distribution is limited to the selected process.
4. Verify owner, pipeline-run, and context identities are present.
5. Verify `outputs/shadow_observations/` is operator-owned, mode `0700`,
   has adequate disk space, and is not a symlink.
6. Verify JSONL segments, lock, and HMAC secret use mode `0600`.
7. Confirm 30-day record retention and zero-retention temporary cleanup.
8. Record the named operator, rollback owner, cohort entry, and approvals.

This document intentionally contains no command that enables the production
flag.

## Monitoring

Monitor authoritative status independently from shadow status. Observe:

- bounded terminal classification;
- total and per-job latency;
- timeout count;
- safety-violation count;
- cleanup failure categories and count;
- positive process-liveness confirmation;
- observation-store result.

Do not interrupt or alter authoritative planning solely because of a parity
mismatch.

After each selected run, verify authoritative success and unchanged outputs,
absence of actions/submissions, temporary-file deletion, child/process-group
liveness, and exactly one stored or idempotently recognized observation.

## Immediate rollback

The rollback owner removes the per-run flag from subsequent launches and
verifies the next equivalent run creates no projection, shadow temporary
directory, child process, HMAC secret, or observation record. Preserve existing
bounded records and logs. Never modify or delete authoritative business
outputs. Inspect any already-running owned process before declaring rollback
complete; never target an unresolved process group.

Rollback requires no database migration, schema cleanup, or authoritative-data
deletion.

## Escalation

| Event | Severity | Owner |
|---|---|---|
| Shadow execution failure | Warning | Engineering on-call |
| Timeout | Warning; urgent rollback when repeated | Operations and engineering |
| Selected-resume mismatch | Urgent rollback | Engineering and product |
| Safety or write-suppression violation | Security incident and urgent rollback | Security and engineering |
| Application action or submission detected | Security incident | Security and application owner |
| Cleanup failure | Urgent rollback | Operations and security |
| Process liveness unconfirmed | Security incident and urgent rollback | Operations and security |
| Observation failure | Warning; pause the cohort | Operations |
| Unexpected LLM call | Security incident | Security and ML engineering |
| Unexpected durable connection | Security incident | Security and platform engineering |

Preserve only bounded classifications and counts during escalation. Do not copy
paths, exceptions, stdout/stderr, child payloads, or user/run identities into
diagnostics.

## Retention

- Temporary projection, evidence, facts, and handoff files: zero retention
  after execution.
- Runtime shadow status and aggregate logs: recommended 14 days.
- Observation JSONL segments: 30 days.
- Final aggregate review report: up to 90 days only after approval.

Retention runs opportunistically during enabled observation writes. It deletes
only owned daily JSONL segments older than 30 days, ignores unrelated files,
and does not run while shadow is disabled. A retention failure is bounded and
cannot affect authoritative production.

The retention-scoped HMAC secret remains stable while retained observations
depend on it. Key rotation is deferred until every retained segment from the
old key window has expired. Rotation and final-report retention require
Operations and Security/privacy ownership.

Windows process-group proof is unsupported for controlled observation. It must
be implemented and reviewed before broader Windows deployment.
