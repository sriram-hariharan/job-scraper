import re
from collections import Counter

from src.metrics.skill_db import (
    init_skill_db,
    get_existing_skills,
    insert_or_update_skill
)

MIN_OCCURRENCES = 3


def extract_candidate_skills(text):

    text = text.lower()

    tokens = re.findall(r"[a-z][a-z0-9\-\+\.]{2,}", text)

    candidates = []

    for token in tokens:

        if token.isdigit():
            continue

        if len(token) < 3:
            continue

        candidates.append(token)

    return candidates


def discover_new_skills(jobs):

    init_skill_db()

    counter = Counter()

    for job in jobs:

        desc = job.get("description_text", "")

        if not desc:
            continue

        tokens = extract_candidate_skills(desc)

        counter.update(tokens)

    existing = get_existing_skills()

    new_skills = []

    for token, count in counter.items():

        if count < MIN_OCCURRENCES:
            continue

        if any(x in token for x in [
            "ai",
            "ml",
            "model",
            "vector",
            "tensor",
            "torch",
            "lang",
            "transformer"
        ]):

            insert_or_update_skill(token)

            if token not in existing:
                new_skills.append(token)

    return new_skills