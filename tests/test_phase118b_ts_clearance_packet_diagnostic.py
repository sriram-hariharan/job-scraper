from types import SimpleNamespace

from jd_resume_diff_helper import _payload_for_json


def _result(*, resume_name: str = "AI2.pdf", score: float = 0.87):
    return SimpleNamespace(
        pair=SimpleNamespace(resume_name=resume_name),
        final_score=score,
        match_bucket="strong",
        prefilter=SimpleNamespace(matched_terms=["rag", "python"]),
        dimension_scores=[],
    )


def _resume(raw_text: str, resume_name: str = "AI2.pdf"):
    return SimpleNamespace(
        document=SimpleNamespace(
            resume_name=resume_name,
            raw_text=raw_text,
        )
    )


def _job(text: str):
    return SimpleNamespace(
        job_doc_id="job-1",
        company="Snorkel",
        title="Applied AI Engineer",
        retrieval_text=text,
        preview=text,
    )


def _packet(job_text: str, resume_text: str):
    return _payload_for_json(
        job_evidence=_job(job_text),
        selected_job_record={
            "job_doc_id": "job-1",
            "job_url": "https://jobs.example/1",
            "description_text": job_text,
        },
        selected_resume=_resume(resume_text),
        selected_result=_result(),
        runner_up_result=None,
        is_tie=False,
        matched_required=["rag", "python"],
        missing_required=["fastapi"],
        matched_preferred=["langgraph"],
        missing_preferred=["crewai"],
        summary_term_support={"rag": {"matched": True}},
        summary_facet_support=[],
        top_bullets=[],
        top_evidence_units=[],
    )


def _diagnostics(packet):
    return packet["summary"]["hard_requirement_diagnostics"]


def test_packet_summary_records_missing_active_ts_diagnostic_metadata_only():
    packet = _packet(
        "Applied AI Engineer. Active TS clearance required. Build RAG systems.",
        "Built RAG, evaluation workflows, FastAPI, and Python systems.",
    )

    assert _diagnostics(packet) == [
        {
            "code": "missing_active_ts_clearance",
            "severity": "hard_requirement_gap",
            "requirement": "active_ts_clearance",
            "message": "Active TS clearance is required but was not found in this resume.",
            "score_cap_applied": False,
        }
    ]
    assert packet["summary"]["missing_required"] == ["fastapi"]
    assert packet["selection"]["selected_resume"] == "AI2.pdf"
    assert packet["selection"]["selected_score"] == 0.87
    assert packet["selection"]["runner_up_resume"] is None


def test_packet_summary_records_ts_sci_diagnostic_when_resume_lacks_evidence():
    packet = _packet(
        "Must have an active TS/SCI for applied AI delivery.",
        "Built agentic workflows and customer-facing AI systems.",
    )

    assert _diagnostics(packet)[0]["code"] == "missing_active_ts_clearance"
    assert _diagnostics(packet)[0]["score_cap_applied"] is False


def test_packet_summary_has_empty_diagnostics_when_resume_has_active_ts():
    packet = _packet(
        "Current Top Secret clearance required.",
        "Holds current Top Secret clearance. Built Applied AI systems.",
    )

    assert _diagnostics(packet) == []


def test_packet_summary_has_empty_diagnostics_when_resume_has_ts_sci():
    packet = _packet(
        "TS/SCI required for mission deployment.",
        "TS/SCI. Built RAG and evaluation workflows.",
    )

    assert _diagnostics(packet) == []


def test_packet_summary_ignores_ability_to_obtain_clearance():
    packet = _packet(
        "Ability to obtain and maintain Top Secret clearance after hire.",
        "Built Applied AI and RAG systems.",
    )

    assert _diagnostics(packet) == []


def test_packet_summary_ignores_secret_clearance_without_ts_requirement():
    packet = _packet(
        "Secret clearance required for this federal engineering role.",
        "Built Python services.",
    )

    assert _diagnostics(packet) == []


def test_packet_summary_ignores_generic_data_scientist_jd():
    packet = _packet(
        "Data Scientist needed for experimentation, SQL, forecasting, and Python.",
        "General Data Scientist with SQL and Python.",
    )

    assert _diagnostics(packet) == []


def test_packet_diagnostic_does_not_change_score_ranking_or_missing_terms():
    packet = _packet(
        "Must possess active Top Secret clearance.",
        "Built GenAI systems with RAG and FastAPI.",
    )

    assert packet["selection"] == {
        "selected_resume": "AI2.pdf",
        "selected_score": 0.87,
        "selected_bucket": "strong",
        "runner_up_resume": None,
        "runner_up_score": None,
        "score_gap": None,
        "is_tie": False,
        "tie_epsilon": 0.01,
    }
    assert packet["summary"]["matched_required"] == ["rag", "python"]
    assert packet["summary"]["missing_required"] == ["fastapi"]
    assert packet["summary"]["missing_preferred"] == ["crewai"]


def test_packet_diagnostic_path_does_not_reference_provider_or_llm_runtime():
    import jd_resume_diff_helper

    source = jd_resume_diff_helper.Path("jd_resume_diff_helper.py").read_text(
        encoding="utf-8"
    )
    payload_builder = source.split("def _payload_for_json", 1)[1].split(
        "def _load_candidate_resume_documents", 1
    )[0]

    assert "run_chat_completion" not in payload_builder
    assert "llm_client" not in payload_builder
    assert "provider" not in payload_builder
