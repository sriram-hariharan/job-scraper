from __future__ import annotations

import json
from pathlib import Path

from src.pipeline import post_planning_shadow as shadow
from src.pipeline import runtime_status
from src.pipeline.shadow_observation_contract import (
    OBSERVATION_CONTRACT_VERSION,
    parse_observation_json,
)
from src.pipeline.shadow_observation_store import ShadowObservationStore
from tests.test_phase10_step5c_default_off_post_planning_shadow_hook import (
    _artifacts,
    _env,
    _ready,
)
from tests.test_phase10_step8_shadow_cleanup_liveness import _payload
from tests.test_phase10_step8_shadow_observation_contract import valid_record


def _enabled_lifecycle(tmp_path, monkeypatch, outcome):
    tmp_path.mkdir(parents=True, exist_ok=True)
    corpus, output = _artifacts(tmp_path)
    lifecycle = shadow.prepare_post_planning_shadow(_env())
    lifecycle.observation_root = tmp_path / "observations"
    _ready(lifecycle)
    monkeypatch.setattr(
        shadow, "_run_shadow_command", lambda _command: dict(outcome)
    )
    monkeypatch.setattr(runtime_status, "update_counts", lambda **_counts: None)
    return lifecycle, corpus, output


def _success_outcome():
    return {
        "classification": "shadow_completed",
        "jobs_attempted": 1,
        "shadow_completed": 1,
        "shadow_parity_matches": 1,
        "shadow_parity_mismatches": 0,
        "parity_mismatch_count": 0,
        "adapter_rejection_count": 0,
        "graph_failure_count": 0,
        "parity_processing_failure_count": 0,
        "safety_violation_count": 0,
        "exact_identity_total": 3,
        "exact_identity_matched": 3,
        "selected_resume_total": 1,
        "selected_resume_matched": 1,
        "ordered_parity_total": 1,
        "ordered_parity_matched": 1,
        "categorical_parity_total": None,
        "categorical_parity_matched": None,
        "intentionally_incomparable_count": 0,
        "max_job_graph_latency_ms": 5,
        "subprocess_wall_clock_ms": 20,
        "cleanup_categories": {},
        "process_liveness_confirmed": True,
    }


def test_disabled_mode_constructs_no_observation_resource(tmp_path):
    root = tmp_path / "observations"
    lifecycle = shadow.prepare_post_planning_shadow({})
    lifecycle.observation_root = root
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=tmp_path / "unused.jsonl",
        output_dir=tmp_path / "unused",
    )
    assert outcome["classification"] == "shadow_disabled"
    assert outcome["observation_store_status"] == "not_applicable"
    assert not root.exists()
    assert lifecycle.directory is None


def test_success_is_written_once_after_cleanup_without_output_mutation(
    tmp_path, monkeypatch
):
    lifecycle, corpus, output = _enabled_lifecycle(
        tmp_path, monkeypatch, _success_outcome()
    )
    directory = lifecycle.directory
    authoritative = {
        path: path.read_bytes()
        for path in (
            corpus,
            output / "best_resume_variant_by_job.csv",
            output / "application_execution_queue.csv",
            output / "job_packet_manifest.csv",
        )
    }
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=corpus, output_dir=output
    )
    assert outcome["classification"] == "shadow_completed"
    assert outcome["observation_store_status"] == "stored"
    assert outcome["cleanup_complete"] is True
    assert outcome["process_liveness_confirmed"] is True
    assert not directory.exists()
    assert {path: path.read_bytes() for path in authoritative} == authoritative
    segments = list(lifecycle.observation_root.glob("*.jsonl"))
    assert len(segments) == 1
    lines = segments[0].read_bytes().splitlines()
    assert len(lines) == 1
    record = parse_observation_json(lines[0])
    assert record.contract_version == OBSERVATION_CONTRACT_VERSION
    assert record.authoritative_run_succeeded is True
    assert record.cleanup_complete is True
    assert record.process_liveness_confirmed is True
    assert record.status_update_succeeded is None
    assert record.aggregate_log_succeeded is None


