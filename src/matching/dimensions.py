from typing import Dict, List

from src.matching.models import MatchDimensionDefinition


MATCH_DIMENSIONS: List[MatchDimensionDefinition] = [
    MatchDimensionDefinition(
        name="title_alignment",
        weight=0.209302,
        description="How closely the resume's titles align with the target job title and function.",
    ),
    MatchDimensionDefinition(
        name="required_skills_alignment",
        weight=0.255814,
        description="Coverage and strength of required job skills in the resume evidence.",
    ),
    MatchDimensionDefinition(
        name="preferred_skills_alignment",
        weight=0.093023,
        description="Coverage of preferred or bonus skills in the resume evidence.",
    ),
    MatchDimensionDefinition(
        name="domain_relevance",
        weight=0.093023,
        description="Relevance of past domain experience to the target job's business or problem space.",
    ),
    MatchDimensionDefinition(
        name="analytics_ml_depth",
        weight=0.116279,
        description="Strength of analytics, statistics, machine learning, or data science depth.",
    ),
    MatchDimensionDefinition(
        name="experimentation_depth",
        weight=0.093023,
        description="Evidence of experimentation, causal inference, statistical testing, or measurement work.",
    ),
    MatchDimensionDefinition(
        name="tooling_alignment",
        weight=0.093023,
        description="Overlap between the resume's tools/stack and the job's required tooling.",
    ),
    MatchDimensionDefinition(
        name="project_relevance",
        weight=0.046513,
        description="Relevance of resume projects or side work to the target role.",
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