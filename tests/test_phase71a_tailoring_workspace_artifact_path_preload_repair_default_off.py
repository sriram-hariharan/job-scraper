import json
import inspect
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.app import api
from src.app import planning_ui
from src.app import services

PLANNING_JS = Path("src/app/static/planning.js")


def _source() -> str:
    return PLANNING_JS.read_text(encoding="utf-8")


def _function_source(source: str, name: str) -> str:
    # Extracts one real function's source by brace-matching, the same
    # technique used in tests/test_phase110b_generate_suggestions_loader_static_only.py,
    # so workspace-gating tests execute the actual planning.js code rather
    # than a reimplementation.
    start = source.index(f"function {name}")
    paren = source.index("(", start)
    depth = 0
    brace = -1
    for index in range(paren, len(source)):
        if source[index] == "(":
            depth += 1
        elif source[index] == ")":
            depth -= 1
            if depth == 0:
                brace = source.index("{", index)
                break
    assert brace >= 0
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"could not extract function {name}")


@pytest.fixture
def synthetic_resume_dir(monkeypatch, tmp_path):
    resume_dir = tmp_path / "synthetic_resumes"
    resume_dir.mkdir()
    (resume_dir / "resume.pdf").write_bytes(b"%PDF-1.4\n%synthetic-test\n")
    monkeypatch.setenv("RESUME_DIR", str(resume_dir))
    monkeypatch.setattr(
        "src.resume.resume_loader.extract_resume_texts",
        lambda _path: {
            "raw_text": "Built Python services.",
            "text": "Built Python services.",
        },
    )
    return resume_dir


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


def test_run_scoped_tailoring_artifact_loads_without_relaxing_path_guard(
    tmp_path,
    synthetic_resume_dir,
):
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


