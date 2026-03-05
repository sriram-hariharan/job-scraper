from .ats_detector import *
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def load_domains():

    domains = []

    with open("data/company_domains.txt") as f:

        for line in f:

            d = line.strip()

            if d:
                domains.append(d)

    return domains


def save_companies(filename, companies):

    existing = set()

    try:
        with open(filename, "r") as f:
            for line in f:
                existing.add(line.strip())
    except:
        pass

    with open(filename, "a") as f:
        for c in companies:
            if c not in existing:
                f.write(c + "\n")

def check_domain(domain):

    greenhouse = None
    ashby = None
    lever = None
    workday = None

    slug = slug_from_domain(domain)

    if slug:

        try:
            if check_greenhouse(slug):
                greenhouse = slug
        except:
            pass

        try:
            if check_ashby(slug):
                ashby = slug
        except:
            pass

    try:
        lever_slug = extract_lever_slug_from_domain(domain)
        if lever_slug:
            lever = lever_slug
    except:
        pass

    try:
        # if check_workday(domain):
        wd_url = extract_workday_board_url(domain)

        if wd_url:
            workday = wd_url
            
    except:
        pass

    return greenhouse, ashby, lever, workday

def discover_from_domains():

    domains = load_domains()

    greenhouse = []
    ashby = []
    lever = []
    workday = []

    results = []

    with ThreadPoolExecutor(max_workers=20) as executor:

        results = list(
            tqdm(
                executor.map(check_domain, domains),
                total=len(domains),
                desc="ATS discovery"
            )
        )

    for greenhouse_slug, ashby_slug, lever_slug, workday_url in results:

        if greenhouse_slug:
            greenhouse.append(greenhouse_slug)
        if ashby_slug:
            ashby.append(ashby_slug)
        if lever_slug:
            lever.append(lever_slug)
        if workday_url:
            workday.append(workday_url)

    save_companies("data/greenhouse_companies.txt", greenhouse)
    save_companies("data/ashby_companies.txt", ashby)
    save_companies("data/lever_companies.txt", lever)
    save_companies("data/workday_companies.txt", workday)

    print("\nSaved company lists to data/")

    return greenhouse, ashby, lever, workday