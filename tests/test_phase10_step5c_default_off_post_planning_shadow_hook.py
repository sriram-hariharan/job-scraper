from __future__ import annotations

import asyncio
import csv
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import main as production
from src.pipeline import post_planning_shadow as shadow
from src.pipeline import runtime_status
from src.pipeline.shadow_resume_evidence_projection import (
    PROJECTION_CONTRACT_VERSION,
    build_handoff_status,
    write_handoff_status_atomic,
    write_projection_atomic,
)


def _env(**overrides):
    values = {
        shadow.SHADOW_FLAG: "true",
        "JOB_STACK_OWNER_USER_ID": "owner-1",
        "JOB_APP_PIPELINE_RUN_ID": "run-1",
    }
    values.update(overrides)
    return values


def _projection():
    return {
        "contract_version": PROJECTION_CONTRACT_VERSION,
        "resumes": [
            {
                "resume_id": "resume-1",
                "evidence_rows": [
                    {"resume_id": "resume-1", "skills": ["Python"]}
                ],
            }
        ],
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _artifacts(tmp_path: Path, count: int = 1):
    output = tmp_path / "planning"
    output.mkdir()
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        "".join(
            json.dumps(
                {
                    "doc_id": f"job-{index}",
                    "title": "Synthetic Engineer",
                    "company": "Synthetic Co",
                    "intelligence": {
                        "skills": {
                            "required": ["Python"],
                            "preferred": [],
                            "all": ["Python"],
                        }
                    },
                    "ai_fit_score": 7,
                    "priority_score": 9,
                }
            )
            + "\n"
            for index in range(count)
        ),
        encoding="utf-8",
    )
    _write_csv(
        output / "best_resume_variant_by_job.csv",
        [
            {
                "job_doc_id": f"job-{index}",
                "winner_resume": "resume-1",
            }
            for index in range(count)
        ],
    )
    _write_csv(
        output / "application_execution_queue.csv",
        [
            {
                "job_doc_id": f"job-{index}",
                "queue_rank": str(count - index),
                "action": "REVIEW",
            }
            for index in range(count)
        ],
    )
    _write_csv(
        output / "job_packet_manifest.csv",
        [
            {
                "job_doc_id": f"job-{index}",
                "packet_resume": "resume-1",
            }
            for index in range(count)
        ],
    )
    return corpus, output


def _ready(lifecycle: shadow.PostPlanningShadowLifecycle) -> None:
    write_projection_atomic(lifecycle.projection_path, _projection())
    write_handoff_status_atomic(
        lifecycle.status_path,
        build_handoff_status(
            status="ready",
            reason_code="projection_ready",
            selected_resume_count=1,
            projected_resume_count=1,
        ),
    )


def test_flag_parser_is_exact_and_default_off():
    for value in ("1", "true", "TRUE", "yes", "on"):
        assert shadow.shadow_enabled({shadow.SHADOW_FLAG: value})
    for value in ("", "0", "false", "y", "enabled", "unexpected"):
        assert not shadow.shadow_enabled({shadow.SHADOW_FLAG: value})


def test_eligibility_and_deterministic_context_resolution():
    lifecycle = shadow.prepare_post_planning_shadow(_env())
    try:
        assert lifecycle.armed
        assert lifecycle.context_id == "application_planning:run-1"
        assert lifecycle.directory.stat().st_mode & 0o777 == 0o700
    finally:
        lifecycle.cleanup()

    explicit = shadow.prepare_post_planning_shadow(
        _env(APPLYLENS_AGENT_CONTEXT_ID="context-explicit")
    )
    try:
        assert explicit.context_id == "context-explicit"
    finally:
        explicit.cleanup()


@pytest.mark.parametrize(
    "missing",
    ["JOB_STACK_OWNER_USER_ID", "JOB_APP_PIPELINE_RUN_ID"],
)
def test_missing_or_invalid_identity_skips_without_resources(missing):
    env = _env()
    env[missing] = ""
    lifecycle = shadow.prepare_post_planning_shadow(env)
    assert lifecycle.enabled
    assert not lifecycle.armed
    assert lifecycle.directory is None
    assert lifecycle.planning_arguments == []
    assert lifecycle.initial_classification == "shadow_skipped_missing_identity"


