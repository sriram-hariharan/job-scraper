"""Candidate-local Job Fit qualification semantics and dormant live binding.

The reviewed V1 Job Fit overlay remains the active routing authority.  This
module only binds a future controlled qualification of one Job Fit candidate
to the provider-transport semantic that production currently sends.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Callable, Dict, Mapping

from src.evaluation.production_task_contract_fingerprints import (
    production_task_contract_sha256,
)


JOB_FIT_WORKLOAD_ID = "job_fit_evaluation"
JOB_FIT_LOW_REASONING_PROVIDER = "groq"
JOB_FIT_LOW_REASONING_MODEL = "openai/gpt-oss-20b"
JOB_FIT_REVIEWED_CANDIDATES = frozenset(
    {
        ("groq", "openai/gpt-oss-20b"),
        ("groq", "openai/gpt-oss-120b"),
        ("openai", "gpt-5-mini"),
        ("openai", "gpt-5.1"),
    }
)
CANDIDATE_TRANSPORT_SEMANTICS_VERSION = (
    "job-fit-candidate-transport-semantics-v1"
)
CANDIDATE_LIVE_AUTHORIZATION_VERSION = (
    "job-fit-candidate-live-authorization-v1"
)
CANDIDATE_LIVE_EVIDENCE_VERSION = "job-fit-candidate-live-evidence-v1"
CANDIDATE_TRANSPORT_SEMANTICS_FIELD = (
    "candidate_transport_semantics_sha256"
)

_SEMANTIC_FIELDS = {
    "semantics_version",
    "workload_id",
    "provider",
    "model",
    "production_task_contract_sha256",
    "thinking_budget",
}
_AUTHORIZATION_FIELDS = {
    "authorization_version",
    "schedule_key",
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "production_task_contract_sha256",
    CANDIDATE_TRANSPORT_SEMANTICS_FIELD,
    "live_authorization_sha256",
}
_EVIDENCE_FIELDS = {
    "evidence_version",
    "candidate_authorization_sha256",
    "base_live_evidence_sha256",
    "schedule_key",
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "tested_candidate_transport_semantics_sha256",
    "tested_workload_qualification_semantics_sha256",
    "qualification_observation_sha256",
    "candidate_qualification_valid",
    "ready_for_activation",
    "qualification_observation",
    "live_evidence",
}
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


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


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


def build_job_fit_candidate_transport_semantics(
    provider: str,
    model: str,
    *,
    historical: bool = False,
) -> Dict[str, Any]:
    """Return one deterministic candidate semantic, with no authority."""

    provider_name = str(provider or "").strip().lower()
    model_name = str(model or "").strip()
    _require(
        (provider_name, model_name) in JOB_FIT_REVIEWED_CANDIDATES,
        "Job Fit candidate identity is invalid",
    )
    task_digest = production_task_contract_sha256(JOB_FIT_WORKLOAD_ID)
    _require(_is_sha256(task_digest), "Job Fit task contract is unavailable")
    thinking_budget = None
    if (
        not historical
        and provider_name == JOB_FIT_LOW_REASONING_PROVIDER
        and model_name == JOB_FIT_LOW_REASONING_MODEL
    ):
        from src.ai.job_fit_evaluator import JOB_FIT_THINKING_BUDGET

        thinking_budget = JOB_FIT_THINKING_BUDGET
    semantic = {
        "semantics_version": CANDIDATE_TRANSPORT_SEMANTICS_VERSION,
        "workload_id": JOB_FIT_WORKLOAD_ID,
        "provider": provider_name,
        "model": model_name,
        "production_task_contract_sha256": task_digest,
        "thinking_budget": thinking_budget,
    }
    validate_job_fit_candidate_transport_semantics(semantic)
    return deepcopy(semantic)


def validate_job_fit_candidate_transport_semantics(
    semantic: Dict[str, Any],
) -> bool:
    _require(
        isinstance(semantic, dict) and set(semantic) == _SEMANTIC_FIELDS,
        "Job Fit candidate semantic fields are invalid",
    )
    _require(
        semantic["semantics_version"] == CANDIDATE_TRANSPORT_SEMANTICS_VERSION
        and semantic["workload_id"] == JOB_FIT_WORKLOAD_ID,
        "Job Fit candidate semantic version or workload is invalid",
    )
    _require(
        (semantic["provider"], semantic["model"])
        in JOB_FIT_REVIEWED_CANDIDATES,
        "Job Fit candidate semantic identity is invalid",
    )
    _require(
        semantic["production_task_contract_sha256"]
        == production_task_contract_sha256(JOB_FIT_WORKLOAD_ID),
        "Job Fit candidate task-contract binding is stale",
    )
    _require(
        semantic["thinking_budget"] is None
        or (
            semantic["provider"] == JOB_FIT_LOW_REASONING_PROVIDER
            and semantic["model"] == JOB_FIT_LOW_REASONING_MODEL
            and isinstance(semantic["thinking_budget"], int)
            and not isinstance(semantic["thinking_budget"], bool)
            and semantic["thinking_budget"] >= 0
        ),
        "Job Fit candidate thinking budget is invalid",
    )
    return True


def job_fit_candidate_transport_semantics_sha256(
    provider: str,
    model: str,
    *,
    historical: bool = False,
) -> str:
    semantic = build_job_fit_candidate_transport_semantics(
        provider,
        model,
        historical=historical,
    )
    return sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def validate_current_job_fit_candidate_semantic_binding(
    *,
    provider: str,
    model: str,
    tested_candidate_transport_semantics_sha256: str,
) -> bool:
    _require(
        _is_sha256(tested_candidate_transport_semantics_sha256),
        "tested Job Fit candidate semantic fingerprint is invalid",
    )
    _require(
        tested_candidate_transport_semantics_sha256
        == job_fit_candidate_transport_semantics_sha256(provider, model),
        "tested Job Fit candidate transport semantics are stale",
    )
    return True


def job_fit_candidate_thinking_budget_for_request(
    request: Mapping[str, Any],
) -> int | None:
    """Validate request metadata and return the candidate task intent."""

    _require(
        request.get("workload_id") == JOB_FIT_WORKLOAD_ID,
        "candidate semantic request workload mismatch",
    )
    provider = str(request.get("provider") or "").strip().lower()
    model = str(request.get("model") or "").strip()
    _require(
        request.get(CANDIDATE_TRANSPORT_SEMANTICS_FIELD)
        == job_fit_candidate_transport_semantics_sha256(provider, model),
        "candidate semantic request fingerprint mismatch",
    )
    return build_job_fit_candidate_transport_semantics(provider, model)[
        "thinking_budget"
    ]


def build_job_fit_candidate_live_authorization(
    *,
    schedule_key: str,
    plan: Dict[str, Any],
    live_authorization: Dict[str, Any],
) -> Dict[str, Any]:
    """Bind one existing V1 live authorization to current candidate semantics."""

    from src.evaluation import controlled_live_provider_qualification as live

    rows = [
        row
        for row in live.build_live_qualification_universe(plan)
        if row["schedule_key"] == schedule_key
    ]
    _require(len(rows) == 1, "Job Fit candidate schedule is unknown")
    row = rows[0]
    _require(
        row["workload_id"] == JOB_FIT_WORKLOAD_ID,
        "candidate authorization is not Job Fit",
    )
    _require(
        live_authorization.get("approved_schedule_keys") == [schedule_key]
        and live_authorization.get("maximum_request_count") == 1,
        "candidate authorization must bind exactly one request",
    )
    authorization = {
        "authorization_version": CANDIDATE_LIVE_AUTHORIZATION_VERSION,
        "schedule_key": row["schedule_key"],
        "case_alias": row["case_alias"],
        "workload_id": row["workload_id"],
        "provider": row["provider"],
        "model": row["model"],
        "production_task_contract_sha256": row[
            "production_task_contract_sha256"
        ],
        CANDIDATE_TRANSPORT_SEMANTICS_FIELD: (
            job_fit_candidate_transport_semantics_sha256(
                row["provider"], row["model"]
            )
        ),
        "live_authorization_sha256": live.live_authorization_sha256(
            live_authorization
        ),
    }
    validate_job_fit_candidate_live_authorization(
        authorization,
        plan=plan,
        live_authorization=live_authorization,
    )
    return deepcopy(authorization)


def validate_job_fit_candidate_live_authorization(
    authorization: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    live_authorization: Dict[str, Any],
) -> bool:
    from src.evaluation import controlled_live_provider_qualification as live

    _require(
        isinstance(authorization, dict)
        and set(authorization) == _AUTHORIZATION_FIELDS,
        "Job Fit candidate authorization fields are invalid",
    )
    _require(
        authorization["authorization_version"]
        == CANDIDATE_LIVE_AUTHORIZATION_VERSION,
        "Job Fit candidate authorization version is invalid",
    )
    rows = [
        row
        for row in live.build_live_qualification_universe(plan)
        if row["schedule_key"] == authorization["schedule_key"]
    ]
    _require(len(rows) == 1, "Job Fit candidate schedule is unknown")
    row = rows[0]
    _require(
        row["workload_id"] == JOB_FIT_WORKLOAD_ID,
        "candidate authorization is not Job Fit",
    )
    for field in (
        "schedule_key",
        "case_alias",
        "workload_id",
        "provider",
        "model",
        "production_task_contract_sha256",
    ):
        _require(
            authorization[field] == row[field],
            "Job Fit candidate authorization identity mismatch",
        )
    _require(
        authorization[CANDIDATE_TRANSPORT_SEMANTICS_FIELD]
        == job_fit_candidate_transport_semantics_sha256(
            row["provider"], row["model"]
        ),
        "Job Fit candidate authorization semantics are stale",
    )
    _require(
        authorization["live_authorization_sha256"]
        == live.live_authorization_sha256(live_authorization),
        "Job Fit candidate base authorization binding mismatch",
    )
    _require(
        live_authorization.get("approved_schedule_keys")
        == [authorization["schedule_key"]]
        and live_authorization.get("maximum_request_count") == 1,
        "candidate authorization must bind exactly one request",
    )
    return True


def job_fit_candidate_live_authorization_sha256(
    authorization: Dict[str, Any],
) -> str:
    _require(
        isinstance(authorization, dict)
        and set(authorization) == _AUTHORIZATION_FIELDS,
        "Job Fit candidate authorization fields are invalid",
    )
    return sha256(_canonical_json(authorization).encode("utf-8")).hexdigest()


def _candidate_qualification_succeeded(
    observation: Mapping[str, Any] | None,
    candidate_authorization: Mapping[str, Any],
    *,
    expected_workload_qualification_semantics_sha256: str,
) -> bool:
    """Return whether one bounded observation qualifies this exact candidate."""

    if not isinstance(observation, Mapping):
        return False
    return bool(
        observation.get("schedule_key")
        == candidate_authorization["schedule_key"]
        and observation.get("case_alias")
        == candidate_authorization["case_alias"]
        and observation.get("workload_id")
        == candidate_authorization["workload_id"]
        and observation.get("provider")
        == candidate_authorization["provider"]
        and observation.get("model") == candidate_authorization["model"]
        and observation.get("tested_task_contract_sha256")
        == candidate_authorization["production_task_contract_sha256"]
        and observation.get(
            "tested_workload_qualification_semantics_sha256"
        )
        == expected_workload_qualification_semantics_sha256
        and observation.get("schedule_completed") is True
        and observation.get("provider_outcome_category") == "success"
        and observation.get("contract_valid") is True
        and observation.get("quality_gate_passed") is True
        and observation.get("hard_failure_present") is False
        and observation.get("authority_safety_valid") is True
    )


def execute_job_fit_candidate_local_live_qualification(
    *,
    plan: Dict[str, Any],
    candidate_authorization: Dict[str, Any],
    live_authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    operator_credentials: Mapping[str, str],
    execution_time_source: Callable[[], str],
    transport_dispatchers: Mapping[str, Callable[..., Dict[str, Any]]] | None = None,
    monotonic_clock: Callable[[], float],
    corpus: Dict[str, Any] | None = None,
    qualification_observation_target: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> Dict[str, Any]:
    """Execute the renderer-bound gate once and return candidate evidence."""

    from src.evaluation import controlled_live_provider_qualification as live
    from src.evaluation import (
        controlled_provider_qualification_evidence_adapter as adapter,
    )

    validate_job_fit_candidate_live_authorization(
        candidate_authorization,
        plan=plan,
        live_authorization=live_authorization,
    )
    schedule_key = candidate_authorization["schedule_key"]
    _require(
        (qualification_observation_target is None)
        == (repository_root is None),
        "qualification observation target and repository root must be supplied together",
    )
    if qualification_observation_target is not None:
        adapter.validate_renderer_bound_qualification_observation_target(
            qualification_observation_target,
            repository_root=repository_root,
        )
    renderer_authorization = live.build_renderer_bound_live_authorization(
        live_authorization,
        plan=plan,
        corpus=corpus,
    )
    evidence = live.execute_controlled_live_qualification(
        plan=plan,
        live_authorization=renderer_authorization,
        pricing=pricing,
        requested_schedule_keys=[schedule_key],
        operator_credentials=operator_credentials,
        execution_time_source=execution_time_source,
        transport_dispatchers=transport_dispatchers,
        monotonic_clock=monotonic_clock,
        corpus=corpus,
    )
    observation = None
    if any(
        isinstance(summary, Mapping)
        and summary.get("schedule_key") == schedule_key
        for summary in evidence.get("grading_summaries", [])
    ):
        observation = adapter.build_renderer_bound_qualification_observation(
            evidence=evidence,
            schedule_key=schedule_key,
            plan=plan,
            authorization=renderer_authorization,
            pricing=pricing,
            corpus=corpus,
        )
    if qualification_observation_target is not None and observation is not None:
        adapter.write_renderer_bound_qualification_observation_exclusive(
            qualification_observation_target,
            observation,
            repository_root=repository_root,
        )
    qualification_valid = _candidate_qualification_succeeded(
        observation,
        candidate_authorization,
        expected_workload_qualification_semantics_sha256=(
            renderer_authorization[
                live.APPROVED_WORKLOAD_SEMANTICS_FIELD
            ][candidate_authorization["workload_id"]]
        ),
    )
    envelope = {
        "evidence_version": CANDIDATE_LIVE_EVIDENCE_VERSION,
        "candidate_authorization_sha256": (
            job_fit_candidate_live_authorization_sha256(
                candidate_authorization
            )
        ),
        "base_live_evidence_sha256": (
            live.renderer_bound_live_qualification_evidence_sha256(
                evidence,
                plan=plan,
                authorization=renderer_authorization,
                pricing=pricing,
                corpus=corpus,
            )
        ),
        "schedule_key": candidate_authorization["schedule_key"],
        "case_alias": candidate_authorization["case_alias"],
        "workload_id": candidate_authorization["workload_id"],
        "provider": candidate_authorization["provider"],
        "model": candidate_authorization["model"],
        "tested_candidate_transport_semantics_sha256": (
            candidate_authorization[CANDIDATE_TRANSPORT_SEMANTICS_FIELD]
        ),
        "tested_workload_qualification_semantics_sha256": (
            observation[
                "tested_workload_qualification_semantics_sha256"
            ]
            if observation is not None
            else None
        ),
        "qualification_observation_sha256": (
            adapter.renderer_bound_qualification_observation_sha256(
                observation
            )
            if observation is not None
            else None
        ),
        "candidate_qualification_valid": qualification_valid,
        "ready_for_activation": qualification_valid,
        "qualification_observation": deepcopy(observation),
        "live_evidence": deepcopy(evidence),
    }
    validate_job_fit_candidate_live_evidence(
        envelope,
        candidate_authorization=candidate_authorization,
        live_authorization=live_authorization,
        plan=plan,
        pricing=pricing,
        corpus=corpus,
    )
    return deepcopy(envelope)


def validate_job_fit_candidate_live_evidence(
    evidence: Dict[str, Any],
    *,
    candidate_authorization: Dict[str, Any],
    live_authorization: Dict[str, Any],
    plan: Dict[str, Any],
    pricing: Dict[str, Any],
    corpus: Dict[str, Any] | None = None,
) -> bool:
    from src.evaluation import controlled_live_provider_qualification as live
    from src.evaluation import (
        controlled_provider_qualification_evidence_adapter as adapter,
    )

    _require(
        isinstance(evidence, dict) and set(evidence) == _EVIDENCE_FIELDS,
        "Job Fit candidate evidence fields are invalid",
    )
    _require(
        evidence["evidence_version"] == CANDIDATE_LIVE_EVIDENCE_VERSION,
        "Job Fit candidate evidence version is invalid",
    )
    validate_job_fit_candidate_live_authorization(
        candidate_authorization,
        plan=plan,
        live_authorization=live_authorization,
    )
    base = deepcopy(evidence["live_evidence"])
    renderer_authorization = live.build_renderer_bound_live_authorization(
        live_authorization,
        plan=plan,
        corpus=corpus,
    )
    live.validate_renderer_bound_live_qualification_evidence(
        base,
        plan=plan,
        authorization=renderer_authorization,
        pricing=pricing,
        corpus=corpus,
    )
    for field in ("schedule_key", "case_alias", "workload_id", "provider", "model"):
        _require(
            evidence[field] == candidate_authorization[field],
            "Job Fit candidate evidence identity mismatch",
        )
    _require(
        evidence["candidate_authorization_sha256"]
        == job_fit_candidate_live_authorization_sha256(
            candidate_authorization
        )
        and evidence["base_live_evidence_sha256"]
        == live.renderer_bound_live_qualification_evidence_sha256(
            base,
            plan=plan,
            authorization=renderer_authorization,
            pricing=pricing,
            corpus=corpus,
        ),
        "Job Fit candidate evidence digest binding mismatch",
    )
    validate_current_job_fit_candidate_semantic_binding(
        provider=evidence["provider"],
        model=evidence["model"],
        tested_candidate_transport_semantics_sha256=evidence[
            "tested_candidate_transport_semantics_sha256"
        ],
    )
    _require(
        evidence["tested_candidate_transport_semantics_sha256"]
        == candidate_authorization[CANDIDATE_TRANSPORT_SEMANTICS_FIELD],
        "Job Fit candidate evidence semantic binding mismatch",
    )
    observation = evidence["qualification_observation"]
    matching_summary = any(
        isinstance(summary, Mapping)
        and summary.get("schedule_key") == evidence["schedule_key"]
        for summary in base.get("grading_summaries", [])
    )
    if observation is None:
        _require(
            not matching_summary
            and evidence[
                "tested_workload_qualification_semantics_sha256"
            ]
            is None
            and evidence["qualification_observation_sha256"] is None,
            "Job Fit candidate evidence is missing its qualification observation",
        )
    else:
        adapter.validate_renderer_bound_qualification_observation(
            observation
        )
        rebuilt = adapter.build_renderer_bound_qualification_observation(
            evidence=base,
            schedule_key=evidence["schedule_key"],
            plan=plan,
            authorization=renderer_authorization,
            pricing=pricing,
            corpus=corpus,
        )
        _require(
            observation == rebuilt,
            "Job Fit candidate qualification observation binding mismatch",
        )
        _require(
            evidence[
                "tested_workload_qualification_semantics_sha256"
            ]
            == observation[
                "tested_workload_qualification_semantics_sha256"
            ]
            and evidence["qualification_observation_sha256"]
            == adapter.renderer_bound_qualification_observation_sha256(
                observation
            ),
            "Job Fit candidate qualification observation digest mismatch",
        )
    qualification_valid = _candidate_qualification_succeeded(
        observation,
        candidate_authorization,
        expected_workload_qualification_semantics_sha256=(
            renderer_authorization[
                live.APPROVED_WORKLOAD_SEMANTICS_FIELD
            ][candidate_authorization["workload_id"]]
        ),
    )
    _require(
        isinstance(evidence["candidate_qualification_valid"], bool)
        and isinstance(evidence["ready_for_activation"], bool)
        and evidence["candidate_qualification_valid"] is qualification_valid
        and evidence["ready_for_activation"] is qualification_valid,
        "Job Fit candidate qualification status is invalid",
    )
    return True


def serialize_job_fit_candidate_live_evidence(
    evidence: Dict[str, Any],
    **validation_context: Any,
) -> str:
    payload = deepcopy(evidence)
    validate_job_fit_candidate_live_evidence(
        payload,
        **validation_context,
    )
    return _canonical_json(payload)
