from pathlib import Path

from src.app import services


def test_queue_ui_renders_job_location_below_title():
    source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    assert "row.job_location" in source
    assert "queue-job-location" in source
    assert "queue-simple-location" in source
    assert ".queue-job-location" in css
    assert ".queue-simple-location" in css
    assert "color: var(--app-muted)" in css
    assert "font-size: 12px" in css


def test_queue_ui_labels_allowed_unknown_timestamps():
    source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    assert 'freshness_status === "unknown_timestamp_allowed"' in source
    assert "Timestamp unavailable" in source
    assert "timestamp-unavailable-label" in source
    assert ".timestamp-unavailable-label" in css


def test_queue_ui_renders_job_prioritization_advisory_separately():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "buildAdvisoryPriorityHtml" in source
        assert "advisory_priority" in source
        assert "existing_action" in source
        assert "Ready for review" in source
        assert "Review later" in source
        assert "Watch source" in source
        assert "<summary>Why?</summary>" in source
        assert "Raw action" in source
        assert "No clear resume match" in source
        assert "Borderline match" in source
        assert "Tailoring may improve fit" in source
        assert "Packet unavailable" in source
        assert "queue-advisory-kicker" not in source
        assert "row.action" in source

    assert ".queue-advisory-priority" in css
    assert ".queue-advisory-pill--skip_for_now" in css
    assert ".queue-advisory-pill--watch_source" in css
    assert ".queue-recommendation-details" in css
    assert ".queue-packet-pill--ready" in css
    assert ".queue-packet-pill--blocked" in css
    assert "job_prioritization_recommendations.csv" in services_source
    assert "JOB_PRIORITIZATION_OVERLAY_FIELDS" in services_source


def test_queue_ui_uses_compact_decision_chips_and_details():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "formatQueueActionLabel" in source
        assert "Ready for review" in source
        assert "Review resume choice" in source
        assert "Tailor first" in source
        assert "Review later" in source
        assert "buildPacketStatusChipHtml" in source
        assert "Packet ready" in source
        assert "No packet" in source
        assert "queue-recommendation-details" in source
        assert "<summary>Why?</summary>" in source
        assert "Action: ${" not in source
        assert "Packet: ${" not in source
        assert "Block: ${" not in source

    assert "flex-direction: row" in css
    assert ".queue-packet-pill" in css
    assert ".queue-recommendation-detail-row" in css


