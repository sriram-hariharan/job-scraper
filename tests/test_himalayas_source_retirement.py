from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import manage_himalayas_retention as command
from src.app import services
from src.pipeline import himalayas_retention as retention
from src.rag import export_job_corpus
from src.storage import rag_store
from src.storage.user_pipeline import store as user_store


NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
EXPIRED = "2026-08-05T12:00:00Z"


def _command_result(*, dry_run=True):
    return {
        "ok": True,
        "dry_run": dry_run,
        "cross_store_atomic": False,
        "failures": [],
        "surfaces": {
            "jsonl_preflight": {
                "retirement_candidates": 2,
                "missing_identity": 1,
                "malformed_records": 1,
            },
            "rag_candidates": {"candidate_count": 2},
            "seen_candidates": {"candidate_count": 2},
            "rag": {
                "candidate_count": 2,
                "deleted_count": 0 if dry_run else 2,
                "cache_invalidation_succeeded": not dry_run,
            },
            "seen": {
                "promoted_candidate_count": 1,
                "staging_candidate_count": 1,
                "promoted_deleted_count": 0 if dry_run else 1,
                "staging_deleted_count": 0 if dry_run else 1,
            },
        },
    }


def test_command_defaults_to_dry_run_and_prints_only_bounded_counts(capsys):
    args = command.build_parser().parse_args([])
    calls = []
    result = command.run_command(
        args,
        retirement_owner=lambda **kwargs: calls.append(kwargs) or _command_result(),
    )
    summary = command.public_summary(result)
    assert calls == [
        {
            "corpus_path": command.DEFAULT_CORPUS_PATH,
            "owner_user_id": "",
            "dry_run": True,
            "batch_size": 250,
            "database_url_env": "DATABASE_URL",
        }
    ]
    assert summary["mode"] == "dry_run"
    assert summary["total_eligible"] == 6
    assert summary["failures"] == 0
    rendered = json.dumps(summary, sort_keys=True)
    for forbidden in ("https://", "merge_key", "seen_key", "password", "description"):
        assert forbidden not in rendered
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    "argv",
    [
        ["--execute"],
        ["--execute", "--confirm-source", "other", "--owner-user-id", "owner"],
        ["--confirm-source", "other"],
        ["--batch-size", "0"],
        ["--batch-size", "251"],
    ],
)
def test_command_rejects_missing_or_wrong_confirmation_and_unsafe_bounds(argv):
    args = command.build_parser().parse_args(argv)
    with pytest.raises(ValueError):
        command.run_command(
            args,
            retirement_owner=lambda **_kwargs: (_ for _ in ()).throw(
                AssertionError("validation must precede owners")
            ),
        )


def test_execute_requires_owner_and_exact_confirmation_before_owner_call():
    args = command.build_parser().parse_args(
        ["--execute", "--confirm-source", "himalayas"]
    )
    with pytest.raises(ValueError, match="owner"):
        command.run_command(args, retirement_owner=lambda **_kwargs: {})

    args = command.build_parser().parse_args(
        [
            "--execute",
            "--confirm-source",
            "himalayas",
            "--owner-user-id",
            "owner-1",
        ]
    )
    calls = []
    result = command.run_command(
        args,
        retirement_owner=lambda **kwargs: calls.append(kwargs)
        or _command_result(dry_run=False),
    )
    assert result["dry_run"] is False
    assert calls[0]["owner_user_id"] == "owner-1"


def test_retirement_classifier_is_exact_identity_only_and_expiry_independent():
    assert retention.classify_retirement_record(
        {"source": "himalayas", "job_id": "himalayas_1"}
    )["eligible"] is True
    assert retention.classify_retirement_record(
        {"source": "greenhouse", "job_id": "himalayas_1"}
    )["reason"] == "unmanaged_source"
    assert retention.classify_retirement_record(
        {"source": "himalayas", "company": "A", "title": "B"}
    )["reason"] == "missing_identity"
    assert retention.classify_retirement_record(
        {"source": "himalayas", "job_id": "himalayas_2", "expiry_date": "bad"}
    )["eligible"] is True
    assert retention.classify_expired_record(
        {"source": "himalayas", "job_id": "himalayas_2", "expiry_date": "bad"},
        now=NOW,
    )["eligible"] is False


