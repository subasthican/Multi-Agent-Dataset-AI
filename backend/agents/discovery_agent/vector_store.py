from typing import Dict, List, Optional
import os

import faiss
import numpy as np

from security.db import SessionLocal
from security.db_models import CatalogDataset

from .embeddings import create_embeddings

# Both caches are invalidated together — the FAISS index is built from the
# dataset list, so a stale dataset list means a stale index regardless of
# which one actually changed.
_datasets_cache: Optional[List[Dict]] = None
_index_cache: Optional[faiss.IndexFlatIP] = None


def invalidate_cache() -> None:
    """Call after any write to the catalog (admin add/edit/delete via
    /admin/catalog) so the next search rebuilds against current data
    instead of serving a FAISS index built from what the catalog used to
    contain. Without this, an admin's edit would silently never show up in
    search results until the server happened to restart."""
    global _datasets_cache, _index_cache
    _datasets_cache = None
    _index_cache = None


def _read_datasets() -> List[Dict]:
    db = SessionLocal()
    try:
        rows = db.query(CatalogDataset).order_by(CatalogDataset.created_at).all()
        return [{"id": row.id, "name": row.name, "description": row.description,
                 "domain": row.domain, "task": row.task, "data_type": row.data_type,
                 "url": row.url} for row in rows]
    finally:
        db.close()


def load_datasets() -> List[Dict]:
    global _datasets_cache
    if _datasets_cache is None:
        _datasets_cache = _read_datasets()
    return _datasets_cache


def _index_for(datasets):
    if not datasets:
        return None
    vectors = np.array(create_embeddings([dataset["description"] for dataset in datasets])).astype("float32")
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return index


def build_index() -> Optional[faiss.IndexFlatIP]:
    global _index_cache
    if _index_cache is None:
        _index_cache = _index_for(load_datasets())
    return _index_cache


def search_vectors(query: str, k: int = 3) -> List[Dict]:
    if os.getenv("VERCEL") == "1":
        # Other function instances can edit the shared catalog. Search a fresh
        # local snapshot rather than retain an index invalidated only in the
        # instance that handled an admin update. The embedding model is cached.
        datasets = _read_datasets()
        index = _index_for(datasets)
    else:
        datasets = load_datasets()
        index = build_index()
    k = min(k, len(datasets))
    if k == 0 or index is None:
        return []

    query_vector = np.array(create_embeddings([query])).astype("float32")
    faiss.normalize_L2(query_vector)
    similarities, indices = index.search(query_vector, k)

    results = []
    for value, position in zip(similarities[0], indices[0]):
        # Same normalized cosine metric as external-source ranking.
        similarity = max(0.0, min(1.0, float(value)))
        results.append({**datasets[position], "similarity": similarity})
    return results
