from src.discovery.discovery import discover_from_domains
from src.discovery.save_companies import append_new_companies
from src.utils.file_loader import load_lines
from src.utils.logging import get_logger

logger = get_logger(__name__)


def run_discovery():

    logger.info("=============================")
    logger.info("ATS DISCOVERY")
    logger.info("=============================\n")

    domains = load_lines("data/company_domains.txt")

    discovered = discover_from_domains(domains)

    for ats, companies in discovered.items():
        logger.info(f"{ats}: {len(companies)} discovered")

    append_new_companies("data/greenhouse_companies.txt", discovered["greenhouse"])
    append_new_companies("data/lever_companies.txt", discovered["lever"])
    append_new_companies("data/workday_companies.txt", discovered["workday"])
    append_new_companies("data/ashby_companies.txt", discovered["ashby"])
    append_new_companies("data/workable_companies.txt", discovered["workable"])
    append_new_companies("data/jobvite_companies.txt", discovered["jobvite"])