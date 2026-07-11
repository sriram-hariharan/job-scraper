import ast
from pathlib import Path

from src.matching.semantic_similarity import (
    build_semantic_similarity_diagnostic,
    token_cosine_similarity,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src/matching/semantic_similarity.py"


APPLIED_AI_JD = """
Applied AI Engineer building GenAI products with RAG, prompt engineering,
evaluation workflows, vector search, LangGraph, LlamaIndex, FastAPI, pytest,
and customer-facing AI solution delivery.
"""

APPLIED_AI_RESUME = """
Built applied AI and generative AI systems using RAG, vector search, prompt
engineering, evaluation workflows, LangGraph, LlamaIndex, FastAPI, pytest,
and customer-facing delivery.
"""

UNRELATED_RESUME = """
Managed retail store operations, inventory counts, cashier training, vendor
orders, shift scheduling, merchandising, and point-of-sale reconciliation.
"""


def test_related_jd_resume_pair_scores_higher_than_unrelated_pair():
    related = token_cosine_similarity(APPLIED_AI_JD, APPLIED_AI_RESUME)
    unrelated = token_cosine_similarity(APPLIED_AI_JD, UNRELATED_RESUME)

    assert related > unrelated
    assert related >= 0.45
    assert unrelated <= 0.15


def test_identical_or_near_identical_text_scores_high():
    assert token_cosine_similarity(APPLIED_AI_JD, APPLIED_AI_JD) == 1.0

    near_identical = token_cosine_similarity(
        "RAG evaluation workflows vector search FastAPI pytest",
        "RAG evaluation workflows vector search FastAPI pytest Python",
    )

    assert near_identical >= 0.9


def test_empty_inputs_return_zero_safely():
    assert token_cosine_similarity("", APPLIED_AI_RESUME) == 0.0
    assert token_cosine_similarity(APPLIED_AI_JD, "") == 0.0
    assert token_cosine_similarity(None, APPLIED_AI_RESUME) == 0.0
    assert token_cosine_similarity(APPLIED_AI_JD, None) == 0.0


def test_similarity_is_deterministic_and_bounded():
    first = token_cosine_similarity(APPLIED_AI_JD, APPLIED_AI_RESUME)
    second = token_cosine_similarity(APPLIED_AI_JD, APPLIED_AI_RESUME)

    assert first == second
    assert 0.0 <= first <= 1.0


def test_diagnostic_payload_is_score_impact_false():
    diagnostic = build_semantic_similarity_diagnostic(
        APPLIED_AI_JD,
        APPLIED_AI_RESUME,
    )

    assert diagnostic["code"] == "jd_resume_semantic_similarity"
    assert diagnostic["method"] == "deterministic_token_cosine"
    assert diagnostic["score_impact"] is False
    assert 0.0 <= diagnostic["similarity"] <= 1.0


def test_helper_has_no_provider_llm_embedding_or_rag_imports():
    tree = ast.parse(HELPER_PATH.read_text(encoding="utf-8"))
    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.add(node.module or "")

    forbidden_roots = (
        "groq",
        "openai",
        "sentence_transformers",
        "llama_index",
        "src.ai",
        "src.rag",
        "src.agents",
        "src.tailoring",
    )

    assert not {
        module
        for module in imported_modules
        if any(module == root or module.startswith(f"{root}.") for root in forbidden_roots)
    }


def test_helper_does_not_touch_scoring_or_selector_surfaces():
    source = HELPER_PATH.read_text(encoding="utf-8")

    for forbidden_text in (
        "final_score",
        "weighted_score",
        "winner_resume",
        "runner_up_resume",
        "run_chat_completion",
        "provider_call",
        "Groq",
    ):
        assert forbidden_text not in source
