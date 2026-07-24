from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import main as production
from src.pipeline import postgres_planning_corpus_snapshot as snapshot_module


def _job(job_id: str, *, title: str = "Engineer") -> dict:
    return {
        "doc_id": job_id,
        "title": title,
        "company": "Synthetic",
        "retrieval_text": "bounded synthetic record",
    }


def _args(tmp_path: Path, *, source: str = "filesystem") -> SimpleNamespace:
    return SimpleNamespace(
        application_planning_only=True,
        application_planning_corpus_source=source,
        run_application_planning=True,
        application_planning_job_limit=10,
        application_planning_job_packet_limit=10,
        application_planning_output_dir=str(tmp_path / "planning"),
        application_planning_llm_actions="APPLY",
        application_planning_generate_tailoring=False,
        application_planning_generate_llm_tailoring=False,
        application_planning_refresh_llm_tailoring=False,
        application_planning_generate_llm_fallback=False,
        application_planning_generate_llm_adjudication=False,
        delete_seen_data="no",
    )


def _patch_authoritative_flow(
    monkeypatch: pytest.MonkeyPatch,
    snapshot: snapshot_module.PostgresPlanningCorpusSnapshot,
    events: list[str],
    *,
    failure_at: str = "",
) -> None:
    monkeypatch.setenv("JOB_STACK_USER_PIPELINE_MODE", "true")
    monkeypatch.setenv(
        "APPLYLENS_DURABLE_EVIDENCE_CHAIN_SHADOW_ENABLED", "true"
    )
    monkeypatch.setattr(production, "initialize_run", lambda **_kw: None)
    monkeypatch.setattr(production, "start_stage", lambda *_a, **_kw: None)
    monkeypatch.setattr(production, "complete_stage", lambda *_a, **_kw: None)
    monkeypatch.setattr(production, "update_config", lambda **_kw: None)
    monkeypatch.setattr(production, "update_counts", lambda **_kw: None)

    def assert_live(event: str) -> None:
        assert snapshot.corpus_path.is_file()
        events.append(event)
        if failure_at == event:
            raise RuntimeError(f"{event}_failed")

    monkeypatch.setattr(
        production,
        "_run_application_planning",
        lambda *_a, **_kw: assert_live("planning"),
    )
    monkeypatch.setattr(
        production,
        "_load_jobs_from_corpus",
        lambda path: [json.loads(Path(path).read_text().splitlines()[0])],
    )
    monkeypatch.setattr(production, "_load_best_variant_lookup", lambda _p: {})
    monkeypatch.setattr(production, "_load_execution_queue_lookup", lambda _p: {})
    monkeypatch.setattr(production, "_load_packet_manifest_lookup", lambda _p: {})
    monkeypatch.setattr(
        production,
        "_merge_application_planning_into_jobs",
        lambda *_a, **_kw: assert_live("merge") or 1,
    )
    monkeypatch.setattr(
        production,
        "_application_planning_summary_message",
        lambda _count: "done",
    )
    monkeypatch.setattr(
        production,
        "finish_run",
        lambda **_kw: assert_live("finish"),
    )

    class ShadowLifecycle:
        planning_arguments = ["bounded-projection"]

        def cleanup(self):
            events.append("shadow_cleanup")

        def complete_after_authoritative_success(self, **_kwargs):
            assert_live("shadow")

    from src.pipeline import post_planning_shadow

    monkeypatch.setattr(
        post_planning_shadow,
        "prepare_post_planning_shadow",
        lambda: ShadowLifecycle(),
    )


def test_default_filesystem_source_never_constructs_postgres_snapshot(
    tmp_path, monkeypatch
):
    called = []
    monkeypatch.setattr(
        snapshot_module,
        "create_postgres_planning_corpus_snapshot",
        lambda *_a, **_kw: called.append(True),
    )

    async def core(_args, *, postgres_snapshot=None):
        assert postgres_snapshot is None

    monkeypatch.setattr(production, "_main_async", core)
    asyncio.run(production.main_async(_args(tmp_path)))
    assert called == []


@pytest.mark.parametrize(
    ("run_planning", "planning_only"),
    [(False, False), (True, False), (False, True)],
)
def test_postgres_source_requires_both_planning_flags(
    tmp_path, run_planning, planning_only
):
    args = _args(tmp_path, source="postgres")
    args.run_application_planning = run_planning
    args.application_planning_only = planning_only
    with pytest.raises(SystemExit):
        production._validate_application_planning_only_args(args)


def test_argparse_defaults_to_filesystem(monkeypatch):
    monkeypatch.setattr("sys.argv", ["main.py"])
    args = production._parse_args()
    assert args.application_planning_corpus_source == "filesystem"


def test_postgres_planning_command_marks_private_corpus_path_for_redaction(
    tmp_path, monkeypatch
):
    captured = {}
    private_path = str(tmp_path / "private.jsonl")
    monkeypatch.setattr(
        production,
        "_run_cmd",
        lambda cmd, **kwargs: captured.update(
            cmd=list(cmd), kwargs=dict(kwargs)
        ),
    )
    production._run_application_planning(
        _args(tmp_path, source="postgres"),
        job_corpus_path=private_path,
    )
    assert captured["kwargs"]["redact_values"] == [private_path]


