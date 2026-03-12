from xml.etree import ElementTree
from src.config.consts import ATS_REGEX, CAREER_PATHS, CAREER_SUBDOMAINS, SITEMAP_PATHS
from src.utils.http_retry import http_get
from src.discovery.learned_companies import learn_company


def extract_sitemap_urls(xml):

    try:
        root = ElementTree.fromstring(xml)
    except Exception:
        return []

    urls = []

    for elem in root.iter():
        if elem.tag.endswith("loc") and elem.text:
            urls.append(elem.text.strip())

    return urls


def fetch_sitemap(domain):

    domain = domain.replace("https://", "").replace("http://", "").strip("/")
    if "." not in domain:
        return None
    
    for path in SITEMAP_PATHS:
        
        url = f"https://{domain}{path}"

        try:
            r = http_get(url, timeout=10)

            if r.status_code == 200 and ("<urlset" in r.text or "<sitemapindex" in r.text):
                return r.text

        except Exception:
            continue

    return None


def filter_career_urls(urls):

    career_urls = []

    for url in urls:

        u = url.lower()

        if any(path in u for path in CAREER_PATHS):
            career_urls.append(url)
            continue

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

def expand_nested_sitemaps(urls, limit=10):

    expanded = []

    for url in urls:

        if not url.endswith(".xml"):
            expanded.append(url)
            continue

        try:
            r = http_get(url, timeout=10)

            if r.status_code == 200:
                nested_urls = extract_sitemap_urls(r.text)

                if nested_urls:
                    expanded.extend(nested_urls)
                else:
                    expanded.append(url)

        except Exception:
            expanded.append(url)

        if len(expanded) > limit * 100:
            break

    return expanded

def discover_from_sitemap(domain):
    
    xml = fetch_sitemap(domain)

    if not xml:
        return {}

    urls = extract_sitemap_urls(xml)

    if not urls:
        return {}

    # expand nested sitemaps
    urls = expand_nested_sitemaps(urls)

    career_urls = filter_career_urls(urls)

    if not career_urls:
        return {}

    return detect_ats_from_urls(career_urls)