def test_queue_ui_uses_simplified_job_seeker_columns():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    app_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    planning_markup = Path("src/app/planning_ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert 'label: "Rank"' in source
        assert 'label: "Job title"' in source
        assert 'label: "Posted at"' in source
        assert 'label: "Recommendation"' in source
        assert 'label: "Match"' in source
        assert 'label: "Selected Resume"' in source
        assert 'label: "Review"' in source
        assert "Review job" in source
        assert "Review later" in source
        assert "Choose resume" in source
        assert "Close resume match" in source
        assert "No clear resume match" in source or "No resume match" in source
        assert "Runner-up resume" in source
        assert "Score gap" in source
        assert "Missing req count" in source or "Missing requirements" in source
        assert "Next step" in source
        assert "Priority reason" in source
        assert "A packet is a review bundle for this job." in source

    for markup in (app_markup, planning_markup):
        assert "Recommendation" in markup
        assert "Posted at" in markup
        assert "Selected Resume" in markup
        assert "Review" in markup
        assert ">Apply<" not in markup

    assert ".queue-job-summary" in css
    assert ".queue-status-stack" in css
    assert ".queue-workspace-pill" in css


def test_phase77b_executive_detail_and_packet_help_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    app_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    planning_markup = Path("src/app/planning_ui.py").read_text(encoding="utf-8")

    assert 'key: "posted_at", label: "Posted at", type: "date"' in app_source
    assert 'key: "runner_up_resume", label: "Runner-up resume"' in app_source
    assert 'key: "score_gap", label: "Score gap"' in app_source
    assert 'key: "missing_requirement_count", label: "Missing req count"' in app_source
    assert 'key: "next_step", label: "Next step"' in app_source
    assert 'key: "queue_priority_reason", label: "Priority reason"' in app_source
    assert 'data-col-key="runner_up_resume"' in app_markup
    assert 'data-col-key="score_gap"' in app_markup
    assert 'data-col-key="missing_requirement_count"' in app_markup
    assert 'data-col-key="next_step"' in app_markup
    assert 'data-col-key="queue_priority_reason"' in app_markup

    for source in (app_source, planning_source, app_markup, planning_markup):
        assert "A packet is a review bundle for this job." in source
        assert "It does not apply to the job." in source

    assert "executive-view-mode-row--table" in app_markup
    queue_header_index = app_markup.index("<h2>Queue Table</h2>")
    toggle_index = app_markup.index("executive-view-mode-row--table")
    controls_start = app_markup.index('<section class="card controls-card">')
    controls_end = app_markup.index('<div class="subtext pipeline-run-meta"')
    assert toggle_index > queue_header_index
    assert "executive-view-mode-row--table" not in app_markup[controls_start:controls_end]


def test_phase77b_recommendation_has_single_why_control_per_cell():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "buildQueueRecommendationCellHtml" in source or "buildPlanningRecommendationCellHtml" in source
        assert "${buildAdvisoryPriorityHtml(row)}" not in source
        assert "${buildTailoringDecisionHtml(row)}" not in source
        assert "${buildOperatorReviewHtml(row)}" not in source
        assert "<summary>Why?</summary>" in source


def test_phase77c_table_polish_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    app_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    assert "binary-toggle--small" in app_markup
    assert "executive-view-mode-row--table" in app_markup
    assert "Posted:" not in app_source
    assert "Posted:" not in planning_source
    assert 'key: "posted_at", label: "Posted at", type: "date"' in app_source
    assert 'key: "posted_at", label: "Posted at", type: "date"' in planning_source
    assert "grid-template-columns: minmax(0, 1fr) auto" in css
    assert "justify-self: end" in css
    assert "body .multi-select-trigger-icon" in css
    assert "border-radius: 0 !important" in css
    assert ".table-wrap thead .sort-header-btn" in css


def test_queue_ui_renders_tailoring_decision_advisory_separately():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "buildTailoringDecisionHtml" in source
        assert "tailoring_decision" in source
        assert "tailoring_reason_codes" in source
        assert "No tailoring needed" in source
        assert "Tailor before apply" in source
        assert "Do not tailor" in source
        assert "<summary>Why?</summary>" in source
        assert "queue-tailoring-kicker" not in source
        assert "row.action" in source

    assert ".queue-tailoring-decision" in css
    assert ".queue-tailoring-pill--do_not_tailor" in css
    assert ".queue-tailoring-pill--tailor_before_apply" in css
    assert "tailoring_decision_recommendations.csv" in services_source
    assert "TAILORING_DECISION_OVERLAY_FIELDS" in services_source


def test_queue_ui_renders_operator_review_advisory_separately():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "buildOperatorReviewHtml" in source
        assert "operator_review_lane" in source
        assert "operator_review_reason_codes" in source
        assert "Ready for review" in source
        assert "Skip for now" in source
        assert "<summary>Why?</summary>" in source
        assert "queue-operator-kicker" not in source
        assert "row.action" in source

    assert ".queue-operator-review" in css
    assert ".queue-operator-pill--ready_to_apply" in css
    assert ".queue-operator-pill--hold_or_skip" in css
    assert "operator_review_recommendations.csv" in services_source
    assert "OPERATOR_REVIEW_OVERLAY_FIELDS" in services_source


def test_agentic_workflow_summary_ui_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    profile_source = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source, profile_source):
        assert "renderAgenticWorkflowSummaryPanel" in source
        assert "Agentic Workflow Summary" in source
        assert "ready_to_apply_count" in source
        assert "hold_or_skip_count" in source
        assert "missing_artifacts" in source
        assert "summary_markdown" in source
        assert "escapeHtml(markdown)" in source

    assert "No agentic workflow summary recorded for this run." in profile_source
    assert ".agentic-workflow-summary-card" in css
    assert ".agentic-workflow-markdown" in css
    assert "agentic_workflow_summary.json" in services_source
    assert "agentic_workflow_summary.md" in services_source
    assert "agentic_workflow_summary_json" in services_source
    assert "agentic_workflow_summary_md" in services_source


