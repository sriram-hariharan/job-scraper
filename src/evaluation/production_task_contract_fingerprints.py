"""Deterministic fingerprints for current production LLM task semantics."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib import import_module
import json
import re
from typing import Any, Callable, Dict

from src.evaluation.provider_benchmark_contract import WORKLOAD_ORDER


PRODUCTION_TASK_CONTRACT_FINGERPRINT_VERSION = (
    "production-task-contract-fingerprints-v1"
)
UNRESOLVED_PRODUCTION_WORKLOADS = (
    "manual_provider_preview",
)
FINGERPRINTED_PRODUCTION_WORKLOADS = tuple(
    workload_id
    for workload_id in WORKLOAD_ORDER
    if workload_id not in UNRESOLVED_PRODUCTION_WORKLOADS
)

_CONTRACT_FIELDS = {
    "workload_id",
    "task_contract_version",
    "prompt_contract",
    "input_contract",
    "output_contract",
    "deterministic_transformation_contract",
    "task_parameters",
}
_OWNER_BUILDERS = {
    "skill_extraction": (
        "src.ai.skill_llm_enricher",
        "build_skill_extraction_production_task_contract_material",
    ),
    "job_fit_evaluation": (
        "src.ai.job_fit_evaluator",
        "build_job_fit_production_task_contract_material",
    ),
    "jd_intelligence": (
        "src.app.services",
        "build_jd_intelligence_production_task_contract_material",
    ),
    "grounded_rag_answer": (
        "src.rag.rag_answerer",
        "build_grounded_rag_production_task_contract_material",
    ),
    "resume_fallback_ranking": (
        "batch_select_best_resume_variant",
        "build_resume_fallback_ranking_production_task_contract_material",
    ),
    "ambiguous_resume_adjudication": (
        "src.agents.llm_adjudicator_readback",
        "build_llm_adjudicator_readback_production_task_contract_material",
    ),
    "critic_evaluation": (
        "src.app.services",
        "build_critic_evaluation_production_task_contract_material",
    ),
    "tailoring_generation": (
        "src.tailoring.llm",
        "build_tailoring_generation_production_task_contract_material",
    ),
    "tailoring_refinement": (
        "src.tailoring.llm",
        "build_tailoring_refinement_production_task_contract_material",
    ),
    "tailoring_judge": (
        "src.tailoring.llm",
        "build_tailoring_judge_production_task_contract_material",
    ),
    "manual_scan_phrase": (
        "src.app.services",
        "build_manual_scan_phrase_production_task_contract_material",
    ),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _owner_builder(workload_id: str) -> Callable[[], Dict[str, Any]]:
    module_name, function_name = _OWNER_BUILDERS[workload_id]
    module = import_module(module_name)
    builder = getattr(module, function_name, None)
    _require(callable(builder), "production task-contract owner is unavailable")
    return builder


def _validate_contract(contract: Dict[str, Any], workload_id: str) -> None:
    _require(
        isinstance(contract, dict) and set(contract) == _CONTRACT_FIELDS,
        "production task contract fields are invalid",
    )
    _require(
        contract.get("workload_id") == workload_id,
        "production task contract workload mismatch",
    )
    _require(
        isinstance(contract.get("task_contract_version"), str)
        and bool(contract["task_contract_version"].strip()),
        "production task contract version is invalid",
    )
    for field in (
        "prompt_contract",
        "input_contract",
        "output_contract",
        "deterministic_transformation_contract",
        "task_parameters",
    ):
        _require(
            isinstance(contract.get(field), dict),
            f"production task contract {field} is invalid",
        )
    _canonical_json(contract)


def build_production_task_contract(workload_id: str) -> Dict[str, Any] | None:
    """Return one current semantic contract, or ``None`` when unresolved."""

    normalized = str(workload_id or "").strip()
    _require(normalized in WORKLOAD_ORDER, "unknown production workload")
    if normalized in UNRESOLVED_PRODUCTION_WORKLOADS:
        return None

    material = deepcopy(_owner_builder(normalized)())
    _require(isinstance(material, dict), "production task-contract material is invalid")
    contract = {"workload_id": normalized, **material}
    _validate_contract(contract, normalized)
    return deepcopy(contract)


def production_task_contract_sha256(workload_id: str) -> str | None:
    """Return the lowercase SHA-256 for one current production contract."""

    contract = build_production_task_contract(workload_id)
    if contract is None:
        return None
    digest = sha256(_canonical_json(contract).encode("utf-8")).hexdigest()
    _require(
        re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
        "production task-contract fingerprint is malformed",
    )
    return digest


def build_all_production_task_contract_fingerprints() -> Dict[str, str | None]:
    """Return all 12 canonical workloads in deterministic benchmark order."""

    fingerprints = {
        workload_id: production_task_contract_sha256(workload_id)
        for workload_id in WORKLOAD_ORDER
    }
    _require(
        tuple(fingerprints) == WORKLOAD_ORDER,
        "production task-contract fingerprint order changed",
    )
    _require(
        {key for key, value in fingerprints.items() if value is not None}
        == set(FINGERPRINTED_PRODUCTION_WORKLOADS),
        "production task-contract fingerprint coverage changed",
    )
    return fingerprints
