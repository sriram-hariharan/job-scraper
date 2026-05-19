import sys
import types


class _FakeTqdm:
    def __call__(self, iterable=None, **kwargs):
        return iterable

    @staticmethod
    def write(*args, **kwargs):
        return None


sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))
sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=_FakeTqdm()))

from src.scrapers import ashby_scraper


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_ashby_timestamp_transient_failure_then_success(monkeypatch):
    calls = []
    monkeypatch.setattr(ashby_scraper.time, "sleep", lambda seconds: None)

    def fake_http_post(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            return FakeResponse(status_code=503)
        return FakeResponse(
            payload={
                "data": {
                    "jobPosting": {
                        "publishedDate": "2026-05-19",
                    }
                }
            }
        )

    monkeypatch.setattr(ashby_scraper, "http_post", fake_http_post)

    result = ashby_scraper.fetch_ashby_timestamp_result("plaid", "posting-123")

    assert len(calls) == 2
    assert result == {
        "posted_at": "2026-05-19",
        "marker": "",
        "status_code": None,
    }
    assert ashby_scraper.fetch_ashby_timestamp("plaid", "posting-123") == "2026-05-19"


def test_ashby_timestamp_repeated_failure_sets_request_failed(monkeypatch):
    calls = []
    monkeypatch.setattr(ashby_scraper.time, "sleep", lambda seconds: None)

    def fake_http_post(*args, **kwargs):
        calls.append(1)
        return FakeResponse(status_code=500)

    monkeypatch.setattr(ashby_scraper, "http_post", fake_http_post)

    result = ashby_scraper.fetch_ashby_timestamp_result("plaid", "posting-123")

    assert len(calls) == 3
    assert result == {
        "posted_at": None,
        "marker": "ashby_timestamp_request_failed",
        "status_code": 500,
    }


def test_ashby_timestamp_missing_published_date_sets_marker(monkeypatch):
    monkeypatch.setattr(ashby_scraper.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        ashby_scraper,
        "http_post",
        lambda *args, **kwargs: FakeResponse(
            payload={"data": {"jobPosting": {"publishedDate": ""}}},
        ),
    )

    result = ashby_scraper.fetch_ashby_timestamp_result("plaid", "posting-123")

    assert result == {
        "posted_at": None,
        "marker": "ashby_timestamp_no_published_date",
        "status_code": 200,
    }


def test_ashby_timestamp_unexpected_shape_sets_parse_failed(monkeypatch):
    monkeypatch.setattr(ashby_scraper.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        ashby_scraper,
        "http_post",
        lambda *args, **kwargs: FakeResponse(payload={"data": {"jobPosting": None}}),
    )

    result = ashby_scraper.fetch_ashby_timestamp_result("plaid", "posting-123")

    assert result == {
        "posted_at": None,
        "marker": "ashby_timestamp_parse_failed",
        "status_code": 200,
    }
