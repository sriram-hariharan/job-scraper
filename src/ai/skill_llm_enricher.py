import hashlib
import json
import os
import re

from dotenv import load_dotenv
from tqdm import tqdm
from threading import Lock

from src.ai.llm_client import run_chat_completion
from src.utils.skill_normalizer import (
    EXTRACTED_SKILL_NORMALIZATION_CONTRACT_VERSION,
    normalize_extracted_skills,
)

from src.storage.skill_corpus_store import (
    get_cached_llm_skills,
    store_cached_llm_skills,
)
from src.config.consts import (
    REQUIRED_CONTEXT_PATTERNS,
    PREFERRED_CONTEXT_PATTERNS,
    EMBEDDED_SKILL_PATTERNS
)
from src.utils.logging import get_logger

load_dotenv()

logger = get_logger("ai_eval_filter")

SKILL_EXTRACTION_MODE = os.getenv("SKILL_EXTRACTION_MODE", "cache_prefer_live").strip().lower()
VALID_EXTRACTION_MODES = {"cache_prefer_live", "cache_only", "live_only"}

SKILL_EXTRACTION_STATUS_SUCCESS_NONEMPTY = "success_nonempty"
SKILL_EXTRACTION_STATUS_SUCCESS_EMPTY = "success_empty"
SKILL_EXTRACTION_STATUS_FAILURE = "failure"
SKILL_EXTRACTION_STATUSES = frozenset(
    {
        SKILL_EXTRACTION_STATUS_SUCCESS_NONEMPTY,
        SKILL_EXTRACTION_STATUS_SUCCESS_EMPTY,
        SKILL_EXTRACTION_STATUS_FAILURE,
    }
)
SKILL_EXTRACTION_FAILURE_STAGES = frozenset(
    {"cache", "execution", "input", "response", "route", "unknown"}
)

SKILL_EXTRACTION_PROMPT_VERSION = "v6_postfilter_cleanup"
SKILL_CONTEXT_REASSIGNMENT_CONTRACT_VERSION = (
    "section-bounded-context-v2"
)
SKILL_EXTRACTION_TEMPERATURE = 0
SKILL_EXTRACTION_MAX_TOKENS = 500
# Lowest-reasoning task intent. The shared transport owns the mapping to a
# provider request field (Groq GPT-OSS: reasoning_effort="low"); this module
# never constructs provider SDK reasoning parameters itself.
SKILL_EXTRACTION_THINKING_BUDGET = 0
SKILL_EXTRACTION_FULL_TEXT_LIMIT = 7000
SKILL_EXTRACTION_HEAD_CHARS = 2500
SKILL_EXTRACTION_TAIL_CHARS = 1800
SKILL_EXTRACTION_WINDOW_CHARS = 900
SKILL_EXTRACTION_MAX_KEYWORD_WINDOWS = 10

skill_cache_metrics_lock = Lock()

skill_cache_metrics = {
    "cache_hits": 0,
    "cache_misses": 0,
    "cache_stores": 0,
    "cache_only_skips": 0,
    "live_failures": 0,
}

# progress bar for LLM calls
llm_bar = tqdm(desc="LLM skill extraction", unit="job")


