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
    embedding_retrieval_enabled: bool = False,
    embedding_retrieval_attempted: bool = False,
    semantic_evidence_attached: bool = False,
    runtime_embedding_bridge_enabled: bool = False,
    runtime_embedding_attempted: bool = False,
    provider_calls_made: bool = False,
    embeddings_created: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "vector_evidence_hook_enabled": enabled,
        "vector_evidence_hook_attempted": attempted,
        "vector_evidence_context_attached": context_attached,
        "embedding_retrieval_enabled": embedding_retrieval_enabled,
        "embedding_retrieval_attempted": embedding_retrieval_attempted,
        "semantic_evidence_attached": semantic_evidence_attached,
        "runtime_embedding_bridge_enabled": runtime_embedding_bridge_enabled,
        "runtime_embedding_attempted": runtime_embedding_attempted,
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
        "provider_calls_made": provider_calls_made,
        "embeddings_created": embeddings_created,
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
    embedding_retrieval_enabled: bool = False,
    embedding_retrieval_owner_user_id: str = "",
    embedding_retrieval_model_id: str = "",
    embedding_retrieval_dimension: int = 0,
    embedding_retrieval_top_k: int = 5,
    embedding_retrieval_filters: dict[str, Any] | None = None,
    embedding_retrieval_provider: Any = None,
    embedding_retrieval_read_enabled: bool = False,
    embedding_retrieval_db_executor: Any = None,
    embedding_retrieval_helper: Any = None,
    runtime_embedding_bridge_enabled: bool = False,
    runtime_embedding_provider: Any = None,
    runtime_embedding_client: Any = None,
    runtime_embedding_service_helper: Any = None,
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
                embedding_retrieval_enabled=False,
            ),
            "provider_backed_automated_agents": 0,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "mutation_authorized_scoring_agents": 0,
            "mutation_authorized_ranking_agents": 0,
            "mutation_authorized_application_agents": 0,
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
    semantic_payload: dict[str, Any] = {}
    semantic_safety: dict[str, Any] = {}
    runtime_embedding_payload: dict[str, Any] = {}
    runtime_embedding_attempted = False
    if embedding_retrieval_enabled is True:
        retrieval_helper = embedding_retrieval_helper
        if retrieval_helper is None:
            from src.storage.vector_evidence.embedding_retrieval import (
                run_vector_evidence_embedding_retrieval,
            )

            retrieval_helper = run_vector_evidence_embedding_retrieval
        retrieval_provider = embedding_retrieval_provider
        if runtime_embedding_bridge_enabled is True:
            runtime_service = runtime_embedding_service_helper
            if runtime_service is None:
                from src.app.services import (
                    vector_evidence_embedding_runtime_service_helper_payload,
                )

                runtime_service = (
                    vector_evidence_embedding_runtime_service_helper_payload
                )

            def runtime_provider(request: dict[str, Any]) -> Any:
                nonlocal runtime_embedding_attempted
                nonlocal runtime_embedding_payload
                runtime_embedding_attempted = True
                result = runtime_service(
                    enabled=True,
                    text=str(request.get("text", "") or ""),
                    embedding_model_id=str(
                        request.get("embedding_model_id", "") or ""
                    ),
                    expected_dimension=request.get(
                        "expected_dimension",
                        embedding_retrieval_dimension,
                    ),
                    request_id=str(request.get("request_id", "") or ""),
                    provider_callable=runtime_embedding_provider,
                    provider_client=runtime_embedding_client,
                )
                runtime_embedding_payload = (
                    deepcopy(result) if isinstance(result, dict) else {}
                )
                return {
                    "embedding": deepcopy(
                        runtime_embedding_payload.get("embedding", []) or []
                    )
                }

            retrieval_provider = runtime_provider
        try:
            result = retrieval_helper(
                enabled=True,
                query_text=str(query_text or ""),
                owner_user_id=str(embedding_retrieval_owner_user_id or ""),
                run_id=str(run_id or ""),
                job_id=str(job_id or ""),
                embedding_model_id=str(embedding_retrieval_model_id or ""),
                expected_dimension=embedding_retrieval_dimension,
                top_k=embedding_retrieval_top_k,
                filters=deepcopy(embedding_retrieval_filters or {}),
                provider=retrieval_provider,
                read_enabled=embedding_retrieval_read_enabled is True,
                db_executor=embedding_retrieval_db_executor,
            )
            semantic_payload = result if isinstance(result, dict) else {}
        except Exception as exc:
            semantic_payload = {
                "status": "embedding_retrieval_hook_failed_non_blocking",
                "retrieval_candidates": [],
                "result_count": 0,
                "errors": [exc.__class__.__name__],
                "safety_metadata": {
                    "provider_calls_made": False,
                    "embeddings_created": False,
                    "did_read_database": False,
                    "did_write_database": False,
                },
            }
        semantic_safety = semantic_payload.get("safety_metadata")
        if not isinstance(semantic_safety, dict):
            semantic_safety = {}

    semantic_candidates = deepcopy(
        semantic_payload.get("retrieval_candidates", []) or []
    )
    semantic_evidence_attached = bool(
        semantic_payload.get("status") == "embedding_retrieval_completed"
        and semantic_candidates
    )
    did_read_database = bool(
        service_safety.get("did_read_database")
        or semantic_safety.get("did_read_database")
    )
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
    if embedding_retrieval_enabled is True:
        evidence_context["semantic_retrieval"] = {
            "status": str(semantic_payload.get("status", "") or ""),
            "retrieval_candidates": semantic_candidates,
            "result_count": int(semantic_payload.get("result_count", 0) or 0),
            "errors": deepcopy(semantic_payload.get("errors", []) or []),
            "read_only": True,
            "advisory_only": True,
            "shadow_only": True,
        }
        if runtime_embedding_bridge_enabled is True:
            evidence_context["semantic_retrieval"][
                "runtime_embedding_bridge"
            ] = {
                "status": str(
                    runtime_embedding_payload.get("status", "") or ""
                ),
                "provider_mechanism": str(
                    runtime_embedding_payload.get(
                        "provider_mechanism",
                        "",
                    )
                    or ""
                ),
                "runtime_embedding_attempted": runtime_embedding_attempted,
                "read_only": True,
                "advisory_only": True,
                "shadow_only": True,
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
            embedding_retrieval_enabled=embedding_retrieval_enabled is True,
            embedding_retrieval_attempted=embedding_retrieval_enabled is True,
            semantic_evidence_attached=semantic_evidence_attached,
            runtime_embedding_bridge_enabled=(
                runtime_embedding_bridge_enabled is True
            ),
            runtime_embedding_attempted=runtime_embedding_attempted,
            provider_calls_made=bool(
                semantic_safety.get("provider_calls_made")
            ),
            embeddings_created=bool(
                semantic_safety.get("embeddings_created")
            ),
        ),
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
    }
