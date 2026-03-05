from src.pipeline.collector import collect_all_jobs

def main():

    print("=============================")
    print("ATS DISCOVERY")
    print("=============================\n")

    # greenhouse, ashby, lever, workday = discover_from_domains()

    # print("Greenhouse detected:", len(greenhouse))
    # print("Ashby detected:", len(ashby))
    # print("Lever detected:", len(lever))
    # print("Workday detected:", len(workday))

    print("\n=============================")
    print("SCRAPING JOBS")
    print("=============================\n")

    all_jobs = collect_all_jobs()
    if all_jobs:
        print("Sample job:")
        print(all_jobs[0])
    else:
        print("No jobs returned.")
    print("Final jobs:", len(all_jobs))

if __name__ == "__main__":
    main()