import re
from typing import List, Dict, Any

SKILL_PATTERNS = {
    "python": r"\bpython\b",
    "pytorch": r"\bpytorch\b",
    "tensorflow": r"\btensorflow\b",
    "sql": r"\bsql\b",
    "spark": r"\bspark\b",
    "aws": r"\baws\b",
    "gcp": r"\bgcp\b",
    "azure": r"\bazure\b",
    "docker": r"\bdocker\b",
    "kubernetes": r"\bkubernetes\b",
    "llm": r"\b(llm|large language model)\b",
    "transformers": r"\btransformer(s)?\b",
    "pandas": r"\bpandas\b",
    "numpy": r"\bnumpy\b",
    "scikit-learn": r"\bscikit[- ]learn\b",
}

SENIORITY_PATTERNS = {
    "intern": r"\bintern\b",
    "junior": r"\bjunior\b",
    "mid": r"\bmid[- ]level\b",
    "senior": r"\bsenior\b",
    "staff": r"\bstaff\b",
    "principal": r"\bprincipal\b",
    "lead": r"\blead\b",
}


def extract_skills(text: str) -> List[str]:

    if not text:
        return []

    text = text.lower()

    skills = []

    for skill, pattern in SKILL_PATTERNS.items():
        if re.search(pattern, text):
            skills.append(skill)

    return skills


def extract_seniority(title: str, description: str) -> str:

    combined = f"{title} {description}".lower()

    for level, pattern in SENIORITY_PATTERNS.items():
        if re.search(pattern, combined):
            return level

    return "unknown"


def detect_remote(description: str) -> bool:

    if not description:
        return False

    description = description.lower()

    if "remote" in description:
        return True

    if "work from home" in description:
        return True

    return False


def enrich_job_intelligence(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    for job in jobs:

        desc = job.get("description", "")
        title = job.get("title", "")

        job["skills"] = extract_skills(desc)
        job["seniority"] = extract_seniority(title, desc)
        job["remote"] = detect_remote(desc)

    return jobs