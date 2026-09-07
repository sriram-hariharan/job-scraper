"""P3S2 — zero-point materiality policy.

Materiality branching must work in the user-visible point unit rather than the
raw float. Any delta rounding to zero points enters the existing zero-point
policy regardless of raw sign; genuine point losses stay rejected; and the raw
delta continues to be reported for telemetry.

These tests drive the real ``_materiality_validate_rewrite_candidate`` branch
logic, including the real fronting predicates and the real score helpers. Only
the scoring inputs are controlled, so the policy under test executes unmodified.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import pytest

from src.tailoring import rendering
from src.tailoring.replacement_selector import _is_direct_apply_ready
from src.tailoring.score_utils import score_delta_to_points


ORIGINAL_SCORE = 0.775812


class _Result:
    def __init__(self, final_score: float) -> None:
        self.final_score = final_score
        self.dimension_scores: Dict[str, float] = {}


def _context() -> Dict[str, Any]:
    return {
        "ok": True,
        "original_resume": object(),
        "job_evidence": object(),
        "original_result": _Result(ORIGINAL_SCORE),
    }


def _candidate(
    method: str,
    *,
    supported: Tuple[str, ...] = ("python", "sql"),
    **extra: Any,
) -> Dict[str, Any]:
    candidate: Dict[str, Any] = {
        "candidate_id": "replacement_1",
        "operation_type": "rewrite",
        "proposal_status": "patch_ready",
        "patch_text": "Identified key features using Python and SQL, reporting findings to Finance.",
        "patch_generation_method": method,
        "supported_jd_signals": list(supported),
        "claim_safety": "safe_strengthen",
        "confidence": "high",
        "evidence_type": "direct_overlap",
        "counterfactual_status": "scored",
    }
    candidate.update(extra)
    return candidate


@pytest.fixture
def run_materiality(monkeypatch):
    """Execute the real materiality policy against a controlled score delta."""

    def _run(
        candidate: Dict[str, Any],
        delta: float,
        *,
        evidence_changed: bool = False,
        evidence_delta: Dict[str, Dict[str, list]] | None = None,
    ):
        monkeypatch.setattr(
            rendering,
            "_patched_resume_evidence_for_candidate",
            lambda resume, cand: (object(), "ok"),
        )
        monkeypatch.setattr(
            rendering,
            "score_resume_job_match",
            lambda resume, job: _Result(round(ORIGINAL_SCORE + delta, 6)),
        )
        monkeypatch.setattr(
            rendering, "_resume_counterfactual_snapshot", lambda resume: {}
        )
        # The real diagnostics derive gains/regressions from this delta, so the
        # test supplies it rather than pre-setting the derived fields.
        resolved_delta = (
            evidence_delta
            if evidence_delta is not None
            else ({"explicit_skills": {"added": ["sql"], "removed": []}} if evidence_changed else {})
        )
        monkeypatch.setattr(
            rendering, "_counterfactual_snapshot_delta", lambda a, b: resolved_delta
        )
        monkeypatch.setattr(rendering, "_nonzero_dimension_deltas", lambda a, b: {})
        return rendering._materiality_validate_rewrite_candidate(
            {}, candidate, _context()
        )

    return _run


# --- Case 1: exact zero, fronting rewrite (unchanged baseline) ---------------


def test_exact_zero_fronting_rewrite_is_export_safe_no_score_lift(run_materiality):
    result = run_materiality(_candidate("llm_substantive_multisignal_reframe"), 0.0)

    assert result["materiality_validation_status"] == "export_safe_no_score_lift"
    assert result["proposal_status"] == "patch_ready"
    assert result["material_delta_found"] is False
    assert result["patch_text"]
    assert _is_direct_apply_ready(result) is False


# --- Case 2: tiny-negative zero-point, Stripe Case-A shape ------------------


def test_tiny_negative_zero_point_enters_zero_point_policy(run_materiality):
    result = run_materiality(
        _candidate("deterministic_based_modifier_head", supported=("forecasting",)),
        -0.000043,
    )

    # Raw telemetry preserved.
    assert result["precheck_projected_overall_delta"] == -4.3e-05
    # Zero-point policy applied instead of raw-sign rejection.
    assert result["materiality_validation_status"] == "export_safe_no_score_lift"
    assert result["proposal_status"] == "patch_ready"
    assert result["patch_text"]
    assert _is_direct_apply_ready(result) is False


# --- Case 3: tiny-positive zero-point ---------------------------------------


def test_tiny_positive_zero_point_is_not_material_candidate(run_materiality):
    result = run_materiality(
        _candidate("deterministic_based_modifier_head"), 0.000043
    )

    assert result["precheck_projected_overall_delta"] == 4.3e-05
    assert result["materiality_validation_status"] == "export_safe_no_score_lift"
    assert result["materiality_validation_status"] != "material_candidate"
    assert _is_direct_apply_ready(result) is False


# --- Case 4: rounding boundary ----------------------------------------------


def test_point_mapping_boundaries_are_pinned():
    # Python round-half-to-even: +/-0.005 maps to zero points.
    assert score_delta_to_points(-0.005) == 0
    assert score_delta_to_points(-0.00501) == -1
    assert score_delta_to_points(0.005) == 0
    assert score_delta_to_points(0.00501) == 1


def test_negative_boundary_pair_routes_correctly(run_materiality):
    neutral = run_materiality(
        _candidate("deterministic_based_modifier_head"), -0.005
    )
    assert neutral["materiality_validation_status"] == "export_safe_no_score_lift"
    assert neutral["proposal_status"] == "patch_ready"

    loss = run_materiality(_candidate("deterministic_based_modifier_head"), -0.00501)
    assert loss["materiality_validation_status"] == "negative_projected_score_delta"
    assert loss["proposal_status"] == "direction_only"


# --- Case 5: genuine negative point loss ------------------------------------


def test_real_point_loss_is_still_rejected(run_materiality):
    result = run_materiality(_candidate("deterministic_based_modifier_head"), -0.01)

    assert result["precheck_projected_overall_delta"] == -0.01
    assert result["materiality_validation_status"] == "negative_projected_score_delta"
    assert result["proposal_status"] == "direction_only"
    assert result["patch_ready"] is False
    assert result["material_delta_found"] is False


# --- Case 6: zero-point non-fronting rewrite --------------------------------


def test_zero_point_non_fronting_rewrite_stays_directional(run_materiality):
    result = run_materiality(_candidate("some_unrecognized_method"), -0.000043)

    assert result["materiality_validation_status"] == "scorer_neutral_no_evidence_change"
    assert result["proposal_status"] == "direction_only"
    assert result["patch_ready"] is False


# --- Case 7: zero-point with evidence change + fronting method --------------


def test_zero_point_with_evidence_change_is_material(run_materiality):
    result = run_materiality(
        _candidate("deterministic_based_modifier_head"),
        -0.000043,
        evidence_changed=True,
    )

    assert result["materiality_validation_status"] == "material_candidate"
    assert result["material_delta_found"] is True


# --- Case 8: tiny-negative live LLM concrete patch candidate ----------------


def test_tiny_negative_live_llm_reaches_neutral_llm_gate(run_materiality):
    """Previously rejected on raw sign; must now reach the neutral-LLM logic."""

    result = run_materiality(
        _candidate("live_llm_concrete_patch_candidate"), -0.000043
    )

    assert result["materiality_validation_status"] == (
        "scorer_neutral_no_supported_jd_signal_gain"
    )
    assert result["proposal_status"] == "direction_only"


def test_tiny_negative_live_llm_with_supported_gain_is_material(run_materiality):
    result = run_materiality(
        _candidate("live_llm_concrete_patch_candidate"),
        -0.000043,
        evidence_delta={"explicit_skills": {"added": ["sql"], "removed": []}},
    )

    assert result["materiality_validation_status"] == "material_candidate"
    assert result["material_delta_found"] is True


def test_tiny_negative_live_llm_with_regression_stays_directional(run_materiality):
    result = run_materiality(
        _candidate("live_llm_concrete_patch_candidate"),
        -0.000043,
        evidence_delta={"tooling_signals": {"added": [], "removed": ["tableau"]}},
    )

    assert result["materiality_validation_status"] == "scorer_neutral_evidence_regression"
    assert result["proposal_status"] == "direction_only"


# --- Case 9: genuine positive lift ------------------------------------------


def test_genuine_positive_lift_remains_material(run_materiality):
    result = run_materiality(_candidate("deterministic_based_modifier_head"), 0.02)

    assert result["precheck_projected_overall_delta"] == 0.02
    assert result["materiality_validation_status"] == "material_candidate"
    assert result["material_delta_found"] is True


# --- Case 10: app-ready invariance ------------------------------------------


@pytest.mark.parametrize("delta", [-0.000043, 0.0, 0.000043, -0.005, 0.005])
def test_zero_point_rewrites_are_never_direct_apply_ready(run_materiality, delta):
    result = run_materiality(_candidate("deterministic_based_modifier_head"), delta)

    result["projected_overall_delta"] = result["precheck_projected_overall_delta"]
    assert _is_direct_apply_ready(result) is False


# =====================================================================
# P3S7 — review visibility for zero-point export-safe rewrites
#
# The raw-sign ``score_gate`` contract is protected and unchanged: a
# tiny-negative zero-point rewrite still reports ``rejected_by_score_gate``.
# That label governs direct acceptance, not operator visibility -- a rewrite
# materiality classified as ``export_safe_no_score_lift`` with zero displayed
# points carries concrete replacement text and belongs in human review.
# Genuine point losses stay hidden.
# =====================================================================

from src.app.services import _scan_issue_from_replacement_row  # noqa: E402
from src.tailoring.replacement_selector import _score_metadata  # noqa: E402


def _scan_row(delta: float, materiality: str, *, patch_ready: bool = True,
              method: str = "deterministic_based_modifier_head") -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "candidate_id": "replacement_1",
        "operation_type": "rewrite",
        "proposal_status": "patch_ready" if patch_ready else "direction_only",
        "patch_text": "Built seasonal forecasting models on 250k+ records using ARIMA." if patch_ready else "",
        "patch_generation_method": method,
        "materiality_validation_status": materiality,
        "projected_overall_delta": delta,
        "precheck_projected_overall_delta": delta,
        "confidence": "high",
        "claim_safety": "safe_strengthen",
        "counterfactual_status": "scored",
        "supported_jd_signals": ["forecasting"],
        "apply_priority": "medium",
        "original_text": "Built ARIMA-based seasonal forecasting models on 250k+ records.",
    }
    row["final_replacement_text"] = row["patch_text"]
    row.update(_score_metadata(row))          # real selector metadata
    return row


def _scan_issue(row: Dict[str, Any]) -> Dict[str, Any]:
    return _scan_issue_from_replacement_row(
        row, lane="rewrite", group_id="g", group_label="G",
        bucket="b", bucket_label="B", can_accept=True, can_accept_all=True, index=0,
    )


# --- Case 1: Stripe tiny-negative export-safe -------------------------------


def test_tiny_negative_export_safe_rewrite_stays_review_visible():
    issue = _scan_issue(_scan_row(-0.000043, "export_safe_no_score_lift"))

    assert issue["projected_score_delta_points"] == 0
    # Protected raw-sign contract is untouched.
    assert issue["scan_issue_type"] == "rejected_by_score_gate"
    # ...but the rewrite is available for human review.
    assert issue["is_visible_in_review"] is True
    assert issue["suggested_text"]
    assert issue["scan_issue_type"] != "direct_replacement"


# --- Case 2: genuine negative point loss ------------------------------------


@pytest.mark.parametrize("delta", [-0.02, -0.01])
def test_genuine_point_losses_remain_hidden(delta):
    issue = _scan_issue(
        _scan_row(delta, "negative_projected_score_delta", patch_ready=False)
    )

    assert issue["projected_score_delta_points"] < 0
    assert issue["scan_issue_type"] == "rejected_by_score_gate"
    assert issue["is_visible_in_review"] is False


# --- Case 3: exact-zero export-safe (unchanged baseline) --------------------


def test_exact_zero_export_safe_remains_visible():
    issue = _scan_issue(_scan_row(0.0, "export_safe_no_score_lift"))

    assert issue["projected_score_delta_points"] == 0
    assert issue["is_visible_in_review"] is True
    assert issue["scan_issue_type"] != "direct_replacement"


# --- Case 4: tiny-positive export-safe --------------------------------------


def test_tiny_positive_export_safe_remains_visible():
    issue = _scan_issue(_scan_row(0.000043, "export_safe_no_score_lift"))

    assert issue["projected_score_delta_points"] == 0
    assert issue["is_visible_in_review"] is True


# --- Case 5: zero-point but NOT export-safe ---------------------------------


def test_zero_point_non_export_safe_row_is_not_unhidden():
    """The exception is tied to the materiality policy, not point neutrality."""

    issue = _scan_issue(_scan_row(-0.000043, "scorer_neutral_no_evidence_change"))

    assert issue["projected_score_delta_points"] == 0
    assert issue["scan_issue_type"] == "rejected_by_score_gate"
    assert issue["is_visible_in_review"] is False


# --- Case 6: direct-accept invariance ---------------------------------------


@pytest.mark.parametrize(
    "delta,materiality",
    [
        (-0.000043, "export_safe_no_score_lift"),
        (0.0, "export_safe_no_score_lift"),
        (0.000043, "export_safe_no_score_lift"),
        (-0.02, "negative_projected_score_delta"),
    ],
)
def test_visibility_exception_never_grants_direct_accept(delta, materiality):
    issue = _scan_issue(_scan_row(delta, materiality))

    # can_direct_accept is derived from score_gate == "direct_replacement".
    assert issue["scan_issue_type"] != "direct_replacement"


# --- Case 7: app-ready invariance -------------------------------------------


@pytest.mark.parametrize("delta", [-0.000043, 0.0, 0.000043])
def test_visibility_exception_never_grants_app_ready(delta):
    row = _scan_row(delta, "export_safe_no_score_lift")

    assert _is_direct_apply_ready(row) is False


def test_genuine_positive_lift_remains_app_ready_and_visible():
    row = _scan_row(0.04, "material_candidate")
    issue = _scan_issue(row)

    assert issue["projected_score_delta_points"] > 0
    assert issue["is_visible_in_review"] is True
    assert _is_direct_apply_ready(row) is True
