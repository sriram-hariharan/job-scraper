from pathlib import Path


DOC_PATH = Path("docs/critic_evaluator_runtime_skeleton_wrap_checkpoint.md")
README_PATH = Path("README.md")
READINESS_PATH = Path("docs/orchestrator_readiness.md")

STEP_201_ALLOWED_FILES = [
    "docs/critic_evaluator_runtime_skeleton_wrap_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_critic_evaluator_runtime_skeleton_wrap_checkpoint.py",
    "tests/test_agentic_docs.py",
]

REQUIRED_TERMS = [
    "Critic/Evaluator runtime skeleton wrap checkpoint",
    "docs/tests only",
    "completed runtime skeleton scope",
    "isolated deterministic skeleton",
    "trace-only evaluation inputs",
    "CRITIC_EVALUATOR_RUBRIC_VERSION",
    "build_empty_evaluator_result",
    "evaluate_agent_trace",
    "evaluator_status",
    "evaluator_findings",
    "evaluator_warnings",
    "evaluator_recommendations",
    "requires_human_review",
    "deterministic_rubric_version",
    "trace completeness",
    "agent step ordering",
    "safety metadata completeness",
    "validation_json consistency",
    "separation of prefilter relevance, LLM evaluation, and final application scoring",
    "no live LLM call",
    "no model provider call",
    "no API behavior change",
    "no UI behavior change",
    "no storage writes",
    "no schema migration",
    "no pipeline wiring",
    "no scheduler",
    "no background task",
    "no file export",
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
    "1. Critic/Evaluator explicit read-only API action readiness",
    "2. Critic/Evaluator trace persistence readiness",
    "3. Critic/Evaluator UI display readiness",
    "4. Critic/Evaluator pipeline wiring readiness",
    "5. Feedback capture storage readiness",
]


def _doc_text() -> str:
    return DOC_PATH.read_text()


def test_critic_evaluator_runtime_wrap_doc_exists_and_has_required_terms():
    doc = _doc_text()

    for term in REQUIRED_TERMS:
        assert term in doc


def test_critic_evaluator_runtime_wrap_next_options_are_exact():
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


def test_critic_evaluator_runtime_wrap_recommended_next_step_is_safest_option():
    doc = _doc_text()
    start = doc.index("## Recommended next step")
    end = doc.index("## Rollback plan")
    section = doc[start:end]

    assert (
        "Recommended next step: Critic/Evaluator explicit read-only API action readiness."
        in section
    )
    for phrase in [
        "read-only",
        "deterministic",
        "no storage writes",
        "no LLM calls",
        "no scoring change",
        "no pipeline wiring",
    ]:
        assert phrase in section


def test_critic_evaluator_runtime_wrap_links_are_present():
    path = "docs/critic_evaluator_runtime_skeleton_wrap_checkpoint.md"

    assert path in README_PATH.read_text()
    assert path in READINESS_PATH.read_text()


def test_step_201_allowed_files_are_docs_tests_only():
    for path in STEP_201_ALLOWED_FILES:
        assert Path(path).exists(), path
        assert path == "README.md" or path.startswith("docs/") or path.startswith("tests/")

    forbidden_prefixes = (
        "src/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in STEP_201_ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes)
