import csv
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.app import api, services
from src.resume import document_store


ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "src/app/static/styles.css"
PLANNING_UI = ROOT / "src/app/planning_ui.py"
PLANNING_JS = ROOT / "src/app/static/planning.js"


def test_workflow_overlay_has_one_canonical_css_owner():
    css = CSS.read_text(encoding="utf-8")
    planning_markup = PLANNING_UI.read_text(encoding="utf-8")

    for selector in (
        ".workflow-overlay",
        ".workflow-overlay__panel",
        ".workflow-overlay__header",
        ".workflow-overlay__body",
        ".workflow-overlay__metrics",
        ".workflow-step-viewport",
        ".workflow-step",
        ".workflow-overlay__footer",
    ):
        pattern = rf"(?m)^{re.escape(selector)}\s*\{{"
        assert len(re.findall(pattern, css)) == 1, selector

    assert "<style>" not in planning_markup
    for obsolete in (
        "pipeline-workflow-orbit",
        "pipeline-workflow-visual",
        "generate-suggestions-document-stack",
        "pipeline-success-gif",
        "pipeline-step--current",
    ):
        assert obsolete not in css


def _install_run_record(monkeypatch, output_dir: Path):
    monkeypatch.setattr(
        services,
        "_user_pipeline_run_and_artifacts",
        lambda owner, run_id: (
            {
                "run_id": run_id,
                "status": "succeeded",
                "config_json": {"output_dir": str(output_dir)},
            },
            [],
        ),
    )


def test_run_scoped_corpus_resolution_uses_exact_owner_and_run(tmp_path, monkeypatch):
    output_dir = tmp_path / "tmp" / "pipeline_runs" / "owner-1" / "run-1" / "application_planning"
    output_dir.mkdir(parents=True)
    corpus = output_dir / "current_run_job_corpus.jsonl"
    corpus.write_text('{"job_doc_id":"job-1"}\n', encoding="utf-8")
    _install_run_record(monkeypatch, output_dir)

    resolved_output, resolved_corpus = services.resolve_user_pipeline_run_planning_paths(
        owner_user_id="owner-1",
        run_id="run-1",
    )

    assert resolved_output == output_dir.resolve()
    assert resolved_corpus == corpus.resolve()


@pytest.mark.parametrize(
    ("owner", "run_id", "path_owner", "path_run"),
    [
        ("owner-1", "run-1", "owner-2", "run-1"),
        ("owner-1", "run-1", "owner-1", "run-2"),
    ],
)
def test_run_scoped_corpus_cannot_cross_owner_or_run(
    tmp_path, monkeypatch, owner, run_id, path_owner, path_run
):
    output_dir = tmp_path / "tmp" / "pipeline_runs" / path_owner / path_run / "application_planning"
    output_dir.mkdir(parents=True)
    (output_dir / "current_run_job_corpus.jsonl").write_text("{}\n", encoding="utf-8")
    _install_run_record(monkeypatch, output_dir)

    with pytest.raises(ValueError, match="invalid artifact location"):
        services.resolve_user_pipeline_run_planning_paths(
            owner_user_id=owner,
            run_id=run_id,
        )


def test_missing_run_scoped_corpus_returns_friendly_error(tmp_path, monkeypatch):
    output_dir = tmp_path / "tmp" / "pipeline_runs" / "owner-1" / "run-1" / "application_planning"
    output_dir.mkdir(parents=True)
    _install_run_record(monkeypatch, output_dir)

    with pytest.raises(ValueError, match="completed run is unavailable"):
        services.resolve_user_pipeline_run_planning_paths(
            owner_user_id="owner-1",
            run_id="run-1",
        )


