from pathlib import Path


DOC_PATH = Path("docs/agentic_platform.md")
ORCHESTRATOR_READINESS_DOC_PATH = Path("docs/orchestrator_readiness.md")
READ_ONLY_CHAIN_SMOKE_DOC_PATH = Path("docs/read_only_chain_smoke.md")
READ_ONLY_CHAIN_OPERATOR_RUNBOOK_DOC_PATH = Path("docs/read_only_chain_operator_runbook.md")
LIVE_ORCHESTRATION_READINESS_GAP_DOC_PATH = Path("docs/live_orchestration_readiness_gap_analysis.md")
PRODUCTION_EXECUTION_CONTRACT_DOC_PATH = Path("docs/production_execution_contract_design.md")
MUTATION_POLICY_APPROVAL_GATE_DOC_PATH = Path("docs/mutation_policy_approval_gate_design.md")
LIVE_RUN_AUDIT_LEDGER_SCHEMA_DOC_PATH = Path("docs/live_run_audit_ledger_schema_design.md")
IDEMPOTENCY_LOCKING_DESIGN_DOC_PATH = Path("docs/idempotency_locking_design.md")
DRY_RUN_EXECUTION_SIMULATOR_DOC_PATH = Path("docs/dry_run_execution_simulator.md")
CONTROLLED_EXECUTION_DECISION_GATE_DOC_PATH = Path("docs/controlled_execution_decision_gate.md")
PORTFOLIO_DOC_PATHS = [
    Path("docs/portfolio_overview.md"),
    Path("docs/architecture_summary.md"),
    Path("docs/demo_walkthrough.md"),
]


def test_agentic_platform_docs_cover_agents_flags_and_commands():
    assert DOC_PATH.exists()
    source = DOC_PATH.read_text(encoding="utf-8")

    for agent_name in [
        "Resume Match Agent",
        "Source Health Agent",
        "Critic Agent",
        "Job Prioritization Agent",
        "Tailoring Decision Agent",
        "Operator Review Agent",
    ]:
        assert agent_name in source

    for flag_name in [
        "APPLYLENS_AGENT_TRACE_ENABLED",
        "APPLYLENS_AGENT_TRACE_STRICT",
        "APPLYLENS_CRITIC_ADVISORY_ENABLED",
        "APPLYLENS_WORKFLOW_VERIFIER_STRICT",
    ]:
        assert flag_name in source

    assert "python -m src.evaluation.agentic_benchmark --no-write --print-summary" in source
    assert "python -m src.evaluation.agentic_benchmark --output-dir outputs/evaluation --print-summary" in source
    assert "python -m src.agents.workflow_verifier --output-dir <artifact_dir>" in source
    assert "python -m src.agents.workflow_verifier --output-dir <artifact_dir> --strict --json" in source
    assert "src/agents/workflow_registry.py" in source
    assert "get_agentic_workflow_manifest()" in source
    assert "validate_agentic_workflow_manifest()" in source
    assert "src/agents/workflow_planner.py" in source
    assert "build_agentic_workflow_execution_plan()" in source
    assert "execution_enabled=false" in source
    assert "src/agents/workflow_runner.py" in source
    assert "python -m src.agents.workflow_runner --dry-run --json" in source
    assert "did_execute=false" in source
    assert "Human Feedback Export" in source
    assert "export_agent_feedback_events()" in source
    assert "build_agent_feedback_evaluation_dataset()" in source
    assert "agent_feedback_export_schema_valid" in source
    assert "RAG Evaluation Dashboard Foundation" in source
    assert "src/evaluation/rag_evaluation.py" in source
    assert "rag_evaluation_schema_valid" in source


def test_agentic_platform_docs_state_safety_guarantees():
    source = DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "No advisory agent overwrites production `action`.",
        "No advisory agent mutates packet generation.",
        "No advisory agent generates resume text.",
        "Human feedback export is read-only and diagnostic.",
        "RAG evaluation is diagnostic/read-only.",
        "The workflow verifier is diagnostic only.",
        "There is no LangGraph integration.",
        "Per-job trace rows are intentionally not implemented yet.",
    ]:
        assert phrase in source


