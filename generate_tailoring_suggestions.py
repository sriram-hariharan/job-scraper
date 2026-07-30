import argparse
from contextlib import ExitStack
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from src.tailoring.packet_support import _load_packet, _source_label
from src.tailoring.rendering import (
    _build_payload,
    _build_operator_markdown_payload,
    _markdown_from_payload,
    _build_training_log_row,
)

AUTHORITATIVE_TAILORING_GENERATION_LANGGRAPH_FLAG = (
    "APPLYLENS_AUTHORITATIVE_TAILORING_GENERATION_LANGGRAPH_ENABLED"
)
PRODUCTION_DURABLE_GRAPH_RUNTIME_FLAG = (
    "APPLYLENS_PRODUCTION_DURABLE_GRAPH_RUNTIME_ENABLED"
)
PRODUCTION_DURABLE_REPOSITORY_TARGET = (
    "APPLYLENS_DURABLE_ORCHESTRATION_DATABASE_URL"
)
PRODUCTION_DURABLE_SAVER_TARGET = (
    "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_DATABASE_URL"
)


def _truthy_env_value(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _authoritative_tailoring_generation_langgraph_enabled(
    env: dict[str, str] | None = None,
) -> bool:
    env_map = env if env is not None else os.environ
    return _truthy_env_value(
        env_map.get(AUTHORITATIVE_TAILORING_GENERATION_LANGGRAPH_FLAG)
    )


def _production_durable_graph_runtime_enabled(
    env: dict[str, str] | None = None,
) -> bool:
    env_map = env if env is not None else os.environ
    return _truthy_env_value(
        env_map.get(PRODUCTION_DURABLE_GRAPH_RUNTIME_FLAG)
    )


def _execute_durable_tailoring_graph(
    *,
    packet: dict,
    payload: dict,
    run_tailoring_func,
    output_llm_json: str,
    refresh_llm_cache: bool,
    enable_safe_app_ready_rewrite_promotion: bool,
    pipeline_run_id: str,
    owner_user_id: str,
    context_id: str,
    job_index: int | None,
    env_map: dict[str, str],
    durable_repository=None,
    durable_saver=None,
    durable_consumer_instance_id: str = "",
) -> dict:
    if isinstance(job_index, bool) or not isinstance(job_index, int):
        raise RuntimeError("production_durable_tailoring_job_index_required")
    if not pipeline_run_id or not owner_user_id or not context_id:
        raise RuntimeError(
            "production_durable_tailoring_run_identity_required"
        )

    from src.agents.production_durable_graph_runtime import (
        ProductionDurableGraphRuntime,
        build_tailoring_execution_identity,
    )
    from src.agents.tailoring_generation_authoritative_graph import (
        AUTHORITATIVE_TAILORING_GENERATION_GRAPH_VERSION,
        AUTHORITATIVE_TAILORING_GENERATION_NODE,
        AUTHORITATIVE_TAILORING_GENERATION_STATE_VERSION,
        execute_authoritative_tailoring_generation_graph,
    )

    identity = build_tailoring_execution_identity(
        packet=packet,
        payload=payload,
        graph_version=AUTHORITATIVE_TAILORING_GENERATION_GRAPH_VERSION,
        state_version=AUTHORITATIVE_TAILORING_GENERATION_STATE_VERSION,
        node_key=AUTHORITATIVE_TAILORING_GENERATION_NODE,
        owner_user_id=owner_user_id,
        pipeline_run_id=pipeline_run_id,
        context_id=context_id,
        job_index=job_index,
        refresh_llm_cache=refresh_llm_cache,
        enable_safe_app_ready_rewrite_promotion=(
            enable_safe_app_ready_rewrite_promotion
        ),
        created_at=datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
    )

    def invoke_graph(saver, configurable):
        return execute_authoritative_tailoring_generation_graph(
            packet=packet,
            payload=payload,
            run_tailoring_func=run_tailoring_func,
            output_llm_json=output_llm_json,
            refresh_llm_cache=refresh_llm_cache,
            enable_safe_app_ready_rewrite_promotion=(
                enable_safe_app_ready_rewrite_promotion
            ),
            pipeline_run_id=pipeline_run_id,
            owner_user_id=owner_user_id,
            context_id=context_id,
            checkpointer=saver,
            configurable=configurable,
        )

    consumer_id = (
        str(durable_consumer_instance_id or "").strip()
        or str(
            env_map.get(
                "APPLYLENS_PRODUCTION_DURABLE_CONSUMER_INSTANCE_ID"
            )
            or ""
        ).strip()
        or f"tailoring_generation:{pipeline_run_id}:{job_index}"
    )
    if durable_repository is not None or durable_saver is not None:
        if durable_repository is None or durable_saver is None:
            raise RuntimeError(
                "production_durable_dependencies_incomplete"
            )
        runtime = ProductionDurableGraphRuntime(
            repository=durable_repository,
            saver=durable_saver,
            consumer_instance_id=consumer_id,
            enabled=True,
        )
        return runtime.execute(identity=identity, invoke_graph=invoke_graph)

    repository_target = str(
        env_map.get(PRODUCTION_DURABLE_REPOSITORY_TARGET) or ""
    ).strip()
    saver_target = str(
        env_map.get(PRODUCTION_DURABLE_SAVER_TARGET) or ""
    ).strip()
    ordinary_target = str(env_map.get("DATABASE_URL") or "").strip()
    if (
        not repository_target
        or not saver_target
        or (ordinary_target and repository_target == ordinary_target)
        or (ordinary_target and saver_target == ordinary_target)
    ):
        raise RuntimeError(
            "production_durable_dedicated_targets_required"
        )

    from src.storage.durable_orchestration.langgraph_postgres import (
        open_langgraph_postgres_saver,
    )
    from src.storage.durable_orchestration.postgres_connection import (
        build_postgres_connection_factory,
    )
    from src.storage.durable_orchestration.repository import (
        DurableOrchestrationRepository,
    )

    connection_factory = build_postgres_connection_factory(
        enabled=True,
        database_url=repository_target,
        application_name="applylens-production-durable-tailoring",
    )
    repository = DurableOrchestrationRepository(
        connection_factory,
        enabled=True,
    )
    with ExitStack() as stack:
        saver = stack.enter_context(
            open_langgraph_postgres_saver(
                enabled=True,
                database_url=saver_target,
                application_name=(
                    "applylens-production-durable-tailoring-saver"
                ),
            )
        )
        runtime = ProductionDurableGraphRuntime(
            repository=repository,
            saver=saver,
            consumer_instance_id=consumer_id,
            enabled=True,
        )
        return runtime.execute(identity=identity, invoke_graph=invoke_graph)


def _maybe_execute_authoritative_tailoring_generation_graph(
    *,
    packet: dict,
    payload: dict,
    run_tailoring_func,
    output_llm_json: str = "",
    refresh_llm_cache: bool = False,
    enable_safe_app_ready_rewrite_promotion: bool = False,
    env: dict[str, str] | None = None,
    job_index: int | None = None,
    durable_repository=None,
    durable_saver=None,
    durable_consumer_instance_id: str = "",
) -> dict | None:
    env_map = env if env is not None else os.environ
    if not _authoritative_tailoring_generation_langgraph_enabled(env_map):
        return None

    from src.agents.tailoring_generation_authoritative_graph import (
        execute_authoritative_tailoring_generation_graph,
    )

    pipeline_run_id = str(
        env_map.get("JOB_APP_PIPELINE_RUN_ID")
        or env_map.get("JOB_STACK_USER_PIPELINE_RUN_ID")
        or ""
    ).strip()
    owner_user_id = str(
        env_map.get("JOB_STACK_OWNER_USER_ID") or ""
    ).strip()
    context_id = str(
        env_map.get("APPLYLENS_AGENT_CONTEXT_ID")
        or (
            f"tailoring_generation:{pipeline_run_id}"
            if pipeline_run_id
            else ""
        )
    ).strip()
    if _production_durable_graph_runtime_enabled(env_map):
        result = _execute_durable_tailoring_graph(
            packet=packet,
            payload=payload,
            run_tailoring_func=run_tailoring_func,
            output_llm_json=output_llm_json,
            refresh_llm_cache=refresh_llm_cache,
            enable_safe_app_ready_rewrite_promotion=(
                enable_safe_app_ready_rewrite_promotion
            ),
            pipeline_run_id=pipeline_run_id,
            owner_user_id=owner_user_id,
            context_id=context_id,
            job_index=job_index,
            env_map=env_map,
            durable_repository=durable_repository,
            durable_saver=durable_saver,
            durable_consumer_instance_id=(
                durable_consumer_instance_id
            ),
        )
    else:
        result = execute_authoritative_tailoring_generation_graph(
            packet=packet,
            payload=payload,
            run_tailoring_func=run_tailoring_func,
            output_llm_json=output_llm_json,
            refresh_llm_cache=refresh_llm_cache,
            enable_safe_app_ready_rewrite_promotion=(
                enable_safe_app_ready_rewrite_promotion
            ),
            pipeline_run_id=pipeline_run_id,
            owner_user_id=owner_user_id,
            context_id=context_id,
        )
    metadata = dict(result.get("execution_metadata") or {})
    if (
        metadata.get("execution_mode") != "langgraph"
        or metadata.get("production_node_count") != 1
        or metadata.get("node_invocation_count") not in {0, 1}
        or metadata.get("tailoring_owner_invocation_count") not in {0, 1}
        or metadata.get("critic_invocation_count") != 0
        or metadata.get("status") != "completed"
    ):
        raise RuntimeError(
            "authoritative_tailoring_generation_execution_metadata_invalid"
        )
    return result


def _print_rewrite_ideas_console(final_payload: dict) -> None:
    print("-" * 100)
    print("EVIDENCE-BACKED EDIT RECOMMENDATIONS")
    print("-" * 100)

    edit_cards = list(final_payload.get("edit_cards", []) or [])

    rewrite_cards = [
        row
        for row in edit_cards
        if str(row.get("edit_type", "") or "").strip() == "rewrite"
    ]

    directional_cards = [
        row
        for row in edit_cards
        if str(row.get("edit_type", "") or "").strip() != "rewrite"
    ]

    if rewrite_cards:
        print("PATCH-READY / REWRITE")
        for row in rewrite_cards:
            print(
                f"- [{row.get('section', '')}] {row.get('source', '')} | "
                f"action={row.get('edit_type', '')} | "
                f"type={row.get('evidence_type', '')} | supports={row.get('jd_signal_terms', [])}"
            )

            if str(row.get("replacement_materiality_validation_status", "") or "").strip():
                print(
                    f"  Patch status: {row.get('replacement_materiality_validation_status', '')}"
                )

            if str(row.get("patch_generation_method", "") or "").strip():
                print(
                    f"  Patch method: {row.get('patch_generation_method', '')}"
                )

            print(f"  Proposed rewrite: {row.get('recommended_rewrite', '')}")
            print(f"  Why it matters: {row.get('why_it_matters', '')}")
            print(f"  Placement guidance: {row.get('placement_guidance', '')}")
            print(f"  Evidence: {row.get('current_evidence', '')}")
            if row.get("parent_bullet"):
                print(f"  Parent bullet: {row.get('parent_bullet', '')}")
        print()

    if directional_cards:
        print("DIRECTIONAL-ONLY ACTIONS")
        for row in directional_cards:
            print(
                f"- [{row.get('section', '')}] {row.get('source', '')} | "
                f"action={row.get('edit_type', '')} | "
                f"type={row.get('evidence_type', '')} | supports={row.get('jd_signal_terms', [])}"
            )

            if str(row.get("direction_only_reason", "") or "").strip():
                print(
                    f"  Direction-only reason: {row.get('direction_only_reason', '')}"
                )

            if str(row.get("why_it_matters", "") or "").strip():
                print(f"  Why it matters: {row.get('why_it_matters', '')}")

            if str(row.get("placement_guidance", "") or "").strip():
                print(f"  Placement guidance: {row.get('placement_guidance', '')}")

            print(f"  Evidence: {row.get('current_evidence', '')}")
            if row.get("parent_bullet"):
                print(f"  Parent bullet: {row.get('parent_bullet', '')}")
        print()

    if rewrite_cards or directional_cards:
        return

    for row in final_payload.get("rewrite_candidates", []):
        print(
            f"- [{row.get('section', '')}] {row.get('source', '')} | "
            f"type={row.get('evidence_type', '')} | supports={row.get('supported_terms', [])}"
        )
        print(f"  Action: {row.get('action', '')}")
        print(f"  Evidence: {row.get('bullet_excerpt', '')}")
        if row.get("parent_bullet"):
            print(f"  Parent bullet: {row.get('parent_bullet', '')}")
    print()
    
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate grounded tailoring suggestions from a JD diff packet."
    )
    parser.add_argument(
        "--packet-json",
        required=True,
        help="Path to one JD diff packet JSON.",
    )
    parser.add_argument(
        "--job-index",
        type=int,
        default=None,
        help=(
            "Real source-corpus job index; mandatory only when the "
            "production durable graph runtime is enabled."
        ),
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path to write the tailoring suggestions JSON.",
    )
    parser.add_argument(
        "--output-md",
        default="",
        help="Optional path to write the tailoring suggestions Markdown.",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Run a live grounded LLM tailoring pass on top of the deterministic payload.",
    )
    parser.add_argument(
        "--output-llm-json",
        default="",
        help="Optional path to write the live LLM tailoring output JSON.",
    )
    parser.add_argument(
        "--refresh-llm-cache",
        action="store_true",
        help="Ignore any existing live LLM cache and regenerate the LLM tailoring output.",
    )
    parser.add_argument(
        "--enable-safe-app-ready-rewrite-promotion",
        action="store_true",
        help=(
            "Default-off: allow strictly validated safe app-ready rewrite promotion "
            "through existing replacement-selector gates."
        ),
    )
    parser.add_argument(
        "--training-log-jsonl",
        default="",
        help="Optional path to append one structured tailoring training-log JSONL row per run.",
    )
    args = parser.parse_args()

    generated_at_utc = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    
    packet = _load_packet(Path(args.packet_json))
    payload = _build_payload(packet, include_llm_prompts=args.use_llm)
    enable_safe_app_ready_rewrite_promotion = bool(
        args.enable_safe_app_ready_rewrite_promotion
        or os.getenv("APPLYLENS_SAFE_APP_READY_REWRITE_PROMOTION_ENABLED", "false").strip().lower()
        == "true"
    )

    final_payload = _build_operator_markdown_payload(
        payload,
        None,
        enable_safe_app_ready_rewrite_promotion=enable_safe_app_ready_rewrite_promotion,
    )
    markdown = _markdown_from_payload(final_payload)

    print("=" * 100)
    print("GROUNDED TAILORING SUGGESTIONS")
    print("=" * 100)
    print(f"JOB: {payload['job'].get('company', '')} | {payload['job'].get('title', '')}")
    print(f"SELECTED RESUME: {payload['selection'].get('selected_resume', '')}")
    print()

    print("-" * 100)
    print("RECRUITER SUMMARY")
    print("-" * 100)
    print(payload["recruiter_summary"])
    print()

    print("-" * 100)
    print("KEEP / EMPHASIZE")
    print("-" * 100)
    for item in payload["keep_emphasize"]:
        print(f"- {item}")
    print()

    print("-" * 100)
    print("TAILORING ACTIONS")
    print("-" * 100)
    for item in payload["tailoring_actions"]:
        print(f"- {item}")
    print()

    _print_rewrite_ideas_console(final_payload)

    print("-" * 100)
    print("EVIDENCE LAYERS")
    print("-" * 100)
    evidence_layers = payload.get("evidence_layers", {})
    for label in ["anchors", "supports", "context"]:
        print(label.upper())
        for row in evidence_layers.get(label, []):
            print(f"- {_source_label(row)} | {row.get('evidence_type')}")
        print()

    print("-" * 100)
    print("DO NOT CLAIM")
    print("-" * 100)
    for item in payload["do_not_claim"]:
        print(f"- {item}")
    print()

    output_json_path = None
    if args.output_json.strip():
        output_json_path = Path(args.output_json)

    output_md_path = None
    if args.output_md.strip():
        output_md_path = Path(args.output_md)
    
    llm_output = None
    if args.use_llm:
        from src.tailoring.llm import _run_live_llm_tailoring
        graph_result = _maybe_execute_authoritative_tailoring_generation_graph(
            packet=packet,
            payload=payload,
            run_tailoring_func=_run_live_llm_tailoring,
            output_llm_json=args.output_llm_json or "",
            refresh_llm_cache=args.refresh_llm_cache,
            enable_safe_app_ready_rewrite_promotion=(
                enable_safe_app_ready_rewrite_promotion
            ),
            job_index=args.job_index,
        )
        if graph_result is None:
            llm_output = _run_live_llm_tailoring(
                packet=packet,
                payload=payload,
                output_llm_json=args.output_llm_json or "",
                refresh_llm_cache=args.refresh_llm_cache,
                enable_safe_app_ready_rewrite_promotion=(
                    enable_safe_app_ready_rewrite_promotion
                ),
            )
        else:
            llm_output = graph_result["tailoring_result"]
            print(
                "Authoritative tailoring graph: "
                + json.dumps(
                    graph_result["execution_metadata"],
                    sort_keys=True,
                )
            )

        print("-" * 100)
        print("LIVE LLM TAILORING OUTPUT")
        print("-" * 100)
        print(f"Requested provider: {llm_output.get('requested_provider', '')}")
        print(f"Requested model: {llm_output.get('requested_model', '')}")
        print(f"Resolved provider: {llm_output.get('resolved_provider', '') or '<none>'}")
        print(f"Resolved model: {llm_output.get('resolved_model', '') or '<none>'}")
        print(f"Fallback used: {llm_output.get('fallback_used', False)}")
        print(f"Parse OK: {llm_output['parse_ok']}")
        print(f"Cache hit: {llm_output.get('cache_hit', False)}")
        if llm_output["parse_error"]:
            print(f"Parse error: {llm_output['parse_error']}")
        print()

        parsed = llm_output["parsed"]

        if llm_output["parse_ok"]:
            print("Recruiter summary:")
            print(parsed.get("recruiter_summary", ""))
            print()

            print("Keep / emphasize:")
            for item in parsed.get("keep_emphasize", []):
                print(f"- {item}")
            print()

            print("Tailoring actions:")
            for item in parsed.get("tailoring_actions", []):
                print(f"- {item}")
            print()

            print("Do not claim:")
            for item in parsed.get("do_not_claim", []):
                print(f"- {item}")
            print()

            print("Rewrite directions:")
            for item in llm_output["parsed"].get("rewrite_directions", []):
                print(f"- {item}")
        else:
            print("Raw response preview:")
            print(llm_output["raw_response"][:1200])
            print()

        if args.output_llm_json.strip():
            output_llm_json_path = Path(args.output_llm_json)
            output_llm_json_path.write_text(
                json.dumps(llm_output, indent=2),
                encoding="utf-8",
            )
            print(f"LLM JSON written: {output_llm_json_path}")
        
        final_payload = _build_operator_markdown_payload(
            payload,
            llm_output,
            enable_safe_app_ready_rewrite_promotion=enable_safe_app_ready_rewrite_promotion,
        )
        markdown = _markdown_from_payload(final_payload)

        print()
        _print_rewrite_ideas_console(final_payload)

        if output_json_path is not None:
            output_json_path.write_text(json.dumps(final_payload, indent=2), encoding="utf-8")
            print(f"JSON written: {output_json_path}")

        if output_md_path is not None:
            output_md_path.write_text(markdown, encoding="utf-8")
            print(
                f"Markdown written with {final_payload.get('preferred_rewrite_source', 'deterministic')} rewrite directions: "
                f"{args.output_md}"
            )

    if not args.use_llm:
        if output_json_path is not None:
            output_json_path.write_text(json.dumps(final_payload, indent=2), encoding="utf-8")
            print(f"JSON written: {output_json_path}")

        if output_md_path is not None:
            output_md_path.write_text(markdown, encoding="utf-8")
            print(f"Markdown written: {args.output_md}")
    
    if args.training_log_jsonl.strip():
        training_log_path = Path(args.training_log_jsonl)
        training_log_path.parent.mkdir(parents=True, exist_ok=True)

        training_log_row = _build_training_log_row(
            final_payload,
            llm_output,
            packet_json_path=args.packet_json,
            generated_at_utc=generated_at_utc,
            output_json_path=args.output_json,
            output_md_path=args.output_md,
            output_llm_json_path=args.output_llm_json,
        )

        with training_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(training_log_row, ensure_ascii=False) + "\n")

        print(f"Training log row appended: {training_log_path}")

if __name__ == "__main__":
    main()
