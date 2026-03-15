import json
from pathlib import Path
from typing import List, Dict, Any

from src.rag.job_document_builder import build_job_document


def export_job_corpus(jobs: List[Dict[str, Any]], output_path: str) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0

    with path.open("w", encoding="utf-8") as f:
        for job in jobs:
            doc = build_job_document(job)
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            count += 1

    return count