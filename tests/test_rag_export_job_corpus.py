import json
import sys
import tempfile
import types
from copy import deepcopy
from pathlib import Path

import pytest

class _FakeTqdm:
    def __call__(self, iterable=None, **kwargs):
        return iterable

    @staticmethod
    def write(*args, **kwargs):
        return None


sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=_FakeTqdm()))

import main
from src.rag import export_job_corpus as exporter


def _job(job_id: str, title: str = "Backend Engineer"):
    return {
        "job_id": job_id,
        "url": f"https://example.com/jobs/{job_id}",
        "title": title,
        "company": "Acme",
        "location": "United States",
        "source": "lever",
        "description_text": "Build APIs and services.",
        "ai_fit_score": 90,
        "_freshness_status": "unknown_timestamp_allowed",
        "_ashby_timestamp_status": "ashby_timestamp_request_failed",
    }


def _read_jsonl(path: Path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_export_job_corpus_writes_non_empty_jsonl_to_filesystem_path():
    original_upsert = exporter.upsert_rag_job_documents
    original_count = exporter.count_rag_job_documents
    exporter.upsert_rag_job_documents = lambda docs: {"upserted_count": len(list(docs))}
    exporter.count_rag_job_documents = lambda: 999

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "nested" / "current_run_job_corpus.jsonl"
        try:
            count = exporter.export_job_corpus([_job("1")], str(output_path), merge_existing=False)
        finally:
            exporter.upsert_rag_job_documents = original_upsert
            exporter.count_rag_job_documents = original_count

        rows = _read_jsonl(output_path)

    assert count == 1
    assert len(rows) == 1
    assert rows[0]["job_id"] == "1"
    assert rows[0]["title"] == "Backend Engineer"
    assert rows[0]["location"] == "United States"
    assert rows[0]["freshness_status"] == "unknown_timestamp_allowed"
    assert rows[0]["ashby_timestamp_status"] == "ashby_timestamp_request_failed"


def test_export_job_corpus_merge_existing_false_writes_only_current_jobs():
    original_upsert = exporter.upsert_rag_job_documents
    original_count = exporter.count_rag_job_documents
    exporter.upsert_rag_job_documents = lambda docs: {"upserted_count": len(list(docs))}
    exporter.count_rag_job_documents = lambda: 999

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "corpus.jsonl"
        output_path.write_text(json.dumps({"job_id": "old"}) + "\n", encoding="utf-8")
        try:
            count = exporter.export_job_corpus([_job("new")], str(output_path), merge_existing=False)
        finally:
            exporter.upsert_rag_job_documents = original_upsert
            exporter.count_rag_job_documents = original_count

        rows = _read_jsonl(output_path)

    assert count == 1
    assert [row["job_id"] for row in rows] == ["new"]


def test_export_job_corpus_postgres_path_does_not_write_local_file():
    calls = {"count": 0}
    original_upsert = exporter.upsert_rag_job_documents
    original_count = exporter.count_rag_job_documents

    def fake_count():
        calls["count"] += 1
        return 42

    exporter.upsert_rag_job_documents = lambda docs: {"upserted_count": len(list(docs))}
    exporter.count_rag_job_documents = fake_count

    try:
        count = exporter.export_job_corpus([_job("1")], "postgres://rag_job_documents")
    finally:
        exporter.upsert_rag_job_documents = original_upsert
        exporter.count_rag_job_documents = original_count

    assert count == 42
    assert calls["count"] == 1
    assert not Path("postgres:/rag_job_documents").exists()


def test_private_filesystem_export_does_not_upsert_shared_postgres():
    original_upsert = exporter.upsert_rag_job_documents
    exporter.upsert_rag_job_documents = lambda _docs: (_ for _ in ()).throw(
        AssertionError("private corpus must not update shared Postgres")
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "private" / "corpus.jsonl"
        try:
            count = exporter.export_job_corpus(
                [_job("private")],
                str(output_path),
                merge_existing=False,
                persist_postgres=False,
            )
        finally:
            exporter.upsert_rag_job_documents = original_upsert

        rows = _read_jsonl(output_path)

    assert count == 1
    assert [row["job_id"] for row in rows] == ["private"]


def test_owner_neutral_shared_export_clears_owner_derived_fields():
    captured = {}
    original_upsert = exporter.upsert_rag_job_documents
    original_count = exporter.count_rag_job_documents
    exporter.upsert_rag_job_documents = lambda docs: captured.setdefault(
        "docs", deepcopy(list(docs))
    )
    exporter.count_rag_job_documents = lambda: 1
    job = _job("shared")
    job["ai_fit_reason"] = "Owner-specific reason"
    job["resume_matches"] = [{"resume_id": "owner-resume"}]

    try:
        count = exporter.export_job_corpus(
            [job],
            "postgres://rag_job_documents",
            owner_neutral=True,
        )
    finally:
        exporter.upsert_rag_job_documents = original_upsert
        exporter.count_rag_job_documents = original_count

    assert count == 1
    assert captured["docs"][0]["ai_fit_score"] is None
    assert captured["docs"][0]["ai_fit_reason"] == ""
    assert captured["docs"][0]["resume_matches"] == []
    assert "Owner-specific reason" not in captured["docs"][0]["retrieval_text"]


def test_owner_current_run_planning_corpus_does_not_upsert_shared_postgres():
    original_upsert = exporter.upsert_rag_job_documents
    exporter.upsert_rag_job_documents = lambda _docs: (_ for _ in ()).throw(
        AssertionError("owner planning corpus must remain private")
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            corpus_path = main._write_current_run_planning_corpus(
                [_job("owner")],
                tmp_dir,
                persist_postgres=False,
            )
        finally:
            exporter.upsert_rag_job_documents = original_upsert

        rows = _read_jsonl(Path(corpus_path))

    assert [row["job_id"] for row in rows] == ["owner"]


def test_global_acquisition_only_is_default_off_and_rejects_planning():
    defaults = {
        "global_acquisition_only": False,
        "run_application_planning": False,
        "application_planning_only": False,
        "application_planning_corpus_source": "filesystem",
        "application_planning_generate_tailoring": False,
        "application_planning_generate_llm_tailoring": False,
        "application_planning_refresh_llm_tailoring": False,
        "application_planning_generate_llm_fallback": False,
        "application_planning_generate_llm_adjudication": False,
        "delete_seen_data": "no",
    }
    main._validate_application_planning_only_args(types.SimpleNamespace(**defaults))

    contradictory = dict(defaults)
    contradictory.update(
        global_acquisition_only=True,
        run_application_planning=True,
    )
    with pytest.raises(SystemExit, match="cannot be combined"):
        main._validate_application_planning_only_args(
            types.SimpleNamespace(**contradictory)
        )


def test_write_current_run_planning_corpus_produces_accepted_file():
    original_upsert = exporter.upsert_rag_job_documents
    original_count = exporter.count_rag_job_documents
    exporter.upsert_rag_job_documents = lambda docs: {"upserted_count": len(list(docs))}
    exporter.count_rag_job_documents = lambda: 999

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            corpus_path = main._write_current_run_planning_corpus([_job("1")], tmp_dir)
        finally:
            exporter.upsert_rag_job_documents = original_upsert
            exporter.count_rag_job_documents = original_count

        path = Path(corpus_path)
        rows = _read_jsonl(path)
        has_records = main._corpus_has_job_records(corpus_path)

    assert path.name == "current_run_job_corpus.jsonl"
    assert len(rows) == 1
    assert has_records is True


def test_build_job_document_accepts_non_string_posted_at():
    from src.rag.job_document_builder import build_job_document

    doc = build_job_document(
        {
            "company": "example",
            "title": "Backend Engineer",
            "location": "New York, NY",
            "posted_at": 20260522,
            "url": "https://example.com/job",
            "description": "Build backend systems.",
        }
    )

    assert doc["posted_at"] == "20260522"


def test_job_document_normalizes_list_location_without_mutating_input():
    from src.rag.job_document_builder import build_job_document

    job = _job("list-location")
    job["location"] = ["United States", "Canada", "United States", "", 7]
    original = deepcopy(job)

    doc = build_job_document(job)

    assert doc["location"] == "United States, Canada"
    assert "Location: United States, Canada" in doc["retrieval_text"]
    assert doc["doc_id"] == job["url"]
    assert job == original

    fallback_job = deepcopy(job)
    fallback_job["url"] = ""
    assert build_job_document(fallback_job)["doc_id"] == build_job_document(
        deepcopy(fallback_job)
    )["doc_id"]

    string_job = _job("string-location")
    string_job["location"] = "  New York, NY  "
    assert build_job_document(string_job)["location"] == "New York, NY"
    empty_list_job = _job("empty-list-location")
    empty_list_job["location"] = []
    assert build_job_document(empty_list_job)["location"] == ""


def test_job_document_preserves_bounded_attribution_outside_retrieval_text():
    from src.rag import job_document_builder

    job = _job("attributed")
    job.update(
        {
            "provider_attribution_required": True,
            "provider_attribution_label": "  " + "H" * 250 + "  ",
            "provider_attribution_url": "  https://himalayas.app/" + "x" * 2200 + "  ",
        }
    )
    doc = job_document_builder.build_job_document(job)

    assert doc["provider_attribution_required"] is True
    assert doc["provider_attribution_label"] == "H" * 200
    assert len(doc["provider_attribution_url"]) == 2048
    assert doc["provider_attribution_url"].startswith("https://himalayas.app/")
    assert "provider_attribution" not in doc["retrieval_text"]
    assert "Himalayas" not in doc["retrieval_text"]
    assert doc["doc_id"] == job["url"]
    assert doc["job_url"] == job["url"]


def test_job_document_attribution_defaults_and_boolean_safety():
    from src.rag.job_document_builder import build_job_document

    defaults = build_job_document(_job("default"))
    assert defaults["provider_attribution_required"] is False
    assert defaults["provider_attribution_label"] == ""
    assert defaults["provider_attribution_url"] == ""

    for value in ("true", "false", "1", 1):
        job = _job(f"value-{value}")
        job["provider_attribution_required"] = value
        assert build_job_document(job)["provider_attribution_required"] is False


def test_exported_document_retains_provider_attribution():
    job = _job("transport")
    job.update(
        {
            "provider_attribution_required": True,
            "provider_attribution_label": "Himalayas",
            "provider_attribution_url": "https://himalayas.app",
        }
    )
    original_upsert = exporter.upsert_rag_job_documents
    original_count = exporter.count_rag_job_documents
    exporter.upsert_rag_job_documents = lambda docs: {"upserted_count": len(list(docs))}
    exporter.count_rag_job_documents = lambda: 999

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "corpus.jsonl"
        try:
            exporter.export_job_corpus([job], str(output_path), merge_existing=False)
        finally:
            exporter.upsert_rag_job_documents = original_upsert
            exporter.count_rag_job_documents = original_count
        row = _read_jsonl(output_path)[0]

    assert row["provider_attribution_required"] is True
    assert row["provider_attribution_label"] == "Himalayas"
    assert row["provider_attribution_url"] == "https://himalayas.app"
