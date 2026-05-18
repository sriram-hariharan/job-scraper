from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Pattern, Tuple


COMMON_TITLE_EXCLUDE_PATTERNS: Tuple[str, ...] = (
    r"director",
    r"vp",
    r"vice president",
    r"manager",
    r"intern",
    r"student",
    r"principal architect",
    r"lead",
    r"staff",
    r"principal",
    r"architect",
)

DEFAULT_ROLE_FAMILY_IDS: Tuple[str, ...] = (
    "data_science",
    "ml_ai_engineering",
    "analytics",
)


ROLE_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "data_science": {
        "role_family_id": "data_science",
        "display_name": "Data Science",
        "title_include_patterns": (
            r"data scientist",
            r"applied scientist",
            r"research scientist",
            r"decision scientist",
            r"ml scientist",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"statistics",
            r"predictive modeling",
            r"feature engineering",
            r"experimentation",
            r"causal inference",
        ),
        "tooling_patterns": (
            r"python",
            r"r\b",
            r"scikit-learn",
            r"pandas",
            r"notebook",
        ),
        "responsibility_patterns": (
            r"build predictive models",
            r"analyze experiments",
            r"develop statistical models",
            r"translate data into insights",
        ),
    },
    "ml_ai_engineering": {
        "role_family_id": "ml_ai_engineering",
        "display_name": "ML / AI Engineering",
        "title_include_patterns": (
            r"machine learning engineer",
            r"\bml engineer\b",
            r"ai engineer",
            r"deep learning engineer",
            r"nlp engineer",
            r"\bgenai\b",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"machine learning",
            r"deep learning",
            r"model training",
            r"model deployment",
            r"inference",
        ),
        "tooling_patterns": (
            r"pytorch",
            r"tensorflow",
            r"mlflow",
            r"kubeflow",
            r"vector database",
        ),
        "responsibility_patterns": (
            r"deploy models",
            r"build ml pipelines",
            r"optimize inference",
            r"productionize ai systems",
        ),
    },
    "data_engineering": {
        "role_family_id": "data_engineering",
        "display_name": "Data Engineering",
        "title_include_patterns": (
            r"data engineer",
            r"etl engineer",
            r"analytics platform engineer",
            r"data platform engineer",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"etl",
            r"data pipeline",
            r"data warehouse",
            r"data modeling",
            r"stream processing",
        ),
        "tooling_patterns": (
            r"spark",
            r"airflow",
            r"dbt",
            r"snowflake",
            r"databricks",
        ),
        "responsibility_patterns": (
            r"build data pipelines",
            r"maintain data platforms",
            r"orchestrate workflows",
            r"deliver trusted datasets",
        ),
    },
    "analytics": {
        "role_family_id": "analytics",
        "display_name": "Analytics",
        "title_include_patterns": (
            r"data analyst",
            r"analytics engineer",
            r"business intelligence analyst",
            r"\bbi analyst\b",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"sql",
            r"dashboard",
            r"reporting",
            r"business intelligence",
            r"metrics",
        ),
        "tooling_patterns": (
            r"tableau",
            r"power bi",
            r"looker",
            r"dbt",
            r"excel",
        ),
        "responsibility_patterns": (
            r"build dashboards",
            r"define metrics",
            r"analyze business performance",
            r"support decision making",
        ),
    },
    "backend_engineering": {
        "role_family_id": "backend_engineering",
        "display_name": "Backend Engineering",
        "title_include_patterns": (
            r"backend engineer",
            r"backend.*engineer",
            r"back end engineer",
            r"back end.*engineer",
            r"api engineer",
            r"server engineer",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"api design",
            r"distributed systems",
            r"microservices",
            r"database design",
        ),
        "tooling_patterns": (
            r"python",
            r"java",
            r"go\b",
            r"node\.?js",
            r"postgres",
        ),
        "responsibility_patterns": (
            r"build backend services",
            r"design apis",
            r"scale services",
            r"maintain service reliability",
        ),
    },
    "frontend_engineering": {
        "role_family_id": "frontend_engineering",
        "display_name": "Frontend Engineering",
        "title_include_patterns": (
            r"frontend engineer",
            r"frontend.*engineer",
            r"front end engineer",
            r"front end.*engineer",
            r"ui engineer",
            r"web engineer",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"frontend",
            r"accessibility",
            r"responsive design",
            r"component architecture",
        ),
        "tooling_patterns": (
            r"javascript",
            r"typescript",
            r"react",
            r"vue",
            r"css",
        ),
        "responsibility_patterns": (
            r"build user interfaces",
            r"implement design systems",
            r"improve frontend performance",
            r"ship web experiences",
        ),
    },
    "fullstack_engineering": {
        "role_family_id": "fullstack_engineering",
        "display_name": "Full-Stack Engineering",
        "title_include_patterns": (
            r"full stack engineer",
            r"full stack.*engineer",
            r"full-stack engineer",
            r"full-stack.*engineer",
            r"fullstack engineer",
            r"fullstack.*engineer",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"full stack",
            r"frontend",
            r"backend",
            r"api",
        ),
        "tooling_patterns": (
            r"typescript",
            r"react",
            r"node\.?js",
            r"python",
            r"postgres",
        ),
        "responsibility_patterns": (
            r"build end-to-end features",
            r"own full stack development",
            r"deliver user-facing features",
        ),
    },
    "software_engineering": {
        "role_family_id": "software_engineering",
        "display_name": "Software Engineering",
        "title_include_patterns": (
            r"software engineer",
            r"software developer",
            r"application developer",
            r"platform engineer",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"software development",
            r"system design",
            r"object oriented",
            r"code quality",
        ),
        "tooling_patterns": (
            r"git",
            r"python",
            r"java",
            r"c\+\+",
            r"go\b",
        ),
        "responsibility_patterns": (
            r"design software systems",
            r"build application features",
            r"write maintainable code",
            r"deliver reliable software",
        ),
    },
    "cloud_devops": {
        "role_family_id": "cloud_devops",
        "display_name": "Cloud / DevOps",
        "title_include_patterns": (
            r"devops engineer",
            r"cloud engineer",
            r"infrastructure engineer",
            r"platform operations engineer",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"ci/cd",
            r"infrastructure as code",
            r"containerization",
            r"cloud infrastructure",
        ),
        "tooling_patterns": (
            r"aws",
            r"azure",
            r"gcp",
            r"terraform",
            r"kubernetes",
        ),
        "responsibility_patterns": (
            r"manage cloud infrastructure",
            r"automate deployments",
            r"build ci/cd pipelines",
            r"operate platform services",
        ),
    },
    "sre": {
        "role_family_id": "sre",
        "display_name": "Site Reliability Engineering",
        "title_include_patterns": (
            r"site reliability engineer",
            r"\bsre\b",
            r"reliability engineer",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"observability",
            r"incident response",
            r"service reliability",
            r"capacity planning",
        ),
        "tooling_patterns": (
            r"prometheus",
            r"grafana",
            r"datadog",
            r"kubernetes",
            r"terraform",
        ),
        "responsibility_patterns": (
            r"improve reliability",
            r"respond to incidents",
            r"define slos",
            r"operate production systems",
        ),
    },
    "qa_automation": {
        "role_family_id": "qa_automation",
        "display_name": "QA Automation",
        "title_include_patterns": (
            r"qa automation engineer",
            r"quality automation engineer",
            r"test automation engineer",
            r"software development engineer in test",
            r"\bsdet\b",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"test automation",
            r"quality assurance",
            r"regression testing",
            r"test strategy",
        ),
        "tooling_patterns": (
            r"selenium",
            r"playwright",
            r"cypress",
            r"pytest",
            r"junit",
        ),
        "responsibility_patterns": (
            r"build automated tests",
            r"maintain test frameworks",
            r"improve quality coverage",
            r"validate releases",
        ),
    },
    "security": {
        "role_family_id": "security",
        "display_name": "Security Engineering",
        "title_include_patterns": (
            r"security engineer",
            r"application security engineer",
            r"cloud security engineer",
            r"security analyst",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"threat modeling",
            r"vulnerability management",
            r"incident response",
            r"identity and access",
        ),
        "tooling_patterns": (
            r"siem",
            r"iam",
            r"aws security",
            r"okta",
            r"splunk",
        ),
        "responsibility_patterns": (
            r"secure systems",
            r"perform security reviews",
            r"detect threats",
            r"manage vulnerabilities",
        ),
    },
    "systems_it": {
        "role_family_id": "systems_it",
        "display_name": "Systems / IT",
        "title_include_patterns": (
            r"systems engineer",
            r"it engineer",
            r"systems administrator",
            r"network engineer",
            r"desktop engineer",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"systems administration",
            r"networking",
            r"endpoint management",
            r"identity management",
        ),
        "tooling_patterns": (
            r"linux",
            r"windows",
            r"active directory",
            r"jamf",
            r"intune",
        ),
        "responsibility_patterns": (
            r"administer systems",
            r"support endpoints",
            r"manage networks",
            r"resolve it issues",
        ),
    },
    "solutions_engineering": {
        "role_family_id": "solutions_engineering",
        "display_name": "Solutions Engineering",
        "title_include_patterns": (
            r"solutions engineer",
            r"solution engineer",
            r"sales engineer",
            r"customer engineer",
            r"solutions consultant",
        ),
        "title_exclude_patterns": COMMON_TITLE_EXCLUDE_PATTERNS,
        "skill_patterns": (
            r"technical discovery",
            r"proof of concept",
            r"customer integration",
            r"technical sales",
        ),
        "tooling_patterns": (
            r"api",
            r"sql",
            r"python",
            r"crm",
            r"salesforce",
        ),
        "responsibility_patterns": (
            r"support technical sales",
            r"build proof of concept",
            r"advise customers",
            r"design customer solutions",
        ),
    },
}