def test_timeout_and_unconfirmed_liveness_are_non_authoritative(
    tmp_path, monkeypatch
):
    timeout = {
        "classification": "shadow_timeout",
        "jobs_attempted": None,
        "cleanup_categories": {},
        "process_liveness_confirmed": True,
        "subprocess_wall_clock_ms": 50,
    }
    lifecycle, corpus, output = _enabled_lifecycle(
        tmp_path / "timeout", monkeypatch, timeout
    )
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=corpus, output_dir=output
    )
    assert outcome["classification"] == "shadow_timeout"
    assert outcome["process_liveness_confirmed"] is True
    assert outcome["observation_store_status"] == "stored"

    unsafe = {
        "classification": "shadow_execution_failure",
        "jobs_attempted": 1,
        "cleanup_categories": {"process_liveness_unconfirmed": 1},
        "process_liveness_confirmed": False,
    }
    lifecycle, corpus, output = _enabled_lifecycle(
        tmp_path / "unsafe", monkeypatch, unsafe
    )
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=corpus, output_dir=output
    )
    assert outcome["classification"] == "shadow_safety_violation"
    assert outcome["process_liveness_failure_count"] == 1
    assert outcome["observation_store_status"] == "stored"
    record = parse_observation_json(
        next(lifecycle.observation_root.glob("*.jsonl")).read_bytes()
    )
    assert record.terminal_classification == "shadow_safety_violation"
    assert record.authoritative_run_succeeded is True


def test_store_failure_is_bounded_without_retry_or_partial_record(
    tmp_path, monkeypatch
):
    lifecycle, corpus, output = _enabled_lifecycle(
        tmp_path, monkeypatch, _success_outcome()
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    lifecycle.observation_root.symlink_to(outside, target_is_directory=True)
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=corpus, output_dir=output
    )
    assert outcome["classification"] == "shadow_completed"
    assert outcome["observation_store_status"] == "unsafe_root"
    assert list(outside.iterdir()) == []


def test_duplicate_semantics_remain_non_authoritative(tmp_path):
    store = ShadowObservationStore(tmp_path / "observations")
    identity = {
        "owner_id": "synthetic-owner",
        "pipeline_run_id": "synthetic-run",
        "context_id": "synthetic-context",
    }
    key = store.observation_key(**identity)
    record = valid_record(observation_key=key)
    assert store.append(record).status == "stored"
    assert store.append(record).status == "already_recorded"
    conflict = valid_record(
        observation_key=key,
        terminal_classification="parity_mismatch",
        parity_mismatch_count=1,
    )
    assert store.append(conflict).status == "duplicate_conflict"
    assert len(next(store.root.glob("*.jsonl")).read_text().splitlines()) == 1


def test_transient_child_content_is_aggregated_then_discarded(
    tmp_path, monkeypatch, caplog
):
    marker_values = {
        "owner_id": "RAW_OWNER_SENSITIVE",
        "pipeline_run_id": "RAW_RUN_SENSITIVE",
        "context_id": "RAW_CONTEXT_SENSITIVE",
    }
    payload = _payload()
    payload.update(marker_values)
    payload["results"][0]["job_id"] = "RAW_JOB_SENSITIVE"
    payload["results"][0]["graph_invocation_id"] = "RAW_GRAPH_SENSITIVE"
    payload["results"][0]["selected_resume_id"] = "RAW_RESUME_SENSITIVE"
    payload["results"][0]["shadow_facts"]["warnings"] = [
        "RAW_WARNING_SENSITIVE"
    ]
    payload["results"][0]["shadow_facts"]["artifact_digests"] = {
        "/RAW/PATH/SENSITIVE": "RAW_DIGEST_SENSITIVE"
    }
    aggregate = shadow._classify_command_payload(payload)
    aggregate.update(
        {
            "cleanup_categories": {},
            "process_liveness_confirmed": True,
            "subprocess_wall_clock_ms": 1,
        }
    )
    lifecycle, corpus, output = _enabled_lifecycle(
        tmp_path, monkeypatch, aggregate
    )
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=corpus, output_dir=output
    )
    assert outcome["observation_store_status"] == "stored"
    combined = next(lifecycle.observation_root.glob("*.jsonl")).read_text()
    combined += repr(outcome)
    combined += caplog.text
    for marker in (
        *marker_values.values(),
        "RAW_JOB_SENSITIVE",
        "RAW_GRAPH_SENSITIVE",
        "RAW_RESUME_SENSITIVE",
        "RAW_WARNING_SENSITIVE",
        "RAW_PATH_SENSITIVE",
        "RAW_DIGEST_SENSITIVE",
        "stdout",
        "stderr",
    ):
        assert marker not in combined


def test_source_order_is_cleanup_then_observation_then_status_log():
    source = Path(shadow.__file__).read_text(encoding="utf-8")
    complete = source[source.index("def complete_after_authoritative_success") :]
    assert complete.index("self.cleanup()") < complete.index("self._observe(")
    observe = source[source.index("def _observe(") :]
    assert observe.index("self._persist_observation(") < observe.index(
        "update_counts(**counts)"
    )
