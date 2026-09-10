"""Offline matching-v2 contract, grounding, and taxonomy regressions.

The regression payloads are deterministic test doubles derived from the P1S11
failure classes. They are grounded against the full local authoritative corpus;
no provider, model, embedding, cache, or application-data path is invoked.
"""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from src.matching.jd_intelligence_contract import (
    JD_INTELLIGENCE_MATCHING_CATEGORY_MAX_ITEMS,
    JD_INTELLIGENCE_MATCHING_CONTRACT_VERSION,
    JD_INTELLIGENCE_MATCHING_ENRICHMENT_FIELDS,
    JD_INTELLIGENCE_MATCHING_EVIDENCE_SPAN_MAX_LENGTH,
    JD_INTELLIGENCE_MATCHING_PROMPT_VERSION,
    JD_INTELLIGENCE_MATCHING_PROVENANCE_FIELDS,
    JD_INTELLIGENCE_MATCHING_RESPONSE_SCHEMA,
    JD_INTELLIGENCE_MATCHING_SCHEMA_NAME,
    JD_INTELLIGENCE_MATCHING_SIGNAL_MAX_LENGTH,
    JD_INTELLIGENCE_MATCHING_SYSTEM_PROMPT,
    build_jd_intelligence_matching_prompt,
    jd_intelligence_matching_structured_output_contract,
    validate_jd_intelligence_matching_payload,
)
from src.matching.job_adapter import (
    JD_INTELLIGENCE_V2_CANDIDATE_FIELD_MAP,
    build_job_evidence,
    build_job_evidence_enrichment_candidate_v2,
    ground_jd_intelligence_signals_v2,
    merge_missing_job_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
CORPUS_SOURCE = ROOT / "outputs/application_planning/current_run_job_corpus.jsonl"

MATTEL = "mattelinc|Staff Data Analyst, Lean and Process Improvement, Co Manufacturing"
CODE_RL = "anthropic|Research Engineer, Code RL (Reinforcement Learning)"
PERFORMANCE_RL = "anthropic|Research Engineer, Performance RL (Reinforcement Learning)"
KNOWLEDGE = "anthropic|Research Engineer, Knowledge Team"
SCALE = "scaleai|ML Research Engineer, ML Systems"


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
    for key in (MATTEL, CODE_RL, PERFORMANCE_RL, KNOWLEDGE, SCALE):
        assert key in records
    return records


def _item(signal, evidence_span):
    return {"signal": signal, "evidence_span": evidence_span}


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


def _ground(payload, record):
    validated, errors = validate_jd_intelligence_matching_payload(payload)
    assert errors == []
    assert validated == payload
    return ground_jd_intelligence_signals_v2(validated, record["retrieval_text"])


def test_v2_contract_is_strict_bounded_and_versioned_separately_from_v1():
    from src.app import services

    contract = jd_intelligence_matching_structured_output_contract()
    assert contract["name"] == JD_INTELLIGENCE_MATCHING_SCHEMA_NAME
    assert contract["strict"] is True
    assert contract["schema"] == JD_INTELLIGENCE_MATCHING_RESPONSE_SCHEMA
    assert JD_INTELLIGENCE_MATCHING_PROMPT_VERSION == (
        "v2_verbatim_required_preferred_taxonomy"
    )
    assert contract["schema"]["additionalProperties"] is False

    for field in (
        *JD_INTELLIGENCE_MATCHING_ENRICHMENT_FIELDS,
        "domain",
        "seniority",
    ):
        item_schema = contract["schema"]["properties"][field]["items"]
        assert item_schema["additionalProperties"] is False
        assert item_schema["required"] == ["signal", "evidence_span"]
        assert item_schema["properties"]["signal"]["maxLength"] == 128
        assert item_schema["properties"]["evidence_span"]["maxLength"] == 160

    # New Scan/manual v1 remains byte/behavior compatible and separate.
    assert services.LIVE_JD_INTELLIGENCE_DRY_RUN_SCHEMA_NAME == (
        "live_jd_intelligence_dry_run_v1"
    )
    assert services.LIVE_JD_INTELLIGENCE_DRY_RUN_PROMPT_VERSION == "v1"
    assert "workflows" in services.LIVE_JD_INTELLIGENCE_DRY_RUN_RESPONSE_SCHEMA[
        "properties"
    ]
    assert "required_workflows" not in (
        services.LIVE_JD_INTELLIGENCE_DRY_RUN_RESPONSE_SCHEMA["properties"]
    )


def test_v2_prompt_states_every_grounding_and_classification_rule():
    prompt = JD_INTELLIGENCE_MATCHING_SYSTEM_PROMPT
    required_phrases = (
        "only the full job description",
        "only signals explicitly supported",
        "short evidence_span verbatim",
        "lexically close to its evidence span",
        "instead of substituting synonyms",
        "Classify each signal once in its most specific allowed category",
        "never use skills as a catch-all",
        "Skills are capabilities, competencies, or bodies of knowledge",
        "Tools are named software, platforms, technologies, applications, systems",
        "Methods are named analytical, scientific, statistical",
        "Workflows are recurring responsibilities, processes, or work activities",
        "Business contexts are functional or operating environments",
        "Stakeholder contexts are people, groups, or functions collaborated with",
        "Domain is the one broader industry or subject-matter domain",
        "Ownership signals require explicit ownership or accountability language",
        "prefer tool, then method, then workflow, then business context",
        "A named system is a tool",
        "operating-domain experience is not a tool",
        "A named methodology or technique is a method",
        "experience in an industry or operating context is not a skill",
        "Do not duplicate semantic equivalents across categories",
        "Omit degrees, education, certifications, and credentials",
        "Distinguish required from preferred",
        "responsibilities, must-haves, required or minimum qualifications",
        "explicit expectations or equivalent mandatory language",
        "preferred, nice-to-have, bonus, strong-candidate, desired, plus",
        "Do not infer required from apparent importance",
        "preferred from late placement alone",
        "Never strengthen a preferred qualification into a required one",
        "omit an ambiguous classification rather than guess",
        "boilerplate, equal-employment language, compensation, and benefits",
        "only JSON matching the provided schema",
        "Do not provide reasoning",
    )
    for phrase in required_phrases:
        assert phrase in prompt

    full_jd = "Required: build reliable systems."
    user_prompt = build_jd_intelligence_matching_prompt(
        full_job_description=full_jd
    )
    assert "only factual source" in user_prompt
    assert user_prompt.endswith(full_jd)


@pytest.mark.parametrize(
    "mutate, expected_error",
    [
        (
            lambda payload: payload.pop("required_skills"),
            "missing_required_fields:required_skills",
        ),
        (
            lambda payload: payload["required_skills"].append("Python"),
            "invalid_type:required_skills[0]:object_required",
        ),
        (
            lambda payload: payload["required_skills"].append({"signal": "Python"}),
            "missing_required_fields:required_skills[0]:evidence_span",
        ),
        (
            lambda payload: payload.__setitem__("required_tools", "Python"),
            "invalid_type:required_tools:array_required",
        ),
        (
            lambda payload: payload.__setitem__("unsupported", []),
            "unexpected_fields:unsupported",
        ),
        (
            lambda payload: payload["required_skills"].append(
                _item("Python", "x" * (JD_INTELLIGENCE_MATCHING_EVIDENCE_SPAN_MAX_LENGTH + 1))
            ),
            "bound_exceeded:required_skills[0].evidence_span:max_length_160",
        ),
        (
            lambda payload: payload["required_skills"].append(
                _item("x" * (JD_INTELLIGENCE_MATCHING_SIGNAL_MAX_LENGTH + 1), "Python")
            ),
            "bound_exceeded:required_skills[0].signal:max_length_128",
        ),
        (
            lambda payload: payload["required_skills"].append(
                {"signal": "Python", "evidence_span": "Python", "reason": "because"}
            ),
            "unexpected_fields:required_skills[0]:reason",
        ),
    ],
)
def test_v2_validator_rejects_malformed_or_unbounded_payloads(
    mutate, expected_error
):
    payload = _payload()
    mutate(payload)
    validated, errors = validate_jd_intelligence_matching_payload(payload)
    assert validated == {}
    assert expected_error in errors


def test_v2_validator_enforces_category_and_singleton_bounds():
    payload = _payload(
        required_skills=[_item(f"skill {index}", f"skill {index}") for index in range(9)],
        domain=[_item("analytics", "analytics"), _item("retail", "retail")],
    )
    validated, errors = validate_jd_intelligence_matching_payload(payload)
    assert validated == {}
    assert (
        f"bound_exceeded:required_skills:max_items_{JD_INTELLIGENCE_MATCHING_CATEGORY_MAX_ITEMS}"
        in errors
    )
    assert "bound_exceeded:domain:max_items_1" in errors


def test_p1s11_grounding_failure_classes_accept_narrow_variants_and_reject_hallucination():
    records = _corpus_records()

    # Case A: conservative singular/plural normalization.
    mattel_grounded, _ = _ground(
        _payload(
            required_workflows=[
                _item(
                    "process improvement initiative",
                    "Demonstrated experience leading complex process improvement initiatives from diagnostics through implementation and sustainment.",
                )
            ]
        ),
        records[MATTEL],
    )
    assert mattel_grounded["required_workflows"][0]["signal"] == (
        "process improvement initiative"
    )

    # Case B: punctuation/hyphen differences.
    code_grounded, _ = _ground(
        _payload(
            preferred_tools=[
                _item(
                    "code execution sandboxes",
                    "Built coding agents, code-execution sandboxes, eval harnesses, verifiers, or developer tooling",
                )
            ]
        ),
        records[CODE_RL],
    )
    assert code_grounded["preferred_tools"][0]["signal"] == (
        "code execution sandboxes"
    )

    # Case C: an article/stopword in the verbatim span may be absent in signal.
    performance_grounded, _ = _ground(
        _payload(
            required_workflows=[
                _item(
                    "shape research roadmap",
                    "Conduct experiments and shape our research roadmap.",
                )
            ]
        ),
        records[PERFORMANCE_RL],
    )
    assert performance_grounded["required_workflows"][0]["signal"] == (
        "shape research roadmap"
    )

    # Case D1: an invented span fails exact source presence.
    _, missing_span_rejected = _ground(
        _payload(
            business_contexts=[
                _item("quantum cryptography", "Quantum cryptography trading desk")
            ]
        ),
        records[MATTEL],
    )
    assert missing_span_rejected["business_contexts"][0]["reason"] == (
        "span_not_verbatim"
    )

    # Case D2: a real span cannot self-certify an unrelated signal.
    _, unrelated_rejected = _ground(
        _payload(
            business_contexts=[
                _item(
                    "quantum cryptography",
                    "Analyze operational, financial and supply chain data and processes",
                )
            ]
        ),
        records[MATTEL],
    )
    assert unrelated_rejected["business_contexts"][0]["reason"] == (
        "signal_not_supported"
    )


def _mattel_payload():
    return _payload(
        preferred_skills=[
            _item(
                "Python",
                "Experience using Python, R, process mining, automation tools or applied AI to improve reporting, diagnostics and decision making.",
            )
        ],
        required_workflows=[
            _item(
                "process improvement initiative",
                "Demonstrated experience leading complex process improvement initiatives from diagnostics through implementation and sustainment.",
            )
        ],
        required_methods=[
            _item(
                "root cause analysis",
                "Deep knowledge of Lean methodologies, process design, root cause analysis, value stream mapping, standard work, operating model design and change management.",
            )
        ],
        preferred_methods=[
            _item(
                "process mining",
                "Experience using Python, R, process mining, automation tools or applied AI to improve reporting, diagnostics and decision making.",
            )
        ],
        business_contexts=[
            _item(
                "supply chain",
                "Analyze operational, financial and supply chain data and processes to identify trends, performance drivers, recurring issues and improvement opportunities.",
            ),
            _item(
                "quantum cryptography",
                "Analyze operational, financial and supply chain data and processes",
            ),
        ],
        stakeholder_contexts=[
            _item(
                "cross functional workshops",
                "Plan and lead cross functional workshops with Product Supply, Contract Manufacturing, Supply Chain",
            )
        ],
        ownership_signals=[
            _item(
                "own diagnostics",
                "this role will own diagnostics, solution design, implementation and sustainment",
            )
        ],
    )


def test_full_authoritative_mattel_payload_grounds_and_merges_fill_missing_only():
    record = _corpus_records()[MATTEL]
    assert len(record["retrieval_text"]) > 10_000

    grounded, rejected = _ground(_mattel_payload(), record)
    candidate = build_job_evidence_enrichment_candidate_v2(grounded)

    assert candidate["business_contexts"] == ["supply chain"]
    assert candidate["required_workflows"] == ["process improvement initiative"]
    assert candidate["required_methods"] == ["root cause analysis"]
    assert candidate["preferred_methods"] == ["process mining"]
    assert candidate["ownership_signals"] == ["own diagnostics"]
    assert rejected["business_contexts"][0]["item"]["signal"] == (
        "quantum cryptography"
    )

    before = build_job_evidence(record)
    after = merge_missing_job_evidence(before, candidate)

    # Populated deterministic evidence remains authoritative byte-for-byte.
    assert after.required_skills == before.required_skills
    assert after.preferred_skills == before.preferred_skills
    assert after.required_tools == before.required_tools
    assert after.required_workflows == before.required_workflows == ["reporting"]
    assert after.role_archetype == before.role_archetype
    assert after.seniority == before.seniority

    # Empty required/preferred groups fill independently without strengthening.
    assert before.required_methods == []
    assert after.required_methods == ["root cause analysis"]
    assert before.preferred_methods == []
    assert after.preferred_methods == ["process mining"]
    # P1S19 populates business_contexts deterministically, so fill-missing must
    # preserve it; "supply chain" is still gated out of that field.
    assert before.business_contexts == ["contract manufacturing", "procurement"]
    assert after.business_contexts == before.business_contexts
    assert "quantum" not in str(after).casefold()


def _mattel_taxonomy_payload():
    method_span = (
        "Deep knowledge of Lean methodologies, process design, root cause "
        "analysis, value stream mapping, standard work, operating model design "
        "and change management."
    )
    return _payload(
        required_skills=[_item("change management", method_span)],
        preferred_tools=[
            _item(
                "ERP",
                "Experience with ERP, planning, procurement, quality, "
                "manufacturing or supplier management systems.",
            ),
            _item(
                "supplier management systems",
                "Experience with ERP, planning, procurement, quality, "
                "manufacturing or supplier management systems.",
            ),
            _item(
                "Excel",
                "Advanced Excel and PowerPoint skills, with experience using "
                "Tableau, Power BI, SQL, Google BigQuery or similar tools "
                "preferred.",
            ),
        ],
        required_workflows=[
            _item(
                "process improvement initiatives",
                "Demonstrated experience leading complex process improvement "
                "initiatives from diagnostics through implementation and "
                "sustainment.",
            )
        ],
        required_methods=[
            _item("value stream mapping", method_span),
            _item("root cause analysis", method_span),
            _item("standard work", method_span),
        ],
        business_contexts=[
            _item(
                "supply chain",
                "experience in process improvement, supply chain, manufacturing "
                "operations, strategy, operations excellence, business "
                "analytics or management consulting.",
            ),
            _item(
                "manufacturing operations",
                "experience in process improvement, supply chain, manufacturing "
                "operations, strategy, operations excellence, business "
                "analytics or management consulting.",
            ),
            _item(
                "consumer products",
                "Experience in consumer products, manufacturing, supply chain, "
                "toy industry, retail supply chain or seasonal product "
                "environments.",
            ),
            _item(
                "contract manufacturing",
                "Experience supporting contract manufacturing, vendor "
                "manufacturing or third party production networks.",
            ),
        ],
    )


def test_p1s15_failure_classes_a_through_j_use_specific_taxonomy_and_strength():
    """Permanent mocked oracle derived from classes, not from live output text."""

    record = _corpus_records()[MATTEL]
    grounded, rejected = _ground(_mattel_taxonomy_payload(), record)
    candidate = build_job_evidence_enrichment_candidate_v2(grounded)

    assert rejected == {}
    # A-C: named Lean techniques are methods, never generic skills.
    assert candidate["required_methods"] == [
        "value stream mapping",
        "root cause analysis",
        "standard work",
    ]
    # D: degrees and credentials have no schema category and are omitted.
    all_signals = {
        item["signal"].casefold()
        for field in JD_INTELLIGENCE_MATCHING_PROVENANCE_FIELDS
        for item in _mattel_taxonomy_payload()[field]
    }
    assert not all_signals & {
        "bachelor degree",
        "mba",
        "master degree",
        "black belt",
        "process improvement certification",
    }
    assert not any(
        word in field
        for field in JD_INTELLIGENCE_MATCHING_PROVENANCE_FIELDS
        for word in ("degree", "education", "credential", "certification")
    )
    # E-F: industry and operating-environment experience are business context.
    assert candidate["business_contexts"] == [
        "supply chain",
        "manufacturing operations",
        "consumer products",
        "contract manufacturing",
    ]
    # G-H: named software/systems remain preferred tools.
    assert candidate["preferred_tools"] == [
        "erp",
        "supplier management systems",
        "excel",
    ]
    # I: an actual competency remains a skill.
    assert candidate["required_skills"] == ["change management"]
    # J: explicit must-have responsibility and preferred wording retain strength.
    assert candidate["required_workflows"] == [
        "process improvement initiatives"
    ]
    assert "required_tools" not in candidate
    assert {
        "value stream mapping",
        "root cause analysis",
        "standard work",
        "supply chain",
        "manufacturing operations",
        "consumer products",
        "contract manufacturing",
        "erp",
        "supplier management systems",
        "excel",
    }.isdisjoint(candidate["required_skills"])

    before = build_job_evidence(record)
    after = merge_missing_job_evidence(before, candidate)
    assert after.required_methods == candidate["required_methods"]
    # business_contexts is already populated deterministically after the P1S19
    # vocabulary additions, so fill-missing must preserve it rather than take
    # the candidate's values.
    assert after.business_contexts == before.business_contexts
    for field in before.__dataclass_fields__:
        if getattr(before, field):
            assert getattr(after, field) == getattr(before, field)


P1S11_SUCCESS_CASES = {
    CODE_RL: _payload(
        required_workflows=[
            _item(
                "build reward signals and verifiers",
                'build the reward signals and verifiers that capture what "good code" means',
            )
        ],
        preferred_workflows=[
            _item(
                "built coding agents",
                "Built coding agents, code-execution sandboxes, eval harnesses, verifiers, or developer tooling",
            )
        ],
        preferred_methods=[
            _item(
                "testing and verification",
                "Background in program analysis, testing, verification, compilers, or formal methods",
            )
        ],
        preferred_tools=[
            _item(
                "code execution sandboxes",
                "Built coding agents, code-execution sandboxes, eval harnesses, verifiers, or developer tooling",
            )
        ],
    ),
    PERFORMANCE_RL: _payload(
        required_workflows=[
            _item(
                "shape research roadmap",
                "Conduct experiments and shape our research roadmap.",
            )
        ],
        preferred_methods=[
            _item(
                "reinforcement learning",
                "Strong candidates may also have: Experience with reinforcement learning.",
            )
        ],
        stakeholder_contexts=[
            _item(
                "performance engineering specialists",
                "Collaborate with other researchers, engineers, and performance engineering specialists across and outside Anthropic.",
            )
        ],
    ),
    KNOWLEDGE: _payload(
        required_workflows=[
            _item(
                "agentic search capabilities",
                "Designing and evaluating advanced agentic search capabilities.",
            )
        ],
        required_methods=[
            _item(
                "finetuning and reinforcement learning",
                "Performing finetuning and reinforcement learning to teach language models how to interact with new information architectures",
            )
        ],
        preferred_methods=[
            _item(
                "indexing and ranking",
                "such as search engines, knowledge graphs, RAG, indexing, ranking, query understanding",
            )
        ],
    ),
    SCALE: _payload(
        required_workflows=[
            _item(
                "training and inference framework",
                "Build, profile and optimize our training and inference framework",
            )
        ],
        required_methods=[
            _item(
                "profile and optimize",
                "Build, profile and optimize our training and inference framework",
            )
        ],
        preferred_methods=[
            _item(
                "post training methods",
                "post-training methods &/or next generation use cases for large language models including instruction tuning, RLHF",
            )
        ],
    ),
}


P1S16_STARVED_TAXONOMY_CASES = {
    CODE_RL: (
        _payload(
            required_skills=[
                _item(
                    "software engineering",
                    "Have strong software-engineering skills and deep Python "
                    "expertise, including async/concurrent programming",
                )
            ],
            preferred_tools=[
                _item(
                    "code execution sandboxes",
                    "Built coding agents, code-execution sandboxes, eval "
                    "harnesses, verifiers, or developer tooling",
                )
            ],
            required_workflows=[
                _item(
                    "build reward signals and verifiers",
                    'build the reward signals and verifiers that capture what "good code" means',
                )
            ],
            preferred_methods=[
                _item(
                    "testing and verification",
                    "Background in program analysis, testing, verification, "
                    "compilers, or formal methods",
                )
            ],
        ),
        {
            "required_skills": ["software engineering"],
            "preferred_tools": ["code execution sandboxes"],
            "required_workflows": ["build reward signals and verifiers"],
            "preferred_methods": ["testing and verification"],
        },
    ),
    PERFORMANCE_RL: (
        _payload(
            required_skills=[
                _item(
                    "ML framework programming",
                    "Have expertise with accelerators (CUDA, ROCm, Triton, "
                    "Pallas), ML framework programming (JAX or PyTorch).",
                )
            ],
            required_tools=[
                _item(
                    "JAX",
                    "Have expertise with accelerators (CUDA, ROCm, Triton, "
                    "Pallas), ML framework programming (JAX or PyTorch).",
                ),
                _item(
                    "PyTorch",
                    "Have expertise with accelerators (CUDA, ROCm, Triton, "
                    "Pallas), ML framework programming (JAX or PyTorch).",
                ),
            ],
            required_workflows=[
                _item(
                    "shape research roadmap",
                    "Conduct experiments and shape our research roadmap.",
                )
            ],
            preferred_methods=[
                _item(
                    "reinforcement learning",
                    "Strong candidates may also have: Experience with "
                    "reinforcement learning.",
                )
            ],
            stakeholder_contexts=[
                _item(
                    "performance engineering specialists",
                    "Collaborate with other researchers, engineers, and "
                    "performance engineering specialists across and outside "
                    "Anthropic.",
                )
            ],
        ),
        {
            "required_skills": ["ml framework programming"],
            "required_tools": ["jax", "pytorch"],
            "required_workflows": ["shape research roadmap"],
            "preferred_methods": ["reinforcement learning"],
            "stakeholder_contexts": ["performance engineering specialists"],
        },
    ),
    KNOWLEDGE: (
        _payload(
            required_skills=[
                _item(
                    "machine learning research",
                    "Have good machine learning research experience",
                )
            ],
            required_workflows=[
                _item(
                    "agentic search capabilities",
                    "Designing and evaluating advanced agentic search "
                    "capabilities.",
                )
            ],
            required_methods=[
                _item(
                    "finetuning and reinforcement learning",
                    "Performing finetuning and reinforcement learning to teach "
                    "language models how to interact with new information "
                    "architectures",
                )
            ],
            business_contexts=[
                _item(
                    "information retrieval systems",
                    "Developing scalable distributed information retrieval "
                    "systems, such as search engines, knowledge graphs, RAG, "
                    "indexing, ranking",
                )
            ],
        ),
        {
            "required_skills": ["machine learning research"],
            "required_workflows": ["agentic search capabilities"],
            "required_methods": ["finetuning and reinforcement learning"],
            "business_contexts": ["information retrieval systems"],
        },
    ),
    SCALE: (
        _payload(
            required_skills=[
                _item(
                    "software engineering",
                    "Strong software engineering skills, proficient in "
                    "frameworks and tools such as CUDA, Pytorch, transformers, "
                    "flash attention, etc.",
                )
            ],
            required_tools=[
                _item(
                    "CUDA",
                    "Strong software engineering skills, proficient in "
                    "frameworks and tools such as CUDA, Pytorch, transformers, "
                    "flash attention, etc.",
                ),
                _item(
                    "PyTorch",
                    "Strong software engineering skills, proficient in "
                    "frameworks and tools such as CUDA, Pytorch, transformers, "
                    "flash attention, etc.",
                ),
            ],
            required_workflows=[
                _item(
                    "build training and inference framework",
                    "Build, profile and optimize our training and inference "
                    "framework",
                )
            ],
            preferred_methods=[
                _item(
                    "post training methods",
                    "post-training methods &/or next generation use cases for "
                    "large language models including instruction tuning, RLHF",
                )
            ],
            business_contexts=[
                _item(
                    "large-scale distributed ML systems",
                    "Experience with developing large-scale distributed ML "
                    "systems",
                )
            ],
        ),
        {
            "required_skills": ["software engineering"],
            "required_tools": ["cuda", "pytorch"],
            "required_workflows": ["build training and inference framework"],
            "preferred_methods": ["post training methods"],
            "business_contexts": ["large-scale distributed ml systems"],
        },
    ),
}


@pytest.mark.parametrize("job_key", tuple(P1S16_STARVED_TAXONOMY_CASES))
def test_other_starved_full_jds_keep_specific_categories_and_strength(job_key):
    payload, expected = P1S16_STARVED_TAXONOMY_CASES[job_key]
    record = _corpus_records()[job_key]
    assert len(record["retrieval_text"]) > 5_000

    grounded, rejected = _ground(payload, record)
    candidate = build_job_evidence_enrichment_candidate_v2(grounded)

    assert rejected == {}
    assert candidate == expected
    skill_signals = set(candidate.get("required_skills", [])) | set(
        candidate.get("preferred_skills", [])
    )
    non_skill_signals = {
        signal
        for field, signals in expected.items()
        if field not in {"required_skills", "preferred_skills"}
        for signal in signals
    }
    assert skill_signals.isdisjoint(non_skill_signals)


@pytest.mark.parametrize("job_key", tuple(P1S11_SUCCESS_CASES))
def test_full_authoritative_p1s11_success_cases_preserve_strength_and_safe_fill(
    job_key,
):
    record = _corpus_records()[job_key]
    assert len(record["retrieval_text"]) > 5_000

    grounded, rejected = _ground(P1S11_SUCCESS_CASES[job_key], record)
    candidate = build_job_evidence_enrichment_candidate_v2(grounded)

    assert rejected == {}
    assert candidate
    for field, values in candidate.items():
        assert field in JD_INTELLIGENCE_V2_CANDIDATE_FIELD_MAP.values()
        assert values
    if P1S11_SUCCESS_CASES[job_key]["required_workflows"]:
        assert "required_workflows" in candidate
    if P1S11_SUCCESS_CASES[job_key]["preferred_methods"]:
        assert "preferred_methods" in candidate
        assert candidate["preferred_methods"] != candidate.get("required_methods")


def test_cases_e_through_h_keep_explicit_requirement_strength():
    records = _corpus_records()
    code_grounded, _ = _ground(P1S11_SUCCESS_CASES[CODE_RL], records[CODE_RL])
    code_candidate = build_job_evidence_enrichment_candidate_v2(code_grounded)
    knowledge_grounded, _ = _ground(
        P1S11_SUCCESS_CASES[KNOWLEDGE], records[KNOWLEDGE]
    )
    knowledge_candidate = build_job_evidence_enrichment_candidate_v2(
        knowledge_grounded
    )

    # E/F: preferred and required workflows are distinct target fields.
    assert code_candidate["preferred_workflows"] == ["built coding agents"]
    assert code_candidate["required_workflows"] == [
        "build reward signals and verifiers"
    ]
    # G/H: preferred and required methods are distinct target fields.
    assert code_candidate["preferred_methods"] == ["testing and verification"]
    assert knowledge_candidate["required_methods"] == [
        "finetuning and reinforcement learning"
    ]


def test_grounding_deduplicates_normalized_signals_within_category():
    record = _corpus_records()[MATTEL]
    item = _item(
        "supply chain",
        "Analyze operational, financial and supply chain data and processes",
    )
    grounded, rejected = _ground(
        _payload(business_contexts=[item, deepcopy(item)]),
        record,
    )
    assert rejected == {}
    assert grounded["business_contexts"] == [item]


def test_grounding_omits_conflicting_required_and_preferred_classification():
    record = _corpus_records()[CODE_RL]
    item = _item(
        "testing and verification",
        "Background in program analysis, testing, verification, compilers, or formal methods",
    )
    grounded, rejected = _ground(
        _payload(required_methods=[item], preferred_methods=[deepcopy(item)]),
        record,
    )
    assert "required_methods" not in grounded
    assert "preferred_methods" not in grounded
    assert rejected["required_methods"][0]["reason"] == (
        "conflicting_requirement_strength"
    )
    assert rejected["preferred_methods"][0]["reason"] == (
        "conflicting_requirement_strength"
    )


def test_required_and_preferred_fields_fill_independently_without_overwrite():
    record = _corpus_records()[MATTEL]
    grounded, _ = _ground(_mattel_payload(), record)
    candidate = build_job_evidence_enrichment_candidate_v2(grounded)
    deterministic = build_job_evidence(record)
    before = replace(
        deterministic,
        required_workflows=[],
        preferred_workflows=["deterministic preferred workflow"],
        required_methods=["deterministic required method"],
        preferred_methods=[],
    )

    after = merge_missing_job_evidence(before, candidate)

    assert after.required_workflows == ["process improvement initiative"]
    assert after.preferred_workflows == ["deterministic preferred workflow"]
    assert after.required_methods == ["deterministic required method"]
    assert after.preferred_methods == ["process mining"]
    assert before.preferred_methods == []
    for field in before.__dataclass_fields__:
        if getattr(before, field):
            assert getattr(after, field) == getattr(before, field)


def test_v2_helpers_have_no_runtime_activation_call_sites():
    production_python = list((ROOT / "src").rglob("*.py"))
    owners = {
        ROOT / "src/matching/jd_intelligence_contract.py",
        ROOT / "src/matching/job_adapter.py",
    }
    symbols = (
        "validate_jd_intelligence_matching_payload",
        "ground_jd_intelligence_signals_v2",
        "build_job_evidence_enrichment_candidate_v2",
    )
    for symbol in symbols:
        outside = [
            str(path.relative_to(ROOT))
            for path in production_python
            if path not in owners and symbol in path.read_text(encoding="utf-8")
        ]
        assert outside == [], f"{symbol} is activated outside its offline owner: {outside}"

    adapter = (ROOT / "src/matching/job_adapter.py").read_text(encoding="utf-8")
    build_body = adapter.split("def build_job_evidence(", 1)[1].split("\ndef ", 1)[0]
    for symbol in symbols:
        assert symbol not in build_body


def test_v2_contract_does_not_mutate_inputs():
    payload = _payload(
        required_skills=[_item("Python", "Python")],
    )
    before = deepcopy(payload)
    validated, errors = validate_jd_intelligence_matching_payload(payload)
    assert errors == []
    assert payload == before
    assert validated == before
    assert validated is not payload


def test_p1s12_guard_surface_is_finite_and_currently_registered():
    from tests.support.phase_guard_registry import (
        PROBLEM1_JD_INTELLIGENCE_CONTRACT_REVISION_FILES,
        current_milestone_guard_compatibility_allowlist,
    )

    # P1S32 registered the experience-entry morphology repair on the same
    # Problem-1 milestone surface; the guard family is still finite and exact.
    expected = {
        "src/matching/jd_intelligence_contract.py",
        "src/matching/job_adapter.py",
        "src/resume/evidence_builder.py",
        "tests/fixtures/p1s3_jd_evidence/corpus_jobevidence_baseline.json",
        "tests/fixtures/p1s3_jd_evidence/starved_jd_records.json",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_problem1_experience_skill_morphology.py",
        "tests/test_problem1_jd_category_validator.py",
        "tests/test_problem1_jd_evidence_starvation.py",
        "tests/test_problem1_jd_intelligence_contract_v2.py",
    }
    assert PROBLEM1_JD_INTELLIGENCE_CONTRACT_REVISION_FILES == expected
    assert expected <= current_milestone_guard_compatibility_allowlist()
    assert not any("*" in path for path in expected)
