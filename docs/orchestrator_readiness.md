# Real Orchestrator Readiness Audit

Phase 19A is a readiness audit only. The implemented workflow remains dry-run only: `src/agents/workflow_runner.py` does not execute agents, does not call LLMs, does not write production decisions, and does not change pipeline behavior.

There is no autonomous execution in this phase. There is no LangGraph integration or agent framework. Human feedback does not tune ranking or scoring. RAG Evaluation does not change retrieval, embeddings, corpus generation, ranking, scoring, queue action, tailoring, or packet behavior.

No production decision mutation is implemented or enabled by this readiness audit.

Phase 19B adds `src/agents/orchestrator_adapters.py` as a static adapter contract metadata module. It is contract-only: it does not execute agents, does not enable autonomous execution, does not wire into live planning, and does not change runtime behavior.

Phase 20A adds `src/agents/orchestrator_adapter_harness.py` as a read-only preflight harness. It inspects the workflow registry order, adapter contract metadata, and optional artifact presence only. It does not import or call agent execution functions, does not enable autonomous execution, does not wire into live planning, and does not change production behavior. Future real execution still requires a separate reviewed phase.

Phase 21A adds `src/agents/read_only_job_prioritization_adapter.py` as a manual read-only adapter prototype for `job_prioritization` only. The prototype accepts explicit rows or an explicit input CSV path, writes only adapter-specific diagnostics when an isolated output directory is provided, and does not update queue action, packet generation, tailoring, scoring, ranking, or production artifacts. `workflow_runner.py` remains dry-run only, and future multi-agent execution still requires a separate reviewed phase.

Phase 22A adds `src/agents/read_only_tailoring_decision_adapter.py` as a manual read-only adapter prototype for `tailoring_decision` only. The prototype accepts explicit queue rows or an explicit queue input CSV path, may use optional explicit prioritization rows or an explicit prioritization CSV path, writes only adapter-specific diagnostics when an isolated output directory is provided, and does not update queue action, packet generation, tailoring generation, scoring, ranking, or production artifacts. `workflow_runner.py` remains dry-run only, and future multi-agent execution still requires a separate reviewed phase.

Phase 23A adds `src/agents/read_only_operator_review_adapter.py` as a manual read-only adapter prototype for `operator_review` only. The prototype accepts explicit queue rows or an explicit queue input CSV path, may use optional explicit prioritization or tailoring rows or explicit CSV paths, writes only adapter-specific diagnostics when an isolated output directory is provided, and does not update queue action, packet generation, tailoring generation, scoring, ranking, application submission, or production artifacts. `workflow_runner.py` remains dry-run only, and future multi-agent execution still requires a separate reviewed phase.

Phase 24A adds `src/agents/read_only_adapter_chain.py` as a manual read-only adapter chain for `job_prioritization`, `tailoring_decision`, and `operator_review`. The chain runs only explicit/manual adapter prototypes with caller-provided rows or an explicit queue CSV path, writes only chain-specific diagnostics and adapter-specific subdirectory diagnostics when an isolated output directory is provided, and does not update queue action, packet generation, tailoring generation, scoring, ranking, application submission, or production artifacts. It is not wired into live planning, the scheduler, UI actions, or `workflow_runner.py`; future real orchestration still requires a separate reviewed phase.

Phase 25A allows manually produced chain artifacts (`read_only_adapter_chain_result.json` and `read_only_adapter_chain_report.md`) to be ingested, verified, and displayed in Agentic Review diagnostics. This does not run the chain, does not change production decisions, and does not wire the chain into live planning, the scheduler, UI actions, or `workflow_runner.py`. Future real orchestration still requires a separate reviewed phase.

Phase 29A allows explicitly produced read-only chain generator artifacts (`read_only_chain_artifact_generation_result.json` and `read_only_chain_artifact_generation_report.md`) to be ingested, verified, and displayed in Agentic Review diagnostics. This does not run the generator, does not change production decisions, and does not wire the generator into live planning, the scheduler, UI actions, or `workflow_runner.py`. Future real orchestration still requires a separate reviewed phase.

Operator-facing steps for the explicit generator live in `docs/read_only_chain_operator_runbook.md`; the runbook is manual/read-only documentation and does not enable live orchestration.

