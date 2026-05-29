from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Tuple

from src.config.role_taxonomy import ROLE_TAXONOMY


DEFAULT_SCORING_ROLE_FAMILY_ID = "data_science"

_BASE_DIMENSION_WEIGHTS: Dict[str, float] = {
    "title_alignment": 0.160000,
    "required_skills_alignment": 0.200000,
    "preferred_skills_alignment": 0.060000,
    "workflow_alignment": 0.120000,
    "business_context_alignment": 0.070000,
    "stakeholder_translation_alignment": 0.050000,
    "domain_relevance": 0.060000,
    "analytics_ml_depth": 0.130000,
    "experimentation_depth": 0.070000,
    "tooling_alignment": 0.080000,
}


def _profile(
    role_family_id: str,
    *,
    dimension_weights: Dict[str, float],
    signal_families: Tuple[str, ...],
    skill_groups: Dict[str, Tuple[str, ...]],
) -> Dict[str, Any]:
    if role_family_id not in ROLE_TAXONOMY:
        raise KeyError(f"Unknown role family id={role_family_id!r}.")

    total = round(sum(dimension_weights.values()), 6)
    if total != 1.0:
        raise ValueError(f"Role scoring profile weights must sum to 1.0 for {role_family_id}; got {total}.")

    return {
        "role_family_id": role_family_id,
        "display_name": ROLE_TAXONOMY[role_family_id]["display_name"],
        "dimensions": tuple(dimension_weights.keys()),
        "dimension_weights": dict(dimension_weights),
        "signal_families": signal_families,
        "skill_groups": skill_groups,
    }


