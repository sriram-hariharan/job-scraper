from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.resume.models import ResumeDocument
from src.resume.resume_loader import (
    extract_resume_texts,
    load_resumes,
    load_resumes_by_name,
)
from src.storage.profile_resumes.store import (
    get_profile_resume_blob_postgres_payload,
    get_profile_resumes_postgres_payload,
)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _truthy_env(name: str) -> bool:
    return _clean_text(os.environ.get(name)).lower() in {
        "1",
        "true",
        "yes",
        "y",
    }


def _is_user_pipeline_mode() -> bool:
    return _truthy_env("JOB_STACK_USER_PIPELINE_MODE")


def _owner_user_id_from_env() -> str:
    return _clean_text(os.environ.get("JOB_STACK_OWNER_USER_ID"))


def _safe_resume_suffix(resume_name: str = "", content_type: str = "") -> str:
    suffix = Path(_clean_text(resume_name)).suffix.lower()

    if suffix in {".pdf"}:
        return suffix

    normalized_content_type = _clean_text(content_type).lower()
    if normalized_content_type == "application/pdf":
        return ".pdf"

    # The existing parser path is PDF-based. Keep a safe suffix instead of
    # pretending we support other binary resume formats here.
    return ".pdf"


def _extract_profile_resume_blob_record(
    *,
    owner_user_id: str,
    resume_name: str,
) -> Dict[str, Any]:
    payload = get_profile_resume_blob_postgres_payload(
        owner_user_id=owner_user_id,
        resume_name=resume_name,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
        ensure_schema=True,
    )

    resume = dict(payload.get("resume", {}) or {})
    file_bytes = payload.get("file_bytes", b"")

    if not file_bytes:
        return {}

    safe_resume_name = _clean_text(resume.get("resume_name")) or _clean_text(resume_name)
    suffix = _safe_resume_suffix(
        safe_resume_name,
        _clean_text(resume.get("content_type")),
    )

    with tempfile.NamedTemporaryFile(suffix=suffix) as handle:
        handle.write(file_bytes)
        handle.flush()

        extracted = extract_resume_texts(Path(handle.name))

    raw_text = _clean_text(extracted.get("raw_text"))
    normalized_text = _clean_text(extracted.get("text"))

    if not raw_text:
        return {}

    return {
        "resume_name": safe_resume_name,
        "path": "",
        "raw_text": raw_text,
        "text": normalized_text or raw_text,
        "normalized_text": normalized_text or raw_text,
        "storage": "postgres",
        "owner_user_id": owner_user_id,
    }


def _load_profile_resume_records_from_postgres(
    *,
    names: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    owner_user_id = _owner_user_id_from_env()
    if not owner_user_id:
        raise RuntimeError("JOB_STACK_OWNER_USER_ID not set for user pipeline resume loading.")

    requested_names = [
        _clean_text(name)
        for name in list(names or [])
        if _clean_text(name)
    ]

    if requested_names:
        resume_names = requested_names
    else:
        payload = get_profile_resumes_postgres_payload(
            owner_user_id=owner_user_id,
            database_url="",
            database_url_env="DATABASE_URL",
            psql_bin="psql",
            print_only=False,
            ensure_schema=True,
        )
        resume_names = [
            _clean_text(row.get("resume_name"))
            for row in list(payload.get("resumes", []) or [])
            if _clean_text(row.get("resume_name"))
        ]

    records: List[Dict[str, Any]] = []
    for resume_name in resume_names:
        record = _extract_profile_resume_blob_record(
            owner_user_id=owner_user_id,
            resume_name=resume_name,
        )
        if record:
            records.append(record)

    return records


def load_resume_documents() -> List[ResumeDocument]:
    records = (
        _load_profile_resume_records_from_postgres()
        if _is_user_pipeline_mode()
        else load_resumes()
    )
    return [ResumeDocument.from_loader_record(record) for record in records]


def load_resume_documents_by_name(names: List[str]) -> List[ResumeDocument]:
    if not names:
        return []

    records = (
        _load_profile_resume_records_from_postgres(names=names)
        if _is_user_pipeline_mode()
        else load_resumes_by_name(names)
    )
    return [ResumeDocument.from_loader_record(record) for record in records]


def get_resume_document_map(names: Optional[List[str]] = None) -> dict[str, ResumeDocument]:
    documents = (
        load_resume_documents_by_name(names)
        if names is not None
        else load_resume_documents()
    )
    return {doc.resume_id: doc for doc in documents}
