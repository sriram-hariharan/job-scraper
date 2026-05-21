import pytest

from batch_select_best_resume_variant import (
    _normalize_llm_adjudication_parsed,
    _normalize_llm_fallback_parsed,
)


def test_normalize_llm_fallback_parsed_handles_non_string_allowed_names():
    parsed = {
        "best_resume": "123",
        "best_score": 0.8,
        "backup_resume": "backend.pdf",
        "backup_score": 0.4,
        "reason": "Best available option.",
    }

    normalized = _normalize_llm_fallback_parsed(
        parsed,
        [" backend.pdf ", 123, None, ""],
    )

    assert normalized["best_resume"] == "123"
    assert normalized["backup_resume"] == "backend.pdf"
    assert normalized["best_score"] == 0.8
    assert normalized["backup_score"] == 0.4


def test_normalize_llm_adjudication_parsed_handles_non_string_allowed_names():
    parsed = {
        "adjudicated_resume": "456",
        "confidence": "medium",
        "reason": "Slightly better evidence.",
    }

    normalized = _normalize_llm_adjudication_parsed(
        parsed,
        [" frontend.pdf ", 456, None, ""],
    )

    assert normalized["adjudicated_resume"] == "456"
    assert normalized["confidence"] == "medium"


def test_normalize_llm_fallback_parsed_invalid_selected_resume_still_raises():
    parsed = {
        "best_resume": "not-allowed.pdf",
        "best_score": 0.8,
        "backup_resume": "",
        "backup_score": 0.0,
        "reason": "Invalid choice.",
    }

    with pytest.raises(ValueError, match="invalid best_resume"):
        _normalize_llm_fallback_parsed(parsed, ["allowed.pdf", 123, None, ""])


def test_normalize_llm_adjudication_parsed_invalid_selected_resume_still_raises():
    parsed = {
        "adjudicated_resume": "not-allowed.pdf",
        "confidence": "high",
        "reason": "Invalid choice.",
    }

    with pytest.raises(ValueError, match="invalid adjudicated_resume"):
        _normalize_llm_adjudication_parsed(parsed, ["allowed.pdf", 456, None, ""])
