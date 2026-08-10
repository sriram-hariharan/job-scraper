from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import re

import pytest

from src.evaluation import production_task_contract_fingerprints as fingerprints
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
)
from src.evaluation.controlled_provider_qualification_registry import (
    build_provider_qualification_registry,
)
from src.evaluation.provider_benchmark_contract import WORKLOAD_ORDER


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / "src/evaluation/production_task_contract_fingerprints.py"
FINGERPRINTED_WORKLOADS = (
    "skill_extraction",
    "job_fit_evaluation",
    "jd_intelligence",
    "grounded_rag_answer",
    "resume_fallback_ranking",
    "ambiguous_resume_adjudication",
    "critic_evaluation",
    "tailoring_generation",
    "tailoring_refinement",
    "tailoring_judge",
    "manual_scan_phrase",
)
UNRESOLVED_WORKLOADS = (
    "manual_provider_preview",
)


def _iter_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).lower()
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _material():
    return {
        "task_contract_version": "test-v1",
        "prompt_contract": {
            "system": "system semantics",
            "user_template": "user semantics <input>",
        },
        "input_contract": {"fields": ["input"]},
        "output_contract": {"schema": {"type": "object"}},
        "deterministic_transformation_contract": {"normalizer": "v1"},
        "task_parameters": {"temperature": 0, "max_tokens": 100},
    }


def _digest_for_material(monkeypatch, material):
    monkeypatch.setattr(
        fingerprints,
        "_owner_builder",
        lambda _workload_id: lambda: deepcopy(material),
    )
    return fingerprints.production_task_contract_sha256("skill_extraction")


def test_exact_workload_universe_and_fingerprint_coverage_are_deterministic():
    first = fingerprints.build_all_production_task_contract_fingerprints()
    second = fingerprints.build_all_production_task_contract_fingerprints()

    assert len(WORKLOAD_ORDER) == 12
    assert tuple(first) == tuple(second) == WORKLOAD_ORDER
    assert fingerprints.FINGERPRINTED_PRODUCTION_WORKLOADS == FINGERPRINTED_WORKLOADS
    assert fingerprints.UNRESOLVED_PRODUCTION_WORKLOADS == UNRESOLVED_WORKLOADS
    assert tuple(key for key, value in first.items() if value is not None) == FINGERPRINTED_WORKLOADS
    assert tuple(key for key, value in first.items() if value is None) == UNRESOLVED_WORKLOADS
    assert first == second
    assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in first.values() if value)


@pytest.mark.parametrize("workload_id", UNRESOLVED_WORKLOADS)
def test_unresolved_or_benchmark_only_workload_has_no_production_contract(workload_id):
    assert fingerprints.build_production_task_contract(workload_id) is None
    assert fingerprints.production_task_contract_sha256(workload_id) is None


def test_unknown_workload_fails_closed():
    with pytest.raises(ValueError, match="unknown production workload"):
        fingerprints.production_task_contract_sha256("not_a_workload")


def test_ambiguous_workload_is_owned_only_by_readback_adjudication():
    assert fingerprints._OWNER_BUILDERS["ambiguous_resume_adjudication"] == (
        "src.agents.llm_adjudicator_readback",
        "build_llm_adjudicator_readback_production_task_contract_material",
    )
    contract = fingerprints.build_production_task_contract(
        "ambiguous_resume_adjudication"
    )
    serialized = json.dumps(contract, sort_keys=True).lower()
    assert contract["deterministic_transformation_contract"]["readback_only"] is True
    assert contract["deterministic_transformation_contract"]["no_winner_override"] is True
    assert "adjudicated_resume" not in serialized
    assert "winner-resolving" not in serialized


@pytest.mark.parametrize(
    ("section", "key", "changed_value"),
    [
        ("prompt_contract", "system", "changed system semantics"),
        ("prompt_contract", "user_template", "changed user semantics <input>"),
        ("input_contract", "fields", ["changed_input"]),
        ("output_contract", "schema", {"type": "array"}),
        ("deterministic_transformation_contract", "normalizer", "v2"),
        ("task_parameters", "max_tokens", 101),
    ],
)
def test_each_semantic_contract_section_changes_the_digest(
    monkeypatch,
    section,
    key,
    changed_value,
):
    baseline_material = _material()
    baseline = _digest_for_material(monkeypatch, baseline_material)
    changed = deepcopy(baseline_material)
    changed[section][key] = changed_value

    assert _digest_for_material(monkeypatch, changed) != baseline