Phase 33A live orchestration readiness gaps are tracked in `docs/live_orchestration_readiness_gap_analysis.md`. That document is planning-only and does not enable live orchestration.

Phase 34A production execution contract boundaries are tracked in `docs/production_execution_contract_design.md`. That document is design-only and does not enable live orchestration.

Phase 35A mutation policy and approval gate boundaries are tracked in `docs/mutation_policy_approval_gate_design.md`. That document is design-only and does not enable mutation execution.

Phase 36A live-run audit ledger schema boundaries are tracked in `docs/live_run_audit_ledger_schema_design.md`. That document is design/schema proposal-only and does not enable persistence, ledger writes, live execution, or mutation execution.

Phase 37A idempotency and locking boundaries are tracked in `docs/idempotency_locking_design.md`. That document is design-only and does not add lock tables, migrations, idempotency stores, runtime lock checks, live execution, or mutation execution.

Phase 38A dry-run execution simulation is tracked in `docs/dry_run_execution_simulator.md`. The simulator is explicit/manual and diagnostic-only; it consumes existing read-only artifacts, does not run the chain/generator, and does not enable live execution, mutation, DB writes, queue updates, application submission, scheduler execution, or `workflow_runner.py` execution.

Phase 39A allows dry-run execution simulation artifacts to be displayed in Agentic Review with an Operator Approval Mock. The mock is read-only and non-actionable; it does not approve, reject, store approval, mutate queues, write to the database, submit applications, or execute anything.

Phase 40A controlled execution decisions are tracked in `docs/controlled_execution_decision_gate.md`. That decision gate is planning-only: live mutation is `NO_GO`, proposal-only mutation planning is `LIMITED_GO` only if explicit/manual/read-only/non-mutating, and no execution or approval implementation is enabled.

Phase 41A proposal-only mutation planning is tracked in `docs/proposal_only_mutation_planner.md`. The planner is explicit/manual and diagnostic-only; it consumes an existing dry-run simulation result, does not run the simulator/chain/generator, and does not enable live execution, mutation, approval, DB writes, queue updates, application submission, scheduler execution, or `workflow_runner.py` execution.

Phase 42A displays proposal-only planner diagnostics in Agentic Review. The display is read-only/non-actionable and still does not enable live execution, mutation, approval APIs, approval storage, DB writes, queue updates, application submission, or scheduler execution.

Phase 43A release safety checkpoint is tracked in `docs/proposal_planner_release_safety_checkpoint.md`. That checkpoint is docs/tests only and confirms the proposal-planner stack remains explicit/manual/read-only/non-mutating before any future release work.

Phase 44A storage design review is tracked in `docs/storage_design_review_audit_idempotency_locks.md`. That review is docs/tests only and does not add DB schemas, migrations, storage APIs, DB writes, approval storage, audit ledger storage, idempotency storage, execution lock storage, or live mutation.

Phase 45A transaction boundary design is tracked in `docs/transaction_boundary_design.md`. That design is docs/tests only and does not add transaction code, DB schemas, migrations, storage APIs, DB writes, approval storage, audit ledger storage, idempotency storage, execution lock storage, or live mutation.

Phase 46A failure-mode test planning is tracked in `docs/failure_mode_test_plan.md`. That plan is docs/tests only and does not add runtime failure-mode tests, transaction code, DB schemas, migrations, storage APIs, DB writes, approval storage, audit ledger storage, idempotency storage, execution lock storage, or live mutation.

Phase 47A storage schema proposal is tracked in `docs/storage_schema_proposal.md`. That proposal is docs/tests only and does not add DB schema files, migrations, SQL DDL, storage APIs, DB writes, approval storage, audit ledger storage, idempotency storage, execution lock storage, transaction code, runtime failure-mode tests, or live mutation.

Phase 48A storage schema release safety checkpoint is tracked in `docs/storage_schema_release_safety_checkpoint.md`. That checkpoint is docs/tests only and confirms the storage schema proposal remains design-only before any future migration, storage API, DB write, approval storage, mutation API, transaction code, or live mutation work.

