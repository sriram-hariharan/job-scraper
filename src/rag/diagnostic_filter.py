from typing import Any, Dict, Iterable, List


DIAGNOSTIC_RAG_MARKERS = (
    "rag corpus smoke",
)


def _diagnostic_text(row: Dict[str, Any]) -> str:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    values = [
        row.get("title", ""),
        row.get("company", ""),
        row.get("doc_id", ""),
        row.get("source", ""),
        metadata.get("title", ""),
        metadata.get("company", ""),
        metadata.get("doc_id", ""),
        metadata.get("source", ""),
    ]
    return " ".join(str(value or "").strip().lower() for value in values)


def is_diagnostic_rag_row(row: Dict[str, Any]) -> bool:
    text = _diagnostic_text(row or {})
    return any(marker in text for marker in DIAGNOSTIC_RAG_MARKERS)


def filter_diagnostic_rag_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        row
        for row in rows
        if not is_diagnostic_rag_row(row)
    ]
