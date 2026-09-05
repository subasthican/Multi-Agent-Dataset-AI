from typing import Dict, List

import requests

from agents.discovery_agent.embeddings import rank_by_similarity

HF_DATASETS_URL = "https://huggingface.co/api/datasets"
REQUEST_TIMEOUT_SECONDS = 8
DESCRIPTION_MAX_LENGTH = 300
DEFAULT_DOMAIN = "unspecified"
DEFAULT_TASK = "unspecified"


def search_huggingface_datasets(query: str, limit: int = 5) -> List[Dict]:
    """Search the HuggingFace Hub's free, no-auth datasets API.

    Like Kaggle, this needs a short query - long multi-word strings
    (verified directly against the live API) return zero results, so callers
    should pass the same short domain+keywords query built for Kaggle, not
    the long one built for the local FAISS catalog search.
    """
    try:
        response = requests.get(
            HF_DATASETS_URL, params={"search": query, "limit": limit}, timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException:
        return []

    if response.status_code != 200:
        return []

    try:
        items = response.json()
    except ValueError:
        return []
    if not items:
        return []

    descriptions = [(item.get("description") or item["id"])[:DESCRIPTION_MAX_LENGTH] for item in items]
    similarities = rank_by_similarity(query, descriptions)

    results = []
    for item, description, similarity in zip(items, descriptions, similarities):
        results.append(
            {
                "id": item["id"],
                "name": item["id"],
                "description": description,
                "domain": DEFAULT_DOMAIN,
                "task": DEFAULT_TASK,
                "similarity": similarity,
                "source": "huggingface",
                # The Hub's own dataset page — the "Files and versions" tab
                # there is where an actual download happens, not proxied here.
                "url": f"https://huggingface.co/datasets/{item['id']}",
            }
        )
    return results
