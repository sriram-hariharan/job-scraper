import re

import pytest

from src.resume.evidence_builder import (
    build_counterfactual_resume_evidence,
    build_counterfactual_resume_evidence_for_patches,
    build_resume_evidence,
)
from src.resume.models import ResumeDocument


def _build_resume(*, bullets, elsewhere=""):
    bullet_text = "\n".join(f"- {bullet}" for bullet in bullets)
    raw_text = (
        "SUMMARY\n"
        f"{elsewhere}\n"
        "EXPERIENCE\n"
        "Data Scientist at ExampleCo\n"
        "January 2020 - Present\n"
        f"{bullet_text}\n"
    )
    document = ResumeDocument(
        resume_id="counterfactual-test",
        resume_name="counterfactual-test",
        path="",
        raw_text=raw_text,
        normalized_text=re.sub(r"\s+", " ", raw_text).strip(),
    )
    resume = build_resume_evidence(document)
    assert len(resume.experience_entries) == 1
    assert resume.experience_entries[0].bullets == bullets
    return resume


def _bullet_id(resume, index):
    return resume.experience_entries[0].bullet_ids[index]


def _global_signal_snapshot(resume):
    return {
        "domain_signals": resume.domain_signals,
        "analytics_ml_signals": resume.analytics_ml_signals,
        "experimentation_signals": resume.experimentation_signals,
        "tooling_signals": resume.tooling_signals,
    }


def test_counterfactual_noop_preserves_all_document_wide_signal_families():
    bullet = "Built SQL forecasting dashboards for fintech A/B testing."
    original = _build_resume(
        bullets=[bullet],
        elsewhere="Probability & statistics with Python and Snowflake.",
    )

    rebuilt, status = build_counterfactual_resume_evidence(
        original,
        _bullet_id(original, 0),
        bullet,
    )

    assert status == "ok"
    assert rebuilt is not None
    assert _global_signal_snapshot(rebuilt) == _global_signal_snapshot(original)


def test_counterfactual_preserves_statistics_from_untouched_document_text():
    original = _build_resume(
        bullets=["Built SQL reporting dashboards."],
        elsewhere="Probability & statistics practitioner.",
    )

    rebuilt, status = build_counterfactual_resume_evidence(
        original,
        _bullet_id(original, 0),
        "Created SQL reporting dashboards.",
    )

    assert status == "ok"
    assert "statistics" in original.analytics_ml_signals
    assert "statistics" in rebuilt.analytics_ml_signals


def test_counterfactual_removes_signal_when_final_document_occurrence_is_removed():
    original = _build_resume(bullets=["Built forecasting models."])

    rebuilt, status = build_counterfactual_resume_evidence(
        original,
        _bullet_id(original, 0),
        "Built reporting dashboards.",
    )

    assert status == "ok"
    assert "forecasting" in original.analytics_ml_signals
    assert "forecasting" not in rebuilt.analytics_ml_signals


def test_counterfactual_adds_document_wide_signal_from_replacement_text():
    original = _build_resume(bullets=["Built reporting dashboards."])

    rebuilt, status = build_counterfactual_resume_evidence(
        original,
        _bullet_id(original, 0),
        "Built TensorFlow reporting dashboards.",
    )

    assert status == "ok"
    assert "tensorflow" not in original.tooling_signals
    assert "tensorflow" in rebuilt.tooling_signals


def test_counterfactual_preserves_unrelated_global_families_elsewhere():
    original = _build_resume(
        bullets=["Built SQL reporting dashboards."],
        elsewhere="Fintech A/B testing with Snowflake and statistical analysis.",
    )

    rebuilt, status = build_counterfactual_resume_evidence(
        original,
        _bullet_id(original, 0),
        "Created SQL reporting dashboards.",
    )

    assert status == "ok"
    assert _global_signal_snapshot(rebuilt) == _global_signal_snapshot(original)