def test_bounded_reader_order_validation_and_deduplication():
    requested = []
    rows = [
        _job("job-2"),
        None,
        _job("job-1"),
        _job("job-2", title="Duplicate"),
        {},
        _job("job-3"),
    ]

    def reader(*, limit):
        requested.append(limit)
        return rows

    lifecycle = snapshot_module.create_postgres_planning_corpus_snapshot(
        10, reader=reader
    )
    try:
        emitted = [
            json.loads(line)
            for line in lifecycle.corpus_path.read_text(
                encoding="utf-8"
            ).splitlines()
        ]
        assert requested == [10]
        assert [row["job_doc_id"] for row in emitted] == [
            "job-2",
            "job-1",
            "job-3",
        ]
        assert lifecycle.counts.requested == 10
        assert lifecycle.counts.fetched == 6
        assert lifecycle.counts.emitted == 3
        assert lifecycle.counts.invalid_rejected == 2
        assert lifecycle.counts.duplicate_rejected == 1
    finally:
        lifecycle.cleanup()


def test_requested_limit_ten_emits_no_more_than_ten():
    rows = [_job(f"job-{index}") for index in range(20)]
    lifecycle = snapshot_module.create_postgres_planning_corpus_snapshot(
        10, reader=lambda *, limit: rows[:limit]
    )
    try:
        assert lifecycle.counts.requested == 10
        assert lifecycle.counts.fetched == 10
        assert lifecycle.counts.emitted == 10
        assert len(lifecycle.corpus_path.read_text().splitlines()) == 10
    finally:
        lifecycle.cleanup()


def test_zero_limit_uses_hard_ceiling():
    requested = []
    lifecycle = snapshot_module.create_postgres_planning_corpus_snapshot(
        0,
        reader=lambda *, limit: requested.append(limit)
        or [_job("job-1")],
    )
    try:
        assert requested == [snapshot_module.MAX_POSTGRES_SNAPSHOT_JOBS]
        assert lifecycle.counts.requested == 50
    finally:
        lifecycle.cleanup()


@pytest.mark.parametrize(
    ("rows", "code"),
    [
        ([], "postgres_snapshot_empty"),
        ([None, {}], "postgres_snapshot_no_usable_documents"),
    ],
)
def test_empty_or_unusable_results_fail_closed(rows, code):
    with pytest.raises(
        snapshot_module.PostgresPlanningCorpusSnapshotError, match=code
    ):
        snapshot_module.create_postgres_planning_corpus_snapshot(
            10, reader=lambda *, limit: rows
        )


def test_snapshot_permissions_and_idempotent_cleanup():
    lifecycle = snapshot_module.create_postgres_planning_corpus_snapshot(
        1, reader=lambda *, limit: [_job("job-1")]
    )
    directory = lifecycle.directory
    assert directory.stat().st_mode & 0o777 == 0o700
    assert lifecycle.corpus_path.stat().st_mode & 0o777 == 0o600
    assert lifecycle.cleanup() is True
    assert lifecycle.cleanup() is True
    assert not directory.exists()


def test_unsafe_existing_snapshot_symlink_is_rejected(tmp_path):
    target = tmp_path / "target"
    target.write_text("keep", encoding="utf-8")
    path = tmp_path / "planning_corpus.jsonl"
    path.symlink_to(target)
    with pytest.raises(
        snapshot_module.PostgresPlanningCorpusSnapshotError,
        match="postgres_snapshot_unsafe_storage",
    ):
        snapshot_module._write_snapshot(tmp_path, b"{}\n")
    assert target.read_text(encoding="utf-8") == "keep"


def test_serialization_bound_fails_before_temporary_storage(monkeypatch):
    monkeypatch.setattr(snapshot_module, "MAX_POSTGRES_SNAPSHOT_BYTES", 10)
    with pytest.raises(
        snapshot_module.PostgresPlanningCorpusSnapshotError,
        match="postgres_snapshot_serialization_limit_exceeded",
    ):
        snapshot_module.create_postgres_planning_corpus_snapshot(
            1, reader=lambda *, limit: [_job("job-1")]
        )


def test_adapter_source_has_no_write_owner():
    source = Path(snapshot_module.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "export_job_corpus",
        "upsert_rag_job_documents",
        "record_pipeline_run",
        "application_actions",
        "ats_submission",
        "finalize(",
    ):
        assert forbidden not in source


def test_snapshot_lives_through_planning_merge_finish_and_shadow(
    tmp_path, monkeypatch
):
    lifecycle = snapshot_module.create_postgres_planning_corpus_snapshot(
        1, reader=lambda *, limit: [_job("job-1")]
    )
    events = []
    _patch_authoritative_flow(monkeypatch, lifecycle, events)
    monkeypatch.setattr(
        snapshot_module,
        "create_postgres_planning_corpus_snapshot",
        lambda _limit: lifecycle,
    )
    asyncio.run(production.main_async(_args(tmp_path, source="postgres")))
    assert events == ["planning", "merge", "finish", "shadow"]
    assert lifecycle.cleanup_complete is True
    assert not lifecycle.directory.exists()


@pytest.mark.parametrize("failure_at", ["planning", "merge", "finish", "shadow"])
def test_snapshot_cleanup_on_every_authoritative_failure(
    tmp_path, monkeypatch, failure_at
):
    lifecycle = snapshot_module.create_postgres_planning_corpus_snapshot(
        1, reader=lambda *, limit: [_job("job-1")]
    )
    events = []
    _patch_authoritative_flow(
        monkeypatch, lifecycle, events, failure_at=failure_at
    )
    monkeypatch.setattr(
        snapshot_module,
        "create_postgres_planning_corpus_snapshot",
        lambda _limit: lifecycle,
    )
    args = _args(tmp_path, source="postgres")
    if failure_at == "shadow":
        asyncio.run(production.main_async(args))
    else:
        with pytest.raises(RuntimeError, match=f"{failure_at}_failed"):
            asyncio.run(production.main_async(args))
    assert lifecycle.cleanup_complete is True
    assert not lifecycle.directory.exists()