def test_regenerate_endpoint_prefers_authenticated_run_context(monkeypatch, tmp_path):
    output_dir = tmp_path / "tmp" / "pipeline_runs" / "owner-1" / "run-1" / "application_planning"
    corpus = output_dir / "current_run_job_corpus.jsonl"
    calls = {}

    def fake_auth_owner(request):
        calls["auth_count"] = calls.get("auth_count", 0) + 1
        return "owner-1"

    monkeypatch.setattr(api, "_auth_owner_user_id", fake_auth_owner)

    def fake_resolve(*, owner_user_id, run_id):
        calls["identity"] = (owner_user_id, run_id)
        return output_dir, corpus

    def fake_regenerate(**kwargs):
        calls["regenerate"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(services, "resolve_user_pipeline_run_planning_paths", fake_resolve)
    monkeypatch.setattr(services, "regenerate_selected_resume_tailoring_payload", fake_regenerate)

    result = api.planning_regenerate_selected_resume(
        object(),
        {
            "pipeline_run_id": "run-1",
            "job_doc_id": "job-1",
            "selected_resume": "SWATIKA_test_1.pdf",
        },
        output_dir="outputs/application_planning",
        job_corpus="outputs/application_planning/current_run_job_corpus.jsonl",
    )

    assert result == {"ok": True}
    assert calls["auth_count"] == 1
    assert calls["identity"] == ("owner-1", "run-1")
    assert calls["regenerate"]["output_dir"] == output_dir
    assert calls["regenerate"]["job_corpus"] == corpus
    assert calls["regenerate"]["owner_user_id"] == "owner-1"
    assert calls["regenerate"]["selected_resume"] == "SWATIKA_test_1.pdf"


def _install_targeted_regeneration_fixture(monkeypatch, tmp_path):
    selected_resume = "SWATIKA_test_1.pdf"
    output_dir = tmp_path / "application_planning"
    output_dir.mkdir(parents=True)
    job_corpus = output_dir / "current_run_job_corpus.jsonl"
    job_corpus.write_text('{"job_doc_id":"job-1"}\n', encoding="utf-8")

    target_row = {
        "queue_rank": "1",
        "job_doc_id": "job-1",
        "job_url": "https://example.test/job-1",
        "job_company": "Example",
        "job_title": "Engineer",
        "action": "APPLY",
        "winner_resume": selected_resume,
        "winner_score": "0.9",
        "runner_up_resume": "Runner.pdf",
        "runner_up_score": "0.8",
        "score_gap": "0.1",
        "is_tie": "False",
        "needs_variant_review": "False",
        "missing_requirement_count": "0",
        "queue_priority_reason": "fixture",
    }
    monkeypatch.setattr(
        services,
        "_job_app",
        lambda: SimpleNamespace(_build_job_index=lambda path: [target_row]),
    )
    monkeypatch.setattr(
        services,
        "_resolve_job_index_for_regeneration",
        lambda *args, **kwargs: 0,
    )

    fieldnames = [
        "queue_rank",
        "needs_variant_review",
        "missing_requirement_count",
        "queue_priority_reason",
        "job_doc_id",
        "job_company",
        "job_title",
        "action",
        "winner_resume",
        "winner_score",
        "runner_up_resume",
        "runner_up_score",
        "score_gap",
        "is_tie",
        "packet_status",
        "packet_json",
        "tailoring_json",
        "tailoring_md",
        "tailoring_llm_json",
        "llm_tailoring_status",
        "llm_cache_hit",
        "llm_parse_ok",
        "llm_provider",
        "llm_model",
        "llm_error_type",
        "llm_retryable",
        "llm_retry_used",
    ]
    with (output_dir / "job_packet_manifest.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({field: target_row.get(field, "") for field in fieldnames})

    return output_dir, job_corpus, selected_resume


def test_targeted_regeneration_passes_owner_scoped_env_to_both_commands(
    tmp_path, monkeypatch
):
    output_dir, job_corpus, selected_resume = _install_targeted_regeneration_fixture(
        monkeypatch, tmp_path
    )
    calls = []
    monkeypatch.delenv(
        "APPLYLENS_SAFE_APP_READY_REWRITE_PROMOTION_ENABLED",
        raising=False,
    )
    monkeypatch.setenv("JOB_STACK_USER_PIPELINE_MODE", "parent-mode")
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "parent-owner")
    parent_before = {
        "JOB_STACK_USER_PIPELINE_MODE": os.environ.get("JOB_STACK_USER_PIPELINE_MODE"),
        "JOB_STACK_OWNER_USER_ID": os.environ.get("JOB_STACK_OWNER_USER_ID"),
    }

    def fake_run(cmd, *, env=None):
        calls.append((list(cmd), env))

    monkeypatch.setattr(services, "_run_checked_cmd", fake_run)

    result = services.regenerate_selected_resume_tailoring_payload(
        output_dir=output_dir,
        job_corpus=job_corpus,
        job_doc_id="job-1",
        selected_resume=selected_resume,
        generate_llm_tailoring=True,
        owner_user_id="owner-a",
    )

    assert result["ok"] is True
    assert result["selected_resume"] == selected_resume
    assert len(calls) == 2
    assert calls[0][0][calls[0][0].index("--resume-name-contains") + 1] == selected_resume
    assert "--enable-safe-app-ready-rewrite-promotion" not in calls[0][0]
    assert "--enable-safe-app-ready-rewrite-promotion" in calls[1][0]
    assert calls[0][1] is calls[1][1]
    assert calls[0][1]["JOB_STACK_USER_PIPELINE_MODE"] == "1"
    assert calls[0][1]["JOB_STACK_OWNER_USER_ID"] == "owner-a"
    assert all("owner-a" not in argument for command, _ in calls for argument in command)
    assert {
        "JOB_STACK_USER_PIPELINE_MODE": os.environ.get("JOB_STACK_USER_PIPELINE_MODE"),
        "JOB_STACK_OWNER_USER_ID": os.environ.get("JOB_STACK_OWNER_USER_ID"),
    } == parent_before
    assert "owner_user_id" not in result


def test_targeted_regeneration_explicit_false_disables_safe_rewrite_promotion(
    tmp_path, monkeypatch
):
    output_dir, job_corpus, selected_resume = _install_targeted_regeneration_fixture(
        monkeypatch, tmp_path
    )
    calls = []
    monkeypatch.setenv(
        "APPLYLENS_SAFE_APP_READY_REWRITE_PROMOTION_ENABLED",
        "false",
    )
    monkeypatch.setattr(
        services,
        "_run_checked_cmd",
        lambda cmd, *, env=None: calls.append((list(cmd), env)),
    )

    result = services.regenerate_selected_resume_tailoring_payload(
        output_dir=output_dir,
        job_corpus=job_corpus,
        job_doc_id="job-1",
        selected_resume=selected_resume,
        generate_llm_tailoring=True,
        owner_user_id="owner-a",
    )

    assert result["ok"] is True
    assert len(calls) == 2
    assert "--enable-safe-app-ready-rewrite-promotion" not in calls[0][0]
    assert "--enable-safe-app-ready-rewrite-promotion" not in calls[1][0]


def test_targeted_regeneration_child_envs_are_owner_isolated_and_legacy_safe(
    monkeypatch,
):
    monkeypatch.setenv("JOB_STACK_USER_PIPELINE_MODE", "parent-mode")
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "parent-owner")
    parent_before = {
        "JOB_STACK_USER_PIPELINE_MODE": os.environ.get("JOB_STACK_USER_PIPELINE_MODE"),
        "JOB_STACK_OWNER_USER_ID": os.environ.get("JOB_STACK_OWNER_USER_ID"),
    }
    owners = ["owner-a", "owner-b"] * 8

    with ThreadPoolExecutor(max_workers=8) as pool:
        child_envs = list(pool.map(services._targeted_regeneration_child_env, owners))

    assert all(env is not None for env in child_envs)
    assert [env["JOB_STACK_OWNER_USER_ID"] for env in child_envs] == owners
    assert all(env["JOB_STACK_USER_PIPELINE_MODE"] == "1" for env in child_envs)
    assert len({id(env) for env in child_envs}) == len(child_envs)
    assert services._targeted_regeneration_child_env("") is None
    assert {
        "JOB_STACK_USER_PIPELINE_MODE": os.environ.get("JOB_STACK_USER_PIPELINE_MODE"),
        "JOB_STACK_OWNER_USER_ID": os.environ.get("JOB_STACK_OWNER_USER_ID"),
    } == parent_before


