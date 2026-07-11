import ast
import json
from pathlib import Path

import pytest

from batch_select_best_resume_variant import (
    _llm_adjudicator_candidate_summary,
    _llm_adjudicator_readback_csv_fields,
)
from src.agents.llm_adjudicator_readback import (
    build_llm_adjudicator_readback,
    llm_adjudicator_readback_enabled,
)
from src.matching.models import (
    MatchDimensionScore,
    MatchPrefilterResult,
    ResumeJobMatchResult,
    ResumeJobPair,
)


HELPER_PATH = Path("src/agents/llm_adjudicator_readback.py")


def _candidate(name="AI2.pdf", score=0.91):
    return {
        "resume_name": name,
        "final_score": score,
        "match_bucket": "strong",
        "semantic_alignment": {
            "score": 0.8,
            "weight": 0.05,
            "weighted_score": 0.04,
        },
        "hard_requirement_diagnostics": [
            {"code": "missing_active_ts_clearance", "severity": "warning"}
        ],
        "top_dimensions": "semantic_alignment=0.80/0.040",
    }


def _match_result(name="AI2.pdf", score=0.91):
    return ResumeJobMatchResult(
        pair=ResumeJobPair(
            resume_id=name,
            resume_name=name,
            job_doc_id="job-1",
            job_company="Snorkel",
            job_title="Applied AI Engineer",
        ),
        prefilter=MatchPrefilterResult(
            passed=True,
            matched_terms=["rag", "agentic workflows"],
            missing_requirements=["active TS clearance"],
        ),
        dimension_scores=[
            MatchDimensionScore(
                name="semantic_alignment",
                score=0.8,
                weight=0.05,
                weighted_score=0.04,
                reason="Semantic JD/resume similarity.",
                evidence=["rag", "agentic workflows"],
            ),
            MatchDimensionScore(
                name="role_family",
                score=0.9,
                weight=0.2,
                weighted_score=0.18,
            ),
        ],
        final_score=score,
        match_bucket="strong",
    )


def test_gate_off_does_not_call_provider_and_returns_disabled_readback():
    calls = []

    def provider(payload):
        calls.append(payload)
        return {"adjudicator_summary": "Should not run."}

    readback = build_llm_adjudicator_readback(
        candidates=[_candidate()],
        provider="groq",
        model="llama-test",
        enabled=False,
        provider_callable=provider,
    )

    assert calls == []
    assert readback["enabled"] is False
    assert readback["status"] == "disabled"
    assert readback["readback_only"] is True
    assert readback["no_winner_override"] is True
    assert readback["no_score_override"] is True
    assert readback["no_queue_mutation"] is True


def test_gate_parser_accepts_only_documented_true_values(monkeypatch):
    monkeypatch.delenv("APPLYLENS_LLM_ADJUDICATOR_READBACK_ENABLED", raising=False)
    assert llm_adjudicator_readback_enabled() is False
    for value in ("1", "true", "yes", "on", " TRUE "):
        assert llm_adjudicator_readback_enabled(value) is True
    for value in ("", "0", "false", "off", "no"):
        assert llm_adjudicator_readback_enabled(value) is False


def test_gate_on_with_fake_provider_emits_readback_only_candidate_summary():
    calls = []

    def provider(payload):
        calls.append(payload)
        return json.dumps(
            {
                "adjudicator_summary": "AI2 has stronger applied AI evidence.",
                "adjudicator_recommendation_label": "AI2 remains strongest",
            }
        )

    candidates = [_candidate("AI2.pdf", 0.91), _candidate("General_DS.pdf", 0.83)]
    readback = build_llm_adjudicator_readback(
        candidates=candidates,
        provider="groq",
        model="llama-test",
        enabled=True,
        provider_callable=provider,
    )

    assert len(calls) == 1
    assert calls[0]["readback_only"] is True
    assert calls[0]["no_winner_override"] is True
    assert readback["status"] == "ok"
    assert readback["candidate_resume_names"] == ["AI2.pdf", "General_DS.pdf"]
    assert readback["candidate_scores"] == {"AI2.pdf": 0.91, "General_DS.pdf": 0.83}
    assert readback["semantic_alignment"]["AI2.pdf"]["weighted_score"] == 0.04
    assert (
        readback["hard_requirement_diagnostics"]["AI2.pdf"][0]["code"]
        == "missing_active_ts_clearance"
    )
    assert readback["adjudicator_recommendation_label"] == "AI2 remains strongest"
    assert "adjudicated_resume" not in readback
    assert "winner_resume" not in readback


def test_provider_failure_is_non_blocking_readback_error():
    def provider(payload):
        raise RuntimeError("provider unavailable")

    readback = build_llm_adjudicator_readback(
        candidates=[_candidate()],
        provider="groq",
        model="llama-test",
        enabled=True,
        provider_callable=provider,
    )

    assert readback["status"] == "provider_error"
    assert "provider unavailable" in readback["error"]
    assert readback["readback_only"] is True
    assert readback["no_winner_override"] is True


def test_malformed_provider_response_is_safe_and_non_mutating():
    readback = build_llm_adjudicator_readback(
        candidates=[_candidate()],
        provider="groq",
        model="llama-test",
        enabled=True,
        provider_callable=lambda payload: "not json",
    )

    assert readback["status"] == "malformed_response"
    assert readback["readback_only"] is True
    assert readback["no_score_override"] is True
    assert "winner_resume" not in readback


def test_selector_candidate_summary_reuses_existing_scores_and_semantic_dimension():
    summary = _llm_adjudicator_candidate_summary(_match_result())

    assert summary["resume_name"] == "AI2.pdf"
    assert summary["final_score"] == 0.91
    assert summary["match_bucket"] == "strong"
    assert summary["semantic_alignment"]["score"] == 0.8
    assert summary["semantic_alignment"]["weighted_score"] == 0.04
    assert summary["missing_requirements"] == ["active TS clearance"]


def test_selector_csv_fields_are_namespaced_and_do_not_mutate_selection_fields():
    baseline = {
        "winner_resume": "AI2.pdf",
        "runner_up_resume": "General_DS.pdf",
        "resolved_resume": "AI2.pdf",
        "winner_score": "0.910000",
        "resolved_score": "0.910000",
        "action": "manual_review",
    }
    readback = build_llm_adjudicator_readback(
        candidates=[_candidate()],
        provider="groq",
        model="llama-test",
        enabled=False,
    )
    merged = dict(baseline)
    merged.update(_llm_adjudicator_readback_csv_fields(readback))

    for key, value in baseline.items():
        assert merged[key] == value
    assert set(merged) - set(baseline) == {
        "llm_adjudicator_readback_enabled",
        "llm_adjudicator_readback_status",
        "llm_adjudicator_readback",
    }


def test_new_helper_has_no_direct_provider_or_rag_sdk_imports():
    tree = ast.parse(HELPER_PATH.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    forbidden = {
        "groq",
        "openai",
        "google.genai",
        "src.rag",
        "src.app.api",
        "src.app.services",
        "src.pipeline.collector",
        "src.tailoring.llm",
    }
    assert not (set(imports) & forbidden)
    assert Path("requirements.txt").read_text(encoding="utf-8").count("groq") == 1

