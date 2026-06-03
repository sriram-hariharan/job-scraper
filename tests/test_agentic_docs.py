from pathlib import Path


DOC_PATH = Path("docs/agentic_platform.md")
ORCHESTRATOR_READINESS_DOC_PATH = Path("docs/orchestrator_readiness.md")
READ_ONLY_CHAIN_SMOKE_DOC_PATH = Path("docs/read_only_chain_smoke.md")
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
