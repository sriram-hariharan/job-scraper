"""Problem 1 characterization: JD-evidence starvation in build_job_evidence.

These tests pin CURRENT behavior, not desired behavior. P1S3 proved that
structured JD evidence is frequently lost before the scorer ever runs, which
starves substantive match dimensions and lets weak supporting or semantic
signals decide resume ranking.

Two distinct existing loss mechanisms are characterized separately, because
they need different corrections:

  A. vocabulary gap    - the concept has no entry in any repository taxonomy,
                         so no amount of context gating would surface it.
  B. context-gate loss - the concept IS in a repository taxonomy and IS in the
                         JD, but sits outside the section chunks that
                         _collect_context_chunks admits.

The dropped Lean / process-improvement evidence characterized here is a
defect, not a product requirement. P1S5 is expected to change some of these
expectations deliberately; that is what this module exists to measure.

Fixture provenance: tests/fixtures/p1s3_jd_evidence/starved_jd_records.json
holds five real corpus records whose retrieval_text was reduced to the
smallest verbatim excerpt that still reproduces byte-identical
build_job_evidence output. No JD text was invented, and no resume or other
user content is stored.
"""

import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from src.matching.job_adapter import build_job_evidence
from src.matching.job_models import JobEvidence
from src.matching.scorer import score_resume_job_match
from src.resume.evidence_builder import build_resume_evidence
from src.resume.models import ResumeDocument


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/p1s3_jd_evidence/starved_jd_records.json"
CORPUS_BASELINE = ROOT / "tests/fixtures/p1s3_jd_evidence/corpus_jobevidence_baseline.json"
CORPUS_SOURCE = ROOT / "outputs/application_planning/current_run_job_corpus.jsonl"

# Substantive target categories that feed the weighted match dimensions.
# kpi_metrics and ownership_signals are deliberately excluded: build_job_evidence
# populates them but no scorer or prefilter reads them.
SUBSTANTIVE_TARGET_FIELDS = (
    "required_methods",
    "preferred_methods",
    "required_workflows",
    "preferred_workflows",
    "business_contexts",
    "stakeholder_contexts",
)

# Role-defining concepts repeated throughout the real Mattel JD.
MATTEL_ROLE_CONCEPTS = (
    "lean",
    "process improvement",
    "manufacturing",
    "root cause",
    "six sigma",
    "kaizen",
    "cycle time",
    "continuous improvement",
)


def _records():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return {record["doc_id"]: record for record in payload["jobs"]}


def _job(doc_id):
    return build_job_evidence(_records()[doc_id])


def _all_target_terms(job):
    """Every term the job exposes to any scorer dimension."""
    return {
        term.lower()
        for term in (
            list(job.required_skills)
            + list(job.preferred_skills)
            + list(job.all_skills)
            + list(job.required_tools)
            + list(job.preferred_tools)
            + list(job.required_workflows)
            + list(job.preferred_workflows)
            + list(job.required_methods)
            + list(job.preferred_methods)
            + list(job.business_contexts)
            + list(job.stakeholder_contexts)
        )
    }


def _probe_terms(term, inside_recognized_section):
    """Recognition probe: does build_job_evidence surface `term` at all?

    Isolates taxonomy membership from context gating by placing the same term
    inside vs outside a section header that REQUIRED_CONTEXT_PATTERNS matches.
    """
    retrieval_text = (
        f"Requirements: {term} experience required."
        if inside_recognized_section
        else f"About the team: we care about {term} every day."
    )
    job = build_job_evidence(
        {
            "doc_id": "recognition_probe",
            "company": "Probe Co",
            "title": "Staff Data Analyst",
            "location": "US",
            "source": "test",
            "retrieval_text": retrieval_text,
        }
    )
    return _all_target_terms(job)


# --- fixture integrity -------------------------------------------------------


def test_reduced_fixtures_cover_the_five_proven_p1s3_cases():
    records = _records()

    assert set(records) == {
        "mattel_lean_process_improvement",
        "anthropic_research_engineer_code_rl",
        "anthropic_research_engineer_performance_rl",
        "anthropic_research_engineer_knowledge_team",
        "scaleai_ml_research_engineer_ml_systems",
    }
    for record in records.values():
        assert record["retrieval_text"].strip()
        # the adapter reads preview + retrieval_text; the real corpus records
        # carry no preview, so the fixtures must not add one
        assert "preview" not in record


# --- corpus-wide extraction baseline -----------------------------------------


def test_corpus_baseline_fixture_is_well_formed():
    """Always runs: the recorded baseline is the reference for measuring the
    blast radius of any extraction change, so its shape must stay stable."""
    payload = json.loads(CORPUS_BASELINE.read_text(encoding="utf-8"))
    jobs = payload["jobs"]
    fields = payload["provenance"]["fields"]

    assert payload["provenance"]["job_count"] == len(jobs) == 80
    assert len({entry["job_key"] for entry in jobs}) == 80
    for entry in jobs:
        assert set(entry) == {"job_key", *fields}
    # outputs only - no raw JD text is stored in this baseline
    assert "retrieval_text" not in fields
    assert "description" not in fields


