"""Item 4D: generate_llm_tailoring / refresh_llm_tailoring contract audit.

4A flagged that the planning.js helper default (generateLlmTailoring=false)
differs from one call site (=true). Tracing every caller proves this is an
INTENTIONAL, cost-aware design, not a bug:

  false = deterministic tailoring only (no LLM spend) -- the safe default
          used by passive/default paths ("Select" button, helper default,
          missing API field).
  true  = explicit LLM tailoring generation, sent ONLY from clearly labeled
          user-initiated actions ("Regenerate Suggestions" button,
          "Generate LLM tailoring" button, "Generate Suggestions" queue
          action).

No runtime behavior is changed in this step. These tests close the coverage
gap: no existing test asserted the actual --use-llm / --refresh-llm-cache
subprocess-command semantics, or that a passive workspace load never
triggers LLM generation.
"""
import csv
from pathlib import Path

import pytest


ROW = {
    "job_doc_id": "job-1",
    "job_url": "https://example.test/job-1",
    "job_company": "Acme",
    "job_title": "Engineer",
    "action": "apply",
    "queue_rank": "1",
    "needs_variant_review": "",
    "missing_requirement_count": "",
    "queue_priority_reason": "",
    "winner_resume": "resume_a.pdf",
    "winner_score": "0.9",
    "runner_up_resume": "resume_b.pdf",
    "runner_up_score": "0.5",
    "score_gap": "0.4",
    "is_tie": "",
    "operator_selected_resume": "resume_a.pdf",
}


@pytest.fixture
def regen_env(tmp_path, monkeypatch):
    """Minimal deterministic environment for regenerate_selected_resume_tailoring_payload.

    Stubs only the heavy I/O boundaries (job index building, subprocess
    execution, LLM status readback) so the test exercises the actual
    generate/refresh conditional logic in services.py, not tailoring
    internals or real subprocesses.
    """
    from src.app import services
    import job_app

    output_dir = tmp_path / "application_planning"
    output_dir.mkdir(parents=True)
    manifest_path = output_dir / "job_packet_manifest.csv"
    manifest_fieldnames = [
        "job_doc_id", "job_company", "job_title", "action", "queue_rank",
        "needs_variant_review", "missing_requirement_count", "queue_priority_reason",
        "winner_resume", "winner_score", "runner_up_resume", "runner_up_score",
        "score_gap", "is_tie", "packet_status", "packet_json", "tailoring_json",
        "tailoring_md", "tailoring_llm_json", "llm_tailoring_status", "llm_cache_hit",
        "llm_parse_ok", "llm_provider", "llm_model", "llm_error_type",
        "llm_retryable", "llm_retry_used",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=manifest_fieldnames).writeheader()

    monkeypatch.setattr(job_app, "_build_job_index", lambda _output_dir: [dict(ROW)])
    monkeypatch.setattr(
        services, "_resolve_job_index_for_regeneration",
        lambda *_a, **_k: tmp_path / "job_index.json",
    )

    captured_cmds = []

    def fake_run(cmd, *, env=None, stage=""):
        captured_cmds.append({"stage": stage, "cmd": list(cmd)})

    monkeypatch.setattr(services, "_run_selected_resume_regeneration_cmd", fake_run)
    monkeypatch.setattr(
        services, "_read_regenerated_llm_status",
        lambda _path: {
            "llm_tailoring_status": "generated", "llm_cache_hit": "false",
            "llm_parse_ok": "true", "llm_provider": "test", "llm_model": "test",
            "llm_error_type": "", "llm_retryable": "", "llm_retry_used": "",
        },
    )

    return {"output_dir": output_dir, "job_corpus": tmp_path / "corpus.jsonl", "cmds": captured_cmds}


def _tailoring_cmd(cmds):
    matches = [c["cmd"] for c in cmds if c["stage"] == "tailoring_generation"]
    assert len(matches) == 1, cmds
    return matches[0]


def _regenerate(regen_env, *, generate, refresh):
    from src.app import services

    return services.regenerate_selected_resume_tailoring_payload(
        output_dir=regen_env["output_dir"],
        job_corpus=regen_env["job_corpus"],
        job_doc_id="job-1",
        selected_resume="resume_a.pdf",
        generate_llm_tailoring=generate,
        refresh_llm_tailoring=refresh,
    )


# --- backend truth table --------------------------------------------------------

