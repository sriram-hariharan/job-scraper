import pytest

from src.agents import company_discovery_agent as agent
from src.discovery import career_ats_detector, learned_companies
from src.scrapers import smartrecruiters_scraper, workable_scraper


class _Response:
    def __init__(self, text=""):
        self.text = text


class _TavilyClient:
    def __init__(self, results):
        self.results = results
        self.queries = []

    def search(self, *, query, max_results):
        self.queries.append((query, max_results))
        return {"results": list(self.results)}


@pytest.mark.parametrize("key", [None, "", "   "])
def test_missing_tavily_key_is_default_off(monkeypatch, key):
    if key is None:
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    else:
        monkeypatch.setenv("TAVILY_API_KEY", key)

    monkeypatch.setattr(
        agent,
        "TavilyClient",
        lambda **kwargs: pytest.fail("Tavily client must not be constructed"),
    )
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: pytest.fail("HTTP must not be called"),
    )
    monkeypatch.setattr(
        agent,
        "validate_jobvite_companies",
        lambda values: pytest.fail("Jobvite validator must not be called"),
    )
    monkeypatch.setattr(
        agent,
        "validate_recruitee_companies",
        lambda values: pytest.fail("validator must not be called"),
    )
    monkeypatch.setattr(
        agent,
        "append_new_companies",
        lambda *args, **kwargs: pytest.fail("persistence must not be called"),
    )

    assert agent.run_company_discovery_agent() is None


def test_extract_urls_retains_direct_recruitee_offers():
    results = [
        {"url": "https://example.recruitee.com/o/data-scientist"},
        {"url": "https://example.recruitee.com/o/machine-learning-engineer"},
        {"url": "https://example.com/careers"},
        {"url": "https://example.com/about"},
        {"url": "https://recruitee.com/"},
        {"url": "https://www.recruitee.com/"},
        {"url": "https://example.com/?next=tenant.recruitee.com"},
        {"url": "https://tenant.recruitee.com.evil.example/o/role"},
        {"url": "ftp://tenant.recruitee.com/o/role"},
    ]

    assert agent.extract_urls(results) == [
        "https://example.recruitee.com/o/data-scientist",
        "https://example.recruitee.com/o/machine-learning-engineer",
        "https://example.com/careers",
    ]


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.recruitee.com/o/data-scientist", "example"),
        ("https://Example.recruitee.com/o/data-scientist", "example"),
        (
            "https://Example-Tenant.recruitee.com/o/data-scientist",
            "example-tenant",
        ),
        ("https://recruitee.com/tenant/o/role", None),
        ("https://www.recruitee.com/o/role", None),
        ("https://tenant.recruitee.com.evil.example/o/role", None),
        ("https://example.com/?next=tenant.recruitee.com", None),
        ("ftp://tenant.recruitee.com/o/role", None),
        ("https://-tenant.recruitee.com/o/role", None),
        ("https://tenant-.recruitee.com/o/role", None),
        ("https://recruitee.com/tenant.recruitee.com/o/role", None),
        (f"https://{'a' * 64}.recruitee.com/o/role", None),
    ],
)
def test_extract_company_slug_enforces_recruitee_tenant_contract(url, expected):
    assert agent.extract_company_slug(url) == expected


def test_direct_recruitee_detection_does_not_fetch(monkeypatch):
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: pytest.fail("direct detection must not fetch"),
    )

    assert (
        agent.detect_ats_from_page(
            "https://Example-Tenant.recruitee.com/o/data-scientist"
        )
        == "recruitee"
    )