def test_run_checked_cmd_preserves_legacy_inherited_environment(monkeypatch):
    calls = []

    def fake_subprocess_run(cmd, **kwargs):
        calls.append((cmd, kwargs))

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)
    services._run_checked_cmd(["legacy-command"])

    assert calls == [(["legacy-command"], {"check": True})]


def test_postgres_only_profile_resume_lookup_uses_exact_owner_without_fallback(
    monkeypatch,
):
    selected_resume = "SWATIKA_test_1.pdf"
    calls = []
    monkeypatch.setenv("JOB_STACK_USER_PIPELINE_MODE", "1")
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "owner-a")
    monkeypatch.setattr(
        document_store,
        "load_resumes_by_name",
        lambda names: pytest.fail("user mode must not fall back to filesystem resumes"),
    )
    monkeypatch.setattr(
        document_store,
        "extract_resume_texts",
        lambda path: {"raw_text": "PostgreSQL resume", "text": "PostgreSQL resume"},
    )

    def fake_blob_payload(*, owner_user_id, resume_name, **kwargs):
        calls.append((owner_user_id, resume_name))
        if owner_user_id == "owner-a" and resume_name == selected_resume:
            return {
                "resume": {
                    "resume_name": selected_resume,
                    "content_type": "application/pdf",
                },
                "file_bytes": b"stub-pdf",
            }
        return {"resume": {}, "file_bytes": b""}

    monkeypatch.setattr(
        document_store,
        "get_profile_resume_blob_postgres_payload",
        fake_blob_payload,
    )

    documents = document_store.load_resume_documents_by_name([selected_resume])
    assert [document.resume_name for document in documents] == [selected_resume]
    assert calls == [("owner-a", selected_resume)]

    documents = document_store.load_resume_documents_by_name(["owner-b-only.pdf"])
    assert documents == []
    assert calls[-1] == ("owner-a", "owner-b-only.pdf")

    monkeypatch.delenv("JOB_STACK_OWNER_USER_ID")
    with pytest.raises(RuntimeError, match="JOB_STACK_OWNER_USER_ID not set"):
        document_store.load_resume_documents_by_name(["owner-b-only.pdf"])


