"""
Manual curated ATS source seed loader.

Run from the repo root:
    PYTHONPATH="$PWD" python -m src.discovery.curated_ats_sources
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Set

from src.utils.logging import get_logger

logger = get_logger("curated_ats_sources")

DEFAULT_CURATED_ATS_SOURCES_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "config"
    / "curated_ats_sources.json"
)

ValidatorMap = Mapping[str, Callable[[Iterable[str]], Iterable[str]]]
ExistingFunc = Callable[[str], Set[str]]
UpsertFunc = Callable[[str, Iterable[str]], int]


def _clean_text(value) -> str:
    return str(value or "").strip()


def _normalize_slug(value) -> str:
    return _clean_text(value).lower()


def _dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    normalized: List[str] = []
    for value in values:
        slug = _normalize_slug(value)
        if slug and slug not in seen:
            seen.add(slug)
            normalized.append(slug)
    return normalized


def load_curated_ats_sources(path: Optional[Path | str] = None) -> Dict[str, List[str]]:
    config_path = Path(path or DEFAULT_CURATED_ATS_SOURCES_PATH)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Curated ATS source config must be a JSON object.")

    normalized: Dict[str, List[str]] = {}
    for ats, values in payload.items():
        safe_ats = _normalize_slug(ats)
        if not safe_ats:
            continue
        if not isinstance(values, list):
            raise ValueError(f"Curated ATS source list for {safe_ats!r} must be a list.")
        normalized[safe_ats] = _dedupe_preserve_order(values)

    return normalized


def _default_validators() -> Dict[str, Callable[[Iterable[str]], Iterable[str]]]:
    from src.discovery.greenhouse_api_discovery import validate_greenhouse_companies
    from src.scrapers.lever_scraper import validate_lever_companies

    return {
        "greenhouse": validate_greenhouse_companies,
        "lever": validate_lever_companies,
    }


def _default_existing_func(ats: str) -> Set[str]:
    from src.storage.discovery_store import get_discovered_ats_companies

    return {
        _normalize_slug(company)
        for company in get_discovered_ats_companies(ats)
        if _normalize_slug(company)
    }


def _default_upsert_func(ats: str, companies: Iterable[str]) -> int:
    from src.storage.discovery_store import upsert_discovered_ats_companies

    return upsert_discovered_ats_companies(
        ats,
        companies,
        source="curated_ats_sources",
    )


def seed_curated_ats_sources(
    *,
    path: Optional[Path | str] = None,
    validators: Optional[ValidatorMap] = None,
    existing_func: Optional[ExistingFunc] = None,
    upsert_func: Optional[UpsertFunc] = None,
) -> Dict[str, Dict[str, object]]:
    config = load_curated_ats_sources(path)
    validator_map = dict(_default_validators() if validators is None else validators)
    load_existing = existing_func or _default_existing_func
    upsert = upsert_func or _default_upsert_func

    summary: Dict[str, Dict[str, object]] = {}

    for ats in sorted(config):
        candidates = config[ats]
        if ats not in validator_map:
            summary[ats] = {
                "status": "skipped_unsupported_ats",
                "candidate_count": len(candidates),
                "valid_count": 0,
                "existing_count": 0,
                "inserted_count": 0,
                "invalid": candidates,
            }
            logger.info(
                "%s curated ATS seed skipped: unsupported ats | candidates=%s",
                ats,
                len(candidates),
            )
            continue

        valid = set(_dedupe_preserve_order(validator_map[ats](candidates)))
        existing = load_existing(ats)
        to_insert = sorted(valid - existing)
        inserted_count = upsert(ats, to_insert) if to_insert else 0
        invalid = sorted(set(candidates) - valid)

        summary[ats] = {
            "status": "seeded",
            "candidate_count": len(candidates),
            "valid_count": len(valid),
            "existing_count": len(valid & existing),
            "inserted_count": inserted_count,
            "invalid": invalid,
        }
        logger.info(
            "%s curated ATS seed complete | candidates=%s valid=%s existing=%s inserted=%s invalid=%s",
            ats,
            len(candidates),
            len(valid),
            len(valid & existing),
            inserted_count,
            len(invalid),
        )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and load curated ATS source seeds.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CURATED_ATS_SOURCES_PATH),
        help="Path to curated ATS source JSON config.",
    )
    args = parser.parse_args()

    summary = seed_curated_ats_sources(path=args.config)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
