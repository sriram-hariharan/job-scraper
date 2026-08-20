import os
import json
import re
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from threading import Lock

load_dotenv()

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
DEFAULT_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip()

FALLBACK_ENABLED = os.getenv("LLM_FALLBACK_ENABLED", "false").strip().lower() == "true"
FALLBACK_PROVIDER = os.getenv("LLM_FALLBACK_PROVIDER", "openai").strip().lower()
FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "gpt-5-mini").strip()

_GROQ_MODELS_WITHOUT_JSON_SCHEMA = {
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
}

_OPENAI_GPT_5_MINI_MODEL_PATTERN = re.compile(
    r"^gpt-5-mini(?:-\d{4}-\d{2}-\d{2})?$",
    re.IGNORECASE,
)

_SUPPORTED_PROVIDERS = {"groq", "openai"}
_KNOWN_MODEL_PROVIDERS = {
    "llama-3.1-8b-instant": "groq",
    "llama-3.3-70b-versatile": "groq",
    "openai/gpt-oss-20b": "groq",
    "openai/gpt-oss-120b": "groq",
    "gpt-5-mini": "openai",
    "gpt-5.1": "openai",
}
_PROVIDER_ERROR_CATEGORIES = {
    "timeout",
    "connection",
    "rate_limit",
    "provider_5xx",
    "authentication",
    "authorization",
    "configuration",
    "invalid_request",
    "provider_model_mismatch",
    "unsupported_provider",
    "schema_or_parse",
    "refusal_or_empty_content",
    "safety",
    "unknown",
}
_FALLBACK_ELIGIBLE_ERROR_CATEGORIES = {
    "timeout",
    "connection",
    "rate_limit",
    "provider_5xx",
}
_INVALID_REQUEST_REASON_CATEGORIES = frozenset(
    {
        "generated_schema_mismatch",
        "messages",
        "model_parameter",
        "other_invalid_request",
        "reasoning_parameter",
        "response_format",
        "response_schema",
        "temperature",
        "token_limit",
        "unsupported_parameter",
        "unsupported_schema_keyword",
    }
)
_SAFE_PROVIDER_ERROR_TYPES = frozenset(
    {
        "bad_request",
        "bad_request_error",
        "invalid_request",
        "invalid_request_error",
    }
)
_SAFE_PROVIDER_ERROR_CODES = frozenset(
    {
        "context_length_exceeded",
        "invalid_request",
        "json_schema_validation_failed",
        "json_validate_failed",
        "model_not_found",
        "schema_validation_failed",
        "tool_use_failed",
        "unsupported_parameter",
        "unsupported_value",
    }
)
_SAFE_PROVIDER_ERROR_PARAMS = frozenset(
    {
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "messages",
        "model",
        "reasoning_effort",
        "response_format",
        "response_schema",
        "temperature",
    }
)
_SAFE_SCHEMA_KEYWORD_PATTERNS = (
    (
        "additionalProperties",
        r"(?<![A-Za-z0-9_])additionalproperties(?![A-Za-z0-9_])",
    ),
    ("properties", r"(?<![A-Za-z0-9_])properties(?![A-Za-z0-9_])"),
    ("required", r"(?<![A-Za-z0-9_])required(?![A-Za-z0-9_])"),
    ("anyOf", r"(?<![A-Za-z0-9_])anyof(?![A-Za-z0-9_])"),
    ("items", r"(?<![A-Za-z0-9_])items(?![A-Za-z0-9_])"),
    ("enum", r"(?<![A-Za-z0-9_])enum(?![A-Za-z0-9_])"),
    ("type", r"(?<![A-Za-z0-9_])type(?![A-Za-z0-9_])"),
    ("$defs", r"(?<![A-Za-z0-9_])\$defs(?![A-Za-z0-9_])"),
    ("$ref", r"(?<![A-Za-z0-9_])\$ref(?![A-Za-z0-9_])"),
)


