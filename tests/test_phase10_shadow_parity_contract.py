from __future__ import annotations

import math

import pytest

from src.agents.evidence_chain_shadow_parity import compare_shadow_parity


def _compare(fields, **kwargs):
    return compare_shadow_parity(
        pipeline_run_id="run-1",
        job_id="job-1",
        selected_resume_id="resume-1",
        fields=fields,
        **kwargs,
    )


def test_complete_exact_match_and_mismatch():
    matched = _compare(
        [{"field": "recommendation", "mode": "exact",
          "authoritative_value": "review", "shadow_value": "review"}]
    )
    assert matched["contract_version"] == "evidence-chain-shadow-parity-v1"
    assert matched["overall_classification"] == "match"
    assert matched["match_count"] == 1

    mismatched = _compare(
        [{"field": "job_id", "mode": "exact",
          "authoritative_value": "a", "shadow_value": "b"}]
    )
    assert mismatched["overall_classification"] == "mismatch"
    assert mismatched["mismatch_count"] == 1


def test_ordered_and_set_comparisons():
    result = _compare(
        [
            {"field": "node_order", "mode": "ordered",
             "authoritative_value": ["a", "b"], "shadow_value": ["a", "b"]},
            {"field": "job_order", "mode": "ordered",
             "authoritative_value": ["a", "b"], "shadow_value": ["b", "a"]},
            {"field": "warnings", "mode": "set",
             "authoritative_value": ["a", "b"], "shadow_value": ["b", "a"]},
            {"field": "reasons", "mode": "set",
             "authoritative_value": ["a"], "shadow_value": ["b"]},
        ]
    )
    assert [row["status"] for row in result["field_results"]] == [
        "mismatch", "match", "mismatch", "match"
    ]
    assert result["overall_classification"] == "mismatch"


def test_numeric_tolerance_and_zero_behavior():
    result = _compare(
        [
            {"field": "inside", "mode": "numeric",
             "authoritative_value": 10.0, "shadow_value": 10.05,
             "absolute_tolerance": 0.1},
            {"field": "outside", "mode": "numeric",
             "authoritative_value": 10.0, "shadow_value": 10.2,
             "absolute_tolerance": 0.1},
            {"field": "zero", "mode": "numeric",
             "authoritative_value": 0.0, "shadow_value": 0.0,
             "absolute_tolerance": 0.0, "relative_tolerance": 0.0},
        ]
    )
    by_field = {row["field"]: row for row in result["field_results"]}
    assert by_field["inside"]["status"] == "match"
    assert by_field["outside"]["status"] == "mismatch"
    assert by_field["zero"]["status"] == "match"
    assert by_field["inside"]["delta"] == pytest.approx(0.05)


def test_numeric_rejects_booleans_nan_and_infinity():
    result = _compare(
        [
            {"field": "bool", "mode": "numeric",
             "authoritative_value": True, "shadow_value": 1},
            {"field": "nan", "mode": "numeric",
             "authoritative_value": math.nan, "shadow_value": 1},
            {"field": "inf", "mode": "numeric",
             "authoritative_value": math.inf, "shadow_value": 1},
        ]
    )
    assert result["malformed_count"] == 3
    assert result["overall_classification"] == "malformed"


def test_missing_and_intentionally_incomparable():
    result = _compare(
        [
            {"field": "a", "mode": "exact", "shadow_value": "x"},
            {"field": "b", "mode": "exact", "authoritative_value": "x"},
            {"field": "finalization", "mode": "incomparable",
             "reason": "shadow_stops_at_operator_review"},
        ]
    )
    assert result["missing_count"] == 2
    assert result["intentionally_incomparable_count"] == 1
    assert result["overall_classification"] == "incomplete"


def test_canonical_digest_match_and_mismatch_without_payload_exposure():
    secret = {"resume": "sensitive resume body", "score": 1}
    result = _compare(
        [
            {"field": "same", "mode": "digest",
             "authoritative_value": secret, "shadow_value": dict(secret)},
            {"field": "different", "mode": "digest",
             "authoritative_value": secret, "shadow_value": {"score": 2}},
        ]
    )
    by_field = {row["field"]: row for row in result["field_results"]}
    assert by_field["same"]["status"] == "match"
    assert by_field["different"]["status"] == "mismatch"
    assert "sensitive resume body" not in repr(result)
    assert "authoritative_value" not in by_field["same"]


def test_deterministic_order_counts_and_bounded_warnings():
    fields = [
        {"field": "z", "mode": "exact", "authoritative_value": 1, "shadow_value": 1},
        {"field": "a", "mode": "exact", "authoritative_value": 1, "shadow_value": 2},
    ]
    first = _compare(fields, warnings=["z", "a", "a"])
    second = _compare(list(reversed(fields)), warnings=["a", "z"])
    assert first == second
    assert [row["field"] for row in first["field_results"]] == ["a", "z"]
    assert first["warnings"] == ["a", "z"]


def test_sensitive_warning_and_reason_text_are_redacted():
    result = _compare(
        [{"field": "finalization", "mode": "incomparable",
          "reason": "full resume content must not escape"}],
        warnings=["full job description must not escape"],
    )
    assert result["warnings"] == ["warning_redacted"]
    assert result["field_results"][0]["reason"] == "intentionally_incomparable"
    assert "must not escape" not in repr(result)


def test_malformed_mode_and_value_are_stable():
    result = _compare(
        [
            {"field": "bad-mode", "mode": "semantic",
             "authoritative_value": "a", "shadow_value": "a"},
            {"field": "bad-set", "mode": "set",
             "authoritative_value": {"a": 1}, "shadow_value": ["a"]},
        ]
    )
    assert result["malformed_count"] == 2
    assert result["overall_classification"] == "malformed"
