from pathlib import Path
import base64
import binascii
from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from src.app import services
from src.auth.runtime import auth_guard_response
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
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
):
    try:
        return services.agent_trace_payload(
            owner_user_id=_require_auth_owner_user_id(http_request),
            pipeline_run_id=run_id,
            context_id=context_id,
            agent_run_id=agent_run_id,
        )
    except (SystemExit, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