class _ProviderValidationError(ValueError):
    def __init__(self, category, provider, model):
        self.error_category = category
        self.provider = provider
        self.model = model
        super().__init__(
            f"LLM provider validation failed "
            f"(category={category}, provider={provider or 'missing'}, "
            f"model={model or 'missing'})"
        )


class _ProviderResponseError(RuntimeError):
    def __init__(
        self,
        provider,
        model,
        *,
        refusal_present=False,
        reasoning_present=False,
        response_mime_type=None,
        schema_present=False,
    ):
        self.error_category = "refusal_or_empty_content"
        mime_classification = (
            "json"
            if response_mime_type == "application/json"
            else "text_or_unspecified"
        )
        super().__init__(
            f"LLM provider response unusable "
            f"(category=refusal_or_empty_content, provider={provider}, "
            f"model={model}, empty_content=true, "
            f"refusal_present={str(bool(refusal_present)).lower()}, "
            f"reasoning_present={str(bool(reasoning_present)).lower()}, "
            f"response_mime_type={mime_classification}, "
            f"schema_present={str(bool(schema_present)).lower()})"
        )


def _normalize_and_validate_provider_model(provider, model):
    provider_name = str(provider or "").strip().lower()
    model_name = str(model or "").strip()
    model_key = model_name.lower()

    if not provider_name:
        raise _ProviderValidationError(
            "unsupported_provider",
            provider_name,
            model_name,
        )
    if not model_name:
        raise _ProviderValidationError(
            "configuration",
            provider_name,
            model_name,
        )
    if provider_name not in _SUPPORTED_PROVIDERS:
        raise _ProviderValidationError(
            "unsupported_provider",
            provider_name,
            model_name,
        )

    known_provider = _KNOWN_MODEL_PROVIDERS.get(model_key)
    if known_provider and known_provider != provider_name:
        raise _ProviderValidationError(
            "provider_model_mismatch",
            provider_name,
            model_name,
        )

    return provider_name, model_name


def _classify_provider_error(exc):
    explicit_category = str(getattr(exc, "error_category", "") or "").strip()
    if explicit_category in _PROVIDER_ERROR_CATEGORIES:
        return explicit_category

    status_code = getattr(exc, "status_code", None)
    try:
        status_code = int(status_code)
    except Exception:
        status_code = None

    class_name = exc.__class__.__name__.strip().lower()
    message = str(exc or "").strip().lower()[:512]
    classification_text = f"{class_name} {message}"

    if "provider_model_mismatch" in classification_text or (
        "provider" in classification_text and "model mismatch" in classification_text
    ):
        return "provider_model_mismatch"
    if "unsupported provider" in classification_text:
        return "unsupported_provider"
    if (
        "not found in environment" in classification_text
        or "missing credential" in classification_text
        or "missing configuration" in classification_text
        or "configuration" in class_name
    ):
        return "configuration"
    if isinstance(exc, TimeoutError) or "timeout" in class_name or "timed out" in message:
        return "timeout"
    if (
        isinstance(exc, ConnectionError)
        or "connection" in class_name
        or "connecterror" in class_name
        or "connection reset" in message
        or "network unavailable" in message
    ):
        return "connection"
    if status_code == 429 or "ratelimit" in class_name or "rate limit" in message:
        return "rate_limit"
    if (
        status_code is not None
        and 500 <= status_code <= 599
    ) or any(
        marker in classification_text
        for marker in (
            "internal server error",
            "service unavailable",
            "bad gateway",
            "gateway timeout",
            "servererror",
        )
    ):
        return "provider_5xx"
    if status_code == 401 or "authentication" in class_name or "unauthenticated" in message:
        return "authentication"
    if (
        status_code == 403
        or "permissiondenied" in class_name
        or "authorization" in class_name
        or "forbidden" in message
    ):
        return "authorization"
    if status_code in {400, 404, 405, 409, 422} or any(
        marker in classification_text
        for marker in ("badrequest", "invalid request", "invalid parameter")
    ):
        return "invalid_request"
    if any(
        marker in classification_text
        for marker in (
            "jsondecodeerror",
            "schema validation",
            "schema error",
            "parse error",
            "malformed json",
        )
    ):
        return "schema_or_parse"
    if any(
        marker in classification_text
        for marker in (
            "refusal_or_empty_content",
            "returned no usable content",
            "empty response",
            "refused response",
        )
    ):
        return "refusal_or_empty_content"
    if any(
        marker in classification_text
        for marker in (
            "safetyerror",
            "safety violation",
            "content filter",
            "policy violation",
        )
    ):
        return "safety"
    return "unknown"


