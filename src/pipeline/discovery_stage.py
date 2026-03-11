from src.discovery.discovery import discover_from_domains
from src.utils.file_loader import load_lines
from src.utils.logging import get_logger
from src.discovery.career_ats_detector import detect_ats_from_domains
from src.discovery.persist_discovered import persist_discovered_companies
from src.discovery.learned_companies import get_learned
from src.discovery.smartrecruiters_discovery import discover_smartrecruiters_companies
from src.discovery.sitemap_discovery import run_sitemap_discovery
from src.utils.log_sections import section
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
        "jobvite": set(),
        "workday": set()
    }

    semaphore = asyncio.Semaphore(20)   # limit concurrent requests
    async with aiohttp.ClientSession() as session:

        async def scan(url):

            async with semaphore:   # concurrency control

                try:
                    async with session.get(
                        url,
                        timeout=10,
                        headers={"User-Agent": "Mozilla/5.0"}
                    ) as resp:

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

        ATS_BOARD_URLS = {
            "greenhouse": ("data/greenhouse_companies.txt", "https://boards.greenhouse.io/{}"),
            "lever": ("data/lever_companies.txt", "https://jobs.lever.co/{}"),
            "ashby": ("data/ashby_companies.txt", "https://jobs.ashbyhq.com/{}"),
            "workable": ("data/workable_companies.txt", "https://apply.workable.com/{}"),
            "jobvite": ("data/jobvite_companies.txt", "https://jobs.jobvite.com/{}")
        }

        tasks = []
        for ats, (file_path, url_template) in ATS_BOARD_URLS.items():

            companies = load_lines(file_path)

            for slug in companies[:100]:   # safety limit
                url = url_template.format(slug)
                tasks.append(scan(url))

        await asyncio.gather(*tasks)

    return discovered


def run_discovery():

    section("ATS DISCOVERY", logger)

    domains = load_lines("data/company_domains.txt")
    learned = get_learned()

    # ---------------- DOMAIN ATS DISCOVERY ----------------

    logger.info("Domain-based ATS detection")

    domain_discovered = discover_from_domains(domains)

    for ats, companies in domain_discovered.items():
        learned[ats].update(companies)
        logger.info(f"{ats:15} {len(companies)} discovered via domains")

    # ---------------- CAREER PAGE ATS DETECTION ----------------

    logger.info("")
    logger.info("Career page ATS detection")

    career_discovered = asyncio.run(
        detect_ats_from_domains(domains)
    )

    for ats, companies in career_discovered.items():
        learned[ats].update(companies)
        logger.info(f"{ats:15} {len(companies)} discovered via career pages")

    # ---------------- ATS NETWORK DISCOVERY ----------------

    logger.info("")
    logger.info("ATS network discovery")

    network_discovered = asyncio.run(
        discover_from_existing_boards()
    )

    for ats, companies in network_discovered.items():
        learned[ats].update(companies)
        logger.info(f"{ats:15} {len(companies)} discovered via ATS network")

    # ---------------- SMARTRECRUITERS GLOBAL DISCOVERY ----------------
    logger.info("")
    logger.info("SmartRecruiters global discovery")

    sr_found = discover_smartrecruiters_companies()
    learned["smartrecruiters"].update(sr_found)
    logger.info(f"{'smartrecruiters':15} {len(sr_found)} companies discovered from global feed")

    # ---------------- SITEMAP DISCOVERY ----------------

    logger.info("")
    logger.info("Sitemap discovery")

    sitemap_found = run_sitemap_discovery()

    for ats, companies in sitemap_found.items():
        learned[ats].update(companies)
        logger.info(f"{ats:15} {len(companies)} discovered via sitemap")

    # Final common persisting
    persist_discovered_companies()