from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class JobEvidence:
    job_doc_id: str
    company: str
    title: str
    location: str
    source: str
    job_url: str
    posted_at: str
    role_family: str
    seniority: str
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    all_skills: List[str] = field(default_factory=list)
    visa_sponsorship: str = ""
    ai_fit_score: Optional[float] = None
    retrieval_text: str = ""
    preview: str = ""
    notes: Dict[str, Any] = field(default_factory=dict)