import re
import json


def extract_jsonld_dateposted(html):

    scripts = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )

    for block in scripts:
        try:
            data = json.loads(block)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        if item.get("datePosted"):
                            return item["datePosted"]

            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                if data.get("datePosted"):
                    return data["datePosted"]

        except Exception:
            continue

    return None