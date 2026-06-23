# Phase 18 Live-Readiness Approval Boundary

## Scope

Phase 18A is docs/tests-only and authorizes no runtime behavior. It does not
activate a provider, create a new approval path, mutate application state, or
change the completed Phase 17 implementation.

The system remains:

- default-off
- read-only
- shadow-only
- advisory-only

This boundary follows the completed Phase 17 release:
`phase17-three-core-shadow-readiness-release-v1`.

## Ordered three-core agents

The protected three-core sequence remains:

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

The agents retain separate responsibilities. Provider evaluation, prefilter
relevance, JD intelligence, final scoring, ranking, queueing, resume mutation,
execution, and submission must not be collapsed into one authority.

## Phase 18 boundary categories

### 1. Still shadow-only

Existing Phase 17 readback, operator canary, and local fixture visibility stay
default-off, read-only, shadow-only, and advisory-only. Phase 18A adds no
execution or mutation capability.

### 2. Eligible for future approval design

A later phase may design a narrowly scoped contract for one capability at a
time—for example, a human approval gate or an isolated provider activation
plan—provided the design remains default-off and meets every future approval
gate below.

### 3. Explicitly blocked until separate approval

Provider execution, provider SDK/network calls, scoring mutation, ranking
mutation, queue mutation, resume mutation, approval creation, execution request
creation, application execution, application submission, database writes, and
secrets access are blocked until separately designed, reviewed, tested, and
approved.

## Phase 18A safety decision matrix

| Capability | Current Phase 18A state |
| --- | --- |
| Live provider execution | Not authorized |
| Provider SDK/network calls | Not authorized |
| Final scoring mutation | Not authorized |
| Ranking mutation | Not authorized |
| Queue mutation | Not authorized |
| Resume mutation | Not authorized |
| Approval creation | Not authorized |
| Execution request creation | Not authorized |
| Application execution | Not authorized |
| Application submission | Not authorized |
| DB writes | Not authorized |
| Secrets access | Not authorized |

“Not authorized” means Phase 18A provides no implementation permission, no
implicit rollout permission, and no combined approval for adjacent
capabilities.

## Required future approval gates

Before any live behavior, the proposed phase must include all of the following:

1. A named feature flag that is default-off.
2. Explicit operator/human approval for the narrowly scoped capability.
3. Dry-run/readback evidence demonstrating the proposed behavior and boundary.
4. Fail-closed behavior for missing configuration, rejected approval, invalid
   output, provider failure, or unexpected runtime state.
5. An audit log or trace summary sufficient for operator review.
6. A rollback/disable plan that restores the default-off state.
7. Tests proving no submit/apply path is reachable from the proposed scope.

Passing these gates makes a proposal eligible for review; it does not itself
authorize deployment or execution.

## Minimum future live-provider plan requirements

- Provider execution must be isolated from scoring/ranking mutation.
- Provider outputs must remain advisory until separately approved.
- Provider failures must fail closed.
- Provider calls must be traceable.
- Secrets must not be logged.
- Network/provider SDK calls must be behind explicit default-off flags.
- The plan must not grant queue, resume, execution, or submission authority.

## Minimum future mutation plan requirements

- Separate approval is required for scoring mutation.
- Separate approval is required for ranking mutation.
- Separate approval is required for queue mutation.
- Separate approval is required for resume mutation.
- Separate approval is required for execution request creation.
- Separate approval is required for application execution.
- Separate approval is required for application submission.

Approval for one mutation class does not imply approval for another class.
Provider activation does not imply approval for any mutation.

## Not authorized by Phase 18A

- No live provider execution.
- No provider SDK/network call.
- No DB writes.
- No secrets access.
- No final scoring mutation.
- No ranking mutation.
- No queue mutation.
- No resume mutation.
- No approval creation.
- No execution request creation.
- No application execution.
- No application submission.

## Recommended Phase 18 sequence

1. **18A:** approval boundary docs/tests.
2. **18B:** human approval gate contract, default-off.
3. **18C:** read-only approval preview.
4. **18D:** operator decision capture, no execution.
5. **18E:** protected live-provider activation plan, still no mutation.
6. **Later phase only after approval:** controlled live provider or mutation
   experiment.

## Non-combination rule

No future phase may combine provider execution, scoring mutation, ranking
mutation, queue mutation, resume mutation, and application submission in one
step.

Each capability requires a separate scope, explicit approval boundary,
fail-closed tests, and independent rollback plan.

## Manual verification

1. Run the full tests:
   `PYTHONPATH="$PWD" python -m pytest tests -q`
2. Inspect the changed files and confirm they are docs/tests only.
3. Confirm the Phase 17 readback UI/API remains unchanged.
4. Confirm no runtime file changed.
5. Confirm the safety matrix marks every listed capability as not authorized.