def test_portfolio_demo_docs_cover_phase_18a_contract():
    for doc_path in PORTFOLIO_DOC_PATHS:
        assert doc_path.exists()

    source = "\n".join(path.read_text(encoding="utf-8") for path in PORTFOLIO_DOC_PATHS)

    for phrase in [
        "ApplyLens AI",
        "Agentic Review",
        "src/agents/workflow_registry.py",
        "src/agents/workflow_runner.py",
        "dry-run only",
        "agent feedback export",
        "RAG Evaluation",
        "sanitized/offline fixtures",
        "no production decision mutation",
        "Human feedback is append-only/read-only for evaluation.",
        "RAG Evaluation does not alter retrieval or ranking.",
        "The dry-run runner does not execute agents.",
        "Not Yet Implemented / Roadmap",
        "AI Engineer",
        "Applied AI Engineer",
        "Data Scientist",
        "ML Platform",
        "manual read-only adapter chain",
        "docs/read_only_chain_smoke.md",
        "manual_read_only_adapter_chain",
        "did_mutate_production=false",
        "allow_live_pipeline_wiring=false",
        "allow_application_submission=false",
        "not production",
        "not live orchestration",
        "remains dry-run only",
    ]:
        assert phrase in source

    forbidden_claims = [
        "live orchestration is implemented",
        "automatic application submission is enabled",
        "the app runs the chain automatically",
        "workflow_runner.py executes the chain",
    ]
    lower_source = source.lower()
    for claim in forbidden_claims:
        assert claim.lower() not in lower_source


def test_orchestrator_readiness_docs_cover_phase_19a_contract():
    assert ORCHESTRATOR_READINESS_DOC_PATH.exists()
    source = ORCHESTRATOR_READINESS_DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "dry-run only",
        "There is no autonomous execution in this phase.",
        "No production decision mutation",
        "Future Adapter Contract",
        "This is a proposed contract only.",
        "Human feedback does not tune ranking or scoring.",
        "RAG Evaluation does not change retrieval",
        "No active runner adapter exists.",
        "workflow_runner.py remains dry-run only",
        "src/agents/orchestrator_adapter_harness.py",
        "read_only_preflight",
        "allow_agent_execution=false",
        "executable_adapter_count=0",
        "python -m src.agents.orchestrator_adapter_harness --preflight --json",
        "Future real execution still requires a separate reviewed phase.",
        "src/agents/read_only_job_prioritization_adapter.py",
        "manual read-only adapter prototype",
        "does not update queue action, packet generation, tailoring, scoring, ranking, or production artifacts.",
        "not wired into live planning",
        "does not call other agents",
        "src/agents/read_only_tailoring_decision_adapter.py",
        "does not update queue action, packet generation, tailoring generation, scoring, ranking, or production artifacts.",
        "deterministic Tailoring Decision advisory helpers only",
        "src/agents/read_only_operator_review_adapter.py",
        "does not update queue action, packet generation, tailoring generation, scoring, ranking, application submission, or production artifacts.",
        "deterministic Operator Review advisory helpers only",
        "src/agents/read_only_adapter_chain.py",
        "manual read-only adapter chain",
        "It calls only the existing read-only adapter modules",
        "It is not wired into live planning, the scheduler, UI actions, or `workflow_runner.py`",
        "read_only_adapter_chain_result.json",
        "read_only_adapter_chain_report.md",
        "This does not run the chain",
        "Manual read-only adapter chain artifacts can be displayed in Agentic Review diagnostics",
        "read_only_chain_artifact_generation_result.json",
        "read_only_chain_artifact_generation_report.md",
        "This does not run the generator",
        "displayed in Agentic Review diagnostics",
        "docs/live_orchestration_readiness_gap_analysis.md",
        "planning-only and does not enable live orchestration",
        "docs/production_execution_contract_design.md",
        "design-only and does not enable live orchestration",
        "docs/mutation_policy_approval_gate_design.md",
        "design-only and does not enable mutation execution",
        "docs/live_run_audit_ledger_schema_design.md",
        "design/schema proposal-only and does not enable persistence",
        "docs/idempotency_locking_design.md",
        "design-only and does not add lock tables",
        "docs/dry_run_execution_simulator.md",
        "explicit/manual and diagnostic-only",
        "does not run the chain/generator",
        "Operator Approval Mock",
        "read-only and non-actionable",
    ]:
        assert phrase in source

    for agent_key in [
        "source_health",
        "resume_match",
        "critic",
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
    ]:
        assert f"`{agent_key}`" in source

    for status in [
        "ready_for_read_only_orchestrator",
        "needs_adapter",
    ]:
        assert status in source