def test_provider_model_credentials_runtime_and_operational_state_are_excluded(
    monkeypatch,
):
    from src.ai import job_fit_evaluator, skill_llm_enricher
    from src.app import services
    from src.rag import rag_answerer
    from src.tailoring import llm as tailoring_llm
    import batch_select_best_resume_variant as resume_selector

    baseline = fingerprints.build_all_production_task_contract_fingerprints()

    for owner, name in (
        (skill_llm_enricher, "MODEL"),
        (job_fit_evaluator, "MODEL"),
        (rag_answerer, "MODEL"),
        (resume_selector, "LLM_FALLBACK_PROVIDER"),
        (resume_selector, "LLM_FALLBACK_MODEL"),
        (services, "LIVE_JD_INTELLIGENCE_DRY_RUN_PROVIDER"),
        (services, "LIVE_JD_INTELLIGENCE_DRY_RUN_MODEL"),
        (services, "LIVE_CRITIC_GUARDRAIL_DRY_RUN_PROVIDER"),
        (services, "LIVE_CRITIC_GUARDRAIL_DRY_RUN_MODEL"),
        (services, "SCAN_PHRASE_PROVIDER"),
        (services, "SCAN_PHRASE_MODEL"),
        (tailoring_llm, "LLM_TAILOR_PROVIDER"),
        (tailoring_llm, "LLM_TAILOR_MODEL"),
        (tailoring_llm, "PATCH_REFINEMENT_WRITER_PROVIDER"),
        (tailoring_llm, "PATCH_REFINEMENT_WRITER_MODEL"),
        (tailoring_llm, "PATCH_REFINEMENT_JUDGE_PROVIDER"),
        (tailoring_llm, "PATCH_REFINEMENT_JUDGE_MODEL"),
    ):
        monkeypatch.setattr(owner, name, "changed-provider-or-model")

    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key")
    monkeypatch.setenv("GROQ_API_KEY", "not-a-real-key")
    monkeypatch.setenv("USER_ID", "runtime-user")
    monkeypatch.setenv("JOB_ID", "runtime-job")
    monkeypatch.setenv("RESUME_TEXT", "runtime-resume")
    monkeypatch.setenv("CURRENT_TIMESTAMP", "2099-01-01T00:00:00Z")
    monkeypatch.setitem(skill_llm_enricher.skill_cache_metrics, "hits", 999)
    monkeypatch.setitem(job_fit_evaluator.eval_cache_metrics, "hits", 999)
    monkeypatch.setattr(skill_llm_enricher, "logger", object())
    monkeypatch.setattr(services, "logger", object())

    assert fingerprints.build_all_production_task_contract_fingerprints() == baseline

    for workload_id in FINGERPRINTED_WORKLOADS:
        contract = fingerprints.build_production_task_contract(workload_id)
        keys = set(_iter_keys(contract))
        assert not keys.intersection(
            {
                "provider",
                "model",
                "api_key",
                "credential",
                "user_id",
                "job_id",
                "resume_text",
                "timestamp",
                "latency",
                "token_usage",
                "metrics",
                "logs",
                "cache",
                "retry_count",
                "file_path",
                "source_line",
            }
        )


@pytest.mark.parametrize(
    ("workload_id", "expected_parameters"),
    [
        ("skill_extraction", {"temperature": 0, "max_tokens": 500}),
        ("job_fit_evaluation", {"temperature": 0, "max_tokens": 600}),
        (
            "jd_intelligence",
            {
                "temperature": 0,
                "max_tokens": 700,
                "thinking_budget": 0,
                "response_mime_type": "application/json",
                "return_parsed": True,
            },
        ),
        ("grounded_rag_answer", {"temperature": 0, "max_tokens": 500}),
        ("resume_fallback_ranking", {"temperature": 0.0, "max_tokens": 900}),
        (
            "ambiguous_resume_adjudication",
            {
                "temperature": 0,
                "max_tokens": 500,
                "response_mime_type": "application/json",
                "fallback_enabled": False,
            },
        ),
        (
            "critic_evaluation",
            {
                "temperature": 0,
                "max_tokens": 900,
                "thinking_budget": 0,
                "response_mime_type": "application/json",
                "return_parsed": True,
            },
        ),
        (
            "tailoring_generation",
            {
                "temperature": 0,
                "max_tokens": 700,
                "thinking_budget": 0,
                "response_mime_type": "application/json",
                "return_parsed": True,
            },
        ),
        (
            "tailoring_refinement",
            {
                "temperature": 0,
                "max_tokens": 420,
                "thinking_budget": 0,
                "response_mime_type": None,
                "return_parsed": False,
            },
        ),
        (
            "tailoring_judge",
            {
                "temperature": 0,
                "max_tokens": 500,
                "thinking_budget": 0,
                "response_mime_type": None,
                "return_parsed": False,
            },
        ),
        (
            "manual_scan_phrase",
            {
                "temperature": 0,
                "max_tokens": 520,
                "thinking_budget": 0,
                "structured_response_mime_type": "application/json",
                "structured_return_parsed": True,
                "plain_retry_return_parsed": False,
            },
        ),
    ],
)
def test_current_production_task_parameters_are_preserved(
    workload_id,
    expected_parameters,
):
    contract = fingerprints.build_production_task_contract(workload_id)
    assert contract["task_parameters"] == expected_parameters


