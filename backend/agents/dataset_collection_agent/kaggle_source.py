import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import numpy as np
from dotenv import load_dotenv

from agents.discovery_agent.embeddings import create_embeddings

# Repo-root .env, same convention as llm/gemini_client.py.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

DEFAULT_DOMAIN = "unspecified"
DEFAULT_TASK = "unspecified"


class KaggleUnavailableError(Exception):
    """Raised when Kaggle search can't be performed (no token, auth/API error)."""


@lru_cache(maxsize=1)
def _get_client():
    if not os.getenv("KAGGLE_API_TOKEN"):
        raise KaggleUnavailableError("KAGGLE_API_TOKEN is not set")

    # Imported lazily: the kaggle package prints an auth-help banner on import
    # and its own authenticate() calls sys.exit(1) on total failure, so we
    # only import/authenticate once a token is actually configured, and still
    # guard the call below.
    from kaggle import KaggleApi

    api = KaggleApi()
    try:
        api.authenticate()
    except (Exception, SystemExit) as exc:  # noqa: BLE001 - kaggle's authenticate() can exit(1)
        raise KaggleUnavailableError(str(exc)) from exc
    return api


def _cosine_similarity(query: str, texts: List[str]) -> List[float]:
    vectors = np.array(create_embeddings([query, *texts]))
    query_vector, text_vectors = vectors[0], vectors[1:]
    query_norm = query_vector / np.linalg.norm(query_vector)

    similarities = []
    for vector in text_vectors:
        vector_norm = vector / np.linalg.norm(vector)
        similarities.append(max(0.0, float(np.dot(query_norm, vector_norm))))
    return similarities


def search_kaggle_datasets(query: str, limit: int = 5) -> List[Dict]:
    """Search live Kaggle datasets and score them against the query.

    Domain/task are left as "unspecified" since Kaggle's search API doesn't
    expose that metadata directly (unlike the curated catalog in
    discovery_agent/datasets.json).
    """
    api = _get_client()
    try:
        results = api.dataset_list(search=query) or []
    except Exception as exc:  # noqa: BLE001 - surface any Kaggle API failure uniformly
        raise KaggleUnavailableError(str(exc)) from exc

    results = results[:limit]
    if not results:
        return []

    descriptions = [item.description or item.subtitle or item.title for item in results]
    similarities = _cosine_similarity(query, descriptions)

    datasets = []
    for item, description, similarity in zip(results, descriptions, similarities):
        datasets.append(
            {
                "id": item.ref,
                "name": item.title,
                "description": description,
                "domain": DEFAULT_DOMAIN,
                "task": DEFAULT_TASK,
                "similarity": similarity,
                "source": "kaggle",
            }
        )
    return datasets