def test_planning_arguments_are_explicit_and_share_one_private_directory():
    lifecycle = shadow.prepare_post_planning_shadow(_env())
    try:
        arguments = lifecycle.planning_arguments
        assert arguments == [
            "--shadow-resume-evidence-output",
            str(lifecycle.projection_path),
            "--shadow-resume-evidence-status-output",
            str(lifecycle.status_path),
            "--shadow-resume-evidence-non-authoritative",
        ]
        assert lifecycle.projection_path.parent == lifecycle.directory
        assert lifecycle.status_path.parent == lifecycle.directory
        assert lifecycle.facts_path.parent == lifecycle.directory
    finally:
        lifecycle.cleanup()


def test_authoritative_facts_are_deterministic_bounded_and_limited(tmp_path):
    _, output = _artifacts(tmp_path, count=30)
    facts, skipped = shadow.build_authoritative_facts(
        execution_queue_path=output / "application_execution_queue.csv",
        packet_manifest_path=output / "job_packet_manifest.csv",
        pipeline_run_id="run-1",
    )
    assert len(facts["jobs"]) == 25
    assert skipped == 5
    assert [row["queue_rank"] for row in facts["jobs"]] == list(range(1, 26))
    rendered = json.dumps(facts, sort_keys=True)
    assert len(rendered.encode()) < shadow.MAX_FACTS_BYTES
    assert "description" not in rendered
    assert "resume content" not in rendered


def test_ready_handoff_launches_once_observes_once_and_cleans(
    tmp_path, monkeypatch
):
    corpus, output = _artifacts(tmp_path)
    lifecycle = shadow.prepare_post_planning_shadow(_env())
    directory = lifecycle.directory
    _ready(lifecycle)
    calls = []
    updates = []
    def run(command):
        calls.append(command)
        assert lifecycle.facts_path.stat().st_mode & 0o777 == 0o600
        facts = json.loads(lifecycle.facts_path.read_text(encoding="utf-8"))
        assert facts["contract_version"] == shadow.AUTHORITATIVE_FACTS_VERSION
        return {
            "classification": "shadow_completed",
            "shadow_completed": 1,
            "shadow_parity_matches": 1,
            "shadow_parity_mismatches": 0,
        }

    monkeypatch.setattr(shadow, "_run_shadow_command", run)
    monkeypatch.setattr(
        runtime_status, "update_counts", lambda **counts: updates.append(counts)
    )
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=corpus,
        output_dir=output,
    )
    assert outcome["classification"] == "shadow_completed"
    assert len(calls) == 1
    command = calls[0]
    assert command[0] == shadow.sys.executable
    assert "--execute-shadow" in command
    assert "--include-trace-payload" not in command
    assert len(updates) == 1
    assert updates[0]["shadow_parity_matches"] == 1
    assert not directory.exists()


def test_enabled_hook_runs_real_shadow_through_six_nodes_without_writes(
    tmp_path, monkeypatch
):
    corpus, output = _artifacts(tmp_path)
    lifecycle = shadow.prepare_post_planning_shadow(_env())
    directory = lifecycle.directory
    _ready(lifecycle)
    authoritative_paths = [
        corpus,
        output / "best_resume_variant_by_job.csv",
        output / "application_execution_queue.csv",
        output / "job_packet_manifest.csv",
    ]
    before = {path: path.read_bytes() for path in authoritative_paths}
    observed = {}
    original_classifier = shadow._classify_command_payload

    def inspect(payload):
        observed.update(payload)
        return original_classifier(payload)

    monkeypatch.setattr(shadow, "_classify_command_payload", inspect)
    monkeypatch.setattr(runtime_status, "update_counts", lambda **_counts: None)
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=corpus,
        output_dir=output,
    )
    assert outcome["classification"] == "shadow_completed"
    assert outcome["shadow_parity_matches"] == 1
    result = observed["results"][0]
    assert result["shadow_facts"]["completed_node_order"] == [
        "jd_intelligence",
        "resume_match",
        "critic",
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
    ]
    assert result["shadow_facts"]["pending_node"] == "finalize"
    assert result["shadow_facts"]["finalization_executed"] is False
    assert {path: path.read_bytes() for path in authoritative_paths} == before
    assert not directory.exists()