def test_read_only_chain_smoke_docs_cover_manual_fixture_contract():
    assert READ_ONLY_CHAIN_SMOKE_DOC_PATH.exists()
    source = READ_ONLY_CHAIN_SMOKE_DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv",
        "python -m src.agents.read_only_adapter_chain",
        "python -m src.agents.read_only_chain_artifact_generator",
        "--queue-input tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv",
        "read_only_adapter_chain_result.json",
        "read_only_adapter_chain_report.md",
        "read_only_chain_artifact_generation_result.json",
        "read_only_chain_artifact_generation_report.md",
        "job_prioritization/job_prioritization_read_only_adapter_recommendations.csv",
        "tailoring_decision/tailoring_decision_read_only_adapter_decisions.csv",
        "operator_review/operator_review_read_only_adapter_reviews.csv",
        "requires both `--queue-input` and `--output-dir`",
        "refuses to run without an explicit queue input and explicit output directory",
        "This fixture does not run automatically.",
        "This fixture is not production data.",
        "not wired into live planning",
        "`workflow_runner.py` remains dry-run only.",
        "executable_adapter_count=0",
        "does not implement real orchestration",
        "automated application submission",
    ]:
        assert phrase in source

    forbidden_claims = [
        "real orchestration is implemented",
        "agents run automatically",
        "live pipeline uses the chain",
        "LangGraph is integrated",
        "feedback tunes scoring",
        "RAG evaluation changes retrieval",
        "application submission is automated",
    ]
    lower_source = source.lower()
    for claim in forbidden_claims:
        assert claim.lower() not in lower_source


def test_read_only_chain_operator_runbook_covers_manual_generator_contract():
    assert READ_ONLY_CHAIN_OPERATOR_RUNBOOK_DOC_PATH.exists()
    source = READ_ONLY_CHAIN_OPERATOR_RUNBOOK_DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "docs/read_only_chain_operator_runbook.md",
        "--queue-input",
        "--output-dir",
        "explicit/manual only",
        "read-only",
        "not live orchestration",
        "No application submission.",
        "No queue update.",
        "No tailoring generation.",
        "No packet generation.",
        "No scoring or ranking change.",
        "No database write.",
        "No live planning.",
        "No `workflow_runner.py` execution.",
        "No scheduler or background run.",
        "workflow_runner.py` remains dry-run only",
        "executable_adapter_count=0",
        "missing_explicit_queue_input",
        "missing_explicit_output_dir",
        "queue_input_artifact_not_found",
        "Agentic Review",
        "does not run the generator automatically",
    ]:
        assert phrase in source

    linked_docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            READ_ONLY_CHAIN_SMOKE_DOC_PATH,
            Path("docs/demo_walkthrough.md"),
            ORCHESTRATOR_READINESS_DOC_PATH,
            Path("README.md"),
        ]
    )
    assert "docs/read_only_chain_operator_runbook.md" in linked_docs

    forbidden_claims = [
        "live orchestration is implemented",
        "autonomous execution is implemented",
        "scheduler runs the chain",
        "ui runs the generator",
        "LangGraph is integrated",
        "feedback tunes scoring",
        "application submission is automated",
    ]
    lower_source = source.lower()
    for claim in forbidden_claims:
        assert claim.lower() not in lower_source


