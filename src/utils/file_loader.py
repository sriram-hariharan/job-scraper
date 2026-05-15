from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


_ATS_COMPANY_FILES = {
    "greenhouse_companies.txt": "greenhouse",
    "lever_companies.txt": "lever",
    "workday_companies.txt": "workday",
    "ashby_companies.txt": "ashby",
    "workable_companies.txt": "workable",
    "jobvite_companies.txt": "jobvite",
    "smartrecruiters_companies.txt": "smartrecruiters",
}


def _clean_text(value) -> str:
    return str(value or "").strip()


def _sorted_lines(values: Iterable[str]) -> List[str]:
    return sorted({_clean_text(value) for value in values if _clean_text(value)})


def _postgres_discovery_lines(path: str):
    safe_path = _clean_text(path)
    name = Path(safe_path).name

    if safe_path == "data/company_domains.txt" or name == "company_domains.txt":
        from src.storage.discovery_store import get_company_domains

        return _sorted_lines(get_company_domains())

    ats = _ATS_COMPANY_FILES.get(name)
    if ats:
        from src.storage.discovery_store import get_discovered_ats_companies

        return _sorted_lines(get_discovered_ats_companies(ats))

    return None


def load_lines(path: str):
    postgres_lines = _postgres_discovery_lines(path)
    if postgres_lines is not None:
        return postgres_lines

    items = []

    with open(path) as f:
        for line in f:
            val = line.strip()
            if val:
                items.append(val)

    return items
