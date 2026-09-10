"""P1S18 offline deterministic category-validation regressions.

All payloads are local test doubles grounded against authoritative local JDs.
This module performs no provider, embedding, cache, or application-data work.
"""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from src.config.consts import (
    ANALYTICS_ML_SIGNAL_PATTERNS,
    EXPERIMENTATION_SIGNAL_PATTERNS,
    TOOLING_SIGNAL_PATTERNS,
    _BUSINESS_CONTEXT_CANDIDATES,
    _STAKEHOLDER_CONTEXT_CANDIDATES,
    _WORKFLOW_CANDIDATES,
)
from src.matching.jd_intelligence_contract import (
    JD_INTELLIGENCE_MATCHING_CONTRACT_VERSION,
    JD_INTELLIGENCE_MATCHING_ENRICHMENT_FIELDS,
    validate_jd_intelligence_matching_payload,
)
from src.matching.job_adapter import (
    _extract_text_phrase_hits,
    _prune_method_targets,
    build_job_evidence,
    build_job_evidence_enrichment_candidate_v2,
    ground_jd_intelligence_signals_v2,
    merge_missing_job_evidence,
    validate_grounded_jd_intelligence_categories_v2,
)


ROOT = Path(__file__).resolve().parents[1]
CORPUS_SOURCE = ROOT / "outputs/application_planning/current_run_job_corpus.jsonl"

MATTEL = "mattelinc|Staff Data Analyst, Lean and Process Improvement, Co Manufacturing"
OTHER_STARVED = {
    "anthropic|Research Engineer, Code RL (Reinforcement Learning)": (
        "python",
        "verification",
    ),
    "anthropic|Research Engineer, Performance RL (Reinforcement Learning)": (
        "pytorch",
        "distributed systems",
    ),
    "anthropic|Research Engineer, Knowledge Team": ("python", "training"),
    "scaleai|ML Research Engineer, ML Systems": ("pytorch", "inference"),
}


