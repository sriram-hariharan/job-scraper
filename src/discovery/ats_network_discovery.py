import re
from urllib.parse import urlparse

from src.config.consts import GREENHOUSE_PATTERNS, INVALID_GREENHOUSE_SLUGS

def discover_greenhouse_neighbors(html: str):

    if not html:
        return []

    discovered = set()

    # extract all href links once
    links = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)

    for link in links:

        if "boards.greenhouse.io" not in link:
            continue

        try:
            path = urlparse(link).path.strip("/")
            slug = path.split("/")[0].lower()

            if slug:
                discovered.add(slug)

        except Exception:
            continue

    return sorted(discovered)

def discover_lever_neighbors(html: str):

    if not html:
        return []

    matches = re.findall(r"jobs\.lever\.co/([a-zA-Z0-9\-_]+)", html)

    return sorted(set(m.lower() for m in matches))

def discover_ashby_neighbors(html: str):

    if not html:
        return []

    matches = re.findall(r"jobs\.ashbyhq\.com/([a-zA-Z0-9\-_]+)", html)

    return sorted(set(m.lower() for m in matches))

def discover_workable_neighbors(html: str):

    if not html:
        return []

    matches = re.findall(r"apply\.workable\.com/([a-zA-Z0-9\-_]+)", html)

    return sorted(set(m.lower() for m in matches))

def discover_jobvite_neighbors(html: str):

    if not html:
        return []

    matches = re.findall(r"jobs\.jobvite\.com/([a-zA-Z0-9\-_]+)", html)

    return sorted(set(m.lower() for m in matches))