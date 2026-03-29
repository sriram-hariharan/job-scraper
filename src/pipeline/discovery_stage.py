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
from src.discovery.discovery_progress import get_next_batch
from src.discovery.greenhouse_api_discovery import validate_greenhouse_companies
from src.discovery.greenhouse_embed_discovery import discover_greenhouse_embed
from src.discovery.github_discovery import run_github_discovery

from src.discovery.ats_network_discovery import (
    discover_greenhouse_neighbors,
    discover_lever_neighbors,
    discover_ashby_neighbors,
    discover_workable_neighbors,
    discover_jobvite_neighbors
)

logger = get_logger(__name__)

def _counts_by_ats(discovered):
    counts = {}

    for ats, companies in discovered.items():
        count = len(companies or [])
        if count > 0:
            counts[ats] = count

    return counts

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
    connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)

    async with aiohttp.ClientSession(connector=connector) as session:

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

                except Exception as e:
                    logger.debug(f"Discovery scan failed: {url} | {e}")
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
            batch = get_next_batch(companies, ats, batch_size=100)

            logger.info(f"{ats:12} scanning {len(batch)} companies for network discovery")

            for slug in batch:
                url = url_template.format(slug)
                tasks.append(scan(url))

        await asyncio.gather(*tasks)

    return discovered


def run_discovery():

    section("ATS DISCOVERY", logger)

    domains = load_lines("data/company_domains.txt")
    learned = get_learned()

    summary = {
        "sources": {},
        "run_unique_discovered_by_ats": {},
    }
    run_unique_discovered = {}

    # ---------------- DOMAIN ATS DISCOVERY ----------------

    logger.info("Domain-based ATS detection")

    domain_discovered = discover_from_domains(domains)
    summary["sources"]["domain_discovered"] = _counts_by_ats(domain_discovered)

    for ats, companies in domain_discovered.items():
        run_unique_discovered.setdefault(ats, set()).update(companies)
        learned[ats].update(companies)
        logger.info(f"{ats:15} {len(companies)} discovered via domains")

    # ---------------- CAREER PAGE ATS DETECTION ----------------

    logger.info("")
    logger.info("Career page ATS detection")

    career_discovered = asyncio.run(
        detect_ats_from_domains(domains)
    )
    summary["sources"]["career_discovered"] = _counts_by_ats(career_discovered)

    for ats, companies in career_discovered.items():
        run_unique_discovered.setdefault(ats, set()).update(companies)
        learned[ats].update(companies)
        logger.info(f"{ats:15} {len(companies)} discovered via career pages")

    # ---------------- ATS NETWORK DISCOVERY ----------------

    logger.info("")
    logger.info("ATS network discovery")

    network_discovered = asyncio.run(
        discover_from_existing_boards()
    )

    normalized_network_discovered = {}
    for ats, companies in network_discovered.items():

        normalized_companies = validate_greenhouse_companies(companies) if ats == "greenhouse" else companies
        normalized_companies = set(normalized_companies)

        normalized_network_discovered[ats] = normalized_companies
        run_unique_discovered.setdefault(ats, set()).update(normalized_companies)
        learned[ats].update(normalized_companies)
        logger.info(f"{ats:15} {len(normalized_companies)} discovered via ATS network")

    summary["sources"]["network_discovered"] = _counts_by_ats(normalized_network_discovered)

    # ---------------- GREENHOUSE EMBED GRAPH DISCOVERY ----------------

    logger.info("")
    logger.info("Greenhouse embed graph discovery")

    greenhouse_companies = load_lines("data/greenhouse_companies.txt")
    batch = get_next_batch(greenhouse_companies, "greenhouse_embed", batch_size=50)

    logger.info(f"{'greenhouse':15} scanning {len(batch)} companies for embed discovery")

    embed_found = discover_greenhouse_embed(batch)
    embed_found = set(validate_greenhouse_companies(embed_found))

    run_unique_discovered.setdefault("greenhouse", set()).update(embed_found)
    learned["greenhouse"].update(embed_found)
    logger.info(f"{'greenhouse':15} {len(embed_found)} discovered via embed graph")

    summary["sources"]["greenhouse_embed_discovered"] = _counts_by_ats(
        {"greenhouse": embed_found}
    )

    # ---------------- SMARTRECRUITERS GLOBAL DISCOVERY ----------------

    logger.info("")
    logger.info("SmartRecruiters global discovery")

    sr_found = set(discover_smartrecruiters_companies())
    run_unique_discovered.setdefault("smartrecruiters", set()).update(sr_found)
    learned["smartrecruiters"].update(sr_found)
    logger.info(f"{'smartrecruiters':15} {len(sr_found)} companies discovered from global feed")

    summary["sources"]["smartrecruiters_global_discovered"] = _counts_by_ats(
        {"smartrecruiters": sr_found}
    )

    # ---------------- GITHUB DISCOVERY ----------------

    logger.info("")
    logger.info("GitHub ATS discovery")

    github_found = run_github_discovery()
    summary["sources"]["github_discovered"] = _counts_by_ats(github_found)

    for ats, companies in github_found.items():
        run_unique_discovered.setdefault(ats, set()).update(companies)
        learned[ats].update(companies)
        logger.info(f"{ats:15} {len(companies)} discovered via github")

    # ---------------- SITEMAP DISCOVERY ----------------

    logger.info("")
    logger.info("Sitemap discovery")

    sitemap_found = run_sitemap_discovery()
    summary["sources"]["sitemap_discovered"] = _counts_by_ats(sitemap_found)

    for ats, companies in sitemap_found.items():
        run_unique_discovered.setdefault(ats, set()).update(companies)
        learned[ats].update(companies)
        logger.info(f"{ats:15} {len(companies)} discovered via sitemap")

    summary["run_unique_discovered_by_ats"] = _counts_by_ats(run_unique_discovered)

    # Final common persisting
    persist_discovered_companies()

    return summary