def test_production_call_sites_use_the_extracted_authoritative_material():
    expected_snippets = {
        "src/ai/skill_llm_enricher.py": (
            "prompt = _build_skill_extraction_user_prompt(extraction_text)",
            "retry_prompt = _build_skill_extraction_retry_prompt(prompt)",
            "temperature=SKILL_EXTRACTION_TEMPERATURE",
            "max_tokens=SKILL_EXTRACTION_MAX_TOKENS",
        ),
        "src/ai/job_fit_evaluator.py": (
            '"content": SYSTEM_PROMPT',
            "temperature=JOB_FIT_TEMPERATURE",
            "max_tokens=JOB_FIT_MAX_TOKENS",
        ),
        "src/rag/rag_answerer.py": (
            '{"role": "system", "content": SYSTEM_PROMPT}',
            "temperature=GROUNDED_RAG_TEMPERATURE",
            "max_tokens=GROUNDED_RAG_MAX_TOKENS",
        ),
        "src/agents/llm_adjudicator_readback.py": (
            '"content": LLM_ADJUDICATOR_READBACK_SYSTEM_PROMPT',
            "max_tokens=int(",
            "response_mime_type=\"application/json\"",
            "fallback_enabled=False",
        ),
        "batch_select_best_resume_variant.py": (
            "system_prompt = LLM_FALLBACK_SYSTEM_PROMPT",
            "max_tokens=LLM_FALLBACK_MAX_TOKENS",
            "temperature=LLM_FALLBACK_TEMPERATURE",
        ),
        "src/app/services.py": (
            '"content": LIVE_JD_INTELLIGENCE_DRY_RUN_SYSTEM_PROMPT',
            '"content": LIVE_CRITIC_GUARDRAIL_DRY_RUN_SYSTEM_PROMPT',
            "system_prompt = SCAN_PHRASE_SYSTEM_PROMPT",
            "temperature=SCAN_PHRASE_TEMPERATURE",
            "max_tokens=SCAN_PHRASE_MAX_TOKENS",
        ),
        "src/tailoring/llm.py": (
            "primary_system_prompt = TAILORING_GENERATION_PRIMARY_SYSTEM_PROMPT",
            "retry_system_prompt = TAILORING_GENERATION_RETRY_SYSTEM_PROMPT",
            "writer_system_prompt = PATCH_REFINEMENT_WRITER_SYSTEM_PROMPT",
            "judge_system_prompt = PATCH_REFINEMENT_JUDGE_SYSTEM_PROMPT",
        ),
    }
    for relative_path, snippets in expected_snippets.items():
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        for snippet in snippets:
            assert snippet in source


def test_extracted_prompt_constants_preserve_exact_runtime_text():
    from src.agents import llm_adjudicator_readback
    from src.ai import skill_llm_enricher
    from src.app import services
    from src.tailoring import llm as tailoring_llm
    import batch_select_best_resume_variant as resume_selector

    assert skill_llm_enricher._build_skill_extraction_retry_prompt("primary") == (
        "primary\n\nReturn ONLY valid JSON. No prose. No markdown. No explanation."
    )
    assert llm_adjudicator_readback._provider_prompt([])[0]["content"] == (
        llm_adjudicator_readback
        .build_llm_adjudicator_readback_production_task_contract_material()[
            "prompt_contract"
        ]["system"]
    )
    assert resume_selector.LLM_FALLBACK_SYSTEM_PROMPT.startswith(
        "You rank resume variants for fallback use"
    )
    assert services.LIVE_JD_INTELLIGENCE_DRY_RUN_SYSTEM_PROMPT == (
        "You extract structured job-description intelligence for a manual dry-run. "
        "Return only JSON and never recommend application actions."
    )
    assert services.LIVE_CRITIC_GUARDRAIL_DRY_RUN_SYSTEM_PROMPT == (
        "You are a conservative critic guardrail for a manual dry-run. "
        "Return only JSON and never apply changes."
    )
    assert services.SCAN_PHRASE_SYSTEM_PROMPT == (
        "You generate conservative, truthful resume bullet rewrite options for manual editing. "
        "Return only JSON."
    )
    assert tailoring_llm.PATCH_REFINEMENT_WRITER_SYSTEM_PROMPT.endswith(
        "OPTION_2: <single rewritten bullet>\n"
    )
    assert tailoring_llm.PATCH_REFINEMENT_JUDGE_SYSTEM_PROMPT.endswith(
        "RISK_FLAGS: <comma-separated risk tags or none>\n"
    )


