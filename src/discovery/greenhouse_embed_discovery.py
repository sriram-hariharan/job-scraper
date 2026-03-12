import re
import asyncio
import aiohttp
from src.utils.logging import get_logger

logger = get_logger("greenhouse_embed_discovery")

EMBED_URL = "https://boards.greenhouse.io/embed/job_board?for={}"

PATTERN = re.compile(r"boards\.greenhouse\.io/([a-zA-Z0-9\-]+)")


async def fetch_embed(session, slug, semaphore):

    url = EMBED_URL.format(slug)

    found = set()

    async with semaphore:

        try:
            async with session.get(url, timeout=10) as resp:

                if resp.status != 200:
                    return found

                html = await resp.text()

                matches = PATTERN.findall(html)

                for m in matches:
                    found.add(m)

        except Exception:
            return found

    return found


async def _discover_async(slugs):

    discovered = set()

    semaphore = asyncio.Semaphore(20)

    async with aiohttp.ClientSession() as session:

        tasks = [
            fetch_embed(session, slug, semaphore)
            for slug in slugs
        ]

        results = await asyncio.gather(*tasks)

        for r in results:
            discovered.update(r)

    return discovered


def discover_greenhouse_embed(slugs):

    discovered = asyncio.run(_discover_async(slugs))

    logger.info(f"{len(discovered)} greenhouse companies discovered via embed graph")

    return discovered