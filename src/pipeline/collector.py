from config.queries import build_queries
from src.google_search import search_google


def collect_jobs():

    queries = build_queries()

    all_jobs = []

    for q in queries:

        print(f"Searching: {q}")

        results = search_google(q)

        for r in results:

            job = {
                "query": q,
                "title": r["title"],
                "url": r["link"]
            }

            all_jobs.append(job)

    return all_jobs