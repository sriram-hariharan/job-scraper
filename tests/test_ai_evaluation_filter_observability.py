from src.intelligence.job_intelligence import (
    SKIPPED_NO_DESCRIPTION,
    ai_evaluation_skip_summary,
    filter_jobs_for_ai_evaluation,
)


def test_empty_description_job_gets_structured_ai_evaluation_skip_metadata():
    jobs = [
        {
            "company": "Acme",
            "title": "Backend Engineer",
            "url": "https://example.com/backend",
            "source": "LinkedIn",
            "description_text": "   ",
        }
    ]

    evaluable_jobs = filter_jobs_for_ai_evaluation(jobs)

    assert evaluable_jobs == []
    skipped = jobs[0]
    assert skipped["ai_fit"] == SKIPPED_NO_DESCRIPTION
    assert skipped["ai_evaluation_skip_reason"] == SKIPPED_NO_DESCRIPTION
    assert skipped["ai_evaluation_skip_stage"] == "ai_evaluation_filter"
    assert skipped["ai_evaluation_skip_company"] == "Acme"
    assert skipped["ai_evaluation_skip_title"] == "Backend Engineer"
    assert skipped["ai_evaluation_skip_url"] == "https://example.com/backend"
    assert skipped["ai_evaluation_skip_source"] == "LinkedIn"
    assert skipped["ai_evaluation_skip_metadata"] == {
        "company": "Acme",
        "title": "Backend Engineer",
        "url": "https://example.com/backend",
        "source": "LinkedIn",
        "reason": SKIPPED_NO_DESCRIPTION,
        "stage": "ai_evaluation_filter",
        "message": "Job description missing",
    }


def test_ai_evaluation_skip_summary_includes_job_identity_and_reason_counts():
    jobs = [
        {
            "company": "Beta",
            "title": "QA Automation Engineer",
            "job_url": "https://example.com/qa",
            "source": "Indeed",
            "description_text": "",
        },
        {
            "company": "Acme",
            "title": "Data Engineer",
            "url": "https://example.com/data",
            "platform": "Greenhouse",
            "description_text": None,
        },
    ]

    filter_jobs_for_ai_evaluation(jobs)
    summary = ai_evaluation_skip_summary(jobs)

    assert summary["skipped_count"] == 2
    assert summary["reason_counts"] == {SKIPPED_NO_DESCRIPTION: 2}
    assert summary["skipped_jobs"] == [
        {
            "company": "Beta",
            "title": "QA Automation Engineer",
            "url": "https://example.com/qa",
            "source": "Indeed",
            "reason": SKIPPED_NO_DESCRIPTION,
        },
        {
            "company": "Acme",
            "title": "Data Engineer",
            "url": "https://example.com/data",
            "source": "Greenhouse",
            "reason": SKIPPED_NO_DESCRIPTION,
        },
    ]
    assert summary["skipped_samples"] == summary["skipped_jobs"]


def test_ai_evaluation_skipped_samples_are_capped_at_10():
    jobs = [
        {
            "company": f"Company {index:02d}",
            "title": f"Backend Engineer {index:02d}",
            "url": f"https://example.com/jobs/{index:02d}",
            "source": "TestSource",
            "description_text": "",
        }
        for index in range(12)
    ]

    filter_jobs_for_ai_evaluation(jobs)
    summary = ai_evaluation_skip_summary(jobs)

    assert summary["skipped_count"] == 12
    assert summary["reason_counts"] == {SKIPPED_NO_DESCRIPTION: 12}
    assert len(summary["skipped_samples"]) == 10
    assert summary["skipped_samples"][0] == {
        "company": "Company 00",
        "title": "Backend Engineer 00",
        "url": "https://example.com/jobs/00",
        "source": "TestSource",
        "reason": SKIPPED_NO_DESCRIPTION,
    }
    assert summary["skipped_samples"][-1]["company"] == "Company 09"


def test_job_with_description_remains_evaluable_without_skip_metadata():
    jobs = [
        {
            "company": "Gamma",
            "title": "Frontend Engineer",
            "url": "https://example.com/frontend",
            "description_text": "Build accessible React interfaces.",
            "ai_evaluation_skip_reason": SKIPPED_NO_DESCRIPTION,
            "ai_evaluation_skip_stage": "ai_evaluation_filter",
            "ai_evaluation_skip_metadata": {"reason": SKIPPED_NO_DESCRIPTION},
        }
    ]

    evaluable_jobs = filter_jobs_for_ai_evaluation(jobs)

    assert evaluable_jobs == jobs
    assert "ai_evaluation_skip_reason" not in jobs[0]
    assert "ai_evaluation_skip_stage" not in jobs[0]
    assert "ai_evaluation_skip_company" not in jobs[0]
    assert "ai_evaluation_skip_title" not in jobs[0]
    assert "ai_evaluation_skip_url" not in jobs[0]
    assert "ai_evaluation_skip_source" not in jobs[0]
    assert "ai_evaluation_skip_metadata" not in jobs[0]
    assert ai_evaluation_skip_summary(jobs) == {
        "skipped_count": 0,
        "reason_counts": {},
        "skipped_jobs": [],
        "skipped_samples": [],
    }