def _run_agent(
    monkeypatch,
    results,
    validator,
    jobvite_validator=lambda companies: companies,
):
    client = _TavilyClient(results)
    persisted = []
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(agent, "TavilyClient", lambda **kwargs: client)
    monkeypatch.setattr(agent, "tqdm", lambda values, **kwargs: values)
    monkeypatch.setattr(agent, "validate_jobvite_companies", jobvite_validator)
    monkeypatch.setattr(agent, "validate_recruitee_companies", validator)
    monkeypatch.setattr(
        agent,
        "append_new_companies",
        lambda path, companies: persisted.append((path, list(companies))),
    )
    agent.run_company_discovery_agent()
    return client, persisted


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        (
            '<a href="https://boards.greenhouse.io/acme/jobs/123">Open</a>',
            ("greenhouse", "acme"),
        ),
        (
            '<script>const board="https://jobs.lever.co/acme/123";</script>',
            ("lever", "acme"),
        ),
        (
            '<a href="https://jobs.ashbyhq.com/acme/123">Open</a>',
            ("ashby", "acme"),
        ),
        (
            '<a href="https://apply.workable.com/acme/j/ABC">Open</a>',
            ("workable", "acme"),
        ),
        (
            '<a href="https://jobs.jobvite.com/Acme-Co2/job/ABC">Open</a>',
            ("jobvite", "acme-co2"),
        ),
        (
            '<a href="https://acme.wd1.myworkdayjobs.com/'
            'External_Careers/job/REQ123">Open</a>',
            (
                "workday",
                "https://acme.wd1.myworkdayjobs.com/External_Careers",
            ),
        ),
        (
            '<a href="https://jobs.smartrecruiters.com/Nvidia/123-role">'
            "Open</a>",
            ("smartrecruiters", "nvidia"),
        ),
    ],
)
def test_generic_page_resolves_concrete_ats_identity_once(
    monkeypatch,
    html,
    expected,
):
    calls = []
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda url, timeout: calls.append((url, timeout)) or _Response(html),
    )

    assert agent._resolve_ats_identity_from_page(
        "https://acme.example/careers"
    ) == expected
    assert calls == [("https://acme.example/careers", 10)]


@pytest.mark.parametrize(
    ("html", "ats", "identity"),
    [
        (
            '<a href="https://boards.greenhouse.io/acme/jobs/123">Open</a>',
            "greenhouse",
            "acme",
        ),
        (
            '<script>const board="https://jobs.lever.co/acme/123";</script>',
            "lever",
            "acme",
        ),
    ],
)
def test_generic_page_persists_resolved_identity_once(
    monkeypatch,
    html,
    ats,
    identity,
):
    calls = []
    monkeypatch.setattr(agent, "SEARCH_QUERIES", ["fixed query"])
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda url, timeout: calls.append((url, timeout)) or _Response(html),
    )

    _, persisted = _run_agent(
        monkeypatch,
        [{"url": "https://acme.example/careers"}],
        lambda companies: companies,
    )

    assert persisted == [(f"discovery://ats/{ats}", [identity])]
    assert calls == [("https://acme.example/careers", 10)]


def test_generic_workable_route_token_fails_closed(monkeypatch):
    html = '<a href="https://apply.workable.com/j/ABC">Open</a>'
    calls = []
    monkeypatch.setattr(agent, "SEARCH_QUERIES", ["fixed query"])
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda url, timeout: calls.append((url, timeout)) or _Response(html),
    )

    assert agent._resolve_ats_identity_from_page(
        "https://acme.example/careers"
    ) == ("workable", None)
    calls.clear()
    _, persisted = _run_agent(
        monkeypatch,
        [{"url": "https://acme.example/careers"}],
        lambda companies: companies,
    )

    assert persisted == []
    assert calls == [("https://acme.example/careers", 10)]


def test_marker_only_detection_preserves_public_contract_and_fails_closed(
    monkeypatch,
):
    calls = []
    monkeypatch.setattr(agent, "SEARCH_QUERIES", ["fixed query"])
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda url, timeout: calls.append((url, timeout))
        or _Response("powered by boards.greenhouse.io"),
    )

    assert agent._resolve_ats_identity_from_page(
        "https://acme.example/careers"
    ) == ("greenhouse", None)
    assert calls == [("https://acme.example/careers", 10)]

    calls.clear()
    assert agent.detect_ats_from_page(
        "https://acme.example/careers"
    ) == "greenhouse"
    assert calls == [("https://acme.example/careers", 10)]

    calls.clear()
    _, persisted = _run_agent(
        monkeypatch,
        [{"url": "https://acme.example/careers"}],
        lambda companies: companies,
    )
    assert persisted == []
    assert calls == [("https://acme.example/careers", 10)]


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://Example-Tenant.recruitee.com/o/data-scientist",
            ("recruitee", "example-tenant"),
        ),
        (
            "https://jobs.jobvite.com/Acme-Co2/job/example-id",
            ("jobvite", "acme-co2"),
        ),
        (
            "https://acme.wd1.myworkdayjobs.com/External/job/REQ123",
            ("workday", "https://acme.wd1.myworkdayjobs.com/External"),
        ),
    ],
)
def test_direct_resolver_identity_remains_network_free(monkeypatch, url, expected):
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: pytest.fail("direct resolution must not fetch"),
    )

    assert agent._resolve_ats_identity_from_page(url) == expected


