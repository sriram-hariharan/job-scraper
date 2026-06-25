from hashlib import sha256
from pathlib import Path


DOC_PATH = Path("docs/agent_trace_ui_readiness_checkpoint.md")

PROTECTED_FILE_HASHES = {
    "src/app/api.py": "bb4755cd3d74c72e7ed0af24de9d617c0ff568b61639b6d61e59c057348f424a",
    "src/app/static/agentic_review.js": "f7cdf115e412f34094e80e71b18e86f94365715c6f5010faa8e2ba7fe41daeff",
    "src/agents/trace.py": "f4527c224ea0d3fc05d14883bb036311e7120a6a9abc9a54a58396e76ddada41",
    "src/agents/agent_state.py": "6daaa56b2af95e36547e89e928c354038b5bab6ff2cc35e49bf259d0d9d1cdac",
    "src/agents/relevance_prefilter.py": "5be6d21c27b720472daef6f85f813bc6561c90f9f8abfcfc09e88a5cd36a490b",
    "src/agents/deduplication.py": "7aeb6e831197a63f66b83fff898ccef77db177e39594464e1c215cffaed432b8",
    "src/agents/jd_intelligence.py": "1f79df7e4349ce9ae7b1e5bad185a7958d86aa654d7c8bbd77634f59f529f81e",
    "src/agents/final_application_scoring.py": "eed7eed337b860345f38005c1f898732c8c809f6087e7fbbf33de6f4ad7ed2fd",
    "src/agents/workflow_runner.py": "bbdaf6d1dcc829809de6ee62a864ef5048a73ef63c288173f676a42ca1e6cd05",
    "src/storage/agent_state/schema.sql": "d7e91c2b7e6e7720a8aeb64b7292d9ce28d6008b14c1d149f56a6c1fa39b3526",
    "src/storage/agent_state/store.py": "35f23fe4421b6a880728e940a95cdd62268c1fbe2f92c823a385af7c40102cf9",
    "src/storage/agent_state/migration_runner.py": "488e25670d7043c6a5b938441e13d7c066bbcf5fccda1a41401723650e61969e",
    "src/storage/agentic_approvals/store.py": "9cd153ba1bdcac520c1ea0d3b04374671e8ace6c2635a60fce2544526201f5bf",
    "src/storage/agentic_approvals/schema.sql": "57e84094cdbd3a4e8542fd205d89bfde18179c5d07c15084354f31f77bf5d98f",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _doc_text() -> str:
    return DOC_PATH.read_text()


def _file_hash(path: str) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def test_agent_trace_ui_readiness_doc_exists_and_has_required_sections():
    doc = _doc_text()

    required_sections = [
        "# Agent Trace UI readiness checkpoint",
        "## Current foundation inventory",
        "## Proposed next implementation path",
        "## Intended API contract for next implementation step",
        "## Intended UI contract for next implementation step",
        "## Safety contract terms",
        "## Explicit separation",
        "## Rollback plan",
        "## Verification plan for future implementation",
    ]
    for section in required_sections:
        assert section in doc


def test_agent_trace_ui_readiness_doc_contains_required_foundation_inventory():
    doc = _doc_text()

    required_terms = [
        "JobApplicationContext",
        "agent_runs",
        "agent_steps",
        "migration runner",
        "trace recorder",
        "Relevance Prefilter Agent wrapper",
        "Deduplication Agent wrapper",
        "JD Intelligence Agent wrapper",
        "Final Application Scoring Agent wrapper",
    ]
    for term in required_terms:
        assert term in doc


def test_agent_trace_ui_readiness_doc_contains_future_api_and_ui_contracts():
    doc = _doc_text()

    required_terms = [
        "read-only backend trace retrieval endpoint",
        "read-only frontend trace panel",
        "no edits to workflow runner in first UI step",
        "no live pipeline wiring in first UI step",
        "read-only endpoint",
        "caller-supplied run or approval identifier",
        "returns agent run metadata and ordered agent steps",
        "supports empty trace safely",
        "does not create agent runs",
        "does not create agent steps",
        "does not mutate approvals",
        "does not execute pipeline",
        "read-only trace panel",
        "shows ordered agent steps",
        "shows agent name, status, started/completed timestamps if supplied, input/output summary, validation_json, and safety metadata",
        "empty-state message when no trace exists",
        "no approve/apply/submit/run/retry/export action",
    ]
    for term in required_terms:
        assert term in doc


def test_agent_trace_ui_readiness_doc_contains_safety_terms_and_separation():
    doc = _doc_text()

    required_terms = [
        "no behavior change",
        "no API behavior change",
        "no UI behavior change",
        "no pipeline wiring",
        "no scheduler",
        "no background task",
        "no storage writes",
        "no schema migration",
        "no file export",
        "no application execution",
        "no application submission",
        "read-only",
        "deterministic",
        "prefilter relevance",
        "deduplication",
        "JD intelligence",
        "final application scoring",
        "LLM evaluation",
        "application execution",
        "application submission",
    ]
    for term in required_terms:
        assert term in doc


def test_readme_and_orchestrator_readiness_link_to_checkpoint_doc():
    path = "docs/agent_trace_ui_readiness_checkpoint.md"

    assert path in Path("README.md").read_text()
    assert path in Path("docs/orchestrator_readiness.md").read_text()


def test_protected_runtime_files_match_checkpoint_hashes_without_git():
    later_readonly_api_step_exists = Path(
        "docs/agent_trace_readonly_api_endpoint_no_ui_no_writes.md"
    ).exists()
    later_readonly_api_paths = {
        "src/app/api.py",
        "src/storage/agent_state/store.py",
    }
    later_readonly_ui_step_exists = Path("docs/agent_trace_readonly_ui_panel_no_api_no_writes.md").exists()
    later_readonly_ui_paths = {
        "src/app/static/agentic_review.js",
    }

    for path, expected_hash in PROTECTED_FILE_HASHES.items():
        assert Path(path).exists()
        if later_readonly_api_step_exists and path in later_readonly_api_paths:
            continue
        if later_readonly_ui_step_exists and path in later_readonly_ui_paths:
            continue
        assert _file_hash(path) == expected_hash
