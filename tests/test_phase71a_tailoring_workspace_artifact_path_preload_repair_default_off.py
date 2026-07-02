import json
import inspect
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app import api
from src.app import planning_ui
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


def _write_direction_only_tailoring_artifact(output_dir: Path) -> Path:
    packet_dir = output_dir / "job_packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = packet_dir / "acme__platform_engineer__resume__tailoring.json"
    artifact_path.write_text(
        json.dumps(
            {
                "job": {
                    "company": "Acme",
                    "title": "Platform Engineer",
                    "description": "Build Python workflow systems.",
                    "job_doc_id": "job-acme-platform",
                },
                "selection": {"selected_resume": "resume.pdf"},
                "app_ready_replacements": [],
                "direct_apply_optional_replacements": [],
                "ai_optimize_optional_replacements": [],
                "rewrite_directions": [
                    {
                        "prefix": "Lead with",
                        "source": "resume:experience:1",
                        "direction": "Emphasize workflow automation context.",
                    }
                ],
                "shadow_replacement_candidates": [
                    {
                        "candidate_id": "direction-1",
                        "proposal_status": "direction_only",
                        "rewrite_direction": "Lead with workflow automation evidence.",
                    }
                ],
                "final_replacement_summary": {
                    "app_ready_count": 0,
                    "direct_apply_optional_count": 0,
                    "ai_optimize_optional_count": 0,
                    "direction_only_count": 1,
                },
            }
        ),
        encoding="utf-8",
    )
    return artifact_path


def _write_base_packet(output_dir: Path, *, selected_resume: str = "resume.pdf") -> Path:
    packet_dir = output_dir / "job_packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_path = packet_dir / "acme__platform_engineer__resume.json"
    packet_path.write_text(
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
                "selection": {"selected_resume": selected_resume},
                "resume": {"filename": selected_resume},
            }
        ),
        encoding="utf-8",
    )
    return packet_path


