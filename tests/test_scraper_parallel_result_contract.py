from collections import Counter

import pytest

from src.discovery import sitemap_discovery
from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.scrapers import (
    ashby_scraper,
    jobvite_scraper,
    smartrecruiters_scraper,
    workable_scraper,
    workday_scraper,
)
from src.utils import parallel


def _job(company, suffix="job"):
    return {
        "company": company,
        "job_id": f"{company}-{suffix}",
        "title": f"{company} engineer",
    }


def _completion_order_parallel(completion_order):
    def fake_run_parallel(items, worker_fn, max_workers=10, desc="Processing"):
        assert Counter(items) == Counter(completion_order)
        results = []

        for item in completion_order:
            try:
                result = worker_fn(item)
            except Exception as exc:
                assert item == "failed", f"unexpected worker failure for {item}: {exc!r}"
                continue

            if result:
                results.extend(result)

        return results

    return fake_run_parallel


def _unexpected_request(*args, **kwargs):
    raise AssertionError("external request function must not be invoked")


def test_run_parallel_default_contract_still_flattens_and_isolates_failures(
    monkeypatch,
):
    monkeypatch.setattr(parallel, "tqdm", lambda iterable, **kwargs: iterable)

    def worker(company):
        if company == "failed":
            raise RuntimeError("fixture failure")
        if company == "empty":
            return []
        return [_job(company)]

    results = parallel.run_parallel(
        ["alpha", "failed", "empty", "omega"],
        worker,
        max_workers=2,
        desc="fixture",
    )

    assert sorted(job["company"] for job in results) == ["alpha", "omega"]
    assert all(isinstance(job, dict) for job in results)


@pytest.mark.parametrize(
    ("scraper", "entrypoint_name", "outcome_worker_name", "request_names"),
    [
        (
            workday_scraper,
            "scrape_all_workday",
            "_scrape_company_outcome",
            ("workday_post",),
        ),
        (
            workable_scraper,
            "scrape_all_workable",
            "_fetch_company_outcome",
            ("workable_get", "workable_post"),
        ),
        (
            jobvite_scraper,
            "scrape_all_jobvite",
            "_fetch_company_outcome",
            ("jobvite_get",),
        ),
    ],
    ids=["workday", "workable", "jobvite"],
)
def test_scheduled_scrapers_keep_company_results_under_reordered_completion(
    monkeypatch,
    scraper,
    entrypoint_name,
    outcome_worker_name,
    request_names,
):
    companies = ["alpha", "empty", "failed", "omega"]
    completion_order = ["omega", "failed", "empty", "alpha"]
    marked = []
    saved = []
    schedule = {}

    def worker(company):
        if company == "failed":
            raise RuntimeError("fixture failure")
        if company == "empty":
            return AcquisitionOutcome(company, AcquisitionStatus.EMPTY)
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.SUCCESS,
            (_job(company),),
        )

    monkeypatch.setattr(scraper, "load_lines", lambda path: list(companies))
    monkeypatch.setattr(scraper, "load_schedule", lambda: schedule)
    monkeypatch.setattr(scraper, "should_scrape", lambda company, value: True)
    monkeypatch.setattr(
        scraper,
        "mark_scraped",
        lambda company, value: marked.append((company, value)),
    )
    monkeypatch.setattr(scraper, "save_schedule", lambda value: saved.append(value))
    monkeypatch.setattr(scraper, outcome_worker_name, worker)
    monkeypatch.setattr(
        scraper,
        "run_parallel",
        _completion_order_parallel(completion_order),
    )
    for request_name in request_names:
        monkeypatch.setattr(scraper, request_name, _unexpected_request)

    results = getattr(scraper, entrypoint_name)()

    assert results == [_job("omega"), _job("alpha")]
    assert all(isinstance(job, dict) for job in results)
    assert [company for company, _ in marked] == ["omega", "empty", "alpha"]
    assert all(value is schedule for _, value in marked)
    assert saved == [schedule]


