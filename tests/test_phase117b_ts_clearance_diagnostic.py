from src.matching.clearance_requirements import (
    active_ts_clearance_diagnostic,
    has_active_ts_clearance_evidence,
    requires_active_ts_clearance,
)


def test_active_ts_required_and_resume_lacks_evidence_emits_diagnostic():
    diagnostic = active_ts_clearance_diagnostic(
        "Applied AI Engineer. Active TS clearance required for this role.",
        "Built RAG, evaluation workflows, and agentic AI systems.",
    )

    assert diagnostic == {
        "code": "missing_active_ts_clearance",
        "severity": "hard_requirement_gap",
        "requirement": "active_ts_clearance",
        "message": "Active TS clearance is required but was not found in this resume.",
        "score_cap_applied": False,
    }


def test_ts_sci_required_and_resume_lacks_evidence_emits_diagnostic():
    diagnostic = active_ts_clearance_diagnostic(
        "Must have an active TS/SCI for customer deployment work.",
        "Python, FastAPI, LangGraph, LlamaIndex, and RAG systems.",
    )

    assert diagnostic is not None
    assert diagnostic["code"] == "missing_active_ts_clearance"
    assert diagnostic["score_cap_applied"] is False


def test_active_ts_required_and_resume_has_active_ts_returns_no_diagnostic():
    diagnostic = active_ts_clearance_diagnostic(
        "Current Top Secret clearance required.",
        "Holds current Top Secret clearance. Built applied AI platforms.",
    )

    assert diagnostic is None


def test_ts_sci_required_and_resume_has_ts_sci_returns_no_diagnostic():
    diagnostic = active_ts_clearance_diagnostic(
        "TS/SCI required for this Applied AI Engineer role.",
        "TS/SCI. Designed RAG, evaluation workflows, and AI guardrails.",
    )

    assert diagnostic is None


def test_ability_to_obtain_clearance_does_not_trigger_active_ts_requirement():
    assert not requires_active_ts_clearance(
        "Candidates must have the ability to obtain and maintain a clearance."
    )
    assert (
        active_ts_clearance_diagnostic(
            "Ability to obtain Top Secret clearance after hire.",
            "Applied AI engineer with RAG experience.",
        )
        is None
    )


def test_us_citizenship_required_does_not_trigger_active_ts_requirement():
    assert (
        active_ts_clearance_diagnostic(
            "US citizenship required. Build GenAI systems for public-sector clients.",
            "US citizen. Built GenAI systems.",
        )
        is None
    )


def test_secret_clearance_without_top_secret_does_not_trigger_active_ts_diagnostic():
    assert (
        active_ts_clearance_diagnostic(
            "Secret clearance required for this federal engineering role.",
            "No clearance listed.",
        )
        is None
    )


def test_generic_data_scientist_job_does_not_trigger_clearance_diagnostic():
    assert (
        active_ts_clearance_diagnostic(
            "Data Scientist needed for experimentation, forecasting, SQL, and Python.",
            "General Data Scientist with SQL, Python, and statistics.",
        )
        is None
    )


def test_resume_evidence_requires_explicit_active_or_current_ts_signal():
    assert has_active_ts_clearance_evidence("Active TS clearance. Python and RAG.")
    assert has_active_ts_clearance_evidence("TS/SCI. Built AI systems.")
    assert not has_active_ts_clearance_evidence("Defense client and government project.")
    assert not has_active_ts_clearance_evidence("Public trust and US citizenship.")


def test_diagnostic_helper_is_deterministic_and_has_no_provider_dependency():
    args = (
        "Must possess active Top Secret clearance.",
        "Built applied AI systems with evaluation workflows.",
    )

    assert active_ts_clearance_diagnostic(*args) == active_ts_clearance_diagnostic(*args)
