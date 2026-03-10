from src.discovery.discovery import discover_from_domains
from src.utils.file_loader import load_lines
from src.utils.logging import get_logger
from src.discovery.career_ats_detector import detect_ats_from_domains
from src.discovery.persist_discovered import persist_discovered_companies
from src.discovery.learned_companies import get_learned

import asyncio
import aiohttp

from src.discovery.ats_network_discovery import (
    discover_greenhouse_neighbors,
    discover_lever_neighbors,
    discover_ashby_neighbors,
    discover_workable_neighbors,
    discover_jobvite_neighbors
)

logger = get_logger(__name__)


async def discover_from_existing_boards():

    discovered = {
        "greenhouse": set(),
        "lever": set(),
        "ashby": set(),
        "workable": set(),
        "jobvite": set()
    }

    async with aiohttp.ClientSession() as session:

        async def scan(url):

            try:
                async with session.get(url, timeout=10) as resp:

                    if resp.status != 200:
                        return

                    html = await resp.text()

                    discovered["greenhouse"].update(
                        discover_greenhouse_neighbors(html)
                    )

                    discovered["lever"].update(
                        discover_lever_neighbors(html)
                    )

                    discovered["ashby"].update(
                        discover_ashby_neighbors(html)
                    )

                    discovered["workable"].update(
                        discover_workable_neighbors(html)
                    )

                    discovered["jobvite"].update(
                        discover_jobvite_neighbors(html)
                    )

            except Exception:
                return

        companies = load_lines("data/greenhouse_companies.txt")

        tasks = []

        for slug in companies[:100]:  # safety limit
            url = f"https://boards.greenhouse.io/{slug}"
            tasks.append(scan(url))

        await asyncio.gather(*tasks)

    return discovered


def run_discovery():

    logger.info("=============================")
    logger.info("ATS DISCOVERY")
    logger.info("=============================\n")

    domains = load_lines("data/company_domains.txt")

    # -------- DOMAIN ATS DISCOVERY --------

    domain_discovered = discover_from_domains(domains)

    learned = get_learned()

    for ats, companies in domain_discovered.items():
        learned[ats].update(companies)
        logger.info(f"{ats}: {len(companies)} discovered")

    # -------- CAREER PAGE ATS DETECTION --------

    logger.info("Running career page ATS detection...")

    career_discovered = asyncio.run(
        detect_ats_from_domains(domains)
    )

    logger.info("Career ATS detection results:")

    for ats, companies in career_discovered.items():
        learned[ats].update(companies)
        logger.info(f"{ats}: {len(companies)} discovered")

    # -------- ATS NETWORK DISCOVERY --------

    logger.info("Running ATS network discovery...")

    network_discovered = asyncio.run(
        discover_from_existing_boards()
    )

    for ats, companies in network_discovered.items():
        learned[ats].update(companies)
        logger.info(f"{ats}: {len(companies)} discovered from ATS network")

    #Final common persisting
    persist_discovered_companies()