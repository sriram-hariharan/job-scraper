import os
from pathlib import Path
from typing import List

from llama_index.core import Document

from src.storage.rag_store import get_rag_job_documents

EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"


def _legacy_rag_index_enabled() -> bool:
    return str(os.environ.get("JOB_STACK_ENABLE_LEGACY_RAG_INDEX", "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def load_job_documents(corpus_path: Path | None = None) -> List[Document]:
    documents: List[Document] = []

    for row in get_rag_job_documents():
        metadata = row.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        documents.append(
            Document(
                text=row.get("retrieval_text", "") or row.get("text", ""),
                metadata=metadata,
                doc_id=row.get("doc_id", ""),
            )
        )

    return documents


def build_rag_index(
    corpus_path: Path | None = None,
    index_dir: Path | None = None,
) -> int:
    if not _legacy_rag_index_enabled():
        raise RuntimeError(
            "Legacy filesystem RAG index is disabled. "
            "Use Postgres-backed RAG corpus now; semantic vector index will move to pgvector/vector DB in 6B.16."
        )

    from llama_index.core import Settings, VectorStoreIndex
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    target_index_dir = index_dir or Path(os.environ.get("JOB_STACK_LEGACY_RAG_INDEX_DIR", "data/rag/index"))

    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)

    documents = load_job_documents(corpus_path)
    index = VectorStoreIndex.from_documents(documents)

    target_index_dir.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(target_index_dir))

    return len(documents)


if __name__ == "__main__":
    count = build_rag_index()
    print(f"RAG index built for {count} documents")
