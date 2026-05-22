import sys
import types
from datetime import datetime, timedelta, timezone


class _FakeTqdm:
    def __call__(self, iterable=None, **kwargs):
        return iterable

    @staticmethod
    def write(*args, **kwargs):
        return None


sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))
sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=_FakeTqdm()))
sys.modules.setdefault(
    "src.utils.workday_timestamp",
    types.SimpleNamespace(fetch_workday_timestamp=lambda *args, **kwargs: None),
)
from src.pipeline import job_filter
from src.config.consts import USER_PIPELINE_UNKNOWN_TIMESTAMP_JOB_CAP


def _fresh_timestamp():
    return datetime.now(timezone.utc).isoformat()


def _ashby_job(**overrides):
    job = {
        "company": "plaid",
        "title": "Backend Engineer",
        "location": "Remote",
        "source": "ashby",
        "posted_at": None,
        "url": "https://jobs.ashbyhq.com/plaid/posting-123",
    }
    job.update(overrides)
    return job


def _stale_timestamp():
    return (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()


def test_ashby_job_with_meta_job_id_gets_timestamp_hydrated(monkeypatch):
    calls = []

    def fake_fetch_ashby_timestamp_result(company, job_id):
        calls.append((company, job_id))
        return {"posted_at": _fresh_timestamp(), "marker": "", "status_code": 200}

    monkeypatch.setattr(job_filter, "fetch_ashby_timestamp_result", fake_fetch_ashby_timestamp_result)

    jobs = [_ashby_job(meta={"_job_id": "posting-123"})]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
    )

    assert calls == [("plaid", "posting-123")]
    assert filtered == jobs
    assert jobs[0]["posted_at"]


def test_ashby_job_with_top_level_job_id_still_gets_timestamp_hydrated(monkeypatch):
    calls = []

    def fake_fetch_ashby_timestamp_result(company, job_id):
        calls.append((company, job_id))
        return {"posted_at": _fresh_timestamp(), "marker": "", "status_code": 200}

    monkeypatch.setattr(job_filter, "fetch_ashby_timestamp_result", fake_fetch_ashby_timestamp_result)

    jobs = [_ashby_job(_job_id="posting-456")]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
    )

    assert calls == [("plaid", "posting-456")]
    assert filtered == jobs
    assert jobs[0]["posted_at"]


def test_ashby_job_id_falls_back_to_prefixed_public_job_id(monkeypatch):
    calls = []

    def fake_fetch_ashby_timestamp_result(company, job_id):
        calls.append((company, job_id))
        return {"posted_at": _fresh_timestamp(), "marker": "", "status_code": 200}

    monkeypatch.setattr(job_filter, "fetch_ashby_timestamp_result", fake_fetch_ashby_timestamp_result)

    jobs = [_ashby_job(job_id="as_posting-789")]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
    )

    assert calls == [("plaid", "posting-789")]
    assert filtered == jobs


def test_ashby_job_with_no_id_remains_rejected_without_posted_at(monkeypatch):
    calls = []
    monkeypatch.setattr(
        job_filter,
        "fetch_ashby_timestamp_result",
        lambda company, job_id: calls.append((company, job_id)) or {
            "posted_at": _fresh_timestamp(),
            "marker": "",
            "status_code": 200,
        },
    )

    jobs = [_ashby_job()]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
    )

    assert calls == []
    assert filtered == []


def test_non_ashby_missing_posted_at_behavior_is_unchanged(monkeypatch):
    calls = []
    monkeypatch.setattr(
        job_filter,
        "fetch_ashby_timestamp_result",
        lambda company, job_id: calls.append((company, job_id)) or {
            "posted_at": _fresh_timestamp(),
            "marker": "",
            "status_code": 200,
        },
    )

    jobs = [
        {
            "company": "Acme",
            "title": "Data Scientist",
            "location": "United States",
            "source": "greenhouse",
            "posted_at": None,
        }
    ]

    assert job_filter.filter_jobs(jobs) == []
    assert calls == []


