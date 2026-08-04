from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.app import services
from src.pipeline import collector
from src.utils.job_cache import cache_keys_for_jobs, structured_seen_records_for_jobs


FLAG = "APPLYLENS_HIMALAYAS_ACTIVE_RETENTION_ENABLED"
NOW = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
EXPIRED = "2026-08-05T12:00:00Z"
FUTURE = "2026-08-06T12:00:00Z"


def _success_result(*, with_owner: bool = False):
    seen = (
        {
            "ok": True,
            "promoted_deleted_count": 2,
            "staging_deleted_count": 1,
        }
        if with_owner
        else {"attempted": False, "reason": "owner_not_requested"}
    )
    return {
        "ok": True,
        "dry_run": False,
        "cross_store_atomic": False,
        "failures": [],
        "surfaces": {
            "jsonl": {
                "inspected": 4,
                "expired_pruned": 1,
                "missing_or_invalid_expiry": 1,
                "malformed_lines": 1,
            },
            "rag_candidates": {"count": 3, "next_cursor_present": True},
            "rag_delete": {"ok": True, "deleted_count": 1},
            "rag_expiry_summary": {
                "inspected": 3,
                "eligible_expired": 1,
                "missing_or_invalid_expiry": 1,
            },
            "seen_delete": seen,
        },
    }


def test_disabled_preserves_export_completion_and_key_only_seen_path(tmp_path):
    order = []
    env = {}
    jobs = [{"source": "himalayas", "job_id": "himalayas_1"}]
    corpus = tmp_path / "corpus.jsonl"

    counts = collector._complete_rag_export_with_optional_himalayas_retention(
        jobs,
        str(corpus),
        export_owner=lambda *_args: order.append("export") or 1,
        env=env,
        retention_owner=lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("retention must remain unconstructed")
        ),
        stage_completer=lambda *_args, **_kwargs: order.append("complete"),
    )
    collector._save_seen_jobs_with_optional_himalayas_expiry(
        jobs,
        env=env,
        cache_key_owner=lambda values: cache_keys_for_jobs(values),
        key_save_owner=lambda keys: order.append(("keys", keys)),
        structured_record_owner=lambda _values: (_ for _ in ()).throw(
            AssertionError("structured records must remain unconstructed")
        ),
        structured_save_owner=lambda _records: order.append("structured"),
    )

    assert counts == {"rag_export_count": 1}
    assert order == ["export", "complete", ("keys", ["himalayas:himalayas_1"])]
    assert collector._himalayas_active_retention_enabled({}) is False


def test_enabled_orders_export_cleanup_completion_then_one_structured_save(tmp_path):
    order = []
    env = {FLAG: "true"}
    jobs = [
        {
            "source": "himalayas",
            "job_id": "himalayas_1",
            "expiry_date": FUTURE,
        },
        {"source": "greenhouse", "job_id": "greenhouse_1", "expiry_date": FUTURE},
    ]

    def retain(**kwargs):
        order.append(("cleanup", kwargs))
        return _success_result()

    counts = collector._complete_rag_export_with_optional_himalayas_retention(
        jobs,
        str(tmp_path / "corpus.jsonl"),
        export_owner=lambda *_args: order.append("export") or 2,
        env=env,
        retention_owner=retain,
        clock_owner=lambda: NOW,
        stage_completer=lambda stage, **kwargs: order.append(
            ("complete", stage, kwargs["counts"])
        ),
    )
    saved = []
    collector._save_seen_jobs_with_optional_himalayas_expiry(
        jobs,
        env=env,
        cache_key_owner=cache_keys_for_jobs,
        key_save_owner=lambda _keys: order.append("key_save"),
        structured_record_owner=structured_seen_records_for_jobs,
        structured_save_owner=lambda records: saved.append(records) or order.append(
            "structured_save"
        ),
    )

    cleanup_call = order[1][1]
    assert order[0] == "export"
    assert order[1][0] == "cleanup"
    assert order[2][0:2] == ("complete", "rag_export")
    assert order[3] == "structured_save"
    assert cleanup_call == {
        "corpus_path": str(tmp_path / "corpus.jsonl"),
        "owner_user_id": "",
        "dry_run": False,
        "batch_size": 250,
        "now": NOW,
    }
    assert counts["rag_export_count"] == 2
    assert counts["himalayas_retention_inspected"] == 7
    assert counts["himalayas_retention_jsonl_pruned"] == 1
    assert counts["himalayas_retention_invalid_expiry_skipped"] == 3
    assert [row["seen_key"] for row in saved[0]] == cache_keys_for_jobs(jobs)
    assert saved[0][0]["expiry_date"] == FUTURE
    assert saved[0][1]["expiry_date"] == ""
    assert "key_save" not in order


def test_enabled_cleanup_runs_for_empty_jobs_after_existing_corpus_preservation(tmp_path):
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text("existing\n", encoding="utf-8")
    order = []
    collector._complete_rag_export_with_optional_himalayas_retention(
        [],
        str(corpus),
        export_owner=lambda *_args: order.append("unexpected_export") or 0,
        env={FLAG: "1"},
        retention_owner=lambda **_kwargs: order.append("cleanup")
        or _success_result(),
        clock_owner=lambda: NOW,
        stage_completer=lambda *_args, **_kwargs: order.append("complete"),
    )
    assert order == ["cleanup", "complete"]


