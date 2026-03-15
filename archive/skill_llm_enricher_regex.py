import json
import os
import re
from groq import Groq
from dotenv import load_dotenv
from tqdm import tqdm

from src.utils.logging import get_logger
from src.config.consts import (
    SKILL_STOPWORDS,
    DOMAIN_STOPWORDS,
    INVALID_SKILL_WORDS,
    TECH_CATEGORY_EXAMPLES,
    NORMALIZATION_MAP,
    TRUSTED_CORE_SKILLS,
    TECH_KEYWORDS,
    GENERIC_SKILL_PHRASES
)

load_dotenv()

logger = get_logger("ai_eval_filter")

MODEL = "llama-3.1-8b-instant"

TECH_SIGNAL = set(TRUSTED_CORE_SKILLS) | set(TECH_KEYWORDS)

for skills in TECH_CATEGORY_EXAMPLES.values():
    TECH_SIGNAL.update(skills)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Progress bar for LLM calls
llm_bar = tqdm(desc="LLM skill extraction", unit="job")


def build_tech_examples_text():
    """
    Convert TECH_CATEGORY_EXAMPLES dict into readable text
    for the system prompt.
    """

    lines = []

    for category, skills in TECH_CATEGORY_EXAMPLES.items():

        label = category.replace("_", " ").title()
        skills_str = ", ".join(skills)

        lines.append(f"{label}: {skills_str}")

    return "\n".join(lines)


TECH_EXAMPLES_TEXT = build_tech_examples_text()


SYSTEM_PROMPT = f"""
You analyze job descriptions and extract ONLY valid technical skills.

Every candidate phrase must belong to ONE of the following categories.

TECHNOLOGY
Concrete tools, languages, frameworks, libraries, infrastructure or platforms.

Examples:
python, sql, spark, pytorch, tensorflow, airflow, dbt, kafka,
snowflake, databricks, kubernetes, docker, terraform, tableau

ML_CONCEPT
Machine learning or AI concepts used in model development.

Examples:
machine learning, deep learning, computer vision, NLP,
transformers, embeddings, vector databases, rag

METHOD
Statistical, data science, experimentation, or modeling methods.

Examples:
a/b testing
causal inference
bayesian inference
statistical modeling
forecasting
hypothesis testing
experimental design
time series analysis

DOMAIN_KNOWLEDGE
Knowledge about a business or scientific domain.

Examples:
clinical records, genomics, oncology, marketing analytics,
financial modeling, biomedical literature

RESPONSIBILITY
Actions, behaviors, or descriptions of work.

Examples:
leveraging data platforms
building pipelines
pragmatic mindset
develop scalable systems

You must return ONLY items that belong to:

- TECHNOLOGY
- ML_CONCEPT
- METHOD

Discard anything that belongs to DOMAIN_KNOWLEDGE or RESPONSIBILITY.

Technology examples (not exhaustive):

{TECH_EXAMPLES_TEXT}

Return ONLY JSON:

{{
  "required_skills": [],
  "preferred_skills": []
}}

Rules:
- include only technologies, ML concepts, or data science / statistical methods
- methods such as a/b testing, causal inference, forecasting, statistical modeling are valid skills
- do not include adjectives, verbs, or domain knowledge
- do not include explanations
- do not repeat the same skill in both required_skills and preferred_skills.
"""

def clean_llm_skills(skills):

    cleaned = []

    for skill in skills:

        if not skill:
            continue

        skill = skill.lower().strip()

        # remove punctuation artifacts
        skill = re.sub(r"[^\w\s\+\#\.\-]", "", skill)

        if len(skill) < 2:
            continue

        if skill in SKILL_STOPWORDS:
            continue

        if any(w in skill for w in DOMAIN_STOPWORDS):
            continue

        if skill in INVALID_SKILL_WORDS:
            continue

        # reject phrases longer than 4 words
        if len(skill.split()) > 4:
            continue

        # must contain at least one technical signal
        skill_tokens = set(skill.split())

        if not (
            skill in TECH_SIGNAL
            or skill_tokens & TECH_SIGNAL
        ):
            continue
        
        if skill in GENERIC_SKILL_PHRASES:
            continue

        skill = NORMALIZATION_MAP.get(skill, skill)
        cleaned.append(skill)
    
    return list(set(cleaned))

def process_result(response):

    response = response.replace("```json", "").replace("```", "").strip()

    # --- robust JSON extraction ---
    start = response.find("{")
    end = response.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM response")

    json_str = response[start:end + 1]

    parsed = json.loads(json_str)

    return parsed
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

        parsed = process_result(response)

        required = clean_llm_skills(parsed.get("required_skills", []))
        preferred = clean_llm_skills(parsed.get("preferred_skills", []))

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