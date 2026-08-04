import json
import os
import tempfile
from datetime import datetime
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


def _assert_safe_existing_jsonl_path(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("JSONL cleanup target must not be a symlink.")
    current = path.parent
    while current != current.parent:
        if current.exists() and current.is_symlink():
            raise ValueError("JSONL cleanup path must not traverse a symlink.")
        current = current.parent


def prune_expired_himalayas_jsonl(
    output_path: str | Path,
    *,
    dry_run: bool = True,
    now: datetime | None = None,
) -> Dict[str, Any]:
    from src.pipeline.himalayas_retention import classify_expired_record

    path = Path(output_path)
    summary = {
        "inspected": 0,
        "retained": 0,
        "expired_pruned": 0,
        "malformed_lines": 0,
        "missing_or_invalid_expiry": 0,
        "missing_identity": 0,
        "write_performed": False,
    }
    _assert_safe_existing_jsonl_path(path)
    if not path.exists():
        return summary
    if not path.is_file():
        raise ValueError("JSONL cleanup target must be a regular file.")

    retained_lines = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line in handle:
            summary["inspected"] += 1
            raw = line.strip()
            try:
                record = json.loads(raw)
            except (json.JSONDecodeError, UnicodeError):
                summary["malformed_lines"] += 1
                summary["retained"] += 1
                retained_lines.append(line)
                continue
            if not isinstance(record, dict):
                summary["malformed_lines"] += 1
                summary["retained"] += 1
                retained_lines.append(line)
                continue

            classification = classify_expired_record(record, now=now)
            if classification["eligible"]:
                summary["expired_pruned"] += 1
                continue
            if classification["reason"] == "missing_or_invalid_expiry":
                summary["missing_or_invalid_expiry"] += 1
            elif classification["reason"] == "missing_identity":
                summary["missing_identity"] += 1
            summary["retained"] += 1
            retained_lines.append(line)

    if dry_run or not summary["expired_pruned"]:
        return summary

    temporary_path = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
        )
        temporary_path = Path(temporary_name)
        os.chmod(temporary_path, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.writelines(retained_lines)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
        summary["write_performed"] = True
        return summary
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


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
