from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.pipeline import himalayas_retention as retention
from src.rag import export_job_corpus, job_document_builder
from src.storage import rag_store
from src.storage.user_pipeline import store as user_store
from src.utils import job_cache


NOW = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc)
EXPIRED = "2026-08-04T12:00:00Z"
FUTURE = "2026-08-05T12:00:00Z"


def _row(identity="merge:1", *, source="himalayas", expiry=EXPIRED):
    return {
        "merge_key": identity,
        "doc_id": f"doc:{identity}",
        "job_id": f"job:{identity}",
        "source": source,
        "expiry_date": expiry,
    }


def test_expiry_survives_document_without_retrieval_or_identity_changes():
    job = {
        "url": "https://example.test/job/1",
        "company": "Acme",
        "title": "Engineer",
        "location": "Remote",
        "source": "himalayas",
        "description": "Build systems",
        "expiry_date": f"  {FUTURE}  ",
    }
    without_expiry = dict(job)
    without_expiry.pop("expiry_date")

    document = job_document_builder.build_job_document(job)
    baseline = job_document_builder.build_job_document(without_expiry)

    assert document["expiry_date"] == FUTURE
    assert FUTURE not in document["retrieval_text"]
    assert document["description"] == "Build systems"
    assert document["doc_id"] == baseline["doc_id"]


@pytest.mark.parametrize("value", [None, 1, True, [], "   "])
def test_missing_or_non_string_expiry_becomes_empty(value):
    document = job_document_builder.build_job_document(
        {"company": "A", "title": "B", "location": "", "source": "lever", "expiry_date": value}
    )
    assert document["expiry_date"] == ""


@pytest.mark.parametrize(
    "value",
    ["", "not-a-date", "2026-08-04T12:00:00", True, 1, "x" * 65],
)
def test_stored_expiry_parser_rejects_unsafe_values(value):
    assert retention.parse_stored_expiry(value) is None


def test_expiry_classification_is_exact_and_clock_deterministic():
    assert retention.classify_expired_record(_row(expiry=EXPIRED), now=NOW)["eligible"] is True
    assert retention.classify_expired_record(_row(expiry=FUTURE), now=NOW)["reason"] == "unexpired"
    assert retention.classify_expired_record(_row(source="lever"), now=NOW)["reason"] == "unmanaged_source"
    assert retention.classify_expired_record(_row(expiry="bad"), now=NOW)["reason"] == "missing_or_invalid_expiry"
    missing = _row(identity="")
    missing.update(merge_key="", doc_id="", job_id="")
    assert retention.classify_expired_record(missing, now=NOW)["reason"] == "missing_identity"
    with pytest.raises(ValueError):
        retention.classify_expired_record(_row(), now=datetime(2026, 8, 4, 12, 0))


def test_summary_is_bounded_and_contains_no_rows():
    summary = retention.summarize_expiry_candidates(
        [_row(str(index)) for index in range(300)], now=NOW
    )
    assert summary["inspected"] == 300
    assert summary["eligible_expired"] == 300
    assert len(summary["identities"]) == 250
    assert "records" not in summary


