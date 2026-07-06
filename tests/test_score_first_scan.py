import sys
import tempfile
import types
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))

from src.app.services import (
    _build_tailoring_scan_issue_contract,
    _build_workspace_draft_fragments_contract,
    _build_workspace_score_preview_contract,
    _extract_resume_personal_details,
    load_tailoring_workspace_draft_payload,
    save_tailoring_workspace_draft_payload,
    create_saved_scan_payload,
    extract_scan_resume_upload_text_payload,
    scan_workspace_job_context_payload,
    _scan_phrase_parse_options_payload,
    _scan_phrase_signal_terms,
    _scan_phrase_structured_output_contract,
    _scan_phrase_validate_llm_options,
)
from src.app.planning_ui import scan_workspace
from src.app.profile_ui import saved_scans_page
from src.storage.saved_scans.store import (
    saved_scan_db_row,
    saved_scans_contract_health_payload,
)
from src.tailoring.replacement_selector import build_final_replacement_plan
from src.tailoring import rendering as tailoring_rendering
from src.tailoring import llm as tailoring_llm
from src.tailoring.score_utils import score_delta_to_points, score_to_points


def _candidate(candidate_id, *, bullet_id="bullet_1", delta=0.0, llm=False, patch_text="patched bullet"):
    return {
        "candidate_id": candidate_id,
        "source_bullet_id": bullet_id,
        "operation_type": "rewrite",
        "proposal_status": "patch_ready",
        "patch_text": patch_text,
        "original_text": "original bullet",
        "current_evidence": "original bullet",
        "rewrite_instruction": "Improve supported JD signal placement.",
        "materiality_validation_status": "material_candidate",
        "projected_overall_delta": delta,
        "projected_dimension_deltas": {"required_skills_alignment": delta},
        "confidence": "high",
        "llm_refinement_used": llm,
        "unsupported_risk_signals": [],
        "adjacent_risk_signals": [],
        "likely_impacted_dimensions": ["required_skills_alignment"],
    }


def _resume_evidence(*, skills=None, bullets=None, raw_text=None, education_entries=None):
    default_raw_text = "\n".join(["Skills", *(skills or []), *(bullets or [])])
    return SimpleNamespace(
        skills=list(skills or []),
        tools=[],
        methods=[],
        workflows=[],
        tooling_signals=[],
        analytics_ml_signals=[],
        experimentation_signals=[],
        domain_signals=[],
        quantified_bullets=[],
        experience_entries=[SimpleNamespace(bullets=list(bullets or []))],
        project_entries=[],
        education_entries=list(education_entries or []),
        document=SimpleNamespace(raw_text=raw_text if raw_text is not None else default_raw_text),
    )


def test_score_point_normalization_handles_normalized_and_point_values():
    assert score_to_points(0.42) == 42
    assert score_to_points(42) == 42
    assert score_delta_to_points(0.03) == 3
    assert score_delta_to_points(-0.02) == -2


def test_workspace_score_preview_contract_exposes_points_and_changed_bullets():
    preview = _build_workspace_score_preview_contract(
        preview_status="workspace_draft_rescored",
        preview_note="rescored",
        original_score=0.71,
        projected_score=0.78,
        projected_delta=0.07,
        selected_candidate_ids=["candidate_1"],
        manual_bullet_edits={"candidate:candidate_2": "manual bullet"},
        patch_specs=[
            {"bullet_key": "candidate:candidate_1"},
            {"bullet_key": "candidate:candidate_2"},
        ],
        dimension_deltas={"required_skills_alignment": 0.04},
    )

    assert preview["version"] == "workspace_score_preview_v1"
    assert preview["original_score_points"] == 71
    assert preview["projected_score_points"] == 78
    assert preview["delta_points"] == 7
    assert preview["dimension_delta_points"]["required_skills_alignment"] == 4
    assert preview["changed_bullet_keys"] == [
        "candidate:candidate_1",
        "candidate:candidate_2",
    ]
    assert preview["requires_full_preview_reload"] is False


def test_workspace_draft_fragments_contract_returns_patchable_bullets():
    fragments = _build_workspace_draft_fragments_contract(
        preview_status="workspace_draft_rescored",
        preview_note="rescored",
        patch_specs=[
            {
                "bullet_key": "candidate:candidate_1",
                "candidate_id": "candidate_1",
                "source_bullet_id": "bullet_1",
                "source_raw_text": "old bullet",
                "patch_text": "new bullet",
                "patch_source": "selected_patch",
            }
        ],
    )

    assert fragments["version"] == "workspace_draft_fragments_v1"
    assert fragments["fragment_count"] == 1
    assert fragments["changed_bullet_keys"] == ["candidate:candidate_1"]
    assert fragments["changed_bullets"][0]["current_text"] == "new bullet"
    assert fragments["requires_full_preview_reload"] is False


def test_scan_phrase_signal_terms_prefers_lead_with_guidance():
    terms = _scan_phrase_signal_terms(
        guidance_text="Lead with sql in this opening clause, then keep the rest truthful.",
        supported_terms=["Python", "SQL"],
    )

    assert terms[0] == "SQL"
    assert "Python" in terms


def test_scan_phrase_validate_llm_options_marks_manual_only():
    options = _scan_phrase_validate_llm_options(
        [
            {
                "text": "Built SQL validation workflows that reduced defects by 20%",
                "reason": "Surfaces SQL earlier.",
                "supported_terms": ["SQL"],
                "risk_flags": [],
            }
        ],
        current="Built validation workflows with SQL that reduced defects by 20%",
        terms=["SQL"],
    )

    assert options[0]["source"] == "llm_guidance_phrase"
    assert options[0]["can_accept_directly"] is False
    assert options[0]["requires_review"] is True


def test_scan_phrase_parse_options_payload_accepts_fenced_json_text():
    rows = _scan_phrase_parse_options_payload(
        '```json\n{"options":[{"text":"Draft","reason":"Clearer","supported_terms":["SQL"],"risk_flags":[]}]}\n```'
    )

    assert rows[0]["text"] == "Draft"


def test_scan_phrase_structured_output_contract_is_strict_schema():
    contract = _scan_phrase_structured_output_contract()

    assert contract["name"] == "scan_phrase_options_v1"
    assert contract["strict"] is True
    assert contract["schema"]["additionalProperties"] is False
    assert contract["schema"]["properties"]["options"]["maxItems"] == 3


def test_saved_scan_contract_normalizes_pasted_text_record():
    row = saved_scan_db_row(
        {
            "scan_timestamp": "2026-05-08T12:00:00+00:00",
            "resume_source": "pasted_text",
            "resume_text": "Built SQL dashboards.",
            "job_company": "Acme",
            "job_title": "Data Analyst",
            "job_description_text": "Need SQL dashboards.",
        }
    )

    assert row["scan_id"]
    assert row["resume_source"] == "pasted_text"
    assert row["scan_status"] == "report_pending"
    assert saved_scans_contract_health_payload()["all_checks_pass"] is True


