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
    "src/app/api.py",
    "tests/test_agent_trace_api.py",
    "tests/test_agent_trace_service_summary_readonly_no_api_change.py",
    "src/app/services.py",
    "tests/test_agent_trace_summary_helper_no_pipeline_change.py",
    "src/storage/agent_trace/store.py",
    "src/agents/trace.py",
    "tests/test_agent_stage_trace_bundle_no_pipeline_change.py",
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
    "tests/test_agent_trace_readonly_api_endpoint_no_ui_no_writes.py",
    "tests/test_agent_trace_ui_readiness_checkpoint.py",
    "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
    "tests/test_agentic_review_ui_portfolio_polish_no_backend_change.py",
    "tests/test_critic_evaluator_readonly_api_action_no_storage_no_llm.py",
    "docs/agentic_review_ui_portfolio_polish_no_backend_change.md",
    "src/app/static/app_redesign.css",
    "src/app/static/agentic_review.js",
    "docs/portfolio_demo_readiness_wrap_checkpoint.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    "tests/test_agentic_docs.py",
    "src/agents/relevance_prefilter.py",
    "tests/test_relevance_prefilter_agent_trace_wrapper_no_behavior_change.py",
    "src/agents/deduplication.py",
    "tests/test_deduplication_agent_trace_wrapper_no_behavior_change.py",
    "src/agents/jd_intelligence.py",
    "tests/test_jd_intelligence_agent_trace_wrapper_no_behavior_change.py",
    "src/agents/final_application_scoring.py",
    "tests/test_final_application_scoring_agent_trace_wrapper_no_behavior_change.py",
    "tests/test_agent_stage_wrapper_trace_summary_consistency_no_runtime_change.py",
    "tests/test_live_jd_intelligence_dry_run_contract_no_pipeline_change.py",
    "tests/test_manual_jd_intelligence_dry_run_surface_no_pipeline_change.py",
    "src/agents/resume_match_agent.py",
    "tests/test_resume_match_dry_run_contract_no_pipeline_change.py",
    "tests/test_manual_resume_match_dry_run_surface_no_pipeline_change.py",
    "src/agents/tailoring_decision_agent.py",
    "tests/test_tailoring_suggestion_dry_run_contract_no_pipeline_change.py",
    "tests/test_manual_tailoring_suggestion_dry_run_surface_no_pipeline_change.py",
    "src/agents/critic_agent.py",
    "tests/test_critic_guardrail_dry_run_contract_no_pipeline_change.py",
    "tests/test_manual_critic_guardrail_dry_run_surface_no_pipeline_change.py",
    "src/agents/job_prioritization_agent.py",
    "tests/test_strategy_recommendation_dry_run_contract_no_pipeline_change.py",
    "tests/test_manual_strategy_recommendation_dry_run_surface_no_pipeline_change.py",
    "tests/test_shadow_agentic_workflow_chain_dry_run_no_pipeline_change.py",
    "tests/test_manual_shadow_agentic_workflow_chain_surface_no_pipeline_change.py",
    "tests/test_shadow_recommendation_handoff_dry_run_no_pipeline_change.py",
    "tests/test_human_decision_capture_dry_run_no_pipeline_change.py",
    "tests/test_human_approved_action_plan_dry_run_no_pipeline_change.py",
    "tests/test_review_packet_preview_dry_run_no_pipeline_change.py",
    "tests/test_approval_request_preview_dry_run_no_pipeline_change.py",
    "tests/test_approval_creation_gate_dry_run_no_pipeline_change.py",
    "tests/test_guarded_approval_request_creation_manual_only.py",
    "tests/test_guarded_approval_creation_observability_no_writes.py",
    "tests/test_approval_request_readback_detail_surface_no_writes.py",
    "tests/test_approval_status_transition_preview_dry_run_no_writes.py",
    "tests/test_guarded_approval_status_transition_manual_only.py",
    "tests/test_approval_status_transition_observability_no_writes.py",
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

    approved_runtime_paths = {
        "src/app/api.py",
        "src/app/services.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "src/storage/agent_trace/store.py",
        "src/agents/trace.py",
        "src/agents/relevance_prefilter.py",
        "src/agents/deduplication.py",
        "src/agents/jd_intelligence.py",
        "src/agents/final_application_scoring.py",
        "src/agents/resume_match_agent.py",
        "src/agents/tailoring_decision_agent.py",
        "src/agents/critic_agent.py",
        "src/agents/job_prioritization_agent.py",
    }
    runtime_paths = [
        path for path in changed
        if path not in approved_runtime_paths
        and (
            path.startswith("src/")
            or path == "application_execution_queue.py"
            or path.endswith(".js")
            or path.endswith(".html")
            or path.endswith(".css")
        )
    ]
    assert not runtime_paths
