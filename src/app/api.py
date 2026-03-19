from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from src.app import services
from fastapi.staticfiles import StaticFiles
from src.app.ui import router as ui_router

app = FastAPI(
    title="Job Operator API",
    version="0.1.0",
    description="Thin API shell over deterministic operator workflows and local job RAG.",
)
app.mount("/static", StaticFiles(directory="src/app/static"), name="static")
app.include_router(ui_router)

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