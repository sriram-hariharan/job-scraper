import requests

DATASET_URL = "https://raw.githubusercontent.com/iamxjb/startup-domains/master/domains.txt"


def load_company_domains():

    try:
        r = requests.get(DATASET_URL, timeout=30)

        print("Dataset status:", r.status_code)

        if r.status_code != 200:
            return []

        lines = r.text.splitlines()

    except Exception as e:
        print("Dataset request failed:", e)
        return []

    domains = []

    for line in lines:

        domain = line.strip()

        if domain and "." in domain:
            domains.append(domain)

    print("Dataset domains loaded:", len(domains))

    return domains


def save_domains_to_file(domains, file_path="data/company_domains.txt"):

    existing = set()

    try:
        with open(file_path, "r") as f:
            existing = set(x.strip() for x in f.readlines())
    except:
        pass

    new_domains = set(domains) - existing

    if not new_domains:
        print("No new domains added")
        return

    with open(file_path, "a") as f:

        for d in new_domains:
            f.write(d + "\n")

    print("New domains added:", len(new_domains))