def test_live_orchestration_readiness_gap_analysis_covers_phase_33a_contract():
    assert LIVE_ORCHESTRATION_READINESS_GAP_DOC_PATH.exists()
    source = LIVE_ORCHESTRATION_READINESS_GAP_DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "docs/live_orchestration_readiness_gap_analysis.md",
        "No live orchestration.",
        "workflow_runner.py` remains dry-run only",
        "executable_adapter_count=0",
        "No production queue mutation.",
        "No application submission automation.",
        "operator approval gate",
        "rollback mechanism",
        "idempotent production execution contract",
        "audit ledger",
        "feature flags",
        "dry-run-to-live promotion gate",
        "per-agent production adapter contracts",
        "34A: production execution contract design doc only.",
        "35A: mutation policy and approval gate design doc only.",
        "36A: live-run audit ledger schema proposal only.",
        "37A: idempotency/locking design doc only.",
        "docs/idempotency_locking_design.md",
        "38A: dry-run execution simulator, still no mutation.",
        "docs/dry_run_execution_simulator.md",
        "39A: operator approval UI mock/read-only only.",
        "40A: controlled execution decision gate only.",
        "docs/controlled_execution_decision_gate.md",
        "40B+: only consider proposal-only safety scaffolding",
        "No queue mutation.",
        "No scoring/ranking changes.",
        "docs/production_execution_contract_design.md",
        "docs/mutation_policy_approval_gate_design.md",
        "docs/live_run_audit_ledger_schema_design.md",
        "docs/idempotency_locking_design.md",
    ]:
        assert phrase in source

    for section in [
        "## What Exists Today",
        "## What Does Not Exist Yet",
        "## Required Gaps Before Live Orchestration",
        "### Execution Architecture",
        "### Safety Gates",
        "### Mutation Policy",
        "### Approval Workflow",
        "### Rollback/Recovery",
        "### Observability/Audit Logging",
        "### Idempotency and Locking",
        "### Artifact/Version Compatibility",
        "### UI/Operator Controls",
        "### Test Strategy",
        "### Deployment/Feature Flag Strategy",
        "## Proposed Future Milestones",
        "## Hard Blockers",
        "## Non-Goals",
    ]:
        assert section in source

    linked_docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ORCHESTRATOR_READINESS_DOC_PATH,
            Path("README.md"),
            DRY_RUN_EXECUTION_SIMULATOR_DOC_PATH,
        ]
    )
    assert "docs/live_orchestration_readiness_gap_analysis.md" in linked_docs


def test_dry_run_execution_simulator_docs_cover_phase_38a_contract():
    assert DRY_RUN_EXECUTION_SIMULATOR_DOC_PATH.exists()
    source = DRY_RUN_EXECUTION_SIMULATOR_DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "docs/dry_run_execution_simulator.md",
        "explicit/manual dry-run execution simulator only",
        "consumes existing diagnostic artifacts",
        "Does not run the chain/generator.",
        "Does not run agents.",
        "does not mutate production",
        "No DB write.",
        "No queue mutation.",
        "No application submission.",
        "No tailoring generation.",
        "No packet generation.",
        "No scoring/ranking changes.",
        "`workflow_runner.py` remains dry-run only",
        "executable_adapter_count=0",
        "read_only_adapter_chain_result.json",
        "read_only_chain_artifact_generation_result.json",
        "dry_run_execution_simulation_result.json",
        "dry_run_execution_simulation_report.md",
        "application_execution_queue.csv",
        "job_prioritization_recommendations.csv",
        "tailoring_decision_recommendations.csv",
        "operator_review_recommendations.csv",
        "simulated_mutation_proposals",
        "proposal_mode=simulated_non_executable",
        "can_execute_live=false",
        "requires_approval=true",
        "blocked_by_default=true",
        "queue_diagnostic_status_marker",
        "operator_note",
        "artifact_status_marker",
        "operator approval gate",
        "audit ledger",
        "idempotency key",
        "execution lock",
        "rollback plan",
        "Does not call `run_read_only_adapter_chain()`",
        "Does not call `generate_read_only_chain_artifacts()`",
        "Is not wired into `run_application_planning.py`",
        "Is not wired into `application_execution_queue.py`",
        "No DB schema, migration, storage, or persistence implementation.",
        "No runtime/pipeline behavior changes.",
        "Agentic Review can show",
        "Operator Approval Mock",
        "read-only and non-actionable",
        "does not approve, reject, store approval, mutate queue state, write to the database, submit applications, execute anything, call approval APIs, call mutation APIs, or add approval storage.",
        "Future real approval requires a separate approved phase",
    ]:
        assert phrase in source

    for section in [
        "## Current Boundary",
        "## Safety Guarantees",
        "## Agentic Review Display",
        "## CLI",
        "## Simulation Payload",
        "## Validation Rules",
        "## Non-Goals",
        "## Relationship To Future Milestones",
    ]:
        assert section in source

    linked_docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            LIVE_ORCHESTRATION_READINESS_GAP_DOC_PATH,
            ORCHESTRATOR_READINESS_DOC_PATH,
            Path("README.md"),
        ]
    )
    assert "docs/dry_run_execution_simulator.md" in linked_docs