def test_generic_recruitee_html_detection_is_not_added(monkeypatch):
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *_args, **_kwargs: _Response(
            '<a href="https://acme.recruitee.com/o/role">Open</a>'
        ),
    )

    assert agent._resolve_ats_identity_from_page(
        "https://acme.example/careers"
    ) == (None, None)


def test_generic_page_failure_does_not_block_other_candidate(monkeypatch):
    calls = []
    monkeypatch.setattr(agent, "SEARCH_QUERIES", ["fixed query"])

    def fail_generic(url, timeout):
        calls.append((url, timeout))
        raise OSError("offline")

    monkeypatch.setattr(agent.requests, "get", fail_generic)
    _, persisted = _run_agent(
        monkeypatch,
        [
            {"url": "https://acme.example/careers"},
            {"url": "https://jobs.jobvite.com/alpha/job/ABC"},
        ],
        lambda companies: companies,
    )

    assert persisted == [("discovery://ats/jobvite", ["alpha"])]
    assert calls == [("https://acme.example/careers", 10)]


def test_recruitee_candidates_are_validated_and_persisted_deterministically(
    monkeypatch,
):
    validator_calls = []

    def validate(companies):
        validator_calls.append(list(companies))
        return {"zulu", "beta", "not-a-candidate"}

    client, persisted = _run_agent(
        monkeypatch,
        [
            {"url": "https://Zulu.recruitee.com/o/data-scientist"},
            {"url": "https://alpha.recruitee.com/o/data-scientist"},
            {"url": "https://Beta.recruitee.com/o/data-scientist"},
            {"url": "https://alpha.recruitee.com/o/data-scientist"},
        ],
        validate,
    )

    assert validator_calls == [["alpha", "beta", "zulu"]]
    assert persisted == [
        ("discovery://ats/recruitee", ["beta", "zulu"]),
    ]
    assert client.queries == [(query, 20) for query in agent.SEARCH_QUERIES]


def test_empty_recruitee_validation_result_does_not_persist(monkeypatch):
    _, persisted = _run_agent(
        monkeypatch,
        [{"url": "https://alpha.recruitee.com/o/data-scientist"}],
        lambda companies: set(),
    )

    assert persisted == []


def test_recruitee_validator_failure_is_bounded_and_isolated(
    monkeypatch,
):
    secret = "secret-validator-token"
    warnings = []

    def validate(_companies):
        raise RuntimeError(secret)

    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: _Response("boards.greenhouse.io"),
    )
    monkeypatch.setattr(agent.logger, "warning", warnings.append)
    _, persisted = _run_agent(
        monkeypatch,
        [
            {"url": "https://boards.greenhouse.io/acme/jobs/1"},
            {"url": "https://alpha.recruitee.com/o/data-scientist"},
        ],
        validate,
    )

    assert persisted == [("discovery://ats/greenhouse", ["acme"])]
    assert warnings == ["Recruitee validation failed; no candidates persisted"]
    assert secret not in warnings[0]


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://boards.greenhouse.io/acme/jobs/1", "acme"),
        ("https://jobs.lever.co/acme/role", "acme"),
        ("https://jobs.ashbyhq.com/acme/role", "acme"),
        ("https://apply.workable.com/acme/j/ABC", "acme"),
        (
            "https://capitalone.wd12.myworkdayjobs.com/Capital_One/job/Role",
            "https://capitalone.wd12.myworkdayjobs.com/Capital_One",
        ),
        ("https://jobs.smartrecruiters.com/Nvidia/123-role", "nvidia"),
        ("https://jobs.jobvite.com/acme/job/role", "acme"),
    ],
)
def test_existing_provider_extraction_contracts_are_unchanged(url, expected):
    assert agent.extract_company_slug(url) == expected


