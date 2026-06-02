from src.agents import workflow_planner, workflow_registry


EXPECTED_AGENT_KEYS = [
    "source_health",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]


def test_workflow_planner_builds_dry_run_plan_in_registry_order():
    plan = workflow_planner.build_agentic_workflow_execution_plan()
    steps = plan["ordered_steps"]

    assert plan["workflow_name"] == "ApplyLens Agentic Workflow"
    assert plan["planner_version"] == "agentic_workflow_planner_v1"
    assert plan["execution_mode"] == "dry_run"
    assert [step["agent_key"] for step in steps] == EXPECTED_AGENT_KEYS
    assert [step["step_index"] for step in steps] == [1, 2, 3, 4, 5, 6]


def test_workflow_planner_steps_are_planned_and_disabled():
    plan = workflow_planner.build_agentic_workflow_execution_plan()

    for step in plan["ordered_steps"]:
        assert step["execution_enabled"] is False
        assert step["execution_status"] == "planned"
        assert step["mutates_production_decisions"] is False
        assert step["model_provider"] == "deterministic"
        assert step["model_name"]
        assert step["owner_module"].startswith("src.agents.")
        assert step["trace_step_name"] == step["agent_name"]


def test_workflow_planner_dependencies_are_ordered_correctly():
    plan = workflow_planner.build_agentic_workflow_execution_plan()
    deps = {
        step["agent_key"]: step["depends_on_agent_keys"]
        for step in plan["ordered_steps"]
    }

    assert deps["source_health"] == []
    assert deps["resume_match"] == []
    assert deps["critic"] == []
    assert deps["job_prioritization"] == ["source_health"]
    assert deps["tailoring_decision"] == ["job_prioritization"]
    assert deps["operator_review"] == ["job_prioritization", "tailoring_decision"]


def test_workflow_planner_validation_passes():
    plan = workflow_planner.build_agentic_workflow_execution_plan()
    validation = workflow_planner.validate_agentic_workflow_execution_plan(plan)

    assert plan["validation"]["validation_status"] == "passed"
    assert validation["validation_status"] == "passed"
    assert validation["reason_codes"] == []
    assert validation["expected_order"] == EXPECTED_AGENT_KEYS
    assert validation["actual_order"] == EXPECTED_AGENT_KEYS


def test_workflow_planner_validation_catches_out_of_order_dependency():
    plan = workflow_planner.build_agentic_workflow_execution_plan()
    plan["ordered_steps"][0]["depends_on_agent_keys"] = ["operator_review"]

    validation = workflow_planner.validate_agentic_workflow_execution_plan(plan)

    assert validation["validation_status"] == "failed"
    assert "source_health:dependency_not_earlier" in validation["reason_codes"]


def test_workflow_planner_validation_catches_enabled_execution():
    plan = workflow_planner.build_agentic_workflow_execution_plan()
    plan["ordered_steps"][0]["execution_enabled"] = True

    validation = workflow_planner.validate_agentic_workflow_execution_plan(plan)

    assert validation["validation_status"] == "failed"
    assert "source_health:execution_enabled" in validation["reason_codes"]


def test_workflow_planner_validation_catches_undeclared_output_artifact_kind():
    manifest = workflow_registry.get_agentic_workflow_manifest()
    manifest["generated_artifact_kinds"] = [
        kind for kind in manifest["generated_artifact_kinds"]
        if kind != "operator_review_recommendations"
    ]
    plan = workflow_planner.build_agentic_workflow_execution_plan(manifest)

    validation = workflow_planner.validate_agentic_workflow_execution_plan(plan, manifest=manifest)

    assert validation["validation_status"] == "failed"
    assert "operator_review:output_artifact_kind_not_declared" in validation["reason_codes"]


def test_workflow_planner_markdown_includes_all_agent_names():
    markdown = workflow_planner.render_agentic_workflow_execution_plan_markdown()

    assert "# Agentic Workflow Execution Plan" in markdown
    assert "Execution mode: `dry_run`" in markdown
    for agent_name in [
        "Resume Match Agent",
        "Source Health Agent",
        "Critic Agent",
        "Job Prioritization Agent",
        "Tailoring Decision Agent",
        "Operator Review Agent",
    ]:
        assert agent_name in markdown


def test_workflow_planner_writes_execution_plan_artifacts(tmp_path):
    result = workflow_planner.write_agentic_workflow_execution_plan_artifacts(output_dir=tmp_path)

    json_path = tmp_path / "agentic_workflow_execution_plan.json"
    md_path = tmp_path / "agentic_workflow_execution_plan.md"

    assert result["validation_status"] == "passed"
    assert json_path.exists()
    assert md_path.exists()
    assert '"execution_mode": "dry_run"' in json_path.read_text(encoding="utf-8")
    assert "# Agentic Workflow Execution Plan" in md_path.read_text(encoding="utf-8")
