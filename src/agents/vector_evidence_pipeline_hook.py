from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable


VectorEvidenceService = Callable[..., dict[str, Any]]


def _safety_metadata(
    *,
    enabled: bool,
    attempted: bool,
    context_attached: bool,
    did_read_database: bool,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "vector_evidence_hook_enabled": enabled,
        "vector_evidence_hook_attempted": attempted,
        "vector_evidence_context_attached": context_attached,
        "did_read_database": did_read_database,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "provider_calls_made": False,
        "embeddings_created": False,
        "mutation_authorized": False,
    }


def run_vector_evidence_pipeline_hook(
    *,
    enabled: bool = False,
    run_id: str = "",
    job_id: str = "",
    stage_name: str = "post_final_scoring",
    query_text: str = "",
    job_payload: dict[str, Any] | None = None,
    vector_evidence_service: VectorEvidenceService | None = None,
) -> dict[str, Any]:
    """Collect isolated advisory evidence without influencing pipeline decisions."""

    if enabled is not True:
        return {
            "status": "vector_evidence_pipeline_hook_default_off",
            "hook_surface": "vector_evidence_pipeline_hook",
            "run_id": str(run_id or ""),
            "job_id": str(job_id or ""),
            "stage_name": str(stage_name or ""),
            "evidence_context": {},
            "safety_metadata": _safety_metadata(
                enabled=False,
                attempted=False,
                context_attached=False,
                did_read_database=False,
            ),
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
        }

    if vector_evidence_service is None:
        from src.app.services import vector_evidence_service_helper_payload

        vector_evidence_service = vector_evidence_service_helper_payload

    source_job = deepcopy(job_payload) if isinstance(job_payload, dict) else {}
    service_payload = vector_evidence_service(
        query_text=str(query_text or ""),
        job_payload=source_job,
        job_id=str(job_id or ""),
        stage=str(stage_name or ""),
    )
    if not isinstance(service_payload, dict):
        service_payload = {}

    service_safety = service_payload.get("safety_metadata")
    if not isinstance(service_safety, dict):
        service_safety = {}
    did_read_database = bool(service_safety.get("did_read_database"))
    evidence_context = {
        "status": str(service_payload.get("status", "") or ""),
        "service_surface": str(
            service_payload.get("service_surface", "") or ""
        ),
        "retrieval_summary": deepcopy(
            service_payload.get("retrieval_summary", {}) or {}
        ),
        "matched_chunks": deepcopy(service_payload.get("matched_chunks", []) or []),
        "skipped_reasons": deepcopy(
            service_payload.get("skipped_reasons", {}) or {}
        ),
        "read_only": True,
        "advisory_only": True,
    }
    return {
        "status": "vector_evidence_pipeline_hook_context_attached",
        "hook_surface": "vector_evidence_pipeline_hook",
        "run_id": str(run_id or ""),
        "job_id": str(job_id or ""),
        "stage_name": str(stage_name or ""),
        "evidence_context": evidence_context,
        "safety_metadata": _safety_metadata(
            enabled=True,
            attempted=True,
            context_attached=True,
            did_read_database=did_read_database,
        ),
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
    }
