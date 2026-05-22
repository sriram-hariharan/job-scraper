import json
import sys
import tempfile
import types
from pathlib import Path

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
