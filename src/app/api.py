from pathlib import Path
import base64
import binascii
import json
from typing import Any
from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from src.app import services
from src.auth.runtime import auth_guard_response
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
from src.agents.critic_evaluator import evaluate_agent_trace
from src.agents.core_agent_evidence_materialization_preview import (
    build_core_agent_evidence_materialization_preview,
)
from src.agents import manual_review_readiness_contract
from src.agents import operator_decision_capture_readback_contract
from src.agents import provider_call_readiness_experiment
from src.agents import three_core_approval_preview_service_readback
from src.app.ui import router as ui_router
from src.app.planning_ui import router as planning_ui_router
from src.app.decisions_ui import router as decisions_ui_router
from src.app.intelligence_ui import router as intelligence_ui_router
from src.app.applied_ui import router as applied_ui_router
from src.app.saved_ui import router as saved_ui_router
from src.app.application_hub_ui import router as application_hub_ui_router
from src.app.profile_ui import router as profile_ui_router
from src.app.auth_ui import router as auth_ui_router
from src.app.onboarding_ui import router as onboarding_ui_router
import threading

from contextlib import asynccontextmanager

from src.utils.logging import get_logger

logger = get_logger("app.api")

def _warm_semantic_retrieval_background() -> None:
    from src.rag.retriever import warm_semantic_retrieval

    try:
        warm_semantic_retrieval(top_ks=(5, 15))
    except Exception:
        logger.exception("RAG semantic warmup failed during background startup")

def _start_semantic_warmup_thread() -> None:
    threading.Thread(
        target=_warm_semantic_retrieval_background,
        daemon=True,
        name="rag-semantic-warmup",
    ).start()


class PlanningWorkspaceDraftLoadRequest(BaseModel):
    tailoring_json_path: str
    selected_resume: str = ""


class PlanningWorkspaceDraftSaveRequest(BaseModel):
    tailoring_json_path: str
    selected_resume: str = ""
    selected_patch_candidate_ids: list[str] = Field(default_factory=list)
    manual_bullet_edits: dict[str, str] = Field(default_factory=dict)
    rewrite_review_decisions: dict[str, dict[str, str] | str] = Field(default_factory=dict)
    excluded_scan_issue_ids: list[str] = Field(default_factory=list)
    personal_details: dict[str, str] = Field(default_factory=dict)
    note: str = ""


class PlanningWorkspaceDraftPreviewRequest(BaseModel):
    tailoring_json_path: str
    selected_resume: str = ""
    selected_patch_candidate_ids: list[str] | None = None
    manual_bullet_edits: dict[str, str] | None = None
    rewrite_review_decisions: dict[str, dict[str, str] | str] | None = None
    excluded_scan_issue_ids: list[str] | None = None

class PlanningWorkspaceDraftRenderRequest(BaseModel):
    tailoring_json_path: str
    selected_resume: str = ""
    selected_patch_candidate_ids: list[str] | None = None
    manual_bullet_edits: dict[str, str] | None = None
    excluded_scan_issue_ids: list[str] | None = None

class PlanningScanPhraseRequest(BaseModel):
    tailoring_json_path: str
    selected_resume: str = ""
    bullet_key: str = ""
    current_text: str = ""
    guidance_text: str = ""
    supported_terms: list[str] = Field(default_factory=list)

class PlanningWorkspaceDraftExportRequest(BaseModel):
    tailoring_json_path: str
    selected_resume: str = ""
    format: str = "pdf"

class PlanningScanPreloadRequest(BaseModel):
    tailoring_json_path: str
    selected_resume: str = ""

class PlanningStartScanRequest(BaseModel):
    scan_id: str = ""
    company: str = ""
    role: str = ""
    job_description_text: str = ""
    job_url: str = ""
    job_doc_id: str = ""
    saved_resume_name: str = ""
    resume_text: str = ""
    tailoring_json_path: str = ""
    upload_filename: str = ""
    upload_content_type: str = ""
    upload_base64: str = ""

class PlanningExtractResumeUploadRequest(BaseModel):
    filename: str
    content_type: str = ""
    upload_base64: str

class PlanningSavedScanStateRequest(BaseModel):
    selected_patch_candidate_ids: list[str] = Field(default_factory=list)
    manual_bullet_edits: dict[str, str] = Field(default_factory=dict)
    rewrite_review_decisions: dict[str, dict[str, str] | str] = Field(default_factory=dict)
    excluded_scan_issue_ids: list[str] = Field(default_factory=list)
    personal_details: dict[str, str] = Field(default_factory=dict)


class AgentFeedbackRequest(BaseModel):
    pipeline_run_id: str = ""
    context_id: str = ""
    agent_run_id: str = ""
    agent_step_id: str = ""
    target_type: str
    target_id: str
    event_type: str
    payload_json: dict[str, object] = Field(default_factory=dict)
    source: str = "api"


class AgenticApprovalDecisionRequest(BaseModel):
    reviewer_id: str
    review_decision: str
    review_reason: str = ""
    decided_at: str | None = None


class CriticEvaluatorReadonlyRequest(BaseModel):
    trace_payload: dict[str, Any] | list[dict[str, Any]] = Field(default_factory=dict)
    trace_payload_source: str = "request_body"
    evaluator_rubric_version: str = ""


class ManualJdIntelligenceDryRunRequest(BaseModel):
    job_title: str = ""
    company: str = ""
    location: str = ""
    job_description: str = ""
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""
    feature_enabled: bool = False
    config: dict[str, Any] = Field(default_factory=dict)


class ManualResumeMatchDryRunRequest(BaseModel):
    jd_intelligence: dict[str, Any] = Field(default_factory=dict)
    jd_signals: dict[str, Any] = Field(default_factory=dict)
    resume_variants: list[dict[str, Any]] = Field(default_factory=list)
    resume_evidence_rows: list[dict[str, Any]] = Field(default_factory=list)
    selected_resume_id: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualTailoringSuggestionDryRunRequest(BaseModel):
    jd_intelligence: dict[str, Any] = Field(default_factory=dict)
    jd_signals: dict[str, Any] = Field(default_factory=dict)
    resume_match_payload: dict[str, Any] = Field(default_factory=dict)
    resume_variants: list[dict[str, Any]] = Field(default_factory=list)
    resume_evidence_rows: list[dict[str, Any]] = Field(default_factory=list)
    selected_resume_id: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualCriticGuardrailDryRunRequest(BaseModel):
    tailoring_suggestion_payload: dict[str, Any] = Field(default_factory=dict)
    jd_intelligence: dict[str, Any] = Field(default_factory=dict)
    jd_signals: dict[str, Any] = Field(default_factory=dict)
    resume_variants: list[dict[str, Any]] = Field(default_factory=list)
    resume_evidence_rows: list[dict[str, Any]] = Field(default_factory=list)
    context_id: str = ""
    job_id: str = ""


class ManualStrategyRecommendationDryRunRequest(BaseModel):
    jd_intelligence: dict[str, Any] = Field(default_factory=dict)
    jd_signals: dict[str, Any] = Field(default_factory=dict)
    resume_match_payload: dict[str, Any] = Field(default_factory=dict)
    tailoring_suggestion_payload: dict[str, Any] = Field(default_factory=dict)
    critic_guardrail_payload: dict[str, Any] = Field(default_factory=dict)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualShadowAgenticWorkflowChainDryRunRequest(BaseModel):
    job_title: str = ""
    company: str = ""
    location: str = ""
    job_description: str = ""
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    jd_intelligence: dict[str, Any] = Field(default_factory=dict)
    jd_signals: dict[str, Any] = Field(default_factory=dict)
    resume_variants: list[dict[str, Any]] = Field(default_factory=list)
    resume_evidence_rows: list[dict[str, Any]] = Field(default_factory=list)
    selected_resume_id: str = ""
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualShadowRecommendationHandoffDryRunRequest(BaseModel):
    shadow_chain_payload: dict[str, Any] = Field(default_factory=dict)
    job_title: str = ""
    company: str = ""
    location: str = ""
    job_description: str = ""
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    jd_intelligence: dict[str, Any] = Field(default_factory=dict)
    jd_signals: dict[str, Any] = Field(default_factory=dict)
    resume_variants: list[dict[str, Any]] = Field(default_factory=list)
    resume_evidence_rows: list[dict[str, Any]] = Field(default_factory=list)
    selected_resume_id: str = ""
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualHumanDecisionCaptureDryRunRequest(BaseModel):
    handoff_payload: dict[str, Any] = Field(default_factory=dict)
    shadow_chain_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_decision: str = ""
    reviewer_note: str = ""
    job_title: str = ""
    company: str = ""
    location: str = ""
    job_description: str = ""
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    jd_intelligence: dict[str, Any] = Field(default_factory=dict)
    jd_signals: dict[str, Any] = Field(default_factory=dict)
    resume_variants: list[dict[str, Any]] = Field(default_factory=list)
    resume_evidence_rows: list[dict[str, Any]] = Field(default_factory=list)
    selected_resume_id: str = ""
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualHumanApprovedActionPlanDryRunRequest(BaseModel):
    decision_capture_payload: dict[str, Any] = Field(default_factory=dict)
    handoff_payload: dict[str, Any] = Field(default_factory=dict)
    shadow_chain_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_decision: str = ""
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualReviewPacketPreviewDryRunRequest(BaseModel):
    action_plan_payload: dict[str, Any] = Field(default_factory=dict)
    decision_capture_payload: dict[str, Any] = Field(default_factory=dict)
    handoff_payload: dict[str, Any] = Field(default_factory=dict)
    shadow_chain_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_decision: str = ""
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualApprovalRequestPreviewDryRunRequest(BaseModel):
    review_packet_payload: dict[str, Any] = Field(default_factory=dict)
    action_plan_payload: dict[str, Any] = Field(default_factory=dict)
    decision_capture_payload: dict[str, Any] = Field(default_factory=dict)
    handoff_payload: dict[str, Any] = Field(default_factory=dict)
    shadow_chain_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_decision: str = ""
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualApprovalCreationGateDryRunRequest(BaseModel):
    approval_preview_payload: dict[str, Any] = Field(default_factory=dict)
    review_packet_payload: dict[str, Any] = Field(default_factory=dict)
    action_plan_payload: dict[str, Any] = Field(default_factory=dict)
    decision_capture_payload: dict[str, Any] = Field(default_factory=dict)
    handoff_payload: dict[str, Any] = Field(default_factory=dict)
    shadow_chain_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_confirmation: bool = False
    reviewer_decision: str = ""
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualGuardedApprovalRequestCreateRequest(BaseModel):
    approval_creation_gate_payload: dict[str, Any] = Field(default_factory=dict)
    approval_preview_payload: dict[str, Any] = Field(default_factory=dict)
    review_packet_payload: dict[str, Any] = Field(default_factory=dict)
    action_plan_payload: dict[str, Any] = Field(default_factory=dict)
    decision_capture_payload: dict[str, Any] = Field(default_factory=dict)
    handoff_payload: dict[str, Any] = Field(default_factory=dict)
    shadow_chain_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_confirmation: bool = False
    reviewer_decision: str = ""
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class HumanReviewedInfluenceApprovalRequest(BaseModel):
    human_reviewed_influence_preview_payload: dict[str, Any] = Field(default_factory=dict)
    deterministic_score_context: dict[str, Any] = Field(default_factory=dict)
    shadow_score_comparison_context: dict[str, Any] = Field(default_factory=dict)
    preview_config: dict[str, Any] = Field(default_factory=dict)
    reviewer_confirmation: bool = False
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class AgentRecommendationOverlayRequest(BaseModel):
    deterministic_score_context: dict[str, Any] = Field(default_factory=dict)
    shadow_score_comparison_context: dict[str, Any] = Field(default_factory=dict)
    human_reviewed_influence_preview_payload: dict[str, Any] = Field(default_factory=dict)
    influence_approval_request_payload: dict[str, Any] = Field(default_factory=dict)
    overlay_config: dict[str, Any] = Field(default_factory=dict)


class PipelineGeneratedAgentRecommendationOverlayReadbackRequest(BaseModel):
    hook_payload: dict[str, Any] = Field(default_factory=dict)
    trace_capture_payload: dict[str, Any] = Field(default_factory=dict)
    trace_persistence_payload: dict[str, Any] = Field(default_factory=dict)
    trace_readback_payload: dict[str, Any] = Field(default_factory=dict)
    readback_source: dict[str, Any] = Field(default_factory=dict)


class PipelineGeneratedAgentRecommendationOverlayReadinessSummaryRequest(BaseModel):
    overlay_readback_payload: dict[str, Any] = Field(default_factory=dict)
    hook_payload: dict[str, Any] = Field(default_factory=dict)
    trace_capture_payload: dict[str, Any] = Field(default_factory=dict)
    trace_persistence_payload: dict[str, Any] = Field(default_factory=dict)
    trace_readback_payload: dict[str, Any] = Field(default_factory=dict)
    readback_source: dict[str, Any] = Field(default_factory=dict)


class PipelineGeneratedOverlayReviewPacketRequest(BaseModel):
    overlay_readback_payload: dict[str, Any] = Field(default_factory=dict)
    overlay_payload: dict[str, Any] = Field(default_factory=dict)
    pipeline_generated_overlay_payload: dict[str, Any] = Field(default_factory=dict)
    agent_recommendation_overlay_payload: dict[str, Any] = Field(default_factory=dict)
    hook_payload: dict[str, Any] = Field(default_factory=dict)
    trace_context_payload: dict[str, Any] = Field(default_factory=dict)
    trace_capture_payload: dict[str, Any] = Field(default_factory=dict)
    trace_persistence_payload: dict[str, Any] = Field(default_factory=dict)
    trace_readback_payload: dict[str, Any] = Field(default_factory=dict)
    readback_source: dict[str, Any] = Field(default_factory=dict)


class VectorEvidenceRequest(BaseModel):
    query_text: str = ""
    job_payload: dict[str, Any] = Field(default_factory=dict)
    job_description_payload: dict[str, Any] = Field(default_factory=dict)
    resume_profile_payload: dict[str, Any] = Field(default_factory=dict)
    trace_evidence_payload: dict[str, Any] = Field(default_factory=dict)
    operator_review_packet_payload: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)
    chunk_type: str = ""
    job_id: str = ""
    company: str = ""
    agent_name: str = ""
    stage: str = ""
    top_k: int = 5


class PgvectorExtensionProbeRequest(BaseModel):
    extension_name: str = "vector"
    requested_dimension: int | None = None
    probe_context: dict[str, Any] = Field(default_factory=dict)


class VectorEvidenceReadbackRequest(BaseModel):
    enabled: bool = False
    owner_user_id: str = ""
    smoke_identifier: str = ""
    connection_provider_enabled: bool = False


class ThreeAgentLlmopsObservabilityReadbackRequest(BaseModel):
    enabled: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)
    chain_payload: dict[str, Any] = Field(default_factory=dict)
    review_packet_payload: dict[str, Any] = Field(default_factory=dict)


class ThreeCoreShadowOperatorCanaryReadbackRequest(BaseModel):
    enabled: bool = False
    shadow_sidecar_hook_payload: dict[str, Any] | None = None
    canary_context: dict[str, Any] | None = None


class ProviderRuntimeReadbackRequest(BaseModel):
    enabled: bool = False
    config: dict[str, Any] = Field(default_factory=dict)
    provider_calls_allowed: bool = False
    shadow_payload: dict[str, Any] = Field(default_factory=dict)


class JdProviderRuntimeReadbackRequest(BaseModel):
    enabled: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)
    review_packet_payload: dict[str, Any] = Field(default_factory=dict)


class JdLiveProviderCanaryReadbackRequest(BaseModel):
    enabled: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)
    review_packet_payload: dict[str, Any] = Field(default_factory=dict)


class ManualGuardedApprovalCreationObservabilityRequest(BaseModel):
    guarded_creation_payload: dict[str, Any] = Field(default_factory=dict)
    approval_creation_gate_payload: dict[str, Any] = Field(default_factory=dict)
    approval_preview_payload: dict[str, Any] = Field(default_factory=dict)
    review_packet_payload: dict[str, Any] = Field(default_factory=dict)
    action_plan_payload: dict[str, Any] = Field(default_factory=dict)
    decision_capture_payload: dict[str, Any] = Field(default_factory=dict)
    handoff_payload: dict[str, Any] = Field(default_factory=dict)
    shadow_chain_payload: dict[str, Any] = Field(default_factory=dict)
    created_approval_request_id: str = ""
    reviewer_confirmation: bool = False
    context_id: str = ""
    job_id: str = ""


class ManualApprovalRequestReadbackRequest(BaseModel):
    approval_request_id: str = ""
    guarded_creation_payload: dict[str, Any] = Field(default_factory=dict)
    observability_payload: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualApprovalStatusTransitionPreviewRequest(BaseModel):
    approval_request_id: str = ""
    proposed_transition: str = ""
    reviewer_note: str = ""
    approval_request_readback_payload: dict[str, Any] = Field(default_factory=dict)
    guarded_creation_payload: dict[str, Any] = Field(default_factory=dict)
    observability_payload: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualGuardedApprovalStatusTransitionRequest(BaseModel):
    approval_request_id: str = ""
    proposed_transition: str = ""
    reviewer_confirmation: bool = False
    reviewer_note: str = ""
    transition_preview_payload: dict[str, Any] = Field(default_factory=dict)
    approval_request_readback_payload: dict[str, Any] = Field(default_factory=dict)
    guarded_creation_payload: dict[str, Any] = Field(default_factory=dict)
    observability_payload: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualApprovalStatusTransitionObservabilityRequest(BaseModel):
    guarded_status_transition_payload: dict[str, Any] = Field(default_factory=dict)
    approval_request_id: str = ""
    proposed_transition: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualQueueHandoffReadinessPreviewRequest(BaseModel):
    approval_request_id: str = ""
    approval_request_readback_payload: dict[str, Any] = Field(default_factory=dict)
    approval_status_transition_observability_payload: dict[str, Any] = Field(default_factory=dict)
    approval_status_transition_payload: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualGuardedQueueHandoffCreateRequest(BaseModel):
    approval_request_id: str = ""
    reviewer_confirmation: bool = False
    queue_handoff_readiness_payload: dict[str, Any] = Field(default_factory=dict)
    approval_request_readback_payload: dict[str, Any] = Field(default_factory=dict)
    approval_status_transition_observability_payload: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""
    reviewer_note: str = ""