Phase 49A storage/transaction failure fixture design is tracked in `docs/storage_transaction_failure_fixture_design.md`. That document is docs/tests only and designs future synthetic fixtures without adding fixture files, runtime failure-mode tests, DB schemas, migrations, SQL DDL, storage APIs, DB writes, transaction code, mutation execution, or live execution.

Phase 50A storage/transaction fixture release safety checkpoint is tracked in `docs/storage_transaction_fixture_release_safety_checkpoint.md`. That checkpoint is docs/tests only and confirms the fixture design remains design-only before any fixture files, fixture directories, runtime failure-mode tests, storage integration tests, migrations, storage APIs, DB writes, transaction code, mutation execution, or live execution.

Phase 51A fixture validator contract design is tracked in `docs/fixture_validator_contract_design.md`. That document is docs/tests only and defines a future diagnostic validator contract without adding validator code, fixture files, fixture directories, runtime failure-mode tests, storage integration tests, DB writes, mutation execution, or live execution.

Phase 52A fixture validator contract release safety checkpoint is tracked in `docs/fixture_validator_contract_release_safety_checkpoint.md`. That checkpoint is docs/tests only and confirms the validator contract remains design-only before any validator code, fixture files, fixture directories, runtime failure-mode tests, storage integration tests, DB writes, mutation execution, or live execution.

Phase 53A fixture naming and reason-code taxonomy checkpoint is tracked in `docs/fixture_naming_reason_code_taxonomy_checkpoint.md`. That checkpoint is docs/tests only and freezes proposed future fixture naming and reason-code taxonomy before any validator code, fixture files, fixture directories, runtime failure-mode tests, storage integration tests, DB writes, mutation execution, or live execution.

Phase 54A fixture naming and reason-code taxonomy release safety checkpoint is tracked in `docs/fixture_naming_reason_code_taxonomy_release_safety_checkpoint.md`. That checkpoint is docs/tests only and confirms the naming and reason-code taxonomy remains design-only before any validator code, fixture files, fixture directories, runtime failure-mode tests, storage integration tests, DB writes, mutation execution, or live execution.

## Current Status

- `src/agents/workflow_registry.py` defines the ordered advisory workflow and marks all six implemented agents as non-mutating.
- `src/agents/workflow_planner.py` builds a diagnostic dry-run plan with `execution_enabled=false` and `execution_status=planned`.
- `src/agents/workflow_runner.py` only emits skipped dry-run step results with `did_execute=false`.
- `src/agents/orchestrator_adapter_harness.py` builds a `read_only_preflight` plan with `allow_agent_execution=false`, `executable_adapter_count=0`, and `did_execute=false` for every adapter.
- `src/agents/read_only_job_prioritization_adapter.py` is explicit/manual only and is not wired into live planning, the scheduler, or `workflow_runner.py`.
- `src/agents/read_only_tailoring_decision_adapter.py` is explicit/manual only and is not wired into live planning, the scheduler, or `workflow_runner.py`.
- `src/agents/read_only_operator_review_adapter.py` is explicit/manual only and is not wired into live planning, the scheduler, or `workflow_runner.py`.
- `src/agents/read_only_adapter_chain.py` is explicit/manual only and is not wired into live planning, the scheduler, UI actions, or `workflow_runner.py`.
- Manual read-only adapter chain artifacts can be displayed in Agentic Review diagnostics when a user has produced them explicitly.
- `src/agents/workflow_verifier.py` validates artifacts and dry-run payloads when present.
- `run_application_planning.py` writes manifest, execution-plan, dry-run, verifier, and RAG Evaluation diagnostics through existing artifact hooks.
- `application_execution_queue.py` writes current advisory artifacts for job prioritization, tailoring decision, and operator review, and may record aggregate trace rows when tracing is explicitly enabled.

Real execution is not enabled because there is no adapter boundary that can safely load inputs, validate context, call each agent in read-only mode, write diagnostics idempotently, and record trace rows without affecting production decisions.

The adapter contract layer now defines the proposed boundary as static metadata and validation helpers. It stores callable entrypoint names as strings only, records allowed future read-only modes, and validates that no adapter mutates production decisions or enables live execution.

