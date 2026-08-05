from copy import deepcopy

from src.pipeline import dedupe


ATTRIBUTION = {
    "provider_attribution_required": True,
    "provider_attribution_label": "Himalayas",
    "provider_attribution_url": "https://himalayas.app",
}


def _job(
    job_id,
    *,
    source="greenhouse",
    company="Acme",
    title="Backend Engineer",
    url=None,
    **extra,
):
    return {
        "job_id": job_id,
        "source": source,
        "company": company,
        "title": title,
        "url": url if url is not None else f"https://jobs.example/{job_id}",
        **extra,
    }


def test_direct_source_wins_title_duplicate_in_either_input_order():
    supplemental = _job("h1", source="himalayas", **ATTRIBUTION)
    direct = _job("d1", source="greenhouse")

    assert dedupe.dedupe_jobs([supplemental, direct]) == [direct]
    assert dedupe.dedupe_jobs([direct, supplemental]) == [direct]


def test_direct_source_replaces_supplemental_identity_at_original_position():
    supplemental = _job(
        "",
        source="himalayas",
        company="Supplemental name",
        title="Old title",
        url="https://jobs.example/shared",
        **ATTRIBUTION,
    )
    unrelated = _job("middle", company="Beta", title="Data Engineer")
    direct = _job(
        "",
        source="lever",
        company="Direct name",
        title="New title",
        url="https://jobs.example/shared",
    )

    result = dedupe.dedupe_jobs([supplemental, unrelated, direct])

    assert result == [direct, unrelated]
    assert not any("provider_attribution" in key for key in result[0])


def test_equal_priority_duplicates_preserve_first_wins():
    first_direct = _job("d1", source="greenhouse", marker="first")
    second_direct = _job("d2", source="lever", marker="second")
    first_supplemental = _job(
        "h1", source="himalayas", marker="first", **ATTRIBUTION
    )
    second_supplemental = _job(
        "h2", source="himalayas", marker="second", **ATTRIBUTION
    )

    assert dedupe.dedupe_jobs([first_direct, second_direct]) == [first_direct]
    assert dedupe.dedupe_jobs(
        [first_supplemental, second_supplemental]
    ) == [first_supplemental]


def test_unique_jobs_and_unrelated_order_are_unchanged():
    jobs = [
        _job("d1", company="Direct", title="API Engineer"),
        _job(
            "h1",
            source="himalayas",
            company="Supplemental",
            title="ML Engineer",
            **ATTRIBUTION,
        ),
        _job("d2", company="Other", title="Data Engineer"),
    ]

    assert dedupe.dedupe_jobs(jobs) == jobs


def test_missing_source_preserves_non_supplemental_first_wins_behavior():
    first = _job("first", source="")
    later = _job("later", source="greenhouse")

    assert dedupe.dedupe_jobs([first, later]) == [first]


def test_replacement_removes_stale_identity_and_title_ownership():
    supplemental = _job(
        "shared",
        source="himalayas",
        company="Acme",
        title="Old Engineer",
        **ATTRIBUTION,
    )
    direct = _job(
        "shared",
        source="lever",
        company="Acme",
        title="New Engineer",
    )
    old_title_is_now_unique = _job(
        "h2",
        source="himalayas",
        company="Acme",
        title="Old Engineer",
        **ATTRIBUTION,
    )
    duplicate_of_replacement = _job(
        "d2",
        source="greenhouse",
        company="Acme",
        title="New Engineer",
    )

    result = dedupe.dedupe_jobs(
        [supplemental, direct, old_title_is_now_unique, duplicate_of_replacement]
    )

    assert result == [direct, old_title_is_now_unique]


def test_input_records_are_not_mutated():
    jobs = [
        _job("h1", source="himalayas", **ATTRIBUTION),
        _job("d1", source="greenhouse"),
    ]
    before = deepcopy(jobs)

    dedupe.dedupe_jobs(jobs)

    assert jobs == before


def test_logging_is_bounded_to_counts(monkeypatch):
    supplemental = _job("h1", source="himalayas", **ATTRIBUTION)
    direct = _job("d1", source="greenhouse")
    messages = []

    class _Logger:
        def info(self, message, *args):
            messages.append(message % args if args else message)

    monkeypatch.setattr(dedupe, "logger", _Logger())

    dedupe.dedupe_jobs([supplemental, direct])

    assert any("Jobs before dedupe: 2" in message for message in messages)
    assert any("Jobs after dedupe: 1" in message for message in messages)
    assert any("Supplemental jobs replaced" in message for message in messages)
    assert all("https://" not in message for message in messages)
