from pathlib import Path


DOC_PATH = Path("docs/critic_evaluator_readonly_api_action_readiness_checkpoint.md")
README_PATH = Path("README.md")
READINESS_PATH = Path("docs/orchestrator_readiness.md")

STEP_202_ALLOWED_FILES = [
    "docs/critic_evaluator_readonly_api_action_readiness_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_critic_evaluator_readonly_api_action_readiness_checkpoint.py",
    "tests/test_agentic_docs.py",
]

REQUIRED_TERMS = [
    "Critic/Evaluator explicit read-only API action readiness checkpoint",
    "docs/tests only",
    "Critic/Evaluator explicit read-only API action readiness",
    "future explicit read-only API action",
    "no API implementation",
    "no endpoint implementation",
    "no API route change",
    "Critic/Evaluator runtime skeleton",
    "src/agents/critic_evaluator.py",
    "evaluate_agent_trace",
    "build_empty_evaluator_result",
    "evaluator_status",
    "evaluator_findings",
    "evaluator_warnings",
    "evaluator_recommendations",
    "requires_human_review",
    "deterministic_rubric_version",
    "read-only Agent Trace API endpoint",
    "explicit user action",
    "read-only evaluation",
    "trace-only evaluation inputs",
    "endpoint contract proposal",
    "request contract",
    "response contract",
    "error handling contract",
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
    "implementation guardrails",
    "non-goals",
    "rollback plan",
    "verification plan",
]

REQUEST_CONTRACT_TERMS = [
    "approval_request_id",
    "trace payload source",
    "optional evaluator_rubric_version",
    "no mutation fields",
]

RESPONSE_CONTRACT_TERMS = [
    "evaluator_status",
    "evaluator_findings",
    "evaluator_warnings",
    "evaluator_recommendations",
    "requires_human_review",
    "deterministic_rubric_version",
    "did_write_storage",
    "did_call_llm",
    "did_mutate_approval",
    "did_change_score",
    "did_execute_application",
    "did_submit_application",
]


def _doc_text() -> str:
    return DOC_PATH.read_text()


def test_critic_evaluator_readonly_api_action_doc_exists_and_has_required_terms():
    doc = _doc_text()

    for term in REQUIRED_TERMS:
        assert term in doc


def test_critic_evaluator_readonly_api_action_endpoint_contract_is_proposed_only():
    doc = _doc_text()
    start = doc.index("## Endpoint contract proposal")
    end = doc.index("## Request contract")
    section = doc[start:end]

    assert (
        "POST /api/agentic-approvals/{approval_request_id}/critic-evaluator-readonly"
        in section
    )
    for phrase in [
        "not implemented in this checkpoint",
        "explicit user action only",
        "read-only",
        "deterministic",
        "no storage writes",
        "no LLM calls",
        "no approval mutation",
        "no scoring change",
        "no pipeline wiring",
        "no application execution/submission",
    ]:
        assert phrase in section


def test_critic_evaluator_readonly_api_action_request_contract_terms_are_present():
    doc = _doc_text()
    start = doc.index("## Request contract")
    end = doc.index("## Response contract")
    section = doc[start:end]

    for term in REQUEST_CONTRACT_TERMS:
        assert term in section


def test_critic_evaluator_readonly_api_action_response_contract_terms_are_present():
    doc = _doc_text()
    start = doc.index("## Response contract")
    end = doc.index("## Error handling contract")
    section = doc[start:end]

    for term in RESPONSE_CONTRACT_TERMS:
        assert term in section


def test_critic_evaluator_readonly_api_action_links_are_present():
    path = "docs/critic_evaluator_readonly_api_action_readiness_checkpoint.md"

    assert path in README_PATH.read_text()
    assert path in READINESS_PATH.read_text()


def test_step_202_allowed_files_are_docs_tests_only():
    for path in STEP_202_ALLOWED_FILES:
        assert Path(path).exists(), path
        assert path == "README.md" or path.startswith("docs/") or path.startswith("tests/")

    forbidden_prefixes = (
        "src/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in STEP_202_ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes)
