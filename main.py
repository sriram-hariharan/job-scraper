from src.discovery.domain_ats_discovery import discover_from_domains
# from src.scrapers.greenhouse_scraper import scrape_all_greenhouse
# from src.scrapers.ashby_scraper import scrape_all_ashby
# from src.scrapers.lever_scraper import scrape_all_lever
from src.scrapers.workday_scraper import scrape_all_workday

print("=============================")
print("ATS DISCOVERY")
print("=============================\n")

greenhouse, ashby, lever, workday = discover_from_domains()

print("Greenhouse detected:", len(greenhouse))
print("Ashby detected:", len(ashby))
print("Lever detected:", len(lever))
print("Workday detected:", len(workday))

print("\n=============================")
print("SCRAPING JOBS")
print("=============================\n")

# gh_jobs = scrape_all_greenhouse()
# ashby_jobs = scrape_all_ashby()
# lever_jobs = scrape_all_lever()

wd_jobs = scrape_all_workday()

# print("Greenhouse jobs fetched:", len(gh_jobs))
# print("Ashby jobs fetched:", len(ashby_jobs))
# print("Lever jobs fetched:", len(lever_jobs))
print("Workday jobs fetched:", len(wd_jobs))