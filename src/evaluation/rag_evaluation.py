from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


RAG_EVALUATION_VERSION = "rag_evaluation_v1"
RAG_EVALUATION_SUMMARY_ARTIFACT = "rag_evaluation_summary.json"
RAG_EVALUATION_REPORT_ARTIFACT = "rag_evaluation_report.md"
RAG_EVALUATION_EMPTY_STATE_REASON = "no_rag_evaluation_data"
RAG_EVALUATION_INVALID_SCORE_REASON = "invalid_retrieval_score"
RAG_EVALUATION_INVALID_RANK_REASON = "invalid_rank"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = _clean_text(value).lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return None


def _reason_codes(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    return [
        item.strip()
        for item in _clean_text(value).split(";")
        if item.strip()
    ]


def _first_value(row: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return ""


def _preview_text(value: Any, max_chars: int = 180) -> str:
    text = _clean_text(value).replace("\n", " ")
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def build_rag_evaluation_rows(
    records: Iterable[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for index, record in enumerate(list(records or []), start=1):
        if not isinstance(record, dict):
            continue
        query_id = _clean_text(_first_value(record, ["query_id", "question_id"])) or f"query_{index}"
        score = _safe_float(_first_value(record, ["retrieval_score", "score", "similarity_score"]))
        expected_relevant = _safe_bool(_first_value(record, ["expected_relevant", "is_expected_relevant"]))
        supported_decision = _clean_text(
            _first_value(record, ["supported_decision", "decision", "answer_support"])
        )
        missing_warning = _safe_bool(
            _first_value(record, ["missing_evidence_warning", "insufficient_evidence"])
        )
        if missing_warning is None:
            missing_warning = supported_decision.lower() in {"unsupported", "insufficient_evidence"}

        rows.append(
            {
                "query_id": query_id,
                "query_text": _clean_text(_first_value(record, ["query_text", "question", "query"])),
                "target_type": _clean_text(_first_value(record, ["target_type", "entity_type"])),
                "target_id": _clean_text(_first_value(record, ["target_id", "doc_id", "job_id"])),
                "retrieved_doc_id": _clean_text(_first_value(record, ["retrieved_doc_id", "doc_id", "job_id"])),
                "retrieved_chunk_id": _clean_text(
                    _first_value(record, ["retrieved_chunk_id", "chunk_id", "node_id"])
                ),
                "retrieved_text_preview": _preview_text(
                    _first_value(record, ["retrieved_text_preview", "retrieval_text", "text", "preview"])
                ),
                "retrieval_score": score,
                "rank": _safe_int(_first_value(record, ["rank", "position"])),
                "source": _clean_text(_first_value(record, ["source", "retrieval_lane"])),
                "latency_ms": _safe_float(_first_value(record, ["latency_ms", "retrieval_latency_ms"])),
                "supported_decision": supported_decision,
                "expected_relevant": expected_relevant,
                "relevance_hit": bool(expected_relevant and _safe_int(_first_value(record, ["rank", "position"])) > 0),
                "missing_evidence_warning": bool(missing_warning),
                "reason_codes": _reason_codes(record.get("reason_codes", [])),
            }
        )
    return rows


def build_rag_evaluation_summary(
    rows: Iterable[Dict[str, Any]] | None = None,
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
) -> Dict[str, Any]:
    normalized_rows = build_rag_evaluation_rows(rows)
    query_ids = {_clean_text(row.get("query_id")) for row in normalized_rows if _clean_text(row.get("query_id"))}
    scores = [
        float(row["retrieval_score"])
        for row in normalized_rows
        if isinstance(row.get("retrieval_score"), (int, float))
    ]
    latency_values = [
        float(row["latency_ms"])
        for row in normalized_rows
        if isinstance(row.get("latency_ms"), (int, float))
    ]
    labeled_rows = [row for row in normalized_rows if row.get("expected_relevant") is not None]
    hit_count = sum(1 for row in labeled_rows if bool(row.get("relevance_hit")))
    missing_warnings = sum(1 for row in normalized_rows if bool(row.get("missing_evidence_warning")))
    unsupported_preventions = sum(
        1
        for row in normalized_rows
        if _clean_text(row.get("supported_decision")).lower()
        in {"unsupported", "insufficient_evidence", "prevented"}
    )
    validation = validate_rag_evaluation_payload(
        {
            "evaluation_version": RAG_EVALUATION_VERSION,
            "pipeline_run_id": _clean_text(pipeline_run_id),
            "owner_user_id": _clean_text(owner_user_id),
            "rows": normalized_rows,
        }
    )

    return {
        "evaluation_version": RAG_EVALUATION_VERSION,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "query_count": len(query_ids),
        "retrieved_chunk_count": len(normalized_rows),
        "average_retrieval_score": round(sum(scores) / len(scores), 6) if scores else None,
        "top_k_hit_rate": round(hit_count / len(labeled_rows), 6) if labeled_rows else None,
        "average_latency_ms": round(sum(latency_values) / len(latency_values), 3) if latency_values else None,
        "missing_evidence_warning_count": missing_warnings,
        "unsupported_claim_prevention_count": unsupported_preventions,
        "validation_status": validation["validation_status"],
        "reason_codes": validation["reason_codes"],
        "rows": normalized_rows,
    }


def validate_rag_evaluation_payload(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    data = payload if isinstance(payload, dict) else {}
    reason_codes: List[str] = []

    evaluation_version = _clean_text(data.get("evaluation_version"))
    if not evaluation_version:
        reason_codes.append("missing_evaluation_version")
    elif evaluation_version != RAG_EVALUATION_VERSION:
        reason_codes.append("unknown_evaluation_version")

    rows_value = data.get("rows")
    rows = rows_value if isinstance(rows_value, list) else []
    if not isinstance(rows_value, list):
        reason_codes.append("invalid_rows")

    validation_status = _clean_text(data.get("validation_status"))
    if validation_status and validation_status not in {"passed", "warning"}:
        reason_codes.append("invalid_validation_status")

    if not rows:
        reason_codes.append(RAG_EVALUATION_EMPTY_STATE_REASON)

    for row in rows:
        if not isinstance(row, dict):
            reason_codes.append("invalid_row")
            continue
        score = row.get("retrieval_score")
        if score is not None and (
            not isinstance(score, (int, float)) or float(score) < 0.0 or float(score) > 1.0
        ):
            reason_codes.append(RAG_EVALUATION_INVALID_SCORE_REASON)
        rank = row.get("rank")
        if rank is not None and (not isinstance(rank, int) or int(rank) < 0):
            reason_codes.append(RAG_EVALUATION_INVALID_RANK_REASON)

    unique_reasons = sorted(set(reason_codes))
    invalid_reasons = {
        "unknown_evaluation_version",
        "missing_evaluation_version",
        "invalid_row",
        "invalid_rows",
        "invalid_validation_status",
        RAG_EVALUATION_INVALID_SCORE_REASON,
        RAG_EVALUATION_INVALID_RANK_REASON,
    }
    if any(reason in invalid_reasons for reason in unique_reasons):
        status = "failed"
    elif unique_reasons:
        status = "warning"
    else:
        status = "passed"
    return {
        "validation_status": status,
        "reason_codes": unique_reasons,
    }


def render_rag_evaluation_report_markdown(payload: Dict[str, Any] | None = None) -> str:
    data = payload if isinstance(payload, dict) else {}
    lines = [
        "# RAG Evaluation Report",
        "",
        f"Evaluation version: `{_clean_text(data.get('evaluation_version')) or RAG_EVALUATION_VERSION}`",
        f"Pipeline run id: `{_clean_text(data.get('pipeline_run_id')) or 'none'}`",
        f"Query count: `{_safe_int(data.get('query_count'))}`",
        f"Retrieved chunks: `{_safe_int(data.get('retrieved_chunk_count'))}`",
        f"Average retrieval score: `{data.get('average_retrieval_score') if data.get('average_retrieval_score') is not None else 'n/a'}`",
        f"Top-k hit rate: `{data.get('top_k_hit_rate') if data.get('top_k_hit_rate') is not None else 'n/a'}`",
        f"Missing evidence warnings: `{_safe_int(data.get('missing_evidence_warning_count'))}`",
        f"Validation status: `{_clean_text(data.get('validation_status')) or 'warning'}`",
        "",
        "## Reason Codes",
        "",
    ]
    reason_codes = data.get("reason_codes") if isinstance(data.get("reason_codes"), list) else []
    lines.append(", ".join(f"`{_clean_text(item)}`" for item in reason_codes if _clean_text(item)) or "None")
    return "\n".join(lines).strip() + "\n"


def write_rag_evaluation_artifacts(
    *,
    output_dir: str | Path,
    rows: Iterable[Dict[str, Any]] | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
) -> Dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    payload = build_rag_evaluation_summary(
        rows,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
    )
    summary_path = root / RAG_EVALUATION_SUMMARY_ARTIFACT
    report_path = root / RAG_EVALUATION_REPORT_ARTIFACT
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(render_rag_evaluation_report_markdown(payload), encoding="utf-8")
    return {
        "summary_json": str(summary_path),
        "report_md": str(report_path),
    }
