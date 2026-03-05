ATS_SITES = [
    "boards.greenhouse.io",
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "apply.workable.com",
    "jobs.jobvite.com",
    # "recruiting.adp.com",
    "wd1.myworkdayjobs.com",
    # "careers.icims.com",
    # "jobs.bamboohr.com",
    # "recruiting.paylocity.com",
    # "jobs.smartrecruiters.com",
    # "jobs.gem.com",
    # "app.dover.com"
]

JOB_TITLES = [
    "Data Scientist",
    "Senior Data Scientist",
    "Data Analyst",
    "Senior Data Analyst",
    "Machine Learning Engineer",
    "AI Engineer",
    "Applied Scientist"
]


def build_queries():
    """
    Generates Google search queries combining ATS sites and job titles.
    """

    queries = []

    for site in ATS_SITES:
        for title in JOB_TITLES:

            query = f'site:{site} "{title}"'
            queries.append(query)

    return queries