from __future__ import annotations

from pathlib import Path

from tests.support.phase_guard_registry import (
    assert_changed_files_allowed,
    get_changed_files,
    legacy_guard_allowlist,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATHS = (
    "README.md",
    "docs/architecture_summary.md",
    "docs/agentic_platform.md",
    "docs/full_fledged_agentic_ai_app_roadmap.md",
    "docs/portfolio_overview.md",
    "docs/demo_walkthrough.md",
    "docs/portfolio_demo_readiness_wrap_checkpoint.md",
)


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _all_docs() -> str:
    return "\n".join(_text(path) for path in DOC_PATHS)


def test_docs_describe_always_on_weighted_local_semantic_alignment():
    readme = _text("README.md")
    architecture = _text("docs/architecture_summary.md")
    portfolio = _text("docs/portfolio_overview.md")

    for text in (readme, architecture, portfolio):
        assert "semantic_alignment" in text
        assert "0.05" in text
        assert "deterministic" in text.lower()
        assert "token-cosine" in text.lower()
        assert "final_score" in text
    assert "always-on" in readme
    assert "weighted score is included in `final_score`" in readme


def test_docs_exclude_external_ai_from_final_scoring():
    readme = _text("README.md")
    platform = _text("docs/agentic_platform.md")
    portfolio = _text("docs/portfolio_overview.md")

    for term in ("provider", "Groq", "LLM", "RAG", "embedding", "vector"):
        assert term.lower() in readme.lower()
        assert term.lower() in platform.lower()
    assert "not part of final scoring" in portfolio
    assert "does not calculate `final_score`" in _text(
        "docs/full_fledged_agentic_ai_app_roadmap.md"
    )


def test_clearance_is_documented_as_diagnostic_without_cap_or_penalty():
    text = _all_docs()

    assert "TS/Top Secret clearance" in text
    assert "diagnostic-only" in text
    assert "no cap or penalty" in text
    assert "do not cap, penalize, or reorder scores" in text


def test_llm_adjudicator_is_default_off_readback_only_and_non_mutating():
    text = _all_docs().lower()

    assert "default-off" in text
    assert "readback-only" in text
    for protected_term in (
        "winner",
        "resolved resume",
        "final score",
        "ranking",
        "queue",
        "action",
    ):
        assert protected_term in text
    assert "cannot override" in text


def test_planning_ui_is_documented_as_display_only_without_provider_trigger():
    architecture = _text("docs/architecture_summary.md")
    demo = _text("docs/demo_walkthrough.md")

    assert "existing Planning row fields" in architecture
    assert "without invoking adjudication or calling a provider" in architecture
    assert "Planning displays that existing selector readback" in demo
    assert "does not call a provider" in demo


def test_docs_preserve_human_control_and_no_application_automation_claims():
    text = _all_docs().lower()

    for term in (
        "no auto-apply",
        "ats submission",
        "recruiter messaging",
        "source-resume overwrite",
    ):
        assert term in text
    assert "human-in-the-loop" in text


def test_phase125b_guard_profile_is_docs_and_tests_only():
    allowed = legacy_guard_allowlist("hybrid_scoring_readiness_docs_wrap")

    assert set(DOC_PATHS) <= allowed
    assert "tests/test_phase125b_hybrid_scoring_readiness_docs.py" in allowed
    assert not {path for path in allowed if path.startswith("src/")}
    assert_changed_files_allowed(
        get_changed_files(ROOT),
        set(),
        legacy_guard_profiles=("hybrid_scoring_readiness_docs_wrap",),
    )
