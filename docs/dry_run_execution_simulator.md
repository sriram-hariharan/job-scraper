# Dry-Run Execution Simulator

Doc path: `docs/dry_run_execution_simulator.md`

Phase 38A adds an explicit/manual dry-run execution simulator only. The simulator is diagnostic-only and consumes existing diagnostic artifacts; it does not enable live orchestration, mutation execution, scheduler execution, UI execution, or autonomous execution.

The simulator reads only these existing read-only artifacts from an explicit input artifact directory:

- `read_only_adapter_chain_result.json`
- `read_only_chain_artifact_generation_result.json`

It writes only these simulator diagnostics to an explicit output directory:

- `dry_run_execution_simulation_result.json`
- `dry_run_execution_simulation_report.md`

It must not write production artifact names at the output root:

- `application_execution_queue.csv`
- `job_prioritization_recommendations.csv`
- `tailoring_decision_recommendations.csv`
- `operator_review_recommendations.csv`

`workflow_runner.py` remains dry-run only. The orchestrator preflight remains read-only and must continue to report `executable_adapter_count=0`.

## Current Boundary

- Explicit/manual dry-run execution simulator only.
- Reads existing read-only chain and generator result JSON artifacts only.
- Validates those artifacts using existing validation helpers.
- Builds simulated non-executable mutation proposals for future design review.
- It does not mutate production.
- Does not run agents.
- Does not run the chain/generator.
- Does not call `run_read_only_adapter_chain()`.
- Does not call `generate_read_only_chain_artifacts()`.
- Does not call `workflow_runner.py`.
- Is not wired into `run_application_planning.py`.
- Is not wired into `application_execution_queue.py`.
- Is not wired into scheduler, background jobs, app routes, or Agentic Review buttons.

## Safety Guarantees

- No live orchestration.
- No automatic execution.
- No scheduler/background execution.
- No UI run button.
- No workflow_runner execution.
- No DB write.
- No queue mutation.
- No application submission.
- No tailoring generation.
- No packet generation.
- No scoring/ranking changes.
- No filtering, scraping/source, resume selection, RAG, scheduler, or application workflow behavior changes.
- No new dependencies.
- No LangGraph or agent framework.

## CLI

The simulator requires explicit paths. It does not discover defaults and does not read application state.

```bash
python -m src.agents.dry_run_execution_simulator \
  --input-artifact-dir <dir> \
  --output-dir <dir> \
  --json
```

Missing arguments fail safely with JSON output and a nonzero exit code:

- `missing_explicit_input_artifact_dir`
- `missing_explicit_output_dir`

Missing input artifacts also fail safely:

- `missing_read_only_adapter_chain_result`
- `missing_read_only_chain_artifact_generation_result`

## Simulation Payload

The result payload includes:

- `execution_mode=explicit_dry_run_execution_simulation`
- `did_simulate`
- `did_execute_live=false`
- `did_mutate_production=false`
- `allow_application_submission=false`
- `allow_queue_action_update=false`
- `allow_packet_update=false`
- `allow_tailoring_generation_update=false`
- `allow_scoring_update=false`
- `allow_ranking_update=false`
- `allow_db_write=false`
- `allow_scheduler_execution=false`
- `simulated_execution_plan`
- `simulated_mutation_proposals`
- `blocked_live_execution_reasons`
- `validation`

Simulated mutation proposals are non-executable evidence only:

- `proposal_mode=simulated_non_executable`
- `can_execute_live=false`
- `requires_approval=true`
- `blocked_by_default=true`

Allowed simulated mutation proposal types are diagnostic placeholders only:

- `queue_diagnostic_status_marker`
- `operator_note`
- `artifact_status_marker`

These are not production mutations. They are future-contract placeholders that remain blocked until a separate reviewed phase designs and implements an operator approval gate, audit ledger, idempotency key, execution lock, and rollback plan.

## Validation Rules

`validate_dry_run_execution_simulation_result(...)` fails closed if:

- execution mode is not `explicit_dry_run_execution_simulation`;
- explicit input or output directories are missing;
- any live execution flag is true;
- any mutation or production-write flag is true;
- the simulated plan can execute live;
- operator approval, audit ledger, idempotency key, execution lock, or rollback plan requirements are missing;
- a simulated proposal is executable, unapproved, not blocked by default, or uses a forbidden mutation type;
- `queue_mutation_blocked` or `application_submission_blocked` is absent from blocked reasons;
- production artifact names are written at the output root;
- non-simulator artifact names are written at the output root.

## Non-Goals

- No live execution.
- No live-run audit ledger implementation.
- No DB schema, migration, storage, or persistence implementation.
- No mutation policy implementation.
- No approval API/UI/storage implementation.
- No idempotency store or persisted lock implementation.
- No rollback implementation.
- No execution adapter implementation.
- No application submission.
- No queue updates.
- No tailoring or packet generation.
- No scoring/ranking behavior changes.
- No runtime/pipeline behavior changes.

## Relationship To Future Milestones

Phase 38A remains planning-first. It creates a diagnostic simulator that can help operators inspect what a future mutation proposal might look like without allowing any mutation.

The simulator does not satisfy the hard blockers from `docs/live_orchestration_readiness_gap_analysis.md`. Future phases still need separate reviewed design and implementation work for:

- operator approval;
- audit ledger;
- idempotency key;
- execution lock;
- rollback plan;
- feature flag strategy;
- read-only approval UI mock;
- controlled execution prototype behind explicit gates.