def test_run_scoped_tailoring_artifact_loads_without_relaxing_path_guard(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_tailoring_artifact(output_dir)
    artifact_key = artifact_path.relative_to(output_dir).as_posix()

    payload = services.planning_artifact_payload(
        path=artifact_key,
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
    artifact_key = artifact_path.relative_to(output_dir).as_posix()

    draft = services.load_tailoring_workspace_draft_payload(
        output_dir=output_dir,
        tailoring_json_path=artifact_key,
        selected_resume="resume.pdf",
    )
    preload = services.tailoring_scan_preload_payload(
        output_dir=output_dir,
        tailoring_json_path=artifact_key,
        selected_resume="resume.pdf",
    )

    assert draft["ok"] is True
    assert draft["draft"]["selected_resume"] == "resume.pdf"
    assert preload["ok"] is True
    assert preload["selected_resume"] == "resume.pdf"
    assert preload["job"]["company"] == "Acme"
    assert preload["tailoring_json_path"] == artifact_key
    assert preload["artifact_references"]["tailoring_json_key"] == artifact_key


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
    assert row["tailoring_json_key"] == artifact_path.relative_to(output_dir).as_posix()


def test_no_artifact_paths_remain_unavailable_tailoring_state(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"

    matches, row = services._row_matches_tailoring_state_filter(
        {
            "job_doc_id": "job-acme-platform",
        },
        ["unavailable"],
        output_dir=output_dir,
    )

    assert matches is True
    assert row["tailoring_workspace_state"] == "unavailable"
    assert row["tailoring_actionable_replacement_count"] == 0
    assert row["tailoring_review_replacement_count"] == 0


def test_direction_only_artifacts_are_no_safe_rewrites_not_unavailable(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_direction_only_tailoring_artifact(output_dir)

    unavailable_matches, unavailable_row = services._row_matches_tailoring_state_filter(
        {
            "job_doc_id": "job-acme-platform",
            "tailoring_json": str(artifact_path),
        },
        ["unavailable"],
        output_dir=output_dir,
    )
    no_safe_matches, no_safe_row = services._row_matches_tailoring_state_filter(
        {
            "job_doc_id": "job-acme-platform",
            "tailoring_json": str(artifact_path),
        },
        ["no_safe_rewrites"],
        output_dir=output_dir,
    )

    assert unavailable_matches is False
    assert unavailable_row["tailoring_workspace_state"] == "no_safe_rewrites"
    assert no_safe_matches is True
    assert no_safe_row["tailoring_workspace_state"] == "no_safe_rewrites"
    assert no_safe_row["tailoring_actionable_replacement_count"] == 0
    assert no_safe_row["tailoring_review_replacement_count"] == 1


def test_safe_rewrite_artifacts_remain_ready_and_workspace_openable(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_tailoring_artifact(output_dir, suggestions=True)

    matches, row = services._row_matches_tailoring_state_filter(
        {
            "job_doc_id": "job-acme-platform",
            "tailoring_json": str(artifact_path),
        },
        ["ready"],
        output_dir=output_dir,
    )

    assert matches is True
    assert row["tailoring_workspace_state"] == "ready"
    assert row["tailoring_actionable_replacement_count"] == 1


def test_browse_tailoring_state_filters_separate_unavailable_and_no_safe_rewrites(
    monkeypatch, tmp_path
):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    empty_tailoring_artifact = _write_tailoring_artifact(output_dir, suggestions=False)
    direction_only_llm_artifact = _write_direction_only_tailoring_artifact(
        output_dir / "llm_direction_only"
    )
    ready_artifact = _write_tailoring_artifact(output_dir / "ready", suggestions=True)

    manifest_rows = [
        {
            "queue_rank": "1",
            "job_doc_id": "job-no-artifact",
            "job_company": "No Artifact Co",
            "job_title": "Pending Variant",
            "packet_status": "pending_variant_selection",
        },
        {
            "queue_rank": "2",
            "job_doc_id": "job-direction-only",
            "job_company": "Direction Co",
            "job_title": "Direction Only",
            "packet_status": "generated",
            "tailoring_json": str(empty_tailoring_artifact),
            "tailoring_llm_json": str(direction_only_llm_artifact),
            "packet_json": str(output_dir / "job_packets" / "direction.json"),
        },
        {
            "queue_rank": "3",
            "job_doc_id": "job-ready",
            "job_company": "Ready Co",
            "job_title": "Ready Role",
            "packet_status": "generated",
            "tailoring_json": str(ready_artifact),
            "packet_json": str(output_dir / "ready" / "job_packets" / "ready.json"),
        },
    ]

    monkeypatch.setattr(
        services,
        "_latest_user_pipeline_artifact_context",
        lambda owner_user_id="": {
            "output_dir": str(output_dir),
            "best_rows": [],
            "queue_rows": [],
            "manifest_rows": manifest_rows,
            "job_prioritization_rows": [],
            "tailoring_decision_rows": [],
            "operator_review_rows": [],
            "current_run_job_corpus_text": "",
        },
    )
    monkeypatch.setattr(services._job_app(), "_overlay_operator_decisions", lambda rows: rows)
    monkeypatch.setattr(services, "_overlay_application_actions", lambda rows, owner_user_id="": rows)
    monkeypatch.setattr(services, "_exclude_applied_rows", lambda rows: rows)

    unavailable_payload = services.browse_payload(
        output_dir=output_dir,
        tailoring_state=["unavailable"],
        limit=15,
    )
    no_safe_payload = services.browse_payload(
        output_dir=output_dir,
        tailoring_state=["no_safe_rewrites"],
        limit=15,
    )
    ready_payload = services.browse_payload(
        output_dir=output_dir,
        tailoring_state=["ready"],
        limit=15,
    )

    assert [row["job_doc_id"] for row in unavailable_payload["rows"]] == ["job-no-artifact"]
    assert unavailable_payload["rows"][0]["tailoring_workspace_state"] == "unavailable"

    assert [row["job_doc_id"] for row in no_safe_payload["rows"]] == ["job-direction-only"]
    assert no_safe_payload["rows"][0]["tailoring_workspace_state"] == "no_safe_rewrites"
    assert no_safe_payload["rows"][0]["tailoring_actionable_replacement_count"] == 0

    assert [row["job_doc_id"] for row in ready_payload["rows"]] == ["job-ready"]
    assert ready_payload["rows"][0]["tailoring_workspace_state"] == "ready"
    assert ready_payload["rows"][0]["tailoring_actionable_replacement_count"] == 1


def test_source_resume_preview_uses_resume_resolver_not_planning_artifact_guard(monkeypatch, tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_tailoring_artifact(output_dir)
    artifact_key = artifact_path.relative_to(output_dir).as_posix()
    source_resume_path = tmp_path / "profile_resume_library" / "resume.pdf"
    source_resume_path.parent.mkdir(parents=True)
    source_resume_path.write_bytes(b"%PDF-1.4\n%test\n")

    resolver_calls = []

    def fake_resume_preview_path(resume_name, *, owner_user_id=""):
        resolver_calls.append((resume_name, owner_user_id))
        return source_resume_path

    monkeypatch.setattr(services, "planning_resume_preview_path", fake_resume_preview_path)
    monkeypatch.setattr(
        services,
        "_extract_resume_pdf_paragraph_pages_for_export",
        lambda path: [
            {
                "page_number": 1,
                "width": 612,
                "height": 792,
                "blocks": [
                    {
                        "paragraphs": [
                            {
                                "text": "Built Python services.",
                                "alignment": "left",
                                "gap_before": 0,
                                "left_indent_pt": 0,
                                "is_bullet": True,
                            }
                        ]
                    }
                ],
            }
        ],
    )

    payload = services.render_tailoring_workspace_draft_preview_payload(
        output_dir=output_dir,
        tailoring_json_path=artifact_key,
        selected_resume="resume.pdf",
        owner_user_id="owner-1",
    )

    assert payload["ok"] is True
    assert payload["preview_status"] == "rendered"
    assert resolver_calls == [("resume.pdf", "owner-1")]
    assert source_resume_path.parent != output_dir


def test_missing_optional_tailoring_artifact_returns_no_suggestions_not_http_400(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    packet_path = _write_base_packet(output_dir)
    missing_tailoring_key = (
        packet_path.with_name("acme__platform_engineer__resume__tailoring.json")
        .relative_to(output_dir)
        .as_posix()
    )

    payload = services.planning_artifact_payload(
        path=missing_tailoring_key,
        output_dir=output_dir,
    )
    draft = services.load_tailoring_workspace_draft_payload(
        output_dir=output_dir,
        tailoring_json_path=missing_tailoring_key,
        selected_resume="resume.pdf",
    )

    assert payload["ok"] is True
    assert payload["artifact_status"] == "missing_optional_tailoring_artifact"
    assert payload["data"]["missing_tailoring_artifact"] is True
    assert payload["data"]["replacement_candidates"] == []
    assert payload["data"]["ai_optimize_optional_replacements"] == []
    assert "Optional tailoring suggestions were not generated" in payload["data"]["no_suggestions_reason"]
    assert draft["ok"] is True
    assert draft["missing_tailoring_artifact"] is True
    assert draft["tailoring_artifact_status"] == "missing_optional"
    assert draft["draft"]["selected_resume"] == "resume.pdf"
    assert draft["draft"]["selected_patch_candidate_ids"] == []


def test_ai_optimize_preload_uses_base_packet_when_tailoring_artifact_is_absent(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    packet_path = _write_base_packet(output_dir)
    missing_tailoring_key = (
        packet_path.with_name("acme__platform_engineer__resume__tailoring.json")
        .relative_to(output_dir)
        .as_posix()
    )

    preload = services.tailoring_scan_preload_payload(
        output_dir=output_dir,
        tailoring_json_path=missing_tailoring_key,
        selected_resume="resume.pdf",
    )

    assert preload["ok"] is True
    assert preload["preload_mode"] == "base_packet_no_suggestions"
    assert preload["scan_entry_source"] == "base_planning_packet"
    assert preload["tailoring_artifact_status"] == "missing_optional"
    assert preload["missing_tailoring_artifact"] is True
    assert preload["job"]["company"] == "Acme"
    assert preload["selected_resume"] == "resume.pdf"
    assert preload["trusted_suggestions"]["direct_apply_ready"] == []
    assert preload["trusted_suggestions"]["direct_apply_optional"] == []
    assert preload["ai_optimize_suggestions"] == []
    assert preload["lane_counts"] == {
        "direct_apply_ready": 0,
        "direct_apply_optional": 0,
        "ai_optimize_optional": 0,
        "direction_only": 0,
    }
    assert preload["artifact_references"]["packet_json_key"] == packet_path.relative_to(output_dir).as_posix()


def test_missing_optional_tailoring_artifact_preview_uses_source_resume_resolver(monkeypatch, tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    packet_path = _write_base_packet(output_dir)
    missing_tailoring_key = (
        packet_path.with_name("acme__platform_engineer__resume__tailoring.json")
        .relative_to(output_dir)
        .as_posix()
    )
    source_resume_path = tmp_path / "profile_resume_library" / "resume.pdf"
    source_resume_path.parent.mkdir(parents=True)
    source_resume_path.write_bytes(b"%PDF-1.4\n%test\n")

    resolver_calls = []

    def fake_resume_preview_path(resume_name, *, owner_user_id=""):
        resolver_calls.append((resume_name, owner_user_id))
        return source_resume_path

    monkeypatch.setattr(services, "planning_resume_preview_path", fake_resume_preview_path)
    monkeypatch.setattr(
        services,
        "_extract_resume_pdf_paragraph_pages_for_export",
        lambda path: [
            {
                "page_number": 1,
                "width": 612,
                "height": 792,
                "blocks": [
                    {
                        "paragraphs": [
                            {
                                "text": "Built Python services.",
                                "alignment": "left",
                                "gap_before": 0,
                                "left_indent_pt": 0,
                                "is_bullet": True,
                            }
                        ]
                    }
                ],
            }
        ],
    )

    payload = services.render_tailoring_workspace_draft_preview_payload(
        output_dir=output_dir,
        tailoring_json_path=missing_tailoring_key,
        selected_resume="resume.pdf",
        owner_user_id="owner-1",
    )

    assert payload["ok"] is True
    assert payload["preview_status"] == "rendered"
    assert resolver_calls == [("resume.pdf", "owner-1")]
    assert source_resume_path.parent != output_dir


def test_resume_preview_resolver_reroutes_accidental_tailoring_artifact_to_packet_resume(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    packet_path = _write_base_packet(output_dir, selected_resume="resume.pdf")
    missing_tailoring_key = (
        packet_path.with_name("acme__platform_engineer__resume__tailoring.json")
        .relative_to(output_dir)
        .as_posix()
    )

    resolved = services.resolve_resume_preview_name_from_planning_context(
        resume_name=missing_tailoring_key,
        packet_json_path=packet_path.relative_to(output_dir).as_posix(),
        output_dir=output_dir,
    )

    assert resolved == "resume.pdf"


def test_resume_preview_resolver_does_not_render_tailoring_artifact_without_packet(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"

    with pytest.raises(ValueError, match="optional tailoring artifacts cannot be rendered"):
        services.resolve_resume_preview_name_from_planning_context(
            resume_name="job_packets/acme__platform_engineer__resume__tailoring.json",
            output_dir=output_dir,
        )


def test_missing_required_base_packet_still_fails_safely(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"

    with pytest.raises(ValueError, match="Artifact not found"):
        services.planning_artifact_payload(
            path="job_packets/acme__platform_engineer__resume__tailoring.json",
            output_dir=output_dir,
        )


def test_actual_workspace_suggestion_route_returns_no_suggestions_for_missing_tailoring_json(monkeypatch, tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    packet_path = _write_base_packet(output_dir)
    missing_tailoring_key = (
        packet_path.with_name("acme__platform_engineer__resume__tailoring.json")
        .relative_to(output_dir)
        .as_posix()
    )
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    client = TestClient(api.app)

    response = client.get(
        "/planning-artifact",
        params={"path": missing_tailoring_key, "output_dir": str(output_dir)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["missing_tailoring_artifact"] is True
    assert payload["data"]["replacement_candidates"] == []


def test_actual_ai_optimize_preload_route_uses_base_packet_for_missing_tailoring_json(monkeypatch, tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    packet_path = _write_base_packet(output_dir)
    missing_tailoring_key = (
        packet_path.with_name("acme__platform_engineer__resume__tailoring.json")
        .relative_to(output_dir)
        .as_posix()
    )
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    client = TestClient(api.app)

    response = client.post(
        "/planning/scan-preload",
        params={"output_dir": str(output_dir)},
        json={"tailoring_json_path": missing_tailoring_key, "selected_resume": "resume.pdf"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["preload_mode"] == "base_packet_no_suggestions"
    assert payload["missing_tailoring_artifact"] is True
    assert payload["job"]["company"] == "Acme"
    assert payload["ai_optimize_suggestions"] == []


def test_actual_resume_preview_route_reroutes_tailoring_json_to_packet_resume(monkeypatch, tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    packet_path = _write_base_packet(output_dir)
    missing_tailoring_key = (
        packet_path.with_name("acme__platform_engineer__resume__tailoring.json")
        .relative_to(output_dir)
        .as_posix()
    )
    resolved_names = []

    def fake_profile_resume_file_payload(resume_name, *, owner_user_id=""):
        resolved_names.append(resume_name)
        return {
            "file_bytes": b"%PDF-1.4\n%route-test\n",
            "content_type": "application/pdf",
            "size_bytes": 21,
        }

    monkeypatch.setattr(services, "profile_resume_file_payload", fake_profile_resume_file_payload)
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    client = TestClient(api.app)

    response = client.get(
        "/planning/resume-preview",
        params={
            "resume_name": missing_tailoring_key,
            "packet_json": packet_path.relative_to(output_dir).as_posix(),
            "output_dir": str(output_dir),
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert resolved_names == ["resume.pdf"]


def test_planning_ui_tailoring_workspace_metadata_resolves_resume_separately_from_suggestions(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    packet_path = _write_base_packet(output_dir)
    packet_key = packet_path.relative_to(output_dir).as_posix()
    missing_tailoring_key = (
        packet_path.with_name("acme__platform_engineer__resume__tailoring.json")
        .relative_to(output_dir)
        .as_posix()
    )

    html = planning_ui.tailoring_workspace(
        company="Acme",
        title="Platform Engineer",
        resume=missing_tailoring_key,
        tailoring_json=missing_tailoring_key,
        packet_json=packet_key,
        output_dir=str(output_dir),
    )

    assert 'data-resume-name="resume.pdf"' in html
    assert 'data-tailoring-json-path="job_packets/acme__platform_engineer__resume__tailoring.json"' in html
    assert 'data-packet-json-path="job_packets/acme__platform_engineer__resume.json"' in html
    assert 'data-resume-name="job_packets/acme__platform_engineer__resume__tailoring.json"' not in html
    assert 'resume=job_packets/acme__platform_engineer__resume__tailoring.json' not in html


def test_planning_ui_scan_workspace_metadata_resolves_resume_separately_from_suggestions(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    packet_path = _write_base_packet(output_dir)
    packet_key = packet_path.relative_to(output_dir).as_posix()
    missing_tailoring_key = (
        packet_path.with_name("acme__platform_engineer__resume__tailoring.json")
        .relative_to(output_dir)
        .as_posix()
    )

    html = planning_ui.scan_workspace(
        company="Acme",
        title="Platform Engineer",
        resume=missing_tailoring_key,
        tailoring_json=missing_tailoring_key,
        packet_json=packet_key,
        output_dir=str(output_dir),
    )

    assert 'data-resume-name="resume.pdf"' in html
    assert 'data-tailoring-json-path="job_packets/acme__platform_engineer__resume__tailoring.json"' in html
    assert 'data-packet-json-path="job_packets/acme__platform_engineer__resume.json"' in html
    assert 'data-resume-name="job_packets/acme__platform_engineer__resume__tailoring.json"' not in html
    assert 'resume=job_packets/acme__platform_engineer__resume__tailoring.json' not in html


def test_browser_readback_code_passes_run_scoped_output_dir_to_guarded_endpoints():
    planning_js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    scan_workspace_js = Path("src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    app_js = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_ui = Path("src/app/planning_ui.py").read_text(encoding="utf-8")

    assert "data-planning-output-dir" in planning_ui
    assert "planning_output_dir" in planning_js
    assert "tailoring_json_key" in planning_js
    assert "getTailoringWorkspaceSuggestionArtifactKey" in planning_js
    assert "getTailoringWorkspaceBasePacketKey" in planning_js
    assert "normalizeResumePreviewName" in planning_js
    assert "suggestion_artifact_path" in planning_js
    assert "base_packet_path" in planning_js
    assert "buildArtifactUrl(path, outputDir" in planning_js
    assert 'params.set("output_dir", safeOutputDir)' in planning_js
    assert 'params.set("tailoring_json", row.tailoring_json_key || row.tailoring_json)' in planning_js
    assert 'params.set("resume_name", safeName || "__resolve_from_packet__")' in planning_js
    assert "buildResumePdfFileUrl(safeName, context)" in planning_js
    assert '"/planning/scan-preload", context.planningOutputDir' in planning_js
    assert "tailoring_json_path: context.tailoringJsonPath" not in planning_js
    assert "selected_resume: context.resumeName" not in planning_js
    assert "buildScanWorkspacePlanningEndpoint" in scan_workspace_js
    assert "getScanWorkspaceArtifactKey" in scan_workspace_js
    assert "getScanWorkspaceBasePacketKey" in scan_workspace_js
    assert "normalizeScanWorkspaceResumePreviewName" in scan_workspace_js
    assert "planningOutputDir" in scan_workspace_js
    assert "tailoring_json_path: context.tailoringJsonPath" not in scan_workspace_js
    assert "tailoring_json_path: payload.tailoring_json_path" not in scan_workspace_js
    assert "tailoring_json_path" not in app_js
    assert "resumePreview" not in app_js
    assert "split(\"/\")" in planning_js
    assert "resolve_resume_preview_name_from_planning_context" in planning_ui

    guarded_sources = {
        "app.js": app_js,
        "planning.js": planning_js,
        "scan_workspace.js": scan_workspace_js,
        "planning_ui.py": planning_ui,
    }
    forbidden_patterns = [
        r"resume[^\\n]{0,80}tailoring_json_path",
        r"preview[^\\n]{0,80}tailoring_json_path",
        r"preload[^\\n]{0,80}tailoring_json_path",
        r"resume[^\\n]{0,120}__tailoring\.json",
        r"preview[^\\n]{0,120}__tailoring\.json",
        r"preload[^\\n]{0,120}__tailoring\.json",
    ]
    import re

    for source_name, source_text in guarded_sources.items():
        for pattern in forbidden_patterns:
            assert not re.search(pattern, source_text, flags=re.IGNORECASE), (
                source_name,
                pattern,
            )

    assert "tailoring_json_path: getTailoringWorkspaceSuggestionArtifactKey" in planning_js
    assert "tailoring_json_path: suggestionArtifactPath" in scan_workspace_js


def test_planning_table_workspace_button_blocks_rows_without_actionable_content():
    planning_js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    planning_ui_source = Path("src/app/planning_ui.py").read_text(encoding="utf-8")

    assert "function getWorkspaceBlockedReason(row)" in planning_js
    assert "No safe bullet-level rewrites were found for this row." in planning_js
    assert 'workspaceState === "no_safe_rewrites"' in planning_js
    assert 'data-value="no_safe_rewrites"' in planning_ui_source
    assert "No safe rewrites" in planning_ui_source
    assert "LLM tailoring generation is off for this row." in planning_js
    assert "data-workspace-blocked-reason" in planning_js
    assert 'const disabledAttr = hasArtifacts && !blockedReason ? "" : "disabled";' in planning_js
    assert 'showAppError("Workspace unavailable", new Error(blockedReason))' not in planning_js
    assert "actionableCount <= 0" in planning_js
    assert '"review"' in planning_js
    assert '"unavailable"' in planning_js
    assert '"disabled"' in planning_js


def test_planning_table_workspace_button_preserves_eligible_navigation():
    planning_js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    handler_source = planning_js.split("async function handleTailoringClick(button)", 1)[1].split(
        "function openApplicationModal", 1
    )[0]

    assert "button.dataset.workspaceBlockedReason" in handler_source
    assert 'showAppError("Workspace unavailable"' not in handler_source
    assert "window.location.href = buildTailoringWorkspaceUrl(row);" in handler_source
    assert handler_source.index("button.dataset.workspaceBlockedReason") < handler_source.index(
        "window.location.href = buildTailoringWorkspaceUrl(row);"
    )


def test_no_provider_artifact_creation_or_application_execution_added_by_repair():
    changed_sources = "\n".join(
        [
            inspect.getsource(services._infer_planning_output_dir_from_row),
            inspect.getsource(services._planning_artifact_key_for_row_path),
            inspect.getsource(services._row_matches_tailoring_state_filter),
            inspect.getsource(services._resolve_planning_artifact_path),
            inspect.getsource(services._load_tailoring_artifact_or_packet_fallback),
            inspect.getsource(services.resolve_resume_preview_name_from_planning_context),
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