def test_agentic_workflow_verification_ui_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    profile_source = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source, profile_source):
        assert "renderAgenticWorkflowVerificationPanel" in source
        assert "Agentic Workflow Verification" in source
        assert "validation_status" in source
        assert "checked_artifacts" in source
        assert "missing_artifacts" in source
        assert "reason_codes" in source
        assert "consistency_checks" in source
        assert "verification_json" in source

    assert "No agentic workflow verification recorded for this run." in profile_source
    assert ".agentic-workflow-verification-card" in css
    assert ".agentic-workflow-verification-status--passed" in css
    assert ".agentic-workflow-verification-status--warning" in css
    assert ".agentic-workflow-verification-status--failed" in css
    assert "agentic_workflow_verification.json" in services_source
    assert "agentic_workflow_verification_json" in services_source


def test_agentic_workflow_manifest_ui_contract():
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Agentic Workflow Manifest" in review_source
    assert "agentic_workflow_manifest" in review_source
    assert "manifest_json" in review_source
    assert "manifest_markdown" in review_source
    assert "ordered_agent_keys" in review_source
    assert "generated_artifact_kinds" in review_source
    assert "artifact_dependency_order" in review_source
    assert "mutates_production_decisions" in review_source
    assert "No agentic workflow manifest recorded for this run." in review_source
    assert "Manifest markdown" in review_source
    assert "escapeHtml(markdown)" in review_source

    assert ".agentic-workflow-manifest-card" in review_css
    assert ".agentic-review-manifest-agent" in review_css
    assert ".agentic-review-manifest-metrics" in review_css
    assert ".agentic-review-manifest-agent-pills" in review_css

    assert "agentic_workflow_manifest.json" in services_source
    assert "agentic_workflow_manifest.md" in services_source
    assert "agentic_workflow_manifest_json" in services_source
    assert "agentic_workflow_manifest_md" in services_source
    assert "_agentic_workflow_manifest_from_artifacts" in services_source


def test_agentic_workflow_execution_plan_ui_contract():
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Agentic Workflow Execution Plan" in review_source
    assert "agentic_workflow_execution_plan" in review_source
    assert "plan_json" in review_source
    assert "plan_markdown" in review_source
    assert "ordered_steps" in review_source
    assert "execution_mode" in review_source
    assert "execution_enabled" in review_source
    assert "execution_status" in review_source
    assert "No agentic workflow execution plan recorded for this run." in review_source
    assert "Execution plan markdown" in review_source
    assert "escapeHtml(markdown)" in review_source

    assert ".agentic-workflow-execution-plan-card" in review_css
    assert ".agentic-review-plan-step" in review_css
    assert ".agentic-review-plan-metrics" in review_css

    assert "agentic_workflow_execution_plan.json" in services_source
    assert "agentic_workflow_execution_plan.md" in services_source
    assert "agentic_workflow_execution_plan_json" in services_source
    assert "agentic_workflow_execution_plan_md" in services_source
    assert "_agentic_workflow_execution_plan_from_artifacts" in services_source


def test_agentic_workflow_dry_run_ui_contract():
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Agentic Workflow Dry Run" in review_source
    assert "agentic_workflow_dry_run" in review_source
    assert "result_json" in review_source
    assert "report_markdown" in review_source
    assert "ordered_step_results" in review_source
    assert "runner_version" in review_source
    assert "executed_step_count" in review_source
    assert "did_execute" in review_source
    assert "would_trace" in review_source
    assert "No agentic workflow dry run recorded for this run." in review_source
    assert "Dry-run report markdown" in review_source
    assert "escapeHtml(markdown)" in review_source

    assert ".agentic-workflow-dry-run-card" in review_css
    assert ".agentic-review-dry-run-step" in review_css
    assert ".agentic-review-dry-run-metrics" in review_css

    assert "agentic_workflow_dry_run_result.json" in services_source
    assert "agentic_workflow_dry_run_report.md" in services_source
    assert "agentic_workflow_dry_run_result_json" in services_source
    assert "agentic_workflow_dry_run_report_md" in services_source
    assert "_agentic_workflow_dry_run_from_artifacts" in services_source