SYSTEM_PROMPT = """
You analyze job descriptions and extract concrete technical skills.

A valid skill must be one of the following:

TECHNOLOGY
Specific tools, programming languages, frameworks, libraries, or platforms.
Examples: python, sql, spark, pytorch, tensorflow, airflow, dbt, kafka,
snowflake, databricks, kubernetes, docker, terraform, tableau, looker

ML_CONCEPT
Machine learning or AI concepts used in model development.
Examples: machine learning, deep learning, computer vision, nlp,
transformers, embeddings, vector databases, rag, large language models

METHOD
Statistical or experimentation methods.
Examples: a/b testing, causal inference, bayesian inference,
statistical modeling, forecasting, hypothesis testing,
experimental design, time series analysis

════════════════════════════════════════
STRICT RULES
════════════════════════════════════════

RULE 1 — Extract ONLY skills explicitly written in the job description.

RULE 2 — A skill must be a single specific technology, ML concept, or method.
         It must map to something a developer would import, install, or learn as a discipline.

RULE 3 — NEVER extract the following. If you are unsure, DO NOT include it:

  ✗ Generic categories       → "cloud data platforms", "bi tools", "data pipelines"
  ✗ Engineering activities   → "deployment", "monitoring", "fine-tuning", "optimization",
                               "distributed training", "inference optimization",
                               "application development", "ci/cd pipelines"
  ✗ Vague descriptors        → "noisy data", "analysis-ready tables", "regression basics",
                               "sql/python code", "deep specialization"
  ✗ Business/domain terms    → "fintech", "healthcare", "payments", "marketing"
  ✗ Soft skills              → "stakeholder management", "communication", "collaboration",
                               "confident presenting", "clear writing", "structured thinking",
                               "problem solving", "qa/validation"
  ✗ Experience requirements  → "5+ years", "advanced sql proficiency", "strong cs fundamentals"
  ✗ Education requirements   → "bachelor's degree", "master's degree", "phd", "ms in cs"
  ✗ Compound skill phrases   → anything with more than 3 words describing an activity

RULE 4 — If a phrase describes WHAT YOU DO with a skill rather than the skill itself, ignore it.
  ✗ BAD: "distributed training of ml models"   ✓ GOOD: (nothing — this is an activity)
  ✗ BAD: "sql/python code"                     ✓ GOOD: sql, python
  ✗ BAD: "statistical modeling/forecasting"    ✓ GOOD: statistical modeling, forecasting
  ✗ BAD: "causal inference/experimentation"    ✓ GOOD: causal inference, experimental design

RULE 5 — Split slash-separated compound terms into individual skills only if EACH part is valid.

RULE 6 — Return skills exactly as they appear in the job description (lowercase).

RULE 7 — When in doubt, leave it out.

RULE 8 — Preserve requirement level exactly as written in the job description.

  • Skills from sections or phrases like:
    "required qualifications", "minimum qualifications", "basic qualifications",
    "must have", "requirements", "secondary qualifications"
    → put in "required_skills"

  • Skills from sections or phrases like:
    "preferred qualifications", "bonus points", "nice to have", "plus", "preferred"
    → put in "preferred_skills"

RULE 9 — NEVER upgrade a preferred / bonus skill into required just because it is technical.

RULE 10 — If the same skill appears in both required and preferred contexts,
          keep it only in "required_skills".

════════════════════════════════════════
EXAMPLE 1
════════════════════════════════════════

Job description snippet:
"We need strong SQL and Python skills, experience with Airflow for pipeline orchestration.
A/B testing and causal inference experience preferred. Must have a bachelor's degree."

Correct output:
{
  "required_skills": ["sql", "python", "airflow"],
  "preferred_skills": ["a/b testing", "causal inference"]
}

Wrong output (DO NOT do this):
{
  "required_skills": ["sql", "python", "airflow", "a/b testing", "causal inference"],
  "preferred_skills": []
}

════════════════════════════════════════
EXAMPLE 2
════════════════════════════════════════

Job description snippet:
"Required Qualifications:
- advanced user of excel / google sheets

Bonus Points:
- experience working with netsuite, floqast, cryptio"

Correct output:
{
  "required_skills": ["excel", "google sheets"],
  "preferred_skills": ["netsuite", "floqast", "cryptio"]
}
"""


def _build_skill_extraction_user_prompt(extraction_text: str) -> str:
    return f"""
    Extract REQUIRED and PREFERRED technical skills
    from the following job description.

    JOB DESCRIPTION:
    {extraction_text}
    """


def _build_skill_extraction_retry_prompt(primary_prompt: str) -> str:
    return primary_prompt + "\n\nReturn ONLY valid JSON. No prose. No markdown. No explanation."


def resolve_effective_user_provider_route(owner_user_id: str, workload_id: str):
    from importlib import import_module

    routing_service = import_module(
        "src.app.provider_model_" "routing_service"
    )
    return routing_service.resolve_effective_user_provider_route(
        owner_user_id,
        workload_id,
    )


def resolve_recommended_user_provider_route(workload_id: str):
    from importlib import import_module

    routing_service = import_module(
        "src.app.provider_model_" "routing_service"
    )
    return routing_service.resolve_recommended_user_provider_route(
        workload_id,
    )


def run_user_chat_completion_with_metadata(**kwargs):
    from src.ai.user_provider_runtime import (
        run_user_chat_completion_with_metadata as execute,
    )

    return execute(**kwargs)


