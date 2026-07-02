import json
import inspect
from pathlib import Path

import pytest

from src.app import services


def _write_tailoring_artifact(output_dir: Path, *, suggestions: bool = True) -> Path:
    packet_dir = output_dir / "job_packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = packet_dir / "acme__platform_engineer__resume__tailoring.json"
    ready = [
        {
            "best_candidate_id": "candidate-1",
            "section": "Experience",
            "source": "resume",
            "current_bullet": "Built Python services.",
            "recommended_rewrite": "Built production Python services for workflow automation.",
        }
    ] if suggestions else []
    artifact_path.write_text(
        json.dumps(
            {
                "job": {
                    "company": "Acme",
                    "title": "Platform Engineer",
                    "description": "Build Python workflow systems.",
                    "job_doc_id": "job-acme-platform",
                },
                "job_snapshot": {
                    "company": "Acme",
                    "title": "Platform Engineer",
                    "job_url": "https://example.test/jobs/platform",
                    "description_text": "Build Python workflow systems.",
                },
                "selection": {"selected_resume": "resume.pdf"},
                "replacement_candidates": ready,
                "app_ready_replacements": ready,
                "direct_apply_optional_replacements": [],
                "ai_optimize_optional_replacements": [],
                "direction_only_replacements": [],
                "final_replacement_summary": {},
                "rewrite_review_summary": {},
                "rewrite_review_groups": [],
            }
        ),
        encoding="utf-8",
    )
    return artifact_path


def test_run_scoped_tailoring_artifact_loads_without_relaxing_path_guard(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_tailoring_artifact(output_dir)

    payload = services.planning_artifact_payload(
        path=str(artifact_path),
        output_dir=output_dir,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "json"
    assert payload["data"]["job"]["company"] == "Acme"

    with pytest.raises(ValueError, match="Artifact path must stay inside"):
        services.planning_artifact_payload(
            path=str(artifact_path),
            output_dir=tmp_path / "other-run" / "application_planning",
        )


def test_tailoring_workspace_draft_and_scan_preload_use_same_run_scoped_output_dir(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_tailoring_artifact(output_dir)

    draft = services.load_tailoring_workspace_draft_payload(
        output_dir=output_dir,
        tailoring_json_path=str(artifact_path),
        selected_resume="resume.pdf",
    )
    preload = services.tailoring_scan_preload_payload(
        output_dir=output_dir,
        tailoring_json_path=str(artifact_path),
        selected_resume="resume.pdf",
    )

    assert draft["ok"] is True
    assert draft["draft"]["selected_resume"] == "resume.pdf"
    assert preload["ok"] is True
    assert preload["selected_resume"] == "resume.pdf"
    assert preload["job"]["company"] == "Acme"
    assert preload["artifact_references"]["tailoring_json_path"] == str(artifact_path)


def test_missing_suggestions_are_safe_no_suggestions_state_not_failed_load(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_tailoring_artifact(output_dir, suggestions=False)

    draft = services.load_tailoring_workspace_draft_payload(
        output_dir=output_dir,
        tailoring_json_path=str(artifact_path),
        selected_resume="resume.pdf",
    )
    matches, row = services._row_matches_tailoring_state_filter(
        {
            "job_doc_id": "job-acme-platform",
            "tailoring_json": str(artifact_path),
        },
        [],
        output_dir=services.DEFAULT_OUTPUT_DIR,
    )

    assert draft["ok"] is True
    assert matches is True
    assert row["tailoring_workspace_state"] == "unavailable"
    assert row["tailoring_actionable_replacement_count"] == 0
    assert row["planning_output_dir"] == str(output_dir)


def test_browser_readback_code_passes_run_scoped_output_dir_to_guarded_endpoints():
    planning_js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    scan_workspace_js = Path("src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    planning_ui = Path("src/app/planning_ui.py").read_text(encoding="utf-8")

    assert "data-planning-output-dir" in planning_ui
    assert "planning_output_dir" in planning_js
    assert "buildArtifactUrl(path, outputDir" in planning_js
    assert 'params.set("output_dir", safeOutputDir)' in planning_js
    assert 'params.set("output_dir", row.planning_output_dir)' in planning_js
    assert '"/planning/scan-preload", context.planningOutputDir' in planning_js
    assert "buildScanWorkspacePlanningEndpoint" in scan_workspace_js
    assert "planningOutputDir" in scan_workspace_js


def test_no_provider_artifact_creation_or_application_execution_added_by_repair():
    changed_sources = "\n".join(
        [
            inspect.getsource(services._infer_planning_output_dir_from_row),
            inspect.getsource(services._row_matches_tailoring_state_filter),
            inspect.getsource(services._resolve_planning_artifact_path),
        ]
    )

    forbidden_markers = [
        "openai",
        "anthropic",
        "requests.post",
        "httpx",
        "enqueue_apply",
        "submit_application",
        "mark_applied",
    ]
    for marker in forbidden_markers:
        assert marker not in changed_sources.lower()
