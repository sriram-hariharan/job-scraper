from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = (
    ROOT / "src/agents/evidence_chain_shadow_execution.py",
    ROOT / "run_evidence_chain_shadow.py",
)


def test_runtime_sources_have_no_production_durable_mutation_or_provider_imports():
    forbidden_modules = (
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
        "src.notifications",
    )
    for path in RUNTIME_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not any(
            module == forbidden or module.startswith(forbidden + ".")
            for module in imported
            for forbidden in forbidden_modules
        )


def test_runtime_sources_never_call_resume_finalize_or_write_owners():
    forbidden_calls = {
        "save_new_job_ids",
        "filter_new_jobs",
        "dedupe_jobs",
        "rank_jobs",
        "filter_jobs",
        "score_jobs",
        "load_resume_documents",
        "export_job_corpus",
        "write_agentic_workflow_summary_artifacts",
        "insert_patch_selection_row_to_postgres",
        "insert_operator_decision_row_to_postgres",
        "insert_application_action_row_to_postgres",
        "insert_notification_state_row_to_postgres",
        "_apply_operator_review_pause_resume_decision",
        "_finalize_node",
    }
    for path in RUNTIME_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert forbidden_calls.isdisjoint(called)


def test_no_module_global_graph_saver_or_mutable_cache():
    for path in RUNTIME_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                assert not isinstance(value, (ast.List, ast.Dict, ast.Set))
                if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
                    assert value.func.id not in {"InMemorySaver", "StateGraph"}


def test_no_production_entrypoint_references_step3_runtime():
    for relative in (
        "main.py",
        "run_application_planning.py",
        "run_api.py",
        "src/pipeline/collector.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "evidence_chain_shadow_execution" not in source
        assert "run_evidence_chain_shadow" not in source
