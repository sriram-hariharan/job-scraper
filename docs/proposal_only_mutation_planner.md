# Proposal-Only Mutation Planner

Doc path: `docs/proposal_only_mutation_planner.md`

Phase 41A adds an explicit/manual proposal-only mutation planner. It consumes an existing dry-run simulator result artifact and writes diagnostic proposal-only artifacts.

This planner does not run the simulator. It does not run the read-only chain. It does not run the explicit generator. It does not run agents, `workflow_runner.py`, live planning, scheduler jobs, app routes, or storage.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Boundary

- Explicit/manual proposal-only planner only.
- Requires an explicit `--simulation-result` path.
- Requires an explicit `--output-dir`.
- Reads only an already-existing `dry_run_execution_simulation_result.json`.
- Validates the simulator result before planning.
- Produces non-executable proposal-only items from `simulated_mutation_proposals` only.
- Does not invent real mutations.
- Does not mutate production.
- Does not update queue state.
- Does not submit applications.
- Does not write DB rows.
- Does not approve, reject, or store approval.
- Does not call approval APIs.
- Does not call mutation APIs.
- Does not add approval storage.
- Does not add audit ledger storage.
- Does not add lock/idempotency storage.
- Does not generate tailoring or packets.
- Does not change scoring/ranking.
- Does not change filtering, scraping/source, resume, RAG, scheduler, or application submission behavior.
- Future live execution remains blocked.

## Inputs

The planner accepts only an existing simulator result JSON:

- `dry_run_execution_simulation_result.json`

The simulator artifact must validate and remain non-live:

- `execution_mode=explicit_dry_run_execution_simulation`
- `did_execute_live=false`
- `did_mutate_production=false`
- `simulated_execution_plan.can_execute_live=false`

Missing, nonexistent, malformed, or unsafe simulator results fail closed and do not produce a plan.

## Outputs

The planner writes only these diagnostic proposal-only artifacts to the explicit output directory:

- `proposal_only_mutation_plan_result.json`
- `proposal_only_mutation_plan_report.md`

It must not write production artifact names at the output root:

- `application_execution_queue.csv`
- `job_prioritization_recommendations.csv`
- `tailoring_decision_recommendations.csv`
- `operator_review_recommendations.csv`
- `dry_run_execution_simulation_result.json`

It does not write approval records, mutation records, audit ledger records, lock records, idempotency records, DB rows, queue rows, application submissions, tailoring artifacts, packet artifacts, scoring artifacts, or ranking artifacts.

## Proposal Plan

The proposal plan is non-executable:

- `plan_mode=proposal_only_non_executable`
- `can_execute_live=false`
- `can_mutate=false`
- `can_approve=false`
- `requires_operator_approval=true`
- `requires_approval_api=true`
- `requires_approval_storage=true`
- `requires_audit_ledger=true`
- `requires_idempotency_key=true`
- `requires_execution_lock=true`
- `requires_rollback_plan=true`

Next review steps remain planning-only:

- `review_non_executable_proposals`
- `verify_mutation_type_allowlist`
- `require_future_approval_gate`
- `require_future_audit_ledger`
- `require_future_idempotency_locking`
- `block_live_execution`
- `block_application_submission`
- `block_queue_mutation`

## Proposal Items

Every proposal-only item is non-executable:

- `proposal_mode=proposal_only_non_executable`
- `can_execute_live=false`
- `can_mutate=false`
- `can_approve=false`
- `blocked_by_default=true`
- `requires_operator_approval=true`
- `requires_audit_ledger=true`
- `requires_idempotency_key=true`
- `requires_execution_lock=true`
- `requires_rollback_plan=true`

Allowed mutation type placeholders are diagnostic only:

- `queue_diagnostic_status_marker`
- `operator_note`
- `artifact_status_marker`

Forbidden mutation types fail validation if present:

- `application_submission`
- `queue_action_update`
- `tailoring_generation`
- `packet_generation`
- `scoring_update`
- `ranking_update`
- `resume_rewrite`
- `scraper_source_mutation`
- `rag_corpus_mutation`
- `production_record_delete`

## CLI

```bash
python -m src.agents.proposal_only_mutation_planner \
  --simulation-result <path/to/dry_run_execution_simulation_result.json> \
  --output-dir <dir> \
  --json
```

The CLI has no default production paths, no automatic discovery, and no DB requirement.

Missing arguments return safe JSON and a nonzero exit code:

- `missing_explicit_simulation_result_path`
- `missing_explicit_output_dir`

Nonexistent simulator artifacts return safe JSON and a nonzero exit code:

- `simulation_result_path_not_found`

Invalid simulator artifacts return safe JSON and a nonzero exit code:

- `simulation_result_validation_failed`

## Non-Goals

- No live execution.
- No mutation.
- No queue mutation.
- No application submission.
- No DB write.
- No approval/reject action.
- No approval API/storage.
- No mutation API.
- No audit ledger storage.
- No lock/idempotency implementation.
- No scheduler/background execution.
- No UI action.
- No runtime/pipeline/app behavior changes.
- No LangGraph or agent framework.

## Relationship To Decision Gate

The controlled execution decision gate allows proposal-only safety scaffolding as `LIMITED_GO` only if it remains explicit/manual/read-only/non-mutating.

This planner satisfies that boundary by producing diagnostic proposal-only artifacts. It does not close the blockers for live mutation. Future live execution still requires reviewed approval storage/API, audit ledger storage, idempotency storage, execution lock storage, rollback implementation, feature flag/environment gates, failure recovery tests, and a dry-run-to-live promotion policy.

## Agentic Review Display

Proposal-only planner artifacts can now be displayed in Agentic Review.

- `proposal_only_mutation_plan_result.json`
- `proposal_only_mutation_plan_report.md`

The display is read-only and non-actionable. It does not approve, reject, store approval, mutate queue state, write DB rows, submit applications, execute anything, call approval APIs, call mutation APIs, or add approval storage.

Future real approval or mutation behavior requires separate reviewed phases.
