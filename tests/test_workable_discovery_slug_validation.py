from src.discovery import learned_companies


def _clear_learned():
    for companies in learned_companies.get_learned().values():
        companies.clear()


def test_workable_job_url_learns_company_slug():
    _clear_learned()

    learned_companies.learn_from_job_url("https://apply.workable.com/acme/j/ABC123/")

    assert learned_companies.get_learned()["workable"] == {"acme"}


def test_workable_route_url_does_not_learn_j_as_company():
    _clear_learned()

    learned_companies.learn_from_job_url("https://apply.workable.com/j/ABC123/")

    assert learned_companies.get_learned()["workable"] == set()


def test_existing_non_workable_ats_parsing_still_works():
    _clear_learned()

    learned_companies.learn_from_job_url("https://boards.greenhouse.io/acme/jobs/123")
    learned_companies.learn_from_job_url("https://jobs.lever.co/example/abc123")
    learned_companies.learn_from_job_url("https://jobs.ashbyhq.com/plaid/abc123")

    learned = learned_companies.get_learned()
    assert learned["greenhouse"] == {"acme"}
    assert learned["lever"] == {"example"}
    assert learned["ashby"] == {"plaid"}


def test_learn_company_rejects_workable_route_tokens():
    _clear_learned()

    learned_companies.learn_company("workable", "jobs")
    learned_companies.learn_company("workable", "Acme")

    assert learned_companies.get_learned()["workable"] == {"acme"}