The read-only adapter harness is a diagnostic preflight for that metadata. It reports whether each adapter is contract-ready, needs more adapter work, or is blocked, but it never calls the callable entrypoints listed in the contract.

The Job Prioritization read-only adapter prototype is narrower than a runner. It can call deterministic Job Prioritization advisory helpers only when invoked directly by tests, helpers, or its CLI. It does not call other agents, does not call LLMs, does not write to the database, and does not mutate source input rows.

The Tailoring Decision read-only adapter prototype is narrower than a runner. It can call deterministic Tailoring Decision advisory helpers only when invoked directly by tests, helpers, or its CLI. It does not call other agents, does not call LLMs, does not write to the database, and does not mutate source input rows.

The Operator Review read-only adapter prototype is narrower than a runner. It can call deterministic Operator Review advisory helpers only when invoked directly by tests, helpers, or its CLI. It does not call other agents, does not call LLMs, does not write to the database, and does not mutate source input rows.

The manual read-only adapter chain is narrower than a runner. It calls only the existing read-only adapter modules in the fixed order `job_prioritization`, `tailoring_decision`, `operator_review`; it does not call original agent modules directly, does not call LLMs, does not write to the database, and does not mutate source input rows.

## Readiness Matrix

| Agent | Owner module | Callable/helper entry points found | Required input artifacts/env/context | Output artifacts/payloads | Writes artifacts now | Writes traces now | Database access | Env vars | LLM calls | Mutates production decisions | Readiness status | Reason codes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `source_health` | `src.agents.source_health_agent` | `parse_source_health_report_csv()`, `build_source_health_agent_input_payload()`, `build_source_health_agent_output_payload()`, `build_source_health_agent_validation_payload()`, `render_source_health_recommendations()`, `record_source_health_agent_trace()` | `source_health_report.csv`; optional `pipeline_run_id`, `artifact_name`, `artifact_path`; trace requires `JOB_APP_PIPELINE_RUN_ID` or `JOB_STACK_USER_PIPELINE_RUN_ID`, `JOB_STACK_OWNER_USER_ID`, optional `APPLYLENS_AGENT_CONTEXT_ID` | recommendation payload, validation payload, summary payload; registry declares `source_health_report.csv` | No dedicated artifact writer in the agent module | Yes, only when `APPLYLENS_AGENT_TRACE_ENABLED=1` and owner/run context exists | Only through optional trace store | `APPLYLENS_AGENT_TRACE_ENABLED`, `APPLYLENS_AGENT_TRACE_STRICT`, trace context env | No | No | `needs_adapter` | `no_active_runner_adapter`, `needs_input_loader`, `needs_diagnostic_artifact_policy`, `trace_context_required` |
| `resume_match` | `src.agents.resume_match_agent` | `build_resume_match_agent_input_payload()`, `build_resume_match_agent_output_payload()`, `build_resume_match_agent_validation_payload()`, `build_resume_match_agent_summary_payload()`, `record_resume_match_agent_trace()` | `best_resume_variant_by_job.csv` rows, candidate resume names, source artifact path; optional run/owner context; trace env as above | input/output/validation/summary payloads; registry declares `best_resume_variant_by_job.csv` | No dedicated artifact writer in the agent module | Yes, only when tracing is enabled and owner/run context exists | Only through optional trace store | `APPLYLENS_AGENT_TRACE_ENABLED`, `APPLYLENS_AGENT_TRACE_STRICT`, trace context env | No | No | `needs_adapter` | `no_active_runner_adapter`, `needs_input_loader`, `needs_candidate_resume_context`, `needs_diagnostic_artifact_policy`, `trace_context_required` |
| `critic` | `src.agents.critic_agent` | `build_critic_agent_input_payload()`, `evaluate_critic_suggestion()`, `build_critic_agent_validation_payload()`, `render_critic_decision()`, `build_critic_agent_summary_payload()`, `record_critic_agent_trace()` | Scan/tailoring suggestion payloads with resume evidence, JD skills, proposed text, source bullet, score delta, and suggestion type; advisory use is feature-flagged in existing flows | critic decision payloads, validations, summary payload | No dedicated artifact writer in the agent module | Yes, only when tracing is enabled and owner/run context exists | Only through optional trace store | `APPLYLENS_CRITIC_ADVISORY_ENABLED`, `APPLYLENS_AGENT_TRACE_ENABLED`, `APPLYLENS_AGENT_TRACE_STRICT`, trace context env | No | No | `needs_adapter` | `no_active_runner_adapter`, `needs_scan_suggestion_loader`, `needs_feature_flag_policy`, `needs_diagnostic_artifact_policy`, `trace_context_required` |
| `job_prioritization` | `src.agents.job_prioritization_agent` | `build_job_prioritization_agent_input_payload()`, `recommend_job_priority()`, `build_job_prioritization_agent_output_payload()`, `build_job_prioritization_agent_validation_payload()`, `render_job_prioritization_recommendations()`, `render_job_prioritization_recommendation_rows()`, `write_job_prioritization_artifacts()`, `record_job_prioritization_agent_trace()` | `application_execution_queue.csv` rows plus source health fields when present; run/owner/source artifact context for diagnostics; trace env as above | `job_prioritization_recommendations.csv`, `job_prioritization_summary.json`, payloads | Yes, when called by `application_execution_queue.py` with output paths | Yes, only when tracing is enabled and owner/run context exists | Only through optional trace store | `APPLYLENS_AGENT_TRACE_ENABLED`, `APPLYLENS_AGENT_TRACE_STRICT`, trace context env | No | No | `ready_for_read_only_orchestrator` | `no_active_runner_adapter`, `artifact_writer_exists`, `validation_exists`, `trace_optional` |
| `tailoring_decision` | `src.agents.tailoring_decision_agent` | `build_tailoring_decision_agent_input_payload()`, `recommend_tailoring_decision()`, `build_tailoring_decision_agent_output_payload()`, `build_tailoring_decision_agent_validation_payload()`, `render_tailoring_decisions()`, `render_tailoring_decision_rows()`, `write_tailoring_decision_artifacts()`, `record_tailoring_decision_agent_trace()` | Queue rows overlaid with job prioritization, critic, resume credibility, and packet eligibility fields; run/owner/source artifact context for diagnostics; trace env as above | `tailoring_decision_recommendations.csv`, `tailoring_decision_summary.json`, payloads | Yes, when called by `application_execution_queue.py` with output paths | Yes, only when tracing is enabled and owner/run context exists | Only through optional trace store | `APPLYLENS_AGENT_TRACE_ENABLED`, `APPLYLENS_AGENT_TRACE_STRICT`, trace context env | No | No | `ready_for_read_only_orchestrator` | `no_active_runner_adapter`, `artifact_writer_exists`, `validation_exists`, `trace_optional` |
| `operator_review` | `src.agents.operator_review_agent` | `build_operator_review_agent_input_payload()`, `recommend_operator_lane()`, `build_operator_review_agent_output_payload()`, `build_operator_review_agent_validation_payload()`, `render_operator_review()`, `render_operator_review_rows()`, `write_operator_review_artifacts()`, `record_operator_review_agent_trace()` | Queue rows overlaid with prioritization, tailoring decision, critic, source health, resume credibility, and packet eligibility fields; run/owner/source artifact context for diagnostics; trace env as above | `operator_review_recommendations.csv`, `operator_review_summary.json`, payloads | Yes, when called by `application_execution_queue.py` with output paths | Yes, only when tracing is enabled and owner/run context exists | Only through optional trace store | `APPLYLENS_AGENT_TRACE_ENABLED`, `APPLYLENS_AGENT_TRACE_STRICT`, trace context env | No | No | `ready_for_read_only_orchestrator` | `no_active_runner_adapter`, `artifact_writer_exists`, `validation_exists`, `trace_optional` |