def test_repo_relative_run_scoped_artifact_path_resolves_inside_output_guard(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    output_dir = Path("tmp/pipeline_runs/owner-1/run-1/application_planning")
    artifact_path = output_dir / "job_packets" / "sample__tailoring_llm.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps({"parse_ok": True, "parsed": {}}), encoding="utf-8")

    resolved = services._resolve_planning_artifact_path(
        str(artifact_path),
        output_dir=output_dir,
    )

    assert resolved == artifact_path.resolve()
    assert resolved.relative_to(output_dir.resolve())

    outside_artifact = Path("tmp/pipeline_runs/owner-1/other-run/application_planning/job_packets/outside.json")
    outside_artifact.parent.mkdir(parents=True, exist_ok=True)
    outside_artifact.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Artifact"):
        services._resolve_planning_artifact_path(
            str(outside_artifact),
            output_dir=output_dir,
        )


def test_tailoring_workspace_draft_and_scan_preload_use_same_run_scoped_output_dir(
    tmp_path,
    synthetic_resume_dir,
):
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


def test_ai_optimize_preload_merges_saved_github_with_extracted_linkedin(
    monkeypatch,
    tmp_path,
    synthetic_resume_dir,
):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_tailoring_artifact(output_dir)
    artifact_key = artifact_path.relative_to(output_dir).as_posix()

    services.save_tailoring_workspace_draft_payload(
        output_dir=output_dir,
        tailoring_json_path=artifact_key,
        selected_resume="resume.pdf",
        personal_details={
            "name": "Alex Rivera",
            "email": "alex@example.com",
            "linkedin": "",
            "github": "github.com/alexrivera",
        },
    )
    monkeypatch.setattr(
        services,
        "preview_tailoring_workspace_draft_payload",
        lambda *args, **kwargs: {
            "preview_status": "ok",
            "preview_note": "",
            "original_score": 72,
            "projected_score": 72,
            "projected_delta": 0,
            "score_preview": {},
        },
    )
    monkeypatch.setattr(
        services,
        "_load_resume_evidence_for_workspace_preview",
        lambda *args, **kwargs: SimpleNamespace(
            document=SimpleNamespace(
                resume_name="resume.pdf",
                raw_text=(
                    "Alex Rivera\n"
                    "Harrison, NJ | +1 (555) 123-4567 | alex@example.com | "
                    "linkedin.com/in/alexrivera | github.com/sourceprofile"
                ),
                normalized_text="",
            )
        ),
    )

    preload = services.tailoring_scan_preload_payload(
        output_dir=output_dir,
        tailoring_json_path=artifact_key,
        selected_resume="resume.pdf",
    )

    assert preload["personal_details"]["extracted"]["linkedin"] == "https://linkedin.com/in/alexrivera"
    assert preload["personal_details"]["saved"]["github"] == "https://github.com/alexrivera"
    assert preload["personal_details"]["current"]["linkedin"] == "https://linkedin.com/in/alexrivera"
    assert preload["personal_details"]["current"]["github"] == "https://github.com/alexrivera"
    assert preload["draft"]["personal_details"]["linkedin"] == ""


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


def test_placeholder_bullet_diagnosis_does_not_create_review_guidance():
    state = services._derive_workspace_button_state_from_raw_payload(
        {
            "empty_state_reason": {"code": "no_grounded_rewrite_evidence"},
            "bullet_diagnoses": [
                {
                    "diagnosis_action": "keep",
                    "diagnosis_reason_type": "keep_as_is",
                    "source": "",
                    "entry_id": "",
                    "bullet_id": "",
                    "original_text": "",
                    "current_evidence": "",
                    "jd_signal_terms": [],
                    "likely_impacted_dimensions": [],
                    "recommended_rewrite": "",
                    "why": "Preserve truthful resume language.",
                }
            ],
        }
    )

    assert state["tailoring_workspace_state"] == "empty"
    assert state["tailoring_review_replacement_count"] == 0
    assert state["tailoring_has_review_guidance"] is False


def test_grounded_bullet_diagnosis_remains_no_safe_rewrites_guidance():
    state = services._derive_workspace_button_state_from_raw_payload(
        {
            "bullet_diagnoses": [
                {
                    "diagnosis_action": "keep",
                    "source": "Data Analyst @ ExampleCo",
                    "entry_id": "experience:1",
                    "bullet_id": "experience:1:bullet:1",
                    "original_text": "Built SQL validation workflows.",
                    "current_evidence": "Built SQL validation workflows.",
                    "jd_signal_terms": ["SQL", "workflow"],
                    "recommended_rewrite": "",
                }
            ],
        }
    )

    assert state["tailoring_workspace_state"] == "no_safe_rewrites"
    assert state["tailoring_review_replacement_count"] == 1
    assert state["tailoring_has_review_guidance"] is True


def test_anchor_evidence_remains_meaningful_without_actionable_rewrite():
    state = services._derive_workspace_button_state_from_raw_payload(
        {
            "anchor_cards": [
                {
                    "source": "Data Analyst @ ExampleCo",
                    "current_evidence": "Built SQL validation workflows.",
                }
            ],
        }
    )

    assert state["tailoring_workspace_state"] == "no_safe_rewrites"
    assert state["tailoring_review_replacement_count"] == 1
    assert state["tailoring_has_review_guidance"] is True


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
    expected_bulk_ids = ["job-no-artifact", "job-direction-only", "job-ready"]
    assert [row["job_doc_id"] for row in unavailable_payload["bulk_suggestion_rows"]] == expected_bulk_ids
    assert unavailable_payload["rows"][0]["tailoring_workspace_state"] == "unavailable"

    assert [row["job_doc_id"] for row in no_safe_payload["rows"]] == ["job-direction-only"]
    assert [row["job_doc_id"] for row in no_safe_payload["bulk_suggestion_rows"]] == expected_bulk_ids
    assert no_safe_payload["rows"][0]["tailoring_workspace_state"] == "no_safe_rewrites"
    assert no_safe_payload["rows"][0]["tailoring_actionable_replacement_count"] == 0

    assert [row["job_doc_id"] for row in ready_payload["rows"]] == ["job-ready"]
    assert [row["job_doc_id"] for row in ready_payload["bulk_suggestion_rows"]] == expected_bulk_ids
    assert ready_payload["rows"][0]["tailoring_workspace_state"] == "ready"
    assert ready_payload["rows"][0]["tailoring_actionable_replacement_count"] == 1


def test_browse_bulk_projection_uses_full_owner_run_universe_without_product_cap(
    monkeypatch, tmp_path
):
    output_dir = tmp_path / "pipeline_runs" / "owner-1" / "run-1" / "application_planning"
    output_dir.mkdir(parents=True)
    manifest_rows = [
        {
            "queue_rank": str(index),
            "job_doc_id": f"job-{index:03d}",
            "job_company": "Example Co",
            "job_title": f"Engineer {index:03d}",
            "action": "APPLY" if index <= 125 else "SKIP_FOR_NOW",
            "winner_resume": "Winner.pdf",
        }
        for index in range(1, 131)
    ]

    monkeypatch.setattr(
        services,
        "_latest_user_pipeline_artifact_context",
        lambda owner_user_id="": {
            "run_id": "run-1",
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

    payload = services.browse_payload(
        output_dir=output_dir,
        owner_user_id="owner-1",
        action=["APPLY"],
        sort_key="queue_rank",
        sort_dir="asc",
        limit=125,
        page=1,
    )

    assert payload["total_count"] == 125
    assert len(payload["rows"]) == 15
    assert len(payload["bulk_suggestion_rows"]) == 130
    assert [row["job_doc_id"] for row in payload["bulk_suggestion_rows"][:3]] == [
        "job-001",
        "job-002",
        "job-003",
    ]
    assert payload["bulk_suggestion_rows"][-1]["job_doc_id"] == "job-130"
    assert all(
        row["pipeline_run_id"] == "run-1"
        and row["planning_output_dir"] == str(output_dir)
        for row in payload["bulk_suggestion_rows"]
    )
    assert "job_description" not in payload["bulk_suggestion_rows"][0]
    assert "resume_text" not in payload["bulk_suggestion_rows"][0]
    assert payload["bulk_suggestion_rows"][0]["action"] == "APPLY"

    high_limit_payload = services.browse_payload(
        output_dir=output_dir,
        owner_user_id="owner-1",
        sort_key="queue_rank",
        sort_dir="asc",
        limit=1000,
        page=1,
    )
    assert high_limit_payload["filters"]["limit"] == 1000
    assert high_limit_payload["total_count"] == 130
    assert len(high_limit_payload["bulk_suggestion_rows"]) == 130


def test_bulk_selection_helper_preserves_all_applied_filter_stages_and_limit(
    monkeypatch, tmp_path
):
    captured = {"owner": "", "preferences": None, "tailoring": []}

    class FakeJobApp:
        def _select_browse_rows(self, rows, args):
            assert args.action == ["APPLY"]
            assert args.winner_bucket == ["strong"]
            assert args.undecided_only == "true"
            assert args.company_contains == "example"
            assert args.limit == len(rows)
            return [
                row for row in rows
                if row["action"] == "APPLY"
                and row["winner_bucket"] == "strong"
                and row["operator_decision"] == ""
            ]

    rows = [
        {
            "job_doc_id": "eligible-high",
            "action": "APPLY",
            "winner_bucket": "strong",
            "operator_decision": "",
            "preference_id": "pref-a",
            "tailoring_workspace_state": "unavailable",
            "winner_score": "0.9",
        },
        {
            "job_doc_id": "eligible-low",
            "action": "APPLY",
            "winner_bucket": "strong",
            "operator_decision": "",
            "preference_id": "pref-a",
            "tailoring_workspace_state": "unavailable",
            "winner_score": "0.5",
        },
        {
            "job_doc_id": "wrong-match",
            "action": "APPLY",
            "winner_bucket": "moderate",
            "operator_decision": "",
            "preference_id": "pref-a",
            "tailoring_workspace_state": "unavailable",
            "winner_score": "1.0",
        },
    ]

    def overlay(selected, owner_user_id=""):
        captured["owner"] = owner_user_id
        return selected

    def filter_preferences(selected, *, requested_ids, validated_ids):
        captured["preferences"] = (requested_ids, validated_ids)
        return [row for row in selected if row["preference_id"] in validated_ids]

    def match_tailoring(row, requested_states, *, output_dir):
        captured["tailoring"].append((requested_states, output_dir))
        return row["tailoring_workspace_state"] in requested_states, dict(row)

    monkeypatch.setattr(services, "_overlay_application_actions", overlay)
    monkeypatch.setattr(services, "_exclude_applied_rows", lambda selected: selected)
    monkeypatch.setattr(services, "_overlay_job_metadata_from_map", lambda selected, metadata: selected)
    monkeypatch.setattr(services, "_filter_browse_rows_by_preference_ids", filter_preferences)
    monkeypatch.setattr(services, "_row_matches_tailoring_state_filter", match_tailoring)

    selected = services._select_planning_browse_rows(
        FakeJobApp(),
        rows,
        resolved_filters={
            "action": ["APPLY"],
            "winner_bucket": ["strong"],
            "undecided_only": "true",
            "company_contains": "example",
            "sort_key": "winner_score",
            "sort_dir": "desc",
        },
        requested_limit=1,
        requested_tailoring_states=["unavailable"],
        requested_preference_ids=["pref-a"],
        validated_preference_ids=["pref-a"],
        owner_user_id="owner-1",
        effective_output_dir=tmp_path,
        artifact_context={"run_id": "run-1"},
        job_metadata_by_key={},
    )

    assert [row["job_doc_id"] for row in selected] == ["eligible-high"]
    assert captured["owner"] == "owner-1"
    assert captured["preferences"] == (["pref-a"], ["pref-a"])
    assert captured["tailoring"] == [
        (["unavailable"], tmp_path),
        (["unavailable"], tmp_path),
    ]


def test_authenticated_browse_tailoring_filter_uses_run_scoped_config_output_dir(
    monkeypatch, tmp_path
):
    output_dir = tmp_path / "pipeline_runs" / "owner-1" / "run-1" / "application_planning"
    empty_tailoring_artifact = _write_tailoring_artifact(output_dir, suggestions=False)
    direction_only_llm_artifact = _write_direction_only_tailoring_artifact(
        output_dir / "direction_only"
    )
    ready_artifact = _write_tailoring_artifact(output_dir / "ready", suggestions=True)

    manifest_path = output_dir / "job_packet_manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "\n".join(
            [
                "queue_rank,job_doc_id,job_company,job_title,packet_status,tailoring_json,tailoring_llm_json,packet_json",
                "1,job-no-artifact,No Artifact Co,Pending Variant,pending_variant_selection,,,",
                (
                    "2,job-direction-only,Direction Co,Direction Only,generated,"
                    f"{empty_tailoring_artifact},{direction_only_llm_artifact},"
                    f"{output_dir / 'job_packets' / 'direction.json'}"
                ),
                (
                    "3,job-ready,Ready Co,Ready Role,generated,"
                    f"{ready_artifact},,{output_dir / 'ready' / 'job_packets' / 'ready.json'}"
                ),
            ]
        ),
        encoding="utf-8",
    )

    def fake_runs_payload(**kwargs):
        return {
            "rows": [
                {
                    "run_id": "run-1",
                    "status": "succeeded",
                    "status_json": {
                        "config": {
                            "storage_mode": "run_scoped_scratch",
                            "job_corpus_path": str(output_dir / "current_run_job_corpus.jsonl"),
                            "launch_config_path": str(output_dir / "live_pipeline_launch_config.json"),
                            "status_path": str(output_dir / "live_pipeline_status.json"),
                            "log_path": str(output_dir / "live_pipeline_run.log"),
                        }
                    },
                }
            ]
        }

    def fail_if_postgres_artifacts_are_needed(**kwargs):
        raise AssertionError("filesystem run-scoped output should be discoverable from run config paths")

    monkeypatch.setattr(services, "get_user_pipeline_runs_postgres_payload", fake_runs_payload)
    monkeypatch.setattr(
        services,
        "get_user_pipeline_artifacts_postgres_payload",
        fail_if_postgres_artifacts_are_needed,
    )
    monkeypatch.setattr(services._job_app(), "_overlay_operator_decisions", lambda rows: rows)
    monkeypatch.setattr(services, "_overlay_application_actions", lambda rows, owner_user_id="": rows)
    monkeypatch.setattr(services, "_exclude_applied_rows", lambda rows: rows)

    unavailable_payload = services.browse_payload(
        owner_user_id="owner-1",
        tailoring_state=["unavailable"],
        limit=15,
    )
    no_safe_payload = services.browse_payload(
        owner_user_id="owner-1",
        tailoring_state=["no_safe_rewrites"],
        limit=15,
    )
    ready_payload = services.browse_payload(
        owner_user_id="owner-1",
        tailoring_state=["ready"],
        limit=15,
    )

    assert [row["job_doc_id"] for row in unavailable_payload["rows"]] == ["job-no-artifact"]
    assert [row["job_doc_id"] for row in no_safe_payload["rows"]] == ["job-direction-only"]
    assert [row["job_doc_id"] for row in ready_payload["rows"]] == ["job-ready"]
    assert no_safe_payload["rows"][0]["tailoring_workspace_state"] == "no_safe_rewrites"
    assert no_safe_payload["rows"][0]["tailoring_actionable_replacement_count"] == 0
    assert ready_payload["rows"][0]["tailoring_workspace_state"] == "ready"
    assert ready_payload["rows"][0]["tailoring_actionable_replacement_count"] == 1


def test_actual_browse_route_classifies_runtime_tailoring_states_after_enrichment(
    monkeypatch, tmp_path
):
    output_dir = tmp_path / "pipeline_runs" / "owner-1" / "run-1" / "application_planning"
    empty_tailoring_artifact = _write_tailoring_artifact(output_dir, suggestions=False)
    ready_artifact = _write_tailoring_artifact(output_dir / "ready", suggestions=True)
    llm_dir = output_dir / "job_packets"
    llm_dir.mkdir(parents=True, exist_ok=True)
    direction_only_llm_artifact = llm_dir / "direction_only__tailoring_llm.json"
    direction_only_llm_artifact.write_text(
        json.dumps(
            {
                "parse_ok": True,
                "parsed": {
                    "rewrite_directions": [
                        {
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
                },
            }
        ),
        encoding="utf-8",
    )

    def rel(path: Path) -> str:
        return path.relative_to(output_dir).as_posix()

    manifest_path = output_dir / "job_packet_manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "\n".join(
            [
                "queue_rank,job_doc_id,job_company,job_title,packet_status,llm_tailoring_status,packet_json,tailoring_json,tailoring_md,tailoring_llm_json",
                "1,job-no-artifact,No Artifact Co,Pending Variant,pending_variant_selection,,,,,",
                (
                    "2,job-direction-only,Direction Co,Direction Only,generated,generated,"
                    f"job_packets/direction.json,{rel(empty_tailoring_artifact)},"
                    f"job_packets/direction.md,{rel(direction_only_llm_artifact)}"
                ),
                (
                    "3,job-ready,Ready Co,Ready Role,generated,generated,"
                    f"ready/job_packets/ready.json,{rel(ready_artifact)},"
                    "ready/job_packets/ready.md,"
                ),
            ]
        ),
        encoding="utf-8",
    )

    def fake_runs_payload(**kwargs):
        return {
            "rows": [
                {
                    "run_id": "run-1",
                    "status": "succeeded",
                    "status_json": {
                        "config": {
                            "storage_mode": "run_scoped_scratch",
                            "job_corpus_path": str(output_dir / "current_run_job_corpus.jsonl"),
                            "launch_config_path": str(output_dir / "live_pipeline_launch_config.json"),
                            "status_path": str(output_dir / "live_pipeline_status.json"),
                            "log_path": str(output_dir / "live_pipeline_run.log"),
                        }
                    },
                }
            ]
        }

    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-1")
    monkeypatch.setattr(services, "get_user_pipeline_runs_postgres_payload", fake_runs_payload)
    monkeypatch.setattr(services._job_app(), "_overlay_operator_decisions", lambda rows: rows)
    monkeypatch.setattr(services, "_overlay_application_actions", lambda rows, owner_user_id="": rows)
    monkeypatch.setattr(services, "_exclude_applied_rows", lambda rows: rows)
    client = TestClient(api.app)

    no_filter_payload = client.get("/browse", params={"limit": 15, "page": 1}).json()
    state_by_job = {
        row["job_doc_id"]: row["tailoring_workspace_state"]
        for row in no_filter_payload["rows"]
    }
    assert state_by_job["job-no-artifact"] == "unavailable"
    assert state_by_job["job-direction-only"] == "no_safe_rewrites"
    assert state_by_job["job-ready"] == "ready"

    no_safe_payload = client.get(
        "/browse",
        params={"tailoring_state": "no_safe_rewrites", "limit": 15, "page": 1},
    ).json()
    unavailable_payload = client.get(
        "/browse",
        params={"tailoring_state": "unavailable", "limit": 15, "page": 1},
    ).json()
    ready_payload = client.get(
        "/browse",
        params={"tailoring_state": "ready", "limit": 15, "page": 1},
    ).json()

    assert [row["job_doc_id"] for row in no_safe_payload["rows"]] == ["job-direction-only"]
    assert no_safe_payload["rows"][0]["tailoring_workspace_state"] == "no_safe_rewrites"
    assert no_safe_payload["rows"][0]["tailoring_actionable_replacement_count"] == 0

    assert [row["job_doc_id"] for row in unavailable_payload["rows"]] == ["job-no-artifact"]
    assert unavailable_payload["total_count"] == 1
    assert unavailable_payload["total_count"] != no_filter_payload["total_count"]

    assert [row["job_doc_id"] for row in ready_payload["rows"]] == ["job-ready"]
    assert ready_payload["rows"][0]["tailoring_workspace_state"] == "ready"
    assert ready_payload["rows"][0]["tailoring_actionable_replacement_count"] == 1


def test_actual_browse_route_resolves_repo_relative_run_scoped_manifest_paths(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    output_dir = Path("tmp/pipeline_runs/owner-1/run-1/application_planning")
    empty_tailoring_artifact = _write_tailoring_artifact(output_dir, suggestions=False)
    ready_artifact = _write_tailoring_artifact(output_dir / "ready", suggestions=True)
    llm_dir = output_dir / "job_packets"
    llm_dir.mkdir(parents=True, exist_ok=True)
    direction_only_llm_artifact = llm_dir / "direction_only__tailoring_llm.json"
    direction_only_llm_artifact.write_text(
        json.dumps(
            {
                "parse_ok": True,
                "parsed": {
                    "rewrite_directions": [
                        "Lead with workflow automation evidence while preserving scope."
                    ],
                },
                "shadow_replacement_candidates": [
                    {
                        "candidate_id": "direction-1",
                        "proposal_status": "direction_only",
                        "rewrite_direction": "Lead with workflow automation evidence.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = output_dir / "job_packet_manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "\n".join(
            [
                "queue_rank,job_doc_id,job_company,job_title,packet_status,llm_tailoring_status,packet_json,tailoring_json,tailoring_md,tailoring_llm_json",
                "1,job-no-artifact,No Artifact Co,Pending Variant,pending_variant_selection,,,,,",
                (
                    "2,job-direction-only,Direction Co,Direction Only,generated,generated,"
                    f"{output_dir / 'job_packets' / 'direction.json'},"
                    f"{empty_tailoring_artifact},"
                    f"{output_dir / 'job_packets' / 'direction.md'},"
                    f"{direction_only_llm_artifact}"
                ),
                (
                    "3,job-ready,Ready Co,Ready Role,generated,generated,"
                    f"{output_dir / 'ready' / 'job_packets' / 'ready.json'},"
                    f"{ready_artifact},"
                    f"{output_dir / 'ready' / 'job_packets' / 'ready.md'},"
                ),
            ]
        ),
        encoding="utf-8",
    )

    def fake_runs_payload(**kwargs):
        return {
            "rows": [
                {
                    "run_id": "run-1",
                    "status": "succeeded",
                    "status_json": {
                        "config": {
                            "storage_mode": "run_scoped_scratch",
                            "job_corpus_path": str(output_dir / "current_run_job_corpus.jsonl"),
                            "launch_config_path": str(output_dir / "live_pipeline_launch_config.json"),
                            "status_path": str(output_dir / "live_pipeline_status.json"),
                            "log_path": str(output_dir / "live_pipeline_run.log"),
                        }
                    },
                }
            ]
        }

    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-1")
    monkeypatch.setattr(services, "get_user_pipeline_runs_postgres_payload", fake_runs_payload)
    monkeypatch.setattr(services._job_app(), "_overlay_operator_decisions", lambda rows: rows)
    monkeypatch.setattr(services, "_overlay_application_actions", lambda rows, owner_user_id="": rows)
    monkeypatch.setattr(services, "_exclude_applied_rows", lambda rows: rows)
    client = TestClient(api.app)

    no_filter_payload = client.get("/browse", params={"limit": 15, "page": 1}).json()
    state_by_job = {
        row["job_doc_id"]: row["tailoring_workspace_state"]
        for row in no_filter_payload["rows"]
    }

    assert state_by_job["job-no-artifact"] == "unavailable"
    assert state_by_job["job-direction-only"] == "no_safe_rewrites"
    assert state_by_job["job-ready"] == "ready"

    no_safe_payload = client.get(
        "/browse",
        params={"tailoring_state": "no_safe_rewrites", "limit": 15, "page": 1},
    ).json()
    unavailable_payload = client.get(
        "/browse",
        params={"tailoring_state": "unavailable", "limit": 15, "page": 1},
    ).json()
    ready_payload = client.get(
        "/browse",
        params={"tailoring_state": "ready", "limit": 15, "page": 1},
    ).json()

    assert [row["job_doc_id"] for row in no_safe_payload["rows"]] == ["job-direction-only"]
    assert no_safe_payload["rows"][0]["tailoring_workspace_state"] == "no_safe_rewrites"
    assert no_safe_payload["rows"][0]["tailoring_actionable_replacement_count"] == 0

    assert [row["job_doc_id"] for row in unavailable_payload["rows"]] == ["job-no-artifact"]
    assert unavailable_payload["total_count"] == 1
    assert unavailable_payload["total_count"] != no_filter_payload["total_count"]

    assert [row["job_doc_id"] for row in ready_payload["rows"]] == ["job-ready"]
    assert ready_payload["rows"][0]["tailoring_workspace_state"] == "ready"
    assert ready_payload["rows"][0]["tailoring_actionable_replacement_count"] == 1


def test_source_resume_preview_uses_resume_resolver_not_planning_artifact_guard(
    monkeypatch,
    tmp_path,
    synthetic_resume_dir,
):
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


def test_rendered_workspace_preview_applies_source_resume_linkedin_and_github(
    monkeypatch,
    tmp_path,
    synthetic_resume_dir,
):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_tailoring_artifact(output_dir)
    artifact_key = artifact_path.relative_to(output_dir).as_posix()
    source_resume_path = tmp_path / "profile_resume_library" / "resume.pdf"
    source_resume_path.parent.mkdir(parents=True)
    source_resume_path.write_bytes(b"%PDF-1.4\n%test\n")

    monkeypatch.setattr(
        services,
        "planning_resume_preview_path",
        lambda resume_name, *, owner_user_id="": source_resume_path,
    )

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
                                "text": "Alex Rivera",
                                "alignment": "center",
                                "gap_before": 0,
                                "left_indent_pt": 0,
                                "is_bullet": False,
                            },
                            {
                                "text": "Harrison, NJ | +1 (555) 123-4567 | alex@example.com | linkedin.com/in/alexrivera | github.com/alexrivera",
                                "alignment": "center",
                                "gap_before": 1,
                                "left_indent_pt": 0,
                                "is_bullet": False,
                            },
                            {
                                "text": "Built Python services.",
                                "alignment": "left",
                                "gap_before": 8,
                                "left_indent_pt": 0,
                                "is_bullet": True,
                            },
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

    rows = payload["pages"][0]["rows"]
    contact_rows = [row for row in rows if "LinkedIn" in row.get("text", "")]

    assert contact_rows
    contact = contact_rows[0]
    assert "GitHub" in contact["text"]
    assert {"label": "LinkedIn", "uri": "https://linkedin.com/in/alexrivera"} in contact["link_items"]
    assert {"label": "GitHub", "uri": "https://github.com/alexrivera"} in contact["link_items"]


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
    # Item 4C-R2: /planning-artifact is now owner-scoped, so the run must live
    # under the authenticated owner's server-derived pipeline-runs root.
    monkeypatch.setattr(services, "DEFAULT_PIPELINE_SCRATCH_DIR", tmp_path)
    output_dir = tmp_path / "owner-a" / "run-scoped" / "application_planning"
    packet_path = _write_base_packet(output_dir)
    missing_tailoring_key = (
        packet_path.with_name("acme__platform_engineer__resume__tailoring.json")
        .relative_to(output_dir)
        .as_posix()
    )
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_require_auth_owner_user_id", lambda _request: "owner-a")
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


def test_planning_table_workspace_button_allows_review_only_no_safe_rewrite_artifacts():
    planning_js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    planning_filter_source = Path("frontend/executive-kpi/src/PlanningWorklist.tsx").read_text(encoding="utf-8")
    blocked_source = planning_js.split("function getWorkspaceBlockedReason(row)", 1)[1].split(
        "function buildTailoringButtonHtml", 1
    )[0]

    assert "function getWorkspaceBlockedReason(row)" in planning_js
    assert "No safe bullet-level rewrites were found for this row." in planning_js
    assert 'workspaceState === "no_safe_rewrites"' in planning_js
    assert '{ value: "no_safe_rewrites", label: "No safe rewrites"' in planning_filter_source
    assert "PLANNING_TAILORING_OPTIONS" in planning_filter_source
    assert 'appendMultiValueParams(params, "tailoring_state", tailoringStates)' in planning_js
    assert 'params.getAll("tailoring_state")' in planning_js
    assert "LLM tailoring generation is off for this row." in planning_js
    assert "data-workspace-blocked-reason" in planning_js
    assert 'const canGenerateSuggestions = !hasArtifacts && canGenerateSuggestionsForRow(row);' in planning_js
    assert 'disabled: !((hasArtifacts && !blockedReason) || canGenerateSuggestions)' in planning_js
    assert 'const disabledAttr = actionState.disabled ? "disabled" : "";' in planning_js
    assert 'showAppError("Workspace unavailable", new Error(blockedReason))' not in planning_js
    assert "actionableCount <= 0" in planning_js
    assert '"review"' in planning_js
    assert '"unavailable"' in planning_js
    assert '"disabled"' in planning_js
    # Workspace-gating precedence fix: authoritative usable workspace state
    # (no_safe_rewrites or ready) is now checked, and returns openable,
    # BEFORE the llm failed/unreadable check - not after it. See
    # test_no_safe_rewrites_open_workspace_enabled_regardless_of_llm_status.
    assert 'if (workspaceState === "no_safe_rewrites" || workspaceState === "ready")' in blocked_source
    assert (
        'if (workspaceState === "no_safe_rewrites" || workspaceState === "ready") {\n    return "";'
        in blocked_source
    )
    assert blocked_source.index(
        'if (workspaceState === "no_safe_rewrites" || workspaceState === "ready")'
    ) < blocked_source.index('["failed", "unreadable"].includes(llmStatus)')
    assert '"no_safe_rewrites"].includes(workspaceState)' not in blocked_source
    assert "Review-only guidance is available. No app-ready replacement is available yet." in planning_js
    no_safe_render_source = planning_js.split('workspaceState === "no_safe_rewrites"', 2)[2].split(
        "} else if (hasArtifacts)",
        1,
    )[0]
    assert 'stateClass = "planning-tailoring-btn--review";' in no_safe_render_source
    assert "data-workspace-blocked-reason" in planning_js


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


# ---------------------------------------------------------------------------
# Retire the user-facing Tailoring state "Review".
#
# "review" is folded into "no_safe_rewrites" for filter matching and legacy
# incoming filter values, but the row's own tailoring_workspace_state value
# (which drives getWorkspaceBlockedReason()/resolvePlanningWorklistAction()
# in planning.js) is left byte-for-byte unchanged so Open Workspace
# enable/disable behavior is not affected by retiring the label.
# ---------------------------------------------------------------------------


def test_legacy_incoming_filter_value_review_normalizes_to_no_safe_rewrites():
    assert services._normalize_tailoring_state_filter_values(["review"]) == ["no_safe_rewrites"]
    assert services._normalize_tailoring_state_filter_values("review") == ["no_safe_rewrites"]
    # Deduplicates against an explicit modern value rather than producing both.
    assert services._normalize_tailoring_state_filter_values(["review", "no_safe_rewrites"]) == [
        "no_safe_rewrites"
    ]


def test_normalize_tailoring_state_filter_values_no_longer_exposes_review_standalone():
    # "review" must never survive normalization as its own distinct token;
    # anything reaching downstream filter matching is one of exactly three
    # modern states.
    for raw in (["review"], ["review", "ready"], ["review", "unavailable"]):
        for value in services._normalize_tailoring_state_filter_values(raw):
            assert value in {"ready", "unavailable", "no_safe_rewrites"}


def test_legacy_review_row_matches_no_safe_rewrites_filter_without_changing_workspace_state(
    monkeypatch,
):
    # A row whose workspace state resolves to legacy "review" (modern
    # derivation never produces this; this proves the historical-compat path
    # some artifact could still reach).
    monkeypatch.setattr(
        services,
        "_tailoring_workspace_button_state",
        lambda row, output_dir=services.DEFAULT_OUTPUT_DIR: {
            "tailoring_ready_replacement_count": 0,
            "tailoring_actionable_replacement_count": 0,
            "tailoring_review_replacement_count": 2,
            "tailoring_has_ready_replacements": False,
            "tailoring_has_review_guidance": True,
            "tailoring_workspace_state": "review",
        },
    )

    matches_no_safe, row_no_safe = services._row_matches_tailoring_state_filter(
        {"job_doc_id": "job-legacy-review"},
        ["no_safe_rewrites"],
        output_dir=services.DEFAULT_OUTPUT_DIR,
    )
    matches_unavailable, _ = services._row_matches_tailoring_state_filter(
        {"job_doc_id": "job-legacy-review"},
        ["unavailable"],
        output_dir=services.DEFAULT_OUTPUT_DIR,
    )
    matches_ready, _ = services._row_matches_tailoring_state_filter(
        {"job_doc_id": "job-legacy-review"},
        ["ready"],
        output_dir=services.DEFAULT_OUTPUT_DIR,
    )

    # Step 4: selecting "No safe rewrites" includes the legacy review row.
    assert matches_no_safe is True
    assert matches_unavailable is False
    assert matches_ready is False

    # Critical: the row's own tailoring_workspace_state is NOT rewritten to
    # "no_safe_rewrites". getWorkspaceBlockedReason()/
    # resolvePlanningWorklistAction() in planning.js must keep seeing exactly
    # what they saw before this task, so Open Workspace behavior for legacy
    # review rows is unaffected by retiring the label.
    assert row_no_safe["tailoring_workspace_state"] == "review"


def test_modern_no_safe_rewrites_row_still_matches_no_safe_rewrites_filter(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_direction_only_tailoring_artifact(output_dir)

    matches, row = services._row_matches_tailoring_state_filter(
        {"job_doc_id": "job-modern-no-safe", "tailoring_json": str(artifact_path)},
        ["no_safe_rewrites"],
        output_dir=output_dir,
    )

    assert matches is True
    assert row["tailoring_workspace_state"] == "no_safe_rewrites"


def test_ready_and_unavailable_rows_unaffected_by_review_retirement(tmp_path):
    output_dir = tmp_path / "run-scoped" / "application_planning"
    ready_artifact = _write_tailoring_artifact(output_dir, suggestions=True)

    ready_matches, ready_row = services._row_matches_tailoring_state_filter(
        {"job_doc_id": "job-ready", "tailoring_json": str(ready_artifact)},
        ["ready"],
        output_dir=output_dir,
    )
    unavailable_matches, unavailable_row = services._row_matches_tailoring_state_filter(
        {"job_doc_id": "job-no-artifact"},
        ["unavailable"],
        output_dir=output_dir,
    )

    assert ready_matches is True
    assert ready_row["tailoring_workspace_state"] == "ready"
    assert unavailable_matches is True
    assert unavailable_row["tailoring_workspace_state"] == "unavailable"


def test_legacy_review_row_workspace_button_availability_is_unchanged_by_retirement(
    monkeypatch,
):
    """Steps 7.8-7.10: retiring the Review label must not flip a legacy
    review row's Open Workspace availability in either direction.

    planning.js's getWorkspaceBlockedReason() treats a raw "review" state as
    blocked (it is not in the early "no_safe_rewrites" allow-branch, and is
    explicitly listed among the blocked states); resolvePlanningWorklistAction()
    separately renders it with the review-toned button class. This proves the
    backend still hands planning.js that exact same raw "review" value after
    this task, so both behaviors are preserved unmodified.
    """
    monkeypatch.setattr(
        services,
        "_tailoring_workspace_button_state",
        lambda row, output_dir=services.DEFAULT_OUTPUT_DIR: {
            "tailoring_ready_replacement_count": 0,
            "tailoring_actionable_replacement_count": 0,
            "tailoring_review_replacement_count": 1,
            "tailoring_has_ready_replacements": False,
            "tailoring_has_review_guidance": True,
            "tailoring_workspace_state": "review",
        },
    )

    planning_js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    blocked_source = planning_js.split("function getWorkspaceBlockedReason(row)", 1)[1].split(
        "function resolvePlanningWorklistAction", 1
    )[0]
    # The exact legacy-compat branch that decides blocked vs. openable for a
    # raw "review" row is unchanged by this task.
    assert '["empty", "unavailable", "review"].includes(workspaceState)' in blocked_source

    _, row = services._row_matches_tailoring_state_filter(
        {"job_doc_id": "job-legacy-review-button"},
        [],
        output_dir=services.DEFAULT_OUTPUT_DIR,
    )
    # Same raw value planning.js's getWorkspaceBlockedReason() branches on
    # above, unmodified by review retirement.
    assert row["tailoring_workspace_state"] == "review"


def test_no_review_filter_option_remains_in_react_tailoring_filter():
    planning_filter_source = Path("frontend/executive-kpi/src/PlanningWorklist.tsx").read_text(
        encoding="utf-8"
    )
    options_block = planning_filter_source[
        planning_filter_source.index("const PLANNING_TAILORING_OPTIONS") :
        planning_filter_source.index("const WIDTH_BOUNDS")
    ]

    assert '{ value: "ready", label: "Ready"' in options_block
    assert '{ value: "no_safe_rewrites", label: "No safe rewrites"' in options_block
    assert '{ value: "unavailable", label: "Unavailable"' in options_block
    assert '"review"' not in options_block
    assert "Review" not in options_block


def test_legacy_review_display_label_presented_as_no_safe_rewrites():
    planning_filter_source = Path("frontend/executive-kpi/src/PlanningWorklist.tsx").read_text(
        encoding="utf-8"
    )
    assert "function tailoringStatusLabel" in planning_filter_source
    assert 'tailoringStatusLabel(row.original.tailoring_workspace_state' in planning_filter_source
    # The row's raw tailoring_workspace_state field is not mutated by the
    # presentation mapping; __planning_action (Open Workspace availability)
    # is computed upstream in planning.js from that same untouched field.
    label_fn = planning_filter_source[
        planning_filter_source.index("function tailoringStatusLabel") :
        planning_filter_source.index("function tailoringStatusLabel") + 300
    ]
    assert '"review"' in label_fn.lower() or "review" in label_fn.lower()
    assert "No safe rewrites" in label_fn


def test_browse_payload_legacy_review_filter_returns_the_no_safe_rewrites_rows(
    monkeypatch, tmp_path
):
    """End-to-end proof for Step 6: a saved/old ?tailoring_state=review query
    param degrades into the modern "No safe rewrites" filter rather than
    becoming invalid or silently returning nothing.
    """
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

    legacy_review_payload = services.browse_payload(
        output_dir=output_dir,
        tailoring_state=["review"],
        limit=15,
    )
    no_safe_payload = services.browse_payload(
        output_dir=output_dir,
        tailoring_state=["no_safe_rewrites"],
        limit=15,
    )

    legacy_ids = [row["job_doc_id"] for row in legacy_review_payload["rows"]]
    modern_ids = [row["job_doc_id"] for row in no_safe_payload["rows"]]
    assert legacy_ids == ["job-direction-only"]
    assert legacy_ids == modern_ids
    assert legacy_review_payload["filters"]["tailoring_state"] == ["no_safe_rewrites"]


# ---------------------------------------------------------------------------
# Workspace gating precedence: an authoritative usable workspace state
# (no_safe_rewrites / ready) must not be blocked merely because the separate,
# optional --use-llm refinement pass failed/was unreadable. A row with no
# usable evidence at all (empty/unavailable, or legacy "review") stays
# blocked by a failed/unreadable LLM pass exactly as before.
#
# These tests execute the real planning.js functions in Node (not a
# reimplementation) via the file's existing _function_source extraction
# helper, on row shapes that mirror what services.browse_payload /
# _row_matches_tailoring_state_filter actually return.
# ---------------------------------------------------------------------------


def _evaluate_workspace_blocked_reason_cases():
    source = _source()
    function_names = [
        "hasTailoringWorkspaceArtifacts",
        "getWorkspaceBlockedReason",
        "resolvePlanningWorklistAction",
    ]
    functions = "\n\n".join(_function_source(source, name) for name in function_names)
    script = f"""
function canGenerateSuggestionsForRow(row) {{ return false; }}
{functions}
const cases = {{
  no_safe_rewrites_llm_generated: {{
    tailoring_workspace_state: "no_safe_rewrites",
    tailoring_actionable_replacement_count: 0,
    tailoring_review_replacement_count: 2,
    llm_tailoring_status: "generated",
    tailoring_json: "job_packets/a__tailoring.json",
  }},
  no_safe_rewrites_llm_failed: {{
    tailoring_workspace_state: "no_safe_rewrites",
    tailoring_actionable_replacement_count: 0,
    tailoring_review_replacement_count: 2,
    llm_tailoring_status: "failed",
    llm_error_type: "llm_parse_failed",
    tailoring_json: "job_packets/b__tailoring.json",
    tailoring_llm_json: "job_packets/b__tailoring_llm.json",
  }},
  no_safe_rewrites_llm_unreadable: {{
    tailoring_workspace_state: "no_safe_rewrites",
    tailoring_actionable_replacement_count: 0,
    tailoring_review_replacement_count: 1,
    llm_tailoring_status: "unreadable",
    llm_error_type: "unreadable_json",
    tailoring_json: "job_packets/c__tailoring.json",
    tailoring_llm_json: "job_packets/c__tailoring_llm.json",
  }},
  ready_llm_failed: {{
    tailoring_workspace_state: "ready",
    tailoring_actionable_replacement_count: 1,
    tailoring_review_replacement_count: 0,
    llm_tailoring_status: "failed",
    llm_error_type: "llm_parse_failed",
    tailoring_json: "job_packets/d__tailoring.json",
    tailoring_llm_json: "job_packets/d__tailoring_llm.json",
  }},
  ready_llm_generated: {{
    tailoring_workspace_state: "ready",
    tailoring_actionable_replacement_count: 2,
    tailoring_review_replacement_count: 0,
    llm_tailoring_status: "generated",
    tailoring_json: "job_packets/e__tailoring.json",
  }},
  unavailable_llm_failed: {{
    tailoring_workspace_state: "unavailable",
    tailoring_actionable_replacement_count: 0,
    tailoring_review_replacement_count: 0,
    llm_tailoring_status: "failed",
    llm_error_type: "llm_parse_failed",
    tailoring_json: "job_packets/f__tailoring.json",
    tailoring_llm_json: "job_packets/f__tailoring_llm.json",
  }},
  empty_llm_failed: {{
    tailoring_workspace_state: "empty",
    tailoring_actionable_replacement_count: 0,
    tailoring_review_replacement_count: 0,
    llm_tailoring_status: "failed",
    llm_error_type: "llm_parse_failed",
    tailoring_json: "job_packets/g__tailoring.json",
    tailoring_llm_json: "job_packets/g__tailoring_llm.json",
  }},
  legacy_review_llm_failed: {{
    tailoring_workspace_state: "review",
    tailoring_actionable_replacement_count: 0,
    tailoring_review_replacement_count: 2,
    llm_tailoring_status: "failed",
    llm_error_type: "llm_parse_failed",
    tailoring_json: "job_packets/h__tailoring.json",
    tailoring_llm_json: "job_packets/h__tailoring_llm.json",
  }},
  legacy_review_llm_generated: {{
    tailoring_workspace_state: "review",
    tailoring_actionable_replacement_count: 0,
    tailoring_review_replacement_count: 2,
    llm_tailoring_status: "generated",
    tailoring_json: "job_packets/i__tailoring.json",
  }},
  llm_disabled_off_no_safe_rewrites: {{
    tailoring_workspace_state: "no_safe_rewrites",
    tailoring_actionable_replacement_count: 0,
    tailoring_review_replacement_count: 1,
    llm_tailoring_status: "disabled",
    tailoring_json: "job_packets/j__tailoring.json",
  }},
}};
const results = {{}};
for (const [key, row] of Object.entries(cases)) {{
  const blockedReason = getWorkspaceBlockedReason(row);
  const action = resolvePlanningWorklistAction({{ ...row, hasArtifacts: undefined }});
  results[key] = {{
    blockedReason,
    disabled: action.disabled,
    title: action.title,
    kind: action.kind,
  }};
}}
console.log(JSON.stringify(results));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_no_safe_rewrites_open_workspace_enabled_regardless_of_llm_status():
    results = _evaluate_workspace_blocked_reason_cases()

    for key in (
        "no_safe_rewrites_llm_generated",
        "no_safe_rewrites_llm_failed",
        "no_safe_rewrites_llm_unreadable",
    ):
        assert results[key]["blockedReason"] == "", key
        assert results[key]["disabled"] is False, key
        assert results[key]["kind"] == "open_workspace", key

    # Task 2/3: LLM failure must not produce the misleading blocking message
    # for a usable no_safe_rewrites row.
    assert "AI tailoring unavailable" not in results["no_safe_rewrites_llm_failed"]["title"]
    assert "AI tailoring unavailable" not in results["no_safe_rewrites_llm_unreadable"]["title"]


def test_ready_open_workspace_enabled_regardless_of_llm_status():
    results = _evaluate_workspace_blocked_reason_cases()

    for key in ("ready_llm_failed", "ready_llm_generated"):
        assert results[key]["blockedReason"] == "", key
        assert results[key]["disabled"] is False, key
        assert results[key]["kind"] == "open_workspace", key
    assert "AI tailoring unavailable" not in results["ready_llm_failed"]["title"]


def test_genuinely_unusable_rows_remain_blocked_by_failed_llm():
    results = _evaluate_workspace_blocked_reason_cases()

    for key in ("unavailable_llm_failed", "empty_llm_failed"):
        assert results[key]["blockedReason"] != "", key
        assert results[key]["disabled"] is True, key
        assert results[key]["kind"] != "open_workspace", key

    # A genuinely unusable row with a failed LLM pass still shows the
    # existing (correct, non-misleading) unavailable message.
    assert results["unavailable_llm_failed"]["blockedReason"] == (
        "AI tailoring unavailable. No suggestions were produced for this row."
    )
    assert results["empty_llm_failed"]["blockedReason"] == (
        "AI tailoring unavailable. No suggestions were produced for this row."
    )


def test_legacy_review_workspace_gating_is_pinned_exactly_as_after_retirement():
    results = _evaluate_workspace_blocked_reason_cases()

    # Unchanged by this task: legacy "review" stays blocked either way, per
    # the Review-retirement task's own pinned behavior.
    assert results["legacy_review_llm_failed"]["disabled"] is True
    assert results["legacy_review_llm_generated"]["disabled"] is True
    assert results["legacy_review_llm_failed"]["blockedReason"] == (
        "AI tailoring unavailable. No suggestions were produced for this row."
    )
    assert results["legacy_review_llm_generated"]["blockedReason"] == (
        "No safe bullet-level rewrites were found for this row."
    )


def test_llm_disabled_off_precedence_is_unaffected_by_this_task():
    results = _evaluate_workspace_blocked_reason_cases()

    # Out of scope for this task: LLM generation being off is a distinct,
    # unmodified branch, still checked first.
    assert results["llm_disabled_off_no_safe_rewrites"]["disabled"] is True
    assert results["llm_disabled_off_no_safe_rewrites"]["blockedReason"] == (
        "LLM tailoring generation is off for this row."
    )


def test_no_rejected_llm_rewrite_becomes_actionable_from_the_gating_fix():
    # The gating fix only changes whether the workspace OPENS; it must not
    # change the workspace state itself or promote review-only guidance into
    # an actionable/ready suggestion.
    results = _evaluate_workspace_blocked_reason_cases()
    row = results["no_safe_rewrites_llm_failed"]
    assert row["kind"] == "open_workspace"
    # kind is not "generate_suggestions" or a ready state relabeling; the
    # underlying tailoring_workspace_state stays no_safe_rewrites (proven by
    # the title text staying review-only, not an actionable-count message).
    assert row["title"] == "Review-only guidance is available. No app-ready replacement is available yet."


def test_formerly_disabled_live_rows_now_resolve_open_workspace(monkeypatch, tmp_path):
    """End-to-end proof using the real read-model shape: a row whose
    deterministic artifact has direction-only/anchor evidence (no actionable
    replacements) and whose llm_tailoring_status is "failed" now enriches to
    an openable no_safe_rewrites row, exactly mirroring the six formerly
    disabled live rows found during forensic analysis.
    """
    output_dir = tmp_path / "run-scoped" / "application_planning"
    artifact_path = _write_direction_only_tailoring_artifact(output_dir)

    matches, row = services._row_matches_tailoring_state_filter(
        {
            "job_doc_id": "job-formerly-disabled",
            "tailoring_json": str(artifact_path),
            "llm_tailoring_status": "failed",
            "llm_error_type": "llm_parse_failed",
        },
        ["no_safe_rewrites"],
        output_dir=output_dir,
    )

    assert matches is True
    assert row["tailoring_workspace_state"] == "no_safe_rewrites"
    assert row["llm_tailoring_status"] == "failed"

    source = _source()
    functions = "\n\n".join(
        _function_source(source, name)
        for name in (
            "hasTailoringWorkspaceArtifacts",
            "getWorkspaceBlockedReason",
            "resolvePlanningWorklistAction",
        )
    )
    script = f"""
function canGenerateSuggestionsForRow(row) {{ return false; }}
{functions}
const row = {json.dumps({
    "tailoring_workspace_state": row["tailoring_workspace_state"],
    "tailoring_actionable_replacement_count": row["tailoring_actionable_replacement_count"],
    "tailoring_review_replacement_count": row["tailoring_review_replacement_count"],
    "llm_tailoring_status": row["llm_tailoring_status"],
    "tailoring_json": "job_packets/formerly_disabled__tailoring.json",
})};
console.log(JSON.stringify({{
  blockedReason: getWorkspaceBlockedReason(row),
  disabled: resolvePlanningWorklistAction(row).disabled,
}}));
"""
    completed = subprocess.run(["node", "-e", script], text=True, capture_output=True, check=True)
    result = json.loads(completed.stdout)
    assert result["blockedReason"] == ""
    assert result["disabled"] is False
