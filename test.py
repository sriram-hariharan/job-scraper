from src.scrapers.workday_scraper import load_companies

comp = load_companies()

for c in comp:
    company = (c.split("https://")[1].split(".")[0])
    if company == "otis":
        print(c)