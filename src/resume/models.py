from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional


def _normalize_resume_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


@dataclass
class ResumeDocument:
    resume_id: str
    resume_name: str
    path: str
    raw_text: str
    normalized_text: str

    @classmethod
    def from_loader_record(cls, record: Dict[str, Any]) -> "ResumeDocument":
        resume_name = str(record.get("resume_name") or "").strip()
        path = str(record.get("path") or "").strip()

        raw_text = str(
            record.get("raw_text")
            or record.get("text")
            or ""
        )

        normalized_text = str(
            record.get("normalized_text")
            or record.get("text")
            or _normalize_resume_text(raw_text)
        )

        return cls(
            resume_id=resume_name,
            resume_name=resume_name,
            path=path,
            raw_text=raw_text,
            normalized_text=normalized_text,
        )


@dataclass
class ResumeExperienceEntry:
    entry_id: str = ""
    entry_index: Optional[int] = None
    company: str = ""
    title: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    duration_months: Optional[int] = None
    bullets: List[str] = field(default_factory=list)
    bullet_ids: List[str] = field(default_factory=list)

    normalized_titles: List[str] = field(default_factory=list)
    normalized_skills: List[str] = field(default_factory=list)

    # V2 structured experience-entry fields
    normalized_methods: List[str] = field(default_factory=list)
    normalized_tools: List[str] = field(default_factory=list)
    normalized_workflows: List[str] = field(default_factory=list)
    business_contexts: List[str] = field(default_factory=list)
    stakeholder_contexts: List[str] = field(default_factory=list)
    artifact_types: List[str] = field(default_factory=list)
    kpi_metrics: List[str] = field(default_factory=list)
    ownership_signals: List[str] = field(default_factory=list)


@dataclass
class ResumeProjectEntry:
    entry_id: str = ""
    entry_index: Optional[int] = None
    name: str = ""
    bullets: List[str] = field(default_factory=list)
    bullet_ids: List[str] = field(default_factory=list)
    normalized_skills: List[str] = field(default_factory=list)

    # V2 structured project fields
    normalized_methods: List[str] = field(default_factory=list)
    normalized_tools: List[str] = field(default_factory=list)
    normalized_workflows: List[str] = field(default_factory=list)
    business_contexts: List[str] = field(default_factory=list)
    stakeholder_contexts: List[str] = field(default_factory=list)
    artifact_types: List[str] = field(default_factory=list)
    kpi_metrics: List[str] = field(default_factory=list)
    ownership_signals: List[str] = field(default_factory=list)


@dataclass
class ResumeEducationEntry:
    school: str = ""
    degree: str = ""
    field_of_study: str = ""
    graduation_date: str = ""


@dataclass
class ResumeEvidence:
    document: ResumeDocument
    titles: List[str] = field(default_factory=list)
    companies: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    education_entries: List[ResumeEducationEntry] = field(default_factory=list)
    experience_entries: List[ResumeExperienceEntry] = field(default_factory=list)
    project_entries: List[ResumeProjectEntry] = field(default_factory=list)

    domain_signals: List[str] = field(default_factory=list)
    analytics_ml_signals: List[str] = field(default_factory=list)
    experimentation_signals: List[str] = field(default_factory=list)
    tooling_signals: List[str] = field(default_factory=list)
    quantified_bullets: List[str] = field(default_factory=list)

    # V2 structured aggregate fields
    methods: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    workflows: List[str] = field(default_factory=list)
    business_contexts: List[str] = field(default_factory=list)
    stakeholder_contexts: List[str] = field(default_factory=list)
    artifact_types: List[str] = field(default_factory=list)
    kpi_metrics: List[str] = field(default_factory=list)
    ownership_signals: List[str] = field(default_factory=list)

    notes: Dict[str, Any] = field(default_factory=dict)