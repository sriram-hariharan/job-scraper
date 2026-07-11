import ast
from pathlib import Path

from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.evidence_builder import build_resume_evidence
from src.resume.models import ResumeDocument


ROOT = Path(__file__).resolve().parents[1]
SCORER_PATH = ROOT / "src/matching/scorer.py"
HELPER_PATH = ROOT / "src/matching/semantic_similarity.py"
SEMANTIC_WEIGHT = 0.05


def _resume(raw_text: str | None = None):
    text = raw_text if raw_text is not None else """
Applied AI Engineer

Experience
Applied AI Engineer, Demo Co
2021 - Present
- Built Applied AI systems with RAG, vector search, prompt engineering,
  evaluation workflows, FastAPI, pytest, LangGraph, and Python.

Skills
Python RAG vector search prompt engineering evaluation workflows FastAPI pytest
""".strip()
    return build_resume_evidence(
        ResumeDocument(
            resume_id="ai_resume",
            resume_name="Sriram_Neelakantan_AI2.pdf",
            path="Sriram_Neelakantan_AI2.pdf",
            raw_text=text,
            normalized_text=text.lower(),
        )
    )


def _job(preview: str | None = None, retrieval_text: str | None = None):
    return build_job_evidence(
        {
            "doc_id": "job_1",
            "company": "Demo",
            "title": "Applied AI Engineer",
            "location": "Remote",
            "source": "test",
            "preview": preview
            if preview is not None
            else (
                "Required: Applied AI, RAG, vector search, prompt engineering, "
                "evaluation workflows, FastAPI, pytest, LangGraph, and Python."
            ),
            "retrieval_text": retrieval_text
            if retrieval_text is not None
            else "Applied AI RAG vector search prompt engineering evaluation workflows",
        }
    )


def _dimension_names(result):
    return [score.name for score in result.dimension_scores]


def _semantic_dimension(result):
    matches = [
        score for score in result.dimension_scores if score.name == "semantic_alignment"
    ]
    assert len(matches) == 1
    return matches[0]


def test_semantic_alignment_is_always_present_without_env_gate(monkeypatch):
    monkeypatch.delenv("APPLYLENS_SEMANTIC_SCORE_COMPONENT_ENABLED", raising=False)
    result = score_resume_job_match(_resume(), _job())
    semantic = _semantic_dimension(result)

    assert "semantic_alignment" in _dimension_names(result)
    assert semantic.weight == SEMANTIC_WEIGHT
    assert semantic.weighted_score == round(semantic.score * SEMANTIC_WEIGHT, 6)
    assert 0.0 <= semantic.score <= 1.0
    assert semantic.score > 0.0
    assert "small weighted score component" in semantic.reason.lower()
    assert "score_impact=true" in semantic.evidence


def test_semantic_alignment_ignores_legacy_gate_false_value(monkeypatch):
    monkeypatch.setenv("APPLYLENS_SEMANTIC_SCORE_COMPONENT_ENABLED", "false")

    result = score_resume_job_match(_resume(), _job())

    assert "semantic_alignment" in _dimension_names(result)


def test_final_score_includes_semantic_alignment_weighted_score():
    result = score_resume_job_match(_resume(), _job())

    assert result.final_score == round(
        sum(score.weighted_score for score in result.dimension_scores),
        6,
    )
    assert _semantic_dimension(result).weighted_score > 0.0


def test_related_pair_has_higher_semantic_contribution_than_unrelated_pair():
    related = score_resume_job_match(_resume(), _job())
    unrelated = score_resume_job_match(
        _resume(
            "Finance operations leader with Excel reporting, billing, payroll, "
            "and accounts reconciliation experience."
        ),
        _job(
            preview=(
                "Required: Applied AI, RAG, vector search, prompt engineering, "
                "evaluation workflows, FastAPI, pytest, LangGraph, and Python."
            ),
            retrieval_text="Applied AI RAG vector search prompt engineering",
        ),
    )

    assert _semantic_dimension(related).weighted_score > _semantic_dimension(
        unrelated
    ).weighted_score


def test_empty_text_is_safe_and_contributes_zero():
    result = score_resume_job_match(_resume(raw_text=""), _job(preview="", retrieval_text=""))
    semantic = _semantic_dimension(result)

    assert semantic.score == 0.0
    assert semantic.weight == SEMANTIC_WEIGHT
    assert semantic.weighted_score == 0.0


def test_scorer_and_helper_do_not_import_provider_rag_or_embedding_modules():
    forbidden_roots = (
        "groq",
        "openai",
        "sentence_transformers",
        "transformers",
        "llama_index",
        "src.ai",
        "src.rag",
        "src.agents",
    )

    for path in (SCORER_PATH, HELPER_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add(node.module or "")

        assert not {
            module
            for module in imported_modules
            if any(
                module == root or module.startswith(f"{root}.")
                for root in forbidden_roots
            )
        }


def test_no_forbidden_runtime_surface_files_changed():
    assert not (ROOT / "requirements.txt").read_text(encoding="utf-8").count(
        "semantic_alignment"
    )


def test_scorer_does_not_reference_semantic_env_gate():
    scorer_text = SCORER_PATH.read_text(encoding="utf-8")

    assert "APPLYLENS_SEMANTIC_SCORE_COMPONENT_ENABLED" not in scorer_text
    assert "_semantic_score_component_enabled" not in scorer_text
