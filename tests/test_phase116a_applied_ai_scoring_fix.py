from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.evidence_builder import build_resume_evidence
from src.resume.models import ResumeDocument


def _resume_text(title: str, bullet: str) -> str:
    return f"""
{title}

Experience
{title}, Demo Co
2021 - Present
- {bullet}

Skills
Python SQL machine learning statistics
""".strip()


def _resume(name: str, title: str, bullet: str):
    raw_text = _resume_text(title, bullet)
    return build_resume_evidence(
        ResumeDocument(
            resume_id=name,
            resume_name=name,
            path=name,
            raw_text=raw_text,
            normalized_text=raw_text.lower(),
        )
    )


def _snorkel_applied_ai_job():
    return build_job_evidence(
        {
            "doc_id": "snorkel_applied_ai",
            "company": "Snorkel",
            "title": "Applied AI Engineer",
            "location": "US",
            "source": "test",
            "preview": (
                "Required qualifications: Applied AI, GenAI, RAG, fine-tuning, "
                "prompt engineering, evaluation workflows, Hugging Face, vector "
                "database, LlamaIndex, LangGraph, CrewAI, Python, FastAPI, pytest, "
                "and pydantic. Responsibilities: build agentic workflows and "
                "multi-agent systems for customer-facing AI solution delivery."
            ),
            "retrieval_text": (
                "Applied AI Engineer generative AI large language model retrieval "
                "augmented generation embeddings semantic search AI guardrails "
                "hallucination evaluation OpenAI SDK Bedrock."
            ),
        }
    )


def _generic_data_scientist_job():
    return build_job_evidence(
        {
            "doc_id": "generic_ds",
            "company": "Acme",
            "title": "Data Scientist",
            "location": "US",
            "source": "test",
            "preview": (
                "Required qualifications: Python, SQL, statistics, machine "
                "learning, regression, and A/B testing. Responsibilities: "
                "experimentation, forecasting, dashboards, and business analytics "
                "reporting. Preferred: Tableau, pandas, and scikit-learn."
            ),
        }
    )


def _resume_variants():
    ai2 = _resume(
        "Sriram_Neelakantan_AI2.pdf",
        "Applied AI Engineer",
        (
            "Built Applied AI and Generative AI systems with RAG, retrieval "
            "augmented generation, embeddings, vector database, vector search, "
            "semantic search, prompt engineering, fine-tuning, LoRA, PEFT, "
            "evaluation workflows, evals, hallucination evaluation, AI guardrails, "
            "Hugging Face Transformers, LangChain, LlamaIndex, LangGraph, CrewAI, "
            "OpenAI SDK, Bedrock, FastAPI, pytest, pydantic, and Python. Delivered "
            "agentic workflows and multi-agent systems."
        ),
    )
    ai1 = _resume(
        "Sriram_Neelakantan_AI1.pdf",
        "AI Engineer",
        (
            "Built Generative AI systems with RAG, embeddings, prompt engineering, "
            "Hugging Face, FastAPI, pytest, Python, and evaluation workflows. "
            "Supported semantic search prototypes and AI guardrails."
        ),
    )
    general_ds = _resume(
        "Sriram_Neelakantan_General_Data_Scientist.pdf",
        "General Data Scientist",
        (
            "Built Python SQL machine learning statistics regression classification "
            "dashboards Tableau pandas scikit-learn forecasting A/B testing and "
            "business analytics reporting."
        ),
    )
    return ai2, ai1, general_ds


def _score_by_resume(job):
    return {
        resume.document.resume_name: score_resume_job_match(resume, job).final_score
        for resume in _resume_variants()
    }


def test_snorkel_style_applied_ai_job_prefers_ai2_then_ai1_then_general_ds():
    scores = _score_by_resume(_snorkel_applied_ai_job())

    assert scores["Sriram_Neelakantan_AI2.pdf"] > scores["Sriram_Neelakantan_AI1.pdf"]
    assert (
        scores["Sriram_Neelakantan_AI1.pdf"]
        > scores["Sriram_Neelakantan_General_Data_Scientist.pdf"]
    )


def test_generic_data_scientist_job_still_prefers_general_ds_resume():
    scores = _score_by_resume(_generic_data_scientist_job())

    assert (
        scores["Sriram_Neelakantan_General_Data_Scientist.pdf"]
        > scores["Sriram_Neelakantan_AI2.pdf"]
    )
    assert (
        scores["Sriram_Neelakantan_General_Data_Scientist.pdf"]
        > scores["Sriram_Neelakantan_AI1.pdf"]
    )


def test_applied_ai_vocabulary_is_extracted_without_llm_or_provider_calls():
    job = _snorkel_applied_ai_job()
    ai2, _, _ = _resume_variants()
    extracted_terms = set(job.required_skills + job.required_tools + job.required_workflows)
    resume_terms = set(
        ai2.skills
        + ai2.tools
        + ai2.workflows
        + ai2.experience_entries[0].normalized_skills
    )

    for term in (
        "applied ai",
        "generative ai",
        "rag",
        "vector db",
        "prompt engineering",
        "fine-tuning",
        "evaluation workflows",
        "hugging face",
        "llamaindex",
        "langgraph",
        "crewai",
        "fastapi",
        "pytest",
        "pydantic",
        "agentic workflows",
    ):
        assert term in extracted_terms | resume_terms
