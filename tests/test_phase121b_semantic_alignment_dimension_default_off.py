import ast
from pathlib import Path

from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.evidence_builder import build_resume_evidence
from src.resume.models import ResumeDocument


ROOT = Path(__file__).resolve().parents[1]
SCORER_PATH = ROOT / "src/matching/scorer.py"
HELPER_PATH = ROOT / "src/matching/semantic_similarity.py"
SEMANTIC_GATE = "APPLYLENS_SEMANTIC_SCORE_COMPONENT_ENABLED"


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


def test_gate_off_preserves_final_score_and_dimension_names(monkeypatch):
    monkeypatch.delenv(SEMANTIC_GATE, raising=False)
    baseline = score_resume_job_match(_resume(), _job())

    monkeypatch.setenv(SEMANTIC_GATE, "false")
    result = score_resume_job_match(_resume(), _job())

    assert result.final_score == baseline.final_score
    assert _dimension_names(result) == _dimension_names(baseline)
    assert "semantic_alignment" not in _dimension_names(result)


def test_gate_off_does_not_call_semantic_helper(monkeypatch):
    import src.matching.scorer as scorer

    monkeypatch.delenv(SEMANTIC_GATE, raising=False)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("semantic helper should not be called when gate is off")

    monkeypatch.setattr(scorer, "build_semantic_similarity_diagnostic", fail_if_called)

    result = scorer.score_resume_job_match(_resume(), _job())

    assert "semantic_alignment" not in _dimension_names(result)


def test_gate_on_appends_zero_weight_semantic_alignment(monkeypatch):
    monkeypatch.delenv(SEMANTIC_GATE, raising=False)
    baseline = score_resume_job_match(_resume(), _job())

    monkeypatch.setenv(SEMANTIC_GATE, "true")
    result = score_resume_job_match(_resume(), _job())
    semantic = _semantic_dimension(result)

    assert result.final_score == baseline.final_score
    assert semantic.weight == 0.0
    assert semantic.weighted_score == 0.0
    assert 0.0 <= semantic.score <= 1.0
    assert semantic.score > 0.0
    assert "no score impact" in semantic.reason.lower()
    assert "score_impact=false" in semantic.evidence


def test_gate_on_accepts_project_true_values(monkeypatch):
    for true_value in ("1", "true", "yes", "on"):
        monkeypatch.setenv(SEMANTIC_GATE, true_value)
        result = score_resume_job_match(_resume(), _job())

        assert "semantic_alignment" in _dimension_names(result)


def test_gate_on_empty_text_is_safe_and_zero_weight(monkeypatch):
    monkeypatch.setenv(SEMANTIC_GATE, "1")

    result = score_resume_job_match(_resume(raw_text=""), _job(preview="", retrieval_text=""))
    semantic = _semantic_dimension(result)

    assert 0.0 <= semantic.score <= 1.0
    assert semantic.weight == 0.0
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