@pytest.mark.parametrize(
    ("marker", "expected"),
    [
        ("boards.greenhouse.io", "greenhouse"),
        ("jobs.lever.co", "lever"),
        ("jobs.ashbyhq.com", "ashby"),
        ("apply.workable.com", "workable"),
        ("myworkdayjobs.com", "workday"),
        ("smartrecruiters.com", "smartrecruiters"),
        ("jobs.jobvite.com", "jobvite"),
    ],
)
def test_existing_provider_detection_contracts_are_unchanged(
    monkeypatch,
    marker,
    expected,
):
    calls = []
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda url, timeout: calls.append((url, timeout)) or _Response(marker),
    )

    assert agent.detect_ats_from_page("https://example.com/careers") == expected
    assert calls == [("https://example.com/careers", 10)]


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://apply.workable.com/acme/j/ABC", "acme"),
        ("https://apply.workable.com/Acme-Co/j/ABC", "acme-co"),
        ("https://apply.workable.com/company2/j/ABC", "company2"),
        ("https://apply.workable.com/acme_co/j/ABC", "acme_co"),
    ],
)
def test_extract_company_slug_uses_workable_normalization(url, expected):
    assert agent.extract_company_slug(url) == expected


@pytest.mark.parametrize(
    "route",
    sorted(learned_companies.WORKABLE_ROUTE_SLUGS),
)
def test_extract_company_slug_rejects_workable_route_tokens(route):
    assert agent.extract_company_slug(
        f"https://apply.workable.com/{route}/ABC"
    ) is None


@pytest.mark.parametrize(
    "slug",
    ["Acme-Co", "acme_co", "company2"]
    + sorted(learned_companies.WORKABLE_ROUTE_SLUGS),
)
def test_standalone_workable_extraction_matches_shared_normalizer(slug):
    assert agent.extract_company_slug(
        f"https://apply.workable.com/{slug}/j/ABC"
    ) == learned_companies.normalize_workable_slug(slug)


def test_workable_discovery_persists_only_normalized_company(monkeypatch):
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *_args, **_kwargs: _Response("apply.workable.com"),
    )
    monkeypatch.setattr(
        agent,
        "extract_urls",
        lambda _results: ["https://apply.workable.com/acme/j/ABC"],
    )
    _, persisted = _run_agent(monkeypatch, [{}], lambda companies: companies)

    assert persisted == [("discovery://ats/workable", ["acme"])]

    monkeypatch.setattr(
        agent,
        "extract_urls",
        lambda _results: ["https://apply.workable.com/j/ABC"],
    )
    _, persisted = _run_agent(monkeypatch, [{}], lambda companies: companies)

    assert persisted == []


def test_existing_workable_career_normalization_remains_unchanged():
    assert career_ats_detector.detect_ats_from_url(
        "https://apply.workable.com/acme/j/ABC"
    ) == ("workable", "acme")
    assert career_ats_detector.detect_ats_from_url(
        "https://apply.workable.com/j/ABC"
    ) == ("workable", None)


def test_workable_identity_matches_existing_scraper_account_contract():
    company = agent.extract_company_slug(
        "https://apply.workable.com/acme/j/ABC"
    )

    assert workable_scraper.WORKABLE_PUBLIC_ACCOUNT_API.format(company) == (
        "https://www.workable.com/api/accounts/acme"
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://jobs.smartrecruiters.com/Nvidia/12345-ml-engineer",
            "nvidia",
        ),
        ("https://jobs.smartrecruiters.com/Nvidia", "nvidia"),
        ("http://jobs.smartrecruiters.com/Nvidia/123-role", "nvidia"),
        ("https://jobs.smartrecruiters.com/Acme-Co/123-role", "acme-co"),
        ("https://jobs.smartrecruiters.com/Acme_Co/123-role", "acme_co"),
        ("https://jobs.smartrecruiters.com/Company2/123-role", "company2"),
    ],
)
def test_extract_company_slug_uses_smartrecruiters_company_identity(url, expected):
    assert agent.extract_company_slug(url) == expected


