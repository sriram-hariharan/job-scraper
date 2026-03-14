import os
import json
import time
import re
import random
from groq import Groq
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
from dotenv import load_dotenv
from threading import Lock

request_lock = Lock()
last_request_time = 0

load_dotenv()

MODEL = "llama-3.1-8b-instant"
BATCH_SIZE = 5                  # Fewer calls, more jobs per call
MIN_REQUEST_INTERVAL = 2.0      # More breathing room between requests
GROQ_CONCURRENCY_LIMIT = 1      # Match this to max_workers to avoid confusion

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in environment")

groq_semaphore = Semaphore(GROQ_CONCURRENCY_LIMIT)

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

    response = response.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(response)
    except:
        pass

    # matches = re.findall(r"\{[\s\S]*?\}", response)
    matches = re.search(r"\{[\s\S]*\}", response)

    for m in matches:
        try:
            parsed = json.loads(m)
            if "results" in parsed:
                return parsed
        except:
            continue

    return None


def build_batch_prompt(batch):

    blocks = []

    for i, job in enumerate(batch):

        intel = job.get("intelligence", {})

        skills = intel.get("skills", [])
        seniority = intel.get("seniority", "")

        flags = intel.get("ai_flags", {})
        ai_signals = [k for k, v in flags.items() if v]

        blocks.append(
            f"""
            JOB {i}

            Title: {job.get("title")}
            Company: {job.get("company")}

            AI signals:
            {", ".join(ai_signals)}

            Skills:
            {", ".join(skills)}

            Seniority:
            {seniority}
            """
        )

    return f"""
    {SYSTEM_PROMPT}

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

                completion = client.chat.completions.create(
                    model=MODEL,
                    temperature=0,
                    max_tokens=600,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                )

            response = completion.choices[0].message.content

        except Exception as e:

            if "429" in str(e):
                wait = retry_delay * (2 ** attempt)
                print(f"Rate limited. Waiting {wait}s")
                time.sleep(wait)
                continue

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
                for job in batch:
                    job["ai_fit"] = "PARSE_ERROR"
                return batch

        results = data.get("results", [])

        for item in results:

            idx = item.get("id")

            if idx is None or idx >= len(batch):
                continue

            ai_relevance = item.get("ai_relevance", 0)
            skill_match = item.get("skill_match", 0)
            seniority_match = item.get("seniority_match", 0)
            learning_opportunity = item.get("learning_opportunity", 0)
            overall_score = item.get("overall_score", 0)
            visa_signal = item.get("visa_sponsorship_signal", "unknown")

            reason = item.get("reason", "No explanation")

            batch[idx]["ai_relevance"] = ai_relevance
            batch[idx]["skill_match"] = skill_match
            batch[idx]["seniority_match"] = seniority_match
            batch[idx]["learning_opportunity"] = learning_opportunity
            batch[idx]["ai_fit_score"] = overall_score
            batch[idx]["visa_sponsorship_signal"] = visa_signal
            batch[idx]["ai_fit_reason"] = reason

            batch[idx]["ai_fit"] = (
                f"{overall_score}/10 | "
                f"AI {ai_relevance}, "
                f"Skill {skill_match}, "
                f"Seniority {seniority_match}, "
                f"Learning {learning_opportunity}"
            )

        return batch

    for job in batch:
        job["ai_fit"] = "RATE_LIMIT_FAIL"

    return batch


def chunk_jobs(jobs, size):

    for i in range(0, len(jobs), size):
        yield jobs[i:i + size]


def evaluate_jobs(jobs):

    results = []

    batches = list(chunk_jobs(jobs, BATCH_SIZE))

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
            results.extend(r)

    return results


# --------------------------------------------------------
# FUTURE VISA DETECTION SUPPORT
# --------------------------------------------------------

VISA_PATTERNS = [
    r"h-?1b",
    r"visa sponsorship",
    r"sponsor",
    r"work authorization",
    r"opt",
    r"cpt",
]


def detect_visa_sponsorship(text):

    if not text:
        return "unknown"

    text = text.lower()

    for p in VISA_PATTERNS:
        if re.search(p, text):
            return "possible"

    return "unknown"