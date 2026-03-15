import json
from pathlib import Path
from typing import List

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


CORPUS_PATH = Path("data/rag/job_corpus.jsonl")
INDEX_DIR = Path("data/rag/index")
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"


def load_job_documents(corpus_path: Path) -> List[Document]:
    documents: List[Document] = []

    with corpus_path.open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)

            metadata = {
                "doc_id": row.get("doc_id", ""),
                "company": row.get("company", ""),
                "title": row.get("title", ""),
                "location": row.get("location", ""),
                "source": row.get("source", ""),
                "job_url": row.get("job_url", ""),
                "posted_at": row.get("posted_at", ""),
                "role_family": row.get("role_family", ""),
                "seniority": row.get("seniority", ""),
                "required_skills": row.get("required_skills", []),
                "preferred_skills": row.get("preferred_skills", []),
                "all_skills": row.get("all_skills", []),
                "visa_sponsorship": row.get("visa_sponsorship", ""),
                "ai_fit_score": row.get("ai_fit_score"),
            }

            documents.append(
                Document(
                    text=row.get("retrieval_text", ""),
                    metadata=metadata,
                    doc_id=row.get("doc_id", ""),
                )
            )

    return documents


def build_rag_index(
    corpus_path: Path = CORPUS_PATH,
    index_dir: Path = INDEX_DIR,
) -> int:
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")

    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)

    documents = load_job_documents(corpus_path)
    index = VectorStoreIndex.from_documents(documents)

    index_dir.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(index_dir))

    return len(documents)


if __name__ == "__main__":
    count = build_rag_index()
    print(f"RAG index built for {count} documents")