def build_skill_extraction_production_task_contract_material():
    primary_prompt = _build_skill_extraction_user_prompt("<job_description>")
    return {
        "task_contract_version": SKILL_EXTRACTION_PROMPT_VERSION,
        "prompt_contract": {
            "system": SYSTEM_PROMPT,
            "primary_user_template": primary_prompt,
            "retry_user_template": _build_skill_extraction_retry_prompt(primary_prompt),
        },
        "input_contract": {
            "fields": ["job_description"],
            "full_text_limit": SKILL_EXTRACTION_FULL_TEXT_LIMIT,
            "head_chars": SKILL_EXTRACTION_HEAD_CHARS,
            "tail_chars": SKILL_EXTRACTION_TAIL_CHARS,
            "window_chars": SKILL_EXTRACTION_WINDOW_CHARS,
            "max_keyword_windows": SKILL_EXTRACTION_MAX_KEYWORD_WINDOWS,
            "window_labels": ["HEAD", "PRIORITY:<pattern>", "FALLBACK:<pattern>", "TAIL"],
        },
        "output_contract": {
            "type": "object",
            "required": ["required_skills", "preferred_skills"],
            "properties": {
                "required_skills": {"type": "array", "items": {"type": "string"}},
                "preferred_skills": {"type": "array", "items": {"type": "string"}},
            },
            "parsers": ["json_object_extraction", "sectioned_skill_lists", "json_retry"],
        },
        "deterministic_transformation_contract": {
            "normalizer": EXTRACTED_SKILL_NORMALIZATION_CONTRACT_VERSION,
            "context_reassignment": (
                SKILL_CONTEXT_REASSIGNMENT_CONTRACT_VERSION
            ),
            "steps": [
                "expand_skill_candidates",
                "verbatim_job_text_filter",
                "required_preferred_deduplication",
                "context_bucket_reassignment",
                "shadowed_generic_skill_removal",
            ],
        },
        "task_parameters": {
            "temperature": SKILL_EXTRACTION_TEMPERATURE,
            "max_tokens": SKILL_EXTRACTION_MAX_TOKENS,
            "thinking_budget": SKILL_EXTRACTION_THINKING_BUDGET,
        },
    }

def _response_preview(response: str, limit: int = 500) -> str:
    text = (response or "").replace("\n", "\\n").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "...[truncated]"


def extract_json_from_response(response: str):
    """
    Extract JSON safely from LLM responses even if
    the model adds extra text before or after.
    """

    response = response.replace("```json", "").replace("```", "").strip()

    start = response.find("{")
    end = response.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM response")

    json_str = response[start:end + 1]

    return json.loads(json_str)


def _clean_skill_item(item: str) -> str:
    item = (item or "").strip().lower()
    item = re.sub(r"^[\-\*\u2022\d\.\)\s]+", "", item)
    item = item.strip().strip('"\''"`")
    item = re.sub(r"\s+", " ", item)
    item = item.rstrip(".,:;")
    return item

def _expand_skill_candidates(raw_skill: str):
    raw_text = (raw_skill or "").strip()
    if not raw_text:
        return []

    candidates = []

    cleaned_full = _clean_skill_item(raw_text)
    if cleaned_full:
        candidates.append(cleaned_full)

    # If the model emitted explicit quoted skills, salvage them directly.
    for quoted in re.findall(r'"([^"]+)"', raw_text):
        cleaned = _clean_skill_item(quoted)
        if cleaned:
            candidates.append(cleaned)

    # If the model emitted canonicalized targets after "->", salvage the RHS skills.
    if "->" in raw_text:
        rhs = raw_text.split("->", 1)[1]
        for part in re.split(r"[;,]", rhs):
            cleaned = _clean_skill_item(part)
            if cleaned:
                candidates.append(cleaned)

    # Keep the old parenthetical simplification
    simplified = re.sub(r"\s*\(([^)]*)\)", "", cleaned_full).strip()
    if simplified:
        candidates.append(simplified)

    parenthetical_matches = re.findall(r"\(([^)]*)\)", cleaned_full)
    for inner in parenthetical_matches:
        cleaned = _clean_skill_item(inner)
        if cleaned:
            candidates.append(cleaned)

    # Normalize known acronym + canonical pairs
    if simplified == "ml" and "machine learning" in candidates:
        candidates.append("machine learning")

    # Salvage explicitly known embedded tools/technologies only
    for pattern, canonical in EMBEDDED_SKILL_PATTERNS:
        if re.search(pattern, cleaned_full):
            candidates.append(canonical)

    expanded = []
    for candidate in candidates:
        cleaned = _clean_skill_item(candidate)
        if cleaned:
            expanded.append(cleaned)

    return list(dict.fromkeys(expanded))

def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _filter_skill_candidates(skills, job_text: str):
    expanded = []

    for raw_skill in skills:
        expanded.extend(_expand_skill_candidates(raw_skill))

    return normalize_extracted_skills(expanded, job_text)

def _nearest_preceding_section_bucket(job_norm: str, position: int, max_backscan: int = 2500):
    nearest = None  # (start_idx, bucket)

    for pattern in REQUIRED_CONTEXT_PATTERNS:
        for match in re.finditer(pattern, job_norm):
            if match.start() <= position and position - match.start() <= max_backscan:
                if nearest is None or match.start() > nearest[0]:
                    nearest = (match.start(), "required")

    for pattern in PREFERRED_CONTEXT_PATTERNS:
        for match in re.finditer(pattern, job_norm):
            if match.start() <= position and position - match.start() <= max_backscan:
                if nearest is None or match.start() > nearest[0]:
                    nearest = (match.start(), "preferred")

    return nearest[1] if nearest is not None else None


