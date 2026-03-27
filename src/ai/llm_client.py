import os
import json
from dotenv import load_dotenv
from groq import Groq
from google import genai
from google.genai import types
from threading import Lock

load_dotenv()

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
DEFAULT_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip()

FALLBACK_ENABLED = os.getenv("LLM_FALLBACK_ENABLED", "false").strip().lower() == "true"
FALLBACK_PROVIDER = os.getenv("LLM_FALLBACK_PROVIDER", "gemini").strip().lower()
FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "gemini-2.5-flash").strip()

_GROQ_MODELS_WITHOUT_JSON_SCHEMA = {
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
}

_groq_client = None
_gemini_client = None

_provider_metrics_lock = Lock()

_provider_metrics = {
    "primary_attempts": 0,
    "fallback_attempts": 0,
    "groq_calls": 0,
    "gemini_calls": 0,
    "fallback_successes": 0,
    "provider_failures": 0,
}

def get_default_provider():
    return DEFAULT_PROVIDER


def get_default_model():
    return DEFAULT_MODEL

def reset_provider_metrics():
    with _provider_metrics_lock:
        for key in _provider_metrics:
            _provider_metrics[key] = 0


def get_provider_metrics():
    with _provider_metrics_lock:
        return dict(_provider_metrics)


def increment_provider_metric(metric_name: str):
    with _provider_metrics_lock:
        if metric_name in _provider_metrics:
            _provider_metrics[metric_name] += 1


def get_groq_client():
    global _groq_client

    if _groq_client is None:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise RuntimeError("GROQ_API_KEY not found in environment")
        _groq_client = Groq(api_key=groq_api_key)

    return _groq_client


def get_gemini_client():
    global _gemini_client

    if _gemini_client is None:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY not found in environment")
        _gemini_client = genai.Client(api_key=gemini_api_key)

    return _gemini_client


def _messages_to_gemini_prompt(messages):
    parts = []

    for message in messages:
        role = (message.get("role") or "").strip().lower()
        content = message.get("content") or ""

        if role == "system":
            parts.append(f"SYSTEM:\n{content}")
        elif role == "user":
            parts.append(f"USER:\n{content}")
        elif role == "assistant":
            parts.append(f"ASSISTANT:\n{content}")
        else:
            parts.append(str(content))

    return "\n\n".join(parts)

def _coerce_groq_message_content(content):
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


def _run_groq_chat_completion(
    messages,
    model,
    temperature,
    max_tokens,
    response_mime_type=None,
    response_schema=None,
    return_parsed=False,
    thinking_budget=None,
):
    increment_provider_metric("groq_calls")
    client = get_groq_client()

    request_kwargs = {
        "model": model,
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
        "messages": messages,
    }

    model_name = str(model or "").strip().lower()
    if model_name.startswith("openai/gpt-oss-"):
        request_kwargs["include_reasoning"] = False

    if response_mime_type == "application/json":
        supports_json_schema = model_name not in _GROQ_MODELS_WITHOUT_JSON_SCHEMA
        if response_schema is not None and supports_json_schema:
            request_kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "strict": True,
                    "schema": response_schema,
                },
            }
        else:
            request_kwargs["response_format"] = {"type": "json_object"}

    completion = client.chat.completions.create(**request_kwargs)

    message = completion.choices[0].message
    content = getattr(message, "content", None)
    text = _coerce_groq_message_content(content)

    if not text:
        refusal = getattr(message, "refusal", None)
        reasoning = getattr(message, "reasoning", None)

        detail_parts = []
        if refusal:
            detail_parts.append(f"refusal={refusal}")
        if reasoning:
            detail_parts.append("reasoning_present=true")

        detail = ", ".join(detail_parts) if detail_parts else "no_content_returned"

        try:
            raw_dump = message.model_dump()
        except Exception:
            raw_dump = str(message)

        print("\n[GROQ DEBUG] model =", model)
        print("[GROQ DEBUG] response_mime_type =", response_mime_type)
        print("[GROQ DEBUG] response_schema_present =", response_schema is not None)
        print("[GROQ DEBUG] raw message dump =", json.dumps(raw_dump, indent=2, default=str))

        raise RuntimeError(f"Groq returned no usable content ({detail})")

    if return_parsed and response_mime_type == "application/json":
        try:
            return json.loads(text)
        except Exception:
            return text

    return text