@pytest.mark.parametrize(
    "result",
    [
        {"ok": False, "failures": [{"surface": "jsonl"}], "surfaces": {}},
        {
            **_success_result(),
            "surfaces": {
                **_success_result()["surfaces"],
                "rag_delete": {"ok": False, "deleted_count": 1},
            },
        },
    ],
)
def test_cleanup_failure_raises_before_stage_completion_or_seen_save(tmp_path, result):
    order = []
    with pytest.raises(RuntimeError, match="Himalayas active retention"):
        collector._complete_rag_export_with_optional_himalayas_retention(
            [],
            str(tmp_path / "corpus.jsonl"),
            export_owner=lambda *_args: order.append("export") or 0,
            env={FLAG: "yes"},
            retention_owner=lambda **_kwargs: order.append("cleanup") or result,
            clock_owner=lambda: NOW,
            stage_completer=lambda *_args, **_kwargs: order.append("complete"),
        )
    assert order == ["export", "cleanup"]
    assert "complete" not in order
    assert "structured_save" not in order
    assert "key_save" not in order


def test_postgres_seen_backend_requires_owner_before_cleanup_or_structured_save(tmp_path):
    env = {FLAG: "on", "JOB_STACK_SEEN_JOBS_BACKEND": "postgres"}
    calls = []
    with pytest.raises(RuntimeError, match="requires an owner"):
        collector._complete_rag_export_with_optional_himalayas_retention(
            [],
            str(tmp_path / "corpus.jsonl"),
            export_owner=lambda *_args: 0,
            env=env,
            retention_owner=lambda **_kwargs: calls.append("cleanup") or _success_result(),
            stage_completer=lambda *_args, **_kwargs: calls.append("complete"),
        )
    with pytest.raises(RuntimeError, match="requires an owner"):
        collector._save_seen_jobs_with_optional_himalayas_expiry(
            [],
            env=env,
            cache_key_owner=lambda _jobs: [],
            key_save_owner=lambda _keys: calls.append("keys"),
            structured_record_owner=lambda _jobs: [],
            structured_save_owner=lambda _records: calls.append("structured"),
        )
    assert calls == []


def test_services_active_overlay_filters_only_exact_expired_himalayas(monkeypatch):
    monkeypatch.setenv(FLAG, "true")
    monkeypatch.setattr(services, "_himalayas_retention_utc_now", lambda: NOW)
    monkeypatch.setattr(
        services,
        "_application_row_key_candidates",
        lambda row: [str(row.get("job_doc_id", ""))] if row.get("job_doc_id") else [],
    )
    rows = [
        {"job_doc_id": "expired", "source": "himalayas"},
        {"job_doc_id": "future", "source": "himalayas"},
        {"job_doc_id": "invalid", "source": "himalayas"},
        {"source": "himalayas", "expiry_date": EXPIRED},
        {"job_doc_id": "direct", "source": "greenhouse"},
    ]
    overlays = {
        "expired": {"source": "himalayas", "expiry_date": EXPIRED},
        "future": {"source": "himalayas", "expiry_date": FUTURE},
        "invalid": {"source": "himalayas", "expiry_date": "bad"},
        "direct": {"source": "himalayas", "expiry_date": EXPIRED},
    }
    result = services._overlay_job_metadata_from_map(rows, overlays)

    assert [row.get("job_doc_id", "") for row in result] == [
        "future",
        "invalid",
        "",
        "direct",
    ]
    assert result[0]["expiry_date"] == FUTURE
    assert result[-1]["source"] == "greenhouse"
    assert result[-1].get("expiry_date", "") == ""


def test_services_disabled_overlay_and_filter_are_exact_noops(monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    rows = [{"job_doc_id": "expired", "source": "himalayas", "expiry_date": EXPIRED}]
    assert services._filter_expired_himalayas_active_rows(rows) is rows
    target = dict(rows[0])
    services._apply_himalayas_retention_metadata(
        target, {"source": "himalayas", "expiry_date": FUTURE}
    )
    assert target == rows[0]


def test_current_status_path_filters_after_metadata_but_history_owner_is_untouched():
    source = Path("src/app/services.py").read_text(encoding="utf-8")
    status_start = source.index("def status_payload(")
    browse_start = source.index("def browse_payload(")
    status_source = source[status_start:browse_start]
    assert "_filter_expired_himalayas_active_rows(top_queue)" in status_source

    history_start = source.index("def profile_pipeline_run_detail_payload(")
    history_end = source.index("def profile_pipeline_run_agentic_review_payload(")
    history_source = source[history_start:history_end]
    assert "_filter_expired_himalayas_active_rows" not in history_source
    assert "classify_expired_record" not in history_source


def test_no_new_stage_provider_or_retirement_path_is_introduced():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    assert source.count('start_stage("rag_export"') == 1
    assert "start_stage(\"himalayas_retention\"" not in source
    helper_start = source.index(
        "def _complete_rag_export_with_optional_himalayas_retention("
    )
    helper_end = source.index(
        "def _save_seen_jobs_with_optional_himalayas_expiry("
    )
    helper_source = source[helper_start:helper_end]
    for forbidden in ("requests.", "scrape_all_himalayas", "retire_source"):
        assert forbidden not in helper_source
    assert collector.HIMALAYAS_ACTIVE_RETENTION_FLAG == FLAG
    assert collector._himalayas_active_retention_enabled({}) is False