def _has_inline_preferred_context(context: str) -> bool:
    return any(
        re.search(pattern, context)
        for pattern in [
            r"\bis a plus\b",
            r"\ba plus\b",
            r"\bnice to have\b",
            r"\bbonus points\b",
            r"\bpreferred qualifications\b",
            r"\bpreferred\b",
        ]
    )


def _has_inline_required_context(context: str) -> bool:
    return any(
        re.search(pattern, context)
        for pattern in [
            r"\brequired qualifications\b",
            r"\bminimum qualifications\b",
            r"\bbasic qualifications\b",
            r"\bmust have\b",
            r"\bwhat we're looking for\b",
            r"\bwhat you need\b",
            r"\bwhat you'll need\b",
        ]
    )
def _build_explicit_section_spans(job_norm: str):
    required_headers = [
        r"\brequired qualifications\b",
        r"\bminimum qualifications\b",
        r"\bbasic qualifications\b",
        r"\bwhat we're looking for\b",
        r"\bwhat you need\b",
        r"\bwhat you'll need\b",
        r"\bbecause you have\b",
    ]

    preferred_headers = [
        r"\bpreferred qualifications\b",
        r"\bnice to have\b",
        r"\bbonus points\b",
    ]

    headers = []

    for pattern in required_headers:
        for match in re.finditer(pattern, job_norm):
            headers.append((match.start(), match.end(), "required"))

    for pattern in preferred_headers:
        for match in re.finditer(pattern, job_norm):
            headers.append((match.start(), match.end(), "preferred"))

    headers.sort(key=lambda x: x[0])

    spans = []
    for idx, (start, end, bucket) in enumerate(headers):
        next_start = headers[idx + 1][0] if idx + 1 < len(headers) else len(job_norm)
        spans.append((start, next_start, bucket))

    return spans


def _inline_preferred_override(context: str) -> bool:
    return any(
        re.search(pattern, context)
        for pattern in [
            r"\bis a plus\b",
            r"\ba plus\b",
            r"\bnice to have\b",
            r"\bbonus points\b",
            r"\bpreferred\b",
        ]
    )

def _context_bucket_for_skill(skill: str, job_text: str, window_chars: int = 220):
    skill_norm = _normalize_for_match(skill)
    job_norm = (job_text or "").lower()

    if not skill_norm or not job_norm:
        return None

    candidates = [skill_norm]

    simplified = re.sub(r"\s*\([^)]*\)", "", skill_norm).strip()
    if simplified and simplified not in candidates:
        candidates.append(simplified)

    spans = _build_explicit_section_spans(job_norm)

    saw_required = False
    saw_preferred = False

    for candidate in candidates:
        candidate_pattern = re.escape(candidate).replace(r"\ ", r"\s+")
        pattern = rf"(?<![a-z0-9]){candidate_pattern}(?![a-z0-9])"
        for match in re.finditer(pattern, job_norm):
            containing_span = next(
                (
                    (span_start, span_end, bucket)
                    for span_start, span_end, bucket in spans
                    if span_start <= match.start() < span_end
                ),
                None,
            )

            context_start = max(0, match.start() - window_chars)
            context_end = min(len(job_norm), match.end() + window_chars)
            if containing_span is not None:
                span_start, span_end, _bucket = containing_span
                context_start = max(context_start, span_start)
                context_end = min(context_end, span_end)

            line_start = job_norm.rfind("\n", context_start, match.start()) + 1
            line_start = max(context_start, line_start)
            line_end = job_norm.find("\n", match.end(), context_end)
            if line_end == -1:
                line_end = context_end
            inline_context = job_norm[line_start:line_end]

            # Inline preferred language wins for that specific occurrence.
            if _inline_preferred_override(inline_context):
                saw_preferred = True
                continue

            # Otherwise only use explicit section spans.
            if containing_span is not None:
                _span_start, _span_end, bucket = containing_span
                if bucket == "required":
                    saw_required = True
                elif bucket == "preferred":
                    saw_preferred = True

    if saw_required and saw_preferred:
        return "required"
    if saw_required:
        return "required"
    if saw_preferred:
        return "preferred"
    return None


def _reassign_skills_by_context(required, preferred, job_text: str):
    req = set(required)
    pref = set(preferred)

    pref = {s for s in pref if s not in req}

    for skill in list(req):
        bucket = _context_bucket_for_skill(skill, job_text)
        if bucket == "preferred":
            req.discard(skill)
            pref.add(skill)

    for skill in list(pref):
        bucket = _context_bucket_for_skill(skill, job_text)
        if bucket == "required":
            pref.discard(skill)
            req.add(skill)

    pref = {s for s in pref if s not in req}
    return sorted(req), sorted(pref)


