from __future__ import annotations

from pathlib import Path

from tests.support.phase_guard_registry import (
    assert_changed_files_allowed,
    get_changed_files,
    legacy_guard_allowlist,
)


ROOT = Path(__file__).resolve().parents[1]
WALKTHROUGH = ROOT / "docs/demo_walkthrough.md"
CHECKPOINT = ROOT / "docs/portfolio_demo_readiness_wrap_checkpoint.md"


def _walkthrough() -> str:
    return WALKTHROUGH.read_text(encoding="utf-8")


def _checkpoint() -> str:
    return CHECKPOINT.read_text(encoding="utf-8")


def test_primary_demo_is_honestly_labeled_four_to_five_minutes():
    text = _walkthrough()

    assert "4-5 minute primary portfolio demo" in text
    assert "2-3 minute" not in text
    assert "## Primary Demo Script" in text
    assert "## Optional Technical Appendix" in text


def test_primary_demo_route_is_present_in_product_order():
    text = _walkthrough()
    route = (
        "Run the live pipeline",
        "Open Planning",
        "Trigger Generate Suggestions",
        "Tailoring Workspace",
        "Open AI Optimize Scan",
        "Open Agentic Review",
    )

    positions = [text.index(step) for step in route]
    assert positions == sorted(positions)


def test_walkthrough_covers_hybrid_scoring_and_advisory_readback():
    text = _walkthrough()

    assert "`semantic_alignment`" in text
    assert "weight `0.05`" in text
    assert "AI review notes · advisory" in text
    assert "optional readback" in text
    assert "cannot override the selected resume, score, ranking, queue, or action" in text


def test_clearance_warning_is_documented_as_diagnostic_only():
    text = _walkthrough()

    assert "clearance warning is diagnostic-only" in text
    assert "does not cap or penalize the score" in text
    assert "does not change the selected resume" in text


def test_walkthrough_preserves_permanent_human_control_boundaries():
    text = _walkthrough().lower()

    for marker in (
        "never auto-applies",
        "submits to an ats",
        "messages recruiters",
        "overwrites source resumes",
        "final application action remains manual",
    ):
        assert marker in text


def test_checkpoint_records_phase127_freeze_and_database_verification():
    text = _checkpoint()

    assert "## Phase 127 demo freeze checkpoint" in text
    assert "4-5 minute primary demo route" in text
    assert "feature work is frozen for the portfolio demo" in text
    assert "configured `DATABASE_URL`" in text
    assert "final application action remains manual and human-controlled" in text


def test_phase127b_guard_profile_is_docs_and_tests_only():
    allowed = legacy_guard_allowlist("portfolio_demo_freeze_checkpoint")

    assert {
        "docs/demo_walkthrough.md",
        "docs/portfolio_demo_readiness_wrap_checkpoint.md",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "tests/test_phase127b_portfolio_demo_freeze_checkpoint.py",
    } <= allowed
    assert not {path for path in allowed if path.startswith("src/")}
    assert_changed_files_allowed(
        get_changed_files(ROOT),
        {
            "src/app/auth_ui.py",
            "src/app/ui.py",
            "src/app/planning_ui.py",
            "src/app/static/app.js",
            "src/app/static/planning.js",
            "src/app/static/styles.css",
            "tests/test_phase109b_live_pipeline_popup_ux_static_only.py",
            "tests/test_phase110b_generate_suggestions_loader_static_only.py",
            "tests/test_phase127b_portfolio_demo_freeze_checkpoint.py",
            "tests/test_phase129b_auth_and_loader_overlay_static_only.py",
        },
        legacy_guard_profiles=("portfolio_demo_freeze_checkpoint",),
    )
