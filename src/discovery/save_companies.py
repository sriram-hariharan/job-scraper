import os
import re
from src.utils.logging import get_logger

logger = get_logger("discovery_persist")

def append_new_companies(file_path, companies):

    ats = os.path.basename(file_path).replace("_companies.txt", "")

    if not companies:
        return

    # remove blanks
    companies = {c.strip() for c in companies if c and c.strip()}

    # ---- VALIDATION FIREWALL ----
    if "workday" in file_path:
        companies = {
            c for c in companies
            if re.match(r"^https://[^/]+\.myworkdayjobs\.com/[^/]+$", c)
        }

    # load existing
    existing = set()
    if os.path.exists(file_path):
        with open(file_path) as f:
            existing = {line.strip() for line in f if line.strip()}

    # compute new companies
    new = companies - existing

    if not new:
        logger.info(f"{ats:15} 0 new companies persisted")
        return

    # append new ones
    with open(file_path, "a") as f:
        for c in sorted(new):
            f.write(c + "\n")

    logger.info(f"{ats:15} {len(new)} new companies persisted")