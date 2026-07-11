"""Deterministic JD/resume similarity diagnostics.

This module is intentionally dependency-free and diagnostic-only. It does not
participate in match scoring, ranking, queue behavior, or provider calls.
"""

from __future__ import annotations

from collections import Counter
import math
import re
from typing import Iterable


METHOD = "deterministic_token_cosine"
CODE = "jd_resume_semantic_similarity"

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)?")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "their",
    "this",
    "to",
    "with",
    "you",
    "your",
}


def _normalize_token(token: str) -> str:
    return token.lower().replace("_", "-").strip("-")


def _tokens(text: str | None) -> list[str]:
    raw_tokens = (_normalize_token(match.group(0)) for match in _TOKEN_RE.finditer(text or ""))
    return [
        token
        for token in raw_tokens
        if token and len(token) > 1 and token not in _STOPWORDS
    ]


def _counter(tokens: Iterable[str]) -> Counter[str]:
    return Counter(tokens)


def token_cosine_similarity(left: str | None, right: str | None) -> float:
    """Return a deterministic token cosine similarity bounded to ``0.0..1.0``."""
    left_counts = _counter(_tokens(left))
    right_counts = _counter(_tokens(right))

    if not left_counts or not right_counts:
        return 0.0

    shared = set(left_counts) & set(right_counts)
    dot_product = sum(left_counts[token] * right_counts[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
    right_norm = math.sqrt(sum(value * value for value in right_counts.values()))

    if not left_norm or not right_norm:
        return 0.0

    similarity = dot_product / (left_norm * right_norm)
    return round(max(0.0, min(1.0, similarity)), 6)


def build_semantic_similarity_diagnostic(
    job_text: str | None,
    resume_text: str | None,
) -> dict[str, object]:
    """Build a read-only semantic-style similarity diagnostic for a JD/resume pair."""
    similarity = token_cosine_similarity(job_text, resume_text)
    return {
        "code": CODE,
        "similarity": similarity,
        "method": METHOD,
        "score_impact": False,
    }
