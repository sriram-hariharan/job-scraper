import time
from functools import lru_cache
from typing import Any, Dict, List

from src.storage.rag_store import _rag_cache_ttl_seconds, get_rag_job_documents
from src.utils.logging import get_logger

logger = get_logger("rag.corpus_store")


def _catalog_normalize(value: Any) -> str:
    return str(value or "").strip().lower()


@lru_cache(maxsize=1)
def _load_job_corpus_cached() -> List[Dict[str, Any]]:
    docs = get_rag_job_documents()
    logger.info("RAG lexical corpus loaded from Postgres | docs=%s", len(docs))
    return docs


# Process-level cache state. Without this, the unbounded lru_cache sat above the
# Redis TTL and its explicit invalidation, so a long-running API process kept
# serving the corpus it first loaded and never observed newly ingested jobs.
# The in-process cache now expires on the same TTL the Redis layer already uses,
# so caching and its performance benefit are preserved while staleness stays
# bounded by existing configuration.
_CORPUS_CACHE_STATE: Dict[str, float] = {"loaded_at": 0.0}


def _corpus_cache_expired(now: float) -> bool:
    loaded_at = _CORPUS_CACHE_STATE.get("loaded_at", 0.0)
    if not loaded_at:
        return False
    return (now - loaded_at) >= _rag_cache_ttl_seconds()


def reset_job_corpus_cache() -> None:
    """Drop the in-process corpus and catalog caches."""
    _load_job_corpus_cached.cache_clear()
    _build_metadata_catalog.cache_clear()
    _CORPUS_CACHE_STATE["loaded_at"] = 0.0


def _load_job_corpus() -> List[Dict[str, Any]]:
    now = time.monotonic()

    if _corpus_cache_expired(now):
        logger.info("RAG lexical corpus cache expired; reloading")
        reset_job_corpus_cache()

    docs = _load_job_corpus_cached()

    if not _CORPUS_CACHE_STATE.get("loaded_at"):
        _CORPUS_CACHE_STATE["loaded_at"] = now

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
        metadata = doc.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        company = str(doc.get("company") or metadata.get("company") or "").strip()
        source = str(doc.get("source") or metadata.get("source") or "").strip()
        title = str(doc.get("title") or metadata.get("title") or "").strip()
        role_family = str(doc.get("role_family") or metadata.get("role_family") or "").strip()
        seniority = str(doc.get("seniority") or metadata.get("seniority") or "").strip()
        location = str(doc.get("location") or metadata.get("location") or "").strip()

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