def test_generate_false_never_invokes_llm(regen_env):
    """The safe, cost-free default: deterministic tailoring only."""
    result = _regenerate(regen_env, generate=False, refresh=False)
    cmd = _tailoring_cmd(regen_env["cmds"])
    assert "--use-llm" not in cmd
    assert "--refresh-llm-cache" not in cmd
    assert result["llm_tailoring_status"] == "disabled"
    assert result["tailoring_llm_json"] == ""


def test_generate_true_invokes_llm(regen_env):
    result = _regenerate(regen_env, generate=True, refresh=False)
    cmd = _tailoring_cmd(regen_env["cmds"])
    assert "--use-llm" in cmd
    assert "--output-llm-json" in cmd
    assert result["llm_tailoring_status"] == "generated"
    assert result["tailoring_llm_json"]


def test_refresh_true_with_generate_true_bypasses_cache(regen_env):
    _regenerate(regen_env, generate=True, refresh=True)
    cmd = _tailoring_cmd(regen_env["cmds"])
    assert "--use-llm" in cmd
    assert "--refresh-llm-cache" in cmd


def test_refresh_true_with_generate_false_has_no_effect(regen_env):
    """refresh_llm_tailoring is only meaningful when generate is also true.

    It must never itself trigger an LLM call, and it silently has no effect
    on the deterministic-only path -- it does not raise or change behavior.
    """
    result = _regenerate(regen_env, generate=False, refresh=True)
    cmd = _tailoring_cmd(regen_env["cmds"])
    assert "--use-llm" not in cmd
    assert "--refresh-llm-cache" not in cmd
    assert result["llm_tailoring_status"] == "disabled"


def test_missing_field_backend_default_matches_explicit_false(regen_env):
    """Service default (generate_llm_tailoring: bool = False) is the safe default."""
    import inspect
    from src.app import services

    sig = inspect.signature(services.regenerate_selected_resume_tailoring_payload)
    assert sig.parameters["generate_llm_tailoring"].default is False
    assert sig.parameters["refresh_llm_tailoring"].default is False


def test_api_missing_field_defaults_to_false():
    """payload.get("generate_llm_tailoring", False) -- missing field never spends LLM."""
    src = Path("src/app/api.py").read_text(encoding="utf-8")
    assert 'generate_llm_tailoring=bool(payload.get("generate_llm_tailoring", False))' in src


# --- frontend caller intent -------------------------------------------------------

def test_helper_default_is_the_safe_no_llm_default():
    js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    assert "generateLlmTailoring = false," in js  # regenerateSelectedResumeChoice default


def test_regenerate_button_explicitly_opts_into_llm_and_refresh():
    """Clicking 'Regenerate Suggestions' is a deliberate, cost-aware override."""
    js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    assert "generateLlmTailoring: true," in js
    assert "refreshLlmTailoring: true," in js


def test_resume_choice_modal_offers_two_distinct_labeled_actions():
    """'Select' (no LLM) vs 'Generate LLM tailoring' -- distinct buttons, distinct intent."""
    js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    assert 'qs("resumeChoiceSelectBtn")' in js
    assert 'qs("resumeChoiceGenerateLlmBtn")' in js
    assert "submitResumeChoiceSelection({ generateLlmTailoring: false })" in js
    assert "submitResumeChoiceSelection({ generateLlmTailoring: true })" in js


def test_generate_suggestions_queue_action_is_explicit_and_labeled():
    js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    assert '"Generate Suggestions"' in js
    assert "generate_llm_tailoring: true," in js  # buildGenerateSuggestionsPayload


def test_workspace_passive_load_never_triggers_llm_generation():
    """Opening/reloading the tailoring workspace must not spend LLM calls."""
    js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    start = js.index("async function initTailoringWorkspacePage()")
    # Bounded scan of the load function body only.
    body = js[start:start + 6000]
    end = body.index("\nasync function ", 1)
    body = body[:end]
    for forbidden in (
        "regenerateSelectedResumeChoice(",
        "submitResumeChoiceSelection(",
        "handleGenerateSuggestionsClick(",
        "generate_llm_tailoring: true",
    ):
        assert forbidden not in body, forbidden


# --- safety: no mutation beyond the documented tailoring artifacts --------------

def test_regeneration_touches_no_application_or_queue_state():
    import inspect

    from src.app import services

    src = inspect.getsource(services.regenerate_selected_resume_tailoring_payload)
    for forbidden in (
        "record_application_action", "insert_patch_selection",
        "auto_apply", "recruiter_message", "mark_applied",
    ):
        assert forbidden not in src
