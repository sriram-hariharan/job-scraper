import json
from pathlib import Path

from src.discovery.curated_ats_sources import (
    load_curated_ats_sources,
    seed_curated_ats_sources,
)


def _write_config(tmp_path, payload):
    path = Path(tmp_path) / "curated_ats_sources.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_curated_ats_sources_normalizes_and_dedupes(tmp_path):
    path = _write_config(
        tmp_path,
        {
            "Greenhouse": ["ScaleAI", "scaleai", " anthropic "],
            "lever": ["field-ai"],
        },
    )

    assert load_curated_ats_sources(path) == {
        "greenhouse": ["scaleai", "anthropic"],
        "lever": ["field-ai"],
    }


def test_seed_curated_ats_sources_validates_and_inserts_only_new_valid_sources(tmp_path):
    path = _write_config(
        tmp_path,
        {
            "greenhouse": ["scaleai", "bad-gh", "anthropic"],
            "lever": ["field-ai", "bad-lever"],
        },
    )
    inserted = []

    summary = seed_curated_ats_sources(
        path=path,
        validators={
            "greenhouse": lambda slugs: {"scaleai", "anthropic"},
            "lever": lambda slugs: {"field-ai"},
        },
        existing_func=lambda ats: {"scaleai"} if ats == "greenhouse" else set(),
        upsert_func=lambda ats, companies: inserted.append((ats, list(companies))) or len(list(companies)),
    )

    assert inserted == [
        ("greenhouse", ["anthropic"]),
        ("lever", ["field-ai"]),
    ]
    assert summary["greenhouse"]["inserted_count"] == 1
    assert summary["greenhouse"]["existing_count"] == 1
    assert summary["greenhouse"]["invalid"] == ["bad-gh"]
    assert summary["lever"]["inserted_count"] == 1
    assert summary["lever"]["invalid"] == ["bad-lever"]


def test_seed_curated_ats_sources_skips_invalid_without_crashing(tmp_path):
    path = _write_config(tmp_path, {"greenhouse": ["bad-gh"]})
    inserted = []

    summary = seed_curated_ats_sources(
        path=path,
        validators={"greenhouse": lambda slugs: set()},
        existing_func=lambda ats: set(),
        upsert_func=lambda ats, companies: inserted.append((ats, list(companies))) or len(list(companies)),
    )

    assert inserted == []
    assert summary["greenhouse"]["inserted_count"] == 0
    assert summary["greenhouse"]["invalid"] == ["bad-gh"]


def test_seed_curated_ats_sources_skips_duplicates_already_in_storage(tmp_path):
    path = _write_config(tmp_path, {"lever": ["field-ai", "field-ai"]})
    inserted = []

    summary = seed_curated_ats_sources(
        path=path,
        validators={"lever": lambda slugs: {"field-ai"}},
        existing_func=lambda ats: {"field-ai"},
        upsert_func=lambda ats, companies: inserted.append((ats, list(companies))) or len(list(companies)),
    )

    assert inserted == []
    assert summary["lever"]["candidate_count"] == 1
    assert summary["lever"]["existing_count"] == 1
    assert summary["lever"]["inserted_count"] == 0


def test_seed_curated_ats_sources_skips_unsupported_ats(tmp_path):
    path = _write_config(tmp_path, {"unknownats": ["example"]})
    inserted = []

    summary = seed_curated_ats_sources(
        path=path,
        validators={},
        existing_func=lambda ats: set(),
        upsert_func=lambda ats, companies: inserted.append((ats, list(companies))) or len(list(companies)),
    )

    assert inserted == []
    assert summary["unknownats"]["status"] == "skipped_unsupported_ats"
    assert summary["unknownats"]["invalid"] == ["example"]
