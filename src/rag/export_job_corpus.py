from typing import Any, Dict, List

from src.rag.job_document_builder import build_job_document
from src.storage.rag_store import count_rag_job_documents, upsert_rag_job_documents


def export_job_corpus(
    jobs: List[Dict[str, Any]],
    output_path: str,
    *,
    merge_existing: bool = True,
) -> int:
    docs = [build_job_document(job) for job in jobs]
    upsert_rag_job_documents(docs)
    return count_rag_job_documents()
