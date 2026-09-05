from typing import Dict, List

import requests

from agents.discovery_agent.embeddings import rank_by_similarity

OPENML_LIST_URL = "https://www.openml.org/api/v1/json/data/list/data_name"
REQUEST_TIMEOUT_SECONDS = 8
DEFAULT_DOMAIN = "unspecified"
DEFAULT_TASK = "unspecified"


def search_openml_datasets(query: str, limit: int = 5) -> List[Dict]:
    """Search OpenML's free, no-auth dataset listing.

    OpenML's data_name endpoint only matches a dataset's short technical
    name (e.g. "diabetes", "credit-g") - not descriptions or tags - so it's
    considerably narrower than Kaggle/HuggingFace search and legitimately
    returns nothing for most multi-word or generic terms. That's expected,
    not a bug: only the first keyword in the query is even sent. A 412 from
    OpenML means "no results" (their API's own convention, not an error),
    handled the same as any other failure - an empty list, not an exception.
    """
    keyword = next((token for token in query.strip().split() if token), "")
    if not keyword:
        return []

    try:
        response = requests.get(f"{OPENML_LIST_URL}/{keyword}/limit/{limit}", timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException:
        return []

    if response.status_code != 200:
        return []

    try:
        datasets = response.json()["data"]["dataset"]
    except (ValueError, KeyError, TypeError):
        return []
    if not datasets:
        return []

    descriptions = [_describe(entry) for entry in datasets]
    similarities = rank_by_similarity(query, descriptions)

    results = []
    for entry, description, similarity in zip(datasets, descriptions, similarities):
        results.append(
            {
                "id": f"openml-{entry['did']}",
                "name": entry["name"],
                "description": description,
                "domain": DEFAULT_DOMAIN,
                "task": DEFAULT_TASK,
                "similarity": similarity,
                "source": "openml",
                # OpenML's own dataset page for this "did" — its own
                # download/ARFF/CSV links live there, not proxied here.
                "url": f"https://www.openml.org/d/{entry['did']}",
            }
        )
    return results


def _describe(entry: Dict) -> str:
    """OpenML gives quality metrics, not free-text descriptions - this
    builds a short human-readable summary from them for display and for
    the similarity embedding."""
    quality = {q["name"]: q["value"] for q in entry.get("quality", [])}
    instances = quality.get("NumberOfInstances")
    features = quality.get("NumberOfFeatures")

    parts = [f"{entry['name']} dataset"]
    if instances:
        parts.append(f"{int(float(instances))} instances")
    if features:
        parts.append(f"{int(float(features))} features")
    return ", ".join(parts)