def test_create_saved_scan_payload_skips_postgres_without_database_url():
    old_database_url = os.environ.pop("DATABASE_URL", None)
    try:
        payload = create_saved_scan_payload(
            company="Acme",
            role="Data Analyst",
            job_url="https://example.com/jobs/data-analyst",
            job_description_text="Need SQL dashboards.",
            resume_text="Built SQL dashboards.",
        )
    finally:
        if old_database_url is not None:
            os.environ["DATABASE_URL"] = old_database_url

    assert payload["scan"]["resume_source"] == "pasted_text"
    assert payload["postgres_write"]["skipped"] == "missing_database_url"


def test_extract_scan_resume_upload_text_accepts_txt_upload():
    payload = extract_scan_resume_upload_text_payload(
        filename="resume.txt",
        content_type="text/plain",
        file_bytes=b"Built SQL dashboards.\\nLed analytics delivery.",
    )

    assert payload["ok"] is True
    assert payload["filename"] == "resume.txt"
    assert "SQL dashboards" in payload["text"]


def test_scan_workspace_job_context_prefills_loaded_job_description():
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "planning"
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / "example__tailoring.json"
        artifact_path.write_text(
            """
{
  "job_snapshot": {
    "company": "Meta",
    "title": "AI Software Engineer",
    "job_url": "https://example.com/jobs/ai",
    "description_text": "Build AI software with Python, distributed systems, and production ML."
  },
  "job": {
    "company": "Fallback",
    "title": "Fallback Role",
    "description": "Fallback description"
  },
  "selection": {"selected_resume": "resume.pdf"}
}
""".strip(),
            encoding="utf-8",
        )

        payload = scan_workspace_job_context_payload(
            output_dir=output_dir,
            tailoring_json_path=str(artifact_path),
        )

    assert payload["company"] == "Meta"
    assert payload["title"] == "AI Software Engineer"
    assert payload["job_url"] == "https://example.com/jobs/ai"
    assert payload["job_description_text"] == (
        "Build AI software with Python, distributed systems, and production ML."
    )

def test_scan_workspace_hides_tailoring_navigation_for_direct_new_scan():
    html = scan_workspace(company="Meta", title="wifi")

    assert "Back to Tailoring" not in html
    assert "Prefer full control? Use Power Edit" not in html
    assert 'data-scan-initial-mode="new_scan"' in html
    assert 'id="scanWorkspaceStartScanBtn"' in html


def test_scan_workspace_keeps_tailoring_navigation_for_tailoring_context():
    html = scan_workspace(
        company="Meta",
        title="AI Software Engineer",
        resume="Sriram_Neelakantan_AI1.pdf",
        tailoring_json="outputs/application_planning/job_packets/example__tailoring.json",
    )

    assert "Back to Tailoring" in html
    assert "Prefer full control? Use Power Edit" in html
    assert "/tailoring-workspace?" in html
    assert 'data-scan-initial-mode="review"' in html

def test_saved_scans_page_discloses_ready_report_storage():
    html = saved_scans_page()

    assert "Review New Scan reports generated from submitted resumes and job descriptions." in html
    assert "generated match score and review payload in Postgres" in html
    assert "<th>Action</th>" in html
    assert 'colspan="9"' in html
    assert "/static/profile.js?v=profile_saved_scans_e5_discard_icon" in html
    assert "savedScanDeleteModal" in html


def test_saved_scans_profile_script_labels_ready_reports():
    script = Path("src/app/static/profile.js").read_text(encoding="utf-8")

    assert 'status === "ready" || status === "complete"' in script
    assert "Report generated" in script
    assert "Saved intake only" in script
    assert "/scan-workspace?saved_scan_id=" in script
    assert "data-saved-scan-delete" in script
    assert "saved-scan-action-badge" in script

def test_selector_prefers_score_positive_candidate_over_neutral_llm_candidate():
    plan = build_final_replacement_plan(
        [
            _candidate("neutral_llm", delta=0.0, llm=True, patch_text="neutral llm bullet"),
            _candidate("positive_det", delta=0.03, llm=False, patch_text="positive deterministic bullet"),
        ],
        [],
    )

    assert plan["app_ready_replacements"][0]["replacement_candidate_id"] == "positive_det"
    assert plan["app_ready_replacements"][0]["score_gate"] == "direct_replacement"
    assert plan["ai_optimize_optional_replacements"] == []


def test_selector_demotes_negative_or_neutral_candidates_from_direct_replacements():
    plan = build_final_replacement_plan(
        [
            _candidate("negative_llm", delta=-0.02, llm=True, patch_text="negative llm bullet"),
            _candidate("neutral_det", delta=0.0, llm=False, patch_text="neutral deterministic bullet"),
        ],
        [],
    )

    assert plan["app_ready_replacements"] == []
    assert plan["direct_apply_optional_replacements"] == []
    assert plan["ai_optimize_optional_replacements"] == []
    assert {row["score_gate"] for row in plan["direction_only_replacements"]} == {
        "score_neutral_guidance"
    }


def _direction_only_diagnosis():
    return {
        "diagnosis_action": "rewrite",
        "bullet_id": "bullet_1",
        "section": "Experience",
        "source": "Data Analyst",
        "original_text": "Built reporting dashboards using SQL.",
        "current_evidence": "Built reporting dashboards using SQL.",
    }


def _direction_only_candidate():
    return {
        "candidate_id": "direction_only_1",
        "source_bullet_id": "bullet_1",
        "operation_type": "rewrite",
        "proposal_status": "direction_only",
        "patch_text": "",
        "original_text": "Built reporting dashboards using SQL.",
        "current_evidence": "Built reporting dashboards using SQL.",
        "rewrite_instruction": "Lead with SQL reporting.",
        "materiality_validation_status": None,
        "projected_overall_delta": None,
        "confidence": "high",
        "unsupported_risk_signals": [],
        "adjacent_risk_signals": [],
        "direction_only_reason": "deterministic_patch_not_available",
        "supported_jd_signals": ["SQL", "reporting"],
        "evidence_type": "direct_overlap",
        "claim_safety": "safe_strengthen",
    }