def _normalize_role_family_ids(role_family_ids: Iterable[str] | None) -> Tuple[str, ...]:
    if role_family_ids is None:
        return DEFAULT_ROLE_FAMILY_IDS

    normalized: List[str] = []
    for role_family_id in role_family_ids:
        value = str(role_family_id or "").strip()
        if not value:
            continue
        if value not in normalized:
            normalized.append(value)

    return tuple(normalized)


def _merge_patterns(role_family_ids: Iterable[str] | None, field_name: str) -> Tuple[str, ...]:
    patterns: List[str] = []
    for role_family_id in _normalize_role_family_ids(role_family_ids):
        family = get_role_family(role_family_id)
        for pattern in family[field_name]:
            if pattern not in patterns:
                patterns.append(pattern)
    return tuple(patterns)


def get_role_family(role_family_id: str) -> Dict[str, Any]:
    normalized = str(role_family_id or "").strip()
    if normalized not in ROLE_TAXONOMY:
        allowed = ", ".join(sorted(ROLE_TAXONOMY))
        raise KeyError(f"Unknown role family id={role_family_id!r}. Allowed: {allowed}")
    return ROLE_TAXONOMY[normalized]


def get_default_role_families() -> Tuple[Dict[str, Any], ...]:
    return tuple(get_role_family(role_family_id) for role_family_id in DEFAULT_ROLE_FAMILY_IDS)


def get_title_include_patterns(role_family_ids: Iterable[str] | None = None) -> Tuple[str, ...]:
    return _merge_patterns(role_family_ids, "title_include_patterns")


def get_title_exclude_patterns(role_family_ids: Iterable[str] | None = None) -> Tuple[str, ...]:
    return _merge_patterns(role_family_ids, "title_exclude_patterns")


def compile_role_title_regexes(
    role_family_ids: Iterable[str] | None = None,
) -> Tuple[Tuple[Pattern[str], ...], Tuple[Pattern[str], ...]]:
    include_regexes = tuple(
        re.compile(pattern, re.I)
        for pattern in get_title_include_patterns(role_family_ids)
    )
    exclude_regexes = tuple(
        re.compile(pattern, re.I)
        for pattern in get_title_exclude_patterns(role_family_ids)
    )
    return include_regexes, exclude_regexes
