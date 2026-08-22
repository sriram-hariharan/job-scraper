import os
import json
import time
import re
import random
import hashlib
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
from dotenv import load_dotenv
from threading import Lock
from src.ai.llm_client import run_chat_completion, get_default_model
from src.config.consts import NEGATIVE_VISA_PATTERNS, POSITIVE_VISA_PATTERNS
from src.storage.skill_corpus_store import (
    get_cached_job_evaluation,
    store_cached_job_evaluation,
)

request_lock = Lock()
last_request_time = 0

load_dotenv()

MODEL = get_default_model()
BATCH_SIZE = 5
JOB_FIT_TASK_CONTRACT_VERSION = "v1"
JOB_FIT_TEMPERATURE = 0
JOB_FIT_MAX_TOKENS = 600
MIN_REQUEST_INTERVAL = 2.0
GROQ_CONCURRENCY_LIMIT = 1

EVAL_MODE = os.getenv("EVAL_MODE", "cache_prefer_live").strip().lower()
VALID_EVAL_MODES = {"cache_prefer_live", "cache_only", "live_only"}

_PROVIDER_FAILURE_CATEGORIES = frozenset(
    {
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
)
_TRANSIENT_PROVIDER_FAILURE_CATEGORIES = frozenset(
    {"timeout", "connection", "provider_5xx"}
)
_JOB_FIT_RESULT_FIELDS = (
    "id",
    "ai_relevance",
    "skill_match",
    "seniority_match",
    "learning_opportunity",
    "overall_score",
    "visa_sponsorship_signal",
    "reason",
)
_MAX_RATE_LIMIT_ATTEMPTS = 5
_MAX_BOUNDED_RETRY_ATTEMPTS = 2
_RETRY_DELAY_SECONDS = 10
_PROGRESS_HEARTBEAT_INTERVAL_SECONDS = 20
_TERMINAL_BATCH_FAILURE_MARKERS = frozenset(
    {"LLM_CALL_FAIL", "PARSE_ERROR", "RATE_LIMIT_FAIL"}
)

groq_semaphore = Semaphore(GROQ_CONCURRENCY_LIMIT)

eval_cache_metrics_lock = Lock()

eval_cache_metrics = {
    "eval_cache_hits": 0,
    "eval_cache_misses": 0,
    "eval_cache_stores": 0,
    "eval_cache_only_skips": 0,
    "eval_live_failures": 0,
}

SYSTEM_PROMPT = """
You evaluate data, machine learning, and AI job opportunities.

For each job compute:

1. ai_relevance (0-10)
2. skill_match (0-10)
3. seniority_match (0-10)
4. learning_opportunity (0-10)

Also determine:
visa_sponsorship_signal (true/false/unknown)

Compute:
overall_score = average of the four scores.

Return STRICT JSON.

Example:

{
 "results":[
  {
   "id":0,
   "ai_relevance":7,
   "skill_match":8,
   "seniority_match":7,
   "learning_opportunity":7,
   "overall_score":7,
   "visa_sponsorship_signal":"unknown",
   "reason":"Strong ML role with modern stack"
  }
 ]
}
"""


def build_job_fit_production_task_contract_material():
    representative_batch = [
        {
            "title": "<job_title>",
            "company": "<company>",
            "intelligence": {
                "skills": {
                    "required": ["<required_skill>"],
                    "preferred": ["<preferred_skill>"],
                },
                "seniority": "<seniority>",
                "ai_flags": {"<ai_signal>": True},
            },
        }
    ]
    return {
        "task_contract_version": JOB_FIT_TASK_CONTRACT_VERSION,
        "prompt_contract": {
            "system": SYSTEM_PROMPT,
            "batch_user_template": build_batch_prompt(representative_batch),
        },
        "input_contract": {
            "batch_size": BATCH_SIZE,
            "job_fields": [
                "batch_index",
                "title",
                "company",
                "required_skills",
                "preferred_skills",
                "seniority",
                "enabled_ai_flags",
            ],
            "skill_merge": "required_then_unique_preferred",
        },
        "output_contract": {
            "type": "object",
            "required": ["results"],
            "requested_score_range": "0_to_10",
            "requested_overall_score": "average_of_four_scores",
            "result_fields": [
                "id",
                "ai_relevance",
                "skill_match",
                "seniority_match",
                "learning_opportunity",
                "overall_score",
                "visa_sponsorship_signal",
                "reason",
            ],
            "parser": "json_object_with_results_or_first_embedded_object",
        },
        "deterministic_transformation_contract": {
            "score_projection": "provider_values_projected_without_recalculation_or_clamping",
            "missing_score_default": 0,
            "visa_default": "unknown",
            "reason_default": "No explanation",
            "projection": "apply_evaluation_to_job_v1",
        },
        "task_parameters": {
            "temperature": JOB_FIT_TEMPERATURE,
            "max_tokens": JOB_FIT_MAX_TOKENS,
        },
    }


def extract_json_from_response(response):

    if not response:
        return None

    response = response.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(response)
        if isinstance(parsed, dict) and "results" in parsed:
            return parsed
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", response)

    if match:
        try:
            parsed = json.loads(match.group())
            if "results" in parsed:
                return parsed
        except Exception:
            pass

    return None

def reset_eval_cache_metrics():
    with eval_cache_metrics_lock:
        for key in eval_cache_metrics:
            eval_cache_metrics[key] = 0


def get_eval_cache_metrics():
    with eval_cache_metrics_lock:
        return dict(eval_cache_metrics)


def increment_eval_cache_metric(metric_name: str):
    with eval_cache_metrics_lock:
        if metric_name in eval_cache_metrics:
            eval_cache_metrics[metric_name] += 1


def build_job_eval_cache_key(job):

    intel = job.get("intelligence", {}) or {}
    skills = intel.get("skills", {}) or {}

    required_skills = sorted(skills.get("required", []) or [])
    preferred_skills = sorted(skills.get("preferred", []) or [])
    seniority = intel.get("seniority", "") or ""

    flags = intel.get("ai_flags", {}) or {}
    enabled_ai_flags = sorted([k for k, v in flags.items() if v])

    payload = {
        "title": (job.get("title") or "").strip(),
        "company": (job.get("company") or "").strip(),
        "skills_required": required_skills,
        "skills_preferred": preferred_skills,
        "seniority": seniority.strip(),
        "ai_flags": enabled_ai_flags,
    }

    normalized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def apply_evaluation_to_job(job, evaluation_data):

    ai_relevance = evaluation_data.get("ai_relevance", 0)
    skill_match = evaluation_data.get("skill_match", 0)
    seniority_match = evaluation_data.get("seniority_match", 0)
    learning_opportunity = evaluation_data.get("learning_opportunity", 0)
    overall_score = evaluation_data.get("overall_score", 0)
    visa_signal = evaluation_data.get("visa_sponsorship_signal", "unknown")
    reason = evaluation_data.get("reason", "No explanation")

    job["ai_relevance"] = ai_relevance
    job["skill_match"] = skill_match
    job["seniority_match"] = seniority_match
    job["learning_opportunity"] = learning_opportunity
    job["ai_fit_score"] = overall_score
    job["visa_sponsorship_signal"] = visa_signal
    job["ai_fit_reason"] = reason

    job["ai_fit"] = (
        f"{overall_score}/10 | "
        f"AI {ai_relevance}, "
        f"Skill {skill_match}, "
        f"Seniority {seniority_match}, "
        f"Learning {learning_opportunity}"
    )

def mark_job_eval_skipped(job):

    job["ai_relevance"] = 0
    job["skill_match"] = 0
    job["seniority_match"] = 0
    job["learning_opportunity"] = 0
    job["ai_fit_score"] = 0
    job["visa_sponsorship_signal"] = "unknown"
    job["ai_fit_reason"] = "Skipped live evaluation (cache_only mode)"
    job["ai_fit"] = "EVAL_SKIPPED_CACHE_ONLY"

def build_batch_prompt(batch):

    blocks = []

    for i, job in enumerate(batch):

        intel = job.get("intelligence", {}) or {}

        skills = intel.get("skills", {}) or {}
        required_skills = skills.get("required", []) or []
        preferred_skills = skills.get("preferred", []) or []
        combined_skills = required_skills + [s for s in preferred_skills if s not in required_skills]

        seniority = intel.get("seniority", "")

        flags = intel.get("ai_flags", {}) or {}
        ai_signals = [k for k, v in flags.items() if v]

        blocks.append(
            f"""
JOB {i}

Title: {job.get("title")}
Company: {job.get("company")}

AI signals:
{", ".join(ai_signals) if ai_signals else "none"}

Skills:
{", ".join(combined_skills) if combined_skills else "none"}

Seniority:
{seniority if seniority else "unknown"}
"""
        )

    return f"""
Evaluate the following jobs and return STRICT JSON.

{"".join(blocks)}
"""


def resolve_effective_user_provider_route(owner_user_id, workload_id):
    from importlib import import_module

    routing_service = import_module(
        "src.app.provider_model_" "routing_service"
    )
    return routing_service.resolve_effective_user_provider_route(
        owner_user_id,
        workload_id,
    )


def run_user_chat_completion_with_metadata(**kwargs):
    from src.ai.user_provider_runtime import (
        run_user_chat_completion_with_metadata as execute,
    )

    return execute(**kwargs)


def _is_rate_limit_error(error):
    message = str(error).lower()
    return "429" in message or "category=rate_limit" in message


def _provider_failure_category(error):
    for attribute in ("error_category", "category"):
        category = str(getattr(error, attribute, "") or "").strip().lower()
        if category in _PROVIDER_FAILURE_CATEGORIES:
            return category

    match = re.search(
        r"category=([a-z0-9_]+)",
        str(error or "").lower(),
    )
    if match and match.group(1) in _PROVIDER_FAILURE_CATEGORIES:
        return match.group(1)
    return "unknown"


def _emit_progress(progress_callback, event, **metadata):
    if progress_callback is None:
        return
    payload = {"event": str(event or "")}
    payload.update(metadata)
    try:
        progress_callback(dict(payload))
    except BaseException:
        return


def _sleep_with_progress_heartbeat(
    delay_seconds,
    progress_callback,
    retry_metadata,
):
    if (
        progress_callback is None
        or delay_seconds <= _PROGRESS_HEARTBEAT_INTERVAL_SECONDS
    ):
        time.sleep(delay_seconds)
        return

    remaining_seconds = delay_seconds
    while remaining_seconds > 0:
        sleep_seconds = min(
            _PROGRESS_HEARTBEAT_INTERVAL_SECONDS,
            remaining_seconds,
        )
        time.sleep(sleep_seconds)
        remaining_seconds -= sleep_seconds
        if remaining_seconds > 0:
            _emit_progress(
                progress_callback,
                "retry",
                **retry_metadata,
                heartbeat=True,
                remaining_delay_seconds=remaining_seconds,
            )


def _validate_complete_batch_response(data, expected_count):
    if not isinstance(data, dict):
        return None
    results = data.get("results")
    if not isinstance(results, list) or len(results) != expected_count:
        return None

    expected_ids = set(range(expected_count))
    observed_ids = set()
    for item in results:
        if not isinstance(item, dict):
            return None
        if not all(field in item for field in _JOB_FIT_RESULT_FIELDS):
            return None
        result_id = item["id"]
        if type(result_id) is not int:
            return None
        if result_id not in expected_ids or result_id in observed_ids:
            return None
        observed_ids.add(result_id)

    if observed_ids != expected_ids:
        return None
    return results


def _mark_terminal_batch_failure(batch, marker):
    increment_eval_cache_metric("eval_live_failures")
    for job in batch:
        job["ai_fit"] = marker
    return batch


def evaluate_batch(
    batch,
    owner_user_id="",
    routed_provider="",
    routed_model="",
    progress_callback=None,
    batch_ordinal=0,
    total_batches=0,
):

    prompt = build_batch_prompt(batch)

    attempt = 0
    attempt_limit = _MAX_RATE_LIMIT_ATTEMPTS

    while attempt < attempt_limit:
        current_attempt = attempt
        attempt += 1

        try:

            with groq_semaphore:

                global last_request_time

                with request_lock:
                    now = time.time()
                    elapsed = now - last_request_time

                    if elapsed < MIN_REQUEST_INTERVAL:
                        time.sleep(MIN_REQUEST_INTERVAL - elapsed)

                    last_request_time = time.time()

                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
                if owner_user_id:
                    result = run_user_chat_completion_with_metadata(
                        owner_user_id=owner_user_id,
                        provider=routed_provider,
                        model=routed_model,
                        temperature=JOB_FIT_TEMPERATURE,
                        max_tokens=JOB_FIT_MAX_TOKENS,
                        messages=messages,
                    )
                    response = result["content"]
                else:
                    response = run_chat_completion(
                        model=MODEL,
                        temperature=JOB_FIT_TEMPERATURE,
                        max_tokens=JOB_FIT_MAX_TOKENS,
                        messages=messages,
                    )

        except Exception as e:
            category = _provider_failure_category(e)
            if (
                not owner_user_id
                and category == "unknown"
                and _is_rate_limit_error(e)
            ):
                category = "rate_limit"

            if category == "rate_limit":
                if attempt < attempt_limit:
                    wait = _RETRY_DELAY_SECONDS * (2 ** current_attempt)
                    print(f"Rate limited. Waiting {wait}s")
                    retry_metadata = {
                        "category": category,
                        "attempt": attempt + 1,
                        "maximum_attempts": attempt_limit,
                        "delay_seconds": wait,
                        "batch_ordinal": batch_ordinal,
                        "total_batches": total_batches,
                    }
                    _emit_progress(
                        progress_callback,
                        "retry",
                        **retry_metadata,
                    )
                    _sleep_with_progress_heartbeat(
                        wait,
                        progress_callback,
                        retry_metadata,
                    )
                    continue
                return _mark_terminal_batch_failure(batch, "RATE_LIMIT_FAIL")

            if category in _TRANSIENT_PROVIDER_FAILURE_CATEGORIES:
                attempt_limit = min(
                    attempt_limit,
                    _MAX_BOUNDED_RETRY_ATTEMPTS,
                )
                if attempt < attempt_limit:
                    print(
                        "AI evaluation transient provider failure; "
                        f"retrying (category={category})"
                    )
                    retry_metadata = {
                        "category": category,
                        "attempt": attempt + 1,
                        "maximum_attempts": attempt_limit,
                        "delay_seconds": _RETRY_DELAY_SECONDS,
                        "batch_ordinal": batch_ordinal,
                        "total_batches": total_batches,
                    }
                    _emit_progress(
                        progress_callback,
                        "retry",
                        **retry_metadata,
                    )
                    _sleep_with_progress_heartbeat(
                        _RETRY_DELAY_SECONDS,
                        progress_callback,
                        retry_metadata,
                    )
                    continue

            if owner_user_id:
                print(
                    "AI evaluation failed for owner route "
                    f"(category={category})"
                )
            else:
                print(f"AI evaluation failed (category={category})")
            return _mark_terminal_batch_failure(batch, "LLM_CALL_FAIL")

        data = extract_json_from_response(response)
        results = _validate_complete_batch_response(data, len(batch))

        if results is None:
            attempt_limit = min(
                attempt_limit,
                _MAX_BOUNDED_RETRY_ATTEMPTS,
            )
            if attempt < attempt_limit:
                print("AI evaluation response invalid; retrying once")
                _emit_progress(
                    progress_callback,
                    "retry",
                    category="malformed_response",
                    attempt=attempt + 1,
                    maximum_attempts=attempt_limit,
                    delay_seconds=0,
                    batch_ordinal=batch_ordinal,
                    total_batches=total_batches,
                )
                continue
            return _mark_terminal_batch_failure(batch, "PARSE_ERROR")

        for item in results:

            idx = item["id"]

            evaluation_data = {
                "ai_relevance": item["ai_relevance"],
                "skill_match": item["skill_match"],
                "seniority_match": item["seniority_match"],
                "learning_opportunity": item["learning_opportunity"],
                "overall_score": item["overall_score"],
                "visa_sponsorship_signal": item["visa_sponsorship_signal"],
                "reason": item["reason"],
            }

            apply_evaluation_to_job(batch[idx], evaluation_data)

            cache_key = batch[idx].get("_eval_cache_key")
            eval_mode = batch[idx].get("_eval_mode", "cache_prefer_live")

            if cache_key and eval_mode != "live_only":
                store_cached_job_evaluation(
                    cache_key=cache_key,
                    model=routed_model if owner_user_id else MODEL,
                    evaluation=evaluation_data,
                )
                increment_eval_cache_metric("eval_cache_stores")

        return batch

def chunk_jobs(jobs, size):

    for i in range(0, len(jobs), size):
        yield jobs[i:i + size]


def evaluate_jobs(jobs, owner_user_id="", progress_callback=None):

    reset_eval_cache_metrics()

    if EVAL_MODE not in VALID_EVAL_MODES:
        mode = "cache_prefer_live"
    else:
        mode = EVAL_MODE

    indexed_jobs = []

    for i, job in enumerate(jobs):
        job["_eval_original_index"] = i
        cache_key = build_job_eval_cache_key(job)
        job["_eval_cache_key"] = cache_key
        job["_eval_mode"] = mode

        if mode != "live_only":
            cached = get_cached_job_evaluation(cache_key)

            if cached is not None:
                increment_eval_cache_metric("eval_cache_hits")
                apply_evaluation_to_job(job, cached)
            else:
                increment_eval_cache_metric("eval_cache_misses")

                if mode == "cache_only":
                    increment_eval_cache_metric("eval_cache_only_skips")
                    mark_job_eval_skipped(job)
        else:
            increment_eval_cache_metric("eval_cache_misses")

        indexed_jobs.append(job)

    uncached_jobs = [
        job for job in indexed_jobs
        if "ai_fit_score" not in job
    ]

    progress_state = None
    if progress_callback is not None:
        cache_metrics = get_eval_cache_metrics()
        uncached_job_count = len(uncached_jobs)
        total_batch_count = (
            (uncached_job_count + BATCH_SIZE - 1) // BATCH_SIZE
            if uncached_job_count
            else 0
        )
        progress_state = {
            "total_jobs": len(indexed_jobs),
            "cache_hits": cache_metrics["eval_cache_hits"],
            "cache_misses": cache_metrics["eval_cache_misses"],
            "cache_only_skips": cache_metrics["eval_cache_only_skips"],
            "uncached_jobs": uncached_job_count,
            "total_batches": total_batch_count,
            "completed_batches": 0,
            "failed_batches": 0,
            "processed_live_jobs": 0,
            "failed_live_jobs": 0,
        }
        _emit_progress(progress_callback, "prepared", **progress_state)

    live_results = []

    explicit_owner = str(owner_user_id or "").strip()
    owner = explicit_owner or str(
        os.environ.get("JOB_STACK_OWNER_USER_ID", "") or ""
    ).strip()
    routed_provider = ""
    routed_model = MODEL

    if uncached_jobs and owner:
        try:
            route = resolve_effective_user_provider_route(
                owner,
                "job_fit_evaluation",
            )
            routed_provider = str(route.get("provider") or "").strip()
            routed_model = str(route.get("model") or "").strip()
            if not routed_provider or not routed_model:
                raise ValueError("invalid effective route")
        except (Exception, SystemExit):
            increment_eval_cache_metric("eval_live_failures")
            for job in uncached_jobs:
                job["ai_fit"] = "LLM_CALL_FAIL"
            if progress_state is not None:
                progress_state["failed_live_jobs"] = len(uncached_jobs)
            uncached_jobs = []

    if uncached_jobs:
        batches = list(chunk_jobs(uncached_jobs, BATCH_SIZE))
        random.shuffle(batches)

        with ThreadPoolExecutor(max_workers=1) as executor:

            futures = {
                executor.submit(
                    evaluate_batch,
                    batch,
                    owner,
                    routed_provider,
                    routed_model,
                    progress_callback,
                    i + 1,
                    len(batches),
                ): i
                for i, batch in enumerate(batches)
            }

            batch_results = [None] * len(batches)

            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="AI batch evaluation"
            ):
                idx = futures[future]
                completed_batch = future.result()
                batch_results[idx] = completed_batch
                if progress_state is not None:
                    failed_job_count = sum(
                        1
                        for job in completed_batch
                        if job.get("ai_fit")
                        in _TERMINAL_BATCH_FAILURE_MARKERS
                    )
                    progress_state["completed_batches"] += 1
                    progress_state["processed_live_jobs"] += (
                        len(completed_batch) - failed_job_count
                    )
                    progress_state["failed_live_jobs"] += failed_job_count
                    if failed_job_count:
                        progress_state["failed_batches"] += 1
                    _emit_progress(
                        progress_callback,
                        "batch_completed",
                        **progress_state,
                    )

            for r in batch_results:
                live_results.extend(r)

    all_results = [
        job for job in indexed_jobs
        if "ai_fit_score" in job or job.get("ai_fit") in {
            "LLM_CALL_FAIL",
            "PARSE_ERROR",
            "RATE_LIMIT_FAIL",
            "EVAL_SKIPPED_CACHE_ONLY",
        }
    ]

    all_results.sort(key=lambda job: job.get("_eval_original_index", 0))

    for job in all_results:
        job.pop("_eval_original_index", None)
        job.pop("_eval_cache_key", None)
        job.pop("_eval_mode", None)

    if progress_state is not None:
        _emit_progress(progress_callback, "completed", **progress_state)

    return all_results


# --------------------------------------------------------
# FUTURE VISA DETECTION SUPPORT
# --------------------------------------------------------

def detect_visa_sponsorship(text):

    if not text:
        return "unknown"

    text = text.lower()

    for p in NEGATIVE_VISA_PATTERNS:
        if re.search(p, text):
            return "no"

    for p in POSITIVE_VISA_PATTERNS:
        if re.search(p, text):
            return "possible"

    return "unknown"