## Side-Effect Risk

The current agent helpers are deterministic and advisory, but several helpers can write diagnostic artifacts or trace rows when called directly. A future real orchestrator must treat artifact writes and trace writes as explicit diagnostic side effects with owner/run scoping and idempotency rules.

Known side-effect boundaries:

- Artifact writers exist for job prioritization, tailoring decision, and operator review.
- Trace writers exist for all six agents, but tracing is disabled by default and requires owner/run context.
- Source health, resume match, and critic currently expose render/build helpers but no dedicated diagnostic artifact writer.
- None of the six agent modules makes LLM calls.
- None of the six agent modules mutates production decisions by design or registry contract.

## Trace Readiness

Trace readiness is partial. All six implemented agents have `record_*_agent_trace()` helpers and deterministic LLMOps metadata. The trace path writes aggregate rows through `src/agents/trace.py` and the agent trace store only when `APPLYLENS_AGENT_TRACE_ENABLED=1`.

Blockers before real execution:

- Central orchestrator context must provide authenticated `owner_user_id`, `pipeline_run_id`, and stable `context_id`.
- Trace failure policy must be explicit for real execution; current default is warning unless strict tracing is enabled.
- Per-job trace rows are not implemented and must not be implied by a real orchestrator.

## Artifact Readiness