def test_smartrecruiters_job_token_is_never_company_identity():
    url = "https://jobs.smartrecruiters.com/Nvidia/123-role"

    assert agent.extract_company_slug(url) == "nvidia"
    assert agent.extract_company_slug(url) != "123-role"


@pytest.mark.parametrize(
    "url",
    [
        "https://jobs.smartrecruiters.com/",
        "https://jobs.smartrecruiters.com.evil.example/Nvidia/123-role",
        "https://evil.smartrecruiters.com/Nvidia/123-role",
        "https://smartrecruiters.com/Nvidia/123-role",
        "https://example.com/?next=https://jobs.smartrecruiters.com/Nvidia",
        "ftp://jobs.smartrecruiters.com/Nvidia/123-role",
        "https://user@jobs.smartrecruiters.com/Nvidia/123-role",
        "not a URL",
        "https://jobs.smartrecruiters.com/jobs/123-role",
        "https://jobs.smartrecruiters.com/job/123-role",
        "https://jobs.smartrecruiters.com/careers/123-role",
        "https://jobs.smartrecruiters.com/apply/123-role",
        "https://jobs.smartrecruiters.com/www/123-role",
    ],
)
def test_extract_company_slug_rejects_invalid_smartrecruiters_identity(url):
    assert agent.extract_company_slug(url) is None


def test_smartrecruiters_discovery_persists_company_not_job_token(monkeypatch):
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *_args, **_kwargs: _Response("smartrecruiters.com"),
    )
    _, persisted = _run_agent(
        monkeypatch,
        [{"url": "https://jobs.smartrecruiters.com/Nvidia/123-role"}],
        lambda companies: companies,
    )

    assert persisted == [
        ("discovery://ats/smartrecruiters", ["nvidia"]),
    ]


def test_smartrecruiters_company_identity_matches_scraper_company_api_contract():
    company = agent.extract_company_slug(
        "https://jobs.smartrecruiters.com/Nvidia/123-role"
    )

    assert smartrecruiters_scraper.COMPANY_API.format(company=company) == (
        "https://api.smartrecruiters.com/v1/companies/nvidia/postings"
    )


def test_existing_smartrecruiters_learning_and_career_identity_remain_first_path(
    monkeypatch,
):
    monkeypatch.setitem(learned_companies._DISCOVERED, "smartrecruiters", set())
    url = "https://jobs.smartrecruiters.com/Nvidia/123-role"

    learned_companies.learn_from_job_url(url)

    assert learned_companies.get_learned()["smartrecruiters"] == {"Nvidia"}
    assert career_ats_detector.detect_ats_from_url(url) == (
        "smartrecruiters",
        "Nvidia",
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://jobs.jobvite.com/Acme/jobs/alljobs", "acme"),
        ("https://jobs.jobvite.com/acme/job/example-id", "acme"),
        ("https://jobs.jobvite.com/Acme-Co2/job/example-id", "acme-co2"),
        ("https://jobs.jobvite.com/", None),
        ("https://jobs.jobvite.com.evil.example/acme/job/example-id", None),
        ("https://example.com/?next=jobs.jobvite.com/acme", None),
        ("ftp://jobs.jobvite.com/acme/job/example-id", None),
        ("https://jobs.jobvite.com/jobs/job/example-id", None),
        ("https://jobs.jobvite.com/bad.slug/job/example-id", None),
    ],
)
def test_extract_company_slug_enforces_jobvite_company_contract(url, expected):
    assert agent.extract_company_slug(url) == expected


