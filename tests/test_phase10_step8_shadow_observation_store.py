from __future__ import annotations

from datetime import date
import json
import os
from pathlib import Path
import stat

import pytest

from src.pipeline import shadow_observation_store as store_module
from src.pipeline.shadow_observation_store import ShadowObservationStore
from tests.test_phase10_step8_shadow_observation_contract import valid_record


def _store(tmp_path: Path, *, today: date = date(2026, 7, 24)):
    return ShadowObservationStore(tmp_path / "observations", today=today)


def _identity(**overrides):
    values = {
        "owner_id": "synthetic-owner",
        "pipeline_run_id": "synthetic-run",
        "context_id": "synthetic-context",
    }
    values.update(overrides)
    return values


def _record_for(store: ShadowObservationStore, **identity):
    return valid_record(observation_key=store.observation_key(**identity))


def test_import_and_construction_have_no_filesystem_side_effect(tmp_path):
    root = tmp_path / "observations"
    ShadowObservationStore(root)
    assert not root.exists()


def test_lazy_permissions_key_stability_and_identity_exclusion(tmp_path):
    store = _store(tmp_path)
    key = store.observation_key(**_identity())
    assert key == store.observation_key(**_identity())
    assert key != store.observation_key(
        **_identity(pipeline_run_id="synthetic-run-two")
    )
    result = store.append(valid_record(observation_key=key))
    assert result.status == "stored"
    root = store.root
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    for path in root.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    rendered = next(root.glob("*.jsonl")).read_text(encoding="utf-8")
    assert len(rendered.splitlines()) == 1
    assert json.loads(rendered)["observation_key"] == key
    for marker in _identity().values():
        assert marker not in rendered


def test_same_record_is_idempotent_and_conflict_fails_closed(tmp_path):
    store = _store(tmp_path)
    record = _record_for(store, **_identity())
    assert store.append(record).status == "stored"
    assert store.append(record).status == "already_recorded"
    conflict = valid_record(
        observation_key=record.observation_key,
        terminal_classification="parity_mismatch",
        parity_mismatch_count=1,
    )
    assert store.append(conflict).status == "duplicate_conflict"
    assert len(next(store.root.glob("*.jsonl")).read_text().splitlines()) == 1


def test_malformed_segment_refuses_append_without_repair(tmp_path):
    store = _store(tmp_path)
    record = _record_for(store, **_identity())
    segment = store.root / "shadow-observations-2026-07-24-0001.jsonl"
    segment.write_text("{malformed}\n", encoding="utf-8")
    before = segment.read_bytes()
    assert store.append(record).status == "malformed_segment"
    assert segment.read_bytes() == before


def test_rotation_occurs_before_configured_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(store_module, "MAX_SEGMENT_BYTES", 1400)
    store = _store(tmp_path)
    first = _record_for(store, **_identity())
    assert store.append(first).status == "stored"
    second_key = store.observation_key(
        **_identity(pipeline_run_id="synthetic-run-two")
    )
    assert store.append(valid_record(observation_key=second_key)).status == "stored"
    assert [path.name for path in sorted(store.root.glob("*.jsonl"))] == [
        "shadow-observations-2026-07-24-0001.jsonl",
        "shadow-observations-2026-07-24-0002.jsonl",
    ]


def test_retention_removes_only_old_owned_segments(tmp_path):
    store = _store(tmp_path)
    store.observation_key(**_identity())
    old = store.root / "shadow-observations-2026-06-23-0001.jsonl"
    old.write_text(valid_record().serialize().decode(), encoding="utf-8")
    recent = store.root / "shadow-observations-2026-06-24-0001.jsonl"
    recent.write_text(valid_record().serialize().decode(), encoding="utf-8")
    unrelated = store.root / "keep.txt"
    unrelated.write_text("keep", encoding="utf-8")
    record = _record_for(
        store, **_identity(pipeline_run_id="synthetic-retention-run")
    )
    assert store.append(record).status == "stored"
    assert not old.exists()
    assert recent.exists()
    assert unrelated.read_text() == "keep"


@pytest.mark.parametrize("target", ["root", "secret", "segment"])
def test_symlinked_owned_paths_are_rejected(tmp_path, target):
    outside = tmp_path / "outside"
    outside.write_text("keep", encoding="utf-8")
    root = tmp_path / "observations"
    if target == "root":
        root.symlink_to(tmp_path, target_is_directory=True)
        store = ShadowObservationStore(root)
        with pytest.raises(Exception, match="unsafe_root"):
            store.observation_key(**_identity())
    else:
        store = ShadowObservationStore(root, today=date(2026, 7, 24))
        store._ensure_root()
        if target == "secret":
            (root / ".observation-key").symlink_to(outside)
            with pytest.raises(Exception, match="unsafe_secret"):
                store.observation_key(**_identity())
        else:
            store.observation_key(**_identity())
            (root / "shadow-observations-2026-07-24-0001.jsonl").symlink_to(
                outside
            )
            assert store.append(valid_record()).status == "unsafe_segment"
    assert outside.read_text() == "keep"


def test_failed_segment_write_rolls_back_partial_line(tmp_path, monkeypatch):
    store = _store(tmp_path)
    record = _record_for(store, **_identity())
    original_write = os.write

    def short_write(descriptor, payload):
        if payload.startswith(b"{"):
            return original_write(descriptor, payload[:10])
        return original_write(descriptor, payload)

    monkeypatch.setattr(os, "write", short_write)
    assert store.append(record).status == "append_failed"
    segment = next(store.root.glob("*.jsonl"))
    assert segment.read_bytes() == b""


def test_flush_and_fsync_are_exercised(tmp_path, monkeypatch):
    calls = []
    original = os.fsync

    def tracked(descriptor):
        calls.append(descriptor)
        return original(descriptor)

    monkeypatch.setattr(os, "fsync", tracked)
    store = _store(tmp_path)
    assert store.append(_record_for(store, **_identity())).status == "stored"
    assert len(calls) >= 2


def test_store_module_has_no_database_telemetry_scheduler_or_api_dependency():
    source = Path(store_module.__file__).read_text(encoding="utf-8")
    for marker in (
        "DATABASE_URL",
        "metrics_store",
        "scheduler",
        "src.app",
        "requests",
        "httpx",
        "telemetry",
    ):
        assert marker not in source
