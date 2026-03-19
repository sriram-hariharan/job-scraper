import aiohttp
import asyncio
from src.config.consts import CAREER_PATHS, ATS_REGEX
from src.utils.logging import get_logger
from tqdm import tqdm
from aiohttp import ClientConnectorError
from urllib.parse import urlparse

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

        task_map = {
            asyncio.create_task(
                detect_greenhouse_slug_from_domain(session, d)
            ): d
            for d in domains
        }

        for task in tqdm(
            asyncio.as_completed(task_map.keys()),
            total=len(task_map),
            desc="Career page scan"
        ):

            result = await task

            if result:
                for ats, slug in result.items():
                    results[ats].add(slug)

    return results

def detect_ats_from_url(url):
    """
    Detect ATS platform and company slug from a career/job URL
    """

    if not url:
        return None, None

    try:

        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.strip("/").split("/")

        # Greenhouse
        if "greenhouse.io" in domain and len(path) >= 1:
            return "greenhouse", path[0]

        # Lever
        if "lever.co" in domain and len(path) >= 1:
            return "lever", path[0]

        # Ashby
        if "ashbyhq.com" in domain and len(path) >= 1:
            return "ashby", path[0]

        # SmartRecruiters
        if "smartrecruiters.com" in domain and len(path) >= 1:
            return "smartrecruiters", path[0]

        # Workable
        if "apply.workable.com" in domain and len(path) >= 1:
            return "workable", path[0]

        # Jobvite
        if "jobvite.com" in domain and len(path) >= 1:
            return "jobvite", path[0]

        # Workday
        if "myworkdayjobs.com" in domain and len(path) >= 1:
            return "workday", path[0]

        return None, None

    except Exception:
        return None, None