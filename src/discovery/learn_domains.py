import os

DATA_PATH = "data/company_domains.txt"

def learn_domain_from_slug(slug):

    if not slug:
        return

    # ignore values that already look like domains
    if "." in slug:
        return

    domain = f"{slug}.com"

    existing = set()
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH) as f:
            existing = {line.strip() for line in f if line.strip()}

    if domain in existing:
        return

    with open(DATA_PATH, "a") as f:
        f.write(domain + "\n")