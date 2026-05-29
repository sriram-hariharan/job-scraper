import types
import sys



sys.modules.setdefault(
    "aiohttp",
    types.SimpleNamespace(
        TCPConnector=lambda *args, **kwargs: None,
        ClientSession=lambda *args, **kwargs: None,
    ),
)

from src.scrapers import lever_scraper


class _Response:
    def __init__(self, status_code, payload=None, raises=False):
        self.status_code = status_code
        self._payload = payload
        self._raises = raises

    def json(self):
        if self._raises:
            raise ValueError("malformed json")
        return self._payload


def test_validate_lever_company_accepts_board_with_parseable_jobs(monkeypatch):
    calls = []

    def fake_http_get(url, **kwargs):
        calls.append(url)
        return _Response(
            200,
            [
                {
                    "id": "abc",
                    "text": "Software Engineer",
                    "categories": {"location": "San Francisco, CA"},
                    "createdAt": 1770000000000,
                    "hostedUrl": "https://jobs.lever.co/field-ai/abc",
                }
            ],
        )

    monkeypatch.setattr(lever_scraper, "http_get", fake_http_get)

    assert lever_scraper.validate_lever_company("field-ai") is True
    assert calls == ["https://api.lever.co/v0/postings/field-ai?mode=json"]


def test_validate_lever_company_rejects_empty_board(monkeypatch):
    monkeypatch.setattr(
        lever_scraper,
        "http_get",
        lambda *args, **kwargs: _Response(200, []),
    )

    assert lever_scraper.validate_lever_company("emptyco") is False


def test_validate_lever_company_rejects_404(monkeypatch):
    monkeypatch.setattr(
        lever_scraper,
        "http_get",
        lambda *args, **kwargs: _Response(404, {"error": "not found"}),
    )

    assert lever_scraper.validate_lever_company("missingco") is False


def test_validate_lever_company_rejects_malformed_response(monkeypatch):
    monkeypatch.setattr(
        lever_scraper,
        "http_get",
        lambda *args, **kwargs: _Response(200, raises=True),
    )

    assert lever_scraper.validate_lever_company("badco") is False


def test_seed_valid_lever_companies_reuses_discovery_store(monkeypatch):
    monkeypatch.setattr(
        lever_scraper,
        "validate_lever_companies",
        lambda slugs: {"field-ai"},
    )

    calls = []
    fake_store = types.SimpleNamespace(
        upsert_discovered_ats_companies=lambda ats, companies, source="": calls.append(
            (ats, companies, source)
        )
        or 1
    )
    monkeypatch.setitem(sys.modules, "src.storage.discovery_store", fake_store)

    assert lever_scraper.seed_valid_lever_companies(["field-ai"]) == 1
    assert calls == [("lever", {"field-ai"}, "manual_lever_validation")]