def test_safe_app_ready_rewrite_promotion_default_off_keeps_direction_only(monkeypatch):
    called = {"promotion": 0}

    def fake_promote(payload, candidate):
        called["promotion"] += 1
        promoted = dict(candidate)
        promoted.update(
            {
                "proposal_status": "patch_ready",
                "patch_text": "Built SQL reporting dashboards for weekly stakeholder reporting.",
                "materiality_validation_status": "material_candidate",
                "projected_overall_delta": 0.04,
            }
        )
        return promoted

    monkeypatch.setattr(
        tailoring_rendering,
        "_diagnosis_to_replacement_candidate",
        lambda payload, diagnosis, index: _direction_only_candidate(),
    )
    monkeypatch.setattr(
        tailoring_rendering,
        "_merge_anchor_candidates_for_diagnosis",
        lambda diagnosis, candidates: [],
    )
    monkeypatch.setattr(
        tailoring_rendering,
        "_suppress_anchor_candidates_for_diagnosis",
        lambda diagnosis, candidates: [],
    )
    monkeypatch.setattr(
        tailoring_rendering,
        "_materiality_validate_rewrite_candidate",
        lambda payload, candidate, context: candidate,
    )
    monkeypatch.setattr(
        "src.tailoring.llm._maybe_promote_multisignal_directional_candidate",
        fake_promote,
    )

    candidates = tailoring_rendering._build_replacement_candidates(
        {},
        [_direction_only_diagnosis()],
        enable_safe_app_ready_rewrite_promotion=False,
    )
    plan = build_final_replacement_plan(candidates, [])

    assert called["promotion"] == 0
    assert plan["app_ready_replacements"] == []
    assert plan["direct_apply_optional_replacements"] == []
    assert plan["ai_optimize_optional_replacements"] == []
    assert len(plan["direction_only_replacements"]) == 1


def test_safe_app_ready_rewrite_promotion_flag_allows_existing_selector_lane(monkeypatch):
    def fake_promote(payload, candidate):
        promoted = dict(candidate)
        promoted.update(
            {
                "proposal_status": "patch_ready",
                "proposal_type": "patch_ready_rewrite",
                "patch_ready": True,
                "patch_text": "Built SQL reporting dashboards for weekly stakeholder reporting.",
                "materiality_validation_status": "material_candidate",
                "projected_overall_delta": 0.04,
                "projected_dimension_deltas": {"required_skills_alignment": 0.04},
            }
        )
        return promoted

    monkeypatch.setattr(
        tailoring_rendering,
        "_diagnosis_to_replacement_candidate",
        lambda payload, diagnosis, index: _direction_only_candidate(),
    )
    monkeypatch.setattr(
        tailoring_rendering,
        "_merge_anchor_candidates_for_diagnosis",
        lambda diagnosis, candidates: [],
    )
    monkeypatch.setattr(
        tailoring_rendering,
        "_suppress_anchor_candidates_for_diagnosis",
        lambda diagnosis, candidates: [],
    )
    monkeypatch.setattr(
        tailoring_rendering,
        "_materiality_validate_rewrite_candidate",
        lambda payload, candidate, context: candidate,
    )
    monkeypatch.setattr(
        "src.tailoring.llm._maybe_promote_multisignal_directional_candidate",
        fake_promote,
    )

    candidates = tailoring_rendering._build_replacement_candidates(
        {},
        [_direction_only_diagnosis()],
        enable_safe_app_ready_rewrite_promotion=True,
    )
    plan = build_final_replacement_plan(candidates, [])

    assert plan["app_ready_replacements"][0]["replacement_candidate_id"] == "direction_only_1"
    assert plan["app_ready_replacements"][0]["score_gate"] == "direct_replacement"
    assert plan["direct_apply_optional_replacements"] == []
    assert plan["ai_optimize_optional_replacements"] == []
    assert plan["direction_only_replacements"] == []


def test_instruction_looking_patch_text_remains_non_actionable():
    plan = build_final_replacement_plan(
        [
            _candidate(
                "instruction_like",
                delta=0.05,
                patch_text=(
                    "Lead with SQL reporting in this opening clause, then keep "
                    "the remaining context only if truthful."
                ),
            )
        ],
        [],
    )

    assert plan["app_ready_replacements"] == []
    assert plan["direct_apply_optional_replacements"] == []
    assert plan["ai_optimize_optional_replacements"] == []
    assert plan["direction_only_replacements"][0]["score_gate"] == "direct_replacement"


def _live_patch_payload(*, duplicate_source=False):
    anchor = {
        "source_bullet_id": "bullet_sql",
        "source_entry_id": "entry_sql",
        "section": "Experience",
        "source": "Data Analyst @ ExampleCo",
        "text": "Built SQL reporting dashboards for weekly stakeholder reporting.",
        "parent_bullet": "Built SQL reporting dashboards for weekly stakeholder reporting.",
        "overlaps": ["SQL", "reporting"],
        "supported_terms": ["SQL", "reporting"],
    }
    anchors = [anchor]
    if duplicate_source:
        anchors.append({**anchor, "source_bullet_id": "bullet_sql_duplicate"})
    return {
        "job": {"company": "ExampleCo", "title": "Analytics Engineer"},
        "summary": {
            "matched_required": ["SQL", "reporting"],
            "matched_preferred": [],
            "matched_terms": ["SQL", "reporting"],
        },
        "evidence_layers": {
            "anchors": anchors,
            "supports": [],
            "context": [],
        },
        "edit_cards": [],
    }


def _live_patch_response(*, patch_text=None, source_bullet_id="bullet_sql", source="Data Analyst @ ExampleCo", unsupported=None):
    return {
        "rewrite_directions": [
            {
                "prefix": "Lead with",
                "source": "Data Analyst @ ExampleCo",
                "direction": "sql reporting dashboards in opening clause",
            },
            {
                "prefix": "Support with",
                "source": "Data Analyst @ ExampleCo",
                "direction": "weekly stakeholder reporting context remains explicit",
            },
            {
                "prefix": "Keep gap explicit",
                "source": "",
                "direction": "unsupported certifications not present in evidence",
            },
        ],
        "concrete_replacement_candidates": [
            {
                "source_bullet_id": source_bullet_id,
                "source_entry_id": "entry_sql",
                "section": "Experience",
                "source": source,
                "original_text": "Built SQL reporting dashboards for weekly stakeholder reporting.",
                "operation_type": "rewrite",
                "proposal_status": "patch_ready",
                "patch_text": patch_text or "Built SQL reporting dashboards for weekly stakeholder reporting.",
                "why_this_improves_match": "Keeps SQL and reporting visible.",
                "unsupported_risk_signals": list(unsupported or []),
                "adjacent_risk_signals": [],
                "confidence": "high",
            }
        ],
    }


def _live_patch_response_with_short_directions(**kwargs):
    response = _live_patch_response(**kwargs)
    response["rewrite_directions"] = [
        {
            "prefix": "Lead with",
            "source": "Data Analyst @ ExampleCo",
            "direction": "sql reporting",
        },
        {
            "prefix": "Support with",
            "source": "Data Analyst @ ExampleCo",
            "direction": "weekly context",
        },
    ]
    return response


def _live_patch_packet():
    return {
        "job": {"company": "ExampleCo", "title": "Analytics Engineer"},
        "selection": {"selected_resume": "resume.pdf", "selected_score": 0.81},
        "summary": {
            "matched_required": ["SQL", "reporting"],
            "missing_required": [],
            "missing_preferred": [],
        },
        "guardrail": "Only use supported resume evidence.",
    }


def _live_patch_prompt_payload():
    payload = _live_patch_payload()
    packet = _live_patch_packet()
    payload["live_rewrite_prompt"] = tailoring_llm._build_live_rewrite_prompt(packet, payload)
    return packet, payload


