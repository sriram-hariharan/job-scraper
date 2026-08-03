import sys
import types


class _FakeTqdm:
    def __call__(self, iterable=None, **kwargs):
        return iterable

    @staticmethod
    def write(*args, **kwargs):
        return None


sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))
sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=_FakeTqdm()))
sys.modules.setdefault(
    "src.utils.workday_timestamp",
    types.SimpleNamespace(fetch_workday_timestamp=lambda *args, **kwargs: None),
)

from src.app.onboarding_ui import (
    ROLE_FAMILY_ICON_SVGS,
    _ROLE_FAMILY_SUBTITLE_LABELS,
    _role_family_cards_html,
)
from src.config.role_scoring_profiles import ROLE_SCORING_PROFILES
from src.config.role_taxonomy import DEFAULT_ROLE_FAMILY_IDS, ROLE_TAXONOMY
from src.config.seniority_policy import classify_title_seniority
from src.intelligence.role_family_classifier import (
    SKILL_ROLE_PRIORITY,
    TITLE_ROLE_PRIORITY,
    classify_role_family,
)
from src.pipeline.job_filter import (
    build_role_title_filter_audit_row,
    title_match_detail,
    title_matches,
)
from src.pipeline.job_ranker import title_score


EXISTING_ROLE_FAMILY_IDS = (
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
)
NEW_ROLE_FAMILY_IDS = (
    "technical_product_management",
    "technical_program_management",
)

PRODUCT_TITLES = (
    "Technical Product Manager",
    "Senior Technical Product Manager",
    "Product Manager, Platform",
    "Product Manager, Developer Experience",
    "Product Manager, Developer Platform",
    "Product Manager, API",
    "Product Manager, APIs",
    "Product Manager, Infrastructure",
    "Product Manager, Data Platform",
    "Product Manager, AI Platform",
    "Technical-Product Manager",
)

PROGRAM_TITLES = (
    "Technical Program Manager",
    "Senior Technical Program Manager",
    "Technical Program Manager, Infrastructure",
    "Technical Program Manager, Security",
    "Technical Program Manager, Data",
    "Technical Program Manager, Cloud",
    "Technical Program Manager, Engineering",
    "Technical-Program Manager",
)


def test_new_role_family_ids_append_without_changing_existing_order_or_defaults():
    assert tuple(ROLE_TAXONOMY) == EXISTING_ROLE_FAMILY_IDS + NEW_ROLE_FAMILY_IDS
    assert DEFAULT_ROLE_FAMILY_IDS == (
        "data_science",
        "ml_ai_engineering",
        "analytics",
    )
    assert tuple(ROLE_SCORING_PROFILES) == tuple(ROLE_TAXONOMY)
    assert set(TITLE_ROLE_PRIORITY) == set(ROLE_TAXONOMY)
    assert set(SKILL_ROLE_PRIORITY) == set(ROLE_TAXONOMY)


def test_approved_product_titles_match_only_technical_product_management():
    for title in PRODUCT_TITLES:
        assert title_matches(title, ["technical_product_management"]) is True
        assert title_matches(title, ["technical_program_management"]) is False
        assert title_matches(title, EXISTING_ROLE_FAMILY_IDS) is False


def test_approved_program_titles_match_only_technical_program_management():
    for title in PROGRAM_TITLES:
        assert title_matches(title, ["technical_program_management"]) is True
        assert title_matches(title, ["technical_product_management"]) is False
        assert title_matches(title, EXISTING_ROLE_FAMILY_IDS) is False


def test_generic_and_nonapproved_management_titles_remain_rejected():
    product_negatives = (
        "Product Manager",
        "Product Manager, Data",
        "Product Manager, AI",
        "Associate Product Manager, Platform",
        "Marketing Product Manager, Platform",
        "Product Marketing Manager, Platform",
        "Customer Product Manager, Platform",
        "Sales Product Manager, Platform",
        "Engineering Manager",
        "Technical Account Manager",
    )
    program_negatives = (
        "Program Manager",
        "Project Manager",
        "Implementation Project Manager",
        "Sales Program Manager",
        "Customer Success Program Manager",
        "Engineering Manager",
        "Technical Account Manager",
    )

    for title in product_negatives:
        assert title_matches(title, ["technical_product_management"]) is False
    for title in program_negatives:
        assert title_matches(title, ["technical_program_management"]) is False


def test_staff_seniority_policy_applies_to_technical_management_families():
    staff_cases = (
        ("Staff Technical Product Manager", "technical_product_management"),
        ("Principal Technical Product Manager", "technical_product_management"),
        ("Lead Technical Program Manager", "technical_program_management"),
    )
    for title, role_family_id in staff_cases:
        assert classify_title_seniority(
            title,
            technical_management_role=True,
        ) == "staff"
        assert title_matches(title, [role_family_id]) is True
        assert title_matches(
            title,
            [role_family_id],
            target_seniority=["staff"],
            seniority_strict_match=True,
        ) is True
        assert title_matches(
            title,
            [role_family_id],
            target_seniority=["senior"],
            seniority_strict_match=True,
        ) is False

    director = "Director of Technical Program Management"
    assert classify_title_seniority(
        director,
        technical_management_role=True,
    ) == "manager_or_above"
    assert title_matches(director, ["technical_program_management"]) is False


