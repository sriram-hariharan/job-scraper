from types import SimpleNamespace

from src.cache import description_cache


def _completed(stdout: str):
    return SimpleNamespace(stdout=stdout, stderr="", returncode=0)


def test_psql_json_query_reads_valid_json_object(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/test")
    monkeypatch.setattr(
        description_cache.subprocess,
        "run",
        lambda *args, **kwargs: _completed('{"found":true,"description":{}}\n'),
    )

    assert description_cache._run_psql_json_query("SELECT 1") == {
        "found": True,
        "description": {},
    }


def test_psql_json_query_ignores_non_json_lines_after_payload(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/test")
    monkeypatch.setattr(
        description_cache.subprocess,
        "run",
        lambda *args, **kwargs: _completed(
            '{"found":false,"description":{}}\n'
            'non-json trailing output\n'
        ),
    )

    assert description_cache._run_psql_json_query("SELECT 1") == {
        "found": False,
        "description": {},
    }


def test_psql_json_query_treats_malformed_output_as_cache_miss(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/test")
    monkeypatch.setattr(
        description_cache.subprocess,
        "run",
        lambda *args, **kwargs: _completed(
            "unexpected psql output\n"
        ),
    )

    assert description_cache._run_psql_json_query("SELECT 1") == {}


def test_psql_json_query_treats_empty_output_as_cache_miss(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/test")
    monkeypatch.setattr(
        description_cache.subprocess,
        "run",
        lambda *args, **kwargs: _completed(""),
    )

    assert description_cache._run_psql_json_query("SELECT 1") == {}
