from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.agents import canonical_registry, workflow_registry
from src.agents import evidence_chain_composition
from src.agents import evidence_chain_langgraph_harness


EXPECTED_CANONICAL_KEYS = (
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
)
EXPECTED_OWNER_MODULES = {
    "critic": "src.agents.critic_agent",
    "job_prioritization": "src.agents.job_prioritization_agent",
    "tailoring_decision": "src.agents.tailoring_decision_agent",
    "operator_review": "src.agents.operator_review_agent",
}
EXPECTED_HISTORICAL_WORKFLOW_KEYS = [
    "source_health",
    "resume_match",
    *EXPECTED_CANONICAL_KEYS,
]
EXPECTED_WORKFLOW_SCHEMA = {
    "workflow_name",
    "workflow_version",
    "ordered_agent_keys",
    "artifact_dependency_order",
    "safety_guarantees",
    "feature_flags",
    "generated_artifact_kinds",
    "agents",
}
EXPECTED_WORKFLOW_AGENT_SCHEMA = {
    "agent_key",
    "agent_name",
    "agent_version",
    "model_provider",
    "model_name",
    "phase",
    "advisory_only",
    "diagnostic_only",
    "trace_enabled_by_default",
    "mutates_production_decisions",
    "input_artifacts",
    "output_artifacts",
    "required_feature_flags",
    "benchmark_metric_keys",
    "owner_module",
}
NON_CANONICAL_RESPONSIBILITIES = {
    "source_health",
    "job_discovery",
    "jd_intelligence",
    "relevance_prefilter",
    "resume_match",
    "application_scoring",
    "tailoring_writer",
    "tailoring_judge",
    "rag",
}
MUTATION_FIELDS = (
    "score_mutation",
    "rank_mutation",
    "queue_mutation",
    "resume_text_mutation",
    "operator_state_persistence",
    "application_action_capability",
)


def test_canonical_registry_has_exact_keys_order_and_owner_modules():
    definitions = canonical_registry.list_canonical_agent_definitions()

    assert canonical_registry.CANONICAL_AGENT_KEYS == EXPECTED_CANONICAL_KEYS
    assert tuple(definition.key for definition in definitions) == EXPECTED_CANONICAL_KEYS
    assert {
        definition.key: definition.owner_module
        for definition in definitions
    } == EXPECTED_OWNER_MODULES
    assert set(canonical_registry.CANONICAL_AGENT_DEFINITIONS_BY_KEY) == set(
        EXPECTED_CANONICAL_KEYS
    )


def test_canonical_registry_is_immutable_and_returns_read_only_definitions():
    definitions = canonical_registry.list_canonical_agent_definitions()
    critic = canonical_registry.get_canonical_agent_definition("critic")

    assert isinstance(definitions, tuple)
    assert definitions is canonical_registry.CANONICAL_AGENT_DEFINITIONS
    with pytest.raises(FrozenInstanceError):
        critic.display_name = "Changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        canonical_registry.CANONICAL_AGENT_DEFINITIONS_BY_KEY["critic"] = critic  # type: ignore[index]
    with pytest.raises(KeyError):
        canonical_registry.get_canonical_agent_definition("resume_match")


def test_canonical_registry_excludes_pipeline_tools_and_historical_entries():
    assert set(EXPECTED_CANONICAL_KEYS).isdisjoint(NON_CANONICAL_RESPONSIBILITIES)
    assert "source_health" not in canonical_registry.CANONICAL_AGENT_KEYS
    assert "resume_match" not in canonical_registry.CANONICAL_AGENT_KEYS


def test_canonical_agents_are_advisory_and_have_no_mutation_or_action_capability():
    for definition in canonical_registry.CANONICAL_AGENT_DEFINITIONS:
        assert definition.deterministic_core is True
        assert definition.advisory_only is True
        for field_name in MUTATION_FIELDS:
            assert getattr(definition, field_name) is False

    critic = canonical_registry.get_canonical_agent_definition("critic")
    assert critic.llm_capable is True
    assert critic.optional_controlled_llm_guardrail is True
    for key in EXPECTED_CANONICAL_KEYS[1:]:
        definition = canonical_registry.get_canonical_agent_definition(key)
        assert definition.llm_capable is False
        assert definition.optional_controlled_llm_guardrail is False


def test_operator_review_requires_human_approval():
    operator_review = canonical_registry.get_canonical_agent_definition(
        "operator_review"
    )

    assert operator_review.human_approval_required is True
    assert operator_review.operator_state_persistence is False
    assert operator_review.application_action_capability is False


def test_historical_workflow_registry_preserves_six_entry_order_and_schema():
    manifest = workflow_registry.get_agentic_workflow_manifest()

    assert workflow_registry.ORDERED_AGENT_KEYS == EXPECTED_HISTORICAL_WORKFLOW_KEYS
    assert manifest["ordered_agent_keys"] == EXPECTED_HISTORICAL_WORKFLOW_KEYS
    assert list(manifest["agents"]) == EXPECTED_HISTORICAL_WORKFLOW_KEYS
    assert set(manifest) == EXPECTED_WORKFLOW_SCHEMA
    for agent in manifest["agents"].values():
        assert set(agent) == EXPECTED_WORKFLOW_AGENT_SCHEMA

    for key in EXPECTED_CANONICAL_KEYS:
        canonical = canonical_registry.get_canonical_agent_definition(key)
        historical = manifest["agents"][key]
        assert historical["agent_key"] == canonical.key
        assert historical["agent_name"] == canonical.display_name
        assert historical["owner_module"] == canonical.owner_module


def test_evidence_chain_decision_agent_suffix_matches_canonical_order():
    assert tuple(evidence_chain_composition.ORDERED_AGENT_KEYS[-4:]) == (
        EXPECTED_CANONICAL_KEYS
    )
    assert tuple(evidence_chain_langgraph_harness.ARTIFACT_KEYS_BY_AGENT)[-4:] == (
        EXPECTED_CANONICAL_KEYS
    )


def test_canonical_registry_imports_no_runtime_or_side_effect_modules():
    source_path = Path(canonical_registry.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.add(node.module or "")

    assert imported_modules == {"__future__", "dataclasses", "types", "typing"}
    assert not any(
        module.startswith(("src.", "langgraph", "psycopg", "sqlalchemy"))
        for module in imported_modules
    )

    forbidden_import_time_calls = {
        "open",
        "write_text",
        "write_bytes",
        "connect",
        "execute",
        "invoke",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "StateGraph",
    }
    import_time_calls = set()
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(statement):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    import_time_calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    import_time_calls.add(node.func.attr)

    assert import_time_calls.isdisjoint(forbidden_import_time_calls)