@pytest.mark.parametrize(
    ("status", "reason", "classification"),
    [
        ("failed", "final_projection_failed", "shadow_projection_failed"),
        ("skipped", "no_final_selected_resumes", "shadow_projection_skipped"),
    ],
)
def test_non_ready_handoff_never_launches(
    tmp_path, monkeypatch, status, reason, classification
):
    corpus, output = _artifacts(tmp_path)
    lifecycle = shadow.prepare_post_planning_shadow(_env())
    write_handoff_status_atomic(
        lifecycle.status_path,
        build_handoff_status(
            status=status,
            reason_code=reason,
            selected_resume_count=1 if status == "failed" else 0,
            projected_resume_count=0,
        ),
    )
    monkeypatch.setattr(
        shadow,
        "_run_shadow_command",
        lambda _command: pytest.fail("shadow command launched"),
    )
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=corpus, output_dir=output
    )
    assert outcome["classification"] == classification


@pytest.mark.parametrize("contents", [None, "{bad"])
def test_missing_or_malformed_handoff_never_infers_readiness(
    tmp_path, monkeypatch, contents
):
    corpus, output = _artifacts(tmp_path)
    lifecycle = shadow.prepare_post_planning_shadow(_env())
    write_projection_atomic(lifecycle.projection_path, _projection())
    if contents is not None:
        lifecycle.status_path.write_text(contents, encoding="utf-8")
    monkeypatch.setattr(
        shadow,
        "_run_shadow_command",
        lambda _command: pytest.fail("shadow command launched"),
    )
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=corpus, output_dir=output
    )
    assert outcome["classification"] == "shadow_projection_failed"


def test_command_payload_classifies_match_mismatch_failure_and_safety():
    base = {
        "execution_version": shadow.SHADOW_EXECUTION_VERSION,
        "status": "completed",
        "job_count": 1,
        "artifacts_unchanged": True,
        "results": [
            {
                "status": "parity_completed",
                "shadow_facts": {
                    "pending_node": "finalize",
                    "finalization_executed": False,
                    "final_bundle_present": False,
                    "final_trace_present": False,
                    "completed_node_order": [
                        "jd_intelligence",
                        "resume_match",
                        "critic",
                        "job_prioritization",
                        "tailoring_decision",
                        "operator_review",
                    ],
                },
                "parity": {
                    "contract_version": shadow.SHADOW_PARITY_VERSION,
                    "overall_classification": "match",
                },
            }
        ],
    }
    assert shadow._classify_command_payload(base)["classification"] == (
        "shadow_completed"
    )
    mismatch = json.loads(json.dumps(base))
    mismatch["results"][0]["parity"]["overall_classification"] = "mismatch"
    assert shadow._classify_command_payload(mismatch)["classification"] == (
        "parity_mismatch"
    )
    failure = json.loads(json.dumps(base))
    failure["results"][0]["status"] = "graph_execution_failed"
    assert shadow._classify_command_payload(failure)["classification"] == (
        "shadow_execution_failure"
    )
    unsafe = json.loads(json.dumps(base))
    unsafe["artifacts_unchanged"] = False
    assert shadow._classify_command_payload(unsafe)["classification"] == (
        "shadow_safety_violation"
    )


@pytest.mark.parametrize(
    ("program", "classification"),
    [
        ("print('not-json')", "shadow_execution_failure"),
        ("print('{}'); print('{}')", "shadow_execution_failure"),
        ("raise SystemExit(3)", "shadow_execution_failure"),
        (
            "import sys; sys.stdout.write('x'*70000)",
            "shadow_execution_failure",
        ),
    ],
)
def test_subprocess_output_and_exit_are_bounded(program, classification):
    result = shadow._run_shadow_command([shadow.sys.executable, "-c", program])
    assert result["classification"] == classification