def test_direct_jobvite_detection_does_not_fetch(monkeypatch):
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: pytest.fail("direct detection must not fetch"),
    )

    assert (
        agent.detect_ats_from_page(
            "https://jobs.jobvite.com/Acme-Co2/job/example-id"
        )
        == "jobvite"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://acme.wd1.myworkdayjobs.com/External",
        "https://acme.wd1.myworkdayjobs.com/External/job/REQ123",
        "https://acme.wd1.myworkdayjobs.com/External?source=test",
    ],
)
def test_extract_company_slug_returns_canonical_workday_board_url(url):
    assert agent.extract_company_slug(url) == (
        "https://acme.wd1.myworkdayjobs.com/External"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://acme.wd1.myworkdayjobs.com",
        "ftp://acme.wd1.myworkdayjobs.com/External",
        "https://acme.wd1.myworkdayjobs.com.evil.example/External",
        "https://example.com/?next=https://acme.wd1.myworkdayjobs.com/External",
        "https://user@acme.wd1.myworkdayjobs.com/External",
        "not a URL",
    ],
)
def test_extract_company_slug_rejects_invalid_workday_identity(url):
    assert agent.extract_company_slug(url) is None


def test_direct_workday_detection_does_not_fetch(monkeypatch):
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: pytest.fail("direct detection must not fetch"),
    )

    assert agent.detect_ats_from_page(
        "https://acme.wd1.myworkdayjobs.com/External/job/REQ123"
    ) == "workday"


def test_workday_discovery_persists_canonical_board_url(monkeypatch):
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: pytest.fail("direct detection must not fetch"),
    )
    _, persisted = _run_agent(
        monkeypatch,
        [{"url": "https://acme.wd1.myworkdayjobs.com/External/job/REQ123"}],
        lambda companies: companies,
    )

    assert persisted == [
        ("discovery://ats/workday", [
            "https://acme.wd1.myworkdayjobs.com/External"
        ]),
    ]


def test_jobvite_search_queries_are_bounded_deterministic_and_unique():
    queries = [
        query for query in agent.SEARCH_QUERIES
        if "site:jobs.jobvite.com" in query
    ]

    assert queries == [
        'site:jobs.jobvite.com "machine learning"',
        'site:jobs.jobvite.com "data scientist"',
        'site:jobs.jobvite.com "software engineer"',
    ]
    assert len(agent.SEARCH_QUERIES) == len(set(agent.SEARCH_QUERIES))


def test_jobvite_candidates_are_validated_and_persisted_deterministically(
    monkeypatch,
):
    validator_calls = []

    def validate(companies):
        validator_calls.append(list(companies))
        return ["zulu2", "beta_co", "not-a-candidate"]

    _, persisted = _run_agent(
        monkeypatch,
        [
            {"url": "https://jobs.jobvite.com/Zulu2/job/data-scientist"},
            {"url": "https://jobs.jobvite.com/alpha/jobs/alljobs"},
            {"url": "https://jobs.jobvite.com/Beta_Co/job/ml-engineer"},
            {"url": "https://jobs.jobvite.com/alpha/job/software-engineer"},
        ],
        lambda companies: companies,
        jobvite_validator=validate,
    )

    assert validator_calls == [["alpha", "beta_co", "zulu2"]]
    assert persisted == [
        ("discovery://ats/jobvite", ["beta_co", "zulu2"]),
    ]


def test_empty_jobvite_validation_result_does_not_persist(monkeypatch):
    _, persisted = _run_agent(
        monkeypatch,
        [{"url": "https://jobs.jobvite.com/alpha/job/data-scientist"}],
        lambda companies: companies,
        jobvite_validator=lambda companies: [],
    )

    assert persisted == []


def test_jobvite_validator_failure_is_bounded_and_isolated(monkeypatch):
    secret = "secret-jobvite-validator-token"
    warnings = []

    def validate(_companies):
        raise RuntimeError(secret)

    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: _Response("boards.greenhouse.io"),
    )
    monkeypatch.setattr(agent.logger, "warning", warnings.append)
    _, persisted = _run_agent(
        monkeypatch,
        [
            {"url": "https://boards.greenhouse.io/acme/jobs/1"},
            {"url": "https://jobs.jobvite.com/alpha/job/data-scientist"},
        ],
        lambda companies: companies,
        jobvite_validator=validate,
    )

    assert persisted == [("discovery://ats/greenhouse", ["acme"])]
    assert warnings == ["Jobvite validation failed; no candidates persisted"]
    assert secret not in warnings[0]
