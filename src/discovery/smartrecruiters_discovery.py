import requests
from src.discovery.learned_companies import get_learned

API = "https://jobs.smartrecruiters.com/sr-jobs/search?limit=100&offset={}"

def discover_smartrecruiters_companies():

    learned = get_learned()
    found = set()

    offset = 0
    pages = 0

    # while True:
    for offset in range(0, 3000, 100):
        r = requests.get(API.format(offset), timeout=10)

        if r.status_code != 200:
            break

        data = r.json()
        content = data.get("content", [])

        if not content:
            break

        for job in content:
            identifier = job.get("company", {}).get("identifier")

            if identifier:
                found.add(identifier.lower())

        pages += 1

        if pages % 10 == 0:
            print(f"SmartRecruiters discovery scanned {pages*100} jobs")

        offset += 100

    learned["smartrecruiters"].update(found)

    return found