def test_timeout_terminates_process_group_without_retry(monkeypatch):
    monkeypatch.setattr(shadow, "SHADOW_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(shadow, "PROCESS_STOP_WAIT_SECONDS", 0.2)
    result = shadow._run_shadow_command(
        [
            shadow.sys.executable,
            "-c",
            "import time; time.sleep(10)",
        ]
    )
    assert result["classification"] == "shadow_timeout"


def test_shadow_subprocess_environment_disables_provider_and_durable_flags(
    monkeypatch,
):
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setenv("SOME_LLM_ENABLED", "true")
    monkeypatch.setenv("APPLYLENS_DURABLE_MODE", "true")
    monkeypatch.setenv("DATABASE_URL", "secret")
    monkeypatch.setenv("PATH", "/safe/path")
    sanitized = shadow._shadow_subprocess_environment()
    assert sanitized["PATH"] == "/safe/path"
    assert "OPENAI_API_KEY" not in sanitized
    assert "SOME_LLM_ENABLED" not in sanitized
    assert "APPLYLENS_DURABLE_MODE" not in sanitized
    assert "DATABASE_URL" not in sanitized
    assert shadow.SHADOW_FLAG not in sanitized


def _main_args(tmp_path):
    return SimpleNamespace(
        application_planning_only=True,
        run_application_planning=True,
        application_planning_job_limit=1,
        application_planning_job_packet_limit=1,
        application_planning_output_dir=str(tmp_path / "planning"),
        application_planning_llm_actions="APPLY",
        application_planning_generate_tailoring=False,
        application_planning_generate_llm_tailoring=False,
        application_planning_refresh_llm_tailoring=False,
        application_planning_generate_llm_fallback=False,
        application_planning_generate_llm_adjudication=False,
        delete_seen_data="no",
    )


def _patch_main_flow(monkeypatch, tmp_path, events):
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text('{"doc_id":"job-1"}\n', encoding="utf-8")
    monkeypatch.setenv("JOB_STACK_JOB_CORPUS_PATH", str(corpus))
    monkeypatch.setenv("JOB_STACK_USER_PIPELINE_MODE", "true")
    monkeypatch.setattr(production, "initialize_run", lambda **_kw: None)
    monkeypatch.setattr(production, "start_stage", lambda *_a, **_kw: None)
    monkeypatch.setattr(production, "complete_stage", lambda *_a, **_kw: None)
    monkeypatch.setattr(production, "_load_jobs_from_corpus", lambda _p: [{}])
    monkeypatch.setattr(production, "_load_best_variant_lookup", lambda _p: {})
    monkeypatch.setattr(production, "_load_execution_queue_lookup", lambda _p: {})
    monkeypatch.setattr(production, "_load_packet_manifest_lookup", lambda _p: {})
    monkeypatch.setattr(
        production,
        "_merge_application_planning_into_jobs",
        lambda *_a, **_kw: events.append("merge") or 0,
    )
    monkeypatch.setattr(
        production,
        "finish_run",
        lambda **_kw: events.append("finish"),
    )
    monkeypatch.setattr(
        production,
        "_application_planning_summary_message",
        lambda _count: "done",
    )


def test_disabled_main_path_adds_nothing_and_constructs_no_shadow(
    tmp_path, monkeypatch
):
    events = []
    _patch_main_flow(monkeypatch, tmp_path, events)
    monkeypatch.delenv(shadow.SHADOW_FLAG, raising=False)
    monkeypatch.setattr(
        production,
        "_run_application_planning",
        lambda _args, job_corpus_path=None, additional_arguments=None: (
            events.append(("planning", additional_arguments))
        ),
    )
    asyncio.run(production.main_async(_main_args(tmp_path)))
    assert events == [("planning", None), "merge", "finish"]


def test_authoritative_order_is_planning_merge_finish_then_shadow(
    tmp_path, monkeypatch
):
    events = []
    _patch_main_flow(monkeypatch, tmp_path, events)
    monkeypatch.setenv(shadow.SHADOW_FLAG, "true")

    class Lifecycle:
        planning_arguments = ["projection-options"]

        def cleanup(self):
            events.append("cleanup")

        def complete_after_authoritative_success(self, **_kwargs):
            events.append("shadow")

    monkeypatch.setattr(
        shadow, "prepare_post_planning_shadow", lambda: Lifecycle()
    )
    monkeypatch.setattr(
        production,
        "_run_application_planning",
        lambda _args, job_corpus_path=None, additional_arguments=None: (
            events.append("planning")
        ),
    )
    asyncio.run(production.main_async(_main_args(tmp_path)))
    assert events == ["planning", "merge", "finish", "shadow"]


def test_planning_failure_propagates_and_only_cleans(tmp_path, monkeypatch):
    events = []
    _patch_main_flow(monkeypatch, tmp_path, events)
    monkeypatch.setenv(shadow.SHADOW_FLAG, "true")

    class Lifecycle:
        planning_arguments = ["projection-options"]

        def cleanup(self):
            events.append("cleanup")

        def complete_after_authoritative_success(self, **_kwargs):
            events.append("shadow")

    monkeypatch.setattr(
        shadow, "prepare_post_planning_shadow", lambda: Lifecycle()
    )

    def fail(*_args, **_kwargs):
        events.append("planning")
        raise RuntimeError("authoritative planning failed")

    monkeypatch.setattr(production, "_run_application_planning", fail)
    with pytest.raises(RuntimeError, match="authoritative planning failed"):
        asyncio.run(production.main_async(_main_args(tmp_path)))
    assert events == ["planning", "cleanup"]


def test_runtime_count_failure_does_not_escape_or_leave_files(
    tmp_path, monkeypatch
):
    corpus, output = _artifacts(tmp_path)
    lifecycle = shadow.prepare_post_planning_shadow(
        _env(JOB_STACK_OWNER_USER_ID="")
    )
    monkeypatch.setattr(
        runtime_status,
        "update_counts",
        lambda **_counts: (_ for _ in ()).throw(RuntimeError("status failed")),
    )
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=corpus, output_dir=output
    )
    assert outcome["classification"] == "shadow_skipped_missing_identity"
    assert lifecycle.directory is None