def test_controlled_execution_decision_gate_covers_phase_40a_contract():
    assert CONTROLLED_EXECUTION_DECISION_GATE_DOC_PATH.exists()
    source = CONTROLLED_EXECUTION_DECISION_GATE_DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "docs/controlled_execution_decision_gate.md",
        "decision gate only",
        "no live execution enabled",
        "no mutation enabled",
        "no approval API/storage enabled",
        "no DB writes",
        "`workflow_runner.py` remains dry-run only",
        "executable_adapter_count=0",
        "Live mutation: `NO_GO`",
        "Application submission automation: `NO_GO`",
        "Queue mutation: `NO_GO`",
        "Approval UI/action: `NO_GO`",
        "DB-backed audit ledger implementation: `NOT YET`",
        "Proposal-only mutation planner: `LIMITED_GO`",
        "Live pipeline execution",
        "Queue action mutation",
        "Application submission",
        "DB-backed audit ledger",
        "Approval API/storage",
        "Lock/idempotency store",
        "Read-only approval review UI",
        "Dry-run simulator enhancement",
        "Implemented audit ledger storage missing.",
        "Implemented approval storage/API missing.",
        "Implemented idempotency store missing.",
        "Implemented execution lock store missing.",
        "Rollback implementation missing.",
        "Mutation transaction boundary missing.",
        "Feature flag/environment gate implementation missing.",
        "Operator approval workflow missing.",
        "Failure recovery tests missing.",
        "Production dry-run-to-live promotion policy missing.",
        "No reviewed mutation API contract implemented.",
        "40B: proposal-only mutation planner design or utility, no mutation.",
        "41A: audit ledger storage implementation design review, no migration yet.",
        "42A: idempotency/lock storage implementation design review, no migration yet.",
        "43A: approval API/storage design review, no implementation yet.",
        "44A: read-only approval review UI mock v2, no actions.",
        "45A+: only after approved storage designs, consider migrations behind feature flags.",
        "No live execution in this phase.",
        "No queue updates.",
        "No application submission.",
        "No approval/reject buttons.",
        "No DB writes.",
        "No scheduler.",
        "No agent framework integration.",
        "Do not start live execution.",
        "Build a proposal-only mutation planner next, or finish storage design reviews first.",
        "code must stay explicit/manual and write diagnostic artifacts only",
    ]:
        assert phrase in source

    for section in [
        "## Current State",
        "## Current Hard Safety Boundary",
        "## Decision",
        "## Decision Matrix",
        "## Blockers Before Live Mutation",
        "## Allowed Next Phases",
        "## Explicit Non-Goals",
        "## Recommended Next Step",
    ]:
        assert section in source

    linked_docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            LIVE_ORCHESTRATION_READINESS_GAP_DOC_PATH,
            ORCHESTRATOR_READINESS_DOC_PATH,
            Path("README.md"),
        ]
    )
    assert "docs/controlled_execution_decision_gate.md" in linked_docs


def test_production_execution_contract_design_covers_phase_34a_contract():
    assert PRODUCTION_EXECUTION_CONTRACT_DOC_PATH.exists()
    source = PRODUCTION_EXECUTION_CONTRACT_DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "docs/production_execution_contract_design.md",
        "Phase 34A is design only.",
        "No implementation in this phase",
        "No live execution is enabled.",
        "`workflow_runner.py` remains dry-run only",
        "executable_adapter_count=0",
        "execution_request",
        "execution_plan",
        "mutation_proposal",
        "approval_record",
        "execution_attempt",
        "execution_result",
        "rollback_plan",
        "audit_ledger_entry",
        "idempotency_key",
        "execution_lock",
        "No mutation without an approved mutation proposal.",
        "No application submission",
        "rollback plan",
        "feature flag",
        "Queue diagnostic status update.",
        "Operator-approved queue action update.",
        "Artifact status marker.",
        "Do NOT allow application submission yet.",
        "Application submission.",
        "Resume rewriting.",
        "Tailoring generation.",
        "Packet generation.",
        "Scoring formula changes.",
        "Ranking changes.",
        "Scraper/source mutation.",
        "RAG corpus mutation.",
        "Deletion of production records.",
        "Partial mutation",
        "Duplicate execution",
        "Stale artifact versions",
        "Missing approval",
        "Expired approval",
        "Lock collision",
        "Validation failure",
        "Artifact write failure",
        "Rollback failure",
        "must not execute mutations directly",
        "Mutation policy design.",
        "Approval gate design.",
        "Audit ledger schema.",
        "Idempotency/locking design.",
        "Dry-run simulator.",
        "Read-only approval UI mock.",
        "Feature flag policy.",
        "Operator runbook update.",
        "docs/mutation_policy_approval_gate_design.md",
        "docs/live_run_audit_ledger_schema_design.md",
        "docs/idempotency_locking_design.md",
    ]:
        assert phrase in source

    for section in [
        "## Purpose",
        "## Current Boundary",
        "## Future Execution Contract Entities",
        "## Execution Request Contract",
        "## Execution Plan Contract",
        "## Mutation Proposal Contract",
        "## Approval Contract",
        "## Execution Result Contract",
        "## Safety Invariants",
        "## Allowed Future Mutation Types",
        "## Forbidden Mutation Types for First Live Prototype",
        "## Failure Modes and Rollback Requirements",
        "## Compatibility With Current Read-Only Chain",
        "## Future Implementation Gates",
    ]:
        assert section in source

    linked_docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            LIVE_ORCHESTRATION_READINESS_GAP_DOC_PATH,
            ORCHESTRATOR_READINESS_DOC_PATH,
            Path("README.md"),
        ]
    )
    assert "docs/production_execution_contract_design.md" in linked_docs


