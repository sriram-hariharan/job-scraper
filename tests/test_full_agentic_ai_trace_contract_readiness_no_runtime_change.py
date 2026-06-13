from pathlib import Path


def test_full_agentic_ai_trace_contract_readiness_doc_exists():
    doc = Path("docs/full_agentic_ai_trace_contract_readiness_no_runtime_change.md")
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")

    required = [
        "Full Agentic AI Trace Contract Readiness Audit",
        "No runtime behavior is changed.",
        "No API behavior is changed.",
        "No storage schema is changed.",
        "No migration is executed.",
        "No scheduler behavior is changed.",
        "No pipeline behavior is changed.",
        "src/storage/agent_trace/schema.sql",
        "src/storage/agent_trace/store.py",
        "src/agents/trace.py",
        "src/app/services.py",
        "src/app/api.py",
        "src/app/profile_ui.py",
        "src/app/static/agentic_review.js",
        "Run-level trace",
        "Job-level trace",
        "Scan-level trace",
        "No application execution.",
        "No application submission.",
        "No approval mutation.",
        "No scoring mutation.",
        "full-agentic-ai-stage-wrapper-gap-audit-no-runtime-change",
        "Do not implement trace behavior yet.",
    ]

    for phrase in required:
        assert phrase in text


def test_full_agentic_ai_trace_contract_core_files_exist():
    required_paths = [
        "src/storage/agent_trace/schema.sql",
        "src/storage/agent_trace/store.py",
        "src/agents/trace.py",
        "src/app/services.py",
        "src/app/api.py",
        "src/app/profile_ui.py",
        "src/app/static/agentic_review.js",
    ]

    for path in required_paths:
        assert Path(path).exists(), path
