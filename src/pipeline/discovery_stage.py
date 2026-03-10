from src.discovery.discovery import discover_from_domains
from src.discovery.save_companies import append_new_companies
from src.utils.file_loader import load_lines
from src.utils.logging import get_logger
from src.discovery.career_ats_detector import detect_ats_from_domains
import asyncio

logger = get_logger(__name__)


def run_discovery():

    logger.info("=============================")
    logger.info("ATS DISCOVERY")
    logger.info("=============================\n")

    domains = load_lines("data/company_domains.txt")

    # -------- DOMAIN ATS DISCOVERY --------

    discovered = discover_from_domains(domains)

    for ats, companies in discovered.items():
        logger.info(f"{ats}: {len(companies)} discovered")

    append_new_companies("data/greenhouse_companies.txt", discovered["greenhouse"])
    append_new_companies("data/lever_companies.txt", discovered["lever"])
    append_new_companies("data/workday_companies.txt", discovered["workday"])
    append_new_companies("data/ashby_companies.txt", discovered["ashby"])
    append_new_companies("data/workable_companies.txt", discovered["workable"])
    append_new_companies("data/jobvite_companies.txt", discovered["jobvite"])


    # -------- CAREER PAGE ATS DETECTION --------

    logger.info("Running career page ATS detection...")

    career_discovered = asyncio.run(
        detect_ats_from_domains(domains)
    )

    logger.info("Career ATS detection results:")

    for ats, companies in career_discovered.items():
        logger.info(f"{ats}: {len(companies)} discovered")

    append_new_companies("data/greenhouse_companies.txt", career_discovered["greenhouse"])
    append_new_companies("data/lever_companies.txt", career_discovered["lever"])
    append_new_companies("data/workday_companies.txt", career_discovered["workday"])
    append_new_companies("data/ashby_companies.txt", career_discovered["ashby"])
    append_new_companies("data/workable_companies.txt", career_discovered["workable"])
    append_new_companies("data/jobvite_companies.txt", career_discovered["jobvite"])