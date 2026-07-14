from pathlib import Path
import re

import pytest

from src.app import api, services


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

    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-1")

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
            "selected_resume": "Winner.pdf",
        },
        output_dir="outputs/application_planning",
        job_corpus="outputs/application_planning/current_run_job_corpus.jsonl",
    )

    assert result == {"ok": True}
    assert calls["identity"] == ("owner-1", "run-1")
    assert calls["regenerate"]["output_dir"] == output_dir
    assert calls["regenerate"]["job_corpus"] == corpus


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
