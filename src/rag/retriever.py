from pathlib import Path
from typing import List, Dict, Any
from functools import lru_cache
from time import perf_counter

from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from src.utils.logging import get_logger

INDEX_DIR = Path("data/rag/index")
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"

@lru_cache(maxsize=1)
def _get_embed_model():
    return HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)


@lru_cache(maxsize=1)
def _load_index():
    Settings.embed_model = _get_embed_model()

    storage_context = StorageContext.from_defaults(
        persist_dir=str(INDEX_DIR)
    )
    return load_index_from_storage(storage_context)

@lru_cache(maxsize=8)
def get_retriever(top_k: int = 5):
    Settings.embed_model = _get_embed_model()
    index = _load_index()
    return index.as_retriever(similarity_top_k=top_k)


def retrieve_jobs(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    retriever = get_retriever(top_k=top_k)
    nodes = retriever.retrieve(query)

    results: List[Dict[str, Any]] = []

    for node in nodes:
        results.append(
            {
                "score": getattr(node, "score", None),
                "text": node.text,
                "metadata": node.metadata,
            }
        )

    return results


if __name__ == "__main__":
    query = "experimentation-heavy data science roles using looker and causal inference"
    results = retrieve_jobs(query, top_k=5)

    for i, item in enumerate(results, start=1):
        print(f"\nRESULT {i}")
        print(f"Score: {item['score']}")
        print(f"Metadata: {item['metadata']}")
        print(item["text"][:1000])