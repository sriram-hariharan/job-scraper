import asyncio

import pytest

from src.discovery import career_ats_detector
from src.discovery import discovery
from src.discovery import sitemap_fetcher
from src.discovery import save_companies


BOARD_URL = "https://acme.wd1.myworkdayjobs.com/External"
DEEP_URL = f"{BOARD_URL}/job/REQ123"


class _AsyncResponse:
    status = 200

    async def text(self):
        return f'<a href="{DEEP_URL}">role</a>'

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None


class _AsyncSession:
    def get(self, *_args, **_kwargs):
        return _AsyncResponse()


def test_career_direct_url_returns_canonical_workday_board():
    assert career_ats_detector.detect_ats_from_url(DEEP_URL) == (
        "workday",
        BOARD_URL,
    )


def test_career_html_regex_returns_canonical_workday_board():
    result = asyncio.run(
        career_ats_detector.detect_greenhouse_slug_from_domain(
            _AsyncSession(),
            "example.com",
        )
    )

    assert result == {"workday": BOARD_URL}


def test_sitemap_workday_identity_is_canonical_before_learning(monkeypatch):
    learned = []
    monkeypatch.setattr(
        sitemap_fetcher,
        "learn_company",
        lambda ats, value: learned.append((ats, value)),
    )

    found = sitemap_fetcher.detect_ats_from_urls([DEEP_URL])

    assert found["workday"] == {BOARD_URL}
    assert learned == [("workday", BOARD_URL)]
    assert all(value != "External" for _, value in learned)


def _isolate_domain_detection(monkeypatch):
    monkeypatch.setattr(discovery, "slug_from_domain", lambda _domain: None)
    monkeypatch.setattr(discovery, "check_greenhouse", lambda _slug: False)
    monkeypatch.setattr(discovery, "check_ashby", lambda _slug: False)
    monkeypatch.setattr(
        discovery,
        "extract_lever_slug_from_domain",
        lambda _domain: None,
    )
    monkeypatch.setattr(
        discovery,
        "extract_workday_board_url",
        lambda _domain: None,
    )
    monkeypatch.setattr(discovery, "fetch_career_subdomain", lambda _domain: None)


def test_domain_board_extraction_workday_identity_is_canonical(monkeypatch):
    monkeypatch.setattr(discovery, "slug_from_domain", lambda _domain: None)
    monkeypatch.setattr(
        discovery,
        "extract_lever_slug_from_domain",
        lambda _domain: None,
    )
    monkeypatch.setattr(
        discovery,
        "extract_workday_board_url",
        lambda _domain: DEEP_URL,
    )

    assert discovery.detect_ats_for_domain("example.com")["workday"] == BOARD_URL


def test_domain_redirect_workday_identity_is_canonical(monkeypatch):
    _isolate_domain_detection(monkeypatch)
    monkeypatch.setattr(
        discovery,
        "detect_ats_from_redirect",
        lambda _domain: ("workday", DEEP_URL),
    )
    monkeypatch.setattr(
        discovery,
        "fetch_career_page",
        lambda _domain: pytest.fail("canonical redirect must return immediately"),
    )

    assert discovery.detect_ats_for_domain("example.com")["workday"] == BOARD_URL


def test_domain_link_workday_identity_is_canonical(monkeypatch):
    _isolate_domain_detection(monkeypatch)
    monkeypatch.setattr(
        discovery,
        "detect_ats_from_redirect",
        lambda _domain: (None, None),
    )
    monkeypatch.setattr(discovery, "fetch_career_page", lambda _domain: "html")
    monkeypatch.setattr(discovery, "extract_links_from_html", lambda _html: [])
    monkeypatch.setattr(
        discovery,
        "detect_ats_from_links",
        lambda _links: ("workday", DEEP_URL),
    )

    assert discovery.detect_ats_for_domain("example.com")["workday"] == BOARD_URL


def test_domain_html_workday_identity_is_canonical(monkeypatch):
    _isolate_domain_detection(monkeypatch)
    monkeypatch.setattr(
        discovery,
        "detect_ats_from_redirect",
        lambda _domain: (None, None),
    )
    monkeypatch.setattr(discovery, "fetch_career_page", lambda _domain: "html")
    monkeypatch.setattr(discovery, "extract_links_from_html", lambda _html: [])
    monkeypatch.setattr(
        discovery,
        "detect_ats_from_links",
        lambda _links: (None, None),
    )
    monkeypatch.setattr(
        discovery,
        "detect_ats_from_embeds",
        lambda _html: (None, None),
    )
    monkeypatch.setattr(discovery, "detect_ats_from_html", lambda _html: "workday")
    monkeypatch.setattr(discovery, "extract_workday_url", lambda _html: DEEP_URL)

    assert discovery.detect_ats_for_domain("example.com")["workday"] == BOARD_URL


def test_canonical_workday_identity_passes_existing_persistence_firewall(
    monkeypatch,
):
    writes = []
    monkeypatch.setattr(
        save_companies,
        "get_discovered_ats_companies",
        lambda _ats: set(),
    )
    monkeypatch.setattr(
        save_companies,
        "upsert_discovered_ats_companies",
        lambda ats, companies, source: writes.append(
            (ats, companies, source)
        ) or len(companies),
    )

    save_companies.append_new_companies("discovery://ats/workday", {BOARD_URL})

    assert writes == [
        ("workday", {BOARD_URL}, "persist_discovered_companies"),
    ]


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://boards.greenhouse.io/acme/jobs/1", ("greenhouse", "acme")),
        ("https://jobs.lever.co/acme/role", ("lever", "acme")),
        ("https://jobs.ashbyhq.com/acme/role", ("ashby", "acme")),
        ("https://apply.workable.com/acme/j/ABC", ("workable", "acme")),
        ("https://jobs.jobvite.com/acme/job/role", ("jobvite", "acme")),
    ],
)
def test_non_workday_career_url_identity_is_unchanged(url, expected):
    assert career_ats_detector.detect_ats_from_url(url) == expected