@pytest.mark.parametrize(
    ("scraper", "entrypoint_name", "outcome_worker_name", "deduplicates"),
    [
        (workday_scraper, "scrape_all_workday", "_scrape_company_outcome", False),
        (workable_scraper, "scrape_all_workable", "_fetch_company_outcome", True),
        (jobvite_scraper, "scrape_all_jobvite", "_fetch_company_outcome", True),
    ],
    ids=["workday", "workable", "jobvite"],
)
def test_scheduled_scraper_duplicate_behavior_is_unchanged(
    monkeypatch,
    scraper,
    entrypoint_name,
    outcome_worker_name,
    deduplicates,
):
    input_companies = ["alpha", "alpha", "omega"]
    completion_order = ["omega", "alpha"] if deduplicates else input_companies
    calls = []
    saved = []

    def worker(company):
        calls.append(company)
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.SUCCESS,
            (_job(company, str(len(calls))),),
        )

    monkeypatch.setattr(scraper, "load_lines", lambda path: list(input_companies))
    monkeypatch.setattr(scraper, "load_schedule", lambda: {})
    monkeypatch.setattr(scraper, "should_scrape", lambda company, schedule: True)
    monkeypatch.setattr(scraper, "mark_scraped", lambda company, schedule: None)
    monkeypatch.setattr(scraper, "save_schedule", lambda schedule: saved.append(schedule))
    monkeypatch.setattr(scraper, outcome_worker_name, worker)
    monkeypatch.setattr(
        scraper,
        "run_parallel",
        _completion_order_parallel(completion_order),
    )

    results = getattr(scraper, entrypoint_name)()

    assert Counter(job["company"] for job in results) == Counter(completion_order)
    assert Counter(calls) == Counter(completion_order)
    assert len(saved) == 1


def test_smartrecruiters_keeps_global_and_company_board_jobs(monkeypatch):
    input_companies = ["alpha", "alpha", "empty", "failed", "omega"]
    completion_order = ["omega", "failed", "empty", "alpha"]
    board_calls = []

    def fetch_feed(company):
        assert company is None
        return [_job("global")]

    def fetch_board(company):
        board_calls.append(company)
        if company == "failed":
            raise RuntimeError("fixture failure")
        if company == "empty":
            return []
        return [_job(company)]

    monkeypatch.setattr(
        smartrecruiters_scraper,
        "load_lines",
        lambda path: list(input_companies),
    )
    monkeypatch.setattr(smartrecruiters_scraper, "fetch_company_jobs", fetch_feed)
    monkeypatch.setattr(smartrecruiters_scraper, "fetch_company_board", fetch_board)
    monkeypatch.setattr(smartrecruiters_scraper, "http_get", _unexpected_request)
    monkeypatch.setattr(
        smartrecruiters_scraper,
        "run_parallel",
        _completion_order_parallel(completion_order),
    )

    results = smartrecruiters_scraper.scrape_all_smartrecruiters()

    assert results == [_job("global"), _job("omega"), _job("alpha")]
    assert all(isinstance(job, dict) for job in results)
    assert Counter(board_calls) == Counter(completion_order)
    assert board_calls.count("alpha") == 1


def test_ashby_default_flattened_usage_remains_compatible(monkeypatch):
    saved = []
    marked = []
    monkeypatch.setattr(parallel, "tqdm", lambda iterable, **kwargs: iterable)
    monkeypatch.setattr(
        ashby_scraper,
        "load_lines",
        lambda path: ["alpha", "alpha", "omega"],
    )
    monkeypatch.setattr(ashby_scraper, "load_schedule", lambda: {})
    monkeypatch.setattr(ashby_scraper, "should_scrape", lambda company, schedule: True)
    monkeypatch.setattr(
        ashby_scraper,
        "_fetch_company_outcome",
        lambda company: AcquisitionOutcome(
            company,
            AcquisitionStatus.SUCCESS,
            (_job(company),),
        ),
    )
    monkeypatch.setattr(ashby_scraper, "http_post", _unexpected_request)
    monkeypatch.setattr(
        ashby_scraper,
        "mark_scraped",
        lambda company, schedule: marked.append(company),
    )
    monkeypatch.setattr(ashby_scraper, "save_schedule", lambda schedule: saved.append(schedule))

    results = ashby_scraper.scrape_all_ashby()

    assert Counter(job["company"] for job in results) == Counter({"alpha": 1, "omega": 1})
    assert all(isinstance(job, dict) for job in results)
    assert Counter(marked) == Counter({"alpha": 1, "omega": 1})
    assert len(saved) == 1


def test_sitemap_discovery_parallel_caller_contract_remains_unchanged(monkeypatch):
    captured = {}

    def fake_run_parallel(items, worker_fn, max_workers=10, desc="Processing"):
        captured.update(
            items=list(items),
            worker_fn=worker_fn,
            max_workers=max_workers,
            desc=desc,
        )
        return [
            {"workday": {"alpha"}},
            {"workday": {"omega"}, "ashby": {"acme"}},
        ]

    monkeypatch.setattr(
        sitemap_discovery,
        "load_lines",
        lambda path: ["alpha.example", "omega.example"],
    )
    monkeypatch.setattr(sitemap_discovery, "run_parallel", fake_run_parallel)

    results = sitemap_discovery.run_sitemap_discovery()

    assert results == {"workday": {"alpha", "omega"}, "ashby": {"acme"}}
    assert captured == {
        "items": ["alpha.example", "omega.example"],
        "worker_fn": sitemap_discovery.discover_from_sitemap,
        "max_workers": 20,
        "desc": "Sitemap discovery",
    }
