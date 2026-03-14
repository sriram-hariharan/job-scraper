import json
import os
import re
from groq import Groq
from dotenv import load_dotenv
from tqdm import tqdm

from src.utils.logging import get_logger
from src.config.consts import SKILL_STOPWORDS

load_dotenv()

logger = get_logger("ai_eval_filter")

MODEL = "llama-3.1-8b-instant"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Progress bar for LLM calls
llm_bar = tqdm(desc="LLM skill extraction", unit="job")


SYSTEM_PROMPT = """
You extract technical skills from job descriptions.

Return ONLY actual technical skills.

STRICT RULES:

Only include:
- programming languages
- ML/AI frameworks
- data engineering tools
- databases
- cloud platforms
- analytics tools
- ML techniques

NEVER include:
- verbs (build, create, obtain, maintain, raise)
- generic nouns (business, domain, industry, entertainment)
- soft skills
- responsibilities
- sentences
- company names

Skills must be concrete technologies.

GOOD examples:
python
pytorch
tensorflow
sql
spark
dbt
snowflake
aws
pandas
numpy
langchain
huggingface

BAD examples:
build models
obtain insights
entertainment industry
business strategy

Return JSON ONLY in this format:

{
  "required_skills": [],
  "preferred_skills": []
}
"""


def clean_llm_skills(skills):

    cleaned = []

    for skill in skills:

        if not skill:
            continue

        skill = skill.lower().strip()

        # remove punctuation
        skill = re.sub(r"[^\w\s\+\#\.]", "", skill)

        if len(skill) < 2:
            continue

        if skill in SKILL_STOPWORDS:
            continue

        cleaned.append(skill)

    return list(set(cleaned))

def enrich_skills_with_llm(job_text):

    llm_bar.update(1)

    prompt = f"""
Extract technical skills from the following job description.

JOB DESCRIPTION:
{job_text[:6000]}
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

        response = response.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(response)

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