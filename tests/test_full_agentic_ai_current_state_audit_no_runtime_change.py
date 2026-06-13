from pathlib import Path


def test_full_agentic_ai_current_state_audit_doc_exists():
    doc = Path("docs/full_agentic_ai_current_state_audit_no_runtime_change.md")
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")

    required = [
        "Full Agentic AI Current-State Audit",
        "No runtime behavior is changed.",
        "No API behavior is changed.",
        "No storage schema is changed.",
        "No scheduler behavior is changed.",
        "No pipeline behavior is changed.",
        "The repository already contains substantial agentic infrastructure.",
        "src/storage/agent_state/schema.sql",
        "src/storage/agent_trace/schema.sql",
        "src/storage/agent_feedback/schema.sql",
        "src/storage/agentic_approvals/schema.sql",
        "src/agents/relevance_prefilter.py",
        "src/agents/deduplication.py",
        "src/agents/jd_intelligence.py",
        "src/agents/resume_match_agent.py",
        "src/agents/tailoring_decision_agent.py",
        "src/agents/final_application_scoring.py",
        "src/agents/critic_agent.py",
        "src/agents/critic_evaluator.py",
        "full-agentic-ai-schema-contract-audit-no-runtime-change",
        "Do not add new runtime behavior yet.",
    ]

    for phrase in required:
        assert phrase in text


def test_full_agentic_ai_current_state_audit_referenced_core_files_exist():
    required_paths = [
        "docs/full_fledged_agentic_ai_app_roadmap.md",
        "src/agents/context.py",
        "src/agents/trace.py",
        "src/storage/agent_state/schema.sql",
        "src/storage/agent_state/store.py",
        "src/storage/agent_trace/schema.sql",
        "src/storage/agent_trace/store.py",
        "src/storage/agent_feedback/schema.sql",
        "src/storage/agent_feedback/store.py",
        "src/storage/agentic_approvals/schema.sql",
        "src/storage/agentic_approvals/store.py",
        "src/app/api.py",
        "src/app/services.py",
        "src/app/profile_ui.py",
        "src/app/static/agentic_review.js",
    ]

    for path in required_paths:
        assert Path(path).exists(), path
