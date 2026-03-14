import os
import json
import time
import re
from groq import Groq
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

MODEL = "llama-3.1-8b-instant"
BATCH_SIZE = 5

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in environment")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You evaluate data, machine learning, and AI job opportunities.

For each job compute:

1. ai_relevance (0-10)
How strongly the role involves machine learning, AI, or advanced analytics.

2. skill_match (0-10)
How well the required technical skills align with modern data roles
(e.g. Python, SQL, ML frameworks, data engineering tools).

3. seniority_match (0-10)
How appropriate the role is for a mid-career data professional.

4. learning_opportunity (0-10)
How much opportunity the role provides to work on impactful
data, machine learning, or AI problems.

Compute:
overall_score = average of the four scores.

Return STRICT JSON only.

Example:

{
 "results":[
  {
   "id":0,
   "ai_relevance":6,
   "skill_match":8,
   "seniority_match":7,
   "learning_opportunity":7,
   "overall_score":7,
   "reason":"Strong data science role with ML exposure"
  }
 ]
}
"""

def extract_json_from_response(response, batch):

    # remove markdown fences
    
    response = response.replace("```json", "").replace("```", "").strip()

    # attempt direct parse first
    try:
        return json.loads(response)
    except:
        pass

    # fallback: find first JSON object using regex
    matches = re.findall(r"\{[\s\S]*?\}", response)

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
        frameworks = intel.get("frameworks", [])
        cloud = intel.get("cloud_tools", [])
        seniority = intel.get("seniority", "")
        years = intel.get("years_required", "")
        flags = intel.get("ai_flags", {})

        ai_signals = [k for k, v in flags.items() if v]

        blocks.append(
            f"""
            JOB {i}

            Title: {job.get("title")}
            Company: {job.get("company")}

            Extracted Signals

            AI signals:
            {", ".join(ai_signals)}

            Skills:
            {", ".join(skills)}

            Frameworks:
            {", ".join(frameworks)}

            Cloud:
            {", ".join(cloud)}

            Seniority:
            {seniority}

            Years required:
            {years}
            """
        )

    return SYSTEM_PROMPT + "\n".join(blocks)


def evaluate_batch(batch):

    prompt = build_batch_prompt(batch)

    max_retries = 6
    retry_delay = 2

    for attempt in range(max_retries):

        try:

            completion = client.chat.completions.create(
                model=MODEL,
                temperature=0,
                messages=[
                    {"role": "system", "content": "You evaluate AI/ML job opportunities and return strict JSON only."},
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

        data = extract_json_from_response(response, batch)

        # Retry if parsing failed
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

        # Parse successful
        for item in data.get("results", []):

            idx = item.get("id")

            if idx is None or idx >= len(batch):
                continue

            ai_relevance = item.get("ai_relevance", 0)
            skill_match = item.get("skill_match", 0)
            seniority_match = item.get("seniority_match", 0)
            learning_opportunity = item.get("learning_opportunity", 0)
            overall_score = item.get("overall_score", 0)
            reason = item.get("reason", "No explanation")

            batch[idx]["ai_relevance"] = ai_relevance
            batch[idx]["skill_match"] = skill_match
            batch[idx]["seniority_match"] = seniority_match
            batch[idx]["learning_opportunity"] = learning_opportunity
            batch[idx]["ai_fit_score"] = overall_score
            batch[idx]["ai_fit_reason"] = reason

            batch[idx]["ai_fit"] = (
                f"{overall_score}/10 | "
                f"AI {ai_relevance}, "
                f"Skill {skill_match}, "
                f"Seniority {seniority_match}, "
                f"Learning {learning_opportunity} | "
                f"{reason}"
            )

        return batch

    # Safety fallback
    for job in batch:
        job["ai_fit"] = "RATE_LIMIT_FAIL"

    return batch


def chunk_jobs(jobs, size):

    for i in range(0, len(jobs), size):
        yield jobs[i:i + size]


def evaluate_jobs(jobs):

    results = []
    batches = list(chunk_jobs(jobs, BATCH_SIZE))

    for batch in tqdm(batches, desc="AI batch evaluation"):

        evaluated = evaluate_batch(batch)
        results.extend(evaluated)

        # small throttle to avoid rate limits
        time.sleep(1)

    return results