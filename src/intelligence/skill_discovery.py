from collections import Counter
import re

from src.storage.skill_db import (
    init_skill_db,
    get_existing_skills,
    insert_or_update_skill
)

from src.config.consts import NORMALIZATION_MAP

MIN_OCCURRENCES = 2


def normalize_skill(skill: str) -> str:

    if not skill:
        return ""

    skill = skill.lower().strip()

    # normalize whitespace
    skill = re.sub(r"\s+", " ", skill)

    # canonical map
    skill = NORMALIZATION_MAP.get(skill, skill)

    # singular/plural normalization
    if skill.endswith(" databases"):
        skill = skill.replace(" databases", " database")

    if skill.endswith(" embeddings"):
        skill = skill.replace(" embeddings", " embedding")

    return skill


def discover_new_skills(jobs):

    init_skill_db()

    counter = Counter()

    for job in jobs:

        intel = job.get("intelligence", {}) or {}

        skills = intel.get("skills", {}) or {}

        required = skills.get("required", []) or []
        preferred = skills.get("preferred", []) or []

        for skill in required + preferred:

            skill = normalize_skill(skill)

            if not skill:
                continue

            counter[skill] += 1

    existing = get_existing_skills()

    new_skills = []

    for skill, count in counter.items():

        if count < MIN_OCCURRENCES:
            continue

        insert_or_update_skill(skill)

        if skill not in existing:
            new_skills.append(skill)

    return sorted(new_skills)