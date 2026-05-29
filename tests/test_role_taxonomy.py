import re

from src.config.role_taxonomy import (
    DEFAULT_ROLE_FAMILY_IDS,
    ROLE_TAXONOMY,
    compile_role_title_regexes,
    get_default_role_families,
    get_role_family,
    get_title_exclude_patterns,
    get_title_include_patterns,
)


EXPECTED_ROLE_FAMILY_IDS = {
    "data_science",
    "ml_ai_engineering",
    "data_engineering",
    "analytics",
    "backend_engineering",
    "frontend_engineering",
    "fullstack_engineering",
    "software_engineering",
    "cloud_devops",
    "sre",
    "qa_automation",
    "security",
    "systems_it",
    "solutions_engineering",
}

REQUIRED_FIELDS = {
    "role_family_id",
    "display_name",
    "title_include_patterns",
    "title_exclude_patterns",
    "skill_patterns",
    "tooling_patterns",
    "responsibility_patterns",
}

CURRENT_DATA_AI_TITLE_PATTERNS = (
    r"data scientist",
    r"machine learning engineer",
    r"\bml engineer\b",
    r"ai engineer",
    r"applied scientist",
    r"research scientist",
    r"data analyst",
    r"decision scientist",
    r"ml scientist",
    r"analytics engineer",
    r"deep learning engineer",
    r"nlp engineer",
    r"\bgenai\b",
)


def test_role_taxonomy_loads_all_expected_it_families():
    assert set(ROLE_TAXONOMY) == EXPECTED_ROLE_FAMILY_IDS

    for role_family_id, family in ROLE_TAXONOMY.items():
        assert set(family) == REQUIRED_FIELDS
        assert family["role_family_id"] == role_family_id
        assert family["display_name"]

        for field_name in REQUIRED_FIELDS - {"role_family_id", "display_name"}:
            assert isinstance(family[field_name], tuple)
            assert family[field_name]
            assert all(isinstance(pattern, str) and pattern for pattern in family[field_name])


def test_get_role_family_returns_canonical_family_and_rejects_unknown_id():
    family = get_role_family("data_science")

    assert family is ROLE_TAXONOMY["data_science"]
    assert family["display_name"] == "Data Science"

    try:
        get_role_family("not_a_family")
    except KeyError:
        pass
    else:
        raise AssertionError("Expected get_role_family to reject an unknown family id.")


def test_default_role_families_preserve_current_data_ai_title_scope():
    assert DEFAULT_ROLE_FAMILY_IDS == (
        "data_science",
        "ml_ai_engineering",
        "analytics",
    )

    defaults = get_default_role_families()
    assert tuple(family["role_family_id"] for family in defaults) == DEFAULT_ROLE_FAMILY_IDS

    default_include_patterns = get_title_include_patterns(DEFAULT_ROLE_FAMILY_IDS)
    for pattern in CURRENT_DATA_AI_TITLE_PATTERNS:
        assert pattern in default_include_patterns


def test_title_pattern_helpers_dedupe_and_compile_regexes():
    include_patterns = get_title_include_patterns(
        ["analytics", "analytics", "ml_ai_engineering"]
    )
    exclude_patterns = get_title_exclude_patterns(
        ["analytics", "ml_ai_engineering"]
    )

    assert include_patterns.count(r"analytics engineer") == 1
    assert exclude_patterns.count(r"\bdirector\b") == 1

    include_regexes, exclude_regexes = compile_role_title_regexes(["analytics"])

    assert all(isinstance(regex, re.Pattern) for regex in include_regexes)
    assert all(isinstance(regex, re.Pattern) for regex in exclude_regexes)
    assert any(regex.search("Senior Data Analyst") for regex in include_regexes)
    assert any(regex.search("Director of Analytics") for regex in exclude_regexes)