def test_live_rewrite_prompt_default_stays_direction_only_contract():
    packet, payload = _live_patch_prompt_payload()
    prompt = payload["live_rewrite_prompt"]

    assert "one top-level key: rewrite_directions" in prompt
    assert "Output key: rewrite_directions" in prompt
    assert "concrete_replacement_candidates" not in prompt
    assert "Concrete candidate source table" not in prompt
    assert "source_bullet_id:" not in prompt
    assert "source_entry_id:" not in prompt


def test_enabled_live_rewrite_prompt_is_concrete_candidate_aware():
    packet, payload = _live_patch_prompt_payload()
    prompt = tailoring_llm._build_live_concrete_rewrite_prompt(packet, payload)

    assert "one top-level key: rewrite_directions" not in prompt
    assert "Output key: rewrite_directions" not in prompt
    assert "Required top-level JSON keys:" in prompt
    assert "rewrite_directions" in prompt
    assert "concrete_replacement_candidates" in prompt
    assert "Concrete candidate source table:" in prompt
    assert "source_bullet_id: bullet_sql" in prompt
    assert "source_entry_id: entry_sql" in prompt
    assert "Concrete candidate object schema:" in prompt
    assert "operation_type: rewrite" in prompt
    assert "proposal_status: patch_ready" in prompt
    assert "patch_text: a complete replacement resume bullet, not an instruction." in prompt
    assert "Compact safe example - do NOT copy this example into output:" in prompt
    assert "Do NOT invent tools, methods, metrics, skills, domains, employers" in prompt
    assert "Do NOT inflate credentials" in prompt
    assert "unsupported_risk_signals: []" in prompt


def test_enabled_live_llm_tailoring_parses_groq_json_object_concrete_candidates(monkeypatch, tmp_path):
    packet, payload = _live_patch_prompt_payload()
    captured = {}

    def fake_chat_completion(**kwargs):
        captured["response_schema"] = kwargs.get("response_schema")
        captured["messages"] = kwargs.get("messages")
        return {
            "content": tailoring_llm.json.dumps(_live_patch_response()),
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "fallback_used": False,
        }

    monkeypatch.setattr(
        tailoring_llm,
        "run_chat_completion_with_metadata",
        fake_chat_completion,
    )

    result = tailoring_llm._run_live_llm_tailoring(
        packet,
        payload,
        output_llm_json=str(tmp_path / "tailoring_llm.json"),
        refresh_llm_cache=True,
        enable_safe_app_ready_rewrite_promotion=True,
    )

    user_prompt = captured["messages"][1]["content"]
    assert captured["response_schema"] == tailoring_llm.LIVE_REWRITE_WITH_CONCRETE_PATCH_RESPONSE_SCHEMA
    assert "one top-level key: rewrite_directions" not in user_prompt
    assert "concrete_replacement_candidates" in user_prompt
    assert "source_bullet_id: bullet_sql" in user_prompt
    assert result["parse_ok"] is True
    assert result["concrete_replacement_candidates_requested"] is True
    assert result["raw_response"].startswith("{")
    candidate = result["parsed"]["concrete_replacement_candidates"][0]
    assert candidate["source_bullet_id"] == "bullet_sql"
    assert candidate["proposal_status"] == "patch_ready"
    assert candidate["patch_text"] == "Built SQL reporting dashboards for weekly stakeholder reporting."
    assert result["parsed"]["invalid_concrete_replacement_candidates"] == []


def test_enabled_live_llm_tailoring_keeps_valid_concrete_candidate_when_directions_are_short(monkeypatch, tmp_path):
    packet, payload = _live_patch_prompt_payload()

    def fake_chat_completion(**kwargs):
        return {
            "content": tailoring_llm.json.dumps(_live_patch_response_with_short_directions()),
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "fallback_used": False,
        }

    monkeypatch.setattr(
        tailoring_llm,
        "run_chat_completion_with_metadata",
        fake_chat_completion,
    )

    result = tailoring_llm._run_live_llm_tailoring(
        packet,
        payload,
        output_llm_json=str(tmp_path / "tailoring_llm.json"),
        refresh_llm_cache=True,
        enable_safe_app_ready_rewrite_promotion=True,
    )

    assert result["parse_ok"] is True
    assert result["parsed"]["rewrite_directions"] == []
    assert result["parsed"]["concrete_replacement_candidates"][0]["source_bullet_id"] == "bullet_sql"
    assert [
        row["validation_reason"]
        for row in result["parsed"]["invalid_rewrite_directions"]
    ] == ["too_short:2", "too_short:2"]
    assert result["parsed"]["invalid_concrete_replacement_candidates"] == []


def test_enabled_live_llm_tailoring_short_directions_without_valid_concrete_still_fails(monkeypatch, tmp_path):
    packet, payload = _live_patch_prompt_payload()

    def fake_chat_completion(**kwargs):
        return {
            "content": tailoring_llm.json.dumps(
                _live_patch_response_with_short_directions(
                    patch_text="Lead with SQL reporting in the opening clause.",
                )
            ),
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "fallback_used": False,
        }

    monkeypatch.setattr(
        tailoring_llm,
        "run_chat_completion_with_metadata",
        fake_chat_completion,
    )

    result = tailoring_llm._run_live_llm_tailoring(
        packet,
        payload,
        output_llm_json=str(tmp_path / "tailoring_llm.json"),
        refresh_llm_cache=True,
        enable_safe_app_ready_rewrite_promotion=True,
    )

    assert result["parse_ok"] is False
    assert "live_llm_contract_no_valid_rewrite_or_concrete_candidate" in result["parse_error"]
    assert result["parsed"]["concrete_replacement_candidates"] == []


def test_live_concrete_patch_contract_default_off_still_rejects_short_direction():
    with pytest.raises(ValueError, match="live_llm_contract_direction_1_too_short"):
        tailoring_llm._validate_live_llm_parsed_contract(
            _live_patch_response_with_short_directions(),
            _live_patch_payload(),
            enable_safe_app_ready_rewrite_promotion=False,
        )


def test_live_concrete_patch_contract_default_off_ignores_patch_candidates():
    parsed = tailoring_llm._validate_live_llm_parsed_contract(
        _live_patch_response(),
        _live_patch_payload(),
        enable_safe_app_ready_rewrite_promotion=False,
    )
    normalized = tailoring_llm._normalize_live_llm_parsed(parsed)

    assert normalized["concrete_replacement_candidates_requested"] is False
    assert normalized["concrete_replacement_candidates"] == []


