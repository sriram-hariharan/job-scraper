from src.discovery.sitemap_fetcher import discover_from_sitemap
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger

logger = get_logger("sitemap_discovery")


def run_sitemap_discovery():

    domains = load_lines("data/company_domains.txt")

    logger.info(f"Sitemap discovery domains: {len(domains)}")

    results = run_parallel(
        domains,
        discover_from_sitemap,
        max_workers=20,
        desc="Sitemap discovery"
    )

    discovered = {}

    for r in results:

        if not isinstance(r, dict):
            continue

        for ats, companies in r.items():

            if not companies:
                continue

            discovered.setdefault(ats, set()).update(companies)

    return discovered