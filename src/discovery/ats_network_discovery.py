import re
from src.config.consts import GREENHOUSE_PATTERNS, INVALID_GREENHOUSE_SLUGS

def discover_greenhouse_neighbors(html: str):

    if not html:
        return []

    discovered = set()

    for pattern in GREENHOUSE_PATTERNS:
        matches = re.findall(pattern, html, flags=re.IGNORECASE)

        for slug in matches:
            slug = slug.strip().lower()

            if not slug:
                continue

            if slug in INVALID_GREENHOUSE_SLUGS:
                continue

            discovered.add(slug)

    return sorted(discovered)