from typing import List, Dict, Any
from collections import Counter


def detect_hot_companies(jobs: List[Dict[str, Any]], top_n: int = 10):

    company_counts = Counter()

    for job in jobs:
        company = job.get("company")
        if company:
            company_counts[company] += 1

    return company_counts.most_common(top_n)


def detect_ai_hiring_surges(jobs: List[Dict[str, Any]], top_n: int = 10):

    ai_keywords = [
        "llm",
        "transformer",
        "pytorch",
        "deep learning",
        "machine learning",
        "foundation model",
        "generative ai",
    ]

    company_scores = Counter()

    for job in jobs:

        desc = (job.get("description") or "").lower()
        company = job.get("company")

        if not company:
            continue

        for kw in ai_keywords:
            if kw in desc:
                company_scores[company] += 1

    return company_scores.most_common(top_n)


def detect_emerging_tech(jobs: List[Dict[str, Any]], top_n: int = 15):

    tech_keywords = [
        "pytorch",
        "tensorflow",
        "jax",
        "ray",
        "vllm",
        "langchain",
        "langgraph",
        "huggingface",
        "transformers",
        "vector database",
        "pinecone",
        "weaviate",
        "pgvector",
        "milvus",
    ]

    tech_counts = Counter()

    for job in jobs:

        desc = (job.get("description") or "").lower()

        for kw in tech_keywords:
            if kw in desc:
                tech_counts[kw] += 1

    return tech_counts.most_common(top_n)