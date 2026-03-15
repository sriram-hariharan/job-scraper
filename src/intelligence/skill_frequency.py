from collections import Counter
from typing import List, Dict, Any


def collect_skill_frequencies(jobs: List[Dict[str, Any]]) -> Counter:
    counter = Counter()

    for job in jobs:
        intel = job.get("intelligence", {}) or {}
        skills = intel.get("skills", {}) or {}

        required = skills.get("required", []) or []
        preferred = skills.get("preferred", []) or []

        for skill in required:
            counter[skill] += 1

        for skill in preferred:
            counter[skill] += 1

    return counter


def top_skills(jobs: List[Dict[str, Any]], top_n: int = 50):
    counter = collect_skill_frequencies(jobs)
    return counter.most_common(top_n)