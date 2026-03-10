import re

def normalize_workday_url(url):
    if not url:
        return None

    m = re.search(r"https://[^ ]+\.myworkdayjobs\.com/[^/?#]+", url)
    if not m:
        return None

    base = m.group(0)

    # remove login / jobs / extra paths
    base = re.sub(r"/(login|jobs|introduceYourself|jobAlerts).*", "", base)

    return base