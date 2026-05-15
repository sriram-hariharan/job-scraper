import re

from src.utils.logging import get_logger
from src.storage.discovery_store import get_discovered_ats_companies, upsert_discovered_ats_companies

logger = get_logger("discovery_persist")


def _ats_from_file_path(file_path):
    name = str(file_path or "").split("/")[-1]
    return name.replace("_companies.txt", "").strip().lower()


def append_new_companies(file_path, companies):
    ats = _ats_from_file_path(file_path)

    if not companies:
        return

    companies = {c.strip() for c in companies if c and c.strip()}

    # ---- VALIDATION FIREWALL ----
    if "workday" in str(file_path):
        companies = {
            c
            for c in companies
            if re.match(r"^https://[^/]+\.myworkdayjobs\.com/[^/]+$", c)
        }

    if not companies:
        logger.info(f"{ats:15} 0 new companies persisted")
        return

    existing = get_discovered_ats_companies(ats)
    new = companies - existing

    if not new:
        logger.info(f"{ats:15} 0 new companies persisted")
        return

    new_count = upsert_discovered_ats_companies(
        ats,
        new,
        source="persist_discovered_companies",
    )

    logger.info(f"{ats:15} {new_count} new companies persisted")
