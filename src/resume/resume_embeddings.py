import os
import json
import numpy as np
from tqdm import tqdm

from src.ai.embedding_model import get_model
from src.resume.resume_loader import load_resumes


CACHE_DIR = "data/resume_embeddings"
VECTOR_FILE = f"{CACHE_DIR}/vectors.npy"
NAME_FILE = f"{CACHE_DIR}/names.json"


def cache_exists():
    return os.path.exists(VECTOR_FILE) and os.path.exists(NAME_FILE)


def load_cache():

    vectors = np.load(VECTOR_FILE)

    with open(NAME_FILE) as f:
        names = json.load(f)

    return vectors, names


def save_cache(vectors, names):

    os.makedirs(CACHE_DIR, exist_ok=True)

    np.save(VECTOR_FILE, vectors)

    with open(NAME_FILE, "w") as f:
        json.dump(names, f)


def get_embedding_matrix(names=None):

    if cache_exists():
        print("Loaded resume embedding cache")
        return load_cache()

    model = get_model()

    resumes = load_resumes()

    embeddings = []
    names = []

    for r in tqdm(resumes, desc="Embedding resumes"):

        text = r["text"]
        name = r["resume_name"]

        vec = model.encode(text, normalize_embeddings=True)

        embeddings.append(vec)
        names.append(name)

    matrix = np.array(embeddings)

    save_cache(matrix, names)

    return matrix, names