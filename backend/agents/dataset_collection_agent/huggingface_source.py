from typing import Dict, List
import re

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
        try:
            detail = requests.get(f"{HF_DATASETS_URL}/{item['id']}", timeout=REQUEST_TIMEOUT_SECONDS)
            detail.raise_for_status()
            metadata = detail.json()
        except (requests.RequestException, ValueError, TypeError):
            continue
        card = metadata.get("cardData") or {}
        if not isinstance(card, dict):
            continue
        tags = metadata.get("tags") or []
        categories = card.get("task_categories") or []
        if isinstance(categories, str):
            categories = [categories]
        categories += [tag.split(":", 1)[1] for tag in tags if tag.startswith("task_categories:")]
        task_map = {"image-classification": ("computer_vision", "image"), "object-detection": ("computer_vision", "image"), "text-classification": ("nlp", "text"), "text-generation": ("nlp", "text"), "tabular-classification": ("classification", "tabular"), "tabular-regression": ("regression", "tabular"), "time-series-forecasting": ("regression", "time_series")}
        task, modality = next((task_map[c] for c in categories if c in task_map), (DEFAULT_TASK, None))
        license_value = card.get("license") or next((tag.split(":", 1)[1] for tag in tags if tag.startswith("license:")), None)
        if isinstance(license_value, list):
            license_value = ", ".join(license_value)
        contents = metadata.get("description") or card.get("description") or ""
        if modality is None and "modality:tabular" in tags:
            modality = "tabular"
            if re.search(r"\bclassification\b", contents, re.I):
                task = "classification"
            elif re.search(r"\bregression\b", contents, re.I):
                task = "regression"
        description = f"{contents}\nIntended tasks: {', '.join(categories)}"[:2000]
        results.append(
            {
                "id": item["id"],
                "name": item["id"],
                "description": description,
                "domain": DEFAULT_DOMAIN,
                "task": task,
                "data_type": modality,
                "license": license_value,
                "metadata_verified": bool(contents and modality and license_value),
                "similarity": similarity,
                "source": "huggingface",
                # The Hub's own dataset page — the "Files and versions" tab
                # there is where an actual download happens, not proxied here.
                "url": f"https://huggingface.co/datasets/{item['id']}",
            }
        )
    return results