def _correct_cached_skill_buckets(cached, job_text: str):
    if not isinstance(cached, dict):
        return cached

    required = cached.get("required_skills")
    preferred = cached.get("preferred_skills")
    if (
        not isinstance(required, list)
        or not isinstance(preferred, list)
        or not all(isinstance(skill, str) for skill in required + preferred)
    ):
        return cached

    corrected_required, corrected_preferred = _reassign_skills_by_context(
        required,
        preferred,
        job_text,
    )
    cached["required_skills"] = corrected_required
    cached["preferred_skills"] = corrected_preferred
    return cached

def _drop_shadowed_generic_skills(required, preferred):
    req = set(required)
    pref = set(preferred)

    def remove_shadowed(skill_set):
        items = sorted(skill_set, key=len, reverse=True)
        keep = set(items)

        for item in items:
            if item == "aws" and any(s.startswith("aws ") for s in items if s != item):
                keep.discard(item)
            if item == "ci/cd practices" and "ci/cd" in items:
                keep.discard(item)

        return sorted(keep)

    req = set(remove_shadowed(req))
    pref = set(remove_shadowed(pref))

    pref = {s for s in pref if s not in req}
    return sorted(req), sorted(pref)

def _parse_sectioned_skill_response(response: str):
    """
    Parse common non-JSON LLM responses like:

    **REQUIRED SKILLS:**
    * python
    * sql

    **PREFERRED SKILLS:**
    * tableau
    * causal inference
    """

    lines = (response or "").splitlines()

    required_header_patterns = [
        r"required skills?",
        r"required qualifications?",
        r"minimum qualifications?",
        r"basic qualifications?",
        r"requirements?",
    ]

    preferred_header_patterns = [
        r"preferred skills?",
        r"preferred qualifications?",
        r"bonus points?",
        r"nice to have",
        r"preferred",
    ]

    current_section = None
    required = []
    preferred = []

    def _is_header(line: str, patterns):
        normalized = re.sub(r"[*_`:#\-\s]+", " ", line.strip().lower()).strip()
        return any(re.fullmatch(pattern, normalized) for pattern in patterns)

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        if _is_header(line, required_header_patterns):
            current_section = "required"
            continue

        if _is_header(line, preferred_header_patterns):
            current_section = "preferred"
            continue

        if current_section is None:
            continue

        if re.match(r"^[-*\u2022]\s+", line) or re.match(r"^\d+[\.\)]\s+", line):
            item = _clean_skill_item(line)
            if not item:
                continue

            if current_section == "required":
                required.append(item)
            else:
                preferred.append(item)

    required = sorted(set(required))
    preferred = sorted(set(s for s in preferred if s not in required))

    if not required and not preferred:
        raise ValueError("No sectioned skill lists found in LLM response")

    return {
        "required_skills": required,
        "preferred_skills": preferred,
    }


def build_skill_cache_key(job_text: str) -> str:
    """
    Stable cache key from normalized JD text + extraction strategy version.
    Lowercasing + whitespace collapsing prevents meaningless cache misses from formatting changes.
    """

    normalized = re.sub(r"\s+", " ", (job_text or "").strip().lower())
    payload = f"{SKILL_EXTRACTION_PROMPT_VERSION}::{normalized}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


_BOUNDED_LIVE_FAILURE_CATEGORIES = frozenset(
    {
        # Shared provider transport categories (src/ai/llm_client.py).
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
        # User-scoped runtime configuration categories
        # (src/ai/user_provider_runtime.py).
        "invalid_owner",
        "settings_unavailable",
        "credential_unavailable",
        "credential_not_configured",
        "client_construction_failed",
        "unsupported_provider_model",
    }
)
SKILL_EXTRACTION_FAILURE_CATEGORIES = _BOUNDED_LIVE_FAILURE_CATEGORIES
_BOUNDED_LIVE_FAILURE_ERROR_TYPE_LIMIT = 80
_BOUNDED_LIVE_FAILURE_CATEGORY_PATTERN = re.compile(r"category=([a-z0-9_]+)")
_BOUNDED_LIVE_FAILURE_STAGE_PATTERN = re.compile(r"stage=(primary|fallback)")