def _corpus_records():
    if not CORPUS_SOURCE.exists():
        pytest.skip("local full application-planning corpus is not present")
    records = {
        f"{record.get('company', '')}|{record.get('title', '')}": record
        for record in (
            json.loads(line)
            for line in CORPUS_SOURCE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    for key in (MATTEL, *OTHER_STARVED):
        assert key in records
    return records


def _verbatim(text, signal):
    start = text.casefold().index(signal.casefold())
    return text[start : start + len(signal)]


def _item(text, signal, *, evidence_span=None):
    return {
        "signal": signal,
        "evidence_span": evidence_span or _verbatim(text, signal),
    }


def _payload(**overrides):
    payload = {
        "contract_version": JD_INTELLIGENCE_MATCHING_CONTRACT_VERSION,
        **{field: [] for field in JD_INTELLIGENCE_MATCHING_ENRICHMENT_FIELDS},
        "domain": [],
        "seniority": [],
        "risk_flags": [],
        "extraction_confidence": 0.9,
    }
    payload.update(overrides)
    return payload


def _offline_chain(payload, record):
    validated_payload, errors = validate_jd_intelligence_matching_payload(payload)
    assert errors == []
    grounded, rejected = ground_jd_intelligence_signals_v2(
        validated_payload, record["retrieval_text"]
    )
    categorized, diagnostics = validate_grounded_jd_intelligence_categories_v2(
        grounded
    )
    candidate = build_job_evidence_enrichment_candidate_v2(categorized)
    return grounded, rejected, categorized, diagnostics, candidate


def _diagnostic_signals(diagnostics, status):
    return {
        item["item"]["signal"] for item in diagnostics.get(status, [])
    }


def test_p1s17_failure_classes_reclassify_only_when_existing_owners_prove_it():
    text = _corpus_records()[MATTEL]["retrieval_text"]
    payload = _payload(
        required_skills=[
            _item(text, "process improvement"),
            _item(text, "Lean methodologies"),
            _item(text, "Excel"),
        ],
        preferred_skills=[
            _item(text, "PowerPoint"),
            _item(text, "Black Belt"),
            _item(text, "contract manufacturing"),
            _item(text, "ERP"),
            _item(text, "Google BigQuery"),
            _item(text, "Power BI"),
        ],
        preferred_tools=[
            _item(text, "Google BigQuery"),
            _item(text, "Power BI"),
        ],
        preferred_methods=[_item(text, "automation tools")],
        required_methods=[_item(text, "change management")],
    )

    grounded, rejected, categorized, diagnostics, candidate = _offline_chain(
        payload, _corpus_records()[MATTEL]
    )

    assert rejected == {}
    assert len(grounded["required_skills"]) == 3
    assert candidate["required_tools"] == ["excel"]
    # P1S19 added powerpoint and erp to TOOLING_SIGNAL_PATTERNS
    assert candidate["preferred_tools"] == ["powerpoint", "erp", "bigquery", "power bi"]
    assert "required_skills" not in candidate
    assert "preferred_skills" not in candidate
    assert "preferred_methods" not in candidate
    assert "required_methods" not in candidate
    assert categorized["required_tools"][0]["evidence_span"] == "excel"

    quarantined = _diagnostic_signals(diagnostics, "quarantined")
    # P1S19 gave process improvement, powerpoint, erp and contract manufacturing
    # real deterministic owners, so they now reclassify instead of quarantining.
    # Lean techniques and the credential stay quarantined by design.
    assert {
        "lean methodologies",
        "black belt",
        "automation tools",
        "change management",
    } <= quarantined
    assert not (
        {"process improvement", "powerpoint", "erp", "contract manufacturing"}
        & quarantined
    )
    reclassified = _diagnostic_signals(diagnostics, "reclassified")
    assert reclassified == {
        "contract manufacturing",
        "erp",
        "excel",
        "powerpoint",
        "process improvement",
    }
    assert any(
        item["reason"] == "duplicate_more_specific_category"
        and item["source_category"] == "preferred_skills"
        for item in diagnostics["quarantined"]
    )


def test_existing_method_vocabulary_exposes_lean_taxonomy_gap_without_guessing():
    text = _corpus_records()[MATTEL]["retrieval_text"]
    observed_methods = (
        "root cause analysis",
        "value stream mapping",
        "standard work",
        "A3 problem solving",
        "5 Whys",
        "Kaizen",
        "SIPOC",
    )
    payload = _payload(
        required_methods=[_item(text, signal) for signal in observed_methods]
    )

    _, rejected, categorized, diagnostics, candidate = _offline_chain(
        payload, _corpus_records()[MATTEL]
    )

    assert rejected == {}
    assert categorized == {}
    assert candidate == {}
    assert _diagnostic_signals(diagnostics, "quarantined") == {
        signal.casefold() for signal in observed_methods
    }
    assert {
        item["reason"] for item in diagnostics["quarantined"]
    } == {"unknown_taxonomy_signal"}


def test_supply_chain_domain_component_reaches_fill_missing_business_context():
    record = _corpus_records()[MATTEL]
    evidence_span = (
        "Experience in consumer products, manufacturing, supply chain, toy "
        "industry, retail supply chain or seasonal product environments."
    )
    assert evidence_span in record["retrieval_text"]
    payload = _payload(
        domain=[
            _item(
                record["retrieval_text"],
                "manufacturing and supply chain",
                evidence_span=evidence_span,
            )
        ]
    )

    grounded, rejected, categorized, diagnostics, candidate = _offline_chain(
        payload, record
    )
    assert rejected == {}
    assert grounded["domain"][0]["signal"] == "manufacturing and supply chain"
    assert categorized["business_contexts"] == [
        {"signal": "supply chain", "evidence_span": evidence_span}
    ]
    assert candidate == {"business_contexts": ["supply chain"]}
    assert diagnostics["reclassified"][0]["reason"] == (
        "reclassified_to_business_context"
    )

    before = replace(build_job_evidence(record), business_contexts=[])
    after = merge_missing_job_evidence(before, candidate)
    assert after.business_contexts == ["supply chain"]
    for field in before.__dataclass_fields__:
        if field != "business_contexts":
            assert getattr(after, field) == getattr(before, field)


def test_correct_categories_survive_and_unknown_grounded_evidence_is_quarantined():
    text = (
        "Required prompt engineering with Python and causal inference. "
        "Own reporting for supply chain stakeholders. "
        "The grounded moonshot capability remains required."
    )
    payload = _payload(
        required_skills=[_item(text, "prompt engineering")],
        required_tools=[_item(text, "Python")],
        required_methods=[_item(text, "causal inference")],
        required_workflows=[_item(text, "reporting")],
        business_contexts=[_item(text, "supply chain")],
        stakeholder_contexts=[_item(text, "stakeholders")],
        ownership_signals=[_item(text, "Own")],
        preferred_skills=[_item(text, "grounded moonshot capability")],
    )
    validated_payload, errors = validate_jd_intelligence_matching_payload(payload)
    assert errors == []
    grounded, rejected = ground_jd_intelligence_signals_v2(validated_payload, text)
    categorized, diagnostics = validate_grounded_jd_intelligence_categories_v2(
        grounded
    )

    assert rejected == {}
    assert {key: values[0]["signal"] for key, values in categorized.items()} == {
        "required_skills": "prompt engineering",
        "required_tools": "python",
        "required_workflows": "reporting",
        "required_methods": "causal inference",
        "business_contexts": "supply chain",
        "stakeholder_contexts": "stakeholders",
        "ownership_signals": "own",
    }
    assert len(diagnostics["kept"]) == 7
    assert _diagnostic_signals(diagnostics, "quarantined") == {
        "grounded moonshot capability"
    }


def test_reclassification_preserves_required_and_preferred_strength():
    text = "Required Excel. Power BI is preferred."
    payload = _payload(
        required_skills=[_item(text, "Excel")],
        preferred_skills=[_item(text, "Power BI")],
    )
    validated_payload, errors = validate_jd_intelligence_matching_payload(payload)
    assert errors == []
    grounded, rejected = ground_jd_intelligence_signals_v2(validated_payload, text)
    categorized, _ = validate_grounded_jd_intelligence_categories_v2(grounded)
    candidate = build_job_evidence_enrichment_candidate_v2(categorized)

    assert rejected == {}
    assert candidate == {
        "required_tools": ["excel"],
        "preferred_tools": ["power bi"],
    }


def test_existing_education_normalizer_yields_specific_quarantine_reason():
    text = "A Bachelor's degree is required."
    payload = _payload(
        required_skills=[_item(text, "Bachelor's degree")],
    )
    validated_payload, errors = validate_jd_intelligence_matching_payload(payload)
    assert errors == []
    grounded, rejected = ground_jd_intelligence_signals_v2(validated_payload, text)
    categorized, diagnostics = validate_grounded_jd_intelligence_categories_v2(
        grounded
    )

    assert rejected == {}
    assert categorized == {}
    assert diagnostics["quarantined"][0]["reason"] == (
        "unsupported_matching_category:education"
    )


def test_validator_is_pure_and_does_not_mutate_grounded_input():
    grounded = {
        "required_skills": [
            {"signal": "Excel", "evidence_span": "Excel"}
        ]
    }
    before = deepcopy(grounded)
    first = validate_grounded_jd_intelligence_categories_v2(grounded)
    second = validate_grounded_jd_intelligence_categories_v2(grounded)

    assert grounded == before
    assert first == second


def test_mattel_full_jd_offline_chain_blocks_category_leakage_and_safe_merges():
    record = _corpus_records()[MATTEL]
    text = record["retrieval_text"]
    assert len(text) == 11_479
    domain_span = (
        "Experience in consumer products, manufacturing, supply chain, toy "
        "industry, retail supply chain or seasonal product environments."
    )
    payload = _payload(
        required_skills=[
            _item(text, "applied AI"),
            _item(text, "process improvement"),
            _item(text, "Excel"),
            _item(text, "root cause analysis"),
        ],
        preferred_skills=[
            _item(text, "Google BigQuery"),
            _item(text, "Power BI"),
            _item(text, "Black Belt"),
        ],
        preferred_tools=[
            _item(text, "Google BigQuery"),
            _item(text, "Power BI"),
        ],
        required_workflows=[_item(text, "reporting")],
        business_contexts=[_item(text, "supply chain")],
        stakeholder_contexts=[_item(text, "Engineering")],
        ownership_signals=[_item(text, "Own")],
        domain=[
            _item(
                text,
                "manufacturing and supply chain",
                evidence_span=domain_span,
            )
        ],
    )

    grounded, rejected, categorized, diagnostics, candidate = _offline_chain(
        payload, record
    )
    assert rejected == {}
    assert sum(map(len, grounded.values())) == 14
    assert candidate == {
        "required_skills": ["applied ai"],
        "required_tools": ["excel"],
        "preferred_tools": ["bigquery", "power bi"],
        # P1S19 added "process improvement" to _WORKFLOW_CANDIDATES
        "required_workflows": ["process improvement", "reporting"],
        "business_contexts": ["supply chain"],
        "stakeholder_contexts": ["engineering"],
        "ownership_signals": ["own"],
    }
    assert not (
        set(candidate.get("required_skills", []))
        & {"excel", "root cause analysis", "process improvement"}
    )
    # P1S19: "process improvement" is now a recognised workflow, so only the
    # still-unowned method and credential signals remain quarantined.
    assert _diagnostic_signals(diagnostics, "quarantined") >= {
        "root cause analysis",
        "black belt",
    }
    assert "process improvement" not in _diagnostic_signals(diagnostics, "quarantined")

    deterministic = build_job_evidence(record)
    before = replace(
        deterministic,
        required_skills=[],
        required_tools=[],
        preferred_tools=[],
        required_workflows=[],
        business_contexts=[],
        stakeholder_contexts=[],
        ownership_signals=[],
    )
    after = merge_missing_job_evidence(before, candidate)
    for field, values in candidate.items():
        assert getattr(after, field) == values
    for field in before.__dataclass_fields__:
        if getattr(before, field):
            assert getattr(after, field) == getattr(before, field)
    assert categorized


@pytest.mark.parametrize("job_key", tuple(OTHER_STARVED))
def test_other_starved_full_jds_apply_same_keep_reclassify_quarantine_policy(job_key):
    record = _corpus_records()[job_key]
    text = record["retrieval_text"]
    tool, unknown = OTHER_STARVED[job_key]
    payload = _payload(
        required_skills=[_item(text, tool), _item(text, unknown)],
        stakeholder_contexts=[_item(text, "leaders")],
    )

    _, rejected, _, diagnostics, candidate = _offline_chain(payload, record)

    assert rejected == {}
    assert candidate["required_tools"] == [tool]
    assert candidate["stakeholder_contexts"] == ["leaders"]
    assert "required_skills" not in candidate
    assert unknown in _diagnostic_signals(diagnostics, "quarantined")
    assert tool in _diagnostic_signals(diagnostics, "reclassified")


def test_validator_has_no_automatic_production_call_site():
    symbol = "validate_grounded_jd_intelligence_categories_v2"
    production_python = list((ROOT / "src").rglob("*.py"))
    owner = ROOT / "src/matching/job_adapter.py"
    occurrences = {
        path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8").count(
            symbol
        )
        for path in production_python
        if symbol in path.read_text(encoding="utf-8")
    }
    assert occurrences == {owner.relative_to(ROOT).as_posix(): 1}


def test_full_80_job_corpus_reports_current_owner_vocabulary_coverage():
    records = list(_corpus_records().values())
    assert len(records) == 80
    owners = {
        "tools": TOOLING_SIGNAL_PATTERNS,
        "methods": (
            ANALYTICS_ML_SIGNAL_PATTERNS + EXPERIMENTATION_SIGNAL_PATTERNS
        ),
        "workflows": _WORKFLOW_CANDIDATES,
        "business_contexts": _BUSINESS_CONTEXT_CANDIDATES,
        "stakeholder_contexts": _STAKEHOLDER_CONTEXT_CANDIDATES,
    }
    coverage = {}
    for category, vocabulary in owners.items():
        hit_counts = []
        distinct = set()
        for record in records:
            text = record["retrieval_text"]
            hits = _extract_text_phrase_hits(text, vocabulary)
            if category == "methods":
                hits = _prune_method_targets(
                    hits,
                    _extract_text_phrase_hits(text, _WORKFLOW_CANDIDATES),
                )
            hit_counts.append(len(hits))
            distinct.update(hits)
        coverage[category] = (
            sum(count > 0 for count in hit_counts),
            sum(hit_counts),
            len(distinct),
        )

    # (jobs with >=1 hit, per-job unique hits, corpus-distinct vocabulary hits)
    assert coverage == {
        # P1S19 vocabulary additions: +2 tools, +1 workflow, +3 business contexts
        "tools": (63, 194, 31),
        "methods": (58, 114, 15),
        "workflows": (59, 117, 19),
        "business_contexts": (43, 92, 16),
        "stakeholder_contexts": (80, 341, 12),
    }


# --- P1S19: measured vocabulary additions to existing deterministic owners.
#
# Only the owners with no scorer coupling were extended. ANALYTICS_ML_SIGNAL_PATTERNS
# and EXPERIMENTATION_SIGNAL_PATTERNS are read directly by _score_analytics_ml_depth
# and _score_experimentation_alignment, so adding Lean/process-improvement
# techniques there would reclassify resume evidence into those dimensions. The
# method gap is therefore left open rather than closed unsafely.

from src.matching.job_adapter import _jd_category_hits  # noqa: E402


def _single_owner(signal):
    return {name for name, hits in _jd_category_hits(signal).items() if hits}


def test_p1s19_added_terms_resolve_to_exactly_one_deterministic_owner():
    for signal, owner in (
        ("process improvement", "workflow"),
        ("powerpoint", "tool"),
        ("erp", "tool"),
        ("contract manufacturing", "business_context"),
        ("procurement", "business_context"),
        ("consumer products", "business_context"),
    ):
        assert _single_owner(signal) == {owner}, (signal, _single_owner(signal))


def test_p1s19_leaves_the_method_gap_open_because_method_owners_feed_the_scorer():
    """Lean techniques stay unrecognized on purpose. The only existing method
    owners are the analytics/experimentation vocabularies the scorer reads, so
    adding them there would change analytics_ml_depth / experimentation_depth."""
    for technique in (
        "root cause analysis",
        "value stream mapping",
        "standard work",
        "a3 problem solving",
        "5 whys",
        "kaizen",
        "sipoc",
        "lean methodologies",
    ):
        assert _single_owner(technique) == set(), technique

    scorer = (ROOT / "src/matching/scorer.py").read_text(encoding="utf-8")
    assert "ANALYTICS_ML_SIGNAL_PATTERNS" in scorer
    assert "EXPERIMENTATION_SIGNAL_PATTERNS" in scorer


def test_p1s19_credential_recognition_remains_deferred():
    """No existing matching-side credential owner, so Black Belt stays an
    unknown quarantine rather than being forced into a skill or tool."""
    assert _single_owner("black belt") == set()


def test_p1s19_ambiguous_process_terms_are_not_forced_into_a_taxonomy():
    """Only 'process improvement' had a clear single-category intent in the
    measured case; the rest stay quarantined instead of being duplicated."""
    for ambiguous in ("lean", "continuous improvement", "standard work"):
        assert _single_owner(ambiguous) == set(), ambiguous


def test_p1s19_added_terms_do_not_create_broad_corpus_false_positives():
    """Each added term was measured against the authoritative corpus first."""
    import json

    corpus = ROOT / "outputs/application_planning/current_run_job_corpus.jsonl"
    if not corpus.exists():
        pytest.skip("local application-planning corpus is not present")

    from src.matching.job_adapter import _normalize_text, _skill_present

    records = [
        json.loads(line)
        for line in corpus.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for term, max_jobs in (
        ("process improvement", 2),
        ("powerpoint", 3),
        ("erp", 2),
        ("contract manufacturing", 2),
        ("procurement", 2),
        ("consumer products", 2),
    ):
        matched = sum(
            1
            for record in records
            if _skill_present(
                _normalize_text(
                    f"{record.get('title', '')} {record.get('retrieval_text', '')}"
                ).lower(),
                term,
            )
        )
        assert matched <= max_jobs, f"{term} matched {matched} jobs"


# --- P1S23: context-category admission precision.
#
# P1S22's live Code RL proof produced exactly one wrong-category survivor: the
# stakeholder term "engineering" was admitted from "strong software-engineering
# skills" and from "long-horizon autonomous engineering", neither of which names
# a group. Both matched because the context matcher accepted a vocabulary term
# found anywhere inside a longer signal. Admission now requires the term to fill
# a whole coordination segment. No vocabulary was added.

from src.matching.job_adapter import (  # noqa: E402
    _jd_context_segment_hits,
    assess_jd_extraction_health,
)

CODE_RL = "anthropic|Research Engineer, Code RL (Reinforcement Learning)"


def _hits(signal):
    return _jd_category_hits(signal)


def test_p1s23_case_a_software_engineering_skill_is_not_a_stakeholder():
    """A. The live defect. The model correctly proposed a required skill; the
    validator must never turn it into stakeholder context via the embedded
    token. Quarantine is the correct outcome — 'strong software-engineering
    skills' has no deterministic owner in any category."""
    record = _corpus_records()[CODE_RL]
    span = "Have strong software-engineering skills"
    assert span in record["retrieval_text"]

    assert "stakeholder_context" not in _hits("strong software-engineering skills")
    assert _hits("strong software-engineering skills") == {}

    payload = _payload(
        required_skills=[
            _item(record["retrieval_text"], "strong software-engineering skills",
                  evidence_span=span)
        ]
    )
    grounded, rejected, categorized, diagnostics, candidate = _offline_chain(
        payload, record
    )
    # Grounding is unchanged: the span still supports the signal.
    assert rejected == {}
    assert grounded["required_skills"][0]["signal"] == (
        "strong software-engineering skills"
    )
    assert categorized == {}
    assert candidate == {}
    assert _diagnostic_signals(diagnostics, "quarantined") == {
        "strong software-engineering skills"
    }
    assert diagnostics["quarantined"][0]["reason"] == "unknown_taxonomy_signal"
    assert diagnostics["kept"] == [] and diagnostics["reclassified"] == []


def test_p1s23_case_b_autonomous_engineering_work_is_not_a_stakeholder():
    """B. The same collision on a trailing head rather than a hyphenated
    compound, so a word-boundary fix alone would not have caught it."""
    record = _corpus_records()[CODE_RL]
    span = "to long-horizon autonomous engineering"
    assert span in record["retrieval_text"]

    assert _hits("long-horizon autonomous engineering") == {}

    payload = _payload(
        preferred_workflows=[
            _item(record["retrieval_text"], "long-horizon autonomous engineering",
                  evidence_span=span)
        ]
    )
    _, rejected, categorized, diagnostics, candidate = _offline_chain(
        payload, record
    )
    assert rejected == {}
    assert categorized == {}
    assert candidate == {}
    assert _diagnostic_signals(diagnostics, "quarantined") == {
        "long-horizon autonomous engineering"
    }
    assert "stakeholder_contexts" not in categorized


def test_p1s23_genuine_direct_context_signals_still_classify():
    """Positive control: the fix must not disable context classification. Every
    term here is an existing vocabulary member used as its own whole signal."""
    assert _hits("Engineering") == {"stakeholder_context": ["engineering"]}
    assert _hits("stakeholders") == {"stakeholder_context": ["stakeholders"]}
    assert _hits("leaders") == {"stakeholder_context": ["leaders"]}
    assert _hits("executive") == {"stakeholder_context": ["executive"]}
    assert _hits("procurement") == {"business_context": ["procurement"]}
    assert _hits("contract manufacturing") == {
        "business_context": ["contract manufacturing"]
    }
    # Terms owned by more than one context vocabulary keep every owner.
    assert _hits("customer success") == {
        "business_context": ["customer success"],
        "stakeholder_context": ["customer success"],
    }


def test_p1s23_coordinated_context_components_are_still_projected():
    """P1S18's composite projection is the behavior the fix must not break: a
    known term filling one member of a coordinated list stays admissible."""
    assert _jd_context_segment_hits(
        "manufacturing and supply chain", list(_BUSINESS_CONTEXT_CANDIDATES)
    ) == ["supply chain"]
    assert _hits("manufacturing and supply chain")["business_context"] == [
        "supply chain"
    ]
    # Commas, slashes and "or" separate members exactly as "and" does.
    for phrase in (
        "manufacturing, supply chain",
        "manufacturing / supply chain",
        "manufacturing or supply chain",
    ):
        assert _hits(phrase)["business_context"] == ["supply chain"], phrase


def test_p1s23_corpus_reproduced_context_collisions_are_blocked():
    """The defect class is wider than 'engineering'. Every phrase below is drawn
    from the authoritative 80-job corpus, where the term appears inside a
    compound that does not name a context or group."""
    for phrase in (
        "product-minded approach",
        "product-focused environment",
        "product- and impact-oriented",
        "pre-sales solution engineer",
        "reverse-engineering neural networks",
        "high-growth environment",
        "high-risk activities",
        "misalignment-risk safety cases",
        "operations-research depth",
    ):
        hits = _hits(phrase)
        assert "stakeholder_context" not in hits, (phrase, hits)
        assert "business_context" not in hits, (phrase, hits)
        assert "domain" not in hits, (phrase, hits)


def test_p1s23_prompt_engineering_keeps_its_skill_owner_only():
    """The only deterministic target in the 80-job corpus whose classification
    the fix changes. It loses a spurious stakeholder owner and keeps its skill
    owner, so the signal becomes unambiguous rather than unrecognized."""
    assert _hits("prompt engineering") == {"skill": ["prompt engineering"]}


def test_p1s23_non_context_categories_are_untouched():
    """Tool, ownership and workflow admission keep their existing containment
    behavior; only the three context categories changed."""
    assert _hits("python") == {"tool": ["python"]}
    assert _hits("PyTorch") == {"tool": ["pytorch"]}
    assert _hits("own systems end to end") == {"ownership_signal": ["own"]}
    assert _hits("process improvement") == {"workflow": ["process improvement"]}


# The exact signals and evidence spans the live P1S22 GPT-5 Mini call produced.
# Reconstructed as literals; the captured scratch payload is not a fixture.
_P1S22_CODE_RL_SIGNALS = {
    "required_skills": [
        ("python", "Required skills: python"),
        ("strong software-engineering skills",
         "Have strong software-engineering skills"),
        ("async/concurrent programming", "including async/concurrent programming"),
    ],
    "preferred_skills": [
        ("reinforcement learning", "Experience with reinforcement learning"),
        ("RLHF",
         "Experience with reinforcement learning, RLHF, post-training, or LLM finetuning"),
        ("post-training",
         "Experience with reinforcement learning, RLHF, post-training, or LLM finetuning"),
        ("LLM finetuning",
         "Experience with reinforcement learning, RLHF, post-training, or LLM finetuning"),
        ("built coding agents",
         "Built coding agents, code-execution sandboxes, eval harnesses, verifiers, or developer tooling"),
        ("code-execution sandboxes",
         "Built coding agents, code-execution sandboxes, eval harnesses, verifiers, or developer tooling"),
        ("eval harnesses",
         "Built coding agents, code-execution sandboxes, eval harnesses, verifiers, or developer tooling"),
        ("verifiers",
         "Built coding agents, code-execution sandboxes, eval harnesses, verifiers, or developer tooling"),
    ],
    "preferred_tools": [
        ("PyTorch", "Experience with PyTorch and large-scale distributed training"),
        ("CUDA / GPU or TPU",
         "CUDA / GPU or TPU kernel experience and accelerator-performance intuition"),
    ],
    "required_workflows": [
        ("design RL environments and coding tasks",
         "You'll design RL environments and coding tasks"),
        ("build the reward signals and verifiers",
         'build the reward signals and verifiers that capture what "good code" means'),
        ("run training experiments on frontier models",
         "run training experiments on frontier models"),
        ("diagnose why a model does (or doesn't) get better",
         "diagnose why a model does (or doesn't) get better at a class of software-engineering work"),
        ("improve the speed and reliability of the pipelines",
         "improve the speed and reliability of the pipelines that make all of that iterate fast"),
        ("owning systems end to end and debugging across the stack",
         "Are comfortable owning systems end to end and debugging across the stack"),
    ],
    "preferred_workflows": [
        ("building high-performance code for accelerators",
         "to high-performance code for accelerators"),
        ("long-horizon autonomous engineering",
         "to long-horizon autonomous engineering"),
    ],
    "preferred_methods": [
        ("program analysis",
         "Background in program analysis, testing, verification, compilers, or formal methods"),
        ("testing",
         "Background in program analysis, testing, verification, compilers, or formal methods"),
        ("verification",
         "Background in program analysis, testing, verification, compilers, or formal methods"),
        ("compilers",
         "Background in program analysis, testing, verification, compilers, or formal methods"),
        ("formal methods",
         "Background in program analysis, testing, verification, compilers, or formal methods"),
        ("performance profiling and optimization of ML systems",
         "performance profiling and optimization of ML systems"),
    ],
    "business_contexts": [
        ("Reinforcement Learning teams",
         "Our Reinforcement Learning teams play a critical role"),
        ("applied production training",
         "We partner with the applied production training team"),
    ],
    "stakeholder_contexts": [
        ("alignment and frontier red teams",
         "We collaborate closely with Anthropic's alignment and frontier red teams"),
        ("applied production training team",
         "We partner with the applied production training team"),
    ],
    "ownership_signals": [
        ("own systems end to end", "Are comfortable owning systems end to end"),
        ("we will make every reasonable effort to get you a visa",
         "But if we make you an offer, we will make every reasonable effort to get you a visa"),
    ],
    "domain": [
        ("Reinforcement Learning",
         "We're hiring for the Code RL team within the RL organization"),
    ],
}


def _p1s22_payload():
    return _payload(
        **{
            category: [
                {"signal": signal, "evidence_span": span}
                for signal, span in items
            ]
            for category, items in _P1S22_CODE_RL_SIGNALS.items()
        }
    )


def test_p1s23_live_p1s22_payload_yields_zero_wrong_category_survivors():
    """The whole live result, replayed offline through unchanged grounding and
    the corrected validator. Before the fix this produced one wrong-category
    survivor; now every survivor is independently confirmed by its own owner."""
    record = _corpus_records()[CODE_RL]
    grounded, rejected, categorized, diagnostics, candidate = _offline_chain(
        _p1s22_payload(), record
    )

    # Grounding semantics are untouched: the same two over-reaching signals.
    assert sum(len(items) for items in grounded.values()) == 32
    assert {
        item["item"]["signal"]
        for items in rejected.values()
        for item in items
    } == {
        "building high-performance code for accelerators",
        "Reinforcement Learning",
    }

    survivors = {
        (decision["destination_category"], decision["item"]["signal"])
        for decision in diagnostics["kept"] + diagnostics["reclassified"]
    }
    # P1S24 added the three group-headed stakeholder phrases. The wrong-category
    # count this test guards stays at zero: no survivor carries the bare
    # "engineering" token the P1S22 defect produced.
    assert survivors == {
        ("required_tools", "python"),
        ("preferred_tools", "pytorch"),
        ("ownership_signals", "own"),
        ("stakeholder_contexts", "reinforcement learning teams"),
        ("stakeholder_contexts", "frontier red teams"),
        ("stakeholder_contexts", "applied production training team"),
    }
    assert "engineering" not in {signal for _, signal in survivors}
    assert candidate == {
        "required_tools": ["python"],
        "preferred_tools": ["pytorch"],
        "stakeholder_contexts": [
            "reinforcement learning teams",
            "frontier red teams",
            "applied production training team",
        ],
        "ownership_signals": ["own"],
    }
    assert len(diagnostics["quarantined"]) == 26
    assert {
        decision["reason"] for decision in diagnostics["quarantined"]
    } == {"unknown_taxonomy_signal"}


def test_p1s23_code_rl_extraction_health_stays_honestly_starved():
    """P1S23 left Code RL at 3/3 missing because nothing consumable survived.
    P1S24's supplemental recognition recovers stakeholder context from three
    genuine group references, so the count drops to 2/3 — this time on audited
    correct evidence rather than the P1S22 false stakeholder."""
    record = _corpus_records()[CODE_RL]
    _, _, _, _, candidate = _offline_chain(_p1s22_payload(), record)

    before = build_job_evidence(record)
    after = merge_missing_job_evidence(before, candidate)

    assert assess_jd_extraction_health(before) == {
        "populated_categories": [],
        "missing_categories": [
            "business_context",
            "stakeholder_context",
            "workflows",
        ],
        "missing_count": 3,
        "considered_count": 3,
        "threshold": 3,
        "enrichment_eligible": True,
    }
    assert assess_jd_extraction_health(after) == {
        "populated_categories": ["stakeholder_context"],
        "missing_categories": ["business_context", "workflows"],
        "missing_count": 2,
        "considered_count": 3,
        "threshold": 3,
        "enrichment_eligible": False,
    }

    # Only empty groups were filled; nothing deterministic was overwritten.
    assert before.preferred_tools == [] and after.preferred_tools == ["pytorch"]
    assert before.ownership_signals == [] and after.ownership_signals == ["own"]
    assert before.required_tools == ["python"] == after.required_tools
    assert before.stakeholder_contexts == []
    assert after.stakeholder_contexts == [
        "reinforcement learning teams",
        "frontier red teams",
        "applied production training team",
    ]
    # Workflows and business context are still genuinely unrecovered.
    for field in ("required_workflows", "preferred_workflows",
                  "business_contexts"):
        assert getattr(after, field) == getattr(before, field) == []


def test_p1s23_does_not_change_deterministic_job_evidence():
    """The correction lives only in the validator's category matcher, which
    build_job_evidence never calls, so deterministic extraction is unaffected
    across the whole authoritative corpus."""
    source = (ROOT / "src/matching/job_adapter.py").read_text(encoding="utf-8")
    body = source.split("def build_job_evidence(")[1].split(
        "\ndef build_job_evidence_batch("
    )[0]
    assert "_jd_category_hits" not in body
    assert "_jd_context_segment_hits" not in body

    baseline = json.loads(
        (
            ROOT / "tests/fixtures/p1s3_jd_evidence/corpus_jobevidence_baseline.json"
        ).read_text(encoding="utf-8")
    )
    records = _corpus_records()
    assert len(records) == 80
    assert len(baseline["jobs"]) == 80
    for expected in baseline["jobs"]:
        key = expected["job_key"]
        evidence = build_job_evidence(records[key])
        for field, value in expected.items():
            if field in ("job_key", "role_family", "kpi_metrics"):
                continue
            assert getattr(evidence, field) == value, (key, field)


# --- P1S24: validator-only supplemental stakeholder recognition.
#
# P1S22 proved the model finds genuine, verbatim-grounded group references that
# no shared vocabulary owns. Rather than expanding _STAKEHOLDER_CONTEXT_CANDIDATES
# — which P1S19 proved would move deterministic JobEvidence, scorer inputs and
# fallback eligibility — recognition is structural and lives only in the
# validator's matcher: a coordination segment whose head noun is "team"/"teams",
# built from content words, names a group and is projected verbatim.

from src.matching.job_adapter import (  # noqa: E402
    _JD_SUPPLEMENTAL_FUNCTION_WORDS,
    _JD_SUPPLEMENTAL_STAKEHOLDER_HEADS,
    _jd_supplemental_stakeholder_hits,
)


def test_p1s24_recognizes_the_three_proven_p1s22_group_references():
    """The exact grounded signals P1S22 quarantined for lack of an owner."""
    assert _hits("alignment and frontier red teams") == {
        "stakeholder_context": ["frontier red teams"]
    }
    assert _hits("applied production training team") == {
        "stakeholder_context": ["applied production training team"]
    }
    # Proposed by the model as a business context; the only supported owner is
    # stakeholder context, so the validator reclassifies rather than keeps.
    assert _hits("reinforcement learning teams") == {
        "stakeholder_context": ["reinforcement learning teams"]
    }


def test_p1s24_projects_the_whole_segment_not_an_embedded_term():
    """The structural difference from the P1S22 defect: the phrase is
    recognized as a whole by its head, so no sub-term is ever extracted."""
    assert _jd_supplemental_stakeholder_hits("frontier red teams") == [
        "frontier red teams"
    ]
    assert _jd_supplemental_stakeholder_hits(
        "alignment and frontier red teams"
    ) == ["frontier red teams"]
    assert _JD_SUPPLEMENTAL_STAKEHOLDER_HEADS == {"team", "teams"}


def test_p1s24_does_not_reopen_the_p1s23_containment_defects():
    """Every phrase P1S23 blocked must still be unrecognized."""
    for phrase in (
        "strong software-engineering skills",
        "long-horizon autonomous engineering",
        "product-minded approach",
        "product-focused environment",
        "pre-sales solution engineer",
        "reverse-engineering neural networks",
        "high-growth environment",
        "high-risk activities",
        "misalignment-risk safety cases",
        "operations-research depth",
    ):
        assert _hits(phrase) == {}, phrase
        assert _jd_supplemental_stakeholder_hits(phrase) == [], phrase


def test_p1s24_group_head_guards_reject_prose_and_bare_heads():
    """A bare head carries no information and prose is not a group name. Both
    the token bounds and the closed function-word class are load-bearing."""
    for phrase in (
        "team",
        "teams",                       # bare head
        "join our team",
        "the team",
        "about the rl teams",
        "our reinforcement learning teams",
        "a cross-functional team",     # determiners and possessives
        "automate real work across teams",
        "build lasting relationships across teams",
        "that transcends any single team",
        "you will join our engineering team in a hybrid setting",
    ):
        assert _jd_supplemental_stakeholder_hits(phrase) == [], phrase
    assert {"our", "the", "a"} <= _JD_SUPPLEMENTAL_FUNCTION_WORDS
    assert {"about", "across", "this", "any"} <= _JD_SUPPLEMENTAL_FUNCTION_WORDS


def test_p1s24_shared_context_recognition_is_unchanged():
    """Supplemental recognition is additive; every shared owner still behaves
    exactly as P1S19 and P1S23 left it."""
    assert _hits("stakeholders") == {"stakeholder_context": ["stakeholders"]}
    assert _hits("Engineering") == {"stakeholder_context": ["engineering"]}
    assert _hits("leaders") == {"stakeholder_context": ["leaders"]}
    assert _hits("manufacturing and supply chain")["business_context"] == [
        "supply chain"
    ]
    assert _hits("procurement") == {"business_context": ["procurement"]}
    assert _hits("python") == {"tool": ["python"]}
    assert _hits("own systems end to end") == {"ownership_signal": ["own"]}


def test_p1s24_methods_gain_no_supplemental_owner():
    """P1S20 remains authoritative: generic methods stay outside the fallback."""
    for method in (
        "program analysis",
        "testing",
        "verification",
        "compilers",
        "formal methods",
        "performance profiling and optimization of ml systems",
    ):
        assert _hits(method) == {}, method
        assert _jd_supplemental_stakeholder_hits(method) == [], method


def test_p1s24_supplemental_owner_is_structurally_validator_only():
    """The architectural gate. The inventory lives in the matching owner, not in
    shared config, and is reachable only through the grounded-category
    validator, so it cannot touch baseline extraction or scoring."""
    adapter = ROOT / "src/matching/job_adapter.py"
    source = adapter.read_text(encoding="utf-8")

    # Not in shared config, which baseline extraction and the scorer read.
    consts = (ROOT / "src/config/consts.py").read_text(encoding="utf-8")
    for symbol in (
        "_JD_SUPPLEMENTAL_STAKEHOLDER_HEADS",
        "_jd_supplemental_stakeholder_hits",
    ):
        assert symbol not in consts

    # Exactly one production owner.
    production = [
        path
        for path in (ROOT / "src").rglob("*.py")
        if "_jd_supplemental_stakeholder_hits" in path.read_text(encoding="utf-8")
    ]
    assert production == [adapter]

    # Its only caller is _jd_category_hits, whose only caller is the validator.
    body = source.split("def _jd_category_hits(")[1].split("\ndef _jd_source_strength(")[0]
    assert "_jd_supplemental_stakeholder_hits(normalized)" in body
    assert source.count("_jd_supplemental_stakeholder_hits(") == 2  # def + call

    evidence_body = source.split("def build_job_evidence(")[1].split(
        "\ndef build_job_evidence_batch("
    )[0]
    for symbol in (
        "_jd_supplemental_stakeholder_hits",
        "_JD_SUPPLEMENTAL_STAKEHOLDER_HEADS",
        "_jd_category_hits",
    ):
        assert symbol not in evidence_body

    health_body = source.split("def assess_jd_extraction_health(")[1]
    assert "_jd_supplemental" not in health_body


def test_p1s24_has_no_effect_without_a_provider_payload():
    """Zero-payload isolation across the whole authoritative corpus: baseline
    JobEvidence and every P1S21 PRE extraction-health report are unchanged."""
    baseline = json.loads(
        (
            ROOT / "tests/fixtures/p1s3_jd_evidence/corpus_jobevidence_baseline.json"
        ).read_text(encoding="utf-8")
    )
    records = _corpus_records()
    assert len(baseline["jobs"]) == 80

    distribution = {}
    for expected in baseline["jobs"]:
        evidence = build_job_evidence(records[expected["job_key"]])
        for field, value in expected.items():
            if field in ("job_key", "role_family", "kpi_metrics"):
                continue
            assert getattr(evidence, field) == value, (expected["job_key"], field)
        report = assess_jd_extraction_health(evidence)
        distribution[report["missing_count"]] = (
            distribution.get(report["missing_count"], 0) + 1
        )

    # The P1S21 measured distribution and 20-job activation set are unmoved.
    assert distribution == {0: 13, 1: 25, 2: 22, 3: 20}


def test_p1s24_recognition_is_not_code_rl_specific():
    """Cross-job reuse: group phrasings drawn verbatim from other corpus JDs are
    recognized by the same rule, so the inventory is not a Code RL special case."""
    records = _corpus_records()
    corpus_text = " ".join(
        record["retrieval_text"].lower() for record in records.values()
    )
    for phrase in (
        "product teams",
        "business teams",
        "engineering teams",
        "analytics team",
        "policy teams",
        "infrastructure teams",
        "go-to-market teams",
        "machine learning teams",
    ):
        assert phrase in corpus_text, phrase
        assert _jd_supplemental_stakeholder_hits(phrase) == [phrase], phrase
        assert _hits(phrase)["stakeholder_context"] == [phrase], phrase
