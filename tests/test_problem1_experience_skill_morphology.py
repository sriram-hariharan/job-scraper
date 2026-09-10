"""P1S32 offline regressions for bounded experience-entry skill morphology.

P1S31 proved the scorer's experience-only evidence contract is intentional and
that aggregate ``ResumeEvidence.skills`` is mixed-source (286/325 aggregate-only
occurrences come from the Skills section alone), so it must not become
authoritative. The defect was instead that ``_extract_pattern_hits`` matches a
canonical phrase literally: "Fine-tuned" never yields "fine-tuning". These tests
pin the closed-set repair and, just as importantly, its boundaries.

No provider, embedding, cache, or application-data work.
"""

from dataclasses import replace

from src.config.consts import COMMON_SKILL_PATTERNS
from src.resume.evidence_builder import (
    _EXPERIENCE_SKILL_MORPHOLOGY,
    _experience_skill_morphology_hits,
    _refresh_experience_entry_structured_fields,
)
from src.resume.models import ResumeExperienceEntry


def _entry(*bullets, title="Data Scientist II", company="L.B. Foster Salient Systems"):
    entry = ResumeExperienceEntry(
        entry_id="test", entry_index=0, company=company, title=title,
        bullets=list(bullets),
    )
    _refresh_experience_entry_structured_fields(entry)
    return entry


# --- positive regressions, exercised through the real entry path -------------

def test_fine_tuned_bullet_yields_fine_tuning_in_entry_skills():
    """The P1S31 proof case, verbatim from Sriram_Neelakantan_AI1.pdf."""
    entry = _entry(
        "Fine-tuned a LLaMA-2 model using Hugging Face AutoModelForCausalLM and "
        "LoRA adapters in PyTorch Lightning, tracked via MLflow"
    )
    assert "fine-tuning" in entry.normalized_skills
    # The existing literal extractor still contributes its own hits.
    assert "pytorch" in entry.normalized_skills


def test_data_models_bullet_yields_data_modeling_in_entry_skills():
    entry = _entry(
        "Engineered SQL data models and Power BI reports to visualize wheel "
        "diagnostics, anomaly patterns, and predictive health scores"
    )
    assert "data modeling" in entry.normalized_skills
    assert "sql" in entry.normalized_skills


def test_multi_agent_bullet_yields_multi_agent_systems_in_entry_skills():
    entry = _entry(
        "Cut average response time from 3 min to 45 sec by developing an "
        "LLM-based multi-agent intent framework (LangGraph + Step Functions)",
        title="Data Scientist (Agentic AI)", company="Techmentee",
    )
    assert "multi-agent systems" in entry.normalized_skills


def test_closed_set_inflections_all_fold_to_their_approved_canonical():
    """Only same-lexeme inflections; every canonical must already be approved."""
    for text, canonical in (
        ("fine-tune", "fine-tuning"), ("fine tune", "fine-tuning"),
        ("fine-tuned", "fine-tuning"), ("fine-tunes", "fine-tuning"),
        ("fine tuning", "fine-tuning"), ("finetuning", "fine-tuning"),
        ("data model", "data modeling"), ("data models", "data modeling"),
        ("multi-agent", "multi-agent systems"), ("multi agent", "multi-agent systems"),
    ):
        assert _experience_skill_morphology_hits(text) == [canonical], text

    approved = {value.strip().lower() for value in COMMON_SKILL_PATTERNS}
    for _pattern, canonical in _EXPERIENCE_SKILL_MORPHOLOGY:
        assert canonical in approved, canonical


# --- collision / negative regressions ---------------------------------------

def test_fine_tune_family_does_not_match_unrelated_text():
    for text in (
        "fine", "tuned", "tuning the ingestion pipeline",
        "refined tuning parameters", "confine tuned scope", "fine-grained access",
    ):
        assert _experience_skill_morphology_hits(text) == [], text


def test_data_model_family_does_not_match_generic_model_language():
    for text in (
        "model", "models", "modeling", "model monitoring",
        "predictive models", "data modeler", "data modelers",
    ):
        assert "data modeling" not in _experience_skill_morphology_hits(text), text


def test_multi_agent_family_does_not_match_generic_agent_language():
    for text in ("agent", "agents", "multi", "agentic workflows",
                 "multithreaded agents", "multiagentic"):
        assert _experience_skill_morphology_hits(text) == [], text


def test_bullet_without_any_family_adds_nothing():
    entry = _entry("Built Power BI dashboards in SQL for quarterly reporting")
    assert _experience_skill_morphology_hits(" ".join(entry.bullets)) == []


# --- isolation: experience-only, never project or whole-document ------------

def test_repair_is_not_applied_to_project_entries():
    """Projects keep their separate, weaker evidence path (P1S31 Step 20)."""
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "src/resume/evidence_builder.py"
    ).read_text(encoding="utf-8")

    project_body = source.split("def _refresh_project_entry_structured_fields(")[1].split(
        "\ndef _aggregate_resume_structured_fields("
    )[0]
    assert "_experience_skill_morphology_hits" not in project_body

    build_body = source.split("def build_resume_evidence(")[1]
    assert "_experience_skill_morphology_hits" not in build_body

    # Exactly one caller: the experience-entry refresh.
    assert source.count("_experience_skill_morphology_hits(") == 2  # def + call


def test_aggregate_skill_construction_is_unchanged():
    """build_resume_evidence still scans the whole document for aggregate skills
    and still unions experience skills first; ownership/provenance is untouched."""
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "src/resume/evidence_builder.py"
    ).read_text(encoding="utf-8")
    assert "skills = _extract_pattern_hits(text_norm, COMMON_SKILL_PATTERNS)" in source
    assert "skills = _unique_preserve_order(experience_skills + skills)" in source


def test_shared_alias_table_and_matcher_are_untouched():
    """The repair must not reach _SKILL_ALIASES or _extract_pattern_hits, which
    are shared with the JD adapter, prefilter, tailoring and signal matchers."""
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "src/resume/evidence_builder.py"
    ).read_text(encoding="utf-8")
    matcher = source.split("def _extract_pattern_hits(")[1].split("\ndef _extract_phrase_hits(")[0]
    assert "_EXPERIENCE_SKILL_MORPHOLOGY" not in matcher
    helper = source.split("def _experience_skill_morphology_hits(")[1].split("\ndef _refresh_experience")[0]
    assert "_SKILL_ALIASES" not in helper


def test_helper_is_deterministic_and_order_stable():
    text = "Fine-tuned a model, engineered SQL data models, shipped a multi-agent framework"
    first = _experience_skill_morphology_hits(text)
    assert first == _experience_skill_morphology_hits(text)
    assert first == ["fine-tuning", "data modeling", "multi-agent systems"]
