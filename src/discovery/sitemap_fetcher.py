import requests
from xml.etree import ElementTree
from src.config.consts import ATS_REGEX, CAREER_PATHS, CAREER_SUBDOMAINS, SITEMAP_PATHS
from src.discovery.learned_companies import learn_company

def extract_sitemap_urls(xml):

    root = ElementTree.fromstring(xml)

    urls = []

    for elem in root.iter():
        if elem.tag.endswith("loc"):
            urls.append(elem.text)

    return urls

def fetch_sitemap(domain):

    for path in SITEMAP_PATHS:

        url = f"https://{domain}{path}"

        try:
            r = requests.get(url, timeout=10)

            if r.status_code == 200 and ("<urlset" in r.text or "<sitemapindex" in r.text):
                return r.text

        except Exception:
            continue

    return None

def filter_career_urls(urls):

    career_urls = []

    for url in urls:

        u = url.lower()

        # match known career paths
        if any(path in u for path in CAREER_PATHS):
            career_urls.append(url)
            continue

        # match career subdomains
        if any(f"{sub}." in u for sub in CAREER_SUBDOMAINS):
            career_urls.append(url)

    return list(set(career_urls))

def detect_ats_from_urls(urls):

    found = {ats: set() for ats in ATS_REGEX}

    for url in urls:

        for ats, patterns in ATS_REGEX.items():

            for pattern in patterns:

                m = pattern.search(url)

                if m:
                    slug = m.group(1)
                    found[ats].add(slug)
                    learn_company(ats, slug)

    return found

def discover_from_sitemap(domain):

    xml = fetch_sitemap(domain)

    if not xml:
        return {}

    urls = extract_sitemap_urls(xml)
    career_urls = filter_career_urls(urls)

    if not urls:
        return {}

    if not career_urls:
        return {}

    return detect_ats_from_urls(career_urls)