from src.discovery.learned_companies import get_learned
from src.discovery.save_companies import append_new_companies

ATS_FILES = {
    "greenhouse": "data/greenhouse_companies.txt",
    "lever": "data/lever_companies.txt",
    "workday": "data/workday_companies.txt",
    "ashby": "data/ashby_companies.txt",
    "workable": "data/workable_companies.txt",
    "jobvite": "data/jobvite_companies.txt",
    "smartrecruiters": "data/smartrecruiters_companies.txt",
}

def persist_discovered_companies():
    learned = get_learned()
    for ats, companies in learned.items():
        if not companies:
            continue

        path = ATS_FILES.get(ats)

        if path:
            append_new_companies(path, companies)