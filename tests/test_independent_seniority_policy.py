import sys
import types

import pytest


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

from src.config.seniority_policy import (
    PUBLIC_SENIORITY_IDS,
    SENIORITY_CLASSIFICATION_OUTCOMES,
    classify_title_seniority,
    normalize_target_seniority_ids,
)
from src.pipeline.job_filter import title_matches
from src.pipeline.job_ranker import classify_seniority, preference_score


def test_public_vocabulary_is_exact_ordered_and_legacy_alias_is_canonical():
    assert PUBLIC_SENIORITY_IDS == ("entry", "mid", "senior", "staff")
    assert normalize_target_seniority_ids(" Staff_Or_Above ") == ["staff"]
    assert normalize_target_seniority_ids(
        ["staff_or_above", " STAFF ", "senior", "Senior"]
    ) == ["staff", "senior"]


@pytest.mark.parametrize(
    "unsupported",
    (
        "sr",
        "principal",
        "lead",
        "manager",
        "manager_or_above",
        "intern",
        "executive",
        "arbitrary",
    ),
)
def test_unsupported_public_values_raise(unsupported):
    with pytest.raises(ValueError, match="Unsupported target seniority"):
        normalize_target_seniority_ids(unsupported)


def test_policy_classifier_returns_only_approved_internal_outcomes():
    cases = {
        "Software Engineering Intern": "intern",
        "Junior Software Engineer": "entry",
        "Software Engineer II": "mid",
        "Senior Software Engineer": "senior",
        "Principal Software Engineer": "staff",
        "Engineering Manager": "manager_or_above",
        "Software Engineer": "unknown",
    }
    for title, expected in cases.items():
        outcome = classify_title_seniority(title)
        assert outcome == expected
        assert outcome in SENIORITY_CLASSIFICATION_OUTCOMES


def test_compatibility_classifier_uses_central_technical_manager_context():
    cases = {
        "Technical Product Manager": "unknown",
        "Technical Program Manager": "unknown",
        "Senior Technical Product Manager": "senior",
        "Senior Technical Program Manager": "senior",
        "Staff Technical Product Manager": "staff",
        "Principal Technical Product Manager": "staff",
        "Lead Technical Program Manager": "staff",
        "Director of Technical Program Management": "manager_or_above",
        "Engineering Manager": "manager_or_above",
        "Senior Engineering Manager": "manager_or_above",
        "Data Science Manager": "manager_or_above",
    }
    for title, expected in cases.items():
        assert classify_seniority(title) == expected


def test_soft_ranking_aligns_staff_legacy_and_technical_manager_titles():
    cases = (
        ({"title": "Staff Engineer"}, ["staff"], "staff", True, 4),
        ({"title": "Staff Engineer"}, ["staff_or_above"], "staff", True, 4),
        ({"title": "Senior Technical Product Manager"}, ["senior"], "senior", True, 4),
        ({"title": "Engineering Manager"}, ["senior"], "manager_or_above", False, 0),
        ({"title": "Intern Engineer"}, ["entry"], "intern", False, 0),
        ({"title": "Software Engineer"}, ["senior"], "unknown", False, 0),
    )

    for job, target, outcome, matched, expected_score in cases:
        score = preference_score(job, target_seniority=target)
        assert score == expected_score
        assert job["_preference_seniority"] == outcome
        assert job["_preference_seniority_match"] is matched
        assert job["_preference_seniority_unknown"] is (outcome == "unknown")


def test_location_and_skill_bonuses_remain_additive_and_unchanged():
    job = {
        "title": "Senior Backend Engineer",
        "location": "New York, NY",
        "description": "Build Python services",
    }
    assert preference_score(
        job,
        target_seniority=["senior"],
        preferred_locations=["New York"],
        preferred_skills=["Python"],
    ) == 10


def test_phase_2d_a_does_not_change_filter_eligibility():
    selected = [
        "software_engineering",
        "technical_product_management",
        "technical_program_management",
    ]
    for title in (
        "Staff Software Engineer",
        "Principal Software Engineer",
        "Lead Software Engineer",
        "MTS, Software Engineer",
        "Software Engineer Intern",
        "Staff Technical Product Manager",
        "Lead Technical Program Manager",
    ):
        assert title_matches(title, selected) is False

    assert title_matches("Senior Technical Product Manager", selected) is True