def test_proposal_only_mutation_plan_agentic_review_ui_contract():
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Proposal-Only Mutation Plan" in review_source
    assert "proposal_only_mutation_plan" in review_source
    assert "renderProposalOnlyMutationPlanSection" in review_source
    assert "proposal_only_mutation_planner.EXECUTION_MODE" in services_source or "proposal_only_mutation_planner" in services_source
    assert "proposal_only_mutation_plan_result.json" in services_source
    assert "proposal_only_mutation_plan_report.md" in services_source
    assert "proposal_only_mutation_plan_result_json" in services_source
    assert "proposal_only_mutation_plan_report_md" in services_source
    assert "_proposal_only_mutation_plan_from_artifacts" in services_source
    assert "No proposal-only mutation plan artifacts recorded for this run yet." in review_source
    assert "can_mutate" in review_source
    assert "can_approve" in review_source
    assert "did_store_approval" in review_source
    assert "Required future gates" in review_source
    assert "Proposal mutation types" in review_source
    assert "Blocked execution reasons" in review_source
    assert "Proposal plan report markdown" in review_source
    assert "escapeHtml(markdown)" in review_source

    assert ".proposal-only-mutation-plan-card" in review_css
    assert ".proposal-only-mutation-plan-metrics" in review_css
    assert ".proposal-only-mutation-plan-warning" in review_css
    assert ".proposal-only-mutation-plan-notice" in review_css

    for forbidden in [
        "proposalPlanApprove",
        "proposalPlanReject",
        "proposal_only_mutation_approve",
        "proposal_only_mutation_reject",
        "/proposal-approval",
        "/mutation-execution",
    ]:
        assert forbidden not in review_source
        assert forbidden not in services_source


def test_read_only_adapter_preflight_ui_contract():
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Read-Only Adapter Preflight" in review_source
    assert "read_only_adapter_preflight" in review_source
    assert "renderReadOnlyAdapterPreflightSection" in review_source
    assert "renderReadOnlyAdapterPreflightRow" in review_source
    assert "adapter_preflight_results" in review_source
    assert "planned_adapter_count" in review_source
    assert "executable_adapter_count" in review_source
    assert "ready_read_only_contract_count" in review_source
    assert "needs_adapter_count" in review_source
    assert "blocked_count" in review_source
    assert "preflight_status" in review_source
    assert "allowed_execution_mode" in review_source
    assert "execution_enabled" in review_source
    assert "did_execute" in review_source
    assert "No read-only adapter preflight recorded for this run." in review_source
    assert "Preflight report markdown" in review_source
    assert "no agents executed" in review_source

    assert ".read-only-adapter-preflight-card" in review_css
    assert ".read-only-adapter-preflight-metrics" in review_css
    assert ".read-only-adapter-preflight-row" in review_css
    assert ".read-only-adapter-preflight-pills" in review_css

    assert "read_only_adapter_preflight.json" in services_source
    assert "read_only_adapter_preflight.md" in services_source
    assert "read_only_adapter_preflight_json" in services_source
    assert "read_only_adapter_preflight_md" in services_source
    assert "_read_only_adapter_preflight_from_artifacts" in services_source


def test_manual_read_only_adapter_chain_empty_read_model_is_safe():
    payload = services._manual_read_only_adapter_chain_from_artifacts([])

    assert payload["present"] is False
    assert payload["available"] is False
    assert payload["validation_status"] == "missing"
    assert payload["did_execute_chain"] is False
    assert payload["did_mutate_production"] is False
    assert payload["adapter_execution_order"] == []
    assert payload["summary"] == {}
    assert payload["reason_codes"] == []
    assert payload["warning_codes"] == []