class ManualQueueHandoffCreationObservabilityRequest(BaseModel):
    guarded_queue_handoff_creation_payload: dict[str, Any] = Field(default_factory=dict)
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualExecutionReadinessPreviewRequest(BaseModel):
    queue_handoff_id: str = ""
    approval_request_id: str = ""
    queue_handoff_creation_payload: dict[str, Any] = Field(default_factory=dict)
    queue_handoff_observability_payload: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualExecutionLaunchGatePreviewRequest(BaseModel):
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    execution_readiness_payload: dict[str, Any] = Field(default_factory=dict)
    queue_handoff_observability_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_confirmation_preview: bool = False
    context_id: str = ""
    job_id: str = ""


class ManualExecutionLaunchGateObservabilityRequest(BaseModel):
    execution_launch_gate_payload: dict[str, Any] = Field(default_factory=dict)
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualExecutionRequestPacketPreviewRequest(BaseModel):
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    execution_launch_gate_payload: dict[str, Any] = Field(default_factory=dict)
    execution_launch_gate_observability_payload: dict[str, Any] = Field(default_factory=dict)
    execution_readiness_payload: dict[str, Any] = Field(default_factory=dict)
    queue_handoff_observability_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualGuardedExecutionRequestCreateRequest(BaseModel):
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    reviewer_confirmation: bool = False
    execution_request_packet_payload: dict[str, Any] = Field(default_factory=dict)
    execution_launch_gate_payload: dict[str, Any] = Field(default_factory=dict)
    execution_launch_gate_observability_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualGuardedExecutionRequestObservabilityRequest(BaseModel):
    guarded_execution_request_creation_payload: dict[str, Any] = Field(default_factory=dict)
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    execution_request_id: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualExecutionRequestReadbackRequest(BaseModel):
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    guarded_execution_request_creation_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_creation_observability_payload: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualExecutionRequestStatusTransitionPreviewRequest(BaseModel):
    execution_request_id: str = ""
    requested_transition: str = ""
    execution_request_readback_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_creation_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_creation_observability_payload: dict[str, Any] = Field(default_factory=dict)
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualGuardedExecutionRequestStatusTransitionRequest(BaseModel):
    execution_request_id: str = ""
    requested_transition: str = ""
    reviewer_confirmation: bool = False
    execution_request_status_transition_preview_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_readback_payload: dict[str, Any] = Field(default_factory=dict)
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualGuardedExecutionRequestStatusTransitionObservabilityRequest(BaseModel):
    guarded_execution_request_status_transition_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualApplicationExecutionSimulationPreviewRequest(BaseModel):
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    execution_request_readback_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_status_transition_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_status_transition_observability_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualApplicationExecutionSimulationObservabilityRequest(BaseModel):
    application_execution_simulation_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualApplicationExecutionPreflightChecklistRequest(BaseModel):
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    application_execution_simulation_payload: dict[str, Any] = Field(default_factory=dict)
    application_execution_simulation_observability_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_readback_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_status_transition_observability_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualApplicationExecutionPreflightObservabilityRequest(BaseModel):
    application_execution_preflight_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualGuardedApplicationExecutionLaunchRequestCreateRequest(BaseModel):
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    reviewer_confirmation: bool = False
    application_execution_preflight_payload: dict[str, Any] = Field(default_factory=dict)
    application_execution_preflight_observability_payload: dict[str, Any] = Field(default_factory=dict)
    application_execution_simulation_payload: dict[str, Any] = Field(default_factory=dict)
    application_execution_simulation_observability_payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualGuardedApplicationExecutionLaunchRequestObservabilityRequest(BaseModel):
    guarded_application_execution_launch_request_payload: dict[str, Any] = Field(default_factory=dict)
    execution_launch_request_id: str = ""
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualApplicationExecutionLaunchRequestReadbackRequest(BaseModel):
    execution_launch_request_id: str = ""
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    guarded_application_execution_launch_request_payload: dict[str, Any] = Field(default_factory=dict)
    application_execution_launch_request_observability_payload: dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""
    job_id: str = ""


class ManualExecutionLaunchRequestStatusTransitionPreviewRequest(BaseModel):
    execution_launch_request_id: str = ""
    requested_transition: str = ""
    application_execution_launch_request_readback_payload: dict[str, Any] = Field(default_factory=dict)
    guarded_application_execution_launch_request_payload: dict[str, Any] = Field(default_factory=dict)
    application_execution_launch_request_observability_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualGuardedExecutionLaunchRequestStatusTransitionRequest(BaseModel):
    execution_launch_request_id: str = ""
    requested_transition: str = ""
    reviewer_confirmation: bool = False
    execution_launch_request_status_transition_preview_payload: dict[str, Any] = Field(default_factory=dict)
    application_execution_launch_request_readback_payload: dict[str, Any] = Field(default_factory=dict)
    guarded_application_execution_launch_request_payload: dict[str, Any] = Field(default_factory=dict)
    application_execution_launch_request_observability_payload: dict[str, Any] = Field(default_factory=dict)
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    reviewer_note: str = ""
    context_id: str = ""
    job_id: str = ""


class ManualGuardedExecutionLaunchRequestStatusTransitionObservabilityRequest(BaseModel):
    guarded_execution_launch_request_status_transition_payload: dict[str, Any] = Field(default_factory=dict)
    execution_launch_request_id: str = ""
    execution_request_id: str = ""
    approval_request_id: str = ""
    queue_handoff_id: str = ""
    context_id: str = ""
    job_id: str = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        try:
            services.stop_live_pipeline_for_server_shutdown()
        except Exception:
            logger.exception("Failed to stop live pipeline during API shutdown")

