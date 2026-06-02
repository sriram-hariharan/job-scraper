from pathlib import Path


DOC_PATH = Path("docs/agentic_platform.md")


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


def test_agentic_platform_docs_state_safety_guarantees():
    source = DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "No advisory agent overwrites production `action`.",
        "No advisory agent mutates packet generation.",
        "No advisory agent generates resume text.",
        "The workflow verifier is diagnostic only.",
        "There is no LangGraph integration.",
        "Per-job trace rows are intentionally not implemented yet.",
    ]:
        assert phrase in source
