import asyncio
import sys
import types


class _FakeTqdm:
    def __call__(self, iterable=None, **kwargs):
        return iterable

    @staticmethod
    def write(*args, **kwargs):
        return None


sys.modules.setdefault("aiohttp", types.SimpleNamespace())
sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))
sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=_FakeTqdm()))
sys.modules.setdefault(
    "src.utils.workday_timestamp",
    types.SimpleNamespace(fetch_workday_timestamp=lambda *args, **kwargs: None),
)

from src.scrapers import lever_scraper


class _FakeLeverResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload, status=200):
        self._payload = payload
        self._status = status

    def get(self, *args, **kwargs):
        return _FakeLeverResponse(self._payload, status=self._status)


def _lever_job(title, *, location="New York, NY", created_at=4102444800000):
    return {
        "id": "posting-123",
        "text": title,
        "categories": {"location": location},
        "hostedUrl": "https://jobs.lever.co/acme/posting-123",
        "createdAt": created_at,
    }


def _fetch(payload):
    return asyncio.run(lever_scraper.fetch_company_jobs(_FakeSession(payload), "acme"))


def test_default_lever_scraping_still_rejects_backend_title(monkeypatch):
    monkeypatch.delenv("JOB_STACK_SELECTED_ROLE_FAMILIES", raising=False)
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(lever_scraper, "posted_within_24h", lambda posted_at: True)

    jobs = _fetch([_lever_job("Backend Engineer")])

    assert jobs == []


def test_lever_early_filter_accepts_selected_backend_role(monkeypatch):
    monkeypatch.setenv("JOB_STACK_SELECTED_ROLE_FAMILIES", '["backend_engineering"]')
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(lever_scraper, "posted_within_24h", lambda posted_at: True)

    jobs = _fetch([_lever_job("Backend Engineer")])

    assert [job["title"] for job in jobs] == ["Backend Engineer"]
    assert jobs[0]["source"] == "lever"
    assert jobs[0]["job_id"] == "lv_posting-123"


def test_lever_early_filter_accepts_resolved_role_argument_without_env(monkeypatch):
    monkeypatch.delenv("JOB_STACK_SELECTED_ROLE_FAMILIES", raising=False)
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(lever_scraper, "posted_within_24h", lambda posted_at: True)

    jobs = asyncio.run(
        lever_scraper.fetch_company_jobs(
            _FakeSession([_lever_job("Backend Engineer")]),
            "acme",
            selected_role_families=["backend_engineering"],
        )
    )

    assert [job["title"] for job in jobs] == ["Backend Engineer"]


def test_lever_early_filter_accepts_selected_software_role(monkeypatch):
    monkeypatch.setenv("JOB_STACK_SELECTED_ROLE_FAMILIES", '["software_engineering"]')
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(lever_scraper, "posted_within_24h", lambda posted_at: True)

    jobs = _fetch([_lever_job("Software Engineer")])

    assert [job["title"] for job in jobs] == ["Software Engineer"]


def test_invalid_selected_role_family_json_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("JOB_STACK_SELECTED_ROLE_FAMILIES", "{")
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(lever_scraper, "posted_within_24h", lambda posted_at: True)

    jobs = _fetch([_lever_job("Backend Engineer")])

    assert jobs == []


def test_lever_location_and_freshness_filters_still_apply(monkeypatch):
    monkeypatch.setenv("JOB_STACK_SELECTED_ROLE_FAMILIES", '["backend_engineering"]')
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(lever_scraper, "posted_within_24h", lambda posted_at: True)

    wrong_location_jobs = _fetch([_lever_job("Backend Engineer", location="London, UK")])

    monkeypatch.setattr(lever_scraper, "posted_within_24h", lambda posted_at: False)
    stale_jobs = _fetch([_lever_job("Backend Engineer", location="New York, NY")])

    assert wrong_location_jobs == []
    assert stale_jobs == []