def test_targeted_regeneration_subprocess_failure_is_bounded_in_service_and_api(
    tmp_path, monkeypatch, caplog
):
    output_dir, job_corpus, selected_resume = _install_targeted_regeneration_fixture(
        monkeypatch, tmp_path
    )
    monkeypatch.setattr(
        services,
        "_run_checked_cmd",
        lambda cmd, *, env=None: (_ for _ in ()).throw(
            subprocess.CalledProcessError(1, ["sensitive", "/absolute/path"])
        ),
    )

    with pytest.raises(
        services.SelectedResumeRegenerationError,
        match="Selected resume regeneration failed. Please retry.",
    ):
        services.regenerate_selected_resume_tailoring_payload(
            output_dir=output_dir,
            job_corpus=job_corpus,
            job_doc_id="job-1",
            selected_resume=selected_resume,
            owner_user_id="owner-a",
        )
    assert "stage=resume_diff return_code=1" in caplog.text
    assert "owner-a" not in caplog.text
    assert "/absolute/path" not in caplog.text

    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-a")
    monkeypatch.setattr(
        services,
        "regenerate_selected_resume_tailoring_payload",
        lambda **kwargs: (_ for _ in ()).throw(
            services.SelectedResumeRegenerationError("owner-a /absolute/path DATABASE_URL")
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        api.planning_regenerate_selected_resume(
            object(),
            {"job_doc_id": "job-1", "selected_resume": selected_resume},
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Could not regenerate the selected resume. Please retry."
    assert "owner-a" not in exc_info.value.detail
    assert "/absolute/path" not in exc_info.value.detail


def test_incomplete_run_reports_planning_artifacts_not_ready(tmp_path, monkeypatch):
    output_dir = tmp_path / "tmp" / "pipeline_runs" / "owner-1" / "run-1" / "application_planning"
    output_dir.mkdir(parents=True)
    monkeypatch.setattr(
        services,
        "_user_pipeline_run_and_artifacts",
        lambda owner, run_id: (
            {
                "run_id": run_id,
                "status": "running",
                "config_json": {"output_dir": str(output_dir)},
            },
            [],
        ),
    )

    with pytest.raises(ValueError, match="planning artifacts.*not ready"):
        services.resolve_user_pipeline_run_planning_paths(
            owner_user_id="owner-1",
            run_id="run-1",
        )


def test_frontend_keeps_explicit_workspace_navigation_and_friendly_corpus_copy():
    source = PLANNING_JS.read_text(encoding="utf-8")
    assert 'pipeline_run_id: row?.pipeline_run_id || row?.run_id || ""' in source
    assert 'return "/planning/regenerate-selected-resume"' in source
    assert "The planning corpus for this completed run is unavailable." in source
    assert 'window.location.href = generateSuggestionsState.lastWorkspaceUrl' in source
