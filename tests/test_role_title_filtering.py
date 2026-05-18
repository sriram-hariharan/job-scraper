import sys
import types

sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))
sys.modules.setdefault(
    "src.utils.workday_timestamp",
    types.SimpleNamespace(fetch_workday_timestamp=lambda *args, **kwargs: None),
)
sys.modules.setdefault(
    "src.scrapers.ashby_scraper",
    types.SimpleNamespace(fetch_ashby_timestamp=lambda *args, **kwargs: None),
)

from src.pipeline.job_filter import title_matches
from src.pipeline.job_ranker import rank_jobs, title_score


def test_default_title_filter_keeps_existing_data_ai_behavior():
    assert title_matches("Senior Data Scientist") is True
    assert title_matches("Backend Engineer") is False
    assert title_matches("Backend Engineer", selected_role_families=[]) is False


def test_selected_role_families_expand_title_filtering():
    assert title_matches(
        "Backend Engineer",
        selected_role_families=["backend_engineering"],
    ) is True
    assert title_matches(
        "QA Automation Engineer",
        selected_role_families=["qa_automation"],
    ) is True
    assert title_matches(
        "Backend Engineer",
        selected_role_families=["data_science"],
    ) is False


def test_selected_role_family_title_score_is_positive_only_for_matching_titles():
    assert title_score(
        "Backend Engineer",
        selected_role_families=["backend_engineering"],
    ) > 0
    assert title_score(
        "Backend Engineer",
        selected_role_families=["data_science"],
    ) <= 0


def test_default_ranker_still_scores_data_ai_titles():
    ranked = rank_jobs(
        [
            {"title": "Backend Engineer", "company": "Acme", "posted_at": None},
            {"title": "Data Scientist", "company": "Acme", "posted_at": None},
        ],
        momentum_map={},
    )

    assert ranked[0]["title"] == "Data Scientist"
    assert ranked[0]["_score"] > ranked[1]["_score"]


def test_selected_role_family_ranker_scores_selected_role():
    ranked = rank_jobs(
        [
            {"title": "Data Scientist", "company": "Acme", "posted_at": None},
            {"title": "Backend Engineer", "company": "Acme", "posted_at": None},
        ],
        momentum_map={},
        selected_role_families=["backend_engineering"],
    )

    assert ranked[0]["title"] == "Backend Engineer"
    assert ranked[0]["_score"] > ranked[1]["_score"]
