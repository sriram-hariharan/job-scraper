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
from src.pipeline.job_filter import title_matches
from src.pipeline.job_ranker import rank_jobs, title_score


ALL_SELECTED_ROLE_FAMILIES = [
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
]


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


def test_role_expansion_title_permutations_match_selected_families():
    cases = [
        ("Backend Software Engineer", ["backend_engineering"]),
        ("Software Engineer, Backend", ["backend_engineering"]),
        ("Software Engineer II", ["software_engineering"]),
        ("Member of Technical Staff", ["software_engineering"]),
        ("AI Platform Engineer", ["ml_ai_engineering"]),
        ("Machine Learning Infrastructure Engineer", ["ml_ai_engineering"]),
        ("Data Platform Engineer", ["data_engineering"]),
        ("Cloud Infrastructure Engineer", ["cloud_devops"]),
        ("Application Security Engineer", ["security"]),
        ("QA Engineer, Automation", ["qa_automation"]),
    ]

    for title, selected_role_families in cases:
        assert title_matches(title, selected_role_families=selected_role_families) is True


def test_role_expansion_avoids_manager_and_generic_architect_overmatching():
    for title in (
        "Engineering Manager",
        "Product Manager",
        "Sales Manager",
        "Principal Architect",
    ):
        assert title_matches(title, selected_role_families=ALL_SELECTED_ROLE_FAMILIES) is False


def test_all_selected_role_families_match_representative_it_titles():
    representative_titles = [
        "Software Engineer II",
        "Backend Software Engineer",
        "Frontend Software Engineer",
        "Full Stack Software Engineer",
        "Machine Learning Infrastructure Engineer",
        "Data Platform Engineer",
        "Business Intelligence Engineer",
        "Cloud Infrastructure Engineer",
        "Site Reliability Engineer",
        "Application Security Engineer",
        "QA Engineer, Automation",
        "Systems Administrator",
        "Solutions Architect",
    ]

    for title in representative_titles:
        assert title_matches(title, selected_role_families=ALL_SELECTED_ROLE_FAMILIES) is True


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