def _bounded_live_failure_diagnostic(exc):
    """Allowlisted, non-sensitive metadata about one live extraction failure.

    Never returns the exception message, repr, traceback, credentials,
    prompts, provider response content, job text, or owner identity.
    """

    error_type = str(type(exc).__name__ or "").strip()
    error_type = error_type[:_BOUNDED_LIVE_FAILURE_ERROR_TYPE_LIMIT] or "unknown"

    category = ""
    for attribute in ("category", "error_category"):
        value = getattr(exc, attribute, "")
        if isinstance(value, str) and value.strip():
            category = value.strip()
            break

    message = str(exc)

    if not category:
        category_match = _BOUNDED_LIVE_FAILURE_CATEGORY_PATTERN.search(message)
        if category_match:
            category = category_match.group(1)

    if category not in _BOUNDED_LIVE_FAILURE_CATEGORIES:
        category = "unknown"

    stage_match = _BOUNDED_LIVE_FAILURE_STAGE_PATTERN.search(message)
    stage = stage_match.group(1) if stage_match else "unknown"

    return {
        "error_type": error_type,
        "category": category,
        "stage": stage,
    }


def _successful_skill_result(result, *, invalid_stage: str = "response"):
    if not isinstance(result, dict):
        return get_empty_skill_result(
            failure_category="schema_or_parse",
            failure_stage=invalid_stage,
        )

    required = result.get("required_skills")
    preferred = result.get("preferred_skills")
    if (
        not isinstance(required, list)
        or not isinstance(preferred, list)
        or not all(isinstance(skill, str) for skill in required + preferred)
    ):
        return get_empty_skill_result(
            failure_category="schema_or_parse",
            failure_stage=invalid_stage,
        )

    result["extraction_status"] = (
        SKILL_EXTRACTION_STATUS_SUCCESS_NONEMPTY
        if required or preferred
        else SKILL_EXTRACTION_STATUS_SUCCESS_EMPTY
    )
    result["failure_category"] = ""
    result["failure_stage"] = ""
    return result


def get_empty_skill_result(
    *,
    failure_category: str = "unknown",
    failure_stage: str = "unknown",
):
    safe_category = str(failure_category or "").strip()
    if safe_category not in _BOUNDED_LIVE_FAILURE_CATEGORIES:
        safe_category = "unknown"

    safe_stage = str(failure_stage or "").strip()
    if safe_stage not in SKILL_EXTRACTION_FAILURE_STAGES:
        safe_stage = "unknown"

    return {
        "required_skills": [],
        "preferred_skills": [],
        "extraction_status": SKILL_EXTRACTION_STATUS_FAILURE,
        "failure_category": safe_category,
        "failure_stage": safe_stage,
    }


def reset_skill_cache_metrics():
    with skill_cache_metrics_lock:
        for key in skill_cache_metrics:
            skill_cache_metrics[key] = 0


def get_skill_cache_metrics():
    with skill_cache_metrics_lock:
        return dict(skill_cache_metrics)


def increment_skill_cache_metric(metric_name: str):
    with skill_cache_metrics_lock:
        if metric_name in skill_cache_metrics:
            skill_cache_metrics[metric_name] += 1


def _build_skill_extraction_text(
    job_text: str,
    head_chars: int = SKILL_EXTRACTION_HEAD_CHARS,
    tail_chars: int = SKILL_EXTRACTION_TAIL_CHARS,
    window_chars: int = SKILL_EXTRACTION_WINDOW_CHARS,
    max_keyword_windows: int = SKILL_EXTRACTION_MAX_KEYWORD_WINDOWS,
) -> str:
    text = (job_text or "").strip()
    if not text:
        return ""

    if len(text) <= SKILL_EXTRACTION_FULL_TEXT_LIMIT:
        return text

    priority_patterns = [
        r"\brequired qualifications\b",
        r"\bpreferred qualifications\b",
        r"\bminimum qualifications\b",
        r"\bbasic qualifications\b",
        r"\bnice to have\b",
        r"\bbonus points\b",
        r"\bmust have\b",
        r"\bwhat you'll need\b",
        r"\bwhat you need\b",
    ]

    fallback_patterns = [
        r"\brequirements\b",
        r"\bqualifications\b",
    ]

    snippets = []
    seen_ranges = []

    def add_window(label: str, start: int, end: int):
        overlaps_existing = any(not (end < s or start > e) for s, e in seen_ranges)
        if overlaps_existing:
            return False

        seen_ranges.append((start, end))
        snippet = text[start:end].strip()
        if snippet:
            snippets.append((label, snippet))
            return True
        return False

    head = text[:head_chars].strip()
    if head:
        snippets.append(("HEAD", head))

    # First pass: always prioritize explicit skill-section headers
    for pattern in priority_patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            start = max(0, match.start() - window_chars)
            end = min(len(text), match.end() + window_chars)
            add_window(f"PRIORITY:{pattern}", start, end)

    # Second pass: fill remaining budget with generic section words
    current_windows = len(seen_ranges)
    remaining = max(0, max_keyword_windows - current_windows)

    if remaining > 0:
        for pattern in fallback_patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                if remaining <= 0:
                    break
                start = max(0, match.start() - window_chars)
                end = min(len(text), match.end() + window_chars)
                if add_window(f"FALLBACK:{pattern}", start, end):
                    remaining -= 1
            if remaining <= 0:
                break

    tail = text[-tail_chars:].strip()
    if tail:
        snippets.append(("TAIL", tail))

    parts = []
    seen_bodies = set()

    for label, body in snippets:
        normalized = re.sub(r"\s+", " ", body).strip().lower()
        if not normalized or normalized in seen_bodies:
            continue
        seen_bodies.add(normalized)
        parts.append(f"[{label}]\n{body}")

    return "\n\n".join(parts)