def _allowlisted_provider_error_token(value, allowed_values):
    token = str(value or "").strip().lower()
    return token if token in allowed_values else ""


def _structured_provider_error(exc):
    body = getattr(exc, "body", None)
    if not isinstance(body, dict):
        return {}, {}
    error = body.get("error")
    return body, error if isinstance(error, dict) else body


def _explicit_safe_schema_keyword(message):
    for keyword, pattern in _SAFE_SCHEMA_KEYWORD_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return keyword
    return ""


def _classify_invalid_request_reason(error, body):
    message = str(error.get("message") or "")[:2_000]
    lowered = message.lower()
    error_code = _allowlisted_provider_error_token(
        error.get("code"),
        _SAFE_PROVIDER_ERROR_CODES,
    )
    error_param = _allowlisted_provider_error_token(
        error.get("param"),
        _SAFE_PROVIDER_ERROR_PARAMS,
    )
    classification_text = f"{lowered} {error_code} {error_param}"
    schema_keyword = _explicit_safe_schema_keyword(message)
    unsupported_markers = (
        "not supported",
        "unsupported",
        "unrecognized",
        "unknown keyword",
    )

    if (
        schema_keyword
        and ("schema" in lowered or "json" in lowered)
        and any(marker in classification_text for marker in unsupported_markers)
    ):
        return "unsupported_schema_keyword", schema_keyword
    if "failed_generation" in error or "failed_generation" in body:
        return "generated_schema_mismatch", ""
    if (
        "failed_generation" in classification_text
        or "tool_use_failed" in error_code
    ):
        return "generated_schema_mismatch", ""
    if "response_format" in classification_text or "response format" in lowered:
        return "response_format", ""
    if any(
        marker in classification_text
        for marker in (
            "response_schema",
            "response schema",
            "json_schema",
            "json schema",
        )
    ):
        return "response_schema", ""
    if any(
        marker in classification_text
        for marker in (
            "include_reasoning",
            "reasoning_effort",
            "reasoning parameter",
        )
    ):
        return "reasoning_parameter", ""
    if "temperature" in classification_text:
        return "temperature", ""
    if any(
        marker in classification_text
        for marker in (
            "max_completion_tokens",
            "max_tokens",
            "token limit",
            "context length",
            "context_length_exceeded",
        )
    ):
        return "token_limit", ""
    if "messages" in classification_text:
        return "messages", ""
    if "model" in classification_text:
        return "model_parameter", ""
    if (
        any(marker in classification_text for marker in unsupported_markers)
        and (
            "parameter" in lowered
            or " param" in lowered
            or error_param in _SAFE_PROVIDER_ERROR_PARAMS
        )
    ):
        return "unsupported_parameter", ""
    return "other_invalid_request", ""