app = FastAPI(
    title="Job Operator API",
    version="0.1.0",
    description="Thin API shell over deterministic operator workflows and local job RAG.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="src/app/static"), name="static")


@app.middleware("http")
async def require_dashboard_auth(request: Request, call_next):
    guard_response = auth_guard_response(request)
    if guard_response is not None:
        return guard_response

    return await call_next(request)



def _auth_user_from_request(request: Request) -> dict:
    return dict(getattr(request.state, "auth_user", {}) or {})


def _auth_owner_user_id(request: Request) -> str:
    return str(_auth_user_from_request(request).get("user_id", "") or "").strip()


def _require_auth_owner_user_id(request: Request) -> str:
    owner_user_id = _auth_owner_user_id(request)
    if not owner_user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return owner_user_id


def _auth_owner_email(request: Request) -> str:
    return str(_auth_user_from_request(request).get("email", "") or "").strip()


def _require_admin_user(request: Request) -> dict:
    user = _auth_user_from_request(request)
    access_level = str(user.get("access_level", "") or "").strip().lower()
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not bool(user.get("is_admin", False)) and access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


def _agentic_approval_storage_connection() -> Any:
    return None


def _agent_trace_readonly_storage_connection() -> Any:
    return None


AGENT_TRACE_READONLY_API_SAFETY_METADATA: dict[str, bool] = {
    "read_only": True,
    "did_create_agent_run": False,
    "did_create_agent_step": False,
    "did_mutate_approval": False,
    "did_execute_pipeline": False,
    "did_schedule_background_work": False,
    "did_execute_scheduler": False,
    "did_export_files": False,
    "did_execute_application": False,
    "did_submit_application": False,
    "did_call_llm_provider": False,
    "did_create_connection": False,
    "did_commit_transaction": False,
        "did_" + "run_" + "migration": False,
    "did_" + "run_" + "migration": False,
    "ui_action_added": False,
    "pipeline_wiring_added": False,
}


AGENT_TRACE_RUN_COLUMNS: tuple[str, ...] = (
    "agent_run_id",
    "agent_run_key",
    "context_key",
    "approval_request_id",
    "job_id",
    "candidate_key",
    "agent_name",
    "run_status",
    "observed_at_utc",
    "metadata_json",
    "safety_flags_json",
)


AGENT_TRACE_STEP_COLUMNS: tuple[str, ...] = (
    "agent_step_id",
    "agent_step_key",
    "agent_run_id",
    "context_key",
    "approval_request_id",
    "job_id",
    "candidate_key",
    "agent_name",
    "step_name",
    "step_index",
    "step_status",
    "observed_at_utc",
    "input_summary_json",
    "output_summary_json",
    "reason_codes_json",
    "metadata_json",
    "safety_flags_json",
)


def _agent_trace_readonly_safety_metadata() -> dict[str, bool]:
    return dict(AGENT_TRACE_READONLY_API_SAFETY_METADATA)


def _agent_trace_readonly_json_value(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return default
        return parsed if isinstance(parsed, type(default)) else default
    return default


def _agent_trace_readonly_row_dict(
    row: Any,
    columns: tuple[str, ...],
) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        return dict(row)
    return dict(zip(columns, row))


def _agent_trace_readonly_run_payload(row: Any) -> dict[str, Any]:
    payload = _agent_trace_readonly_row_dict(row, AGENT_TRACE_RUN_COLUMNS)
    if not payload:
        return {}
    return {
        "agent_run_id": str(payload.get("agent_run_id") or "").strip(),
        "agent_run_key": str(payload.get("agent_run_key") or "").strip(),
        "context_key": str(payload.get("context_key") or "").strip(),
        "approval_request_id": str(payload.get("approval_request_id") or "").strip(),
        "job_id": str(payload.get("job_id") or "").strip(),
        "candidate_key": str(payload.get("candidate_key") or "").strip(),
        "agent_name": str(payload.get("agent_name") or "").strip(),
        "run_status": str(payload.get("run_status") or "").strip(),
        "observed_at_utc": str(payload.get("observed_at_utc") or "").strip(),
        "metadata": _agent_trace_readonly_json_value(
            payload.get("metadata_json") or payload.get("metadata"),
            {},
        ),
        "safety_metadata": _agent_trace_readonly_json_value(
            payload.get("safety_flags_json") or payload.get("safety_metadata"),
            {},
        ),
    }


def _agent_trace_readonly_step_payload(row: Any) -> dict[str, Any]:
    payload = _agent_trace_readonly_row_dict(row, AGENT_TRACE_STEP_COLUMNS)
    if not payload:
        return {}
    return {
        "agent_step_id": str(payload.get("agent_step_id") or "").strip(),
        "agent_step_key": str(payload.get("agent_step_key") or "").strip(),
        "agent_run_id": str(payload.get("agent_run_id") or "").strip(),
        "context_key": str(payload.get("context_key") or "").strip(),
        "approval_request_id": str(payload.get("approval_request_id") or "").strip(),
        "job_id": str(payload.get("job_id") or "").strip(),
        "candidate_key": str(payload.get("candidate_key") or "").strip(),
        "agent_name": str(payload.get("agent_name") or "").strip(),
        "step_name": str(payload.get("step_name") or "").strip(),
        "step_index": int(payload.get("step_index") or 0),
        "step_status": str(payload.get("step_status") or "").strip(),
        "observed_at_utc": str(payload.get("observed_at_utc") or "").strip(),
        "input_summary": _agent_trace_readonly_json_value(
            payload.get("input_summary_json") or payload.get("input_summary"),
            {},
        ),
        "output_summary": _agent_trace_readonly_json_value(
            payload.get("output_summary_json") or payload.get("output_summary"),
            {},
        ),
        "reason_codes": _agent_trace_readonly_json_value(
            payload.get("reason_codes_json") or payload.get("reason_codes"),
            [],
        ),
        "metadata": _agent_trace_readonly_json_value(
            payload.get("metadata_json") or payload.get("metadata"),
            {},
        ),
        "safety_metadata": _agent_trace_readonly_json_value(
            payload.get("safety_flags_json") or payload.get("safety_metadata"),
            {},
        ),
    }


def _agent_trace_readonly_step_order(step: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(step.get("step_index") or 0),
        str(step.get("observed_at_utc") or ""),
        str(step.get("agent_step_id") or ""),
        str(step.get("agent_step_key") or ""),
    )


def _agent_trace_readonly_cursor(connection: Any) -> Any:
    if hasattr(connection, "cursor"):
        return connection.cursor()
    return connection


def _agent_trace_readonly_fetchone(cursor: Any) -> Any:
    if hasattr(cursor, "fetchone"):
        return cursor.fetchone()
    return None


def _agent_trace_readonly_fetchall(cursor: Any) -> list[Any]:
    if hasattr(cursor, "fetchall"):
        rows = cursor.fetchall()
        return list(rows or [])
    return []


def _read_agent_trace_for_approval(
    *,
    connection: Any,
    approval_request_id: str,
    agent_run_id: str = "",
) -> dict[str, Any]:
    from src.storage.agent_state import store

    cursor = _agent_trace_readonly_cursor(connection)
    run_query = store.prepare_agent_run_select(
        approval_request_id=approval_request_id,
        agent_run_id=agent_run_id,
    )
    cursor.execute(run_query["sql"], run_query["params"])
    run_row = _agent_trace_readonly_fetchone(cursor)
    agent_run = _agent_trace_readonly_run_payload(run_row)
    if not agent_run:
        return {"agent_run": {}, "agent_steps": []}

    steps_query = store.prepare_agent_steps_select_for_run(
        agent_run_id=agent_run["agent_run_id"],
    )
    cursor.execute(steps_query["sql"], steps_query["params"])
    agent_steps = [
        _agent_trace_readonly_step_payload(row)
        for row in _agent_trace_readonly_fetchall(cursor)
    ]
    return {
        "agent_run": agent_run,
        "agent_steps": [step for step in agent_steps if step],
    }


def _agent_trace_readonly_payload(
    *,
    approval_request_id: str,
    agent_run_id: str = "",
    trace_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = dict(trace_result or {})
    agent_run = dict(result.get("agent_run") or {})
    agent_steps = [
        dict(step)
        for step in result.get("agent_steps") or []
        if isinstance(step, dict)
    ]
    ordered_steps = sorted(agent_steps, key=_agent_trace_readonly_step_order)
    found = bool(agent_run)
    return {
        "approval_request_id": approval_request_id,
        "agent_run_id": agent_run_id,
        "found": found,
        "agent_run": agent_run,
        "agent_steps": ordered_steps,
        "step_count": len(ordered_steps),
        "empty_trace": not ordered_steps,
        "safety_metadata": _agent_trace_readonly_safety_metadata(),
    }


def _agentic_approval_decision_safety_payload(
    *,
    approval_request_id: str,
    review_decision: str = "",
    status: str,
    reason_codes: list[str] | None = None,
    approval_request: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reason_codes = list(reason_codes or [])
    return {
        "approval_api_endpoint": "POST /api/agentic-approvals/{approval_request_id}/decision",
        "approval_request_id": approval_request_id,
        "review_decision": review_decision,
        "approval_api_endpoint_status": status,
        "blocked_by_approval_api_endpoint": status != "passed",
        "approval_api_endpoint_reason_codes": reason_codes,
        "approval_request": dict(approval_request or {}),
        "queue_mutation_enabled": False,
        "did_mutate_queue": False,
        "execution_enabled": False,
        "did_execute_count": 0,
        "did_execute_live": False,
        "did_mutate_production": False,
        "did_submit_application": False,
        "scheduler_background_execution_enabled": False,
    }


def _production_scheduler_observability_reporting_decision_for_approval(
    approval_request_id: str,
) -> dict[str, Any] | None:
    return None


def _agentic_production_scheduler_observability_report_payload(
    *,
    approval_request_id: str,
    reporting_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = dict(reporting_decision or {})
    reason_codes: list[str] = []

    if not isinstance(reporting_decision, dict):
        reason_codes.append("missing_production_scheduler_observability_reporting_decision")
    else:
        if (
            report.get("production_scheduler_observability_reporting_allowed")
            is not True
        ):
            reason_codes.append(
                "production_scheduler_observability_reporting_not_allowed"
            )
        if (
            str(
                report.get("production_scheduler_observability_reporting_status") or ""
            ).strip().lower()
            != "passed"
        ):
            reason_codes.append(
                "production_scheduler_observability_reporting_status_not_passed"
            )
        if (
            report.get("production_scheduler_observability_reporting_read_only")
            is not True
        ):
            reason_codes.append(
                "production_scheduler_observability_reporting_not_read_only"
            )

    merged_reason_codes = sorted(
        set(
            reason_codes
            + list(
                report.get(
                    "production_scheduler_observability_reporting_reason_codes"
                )
                or []
            )
        )
    )
    blocked = bool(merged_reason_codes)
    status = "blocked" if blocked else "passed"
    return {
        **report,
        "approval_request_id": approval_request_id,
        "production_scheduler_observability_reporting_endpoint": (
            "GET /api/agentic-approvals/{approval_request_id}/production-scheduler-observability-report"
        ),
        "production_scheduler_observability_reporting_endpoint_method": "GET",
        "production_scheduler_observability_reporting_endpoint_read_only": True,
        "production_scheduler_observability_reporting_endpoint_status": status,
        "blocked_by_production_scheduler_observability_reporting_endpoint": blocked,
        "production_scheduler_observability_reporting_endpoint_reason_codes": (
            merged_reason_codes
        ),
        "production_scheduler_observability_reporting_allowed": not blocked,
        "production_scheduler_observability_reporting_status": status,
        "production_scheduler_observability_reporting_reason_codes": merged_reason_codes,
        "execution_enabled": False,
        "submission_enabled": False,
        "production_scheduler_wiring_enabled": False,
        "scheduler_background_execution_enabled": False,
        "live_scheduler_loop_enabled": False,
        "migration_execution_enabled": False,
        "metrics_emitter_enabled": False,
        "logging_emitter_enabled": False,
        "audit_writer_enabled": False,
        "dashboard_code_enabled": False,
        "export_code_enabled": False,
        "reporting_job_enabled": False,
        "did_execute_count": 0,
        "did_execute_live": False,
        "did_submit_application": False,
        "did_mutate_production": False,
        "did_write_db": False,
        "did_emit_metrics": False,
        "did_emit_logs": False,
        "did_write_audit_events": False,
        "did_start_background_work": False,
        "did_export_files": False,
        "did_create_dashboard_jobs": False,
        "did_create_reporting_jobs": False,
    }


def _agentic_production_scheduler_observability_dashboard_and_export_base_payload(
    *,
    approval_request_id: str,
    reporting_decision: dict[str, Any] | None = None,
    surface: str,
) -> dict[str, Any]:
    report_payload = _agentic_production_scheduler_observability_report_payload(
        approval_request_id=approval_request_id,
        reporting_decision=reporting_decision,
    )
    reason_codes = list(
        report_payload.get(
            "production_scheduler_observability_reporting_endpoint_reason_codes"
        )
        or []
    )
    if reason_codes:
        reason_codes.append(
            "production_scheduler_observability_reporting_gate_not_passed"
        )
    reason_codes = sorted(set(reason_codes))
    blocked = bool(reason_codes)
    status = "blocked" if blocked else "passed"
    return {
        **report_payload,
        "approval_request_id": approval_request_id,
        f"production_scheduler_observability_{surface}_endpoint_method": "GET",
        f"production_scheduler_observability_{surface}_endpoint_read_only": True,
        f"production_scheduler_observability_{surface}_status": status,
        f"production_scheduler_observability_{surface}_allowed": not blocked,
        f"production_scheduler_observability_{surface}_reason_codes": reason_codes,
        f"blocked_by_production_scheduler_observability_{surface}_endpoint": blocked,
        "did_trigger_execution": False,
        "did_trigger_submission": False,
        "did_trigger_production_scheduler_wiring": False,
        "did_trigger_scheduler_work": False,
        "did_trigger_migration": False,
        "did_write_audit_events": False,
        "did_write_metrics": False,
        "did_emit_logs": False,
        "did_start_background_work": False,
        "did_create_reporting_job": False,
        "did_export_files": False,
        "export_file_creation_enabled": False,
    }


def _agentic_production_scheduler_observability_dashboard_payload(
    *,
    approval_request_id: str,
    reporting_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _agentic_production_scheduler_observability_dashboard_and_export_base_payload(
        approval_request_id=approval_request_id,
        reporting_decision=reporting_decision,
        surface="dashboard",
    )
    return {
        **payload,
        "production_scheduler_observability_dashboard_endpoint": (
            "GET /api/agentic-approvals/{approval_request_id}/production-scheduler-observability-dashboard"
        ),
        "production_scheduler_observability_dashboard_summary": {
            "allowed": payload["production_scheduler_observability_dashboard_allowed"],
            "status": payload["production_scheduler_observability_dashboard_status"],
            "reason_codes": payload[
                "production_scheduler_observability_dashboard_reason_codes"
            ],
            "read_only": True,
            "execution_disabled": True,
            "submission_disabled": True,
            "production_scheduler_wiring_disabled": True,
            "scheduler_work_disabled": True,
            "migration_disabled": True,
            "audit_metrics_logging_disabled": True,
            "reporting_job_disabled": True,
            "file_export_disabled": True,
        },
    }


def _agentic_production_scheduler_observability_export_preview_payload(
    *,
    approval_request_id: str,
    reporting_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _agentic_production_scheduler_observability_dashboard_and_export_base_payload(
        approval_request_id=approval_request_id,
        reporting_decision=reporting_decision,
        surface="export_preview",
    )
    return {
        **payload,
        "production_scheduler_observability_export_preview_endpoint": (
            "GET /api/agentic-approvals/{approval_request_id}/production-scheduler-observability-export-preview"
        ),
        "production_scheduler_observability_export_preview_manifest": {
            "allowed": payload[
                "production_scheduler_observability_export_preview_allowed"
            ],
            "status": payload[
                "production_scheduler_observability_export_preview_status"
            ],
            "reason_codes": payload[
                "production_scheduler_observability_export_preview_reason_codes"
            ],
            "read_only": True,
            "format": "json_preview_only",
            "file_creation_enabled": False,
            "export_file_creation_disabled": True,
            "reporting_job_disabled": True,
            "migration_disabled": True,
        },
        "export_file_creation_disabled": True,
    }


def _agentic_production_scheduler_observability_writer_status_payload(
    *,
    approval_request_id: str,
    reporting_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report_payload = _agentic_production_scheduler_observability_report_payload(
        approval_request_id=approval_request_id,
        reporting_decision=reporting_decision,
    )
    reason_codes = list(
        report_payload.get(
            "production_scheduler_observability_reporting_endpoint_reason_codes"
        )
        or []
    )
    if reason_codes:
        reason_codes.append(
            "production_scheduler_observability_reporting_gate_not_passed"
        )
    reason_codes = sorted(set(reason_codes))
    blocked = bool(reason_codes)
    status = "blocked" if blocked else "passed"
    return {
        **report_payload,
        "approval_request_id": approval_request_id,
        "production_scheduler_observability_writer_status_endpoint": (
            "GET /api/agentic-approvals/{approval_request_id}/production-scheduler-observability-writer-status"
        ),
        "production_scheduler_observability_writer_status_endpoint_method": "GET",
        "production_scheduler_observability_writer_status_read_only": True,
        "production_scheduler_observability_writer_status": status,
        "production_scheduler_observability_writer_status_eligible": not blocked,
        "production_scheduler_observability_writer_status_reason_codes": reason_codes,
        "blocked_by_production_scheduler_observability_writer_status_endpoint": blocked,
        "metrics_writer_enabled": False,
        "logging_writer_enabled": False,
        "audit_writer_enabled": False,
        "persistence_enabled": False,
        "migration_required": False,
        "did_write_metrics": False,
        "did_write_logs": False,
        "did_write_audit_events": False,
        "did_schedule_background_work": False,
        "did_create_reporting_job": False,
        "did_export_files": False,
        "did_trigger_execution": False,
        "did_trigger_submission": False,
        "did_trigger_production_scheduler_wiring": False,
        "did_trigger_scheduler_work": False,
        "did_trigger_migration": False,
        "production_scheduler_observability_writer_status_summary": {
            "eligible": not blocked,
            "status": status,
            "reason_codes": reason_codes,
            "read_only": True,
            "metrics_writer_disabled": True,
            "logging_writer_disabled": True,
            "audit_writer_disabled": True,
            "persistence_disabled": True,
            "migration_required": False,
            "background_work_disabled": True,
            "reporting_job_disabled": True,
            "file_export_disabled": True,
        },
    }


def _agentic_production_scheduler_observability_reporting_job_payload(
    *,
    approval_request_id: str,
    reporting_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report_payload = _agentic_production_scheduler_observability_report_payload(
        approval_request_id=approval_request_id,
        reporting_decision=reporting_decision,
    )
    reason_codes = list(
        report_payload.get(
            "production_scheduler_observability_reporting_endpoint_reason_codes"
        )
        or []
    )
    if reason_codes:
        reason_codes.append(
            "production_scheduler_observability_reporting_gate_not_passed"
        )
    reason_codes = sorted(set(reason_codes))
    blocked = bool(reason_codes)
    status = "blocked" if blocked else "completed"
    reporting_job_key = (
        f"production_scheduler_observability_reporting_job:{approval_request_id}"
    )
    result_summary = {
        "approval_request_id": approval_request_id,
        "surface": "production_scheduler_observability_reporting_job",
        "status": status,
        "reason_codes": reason_codes,
        "structured_json_only": True,
        "persistence_disabled": True,
        "background_work_disabled": True,
        "file_export_disabled": True,
        "scheduler_execution_disabled": True,
        "application_execution_disabled": True,
        "application_submission_disabled": True,
    }
    return {
        **report_payload,
        "approval_request_id": approval_request_id,
        "production_scheduler_observability_reporting_job_endpoint": (
            "POST /api/agentic-approvals/{approval_request_id}/production-scheduler-observability-reporting-job"
        ),
        "production_scheduler_observability_reporting_job_endpoint_method": "POST",
        "production_scheduler_observability_reporting_job_explicit_invocation_only": True,
        "reporting_job_invoked": True,
        "reporting_job_status": status,
        "reporting_job_key": reporting_job_key,
        "surface": "production_scheduler_observability_reporting_job",
        "reason_codes": reason_codes,
        "result_summary": result_summary,
        "blocked_by_production_scheduler_observability_reporting_job_endpoint": blocked,
        "reporting_job_record_enabled": False,
        "persistence_enabled": False,
        "migration_required": False,
        "did_persist_reporting_result": False,
        "did_schedule_background_work": False,
        "did_create_reporting_job_record": False,
        "did_export_files": False,
        "did_execute_scheduler": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "did_trigger_execution": False,
        "did_trigger_submission": False,
        "did_trigger_production_scheduler_wiring": False,
        "did_trigger_scheduler_work": False,
        "did_trigger_migration": False,
        "did_write_metrics": False,
        "did_write_logs": False,
        "did_write_audit_events": False,
        "metrics_writer_enabled": False,
        "logging_writer_enabled": False,
        "audit_writer_enabled": False,
        "export_file_creation_enabled": False,
        "scheduler_execution_enabled": False,
        "application_execution_enabled": False,
        "application_submission_enabled": False,
    }

app.include_router(ui_router)
app.include_router(planning_ui_router)
app.include_router(decisions_ui_router)
app.include_router(intelligence_ui_router)
app.include_router(applied_ui_router)
app.include_router(saved_ui_router)
app.include_router(application_hub_ui_router)
app.include_router(profile_ui_router)
app.include_router(auth_ui_router)
app.include_router(onboarding_ui_router)

@app.get("/health")
def health():
    return services.health_payload()


@app.post("/api/agent-feedback")
def record_agent_feedback(request: AgentFeedbackRequest, http_request: Request):
    try:
        return services.record_agent_feedback_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
            pipeline_run_id=request.pipeline_run_id,
            context_id=request.context_id,
            agent_run_id=request.agent_run_id,
            agent_step_id=request.agent_step_id,
            target_type=request.target_type,
            target_id=request.target_id,
            event_type=request.event_type,
            payload_json=request.payload_json,
            source=request.source or "api",
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/agentic-approvals/{approval_request_id}/decision")
def record_agentic_approval_decision(
    approval_request_id: str,
    request: AgenticApprovalDecisionRequest,
):
    from src.storage.agentic_approvals import store

    review_decision = request.review_decision.strip().lower()
    if review_decision not in store.DECISION_STATUS_VALUES:
        allowed = sorted(store.DECISION_STATUS_VALUES)
        raise HTTPException(
            status_code=400,
            detail={
                "approval_api_endpoint_status": "failed",
                "reason_code": "unsupported_review_decision",
                "allowed_review_decisions": allowed,
            },
        )

    connection = _agentic_approval_storage_connection()
    if connection is None:
        raise HTTPException(
            status_code=503,
            detail=_agentic_approval_decision_safety_payload(
                approval_request_id=approval_request_id,
                review_decision=review_decision,
                status="blocked",
                reason_codes=["approval_storage_connection_unavailable"],
            ),
        )

    try:
        approval_request = store.record_approval_decision(
            connection,
            approval_request_id=approval_request_id,
            approval_status=review_decision,
            reviewer_id=request.reviewer_id,
            review_reason=request.review_reason,
            decided_at=request.decided_at,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "approval_api_endpoint_status": "failed",
                "reason_code": "invalid_approval_decision_request",
                "message": str(exc),
            },
        ) from exc
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=_agentic_approval_decision_safety_payload(
                approval_request_id=approval_request_id,
                review_decision=review_decision,
                status="failed",
                reason_codes=["approval_request_not_found"],
            ),
        ) from exc
    except store.ApprovalStorageError as exc:
        raise HTTPException(
            status_code=503,
            detail=_agentic_approval_decision_safety_payload(
                approval_request_id=approval_request_id,
                review_decision=review_decision,
                status="failed",
                reason_codes=[exc.reason_code],
            ),
        ) from exc

    return _agentic_approval_decision_safety_payload(
        approval_request_id=approval_request_id,
        review_decision=review_decision,
        status="passed",
        approval_request=approval_request,
    )


@app.get(
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-report"
)
def get_production_scheduler_observability_report(approval_request_id: str):
    reporting_decision = (
        _production_scheduler_observability_reporting_decision_for_approval(
            approval_request_id
        )
    )
    return _agentic_production_scheduler_observability_report_payload(
        approval_request_id=approval_request_id,
        reporting_decision=reporting_decision,
    )


@app.get(
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-dashboard"
)
def get_production_scheduler_observability_dashboard(approval_request_id: str):
    reporting_decision = (
        _production_scheduler_observability_reporting_decision_for_approval(
            approval_request_id
        )
    )
    return _agentic_production_scheduler_observability_dashboard_payload(
        approval_request_id=approval_request_id,
        reporting_decision=reporting_decision,
    )


@app.get(
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-export-preview"
)
def get_production_scheduler_observability_export_preview(approval_request_id: str):
    reporting_decision = (
        _production_scheduler_observability_reporting_decision_for_approval(
            approval_request_id
        )
    )
    return _agentic_production_scheduler_observability_export_preview_payload(
        approval_request_id=approval_request_id,
        reporting_decision=reporting_decision,
    )


@app.get(
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-writer-status"
)
def get_production_scheduler_observability_writer_status(approval_request_id: str):
    reporting_decision = (
        _production_scheduler_observability_reporting_decision_for_approval(
            approval_request_id
        )
    )
    return _agentic_production_scheduler_observability_writer_status_payload(
        approval_request_id=approval_request_id,
        reporting_decision=reporting_decision,
    )


@app.get("/api/agentic-approvals/{approval_request_id}/agent-trace")
def get_agentic_approval_agent_trace(
    approval_request_id: str,
    agent_run_id: str = "",
):
    connection = _agent_trace_readonly_storage_connection()
    trace_result = None
    if connection is not None:
        trace_result = _read_agent_trace_for_approval(
            connection=connection,
            approval_request_id=approval_request_id,
            agent_run_id=agent_run_id,
        )
    return _agent_trace_readonly_payload(
        approval_request_id=approval_request_id,
        agent_run_id=agent_run_id,
        trace_result=trace_result,
    )


def _critic_evaluator_readonly_safety_flags() -> dict[str, bool]:
    return {
        "did_write_storage": False,
        "did_call_llm": False,
        "did_mutate_approval": False,
        "did_change_score": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }


@app.post("/api/agentic-approvals/{approval_request_id}/critic-evaluator-readonly")
def invoke_critic_evaluator_readonly_api_action(
    approval_request_id: str,
    request: CriticEvaluatorReadonlyRequest,
):
    evaluator_result = evaluate_agent_trace(request.trace_payload)
    trace_payload = request.trace_payload if isinstance(request.trace_payload, dict) else {}
    evidence_pack = trace_payload.get("trace_evidence_pack")
    evidence_pack_available = isinstance(evidence_pack, dict) and bool(evidence_pack)
    reason_codes = []
    warnings = list(evaluator_result.get("evaluator_warnings", []) or [])
    blockers = list(evaluator_result.get("evaluator_findings", []) or [])
    readiness_status = "unknown"
    if evidence_pack_available:
        readiness_status = str(evidence_pack.get("readiness_status") or "unknown").strip()
        evidence_reason_codes = evidence_pack.get("decision_reason_codes", [])
        evidence_warnings = evidence_pack.get("warning_findings", [])
        evidence_blockers = evidence_pack.get("blocking_findings", [])
        reason_codes = list(evidence_reason_codes) if isinstance(evidence_reason_codes, list) else []
        warnings.extend(list(evidence_warnings) if isinstance(evidence_warnings, list) else [])
        blockers.extend(list(evidence_blockers) if isinstance(evidence_blockers, list) else [])
    critic_status = (
        "blocked"
        if blockers or readiness_status == "blocked"
        else "warning"
        if warnings or readiness_status == "warning"
        else "passed"
    )
    return {
        "approval_request_id": approval_request_id,
        "trace_payload_source": request.trace_payload_source,
        "requested_evaluator_rubric_version": request.evaluator_rubric_version,
        "explicit_user_action": True,
        "read_only": True,
        "critic_status": critic_status,
        "readiness_status": readiness_status,
        "evidence_pack_available": evidence_pack_available,
        "reason_codes": reason_codes,
        "warnings": warnings,
        "blockers": blockers,
        "safety_metadata": _critic_evaluator_readonly_safety_flags(),
        **evaluator_result,
        **_critic_evaluator_readonly_safety_flags(),
    }


@app.post("/api/manual-jd-intelligence-dry-run")
def invoke_manual_jd_intelligence_dry_run_api_action(
    request: ManualJdIntelligenceDryRunRequest,
):
    payload = services.build_manual_jd_intelligence_dry_run_payload(
        job_title=request.job_title,
        company=request.company,
        location=request.location,
        job_description=request.job_description,
        source_metadata=request.source_metadata,
        context_id=request.context_id,
        job_id=request.job_id,
        feature_enabled=request.feature_enabled,
        config=request.config,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_jd_intelligence_dry_run",
    }


@app.post("/api/manual-resume-match-dry-run")
def invoke_manual_resume_match_dry_run_api_action(
    request: ManualResumeMatchDryRunRequest,
):
    payload = services.build_manual_resume_match_dry_run_payload(
        jd_intelligence=request.jd_intelligence,
        jd_signals=request.jd_signals or None,
        resume_variants=request.resume_variants or None,
        resume_evidence_rows=request.resume_evidence_rows,
        selected_resume_id=request.selected_resume_id,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_resume_match_dry_run",
    }


@app.post("/api/manual-tailoring-suggestion-dry-run")
def invoke_manual_tailoring_suggestion_dry_run_api_action(
    request: ManualTailoringSuggestionDryRunRequest,
):
    payload = services.build_manual_tailoring_suggestion_dry_run_payload(
        jd_intelligence=request.jd_intelligence,
        jd_signals=request.jd_signals,
        resume_match_payload=request.resume_match_payload,
        resume_variants=request.resume_variants or None,
        resume_evidence_rows=request.resume_evidence_rows,
        selected_resume_id=request.selected_resume_id,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_tailoring_suggestion_dry_run",
    }


@app.post("/api/manual-critic-guardrail-dry-run")
def invoke_manual_critic_guardrail_dry_run_api_action(
    request: ManualCriticGuardrailDryRunRequest,
):
    payload = services.build_manual_critic_guardrail_dry_run_payload(
        tailoring_suggestion_payload=request.tailoring_suggestion_payload,
        jd_intelligence=request.jd_intelligence,
        jd_signals=request.jd_signals,
        resume_variants=request.resume_variants or None,
        resume_evidence_rows=request.resume_evidence_rows,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_critic_guardrail_dry_run",
    }


@app.post("/api/manual-strategy-recommendation-dry-run")
def invoke_manual_strategy_recommendation_dry_run_api_action(
    request: ManualStrategyRecommendationDryRunRequest,
):
    payload = services.build_manual_strategy_recommendation_dry_run_payload(
        jd_intelligence=request.jd_intelligence,
        jd_signals=request.jd_signals,
        resume_match_payload=request.resume_match_payload,
        tailoring_suggestion_payload=request.tailoring_suggestion_payload,
        critic_guardrail_payload=request.critic_guardrail_payload,
        user_preferences=request.user_preferences,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_strategy_recommendation_dry_run",
    }


@app.post("/api/manual-shadow-agentic-workflow-chain-dry-run")
def invoke_manual_shadow_agentic_workflow_chain_dry_run_api_action(
    request: ManualShadowAgenticWorkflowChainDryRunRequest,
):
    payload = services.build_shadow_agentic_workflow_chain_dry_run_payload(
        job_title=request.job_title,
        company=request.company,
        location=request.location,
        job_description=request.job_description,
        source_metadata=request.source_metadata,
        jd_intelligence=request.jd_intelligence,
        jd_signals=request.jd_signals,
        resume_variants=request.resume_variants or None,
        resume_evidence_rows=request.resume_evidence_rows,
        selected_resume_id=request.selected_resume_id,
        user_preferences=request.user_preferences,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_shadow_agentic_workflow_chain_dry_run",
    }


@app.post("/api/manual-shadow-recommendation-handoff-dry-run")
def invoke_manual_shadow_recommendation_handoff_dry_run_api_action(
    request: ManualShadowRecommendationHandoffDryRunRequest,
):
    payload = services.build_shadow_recommendation_handoff_payload(
        shadow_chain_payload=request.shadow_chain_payload,
        job_title=request.job_title,
        company=request.company,
        location=request.location,
        job_description=request.job_description,
        source_metadata=request.source_metadata,
        jd_intelligence=request.jd_intelligence,
        jd_signals=request.jd_signals,
        resume_variants=request.resume_variants or None,
        resume_evidence_rows=request.resume_evidence_rows,
        selected_resume_id=request.selected_resume_id,
        user_preferences=request.user_preferences,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_shadow_recommendation_handoff_dry_run",
    }


@app.post("/api/manual-human-decision-capture-dry-run")
def invoke_manual_human_decision_capture_dry_run_api_action(
    request: ManualHumanDecisionCaptureDryRunRequest,
):
    payload = services.build_human_decision_capture_dry_run_payload(
        handoff_payload=request.handoff_payload,
        shadow_chain_payload=request.shadow_chain_payload,
        reviewer_decision=request.reviewer_decision,
        reviewer_note=request.reviewer_note,
        job_title=request.job_title,
        company=request.company,
        location=request.location,
        job_description=request.job_description,
        source_metadata=request.source_metadata,
        jd_intelligence=request.jd_intelligence,
        jd_signals=request.jd_signals,
        resume_variants=request.resume_variants or None,
        resume_evidence_rows=request.resume_evidence_rows,
        selected_resume_id=request.selected_resume_id,
        user_preferences=request.user_preferences,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_human_decision_capture_dry_run",
    }


@app.post("/api/manual-human-approved-action-plan-dry-run")
def invoke_manual_human_approved_action_plan_dry_run_api_action(
    request: ManualHumanApprovedActionPlanDryRunRequest,
):
    payload = services.build_human_approved_action_plan_dry_run_payload(
        decision_capture_payload=request.decision_capture_payload,
        handoff_payload=request.handoff_payload,
        shadow_chain_payload=request.shadow_chain_payload,
        reviewer_decision=request.reviewer_decision,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_human_approved_action_plan_dry_run",
    }


@app.post("/api/manual-review-packet-preview-dry-run")
def invoke_manual_review_packet_preview_dry_run_api_action(
    request: ManualReviewPacketPreviewDryRunRequest,
):
    payload = services.build_review_packet_preview_dry_run_payload(
        action_plan_payload=request.action_plan_payload,
        decision_capture_payload=request.decision_capture_payload,
        handoff_payload=request.handoff_payload,
        shadow_chain_payload=request.shadow_chain_payload,
        reviewer_decision=request.reviewer_decision,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_review_packet_preview_dry_run",
    }


@app.post("/api/manual-approval-request-preview-dry-run")
def invoke_manual_approval_request_preview_dry_run_api_action(
    request: ManualApprovalRequestPreviewDryRunRequest,
):
    payload = services.build_approval_request_preview_dry_run_payload(
        review_packet_payload=request.review_packet_payload,
        action_plan_payload=request.action_plan_payload,
        decision_capture_payload=request.decision_capture_payload,
        handoff_payload=request.handoff_payload,
        shadow_chain_payload=request.shadow_chain_payload,
        reviewer_decision=request.reviewer_decision,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_approval_request_preview_dry_run",
    }


@app.post("/api/manual-approval-creation-gate-dry-run")
def invoke_manual_approval_creation_gate_dry_run_api_action(
    request: ManualApprovalCreationGateDryRunRequest,
):
    payload = services.build_approval_creation_gate_dry_run_payload(
        approval_preview_payload=request.approval_preview_payload,
        review_packet_payload=request.review_packet_payload,
        action_plan_payload=request.action_plan_payload,
        decision_capture_payload=request.decision_capture_payload,
        handoff_payload=request.handoff_payload,
        shadow_chain_payload=request.shadow_chain_payload,
        reviewer_confirmation=request.reviewer_confirmation,
        reviewer_decision=request.reviewer_decision,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_approval_creation_gate_dry_run",
    }


@app.post(
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-reporting-job"
)
def invoke_production_scheduler_observability_reporting_job_endpoint(
    approval_request_id: str,
):
    reporting_decision = (
        _production_scheduler_observability_reporting_decision_for_approval(
            approval_request_id
        )
    )
    return _agentic_production_scheduler_observability_reporting_job_payload(
        approval_request_id=approval_request_id,
        reporting_decision=reporting_decision,
    )

@app.post("/api/manual-guarded-approval-request-create")
def invoke_manual_guarded_approval_request_create_api_action(
    request: ManualGuardedApprovalRequestCreateRequest,
):
    payload = services.build_guarded_approval_request_creation_payload(
        approval_creation_gate_payload=request.approval_creation_gate_payload,
        approval_preview_payload=request.approval_preview_payload,
        review_packet_payload=request.review_packet_payload,
        action_plan_payload=request.action_plan_payload,
        decision_capture_payload=request.decision_capture_payload,
        handoff_payload=request.handoff_payload,
        shadow_chain_payload=request.shadow_chain_payload,
        reviewer_confirmation=request.reviewer_confirmation,
        reviewer_decision=request.reviewer_decision,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
        connection_provider=_agentic_approval_storage_connection,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_approval_request_create",
    }


@app.post("/api/manual-guarded-approval-creation-observability")
def invoke_manual_guarded_approval_creation_observability_api_action(
    request: ManualGuardedApprovalCreationObservabilityRequest,
):
    payload = services.build_guarded_approval_creation_observability_payload(
        guarded_creation_payload=request.guarded_creation_payload,
        approval_creation_gate_payload=request.approval_creation_gate_payload,
        approval_preview_payload=request.approval_preview_payload,
        review_packet_payload=request.review_packet_payload,
        action_plan_payload=request.action_plan_payload,
        decision_capture_payload=request.decision_capture_payload,
        handoff_payload=request.handoff_payload,
        shadow_chain_payload=request.shadow_chain_payload,
        created_approval_request_id=request.created_approval_request_id,
        reviewer_confirmation=request.reviewer_confirmation,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_approval_creation_observability",
    }


@app.get("/api/agent-feedback/summary")
def agent_feedback_summary(
    http_request: Request,
    pipeline_run_id: str = "",
    context_id: str = "",
    target_type: str = "",
    event_type: str = "",
    limit: int = 1000,
):
    try:
        return services.agent_feedback_summary_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
            pipeline_run_id=pipeline_run_id,
            context_id=context_id,
            target_type=target_type,
            event_type=event_type,
            limit=limit,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/api/manual-approval-request-readback")
def invoke_manual_approval_request_readback_api_action(
    request: ManualApprovalRequestReadbackRequest,
):
    payload = services.build_approval_request_readback_payload(
        approval_request_id=request.approval_request_id,
        guarded_creation_payload=request.guarded_creation_payload,
        observability_payload=request.observability_payload,
        context_id=request.context_id,
        job_id=request.job_id,
        connection_provider=_agentic_approval_storage_connection,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_approval_request_readback",
    }


@app.post("/api/manual-approval-status-transition-preview-dry-run")
def invoke_manual_approval_status_transition_preview_api_action(
    request: ManualApprovalStatusTransitionPreviewRequest,
):
    payload = services.build_approval_status_transition_preview_payload(
        approval_request_id=request.approval_request_id,
        proposed_transition=request.proposed_transition,
        reviewer_note=request.reviewer_note,
        approval_request_readback_payload=request.approval_request_readback_payload,
        guarded_creation_payload=request.guarded_creation_payload,
        observability_payload=request.observability_payload,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_approval_status_transition_preview_dry_run",
    }


@app.get("/api/agent-feedback/export")
def agent_feedback_export(
    http_request: Request,
    pipeline_run_id: str = "",
    target_type: str = "",
    event_type: str = "",
    limit: int = 1000,
):
    try:
        return services.agent_feedback_export_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
            pipeline_run_id=pipeline_run_id,
            target_type=target_type,
            event_type=event_type,
            limit=limit,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/manual-guarded-approval-status-transition")
def invoke_manual_guarded_approval_status_transition_api_action(
    request: ManualGuardedApprovalStatusTransitionRequest,
):
    payload = services.build_guarded_approval_status_transition_payload(
        approval_request_id=request.approval_request_id,
        proposed_transition=request.proposed_transition,
        reviewer_confirmation=request.reviewer_confirmation,
        reviewer_note=request.reviewer_note,
        transition_preview_payload=request.transition_preview_payload,
        approval_request_readback_payload=request.approval_request_readback_payload,
        guarded_creation_payload=request.guarded_creation_payload,
        observability_payload=request.observability_payload,
        context_id=request.context_id,
        job_id=request.job_id,
        connection_provider=_agentic_approval_storage_connection,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_approval_status_transition",
    }


@app.post("/api/manual-approval-status-transition-observability")
def invoke_manual_approval_status_transition_observability_api_action(
    request: ManualApprovalStatusTransitionObservabilityRequest,
):
    payload = services.build_guarded_approval_status_transition_observability_payload(
        guarded_status_transition_payload=request.guarded_status_transition_payload,
        approval_request_id=request.approval_request_id,
        proposed_transition=request.proposed_transition,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_approval_status_transition_observability",
    }


@app.post("/api/manual-queue-handoff-readiness-preview-dry-run")
def invoke_manual_queue_handoff_readiness_preview_api_action(
    request: ManualQueueHandoffReadinessPreviewRequest,
):
    payload = services.build_queue_handoff_readiness_preview_payload(
        approval_request_id=request.approval_request_id,
        approval_request_readback_payload=request.approval_request_readback_payload,
        approval_status_transition_observability_payload=request.approval_status_transition_observability_payload,
        approval_status_transition_payload=request.approval_status_transition_payload,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_queue_handoff_readiness_preview_dry_run",
    }


@app.post("/api/manual-guarded-queue-handoff-create")
def invoke_manual_guarded_queue_handoff_create_api_action(
    request: ManualGuardedQueueHandoffCreateRequest,
):
    payload = services.build_guarded_queue_handoff_creation_payload(
        approval_request_id=request.approval_request_id,
        reviewer_confirmation=request.reviewer_confirmation,
        queue_handoff_readiness_payload=request.queue_handoff_readiness_payload,
        approval_request_readback_payload=request.approval_request_readback_payload,
        approval_status_transition_observability_payload=request.approval_status_transition_observability_payload,
        context_id=request.context_id,
        job_id=request.job_id,
        reviewer_note=request.reviewer_note,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_queue_handoff_create",
    }


@app.post("/api/manual-queue-handoff-creation-observability")
def invoke_manual_queue_handoff_creation_observability_api_action(
    request: ManualQueueHandoffCreationObservabilityRequest,
):
    payload = services.build_guarded_queue_handoff_creation_observability_payload(
        guarded_queue_handoff_creation_payload=request.guarded_queue_handoff_creation_payload,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_queue_handoff_creation_observability",
    }


@app.post("/api/manual-execution-readiness-preview-dry-run")
def invoke_manual_execution_readiness_preview_api_action(
    request: ManualExecutionReadinessPreviewRequest,
):
    payload = services.build_execution_readiness_preview_payload(
        queue_handoff_id=request.queue_handoff_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_creation_payload=request.queue_handoff_creation_payload,
        queue_handoff_observability_payload=request.queue_handoff_observability_payload,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_execution_readiness_preview_dry_run",
    }


@app.post("/api/manual-execution-launch-gate-preview-dry-run")
def invoke_manual_execution_launch_gate_preview_api_action(
    request: ManualExecutionLaunchGatePreviewRequest,
):
    payload = services.build_execution_launch_gate_preview_payload(
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        execution_readiness_payload=request.execution_readiness_payload,
        queue_handoff_observability_payload=request.queue_handoff_observability_payload,
        reviewer_confirmation_preview=request.reviewer_confirmation_preview,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_execution_launch_gate_preview_dry_run",
    }


@app.post("/api/manual-execution-launch-gate-observability")
def invoke_manual_execution_launch_gate_observability_api_action(
    request: ManualExecutionLaunchGateObservabilityRequest,
):
    payload = services.build_execution_launch_gate_observability_payload(
        execution_launch_gate_payload=request.execution_launch_gate_payload,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_execution_launch_gate_observability",
    }


@app.post("/api/manual-execution-request-packet-preview-dry-run")
def invoke_manual_execution_request_packet_preview_api_action(
    request: ManualExecutionRequestPacketPreviewRequest,
):
    payload = services.build_execution_request_packet_preview_payload(
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        execution_launch_gate_payload=request.execution_launch_gate_payload,
        execution_launch_gate_observability_payload=request.execution_launch_gate_observability_payload,
        execution_readiness_payload=request.execution_readiness_payload,
        queue_handoff_observability_payload=request.queue_handoff_observability_payload,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_execution_request_packet_preview_dry_run",
    }


@app.post("/api/manual-guarded-execution-request-create")
def invoke_manual_guarded_execution_request_create_api_action(
    request: ManualGuardedExecutionRequestCreateRequest,
):
    payload = services.build_guarded_execution_request_creation_payload(
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        reviewer_confirmation=request.reviewer_confirmation,
        execution_request_packet_payload=request.execution_request_packet_payload,
        execution_launch_gate_payload=request.execution_launch_gate_payload,
        execution_launch_gate_observability_payload=request.execution_launch_gate_observability_payload,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_execution_request_create",
    }


@app.post("/api/manual-guarded-execution-request-observability")
def invoke_manual_guarded_execution_request_observability_api_action(
    request: ManualGuardedExecutionRequestObservabilityRequest,
):
    payload = services.build_guarded_execution_request_creation_observability_payload(
        guarded_execution_request_creation_payload=request.guarded_execution_request_creation_payload,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        execution_request_id=request.execution_request_id,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_execution_request_observability",
    }


@app.post("/api/manual-execution-request-readback")
def invoke_manual_execution_request_readback_api_action(
    request: ManualExecutionRequestReadbackRequest,
):
    payload = services.build_execution_request_readback_payload(
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        guarded_execution_request_creation_payload=request.guarded_execution_request_creation_payload,
        execution_request_creation_observability_payload=request.execution_request_creation_observability_payload,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_execution_request_readback",
    }


@app.post("/api/manual-execution-request-status-transition-preview-dry-run")
def invoke_manual_execution_request_status_transition_preview_api_action(
    request: ManualExecutionRequestStatusTransitionPreviewRequest,
):
    payload = services.build_execution_request_status_transition_preview_payload(
        execution_request_id=request.execution_request_id,
        requested_transition=request.requested_transition,
        execution_request_readback_payload=request.execution_request_readback_payload,
        execution_request_creation_payload=request.execution_request_creation_payload,
        execution_request_creation_observability_payload=request.execution_request_creation_observability_payload,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_execution_request_status_transition_preview_dry_run",
    }


@app.post("/api/manual-guarded-execution-request-status-transition")
def invoke_manual_guarded_execution_request_status_transition_api_action(
    request: ManualGuardedExecutionRequestStatusTransitionRequest,
):
    payload = services.build_guarded_execution_request_status_transition_payload(
        execution_request_id=request.execution_request_id,
        requested_transition=request.requested_transition,
        reviewer_confirmation=request.reviewer_confirmation,
        execution_request_status_transition_preview_payload=request.execution_request_status_transition_preview_payload,
        execution_request_readback_payload=request.execution_request_readback_payload,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_execution_request_status_transition",
    }


@app.post("/api/manual-guarded-execution-request-status-transition-observability")
def invoke_manual_guarded_execution_request_status_transition_observability_api_action(
    request: ManualGuardedExecutionRequestStatusTransitionObservabilityRequest,
):
    payload = services.build_guarded_execution_request_status_transition_observability_payload(
        guarded_execution_request_status_transition_payload=(
            request.guarded_execution_request_status_transition_payload
        ),
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_execution_request_status_transition_observability",
    }


@app.post("/api/manual-application-execution-simulation-preview-dry-run")
def invoke_manual_application_execution_simulation_preview_api_action(
    request: ManualApplicationExecutionSimulationPreviewRequest,
):
    payload = services.build_application_execution_simulation_preview_payload(
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        execution_request_readback_payload=request.execution_request_readback_payload,
        execution_request_status_transition_payload=request.execution_request_status_transition_payload,
        execution_request_status_transition_observability_payload=(
            request.execution_request_status_transition_observability_payload
        ),
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_application_execution_simulation_preview_dry_run",
    }


@app.post("/api/manual-application-execution-simulation-observability")
def invoke_manual_application_execution_simulation_observability_api_action(
    request: ManualApplicationExecutionSimulationObservabilityRequest,
):
    payload = services.build_application_execution_simulation_observability_payload(
        application_execution_simulation_payload=request.application_execution_simulation_payload,
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_application_execution_simulation_observability",
    }


@app.post("/api/manual-application-execution-preflight-checklist-dry-run")
def invoke_manual_application_execution_preflight_checklist_api_action(
    request: ManualApplicationExecutionPreflightChecklistRequest,
):
    payload = services.build_application_execution_preflight_checklist_payload(
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        application_execution_simulation_payload=request.application_execution_simulation_payload,
        application_execution_simulation_observability_payload=(
            request.application_execution_simulation_observability_payload
        ),
        execution_request_readback_payload=request.execution_request_readback_payload,
        execution_request_status_transition_observability_payload=(
            request.execution_request_status_transition_observability_payload
        ),
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_application_execution_preflight_checklist_dry_run",
    }


@app.post("/api/manual-application-execution-preflight-observability")
def invoke_manual_application_execution_preflight_observability_api_action(
    request: ManualApplicationExecutionPreflightObservabilityRequest,
):
    payload = services.build_application_execution_preflight_observability_payload(
        application_execution_preflight_payload=request.application_execution_preflight_payload,
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_application_execution_preflight_observability",
    }


@app.post("/api/manual-guarded-application-execution-launch-request-create")
def invoke_manual_guarded_application_execution_launch_request_create_api_action(
    request: ManualGuardedApplicationExecutionLaunchRequestCreateRequest,
):
    payload = services.build_guarded_application_execution_launch_request_payload(
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        reviewer_confirmation=request.reviewer_confirmation,
        application_execution_preflight_payload=request.application_execution_preflight_payload,
        application_execution_preflight_observability_payload=(
            request.application_execution_preflight_observability_payload
        ),
        application_execution_simulation_payload=request.application_execution_simulation_payload,
        application_execution_simulation_observability_payload=(
            request.application_execution_simulation_observability_payload
        ),
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_application_execution_launch_request_create",
    }


@app.post("/api/manual-guarded-application-execution-launch-request-observability")
def invoke_manual_guarded_application_execution_launch_request_observability_api_action(
    request: ManualGuardedApplicationExecutionLaunchRequestObservabilityRequest,
):
    payload = services.build_guarded_application_execution_launch_request_observability_payload(
        guarded_application_execution_launch_request_payload=(
            request.guarded_application_execution_launch_request_payload
        ),
        execution_launch_request_id=request.execution_launch_request_id,
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_application_execution_launch_request_observability",
    }


@app.post("/api/manual-application-execution-launch-request-readback")
def invoke_manual_application_execution_launch_request_readback_api_action(
    request: ManualApplicationExecutionLaunchRequestReadbackRequest,
):
    payload = services.build_application_execution_launch_request_readback_payload(
        execution_launch_request_id=request.execution_launch_request_id,
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        guarded_application_execution_launch_request_payload=(
            request.guarded_application_execution_launch_request_payload
        ),
        application_execution_launch_request_observability_payload=(
            request.application_execution_launch_request_observability_payload
        ),
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_application_execution_launch_request_readback",
    }


@app.post("/api/manual-execution-launch-request-status-transition-preview-dry-run")
def invoke_manual_execution_launch_request_status_transition_preview_api_action(
    request: ManualExecutionLaunchRequestStatusTransitionPreviewRequest,
):
    payload = services.build_execution_launch_request_status_transition_preview_payload(
        execution_launch_request_id=request.execution_launch_request_id,
        requested_transition=request.requested_transition,
        application_execution_launch_request_readback_payload=(
            request.application_execution_launch_request_readback_payload
        ),
        guarded_application_execution_launch_request_payload=(
            request.guarded_application_execution_launch_request_payload
        ),
        application_execution_launch_request_observability_payload=(
            request.application_execution_launch_request_observability_payload
        ),
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_execution_launch_request_status_transition_preview_dry_run",
    }


@app.post("/api/manual-guarded-execution-launch-request-status-transition")
def invoke_manual_guarded_execution_launch_request_status_transition_api_action(
    request: ManualGuardedExecutionLaunchRequestStatusTransitionRequest,
):
    payload = services.build_guarded_execution_launch_request_status_transition_payload(
        execution_launch_request_id=request.execution_launch_request_id,
        requested_transition=request.requested_transition,
        reviewer_confirmation=request.reviewer_confirmation,
        execution_launch_request_status_transition_preview_payload=(
            request.execution_launch_request_status_transition_preview_payload
        ),
        application_execution_launch_request_readback_payload=(
            request.application_execution_launch_request_readback_payload
        ),
        guarded_application_execution_launch_request_payload=(
            request.guarded_application_execution_launch_request_payload
        ),
        application_execution_launch_request_observability_payload=(
            request.application_execution_launch_request_observability_payload
        ),
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_execution_launch_request_status_transition",
    }


@app.post("/api/manual-guarded-execution-launch-request-status-transition-observability")
def invoke_manual_guarded_execution_launch_request_status_transition_observability_api_action(
    request: ManualGuardedExecutionLaunchRequestStatusTransitionObservabilityRequest,
):
    payload = services.build_guarded_execution_launch_request_status_transition_observability_payload(
        guarded_execution_launch_request_status_transition_payload=(
            request.guarded_execution_launch_request_status_transition_payload
        ),
        execution_launch_request_id=request.execution_launch_request_id,
        execution_request_id=request.execution_request_id,
        approval_request_id=request.approval_request_id,
        queue_handoff_id=request.queue_handoff_id,
        context_id=request.context_id,
        job_id=request.job_id,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "manual_guarded_execution_launch_request_status_transition_observability",
    }


@app.get("/api/agent-feedback")
def list_agent_feedback(
    http_request: Request,
    pipeline_run_id: str = "",
    context_id: str = "",
    target_type: str = "",
    event_type: str = "",
    limit: int = 200,
):
    try:
        return services.list_agent_feedback_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
            pipeline_run_id=pipeline_run_id,
            context_id=context_id,
            target_type=target_type,
            event_type=event_type,
            limit=limit,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/user/workspace-state")
def user_workspace_state(http_request: Request):
    return services.user_workspace_state_payload(
        owner_user_id=_auth_owner_user_id(http_request),
    )


@app.get("/status")
def status(
    http_request: Request,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    job_corpus: str = str(services.DEFAULT_CORPUS_PATH),
    top_k: int = 10,
):
    return services.status_payload(
        output_dir=Path(output_dir),
        job_corpus=Path(job_corpus),
        top_k=top_k,
        owner_user_id=_auth_owner_user_id(http_request),
    )

@app.get("/pipeline/status")
def pipeline_status(http_request: Request):
    return services.owner_pipeline_status_payload(
        owner_user_id=_auth_owner_user_id(http_request),
    )

@app.get("/scheduler/jobs")
def scheduler_jobs():
    return services.scheduler_jobs_payload()


@app.get("/scheduler/command")
def scheduler_command(
    job_name: str = Query(..., min_length=1),
    planning_only: bool = False,
    run_application_planning: bool = True,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    job_limit: int = 50,
    job_packet_limit: int = 0,
    llm_actions: str = "APPLY,APPLY_REVIEW_VARIANTS",
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    delete_seen_data: str = "no",
):
    try:
        return services.scheduler_job_command_payload(
            job_name=job_name,
            planning_only=planning_only,
            run_application_planning=run_application_planning,
            output_dir=Path(output_dir),
            job_limit=job_limit,
            job_packet_limit=job_packet_limit,
            llm_actions=llm_actions,
            generate_tailoring=generate_tailoring,
            generate_llm_tailoring=generate_llm_tailoring,
            refresh_llm_tailoring=refresh_llm_tailoring,
            generate_llm_fallback=generate_llm_fallback,
            delete_seen_data=delete_seen_data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/scheduler/launchd-config")
def scheduler_launchd_config(
    job_name: str = "",
    planning_only: bool = False,
    run_application_planning: bool = True,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    job_limit: int = 50,
    job_packet_limit: int = 0,
    llm_actions: str = "APPLY,APPLY_REVIEW_VARIANTS",
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    delete_seen_data: str = "no",
    sync_postgres_run_history: bool = False,
    require_postgres_run_history_sync: bool = False,
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    allow_contract_drift: bool = False,
    launchd_interval_seconds: int = services.DEFAULT_LAUNCHD_INTERVAL_SECONDS,
    launchd_out_dir: str = str(services.DEFAULT_LAUNCHD_OUT_DIR),
    launchd_log_dir: str = str(services.DEFAULT_LAUNCHD_LOG_DIR),
    launchd_label_prefix: str = services.DEFAULT_LAUNCHD_LABEL_PREFIX,
):
    try:
        return services.scheduler_launchd_config_payload(
            job_name=job_name,
            planning_only=planning_only,
            run_application_planning=run_application_planning,
            output_dir=Path(output_dir),
            job_limit=job_limit,
            job_packet_limit=job_packet_limit,
            llm_actions=llm_actions,
            generate_tailoring=generate_tailoring,
            generate_llm_tailoring=generate_llm_tailoring,
            refresh_llm_tailoring=refresh_llm_tailoring,
            generate_llm_fallback=generate_llm_fallback,
            delete_seen_data=delete_seen_data,
            sync_postgres_run_history=sync_postgres_run_history,
            require_postgres_run_history_sync=require_postgres_run_history_sync,
            database_url_env=database_url_env,
            psql_bin=psql_bin,
            allow_contract_drift=allow_contract_drift,
            launchd_interval_seconds=launchd_interval_seconds,
            launchd_out_dir=Path(launchd_out_dir),
            launchd_log_dir=Path(launchd_log_dir),
            launchd_label_prefix=launchd_label_prefix,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
@app.get("/scheduler/launchd-agent-status")
def scheduler_launchd_agent_status(
    job_name: str = "",
    planning_only: bool = False,
    run_application_planning: bool = True,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    job_limit: int = 50,
    job_packet_limit: int = 0,
    llm_actions: str = "APPLY,APPLY_REVIEW_VARIANTS",
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    delete_seen_data: str = "no",
    sync_postgres_run_history: bool = False,
    require_postgres_run_history_sync: bool = False,
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    allow_contract_drift: bool = False,
    launchd_interval_seconds: int = services.DEFAULT_LAUNCHD_INTERVAL_SECONDS,
    launchd_out_dir: str = str(services.DEFAULT_LAUNCHD_OUT_DIR),
    launchd_log_dir: str = str(services.DEFAULT_LAUNCHD_LOG_DIR),
    launchd_label_prefix: str = services.DEFAULT_LAUNCHD_LABEL_PREFIX,
    launchd_agent_dir: str = str(services.DEFAULT_LAUNCHD_AGENT_DIR),
    launchd_target: str = services.DEFAULT_LAUNCHD_TARGET,
):
    try:
        return services.scheduler_launchd_agent_status_payload(
            job_name=job_name,
            planning_only=planning_only,
            run_application_planning=run_application_planning,
            output_dir=Path(output_dir),
            job_limit=job_limit,
            job_packet_limit=job_packet_limit,
            llm_actions=llm_actions,
            generate_tailoring=generate_tailoring,
            generate_llm_tailoring=generate_llm_tailoring,
            refresh_llm_tailoring=refresh_llm_tailoring,
            generate_llm_fallback=generate_llm_fallback,
            delete_seen_data=delete_seen_data,
            sync_postgres_run_history=sync_postgres_run_history,
            require_postgres_run_history_sync=require_postgres_run_history_sync,
            database_url_env=database_url_env,
            psql_bin=psql_bin,
            allow_contract_drift=allow_contract_drift,
            launchd_interval_seconds=launchd_interval_seconds,
            launchd_out_dir=Path(launchd_out_dir),
            launchd_log_dir=Path(launchd_log_dir),
            launchd_label_prefix=launchd_label_prefix,
            launchd_agent_dir=Path(launchd_agent_dir),
            launchd_target=launchd_target,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
@app.get("/scheduler/history")
def scheduler_history(
    history_path: str = str(services.DEFAULT_SCHEDULER_RUN_HISTORY_PATH),
    job_name: str = "",
    status: str = "",
    limit: int = 20,
):
    return services.scheduler_history_payload(
        history_path=Path(history_path),
        job_name=job_name,
        status=status,
        limit=limit,
    )

@app.get("/scheduler/storage-contract")
def scheduler_storage_contract(
    include_sql: bool = False,
    include_generated_seed_sql: bool = False,
    include_generated_init_sql: bool = False,
):
    return services.scheduler_storage_contract_payload(
        include_sql=include_sql,
        include_generated_seed_sql=include_generated_seed_sql,
        include_generated_init_sql=include_generated_init_sql,
    )

@app.get("/scheduler/postgres-status")
def scheduler_postgres_status(
    limit: int = 10,
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
):
    try:
        return services.scheduler_postgres_status_payload(
            limit=limit,
            database_url_env=database_url_env,
            psql_bin=psql_bin,
        )
    except (ValueError, SystemExit) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/scheduler/summary")
def scheduler_summary(
    limit: int = 5,
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
):
    try:
        return services.scheduler_operator_summary_payload(
            limit=limit,
            database_url_env=database_url_env,
            psql_bin=psql_bin,
        )
    except (ValueError, SystemExit) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/notifications")
def notifications(
    notification_dir: str = str(services.DEFAULT_NOTIFICATION_RECORDS_DIR),
    job_name: str = "",
    level: str = "",
    delivery_status: str = "",
    is_read: str = "",
    limit: int = 20,
):
    return services.notifications_payload(
        notification_dir=Path(notification_dir),
        job_name=job_name,
        level=level,
        delivery_status=delivery_status,
        is_read=is_read,
        limit=limit,
    )

@app.get("/notifications/summary")
def notifications_summary(
    notification_dir: str = str(services.DEFAULT_NOTIFICATION_RECORDS_DIR),
    limit: int = 10,
):
    return services.notifications_summary_payload(
        notification_dir=Path(notification_dir),
        limit=limit,
    )

@app.get("/notifications/unread-count")
def notifications_unread_count(
    notification_dir: str = str(services.DEFAULT_NOTIFICATION_RECORDS_DIR),
):
    return services.notifications_unread_count_payload(
        notification_dir=Path(notification_dir),
    )


@app.post("/notifications/read-state")
def notifications_read_state(
    payload: dict = Body(...),
    notification_dir: str = str(services.DEFAULT_NOTIFICATION_RECORDS_DIR),
):
    try:
        return services.record_notification_read_state_payload(
            notification_dir=Path(notification_dir),
            notification_id=str(payload.get("notification_id", "") or ""),
            is_read=payload.get("is_read", True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
@app.post("/pipeline/run")
def run_live_pipeline(http_request: Request, payload: dict = Body(...)):
    try:
        return services.run_live_pipeline_payload(
            owner_user_id=_auth_owner_user_id(http_request),
        output_dir=Path(str(payload.get("output_dir", services.DEFAULT_OUTPUT_DIR))),
        log_path=Path(str(payload.get("log_path", services.DEFAULT_PIPELINE_LOG_PATH))),
        job_limit=int(payload.get("job_limit", 50)),
        job_packet_limit=int(payload.get("job_packet_limit", 0)),
        llm_actions=payload.get("llm_actions", ["APPLY", "APPLY_REVIEW_VARIANTS"]),
        generate_tailoring=bool(payload.get("generate_tailoring", False)),
        generate_llm_tailoring=bool(payload.get("generate_llm_tailoring", False)),
        refresh_llm_tailoring=bool(payload.get("refresh_llm_tailoring", False)),
        generate_llm_fallback=bool(payload.get("generate_llm_fallback", False)),
        generate_llm_adjudication=bool(payload.get("generate_llm_adjudication", False)),
        planning_only=bool(payload.get("planning_only", False)),
        delete_seen_data=str(payload.get("delete_seen_data", "no") or "no"),
    )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
@app.get("/browse")
def browse(
    http_request: Request,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    action: list[str] | None = Query(default=None),
    needs_review: str = "",
    is_tie: str = "",
    fallback_status: list[str] | None = Query(default=None),
    winner_bucket: list[str] | None = Query(default=None),
    tailoring_state: list[str] | None = Query(default=None),
    company_contains: str = "",
    title_contains: str = "",
    undecided_only: str = "",
    page: int = 1,
    limit: int = 15,
):
    return services.browse_payload(
        output_dir=Path(output_dir),
        action=action or [],
        needs_review=needs_review,
        is_tie=is_tie,
        fallback_status=fallback_status or [],
        winner_bucket=winner_bucket or [],
        tailoring_state=tailoring_state or [],
        company_contains=company_contains,
        title_contains=title_contains,
        undecided_only=undecided_only,
        limit=limit,
        page=page,
        owner_user_id=_auth_owner_user_id(http_request),
    )


@app.get("/review")
def review(
    http_request: Request,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    action: str = "",
    queue_rank: int | None = None,
    job_doc_id: str = "",
    company_contains: str = "",
    title_contains: str = "",
    include_non_review: bool = False,
    undecided_only: str = "",
    limit: int = 20,
):
    return services.review_payload(
        output_dir=Path(output_dir),
        action=action,
        queue_rank=queue_rank,
        job_doc_id=job_doc_id,
        company_contains=company_contains,
        title_contains=title_contains,
        include_non_review=include_non_review,
        undecided_only=undecided_only,
        limit=limit,
        owner_user_id=_auth_owner_user_id(http_request),
    )


@app.get("/workflow")
def workflow(
    http_request: Request,
    view: str = Query(
        ...,
        pattern="^(undecided_apply_review|undecided_maybe_tailor|runner_up_selected|direct_apply_pending)$",
    ),
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    limit: int = 20,
):
    return services.workflow_payload(
        view=view,
        limit=limit,
        output_dir=Path(output_dir),
        owner_user_id=_auth_owner_user_id(http_request),
    )


@app.get("/planner")
def planner(
    http_request: Request,
    request: str,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    limit: int = 20,
):
    try:
        return services.planner_payload(
            request=request,
            limit=limit,
            output_dir=Path(output_dir),
            owner_user_id=_auth_owner_user_id(http_request),
        )
    except SystemExit as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/planning-artifact")
def planning_artifact(
    path: str,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
):
    try:
        return services.planning_artifact_payload(
            path=path,
            output_dir=Path(output_dir),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/planning/scan-preload")
def planning_scan_preload(
    http_request: Request,
    request: PlanningScanPreloadRequest,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
):
    try:
        return services.tailoring_scan_preload_payload(
            output_dir=Path(output_dir),
            tailoring_json_path=request.tailoring_json_path,
            selected_resume=request.selected_resume,
            owner_user_id=_auth_owner_user_id(http_request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/planning/start-scan")
def planning_start_scan(http_request: Request, request: PlanningStartScanRequest):
    try:
        upload_bytes = None
        if request.upload_base64:
            upload_bytes = base64.b64decode(request.upload_base64)
        return services.create_saved_scan_payload(
            scan_id=request.scan_id,
            owner_user_id=_auth_owner_user_id(http_request),
            owner_email=_auth_owner_email(http_request),
            company=request.company,
            role=request.role,
            job_description_text=request.job_description_text,
            job_url=request.job_url,
            job_doc_id=request.job_doc_id,
            saved_resume_name=request.saved_resume_name,
            resume_text=request.resume_text,
            upload_filename=request.upload_filename,
            upload_content_type=request.upload_content_type,
            upload_bytes=upload_bytes,
            tailoring_json_path=request.tailoring_json_path,
        )
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/planning/saved-scan/{scan_id}")
def planning_saved_scan(scan_id: str, http_request: Request):
    try:
        return services.saved_scan_report_payload(
            scan_id,
            owner_user_id=_auth_owner_user_id(http_request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.post("/planning/saved-scan/{scan_id}/state")
def planning_save_saved_scan_state(
    scan_id: str,
    http_request: Request,
    request: PlanningSavedScanStateRequest,
):
    try:
        return services.save_saved_scan_state_payload(
            scan_id=scan_id,
            owner_user_id=_auth_owner_user_id(http_request),
            selected_patch_candidate_ids=request.selected_patch_candidate_ids,
            manual_bullet_edits=request.manual_bullet_edits,
            rewrite_review_decisions=request.rewrite_review_decisions,
            excluded_scan_issue_ids=request.excluded_scan_issue_ids,
            personal_details=request.personal_details,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.delete("/profile/saved-scans/{scan_id}")
def profile_delete_saved_scan(scan_id: str, http_request: Request):
    try:
        return services.delete_saved_scan_payload(
            scan_id,
            owner_user_id=_auth_owner_user_id(http_request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/planning/extract-resume-upload")
def planning_extract_resume_upload(request: PlanningExtractResumeUploadRequest):
    try:
        return services.extract_scan_resume_upload_text_payload(
            filename=request.filename,
            content_type=request.content_type,
            file_bytes=base64.b64decode(request.upload_base64),
        )
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
     
@app.get("/planning/resume-preview")
def planning_resume_preview(
    http_request: Request,
    resume_name: str = Query(..., min_length=1),
):
    try:
        payload = services.profile_resume_file_payload(
            resume_name,
            owner_user_id=_auth_owner_user_id(http_request),
        )
        return Response(
            content=payload["file_bytes"],
            media_type=payload.get("content_type", "application/pdf"),
            headers={"Content-Disposition": 'inline; filename="resume.pdf"'},
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
@app.get("/decisions")
def decisions(
    http_request: Request,
    queue_rank: int | None = None,
    decision: list[str] | None = Query(default=None),
    selected_resume: str = "",
    company_contains: str = "",
    title_contains: str = "",
    page: int = 1,
    limit: int = 15,
):
    return services.decisions_payload(
        queue_rank=queue_rank,
        decision=decision or [],
        selected_resume=selected_resume,
        company_contains=company_contains,
        title_contains=title_contains,
        limit=limit,
        page=page,
        owner_user_id=_auth_owner_user_id(http_request),
    )

@app.post("/planning/select-resume")
def planning_select_resume(
    http_request: Request,
    payload: dict = Body(...),
):
    try:
        return services.record_operator_resume_selection_payload(
            queue_rank=str(payload.get("queue_rank", "") or ""),
            job_doc_id=str(payload.get("job_doc_id", "") or ""),
            job_company=str(payload.get("job_company", "") or ""),
            job_title=str(payload.get("job_title", "") or ""),
            planning_action=str(payload.get("planning_action", "") or ""),
            decision=str(payload.get("decision", "SELECT_RESUME") or "SELECT_RESUME"),
            selected_resume=str(payload.get("selected_resume", "") or ""),
            winner_resume=str(payload.get("winner_resume", "") or ""),
            winner_score=str(payload.get("winner_score", "") or ""),
            runner_up_resume=str(payload.get("runner_up_resume", "") or ""),
            runner_up_score=str(payload.get("runner_up_score", "") or ""),
            note=str(payload.get("note", "") or ""),
            owner_user_id=_auth_owner_user_id(http_request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/planning/regenerate-selected-resume")
def planning_regenerate_selected_resume(
    payload: dict = Body(...),
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    job_corpus: str = str(services.DEFAULT_CORPUS_PATH),
):
    try:
        return services.regenerate_selected_resume_tailoring_payload(
            output_dir=Path(output_dir),
            job_corpus=Path(job_corpus),
            job_doc_id=str(payload.get("job_doc_id", "") or ""),
            queue_rank=str(payload.get("queue_rank", "") or ""),
            selected_resume=str(payload.get("selected_resume", "") or ""),
            generate_llm_tailoring=bool(payload.get("generate_llm_tailoring", False)),
            refresh_llm_tailoring=bool(payload.get("refresh_llm_tailoring", False)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/planning/preview-selected-patches")
def planning_preview_selected_patches(
    payload: dict = Body(...),
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
):
    try:
        return services.preview_planning_patch_selection_payload(
            output_dir=Path(output_dir),
            tailoring_json_path=str(payload.get("tailoring_json_path", "") or ""),
            selected_candidate_ids=payload.get("selected_candidate_ids", []),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
@app.post("/planning/select-patches")
def planning_select_patches(
    payload: dict = Body(...),
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
):
    try:
        return services.record_planning_patch_selection_payload(
            output_dir=Path(output_dir),
            tailoring_json_path=str(payload.get("tailoring_json_path", "") or ""),
            job_doc_id=str(payload.get("job_doc_id", "") or ""),
            queue_rank=str(payload.get("queue_rank", "") or ""),
            selected_resume=str(payload.get("selected_resume", "") or ""),
            selected_candidate_ids=payload.get("selected_candidate_ids", []),
            note=str(payload.get("note", "") or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
@app.post("/planning/load-workspace-draft")
def load_workspace_draft(request: PlanningWorkspaceDraftLoadRequest):
    try:
        return services.load_tailoring_workspace_draft_payload(
            tailoring_json_path=request.tailoring_json_path,
            selected_resume=request.selected_resume,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/planning/save-workspace-draft")
def save_workspace_draft(request: PlanningWorkspaceDraftSaveRequest):
    try:
        return services.save_tailoring_workspace_draft_payload(
            tailoring_json_path=request.tailoring_json_path,
            selected_resume=request.selected_resume,
            selected_patch_candidate_ids=request.selected_patch_candidate_ids,
            manual_bullet_edits=request.manual_bullet_edits,
            rewrite_review_decisions=request.rewrite_review_decisions,
            excluded_scan_issue_ids=request.excluded_scan_issue_ids,
            personal_details=request.personal_details,
            note=request.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc



@app.post("/planning/preview-workspace-draft")
def preview_workspace_draft(
    http_request: Request,
    request: PlanningWorkspaceDraftPreviewRequest,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
):
    try:
        return services.preview_tailoring_workspace_draft_payload(
            output_dir=Path(output_dir),
            tailoring_json_path=request.tailoring_json_path,
            selected_resume=request.selected_resume,
            owner_user_id=_auth_owner_user_id(http_request),
            selected_patch_candidate_ids=request.selected_patch_candidate_ids,
            manual_bullet_edits=request.manual_bullet_edits,
            rewrite_review_decisions=request.rewrite_review_decisions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/planning/render-workspace-draft-preview")
def render_workspace_draft_preview(
    http_request: Request,
    request: PlanningWorkspaceDraftRenderRequest,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
):
    try:
        return services.render_tailoring_workspace_draft_preview_payload(
            output_dir=Path(output_dir),
            tailoring_json_path=request.tailoring_json_path,
            selected_resume=request.selected_resume,
            owner_user_id=_auth_owner_user_id(http_request),
            selected_patch_candidate_ids=request.selected_patch_candidate_ids,
            manual_bullet_edits=request.manual_bullet_edits,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/planning/generate-scan-phrases")
def generate_scan_phrases(
    request: PlanningScanPhraseRequest,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
):
    try:
        return services.generate_tailoring_scan_phrase_payload(
            output_dir=Path(output_dir),
            tailoring_json_path=request.tailoring_json_path,
            selected_resume=request.selected_resume,
            bullet_key=request.bullet_key,
            current_text=request.current_text,
            guidance_text=request.guidance_text,
            supported_terms=request.supported_terms,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    

@app.post("/planning/export-workspace-draft")
def export_workspace_draft(
    http_request: Request,
    request: PlanningWorkspaceDraftExportRequest,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
):
    try:
        payload = services.export_tailoring_workspace_draft_payload(
            output_dir=Path(output_dir),
            tailoring_json_path=request.tailoring_json_path,
            selected_resume=request.selected_resume,
            owner_user_id=_auth_owner_user_id(http_request),
            format=request.format,
        )
        return FileResponse(
            path=str(payload["path"]),
            media_type=str(payload["media_type"]),
            filename=str(payload["filename"]),
            headers={
                "X-Tailoring-Export-Status": str(payload.get("export_status", "complete")),
                "X-Tailoring-Export-Workspace-Patch-Count": str(payload.get("workspace_patch_count", 0)),
                "X-Tailoring-Export-Unresolved-Candidate-Count": str(
                    len(payload.get("unresolved_candidate_ids", []) or [])
                ),
                "X-Tailoring-Export-Unresolved-Manual-Key-Count": str(
                    len(payload.get("unresolved_manual_edit_keys", []) or [])
                ),
                "X-Tailoring-Export-Warning-Message": str(payload.get("warning_message", "") or ""),
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/application-actions")
def record_application_action(
    http_request: Request,
    payload: dict = Body(...),
):
    try:
        return services.record_application_action_payload(
            job_doc_id=str(payload.get("job_doc_id", "") or ""),
            job_url=str(payload.get("job_url", "") or ""),
            job_company=str(payload.get("job_company", "") or ""),
            job_title=str(payload.get("job_title", "") or ""),
            application_status=str(payload.get("application_status", "") or ""),
            source_view=str(payload.get("source_view", "") or ""),
            note=str(payload.get("note", "") or ""),
            owner_user_id=_auth_owner_user_id(http_request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/applied-jobs")
def applied_jobs(
    http_request: Request,
    company_contains: str = "",
    title_contains: str = "",
    page: int = 1,
    limit: int = 15,
):
    return services.applied_jobs_payload(
        company_contains=company_contains,
        title_contains=title_contains,
        limit=limit,
        page=page,
        owner_user_id=_auth_owner_user_id(http_request),
    )

@app.get("/rag/search")
def rag_search(
    request: str,
    top_k: int = 5,
    fetch_k: int = 15,
    output_mode: str = "compact",
    include_diagnostics: bool = False,
):
    
    return services.rag_search_payload(
        request=request,
        top_k=top_k,
        fetch_k=fetch_k,
        output_mode=output_mode,
        include_diagnostics=include_diagnostics,
    )

@app.get("/jobs/search-lite")
def jobs_search_lite(
    request: str,
    top_k: int = 10,
):
    return services.jobs_search_lite_payload(
        request=request,
        top_k=top_k,
    )

@app.get("/assistant/query")
def assistant_query(
    request: str,
    top_k: int = 5,
    fetch_k: int = 10,
    include_diagnostics: bool = False,
):
    return services.assistant_query_payload(
        request=request,
        top_k=top_k,
        fetch_k=fetch_k,
        include_diagnostics=include_diagnostics,
    )

@app.get("/rag/answer")
def rag_answer(
    request: str,
    top_k: int = 5,
    fetch_k: int = 15,
    output_mode: str = "compact",
    include_diagnostics: bool = False,
):
    return services.rag_answer_payload(
        request=request,
        top_k=top_k,
        fetch_k=fetch_k,
        output_mode=output_mode,
        include_diagnostics=include_diagnostics,
    )


@app.get("/profile/resumes")
def profile_resumes(http_request: Request):
    try:
        return services.profile_resumes_payload(
            owner_user_id=_auth_owner_user_id(http_request),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/profile/resume-role-mappings")
def profile_resume_role_mappings(http_request: Request):
    try:
        return services.profile_resume_role_mappings_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/profile/resume-role-mappings")
def save_profile_resume_role_mapping(
    http_request: Request,
    payload: dict = Body(...),
):
    try:
        return services.save_profile_resume_role_mapping_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
            resume_name=payload.get("resume_name", ""),
            role_family_id=payload.get("role_family_id", ""),
            is_default_for_role=bool(payload.get("is_default_for_role", False)),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/profile/resume-role-mappings")
def delete_profile_resume_role_mapping(
    http_request: Request,
    resume_name: str = Query(..., min_length=1),
    role_family_id: str = Query(..., min_length=1),
):
    try:
        return services.delete_profile_resume_role_mapping_service_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
            resume_name=resume_name,
            role_family_id=role_family_id,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/onboarding/preferences")
def onboarding_preferences(http_request: Request):
    try:
        return services.onboarding_preferences_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/onboarding/preferences")
def save_onboarding_preferences(
    http_request: Request,
    payload: dict = Body(...),
):
    try:
        return services.save_onboarding_preferences_payload(
            payload,
            owner_user_id=_require_auth_owner_user_id(http_request),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/onboarding/status")
def onboarding_status(http_request: Request):
    try:
        return services.onboarding_status_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/profile/admin/users")
def profile_admin_users(http_request: Request, limit: int = 100):
    _require_admin_user(http_request)
    try:
        return services.admin_profile_users_payload(limit=limit)
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/profile/admin/users/{user_id}/access")
def profile_admin_update_user_access(
    user_id: str,
    http_request: Request,
    payload: dict = Body(...),
):
    _require_admin_user(http_request)
    try:
        return services.admin_profile_update_user_access_payload(
            user_id=user_id,
            is_active=bool(payload.get("is_active", False)),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/profile/admin/users/{user_id}")
def profile_admin_delete_user(user_id: str, http_request: Request):
    _require_admin_user(http_request)
    try:
        return services.admin_profile_delete_user_payload(user_id=user_id)
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/profile/pipeline-runs")
def profile_pipeline_runs(
    http_request: Request,
    page: int = 1,
    page_size: int = 15,
):
    try:
        return services.profile_pipeline_runs_payload(
            owner_user_id=_auth_owner_user_id(http_request),
            page=page,
            page_size=page_size,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/profile/pipeline-runs/{run_id}")
def profile_pipeline_run_detail(run_id: str, http_request: Request):
    try:
        return services.profile_pipeline_run_detail_payload(
            owner_user_id=_auth_owner_user_id(http_request),
            run_id=run_id,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/profile/pipeline-runs/{run_id}/agent-trace")
def profile_pipeline_run_agent_trace(
    run_id: str,
    http_request: Request,
    context_id: str = "",
    agent_run_id: str = "",
    include_trace_summary: str = "",
    include_stage_trace_bundle: str = "",
    include_stage_trace_health: str = "",
    include_stage_trace_readiness: str = "",
    include_trace_evidence_pack: str = "",
):
    try:
        return services.agent_trace_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
            pipeline_run_id=run_id,
            context_id=context_id,
            agent_run_id=agent_run_id,
            include_trace_summary=str(include_trace_summary or "").strip().lower()
            in {"1", "true", "yes", "on"},
            include_stage_trace_bundle=str(include_stage_trace_bundle or "").strip().lower()
            in {"1", "true", "yes", "on"},
            include_stage_trace_health=str(include_stage_trace_health or "").strip().lower()
            in {"1", "true", "yes", "on"},
            include_stage_trace_readiness=str(include_stage_trace_readiness or "").strip().lower()
            in {"1", "true", "yes", "on"},
            include_trace_evidence_pack=str(include_trace_evidence_pack or "").strip().lower()
            in {"1", "true", "yes", "on"},
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/shadow-sidecar/trace-readback")
def shadow_sidecar_trace_readback(payload: dict | None = Body(default=None)):
    request_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    try:
        response = services.shadow_sidecar_trace_readback_service_payload(
            owner_user_id=request_payload.get("owner_user_id", ""),
            pipeline_run_id=request_payload.get("pipeline_run_id", ""),
            context_id=request_payload.get("context_id", ""),
            agent_run_id=request_payload.get("agent_run_id", ""),
            sidecar_config=(
                dict(request_payload.get("sidecar_config") or {})
                if isinstance(request_payload.get("sidecar_config"), dict)
                else {}
            ),
            readback_source=(
                dict(request_payload.get("readback_source") or {})
                if isinstance(request_payload.get("readback_source"), dict)
                else None
            ),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        response = {
            "trace_readback_status": "trace_readback_failed_non_blocking",
            "trace_readback_only": True,
            "readback_attempted": False,
            "source_trace_context": {
                "owner_user_id": str(request_payload.get("owner_user_id", "") or "").strip(),
                "pipeline_run_id": str(request_payload.get("pipeline_run_id", "") or "").strip(),
                "context_id": str(request_payload.get("context_id", "") or "").strip(),
                "agent_run_id": str(request_payload.get("agent_run_id", "") or "").strip(),
            },
            "trace_readback": {},
            "reader_result": {"ok": False, "error_type": exc.__class__.__name__},
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "service_helper_only": True,
            "api_route_added": True,
            "ui_action_added": False,
            "safety_metadata": {
                "read_only": True,
                "shadow_only": True,
                "service_helper_only": True,
                "trace_readback_only": True,
                "did_read_database": False,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_approval": False,
                "did_mutate_resume": False,
                "did_create_execution_request": False,
                "did_create_execution_launch_request": False,
                "did_execute_application": False,
                "did_submit_application": False,
                "auto_apply_enabled": False,
            },
        }
    safety = dict(response.get("safety_metadata", {}) or {})
    safety["api_readback_only"] = True
    safety["trace_readback_only"] = True
    response["safety_metadata"] = safety
    return {
        **response,
        "api_surface": "shadow_sidecar_trace_readback",
        "api_readback_only": True,
        "ui_action_added": False,
    }


@app.post("/api/shadow-sidecar/score-comparison")
def shadow_sidecar_score_comparison(payload: dict | None = Body(default=None)):
    request_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    try:
        response = services.shadow_sidecar_score_comparison_service_payload(
            deterministic_score_context=(
                dict(request_payload.get("deterministic_score_context") or {})
                if isinstance(request_payload.get("deterministic_score_context"), dict)
                else {}
            ),
            shadow_evidence_snapshot_payload=(
                dict(request_payload.get("shadow_evidence_snapshot_payload") or {})
                if isinstance(
                    request_payload.get("shadow_evidence_snapshot_payload"), dict
                )
                else {}
            ),
            sidecar_config=(
                dict(request_payload.get("sidecar_config") or {})
                if isinstance(request_payload.get("sidecar_config"), dict)
                else {}
            ),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        response = {
            "schema_version": "phase5_shadow_sidecar_trace_v1",
            "comparison_status": "comparison_failed_non_blocking",
            "comparison_type": "shadow_sidecar_vs_deterministic_score",
            "comparison_enabled": True,
            "deterministic_score": None,
            "deterministic_decision": "",
            "shadow_snapshot_status": "",
            "shadow_agent_names": [],
            "shadow_risk_flag_count": 0,
            "shadow_blocking_finding_count": 0,
            "agreement_level": "",
            "operator_review_summary": {
                "summary_type": "shadow_sidecar_score_comparison",
                "review_status": "failed_non_blocking",
                "operator_review_only": True,
                "read_only": True,
                "recommended_review_focus": ["retry_comparison_with_safe_inputs"],
            },
            "comparison_findings": [],
            "source_deterministic_context": {},
            "source_shadow_snapshot_context": {},
            "error_type": exc.__class__.__name__,
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "service_helper_only": True,
            "api_route_added": True,
            "ui_action_added": False,
            "safety_metadata": {
                "read_only": True,
                "shadow_only": True,
                "service_helper_only": True,
                "score_comparison_only": True,
                "operator_review_only": True,
                "did_read_database": False,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_approval": False,
                "did_mutate_resume": False,
                "did_create_execution_request": False,
                "did_create_execution_launch_request": False,
                "did_execute_application": False,
                "did_submit_application": False,
                "auto_apply_enabled": False,
                "mutation_authorized": False,
            },
        }
    safety = dict(response.get("safety_metadata", {}) or {})
    safety["api_readback_only"] = True
    safety["score_comparison_only"] = True
    response["safety_metadata"] = safety
    return {
        **response,
        "api_surface": "shadow_sidecar_score_comparison",
        "api_readback_only": True,
        "ui_action_added": False,
    }


@app.post("/api/human-reviewed-influence-preview")
def human_reviewed_influence_preview(payload: dict | None = Body(default=None)):
    request_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    try:
        response = services.human_reviewed_influence_preview_service_payload(
            deterministic_score_context=(
                dict(request_payload.get("deterministic_score_context") or {})
                if isinstance(request_payload.get("deterministic_score_context"), dict)
                else {}
            ),
            shadow_score_comparison_context=(
                dict(request_payload.get("shadow_score_comparison_context") or {})
                if isinstance(
                    request_payload.get("shadow_score_comparison_context"), dict
                )
                else {}
            ),
            preview_config=(
                dict(request_payload.get("preview_config") or {})
                if isinstance(request_payload.get("preview_config"), dict)
                else {}
            ),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        response = {
            "schema_version": "phase5_shadow_sidecar_trace_v1",
            "preview_status": "preview_failed_non_blocking",
            "preview_type": "human_reviewed_shadow_score_influence_preview",
            "preview_enabled": True,
            "deterministic_score_context": {},
            "shadow_comparison_context": {},
            "proposed_influence_summary": {},
            "proposed_score_adjustment_preview": {},
            "proposed_ranking_effect_preview": {},
            "required_human_review": True,
            "approval_gate_required": True,
            "operator_review_summary": {
                "summary_type": "human_reviewed_influence_preview",
                "review_status": "failed_non_blocking",
                "operator_review_only": True,
                "read_only": True,
                "advisory_only": True,
                "required_human_review": True,
                "approval_gate_required": True,
                "recommended_review_focus": ["retry_preview_with_safe_inputs"],
            },
            "preview_findings": [],
            "error_type": exc.__class__.__name__,
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "service_helper_only": True,
            "api_route_added": True,
            "ui_action_added": False,
            "safety_metadata": {
                "read_only": True,
                "advisory_only": True,
                "service_helper_only": True,
                "influence_preview_only": True,
                "human_review_required": True,
                "approval_gate_required": True,
                "did_read_database": False,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_approval": False,
                "did_mutate_resume": False,
                "did_create_execution_request": False,
                "did_create_execution_launch_request": False,
                "did_execute_application": False,
                "did_submit_application": False,
                "auto_apply_enabled": False,
                "mutation_authorized": False,
            },
        }
    safety = dict(response.get("safety_metadata", {}) or {})
    safety["api_readback_only"] = True
    safety["influence_preview_only"] = True
    response["safety_metadata"] = safety
    return {
        **response,
        "api_surface": "human_reviewed_influence_preview",
        "api_readback_only": True,
        "ui_action_added": False,
    }


@app.post("/api/human-reviewed-influence-approval-request")
def human_reviewed_influence_approval_request(
    request: HumanReviewedInfluenceApprovalRequest,
):
    payload = services.build_human_reviewed_influence_approval_request_payload(
        human_reviewed_influence_preview_payload=(
            request.human_reviewed_influence_preview_payload
        ),
        deterministic_score_context=request.deterministic_score_context,
        shadow_score_comparison_context=request.shadow_score_comparison_context,
        preview_config=request.preview_config,
        reviewer_confirmation=request.reviewer_confirmation,
        reviewer_note=request.reviewer_note,
        context_id=request.context_id,
        job_id=request.job_id,
        connection_provider=_agentic_approval_storage_connection,
    )
    return {
        **payload,
        "explicit_user_action": True,
        "api_surface": "human_reviewed_influence_approval_request",
        "ui_action_added": False,
    }


@app.post("/api/agent-recommendation-overlay")
def agent_recommendation_overlay(request: AgentRecommendationOverlayRequest):
    try:
        response = services.agent_recommendation_overlay_service_payload(
            deterministic_score_context=request.deterministic_score_context,
            shadow_score_comparison_context=request.shadow_score_comparison_context,
            human_reviewed_influence_preview_payload=(
                request.human_reviewed_influence_preview_payload
            ),
            influence_approval_request_payload=request.influence_approval_request_payload,
            overlay_config=request.overlay_config,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        response = {
            "schema_version": "phase6_agent_recommendation_overlay_v1",
            "overlay_status": "overlay_failed_non_blocking",
            "overlay_type": "agent_recommendation_overlay",
            "overlay_enabled": True,
            "deterministic_decision_context": {},
            "shadow_score_comparison": {},
            "human_reviewed_influence_preview": {},
            "approval_request_context": {},
            "recommended_review_action": "insufficient_context",
            "recommended_review_label": "Insufficient Context",
            "overlay_findings": [],
            "operator_review_summary": {
                "summary_type": "agent_recommendation_overlay",
                "review_status": "overlay_failed_non_blocking",
                "recommended_review_action": "insufficient_context",
                "operator_review_only": True,
                "read_only": True,
                "advisory_only": True,
                "human_review_required": True,
                "approval_gate_required_for_influence": True,
            },
            "error_type": exc.__class__.__name__,
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "service_helper_only": True,
            "api_route_added": True,
            "ui_action_added": False,
            "safety_metadata": {
                "read_only": True,
                "advisory_only": True,
                "service_helper_only": True,
                "overlay_only": True,
                "human_review_required": True,
                "approval_gate_required_for_influence": True,
                "did_read_database": False,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_approval": False,
                "did_mutate_resume": False,
                "did_create_execution_request": False,
                "did_create_execution_launch_request": False,
                "did_execute_application": False,
                "did_submit_application": False,
                "auto_apply_enabled": False,
                "mutation_authorized": False,
            },
        }
    safety = dict(response.get("safety_metadata", {}) or {})
    safety["api_readback_only"] = True
    safety["overlay_only"] = True
    response["safety_metadata"] = safety
    return {
        **response,
        "api_surface": "agent_recommendation_overlay",
        "api_readback_only": True,
        "ui_action_added": False,
    }


@app.post("/api/pipeline-generated-agent-recommendation-overlay-readback")
def pipeline_generated_agent_recommendation_overlay_readback(
    request: PipelineGeneratedAgentRecommendationOverlayReadbackRequest,
):
    try:
        response = (
            services.pipeline_generated_agent_recommendation_overlay_readback_service_payload(
                hook_payload=request.hook_payload,
                trace_capture_payload=request.trace_capture_payload,
                trace_persistence_payload=request.trace_persistence_payload,
                trace_readback_payload=request.trace_readback_payload,
                readback_source=request.readback_source,
            )
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        response = {
            "schema_version": "phase5_shadow_sidecar_trace_v1",
            "readback_status": "pipeline_generated_overlay_readback_failed_non_blocking",
            "readback_only": True,
            "readback_attempted": False,
            "reader_result": {"ok": False, "error_type": exc.__class__.__name__},
            "pipeline_generated_overlay_found": False,
            "pipeline_generated_overlay": {},
            "agent_recommendation_overlay": {},
            "auto_generation_status": "",
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "service_helper_only": True,
            "api_route_added": True,
            "ui_action_added": False,
            "safety_metadata": {
                "read_only": True,
                "readback_only": True,
                "advisory_only": True,
                "pipeline_generated_overlay_readback": True,
                "did_read_database": False,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_approval": False,
                "did_mutate_resume": False,
                "did_create_execution_request": False,
                "did_create_execution_launch_request": False,
                "did_execute_application": False,
                "did_submit_application": False,
                "auto_apply_enabled": False,
                "mutation_authorized": False,
            },
        }
    safety = dict(response.get("safety_metadata", {}) or {})
    safety["api_readback_only"] = True
    safety["pipeline_generated_overlay_readback"] = True
    response["safety_metadata"] = safety
    return {
        **response,
        "api_surface": "pipeline_generated_agent_recommendation_overlay_readback",
        "api_readback_only": True,
        "ui_action_added": False,
    }


@app.post(
    "/api/pipeline-generated-agent-recommendation-overlay-readiness-summary"
)
def pipeline_generated_agent_recommendation_overlay_readiness_summary(
    request: PipelineGeneratedAgentRecommendationOverlayReadinessSummaryRequest,
):
    try:
        response = (
            services.pipeline_generated_agent_recommendation_overlay_readiness_summary_service_payload(
                overlay_readback_payload=request.overlay_readback_payload,
                hook_payload=request.hook_payload,
                trace_capture_payload=request.trace_capture_payload,
                trace_persistence_payload=request.trace_persistence_payload,
                trace_readback_payload=request.trace_readback_payload,
                readback_source=request.readback_source,
            )
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        response = {
            "schema_version": "phase5_shadow_sidecar_trace_v1",
            "readiness_status": "overlay_failed_non_blocking",
            "reviewable": False,
            "partial": False,
            "source_readback_status": "",
            "auto_generation_status": "",
            "overlay_status": "",
            "recommended_review_action": "",
            "reason_codes": [
                "overlay_readiness_summary_failed_non_blocking"
            ],
            "blocking_findings": [],
            "warning_findings": ["retry_read_only_overlay_readiness_summary"],
            "operator_summary": {
                "summary_type": (
                    "pipeline_generated_agent_recommendation_overlay_readiness"
                ),
                "readiness_status": "overlay_failed_non_blocking",
                "reviewable": False,
                "partial": False,
                "recommended_review_action": "",
                "human_review_required": True,
                "advisory_only": True,
            },
            "source_overlay_summary": {
                "overlay_found": False,
                "auto_generation_status": "",
                "overlay_status": "",
                "recommended_review_action": "",
            },
            "error_type": exc.__class__.__name__,
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "service_helper_only": True,
            "api_route_added": True,
            "ui_action_added": False,
            "read_only": True,
            "advisory_only": True,
            "safety_metadata": {
                "read_only": True,
                "readiness_summary_only": True,
                "service_helper_only": True,
                "api_readiness_summary_only": True,
                "advisory_only": True,
                "pipeline_generated_overlay_readiness_summary": True,
                "provider_calls_disabled_in_tests": True,
                "requires_live_database": False,
                "did_read_database": False,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_approval": False,
                "did_mutate_resume": False,
                "did_create_execution_request": False,
                "did_create_execution_launch_request": False,
                "did_execute_application": False,
                "did_submit_application": False,
                "pipeline_wiring_added": False,
                "ui_action_added": False,
                "auto_apply_enabled": False,
                "mutation_authorized": False,
            },
        }
    safety = dict(response.get("safety_metadata", {}) or {})
    safety["read_only"] = True
    safety["api_readiness_summary_only"] = True
    safety["advisory_only"] = True
    safety["pipeline_generated_overlay_readiness_summary"] = True
    safety["ui_action_added"] = False
    response["safety_metadata"] = safety
    return {
        **response,
        "api_surface": (
            "pipeline_generated_agent_recommendation_overlay_readiness_summary"
        ),
        "api_readiness_summary_only": True,
        "api_readonly": True,
        "read_only": True,
        "advisory_only": True,
        "ui_action_added": False,
    }


@app.post("/api/pipeline-agent-review-packet")
def pipeline_generated_overlay_review_packet(
    request: PipelineGeneratedOverlayReviewPacketRequest,
):
    try:
        response = services.pipeline_generated_overlay_review_packet_service_payload(
            overlay_readback_payload=request.overlay_readback_payload,
            overlay_payload=request.overlay_payload,
            pipeline_generated_overlay_payload=(
                request.pipeline_generated_overlay_payload
            ),
            agent_recommendation_overlay_payload=(
                request.agent_recommendation_overlay_payload
            ),
            hook_payload=request.hook_payload,
            trace_context_payload=request.trace_context_payload,
            trace_capture_payload=request.trace_capture_payload,
            trace_persistence_payload=request.trace_persistence_payload,
            trace_readback_payload=request.trace_readback_payload,
            readback_source=request.readback_source,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        response = {
            "schema_version": "phase5_shadow_sidecar_trace_v1",
            "packet_status": "review_packet_failed_non_blocking",
            "packet_type": (
                "pipeline_generated_agent_recommendation_overlay_review_packet"
            ),
            "read_only": True,
            "advisory_only": True,
            "review_packet_only": True,
            "overlay_found": False,
            "overlay_readiness_status": "overlay_failed_non_blocking",
            "overlay_reviewability": {
                "reviewable": False,
                "partial": False,
            },
            "auto_generation_status": "",
            "overlay_status": "",
            "recommended_operator_action": "retry_read_only_overlay_readback",
            "review_focus": [
                "retry_read_only_overlay_readback",
                "review_packet_failed_non_blocking",
            ],
            "evaluation_boundaries": {
                "prefilter_relevance": "upstream_deterministic_filter_preserved",
                "shadow_evaluation": "advisory_read_only",
                "final_application_scoring": "unchanged",
            },
            "trace_context_summary": {},
            "overlay_readback_summary": {},
            "overlay_readiness_summary": {
                "readiness_status": "overlay_failed_non_blocking",
                "reviewable": False,
                "partial": False,
                "reason_codes": ["review_packet_failed_non_blocking"],
                "blocking_findings": [],
                "warning_findings": ["retry_read_only_overlay_readback"],
            },
            "error_type": exc.__class__.__name__,
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "service_helper_only": True,
            "api_route_added": True,
            "ui_action_added": False,
            "safety_metadata": {
                "read_only": True,
                "service_helper_only": True,
                "api_review_packet_only": True,
                "advisory_only": True,
                "review_packet_only": True,
                "provider_calls_disabled_in_tests": True,
                "requires_live_database": False,
                "did_read_database": False,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_approval": False,
                "did_mutate_resume": False,
                "did_create_execution_request": False,
                "did_create_execution_launch_request": False,
                "did_execute_application": False,
                "did_submit_application": False,
                "pipeline_wiring_added": False,
                "ui_action_added": False,
                "auto_apply_enabled": False,
                "mutation_authorized": False,
            },
        }
    safety = dict(response.get("safety_metadata", {}) or {})
    safety["read_only"] = True
    safety["api_review_packet_only"] = True
    safety["advisory_only"] = True
    safety["review_packet_only"] = True
    safety["pipeline_" + "agent_review_packet"] = True
    safety["ui_action_added"] = False
    response["safety_metadata"] = safety
    return {
        **response,
        "api_surface": "pipeline_" + "agent_review_packet",
        "api_review_packet_only": True,
        "api_readonly": True,
        "read_only": True,
        "advisory_only": True,
        "ui_action_added": False,
    }


@app.post("/api/vector-evidence")
def vector_evidence(request: VectorEvidenceRequest):
    response = services.vector_evidence_service_helper_payload(
        query_text=request.query_text,
        job_payload=request.job_payload,
        job_description_payload=request.job_description_payload,
        resume_profile_payload=request.resume_profile_payload,
        trace_evidence_payload=request.trace_evidence_payload,
        operator_review_packet_payload=request.operator_review_packet_payload,
        filters=request.filters,
        chunk_type=request.chunk_type,
        job_id=request.job_id,
        company=request.company,
        agent_name=request.agent_name,
        stage=request.stage,
        top_k=request.top_k,
    )
    safety = dict(response.get("safety_metadata", {}) or {})
    safety.update(
        {
            "read_only": True,
            "advisory_only": True,
            "vector_evidence_api": True,
            "vector_evidence_service_helper": True,
            "embeddings_created": False,
            "vector_db_connected": False,
            "provider_calls_made": False,
            "did_read_database": False,
            "did_write_database": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_create_approval": False,
            "did_mutate_approval": False,
            "did_mutate_resume": False,
            "did_create_execution_request": False,
            "did_create_execution_launch_request": False,
            "did_execute_application": False,
            "did_submit_application": False,
            "api_route_added": True,
            "ui_action_added": False,
            "pipeline_stage_added": False,
            "auto_apply_enabled": False,
            "mutation_authorized": False,
        }
    )
    return {
        **response,
        "api_surface": "vector_evidence",
        "vector_evidence_api": True,
        "vector_evidence_service_helper": True,
        "api_route_added": True,
        "read_only": True,
        "advisory_only": True,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "safety_metadata": safety,
    }


@app.post("/api/pgvector-extension-probe")
def pgvector_extension_probe(request: PgvectorExtensionProbeRequest):
    response = services.pgvector_extension_probe_service_helper_payload(
        extension_name=request.extension_name,
        requested_dimension=request.requested_dimension,
        probe_context=request.probe_context,
    )
    safety = dict(response.get("safety_metadata", {}) or {})
    safety.update(
        {
            "read_only": True,
            "advisory_only": True,
            "pgvector_extension_probe": True,
            "pgvector_probe_service_helper": True,
            "pgvector_probe_api": True,
            "pgvector_installed_by_app": False,
            "schema_created": False,
            "migration_created": False,
            "embeddings_created": False,
            "provider_calls_made": False,
            "did_write_database": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_create_approval": False,
            "did_mutate_approval": False,
            "did_mutate_resume": False,
            "did_create_execution_request": False,
            "did_create_execution_launch_request": False,
            "did_execute_application": False,
            "did_submit_application": False,
            "api_route_added": True,
            "ui_action_added": False,
            "pipeline_stage_added": False,
            "auto_apply_enabled": False,
            "mutation_authorized": False,
        }
    )
    safety.setdefault("vector_db_connected", False)
    safety.setdefault("did_read_database", False)
    return {
        **response,
        "api_surface": "pgvector_extension_probe",
        "pgvector_probe_api": True,
        "api_route_added": True,
        "read_only": True,
        "advisory_only": True,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "safety_metadata": safety,
    }


@app.post("/api/vector-evidence-readback")
def vector_evidence_readback(request: VectorEvidenceReadbackRequest):
    response = services.vector_evidence_readback_service_helper_payload(
        enabled=request.enabled,
        owner_user_id=request.owner_user_id,
        smoke_identifier=request.smoke_identifier,
        connection_provider_enabled=request.connection_provider_enabled,
    )
    safety = dict(response.get("safety_metadata", {}) or {})
    safety.update(
        {
            "read_only": True,
            "advisory_only": True,
            "vector_evidence_readback_api": True,
            "vector_evidence_readback_service_helper": True,
            "operator_triggered_only": True,
            "api_route_added": True,
            "ui_action_added": False,
            "pipeline_stage_added": False,
            "embeddings_created": False,
            "provider_calls_made": False,
            "did_write_database": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_create_approval": False,
            "did_mutate_approval": False,
            "did_mutate_resume": False,
            "did_create_execution_request": False,
            "did_create_execution_launch_request": False,
            "did_execute_application": False,
            "did_submit_application": False,
            "auto_apply_enabled": False,
            "mutation_authorized": False,
        }
    )
    safety.setdefault("did_read_database", False)
    return {
        **response,
        "api_surface": "vector_evidence_readback",
        "vector_evidence_readback_api": True,
        "api_route_added": True,
        "read_only": True,
        "advisory_only": True,
        "operator_triggered_only": True,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "safety_metadata": safety,
    }


@app.post("/api/three-agent-llmops-observability-readback")
def three_agent_llmops_observability_readback(
    request: ThreeAgentLlmopsObservabilityReadbackRequest,
):
    response = (
        services.three_agent_llmops_observability_readback_service_payload(
            enabled=request.enabled,
            payload=request.payload,
            chain_payload=request.chain_payload,
            review_packet_payload=request.review_packet_payload,
        )
    )
    safety = dict(response.get("safety_metadata", {}) or {})
    safety.update(
        {
            "read_only": True,
            "advisory_only": True,
            "readback_only": True,
            "llmops_observability_readback_api": True,
            "llmops_observability_service_bridge": True,
            "provider_calls_made": False,
            "embeddings_created": False,
            "did_read_database": False,
            "did_write_database": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_create_approval": False,
            "did_mutate_approval": False,
            "did_mutate_resume": False,
            "did_create_execution_request": False,
            "did_create_execution_launch_request": False,
            "did_execute_application": False,
            "did_submit_application": False,
            "api_route_added": True,
            "ui_action_added": False,
            "pipeline_stage_added": False,
            "mutation_authorized": False,
        }
    )
    return {
        **response,
        "api_surface": "three_agent_llmops_observability_readback",
        "api_readback_only": True,
        "api_route_added": True,
        "read_only": True,
        "advisory_only": True,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "safety_metadata": safety,
    }


@app.post("/api/three-core-shadow-operator-canary-readback")
def three_core_shadow_operator_canary_readback(
    request: ThreeCoreShadowOperatorCanaryReadbackRequest,
):
    response = (
        services.build_three_core_shadow_operator_canary_readback_service_payload(
            enabled=request.enabled,
            shadow_sidecar_hook_payload=request.shadow_sidecar_hook_payload,
            canary_context=request.canary_context,
        )
    )
    safety = dict(response.get("safety_metadata", {}) or {})
    safety.update(
        {
            "read_only": True,
            "shadow_only": True,
            "advisory_only": True,
            "readback_only": True,
            "three_core_shadow_operator_canary_readback_api": True,
            "provider_calls_made": False,
            "provider_sdk_imported": False,
            "environment_secrets_read": False,
            "network_calls_made": False,
            "did_read_database": False,
            "did_write_database": False,
            "did_read_files": False,
            "did_write_files": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_create_approval": False,
            "did_mutate_approval": False,
            "did_mutate_resume": False,
            "did_create_execution_request": False,
            "did_create_execution_launch_request": False,
            "did_execute_application": False,
            "did_submit_application": False,
            "api_route_added": True,
            "ui_action_added": False,
            "pipeline_stage_added": False,
            "mutation_authorized": False,
        }
    )
    return {
        **response,
        "api_surface": "three_core_shadow_operator_canary_readback",
        "api_readonly": True,
        "api_readback_only": True,
        "api_route_added": True,
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "safety_metadata": safety,
    }


@app.post("/api/three-core-approval-preview-service-readback")
def three_core_approval_preview_service_readback_api(
    payload: dict | None = Body(default=None),
):
    request_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    return (
        three_core_approval_preview_service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=request_payload.get("enabled", False),
            approval_preview_runtime_payload=request_payload.get(
                "approval_preview_runtime_payload"
            ),
            shadow_runtime_readback_payload=request_payload.get(
                "shadow_runtime_readback_payload"
            ),
            shadow_sidecar_hook_payload=request_payload.get(
                "shadow_sidecar_hook_payload"
            ),
            readback_context=request_payload.get("readback_context"),
            readback_config=request_payload.get("readback_config"),
        )
    )


@app.post("/api/operator-decision-capture-readback")
def operator_decision_capture_readback_api(
    payload: dict | None = Body(default=None),
):
    request_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    return (
        operator_decision_capture_readback_contract
        .build_operator_decision_capture_readback_payload(
            enabled=request_payload.get("enabled", False),
            selected_action=request_payload.get("selected_action", ""),
            selected_resume=request_payload.get("selected_resume", ""),
            selected_variant=request_payload.get("selected_variant", ""),
            operator_note=request_payload.get("operator_note", ""),
            config=request_payload.get("config"),
        )
    )


@app.post("/api/provider-call-readiness-readback")
def provider_call_readiness_readback_api(
    payload: dict | None = Body(default=None),
):
    request_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    return (
        provider_call_readiness_experiment
        .build_provider_call_readiness_experiment_payload(
            enabled=request_payload.get("enabled", False),
            requested_provider_capability=request_payload.get(
                "requested_provider_capability",
                "",
            ),
            provider_name=request_payload.get("provider_name", ""),
            requested_model=request_payload.get("requested_model", ""),
            request_packet_summary=request_payload.get(
                "request_packet_summary"
            ),
            config=request_payload.get("config"),
        )
    )


@app.post("/api/manual-review-readiness-readback")
def manual_review_readiness_readback_api(
    payload: dict | None = Body(default=None),
):
    request_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    return manual_review_readiness_contract.build_manual_review_readiness_payload(
        enabled=request_payload.get("enabled", False),
        review_inputs_summary=request_payload.get("review_inputs_summary"),
    )


@app.post("/api/core-agent-evidence-materialization-preview")
def core_agent_evidence_materialization_preview_api(
    payload: dict | None = Body(default=None),
):
    request_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    return build_core_agent_evidence_materialization_preview(
        enabled=request_payload.get("enabled", False),
        relevance_prefilter_result=request_payload.get(
            "relevance_prefilter_result"
        ),
        jd_intelligence_signals=request_payload.get(
            "jd_intelligence_signals"
        ),
        final_application_scoring_result=request_payload.get(
            "final_application_scoring_result"
        ),
        tailoring_opportunity_signals=request_payload.get(
            "tailoring_opportunity_signals"
        ),
        manual_review_context=request_payload.get(
            "manual_review_context"
        ),
    )


@app.post("/api/provider-runtime-readback")
def provider_runtime_readback(request: ProviderRuntimeReadbackRequest):
    response = services.provider_runtime_readiness_service_payload(
        enabled=request.enabled,
        config=request.config,
        provider_calls_allowed=request.provider_calls_allowed,
        shadow_payload=request.shadow_payload,
    )
    adapter_bridge_metadata = dict(
        response.get("adapter_bridge_summary", {}) or {}
    )
    provider_runtime_readiness = {
        key: response.get(key)
        for key in (
            "provider_runtime_readiness_enabled",
            "readiness_status",
            "provider_runtime_configured",
            "provider_name",
            "model_name",
            "provider_calls_allowed",
            "provider_runtime_default_off",
            "shadow_only",
            "configured_agent_names",
            "provider_backed_agent_count",
            "missing_configuration_keys",
            "next_safe_step",
            "mutation_authorized",
            "mutation_authorized_agent_count",
        )
    }
    safety = dict(response.get("safety_metadata", {}) or {})
    safety.update(
        {
            "read_only": True,
            "advisory_only": True,
            "shadow_only": True,
            "readback_only": True,
            "provider_runtime_readback_api": True,
            "provider_runtime_service_bridge": True,
            "provider_calls_made": False,
            "embeddings_created": False,
            "did_read_database": False,
            "did_write_database": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_create_approval": False,
            "did_mutate_approval": False,
            "did_mutate_resume": False,
            "did_create_execution_request": False,
            "did_create_execution_launch_request": False,
            "did_execute_application": False,
            "did_submit_application": False,
            "api_route_added": True,
            "ui_action_added": False,
            "pipeline_stage_added": False,
            "mutation_authorized": False,
        }
    )
    return {
        **response,
        "api_surface": "provider_runtime_readback",
        "provider_runtime_readback_enabled": request.enabled is True,
        "readback_status": str(
            response.get("readiness_status") or "skipped_default_off"
        ),
        "provider_runtime_readiness": provider_runtime_readiness,
        "adapter_bridge_metadata": adapter_bridge_metadata,
        "api_readback_only": True,
        "api_route_added": True,
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "safety_metadata": safety,
    }


@app.post("/api/jd-provider-runtime-readback")
def jd_provider_runtime_readback(
    request: JdProviderRuntimeReadbackRequest,
):
    response = services.jd_provider_runtime_readback_service_payload(
        enabled=request.enabled,
        payload=request.payload,
        review_packet_payload=request.review_packet_payload,
    )
    safety = dict(response.get("safety_metadata", {}) or {})
    safety.update(
        {
            "read_only": True,
            "advisory_only": True,
            "readback_only": True,
            "shadow_only": True,
            "jd_provider_runtime_readback_api": True,
            "jd_provider_runtime_service_bridge": True,
            "provider_calls_made": False,
            "network_calls_made": False,
            "embeddings_created": False,
            "did_read_database": False,
            "did_write_database": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_create_approval": False,
            "did_mutate_approval": False,
            "did_mutate_resume": False,
            "did_create_execution_request": False,
            "did_create_execution_launch_request": False,
            "did_execute_application": False,
            "did_submit_application": False,
            "api_route_added": True,
            "ui_action_added": False,
            "pipeline_stage_added": False,
            "mutation_authorized": False,
        }
    )
    return {
        **response,
        "api_surface": "jd_provider_runtime_readback",
        "api_readback_only": True,
        "api_route_added": True,
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "safety_metadata": safety,
    }


@app.post("/api/jd-live-provider-canary-readback")
def jd_live_provider_canary_readback(
    request: JdLiveProviderCanaryReadbackRequest,
):
    response = services.jd_live_provider_canary_readback_service_payload(
        enabled=request.enabled,
        payload=request.payload,
        review_packet_payload=request.review_packet_payload,
    )
    safety = dict(response.get("safety_metadata", {}) or {})
    safety.update(
        {
            "read_only": True,
            "advisory_only": True,
            "readback_only": True,
            "shadow_only": True,
            "jd_live_provider_canary_readback_api": True,
            "jd_live_provider_canary_service_bridge": True,
            "provider_calls_made": False,
            "network_calls_made": False,
            "environment_secrets_read": False,
            "embeddings_created": False,
            "did_read_database": False,
            "did_write_database": False,
            "did_write_files": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_create_approval": False,
            "did_mutate_approval": False,
            "did_mutate_resume": False,
            "did_create_execution_request": False,
            "did_create_execution_launch_request": False,
            "did_execute_application": False,
            "did_submit_application": False,
            "api_route_added": True,
            "ui_action_added": False,
            "pipeline_stage_added": False,
            "mutation_authorized": False,
        }
    )
    influence_disabled = dict(
        response.get("influence_disabled", {}) or {}
    )
    influence_disabled.update(
        {
            "scoring": True,
            "ranking": True,
            "queue": True,
            "resume": True,
            "execution": True,
            "submission": True,
        }
    )
    return {
        **response,
        "api_surface": "jd_live_provider_canary_readback",
        "api_readback_only": True,
        "api_route_added": True,
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "influence_disabled": influence_disabled,
        "safety_metadata": safety,
    }


@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")
def profile_pipeline_run_agentic_review_data(run_id: str, http_request: Request):
    try:
        return services.profile_pipeline_run_agentic_review_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
            run_id=run_id,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/profile/pipeline-runs/{run_id}/rerun")
def profile_pipeline_run_rerun(run_id: str, http_request: Request):
    try:
        return services.profile_pipeline_rerun_payload(
            owner_user_id=_auth_owner_user_id(http_request),
            run_id=run_id,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/profile/saved-scans/data")
def profile_saved_scans(http_request: Request, limit: int = 25):
    return services.profile_saved_scans_payload(
        limit=limit,
        owner_user_id=_auth_owner_user_id(http_request),
    )



@app.post("/profile/resumes/upload")
def profile_upload_resume(
    http_request: Request,
    filename: str = Query(..., min_length=1),
    file_bytes: bytes = Body(...),
):
    try:
        return services.profile_upload_resume_payload(
            filename=filename,
            file_bytes=file_bytes,
            owner_user_id=_auth_owner_user_id(http_request),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/profile/resumes/{resume_name}")
def profile_delete_resume(resume_name: str, http_request: Request):
    try:
        return services.profile_delete_resume_payload(
            resume_name,
            owner_user_id=_auth_owner_user_id(http_request),
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

# Explicit read-only Critic/Evaluator response contract keys.
# These literals keep the API contract observable without adding side effects.
_CRITIC_EVALUATOR_READONLY_RESPONSE_KEYS = (
    "evaluator_status",
    "evaluator_findings",
    "evaluator_warnings",
    "evaluator_recommendations",
    "requires_human_review",
    "deterministic_rubric_version",
)
