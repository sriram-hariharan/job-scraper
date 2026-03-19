from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class MatchDimensionDefinition:
    name: str
    weight: float
    description: str


@dataclass
class MatchDimensionScore:
    name: str
    score: float
    weight: float
    weighted_score: float
    reason: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class MatchPrefilterResult:
    passed: bool
    reasons: List[str] = field(default_factory=list)
    matched_terms: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResumeJobPair:
    resume_id: str
    resume_name: str
    job_doc_id: str
    job_company: str
    job_title: str


@dataclass
class ResumeJobMatchResult:
    pair: ResumeJobPair
    prefilter: MatchPrefilterResult
    dimension_scores: List[MatchDimensionScore] = field(default_factory=list)
    final_score: float = 0.0
    match_bucket: str = ""
    rank_for_resume: Optional[int] = None
    rank_for_job: Optional[int] = None