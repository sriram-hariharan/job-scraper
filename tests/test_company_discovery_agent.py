import pytest

from src.agents import company_discovery_agent as agent


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
        ("https://jobs.smartrecruiters.com/Nvidia/123-role", "123-role"),
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