def test_mutation_policy_approval_gate_design_covers_phase_35a_contract():
    assert MUTATION_POLICY_APPROVAL_GATE_DOC_PATH.exists()
    source = MUTATION_POLICY_APPROVAL_GATE_DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "docs/mutation_policy_approval_gate_design.md",
        "Phase 35A is design only.",
        "No implementation in this phase",
        "No live execution is enabled.",
        "No mutation is enabled.",
        "No approval API/UI/storage is implemented.",
        "`workflow_runner.py` remains dry-run only",
        "executable_adapter_count=0",
        "## Mutation Classification",
        "forbidden_mutation",
        "approval_required_mutation",
        "diagnostic_artifact_write",
        "read_only_observation",
        "operator_note",
        "future_deferred_mutation",
        "## Approval Gate Contract",
        "approval_id",
        "mutation_ids",
        "requested_by",
        "approved_by",
        "approval_status",
        "approval_scope",
        "required_evidence_refs",
        "approved_mutation_types",
        "blocked_mutation_types",
        "idempotency_key",
        "audit_ledger_ref",
        "## Approval States",
        "draft",
        "pending_review",
        "approved",
        "rejected",
        "expired",
        "revoked",
        "consumed",
        "blocked_by_policy",
        "## Evidence Required Before Approval",
        "before_value",
        "proposed_after_value",
        "source_agent_key",
        "reason_codes",
        "evidence_refs",
        "validation_status",
        "rollback_strategy",
        "artifact_version_refs",
        "Operator-visible summary.",
        "Risk classification.",
        "## Policy Evaluation Order",
        "Feature flag and environment gate.",
        "Mutation type allow/deny list.",
        "Required evidence presence.",
        "Idempotency key presence.",
        "Lock availability.",
        "Approval state/scope/expiry.",
        "Rollback requirement.",
        "Audit ledger write readiness.",
        "Final pre-execution validation.",
        "No application submission is allowed by this policy.",
        "No mutation without approval can pass this order.",
        "audit ledger",
        "idempotency key",
        "execution lock",
        "Application submission.",
        "Resume rewriting.",
        "Tailoring generation.",
        "Packet generation.",
        "Scoring formula changes.",
        "Ranking changes.",
        "Scraper/source mutation.",
        "RAG corpus mutation.",
        "Deletion of production records.",
        "Credential/token mutation.",
        "User profile mutation.",
        "Hidden scheduler/background execution.",
        "Mutation without before/after capture.",
        "Mutation without approval.",
        "Mutation without audit ledger entry.",
        "Mutation without idempotency key.",
        "Mutation without execution lock.",
        "Mutation without rollback plan where rollback is possible.",
        "can become evidence for future mutation proposals, but cannot directly mutate anything",
        "Audit ledger schema design.",
        "Idempotency/locking design.",
        "Dry-run mutation simulator.",
        "Read-only approval UI mock.",
        "Feature flag and environment gate policy.",
        "Rollback design.",
        "Approval API/storage design.",
        "Operator runbook update.",
        "docs/live_run_audit_ledger_schema_design.md",
    ]:
        assert phrase in source

    for section in [
        "## Purpose",
        "## Current State",
        "## Mutation Classification",
        "## Allowed First-Phase Mutation Proposals",
        "## Explicitly Forbidden Mutations",
        "## Approval Gate Contract",
        "## Approval States",
        "## Approval Scope",
        "## Evidence Required Before Approval",
        "## Human Review Checklist",
        "## Policy Evaluation Order",
        "## Failure And Denial Behavior",
        "## Audit And Trace Requirements",
        "## Relationship To Current Read-Only Chain",
        "## Future Implementation Gates",
    ]:
        assert section in source

    linked_docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            PRODUCTION_EXECUTION_CONTRACT_DOC_PATH,
            LIVE_ORCHESTRATION_READINESS_GAP_DOC_PATH,
            ORCHESTRATOR_READINESS_DOC_PATH,
            Path("README.md"),
        ]
    )
    assert "docs/mutation_policy_approval_gate_design.md" in linked_docs


