import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from src.tailoring.packet_support import _load_packet, _source_label
from src.tailoring.rendering import (
    _build_payload,
    _build_operator_markdown_payload,
    _markdown_from_payload,
    _build_training_log_row,
)
from src.tailoring.llm import _run_live_llm_tailoring

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
        "--training-log-jsonl",
        default="",
        help="Optional path to append one structured tailoring training-log JSONL row per run.",
    )
    args = parser.parse_args()

    generated_at_utc = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    
    packet = _load_packet(Path(args.packet_json))
    payload = _build_payload(packet)
    final_payload = _build_operator_markdown_payload(payload, None)
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

    print("-" * 100)
    print("EVIDENCE-BACKED REWRITE IDEAS")
    print("-" * 100)
    for row in payload.get("rewrite_candidates", []):
        print(
            f"- [{row.get('section', '')}] {row.get('source', '')} | "
            f"type={row.get('evidence_type', '')} | supports={row.get('supported_terms', [])}"
        )
        print(f"  Action: {row.get('action', '')}")
        print(f"  Evidence: {row.get('bullet_excerpt', '')}")
    print()

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
        llm_output = _run_live_llm_tailoring(
            packet=packet,
            payload=payload,
            output_llm_json=args.output_llm_json or "",
            refresh_llm_cache=args.refresh_llm_cache,
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
        
        final_payload = _build_operator_markdown_payload(payload, llm_output)
        markdown = _markdown_from_payload(final_payload)

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