def _bounded_invalid_request_diagnostic(exc, category, provider):
    status_code = getattr(exc, "status_code", None)
    try:
        status_code = int(status_code)
    except Exception:
        status_code = None
    if category != "invalid_request" or provider != "groq" or status_code != 400:
        return {}

    body, error = _structured_provider_error(exc)
    reason, schema_keyword = _classify_invalid_request_reason(error, body)
    if reason not in _INVALID_REQUEST_REASON_CATEGORIES:
        return {}

    diagnostic = {"invalid_request_reason": reason}
    safe_type = _allowlisted_provider_error_token(
        error.get("type"),
        _SAFE_PROVIDER_ERROR_TYPES,
    )
    safe_code = _allowlisted_provider_error_token(
        error.get("code"),
        _SAFE_PROVIDER_ERROR_CODES,
    )
    safe_param = _allowlisted_provider_error_token(
        error.get("param"),
        _SAFE_PROVIDER_ERROR_PARAMS,
    )
    if safe_type:
        diagnostic["error_type"] = safe_type
    if safe_code:
        diagnostic["error_code"] = safe_code
    if safe_param:
        diagnostic["error_param"] = safe_param
    if schema_keyword:
        diagnostic["schema_keyword"] = schema_keyword
    return diagnostic


def _raise_bounded_provider_failure(
    category,
    provider,
    model,
    stage,
    diagnostic=None,
):
    safe_diagnostic = diagnostic if isinstance(diagnostic, dict) else {}
    diagnostic_suffix = "".join(
        f", {field_name}={safe_diagnostic[field_name]}"
        for field_name in (
            "invalid_request_reason",
            "error_type",
            "error_code",
            "error_param",
            "schema_keyword",
        )
        if safe_diagnostic.get(field_name)
    )
    raise RuntimeError(
        f"LLM provider invocation failed "
        f"(stage={stage}, category={category}, provider={provider}, model={model}"
        f"{diagnostic_suffix})"
    ) from None


_groq_client = None
_openai_client = None

_provider_metrics_lock = Lock()

