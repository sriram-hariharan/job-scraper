import json
from pathlib import Path
from typing import List, Dict, Any

from src.rag.job_document_builder import build_job_document


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _raw_job_merge_key(job: Dict[str, Any]) -> str:
    job_doc_id = str(job.get("job_doc_id") or "").strip()
    if job_doc_id:
        return f"job_doc_id:{job_doc_id}"

    url = str(job.get("url") or "").strip()
    if url:
        return f"url:{url}"

    link = str(job.get("link") or "").strip()
    if link:
        return f"link:{link}"

    source = str(job.get("source") or "").strip()
    job_id = str(job.get("job_id") or "").strip()
    if source and job_id:
        return f"source_job_id:{source}:{job_id}"

    company = _normalize_text(job.get("company"))
    title = _normalize_text(job.get("title"))
    if company and title:
        return f"company_title:{company}||{title}"

    return ""


def _doc_merge_key(doc: Dict[str, Any]) -> str:
    job_doc_id = str(doc.get("job_doc_id") or "").strip()
    if job_doc_id:
        return f"job_doc_id:{job_doc_id}"

    url = str(doc.get("url") or "").strip()
    if url:
        return f"url:{url}"

    link = str(doc.get("link") or "").strip()
    if link:
        return f"link:{link}"

    metadata = doc.get("metadata") or {}
    if isinstance(metadata, dict):
        source = str(metadata.get("source") or "").strip()
        job_id = str(metadata.get("job_id") or "").strip()
        if source and job_id:
            return f"source_job_id:{source}:{job_id}"

        company = _normalize_text(metadata.get("company"))
        title = _normalize_text(metadata.get("title"))
        if company and title:
            return f"company_title:{company}||{title}"

    company = _normalize_text(doc.get("company"))
    title = _normalize_text(doc.get("title"))
    if company and title:
        return f"company_title:{company}||{title}"

    return ""


def _load_existing_docs(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    docs: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))
    return docs


def export_job_corpus(jobs: List[Dict[str, Any]], output_path: str) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing_docs = _load_existing_docs(path)

    merged_docs_by_key: Dict[str, Dict[str, Any]] = {}
    ordered_keys: List[str] = []
    anonymous_docs: List[Dict[str, Any]] = []

    for doc in existing_docs:
        key = _doc_merge_key(doc)
        if not key:
            anonymous_docs.append(doc)
            continue
        if key not in merged_docs_by_key:
            ordered_keys.append(key)
        merged_docs_by_key[key] = doc

    for job in jobs:
        doc = build_job_document(job)
        key = _raw_job_merge_key(job)
        if not key:
            key = _doc_merge_key(doc)

        if not key:
            anonymous_docs.append(doc)
            continue

        if key not in merged_docs_by_key:
            ordered_keys.append(key)
        merged_docs_by_key[key] = doc

    final_docs: List[Dict[str, Any]] = [merged_docs_by_key[key] for key in ordered_keys]
    final_docs.extend(anonymous_docs)

    with path.open("w", encoding="utf-8") as f:
        for doc in final_docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    return len(final_docs)