from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

import numpy as np
from tqdm import tqdm


def _clean_text(value) -> str:
    return str(value or "").strip()


def cache_exists():
    return False


def load_cache():
    return None, []


def save_cache(vectors, names):
    return


def _requested_names(names: Optional[Iterable[str]]) -> List[str]:
    return [_clean_text(name) for name in list(names or []) if _clean_text(name)]


def get_embedding_matrix(names=None) -> Tuple[Optional[np.ndarray], List[str]]:
    from src.ai.embedding_model import get_model
    from src.resume.resume_loader import load_resumes, load_resumes_by_name

    requested_names = _requested_names(names)

    if requested_names:
        resumes = load_resumes_by_name(requested_names)
    else:
        resumes = load_resumes()

    if not resumes:
        return None, []

    model = get_model()

    embeddings = []
    resume_names = []

    for resume in tqdm(resumes, desc="Embedding resumes"):
        text = _clean_text(resume.get("text"))
        name = _clean_text(resume.get("resume_name"))

        if not text or not name:
            continue

        vec = model.encode(text, normalize_embeddings=True)

        embeddings.append(vec)
        resume_names.append(name)

    if not embeddings:
        return None, []

    matrix = np.array(embeddings)

    return matrix, resume_names
