import json
import os
from groq import Groq
from dotenv import load_dotenv
from tqdm import tqdm

from src.utils.logging import get_logger

load_dotenv()

logger = get_logger("ai_eval_filter")

MODEL = "llama-3.1-8b-instant"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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

════════════════════════════════════════
EXAMPLE
════════════════════════════════════════

Job description snippet:
"We need strong SQL and Python skills, experience with Airflow for pipeline orchestration,
stakeholder management, and 5+ years in fintech. A/B testing and causal inference experience
preferred. Must have a bachelor's degree."

Correct output:
{
  "required_skills": ["sql", "python", "airflow", "a/b testing", "causal inference"],
  "preferred_skills": []
}

Wrong output (DO NOT do this):
{
  "required_skills": ["sql", "python", "airflow", "pipeline orchestration",
                      "stakeholder management", "fintech", "5+ years"],
  "preferred_skills": ["a/b testing", "causal inference", "bachelor's degree"]
}

════════════════════════════════════════

Return ONLY valid JSON with no explanation:
{
  "required_skills": [],
  "preferred_skills": []
}
"""


def extract_json_from_response(response: str):
    """
    Extract JSON safely from LLM responses even if
    the model adds extra text before or after.
    """

    response = response.replace("```json", "").replace("```", "").strip()

    logger.info("LLM RAW RESPONSE | %s", response)

    start = response.find("{")
    end = response.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM response")

    json_str = response[start:end + 1]

    return json.loads(json_str)


def enrich_skills_with_llm(job_text):

    llm_bar.update(1)

    prompt = f"""
Extract REQUIRED and PREFERRED technical skills
from the following job description.

JOB DESCRIPTION:
{job_text[:4500]}
"""

    try:

        completion = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            max_tokens=500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )

        response = completion.choices[0].message.content

    except Exception as e:

        logger.warning(f"LLM skill extraction failed: {e}")

        return {
            "required_skills": [],
            "preferred_skills": []
        }

    try:

        parsed = extract_json_from_response(response)

        required = [s.lower().strip() for s in parsed.get("required_skills", [])]
        preferred = [s.lower().strip() for s in parsed.get("preferred_skills", [])]

        preferred = [s for s in preferred if s not in required]

        required = list(set(required))
        preferred = list(set(preferred))

        logger.info(    
            "LLM PARSED | required=%s | preferred=%s",
            required,
            preferred
        )

        return {
            "required_skills": required,
            "preferred_skills": preferred
        }

    except Exception as e:

        logger.warning(f"Failed to parse LLM skill output: {e}")

        return {
            "required_skills": [],
            "preferred_skills": []
        }