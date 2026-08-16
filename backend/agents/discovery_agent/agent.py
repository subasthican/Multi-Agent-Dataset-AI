from .models import DatasetMatch, DiscoveryResult
from .vector_store import search_vectors


def search_datasets(query: str, k: int = 3) -> DiscoveryResult:
    """Semantic search over the dataset catalog for a free-text query."""
    raw_matches = search_vectors(query, k=k)
    return DiscoveryResult(
        query=query,
        matches=[DatasetMatch(**match) for match in raw_matches],
    )
