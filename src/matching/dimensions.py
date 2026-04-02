from dataclasses import replace
from typing import Dict, List

from src.matching.models import MatchDimensionDefinition


_DEFAULT_MATCH_DIMENSIONS: List[MatchDimensionDefinition] = [
    MatchDimensionDefinition(
        name="title_alignment",
        weight=0.186046,
        description="How closely the resume's titles align with the target job title and function.",
    ),
    MatchDimensionDefinition(
        name="required_skills_alignment",
        weight=0.255814,
        description="Coverage and strength of required job skills in the resume evidence.",
    ),
    MatchDimensionDefinition(
        name="preferred_skills_alignment",
        weight=0.078023,
        description="Coverage of preferred or bonus skills in the resume evidence.",
    ),
    MatchDimensionDefinition(
        name="workflow_alignment",
        weight=0.076513,
        description="Alignment between JD workflows and the candidate's experience-bullet workflows such as experimentation, reporting, dashboards, data quality, automation, and pipelines.",
    ),
    MatchDimensionDefinition(
        name="business_context_alignment",
        weight=0.046511,
        description="Alignment between the JD's business problem space and the candidate's experience-bullet business contexts such as growth, revenue, customer success, public safety, healthcare, or risk.",
    ),
    MatchDimensionDefinition(
        name="stakeholder_translation_alignment",
        weight=0.023256,
        description="Alignment between the JD's stakeholder context and the candidate's experience-bullet evidence of translating analysis for customers, non-technical stakeholders, and cross-functional partners.",
    ),
    MatchDimensionDefinition(
        name="domain_relevance",
        weight=0.046512,
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
        weight=0.078023,
        description="Overlap between the resume's tools/stack and the job's required tooling.",
    ),
]

_ARCHETYPE_WEIGHT_OVERRIDES: Dict[str, Dict[str, float]] = {
    "data_scientist": {
        "title_alignment": 0.140000,
        "required_skills_alignment": 0.250000,
        "preferred_skills_alignment": 0.070000,
        "workflow_alignment": 0.090000,
        "business_context_alignment": 0.060000,
        "stakeholder_translation_alignment": 0.030000,
        "domain_relevance": 0.040000,
        "analytics_ml_depth": 0.160000,
        "experimentation_depth": 0.090000,
        "tooling_alignment": 0.070000,
    },
    "growth_product_analytics": {
        "title_alignment": 0.100000,
        "required_skills_alignment": 0.230000,
        "preferred_skills_alignment": 0.060000,
        "workflow_alignment": 0.160000,
        "business_context_alignment": 0.110000,
        "stakeholder_translation_alignment": 0.060000,
        "domain_relevance": 0.050000,
        "analytics_ml_depth": 0.100000,
        "experimentation_depth": 0.080000,
        "tooling_alignment": 0.050000,
    },
}

PREFILTER_CHECKS: List[str] = [
    "minimum_title_or_skill_overlap",
    "required_skill_coverage_floor",
    "seniority_mismatch_guard",
    "location_or_work_auth_guard",
]


def _validate_dimension_weights(dimensions: List[MatchDimensionDefinition]) -> None:
    total = round(sum(dimension.weight for dimension in dimensions), 6)
    if total != 1.0:
        raise ValueError(f"Match dimension weights must sum to 1.0, got {total}")


def get_match_dimensions(role_archetype: str = "") -> List[MatchDimensionDefinition]:
    archetype = str(role_archetype or "").strip().lower()
    overrides = _ARCHETYPE_WEIGHT_OVERRIDES.get(archetype)

    if not overrides:
        dimensions = [replace(dimension) for dimension in _DEFAULT_MATCH_DIMENSIONS]
        _validate_dimension_weights(dimensions)
        return dimensions

    dimensions = [
        replace(dimension, weight=overrides.get(dimension.name, dimension.weight))
        for dimension in _DEFAULT_MATCH_DIMENSIONS
    ]
    _validate_dimension_weights(dimensions)
    return dimensions


def get_dimension_weights(role_archetype: str = "") -> Dict[str, float]:
    return {dimension.name: dimension.weight for dimension in get_match_dimensions(role_archetype)}


def total_match_weight(role_archetype: str = "") -> float:
    return sum(dimension.weight for dimension in get_match_dimensions(role_archetype))