_provider_metrics = {
    "primary_attempts": 0,
    "fallback_attempts": 0,
    "groq_calls": 0,
    "openai_calls": 0,
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

def get_openai_client():
    global _openai_client

    if _openai_client is None:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not found in environment")
        _openai_client = OpenAI(api_key=openai_api_key)

    return _openai_client

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


def _is_openai_gpt_5_mini_model(model):
    model_name = str(model or "").strip()
    return bool(_OPENAI_GPT_5_MINI_MODEL_PATTERN.fullmatch(model_name))


def _run_groq_chat_completion(
    messages,
    model,
    temperature,
    max_tokens,
    response_mime_type=None,
    response_schema=None,
    return_parsed=False,
    thinking_budget=None,
    provider_client=None,
):
    increment_provider_metric("groq_calls")
    client = provider_client if provider_client is not None else get_groq_client()

    request_kwargs = {
        "model": model,
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
        "messages": messages,
    }

    model_name = str(model or "").strip().lower()
    supports_json_schema = model_name not in _GROQ_MODELS_WITHOUT_JSON_SCHEMA
    uses_structured_json_schema = (
        response_mime_type == "application/json"
        and response_schema is not None
        and supports_json_schema
    )
    is_groq_gpt_oss = model_name.startswith("openai/gpt-oss-")
    if is_groq_gpt_oss and not uses_structured_json_schema:
        request_kwargs["include_reasoning"] = False
    if is_groq_gpt_oss and thinking_budget == 0:
        # Groq GPT-OSS has no zero-reasoning setting: "low" is the lowest
        # reasoning effort this transport has empirically sustained. Map the
        # existing zero thinking-budget task intent onto it, mirroring the
        # OpenAI gpt-5-mini precedent below. This is an intent mapping, not a
        # claim that "low" performs no reasoning.
        request_kwargs["reasoning_effort"] = "low"

    if response_mime_type == "application/json":
        if uses_structured_json_schema:
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
        raise _ProviderResponseError(
            "groq",
            model,
            refusal_present=bool(refusal),
            reasoning_present=bool(reasoning),
            response_mime_type=response_mime_type,
            schema_present=response_schema is not None,
        )

    if return_parsed and response_mime_type == "application/json":
        try:
            return json.loads(text)
        except Exception:
            return text

    return text

def _run_openai_chat_completion(
    messages,
    model,
    temperature,
    max_tokens,
    response_mime_type=None,
    response_schema=None,
    return_parsed=False,
    thinking_budget=None,
    provider_client=None,
):
    increment_provider_metric("openai_calls")
    client = provider_client if provider_client is not None else get_openai_client()

    request_kwargs = {
        "model": model,
        "max_completion_tokens": max_tokens,
        "messages": messages,
    }

    is_gpt_5_mini = _is_openai_gpt_5_mini_model(model)

    if not is_gpt_5_mini or temperature == 1:
        request_kwargs["temperature"] = temperature

    if is_gpt_5_mini and thinking_budget == 0:
        request_kwargs["reasoning_effort"] = "minimal"

    if response_mime_type == "application/json":
        if response_schema is not None:
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
        raise _ProviderResponseError(
            "openai",
            model,
            refusal_present=bool(refusal),
            reasoning_present=False,
            response_mime_type=response_mime_type,
            schema_present=response_schema is not None,
        )

    if return_parsed and response_mime_type == "application/json":
        try:
            return json.loads(text)
        except Exception:
            return text

    return text

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
    provider_client=None,
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
            provider_client=provider_client,
        )

    if provider_name == "openai":
        return _run_openai_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_mime_type=response_mime_type,
            response_schema=response_schema,
            return_parsed=return_parsed,
            thinking_budget=thinking_budget,
            provider_client=provider_client,
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
    provider_client=None,
):
    primary_provider, primary_model = _normalize_and_validate_provider_model(
        provider or DEFAULT_PROVIDER,
        model or DEFAULT_MODEL,
    )

    effective_fallback_enabled = FALLBACK_ENABLED if fallback_enabled is None else bool(fallback_enabled)
    if provider_client is not None and effective_fallback_enabled:
        raise _ProviderValidationError(
            "configuration",
            primary_provider,
            primary_model,
        )
    effective_fallback_provider = str(
        fallback_provider or FALLBACK_PROVIDER
    ).strip().lower()
    effective_fallback_model = str(
        fallback_model or FALLBACK_MODEL
    ).strip()

    if effective_fallback_enabled:
        (
            effective_fallback_provider,
            effective_fallback_model,
        ) = _normalize_and_validate_provider_model(
            effective_fallback_provider,
            effective_fallback_model,
        )
        if primary_provider == effective_fallback_provider:
            raise _ProviderValidationError(
                "configuration",
                effective_fallback_provider,
                effective_fallback_model,
            )

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
            provider_client=provider_client,
        )
        return {
            "content": content,
            "provider": primary_provider,
            "model": primary_model,
            "fallback_used": False,
        }

    except Exception as primary_error:
        primary_category = _classify_provider_error(primary_error)
        primary_diagnostic = _bounded_invalid_request_diagnostic(
            primary_error,
            primary_category,
            primary_provider,
        )
        if (
            not effective_fallback_enabled
            or primary_category not in _FALLBACK_ELIGIBLE_ERROR_CATEGORIES
        ):
            increment_provider_metric("provider_failures")
            _raise_bounded_provider_failure(
                primary_category,
                primary_provider,
                primary_model,
                "primary",
                primary_diagnostic,
            )

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
            fallback_category = _classify_provider_error(fallback_error)
            increment_provider_metric("provider_failures")
            raise RuntimeError(
                f"LLM provider invocation failed "
                f"(stage=fallback, primary_category={primary_category}, "
                f"primary_provider={primary_provider}, primary_model={primary_model}, "
                f"fallback_category={fallback_category}, "
                f"fallback_provider={effective_fallback_provider}, "
                f"fallback_model={effective_fallback_model})"
            ) from None
        
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
    provider_client=None,
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
        provider_client=provider_client,
    )
    return result["content"]
