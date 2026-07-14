from pathlib import Path

import pytest

from src.app import services


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "src/app/static/app.js"
PLANNING_JS = ROOT / "src/app/static/planning.js"
CSS = ROOT / "src/app/static/styles.css"


def _run_record(output_dir: Path, *, final_job_count: int):
    return {
        "run_id": output_dir.parent.name,
        "status": "succeeded",
        "final_job_count": final_job_count,
        "status_json": {"final_job_count": final_job_count},
        "config_json": {"output_dir": str(output_dir)},
    }


def test_zero_result_filesystem_context_is_retained_without_stale_fallback(tmp_path):
    output_dir = (
        tmp_path
        / "tmp"
        / "pipeline_runs"
        / "owner-1"
        / "run-zero"
        / "application_planning"
    )
    output_dir.mkdir(parents=True)

    context = services._latest_user_pipeline_filesystem_context(
        owner_user_id="owner-1",
        run=_run_record(output_dir, final_job_count=0),
    )

    assert context["run_id"] == "run-zero"
    assert context["zero_result_run"] is True
    assert context["best_rows"] == []
    assert context["queue_rows"] == []
    assert context["job_corpus_rows"] == 0


def test_zero_result_corpus_is_not_opened_for_generate_suggestions(tmp_path, monkeypatch):
    output_dir = (
        tmp_path
        / "tmp"
        / "pipeline_runs"
        / "owner-1"
        / "run-zero"
        / "application_planning"
    )
    output_dir.mkdir(parents=True)
    run = _run_record(output_dir, final_job_count=0)
    monkeypatch.setattr(services, "_user_pipeline_run_and_artifacts", lambda *_: (run, []))

    with pytest.raises(ValueError, match="No planning job is available for this run"):
        services.resolve_user_pipeline_run_planning_paths(
            owner_user_id="owner-1",
            run_id="run-zero",
        )


def test_nonzero_run_requires_nonempty_corpus_but_valid_corpus_resolves(tmp_path, monkeypatch):
    output_dir = (
        tmp_path
        / "tmp"
        / "pipeline_runs"
        / "owner-1"
        / "run-valid"
        / "application_planning"
    )
    output_dir.mkdir(parents=True)
    corpus = output_dir / "current_run_job_corpus.jsonl"
    run = _run_record(output_dir, final_job_count=1)
    monkeypatch.setattr(services, "_user_pipeline_run_and_artifacts", lambda *_: (run, []))

    corpus.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="planning corpus.*unavailable"):
        services.resolve_user_pipeline_run_planning_paths(
            owner_user_id="owner-1",
            run_id="run-valid",
        )

    corpus.write_text('{"job_doc_id":"job-1"}\n', encoding="utf-8")
    resolved_output, resolved_corpus = services.resolve_user_pipeline_run_planning_paths(
        owner_user_id="owner-1",
        run_id="run-valid",
    )
    assert resolved_output == output_dir.resolve()
    assert resolved_corpus == corpus.resolve()


def test_zero_job_success_hides_planning_and_uses_actionable_copy():
    source = APP_JS.read_text(encoding="utf-8")

    assert '"No jobs matched this run"' in source
    assert '"No jobs passed the configured role, location, and freshness filters."' in source
    assert 'classList.toggle("hidden", summary.isEmptyResult)' in source
    assert 'window.location.href = "/planning"' in source
    assert "setTimeout" not in source[source.index("function renderPipelineSuccessSummary") : source.index("function renderPipelineFailureSummary")]


def test_generate_suggestions_has_safe_zero_and_missing_corpus_messages():
    source = PLANNING_JS.read_text(encoding="utf-8")

    assert 'return "No planning job is available for this run."' in source
    assert "The planning corpus for this completed run is unavailable." in source
    assert "tmp/pipeline_runs" not in source[source.index("function extractGenerateSuggestionsError") : source.index("async function handleGenerateSuggestionsClick")]


def test_terminal_workflow_overlay_is_compact_and_collapses_progress_steps():
    css = CSS.read_text(encoding="utf-8")

    assert "width: min(840px, 88vw) !important" in css
    assert "height: auto !important" in css
    assert "max-height: 82dvh !important" in css
    assert "font-size: clamp(32px, 3vw, 42px) !important" in css
    assert ".workflow-overlay__panel.is-success .workflow-overlay__body" in css
    assert "display: none !important" in css
    assert ".workflow-overlay__panel.is-error" in css
    assert "width: min(680px, 90vw) !important" in css
    assert "background: transparent !important" in css
