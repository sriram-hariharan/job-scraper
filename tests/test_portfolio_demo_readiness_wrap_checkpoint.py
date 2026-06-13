from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/portfolio_demo_readiness_wrap_checkpoint.md"

REQUIRED_TERMS = [
    "Portfolio demo readiness wrap checkpoint",
    "portfolio demo readiness",
    "docs/tests only",
    "ApplyLens AI",
    "job scraper app",
    "agentic AI layer",
    "completed portfolio scope",
    "Agent State foundation",
    "trace recorder",
    "Relevance Prefilter Agent",
    "Deduplication Agent",
    "JD Intelligence Agent",
    "Final Application Scoring Agent",
    "read-only Agent Trace API endpoint",
    "read-only Agent Trace UI panel",
    "trace UI polish",
    "Critic/Evaluator runtime skeleton",
    "explicit read-only Critic/Evaluator API action",
    "deterministic evaluator",
    "trace-only evaluation inputs",
    "no live LLM call",
    "no model provider call",
    "no storage writes",
    "no schema migration",
    "no approval mutation",
    "no ranking change",
    "no scoring change",
    "no application execution",
    "no application submission",
    "no pipeline wiring",
    "no scheduler",
    "no background task",
    "no file export",
    "demo flow",
    "portfolio positioning",
    "what is implemented",
    "what is intentionally not implemented",
    "safety guarantees",
    "local demo checklist",
    "resume bullet ideas",
    "GitHub README checklist",
    "rollback plan",
    "verification plan",
    "stop feature work after this checkpoint",
    "How to explain this in interviews",
    "Stop condition",
]

ALLOWED_CHANGED = {
    "tests/test_full_agentic_ai_trace_contract_readiness_no_runtime_change.py",
    "docs/full_agentic_ai_trace_contract_readiness_no_runtime_change.md",
    "tests/test_full_agentic_ai_schema_contract_audit_no_runtime_change.py",
    "docs/full_agentic_ai_schema_contract_audit_no_runtime_change.md",
    "tests/test_full_agentic_ai_current_state_audit_no_runtime_change.py",
    "docs/full_agentic_ai_current_state_audit_no_runtime_change.md",
    "tests/test_agentic_review_ui_compaction_polish_no_backend_change.py",
    "docs/agentic_review_ui_compaction_polish_no_backend_change.md",
    "docs/full_fledged_agentic_ai_app_roadmap.md",
    "tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py",
    "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
    "tests/test_agentic_review_ui_portfolio_polish_no_backend_change.py",
    "docs/agentic_review_ui_portfolio_polish_no_backend_change.md",
    "src/app/static/app_redesign.css",
    "src/app/static/agentic_review.js",
    "docs/portfolio_demo_readiness_wrap_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    "tests/test_agentic_docs.py",
}

def _changed_files():
    tracked = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return set(tracked + untracked)

def test_portfolio_demo_readiness_doc_exists_and_has_required_terms():
    assert DOC.exists()
    text = DOC.read_text()
    missing = [term for term in REQUIRED_TERMS if term not in text]
    assert not missing

def test_portfolio_demo_readiness_doc_is_linked():
    link = "docs/portfolio_demo_readiness_wrap_checkpoint.md"
    assert link in (ROOT / "README.md").read_text()
    assert link in (ROOT / "docs/orchestrator_readiness.md").read_text()

def test_portfolio_demo_readiness_is_docs_tests_only():
    changed = _changed_files()
    extra = sorted(path for path in changed if path not in ALLOWED_CHANGED)
    assert not extra

    approved_ui_runtime_paths = {
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
    }
    runtime_paths = [
        path for path in changed
        if path not in approved_ui_runtime_paths
        and (
            path.startswith("src/")
            or path == "application_execution_queue.py"
            or path.endswith(".js")
            or path.endswith(".html")
            or path.endswith(".css")
        )
    ]
    assert not runtime_paths
