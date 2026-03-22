from pathlib import Path
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from src.app import services
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
    decisions_path: str = str(services.DEFAULT_DECISIONS_PATH),
    top_k: int = 10,
):
    return services.status_payload(
        output_dir=Path(output_dir),
        job_corpus=Path(job_corpus),
        decisions_path=Path(decisions_path),
        top_k=top_k,
    )

@app.get("/pipeline/status")
def pipeline_status():
    return services.pipeline_status_payload()


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
    decisions_path: str = str(services.DEFAULT_DECISIONS_PATH),
    action: str = "",
    needs_review: str = "",
    is_tie: str = "",
    fallback_status: str = "",
    winner_bucket: str = "",
    company_contains: str = "",
    title_contains: str = "",
    undecided_only: str = "",
    limit: int = 20,
):
    return services.browse_payload(
        output_dir=Path(output_dir),
        decisions_path=Path(decisions_path),
        action=action,
        needs_review=needs_review,
        is_tie=is_tie,
        fallback_status=fallback_status,
        winner_bucket=winner_bucket,
        company_contains=company_contains,
        title_contains=title_contains,
        undecided_only=undecided_only,
        limit=limit,
    )


@app.get("/review")
def review(
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    decisions_path: str = str(services.DEFAULT_DECISIONS_PATH),
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
        decisions_path=Path(decisions_path),
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
        pattern="^(undecided_apply_review|undecided_maybe_tailor|decided_apply|decided_tailor|runner_up_selected|direct_apply_pending)$",
    ),
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    decisions_path: str = str(services.DEFAULT_DECISIONS_PATH),
    limit: int = 20,
):
    return services.workflow_payload(
        view=view,
        limit=limit,
        output_dir=Path(output_dir),
        decisions_path=Path(decisions_path),
    )


@app.get("/planner")
def planner(
    request: str,
    output_dir: str = str(services.DEFAULT_OUTPUT_DIR),
    decisions_path: str = str(services.DEFAULT_DECISIONS_PATH),
    limit: int = 20,
):
    try:
        return services.planner_payload(
            request=request,
            limit=limit,
            output_dir=Path(output_dir),
            decisions_path=Path(decisions_path),
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
    decisions_path: str = str(services.DEFAULT_DECISIONS_PATH),
    queue_rank: int | None = None,
    decision: str = "",
    selected_resume: str = "",
    company_contains: str = "",
    title_contains: str = "",
    limit: int = 20,
):
    return services.decisions_payload(
        decisions_path=Path(decisions_path),
        queue_rank=queue_rank,
        decision=decision,
        selected_resume=selected_resume,
        company_contains=company_contains,
        title_contains=title_contains,
        limit=limit,
    )

@app.post("/planning/select-resume")
def planning_select_resume(
    payload: dict = Body(...),
    decisions_path: str = str(services.DEFAULT_DECISIONS_PATH),
):
    try:
        return services.record_operator_resume_selection_payload(
            decisions_path=Path(decisions_path),
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
    
@app.get("/application-actions")
def application_actions(
    actions_path: str = str(services.DEFAULT_APPLICATION_ACTIONS_PATH),
    application_status: str = "",
    company_contains: str = "",
    title_contains: str = "",
    limit: int = 100,
):
    return services.application_actions_payload(
        actions_path=Path(actions_path),
        application_status=application_status,
        company_contains=company_contains,
        title_contains=title_contains,
        limit=limit,
    )


@app.post("/application-actions")
def record_application_action(
    payload: dict = Body(...),
    actions_path: str = str(services.DEFAULT_APPLICATION_ACTIONS_PATH),
):
    try:
        return services.record_application_action_payload(
            actions_path=Path(actions_path),
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
    actions_path: str = str(services.DEFAULT_APPLICATION_ACTIONS_PATH),
    company_contains: str = "",
    title_contains: str = "",
    limit: int = 100,
):
    return services.applied_jobs_payload(
        actions_path=Path(actions_path),
        company_contains=company_contains,
        title_contains=title_contains,
        limit=limit,
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