def test_live_concrete_patch_contract_enabled_accepts_safe_patch_candidate():
    parsed = tailoring_llm._validate_live_llm_parsed_contract(
        _live_patch_response(),
        _live_patch_payload(),
        enable_safe_app_ready_rewrite_promotion=True,
    )
    normalized = tailoring_llm._normalize_live_llm_parsed(parsed)

    assert normalized["concrete_replacement_candidates_requested"] is True
    assert normalized["invalid_concrete_replacement_candidates"] == []
    candidate = normalized["concrete_replacement_candidates"][0]
    assert candidate["proposal_status"] == "patch_ready"
    assert candidate["patch_text"] == "Built SQL reporting dashboards for weekly stakeholder reporting."


def test_live_concrete_patch_contract_rejects_instruction_and_unsupported_patch_text():
    instruction_parsed = tailoring_llm._validate_live_llm_parsed_contract(
        _live_patch_response(
            patch_text="Lead with SQL reporting in the opening clause.",
        ),
        _live_patch_payload(),
        enable_safe_app_ready_rewrite_promotion=True,
    )
    unsupported_parsed = tailoring_llm._validate_live_llm_parsed_contract(
        _live_patch_response(
            patch_text="Built Snowflake reporting dashboards for weekly stakeholder reporting.",
            unsupported=["Snowflake"],
        ),
        _live_patch_payload(),
        enable_safe_app_ready_rewrite_promotion=True,
    )

    assert instruction_parsed["concrete_replacement_candidates"] == []
    assert instruction_parsed["invalid_concrete_replacement_candidates"][0]["validation_reason"] == (
        "instructional_patch_text_not_literal_bullet"
    )
    assert unsupported_parsed["concrete_replacement_candidates"] == []
    assert unsupported_parsed["invalid_concrete_replacement_candidates"][0]["validation_reason"] == (
        "unsupported_risk_signals_present"
    )


def test_live_concrete_patch_contract_rejects_missing_and_ambiguous_source_bullets():
    missing = tailoring_llm._validate_live_llm_parsed_contract(
        _live_patch_response(source_bullet_id="missing"),
        _live_patch_payload(),
        enable_safe_app_ready_rewrite_promotion=True,
    )
    ambiguous = tailoring_llm._validate_live_llm_parsed_contract(
        _live_patch_response(source_bullet_id="", source="Data Analyst @ ExampleCo"),
        _live_patch_payload(duplicate_source=True),
        enable_safe_app_ready_rewrite_promotion=True,
    )

    assert missing["concrete_replacement_candidates"] == []
    assert missing["invalid_concrete_replacement_candidates"][0]["validation_reason"] == (
        "source_bullet_not_found"
    )
    assert ambiguous["concrete_replacement_candidates"] == []
    assert ambiguous["invalid_concrete_replacement_candidates"][0]["validation_reason"] == (
        "ambiguous_source_bullet"
    )


def test_enabled_live_concrete_patch_can_reach_existing_selector_lane(monkeypatch):
    parsed = tailoring_llm._validate_live_llm_parsed_contract(
        _live_patch_response(),
        _live_patch_payload(),
        enable_safe_app_ready_rewrite_promotion=True,
    )
    normalized = tailoring_llm._normalize_live_llm_parsed(parsed)
    llm_output = {"parsed": normalized}

    monkeypatch.setattr(
        tailoring_rendering,
        "_materiality_validate_rewrite_candidate",
        lambda payload, candidate, context: {
            **candidate,
            "materiality_validation_status": "material_candidate",
            "projected_overall_delta": 0.05,
            "projected_dimension_deltas": {"required_skills_alignment": 0.05},
        },
    )

    candidates = tailoring_rendering._build_replacement_candidates(
        _live_patch_payload(),
        [],
        llm_output=llm_output,
        enable_safe_app_ready_rewrite_promotion=True,
    )
    plan = build_final_replacement_plan(candidates, [])

    assert any(row["candidate_id"] == "live_concrete_candidate:1" for row in candidates)
    actionable = (
        plan["app_ready_replacements"]
        + plan["direct_apply_optional_replacements"]
        + plan["ai_optimize_optional_replacements"]
    )
    assert actionable[0]["replacement_candidate_id"] == "live_concrete_candidate:1"
    assert plan["direct_apply_optional_replacements"] == []
    assert plan["app_ready_replacements"] == []
    assert plan["ai_optimize_optional_replacements"]
    assert plan["direction_only_replacements"] == []


def test_scan_issue_contract_marks_direct_guidance_and_hidden_score_gate_items():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[
            {
                "replacement_candidate_id": "positive",
                "source_bullet_id": "bullet_1",
                "final_replacement_text": "positive patch",
                "original_text": "original",
                "projected_overall_delta": 0.04,
            }
        ],
        trusted_optional=[],
        ai_optimize_optional=[
            {
                "replacement_candidate_id": "neutral",
                "source_bullet_id": "bullet_2",
                "final_replacement_text": "neutral patch",
                "original_text": "original",
                "projected_overall_delta": 0.0,
            },
            {
                "replacement_candidate_id": "negative",
                "source_bullet_id": "bullet_3",
                "final_replacement_text": "negative patch",
                "original_text": "original",
                "projected_overall_delta": -0.02,
            },
        ],
        directional_guidance=[],
    )

    issues = {issue["candidate_id"]: issue for issue in contract["issues"]}

    assert contract["version"] == "scan_issue_contract_v2"

    assert issues["positive"]["row_action_type"] == "direct_replacement"
    assert issues["positive"]["can_accept"] is True
    assert issues["positive"]["can_accept_all"] is True
    assert issues["positive"]["projected_score_delta_points"] == 4

    assert issues["neutral"]["row_action_type"] == "phrase_generation"
    assert issues["neutral"]["can_accept"] is False
    assert issues["neutral"]["is_visible_in_review"] is True
    assert issues["neutral"]["row_action_label"] == "Phrase"

    assert issues["negative"]["row_action_type"] == "hidden_rejected"
    assert issues["negative"]["can_accept"] is False
    assert issues["negative"]["is_visible_in_review"] is False

    assert contract["counts"]["actionable"] == 1
    assert contract["counts"]["accept_all_eligible"] == 1
    assert contract["counts"]["hidden"] == 1


def test_scan_issue_contract_demotes_deterministic_only_score_lifts_to_guidance():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[
            {
                "replacement_candidate_id": "deterministic_positive",
                "source_bullet_id": "bullet_1",
                "final_replacement_text": "deterministic positive patch",
                "original_text": "original",
                "projected_overall_delta": 0.07,
                "replacement_source": "deterministic",
            },
            {
                "replacement_candidate_id": "llm_positive",
                "source_bullet_id": "bullet_2",
                "final_replacement_text": "llm positive patch",
                "original_text": "original",
                "projected_overall_delta": 0.04,
                "replacement_source": "live_llm",
            },
        ],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
    )

    issues = {issue["candidate_id"]: issue for issue in contract["issues"]}

    assert issues["deterministic_positive"]["row_action_type"] == "manual_guidance"
    assert issues["deterministic_positive"]["can_accept"] is False
    assert issues["llm_positive"]["row_action_type"] == "direct_replacement"
    assert issues["llm_positive"]["can_accept"] is True


