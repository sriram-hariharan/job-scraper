import requests


def load_domains():

    domains = []

    with open("data/company_domains.txt") as f:

        for line in f:

            d = line.strip()

            if d:
                domains.append(d)

    return domains


def domain_to_slug(domain):

    domain = domain.replace("https://", "")
    domain = domain.replace("http://", "")
    domain = domain.replace("www.", "")

    return domain.split(".")[0]


def ashby_board_exists(slug):

    url = f"https://jobs.ashbyhq.com/{slug}"

    try:

        r = requests.get(url, timeout=5)

        if r.status_code == 200:
            return True

    except:
        pass

    return False


def discover_ashby():

    domains = load_domains()

    discovered = []

    for domain in domains:

        slug = domain_to_slug(domain)

        print("Checking:", slug)

        if ashby_board_exists(slug):

            print("Found Ashby board:", slug)

            discovered.append(slug)

    return discovered