def test_multifamily_matching_is_canonical_ordered_and_exclusions_are_family_specific():
    title = "Technical Product Manager, Platform Engineer"
    first = title_match_detail(
        title,
        ["technical_product_management", "software_engineering"],
    )
    reversed_input = title_match_detail(
        title,
        ["software_engineering", "technical_product_management"],
    )

    assert first == reversed_input
    assert first["matched"] is True
    assert first["matched_role_family"] == "technical_product_management"

    canonical_winner = title_match_detail(
        "Backend Software Engineer",
        ["software_engineering", "backend_engineering"],
    )
    assert canonical_winner["matched_role_family"] == "backend_engineering"

    flexible_staff = title_match_detail(
        "Staff Technical Product Manager, Platform Engineer",
        ["technical_product_management", "software_engineering"],
    )
    assert flexible_staff["matched"] is True
    assert flexible_staff["matched_role_family"] == "technical_product_management"
    assert flexible_staff["classified_seniority"] == "staff"
    assert flexible_staff["seniority_reason"] == "flexible_level_allowed"

    strict_senior = title_match_detail(
        "Staff Technical Product Manager, Platform Engineer",
        ["technical_product_management", "software_engineering"],
        target_seniority=["senior"],
        seniority_strict_match=True,
    )
    assert strict_senior["matched"] is False
    assert strict_senior["reason"] == "exclude_pattern_match"
    assert strict_senior["seniority_reason"] == "strict_selected_level_mismatch"


def test_title_ranking_uses_the_same_matched_family_decision():
    selected = ["software_engineering", "technical_product_management"]
    assert title_matches("Technical Product Manager, Platform Engineer", selected) is True
    assert title_score("Technical Product Manager, Platform Engineer", selected) == 25
    assert title_score("Staff Technical Product Manager", ["technical_product_management"]) == 25
    assert title_score("Product Manager", ["technical_product_management"]) == 0
    assert title_score("", selected) == 0

    existing_cases = (
        ("Backend Engineer", "backend_engineering", 25),
        ("Staff Backend Engineer", "backend_engineering", 25),
        ("Account Executive", "backend_engineering", 0),
    )
    for title, role_family_id, expected_score in existing_cases:
        assert title_score(title, [role_family_id]) == expected_score


def test_audit_records_exact_family_pattern_reason_and_new_family_hints():
    accepted = build_role_title_filter_audit_row(
        {"title": "Product Manager, API"},
        ["technical_product_management"],
    )
    assert accepted["title_filter_decision"] == "pass"
    assert accepted["title_filter_reason"] == "include_pattern_match"
    assert accepted["matched_role_family"] == "technical_product_management"
    assert "product manager" in accepted["matched_pattern"]

    for title, family_id in (
        ("Product Manager", "technical_product_management"),
        ("Program Manager", "technical_program_management"),
    ):
        rejected = build_role_title_filter_audit_row({"title": title}, [family_id])
        assert rejected["title_filter_reason"] == "no_include_pattern_match"
        assert rejected["suspected_role_family_hint"] == family_id


def test_new_scoring_profiles_use_exact_weights_and_distinct_signals():
    expected_product_weights = (0.15, 0.15, 0.05, 0.15, 0.15, 0.15, 0.08, 0.04, 0.03, 0.05)
    expected_program_weights = (0.15, 0.15, 0.05, 0.20, 0.10, 0.15, 0.08, 0.02, 0.02, 0.08)
    product = ROLE_SCORING_PROFILES["technical_product_management"]
    program = ROLE_SCORING_PROFILES["technical_program_management"]

    assert tuple(product["dimension_weights"].values()) == expected_product_weights
    assert tuple(program["dimension_weights"].values()) == expected_program_weights
    assert round(sum(product["dimension_weights"].values()), 6) == 1.0
    assert round(sum(program["dimension_weights"].values()), 6) == 1.0
    assert product["signal_families"] != program["signal_families"]
    assert product["skill_groups"] != program["skill_groups"]


def test_classifier_uses_exact_titles_and_narrow_skill_fallbacks():
    assert classify_role_family({"title": "Technical Product Manager"}) == "technical_product_management"
    assert classify_role_family({"title": "Technical Program Manager"}) == "technical_program_management"
    assert classify_role_family({"title": "", "required_skills": ["technical product management"]}) == "technical_product_management"
    assert classify_role_family({"title": "", "required_skills": ["technical program management"]}) == "technical_program_management"
    assert classify_role_family({"title": "", "required_skills": ["product management"]}) == "other"
    assert classify_role_family({"title": "", "required_skills": ["project management"]}) == "other"
    assert classify_role_family({"title": "", "required_skills": ["pytorch", "product management"]}) == "ml_ai_engineering"


def test_onboarding_cards_have_explicit_subtitles_and_decorative_icons():
    cards = _role_family_cards_html()
    for role_family_id in NEW_ROLE_FAMILY_IDS:
        assert role_family_id in _ROLE_FAMILY_SUBTITLE_LABELS
        assert role_family_id in ROLE_FAMILY_ICON_SVGS
        assert 'class="onboarding-role-icon-svg"' in ROLE_FAMILY_ICON_SVGS[role_family_id]
        assert f'value="{role_family_id}"' in cards