def test_transient_ashby_timestamp_failure_then_success_passes(monkeypatch):
    calls = []

    def fake_fetch_ashby_timestamp_result(company, job_id):
        calls.append((company, job_id))
        return {"posted_at": _fresh_timestamp(), "marker": "", "status_code": 200}

    monkeypatch.setattr(job_filter, "fetch_ashby_timestamp_result", fake_fetch_ashby_timestamp_result)

    jobs = [_ashby_job(meta={"_job_id": "posting-123"})]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
    )

    assert calls == [("plaid", "posting-123")]
    assert filtered == jobs


def test_repeated_ashby_timestamp_failure_is_rejected(monkeypatch):
    calls = []

    def fake_fetch_ashby_timestamp_result(company, job_id):
        calls.append((company, job_id))
        return {
            "posted_at": None,
            "marker": "ashby_timestamp_request_failed",
            "status_code": 500,
        }

    monkeypatch.setattr(job_filter, "fetch_ashby_timestamp_result", fake_fetch_ashby_timestamp_result)

    jobs = [_ashby_job(meta={"_job_id": "posting-123"})]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
    )

    assert calls == [("plaid", "posting-123")]
    assert filtered == []
    assert jobs[0]["_ashby_timestamp_status"] == "ashby_timestamp_request_failed"


def test_user_pipeline_mode_allows_ashby_missing_timestamp_after_title_and_us_location(monkeypatch):
    monkeypatch.setattr(
        job_filter,
        "fetch_ashby_timestamp_result",
        lambda company, job_id: {
            "posted_at": None,
            "marker": "ashby_timestamp_request_failed",
            "status_code": 500,
        },
    )

    jobs = [_ashby_job(meta={"_job_id": "posting-123"})]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
        filter_mode="user_pipeline",
    )

    assert filtered == jobs
    assert jobs[0]["_ashby_timestamp_status"] == "ashby_timestamp_request_failed"
    assert jobs[0]["_freshness_status"] == "unknown_timestamp_allowed"


def test_user_pipeline_mode_does_not_allow_missing_timestamp_for_non_us_location(monkeypatch):
    monkeypatch.setattr(
        job_filter,
        "fetch_ashby_timestamp_result",
        lambda company, job_id: {"posted_at": None, "marker": "missing"},
    )

    jobs = [_ashby_job(location="London", meta={"_job_id": "posting-123"})]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
        filter_mode="user_pipeline",
    )

    assert filtered == []


def test_user_pipeline_mode_does_not_allow_missing_timestamp_for_title_mismatch(monkeypatch):
    monkeypatch.setattr(
        job_filter,
        "fetch_ashby_timestamp_result",
        lambda company, job_id: {"posted_at": None, "marker": "missing"},
    )

    jobs = [_ashby_job(title="Product Manager", meta={"_job_id": "posting-123"})]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
        filter_mode="user_pipeline",
    )

    assert filtered == []


def test_user_pipeline_mode_unknown_timestamp_cap_is_stable(monkeypatch):
    monkeypatch.setattr(
        job_filter,
        "fetch_ashby_timestamp_result",
        lambda company, job_id: {"posted_at": None, "marker": "missing"},
    )

    jobs = [
        _ashby_job(
            title="Backend Engineer",
            meta={"_job_id": f"posting-{index}"},
            url=f"https://jobs.ashbyhq.com/plaid/posting-{index}",
        )
        for index in range(USER_PIPELINE_UNKNOWN_TIMESTAMP_JOB_CAP + 5)
    ]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
        filter_mode="user_pipeline",
    )

    assert len(filtered) == USER_PIPELINE_UNKNOWN_TIMESTAMP_JOB_CAP
    assert filtered == jobs[:USER_PIPELINE_UNKNOWN_TIMESTAMP_JOB_CAP]
    assert all(job["_freshness_status"] == "unknown_timestamp_allowed" for job in filtered)


def test_default_mode_keeps_not_recent_behavior_strict(monkeypatch):
    monkeypatch.setattr(
        job_filter,
        "fetch_ashby_timestamp_result",
        lambda company, job_id: {"posted_at": _stale_timestamp(), "marker": ""},
    )

    jobs = [_ashby_job(meta={"_job_id": "posting-123"})]

    filtered = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
    )

    assert filtered == []
