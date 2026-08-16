import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import faiss
import numpy as np

from .embeddings import create_embeddings

DATASETS_PATH = Path(__file__).parent / "datasets.json"


@lru_cache(maxsize=1)
def load_datasets() -> List[Dict]:
    with open(DATASETS_PATH, "r", encoding="utf-8") as datasets_file:
        return json.load(datasets_file)


@lru_cache(maxsize=1)
def build_index() -> faiss.IndexFlatL2:
    descriptions = [dataset["description"] for dataset in load_datasets()]
    vectors = np.array(create_embeddings(descriptions)).astype("float32")
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)
    return index


def search_vectors(query: str, k: int = 3) -> List[Dict]:
    datasets = load_datasets()
    index = build_index()
    k = min(k, len(datasets))

    query_vector = np.array(create_embeddings([query])).astype("float32")
    distances, indices = index.search(query_vector, k)

    results = []
    for distance, position in zip(distances[0], indices[0]):
        # Convert L2 distance to a 0-1 similarity score (higher = more similar).
        similarity = float(1 / (1 + distance))
        results.append({**datasets[position], "similarity": similarity})
    return results
