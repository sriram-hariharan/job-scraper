from src.pipeline.collector import collect_all_jobs
from src.pipeline.excel_writer import write_jobs_to_sheet

def main():

    print("=============================")
    print("ATS DISCOVERY")
    print("=============================\n")

    # greenhouse, ashby, lever, workday = discover_from_domains()

    # print("Greenhouse detected:", len(greenhouse))
    # print("Ashby detected:", len(ashby))
    # print("Lever detected:", len(lever))
    # print("Workday detected:", len(workday))

    print("=============================")
    print("SCRAPING JOBS")
    print("=============================\n")

    jobs = collect_all_jobs()

    if jobs:
        print("Sample job:")
        print(jobs[0])

        write_jobs_to_sheet(jobs)

    print("Final jobs:", len(jobs))

if __name__ == "__main__":
    main()