def test_multi_patch_uses_progressively_patched_full_document():
    original = _build_resume(
        bullets=[
            "Built SQL reporting dashboards.",
            "Developed forecasting models.",
        ],
        elsewhere="Fintech A/B testing with Snowflake.",
    )

    rebuilt, status = build_counterfactual_resume_evidence_for_patches(
        original,
        [
            {
                "source_bullet_id": _bullet_id(original, 0),
                "patch_text": "Built TensorFlow reporting dashboards.",
            },
            {
                "source_bullet_id": _bullet_id(original, 1),
                "patch_text": "Developed classification models.",
            },
        ],
    )

    assert status == "ok"
    assert "sql" not in rebuilt.tooling_signals
    assert "tensorflow" in rebuilt.tooling_signals
    assert "snowflake" in rebuilt.tooling_signals
    assert "forecasting" not in rebuilt.analytics_ml_signals
    assert "classification" in rebuilt.analytics_ml_signals
    assert rebuilt.domain_signals == original.domain_signals
    assert rebuilt.experimentation_signals == original.experimentation_signals


@pytest.mark.parametrize(
    ("patches", "expected_status"),
    [
        ([], "missing_patch_inputs"),
        ([{"source_bullet_id": "", "patch_text": "Replacement."}], "missing_patch_inputs"),
        ([{"source_bullet_id": "missing", "patch_text": "Replacement."}], "bullet_id_not_found"),
    ],
)
def test_counterfactual_preserves_basic_patch_failure_contracts(
    patches,
    expected_status,
):
    original = _build_resume(bullets=["Built SQL reporting dashboards."])

    rebuilt, status = build_counterfactual_resume_evidence_for_patches(original, patches)

    assert rebuilt is None
    assert status == expected_status


def test_counterfactual_rejects_duplicate_patch_bullet_id():
    original = _build_resume(bullets=["Built SQL reporting dashboards."])
    bullet_id = _bullet_id(original, 0)

    rebuilt, status = build_counterfactual_resume_evidence_for_patches(
        original,
        [
            {"source_bullet_id": bullet_id, "patch_text": "Created SQL dashboards."},
            {"source_bullet_id": bullet_id, "patch_text": "Designed SQL dashboards."},
        ],
    )

    assert rebuilt is None
    assert status == "duplicate_patch_bullet_id"


def test_counterfactual_preserves_bullet_id_uniqueness_and_index_failures():
    original = _build_resume(
        bullets=["Built SQL reporting dashboards.", "Created Python automation."],
    )
    duplicate_id = _bullet_id(original, 0)
    original.experience_entries[0].bullet_ids[1] = duplicate_id

    rebuilt, status = build_counterfactual_resume_evidence_for_patches(
        original,
        [{"source_bullet_id": duplicate_id, "patch_text": "Replacement."}],
    )
    assert rebuilt is None
    assert status == "bullet_id_not_unique"

    original = _build_resume(bullets=["Built SQL reporting dashboards."])
    original.experience_entries[0].bullet_ids.append("out-of-range")
    rebuilt, status = build_counterfactual_resume_evidence_for_patches(
        original,
        [{"source_bullet_id": "out-of-range", "patch_text": "Replacement."}],
    )
    assert rebuilt is None
    assert status == "bullet_index_out_of_range"


@pytest.mark.parametrize(
    ("source_raw_text", "expected_status"),
    [
        ("Absent bullet.", "raw_text_bullet_not_found"),
        ("Repeated SQL bullet.", "raw_text_bullet_not_unique"),
    ],
)
def test_counterfactual_preserves_raw_text_failure_contracts(
    source_raw_text,
    expected_status,
):
    original = _build_resume(
        bullets=["Repeated SQL bullet.", "Repeated SQL bullet."],
    )

    rebuilt, status = build_counterfactual_resume_evidence(
        original,
        "",
        "Replacement.",
        source_raw_text,
    )

    assert rebuilt is None
    assert status == expected_status