def test_keyword_contract_uses_summary_and_resume_evidence_for_matched_missing_rows():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[
            {
                "replacement_candidate_id": "python_candidate",
                "source_bullet_id": "bullet_1",
                "final_replacement_text": "Python patch",
                "original_text": "original",
                "supported_jd_signals": ["Python"],
                "projected_overall_delta": 0.03,
            },
            {
                "replacement_candidate_id": "sql_candidate",
                "source_bullet_id": "bullet_2",
                "final_replacement_text": "SQL patch",
                "original_text": "original",
                "supported_jd_signals": ["SQL"],
                "projected_overall_delta": 0.0,
            },
        ],
        directional_guidance=[],
        resume_evidence=_resume_evidence(skills=["Tableau"], bullets=["Built dashboards in Tableau."]),
        tailoring_summary={
            "matched_required": ["Tableau"],
            "missing_required": ["Python", "SQL"],
        },
    )

    rows = {issue["canonical_term"]: issue for issue in contract["issues"]}

    assert rows["tableau"]["row_action_type"] == "matched"
    assert rows["tableau"]["coverage_label"] == "Backed 2"
    assert rows["tableau"]["matched_count_label"] == "Backed 2"
    assert rows["tableau"]["matched_count"] == 2
    assert rows["tableau"]["evidence_anchors"][0]["text"] == "Built dashboards in Tableau."

    assert rows["python"]["row_action_type"] == "direct_replacement"
    assert rows["python"]["has_ai_suggestion"] is True
    assert rows["python"]["best_candidate_id"] == "python_candidate"
    assert rows["python"]["coverage_label"] == "0/1"
    assert rows["python"]["projected_score_delta_points"] == 3

    assert rows["sql"]["row_action_type"] == "phrase_generation"
    assert rows["sql"]["has_ai_suggestion"] is True
    assert rows["sql"]["can_accept"] is False
    assert rows["sql"]["row_action_label"] == "Phrase"


def test_keyword_contract_selects_highest_positive_candidate_for_duplicate_term():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[
            {
                "replacement_candidate_id": "python_low",
                "source_bullet_id": "bullet_1",
                "final_replacement_text": "low lift Python patch",
                "original_text": "original",
                "supported_jd_signals": ["Python"],
                "projected_overall_delta": 0.01,
            },
            {
                "replacement_candidate_id": "python_high",
                "source_bullet_id": "bullet_2",
                "final_replacement_text": "high lift Python patch",
                "original_text": "original",
                "supported_jd_signals": ["Python"],
                "projected_overall_delta": 0.05,
            },
        ],
        directional_guidance=[],
        tailoring_summary={"missing_required": ["Python"]},
    )

    python_row = {
        issue["canonical_term"]: issue
        for issue in contract["issues"]
    }["python"]

    assert python_row["best_candidate_id"] == "python_high"
    assert python_row["projected_score_delta_points"] == 5
    assert python_row["coverage_label"] == "0/2"


def test_scan_issue_contract_rows_include_jobscan_review_groups():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        resume_evidence=_resume_evidence(
            skills=["Python", "SQL", "Tableau"],
            bullets=[
                "Built Python validation workflows with SQL and Tableau dashboards.",
                "Reduced quality review time by 20% through automation.",
            ],
        ),
        tailoring_summary={"matched_required": ["Python"]},
    )

    groups = {group["group_id"]: group for group in contract["groups"]}
    assert set(groups) == {"skills", "searchability", "formatting", "recruiter_tips"}
    assert any(issue["group_id"] == "skills" for issue in contract["issues"])
    assert any(issue["group_id"] == "searchability" for issue in contract["issues"])
    assert any(issue["group_id"] == "formatting" for issue in contract["issues"])
    assert all("severity" in issue for issue in contract["issues"])

    match_report = contract["match_report"]
    assert match_report["version"] == "scan_match_report_v1"
    assert [row["key"] for row in match_report["priority_order"]] == [
        "hard_skills",
        "education_level",
        "job_title",
        "soft_skills",
        "other_keywords",
    ]
    assert "formatting" in match_report["group_counts"]


def test_searchability_contract_includes_jobscan_parseability_details():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        resume_evidence=_resume_evidence(
            skills=["Python", "SQL"],
            bullets=["Built Python workflows with SQL automation from Jan 2024 to Present."],
            raw_text=(
                "Sriram Neelakantan\n"
                "sriram@example.com | +1 857 437 9513 | linkedin.com/in/sriram\n\n"
                "Professional Experience\n"
                "Senior Data Scientist\n"
                "Built Python workflows with SQL automation from Jan 2024 to Present.\n\n"
                "Skills\n"
                "Python, SQL\n\n"
                "Education\n"
                "Master of Science, Northeastern University, 2023\n"
            ),
            education_entries=[SimpleNamespace(school="Northeastern University")],
        ),
        tailoring_summary={
            "target_job_title": "Senior Data Scientist",
            "required_education": ["Master's degree"],
        },
    )

    rows = {issue["issue_id"]: issue for issue in contract["issues"]}
    for check_id in (
        "contact_info_searchable",
        "education_info_searchable",
        "dates_searchable",
        "section_headings_parseable",
        "job_title_alignment",
    ):
        row = rows[f"scan_issue:searchability:{check_id}"]
        assert row["group_id"] == "searchability"
        assert row["row_action_type"] == "matched"
        assert row["row_action_label"] == "Check"
        assert row["coverage_label"] == "Pass"

    assert rows["scan_issue:searchability:education_info_searchable"]["score_priority_rank"] == 2
    assert rows["scan_issue:searchability:education_info_searchable"]["score_priority_label"] == "Education level"
    assert rows["scan_issue:searchability:job_title_alignment"]["score_priority_rank"] == 3
    assert rows["scan_issue:searchability:job_title_alignment"]["score_priority_label"] == "Job title"


def test_formatting_contract_includes_ats_formatting_checks():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        resume_evidence=_resume_evidence(
            skills=["Python", "SQL", "AWS"],
            bullets=[
                "- Built Python and SQL automation for cloud data quality monitoring.",
                "- Improved AWS reporting workflows and reduced review time by 20 percent.",
            ],
            raw_text=(
                "Sriram Neelakantan\n"
                "sriram@example.com | +1 857 437 9513 | linkedin.com/in/sriram\n\n"
                "Summary\n"
                "Data engineer with experience building reliable analytics platforms, "
                "automation workflows, data quality systems, stakeholder dashboards, "
                "and production monitoring for business teams.\n\n"
                "Skills\n"
                "Python, SQL, AWS, Spark, Tableau, Airflow, dbt, data modeling, "
                "quality checks, pipeline orchestration, cloud analytics.\n\n"
                "Professional Experience\n"
                "- Built Python and SQL automation for cloud data quality monitoring "
                "across finance, operations, and customer reporting workflows.\n"
                "- Improved AWS reporting workflows and reduced review time by 20 percent "
                "through automated validation and weekly stakeholder dashboards.\n"
                "- Partnered with product and analytics teams to translate ambiguous "
                "requirements into resilient data models and documented runbooks.\n\n"
                "Education\n"
                "Master of Science, Northeastern University, 2023\n"
            ),
        ),
        tailoring_summary={"target_job_title": "Data Engineer"},
    )

    rows = {issue["issue_id"]: issue for issue in contract["issues"]}
    for check_id in (
        "text_extractable",
        "table_column_risk",
        "bullet_formatting",
        "special_character_risk",
        "standard_resume_structure",
    ):
        row = rows[f"scan_issue:formatting:{check_id}"]
        assert row["group_id"] == "formatting"
        assert row["row_action_label"] == "Check"

    assert rows["scan_issue:formatting:text_extractable"]["row_action_type"] == "matched"
    assert rows["scan_issue:formatting:table_column_risk"]["coverage_label"] == "Pass"
    assert contract["match_report"]["formatting"]["matched"] >= 4