Artifact readiness is partial.

- Registry, planner, dry-run runner, verifier, RAG Evaluation, job prioritization, tailoring decision, and operator review already have diagnostic artifact writers.
- Source health, resume match, and critic need a future adapter-level artifact policy if their real orchestrator outputs should be persisted separately.
- Existing advisory artifacts preserve production fields such as `action` and add separate advisory fields such as `advisory_priority`, `tailoring_decision`, and `operator_review_lane`.

## Validation Readiness

Validation readiness is good for diagnostic execution and incomplete for real orchestration.

- Each implemented agent exposes validation payload helpers or validation inside render helpers.
- The workflow registry validates ordered agents, feature flags, artifact kinds, and non-mutating contracts.
- The workflow planner and dry-run runner validate disabled execution.
- The workflow verifier validates artifact consistency when artifacts exist.

Missing before real execution:

- Adapter-level validation for loaded inputs.
- Adapter-level validation for output schema and artifact idempotency.
- A no-production-mutation gate after each proposed step.
- Tests proving a real orchestrator cannot call production-mutating functions.

## Proposed Future Adapter Contract

This is a proposed contract only. It is not active production behavior and is not implemented in this phase.

```text
load_inputs(context)
validate_inputs(inputs)
run_read_only(inputs, context)
validate_outputs(outputs)
write_diagnostics(outputs)
record_trace(step)
```

Contract expectations:

- `load_inputs(context)` reads only owner-scoped artifacts and never changes job visibility or ordering.
- `validate_inputs(inputs)` fails closed or returns diagnostic warnings before any agent helper is called.
- `run_read_only(inputs, context)` calls deterministic agent helpers only; no LLM calls and no production writes.
- `validate_outputs(outputs)` checks schema, reason codes, row counts, and non-mutating fields.
- `write_diagnostics(outputs)` writes only advisory/read-only artifacts under the run's diagnostic artifact scope.
- `record_trace(step)` records aggregate trace rows only when trace flags and owner/run context are present.

## Blockers Before Real Execution

- No active runner adapter exists.
- `workflow_runner.py` is intentionally dry-run only and must not be changed to execute agents without a separate reviewed phase.
- `src/agents/orchestrator_adapter_harness.py` is preflight only; `python -m src.agents.orchestrator_adapter_harness --preflight --json` produces deterministic metadata and does not execute agents.
- A central owner-scoped input loader is missing.
- Source health, resume match, and critic need diagnostic artifact policies.
- Idempotent artifact write rules are not defined for a real orchestrator.
- Strict/non-strict behavior for adapter failures is not defined.
- Production mutation checks must be enforced after every future adapter step.
- Real execution must be tested independently from live planning before any planning integration.

## Safe Next Increment

The safe next increment is to add a read-only adapter interface and static adapter metadata behind tests, without wiring it into `run_application_planning.py`, `application_execution_queue.py`, scheduler flows, API routes, or Agentic Review actions.

That increment should prove:

- all adapters load sanitized fixtures only in tests;
- every adapter reports `mutates_production_decisions=false`;
- no adapter changes scoring, ranking, filtering, resume selection, tailoring generation, packet generation, queue action, scheduler behavior, RAG retrieval, source behavior, or pipeline execution;
- workflow_runner.py remains dry-run only until a later explicitly approved execution phase.
