from typing import Any, Dict, List

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


def export_job_corpus(
    jobs: List[Dict[str, Any]],
    output_path: str,
    *,
    merge_existing: bool = True,
) -> int:
    docs = [_build_rag_document_with_raw_identity(job) for job in jobs]
    upsert_rag_job_documents(docs)
    return count_rag_job_documents()
