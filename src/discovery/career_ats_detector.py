import aiohttp
import asyncio
from src.config.consts import CAREER_PATHS, ATS_REGEX
from src.utils.logging import get_logger
from tqdm import tqdm
from aiohttp import ClientConnectorError

logger = get_logger(__name__)

async def detect_greenhouse_slug_from_domain(session, domain):

    if not domain:
        return None

    domain = (
        domain.strip()
        .lower()
        .replace("https://", "")
        .replace("http://", "")
        .split("/")[0]
    )

    if "." not in domain:
        return None
    
    headers = {"User-Agent": "Mozilla/5.0"}

    for path in CAREER_PATHS:

        url = f"https://{domain}{path}"

        try:
            async with session.get(url, headers=headers, timeout=10) as resp:

                if resp.status != 200:
                    continue

                html = await resp.text()

                found = {}
                for ats, regex_list in ATS_REGEX.items():

                    for regex in regex_list:

                        match = regex.search(html)

                        if match:
                            slug = match.group(1).lower()
                            found[ats] = slug
                            break

                if found:
                    return found

        except ClientConnectorError:
            continue
        except asyncio.TimeoutError:
            continue
        except Exception:
            continue

    return None

async def detect_ats_from_domains(domains):

    connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)

    results = {
        "greenhouse": set(),
        "lever": set(),
        "ashby": set(),
        "workable": set(),
        "jobvite": set(),
        "workday": set(),
        "smartrecruiters": set()
    }

    async with aiohttp.ClientSession(connector=connector) as session:

        tasks = [
            detect_greenhouse_slug_from_domain(session, d)
            for d in domains
        ]

        for future in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Career page scan"
        ):
            r = await future

            if r:
                for ats, slug in r.items():
                    results[ats].add(slug)

    return results