def _run_gemini_chat_completion(
    messages,
    model,
    temperature,
    max_tokens,
    response_mime_type=None,
    response_schema=None,
    return_parsed=False,
    thinking_budget=None,
):
    increment_provider_metric("gemini_calls")
    client = get_gemini_client()
    prompt = _messages_to_gemini_prompt(messages)

    config_kwargs = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }

    if response_mime_type:
        config_kwargs["response_mime_type"] = response_mime_type

    if response_schema is not None:
        config_kwargs["response_schema"] = response_schema
    
    if thinking_budget is not None:
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_budget=thinking_budget
        )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(**config_kwargs),
    )

    if return_parsed:
        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            return parsed

    text = getattr(response, "text", None)
    if text:
        return text

    raise RuntimeError("Gemini returned no parsed or text content")


def _run_single_provider(
    provider_name,
    messages,
    model,
    temperature,
    max_tokens,
    response_mime_type=None,
    response_schema=None,
    return_parsed=False,
    thinking_budget=None,
):
    provider_name = provider_name.strip().lower()

    if provider_name == "groq":
        return _run_groq_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_mime_type=response_mime_type,
            response_schema=response_schema,
            return_parsed=return_parsed,
            thinking_budget=thinking_budget,
        )

    if provider_name == "gemini":
        return _run_gemini_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_mime_type=response_mime_type,
            response_schema=response_schema,
            return_parsed=return_parsed,
            thinking_budget=thinking_budget,
        )

    raise ValueError(f"Unsupported LLM provider: {provider_name}")

def run_chat_completion_with_metadata(
    messages,
    model=None,
    temperature=0,
    max_tokens=500,
    provider=None,
    response_mime_type=None,
    response_schema=None,
    return_parsed=False,
    thinking_budget=None,
    fallback_enabled=None,
    fallback_provider=None,
    fallback_model=None,
):
    primary_provider = (provider or DEFAULT_PROVIDER).strip().lower()
    primary_model = model or DEFAULT_MODEL

    effective_fallback_enabled = FALLBACK_ENABLED if fallback_enabled is None else bool(fallback_enabled)
    effective_fallback_provider = (fallback_provider or FALLBACK_PROVIDER).strip().lower()
    effective_fallback_model = (fallback_model or FALLBACK_MODEL).strip()

    increment_provider_metric("primary_attempts")

    try:
        content = _run_single_provider(
            provider_name=primary_provider,
            messages=messages,
            model=primary_model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_mime_type=response_mime_type,
            response_schema=response_schema,
            return_parsed=return_parsed,
            thinking_budget=thinking_budget,
        )
        return {
            "content": content,
            "provider": primary_provider,
            "model": primary_model,
            "fallback_used": False,
        }

    except Exception as primary_error:
        if (
            not effective_fallback_enabled
            or primary_provider == effective_fallback_provider
        ):
            increment_provider_metric("provider_failures")
            raise primary_error

        increment_provider_metric("fallback_attempts")

        try:
            content = _run_single_provider(
                provider_name=effective_fallback_provider,
                messages=messages,
                model=effective_fallback_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_mime_type=response_mime_type,
                response_schema=response_schema,
                return_parsed=return_parsed,
                thinking_budget=thinking_budget,
            )
            increment_provider_metric("fallback_successes")
            return {
                "content": content,
                "provider": effective_fallback_provider,
                "model": effective_fallback_model,
                "fallback_used": True,
            }

        except Exception as fallback_error:
            increment_provider_metric("provider_failures")
            raise RuntimeError(
                f"Primary provider failed ({primary_provider}/{primary_model}): {primary_error} | "
                f"Fallback provider failed ({effective_fallback_provider}/{effective_fallback_model}): {fallback_error}"
            ) from fallback_error
        
def run_chat_completion(
    messages,
    model=None,
    temperature=0,
    max_tokens=500,
    provider=None,
    response_mime_type=None,
    response_schema=None,
    return_parsed=False,
    thinking_budget=None,
    fallback_enabled=None,
    fallback_provider=None,
    fallback_model=None,
):
    result = run_chat_completion_with_metadata(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        provider=provider,
        response_mime_type=response_mime_type,
        response_schema=response_schema,
        return_parsed=return_parsed,
        thinking_budget=thinking_budget,
        fallback_enabled=fallback_enabled,
        fallback_provider=fallback_provider,
        fallback_model=fallback_model,
    )
    return result["content"]