def test_corpus_jobevidence_matches_the_recorded_baseline():
    """Whole-corpus extraction guard. Skips when the local planning corpus is
    absent, following the existing convention for tests that read optional
    local runtime data."""
    if not CORPUS_SOURCE.exists():
        pytest.skip("local application-planning corpus is not present")

    payload = json.loads(CORPUS_BASELINE.read_text(encoding="utf-8"))
    fields = payload["provenance"]["fields"]
    expected = {entry["job_key"]: entry for entry in payload["jobs"]}

    records = [
        json.loads(line)
        for line in CORPUS_SOURCE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(records) == len(expected)

    drift = {}
    for record in records:
        job_key = f"{record.get('company', '')}|{record.get('title', '')}"
        assert job_key in expected, job_key
        job = build_job_evidence(record)
        changed = {
            field: {"baseline": expected[job_key][field], "current": getattr(job, field)}
            for field in fields
            if expected[job_key][field] != getattr(job, field)
        }
        if changed:
            drift[job_key] = changed

    assert drift == {}, f"JobEvidence drifted for {len(drift)} job(s): {sorted(drift)}"


# --- Mattel: overall starvation ---------------------------------------------


def test_mattel_lean_jd_yields_only_a_reporting_workflow_and_no_context_targets():
    """Current behavior: a Lean/process-improvement manufacturing analyst role
    reaches the scorer as 'reporting' plus a tool list."""
    job = _job("mattel_lean_process_improvement")

    assert job.role_archetype == "data_analyst_bi"
    assert job.required_workflows == ["reporting"]
    # P1S19 vocabulary additions (approved by P1S20) recover three categories
    assert job.preferred_workflows == ["process improvement"]
    assert job.business_contexts == ["contract manufacturing", "procurement"]
    assert job.required_skills == [
        "python", "sql", "r", "tableau", "power bi", "powerpoint", "erp", "bigquery",
    ]
    assert job.required_tools == job.required_skills
    assert job.preferred_skills == ["applied ai", "excel"]

    # the unresolved gaps: generic Lean methods and stakeholder context
    assert job.required_methods == []
    assert job.preferred_methods == []
    assert job.stakeholder_contexts == []


def test_mattel_kpi_and_ownership_targets_are_extracted_but_unused_by_scoring():
    """kpi_metrics is populated yet no dimension consumes it, so it cannot
    compensate for the empty workflow/method/context targets."""
    job = _job("mattel_lean_process_improvement")

    assert job.kpi_metrics == ["adoption", "quality"]
    assert job.ownership_signals == []

    scorer_source = (ROOT / "src/matching/scorer.py").read_text(encoding="utf-8")
    prefilter_source = (ROOT / "src/matching/prefilter.py").read_text(encoding="utf-8")
    for unread_field in ("kpi_metrics", "ownership_signals"):
        assert unread_field not in scorer_source
        assert unread_field not in prefilter_source


# --- Mattel mechanism A: vocabulary gap --------------------------------------


def test_mattel_role_concepts_are_present_in_the_jd_text():
    """Premise for the two mechanism tests: the JD really does say these."""
    retrieval_text = _records()["mattel_lean_process_improvement"]["retrieval_text"].lower()

    for concept in MATTEL_ROLE_CONCEPTS:
        assert concept in retrieval_text, concept
    assert "supply chain" in retrieval_text


def test_mattel_lean_concepts_have_no_taxonomy_entry_in_any_position():
    """Mechanism A. These role-defining concepts are unrecognized wherever they
    appear, so context gating is not the reason they are missing."""
    # P1S19 gave "process improvement" a workflow owner; the rest are still
    # unrecognised, which is the Lean method gap P1S20 left open on purpose.
    still_unowned = tuple(c for c in MATTEL_ROLE_CONCEPTS if c != "process improvement")
    assert len(still_unowned) == 7

    for concept in still_unowned:
        assert concept not in _probe_terms(concept, inside_recognized_section=True), concept
        assert concept not in _probe_terms(concept, inside_recognized_section=False), concept

    job = _job("mattel_lean_process_improvement")
    surfaced = _all_target_terms(job)
    for concept in still_unowned:
        assert concept not in surfaced, concept
    assert "process improvement" in surfaced


# --- Mattel mechanism B: context-gate loss -----------------------------------


def test_supply_chain_is_recognized_by_the_taxonomy_unlike_the_lean_concepts():
    """Mechanism B, part 1: 'supply chain' IS a known business context, which is
    what distinguishes it from the Lean vocabulary gap above."""
    assert "supply chain" in _probe_terms("supply chain", inside_recognized_section=True)


def test_mattel_supply_chain_is_discarded_despite_being_a_known_business_context():
    """Mechanism B, part 2: the JD states supply-chain work and the taxonomy has
    known the term throughout, yet it never reaches business_contexts because the
    occurrences sit outside the admitted section chunks. P1S19 populated that
    field with other terms; supply chain itself is still gated out, so the
    original finding is unchanged."""
    job = _job("mattel_lean_process_improvement")

    assert "supply chain" in _records()["mattel_lean_process_improvement"]["retrieval_text"].lower()
    assert job.business_contexts == ["contract manufacturing", "procurement"]
    assert "supply chain" not in job.business_contexts
    assert "supply chain" not in _all_target_terms(job)


def test_context_gating_governs_workflow_extraction_position():
    """Independent confirmation of the gate itself: an in-taxonomy workflow term
    survives inside a recognized section and is dropped outside one.

    'reporting' is used rather than another workflow term because terms that are
    also common skills (for example 'forecasting') still reach all_skills via
    the ungated combined-text fallback, which would mask the gate.
    """
    assert "reporting" in _probe_terms("reporting", inside_recognized_section=True)
    assert "reporting" not in _probe_terms("reporting", inside_recognized_section=False)


# --- section-boundary collection contract ------------------------------------
#
# A recognized section header whose first following chunk is also colon
# terminated used to collect nothing at all, because _collect_context_chunks
# broke on the first heading-like follow chunk. These pin the corrected
# boundary rule: an internal subheading is skipped only while the section has
# collected nothing yet, so a section can never contribute zero chunks and can
# never absorb the section that follows it.


def _probe_job(retrieval_text):
    return build_job_evidence(
        {
            "doc_id": "section_boundary_probe",
            "company": "Probe Co",
            "title": "Data Analyst",
            "location": "US",
            "source": "test",
            "retrieval_text": retrieval_text,
        }
    )


def test_internal_colon_subheading_currently_terminates_a_recognized_section():
    """Current defect, in the shape taken from the real Mattel responsibilities
    section: recognized header, colon-terminated descriptive subheading, then
    the actual content. _collect_context_chunks breaks on the subheading, so the
    section contributes nothing and the workflow evidence is lost.

    Compare with test_ordinary_recognized_section_extraction_is_unchanged, which
    is the identical JD minus the subheading."""
    job = _probe_job(
        "Responsibilities: Drive impact: Build dashboards and reporting for the growth team."
    )

    assert job.required_workflows == []


def test_following_unrecognized_section_is_not_absorbed_into_the_recognized_one():
    """The skip must not run on into the next section. 'Benefits:' is heading
    like but is not a recognized section header, so it must still terminate
    collection once the responsibilities section has content."""
    job = _probe_job(
        "Responsibilities: Build dashboards and reporting for the growth team. "
        "Benefits: We support healthcare and fraud protection for your family. "
        "Equal opportunity statement follows."
    )

    assert job.required_workflows == ["reporting", "dashboard"]
    assert job.business_contexts == ["growth"]
    for leaked in ("healthcare", "fraud"):
        assert leaked not in _all_target_terms(job), leaked


def test_ordinary_recognized_section_extraction_is_unchanged():
    """Guard against the correction broadening every section: a plain
    recognized section with no subheading keeps its existing result."""
    job = _probe_job("Responsibilities: Build dashboards and reporting for the growth team.")

    assert job.required_workflows == ["reporting", "dashboard"]
    assert job.business_contexts == ["growth"]


def test_reduced_fixtures_are_only_faithful_under_the_code_they_were_derived_from():
    """P1S6 finding. The reduced fixtures were verified byte-identical to their
    real corpus records against the current collector. A collector change can
    reach text the reduction dropped, so the fixtures must be re-verified (and
    regenerated if needed) alongside any extraction change - the reduced Mattel
    record must never be treated as a substitute for the full one."""
    provenance = json.loads(FIXTURE.read_text(encoding="utf-8"))["provenance"]

    assert provenance["derived_at_head"] == "e57b90ae27bc3ca7a6350cf36e74874500fd47d7"
    assert "reproduces byte-identical build_job_evidence output" in provenance["reduction"]


def test_section_header_patterns_are_apostrophe_encoding_fragile():
    """P1S7 finding. Three context-header patterns spell the apostrophe as U+0027
    only, while two in the same lists already accept both forms. A real JD
    heading written with a typographic apostrophe therefore fails to register as
    a section boundary. This is an encoding defect in existing patterns, not a
    missing concept."""
    from src.config import consts

    groups = (
        consts.REQUIRED_CONTEXT_PATTERNS
        + consts.RESPONSIBILITY_CONTEXT_PATTERNS
        + consts.PREFERRED_CONTEXT_PATTERNS
    )
    both_forms = [pattern for pattern in groups if "['’]" in pattern]
    straight_only = [
        pattern for pattern in groups if "'" in pattern and "['" not in pattern
    ]

    assert len(both_forms) == 2
    assert sorted(straight_only) == [
        r"\bwhat we're looking for\b",
        r"\bwhat you'll bring\b",
        r"\bwhat you'll need\b",
    ]

    # the straight-apostrophe pattern matches only the straight form
    looking_for = r"\bwhat we're looking for\b"
    assert re.search(looking_for, "What We're Looking For:", re.I) is not None
    assert re.search(looking_for, "What We’re Looking For:", re.I) is None


def test_recognized_section_without_a_later_heading_collects_to_end_of_text():
    """P1S7 finding, and the structural blocker for deterministic boundary work.
    _collect_context_chunks only ever stops at a heading-like chunk, so a
    recognized section whose remaining text contains none runs to the end of the
    document - pulling in compensation, benefits and legal boilerplate."""
    job = _probe_job(
        "Requirements: Build dashboards and reporting for the growth team. "
        "The pay range is indicative of projected hiring range. "
        "We are dedicated to an inclusive workplace and a culture of belonging. "
        "Join our Talent Community for updates about fraud awareness in healthcare."
    )

    # boilerplate that follows an unterminated section reaches the evidence
    surfaced = _all_target_terms(job)
    assert "healthcare" in surfaced
    assert "fraud" in surfaced


# --- four zero-discrimination research/ML jobs -------------------------------


def test_sparse_research_jobs_lose_every_substantive_target_category():
    """Current behavior for the four jobs P1S3 measured at zero discriminating
    substantive dimensions: only skills and their tool echo survive."""
    for doc_id in (
        "anthropic_research_engineer_code_rl",
        "anthropic_research_engineer_performance_rl",
        "anthropic_research_engineer_knowledge_team",
        "scaleai_ml_research_engineer_ml_systems",
    ):
        job = _job(doc_id)
        for field in SUBSTANTIVE_TARGET_FIELDS:
            assert getattr(job, field) == [], f"{doc_id}.{field}"
        assert job.required_skills, doc_id
        assert job.role_archetype == "general_analytics", doc_id


def test_sparse_research_jobs_reduce_their_upstream_skill_lists():
    """The upstream record supplies richer skill lists than survive the
    adapter's known-skill filtering; this is a second, separate loss."""
    records = _records()

    performance_rl = records["anthropic_research_engineer_performance_rl"]
    assert len(performance_rl["required_skills"]) == 6
    assert len(performance_rl["preferred_skills"]) == 7
    job = build_job_evidence(performance_rl)
    assert job.required_skills == ["pytorch"]
    assert job.preferred_skills == ["machine learning"]

    ml_systems = records["scaleai_ml_research_engineer_ml_systems"]
    assert len(ml_systems["required_skills"]) == 4
    assert build_job_evidence(ml_systems).required_skills == ["pytorch", "transformers"]

    code_rl = records["anthropic_research_engineer_code_rl"]
    assert build_job_evidence(code_rl).required_skills == ["python"]

    knowledge = records["anthropic_research_engineer_knowledge_team"]
    assert len(knowledge["required_skills"]) == 10
    assert build_job_evidence(knowledge).required_skills == ["llm", "python", "rag"]


# --- scorer consequence ------------------------------------------------------


def _synthetic_resume(name, title, bullet):
    """Deterministic offline resume evidence, following the inline-fixture
    convention already used by tests/test_phase116a_applied_ai_scoring_fix.py.
    No real resume content is used.

    The skills line carries the Mattel JD's full required-tool set so both
    resumes clear the deterministic prefilter and the comparison isolates
    role-responsibility evidence.
    """
    raw_text = f"""
{title}

Experience
{title}, Demo Co
2021 - Present
- {bullet}

Skills
Python SQL R Tableau Power BI Google BigQuery Excel
""".strip()
    return build_resume_evidence(
        ResumeDocument(
            resume_id=name,
            resume_name=name,
            path=name,
            raw_text=raw_text,
            normalized_text=raw_text.lower(),
        )
    )


def _dimension_scores(job, resume):
    return {
        dimension.name: dimension.score
        for dimension in score_resume_job_match(resume, job).dimension_scores
    }


def test_starved_mattel_targets_make_role_dimensions_neutral_for_every_resume():
    """Scorer consequence of the empty targets above: the dimensions that would
    carry Lean/process-improvement responsibility evidence return the neutral
    0.5 default regardless of what the resume says."""
    job = _job("mattel_lean_process_improvement")
    lean_resume = _synthetic_resume(
        "lean_analyst.pdf",
        "Process Improvement Analyst",
        "Led Lean and Six Sigma process improvement, Kaizen events, root cause analysis "
        "and cycle time reduction across supply chain and manufacturing operations using "
        "Python, SQL, R, Tableau, Power BI and Google BigQuery.",
    )
    unrelated_resume = _synthetic_resume(
        "unrelated_analyst.pdf",
        "Data Analyst",
        "Built Python, SQL, R, Tableau, Power BI and Google BigQuery reporting dashboards.",
    )

    lean_result = score_resume_job_match(lean_resume, job)
    unrelated_result = score_resume_job_match(unrelated_resume, job)
    assert lean_result.prefilter.passed
    assert unrelated_result.prefilter.passed

    lean_scores = _dimension_scores(job, lean_resume)
    unrelated_scores = _dimension_scores(job, unrelated_resume)

    # P1S19 gave Mattel real business-context targets, so that dimension is no
    # longer neutral: it now measures a genuine absence in both resumes.
    assert lean_scores["business_context_alignment"] == 0.0
    assert unrelated_scores["business_context_alignment"] == 0.0

    for dimension in (
        "stakeholder_translation_alignment",
        "domain_relevance",
        "analytics_ml_depth",
        "experimentation_depth",
    ):
        assert lean_scores[dimension] == 0.5, dimension
        assert unrelated_scores[dimension] == 0.5, dimension
        # explicit Lean evidence earns the candidate nothing on these dimensions
        assert lean_scores[dimension] == unrelated_scores[dimension], dimension


def test_lean_evidence_currently_loses_to_a_resume_without_it():
    """End-to-end consequence on portable synthetic resumes. The resume with no
    Lean/process-improvement evidence outranks the one with it, because the only
    surviving JD target is the 'reporting' workflow. This is the Problem 1
    defect, characterized so P1S5 can measure the intended change."""
    job = _job("mattel_lean_process_improvement")
    lean_resume = _synthetic_resume(
        "lean_analyst.pdf",
        "Process Improvement Analyst",
        "Led Lean and Six Sigma process improvement, Kaizen events, root cause analysis "
        "and cycle time reduction across supply chain and manufacturing operations using "
        "Python, SQL, R, Tableau, Power BI and Google BigQuery.",
    )
    unrelated_resume = _synthetic_resume(
        "unrelated_analyst.pdf",
        "Data Analyst",
        "Built Python, SQL, R, Tableau, Power BI and Google BigQuery reporting dashboards.",
    )

    lean_scores = _dimension_scores(job, lean_resume)
    unrelated_scores = _dimension_scores(job, unrelated_resume)

    # the sole surviving workflow target decides it
    # P1S19 added "process improvement" as a second workflow target, so the
    # unrelated resume now covers 1 of 2 rather than 1 of 1.
    assert lean_scores["workflow_alignment"] == 0.0
    assert unrelated_scores["workflow_alignment"] == 0.7

    lean_final = score_resume_job_match(lean_resume, job).final_score
    unrelated_final = score_resume_job_match(unrelated_resume, job).final_score
    assert unrelated_final > lean_final


# --- P1S9: mocked proof that the existing JD-intelligence LLM capability could
# --- serve as a starvation-triggered fallback for JobEvidence.
#
# The subsystem under test lives in src/app/services.py and is default-off. Its
# scan-path behavior is owned by
# tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off.py;
# these tests characterize only whether it can fill starved JobEvidence, which is
# a Problem-1 question. No provider is contacted: the production helpers are
# called directly with a mocked structured payload.

SUBSTANTIVE_TARGET_GROUPS = (
    "required_methods",
    "preferred_methods",
    "required_workflows",
    "preferred_workflows",
    "business_contexts",
    "stakeholder_contexts",
)

# Proven-starved and healthy-control jobs established in P1S3/P1S8.
STARVED_JOB_KEYS = (
    "mattelinc|Staff Data Analyst, Lean and Process Improvement, Co Manufacturing",
    "anthropic|Research Engineer, Code RL (Reinforcement Learning)",
    "anthropic|Research Engineer, Performance RL (Reinforcement Learning)",
    "anthropic|Research Engineer, Knowledge Team",
    "scaleai|ML Research Engineer, ML Systems",
)
HEALTHY_CONTROL_JOB_KEYS = (
    "anthropic|People Research Scientist, Recruiting",
    "mongodb|Senior Data Analyst",
    "reddit|Senior Staff Data Scientist - Consumer Relevance",
    "stripe|Senior Data Scientist",
)


def _starvation_trigger(job):
    """T8: at least five of the six substantive target groups are empty."""
    return sum(1 for field in SUBSTANTIVE_TARGET_GROUPS if not getattr(job, field)) >= 5


def _corpus_records():
    if not CORPUS_SOURCE.exists():
        pytest.skip("local application-planning corpus is not present")
    return {
        f"{record.get('company', '')}|{record.get('title', '')}": record
        for record in (
            json.loads(line)
            for line in CORPUS_SOURCE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def _mattel_mock_payload():
    """Structured payload in the existing schema. Every term is verbatim in the
    authoritative Mattel JD, so grounding must accept all of them."""
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["Tableau"],
        "required_tools": ["Power BI"],
        "preferred_tools": ["Excel"],
        "workflows": ["process improvement"],
        "methods": ["root cause analysis"],
        "business_contexts": ["supply chain"],
        "stakeholder_contexts": ["stakeholders"],
        "ownership_signals": ["ownership"],
        "seniority_signals": ["Staff"],
        "risk_flags": [],
        "extraction_confidence": 0.9,
    }


def test_retired_raw_field_starvation_trigger_is_no_longer_the_contract():
    """P1S21 REPLACE. The experimental raw-field trigger (_starvation_trigger,
    "T8") counted six JobEvidence fields and was retired: it double-counted
    required/preferred, treated an absent "preferred" section as starvation, and
    counted the method fields even though generic process methods cannot be
    scored end to end. Its replacement is assess_jd_extraction_health, pinned by
    the P1S21 tests below.

    This keeps the retired behaviour visible: a single approved vocabulary
    addition moved Mattel out of the old population without the JD changing."""
    records = _corpus_records()
    fired = {
        key
        for key, record in records.items()
        if _starvation_trigger(build_job_evidence(record))
    }

    assert len(records) == 80
    assert len(fired) == 30  # was 31 before the P1S19 vocabulary additions
    assert STARVED_JOB_KEYS[0] not in fired  # Mattel, moved by one workflow term
    for key in STARVED_JOB_KEYS[1:]:
        assert key in fired, key
    for key in HEALTHY_CONTROL_JOB_KEYS:
        assert key not in fired, key

def test_existing_schema_validator_accepts_and_rejects_without_a_provider_call():
    """The production validator is reused as-is; no replacement JSON validator."""
    from src.app import services

    valid, errors = services._validated_planning_scan_jd_provider_payload(
        _mattel_mock_payload()
    )
    assert valid and not errors

    for mutation, expected_error_fragment in (
        ({k: v for k, v in _mattel_mock_payload().items() if k != "methods"}, "missing_required_fields"),
        ({**_mattel_mock_payload(), "workflows": "not-a-list"}, "invalid_type:workflows"),
        ({**_mattel_mock_payload(), "unsupported_extra": ["x"]}, "unexpected_fields"),
        ({**_mattel_mock_payload(), "raw_response": "{bad json"}, "invalid_json_response"),
    ):
        payload, errors = services._validated_planning_scan_jd_provider_payload(mutation)
        assert payload == {}
        assert any(expected_error_fragment in error for error in errors), errors


def test_existing_grounding_accepts_jd_terms_and_rejects_hallucinations():
    """Grounding is exact-substring containment against the full JD, so an
    invented term cannot survive."""
    from src.app import services

    record = _corpus_records()[STARVED_JOB_KEYS[0]]
    payload = _mattel_mock_payload()
    payload["business_contexts"] = ["supply chain", "quantum cryptography trading desk"]

    validated, _ = services._validated_planning_scan_jd_provider_payload(payload)
    mapped = services._planning_scan_phase34a_provider_payload(validated)
    grounded, rejected = services._ground_planning_scan_jd_signals(mapped, job_record=record)

    assert "supply chain" in str(grounded)
    assert "quantum cryptography trading desk" in str(rejected)
    assert "quantum cryptography trading desk" not in str(grounded)


def test_existing_payload_mapping_discards_the_categories_jobevidence_needs():
    """P1S9 blocking finding G5/G3. Before grounding runs, the schema's distinct
    evidence categories are flattened: workflows, methods, ownership_signals and
    stakeholder_contexts all collapse into one 'responsibilities' list, and
    business_contexts collapses into a 'domain' string. JobEvidence needs those
    categories kept apart, so the scan-path mapping cannot be reused unchanged."""
    from src.app import services

    validated, _ = services._validated_planning_scan_jd_provider_payload(
        _mattel_mock_payload()
    )
    mapped = services._planning_scan_phase34a_provider_payload(validated)

    assert mapped["responsibilities"] == [
        "process improvement",
        "root cause analysis",
        "ownership",
        "stakeholders",
    ]
    assert mapped["domain"] == "supply chain"
    for lost_category in ("workflows", "methods", "business_contexts", "stakeholder_contexts"):
        assert lost_category not in mapped, lost_category


def test_existing_apply_step_is_not_fill_missing_and_degrades_healthy_fields():
    """P1S9 blocking finding G6. The scan-path merge is additive on the raw job
    record, not fill-missing on JobEvidence. Re-deriving after it moves four
    healthy required skills into preferred, and the grounded 'supply chain'
    never reaches business_contexts. A future fallback needs its own merge."""
    from src.app import services

    record = _corpus_records()[STARVED_JOB_KEYS[0]]
    validated, _ = services._validated_planning_scan_jd_provider_payload(
        _mattel_mock_payload()
    )
    mapped = services._planning_scan_phase34a_provider_payload(validated)
    grounded, _ = services._ground_planning_scan_jd_signals(mapped, job_record=record)

    before = build_job_evidence(record)
    after = build_job_evidence(
        services._apply_grounded_planning_scan_jd_signals(record, grounded)
    )

    # healthy deterministic evidence is degraded, not preserved
    assert before.required_skills == [
        "python", "sql", "r", "tableau", "power bi", "powerpoint", "erp", "bigquery",
    ]
    assert after.required_skills == ["python", "sql"]
    for demoted in ("r", "tableau", "power bi", "bigquery"):
        assert demoted in after.preferred_skills, demoted

    # P1S19 populated business_contexts deterministically, but the scan-path
    # merge still cannot add "supply chain" - it maps into a "domain" string.
    assert "supply chain" not in before.business_contexts
    assert "supply chain" not in after.business_contexts


# --- P1S10: JobEvidence-shaped compatibility layer for JD-intelligence output.
#
# These characterize the new pure helpers in src/matching/job_adapter.py. They
# are not wired into build_job_evidence or any pipeline stage; the runtime
# activation test below pins that. The existing New Scan mapper and apply logic
# are untouched and remain owned by
# tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off.py.

from src.matching.job_adapter import (  # noqa: E402
    JD_INTELLIGENCE_CANDIDATE_FIELD_MAP,
    build_job_evidence_enrichment_candidate,
    ground_jd_intelligence_signals,
    merge_missing_job_evidence,
)


def _jd_text(record):
    return " ".join([str(record.get("title", "")), str(record.get("retrieval_text", ""))])


def _mattel_payload_with_hallucination():
    payload = _mattel_mock_payload()
    payload["business_contexts"] = ["supply chain", "quantum cryptography trading desk"]
    return payload


def test_grounding_preserves_category_identity_and_rejects_hallucinations():
    """The New Scan mapper flattens four categories into 'responsibilities' and
    business_contexts into 'domain'. This layer must keep them apart."""
    from src.app import services

    record = _corpus_records()[STARVED_JOB_KEYS[0]]
    validated, errors = services._validated_planning_scan_jd_provider_payload(
        _mattel_payload_with_hallucination()
    )
    assert validated and not errors

    grounded, rejected = ground_jd_intelligence_signals(validated, _jd_text(record))

    assert grounded["business_contexts"] == ["supply chain"]
    assert grounded["workflows"] == ["process improvement"]
    assert grounded["methods"] == ["root cause analysis"]
    assert grounded["stakeholder_contexts"] == ["stakeholders"]
    assert grounded["required_tools"] == ["power bi"]
    assert grounded["preferred_tools"] == ["excel"]
    assert grounded["required_skills"] == ["python", "sql"]
    assert grounded["preferred_skills"] == ["tableau"]

    assert rejected["business_contexts"] == ["quantum cryptography trading desk"]
    # categories are never merged into the scan-path shapes
    for flattened in ("responsibilities", "domain", "tools"):
        assert flattened not in grounded


def test_enrichment_candidate_maps_flat_workflows_and_methods_to_required_only():
    """The response schema carries no required/preferred signal for workflows or
    methods, so this layer deliberately fills only the required fields and
    leaves preferred_workflows / preferred_methods deterministic-only."""
    from src.app import services

    record = _corpus_records()[STARVED_JOB_KEYS[0]]
    validated, _ = services._validated_planning_scan_jd_provider_payload(
        _mattel_mock_payload()
    )
    grounded, _ = ground_jd_intelligence_signals(validated, _jd_text(record))
    candidate = build_job_evidence_enrichment_candidate(grounded)

    assert candidate["required_workflows"] == ["process improvement"]
    assert candidate["required_methods"] == ["root cause analysis"]
    assert candidate["business_contexts"] == ["supply chain"]
    assert candidate["stakeholder_contexts"] == ["stakeholders"]
    assert "preferred_workflows" not in candidate
    assert "preferred_methods" not in candidate
    # evidence mapping only - never a scoring or classification field
    for forbidden in ("role_archetype", "seniority", "role_family", "ai_fit_score"):
        assert forbidden not in candidate
    assert set(candidate) <= set(JD_INTELLIGENCE_CANDIDATE_FIELD_MAP.values())


def test_fill_missing_merge_populates_empty_groups_and_preserves_healthy_ones():
    """Contrast with the New Scan apply step, which cut Mattel's six required
    skills to two. This merge must leave every populated field byte-for-byte."""
    from src.app import services

    record = _corpus_records()[STARVED_JOB_KEYS[0]]
    validated, _ = services._validated_planning_scan_jd_provider_payload(
        _mattel_payload_with_hallucination()
    )
    grounded, _ = ground_jd_intelligence_signals(validated, _jd_text(record))
    candidate = build_job_evidence_enrichment_candidate(grounded)

    before = build_job_evidence(record)
    after = merge_missing_job_evidence(before, candidate)

    # populated deterministic groups are untouched even though the candidate
    # proposes different values for them
    assert after.required_skills == before.required_skills == [
        "python", "sql", "r", "tableau", "power bi", "powerpoint", "erp", "bigquery",
    ]
    assert after.required_tools == before.required_tools
    assert after.preferred_skills == before.preferred_skills
    assert after.required_workflows == before.required_workflows == ["reporting"]
    assert after.role_archetype == before.role_archetype
    assert after.seniority == before.seniority

    # empty groups are filled
    # P1S19 already populates business_contexts, so fill-missing must leave it
    # alone; the still-empty groups are the ones that get filled.
    assert after.business_contexts == before.business_contexts
    assert "supply chain" not in after.business_contexts
    assert before.required_methods == [] and after.required_methods == ["root cause analysis"]
    assert before.stakeholder_contexts == [] and after.stakeholder_contexts == ["stakeholders"]

    # preferred workflow/method stay deterministic-only, hallucination absent
    assert after.preferred_workflows == before.preferred_workflows == ["process improvement"]
    assert after.preferred_methods == []
    assert "quantum" not in str(after).lower()

    # enrichment relieves the remaining consumable gap; the retired raw-field
    # trigger no longer fires for Mattel either way after the P1S19 additions.
    assert assess_jd_extraction_health(before)["missing_categories"] == ["stakeholder_context"]
    assert assess_jd_extraction_health(after)["missing_categories"] == []

    # the input object was not mutated
    assert before.stakeholder_contexts == []


def test_merge_cannot_overwrite_a_healthy_job_even_if_called_directly():
    """Defence in depth: the trigger already spares healthy controls, but the
    merge itself must also refuse to replace populated evidence."""
    records = _corpus_records()
    aggressive = {
        "required_skills": ["zzz"],
        "required_workflows": ["zzz"],
        "business_contexts": ["zzz"],
        "stakeholder_contexts": ["zzz"],
    }

    for key in HEALTHY_CONTROL_JOB_KEYS:
        before = build_job_evidence(records[key])
        after = merge_missing_job_evidence(before, aggressive)
        for field in aggressive:
            if getattr(before, field):
                assert getattr(after, field) == getattr(before, field), f"{key}.{field}"
                assert "zzz" not in getattr(after, field), f"{key}.{field}"


def test_merge_returns_deterministic_evidence_unchanged_on_every_failure_path():
    """Empty candidate, fully rejected grounding, and invalid schema output must
    all leave deterministic JobEvidence exactly as it was."""
    from src.app import services

    record = _corpus_records()[STARVED_JOB_KEYS[0]]
    before = build_job_evidence(record)

    # nothing grounded at all
    grounded, rejected = ground_jd_intelligence_signals(
        {"business_contexts": ["quantum cryptography trading desk"]}, _jd_text(record)
    )
    assert grounded == {}
    assert rejected["business_contexts"] == ["quantum cryptography trading desk"]

    # schema rejection yields no payload to ground
    invalid, errors = services._validated_planning_scan_jd_provider_payload(
        {**_mattel_mock_payload(), "workflows": "not-a-list"}
    )
    assert invalid == {} and errors

    for candidate in ({}, build_job_evidence_enrichment_candidate(grounded),
                      build_job_evidence_enrichment_candidate({})):
        assert merge_missing_job_evidence(before, candidate) is before


def test_compatibility_helpers_are_not_wired_into_any_runtime_path():
    """P1S10 builds primitives only. Nothing in src/ may call them yet."""
    import subprocess

    for symbol in (
        "ground_jd_intelligence_signals",
        "build_job_evidence_enrichment_candidate",
        "merge_missing_job_evidence",
    ):
        hits = subprocess.run(
            ["grep", "-rn", "--include=*.py", symbol, "src/"],
            cwd=ROOT, capture_output=True, text=True,
        ).stdout.splitlines()
        outside = [line for line in hits if "job_adapter.py" not in line]
        assert outside == [], f"{symbol} is referenced outside job_adapter.py: {outside}"

    adapter = (ROOT / "src/matching/job_adapter.py").read_text(encoding="utf-8")
    build_body = adapter.split("def build_job_evidence(", 1)[1].split("\ndef ", 1)[0]
    for symbol in (
        "ground_jd_intelligence_signals",
        "build_job_evidence_enrichment_candidate",
        "merge_missing_job_evidence",
    ):
        assert symbol not in build_body


# --- P1S21: consumable-category extraction health.
#
# Replaces the experimental raw-field starvation test (_starvation_trigger,
# "T8") that counted six JobEvidence fields. P1S20 proved that test gave
# required_*/preferred_* separate votes for one conceptual category, treated a
# legitimately absent "preferred" section as starvation, and counted the method
# fields even though generic process methods cannot be scored end to end. The
# replacement counts only categories matching can consume.

from src.matching.job_adapter import (  # noqa: E402
    JD_CONSUMABLE_EVIDENCE_CATEGORIES,
    JD_CONSUMABLE_EVIDENCE_MISSING_THRESHOLD,
    assess_jd_extraction_health,
)


def _evidence(**overrides):
    base = dict(
        job_doc_id="probe", company="Probe Co", title="Staff Data Analyst",
        location="US", source="test", job_url="", posted_at="",
        role_family="analytics", seniority="staff",
    )
    base.update(overrides)
    return JobEvidence(**base)


def _health(**overrides):
    return assess_jd_extraction_health(_evidence(**overrides))


def test_consumable_categories_exclude_methods_skills_and_tools():
    assert set(JD_CONSUMABLE_EVIDENCE_CATEGORIES) == {
        "workflows", "business_context", "stakeholder_context",
    }
    flattened = {
        field
        for fields in JD_CONSUMABLE_EVIDENCE_CATEGORIES.values()
        for field in fields
    }
    for excluded in (
        "required_methods", "preferred_methods",
        "required_skills", "preferred_skills",
        "required_tools", "preferred_tools",
    ):
        assert excluded not in flattened, excluded
    assert JD_CONSUMABLE_EVIDENCE_MISSING_THRESHOLD == 3


def test_required_workflow_alone_makes_the_workflow_category_healthy():
    """A. required present, preferred empty."""
    health = _health(required_workflows=["reporting"], preferred_workflows=[])
    assert "workflows" in health["populated_categories"]


def test_preferred_workflow_alone_makes_the_workflow_category_healthy():
    """B. required empty, preferred present - the collapsing that T8 lacked."""
    health = _health(required_workflows=[], preferred_workflows=["process improvement"])
    assert "workflows" in health["populated_categories"]


def test_both_workflow_fields_empty_makes_the_workflow_category_missing():
    """C."""
    health = _health(required_workflows=[], preferred_workflows=[])
    assert "workflows" in health["missing_categories"]


def test_business_context_evidence_makes_that_category_healthy():
    """D."""
    health = _health(business_contexts=["supply chain"])
    assert "business_context" in health["populated_categories"]


def test_stakeholder_context_evidence_makes_that_category_healthy():
    """E."""
    health = _health(stakeholder_contexts=["engineering"])
    assert "stakeholder_context" in health["populated_categories"]


def test_methods_have_no_influence_on_consumable_health():
    """F. Mandatory: generic methods cannot be scored end to end, so they must
    not affect eligibility in either direction."""
    empty = _health()
    with_methods = _health(
        required_methods=["root cause analysis", "kaizen"],
        preferred_methods=["value stream mapping"],
    )
    assert empty == with_methods
    assert with_methods["enrichment_eligible"] is True


def test_eligibility_requires_every_consumable_category_to_be_missing():
    assert _health()["enrichment_eligible"] is True
    assert _health(business_contexts=["growth"])["enrichment_eligible"] is False
    assert _health(required_workflows=["reporting"])["enrichment_eligible"] is False
    assert _health(stakeholder_contexts=["product"])["enrichment_eligible"] is False


def test_health_report_is_explainable_and_does_not_mutate_evidence():
    evidence = _evidence(business_contexts=["supply chain"])
    snapshot = replace(evidence)
    health = assess_jd_extraction_health(evidence)

    assert health["populated_categories"] == ["business_context"]
    assert health["missing_categories"] == ["stakeholder_context", "workflows"]
    assert health["missing_count"] == 2
    assert health["considered_count"] == 3
    assert evidence == snapshot


# --- corpus regressions --------------------------------------------------


def test_mattel_is_not_enrichment_eligible_under_consumable_health():
    """P1S21 Step 11. Mattel's residual gap is stakeholder context plus the
    non-consumable Lean method gap, which is deliberately not counted."""
    record = _corpus_records()[STARVED_JOB_KEYS[0]]
    evidence = build_job_evidence(record)
    health = assess_jd_extraction_health(evidence)

    assert health["populated_categories"] == ["business_context", "workflows"]
    assert health["missing_categories"] == ["stakeholder_context"]
    assert health["missing_count"] == 1
    assert health["enrichment_eligible"] is False

    # the unresolved method gap is recorded, not counted
    assert evidence.required_methods == []
    assert evidence.preferred_methods == []


def test_four_actionable_starved_jobs_are_enrichment_eligible():
    """P1S21 Step 12. These four lack workflows, business and stakeholder
    context - all categories the scorer can consume."""
    records = _corpus_records()
    for key in STARVED_JOB_KEYS[1:]:
        health = assess_jd_extraction_health(build_job_evidence(records[key]))
        assert health["missing_count"] == 3, key
        assert health["enrichment_eligible"] is True, key


def test_healthy_controls_are_not_enrichment_eligible():
    """P1S21 Step 13."""
    records = _corpus_records()
    for key in HEALTHY_CONTROL_JOB_KEYS:
        health = assess_jd_extraction_health(build_job_evidence(records[key]))
        assert health["missing_count"] == 0, key
        assert health["enrichment_eligible"] is False, key


def test_selected_threshold_matches_the_measured_corpus_distribution():
    """P1S21 Steps 4-7. The threshold was chosen from this distribution, and
    the resulting population is stable across the P1S19 vocabulary additions."""
    records = _corpus_records()
    counts = {0: 0, 1: 0, 2: 0, 3: 0}
    eligible = 0
    for record in records.values():
        health = assess_jd_extraction_health(build_job_evidence(record))
        counts[health["missing_count"]] += 1
        eligible += bool(health["enrichment_eligible"])

    assert counts == {0: 13, 1: 25, 2: 22, 3: 20}
    assert eligible == 20
