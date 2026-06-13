from pathlib import Path


DOC_PATH = Path("docs/feedback_learning_loop_readiness_checkpoint.md")
README_PATH = Path("README.md")
READINESS_PATH = Path("docs/orchestrator_readiness.md")

STEP_197_ALLOWED_FILES = [
    "docs/feedback_learning_loop_readiness_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_feedback_learning_loop_readiness_checkpoint.py",
    "tests/test_agentic_docs.py",
]

REQUIRED_TERMS = [
    "Feedback learning loop readiness checkpoint",
    "docs/tests only",
    "Feedback learning loop readiness",
    "future feedback learning loop",
    "human feedback",
    "agent trace feedback",
    "evaluator findings",
    "review outcomes",
    "feedback input contract",
    "feedback output contract",
    "learning signal taxonomy",
    "no behavior change",
    "no API behavior change",
    "no UI behavior change",
    "no storage writes",
    "no feedback storage",
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
    "read-only Agent Trace API endpoint",
    "read-only Agent Trace UI panel",
    "Critic/Evaluator agent readiness",
    "prefilter relevance",
    "deduplication",
    "JD intelligence",
    "final application scoring",
    "LLM evaluation",
    "application execution",
    "application submission",
    "non-goals",
    "implementation guardrails",
    "rollback plan",
    "verification plan",
]

FEEDBACK_INPUT_FIELDS = [
    "trace_run_id",
    "agent_step_id",
    "reviewer_id_placeholder",
    "feedback_category",
    "feedback_signal",
    "feedback_note",
    "requires_human_review",
]

FEEDBACK_OUTPUT_FIELDS = [
    "accepted_signal",
    "rejected_signal",
    "learning_signal_type",
    "recommended_follow_up",
    "safe_to_use_for_training",
    "deterministic_feedback_schema_version",
]

LEARNING_SIGNAL_TAXONOMY = [
    "1. false positive relevance",
    "2. false negative relevance",
    "3. duplicate detection miss",
    "4. JD extraction issue",
    "5. final application scoring issue",
    "6. safety metadata issue",
    "7. validation_json issue",
    "8. human review required",
]


def _doc_text() -> str:
    return DOC_PATH.read_text()


def test_feedback_learning_loop_readiness_doc_exists_and_has_required_terms():
    doc = _doc_text()

    for term in REQUIRED_TERMS:
        assert term in doc


def test_feedback_learning_loop_input_contract_fields_are_present():
    doc = _doc_text()

    for field in FEEDBACK_INPUT_FIELDS:
        assert field in doc


def test_feedback_learning_loop_output_contract_fields_are_present():
    doc = _doc_text()

    for field in FEEDBACK_OUTPUT_FIELDS:
        assert field in doc


def test_feedback_learning_loop_taxonomy_is_exact():
    doc = _doc_text()
    start = doc.index("## Learning signal taxonomy")
    end = doc.index("## Trace and evaluator context")
    section = doc[start:end]
    taxonomy_lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip().startswith(tuple(f"{index}." for index in range(1, 9)))
    ]

    assert taxonomy_lines == LEARNING_SIGNAL_TAXONOMY


def test_feedback_learning_loop_links_are_present():
    path = "docs/feedback_learning_loop_readiness_checkpoint.md"

    assert path in README_PATH.read_text()
    assert path in READINESS_PATH.read_text()


def test_step_197_allowed_files_are_docs_tests_only():
    for path in STEP_197_ALLOWED_FILES:
        assert Path(path).exists(), path
        assert path == "README.md" or path.startswith("docs/") or path.startswith("tests/")

    forbidden_prefixes = (
        "src/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in STEP_197_ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes)
