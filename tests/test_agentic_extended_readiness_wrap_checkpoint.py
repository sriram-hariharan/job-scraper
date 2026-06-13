from pathlib import Path


DOC_PATH = Path("docs/agentic_extended_readiness_wrap_checkpoint.md")
README_PATH = Path("README.md")
READINESS_PATH = Path("docs/orchestrator_readiness.md")

STEP_199_ALLOWED_FILES = [
    "docs/agentic_extended_readiness_wrap_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_agentic_extended_readiness_wrap_checkpoint.py",
    "tests/test_agentic_docs.py",
]

REQUIRED_TERMS = [
    "Agentic extended readiness wrap checkpoint",
    "docs/tests only",
    "completed foundation scope",
    "completed trace UI scope",
    "completed trace polish scope",
    "persistence activation readiness",
    "Critic/Evaluator agent readiness",
    "Feedback learning loop readiness",
    "LangGraph orchestration spike readiness",
    "JobApplicationContext",
    "trace recorder",
    "Relevance Prefilter Agent",
    "Deduplication Agent",
    "JD Intelligence Agent",
    "Final Application Scoring Agent",
    "read-only Agent Trace API endpoint",
    "read-only Agent Trace UI panel",
    "prefilter relevance",
    "deduplication",
    "JD intelligence",
    "final application scoring",
    "LLM evaluation",
    "application execution",
    "application submission",
    "no behavior change",
    "no API behavior change",
    "no UI behavior change",
    "no storage writes",
    "no schema migration",
    "no pipeline wiring",
    "no scheduler",
    "no background task",
    "no file export",
    "no live LLM call",
    "no model provider call",
    "no approval mutation",
    "no ranking change",
    "no scoring change",
    "no application execution",
    "no application submission",
    "deterministic",
    "current completed scope",
    "remaining non-goals",
    "next implementation options",
    "recommended next step",
    "rollback plan",
    "verification plan",
]

NEXT_IMPLEMENTATION_OPTIONS = [
    "1. Persisted trace activation with explicit operator approval",
    "2. Critic/Evaluator runtime skeleton without LLM calls",
    "3. Feedback capture storage readiness",
    "4. LangGraph dependency decision checkpoint",
    "5. Pipeline wiring readiness checkpoint",
]


def _doc_text() -> str:
    return DOC_PATH.read_text()


def test_agentic_extended_readiness_wrap_doc_exists_and_has_required_terms():
    doc = _doc_text()

    for term in REQUIRED_TERMS:
        assert term in doc


def test_agentic_extended_next_implementation_options_are_exact():
    doc = _doc_text()
    start = doc.index("## Next implementation options")
    end = doc.index("## Recommended next step")
    section = doc[start:end]
    option_lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip().startswith(tuple(f"{index}." for index in range(1, 6)))
    ]

    assert option_lines == NEXT_IMPLEMENTATION_OPTIONS


def test_agentic_extended_recommended_next_step_is_safest_option():
    doc = _doc_text()
    start = doc.index("## Recommended next step")
    end = doc.index("## Safety contract")
    section = doc[start:end]

    assert "Recommended next step: Critic/Evaluator runtime skeleton without LLM calls." in section
    for phrase in [
        "deterministic",
        "trace-only",
        "no provider call",
        "no scoring change",
        "no pipeline wiring",
    ]:
        assert phrase in section


def test_agentic_extended_readiness_wrap_links_are_present():
    path = "docs/agentic_extended_readiness_wrap_checkpoint.md"

    assert path in README_PATH.read_text()
    assert path in READINESS_PATH.read_text()


def test_step_199_allowed_files_are_docs_tests_only():
    for path in STEP_199_ALLOWED_FILES:
        assert Path(path).exists(), path
        assert path == "README.md" or path.startswith("docs/") or path.startswith("tests/")

    forbidden_prefixes = (
        "src/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in STEP_199_ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes)
