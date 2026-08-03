from src.config.role_scoring_profiles import ROLE_SCORING_PROFILES
from src.config.role_taxonomy import DEFAULT_ROLE_FAMILY_IDS, ROLE_TAXONOMY
from src.intelligence.role_family_classifier import (
    SKILL_ROLE_PRIORITY,
    TITLE_ROLE_PRIORITY,
    classify_role_family,
)
from src.pipeline.job_filter import (
    build_role_title_filter_audit_row,
    title_matches,
)


EXPECTED_ROLE_FAMILY_IDS = (
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
    "technical_product_management",
    "technical_program_management",
)

APPROVED_TITLE_ALIASES = (
    ("Mobile Engineer", "software_engineering"),
    ("Mobile Software Engineer", "software_engineering"),
    ("Mobile Developer", "software_engineering"),
    ("iOS Engineer", "software_engineering"),
    ("iOS Developer", "software_engineering"),
    ("Android Engineer", "software_engineering"),
    ("Android Developer", "software_engineering"),
    ("Database Engineer", "data_engineering"),
    ("Implementation Engineer", "solutions_engineering"),
    ("Technical Support Engineer", "systems_it"),
)


def test_approved_aliases_match_only_their_existing_family():
    for title, family_id in APPROVED_TITLE_ALIASES:
        assert title_matches(title, selected_role_families=[family_id]) is True
        assert title_matches(title, selected_role_families=["security"]) is False


def test_existing_data_ai_default_remains_unchanged():
    assert DEFAULT_ROLE_FAMILY_IDS == (
        "data_science",
        "ml_ai_engineering",
        "analytics",
    )
    assert title_matches("Data Scientist") is True
    for title, _family_id in APPROVED_TITLE_ALIASES:
        assert title_matches(title) is False


def test_role_family_ids_and_registry_coverage_remain_exact():
    assert tuple(ROLE_TAXONOMY) == EXPECTED_ROLE_FAMILY_IDS
    assert tuple(ROLE_SCORING_PROFILES) == EXPECTED_ROLE_FAMILY_IDS
    assert set(TITLE_ROLE_PRIORITY) == set(EXPECTED_ROLE_FAMILY_IDS)
    assert set(SKILL_ROLE_PRIORITY) == set(EXPECTED_ROLE_FAMILY_IDS)


def test_classifier_uses_existing_family_ids_for_approved_aliases():
    for title, family_id in APPROVED_TITLE_ALIASES:
        assert classify_role_family({"title": title}) == family_id


def test_required_business_and_nonengineering_negatives_remain_rejected():
    titles = (
        "Mobile Sales Representative",
        "Mobile Technician",
        "Database Sales Specialist",
        "Implementation Consultant",
        "Implementation Coordinator",
        "Implementation Specialist",
        "Implementation Project Manager",
        "Customer Support Representative",
        "Customer Success Manager",
        "Technical Account Manager",
        "Help Desk Representative",
        "Call Center Representative",
        "Guest Service Representative",
        "Product Manager",
        "Program Manager",
        "Engineering Manager",
    )

    for title in titles:
        assert title_matches(
            title,
            selected_role_families=EXPECTED_ROLE_FAMILY_IDS,
        ) is False


def test_existing_seniority_exclusions_remain_unchanged_for_aliases():
    titles = (
        "Staff Mobile Engineer",
        "Principal Database Engineer",
        "Lead Implementation Engineer",
        "Manager, Technical Support Engineer",
        "Director, Mobile Engineer",
        "VP, Database Engineer",
        "Mobile Engineer Intern",
    )

    for title in titles:
        assert title_matches(
            title,
            selected_role_families=EXPECTED_ROLE_FAMILY_IDS,
        ) is False


def test_audit_rows_report_deterministic_alias_family_and_pattern():
    expected = (
        ("Mobile Engineer", "software_engineering", "mobile"),
        ("Database Engineer", "data_engineering", "database engineer"),
        ("Implementation Engineer", "solutions_engineering", "implementation engineer"),
        ("Technical Support Engineer", "systems_it", "technical support engineer"),
    )

    for title, family_id, pattern_fragment in expected:
        row = build_role_title_filter_audit_row(
            {"title": title},
            selected_role_families=[family_id],
        )
        assert row["title_filter_decision"] == "pass"
        assert row["title_filter_reason"] == "include_pattern_match"
        assert row["matched_role_family"] == family_id
        assert pattern_fragment in row["matched_pattern"]
