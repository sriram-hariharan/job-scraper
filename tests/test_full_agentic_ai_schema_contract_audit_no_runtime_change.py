from pathlib import Path


def test_full_agentic_ai_schema_contract_audit_doc_exists():
    doc = Path("docs/full_agentic_ai_schema_contract_audit_no_runtime_change.md")
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")

    required = [
        "Full Agentic AI Schema/Store Contract Audit",
        "No runtime behavior is changed.",
        "No API behavior is changed.",
        "No storage schema is changed.",
        "No migration is executed.",
        "No scheduler behavior is changed.",
        "No pipeline behavior is changed.",
        "src/storage/agent_state/schema.sql",
        "src/storage/agent_state/store.py",
        "src/storage/agent_trace/schema.sql",
        "src/storage/agent_trace/store.py",
        "src/storage/agent_feedback/schema.sql",
        "src/storage/agent_feedback/store.py",
        "src/storage/agentic_approvals/schema.sql",
        "src/storage/agentic_approvals/store.py",
        "full-agentic-ai-trace-contract-readiness-no-runtime-change",
        "Do not implement new persistent agent behavior yet.",
    ]

    for phrase in required:
        assert phrase in text


def test_full_agentic_ai_schema_contract_core_storage_files_exist():
    required_paths = [
        "src/storage/agent_state/schema.sql",
        "src/storage/agent_state/store.py",
        "src/storage/agent_trace/schema.sql",
        "src/storage/agent_trace/store.py",
        "src/storage/agent_feedback/schema.sql",
        "src/storage/agent_feedback/store.py",
        "src/storage/agentic_approvals/schema.sql",
        "src/storage/agentic_approvals/store.py",
    ]

    for path in required_paths:
        assert Path(path).exists(), path
