import requests
from src.utils.logging import get_logger
from tqdm import tqdm

logger = get_logger("greenhouse_api_discovery")

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{}/jobs"

def validate_greenhouse_company(slug):

    url = GREENHOUSE_API.format(slug)

    try:
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            data = r.json()

            if data.get("jobs"):
                return True

    except Exception:
        pass

    return False


def validate_greenhouse_companies(slugs):

    valid = set()

    for slug in tqdm(slugs, desc="Greenhouse API validation"):

        if validate_greenhouse_company(slug):
            valid.add(slug)

    logger.info(f"{len(valid)} valid greenhouse companies from API validation")

    return valid