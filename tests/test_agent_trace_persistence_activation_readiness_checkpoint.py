from pathlib import Path


DOC_PATH = Path("docs/agent_trace_persistence_activation_readiness_checkpoint.md")
README_PATH = Path("README.md")
READINESS_PATH = Path("docs/orchestrator_readiness.md")

STEP_195_ALLOWED_FILES = [
    "docs/agent_trace_persistence_activation_readiness_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_agent_trace_persistence_activation_readiness_checkpoint.py",
    "tests/test_agentic_docs.py",
]

REQUIRED_TERMS = [
    "Agent Trace persistence activation readiness checkpoint",
    "docs/tests only",
    "Trace persistence activation and migration execution plan",
    "persistent Agent Trace storage",
    "agent_runs",
    "agent_steps",
    "schema.sql",
    "migration runner",
    "read-only Agent Trace API endpoint",
    "read-only Agent Trace UI panel",
    "no behavior change",
    "no API behavior change",
    "no UI behavior change",
    "no storage code change",
    "no schema change",
    "no schema migration",
    "no migration execution",
    "no database connection",
    "no storage writes",
    "no pipeline wiring",
    "no scheduler",
    "no background task",
    "no file export",
    "no live LLM call",
    "no approval mutation",
    "no application execution",
    "no application submission",
    "deterministic",
    "activation prerequisites",
    "migration dry-run checklist",
    "rollback plan",
    "verification plan",
    "production safety checks",
    "database backup requirement",
    "idempotency check",
    "read-only API compatibility",
    "UI empty trace compatibility",
    "observability requirements",
    "non-goals",
]

ACTIVATION_PREREQUISITES = [
    "1. explicit operator approval",
    "2. database backup requirement",
    "3. migration dry-run checklist",
    "4. idempotency check",
    "5. rollback plan",
    "6. verification plan",
    "7. production safety checks",
]


def _doc_text() -> str:
    return DOC_PATH.read_text()


def test_agent_trace_persistence_activation_doc_exists_and_has_required_terms():
    doc = _doc_text()

    for term in REQUIRED_TERMS:
        assert term in doc


def test_agent_trace_persistence_activation_prerequisites_are_exact():
    doc = _doc_text()
    start = doc.index("## Activation prerequisites")
    end = doc.index("## Migration dry-run checklist")
    section = doc[start:end]
    prerequisite_lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip().startswith(tuple(f"{index}." for index in range(1, 8)))
    ]

    assert prerequisite_lines == ACTIVATION_PREREQUISITES
    assert "Do not implement migration execution in this checkpoint." in section


def test_agent_trace_persistence_activation_links_are_present():
    path = "docs/agent_trace_persistence_activation_readiness_checkpoint.md"

    assert path in README_PATH.read_text()
    assert path in READINESS_PATH.read_text()


def test_step_195_allowed_files_are_docs_tests_only():
    for path in STEP_195_ALLOWED_FILES:
        assert Path(path).exists(), path
        assert path == "README.md" or path.startswith("docs/") or path.startswith("tests/")

    forbidden_prefixes = (
        "src/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in STEP_195_ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes)