def test_explicit_read_only_chain_generator_empty_read_model_is_safe():
    payload = services._explicit_read_only_chain_artifact_generation_from_artifacts([])

    assert payload["present"] is False
    assert payload["available"] is False
    assert payload["validation_status"] == "missing"
    assert payload["did_run_chain"] is False
    assert payload["did_mutate_production"] is False
    assert payload["require_explicit_input"] is False
    assert payload["require_explicit_output_dir"] is False
    assert payload["queue_input_artifact_path"] == ""
    assert payload["output_dir"] == ""
    assert payload["chain_result_summary"] == {}
    assert payload["generator_artifacts"] == []
    assert payload["reason_codes"] == []
    assert payload["warning_codes"] == []


def test_agentic_review_dedicated_page_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    profile_source = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    profile_ui_source = Path("src/app/profile_ui.py").read_text(encoding="utf-8")
    shell_source = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    api_source = Path("src/app/api.py").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    common_css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    executive_ui_source = Path("src/app/ui.py").read_text(encoding="utf-8")
    planning_ui_source = Path("src/app/planning_ui.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source, profile_source):
        assert "View Agentic Review" not in source
        assert "agentic-review-link-card" not in source

    assert "pipeline-run-agentic-review-btn" in profile_source
    assert 'aria-label="Agentic review"' in profile_source
    assert 'data-tooltip="View"' in profile_source
    assert 'data-tooltip="Agentic review"' in profile_source
    assert '/profile/pipeline-runs/${encodeURIComponent(run.run_id || "")}/agentic-review' in profile_source
    assert '<th>Actions</th>' in profile_ui_source
    assert '<th>View</th>' not in profile_ui_source
    assert "pipeline-run-actions-cell" in profile_source
    assert "pipeline-run-icon-btn pipeline-run-view-btn" in profile_source
    assert "pipeline-run-icon-btn pipeline-run-agentic-review-btn" in profile_source
    assert "pipeline-run-action-icon--view" in profile_source
    assert "pipeline-run-action-icon--agentic" in profile_source
    assert '("Scheduler", "/scheduler", "S")' in shell_source
    assert '("Agentic Review", "/agentic-review", "AR")' not in shell_source

    assert '@router.get("/agentic-review"' not in profile_ui_source
    assert '@router.get("/profile/pipeline-runs/{run_id}/agentic-review"' in profile_ui_source
    assert '@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")' in api_source
    route_source = profile_ui_source.split('@router.get("/profile/pipeline-runs/{run_id}/agentic-review"', 1)[1]
    route_source = route_source.split('@router.get("/profile/preferences"', 1)[0]
    assert "Agentic Workflow Summary" in profile_ui_source
    assert "Agentic Workflow Verification" in profile_ui_source
    assert "Agent Trace" in profile_ui_source
    assert "Overview" in profile_ui_source
    assert "Advisory Board" in profile_ui_source
    assert "Artifacts / Diagnostics" in profile_ui_source
    assert "Job Prioritization" in profile_ui_source
    assert "Tailoring Decision" in profile_ui_source
    assert "Operator Review" in profile_ui_source
    assert "agentic_review.js" in profile_ui_source
    assert "agentic_review.css" in profile_ui_source
    assert route_source.index("app_redesign.css") < route_source.index("agentic_review.css")
    assert "{render_top_shell(\"/profile\")}" in route_source
    assert 'href="/profile?tab=pipeline-runs">Back to pipeline runs</a>' in route_source
    assert 'href="/profile">Back to pipeline runs</a>' not in route_source
    assert "getProfileTabTargetFromUrl" in profile_source
    assert 'tab === "pipeline-runs"' in profile_source
    assert 'activateProfileTab(getProfileTabTargetFromUrl())' in profile_source
    assert "New Scan" in shell_source
    assert "app-shell-top-right" in shell_source
    assert 'body class="agentic-review-body"' not in route_source
    assert "agentic-review-standalone-nav" not in route_source
    assert 'role="tablist"' in profile_ui_source
    assert 'aria-selected="true"' in profile_ui_source
    assert "app_redesign.css" in executive_ui_source
    assert "app_redesign.css" in planning_ui_source

    assert "agenticReviewPriorityPanel" in review_source
    assert "job_prioritization_rows" in review_source
    assert "tailoring_decision_rows" in review_source
    assert "operator_review_rows" in review_source
    assert "No advisory rows recorded for this run." in review_source
    assert "data-agentic-tab-target" in profile_ui_source
    assert "data-agentic-advisory-target" in profile_ui_source
    assert "bindAgenticReviewTabs" in review_source
    assert "renderAgenticReviewDiagnosticsPanel" in review_source
    assert "renderAgenticWorkflowManifestSection" in review_source
    assert "owner_user_id" not in review_source

    assert ".agentic-review-link-card" not in common_css
    assert ".agentic-review-link-btn" not in common_css
    assert ".profile-tabs" in common_css
    assert ".profile-tab-btn::after" in common_css
    assert "--profile-tab-color" in common_css
    assert ".profile-tab-btn.is-active::after" in common_css
    assert ".pipeline-run-actions-cell" in common_css
    assert ".pipeline-run-icon-btn" in common_css
    assert ".pipeline-run-icon-btn::after" in common_css
    assert "content: attr(data-tooltip)" in common_css
    assert "html[data-theme=\"light\"] .pipeline-run-icon-btn" in common_css
    assert 'url("/static/media/view_img.svg")' in common_css
    assert 'url("/static/media/ai-img.svg")' in common_css
    profile_tabs_block = common_css.split(".profile-tabs", 1)[1].split(".profile-tab-btn", 1)[0]
    assert "border-radius: 999px" not in profile_tabs_block
    assert "background: var(--app-surface-2)" not in profile_tabs_block
    assert "box-shadow: var(" not in profile_tabs_block
    profile_tab_button_block = common_css.split("\n.profile-tab-btn {", 1)[1].split(".profile-tab-btn::after", 1)[0]
    assert "border-radius: 999px" not in profile_tab_button_block
    assert "background: var(--app-surface-2)" not in profile_tab_button_block
    profile_active_block = common_css.split(".profile-tab-btn.is-active", 1)[1].split(
        ".profile-tab-btn.is-active .profile-tab-icon", 1
    )[0]
    assert "outline-offset: -4px" not in profile_active_block
    assert "inset 0 0 0 2px" not in profile_active_block
    assert ".agentic-review-body" not in review_css
    assert ".agentic-review-standalone-nav" not in review_css
    assert ".agentic-review-page" in review_css
    assert ".agentic-review-tabs" in review_css
    assert ".agentic-review-segmented" in review_css
    assert ".agentic-review-tab::after" in review_css
    assert ".agentic-review-segment::after" in review_css
    assert "--agentic-tab-color" in review_css
    assert 'data-agentic-tab-target="agenticReviewOverviewTab"' in review_css
    assert 'data-agentic-advisory-target="agenticReviewTailoringPanel"' in review_css
    assert ".agentic-review-table" in review_css
    assert ".agent-trace-json-detail pre" in review_css
    assert "box-sizing: border-box" in review_css
    assert "min-width: 0" in review_css
    assert "overflow: auto" in review_css
    assert "background: #f8fafc" in review_css
    assert "color: #0f172a" in review_css
    assert ".app-shell" not in review_css
    assert ".sidebar" not in review_css
    assert ".topbar" not in review_css
    assert "body {" not in review_css
    assert ".agentic-review-page" not in common_css
    assert ".agentic-review-tabs" not in common_css
    assert ".agentic-review-tab::after" not in common_css
    assert ".agentic-review-segmented" not in common_css
    assert ".agentic-workflow-summary-card" not in common_css
    assert ".agent-trace-panel" not in common_css


def test_missing_job_prioritization_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_job_prioritization(rows, {}) == rows


def test_missing_tailoring_decision_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_tailoring_decisions(rows, {}) == rows


def test_missing_operator_review_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_operator_review(rows, {}) == rows