def test_skills_contract_classifies_hard_soft_and_other_keywords():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        resume_evidence=_resume_evidence(
            skills=["Python"],
            bullets=["Built Python workflows for customer analytics."],
        ),
        tailoring_summary={
            "matched_required": ["Python"],
            "missing_preferred": ["Communication"],
            "missing_terms": ["Customer"],
        },
    )

    skill_rows = {
        issue["canonical_term"]: issue
        for issue in contract["issues"]
        if issue["group_id"] == "skills"
    }

    assert skill_rows["python"]["skill_type"] == "hard_skill"
    assert skill_rows["python"]["skill_type_label"] == "Hard skill"
    assert skill_rows["python"]["score_priority_rank"] == 1
    assert skill_rows["python"]["score_priority_label"] == "Hard skills"
    assert skill_rows["python"]["score_priority_weight"] > skill_rows["customer"]["score_priority_weight"]
    assert skill_rows["communication"]["skill_type"] == "soft_skill"
    assert skill_rows["communication"]["skill_type_label"] == "Soft skill"
    assert skill_rows["communication"]["score_priority_rank"] == 4
    assert skill_rows["communication"]["score_priority_label"] == "Soft skills"
    assert skill_rows["customer"]["skill_type"] == "other_keyword"
    assert skill_rows["customer"]["skill_type_label"] == "Other keyword"
    assert skill_rows["customer"]["score_priority_rank"] == 5
    assert skill_rows["customer"]["score_priority_label"] == "Other keywords"

    skills_group = next(group for group in contract["groups"] if group["group_id"] == "skills")
    assert skills_group["skill_type_counts"]["hard_skill"] == 1
    assert skills_group["skill_type_counts"]["soft_skill"] == 1
    assert skills_group["skill_type_counts"]["other_keyword"] == 1


def test_skill_rows_include_job_description_context_anchors():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        resume_evidence=_resume_evidence(
            skills=["Python"],
            bullets=["Built Python validation workflows."],
        ),
        tailoring_summary={"matched_required": ["Python"]},
        jd_record={
            "title": "Data Scientist",
            "retrieval_text": "We need Python experience for production analytics. SQL is preferred.",
        },
    )

    python_row = next(
        issue for issue in contract["issues"]
        if issue["group_id"] == "skills" and issue["canonical_term"] == "python"
    )

    assert python_row["jd_context_anchors"]
    assert python_row["jd_context_anchors"][0]["type"] == "job_description"
    assert "Python experience" in python_row["jd_context_label"]


def test_jd_context_ignores_job_header_when_body_text_has_no_term():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        resume_evidence=_resume_evidence(
            skills=["Python"],
            bullets=["Built Python validation workflows."],
        ),
        tailoring_summary={"matched_required": ["Python"]},
        jd_record={
            "title": "Python Engineer",
            "company": "Example",
            "location": "Remote",
            "retrieval_text": "This role focuses on stakeholder reporting and dashboard delivery.",
        },
    )

    python_row = next(
        issue for issue in contract["issues"]
        if issue["group_id"] == "skills" and issue["canonical_term"] == "python"
    )

    assert python_row["jd_context_anchors"] == []
    assert python_row["jd_context_label"] == ""


def test_jd_context_ignores_greenhouse_metadata_chunks():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        resume_evidence=_resume_evidence(
            skills=["Tensorflow"],
            bullets=["Built Tensorflow model training workflows."],
        ),
        tailoring_summary={"matched_required": ["Tensorflow"]},
        jd_record={
            "retrieval_text": (
                "New York, New York, United States; Seattle, Washington, United States "
                "Source: greenhouse Role family: ml_engineer Seniority: Required skills: Tensorflow. "
                "You will build ranking systems and partner with product teams."
            ),
        },
    )

    row = next(
        issue for issue in contract["issues"]
        if issue["group_id"] == "skills" and issue["canonical_term"] == "tensorflow"
    )

    assert row["jd_context_anchors"] == []
    assert row["jd_context_label"] == ""


def test_scan_contract_adds_labeled_predicted_skill_rows():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        resume_evidence=_resume_evidence(
            skills=["Python"],
            bullets=["Built Python model validation workflows."],
        ),
        tailoring_summary={"matched_required": ["Python"], "target_job_title": "Machine Learning Engineer"},
        jd_record={
            "title": "Machine Learning Engineer",
            "retrieval_text": "Build ML systems for ranking and recommendation quality.",
        },
    )

    predicted_rows = [
        issue for issue in contract["issues"]
        if issue.get("bucket") == "predicted"
    ]
    predicted_terms = {issue["canonical_term"] for issue in predicted_rows}

    assert "python" not in predicted_terms
    assert "pytorch" in predicted_terms
    assert "tensorflow" in predicted_terms
    assert all(issue["row_action_type"] == "predicted_skill" for issue in predicted_rows)
    assert all(issue["row_action_label"] == "Predicted" for issue in predicted_rows)
    assert all(issue["can_accept"] is False for issue in predicted_rows)
    assert all(issue["can_accept_all"] is False for issue in predicted_rows)
    assert all(issue["score_priority_weight"] == 0.0 for issue in predicted_rows)

    skills_group = next(group for group in contract["groups"] if group["group_id"] == "skills")
    predicted_bucket = next(bucket for bucket in skills_group["buckets"] if bucket["bucket"] == "predicted")
    assert predicted_bucket["count"] == len(predicted_rows)


