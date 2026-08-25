from typing import Dict, List

from .kaggle_source import KaggleUnavailableError, search_kaggle_datasets


def collect_external_datasets(query: str, limit: int = 5) -> List[Dict]:
    """Best-effort live dataset search. Returns [] when Kaggle isn't configured
    or unreachable, so callers don't need to special-case missing credentials."""
    try:
        return search_kaggle_datasets(query, limit=limit)
    except KaggleUnavailableError:
        return []
