from typing import List, Optional

from src.resume.models import ResumeDocument
from src.resume.resume_loader import load_resumes, load_resumes_by_name


def load_resume_documents() -> List[ResumeDocument]:
    records = load_resumes()
    return [ResumeDocument.from_loader_record(record) for record in records]


def load_resume_documents_by_name(names: List[str]) -> List[ResumeDocument]:
    if not names:
        return []

    records = load_resumes_by_name(names)
    return [ResumeDocument.from_loader_record(record) for record in records]


def get_resume_document_map(names: Optional[List[str]] = None) -> dict[str, ResumeDocument]:
    documents = (
        load_resume_documents_by_name(names)
        if names is not None
        else load_resume_documents()
    )
    return {doc.resume_id: doc for doc in documents}