def test_existing_parser_and_normalizer_semantics_are_unchanged():
    from src.agents import llm_adjudicator_readback
    from src.ai import job_fit_evaluator, skill_llm_enricher
    from src.rag import rag_answerer
    from src.tailoring import llm as tailoring_llm
    import batch_select_best_resume_variant as resume_selector

    assert skill_llm_enricher.extract_json_from_response(
        'prefix {"required_skills":["SQL"],"preferred_skills":[]} suffix'
    ) == {"required_skills": ["SQL"], "preferred_skills": []}
    assert job_fit_evaluator.extract_json_from_response(
        '```json\n{"results": []}\n```'
    ) == {"results": []}
    assert rag_answerer._extract_json_from_response(
        'prefix {"answer":"grounded"} suffix'
    ) == {"answer": "grounded"}
    assert llm_adjudicator_readback._parse_provider_response(
        '{"summary":"Close candidates"}'
    ) == {"summary": "Close candidates"}
    assert llm_adjudicator_readback._normalize_provider_response(
        {"reason": "Close candidates", "recommendation": "Review alpha"}
    ) == ("Close candidates", "Review alpha")
    assert resume_selector._normalize_llm_fallback_parsed(
        {
            "best_resume": "resume-a.pdf",
            "best_score": 4,
            "backup_resume": "resume-a.pdf",
            "backup_score": -2,
            "confidence": "high",
            "reason": "best available",
        },
        ["resume-a.pdf"],
    ) == {
        "best_resume": "resume-a.pdf",
        "best_score": 1.0,
        "backup_resume": "",
        "backup_score": 0.0,
        "confidence": "low",
        "reason": "best available",
    }
    assert tailoring_llm._normalize_patch_refinement_judge_parsed(
        {"winner": "unsupported", "reason": "invalid"}
    )["winner"] == "abstain"


def test_fingerprint_owner_uses_semantic_json_not_files_or_runtime_capabilities():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "sha256(_canonical_json(contract).encode(\"utf-8\"))" in source
    for prohibited in (
        "__file__",
        "read_text(",
        "read_bytes(",
        "inspect.getsource",
        "source_line",
        "line_number",
        "run_chat_completion",
        "requests.",
        "httpx.",
        "getenv(",
        "environ",
        "api_key",
        "credential",
        "select_route",
    ):
        assert prohibited not in source
    assert imported_roots.isdisjoint(
        {"openai", "groq", "requests", "httpx", "os", "pathlib"}
    )


def test_canonical_fingerprints_keep_all_44_registry_cells_pending():
    plan = build_controlled_provider_benchmark_plan()
    current = fingerprints.build_all_production_task_contract_fingerprints()
    payload = build_provider_qualification_registry(
        plan=plan,
        current_task_contract_sha256_by_workload=current,
    )

    assert len(payload["cells"]) == 44
    assert {cell["status"] for cell in payload["cells"]} == {"pending"}
    assert all(
        cell["current_task_contract_sha256"] == current[cell["workload_id"]]
        for cell in payload["cells"]
    )
    assert all(
        cell["current_task_contract_sha256"] is None
        for cell in payload["cells"]
        if cell["workload_id"] in UNRESOLVED_WORKLOADS
    )
    assert plan["authority_invariants"]["live_execution_authorized"] is False
    assert plan["authority_invariants"]["provider_calls_allowed"] is False


def test_contracts_are_json_compatible_and_do_not_contain_real_runtime_values():
    for workload_id in FINGERPRINTED_WORKLOADS:
        contract = fingerprints.build_production_task_contract(workload_id)
        serialized = json.dumps(contract, ensure_ascii=False, sort_keys=True)
        assert serialized
        assert "runtime-user" not in serialized
        assert "runtime-job" not in serialized
        assert "not-a-real-key" not in serialized
