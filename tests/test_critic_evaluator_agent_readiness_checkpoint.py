from pathlib import Path


DOC_PATH = Path("docs/critic_evaluator_agent_readiness_checkpoint.md")
README_PATH = Path("README.md")
READINESS_PATH = Path("docs/orchestrator_readiness.md")

STEP_196_ALLOWED_FILES = [
    "docs/critic_evaluator_agent_readiness_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_critic_evaluator_agent_readiness_checkpoint.py",
    "tests/test_agentic_docs.py",
]

REQUIRED_TERMS = [
    "Critic/Evaluator agent readiness checkpoint",
    "docs/tests only",
    "Critic/Evaluator agent readiness",
    "future Critic/Evaluator agent",
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
    "no application execution",
    "no application submission",
    "no scoring change",
    "deterministic",
    "trace-only evaluation inputs",
    "agent trace review",
    "quality rubric",
    "evaluator output contract",
    "safety metadata review",
    "validation_json review",
    "prefilter relevance",
    "deduplication",
    "JD intelligence",
    "final application scoring",
    "LLM evaluation",
    "application execution",
    "application submission",
    "read-only Agent Trace API endpoint",
    "read-only Agent Trace UI panel",
    "non-goals",
    "implementation guardrails",
    "rollback plan",
    "verification plan",
]

QUALITY_RUBRIC = [
    "1. trace completeness",
    "2. agent step ordering",
    "3. safety metadata completeness",
    "4. validation_json consistency",
    "5. separation of prefilter relevance, LLM evaluation, and final application scoring",
    "6. no application execution or submission judgment",
]

EVALUATOR_OUTPUT_FIELDS = [
    "evaluator_status",
    "evaluator_findings",
    "evaluator_warnings",
    "evaluator_recommendations",
    "requires_human_review",
    "deterministic_rubric_version",
]


def _doc_text() -> str:
    return DOC_PATH.read_text()


def test_critic_evaluator_agent_readiness_doc_exists_and_has_required_terms():
    doc = _doc_text()

    for term in REQUIRED_TERMS:
        assert term in doc


def test_critic_evaluator_quality_rubric_is_exact():
    doc = _doc_text()
    start = doc.index("## Quality rubric")
    end = doc.index("## Evaluator output contract")
    section = doc[start:end]
    rubric_lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip().startswith(tuple(f"{index}." for index in range(1, 7)))
    ]

    assert rubric_lines == QUALITY_RUBRIC


def test_critic_evaluator_output_contract_fields_are_present():
    doc = _doc_text()

    for field in EVALUATOR_OUTPUT_FIELDS:
        assert field in doc


def test_critic_evaluator_links_are_present():
    path = "docs/critic_evaluator_agent_readiness_checkpoint.md"

    assert path in README_PATH.read_text()
    assert path in READINESS_PATH.read_text()


def test_step_196_allowed_files_are_docs_tests_only():
    for path in STEP_196_ALLOWED_FILES:
        assert Path(path).exists(), path
        assert path == "README.md" or path.startswith("docs/") or path.startswith("tests/")

    forbidden_prefixes = (
        "src/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in STEP_196_ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes)
