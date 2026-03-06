from config.queries import build_queries
from src.google_search import search_google


def collect_jobs():

<<<<<<< Updated upstream
    queries = build_queries()
=======
    scrapers = [
        # ("workday", scrape_all_workday),
        # ("greenhouse", scrape_all_greenhouse),
        # ("lever", scrape_all_lever),
        # ("ashby", scrape_all_ashby),
        # ("workable", scrape_all_workable),
        ("jobvite", scrape_all_jobvite),
    ]
>>>>>>> Stashed changes

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

<<<<<<< Updated upstream
    return all_jobs
=======
                print(f"{name} scraper finished | jobs: {len(jobs)} | time: {elapsed}s")

                all_jobs.extend(jobs)

            except Exception as e:
                print(f"{name} scraper failed:", e)

    total_elapsed = round(time.time() - start_total, 2)

    print(f"\nTotal scraping time: {total_elapsed}s")
    print("Total raw jobs collected:", len(all_jobs))

    # ----- DEBUG BEFORE FILTERING -----

    print("\nRaw jobs by source:")
    for source, count in Counter(job["source"] for job in all_jobs).items():
        print(source, count)

    # ----- FILTER -----

    filtered_jobs = filter_jobs(all_jobs)
    
    print("\nJobs missing posted_at after filtering:")
    missing = Counter(job["source"] for job in all_jobs if not job.get("posted_at"))
    for source, count in missing.items():
        print(source, count)

    print("\nTotal filtered jobs:", len(filtered_jobs))

    print("\nFiltered jobs by source:")
    for source, count in Counter(job["source"] for job in filtered_jobs).items():
        print(source, count)

    deduped_jobs = dedupe_jobs(filtered_jobs)

    print("\nTotal deduped jobs:", len(deduped_jobs))

    return deduped_jobs
>>>>>>> Stashed changes
