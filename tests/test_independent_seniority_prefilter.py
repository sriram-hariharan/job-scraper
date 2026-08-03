import inspect
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

from src.agents.deterministic_prefilter_dedupe_authoritative_graph import (
    execute_authoritative_prefilter_dedupe_graph,
)
from src.config.role_taxonomy import (
    COMMON_TITLE_EXCLUDE_PATTERNS,
    DEFAULT_ROLE_FAMILY_IDS,
    ROLE_TAXONOMY,
)
from src.config.seniority_policy import (
    DEFAULT_PREFILTER_ELIGIBLE_SENIORITY_OUTCOMES,
    DEFAULT_PREFILTER_REJECTED_SENIORITY_OUTCOMES,
    SENIORITY_CLASSIFICATION_OUTCOMES,
    default_prefilter_seniority_is_eligible,
)
from src.pipeline.job_filter import filter_jobs, title_match_detail, title_matches
from src.pipeline.job_ranker import title_score


ALL_ROLE_FAMILIES = tuple(ROLE_TAXONOMY)

SENIORITY_EXCLUSION_PATTERNS = {
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\blead\b",
    r"\bmember of technical staff\b",
    r"\bmts\b",
    r"\bdirector\b",
    r"\bvp\b",
    r"\bvice president\b",
    r"\bhead of\b",
    r"\bmanager\b",
    r"\bintern\b",
    r"\bstudent\b",
}

EXPECTED_BUSINESS_EXCLUSIONS = (
    r"\brecruiter\b",
    r"\bsales\b",
    r"\bgtm\b",
    r"\baccount executive\b",
    r"\bproduct manager\b",
    r"\bproduct designer\b",
    r"\bmarketing\b",
    r"\bcustomer success\b",
    r"\bcustomer support\b",
    r"\bguest service\b",
    r"\bfinance\b",
    r"\blegal\b",
    r"\baccounting\b",
    r"\bgtm engineer\b",
    r"\bdeveloper evangelist\b",
    r"\bdeveloper relations\b",
    r"\bdeployment strategist\b",
    r"\bpartner development\b",
    r"\btrainer\b",
    r"\bcoach\b",
    r"\bcontent creator\b",
    r"\bcreative producer\b",
    r"\bvideo editor\b",
)


def test_common_exclusions_transfer_only_seniority_ownership():
    assert SENIORITY_EXCLUSION_PATTERNS.isdisjoint(COMMON_TITLE_EXCLUDE_PATTERNS)
    assert COMMON_TITLE_EXCLUDE_PATTERNS == EXPECTED_BUSINESS_EXCLUSIONS


def test_default_prefilter_outcome_partition_is_exact():
    assert DEFAULT_PREFILTER_ELIGIBLE_SENIORITY_OUTCOMES == (
        "entry",
        "mid",
        "senior",
        "unknown",
    )
    assert DEFAULT_PREFILTER_REJECTED_SENIORITY_OUTCOMES == (
        "intern",
        "staff",
        "manager_or_above",
    )
    assert set(DEFAULT_PREFILTER_ELIGIBLE_SENIORITY_OUTCOMES) | set(
        DEFAULT_PREFILTER_REJECTED_SENIORITY_OUTCOMES
    ) == set(SENIORITY_CLASSIFICATION_OUTCOMES)
    for outcome in DEFAULT_PREFILTER_ELIGIBLE_SENIORITY_OUTCOMES:
        assert default_prefilter_seniority_is_eligible(outcome) is True
    for outcome in DEFAULT_PREFILTER_REJECTED_SENIORITY_OUTCOMES:
        assert default_prefilter_seniority_is_eligible(outcome) is False


def test_existing_default_eligible_titles_remain_eligible():
    cases = (
        ("Junior Software Engineer", "software_engineering"),
        ("Software Engineer II", "software_engineering"),
        ("Senior Software Engineer", "software_engineering"),
        ("Software Engineer", "software_engineering"),
        ("Technical Product Manager", "technical_product_management"),
        ("Technical Program Manager", "technical_program_management"),
        ("Senior Technical Product Manager", "technical_product_management"),
        ("Senior Technical Program Manager", "technical_program_management"),
    )
    for title, family_id in cases:
        assert title_matches(title, [family_id]) is True


def test_existing_default_rejected_titles_remain_rejected():
    titles = (
        "Intern Software Engineer",
        "Student Software Engineer",
        "Staff Software Engineer",
        "Principal Data Scientist",
        "Lead Backend Engineer",
        "Member of Technical Staff",
        "MTS Engineer",
        "Director of Engineering",
        "VP Engineering",
        "Vice President of Engineering",
        "Head of Engineering",
        "Engineering Manager",
        "Senior Engineering Manager",
        "Staff Technical Product Manager",
        "Principal Technical Product Manager",
        "Lead Technical Program Manager",
        "Director of Technical Program Management",
    )
    for title in titles:
        assert title_matches(title, ALL_ROLE_FAMILIES) is False


def test_seniority_rejection_retains_family_pattern_reason_and_order_independence():
    first = title_match_detail(
        "Staff Technical Product Manager, Platform Engineer",
        ["technical_product_management", "software_engineering"],
    )
    reversed_input = title_match_detail(
        "Staff Technical Product Manager, Platform Engineer",
        ["software_engineering", "technical_product_management"],
    )
    assert first == reversed_input
    assert first["matched"] is False
    assert first["reason"] == "exclude_pattern_match"
    assert first["matched_role_family"] == "software_engineering"
    assert first["matched_pattern"]


def test_title_score_keeps_central_filter_parity():
    assert title_score("Backend Engineer", ["backend_engineering"]) == 25
    assert title_score("Staff Backend Engineer", ["backend_engineering"]) == -100
    assert title_score("Account Executive", ["backend_engineering"]) == 0


def test_target_seniority_remains_outside_filter_and_graph_contracts():
    assert "target_seniority" not in inspect.signature(filter_jobs).parameters
    assert "target_seniority" not in inspect.signature(
        execute_authoritative_prefilter_dedupe_graph
    ).parameters


def test_role_family_ids_and_defaults_are_unchanged():
    assert tuple(ROLE_TAXONOMY) == (
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
    assert DEFAULT_ROLE_FAMILY_IDS == (
        "data_science",
        "ml_ai_engineering",
        "analytics",
    )
