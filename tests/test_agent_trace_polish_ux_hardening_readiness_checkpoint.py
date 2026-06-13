from pathlib import Path


DOC_PATH = Path("docs/agent_trace_polish_ux_hardening_readiness_checkpoint.md")
README_PATH = Path("README.md")
READINESS_PATH = Path("docs/orchestrator_readiness.md")

STEP_193_ALLOWED_FILES = [
    "docs/agent_trace_polish_ux_hardening_readiness_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_agent_trace_polish_ux_hardening_readiness_checkpoint.py",
    "tests/test_agentic_docs.py",
]

REQUIRED_TERMS = [
    "Agent Trace polish / UX hardening readiness checkpoint",
    "docs/tests only",
    "Trace polish / UX hardening",
    "read-only Agent Trace UI panel",
    "read-only Agent Trace API endpoint",
    "no behavior change",
    "no API behavior change",
    "no UI behavior change",
    "no frontend runtime change",
    "no storage writes",
    "no schema migration",
    "no pipeline wiring",
    "no scheduler",
    "no background task",
    "no file export",
    "no live LLM call",
    "no application execution",
    "no application submission",
    "no approval mutation",
    "deterministic",
    "ordered agent steps",
    "empty trace",
    "not found trace",
    "fetch failure",
    "safety metadata",
    "validation_json",
    "no approve",
    "no apply",
    "no submit",
    "no run",
    "no retry",
    "no export",
    "proposed polish scope",
    "accessibility labels",
    "loading state",
    "empty-state clarity",
    "error-state clarity",
    "long trace readability",
    "collapsed step details",
    "copy-safe summaries",
    "non-goals",
    "implementation guardrails",
    "rollback plan",
    "verification plan",
]

PROPOSED_POLISH_SCOPE = [
    "1. clearer loading state",
    "2. clearer empty/not-found/fetch-failure states",
    "3. collapsed/expanded step details",
    "4. more readable safety metadata and validation_json display",
    "5. accessibility labels for trace sections",
]


def _doc_text() -> str:
    return DOC_PATH.read_text()


def test_agent_trace_polish_readiness_doc_exists_and_has_required_terms():
    doc = _doc_text()

    for term in REQUIRED_TERMS:
        assert term in doc


def test_agent_trace_polish_readiness_proposed_scope_is_exact():
    doc = _doc_text()
    start = doc.index("## Proposed polish scope")
    end = doc.index("## Accessibility and readability targets")
    section = doc[start:end]
    option_lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip().startswith(("1.", "2.", "3.", "4.", "5."))
    ]

    assert option_lines == PROPOSED_POLISH_SCOPE
    assert "Do not implement those improvements in this step." in section


def test_agent_trace_polish_readiness_links_are_present():
    path = "docs/agent_trace_polish_ux_hardening_readiness_checkpoint.md"

    assert path in README_PATH.read_text()
    assert path in READINESS_PATH.read_text()


def test_step_193_allowed_files_are_docs_tests_only():
    for path in STEP_193_ALLOWED_FILES:
        assert Path(path).exists(), path
        assert path == "README.md" or path.startswith("docs/") or path.startswith("tests/")

    forbidden_prefixes = (
        "src/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in STEP_193_ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes)
