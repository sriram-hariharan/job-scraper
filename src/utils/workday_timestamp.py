import requests
from src.utils.html_timestamp_extractor import extract_jsonld_dateposted

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def fetch_workday_timestamp(board_url, external_path):
    try:
        url = f"{board_url.rstrip('/')}{external_path}"
        r = session.get(url, timeout=10)

        if r.status_code != 200:
            return None

    except Exception:
        return None

    return extract_jsonld_dateposted(r.text)