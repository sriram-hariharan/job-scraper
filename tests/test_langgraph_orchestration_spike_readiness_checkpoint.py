from pathlib import Path


DOC_PATH = Path("docs/langgraph_orchestration_spike_readiness_checkpoint.md")
README_PATH = Path("README.md")
READINESS_PATH = Path("docs/orchestrator_readiness.md")

STEP_198_ALLOWED_FILES = [
    "docs/langgraph_orchestration_spike_readiness_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_langgraph_orchestration_spike_readiness_checkpoint.py",
    "tests/test_agentic_docs.py",
]

REQUIRED_TERMS = [
    "LangGraph orchestration spike readiness checkpoint",
    "docs/tests only",
    "LangGraph orchestration spike readiness",
    "future LangGraph orchestration spike",
    "no dependency installation",
    "no LangGraph dependency",
    "no graph runtime code",
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
    "existing agents",
    "JobApplicationContext",
    "trace recorder",
    "Relevance Prefilter Agent",
    "Deduplication Agent",
    "JD Intelligence Agent",
    "Final Application Scoring Agent",
    "Critic/Evaluator agent readiness",
    "Feedback learning loop readiness",
    "read-only Agent Trace API endpoint",
    "read-only Agent Trace UI panel",
    "prefilter relevance",
    "deduplication",
    "JD intelligence",
    "final application scoring",
    "LLM evaluation",
    "application execution",
    "application submission",
    "state graph proposal",
    "node inventory",
    "edge inventory",
    "routing constraints",
    "side-effect boundaries",
    "non-goals",
    "implementation guardrails",
    "rollback plan",
    "verification plan",
]

NODE_INVENTORY = [
    "- agent_state_initialization",
    "- relevance_prefilter",
    "- deduplication",
    "- jd_intelligence",
    "- final_application_scoring",
    "- critic_evaluator",
    "- feedback_learning_loop",
]

EDGE_INVENTORY = (
    "agent_state_initialization -> relevance_prefilter -> deduplication -> "
    "jd_intelligence -> final_application_scoring -> critic_evaluator -> "
    "feedback_learning_loop"
)

SIDE_EFFECT_BOUNDARIES = [
    "- application execution",
    "- application submission",
    "- approval mutation",
    "- storage writes",
    "- scheduler/background work",
    "- file export",
    "- live LLM call",
]


def _doc_text() -> str:
    return DOC_PATH.read_text()


def test_langgraph_orchestration_spike_doc_exists_and_has_required_terms():
    doc = _doc_text()

    for term in REQUIRED_TERMS:
        assert term in doc


def test_langgraph_node_inventory_is_exact():
    doc = _doc_text()
    start = doc.index("## Node inventory")
    end = doc.index("## Edge inventory")
    section = doc[start:end]
    node_lines = [line.strip() for line in section.splitlines() if line.strip().startswith("- ")]

    assert node_lines == NODE_INVENTORY


def test_langgraph_edge_inventory_describes_future_deterministic_order():
    doc = _doc_text()
    start = doc.index("## Edge inventory")
    end = doc.index("## Routing constraints")
    section = doc[start:end]

    assert EDGE_INVENTORY in section
    assert "Future deterministic edge inventory" in section


def test_langgraph_side_effect_boundaries_are_exact():
    doc = _doc_text()
    start = doc.index("## Side-effect boundaries")
    end = doc.index("## Implementation guardrails")
    section = doc[start:end]
    boundary_lines = [
        line.strip() for line in section.splitlines() if line.strip().startswith("- ")
    ]

    assert boundary_lines == SIDE_EFFECT_BOUNDARIES


def test_langgraph_orchestration_spike_links_are_present():
    path = "docs/langgraph_orchestration_spike_readiness_checkpoint.md"

    assert path in README_PATH.read_text()
    assert path in READINESS_PATH.read_text()


def test_step_198_allowed_files_are_docs_tests_only():
    for path in STEP_198_ALLOWED_FILES:
        assert Path(path).exists(), path
        assert path == "README.md" or path.startswith("docs/") or path.startswith("tests/")

    forbidden_prefixes = (
        "src/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in STEP_198_ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes)
