from src.config.role_scoring_profiles import (
    ROLE_SCORING_PROFILES,
    get_default_scoring_profile,
    get_role_scoring_dimensions,
    get_role_scoring_profile,
)
from src.config.role_taxonomy import ROLE_TAXONOMY


def _profile_terms(role_family_id):
    profile = get_role_scoring_profile(role_family_id)
    values = []
    values.extend(profile["dimensions"])
    values.extend(profile["dimension_weights"].keys())
    values.extend(profile["signal_families"])
    for group_values in profile["skill_groups"].values():
        values.extend(group_values)
    return " ".join(values).lower()


def test_role_scoring_profiles_cover_role_taxonomy_and_have_valid_weights():
    assert set(ROLE_SCORING_PROFILES) == set(ROLE_TAXONOMY)

    for role_family_id in ROLE_TAXONOMY:
        profile = get_role_scoring_profile(role_family_id)
        assert profile["role_family_id"] == role_family_id
        assert profile["display_name"] == ROLE_TAXONOMY[role_family_id]["display_name"]
        assert profile["dimensions"]
        assert set(profile["dimensions"]) == set(profile["dimension_weights"])
        assert round(sum(profile["dimension_weights"].values()), 6) == 1.0
        assert profile["signal_families"]
        assert profile["skill_groups"]


def test_backend_profile_includes_api_backend_system_dimensions():
    terms = _profile_terms("backend_engineering")
    assert "api" in terms
    assert "backend" in terms
    assert "system" in terms


def test_frontend_profile_includes_ui_frontend_dimensions():
    terms = _profile_terms("frontend_engineering")
    assert "ui" in terms
    assert "frontend" in terms
    assert "component" in terms


def test_devops_and_sre_profiles_include_cloud_infra_reliability_dimensions():
    devops_terms = _profile_terms("cloud_devops")
    sre_terms = _profile_terms("sre")

    assert "cloud" in devops_terms
    assert "infra" in devops_terms
    assert "ci/cd" in devops_terms
    assert "reliability" in sre_terms
    assert "observability" in sre_terms
    assert "incident" in sre_terms


def test_qa_profile_includes_automation_testing_dimensions():
    terms = _profile_terms("qa_automation")
    assert "automation" in terms
    assert "testing" in terms
    assert "quality" in terms


def test_security_profile_includes_security_iam_vulnerability_dimensions():
    terms = _profile_terms("security")
    assert "security" in terms
    assert "iam" in terms
    assert "vulnerability" in terms


def test_data_science_profile_preserves_ml_statistics_sql_style_dimensions():
    terms = _profile_terms("data_science")
    default_profile = get_default_scoring_profile()

    assert default_profile["role_family_id"] == "data_science"
    assert "machine_learning" in terms or "machine learning" in terms
    assert "statistics" in terms
    assert "sql" in terms
    assert default_profile["dimension_weights"]["analytics_ml_depth"] == 0.13
    assert default_profile["dimension_weights"]["experimentation_depth"] == 0.07


def test_role_scoring_dimensions_helper_returns_ordered_dimensions():
    dimensions = get_role_scoring_dimensions("backend_engineering")

    assert dimensions[0] == "title_alignment"
    assert "tooling_alignment" in dimensions


def test_unknown_role_scoring_profile_rejects_deterministically():
    try:
        get_role_scoring_profile("unknown_role")
    except KeyError as exc:
        assert "Unknown role scoring profile id" in str(exc)
    else:
        raise AssertionError("unknown role scoring profile should be rejected")
