import asyncio
import inspect
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


def test_lever_acquisition_returns_backend_title_without_preferences(monkeypatch):
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)

    jobs = _fetch([_lever_job("Backend Engineer")])

    assert [job["title"] for job in jobs] == ["Backend Engineer"]
    assert jobs[0]["source"] == "lever"
    assert jobs[0]["job_id"] == "lv_posting-123"


def test_lever_acquisition_ignores_role_preference_environment(monkeypatch):
    monkeypatch.setenv("JOB_STACK_SELECTED_ROLE_FAMILIES", '["backend_engineering"]')
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)

    jobs = _fetch([_lever_job("Data Scientist")])

    assert [job["title"] for job in jobs] == ["Data Scientist"]


def test_lever_public_acquisition_entrypoints_have_no_role_argument(monkeypatch):
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)

    assert "selected_role_families" not in inspect.signature(
        lever_scraper.fetch_company_jobs
    ).parameters
    assert "selected_role_families" not in inspect.signature(
        lever_scraper.scrape_all_lever
    ).parameters


def test_lever_acquisition_retains_non_us_and_old_jobs(monkeypatch):
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)

    jobs = _fetch(
        [
            _lever_job(
                "Backend Engineer",
                location="London, UK",
                created_at=946684800000,
            )
        ]
    )

    assert len(jobs) == 1
    assert jobs[0]["location"] == "London, UK"
    assert jobs[0]["posted_at"] == 946684800000