def test_shadow_counts_preserve_authoritative_success_and_return_code(
    tmp_path, monkeypatch
):
    status_path = tmp_path / "runtime_status.json"
    monkeypatch.setenv("JOB_APP_PIPELINE_STATUS_PATH", str(status_path))
    monkeypatch.setenv("JOB_APP_PIPELINE_RUN_ID", "run-1")
    status_path.write_text(
        json.dumps(
            {
                "status": "running",
                "return_code": None,
                "counts": {},
                "completed_stages": [],
            }
        ),
        encoding="utf-8",
    )
    runtime_status.finish_run(
        return_code=0,
        summary_message="authoritative success",
        final_job_count=1,
    )
    lifecycle = shadow.prepare_post_planning_shadow(
        _env(JOB_STACK_OWNER_USER_ID="")
    )
    lifecycle.complete_after_authoritative_success(
        job_corpus_path=tmp_path / "unused.jsonl",
        output_dir=tmp_path / "unused",
    )
    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["status"] == "succeeded"
    assert status["return_code"] == 0
    assert status["summary_message"] == "authoritative success"
    assert status["counts"]["shadow_failure_classification"] == (
        "shadow_skipped_missing_identity"
    )


def test_cleanup_is_idempotent_and_refuses_unowned_directory(tmp_path):
    authoritative = tmp_path / "authoritative.txt"
    authoritative.write_text("keep", encoding="utf-8")
    lifecycle = shadow.PostPlanningShadowLifecycle(
        enabled=True,
        armed=True,
        directory=tmp_path,
    )
    lifecycle.cleanup()
    lifecycle.cleanup()
    assert authoritative.read_text(encoding="utf-8") == "keep"


def test_owned_cleanup_unlinks_symlink_without_following(tmp_path):
    target = tmp_path / "authoritative.txt"
    target.write_text("keep", encoding="utf-8")
    lifecycle = shadow.prepare_post_planning_shadow(_env())
    directory = lifecycle.directory
    link = directory / "partial.json"
    link.symlink_to(target)
    lifecycle.cleanup()
    assert target.read_text(encoding="utf-8") == "keep"
    assert not directory.exists()


def test_step5c_source_has_no_prohibited_runtime_owners():
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "src/pipeline/post_planning_shadow.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "PostgresSaver",
        "durable_evidence_chain_resume_coordinator",
            "src.storage.durable_orchestration",
            "finalize(",
            "application_actions",
            "notification",
        ):
        assert forbidden not in source
    assert 'os.getenv("DATABASE_URL"' not in source
    assert 'source.get("DATABASE_URL"' not in source