def test_live_run_audit_ledger_schema_design_covers_phase_36a_contract():
    assert LIVE_RUN_AUDIT_LEDGER_SCHEMA_DOC_PATH.exists()
    source = LIVE_RUN_AUDIT_LEDGER_SCHEMA_DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "docs/live_run_audit_ledger_schema_design.md",
        "design/schema proposal only",
        "No DB table or migration is added.",
        "No live execution is enabled.",
        "No mutation is enabled.",
        "No approval API/UI/storage is implemented.",
        "`workflow_runner.py` remains dry-run only",
        "executable_adapter_count=0",
        "future immutable audit trail",
        "No live orchestration.",
        "No scheduler/background execution.",
        "No UI run button.",
        "No DB write for live orchestration.",
        "No queue mutation.",
        "No application submission.",
        "No scoring/ranking changes.",
        "agentic_execution_requests",
        "agentic_execution_plans",
        "agentic_mutation_proposals",
        "agentic_approval_records",
        "agentic_execution_attempts",
        "agentic_audit_ledger_entries",
        "agentic_rollback_plans",
        "agentic_execution_locks",
        "before_value_json",
        "after_value_json",
        "proposed_after_value_json",
        "idempotency_key",
        "execution_lock_key",
        "execution_request_created",
        "mutation_proposed",
        "approval_approved",
        "mutation_applied",
        "rollback_succeeded",
        "policy_denied",
        "pending",
        "approved",
        "blocked",
        "running",
        "succeeded",
        "failed",
        "rolled_back",
        "rollback_failed",
        "Every mutation proposal links to `request_id` and `plan_id`.",
        "Every approval links to `mutation_ids` or an explicit approval scope.",
        "Every execution attempt links to `approval_id` when mutation-capable.",
        "Every mutable target includes `execution_lock_key`.",
        "block mutation if ledger unavailable",
        "must not write ledger rows directly in this phase",
        "Idempotency/locking design.",
        "DB migration design.",
        "Storage API design.",
        "Ledger write transaction design.",
        "Read-only ledger viewer mock.",
        "Failure-mode tests.",
        "docs/idempotency_locking_design.md",
    ]:
        assert phrase in source

    for section in [
        "## Purpose",
        "## Current Boundary",
        "## Ledger Design Principles",
        "## Proposed Tables/Entities",
        "## `agentic_audit_ledger_entries` Fields",
        "## Event Types",
        "## Status Values",
        "## Linkage Rules",
        "## Retention And Privacy",
        "## Query Examples",
        "## Failure Behavior",
        "## Relationship To Current Read-Only Chain",
        "## Future Gates",
    ]:
        assert section in source

    linked_docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            PRODUCTION_EXECUTION_CONTRACT_DOC_PATH,
            MUTATION_POLICY_APPROVAL_GATE_DOC_PATH,
            LIVE_ORCHESTRATION_READINESS_GAP_DOC_PATH,
            ORCHESTRATOR_READINESS_DOC_PATH,
            Path("README.md"),
        ]
    )
    assert "docs/live_run_audit_ledger_schema_design.md" in linked_docs


