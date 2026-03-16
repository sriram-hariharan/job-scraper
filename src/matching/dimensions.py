from typing import Dict, List

from src.matching.models import MatchDimensionDefinition


MATCH_DIMENSIONS: List[MatchDimensionDefinition] = [
    MatchDimensionDefinition(
        name="title_alignment",
        weight=0.18,
        description="How closely the resume's titles align with the target job title and function.",
    ),
    MatchDimensionDefinition(
        name="required_skills_alignment",
        weight=0.22,
        description="Coverage and strength of required job skills in the resume evidence.",
    ),
    MatchDimensionDefinition(
        name="preferred_skills_alignment",
        weight=0.08,
        description="Coverage of preferred or bonus skills in the resume evidence.",
    ),
    MatchDimensionDefinition(
        name="seniority_fit",
        weight=0.10,
        description="How well the resume's apparent level matches the target role's seniority.",
    ),
    MatchDimensionDefinition(
        name="domain_relevance",
        weight=0.08,
        description="Relevance of past domain experience to the target job's business or problem space.",
    ),
    MatchDimensionDefinition(
        name="analytics_ml_depth",
        weight=0.10,
        description="Strength of analytics, statistics, machine learning, or data science depth.",
    ),
    MatchDimensionDefinition(
        name="experimentation_depth",
        weight=0.08,
        description="Evidence of experimentation, causal inference, statistical testing, or measurement work.",
    ),
    MatchDimensionDefinition(
        name="tooling_alignment",
        weight=0.08,
        description="Overlap between the resume's tools/stack and the job's required tooling.",
    ),
    MatchDimensionDefinition(
        name="project_relevance",
        weight=0.04,
        description="Relevance of resume projects or side work to the target role.",
    ),
    MatchDimensionDefinition(
        name="evidence_strength",
        weight=0.04,
        description="Quality of evidence, including quantified impact, clear ownership, and concrete outcomes.",
    ),
]


PREFILTER_CHECKS: List[str] = [
    "minimum_title_or_skill_overlap",
    "required_skill_coverage_floor",
    "seniority_mismatch_guard",
    "location_or_work_auth_guard",
]


def get_match_dimensions() -> List[MatchDimensionDefinition]:
    return list(MATCH_DIMENSIONS)


def get_dimension_weights() -> Dict[str, float]:
    return {dimension.name: dimension.weight for dimension in MATCH_DIMENSIONS}


def total_match_weight() -> float:
    return sum(dimension.weight for dimension in MATCH_DIMENSIONS)


_TOTAL_WEIGHT = round(total_match_weight(), 6)
if _TOTAL_WEIGHT != 1.0:
    raise ValueError(f"Match dimension weights must sum to 1.0, got {_TOTAL_WEIGHT}")