def enrich_skills_with_llm(job_text, owner_user_id: str = ""):

    if SKILL_EXTRACTION_MODE not in VALID_EXTRACTION_MODES:
        logger.warning(
            f"Invalid SKILL_EXTRACTION_MODE='{SKILL_EXTRACTION_MODE}'. "
            "Falling back to 'cache_prefer_live'."
        )
        mode = "cache_prefer_live"
    else:
        mode = SKILL_EXTRACTION_MODE

    cache_key = build_skill_cache_key(job_text)

    if mode != "live_only":
        cached = get_cached_llm_skills(cache_key)
        if cached is not None:
            increment_skill_cache_metric("cache_hits")
            logger.info("LLM skill cache hit")
            return _successful_skill_result(
                _correct_cached_skill_buckets(cached, job_text),
                invalid_stage="cache",
            )

        increment_skill_cache_metric("cache_misses")
        logger.info("LLM skill cache miss")

        if mode == "cache_only":
            increment_skill_cache_metric("cache_only_skips")
            logger.info("LLM live extraction skipped (cache_only mode)")
            return get_empty_skill_result(
                failure_category="configuration",
                failure_stage="cache",
            )

    elif mode == "live_only":
        logger.info("LLM cache bypassed (live_only mode)")

    llm_bar.update(1)

    extraction_text = _build_skill_extraction_text(job_text)

    prompt = _build_skill_extraction_user_prompt(extraction_text)

    explicit_owner = str(owner_user_id or "").strip()
    owner = explicit_owner or str(
        os.environ.get("JOB_STACK_OWNER_USER_ID", "") or ""
    ).strip()
    active_provider = ""
    active_model = ""
    if owner:
        try:
            route = resolve_effective_user_provider_route(
                owner,
                "skill_extraction",
            )
            active_provider = str(route.get("provider") or "").strip()
            active_model = str(route.get("model") or "").strip()
            if not active_provider or not active_model:
                raise ValueError("invalid effective route")
        except (Exception, SystemExit) as route_exc:
            increment_skill_cache_metric("live_failures")
            route_diagnostic = _bounded_live_failure_diagnostic(route_exc)
            logger.warning(
                "LLM skill extraction owner route unavailable | "
                "error_type=%s category=%s",
                route_diagnostic["error_type"],
                route_diagnostic["category"],
            )
            return get_empty_skill_result(
                failure_category=route_diagnostic["category"],
                failure_stage="route",
            )
    else:
        try:
            route = resolve_recommended_user_provider_route(
                "skill_extraction",
            )
            active_provider = str(route.get("provider") or "").strip()
            active_model = str(route.get("model") or "").strip()
            if not active_provider or not active_model:
                raise ValueError("invalid recommended route")
        except (Exception, SystemExit) as route_exc:
            increment_skill_cache_metric("live_failures")
            route_diagnostic = _bounded_live_failure_diagnostic(route_exc)
            logger.warning(
                "LLM skill extraction recommended route unavailable | "
                "error_type=%s category=%s",
                route_diagnostic["error_type"],
                route_diagnostic["category"],
            )
            return get_empty_skill_result(
                failure_category=route_diagnostic["category"],
                failure_stage="route",
            )

    def _call_live_llm(user_prompt: str):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        if owner:
            result = run_user_chat_completion_with_metadata(
                owner_user_id=owner,
                provider=active_provider,
                model=active_model,
                temperature=SKILL_EXTRACTION_TEMPERATURE,
                max_tokens=SKILL_EXTRACTION_MAX_TOKENS,
                thinking_budget=SKILL_EXTRACTION_THINKING_BUDGET,
                messages=messages,
            )
            return result.get("content", "")
        return run_chat_completion(
            provider=active_provider,
            model=active_model,
            temperature=SKILL_EXTRACTION_TEMPERATURE,
            max_tokens=SKILL_EXTRACTION_MAX_TOKENS,
            fallback_enabled=False,
            workload_id="skill_extraction",
            messages=messages,
        )

    try:
        response = _call_live_llm(prompt)

    except Exception as exc:
        increment_skill_cache_metric("live_failures")
        live_diagnostic = _bounded_live_failure_diagnostic(exc)
        if owner:
            logger.warning(
                "LLM skill extraction owner execution failed | "
                "provider=%s model=%s error_type=%s category=%s stage=%s",
                active_provider,
                active_model,
                live_diagnostic["error_type"],
                live_diagnostic["category"],
                live_diagnostic["stage"],
            )
        else:
            logger.warning(
                "LLM skill extraction failed | "
                "provider=%s model=%s error_type=%s category=%s stage=%s",
                active_provider or "default",
                active_model,
                live_diagnostic["error_type"],
                live_diagnostic["category"],
                live_diagnostic["stage"],
            )
        return get_empty_skill_result(
            failure_category=live_diagnostic["category"],
            failure_stage="execution",
        )
    except SystemExit as exit_exc:
        if not owner:
            raise
        increment_skill_cache_metric("live_failures")
        exit_diagnostic = _bounded_live_failure_diagnostic(exit_exc)
        logger.warning(
            "LLM skill extraction owner execution failed | "
            "provider=%s model=%s error_type=%s category=%s stage=%s",
            active_provider,
            active_model,
            exit_diagnostic["error_type"],
            exit_diagnostic["category"],
            exit_diagnostic["stage"],
        )
        return get_empty_skill_result(
            failure_category=exit_diagnostic["category"],
            failure_stage="execution",
        )

    def _finalize_skill_result(parsed_obj):
        raw_required = parsed_obj.get("required_skills", [])
        raw_preferred = parsed_obj.get("preferred_skills", [])
        model_emitted_candidates = bool(raw_required) or bool(raw_preferred)

        required = _filter_skill_candidates(raw_required, job_text)
        preferred = _filter_skill_candidates(raw_preferred, job_text)

        preferred = [s for s in preferred if s not in required]
        required, preferred = _reassign_skills_by_context(required, preferred, job_text)
        required, preferred = _drop_shadowed_generic_skills(required, preferred)

        if required or preferred:
            logger.info("LLM skill extraction finalized nonempty")
        elif model_emitted_candidates:
            logger.info("LLM skill extraction finalized empty | source=postfilter")
        else:
            logger.info("LLM skill extraction finalized empty | source=model")

        result = {
            "required_skills": required,
            "preferred_skills": preferred
        }

        if mode != "live_only":
            store_cached_llm_skills(
                cache_key=cache_key,
                model=active_model,
                required_skills=required,
                preferred_skills=preferred,
            )
            increment_skill_cache_metric("cache_stores")
            logger.info("LLM skill cache stored")

        return _successful_skill_result(result)

    try:
        parsed = extract_json_from_response(response)
        return _finalize_skill_result(parsed)

    except Exception as json_error:
        json_diagnostic = _bounded_live_failure_diagnostic(json_error)
        logger.warning(
            "Failed JSON parse on first attempt | error_type=%s "
            "category=schema_or_parse",
            json_diagnostic["error_type"],
        )

    try:
        parsed_sectioned = _parse_sectioned_skill_response(response)
        logger.info("LLM skill extraction section-parser succeeded on first attempt")
        return _finalize_skill_result(parsed_sectioned)

    except Exception as section_error:
        section_diagnostic = _bounded_live_failure_diagnostic(section_error)
        logger.warning(
            "Failed section-parser on first attempt | error_type=%s "
            "category=schema_or_parse",
            section_diagnostic["error_type"],
        )

    retry_prompt = _build_skill_extraction_retry_prompt(prompt)

    try:
        retry_response = _call_live_llm(retry_prompt)

        parsed_retry = extract_json_from_response(retry_response)
        logger.info("LLM skill extraction parse retry succeeded")
        return _finalize_skill_result(parsed_retry)

    except Exception as retry_error:
        retry_diagnostic = _bounded_live_failure_diagnostic(retry_error)
        retry_category = retry_diagnostic["category"]
        retry_stage = "execution"
        if "retry_response" in locals():
            retry_stage = "response"
            if retry_category == "unknown":
                retry_category = "schema_or_parse"
        if owner:
            logger.warning(
                "Failed to parse owner LLM skill output after retry | "
                "error_type=%s category=%s stage=%s",
                retry_diagnostic["error_type"],
                retry_category,
                retry_stage,
            )
        else:
            logger.warning(
                "Failed to parse LLM skill output after retry | "
                "error_type=%s category=%s stage=%s",
                retry_diagnostic["error_type"],
                retry_category,
                retry_stage,
            )
        return get_empty_skill_result(
            failure_category=retry_category,
            failure_stage=retry_stage,
        )