def test_scan_contract_adds_lower_impact_other_keyword_rows():
    contract = _build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        resume_evidence=_resume_evidence(
            skills=["Python"],
            bullets=["Built Python analytics workflows for advertising quality."],
        ),
        tailoring_summary={"matched_required": ["Python"]},
        jd_record={
            "title": "Data Scientist",
            "retrieval_text": "Work on advertising marketplace quality and risk signals.",
        },
    )

    other_rows = [
        issue for issue in contract["issues"]
        if issue.get("bucket") == "other_keyword"
    ]
    other_terms = {issue["canonical_term"] for issue in other_rows}

    assert "advertising" in other_terms
    assert "marketplace" in other_terms
    assert all(issue["row_action_type"] == "other_keyword" for issue in other_rows)
    assert all(issue["row_action_label"] == "Keyword" for issue in other_rows)
    assert all(issue["can_accept"] is False for issue in other_rows)
    assert all(issue["can_accept_all"] is False for issue in other_rows)
    assert all(issue["score_priority_weight"] == 0.0 for issue in other_rows)

    advertising_row = next(issue for issue in other_rows if issue["canonical_term"] == "advertising")
    assert advertising_row["skill_type"] == "other_keyword"
    assert advertising_row["jd_context_anchors"]

    skills_group = next(group for group in contract["groups"] if group["group_id"] == "skills")
    other_bucket = next(bucket for bucket in skills_group["buckets"] if bucket["bucket"] == "other_keyword")
    assert other_bucket["count"] == len(other_rows)


def test_workspace_draft_persists_excluded_scan_issue_ids():
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "planning"
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / "example__tailoring.json"
        artifact_path.write_text(
            """
{
  "job": {"company": "Example", "title": "Data Scientist"},
  "selection": {"selected_resume": "resume.pdf"},
  "selected_patch_candidate_ids": []
}
""".strip(),
            encoding="utf-8",
        )

        saved = save_tailoring_workspace_draft_payload(
            output_dir=output_dir,
            tailoring_json_path=str(artifact_path),
            selected_resume="resume.pdf",
            selected_patch_candidate_ids=[],
            manual_bullet_edits={},
            rewrite_review_decisions={},
            excluded_scan_issue_ids=[
                "scan_issue:skills:keyword:beam",
                "scan_issue:skills:keyword:beam",
                "scan_issue:skills:keyword:flink",
            ],
            note="excluded",
        )

        assert saved["draft"]["excluded_scan_issue_ids"] == [
            "scan_issue:skills:keyword:beam",
            "scan_issue:skills:keyword:flink",
        ]

        loaded = load_tailoring_workspace_draft_payload(
            output_dir=output_dir,
            tailoring_json_path=str(artifact_path),
            selected_resume="resume.pdf",
        )

        assert loaded["draft"]["excluded_scan_issue_ids"] == [
            "scan_issue:skills:keyword:beam",
            "scan_issue:skills:keyword:flink",
        ]


def test_scan_extracts_resume_personal_details_from_header():
    details = _extract_resume_personal_details(
        _resume_evidence(
            raw_text="""
Alex Rivera
Harrison, NJ | +1 (555) 123-4567 | alex@example.com | linkedin.com/in/alexrivera

Technical Skills
Python, SQL
""".strip()
        )
    )

    assert details["name"] == "Alex Rivera"
    assert details["city"] == "Harrison"
    assert details["state"] == "NJ"
    assert details["contact"] == "+1 (555) 123-4567"
    assert details["email"] == "alex@example.com"
    assert details["linkedin"] == "https://linkedin.com/in/alexrivera"


def test_workspace_draft_persists_personal_details():
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "planning"
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / "example__tailoring.json"
        artifact_path.write_text(
            """
{
  "job": {"company": "Example", "title": "Data Scientist"},
  "selection": {"selected_resume": "resume.pdf"},
  "selected_patch_candidate_ids": []
}
""".strip(),
            encoding="utf-8",
        )

        saved = save_tailoring_workspace_draft_payload(
            output_dir=output_dir,
            tailoring_json_path=str(artifact_path),
            selected_resume="resume.pdf",
            selected_patch_candidate_ids=[],
            manual_bullet_edits={},
            rewrite_review_decisions={},
            excluded_scan_issue_ids=[],
            personal_details={
                "name": "Alex Rivera",
                "city": "Harrison",
                "state": "nj",
                "contact": "+1 (555) 123-4567",
                "email": "alex@example.com",
                "linkedin": "linkedin.com/in/alexrivera",
            },
            note="personal",
        )

        assert saved["draft"]["personal_details"]["state"] == "NJ"

        loaded = load_tailoring_workspace_draft_payload(
            output_dir=output_dir,
            tailoring_json_path=str(artifact_path),
            selected_resume="resume.pdf",
        )

        assert loaded["draft"]["personal_details"] == {
            "name": "Alex Rivera",
            "city": "Harrison",
            "state": "NJ",
            "contact": "+1 (555) 123-4567",
            "email": "alex@example.com",
            "linkedin": "https://linkedin.com/in/alexrivera",
            "github": "",
        }


if __name__ == "__main__":
    test_score_point_normalization_handles_normalized_and_point_values()
    test_workspace_score_preview_contract_exposes_points_and_changed_bullets()
    test_workspace_draft_fragments_contract_returns_patchable_bullets()
    test_scan_phrase_signal_terms_prefers_lead_with_guidance()
    test_scan_phrase_validate_llm_options_marks_manual_only()
    test_scan_phrase_parse_options_payload_accepts_fenced_json_text()
    test_scan_phrase_structured_output_contract_is_strict_schema()
    test_saved_scan_contract_normalizes_pasted_text_record()
    test_create_saved_scan_payload_skips_postgres_without_database_url()
    test_extract_scan_resume_upload_text_accepts_txt_upload()
    test_scan_workspace_job_context_prefills_loaded_job_description()
    test_scan_workspace_hides_tailoring_navigation_for_direct_new_scan()
    test_scan_workspace_keeps_tailoring_navigation_for_tailoring_context()
    test_saved_scans_page_discloses_ready_report_storage()
    test_saved_scans_profile_script_labels_ready_reports()
    test_selector_prefers_score_positive_candidate_over_neutral_llm_candidate()
    test_selector_demotes_negative_or_neutral_candidates_from_direct_replacements()
    test_scan_issue_contract_marks_direct_guidance_and_hidden_score_gate_items()
    test_scan_issue_contract_demotes_deterministic_only_score_lifts_to_guidance()
    test_keyword_contract_uses_summary_and_resume_evidence_for_matched_missing_rows()
    test_keyword_contract_selects_highest_positive_candidate_for_duplicate_term()
    test_scan_issue_contract_rows_include_jobscan_review_groups()
    test_searchability_contract_includes_jobscan_parseability_details()
    test_formatting_contract_includes_ats_formatting_checks()
    test_skills_contract_classifies_hard_soft_and_other_keywords()
    test_skill_rows_include_job_description_context_anchors()
    test_jd_context_ignores_job_header_when_body_text_has_no_term()
    test_jd_context_ignores_greenhouse_metadata_chunks()
    test_scan_contract_adds_labeled_predicted_skill_rows()
    test_scan_contract_adds_lower_impact_other_keyword_rows()
    test_workspace_draft_persists_excluded_scan_issue_ids()
    test_scan_extracts_resume_personal_details_from_header()
    test_workspace_draft_persists_personal_details()
