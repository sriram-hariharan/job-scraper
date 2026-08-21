"""Item 4E-T: pin the three demonstrated-but-untested behaviors from 4E.

1. draft_status == "saved" export-eligibility gate
   (_build_tailoring_workspace_export_context)
2. stale_signature draft invalidation on reload
   (load_tailoring_workspace_draft_payload)
3. accepted -> edited_after_accept transition after a manual edit diverges
   (_derive_workspace_rewrite_review_decisions)

This step pins EXISTING behavior only. No runtime code is touched. Bare
tailoring_status (the dead alias 4E identified) is deliberately not exercised
here -- it has no producer and no live consumer, and giving it a test would
wrongly imply it is a supported contract.
"""
import json
from pathlib import Path

import pytest


def _artifact_payload(company="Acme", title="Engineer", resume="resume.pdf", candidate_ids=("c1",)):
    replacement_candidates = [{"candidate_id": cid} for cid in candidate_ids]
    return {
        "job": {"job_doc_id": "job-1", "company": company, "title": title},
        "selection": {"selected_resume": resume},
        "replacement_candidates": replacement_candidates,
        "app_ready_replacements": [
            {
                "replacement_candidate_id": cid,
                "original_text": "Built internal tools.",
                "current_evidence": "Built internal tools.",
                "final_replacement_text": "Built internal tools used by 40 engineers.",
            }
            for cid in candidate_ids
        ],
    }


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Isolated tailoring artifact + real save/load round-trip, no DB dependency."""
    from src.app import services

    # The patch-selection overlay hits Postgres defensively; keep these tests
    # fully deterministic by short-circuiting it, matching its own no-DB fallback.
    monkeypatch.setattr(services, "_load_latest_patch_selection_overlay", lambda: {})

    output_dir = tmp_path / "application_planning" / "job_packets"
    output_dir.mkdir(parents=True)
    artifact_path = output_dir / "acme__engineer__resume__tailoring.json"
    artifact_path.write_text(json.dumps(_artifact_payload()), encoding="utf-8")

    return {"output_dir": tmp_path / "application_planning", "artifact_path": artifact_path}


def _rewrite_artifact(artifact_path: Path, **overrides):
    payload = _artifact_payload(**overrides) if overrides else _artifact_payload()
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")


def _stub_export_pdf_machinery(monkeypatch):
    """Bypass real resume-PDF extraction, which is out of this step's scope.

    _build_tailoring_workspace_export_context does far more than the
    draft_status gate: once the gate passes it resolves and reads a real
    resume PDF and applies patches to extracted pages. That machinery is a
    separate, already-existing concern -- these tests pin the gate, not PDF
    export, so the downstream steps are stubbed to let the gate-passing path
    complete deterministically without a real PDF file.
    """
    from src.app import services

    monkeypatch.setattr(services, "planning_resume_preview_path", lambda *_a, **_k: Path("/fake/resume.pdf"))
    monkeypatch.setattr(services, "_extract_resume_pdf_paragraph_pages_for_export", lambda _path: [{"page_number": 1, "lines": []}])
    monkeypatch.setattr(services, "_workspace_export_personal_details_from_pages", lambda _pages: {})
    monkeypatch.setattr(services, "_workspace_export_apply_personal_details", lambda _pages, _details: None)
    monkeypatch.setattr(services, "_apply_workspace_export_patch_specs", lambda _pages, _specs: {"applied": 0})


# =============================================================================
# Export-gate contract (_build_tailoring_workspace_export_context)
# =============================================================================

def test_export_succeeds_with_saved_draft(workspace, monkeypatch):
    from src.app import services

    _stub_export_pdf_machinery(monkeypatch)
    services.save_tailoring_workspace_draft_payload(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
        selected_patch_candidate_ids=["c1"],
    )

    context = services._build_tailoring_workspace_export_context(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
        require_saved_draft=True,
    )
    assert context["draft"]["draft_status"] == "saved"


def test_export_fails_closed_on_default_draft(workspace):
    """No save has happened yet: draft_status == 'default'."""
    from src.app import services

    with pytest.raises(ValueError, match="Save a tailored draft before exporting"):
        services._build_tailoring_workspace_export_context(
            output_dir=workspace["output_dir"],
            tailoring_json_path=str(workspace["artifact_path"]),
            selected_resume="resume.pdf",
            require_saved_draft=True,
        )


def test_export_fails_closed_on_stale_draft(workspace):
    from src.app import services

    services.save_tailoring_workspace_draft_payload(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
        selected_patch_candidate_ids=["c1"],
    )
    # Change the candidate set so the artifact signature no longer matches
    # the signature captured inside the saved draft.
    _rewrite_artifact(workspace["artifact_path"], candidate_ids=("c1", "c2"))

    # A stale draft sets has_saved_draft=False (same as a fresh/default draft),
    # so it is caught by the FIRST gate check ("Save a tailored draft before
    # exporting."), not the second ("Only a saved..."). The second message is
    # currently unreachable for stale/default drafts -- both paths reject.
    with pytest.raises(ValueError, match="Save a tailored draft before exporting"):
        services._build_tailoring_workspace_export_context(
            output_dir=workspace["output_dir"],
            tailoring_json_path=str(workspace["artifact_path"]),
            selected_resume="resume.pdf",
            require_saved_draft=True,
        )


def test_export_without_require_saved_draft_preserves_existing_behavior(workspace, monkeypatch):
    """require_saved_draft=False (preview's own default) must be unaffected."""
    from src.app import services

    _stub_export_pdf_machinery(monkeypatch)
    # No save at all -- would fail closed under require_saved_draft=True.
    context = services._build_tailoring_workspace_export_context(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
        require_saved_draft=False,
    )
    assert context["draft"]["draft_status"] == "default"


# =============================================================================
# Stale-signature contract (load_tailoring_workspace_draft_payload)
# =============================================================================

def test_matching_signature_restores_saved_draft(workspace):
    from src.app import services

    services.save_tailoring_workspace_draft_payload(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
        selected_patch_candidate_ids=["c1"],
        note="original saved note",
    )

    result = services.load_tailoring_workspace_draft_payload(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
    )
    assert result["draft_status"] == "saved"
    assert result["has_saved_draft"] is True
    assert result["draft"]["note"] == "original saved note"


def test_mismatched_signature_discards_stale_values(workspace):
    from src.app import services

    services.save_tailoring_workspace_draft_payload(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
        selected_patch_candidate_ids=["c1"],
        note="original saved note",
    )
    _rewrite_artifact(workspace["artifact_path"], candidate_ids=("c1", "c2"))

    result = services.load_tailoring_workspace_draft_payload(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
    )
    assert result["draft_status"] == "stale_signature"
    assert result["has_saved_draft"] is False
    # The stale saved note must NOT be silently promoted back to the caller;
    # the implementation instead replaces it with an explanatory message.
    assert result["draft"]["note"] != "original saved note"
    assert result["draft"]["note"] == (
        "Saved workspace draft was ignored because the tailoring artifact changed."
    )


def test_stale_draft_is_not_silently_written_back_as_saved(workspace):
    """Loading a stale draft must not itself mutate the on-disk draft file."""
    from src.app import services

    services.save_tailoring_workspace_draft_payload(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
        selected_patch_candidate_ids=["c1"],
    )
    _rewrite_artifact(workspace["artifact_path"], candidate_ids=("c1", "c2"))

    draft_path = workspace["output_dir"] / "job_packets" / "acme__engineer__resume__tailoring_workspace_draft.json"
    before = draft_path.read_text(encoding="utf-8")
    services.load_tailoring_workspace_draft_payload(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
    )
    after = draft_path.read_text(encoding="utf-8")
    assert before == after
    assert json.loads(after).get("draft_status") == "saved"  # on-disk file unchanged


# =============================================================================
# accepted -> edited_after_accept transition
# =============================================================================

CANDIDATE = "c1"
FINAL_TEXT = "Built internal tools used by 40 engineers."


def _surfaced_payload():
    return {
        "app_ready_replacements": [
            {
                "replacement_candidate_id": CANDIDATE,
                "original_text": "Built internal tools.",
                "current_evidence": "Built internal tools.",
                "final_replacement_text": FINAL_TEXT,
            }
        ],
    }


def test_accepted_with_diverging_manual_edit_becomes_edited_after_accept():
    from src.app import services

    derived = services._derive_workspace_rewrite_review_decisions(
        _surfaced_payload(),
        selected_candidate_ids=[CANDIDATE],
        manual_bullet_edits={f"candidate:{CANDIDATE}": "A completely different bullet."},
        rewrite_review_decisions={CANDIDATE: {"state": "accepted", "note": ""}},
    )
    assert derived[CANDIDATE]["state"] == "edited_after_accept"


def test_accepted_with_unchanged_text_remains_accepted():
    from src.app import services

    derived = services._derive_workspace_rewrite_review_decisions(
        _surfaced_payload(),
        selected_candidate_ids=[CANDIDATE],
        manual_bullet_edits={f"candidate:{CANDIDATE}": FINAL_TEXT},
        rewrite_review_decisions={CANDIDATE: {"state": "accepted", "note": ""}},
    )
    assert derived[CANDIDATE]["state"] == "accepted"


def test_accepted_with_no_manual_edit_remains_accepted():
    """No manual edit present at all -- the mechanism is driven by text divergence."""
    from src.app import services

    derived = services._derive_workspace_rewrite_review_decisions(
        _surfaced_payload(),
        selected_candidate_ids=[CANDIDATE],
        manual_bullet_edits={},
        rewrite_review_decisions={CANDIDATE: {"state": "accepted", "note": ""}},
    )
    assert derived[CANDIDATE]["state"] == "accepted"


def test_rejected_does_not_become_edited_after_accept(workspace):
    """A rejected candidate must stay rejected even if manual text diverges."""
    from src.app import services

    derived = services._derive_workspace_rewrite_review_decisions(
        _surfaced_payload(),
        selected_candidate_ids=[CANDIDATE],
        manual_bullet_edits={f"candidate:{CANDIDATE}": "A completely different bullet."},
        rewrite_review_decisions={CANDIDATE: {"state": "rejected", "note": ""}},
    )
    assert derived[CANDIDATE]["state"] == "rejected"


def test_pending_behavior_is_unaffected_by_manual_edits():
    """No prior decision recorded -- state stays pending regardless of edits."""
    from src.app import services

    derived = services._derive_workspace_rewrite_review_decisions(
        _surfaced_payload(),
        selected_candidate_ids=[CANDIDATE],
        manual_bullet_edits={f"candidate:{CANDIDATE}": "A completely different bullet."},
        rewrite_review_decisions={},
    )
    assert derived[CANDIDATE]["state"] == "pending"


def test_edited_after_accept_itself_stays_edited_after_accept_when_still_diverging():
    """A candidate already in edited_after_accept re-evaluates the same way as accepted."""
    from src.app import services

    derived = services._derive_workspace_rewrite_review_decisions(
        _surfaced_payload(),
        selected_candidate_ids=[CANDIDATE],
        manual_bullet_edits={f"candidate:{CANDIDATE}": "Yet another different bullet."},
        rewrite_review_decisions={CANDIDATE: {"state": "edited_after_accept", "note": ""}},
    )
    assert derived[CANDIDATE]["state"] == "edited_after_accept"


def test_full_save_load_round_trip_promotes_to_edited_after_accept(workspace):
    """End-to-end proof through the real save/load path, not just the pure function."""
    from src.app import services

    services.save_tailoring_workspace_draft_payload(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
        selected_patch_candidate_ids=["c1"],
        manual_bullet_edits={"candidate:c1": "A completely different bullet."},
        rewrite_review_decisions={"c1": {"state": "accepted", "note": ""}},
    )

    result = services.load_tailoring_workspace_draft_payload(
        output_dir=workspace["output_dir"],
        tailoring_json_path=str(workspace["artifact_path"]),
        selected_resume="resume.pdf",
    )
    assert result["draft_status"] == "saved"
    assert result["draft"]["rewrite_review_decisions"]["c1"]["state"] == "edited_after_accept"


# =============================================================================
# Dead-alias boundary: bare tailoring_status must not gain a test-implied contract
# =============================================================================

def test_bare_tailoring_status_still_has_no_producer():
    """Guard against accidentally treating the dead alias as a live contract.

    4E proved no current code path writes a bare "tailoring_status" key. This
    test only reconfirms that absence; it must never be extended to assert
    tailoring_status drives behavior.
    """
    src = Path("src/app/services.py").read_text(encoding="utf-8")
    import re

    assert not re.search(r'"tailoring_status":\s*"', src)
