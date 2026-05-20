import json
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from src.rag.job_document_builder import build_job_document
from src.storage.rag_store import count_rag_job_documents, upsert_rag_job_documents


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _build_rag_document_with_raw_identity(job: Dict[str, Any]) -> Dict[str, Any]:
    doc = build_job_document(job)

    for key in [
        "job_doc_id",
        "job_id",
        "url",
        "link",
    ]:
        value = _clean_text(job.get(key))
        if value:
            doc[key] = value

    return doc


def _is_filesystem_output_path(output_path: str) -> bool:
    raw = _clean_text(output_path)
    if not raw:
        return False

    parsed = urlparse(raw)
    if parsed.scheme and parsed.scheme not in {"", "file"}:
        return False

    return True


def _write_jsonl_documents(
    docs: List[Dict[str, Any]],
    output_path: str,
    *,
    merge_existing: bool,
) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    seen_doc_ids = set()

    if merge_existing and path.exists():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):
                    continue
                doc_id = _clean_text(row.get("doc_id") or row.get("job_doc_id") or row.get("job_id"))
                if doc_id and doc_id in seen_doc_ids:
                    continue
                if doc_id:
                    seen_doc_ids.add(doc_id)
                rows.append(row)

    for doc in docs:
        doc_id = _clean_text(doc.get("doc_id") or doc.get("job_doc_id") or doc.get("job_id"))
        if doc_id and doc_id in seen_doc_ids:
            rows = [
                row
                for row in rows
                if _clean_text(row.get("doc_id") or row.get("job_doc_id") or row.get("job_id")) != doc_id
            ]
        if doc_id:
            seen_doc_ids.add(doc_id)
        rows.append(doc)

    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")

    return len(docs) if not merge_existing else len(rows)


def export_job_corpus(
    jobs: List[Dict[str, Any]],
    output_path: str,
    *,
    merge_existing: bool = True,
) -> int:
    docs = [_build_rag_document_with_raw_identity(job) for job in jobs]
    upsert_rag_job_documents(docs)

    if _is_filesystem_output_path(output_path):
        return _write_jsonl_documents(
            docs,
            output_path,
            merge_existing=bool(merge_existing),
        )

    return count_rag_job_documents()