def test_idempotency_locking_design_covers_phase_37a_contract():
    assert IDEMPOTENCY_LOCKING_DESIGN_DOC_PATH.exists()
    source = IDEMPOTENCY_LOCKING_DESIGN_DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "docs/idempotency_locking_design.md",
        "Phase 37A is design only.",
        "No implementation in this phase",
        "No lock table or migration is added.",
        "No idempotency store is added.",
        "No runtime lock checks are added.",
        "No live execution is enabled.",
        "No mutation is enabled.",
        "`workflow_runner.py` remains dry-run only",
        "executable_adapter_count=0",
        "read-only adapters",
        "manual read-only chain",
        "explicit generator",
        "diagnostic artifacts only",
        "No DB write.",
        "No queue mutation.",
        "No application submission.",
        "No live orchestration.",
        "No idempotency enforcement.",
        "No execution locking.",
        "Every future execution request must have a stable idempotency key.",
        "Retries must return the prior result or block duplicate mutation.",
        "Same key plus same payload must be safe.",
        "Same key plus different payload must be rejected.",
        "Mutation idempotency must be scoped to target and mutation type.",
        "Idempotency records must link to audit ledger entries.",
        "Idempotency must be checked before approval consumption and before mutation attempt.",
        "No application submission can be retried without separate submission-specific idempotency policy.",
        "Every mutable target requires an execution lock.",
        "Locks must be scoped narrowly",
        "owner/run identity",
        "TTL/expiry",
        "Stale locks require safe recovery.",
        "Lock acquisition must occur before mutation execution.",
        "Lock release must be audited.",
        "Lock collision must block mutation and produce diagnostic output.",
        "No global broad lock for the first prototype unless explicitly approved.",
        "execution_request",
        "execution_plan",
        "mutation_proposal",
        "approval_consumption",
        "mutation_attempt",
        "rollback_attempt",
        "owner_user_id",
        "pipeline_run_id",
        "target_type",
        "target_id",
        "mutation_type",
        "source_agent_key",
        "artifact_version_hash",
        "proposed_after_value_hash",
        "approval_id",
        "pipeline_run_lock",
        "job_target_lock",
        "queue_row_lock",
        "artifact_status_lock",
        "approval_consumption_lock",
        "rollback_lock",
        "requested",
        "acquired",
        "renewed",
        "released",
        "expired",
        "force_released",
        "blocked",
        "reserved",
        "running",
        "succeeded",
        "failed_retryable",
        "failed_terminal",
        "duplicate_replayed",
        "duplicate_conflict",
        "Duplicate request same payload",
        "Duplicate request different payload",
        "Concurrent mutation on same queue row",
        "Concurrent rollback for same mutation",
        "Stale approval consumption",
        "Stale artifact version",
        "Lock unavailable",
        "Lock expired mid-run",
        "Idempotency store unavailable",
        "No mutation without idempotency key.",
        "No mutation without execution lock.",
        "No approval consumption without idempotency record.",
        "No retry can apply same mutation twice.",
        "No application submission without separate submission idempotency design.",
        "No live execution if lock store unavailable.",
        "No live execution if idempotency store unavailable.",
        "No lock bypass in production.",
        "All lock/idempotency decisions must link to audit ledger entries.",
        "Future idempotency reservations should write ledger events",
        "Future lock acquire/release decisions should write ledger events",
        "Future duplicate replay/conflict outcomes should write ledger events",
        "The current phase does not write ledger rows",
        "Approval consumption must be idempotent.",
        "Consumed approvals cannot be reused.",
        "Approval scope mismatch blocks lock acquisition.",
        "Expired or revoked approval blocks idempotency reservation.",
        "The chain/generator remains diagnostic only.",
        "The smoke fixture and roundtrip tests do not require locks.",
        "Future proposal artifacts may include calculated keys, but not enforce in this phase.",
        "DB schema/migration design for idempotency records and locks.",
        "Storage API design.",
        "Transaction boundary design.",
        "Lock TTL/recovery design.",
        "Audit ledger integration design.",
        "Dry-run simulator.",
        "Failure-mode tests.",
        "Operator runbook update.",
    ]:
        assert phrase in source

    for section in [
        "## Purpose",
        "## Current Boundary",
        "## Idempotency Principles",
        "## Locking Principles",
        "## Proposed Idempotency Key Structure",
        "## Proposed Lock Scopes",
        "## Lock Lifecycle",
        "## Idempotency Record Lifecycle",
        "## Collision And Duplicate Behavior",
        "## Safety Invariants",
        "## Relationship To Audit Ledger",
        "## Relationship To Approval Gate",
        "## Relationship To Current Read-Only Chain",
        "## Future Implementation Gates",
    ]:
        assert section in source

    linked_docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            LIVE_RUN_AUDIT_LEDGER_SCHEMA_DOC_PATH,
            MUTATION_POLICY_APPROVAL_GATE_DOC_PATH,
            PRODUCTION_EXECUTION_CONTRACT_DOC_PATH,
            LIVE_ORCHESTRATION_READINESS_GAP_DOC_PATH,
            ORCHESTRATOR_READINESS_DOC_PATH,
            Path("README.md"),
        ]
    )
    assert "docs/idempotency_locking_design.md" in linked_docs
