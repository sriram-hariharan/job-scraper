import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from src.utils.logging import get_logger

logger = get_logger("rag.corpus_store")

CORPUS_PATH = Path("data/rag/job_corpus.jsonl")


def _catalog_normalize(value: Any) -> str:
    return str(value or "").strip().lower()


@lru_cache(maxsize=1)
def _load_job_corpus() -> List[Dict[str, Any]]:
    if not CORPUS_PATH.exists():
        logger.warning("RAG lexical corpus missing | path=%s", CORPUS_PATH)
        return []

    docs: List[Dict[str, Any]] = []

    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))

    logger.info("RAG lexical corpus loaded | path=%s | docs=%s", CORPUS_PATH, len(docs))
    return docs


@lru_cache(maxsize=1)
def _build_metadata_catalog() -> Dict[str, Any]:
    docs = _load_job_corpus()

    companies: Dict[str, str] = {}
    sources: Dict[str, str] = {}
    titles: Dict[str, str] = {}
    role_families: Dict[str, str] = {}
    seniorities: Dict[str, str] = {}
    locations: Dict[str, str] = {}

    for doc in docs:
        company = str(doc.get("company") or "").strip()
        source = str(doc.get("source") or "").strip()
        title = str(doc.get("title") or "").strip()
        role_family = str(doc.get("role_family") or "").strip()
        seniority = str(doc.get("seniority") or "").strip()
        location = str(doc.get("location") or "").strip()

        if company:
            companies[_catalog_normalize(company)] = company

        if source:
            sources[_catalog_normalize(source)] = source

        if title:
            titles[_catalog_normalize(title)] = title

        if role_family:
            role_families[_catalog_normalize(role_family)] = role_family

        if seniority:
            seniorities[_catalog_normalize(seniority)] = seniority

        if location:
            locations[_catalog_normalize(location)] = location
            for part in [p.strip() for p in location.split(",") if p.strip()]:
                if len(part) >= 3:
                    locations[_catalog_normalize(part)] = part

    return {
        "companies": companies,
        "sources": sources,
        "titles": titles,
        "role_families": role_families,
        "seniorities": seniorities,
        "locations": locations,
    }