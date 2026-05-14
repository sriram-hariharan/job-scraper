import os
import re

from src.utils.file_lock import exclusive_file_lock
from src.utils.logging import get_logger

logger = get_logger("discovery_persist")


def append_new_companies(file_path, companies):
    ats = os.path.basename(file_path).replace("_companies.txt", "")

    if not companies:
        return

    companies = {c.strip() for c in companies if c and c.strip()}

    # ---- VALIDATION FIREWALL ----
    if "workday" in file_path:
        companies = {
            c
            for c in companies
            if re.match(r"^https://[^/]+\.myworkdayjobs\.com/[^/]+$", c)
        }

    if not companies:
        logger.info(f"{ats:15} 0 new companies persisted")
        return

    lock_path = f"{file_path}.lock"

    with exclusive_file_lock(lock_path):
        existing = set()
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                existing = {line.strip() for line in f if line.strip()}

        new = companies - existing

        if not new:
            logger.info(f"{ats:15} 0 new companies persisted")
            return

        with open(file_path, "a", encoding="utf-8") as f:
            for c in sorted(new):
                f.write(c + "\n")

    logger.info(f"{ats:15} {len(new)} new companies persisted")
