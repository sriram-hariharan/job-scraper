from __future__ import annotations

import inspect
from dataclasses import asdict, fields
from pathlib import Path

from src.agents import canonical_registry
from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
OVERVIEW_PATH = "/profile/admin/agentic-operations/overview"
MODEL_PATH = ROOT / "frontend/executive-kpi/src/agentic/agenticOperationsModel.ts"
COMPONENT_PATH = (
    ROOT
    / "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.tsx"
)

CANONICAL_FIELDS = (
    "key",
    "display_name",
    "owner_module",
    "responsibility",
    "deterministic_core",
    "llm_capable",
    "optional_controlled_llm_guardrail",
    "advisory_only",
    "human_approval_required",
    "score_mutation",
    "rank_mutation",
    "queue_mutation",
    "resume_text_mutation",
    "operator_state_persistence",
    "application_action_capability",
)

ITEM61F_PRODUCTION_FILES = {
    "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.tsx",
    "frontend/executive-kpi/src/agentic/agenticOperationsModel.ts",
    "frontend/executive-kpi/src/styles.css",
    "src/app/static/build/executive-kpi/executive-kpi.js",
    "src/app/static/build/executive-kpi/executive-kpi.css",
}


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_frontend_schema_matches_exact_current_canonical_registry_serialization() -> None:
    definitions = canonical_registry.list_canonical_agent_definitions()
    payload = services.agentic_operations_canonical_agents_payload()
    model_source = _source(MODEL_PATH)

    assert len(definitions) == 4
    assert tuple(field.name for field in fields(canonical_registry.CanonicalAgentDefinition)) == CANONICAL_FIELDS
    assert payload["agents"] == [asdict(definition) for definition in definitions]
    assert all(tuple(agent) == CANONICAL_FIELDS for agent in payload["agents"])
    assert "export type AgenticOperationsCanonicalAgent" in model_source
    for field_name in CANONICAL_FIELDS:
        assert f"  {field_name}?:" in model_source
    assert "canonical_agents?: AgenticOperationsCanonicalAgent[];" in model_source


def test_existing_overview_remains_the_only_agentic_operations_api_owner() -> None:
    overview_source = inspect.getsource(services.agentic_operations_overview_payload)
    api_source = _source(ROOT / "src/app/api.py")

    assert '"canonical_agents": deepcopy(canonical_payload["agents"])' in overview_source
    assert "agentic_operations_canonical_agents_payload()" in overview_source
    assert api_source.count(f'@app.get("{OVERVIEW_PATH}")') == 1
    assert api_source.count('/profile/admin/agentic-operations/') == 1


def test_registry_and_matrix_reuse_the_single_get_without_mutation_networks() -> None:
    model_source = _source(MODEL_PATH)
    component_source = _source(COMPONENT_PATH)
    combined = model_source + "\n" + component_source

    assert model_source.count("fetch(") == 1
    assert combined.count(OVERVIEW_PATH) == 1
    assert 'method: "GET"' in model_source
    assert 'credentials: "same-origin"' in model_source
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert f'method: "{method}"' not in combined
    for endpoint in (
        '"/agents',
        '"/registry',
        '"/agent-status',
        '"/agent-trace',
        '"/trace',
        '"/provider',
        '"/application',
    ):
        assert endpoint not in combined


def test_registry_ui_is_declarative_and_excludes_run_level_controls() -> None:
    component_source = _source(COMPONENT_PATH)

    for required in (
        "Canonical Agent Registry",
        "Safety / Mutation Authority Matrix",
        "Controlled LLM guardrail available",
        "Human approval required",
        "Registry capability totals do not match the returned safety summary.",
    ):
        assert required in component_source
    for forbidden in (
        "Live Agents",
        "Running Agents",
        "Used in this run",
        "Last executed",
        "Select Run",
        "View Run",
        "Approve agent",
        "Execute agent",
    ):
        assert forbidden not in component_source


def test_item61f_ownership_excludes_other_product_surfaces_and_backend() -> None:
    assert ITEM61F_PRODUCTION_FILES.isdisjoint(
        {
            "src/app/api.py",
            "src/app/services.py",
            "src/app/ui.py",
            "src/app/ui_shell.py",
            "frontend/executive-kpi/src/main.tsx",
            "src/agents/canonical_registry.py",
            "src/app/profile_ui.py",
            "src/app/static/agentic_review.js",
            "src/app/static/agentic_review.css",
            "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx",
        }
    )
