from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    ok: bool = True
    service: str = "job-operator-api"


class BrowseParams(BaseModel):
    action: str = ""
    needs_review: str = ""
    is_tie: str = ""
    fallback_status: str = ""
    winner_bucket: str = ""
    company_contains: str = ""
    title_contains: str = ""
    undecided_only: str = ""
    limit: int = 20


class ReviewParams(BaseModel):
    action: str = ""
    queue_rank: Optional[int] = None
    job_doc_id: str = ""
    company_contains: str = ""
    title_contains: str = ""
    include_non_review: bool = False
    undecided_only: str = ""
    limit: int = 20


class WorkflowParams(BaseModel):
    view: str
    limit: int = 20


class PlannerParams(BaseModel):
    request: str
    limit: int = 20


class DecisionsParams(BaseModel):
    queue_rank: Optional[int] = None
    decision: str = ""
    selected_resume: str = ""
    company_contains: str = ""
    title_contains: str = ""
    limit: int = 20


class RagSearchParams(BaseModel):
    request: str
    top_k: int = 5
    fetch_k: int = 15
    output_mode: str = "compact"
    include_diagnostics: bool = False


class RagAnswerParams(BaseModel):
    request: str
    top_k: int = 5
    fetch_k: int = 15
    output_mode: str = "compact"
    include_diagnostics: bool = False


class Envelope(BaseModel):
    ok: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None