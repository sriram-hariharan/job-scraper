from pathlib import Path


DOC_PATH = Path("docs/agentic_foundation_trace_ui_wrap_checkpoint.md")
README_PATH = Path("README.md")
READINESS_PATH = Path("docs/orchestrator_readiness.md")

STEP_192_ALLOWED_FILES = [
    "docs/agentic_foundation_trace_ui_wrap_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_agentic_foundation_trace_ui_wrap_checkpoint.py",
    "tests/test_agentic_docs.py",
]

REQUIRED_TERMS = [
    "Agentic foundation trace UI wrap checkpoint",
    "docs/tests only",
    "Milestone A",
    "Milestone B",
    "Milestone C",
    "Agent state foundation",
    "JobApplicationContext",
    "agent_runs",
    "agent_steps",
    "migration runner",
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
    "no pipeline wiring",
    "no scheduler",
    "no background task",
    "no storage writes",
    "no schema migration",
    "no file export",
    "no live LLM call",
    "no application execution",
    "no application submission",
    "read-only",
    "deterministic",
    "current completed scope",
    "remaining non-goals",
    "next recommended milestone options",
    "rollback plan",
    "verification plan",
]

NEXT_OPTIONS = [
    "1. Trace polish / UX hardening",
    "2. Trace persistence activation and migration execution plan",
    "3. Critic/Evaluator agent readiness",
    "4. Feedback learning loop readiness",
    "5. LangGraph orchestration spike",
]


def _doc_text() -> str:
    return DOC_PATH.read_text()


def test_agentic_foundation_trace_ui_wrap_checkpoint_doc_exists_and_has_required_terms():
    doc = _doc_text()

    for term in REQUIRED_TERMS:
        assert term in doc


def test_agentic_foundation_trace_ui_wrap_checkpoint_next_options_are_exact():
    doc = _doc_text()
    start = doc.index("## Next recommended milestone options")
    end = doc.index("## Rollback plan")
    section = doc[start:end]
    option_lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip().startswith(("1.", "2.", "3.", "4.", "5."))
    ]

    assert option_lines == NEXT_OPTIONS
    assert "Do not implement those options in this checkpoint." in section


def test_agentic_foundation_trace_ui_wrap_checkpoint_links_are_present():
    path = "docs/agentic_foundation_trace_ui_wrap_checkpoint.md"

    assert path in README_PATH.read_text()
    assert path in READINESS_PATH.read_text()


def test_step_192_allowed_files_are_docs_tests_only():
    for path in STEP_192_ALLOWED_FILES:
        assert Path(path).exists(), path
        assert path == "README.md" or path.startswith("docs/") or path.startswith("tests/")

    forbidden_prefixes = (
        "src/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in STEP_192_ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes)
