from dataclasses import replace
from typing import Dict, List

from src.matching.models import MatchDimensionDefinition


_DEFAULT_MATCH_DIMENSIONS: List[MatchDimensionDefinition] = [
    MatchDimensionDefinition(
        name="title_alignment",
        weight=0.160000,
        description="How closely the resume's titles align with the target job title and function.",
    ),
    MatchDimensionDefinition(
        name="required_skills_alignment",
        weight=0.200000,
        description="Coverage and strength of required job skills in the resume evidence.",
    ),
    MatchDimensionDefinition(
        name="preferred_skills_alignment",
        weight=0.060000,
        description="Coverage of preferred or bonus skills in the resume evidence.",
    ),
    MatchDimensionDefinition(
        name="workflow_alignment",
        weight=0.120000,
        description="Alignment between JD workflows and the candidate's experience-bullet workflows such as experimentation, reporting, dashboards, data quality, automation, and pipelines.",
    ),
    MatchDimensionDefinition(
        name="business_context_alignment",
        weight=0.070000,
        description="Alignment between the JD's business problem space and the candidate's experience-bullet business contexts such as growth, revenue, customer success, public safety, healthcare, or risk.",
    ),
    MatchDimensionDefinition(
        name="stakeholder_translation_alignment",
        weight=0.050000,
        description="Alignment between the JD's stakeholder context and the candidate's experience-bullet evidence of translating analysis for customers, non-technical stakeholders, and cross-functional partners.",
    ),
    MatchDimensionDefinition(
        name="domain_relevance",
        weight=0.060000,
        description="Relevance of past domain experience to the target job's business or problem space.",
    ),
    MatchDimensionDefinition(
        name="analytics_ml_depth",
        weight=0.130000,
        description="Strength of analytics, statistics, machine learning, or data science depth.",
    ),
    MatchDimensionDefinition(
        name="experimentation_depth",
        weight=0.070000,
        description="Evidence of experimentation, causal inference, statistical testing, or measurement work.",
    ),
    MatchDimensionDefinition(
        name="tooling_alignment",
        weight=0.080000,
        description="Overlap between the resume's tools/stack and the job's required tooling.",
    ),
]

_ARCHETYPE_WEIGHT_OVERRIDES: Dict[str, Dict[str, float]] = {
    "data_scientist": {
        "title_alignment": 0.120000,
        "required_skills_alignment": 0.200000,
        "preferred_skills_alignment": 0.050000,
        "workflow_alignment": 0.110000,
        "business_context_alignment": 0.060000,
        "stakeholder_translation_alignment": 0.040000,
        "domain_relevance": 0.050000,
        "analytics_ml_depth": 0.180000,
        "experimentation_depth": 0.110000,
        "tooling_alignment": 0.080000,
    },
    "growth_product_analytics": {
        "title_alignment": 0.100000,
        "required_skills_alignment": 0.180000,
        "preferred_skills_alignment": 0.050000,
        "workflow_alignment": 0.170000,
        "business_context_alignment": 0.120000,
        "stakeholder_translation_alignment": 0.070000,
        "domain_relevance": 0.050000,
        "analytics_ml_depth": 0.110000,
        "experimentation_depth": 0.090000,
        "tooling_alignment": 0.060000,
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
    """
    Return scoring dimensions used for resume selection.

    Important: title_alignment is intentionally excluded from weighted selection.
    Resume/job title similarity can be useful as a diagnostic, but it should not
    boost or suppress resume selection because it creates title-based false
    positives and false negatives. Selection should be driven by JD-to-experience
    evidence, skills, methods, workflow, domain, tooling, and business context.
    """
    role_key = (role_archetype or "").strip().lower()
    overrides = _ARCHETYPE_WEIGHT_OVERRIDES.get(role_key)

    dimensions = _DEFAULT_MATCH_DIMENSIONS
    if overrides:
        dimensions = [
            replace(dimension, weight=overrides.get(dimension.name, dimension.weight))
            for dimension in dimensions
        ]

    dimensions = [
        dimension
        for dimension in dimensions
        if dimension.name != "title_alignment"
    ]

    total = sum(dimension.weight for dimension in dimensions)
    if total <= 0:
        raise ValueError("Match dimension weights must have positive total after excluding title_alignment")

    normalized = []
    running_total = 0.0

    for dimension in dimensions[:-1]:
        normalized_weight = round(dimension.weight / total, 6)
        running_total += normalized_weight
        normalized.append(replace(dimension, weight=normalized_weight))

    normalized.append(
        replace(dimensions[-1], weight=round(1.0 - running_total, 6))
    )

    _validate_dimension_weights(normalized)
    return normalized


def get_dimension_weights(role_archetype: str = "") -> Dict[str, float]:
    return {dimension.name: dimension.weight for dimension in get_match_dimensions(role_archetype)}


def total_match_weight(role_archetype: str = "") -> float:
    return sum(dimension.weight for dimension in get_match_dimensions(role_archetype))
