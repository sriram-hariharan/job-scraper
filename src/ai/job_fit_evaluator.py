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
MIN_REQUEST_INTERVAL = 2.0
GROQ_CONCURRENCY_LIMIT = 1

EVAL_MODE = os.getenv("EVAL_MODE", "cache_prefer_live").strip().lower()
VALID_EVAL_MODES = {"cache_prefer_live", "cache_only", "live_only"}

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


def evaluate_batch(batch):

    prompt = build_batch_prompt(batch)

    max_retries = 5
    retry_delay = 10

    for attempt in range(max_retries):

        try:

            with groq_semaphore:

                global last_request_time

                with request_lock:
                    now = time.time()
                    elapsed = now - last_request_time

                    if elapsed < MIN_REQUEST_INTERVAL:
                        time.sleep(MIN_REQUEST_INTERVAL - elapsed)

                    last_request_time = time.time()

                response = run_chat_completion(
                    model=MODEL,
                    temperature=0,
                    max_tokens=600,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                )

        except Exception as e:

            if "429" in str(e):
                wait = retry_delay * (2 ** attempt)
                print(f"Rate limited. Waiting {wait}s")
                time.sleep(wait)
                continue

            increment_eval_cache_metric("eval_live_failures")

            for job in batch:
                job["ai_fit"] = "LLM_CALL_FAIL"

            return batch

        data = extract_json_from_response(response)

        if not data:

            if attempt < max_retries - 1:
                wait = retry_delay * (2 ** attempt)
                print(f"Parse failed. Retrying in {wait}s")
                time.sleep(wait)
                continue
            else:
                increment_eval_cache_metric("eval_live_failures")

                for job in batch:
                    job["ai_fit"] = "PARSE_ERROR"
                return batch

        results = data.get("results", [])

        for item in results:

            idx = item.get("id")

            if idx is None or idx >= len(batch):
                continue

            evaluation_data = {
                "ai_relevance": item.get("ai_relevance", 0),
                "skill_match": item.get("skill_match", 0),
                "seniority_match": item.get("seniority_match", 0),
                "learning_opportunity": item.get("learning_opportunity", 0),
                "overall_score": item.get("overall_score", 0),
                "visa_sponsorship_signal": item.get("visa_sponsorship_signal", "unknown"),
                "reason": item.get("reason", "No explanation"),
            }

            apply_evaluation_to_job(batch[idx], evaluation_data)

            cache_key = batch[idx].get("_eval_cache_key")
            eval_mode = batch[idx].get("_eval_mode", "cache_prefer_live")

            if cache_key and eval_mode != "live_only":
                store_cached_job_evaluation(
                    cache_key=cache_key,
                    model=MODEL,
                    evaluation=evaluation_data,
                )
                increment_eval_cache_metric("eval_cache_stores")

        return batch

    increment_eval_cache_metric("eval_live_failures")

    for job in batch:
        job["ai_fit"] = "RATE_LIMIT_FAIL"

    return batch

def chunk_jobs(jobs, size):

    for i in range(0, len(jobs), size):
        yield jobs[i:i + size]


def evaluate_jobs(jobs):

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

    live_results = []

    if uncached_jobs:
        batches = list(chunk_jobs(uncached_jobs, BATCH_SIZE))
        random.shuffle(batches)

        with ThreadPoolExecutor(max_workers=1) as executor:

            futures = {
                executor.submit(evaluate_batch, batch): i
                for i, batch in enumerate(batches)
            }

            batch_results = [None] * len(batches)

            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="AI batch evaluation"
            ):
                idx = futures[future]
                batch_results[idx] = future.result()

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