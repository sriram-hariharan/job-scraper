from pathlib import Path

from src.config import consts
from src.discovery import curated_ats_sources


ROOT = Path(__file__).resolve().parents[1]


def test_personio_active_source_is_retired():
    assert not (ROOT / "src/scrapers/personio_scraper.py").exists()

    collector_source = (ROOT / "src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )
    assert "personio_scraper" not in collector_source
    assert "scrape_all_personio" not in collector_source
    assert '("personio",' not in collector_source

    validator_source = (ROOT / "src/discovery/curated_ats_sources.py").read_text(
        encoding="utf-8"
    )
    assert "validate_personio" not in validator_source
    assert "personio" not in curated_ats_sources._default_validators()
    assert "personio" not in curated_ats_sources.load_curated_ats_sources()
    assert not hasattr(consts, "PERSONIO_XML_URL")

    for production_path in (ROOT / "src").rglob("*.py"):
        source = production_path.read_text(encoding="utf-8")
        assert "src.scrapers.personio_scraper" not in source
        assert "import personio_scraper" not in source
