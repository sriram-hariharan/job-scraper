from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

DEFAULT_OUTPUT_DIR = Path("outputs/application_planning")
DEFAULT_CORPUS_PATH = Path("data/rag/job_corpus.jsonl")
DEFAULT_DECISIONS_PATH = DEFAULT_OUTPUT_DIR / "operator_decisions.csv"

def _job_app():
    import job_app
    return job_app

def _make_args(**kwargs):
    return SimpleNamespace(**kwargs)


def health_payload() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": "job-operator-api",
    }


def status_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    job_corpus: Path = DEFAULT_CORPUS_PATH,
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
    top_k: int = 10,
) -> Dict[str, Any]:
    ja = _job_app()
    best_rows = ja._load_csv_rows(output_dir / "best_resume_variant_by_job.csv")
    shortlist_rows = ja._load_csv_rows(output_dir / "application_shortlist_by_job.csv")
    queue_rows = ja._load_csv_rows(output_dir / "application_execution_queue.csv")
    manifest_rows = ja._load_csv_rows(output_dir / "job_packet_manifest.csv")
    decision_rows = ja._load_csv_rows(decisions_path)

    merged_rows = ja._build_job_index(output_dir, decisions_path)
    undecided_review_counts = ja._count_undecided_review_rows(merged_rows)

    winner_bucket_counts = Counter(
        str(row.get("winner_bucket", "") or "<empty>")
        for row in best_rows
    )
    fallback_status_counts = Counter(
        str(row.get("llm_fallback_status", "") or "<empty>")
        for row in best_rows
    )
    action_counts = Counter(
        str(row.get("action", "") or "<empty>")
        for row in queue_rows
    )
    llm_tailoring_counts = Counter(
        str(row.get("llm_tailoring_status", "") or "<empty>")
        for row in manifest_rows
    )
    decision_counts = Counter(
        str(row.get("decision", "") or "<empty>")
        for row in decision_rows
    )

    latest_by_key = ja._load_latest_decision_overlay(decisions_path)

    top_rows = sorted(
        queue_rows,
        key=lambda row: (
            int(str(row.get("queue_rank", "999999") or "999999")),
            -ja._parse_float(row.get("winner_score", "0")),
        ),
    )[:top_k]

    top_queue = []
    for row in top_rows:
        overlay_row = dict(row)
        for field in ja.OPERATOR_DECISION_OVERLAY_FIELDS:
            overlay_row.setdefault(field, "")

        key_candidates = [
            ja._decision_row_key(row),
            f"queue_rank::{str(row.get('queue_rank', '') or '').strip()}",
            (
                f"title::{ja._normalize_text(row.get('job_company', ''))}"
                f"||{ja._normalize_text(row.get('job_title', ''))}"
            ),
        ]

        for key in key_candidates:
            if key and key in latest_by_key:
                overlay_row.update(latest_by_key[key])
                break

        top_queue.append(overlay_row)

    return {
        "summary": {
            "job_corpus_path": str(job_corpus),
            "job_corpus_rows": ja._count_jsonl_rows(job_corpus),
            "planning_output_dir": str(output_dir),
            "best_variant_rows": len(best_rows),
            "shortlist_rows": len(shortlist_rows),
            "execution_queue_rows": len(queue_rows),
            "packet_manifest_rows": len(manifest_rows),
            "operator_decisions_file": str(decisions_path),
            "operator_decisions_rows": len(decision_rows),
        },
        "winner_bucket_counts": dict(sorted(winner_bucket_counts.items())),
        "llm_fallback_status_counts": dict(sorted(fallback_status_counts.items())),
        "queue_action_counts": dict(sorted(action_counts.items())),
        "operator_decision_counts": dict(sorted(decision_counts.items())),
        "undecided_review_counts": dict(sorted(undecided_review_counts.items())),
        "llm_tailoring_status_counts": dict(sorted(llm_tailoring_counts.items())),
        "top_queue_rows": top_queue,
    }


def browse_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
    **filters: Any,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._build_job_index(output_dir, decisions_path)
    args = _make_args(**filters)
    selected = ja._select_browse_rows(rows, args)
    return {
        "filters": filters,
        "rows": selected,
        "count": len(selected),
    }


def review_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
    **filters: Any,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._build_job_index(output_dir, decisions_path)
    args = _make_args(**filters)
    selected = ja._select_review_rows(rows, args)
    return {
        "filters": filters,
        "rows": selected,
        "count": len(selected),
    }


def workflow_payload(
    view: str,
    limit: int = 20,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._build_job_index(output_dir, decisions_path)
    selected = ja._workflow_view_rows(rows, view)[:limit]
    return {
        "view": view,
        "rows": selected,
        "count": len(selected),
    }


def planner_payload(
    request: str,
    limit: int = 20,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
) -> Dict[str, Any]:
    ja = _job_app()
    view = ja._infer_planner_view(request)
    rows = ja._build_job_index(output_dir, decisions_path)
    selected = ja._workflow_view_rows(rows, view)[:limit]
    return {
        "request": request,
        "resolved_view": view,
        "rows": selected,
        "count": len(selected),
    }


def decisions_payload(
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
    **filters: Any,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._load_csv_rows(decisions_path)
    args = _make_args(**filters)
    selected = ja._select_decision_rows(rows, args)
    return {
        "filters": filters,
        "rows": selected,
        "count": len(selected),
        "decisions_path": str(decisions_path),
    }


def rag_search_payload(
    request: str,
    top_k: int = 5,
    fetch_k: int = 15,
    output_mode: str = "compact",
    include_diagnostics: bool = False,
) -> Dict[str, Any]:
    from src.rag.rag_executor import execute_rag_request

    return execute_rag_request(
        request=request,
        top_k=top_k,
        fetch_k=fetch_k,
        filters=None,
        output_mode=output_mode,
        include_diagnostics=include_diagnostics,
        intent_override="search_jobs",
    )

def rag_answer_payload(
    request: str,
    top_k: int = 5,
    fetch_k: int = 15,
    output_mode: str = "compact",
    include_diagnostics: bool = False,
) -> Dict[str, Any]:
    from src.rag.rag_executor import execute_rag_request

    return execute_rag_request(
        request=request,
        top_k=top_k,
        fetch_k=fetch_k,
        filters=None,
        output_mode=output_mode,
        include_diagnostics=include_diagnostics,
        intent_override="answer_job_query",
    )