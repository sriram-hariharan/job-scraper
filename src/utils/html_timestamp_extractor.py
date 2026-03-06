import re
import json

def extract_jsonld_dateposted(html):

    scripts = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.DOTALL
    )

    for block in scripts:
        try:
            data = json.loads(block)
        except Exception:
            continue

        ts = find_dateposted(data)
        if ts:
            return ts

    return None


def find_dateposted(obj):

    if isinstance(obj, dict):

        # direct hit
        if obj.get("@type") == "JobPosting":
            if obj.get("datePosted"):
                return obj["datePosted"]

            if obj.get("datePublished"):
                return obj["datePublished"]

        # recursive search
        for v in obj.values():
            ts = find_dateposted(v)
            if ts:
                return ts

    elif isinstance(obj, list):
        for item in obj:
            ts = find_dateposted(item)
            if ts:
                return ts

    return None