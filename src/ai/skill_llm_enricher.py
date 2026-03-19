import hashlib
import json
import os
import re

from dotenv import load_dotenv
from tqdm import tqdm
from threading import Lock

from src.ai.llm_client import run_chat_completion, get_default_model
from src.utils.skill_normalizer import normalize_extracted_skills

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

MODEL = get_default_model()
SKILL_EXTRACTION_MODE = os.getenv("SKILL_EXTRACTION_MODE", "cache_prefer_live").strip().lower()
VALID_EXTRACTION_MODES = {"cache_prefer_live", "cache_only", "live_only"}

SKILL_EXTRACTION_PROMPT_VERSION = "v6_postfilter_cleanup"

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
    job_norm = _normalize_for_match(job_text)

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
        pattern = rf"(?<![a-z0-9]){re.escape(candidate)}(?![a-z0-9])"
        for match in re.finditer(pattern, job_norm):
            start = max(0, match.start() - window_chars)
            end = min(len(job_norm), match.end() + window_chars)
            context = job_norm[start:end]

            # Inline preferred language wins for that specific occurrence.
            if _inline_preferred_override(context):
                saw_preferred = True
                continue

            # Otherwise only use explicit section spans.
            for span_start, span_end, bucket in spans:
                if span_start <= match.start() < span_end:
                    if bucket == "required":
                        saw_required = True
                    elif bucket == "preferred":
                        saw_preferred = True
                    break

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


def get_empty_skill_result():
    return {
        "required_skills": [],
        "preferred_skills": []
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
    head_chars: int = 2500,
    tail_chars: int = 1800,
    window_chars: int = 900,
    max_keyword_windows: int = 10,
) -> str:
    text = (job_text or "").strip()
    if not text:
        return ""

    if len(text) <= 7000:
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


def enrich_skills_with_llm(job_text):

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
            return cached

        increment_skill_cache_metric("cache_misses")
        logger.info("LLM skill cache miss")

        if mode == "cache_only":
            increment_skill_cache_metric("cache_only_skips")
            logger.info("LLM live extraction skipped (cache_only mode)")
            return get_empty_skill_result()

    elif mode == "live_only":
        logger.info("LLM cache bypassed (live_only mode)")

    llm_bar.update(1)

    extraction_text = _build_skill_extraction_text(job_text)

    prompt = f"""
    Extract REQUIRED and PREFERRED technical skills
    from the following job description.

    JOB DESCRIPTION:
    {extraction_text}
    """

    try:
        response = run_chat_completion(
            model=MODEL,
            temperature=0,
            max_tokens=500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
        )

    except Exception as e:
        increment_skill_cache_metric("live_failures")
        logger.warning(f"LLM skill extraction failed: {e}")
        return get_empty_skill_result()

    def _finalize_skill_result(parsed_obj):
        required = _filter_skill_candidates(parsed_obj.get("required_skills", []), job_text)
        preferred = _filter_skill_candidates(parsed_obj.get("preferred_skills", []), job_text)

        preferred = [s for s in preferred if s not in required]
        required, preferred = _reassign_skills_by_context(required, preferred, job_text)
        required, preferred = _drop_shadowed_generic_skills(required, preferred)

        result = {
            "required_skills": required,
            "preferred_skills": preferred
        }

        if mode != "live_only":
            store_cached_llm_skills(
                cache_key=cache_key,
                model=MODEL,
                required_skills=required,
                preferred_skills=preferred,
            )
            increment_skill_cache_metric("cache_stores")
            logger.info("LLM skill cache stored")

        return result

    try:
        parsed = extract_json_from_response(response)
        return _finalize_skill_result(parsed)

    except Exception as json_error:
        logger.warning(
            "Failed JSON parse on first attempt: %s | response_preview=%s",
            json_error,
            _response_preview(response),
        )

    try:
        parsed_sectioned = _parse_sectioned_skill_response(response)
        logger.info("LLM skill extraction section-parser succeeded on first attempt")
        return _finalize_skill_result(parsed_sectioned)

    except Exception as section_error:
        logger.warning(
            "Failed section-parser on first attempt: %s | response_preview=%s",
            section_error,
            _response_preview(response),
        )

    retry_prompt = prompt + "\n\nReturn ONLY valid JSON. No prose. No markdown. No explanation."

    try:
        retry_response = run_chat_completion(
            model=MODEL,
            temperature=0,
            max_tokens=500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": retry_prompt}
            ],
        )

        parsed_retry = extract_json_from_response(retry_response)
        logger.info("LLM skill extraction parse retry succeeded")
        return _finalize_skill_result(parsed_retry)

    except Exception as retry_error:
        logger.warning(
            "Failed to parse LLM skill output after retry: %s | retry_response_preview=%s",
            retry_error,
            _response_preview(retry_response if 'retry_response' in locals() else ""),
        )
        return get_empty_skill_result()