ROLE_SCORING_PROFILES: Dict[str, Dict[str, Any]] = {
    "data_science": _profile(
        "data_science",
        dimension_weights=_BASE_DIMENSION_WEIGHTS,
        signal_families=(
            "statistics",
            "machine_learning",
            "experimentation",
            "sql",
            "analytics_workflows",
        ),
        skill_groups={
            "modeling": ("statistics", "predictive modeling", "machine learning", "feature engineering"),
            "experimentation": ("experimentation", "a/b testing", "causal inference", "hypothesis testing"),
            "data_tools": ("python", "sql", "pandas", "scikit-learn", "notebooks"),
        },
    ),
    "ml_ai_engineering": _profile(
        "ml_ai_engineering",
        dimension_weights={
            "title_alignment": 0.140000,
            "required_skills_alignment": 0.220000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.140000,
            "business_context_alignment": 0.040000,
            "stakeholder_translation_alignment": 0.030000,
            "domain_relevance": 0.050000,
            "analytics_ml_depth": 0.170000,
            "experimentation_depth": 0.050000,
            "tooling_alignment": 0.100000,
        },
        signal_families=("ml_systems", "model_deployment", "inference", "mlops", "ai_tooling"),
        skill_groups={
            "model_engineering": ("pytorch", "tensorflow", "model deployment", "inference", "evaluation"),
            "mlops": ("mlflow", "kubeflow", "feature stores", "vector databases", "model monitoring"),
            "software": ("python", "apis", "distributed systems", "containers"),
        },
    ),
    "data_engineering": _profile(
        "data_engineering",
        dimension_weights={
            "title_alignment": 0.130000,
            "required_skills_alignment": 0.230000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.180000,
            "business_context_alignment": 0.050000,
            "stakeholder_translation_alignment": 0.030000,
            "domain_relevance": 0.050000,
            "analytics_ml_depth": 0.070000,
            "experimentation_depth": 0.020000,
            "tooling_alignment": 0.180000,
        },
        signal_families=("data_pipelines", "etl", "warehousing", "orchestration", "data_quality"),
        skill_groups={
            "pipelines": ("etl", "spark", "airflow", "streaming", "data pipelines"),
            "warehouse": ("snowflake", "databricks", "dbt", "data modeling"),
            "quality": ("data quality", "lineage", "reliability", "observability"),
        },
    ),
    "analytics": _profile(
        "analytics",
        dimension_weights={
            "title_alignment": 0.130000,
            "required_skills_alignment": 0.190000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.170000,
            "business_context_alignment": 0.120000,
            "stakeholder_translation_alignment": 0.080000,
            "domain_relevance": 0.060000,
            "analytics_ml_depth": 0.100000,
            "experimentation_depth": 0.040000,
            "tooling_alignment": 0.050000,
        },
        signal_families=("sql", "dashboards", "metrics", "business_intelligence", "stakeholder_reporting"),
        skill_groups={
            "analytics": ("sql", "metrics", "reporting", "business intelligence"),
            "visualization": ("tableau", "power bi", "looker", "dashboards"),
            "decision_support": ("stakeholder communication", "insights", "kpis"),
        },
    ),
    "backend_engineering": _profile(
        "backend_engineering",
        dimension_weights={
            "title_alignment": 0.150000,
            "required_skills_alignment": 0.240000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.160000,
            "business_context_alignment": 0.040000,
            "stakeholder_translation_alignment": 0.030000,
            "domain_relevance": 0.050000,
            "analytics_ml_depth": 0.030000,
            "experimentation_depth": 0.020000,
            "tooling_alignment": 0.220000,
        },
        signal_families=("backend_services", "api_design", "distributed_systems", "databases", "system_design"),
        skill_groups={
            "backend": ("api design", "microservices", "service architecture", "server-side development"),
            "systems": ("distributed systems", "system design", "scalability", "performance"),
            "data_stores": ("postgres", "redis", "database design", "queues"),
        },
    ),
    "frontend_engineering": _profile(
        "frontend_engineering",
        dimension_weights={
            "title_alignment": 0.150000,
            "required_skills_alignment": 0.230000,
            "preferred_skills_alignment": 0.070000,
            "workflow_alignment": 0.160000,
            "business_context_alignment": 0.050000,
            "stakeholder_translation_alignment": 0.060000,
            "domain_relevance": 0.040000,
            "analytics_ml_depth": 0.020000,
            "experimentation_depth": 0.030000,
            "tooling_alignment": 0.190000,
        },
        signal_families=("frontend_ui", "component_systems", "accessibility", "web_performance", "ux_delivery"),
        skill_groups={
            "frontend": ("react", "typescript", "javascript", "css", "html"),
            "ui": ("design systems", "component architecture", "responsive design", "accessibility"),
            "quality": ("frontend testing", "performance", "browser compatibility"),
        },
    ),
    "fullstack_engineering": _profile(
        "fullstack_engineering",
        dimension_weights={
            "title_alignment": 0.150000,
            "required_skills_alignment": 0.230000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.170000,
            "business_context_alignment": 0.050000,
            "stakeholder_translation_alignment": 0.050000,
            "domain_relevance": 0.040000,
            "analytics_ml_depth": 0.030000,
            "experimentation_depth": 0.030000,
            "tooling_alignment": 0.190000,
        },
        signal_families=("fullstack_delivery", "frontend_ui", "backend_services", "api_design", "databases"),
        skill_groups={
            "frontend": ("react", "typescript", "css", "web ui"),
            "backend": ("apis", "node.js", "python", "databases"),
            "delivery": ("end-to-end features", "testing", "deployment"),
        },
    ),
    "software_engineering": _profile(
        "software_engineering",
        dimension_weights={
            "title_alignment": 0.170000,
            "required_skills_alignment": 0.240000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.150000,
            "business_context_alignment": 0.040000,
            "stakeholder_translation_alignment": 0.040000,
            "domain_relevance": 0.050000,
            "analytics_ml_depth": 0.030000,
            "experimentation_depth": 0.030000,
            "tooling_alignment": 0.190000,
        },
        signal_families=("software_design", "code_quality", "testing", "systems", "delivery"),
        skill_groups={
            "engineering": ("software development", "system design", "data structures", "algorithms"),
            "quality": ("testing", "code review", "maintainability"),
            "tools": ("git", "ci/cd", "language ecosystems"),
        },
    ),
    "cloud_devops": _profile(
        "cloud_devops",
        dimension_weights={
            "title_alignment": 0.150000,
            "required_skills_alignment": 0.230000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.170000,
            "business_context_alignment": 0.030000,
            "stakeholder_translation_alignment": 0.030000,
            "domain_relevance": 0.040000,
            "analytics_ml_depth": 0.020000,
            "experimentation_depth": 0.020000,
            "tooling_alignment": 0.250000,
        },
        signal_families=("cloud_infrastructure", "devops", "ci_cd", "containers", "infrastructure_as_code"),
        skill_groups={
            "cloud": ("aws", "azure", "gcp", "cloud infrastructure"),
            "infra": ("terraform", "kubernetes", "docker", "linux"),
            "delivery": ("ci/cd", "deployment automation", "platform operations"),
        },
    ),
    "sre": _profile(
        "sre",
        dimension_weights={
            "title_alignment": 0.150000,
            "required_skills_alignment": 0.220000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.180000,
            "business_context_alignment": 0.030000,
            "stakeholder_translation_alignment": 0.040000,
            "domain_relevance": 0.040000,
            "analytics_ml_depth": 0.020000,
            "experimentation_depth": 0.020000,
            "tooling_alignment": 0.240000,
        },
        signal_families=("reliability", "observability", "incident_response", "slo_management", "cloud_infra"),
        skill_groups={
            "reliability": ("slo", "sla", "incident response", "capacity planning"),
            "observability": ("prometheus", "grafana", "datadog", "logging", "tracing"),
            "infra": ("kubernetes", "terraform", "linux", "automation"),
        },
    ),
    "qa_automation": _profile(
        "qa_automation",
        dimension_weights={
            "title_alignment": 0.150000,
            "required_skills_alignment": 0.230000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.190000,
            "business_context_alignment": 0.030000,
            "stakeholder_translation_alignment": 0.040000,
            "domain_relevance": 0.030000,
            "analytics_ml_depth": 0.020000,
            "experimentation_depth": 0.030000,
            "tooling_alignment": 0.220000,
        },
        signal_families=("test_automation", "quality_engineering", "regression", "release_validation", "test_frameworks"),
        skill_groups={
            "automation": ("selenium", "playwright", "cypress", "pytest", "junit"),
            "testing": ("test automation", "regression testing", "integration testing", "e2e testing"),
            "quality": ("quality assurance", "release validation", "test strategy"),
        },
    ),
    "security": _profile(
        "security",
        dimension_weights={
            "title_alignment": 0.150000,
            "required_skills_alignment": 0.230000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.160000,
            "business_context_alignment": 0.040000,
            "stakeholder_translation_alignment": 0.050000,
            "domain_relevance": 0.050000,
            "analytics_ml_depth": 0.020000,
            "experimentation_depth": 0.020000,
            "tooling_alignment": 0.220000,
        },
        signal_families=("security_engineering", "iam", "vulnerability_management", "threat_detection", "appsec"),
        skill_groups={
            "security": ("threat modeling", "application security", "cloud security", "incident response"),
            "iam": ("iam", "identity and access", "okta", "access control"),
            "vulnerability": ("vulnerability management", "siem", "splunk", "risk assessment"),
        },
    ),
    "systems_it": _profile(
        "systems_it",
        dimension_weights={
            "title_alignment": 0.160000,
            "required_skills_alignment": 0.230000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.170000,
            "business_context_alignment": 0.040000,
            "stakeholder_translation_alignment": 0.060000,
            "domain_relevance": 0.050000,
            "analytics_ml_depth": 0.020000,
            "experimentation_depth": 0.020000,
            "tooling_alignment": 0.190000,
        },
        signal_families=("systems_administration", "networking", "endpoint_management", "identity", "support_operations"),
        skill_groups={
            "systems": ("linux", "windows", "systems administration", "networking"),
            "identity": ("active directory", "identity management", "intune", "jamf"),
            "operations": ("endpoint support", "troubleshooting", "service desk"),
        },
    ),
    "solutions_engineering": _profile(
        "solutions_engineering",
        dimension_weights={
            "title_alignment": 0.150000,
            "required_skills_alignment": 0.190000,
            "preferred_skills_alignment": 0.060000,
            "workflow_alignment": 0.130000,
            "business_context_alignment": 0.090000,
            "stakeholder_translation_alignment": 0.140000,
            "domain_relevance": 0.080000,
            "analytics_ml_depth": 0.030000,
            "experimentation_depth": 0.020000,
            "tooling_alignment": 0.110000,
        },
        signal_families=("technical_sales", "customer_solutions", "integrations", "proof_of_concept", "stakeholder_translation"),
        skill_groups={
            "solutions": ("technical discovery", "solution design", "proof of concept"),
            "customer": ("customer integration", "technical sales", "stakeholder communication"),
            "tools": ("api", "sql", "python", "salesforce", "crm"),
        },
    ),
}


def get_role_scoring_profile(role_family_id: str) -> Dict[str, Any]:
    normalized = str(role_family_id or "").strip()
    if normalized not in ROLE_SCORING_PROFILES:
        allowed = ", ".join(sorted(ROLE_SCORING_PROFILES))
        raise KeyError(f"Unknown role scoring profile id={role_family_id!r}. Allowed: {allowed}")
    return deepcopy(ROLE_SCORING_PROFILES[normalized])


def get_role_scoring_dimensions(role_family_id: str) -> Tuple[str, ...]:
    profile = get_role_scoring_profile(role_family_id)
    return tuple(profile["dimensions"])


def get_default_scoring_profile() -> Dict[str, Any]:
    return get_role_scoring_profile(DEFAULT_SCORING_ROLE_FAMILY_ID)
