import os
from functools import lru_cache
from pathlib import Path
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    if os.getenv("VERCEL") == "1":
        bundled = Path(__file__).resolve().parents[2] / "model_assets/embeddings"
        if not (bundled / "modules.json").is_file():
            raise RuntimeError("Bundled embedding model missing; run the configured Vercel build command.")
        return SentenceTransformer(str(bundled), local_files_only=True, device="cpu")
    model_name = os.getenv("DISCOVERY_EMBEDDING_MODEL", DEFAULT_MODEL_NAME)
    return SentenceTransformer(model_name)


def create_embeddings(texts: List[str]):
    return get_embedding_model().encode(texts)


def rank_by_similarity(query: str, texts: List[str]) -> List[float]:
    """Cosine similarity between query and each text, clipped to [0, 1].

    Shared by every external dataset source (Kaggle, OpenML, HuggingFace) so
    they all score against a comparable 0-1 scale, the same one the local
    catalog's FAISS search effectively produces via vector_store.py.
    """
    if not texts:
        return []

    vectors = np.array(create_embeddings([query, *texts]))
    query_vector, text_vectors = vectors[0], vectors[1:]
    query_norm = query_vector / max(float(np.linalg.norm(query_vector)), 1e-12)

    similarities = []
    for vector in text_vectors:
        vector_norm = vector / max(float(np.linalg.norm(vector)), 1e-12)
        similarities.append(max(0.0, min(1.0, float(np.dot(query_norm, vector_norm)))))
    return similarities
