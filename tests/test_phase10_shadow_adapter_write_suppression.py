from __future__ import annotations

import ast
import importlib
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    ROOT / "src/agents/evidence_chain_shadow_adapter.py",
    ROOT / "src/agents/evidence_chain_shadow_parity.py",
)


def test_imports_have_no_environment_file_database_or_graph_side_effects(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("forbidden side effect")

    monkeypatch.setattr("os.getenv", forbidden)
    sys.modules.pop("src.agents.evidence_chain_shadow_adapter", None)
    sys.modules.pop("src.agents.evidence_chain_shadow_parity", None)
    adapter = importlib.import_module("src.agents.evidence_chain_shadow_adapter")
    parity = importlib.import_module("src.agents.evidence_chain_shadow_parity")
    assert callable(adapter.adapt_completed_planning_artifacts)
    assert callable(parity.compare_shadow_parity)


def test_modules_import_only_read_only_standard_and_graph_contract_owners():
    imported = set()
    for path in MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
    forbidden_prefixes = (
        "src.pipeline.collector",
        "src.pipeline.job_filter",
        "src.utils.job_cache",
        "src.pipeline.dedupe",
        "src.pipeline.job_ranker",
        "src.pipeline.embedding_prefilter",
        "src.ai.job_fit_evaluator",
        "src.pipeline.application_scorer",
        "src.resume",
        "src.storage",
        "langgraph",
    )
    assert not any(
        module == prefix or module.startswith(prefix + ".")
        for module in imported
        for prefix in forbidden_prefixes
    )


def test_modules_contain_no_execution_persistence_provider_or_action_calls():
    forbidden_names = {
        "execute_langgraph_evidence_chain",
        "finalize",
        "connect",
        "commit",
        "upsert_rag_job_documents",
        "save_new_job_ids",
        "write_agentic_workflow_summary_artifacts",
        "insert_patch_selection_row_to_postgres",
        "insert_operator_decision_row_to_postgres",
        "insert_application_action_row_to_postgres",
        "insert_notification_state_row_to_postgres",
        "load_resume_documents",
        "score_jobs",
        "dedupe_jobs",
        "filter_jobs",
        "rank_jobs",
    }
    for path in MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert forbidden_names.isdisjoint(called)


def test_production_entrypoints_do_not_reference_step2_modules():
    for relative in (
        "main.py",
        "run_application_planning.py",
        "run_api.py",
        "src/pipeline/collector.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "evidence_chain_shadow_adapter" not in source
        assert "evidence_chain_shadow_parity" not in source