def _write_jsonl(path: Path, rows):
    path.write_text(
        "".join(row if isinstance(row, str) else json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_jsonl_retirement_dry_run_execute_and_repeat_are_exact(tmp_path):
    path = tmp_path / "corpus.jsonl"
    malformed = "{malformed\n"
    _write_jsonl(
        path,
        [
            {"source": "himalayas", "doc_id": "retire-me"},
            {"source": "himalayas", "company": "A", "title": "B"},
            {"source": "greenhouse", "doc_id": "keep-me"},
            malformed,
        ],
    )
    before = path.read_bytes()
    dry = export_job_corpus.retire_himalayas_jsonl(path, dry_run=True)
    assert path.read_bytes() == before
    assert dry["retirement_candidates"] == 1
    assert dry["retired"] == 0
    assert dry["missing_identity"] == 1
    assert dry["malformed_records"] == 1
    assert dry["write_performed"] is False

    executed = export_job_corpus.retire_himalayas_jsonl(path, dry_run=False)
    assert executed["retired"] == 1
    assert executed["write_performed"] is True
    text = path.read_text(encoding="utf-8")
    assert "retire-me" not in text
    assert "keep-me" in text
    assert malformed in text
    repeated = export_job_corpus.retire_himalayas_jsonl(path, dry_run=False)
    assert repeated["retired"] == 0
    assert repeated["write_performed"] is False


def test_jsonl_retirement_rejects_symlink(tmp_path):
    target = tmp_path / "target.jsonl"
    _write_jsonl(target, [{"source": "himalayas", "doc_id": "one"}])
    link = tmp_path / "link.jsonl"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        export_job_corpus.retire_himalayas_jsonl(link, dry_run=False)


def test_seen_candidate_listing_is_owner_source_exact_bounded_and_ordered(monkeypatch):
    captured = {}

    def query(**kwargs):
        captured["sql"] = kwargs["sql"]
        return {"data": {"rows": [{"seen_key": "himalayas:1"}]}}

    monkeypatch.setattr(user_store, "_run_psql_json_stdin_query", query)
    result = user_store.list_himalayas_seen_job_candidates_postgres_payload(
        owner_user_id="owner-1",
        after_seen_key="cursor",
        limit=5,
        ensure_schema=False,
    )
    assert result["count"] == 1
    assert result["next_cursor"] == "himalayas:1"
    assert captured["sql"].count("owner_user_id = 'owner-1'") == 2
    assert captured["sql"].count("source = 'himalayas'") == 2
    assert captured["sql"].count("seen_key > 'cursor'") == 2
    assert "ORDER BY seen_key ASC" in captured["sql"]
    assert "LIMIT 5" in captured["sql"]
    assert "company" not in captured["sql"].lower()
    assert "title" not in captured["sql"].lower()
    with pytest.raises(ValueError):
        user_store.list_himalayas_seen_job_candidates_postgres_payload(
            owner_user_id="owner-1", limit=251
        )


def test_rag_retirement_uses_existing_bounded_exact_source_and_cache_contract(monkeypatch):
    sql_calls = []
    invalidations = []
    monkeypatch.setattr(rag_store, "init_rag_store", lambda: None)
    monkeypatch.setattr(
        rag_store,
        "_run_psql_json_query",
        lambda sql: sql_calls.append(sql)
        or ({"rows": [{"merge_key": "m1", "source": "himalayas"}]} if "WITH candidates" in sql else {"deleted_count": 1}),
    )
    monkeypatch.setattr(
        rag_store,
        "_invalidate_rag_document_cache",
        lambda: invalidations.append(True) or True,
    )
    listed = rag_store.list_himalayas_rag_candidates(limit=1)
    dry = rag_store.delete_himalayas_rag_merge_keys(["m1"], dry_run=True)
    executed = rag_store.delete_himalayas_rag_merge_keys(["m1"], dry_run=False)
    assert listed["count"] == 1
    assert dry["deleted_count"] == 0
    assert executed["deleted_count"] == 1
    assert invalidations == [True]
    assert "source = 'himalayas'" in sql_calls[-1]
    assert "merge_key IN ('m1')" in sql_calls[-1]


def test_retirement_orchestration_preflights_then_executes_in_exact_order():
    order = []
    result = retention.run_himalayas_source_retirement(
        corpus_path="unused.jsonl",
        owner_user_id="owner-1",
        dry_run=False,
        batch_size=2,
        jsonl_retirement_owner=lambda *_args, **kwargs: order.append(
            "jsonl_dry" if kwargs["dry_run"] else "jsonl_execute"
        )
        or {
            "retirement_candidates": 1,
            "retired": 1 if not kwargs["dry_run"] else 0,
        },
        rag_candidate_lister=lambda **_kwargs: order.append("rag_list")
        or {"ok": True, "rows": [{"merge_key": "m1", "source": "himalayas"}]},
        rag_deleter=lambda keys, **kwargs: order.append(
            ("rag_delete", keys, kwargs["dry_run"])
        )
        or {"ok": True, "deleted_count": 1},
        seen_candidate_lister=lambda **_kwargs: order.append("seen_list")
        or {"ok": True, "rows": [{"seen_key": "himalayas:1"}]},
        seen_deleter=lambda **kwargs: order.append(
            ("seen_delete", kwargs["seen_keys"], kwargs["dry_run"])
        )
        or {"ok": True, "promoted_deleted_count": 1, "staging_deleted_count": 0},
    )
    assert result["ok"] is True
    assert result["cross_store_atomic"] is False
    assert order == [
        "jsonl_dry",
        "rag_list",
        "seen_list",
        "jsonl_execute",
        ("rag_delete", ["m1"], False),
        ("seen_delete", ["himalayas:1"], False),
    ]


def test_dry_run_orchestration_performs_no_execute_or_invalidation():
    order = []
    result = retention.run_himalayas_source_retirement(
        corpus_path="unused.jsonl",
        owner_user_id="owner-1",
        dry_run=True,
        jsonl_retirement_owner=lambda *_args, **kwargs: order.append(
            ("jsonl", kwargs["dry_run"])
        )
        or {"retirement_candidates": 1},
        rag_candidate_lister=lambda **_kwargs: {"ok": True, "rows": []},
        rag_deleter=lambda _keys, **kwargs: order.append(("rag", kwargs["dry_run"]))
        or {"ok": True},
        seen_candidate_lister=lambda **_kwargs: {"ok": True, "rows": []},
        seen_deleter=lambda **kwargs: order.append(("seen", kwargs["dry_run"]))
        or {"ok": True, "promoted_candidate_count": 0, "staging_candidate_count": 0},
    )
    assert result["ok"] is True
    assert order == [("jsonl", True), ("rag", True), ("seen", True)]


def test_required_rag_failure_is_truthful_and_stops_seen_delete():
    order = []
    result = retention.run_himalayas_source_retirement(
        corpus_path="unused.jsonl",
        owner_user_id="owner-1",
        dry_run=False,
        jsonl_retirement_owner=lambda *_args, **kwargs: {"retirement_candidates": 1},
        rag_candidate_lister=lambda **_kwargs: {"ok": True, "rows": [{"merge_key": "m1", "source": "himalayas"}]},
        rag_deleter=lambda *_args, **_kwargs: {"ok": False, "deleted_count": 1},
        seen_candidate_lister=lambda **_kwargs: {"ok": True, "rows": [{"seen_key": "himalayas:1"}]},
        seen_deleter=lambda **_kwargs: order.append("unsafe_seen_delete") or {"ok": True},
    )
    assert result["ok"] is False
    assert result["failures"] == [{"surface": "rag", "error": "operation_failed"}]
    assert order == []


def test_active_identity_filter_is_exact_and_fail_open(monkeypatch):
    monkeypatch.setenv("APPLYLENS_HIMALAYAS_ACTIVE_RETENTION_ENABLED", "true")
    monkeypatch.setattr(services, "_himalayas_retention_utc_now", lambda: NOW)
    rows = [
        {"source": "himalayas", "job_doc_id": "active", "expiry_date": "2026-08-07T00:00:00Z"},
        {"source": "himalayas", "job_doc_id": "retired", "expiry_date": "2026-08-07T00:00:00Z"},
        {"source": "himalayas", "expiry_date": "2026-08-07T00:00:00Z"},
        {"source": "greenhouse", "job_doc_id": "retired", "expiry_date": EXPIRED},
    ]
    filtered = services._filter_expired_himalayas_active_rows(
        rows,
        active_identities=frozenset({"active"}),
    )
    assert [row.get("job_doc_id", "") for row in filtered] == ["active", "", "retired"]
    assert services._filter_expired_himalayas_active_rows(
        rows,
        active_identities=None,
    ) == rows


def test_active_identity_authority_is_bounded_and_unavailable_fail_open(tmp_path, monkeypatch):
    monkeypatch.setenv("APPLYLENS_HIMALAYAS_ACTIVE_RETENTION_ENABLED", "true")
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        services,
        "_load_job_metadata_overlay_from_corpus",
        lambda _path: {
            "one": {"source": "himalayas", "active_identity": "active"},
            "two": {"source": "greenhouse", "active_identity": "direct"},
        },
    )
    assert services._active_himalayas_identity_authority(corpus) == frozenset({"active"})
    monkeypatch.setattr(
        services,
        "_load_job_metadata_overlay_from_corpus",
        lambda _path: (_ for _ in ()).throw(OSError("unavailable")),
    )
    assert services._active_himalayas_identity_authority(corpus) is None


def test_history_and_automatic_pipeline_do_not_invoke_retirement_command():
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")
    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    main_source = Path("main.py").read_text(encoding="utf-8")
    history_start = services_source.index("def profile_pipeline_run_detail_payload(")
    history_end = services_source.index("def profile_pipeline_run_agentic_review_payload(")
    history = services_source[history_start:history_end]
    assert "active_himalayas_identity_authority" not in history
    assert "source_retirement" not in collector_source
    assert "manage_himalayas_retention" not in collector_source
    assert "manage_himalayas_retention" not in main_source
    for forbidden in ("operator_decision", "application_action", "requests."):
        assert forbidden not in Path("src/pipeline/himalayas_retention.py").read_text(
            encoding="utf-8"
        )


def test_bounded_himalayas_profile_usajobs_active_and_no_new_stage():
    assert json.loads(Path("src/config/himalayas_query_profiles.json").read_text()) == [
        {
            "profile_id": "data-us",
            "query": "data",
            "country": "US",
            "exclude_worldwide": True,
            "sort": "recent",
        }
    ]
    assert json.loads(Path("src/config/usajobs_query_profiles.json").read_text()) == [
        {
            "profile_id": "public-it-data-us",
            "keyword": "",
            "location_name": "",
            "organization_codes": [],
            "job_category_codes": [
                "0391",
                "0854",
                "0855",
                "1515",
                "1529",
                "1530",
                "1550",
                "1560",
                "2210",
            ],
            "remote_only": False,
        }
    ]
    curated = json.loads(Path("src/config/curated_ats_sources.json").read_text())
    assert curated["personio"] == []
    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    assert collector_source.count('start_stage("rag_export"') == 1
    assert "start_stage(\"himalayas_retirement\"" not in collector_source
