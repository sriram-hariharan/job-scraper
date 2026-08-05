from __future__ import annotations

import pytest

from src.config.seniority_policy import (
    classify_title_seniority,
    normalize_seniority_filter_preferences,
    seniority_prefilter_decision,
)
from src.pipeline.job_filter import build_role_title_filter_audit_row, title_match_detail


@pytest.mark.parametrize(
    "outcome",
    ["entry", "mid", "senior", "staff", "unknown"],
)
def test_flexible_policy_allows_public_and_unknown_outcomes(outcome):
    decision = seniority_prefilter_decision(outcome)
    assert decision == {
        "eligible": True,
        "decision": "allow",
        "reason": "flexible_level_allowed",
    }


@pytest.mark.parametrize(
    ("outcome", "reason"),
    [("intern", "intern_rejected"), ("manager_or_above", "manager_or_above_rejected")],
)
def test_intern_and_management_reject_in_both_modes(outcome, reason):
    assert seniority_prefilter_decision(outcome)["reason"] == reason
    assert seniority_prefilter_decision(
        outcome,
        target_seniority=["senior"],
        seniority_strict_match=True,
    ) == {"eligible": False, "decision": "reject", "reason": reason}


def test_strict_policy_matches_only_canonical_selected_public_levels():
    assert seniority_prefilter_decision(
        "staff",
        target_seniority=["staff_or_above"],
        seniority_strict_match=True,
    )["reason"] == "strict_selected_level_match"
    assert seniority_prefilter_decision(
        "senior",
        target_seniority=["staff"],
        seniority_strict_match=True,
    )["reason"] == "strict_selected_level_mismatch"
    assert seniority_prefilter_decision(
        "unknown",
        target_seniority=["senior"],
        seniority_strict_match=True,
    )["reason"] == "strict_unknown_rejected"


def test_strict_preference_validation_requires_a_boolean_and_target():
    assert normalize_seniority_filter_preferences([], False) == ([], False)
    assert normalize_seniority_filter_preferences(["staff_or_above"], True) == (
        ["staff"],
        True,
    )
    with pytest.raises(ValueError, match="must be a boolean"):
        normalize_seniority_filter_preferences(["senior"], "true")
    with pytest.raises(ValueError, match="at least one value"):
        normalize_seniority_filter_preferences([], True)


@pytest.mark.parametrize(
    "title",
    [
        "Staff Software Engineer",
        "Principal Data Scientist",
        "Lead Backend Engineer",
        "Member of Technical Staff",
        "MTS Engineer",
    ],
)
def test_staff_family_titles_classify_as_staff_and_pass_flexible(title):
    assert classify_title_seniority(title) == "staff"
    assert title_match_detail(
        title,
        selected_role_families=[
            "data_science",
            "backend_engineering",
            "software_engineering",
        ],
    )["matched"] is True


def test_central_title_decision_is_strict_and_auditable():
    matched = title_match_detail(
        "Senior Software Engineer",
        selected_role_families=["software_engineering"],
        target_seniority=["senior"],
        seniority_strict_match=True,
    )
    assert matched["matched"] is True
    assert matched["classified_seniority"] == "senior"
    assert matched["seniority_reason"] == "strict_selected_level_match"

    mismatch = title_match_detail(
        "Staff Software Engineer",
        selected_role_families=["software_engineering"],
        target_seniority=["senior"],
        seniority_strict_match=True,
    )
    assert mismatch["matched"] is False
    assert mismatch["reason"] == "exclude_pattern_match"
    assert mismatch["seniority_reason"] == "strict_selected_level_mismatch"

    unknown = title_match_detail(
        "Software Engineer",
        selected_role_families=["software_engineering"],
        target_seniority=["senior"],
        seniority_strict_match=True,
    )
    assert unknown["matched"] is False
    assert unknown["seniority_reason"] == "strict_unknown_rejected"


@pytest.mark.parametrize(
    ("title", "target", "expected", "reason"),
    [
        ("Senior Technical Product Manager", "senior", True, "strict_selected_level_match"),
        ("Staff Technical Product Manager", "staff", True, "strict_selected_level_match"),
        ("Technical Program Manager", "senior", False, "strict_unknown_rejected"),
        ("Director Technical Program Manager", "staff", False, "manager_or_above_rejected"),
    ],
)
def test_technical_management_context_uses_shared_classifier(title, target, expected, reason):
    detail = title_match_detail(
        title,
        selected_role_families=[
            "technical_product_management",
            "technical_program_management",
        ],
        target_seniority=[target],
        seniority_strict_match=True,
    )
    assert detail["matched"] is expected
    assert detail["seniority_reason"] == reason


def test_seniority_is_not_evaluated_when_role_family_does_not_match():
    detail = title_match_detail(
        "Senior Accountant",
        target_seniority=["senior"],
        seniority_strict_match=True,
    )
    assert detail["matched"] is False
    assert detail["seniority_reason"] == "not_evaluated"
    assert detail["classified_seniority"] == ""


def test_audit_row_contains_deterministic_strict_seniority_details():
    row = build_role_title_filter_audit_row(
        {"title": "Staff Software Engineer", "company": "Acme"},
        selected_role_families=["software_engineering"],
        target_seniority=["senior"],
        seniority_strict_match=True,
    )
    assert row["classified_seniority"] == "staff"
    assert row["seniority_strict_match"] is True
    assert row["target_seniority"] == "senior"
    assert row["seniority_decision"] == "reject"
    assert row["seniority_reason"] == "strict_selected_level_mismatch"
    assert row["title_filter_reason"] == "exclude_pattern_match"
