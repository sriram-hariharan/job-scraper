from src.agents import workflow_registry


EXPECTED_AGENT_KEYS = [
    "source_health",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]


def test_workflow_registry_lists_all_implemented_agents_in_stable_order():
    manifest = workflow_registry.get_agentic_workflow_manifest()

    assert manifest["workflow_name"] == "ApplyLens Agentic Workflow"
    assert manifest["workflow_version"] == "agentic_workflow_manifest_v1"
    assert manifest["ordered_agent_keys"] == EXPECTED_AGENT_KEYS
    assert [agent["agent_key"] for agent in workflow_registry.list_agentic_agents()] == EXPECTED_AGENT_KEYS


def test_workflow_registry_agent_metadata_is_complete_and_safe():
    for agent in workflow_registry.list_agentic_agents():
        assert agent["agent_name"]
        assert agent["agent_version"]
        assert agent["model_provider"] == "deterministic"
        assert agent["model_name"]
        assert agent["owner_module"].startswith("src.agents.")
        assert agent["advisory_only"] is True
        assert agent["diagnostic_only"] is False
        assert agent["trace_enabled_by_default"] is False
        assert agent["mutates_production_decisions"] is False
        assert agent["input_artifacts"]
        assert agent["output_artifacts"]
        assert agent["benchmark_metric_keys"]


def test_workflow_registry_required_flags_and_artifact_kinds_are_present():
    manifest = workflow_registry.get_agentic_workflow_manifest()

    for flag_name in [
        "APPLYLENS_AGENT_TRACE_ENABLED",
        "APPLYLENS_AGENT_TRACE_STRICT",
        "APPLYLENS_CRITIC_ADVISORY_ENABLED",
        "APPLYLENS_WORKFLOW_VERIFIER_STRICT",
    ]:
        assert flag_name in manifest["feature_flags"]

    for artifact_kind in [
        "source_health_report",
        "job_prioritization_recommendations",
        "tailoring_decision_recommendations",
        "tailoring_decision_summary",
        "operator_review_recommendations",
        "operator_review_summary",
        "agentic_workflow_summary_json",
        "agentic_workflow_summary_md",
        "agentic_workflow_verification_json",
    ]:
        assert artifact_kind in manifest["generated_artifact_kinds"]


def test_workflow_registry_validation_passes():
    validation = workflow_registry.validate_agentic_workflow_manifest()

    assert validation["validation_status"] == "passed"
    assert validation["reason_codes"] == []
    assert validation["agent_count"] == 6
    assert validation["ordered_agent_count"] == 6
    assert "job_priority_accuracy" in validation["benchmark_metric_keys"]
    assert "operator_review_accuracy" in validation["benchmark_metric_keys"]


def test_workflow_registry_validation_catches_mutating_agent():
    manifest = workflow_registry.get_agentic_workflow_manifest()
    manifest["agents"]["resume_match"]["mutates_production_decisions"] = True

    validation = workflow_registry.validate_agentic_workflow_manifest(manifest)

    assert validation["validation_status"] == "failed"
    assert "resume_match:mutates_production_decisions" in validation["reason_codes"]


def test_workflow_registry_markdown_includes_all_agent_names():
    markdown = workflow_registry.render_agentic_workflow_manifest_markdown()

    assert "# Agentic Workflow Manifest" in markdown
    for agent_name in [
        "Resume Match Agent",
        "Source Health Agent",
        "Critic Agent",
        "Job Prioritization Agent",
        "Tailoring Decision Agent",
        "Operator Review Agent",
    ]:
        assert agent_name in markdown