def _write_lines(path: Path, rows):
    path.write_text("".join(row if isinstance(row, str) else json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_jsonl_dry_run_and_execute_are_exact_and_idempotent(tmp_path):
    path = tmp_path / "corpus.jsonl"
    malformed = "{malformed\n"
    rows = [
        _row("expired"),
        _row("future", expiry=FUTURE),
        _row("direct", source="greenhouse"),
        _row("invalid", expiry="bad"),
        {"source": "himalayas", "expiry_date": EXPIRED},
        malformed,
    ]
    _write_lines(path, rows)
    original = path.read_bytes()

    dry = export_job_corpus.prune_expired_himalayas_jsonl(path, dry_run=True, now=NOW)
    assert path.read_bytes() == original
    assert dry == {
        "inspected": 6,
        "retained": 5,
        "expired_pruned": 1,
        "malformed_lines": 1,
        "missing_or_invalid_expiry": 1,
        "missing_identity": 1,
        "write_performed": False,
    }

    executed = export_job_corpus.prune_expired_himalayas_jsonl(path, dry_run=False, now=NOW)
    assert executed["expired_pruned"] == 1
    assert executed["write_performed"] is True
    assert malformed in path.read_text(encoding="utf-8")
    assert "direct" in path.read_text(encoding="utf-8")
    repeated = export_job_corpus.prune_expired_himalayas_jsonl(path, dry_run=False, now=NOW)
    assert repeated["expired_pruned"] == 0
    assert repeated["write_performed"] is False


def test_jsonl_missing_file_and_current_run_absence_do_not_write(tmp_path):
    missing = tmp_path / "missing.jsonl"
    result = export_job_corpus.prune_expired_himalayas_jsonl(missing, dry_run=False, now=NOW)
    assert result["inspected"] == 0
    assert result["write_performed"] is False
    assert not missing.exists()

    path = tmp_path / "existing.jsonl"
    _write_lines(path, [_row("future", expiry=FUTURE)])
    before = path.read_bytes()
    result = export_job_corpus.prune_expired_himalayas_jsonl(path, dry_run=False, now=NOW)
    assert result["expired_pruned"] == 0
    assert path.read_bytes() == before


def test_jsonl_symlink_is_rejected(tmp_path):
    target = tmp_path / "target.jsonl"
    _write_lines(target, [_row()])
    link = tmp_path / "link.jsonl"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        export_job_corpus.prune_expired_himalayas_jsonl(link, dry_run=False, now=NOW)

    dangling = tmp_path / "dangling.jsonl"
    dangling.symlink_to(tmp_path / "absent.jsonl")
    with pytest.raises(ValueError, match="symlink"):
        export_job_corpus.prune_expired_himalayas_jsonl(
            dangling, dry_run=False, now=NOW
        )


def test_jsonl_replace_failure_cleans_private_temp_file(tmp_path, monkeypatch):
    path = tmp_path / "corpus.jsonl"
    _write_lines(path, [_row()])
    monkeypatch.setattr(export_job_corpus.os, "replace", lambda *_args: (_ for _ in ()).throw(OSError("stop")))
    with pytest.raises(OSError):
        export_job_corpus.prune_expired_himalayas_jsonl(path, dry_run=False, now=NOW)
    assert list(tmp_path.glob(".corpus.jsonl.*.tmp")) == []


def test_rag_candidate_scan_is_source_exact_bounded_and_ordered(monkeypatch):
    captured = {}
    monkeypatch.setattr(rag_store, "init_rag_store", lambda: None)

    def query(sql):
        captured["sql"] = sql
        return {"rows": [_row("a"), _row("b")]}

    monkeypatch.setattr(rag_store, "_run_psql_json_query", query)
    result = rag_store.list_himalayas_rag_candidates(after_merge_key="cursor", limit=2)
    assert result["count"] == 2
    assert result["next_cursor"] == "b"
    assert "source = 'himalayas'" in captured["sql"]
    assert "merge_key > 'cursor'" in captured["sql"]
    assert "ORDER BY merge_key ASC" in captured["sql"]
    assert "LIMIT 2" in captured["sql"]
    assert "company" not in captured["sql"].lower()
    with pytest.raises(ValueError):
        rag_store.list_himalayas_rag_candidates(limit=251)


def test_rag_delete_dry_run_and_execute_are_exact(monkeypatch):
    sql_calls = []
    invalidations = []
    monkeypatch.setattr(rag_store, "init_rag_store", lambda: None)
    monkeypatch.setattr(
        rag_store,
        "_run_psql_json_query",
        lambda sql: sql_calls.append(sql) or ({"candidate_count": 1} if "candidate_count" in sql else {"deleted_count": 1}),
    )
    monkeypatch.setattr(rag_store, "_invalidate_rag_document_cache", lambda: invalidations.append(True) or True)

    dry = rag_store.delete_himalayas_rag_merge_keys(["key-1"], dry_run=True)
    assert dry["candidate_count"] == 1
    assert dry["deleted_count"] == 0
    assert invalidations == []
    assert "DELETE FROM" not in sql_calls[0]

    executed = rag_store.delete_himalayas_rag_merge_keys(["key-1"], dry_run=False)
    assert executed["candidate_count"] == 1
    assert executed["deleted_count"] == 1
    assert executed["cache_invalidation_succeeded"] is True
    assert invalidations == [True]
    assert "source = 'himalayas'" in sql_calls[1]
    assert "merge_key IN ('key-1')" in sql_calls[1]


def test_rag_delete_bounds_and_failed_invalidation(monkeypatch):
    monkeypatch.setattr(rag_store, "init_rag_store", lambda: None)
    monkeypatch.setattr(rag_store, "_run_psql_json_query", lambda _sql: {"deleted_count": 0})
    monkeypatch.setattr(rag_store, "_invalidate_rag_document_cache", lambda: False)
    result = rag_store.delete_himalayas_rag_merge_keys(["missing"], dry_run=False)
    assert result["ok"] is False
    assert result["deleted_count"] == 0
    assert result["cache_invalidation_attempted"] is True
    assert result["cache_invalidation_succeeded"] is False
    with pytest.raises(ValueError):
        rag_store.delete_himalayas_rag_merge_keys([str(index) for index in range(251)])
    assert rag_store.delete_himalayas_rag_merge_keys([1, None], dry_run=True)[
        "candidate_count"
    ] == 0


def test_structured_seen_records_preserve_existing_key_and_expiry():
    records = job_cache.structured_seen_records_for_jobs(
        [{"source": "himalayas", "job_id": "himalayas_1", "url": "https://example.test/1", "expiry_date": f" {FUTURE} "}]
    )
    assert records == [
        {
            "seen_key": "himalayas:himalayas_1",
            "source": "himalayas",
            "job_url": "https://example.test/1",
            "job_doc_id": "https://example.test/1",
            "expiry_date": FUTURE,
        }
    ]
    assert job_cache.cache_keys_for_jobs([{"source": "himalayas", "job_id": "himalayas_1"}]) == ["himalayas:himalayas_1"]
    assert job_cache.filter_new_jobs([{"source": "himalayas", "job_id": "himalayas_1"}], set())[1] == ["himalayas:himalayas_1"]


@pytest.mark.parametrize("run_id, expected", [("run-1", "staging"), ("", "promoted")])
def test_structured_seen_save_preserves_expiry_and_staging_mode(monkeypatch, run_id, expected):
    calls = []
    monkeypatch.setenv("JOB_STACK_SEEN_JOBS_BACKEND", "postgres")
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "owner-1")
    if run_id:
        monkeypatch.setenv("JOB_STACK_USER_PIPELINE_RUN_ID", run_id)
    else:
        monkeypatch.delenv("JOB_STACK_USER_PIPELINE_RUN_ID", raising=False)
        monkeypatch.delenv("JOB_APP_PIPELINE_RUN_ID", raising=False)
    monkeypatch.setattr(user_store, "upsert_user_seen_job_staging_postgres_payload", lambda **kwargs: calls.append(("staging", kwargs["record"])))
    monkeypatch.setattr(user_store, "upsert_user_seen_job_postgres_payload", lambda **kwargs: calls.append(("promoted", kwargs["record"])))

    job_cache.save_new_job_records(
        [{"seen_key": "himalayas:himalayas_1", "source": "himalayas", "job_url": "url", "job_doc_id": "doc", "expiry_date": FUTURE}]
    )
    assert calls[0][0] == expected
    assert calls[0][1]["metadata_json"]["expiry_date"] == FUTURE
    assert calls[0][1]["owner_user_id"] == "owner-1"


def test_seen_delete_uses_exact_owner_source_and_keys(monkeypatch):
    sql_calls = []

    def query(**kwargs):
        sql_calls.append(kwargs["sql"])
        if "promoted_candidate_count" in kwargs["sql"]:
            return {"data": {"promoted_candidate_count": 1, "staging_candidate_count": 2}}
        return {"data": {"promoted_deleted_count": 1, "staging_deleted_count": 2}}

    monkeypatch.setattr(user_store, "_run_psql_json_stdin_query", query)
    dry = user_store.delete_himalayas_seen_jobs_exact_postgres_payload(
        owner_user_id="owner-1", seen_keys=["himalayas:himalayas_1"], dry_run=True, ensure_schema=False
    )
    assert (dry["promoted_candidate_count"], dry["staging_candidate_count"]) == (1, 2)
    assert "DELETE FROM" not in sql_calls[0]
    executed = user_store.delete_himalayas_seen_jobs_exact_postgres_payload(
        owner_user_id="owner-1", seen_keys=["himalayas:himalayas_1"], dry_run=False, ensure_schema=False
    )
    assert (executed["promoted_deleted_count"], executed["staging_deleted_count"]) == (1, 2)
    assert sql_calls[1].count("owner_user_id = 'owner-1'") == 2
    assert sql_calls[1].count("source = 'himalayas'") == 2
    assert sql_calls[1].count("seen_key IN ('himalayas:himalayas_1')") == 2
    assert "company" not in sql_calls[1].lower()
    assert "title" not in sql_calls[1].lower()
    with pytest.raises(ValueError):
        user_store.delete_himalayas_seen_jobs_exact_postgres_payload(
            owner_user_id="owner-1", seen_keys=[str(index) for index in range(251)]
        )
    assert user_store.delete_himalayas_seen_jobs_exact_postgres_payload(
        owner_user_id="owner-1", seen_keys=[1, None], dry_run=True
    )["promoted_candidate_count"] == 0


def test_schema_indexes_are_exact_and_no_tables_or_columns_added():
    generated = user_store.render_user_pipeline_schema_sql()
    checked_in = user_store.user_pipeline_schema_sql_text()
    assert generated.strip() == checked_in.strip()
    assert "idx_user_seen_jobs_owner_source_seen_key" in generated
    assert "ON user_seen_jobs (owner_user_id, source, seen_key)" in generated
    assert "idx_user_seen_jobs_staging_owner_source_seen_key" in generated
    assert "ON user_seen_jobs_staging (owner_user_id, source, seen_key)" in generated
    assert "idx_rag_job_documents_source_merge_key" in rag_store._RAG_SCHEMA_SQL
    assert "ON rag_job_documents (source, merge_key)" in rag_store._RAG_SCHEMA_SQL
    assert generated.count("CREATE TABLE IF NOT EXISTS") == 5


def test_foundation_is_injected_ordered_unwired_and_truthful(monkeypatch):
    order = []
    candidates = [_row("expired"), _row("future", expiry=FUTURE)]

    result = retention.run_himalayas_retention_foundation(
        corpus_path="unused.jsonl",
        owner_user_id="owner-1",
        dry_run=True,
        now=NOW,
        jsonl_pruner=lambda *_args, **_kwargs: order.append("jsonl") or {"expired_pruned": 1},
        rag_candidate_lister=lambda **_kwargs: order.append("list") or {"rows": candidates, "next_cursor": "future"},
        rag_deleter=lambda keys, **_kwargs: order.append(("rag", keys)) or {"deleted_count": 0},
        seen_deleter=lambda **kwargs: order.append(("seen", kwargs["seen_keys"])) or {"promoted_deleted_count": 0},
    )
    assert result["ok"] is True
    assert result["cross_store_atomic"] is False
    assert order == ["jsonl", "list", ("rag", ["expired"]), ("seen", ["himalayas:job:expired"])]
    collector = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    main = Path("main.py").read_text(encoding="utf-8")
    assert collector.count("run_himalayas_retention_foundation") == 2
    assert "run_himalayas_retention_foundation" not in main


def test_foundation_reports_partial_failure_without_history_or_network_owners():
    result = retention.run_himalayas_retention_foundation(
        corpus_path="unused.jsonl",
        dry_run=True,
        now=NOW,
        jsonl_pruner=lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("private")),
        rag_candidate_lister=lambda **_kwargs: {"rows": []},
        rag_deleter=lambda *_args, **_kwargs: {"deleted_count": 0},
    )
    assert result["ok"] is False
    assert result["failures"] == [{"surface": "jsonl", "error": "OSError"}]
    source = Path("src/pipeline/himalayas_retention.py").read_text(encoding="utf-8")
    for forbidden in (
        "requests.",
        "operator_decision",
        "application_action",
        "company_title",
        "src.scrapers",
    ):
        assert forbidden not in source
