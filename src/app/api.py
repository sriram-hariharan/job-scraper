from pathlib import Path
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from src.app import services
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
    note: str = ""

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="Job Operator API",
    version="0.1.0",
    description="Thin API shell over deterministic operator workflows and local job RAG.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="src/app/static"), name="static")
app.include_router(ui_router)
app.include_router(planning_ui_router)
app.include_router(decisions_ui_router)
app.include_router(intelligence_ui_router)
app.include_router(applied_ui_router)
app.include_router(saved_ui_router)
app.include_router(application_hub_ui_router)
app.include_router(profile_ui_router)

@app.get("/health")
def health():
    return services.health_payload()


@app.get("/status")
def status(
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    job_corpus: str = str(services.DEFAULT_CORPUS_PATH),
    top_k: int = 10,
):
    return services.status_payload(
        output_dir=Path(output_dir),
        job_corpus=Path(job_corpus),
        top_k=top_k,
    )

@app.get("/pipeline/status")
def pipeline_status():
    return services.pipeline_status_payload()

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
def run_live_pipeline(payload: dict = Body(...)):
    try:
        return services.run_live_pipeline_payload(
        output_dir=Path(str(payload.get("output_dir", services.DEFAULT_OUTPUT_DIR))),
        log_path=Path(str(payload.get("log_path", services.DEFAULT_PIPELINE_LOG_PATH))),
        job_limit=int(payload.get("job_limit", 50)),
        job_packet_limit=int(payload.get("job_packet_limit", 0)),
        llm_actions=payload.get("llm_actions", ["APPLY", "APPLY_REVIEW_VARIANTS"]),
        generate_tailoring=bool(payload.get("generate_tailoring", False)),
        generate_llm_tailoring=bool(payload.get("generate_llm_tailoring", False)),
        refresh_llm_tailoring=bool(payload.get("refresh_llm_tailoring", False)),
        generate_llm_fallback=bool(payload.get("generate_llm_fallback", False)),
        planning_only=bool(payload.get("planning_only", False)),
        delete_seen_data=str(payload.get("delete_seen_data", "no") or "no"),
    )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
@app.get("/browse")
def browse(
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    action: list[str] | None = Query(default=None),
    needs_review: str = "",
    is_tie: str = "",
    fallback_status: list[str] | None = Query(default=None),
    winner_bucket: list[str] | None = Query(default=None),
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
        company_contains=company_contains,
        title_contains=title_contains,
        undecided_only=undecided_only,
        limit=limit,
        page=page,
    )


@app.get("/review")
def review(
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
    )


@app.get("/workflow")
def workflow(
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
    )


@app.get("/planner")
def planner(
    request: str,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    limit: int = 20,
):
    try:
        return services.planner_payload(
            request=request,
            limit=limit,
            output_dir=Path(output_dir),
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

@app.get("/planning/resume-preview")
def planning_resume_preview(
    resume_name: str = Query(..., min_length=1),
):
    try:
        preview_path = services.planning_resume_preview_path(resume_name)
        return FileResponse(
            path=str(preview_path),
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="resume.pdf"'},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
@app.get("/decisions")
def decisions(
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
    )

@app.post("/planning/select-resume")
def planning_select_resume(
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
            note=request.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/application-actions")
def application_actions(
    application_status: str = "",
    company_contains: str = "",
    title_contains: str = "",
    page: int = 1,
    limit: int = 15,
):
    return services.application_actions_payload(
        application_status=application_status,
        company_contains=company_contains,
        title_contains=title_contains,
        limit=limit,
        page=page,
    )

@app.post("/application-actions")
def record_application_action(
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
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/applied-jobs")
def applied_jobs(
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
def profile_resumes():
    return services.profile_resumes_payload()


@app.post("/profile/resumes/upload")
def profile_upload_resume(
    filename: str = Query(..., min_length=1),
    file_bytes: bytes = Body(...),
):
    try:
        return services.profile_upload_resume_payload(
            filename=filename,
            file_bytes=file_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/profile/resumes/{resume_name}")
def profile_delete_resume(resume_name: str):
    try:
        return services.profile_delete_resume_payload(resume_name=resume_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    