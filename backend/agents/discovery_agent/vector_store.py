from typing import Dict, List, Optional

import faiss
import numpy as np

from security.db import SessionLocal
from security.db_models import CatalogDataset

from .embeddings import create_embeddings

# Both caches are invalidated together — the FAISS index is built from the
# dataset list, so a stale dataset list means a stale index regardless of
# which one actually changed.
_datasets_cache: Optional[List[Dict]] = None
_index_cache: Optional[faiss.IndexFlatL2] = None


def invalidate_cache() -> None:
    """Call after any write to the catalog (admin add/edit/delete via
    /admin/catalog) so the next search rebuilds against current data
    instead of serving a FAISS index built from what the catalog used to
    contain. Without this, an admin's edit would silently never show up in
    search results until the server happened to restart."""
    global _datasets_cache, _index_cache
    _datasets_cache = None
    _index_cache = None


def load_datasets() -> List[Dict]:
    global _datasets_cache
    if _datasets_cache is None:
        db = SessionLocal()
        try:
            rows = db.query(CatalogDataset).order_by(CatalogDataset.created_at).all()
            _datasets_cache = [
                {
                    "id": row.id,
                    "name": row.name,
                    "description": row.description,
                    "domain": row.domain,
                    "task": row.task,
                    "url": row.url,
                }
                for row in rows
            ]
        finally:
            db.close()
    return _datasets_cache


def build_index() -> Optional[faiss.IndexFlatL2]:
    global _index_cache
    if _index_cache is None:
        datasets = load_datasets()
        if not datasets:
            return None
        descriptions = [dataset["description"] for dataset in datasets]
        vectors = np.array(create_embeddings(descriptions)).astype("float32")
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)
        _index_cache = index
    return _index_cache


def search_vectors(query: str, k: int = 3) -> List[Dict]:
    datasets = load_datasets()
    index = build_index()
    k = min(k, len(datasets))
    if k == 0 or index is None:
        return []

    query_vector = np.array(create_embeddings([query])).astype("float32")
    distances, indices = index.search(query_vector, k)

    results = []
    for distance, position in zip(distances[0], indices[0]):
        # Convert L2 distance to a 0-1 similarity score (higher = more similar).
        similarity = float(1 / (1 + distance))
        results.append({**datasets[position], "similarity": similarity})
    return results
