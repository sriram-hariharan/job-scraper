import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from groq import Groq

from src.tailoring.selection import _build_evidence_layers
from src.tailoring.planner import _build_tailoring_plan
from src.tailoring.llm import (
    LIVE_REWRITE_RESPONSE_SCHEMA,
    _build_live_rewrite_prompt,
    _validate_live_llm_parsed_contract,
    _canonicalize_live_direction_objects,
    _normalize_live_llm_parsed,
    _canonicalize_live_direction_sources,
    _build_live_shadow_replacement_plan,
)

load_dotenv()


def _coerce_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    parts.append(text)
                continue

            if isinstance(item, dict):
                text = str(item.get("text") or item.get("content") or "").strip()
                if text:
                    parts.append(text)
                continue

            text = str(item or "").strip()
            if text:
                parts.append(text)

        return "\n".join(parts).strip()

    if isinstance(content, dict):
        text = str(content.get("text") or content.get("content") or "").strip()
        if text:
            return text

    return str(content or "").strip()


def _load_packet(packet_path: Path) -> Dict[str, Any]:
    value = json.loads(packet_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected packet JSON object in {packet_path}")
    return value


def _build_payload(packet: Dict[str, Any]) -> Dict[str, Any]:
    tailoring_plan = _build_tailoring_plan(packet)
    evidence_layers = _build_evidence_layers(packet, tailoring_plan=tailoring_plan)
    payload = {
        "tailoring_plan": tailoring_plan,
        "evidence_layers": evidence_layers,
    }
    payload["live_rewrite_prompt"] = _build_live_rewrite_prompt(packet, payload)
    return payload


def _groq_request(
    *,
    client: Groq,
    model: str,
    prompt: str,
    schema: Dict[str, Any],
    strict: bool,
    max_tokens: int,
) -> Dict[str, Any]:
    completion = client.chat.completions.create(
        model=model,
        temperature=0,
        max_completion_tokens=max_tokens,
        include_reasoning=False if model.startswith("openai/gpt-oss-") else None,
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate evidence-anchored resume rewrite directions. "
                    "Return only JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "structured_output",
                "strict": strict,
                "schema": schema,
            },
        },
    )
    message = completion.choices[0].message
    return {
        "content": getattr(message, "content", None),
        "raw_message": message.model_dump(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe Groq structured-output behavior for live tailoring.")
    parser.add_argument("--packet-json", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--strict", choices=["true", "false"], default="true")
    parser.add_argument("--max-tokens", type=int, default=700)
    parser.add_argument("--output-json", default="")
    args = parser.parse_args()

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise RuntimeError("GROQ_API_KEY not found in environment")

    packet_path = Path(args.packet_json)
    packet = _load_packet(packet_path)
    payload = _build_payload(packet)
    prompt = payload["live_rewrite_prompt"]

    client = Groq(api_key=groq_api_key)
    strict = args.strict == "true"

    result: Dict[str, Any] = {
        "packet_json": str(packet_path),
        "model": args.model,
        "strict": strict,
        "parse_ok": False,
        "parse_error": "",
        "raw_response": "",
        "parsed": {},
        "shadow_replacement_candidates": [],
        "shadow_final_replacement_plan": {},
    }

    try:
        response = _groq_request(
            client=client,
            model=args.model,
            prompt=prompt,
            schema=LIVE_REWRITE_RESPONSE_SCHEMA,
            strict=strict,
            max_tokens=args.max_tokens,
        )
        raw_content = response.get("content")
        result["raw_response"] = _coerce_message_text(raw_content)
        result["raw_message"] = response.get("raw_message", {})
    except Exception as exc:
        result["parse_error"] = f"request_failed: {exc}"
    else:
        try:
            raw_value = raw_content
            if isinstance(raw_value, str):
                parsed = json.loads(raw_value)
            elif isinstance(raw_value, list):
                text = _coerce_message_text(raw_value)
                parsed = json.loads(text)
            elif isinstance(raw_value, dict):
                parsed = raw_value
            else:
                parsed = json.loads(_coerce_message_text(raw_value))

            parsed = _validate_live_llm_parsed_contract(parsed, payload)
            parsed["rewrite_directions"] = _canonicalize_live_direction_objects(
                parsed.get("rewrite_directions", []),
                payload,
            )
            normalized = _normalize_live_llm_parsed(parsed)
            normalized["rewrite_directions"] = _canonicalize_live_direction_sources(
                normalized.get("rewrite_directions", []),
                payload,
            )
            shadow_payload = _build_live_shadow_replacement_plan(
                normalized.get("rewrite_directions_structured", []),
                payload,
            )

            result["parse_ok"] = True
            result["parsed"] = normalized
            result["shadow_replacement_candidates"] = shadow_payload.get("shadow_replacement_candidates", [])
            result["shadow_final_replacement_plan"] = shadow_payload.get("shadow_final_replacement_plan", {})
        except Exception as exc:
            result["parse_error"] = f"parse_failed: {exc}"

    print(json.dumps({
        "packet_json": result["packet_json"],
        "model": result["model"],
        "strict": result["strict"],
        "parse_ok": result["parse_ok"],
        "parse_error": result["parse_error"],
        "structured_count": len((result.get("parsed", {}) or {}).get("rewrite_directions_structured", []) or []),
        "shadow_candidate_count": len(result.get("shadow_replacement_candidates", []) or []),
        "shadow_direction_only_count": len(((result.get("shadow_final_replacement_plan", {}) or {}).get("direction_only_replacements", []) or [])),
    }, indent=2))

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"wrote: {output_path}")


if __name__ == "__main__":
    main()